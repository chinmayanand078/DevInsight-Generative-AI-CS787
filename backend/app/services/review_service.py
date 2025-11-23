import time
import ast

from backend.app.schemas import ReviewRequest, ReviewResponse, ReviewComment
from backend.app.services.rag_service import get_context_for_review
from backend.app.services.metrics_service import record_review_metrics
from backend.app.static_analysis.analyzer import estimate_complexity


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
                )
            )

        if stripped.startswith("print("):
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="warning",
                    message="Replace print with structured logging for observability.",
                )
            )

        if stripped.startswith("except:"):
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="critical",
                    message="Bare except found; catch specific exception types to avoid masking errors.",
                )
            )

        if "eval(" in stripped:
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="critical",
                    message="Use of eval is unsafe; prefer explicit parsing or whitelisted operations.",
                )
            )

        if "password" in line.lower() and "=" in line:
            comments.append(
                ReviewComment(
                    filename=filename,
                    line=idx,
                    severity="warning",
                    message="Potential secret in code; ensure credentials are loaded from environment or vault.",
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
                    )
                )
    return comments


async def run_review(request: ReviewRequest) -> ReviewResponse:
    """
    Main entry point for a PR review.
    Integrates RAG context + deterministic lint review + metrics logging.
    """
    start_time = time.time()  # start metrics timer

    # Combine all new code into a single string to use as RAG query
    diff_text = "\n".join([d.new_code for d in request.diffs])

    # 🔍 Step 1 — retrieve relevant repo context
    rag_context = await get_context_for_review(diff_text)

    # 🔍 Step 2 — heuristic lint pass (deterministic, no external LLM)
    comments: list[ReviewComment] = []
    for diff in request.diffs:
        if diff.new_code:
            comments.extend(_lint_lines(diff.filename, diff.new_code))
            comments.extend(_lint_ast(diff.filename, diff.new_code))

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

