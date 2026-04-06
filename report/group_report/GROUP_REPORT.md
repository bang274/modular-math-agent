# Lab 3: Group Report

**Team Members:**
- [Student 1 Name]
- [Student 2 Name]
- [Student 3 Name]

---

## 1. Trace Analysis

### 1.1 The Chatbot Failure (Baseline)
*Describe a specific case where the `chatbot_baseline.py` failed. Include a snippet of the log.*

**Query used:** `[Insert query here]`

**Log Snippet / Result:**
```
[Insert output showing failure/hallucination here]
```

**Why it failed:**
[Explain why the basic LLM without tools could not solve this problem]

### 1.2 The Agent Success (ReAct)
*Describe how the Agent solved the exact same query using its tools.*

**Log Snippet / Result:**
```
[Insert output showing tool invocation and success here]
```

**Why it succeeded:**
[Explain the mechanism of Thought -> Action -> Observation that allowed this to work]

---

## 2. Quantitative Evaluation

| Metric | Basic Chatbot | ReAct Agent |
| :--- | :--- | :--- |
| **Success Rate (out of 4)** | | |
| **Average Latency (seconds)** | | |
| **Average Token Usage** | | |

*Note: Extract these numbers by running `compare_chatbot_vs_agent.py` and reviewing the latency and success of the output preview.*

---

## 3. Discussion & Insights
*What did the team learn about the trade-offs between a fast, simple chatbot versus a slower, but accurate, agentic system? Discuss latency, loop counts, and reliability.*
