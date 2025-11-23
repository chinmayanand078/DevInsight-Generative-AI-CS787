# Remaining gaps vs. the original project claims

The repository now runs end-to-end in deterministic mode and optionally uses real LLMs/semantic embeddings when configured. The items below are the major gaps that still separate the codebase from the full vision stated in the project description.

1) **Multi-agent workflow is absent.**
   - The backend executes a single-pass review/test generation flow. There is no explicit coordinator that chains reviewer/critic/test agents or multi-step deliberation.

2) **Outcome metrics are not computed automatically.**
   - The backend does not measure or report PR-review time reduction or test-coverage lift. Any “35% faster reviews” or “30–40% coverage gains” must be computed externally.

3) **Real models remain opt-in.**
   - By default, review/test outputs are deterministic heuristics. LLM-backed findings require setting `LLM_PROVIDER=openai` plus an API key, and semantic retrieval requires `EMBEDDING_MODEL` followed by an index rebuild.

4) **Advanced ingest remains manual.**
   - RAG covers Markdown/Python/text/config files and recent Git history, but there is no automatic ingestion of large binary artifacts or design PDFs beyond what FAISS can safely handle.

5) **No production-hardening extras.**
   - Features like rate-limiting, request auth, horizontal scaling, streaming responses, and observability dashboards are not implemented; the backend is intended for controlled lab/demo use.

If you want to close these gaps:
- Add an orchestration layer that calls the reviewer, critic, and test agents in sequence, sharing context between steps.
- Instrument the workflow to log wall-clock review time and run coverage before/after to calculate gains automatically.
- Set `LLM_PROVIDER`/`LLM_API_KEY` and `EMBEDDING_MODEL`, rebuild the FAISS index, and update CI secrets so GitHub PR comments include real model output.
- Extend ingestion to new formats via `backend/app/rag/loaders/repo_loader.py` and guard large/binary inputs appropriately.
- Introduce auth, rate limits, structured logging, and monitoring before deploying beyond a demo environment.
