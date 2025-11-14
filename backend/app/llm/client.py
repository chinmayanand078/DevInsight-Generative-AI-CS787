import httpx
import numpy as np
from ..config import settings


class LLMClient:
    """
    Generic wrapper for any LLM API (OpenAI, Llama3, etc).
    Right now: mock responses so the full DevInsight pipeline works
    (RAG, FAISS, review comments, GitHub bot).
    Later we will replace mock logic with a real LLM API call.
    """

    async def generate_review(self, prompt: str) -> str:
        """
        Generate code review from prompt.
        For now, return a MOCK response so the GitHub bot workflow works end-to-end.
        """
        return (
            "FINDINGS:\n"
            "- filename: sample.py | line: 10 | severity: warning | message: Variable name too short.\n"
            "- filename: sample.py | line: 22 | severity: info | message: Consider adding documentation.\n"
        )

    async def embed(self, texts: list[str]) -> np.ndarray:
        """
        Generate vector embeddings for RAG search.
        For now: return random embeddings so FAISS index works.
        Shape = (num_texts, 768)
        """
        return np.random.randn(len(texts), 768).astype("float32")

