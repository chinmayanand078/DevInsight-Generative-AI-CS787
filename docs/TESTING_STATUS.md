# Testing & Metrics Status

This repository currently ships with deterministic, locally runnable checks and optional coverage summaries. There are **no automated performance/quality benchmarks (e.g., PR time reduction or accuracy metrics) baked into the codebase**. The project report mentions outcome numbers, but they are **not measured by the backend**.

## What runs in CI by default
- `python -m compileall backend` via `.github/workflows/devinsight.yml` to verify imports and syntax.

## How to run functional smoke tests locally
1) Build the FAISS index (deterministic hashing by default):
   ```bash
   uv pip install -r backend/requirements.txt
   python -m backend.app.rag.index_builder --repo . --out index.faiss
   ```
2) Start the API:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
3) Exercise endpoints with sample payloads (deterministic heuristics unless you set `LLM_PROVIDER=openai`):
   ```bash
   curl -X POST http://localhost:8000/review -H 'Content-Type: application/json' \
        -d '{"diff":"--- a/foo.py\n+++ b/foo.py\n@@\n+print(\"debug\")"}'

   curl -X POST http://localhost:8000/generate-tests -H 'Content-Type: application/json' \
        -d '{"file_path":"backend/app/main.py","coverage_goal":"basic"}'
   ```

## Coverage-supported test generation (optional)
- The `generate-tests` endpoint can run `pytest --cov` against the generated scaffold when you set `coverage_goal` (`smoke|basic|strong|max`). The response includes total coverage, missing-line hints, and whether the goal was met. See [docs/SETUP.md](SETUP.md) for the exact payload examples.

## What is still missing
- No automated benchmarks (latency, accuracy, cost) or measurement of reported improvements (e.g., PR time reduction, coverage lift).
- No regression test suite beyond the deterministic smoke flows above.
- No golden outputs for review/test generation; LLM-backed paths depend on your configured model and keys.

If you need repeatable evaluation, consider adding a fixtures directory with known inputs/diffs and expected findings, plus a small harness to compare deterministic outputs across revisions.
