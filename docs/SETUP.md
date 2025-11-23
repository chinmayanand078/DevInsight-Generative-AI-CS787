# DevInsight AI Backend — Step-by-Step Setup

These instructions assume a clean machine with Python 3.10+ and Git installed. Follow each step in order to avoid common environment errors.

## 1) Clone the repository

```bash
git clone https://github.com/chinmayanand078/DevInsight-Generative-AI-CS787.git
cd DevInsight-Generative-AI-CS787
```

## 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

Keeping dependencies isolated prevents system Python conflicts.

## 3) Install backend dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

All runtime packages (FastAPI, uvicorn, faiss-cpu, sentence-transformers, etc.) are declared in `backend/requirements.txt`. Installing from the repo root ensures relative paths resolve correctly.

## 4) Set environment variables (optional for mock mode)

Create a `.env` file in the repo root if you plan to swap in a real model later. The current code runs fully in mock mode, so none of these are strictly required.

```
LLM_PROVIDER=openai            # or leave unset for mock
LLM_API_KEY=<your-key-if-using-a-real-LLM>
LLM_API_BASE=https://api.openai.com/v1  # optional override
MODEL_NAME=gpt-4o-mini         # any chat/completions-capable model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # enables semantic retrieval (set before building the index)
FAISS_INDEX_PATH=backend/app/rag/index
```

### Enabling real ChatGPT responses (instead of deterministic mock)

If you want the `/review` endpoint to stream real findings from ChatGPT (or any OpenAI-compatible endpoint):

1. Obtain an API key and set it in `.env`:
   ```bash
   echo "LLM_PROVIDER=openai" >> .env
   echo "LLM_API_KEY=<your_openai_key>" >> .env
   echo "MODEL_NAME=gpt-4o-mini" >> .env   # adjust to gpt-4o or gpt-4o-mini per your quota
   ```
   If you are using a self-hosted/OpenAI-compatible gateway, also add `LLM_API_BASE=<your_base_url>`.

2. (Optional, recommended) Enable semantic retrieval by choosing an embedding model and rebuilding the FAISS index:
   ```bash
   echo "EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2" >> .env
   python -m backend.app.rag.index_builder
   ```

3. Restart the API so the new environment variables take effect:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

4. Send a review request. The response now merges heuristic findings with model-generated JSON findings from ChatGPT:
   ```bash
   curl -X POST http://localhost:8000/review \
        -H "Content-Type: application/json" \
        -d '{
              "pr_title": "Demo PR",
              "pr_number": 1,
              "repo_name": "example/repo",
              "diffs": [
                {"filename": "sample.py", "old_code": "", "new_code": "def add(a,b):return a+b"}
              ]
            }'
   ```

If the API key is missing or invalid, the service automatically falls back to deterministic mock responses so CI runs remain stable.

## 5) Build (or rebuild) the FAISS index

The RAG pipeline indexes repository Markdown/Python/text files **plus the last ~25 commits** (skipping binaries/huge artifacts). Embeddings are deterministic hash-based vectors with bigrams by default. If you set `EMBEDDING_MODEL`, a sentence-transformer encoder will be used instead for semantic retrieval. The FAISS metadata now records which embedder built the index; switching models without rebuilding the index will raise a clear error telling you to rebuild.

```bash
python -m backend.app.rag.index_builder
```

The command saves `embeddings.faiss` and `metadata.json` under `backend/app/rag/index/`.

## 6) Run the API locally

You can launch the FastAPI app with uvicorn from the repo root:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Alternatively, use the helper script (ensures the module path is set):

```bash
bash backend/uvicorn_run.sh
```

Visit the interactive docs at http://localhost:8000/docs while the server is running.

## 7) Exercise the endpoints

With the server running on port 8000:

- Health check

  ```bash
  curl http://localhost:8000/health
  ```

- PR review (runs deterministic lint + RAG)

  ```bash
  curl -X POST http://localhost:8000/review \
       -H "Content-Type: application/json" \
       -d '{
             "pr_title": "Demo PR",
             "pr_number": 1,
             "repo_name": "example/repo",
             "diffs": [
               {"filename": "sample.py", "old_code": "", "new_code": "def add(a,b):return a+b"}
             ]
           }'
  ```

- Unit-test generation (deterministic scaffold output + optional coverage run)

  ```bash
  curl -X POST http://localhost:8000/generate-tests \
       -H "Content-Type: application/json" \
       -d '{
             "file_path": "sample.py",
             "code": "def add(a, b):\n    return a + b",
             "coverage_goal": "basic"
           }'
  ```

Responses come from deterministic heuristics (no external API keys required). If you pass `coverage_goal`, the service writes the code/tests to a temp dir and runs `pytest --cov`, returning the stdout/stderr summary alongside the generated test file. If `LLM_PROVIDER` is set to `openai` with a valid key, the review endpoint will also surface structured suggestions from the configured model.

## 8) Optional next steps

- **Enable turnkey PR commenting.** The repo already contains `.github/workflows/devinsight.yml`. Leave it as-is to post deterministic review summaries on pull requests using the default `GITHUB_TOKEN` (permissions are declared in the workflow). If you want model-backed findings or semantic retrieval, add `OPENAI_API_KEY` and/or `EMBEDDING_MODEL` as repo secrets and let the workflow rerun to rebuild the FAISS index. The helper script fetches the PR base ref/sha and falls back to local history if the remote cannot be fetched (e.g., forked PRs).
- Fine-tune an LLM with `python training/finetune_llama3.py --dataset data.jsonl --model meta-llama/Meta-Llama-3-8B-Instruct` after installing `training/requirements.txt`.
- Use a semantic encoder by setting `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2` before rebuilding the FAISS index.
