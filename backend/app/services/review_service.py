import time
import re

from backend.app.schemas import ReviewRequest, ReviewResponse, ReviewComment
from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import build_review_prompt
from backend.app.services.rag_service import get_context_for_review
from backend.app.services.metrics_service import record_review_metrics


async def run_review(request: ReviewRequest) -> ReviewResponse:
    """
    Main entry point for a PR review.
    Integrates RAG context + LLM review + metrics logging.
    """
    start_time = time.time()  # start metrics timer

    llm = LLMClient()

    # Combine all new code into a single string to use as RAG query
    diff_text = "\n".join([d.new_code for d in request.diffs])

    # 🔍 Step 1 — retrieve relevant repo context
    rag_context = await get_context_for_review(diff_text)

    # 🔍 Step 2 — build LLM prompt
    prompt = build_review_prompt(request, rag_context)

    # 🔍 Step 3 — call LLM
    raw_output = await llm.generate_review(prompt)

    # 🔍 Step 4 — parse LLM output
    comments = []
    for line in raw_output.split("\n"):
        match = re.match(
            r"- filename: (.+) \| line: (\d+) \| severity: (\w+) \| message: (.+)",
            line.strip(),
        )
        if match:
            comments.append(
                ReviewComment(
                    filename=match.group(1),
                    line=int(match.group(2)),
                    severity=match.group(3),
                    message=match.group(4),
                )
            )

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

