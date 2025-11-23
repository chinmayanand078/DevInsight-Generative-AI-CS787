# Prompt for DeepSeek: Generate a Full LaTeX Code Walkthrough

Use this prompt with DeepSeek (or any strong code-understanding model) to generate a **self-contained LaTeX document** that explains the entire DevInsight AI repository from the ground up: file structure, execution flow, and how each piece of code works. The goal is to help a project supervisor quickly understand what the system does and how the parts interact.

```
You are an expert technical writer and code analyst. Produce a comprehensive LaTeX document that explains the DevInsight AI repository. The document must be fully compilable with `pdflatex` (no external images required) and stand alone. Follow these rules:

1) Document skeleton
- Use `\documentclass[11pt]{article}`.
- Include packages: `hyperref`, `geometry`, `enumitem`, `xcolor`, `listings`, `longtable`, `booktabs`, `amsmath`, `amsfonts`, `amssymb`, `graphicx`.
- Define a `listings` style for Python; keep snippets short and illustrative.
- Start with `\tableofcontents` after the title.

2) High-level narrative
- Begin with a plain-English overview of the project’s purpose: FastAPI backend for automated code review, RAG context, and test generation, with deterministic defaults and optional LLM/semantic modes.
- Summarize current capabilities vs. known gaps (LLM optionality, semantic embeddings require configuration, no multi-agent orchestration, no auto outcome metrics).

3) Repository map (must be accurate)
- Provide a tree-style breakdown of key paths with one-line explanations, covering at least:
  - `backend/app/main.py` (FastAPI app wiring `/health`, `/review`, `/generate-tests`).
  - `backend/app/schemas.py` (Pydantic request/response models including coverage goals and metadata).
  - `backend/app/services/` (review_service, testgen_service, rag_service, metrics, static_analysis helpers).
  - `backend/app/rag/` (index_builder, vector_store, loaders/repo_loader.py, chunking/metadata, FAISS handling, embedder metadata enforcement).
  - `backend/app/llm/` (client with deterministic + OpenAI paths, prompt utilities, semantic embedding toggles).
  - `backend/app/integrations/` (github_client.py, github_workflow.py runner for Actions).
  - `backend/app/testing/coverage_runner.py` (optional pytest+coverage execution and summaries).
  - `backend/requirements.txt`, `.github/workflows/devinsight.yml` (CI/PR automation), `docs/*.md`, `training/finetune_llama3.py`, `training/requirements.txt`.

4) Execution flow explanations
- Describe end-to-end for `/review`: request schema → RAG context retrieval → lint + optional LLM findings → dedup/merge → response structure. Call out how embedder metadata prevents dimension mismatches.
- Describe end-to-end for `/generate-tests`: static analysis → test scaffolding → optional LLM-enriched tests → optional `pytest --cov` run → coverage summary fields in response.
- Describe RAG build/search: repo_loader traversal rules (what files are included/excluded), chunking, embedding (hash vs. SentenceTransformer), FAISS index save/load with embedder id/dimension guards.
- Describe GitHub workflow runner: reading event payload, resolving refs, diffing changed files, calling review API, posting PR comment; note required secrets for LLM/semantic modes.
- Describe training starter (`training/finetune_llama3.py`): dataset loading, tokenization, trainer config, CLI args; clarify that it is a scaffold, not a full production trainer.

5) Per-file highlights
For each core file, include a short bullet list covering:
- Purpose of the module.
- Key functions/classes and what they do.
- Important parameters/return values.
- Notable safeguards (e.g., avoiding eval, avoiding missing docstrings, logging). Keep summaries concise but precise.

6) Interaction diagram (textual)
- Provide a textual sequence (no graphics required) showing how a `/review` request flows through FastAPI → schemas → services → rag/llm/static_analysis → response.
- Provide a similar textual sequence for `/generate-tests` including optional coverage run.

7) Configuration and prerequisites
- Explain `.env` variables that matter: `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `EMBEDDING_MODEL`, `FAISS_INDEX_PATH`, `REPO_ROOT`, `GITHUB_TOKEN`, etc.
- Note that LLM/semantic paths are optional; deterministic hashing/heuristics work without keys but semantic search requires rebuilding the index with the configured encoder.

8) Usage examples
- Provide curl examples for `/health`, `/review`, `/generate-tests` (showing a minimal payload and one with LLM+coverage options).
- Provide a short note on running the GitHub Action (`.github/workflows/devinsight.yml`) and what secrets enable richer behavior.

9) Testing and metrics
- State that CI runs `python -m compileall backend` by default.
- Describe optional local smoke tests (build index, start server, hit endpoints) and coverage-enabled testgen.
- Clarify that performance/quality metrics (e.g., PR time reduction, coverage lift) are not automatically measured by the backend.

10) Tone and safety
- Write factually based on the repository; do not speculate or invent components.
- Use clear headings and short paragraphs/bullets so a supervisor can skim.
- Keep code listings minimal and correct; prefer pseudocode if needed.

Return only the LaTeX source code.
```
