import json
from pathlib import Path

import faiss
import numpy as np


class VectorStore:
    """
    Wrapper over FAISS index + metadata.
    """

    def __init__(self, dim: int | None = None, embedder: str | None = None):
        """Initialize an empty FAISS-backed vector store."""
        self.dim = dim
        self.embedder = embedder
        self.index: faiss.Index | None = None
        self.metadatas: list[dict] = []

    def build_index(self, embeddings: np.ndarray, metadatas: list[dict], embedder: str | None = None):
        """Create a new in-memory FAISS index from embeddings and metadata."""
        self.dim = embeddings.shape[1]
        self.embedder = embedder
        self.index = faiss.IndexFlatL2(self.dim)
        self.index.add(embeddings)
        self.metadatas = metadatas

    def save(self, directory: Path):
        """Persist the FAISS index and metadata to the given directory."""
        directory.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(directory / "embeddings.faiss"))
        with open(directory / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dim": self.dim,
                    "documents": self.metadatas,
                    "embedder": self.embedder,
                },
                f,
                indent=2,
            )

    def load(self, directory: Path):
        """Load a FAISS index and metadata from disk."""
        self.index = faiss.read_index(str(directory / "embeddings.faiss"))
        self.dim = self.index.d
        with open(directory / "metadata.json", encoding="utf-8") as f:
            payload = json.load(f)
            if isinstance(payload, dict) and "documents" in payload:
                self.metadatas = payload.get("documents", [])
                self.embedder = payload.get("embedder")
            else:
                # legacy format without embedder metadata
                self.metadatas = payload
                self.embedder = None

    def search(self, query_embedding: np.ndarray, k: int = 5, embedder: str | None = None):
        """
        query_embedding shape: (1, dim)
        returns: list of metadata dicts
        """
        if self.index is None:
            return []

        if query_embedding.shape[1] != self.index.d:
            raise ValueError(
                f"Query dim {query_embedding.shape[1]} != index dim {self.index.d}. "
                "Rebuild the FAISS index with the same embedding model used at runtime."
            )

        if embedder and self.embedder and embedder != self.embedder:
            raise ValueError(
                "Embedding model mismatch: the FAISS index was built with "
                f"'{self.embedder}' but the current query uses '{embedder}'. "
                "Rebuild the index after setting the desired EMBEDDING_MODEL."
            )

        distances, idxs = self.index.search(query_embedding, k)
        results = []
        for i in idxs[0]:
            if i < len(self.metadatas):
                results.append(self.metadatas[i])
        return results

