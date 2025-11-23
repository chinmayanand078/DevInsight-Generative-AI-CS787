import json
from typing import Iterable, Optional

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from ..config import settings


class LLMClient:
    """Generic wrapper for a real LLM or a deterministic mock.

    - If ``LLM_PROVIDER=mock`` or no API key is supplied, responses are
      deterministic and local.
    - If ``LLM_PROVIDER=openai`` and ``LLM_API_KEY`` is set, the client will call
      the OpenAI chat/completions endpoint with a concise, structured prompt.
    - Embeddings default to a hashing vectorizer but will use a
      sentence-transformers model when ``EMBEDDING_MODEL`` is provided.
    """

    def __init__(self) -> None:
        # Deterministic fallback embedder
        self._vectorizer = HashingVectorizer(
            n_features=2048,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._st_model = None

    @property
    def embedder_id(self) -> str:
        """Human-readable identifier for the active embedding strategy."""

        if self._use_semantic_embeddings:
            model_name = settings.EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
            return f"sentence-transformers:{model_name}"
        return "hashing:sklearn-2048-ngram12"

    @property
    def _use_semantic_embeddings(self) -> bool:
        return settings.EMBEDDING_MODEL is not None

    def _get_sentence_transformer(self):
        if self._st_model is not None:
            return self._st_model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for semantic embeddings. "
                "Install it (pip install sentence-transformers) or unset EMBEDDING_MODEL"
            ) from exc

        model_name = settings.EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
        self._st_model = SentenceTransformer(model_name)
        return self._st_model

    async def generate_review(self, prompt: str) -> str:
        """Return review text from either the configured LLM or a deterministic mock."""

        if settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
                response = await client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise code-review agent. Respond ONLY with a JSON "
                                "object containing a 'findings' list. Each finding must have "
                                "filename, line, severity, and message fields."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )
                content = response.choices[0].message.content or ""

                # If the model returns valid JSON, surface it; otherwise, fall back to mock text
                try:
                    json.loads(content)
                    return content
                except json.JSONDecodeError:
                    pass
            except Exception:
                # Silently drop to mock so workflows stay deterministic in CI
                pass

        # Deterministic mock fallback
        return json.dumps(
            {
                "findings": [
                    {
                        "filename": "sample.py",
                        "line": 10,
                        "severity": "warning",
                        "message": "Variable name too short.",
                    },
                    {
                        "filename": "sample.py",
                        "line": 22,
                        "severity": "info",
                        "message": "Consider adding documentation.",
                    },
                ]
            },
            indent=2,
        )

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for RAG.

        - If a sentence-transformers model is available and configured, we return
          its semantic embeddings.
        - Otherwise we fall back to deterministic hashing features.
        """

        if self._use_semantic_embeddings:
            model = self._get_sentence_transformer()
            vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return vectors.astype("float32")

        sparse_vectors = self._vectorizer.transform(texts)
        return sparse_vectors.toarray().astype("float32")

