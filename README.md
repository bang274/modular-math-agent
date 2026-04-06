# Modular Math ReAct Agent (6-Person Team)
## Advanced Calculus & Algebra Problem Solver

**Use Case**: A collaborative, high-reliability math assistant that solves complex calculus, algebra, and physics-related math using a tiered tool-calling architecture.

**Why this project?** Plain LLMs struggle with multi-step symbolic math and verification. This project implements a **Tiered Reliability Strategy** (Wolfram → Python → Search) to ensure correctness via external verification.

---

## 🏗️ Project Architecture (6-Person Team)

To prevent merge conflicts, the project is split into independent submodules:

| Person | Focus Area | Module | Key Responsibility |
|--------|------------|--------|--------------------|
| **1** | **Input/OCR** | `src/input/` | Image → Tesseract → Structured JSON queries. |
| **2** | **Tier 1 Tool** | `src/tools/wolfram_tool.py` | Symbolic math via Wolfram Alpha API. |
| **3** | **Tier 2 Tool** | `src/tools/python_tool.py` | Sandboxed Python with **3-attempt self-correction**. |
| **4** | **Tier 3 Tool** | `src/tools/search_tool.py` | Procedure lookup via Tavily Web Search. |
| **5** | **Agent/API** | `src/agent/` & `src/api/` | ReAct Engine logic & FastAPI SSE Streaming. |
| **6** | **Frontend** | `frontend/` | Real-time "Thought Visualization" UI (React/SSE). |

---

## 🛠️ Tiered Workflow

The agent follows a strict reliability hierarchy:
1.  **Tier 1: Wolfram Alpha** — First choice for exact symbolic results and verification.
2.  **Tier 2: Python Code** — Fallback for algorithmic steps. If code fails, the agent gets the error and **retries up to 3 times**.
3.  **Tier 3: Web Search** — Final fallback for lookups (e.g., "formula for volume of a sphere").

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) binary installed on your system.

### 2. Setup
```bash
cp .env.example .env          # Add OpenAI, Wolfram, and Tavily API keys
pip install -r requirements.txt
```

### 3. Run the Backend
```bash
uvicorn src.api.main:app --reload --port 8000
```
- **API Docs**: `http://localhost:8000/docs`
- **Stream Live**: `http://localhost:8000/solve/stream?query=solve x^2 + 5x + 6 = 0`

### 4. Tests
```bash
python3 -m pytest tests/ -v    # 37/37 tests passing (offline)
```

---

## 📁 Project Structure
```
day_03_chatbot_vs_agent/
├── src/
│   ├── api/            # FastAPI server & SSE endpoints
│   ├── agent/          # ReAct Logic (react_engine.py)
│   ├── input/          # OCR & Image Processing (ocr_engine.py)
│   ├── tools/          # Wolfram, Python (sandbox), and Search modules
│   ├── core/           # LLM Providers
│   └── telemetry/      # JSON Logging & Performance Metrics
├── frontend/           # index.html (SSE streaming prototype)
├── tests/              # 37 Unit tests for tools & engine
├── FLOWCHART.md        # Reasoning logic & tiered escalation
└── requirements.txt    # Modern dependencies (FastAPI, Tavily, etc.)
```

---

## ⚙️ Requirements for Grading
- **Manual Edits**: Team must tune the `system_prompt` in `src/agent/react_engine.py` and tool descriptions in `src/tools/`.
- **Comparison**: Use `compare.py` to run 5 identical cases against the plain `chatbot.py` baseline.
- **Reporting**: Individual and Group reports are located in the `report/` directory.

---

## 🔗 Repository
**GitHub**: [https://github.com/bang274/modular-math-agent](https://github.com/bang274/modular-math-agent)
