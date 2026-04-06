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
