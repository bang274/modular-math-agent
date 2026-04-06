# 🧠 Math AI Agent Pipeline

AI-powered math problem solver with multi-agent pipeline. Upload text or images of math problems and get step-by-step LaTeX solutions.

## ✨ Features

- **Multi-input**: Text, image (OCR), or both
- **Smart routing**: Easy problems → LLM direct, Hard problems → Wolfram Alpha → Python Sandbox → Web Search
- **Parallel solving**: Multiple problems solved concurrently
- **Prompt caching**: Redis-based semantic caching for instant repeat answers
- **Real-time updates**: WebSocket streaming of solve progress
- **Step-by-step**: LaTeX-formatted solutions with confidence scores
- **Full observability**: LangSmith tracing for every pipeline run

## 🏗️ Architecture

```
User Upload → Extractor (LLM+Vision OCR) → JSON [{id, content}]
    → Cache Check (Redis)
    → Difficulty Classifier (LLM)
    ├── Easy Branch: LLM Direct Solve (+ Web Search if low confidence)
    └── Hard Branch: Wolfram Alpha → Python Sandbox (3 retries) → Web Search
    → Aggregator (LLM reasoning + LaTeX format)
    → Cache Store → Response
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| Frontend | React + TypeScript + Vite |
| Agent | LangChain + LangGraph |
| Tracing | LangSmith |
| LLM | Groq API (free models) |
| Math | Wolfram Alpha API |
| Search | Tavily Search API |
| Cache | Redis |
| Database | SQLite (aiosqlite) |

## 👥 Team (6 People)

| Person | Module | Key Files |
|--------|--------|-----------|
| **1** | Input & OCR | `app/agent/nodes/extractor.py`, `app/utils/image.py` |
| **2** | Tools | `app/tools/wolfram.py`, `app/tools/python_executor.py`, `app/tools/web_search.py` |
| **3** | Agent Graph | `app/agent/graph.py`, `app/agent/nodes/classifier.py`, `easy_solver.py`, `hard_solver.py` |
| **4** | Cache & DB | `app/cache/`, `app/db/`, `app/agent/nodes/cache_node.py` |
| **5** | API & Infra | `app/api/`, `app/main.py`, `app/config.py`, `docker-compose.yml` |
| **6** | Frontend | `frontend/src/` |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Redis (optional, app works without it)

### 1. Setup Backend
```bash
cp .env.example .env        # Fill in API keys
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Docker (all-in-one)
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

## 📡 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/solve` | Solve from text (JSON body) |
| `POST` | `/api/v1/upload` | Solve from text + image (multipart) |
| `GET` | `/api/v1/solve/{id}` | Get session results |
| `GET` | `/api/v1/history` | List past sessions |
| `GET` | `/api/v1/health` | Health check |
| `WS` | `/api/v1/ws/{id}` | Real-time solve progress |

## 🧪 Testing
```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm run test
```

## 🧩 Team Workflow (Git & Rebase)

To keep our 6-person team synced and our Git history clean, please follow these "Golden Rules":

### 1. Syncing with Main (The Rebase Workflow)
Instead of `git merge main`, always use **rebase** to keep a linear history.

```bash
# 1. Update your local main
git checkout main
git pull origin main

# 2. Go back to your feature branch
git checkout feature/your-module

# 3. Rebase your work on top of main
git rebase main

# 4. If conflicts occur (common in config.py):
#   - Edit the file to resolve conflict
#   - git add <conflicted-file>
#   - git rebase --continue

# 5. Push your clean history (since rebase changes history, force is needed)
git push origin feature/your-module --force-with-lease
```

### 2. 🚫 Never Commit These Files
We've updated `.gitignore`, but double-check your `git status` before committing. **NEVER** add:
- `backend/data/*.db*` (including `-shm` and `-wal` files)
- `.env` files (contains your private API keys)
- `node_modules` or `__pycache__`

### 3. Handling `app/config.py` Conflicts
Since multiple people add new settings to `config.py`, conflicts are likely. 
- **Rule**: Keep existing settings from `main` and simply **append** your new ones.
- If you see `<<<<<<< HEAD`, that's the current `main` branch. 
- If you see `>>>>>>> your-commit`, that's your new code. 
- Merge them cleanly; don't delete other people's model configurations!

### 4. Force Push Safety
Always use `--force-with-lease` instead of a plain `--force`. 
- **Reason**: It prevents you from accidentally overwriting a teammate's work if they pushed something to your branch while you were rebasing.
