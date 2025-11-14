import time
from backend.app.utils.logging_utils import log_json


def record_review_metrics(pr_number: int, findings_count: int, rag_sources: list, duration_sec: float):
    """
    Logs review metrics used to evaluate DevInsight performance.
    """
    log_json("review_metrics.log", {
        "pr_number": pr_number,
        "findings_count": findings_count,
        "rag_sources": rag_sources,
        "duration_sec": duration_sec
    })

