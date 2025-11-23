# 🚀 DevInsight AI — Automated Code Review & Documentation Intelligence

DevInsight AI is a FastAPI backend that demonstrates a code-intelligence pipeline (code review + RAG-assisted context + unit-test suggestions). The current repository focuses on the backend skeleton described in the course project report.

## 🎯 What works today

- REST API with `/health`, `/review`, and `/generate-tests` endpoints implemented in FastAPI.
- RAG scaffolding that indexes `README.md` and any `docs/*.md` files into a FAISS store.
- Mocked LLM client that returns deterministic review text and deterministic hash-based embeddings so the pipeline runs end-to-end without external keys.
- Metrics hooks that record basic timing/usage information in memory.

## ⚠️ Known gaps (compared to the project vision)

- No real LLM calls: `LLMClient` returns mock reviews and hash-based TF embeddings; swap in a proper encoder for semantic similarity.
- RAG indexing only reads `README.md` and `docs/*.md`; it does **not** ingest Git history or arbitrary design documents.
- GitHub integration is not wired: there is no `.github/workflows/` pipeline or GitHub API client in this repository.
- Unit-test generation is stubbed; coverage is not measured and generated tests come from mocked LLM output.

## 📁 Project structure (current repository)

```
DevInsight-Generative-AI-CS787/
├─ README.md              # This file
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI app with /health, /review, /generate-tests
│  │  ├─ schemas.py       # Request/response models
│  │  ├─ services/        # Review, test-gen, metrics, and RAG helpers
│  │  ├─ rag/             # Index builder, chunking, FAISS wrapper
│  │  ├─ llm/             # Mock LLM client and prompt helpers
│  │  └─ static_analysis/ # Lightweight static analyzer
│  ├─ requirements.txt    # Backend dependencies
│  └─ uvicorn_run.sh      # Convenience script to launch the API
├─ CS787_report.pdf       # Project write-up (alternate filename: CS787_Report_Final.pdf)
└─ ...
```

## 🧭 Getting started (step-by-step)

If you want exact commands and environment setup guidance, follow [docs/SETUP.md](docs/SETUP.md). It walks through creating a virtual environment, installing dependencies, building the FAISS index, running the API, and exercising each endpoint with sample `curl` payloads.

## 🛣 Roadmap ideas

- Swap the mock `LLMClient` for a real model call (e.g., OpenAI or self-hosted Llama 3) and feed embeddings from a true encoder.
- Expand RAG ingestion to include Git history, code files, and design docs.
- Add a `.github/workflows/devinsight.yml` workflow plus GitHub API calls to post review results as PR comments.
- Implement real coverage measurement and richer test generation beyond the current stub.

## 🤝 Contributing

Contributions are welcome! Please open an Issue to discuss any substantial change, especially if it touches the API contract or introduces new runtime dependencies.
