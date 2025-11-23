# 🚀 DevInsight AI — Automated Code Review & Documentation Intelligence

DevInsight AI is a FastAPI backend that demonstrates a code-intelligence pipeline (code review + RAG-assisted context + unit-test suggestions). The current repository focuses on the backend skeleton described in the course project report and now ships with deterministic, locally runnable behaviors (no external keys required) **plus optional real-model integrations** if you provide credentials.

## 🎯 What works today

- REST API with `/health`, `/review`, and `/generate-tests` endpoints implemented in FastAPI.
- RAG scaffolding that indexes repository Markdown/Python/text/config docs (MD/MDX/RST/JSON/YAML/TOML/INI/CFG) **and recent Git history** into a FAISS store (skips binaries and oversized files) with pluggable embeddings. Chunks store their source path plus snippet so LLM prompts stay grounded. Embeddings are deterministic hashing by default, or Sentence Transformers when configured and rebuilt with that encoder.
- Deterministic, heuristic code review with an **optional OpenAI-backed path** for structured findings when `LLM_PROVIDER=openai` and a key are set. LLM results merge with lint feedback and are deduplicated by severity.
- Deterministic pytest generation based on static analysis that stubs importable tests for each detected function, with optional LLM-enriched tests and one-shot pytest+coverage execution. Coverage output now includes total percent, missing-line hints, and whether a goal (`smoke`/`basic`/`strong`/`max`) was met.
- Metrics hooks that record basic timing/usage information in memory.
- GitHub integration helpers: REST client plus an Actions-friendly runner (`backend/app/integrations/github_workflow.py`) that can post results back to a PR, with a ready-to-use workflow in `.github/workflows/devinsight.yml`.
- A training starter script (`training/finetune_llama3.py`) showing how to fine-tune Llama 3 style models on custom review/test data.

## ⚠️ Known gaps (compared to the project vision)

- Default mode stays deterministic; LLM-backed review requires your own API key and model access.
- Semantic retrieval requires downloading an encoder (Sentence Transformers); set `EMBEDDING_MODEL`, rebuild the FAISS index, and the runtime will enforce that the query embedder matches the stored index embedder.
- GitHub commenting is wired through `.github/workflows/devinsight.yml`; set your secrets (e.g., `OPENAI_API_KEY`, `EMBEDDING_MODEL` if you want semantic retrieval) and the workflow will post a summary comment on pull requests.

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
├─ training/              # Optional fine-tuning scripts + requirements
├─ CS787_report.pdf       # Project write-up (alternate filename: CS787_Report_Final.pdf)
└─ ...
```

## 🧭 Getting started (step-by-step)

If you want exact commands and environment setup guidance, follow [docs/SETUP.md](docs/SETUP.md). It walks through creating a virtual environment, installing dependencies, building the FAISS index, running the API, and exercising each endpoint with sample `curl` payloads.

To switch from deterministic mocks to real ChatGPT-powered findings, see the "Enabling real ChatGPT responses" section in [docs/SETUP.md](docs/SETUP.md) for the exact `.env` variables and restart steps.

## 🔌 GitHub PR automation (turnkey)

- The repo ships with `.github/workflows/devinsight.yml`, which runs compile checks on pushes/PRs and, on pull requests, builds the FAISS index, runs the review pipeline, and posts a summary comment back to the PR.
- Deterministic mode works with the default `GITHUB_TOKEN`; to enable LLM-backed findings, semantic retrieval, and LLM-enriched tests with coverage goals, add `OPENAI_API_KEY` and/or `EMBEDDING_MODEL` as repository secrets and rerun the workflow so the index is rebuilt with the chosen encoder.
- `fetch-depth: 0` is already set so diffs can be computed against the base branch; the workflow helper also fetches the base ref/sha and falls back to local history if the remote is unavailable (e.g., some forked PRs).

## 🛣 Roadmap ideas

- Add optional self-hosted model runners with streaming responses and cost controls.
- Support incremental/continuous indexing so large repos can refresh RAG without a full rebuild.
- Emit inline PR comments from the workflow helper instead of a single summary, and add policy gates (block/approve) based on severity.
- Enrich test generation with fixtures/parametrization plus mutation-fuzzing hooks for differential coverage.

## 🤝 Contributing

Contributions are welcome! Please open an Issue to discuss any substantial change, especially if it touches the API contract or introduces new runtime dependencies.
