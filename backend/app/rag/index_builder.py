from pathlib import Path
from backend.app.rag.loaders.repo_loader import load_repo_text
from backend.app.rag.chunking import chunk_text
from backend.app.llm.client import LLMClient
from backend.app.rag.vector_store import VectorStore
import asyncio

INDEX_DIR = Path("backend/app/rag/index")


async def main():
    print("🔍 Loading repository documentation...")
    docs = load_repo_text(base_path=".")

    print(f"📄 Loaded {len(docs)} documents")

    all_chunks = []
    metadatas = []

    print("✂️ Chunking documents...")
    for content, meta in docs:
        chunks = chunk_text(content)
        for chunk in chunks:
            all_chunks.append(chunk)
            metadatas.append(meta)

    print(f"🔢 Total chunks: {len(all_chunks)}")

    print("🧠 Generating embeddings...")
    llm = LLMClient()
    embeddings = await llm.embed(all_chunks)

    print("💾 Building FAISS vector index...")
    store = VectorStore(dim=768)
    store.build_index(embeddings, metadatas)
    store.save(INDEX_DIR)

    print(f"✅ Index saved to: {INDEX_DIR}")


if __name__ == "__main__":
    asyncio.run(main())

