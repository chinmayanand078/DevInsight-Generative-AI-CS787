import ast
import json
import time
from textwrap import dedent

from backend.app.llm.client import LLMClient
from backend.app.schemas import ReviewRequest, ReviewResponse, ReviewComment
from backend.app.services.metrics_service import record_review_metrics
from backend.app.services.rag_service import get_context_for_review
from backend.app.static_analysis.analyzer import estimate_complexity
from backend.app.config import settings


def _lint_lines(filename: str, new_code: str) -> list[ReviewComment]:
    comments: list[ReviewComment] = []
    for idx, line in enumerate(new_code.splitlines(), start=1):
        stripped = line.strip()

        if "TODO" in line:
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="info",
                    message="TODO left in code; either address or convert to tracked issue.",
                    source="lint",
                )
            )

        if stripped.startswith("print("):
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="warning",
                    message="Replace print with structured logging for observability.",
                    source="lint",
                )
            )

        if stripped.startswith("except:"):
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="critical",
                    message="Bare except found; catch specific exception types to avoid masking errors.",
                    source="lint",
                )
            )

        if "eval(" in stripped:
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="critical",
                    message="Use of eval is unsafe; prefer explicit parsing or whitelisted operations.",
                    source="lint",
                )
            )

        if "password" in line.lower() and "=" in line:
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="warning",
                    message="Potential secret in code; ensure credentials are loaded from environment or vault.",
                    source="lint",
                )
            )
    return comments


def _lint_ast(filename: str, new_code: str) -> list[ReviewComment]:
    comments: list[ReviewComment] = []
    try:
        tree = ast.parse(new_code)
    except SyntaxError:
        return comments

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node) is None:
                comments.append(
                    ReviewComment(
                        filename=filename,
                        line=node.lineno,
                        severity="info",
                        message=f"Function '{node.name}' is missing a docstring.",
                        source="lint",
                    )
                )

            complexity = estimate_complexity(ast.get_source_segment(new_code, node) or "")
            if complexity > 10:
                comments.append(
                    ReviewComment(
                        filename=filename,
                        line=node.lineno,
                        severity="warning",
                        message=f"Function '{node.name}' has high branch count ({complexity}); consider refactoring.",
                        source="lint",
                    )
                )
    return comments


def _dedupe_comments(comments: list[ReviewComment]) -> list[ReviewComment]:
    """Prefer highest-severity comment when duplicates appear on the same line."""

    severity_rank = {"critical": 3, "warning": 2, "info": 1}
    merged: dict[tuple[str, int, str], ReviewComment] = {}

    for comment in comments:
        key = (comment.filename, comment.line, comment.message.strip())
        existing = merged.get(key)
        if existing:
            current_score = severity_rank.get(comment.severity, 0)
            prev_score = severity_rank.get(existing.severity, 0)
            if current_score > prev_score:
                merged[key] = comment
        else:
            merged[key] = comment

    return list(merged.values())


def _format_rag_context(chunks: list[dict]) -> str:
    rendered = []
    for chunk in chunks or []:
        src = chunk.get("source", "repo")
        text = chunk.get("chunk") or chunk.get("text") or ""
        if not text:
            continue
        rendered.append(f"[{src}] {text}")
    return "\n".join(rendered)


async def run_review(request: ReviewRequest) -> ReviewResponse:
    """
    Main entry point for a PR review.
    Integrates RAG context + deterministic lint review + optional LLM + metrics logging.
    """
    start_time = time.time()  # start metrics timer

    # Combine all new code into a single string to use as RAG query
    diff_text = "\n".join([d.new_code for d in request.diffs])

    # 🔍 Step 1 — retrieve relevant repo context
    rag_context = await get_context_for_review(diff_text)
    rag_context_text = _format_rag_context(rag_context)

    # 🔍 Step 2 — heuristic lint pass (deterministic, no external LLM)
    comments: list[ReviewComment] = []
    for diff in request.diffs:
        if diff.new_code:
            comments.extend(_lint_lines(diff.filename, diff.new_code))
            comments.extend(_lint_ast(diff.filename, diff.new_code))

    # 🤖 Step 3 — optional LLM suggestions (structured JSON)
    if settings.LLM_PROVIDER != "mock" and settings.LLM_API_KEY:
        llm = LLMClient()
        lint_summary = "\n".join(
            f"- {c.filename}:{c.line} [{c.severity}] {c.message}" for c in comments
        ) or "(none)"
        prompt = dedent(
            f"""
            You are a senior code reviewer. Given the PR diffs, existing lint findings, and
            repository context snippets, return ONLY JSON of the form:
            {{"findings": [{{"filename": str, "line": int, "severity": str, "message": str}}]}}.

            DIFFS:\n{diff_text}\n
            EXISTING LINT FINDINGS:\n{lint_summary}\n
            RAG CONTEXT SNIPPETS:\n{rag_context_text}
            """
        ).strip()

        try:
            raw = await llm.generate_review(prompt)
            parsed = json.loads(raw)
            for finding in parsed.get("findings", []):
                comments.append(
                    ReviewComment(
                        filename=finding.get("filename", "unknown"),
                        line=int(finding.get("line", 1)),
                        severity=finding.get("severity", "info"),
                        message=finding.get("message", "LLM suggestion"),
                        source="llm",
                        model=settings.MODEL_NAME,
                    )
                )
        except Exception:
            # Keep lint-only output if LLM parsing fails
            pass

    comments = _dedupe_comments(comments)

    # 📊 Step 5 — metrics logging
    duration = time.time() - start_time
    rag_sources_used = [chunk.get("source", "unknown") for chunk in rag_context] if rag_context else []

    record_review_metrics(
        pr_number=request.pr_number,
        findings_count=len(comments),
        rag_sources=rag_sources_used,
        duration_sec=duration
    )

    return ReviewResponse(comments=comments)

