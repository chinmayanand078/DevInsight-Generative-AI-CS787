from pathlib import Path
import numpy as np
from backend.app.llm.client import LLMClient
from backend.app.rag.vector_store import VectorStore

INDEX_DIR = Path("backend/app/rag/index")


async def get_context_for_review(diff_text: str, k: int = 5):
    """
    Convert PR diff to embedding → search FAISS → return top metadata chunks
    """
    llm = LLMClient()
    store = VectorStore()

    if not (INDEX_DIR / "embeddings.faiss").exists():
        return []

    store.load(INDEX_DIR)

    # Use the diff text directly as query
    query_embedding = await llm.embed([diff_text])
    results = store.search(query_embedding, k=k)

    return results

