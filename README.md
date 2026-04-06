# Lab 3 Submission: Chatbot vs ReAct Agent
## Math Problem Solver — Calculus & Algebra

**Use Case**: An assistant that solves calculus and algebra problems — derivatives, integrals, equation solving, and arithmetic evaluation.

**Why this use case?** LLMs frequently make arithmetic errors, hallucinate derivative/integral results, and cannot verify their own answers. A ReAct agent with `sympy`-powered tools computes **exact symbolic results** every time.

---

## 🚀 Quick Start

```bash
cp .env.example .env          # Add your OpenAI API key
pip install -r requirements.txt

python3 chatbot.py             # Run chatbot baseline
python3 agent.py               # Run ReAct agent
python3 compare.py             # Run 5 test cases on both, see comparison table
python3 -m pytest tests/ -v    # Run unit tests (no API key needed)
```

---

## 📁 Project Structure

```
day_03_chatbot_vs_agent/
├── chatbot.py              # Chatbot baseline — plain GPT, no tools
├── agent.py                # ReAct agent — GPT + math tools
├── compare.py              # Runs 5 identical test cases on both systems
├── src/
│   ├── core/               # LLM provider (OpenAI GPT)
│   ├── agent/              # ReAct agent engine (Thought→Action→Observation loop)
│   ├── tools/              # Math tools powered by sympy
│   └── telemetry/          # Structured JSON logging & cost tracking
├── tests/                  # Unit tests for tools & agent parsing
├── report/                 # Group & individual report templates
├── FLOWCHART.md            # Where the agent adds value vs chatbot
└── SCORING.md              # Grading rubric
```

---

## 🛠️ Tools

| Tool | What it does | Why the chatbot fails without it |
|------|-------------|----------------------------------|
| `solve_equation(equation)` | Solves algebraic equations symbolically | Chatbot guesses roots, often wrong |
| `compute_derivative(expr, var)` | Exact symbolic differentiation | Chatbot misapplies chain/product rule |
| `compute_integral(expr, var)` | Exact symbolic integration | Chatbot forgets constants, makes sign errors |
| `evaluate(expr)` | Precise arithmetic evaluation | Chatbot does mental math, gets it wrong |

---

## ⚙️ Key Files to Manually Edit

> **Instructor requirement**: Team must manually edit system prompt, tool descriptions, and stopping conditions.

- **System Prompt**: `src/agent/react_agent.py` → `get_system_prompt()` method
- **Tool Descriptions**: `src/tools/math_tools.py` → `TOOLS` list
- **Stopping Conditions**: `src/agent/react_agent.py` → `max_steps` and Final Answer detection in `run()`
