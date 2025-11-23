# 🚀 DevInsight AI — Automated Code Review & Documentation Intelligence

DevInsight AI is a FastAPI backend that demonstrates a code-intelligence pipeline (code review + RAG-assisted context + unit-test suggestions). The current repository focuses on the backend skeleton described in the course project report and now ships with deterministic, locally runnable behaviors (no external keys required).

## 🎯 What works today

- REST API with `/health`, `/review`, and `/generate-tests` endpoints implemented in FastAPI.
- RAG scaffolding that indexes repository Markdown/Python/text files **and recent Git history** into a FAISS store (skips binaries and oversized files).
- Deterministic, heuristic code review (no LLM dependency) that flags bare `except`, stray `print`, missing docstrings, TODOs, and other quick wins.
- Deterministic pytest generation based on static analysis that stubs importable tests for each detected function, with optional one-shot pytest+coverage execution when you provide a `coverage_goal` in the request.
- Metrics hooks that record basic timing/usage information in memory.
- A minimal GitHub REST helper to post PR/commit comments when supplied with a token.

## ⚠️ Known gaps (compared to the project vision)

- No real LLM calls: review and test generation are deterministic heuristics; swap in a proper encoder or model when available.
- Embeddings are still deterministic HashingVectorizer outputs; swap in a semantic encoder if you need richer retrieval quality.
- GitHub integration is provided as a helper module but not wired to a running bot; connect it to your workflow with a token to post comments automatically.

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

- Swap the heuristic review/test generators for real model calls (e.g., OpenAI or self-hosted Llama 3) and feed embeddings from a true encoder.
- Expand RAG ingestion to include Git history and design docs beyond text/Markdown/Python.
- Add a GitHub bot step that posts review/test suggestions directly on PRs using the existing workflow skeleton.
- Implement real coverage measurement and richer test generation (fixtures, parametrization, mutation checks).

## 🤝 Contributing

Contributions are welcome! Please open an Issue to discuss any substantial change, especially if it touches the API contract or introduces new runtime dependencies.
