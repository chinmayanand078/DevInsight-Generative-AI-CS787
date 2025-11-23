from pathlib import Path
import logging
from backend.app.rag.loaders.repo_loader import load_git_history, load_repo_text
from backend.app.rag.chunking import chunk_text
from backend.app.llm.client import LLMClient
from backend.app.rag.vector_store import VectorStore
import asyncio

INDEX_DIR = Path("backend/app/rag/index")
logger = logging.getLogger(__name__)


async def main():
    """Build the FAISS index for the repository, including git history."""

    logger.info("Loading repository documentation and history...")
    docs = load_repo_text(base_path=".") + load_git_history(base_path=".")

    logger.info("Loaded %d documents", len(docs))

    all_chunks = []
    metadatas = []

    logger.info("Chunking documents...")
    for content, meta in docs:
        chunks = chunk_text(content)
        for chunk in chunks:
            all_chunks.append(chunk)
            enriched = {**meta, "chunk": chunk}
            metadatas.append(enriched)

    logger.info("Total chunks: %d", len(all_chunks))

    logger.info("Generating embeddings...")
    llm = LLMClient()
    embeddings = await llm.embed(all_chunks)

    logger.info("Building FAISS vector index...")
    store = VectorStore()
    store.build_index(embeddings, metadatas, embedder=llm.embedder_id)
    store.save(INDEX_DIR)

    logger.info("Index saved to: %s", INDEX_DIR)


if __name__ == "__main__":
    asyncio.run(main())

