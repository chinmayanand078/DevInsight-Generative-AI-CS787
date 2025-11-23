import json
import faiss
import numpy as np
from pathlib import Path


class VectorStore:
    """
    Wrapper over FAISS index + metadata.
    """

    def __init__(self, dim: int = 2048):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadatas = []

    def build_index(self, embeddings: np.ndarray, metadatas: list[dict]):
        assert embeddings.shape[1] == self.dim
        self.index.add(embeddings)
        self.metadatas = metadatas

    def save(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "embeddings.faiss"))
        with open(directory / "metadata.json", "w") as f:
            json.dump(self.metadatas, f, indent=2)

    def load(self, directory: Path):
        self.index = faiss.read_index(str(directory / "embeddings.faiss"))
        with open(directory / "metadata.json") as f:
            self.metadatas = json.load(f)

    def search(self, query_embedding: np.ndarray, k: int = 5):
        """
        query_embedding shape: (1, dim)
        returns: list of metadata dicts
        """
        distances, idxs = self.index.search(query_embedding, k)
        results = []
        for i in idxs[0]:
            if i < len(self.metadatas):
                results.append(self.metadatas[i])
        return results

