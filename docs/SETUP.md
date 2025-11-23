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

All runtime packages (FastAPI, uvicorn, faiss-cpu, etc.) are declared in `backend/requirements.txt`. Installing from the repo root ensures relative paths resolve correctly.

## 4) Set environment variables (optional for mock mode)

Create a `.env` file in the repo root if you plan to swap in a real model later. The current code runs fully in mock mode, so none of these are strictly required.

```
LLM_API_KEY=<your-key-if-using-a-real-LLM>
MODEL_NAME=llama-3-8b
FAISS_INDEX_PATH=backend/app/rag/index
```

## 5) Build (or rebuild) the FAISS index

The RAG pipeline indexes repository Markdown/Python/text files **plus the last ~25 commits** (skipping binaries/huge artifacts). Embeddings are deterministic hash-based vectors with bigrams (no external model required), so rebuilding is fast and repeatable.

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

Responses come from deterministic heuristics (no external API keys required). If you pass `coverage_goal`, the service writes the code/tests to a temp dir and runs `pytest --cov`, returning the stdout/stderr summary alongside the generated test file.

## 8) Optional next steps

- Swap `backend/app/llm/client.py` to call a real model for both `generate_review` and `embed`.
- Tune `backend/app/llm/client.py` with a semantic encoder instead of hash vectors for stronger retrieval.
- Wire `backend/app/integrations/github_client.py` into your CI to post review feedback directly on PRs.
