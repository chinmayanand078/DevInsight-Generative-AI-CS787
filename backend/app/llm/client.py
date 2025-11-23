import httpx
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from ..config import settings


class LLMClient:
    """
    Generic wrapper for any LLM API (OpenAI, Llama3, etc).
    Right now: mock responses so the full DevInsight pipeline works
    (RAG, FAISS, review comments, GitHub bot).
    Later we will replace mock logic with a real LLM API call.
    """

    def __init__(self) -> None:
        # HashingVectorizer is stateless and deterministic, so the same text always
        # yields the same embedding without needing to fit on a corpus. This keeps
        # FAISS searches repeatable while avoiding random noise.
        # Bigrams + a larger feature space give more meaningful locality than the
        # initial unigram-only setup while staying stateless/deterministic.
        self._vectorizer = HashingVectorizer(
            n_features=2048,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

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
        Uses a deterministic HashingVectorizer so the same text always maps to the
        same 768-dim vector, enabling reproducible FAISS searches without an
        external embedding service.
        """
        sparse_vectors = self._vectorizer.transform(texts)
        return sparse_vectors.toarray().astype("float32")

