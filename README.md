# 🚀 DevInsight AI — Automated Code Review & Documentation Intelligence

DevInsight AI is an end-to-end automated **code intelligence system** that analyzes GitHub repositories and produces:
- 🔍 Deep code reviews
- 🧪 Auto-generated unit tests
- 🧠 RAG-based Q&A on repository code
- 🪪 Automatic GitHub Issues / PR comments

Every time a commit is pushed, DevInsight AI inspects the changes and delivers actionable insights — making development faster, cleaner, and more reliable.

---

## ✨ Features
| Capability | Description |
|-----------|-------------|
| 🔎 Code Review Engine | Detects code smells, bugs, anti-patterns & security flaws |
| 📚 Documentation Assistant | Explains complex modules & missing documentation |
| 🧪 Unit Test Generator | Creates missing test cases automatically |
| 🧠 RAG + FAISS | Vector search over repository for contextual intelligence |
| 🤖 GitHub CI Integration | Automatically runs on every push / PR |
| 🔗 GitHub API Automation | Posts review output directly to GitHub Issues / PRs |

---

## 📁 Project Structure
devinsight-ai/
│── backend/
│ ├── app.py # FastAPI application
│ ├── review_engine/ # Code review engine
│ ├── rag_engine/ # Retrieval augmented generation
│ ├── faiss_index/ # Vector index for embeddings
│ ├── test_generation/ # Unit test generator
│ ├── github_api/ # API module to post to GitHub
│── github-actions/
│ ├── devinsight.yml # GitHub Actions workflow CI
│── scripts/
│ ├── build_index.py # Indexing script
│── requirements.txt
│── README.md

---

## ⚙️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd devinsight-ai
2️⃣ Install dependencies
pip install -r requirements.txt
3️⃣ Add environment variables
Create a .env file:
OPENAI_API_KEY=<your_key>
GH_TOKEN=<github_personal_access_token>
REPO_URL=<repo_to_analyze>
PORT=8000
▶️ Run locally
uvicorn backend.app:app --host 0.0.0.0 --port 8000
Access API docs at:
http://localhost:8000/docs
🔄 GitHub Actions Integration
A workflow file must be added to:
.github/workflows/devinsight.yml
This triggers DevInsight AI automatically on every push or pull request, generating reviews and posting them to GitHub.
☁️ Deployment (Optional)
Supported platforms: Render, Railway, AWS, Azure
Expose this endpoint:
POST /analyze
🧠 Example Output
🔍 Code Review Summary
• 3 possible security flaws
• 6 refactor suggestions
• 2 unused variables
• Missing documentation in 4 functions

🧪 Unit Tests Generated
• tests/test_auth.py
• tests/test_utils.py
🛣 Roadmap
 Inline PR comments on exact lines
 Dashboard with repository trends
 Multi-repository analytics
🤝 Contributing
Contributions are welcome!
For large changes, open an Issue first for discussion.
