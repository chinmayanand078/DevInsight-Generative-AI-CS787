# DevInsight AI: End-to-End Explanation and Comparison

This document explains how the DevInsight AI backend is organized, how requests flow through it, how it differs from general assistants such as GitHub Copilot, and which technical components (including the provided fine-tuning scaffold) underpin the system.

## 1) Goals and high-level behavior
- **Purpose:** Provide a FastAPI backend that automates code review and test suggestion with reproducible defaults and optional LLM/semantic upgrades when you supply keys/models.
- **Key outcomes:** Deterministic lint-based review plus optional LLM findings; RAG-grounded prompts; static-analysis-driven pytest generation with optional coverage runs; GitHub Action to run the pipeline on pull requests.
- **Modes:** Default deterministic mode (no external keys); semantic embeddings and LLM calls are opt-in via environment variables and index rebuilds.

## 2) Repository map (what lives where)
- `backend/app/main.py` wires the FastAPI app and exposes `/health`, `/review`, and `/generate-tests` endpoints.【F:backend/app/main.py†L1-L32】
- `backend/app/schemas.py` defines request/response models, including coverage goals, test metadata, and review comments.【F:backend/app/schemas.py†L1-L150】
- `backend/app/services/review_service.py` implements the review pipeline: RAG lookup, deterministic linting, optional LLM JSON findings, deduplication, and metrics logging.【F:backend/app/services/review_service.py†L1-L112】【F:backend/app/services/review_service.py†L200-L214】
- `backend/app/services/testgen_service.py` builds pytest files from static analysis, optionally enriches them with LLM-suggested cases, and can run `pytest --cov` to report coverage progress.【F:backend/app/services/testgen_service.py†L1-L118】【F:backend/app/services/testgen_service.py†L120-L165】
- `backend/app/rag/loaders/repo_loader.py` walks the repo, filters binaries/large files, and yields chunks for FAISS indexing; other RAG modules (`index_builder.py`, `vector_store.py`) build and load the store with embedder metadata to prevent dimension mismatches.【F:backend/app/rag/loaders/repo_loader.py†L1-L128】【F:backend/app/rag/index_builder.py†L1-L35】【F:backend/app/rag/vector_store.py†L1-L68】
- `backend/app/llm/client.py` centralizes deterministic vs. OpenAI-backed generation and toggles semantic embeddings when configured.【F:backend/app/llm/client.py†L1-L142】
- `backend/app/testing/coverage_runner.py` runs pytest with coverage and summarizes totals, missing lines, and goal attainment for generated tests.【F:backend/app/testing/coverage_runner.py†L1-L143】
- `backend/app/integrations/github_workflow.py` orchestrates GitHub Action runs: reads event payloads, resolves refs, gathers diffs, calls the review API, and posts PR comments.【F:backend/app/integrations/github_workflow.py†L1-L183】
- `training/finetune_llama3.py` is a minimal fine-tuning scaffold for causal Llama 3 models using Hugging Face Trainer (standard LM objective via `DataCollatorForLanguageModeling` with `mlm=False`).【F:training/finetune_llama3.py†L1-L76】

## 3) End-to-end flows
### `/review`
1. **Request parsing:** Pydantic models validate PR number, branch info, and a list of filename+code diffs.【F:backend/app/schemas.py†L17-L74】
2. **Context retrieval:** Diffs are concatenated and passed to `rag_service.get_context_for_review` to fetch repo snippets from FAISS with embedder checks.【F:backend/app/services/review_service.py†L84-L98】【F:backend/app/rag/vector_store.py†L1-L68】
3. **Deterministic lint:** Line-level checks catch TODOs, prints, bare `except`, `eval`, and possible secrets; AST checks flag missing docstrings and high complexity.【F:backend/app/services/review_service.py†L10-L73】
4. **Optional LLM findings:** If keys/provider are set, the LLM is prompted to return structured JSON findings that merge with lint results and are deduped by severity.【F:backend/app/services/review_service.py†L99-L112】
5. **Metrics:** Duration and RAG sources are recorded for basic observability.【F:backend/app/services/review_service.py†L200-L214】

### `/generate-tests`
1. **Static analysis:** Function signatures, edge cases, and complexity are extracted from the submitted code.【F:backend/app/services/testgen_service.py†L25-L49】
2. **Pytest scaffolding:** Importable module path is derived; pytest functions are rendered with heuristically guessed argument values and placeholder assertions.【F:backend/app/services/testgen_service.py†L51-L78】
3. **Optional LLM augmentation:** When enabled, the LLM proposes extra pytest cases appended with provenance labels.【F:backend/app/services/testgen_service.py†L80-L113】
4. **Optional coverage run:** If `coverage_goal` is set, generated tests execute via `pytest --cov`, and summary/goal status are returned alongside missing-line hints.【F:backend/app/testing/coverage_runner.py†L1-L143】【F:backend/app/services/testgen_service.py†L115-L165】

### RAG build/search
- The repo loader includes Markdown, Python, text, and config formats while skipping binaries and large artifacts; chunk text and source paths are stored as metadata to ground prompts.【F:backend/app/rag/loaders/repo_loader.py†L1-L128】
- Embeddings default to deterministic hashing; if `EMBEDDING_MODEL` is set, SentenceTransformers embeddings are enforced with stored model/dimension metadata to prevent mismatches at query time.【F:backend/app/rag/index_builder.py†L1-L35】【F:backend/app/rag/vector_store.py†L1-L68】【F:backend/app/llm/client.py†L89-L142】

### GitHub Action path
- `.github/workflows/devinsight.yml` checks out full history, builds the FAISS index, runs the review pipeline, and posts a PR comment. The runner resolves base refs/SHAs, reads changed files, and pushes results back via the GitHub REST client.【F:backend/app/integrations/github_workflow.py†L1-L183】

## 4) Configuration (env/flags to toggle behavior)
- **LLM provider/model:** `LLM_PROVIDER`, `LLM_API_KEY`, `OPENAI_MODEL` control whether review/testgen call OpenAI or stay deterministic.【F:backend/app/llm/client.py†L1-L88】
- **Embeddings:** `EMBEDDING_MODEL` switches to SentenceTransformers; indexes must be rebuilt to align dimensions and stored embedder ID.【F:backend/app/llm/client.py†L89-L142】【F:backend/app/rag/index_builder.py†L1-L35】
- **Paths:** `FAISS_INDEX_PATH` and `REPO_ROOT` steer where indexes are saved and what repo is scanned.【F:backend/app/config.py†L1-L60】
- **GitHub Action:** `GITHUB_TOKEN` (default), plus optional `OPENAI_API_KEY`/`EMBEDDING_MODEL` secrets for richer PR comments.【F:.github/workflows/devinsight.yml†L1-L65】

## 5) Improvements vs. general assistants (e.g., GitHub Copilot)
- **Repo-grounded context:** Uses FAISS-backed snippets from the target repo (and recent git history) so findings cite local files instead of generic completions.【F:backend/app/rag/loaders/repo_loader.py†L1-L128】【F:backend/app/rag/vector_store.py†L1-L68】
- **Deterministic lint + optional LLM merge:** Review results are reproducible without keys, with LLM suggestions merged/deduped rather than free-form chat output.【F:backend/app/services/review_service.py†L10-L112】
- **Coverage-aware test generation:** Generates runnable pytest files and can immediately execute them with coverage goals—capabilities outside typical autocomplete tools.【F:backend/app/services/testgen_service.py†L51-L165】【F:backend/app/testing/coverage_runner.py†L1-L143】
- **Turnkey PR automation:** Ships with an Actions workflow and a runner script that posts structured comments to pull requests; Copilot normally provides inline suggestions but not a repo-owned end-to-end reviewer pipeline.【F:backend/app/integrations/github_workflow.py†L1-L183】

## 6) Fine-tuning scaffold and loss function
- `training/finetune_llama3.py` trains a causal Llama model on prompt/completion pairs using Hugging Face Trainer. The `DataCollatorForLanguageModeling` with `mlm=False` applies the standard left-to-right language modeling loss (cross-entropy on next-token prediction).【F:training/finetune_llama3.py†L1-L48】
- Training arguments set batch size, gradient accumulation, learning rate, epochs, and save strategy; models and tokenizers are loaded from Hugging Face IDs you provide.【F:training/finetune_llama3.py†L30-L76】
- This script is a starting point—not wired into the backend runtime—to let you experiment with task-specific fine-tuning data.

## 7) How components interact (textual sequence)
- **Review:** FastAPI endpoint → validate request → build diff text → RAG context → lint checks → optional LLM JSON findings → dedupe → metrics → response payload with filename/line/severity/message.【F:backend/app/main.py†L12-L32】【F:backend/app/services/review_service.py†L10-L214】
- **Test generation:** FastAPI endpoint → analyze code (signatures/edge cases/complexity) → render pytest file → optional LLM tests appended → optional coverage run → response with test file path, code, coverage summary/report, and sources.【F:backend/app/main.py†L24-L32】【F:backend/app/services/testgen_service.py†L25-L165】
- **RAG index/search:** Repo loader walks files → chunker emits text + source metadata → embeddings computed (hash or SentenceTransformer) → FAISS index built and saved with embedder ID/dimension → queries run with matching encoder and return top chunks for prompts.【F:backend/app/rag/loaders/repo_loader.py†L1-L128】【F:backend/app/rag/index_builder.py†L1-L35】【F:backend/app/rag/vector_store.py†L1-L68】【F:backend/app/llm/client.py†L89-L142】
- **GitHub Action:** Workflow triggers on PR → runner resolves refs and diffs → calls review API → posts aggregated findings as a PR comment.【F:backend/app/integrations/github_workflow.py†L1-L183】

## 8) Usage pointers for demos
- Build the FAISS index, run the FastAPI app, and hit `/health`, `/review`, and `/generate-tests` with the sample payloads from `docs/SETUP.md` to verify the pipeline end-to-end. LLM/semantic behaviors require setting env vars and rebuilding the index as noted above.【F:docs/SETUP.md†L1-L154】

## 9) Known limitations and open directions
- Default mode is deterministic; semantic retrieval and LLM calls require your own credentials and models.【F:README.md†L6-L31】
- Multi-agent orchestration and automatic measurement of claimed PR/coverage improvements are not implemented in the backend; outcome metrics are documented but not measured at runtime.【F:README.md†L31-L44】【F:docs/TESTING_STATUS.md†L1-L35】
- Consider extending: richer prompt templating, self-hosted model runners, incremental indexing, deeper coverage gating, and inline PR annotations.
