# Flowchart: Where the Agent Adds Value

## Overview

This diagram shows the decision flow for both the Chatbot and the ReAct Agent when handling a math query, highlighting exactly where the Agent's tool-calling ability produces correct results that the Chatbot cannot.

## Flow Diagram

```mermaid
flowchart TD
    A["User asks: Solve x² - 5x + 6 = 0,<br/>then find derivative of x³ at each solution"]

    subgraph CHATBOT["💬 Chatbot Path"]
        B1["Receives full question"]
        B2["Attempts to solve in one shot<br/>using internal 'mental math'"]
        B3{"Correct?"}
        B4["❌ Often wrong:<br/>- Arithmetic errors<br/>- Forgets a solution<br/>- Wrong derivative value"]
        B5["✅ Sometimes lucky<br/>on simple problems"]
    end

    subgraph AGENT["🤖 ReAct Agent Path"]
        C1["Thought: I need to solve x² - 5x + 6 = 0 first"]
        C2["Action: solve_equation(x**2 - 5*x + 6 = 0)"]
        C3["Observation: x = 2, x = 3 ✅ exact"]
        C4["Thought: Now find derivative of x³"]
        C5["Action: compute_derivative(x**3, x)"]
        C6["Observation: 3*x² ✅ exact"]
        C7["Thought: Evaluate 3*x² at x=2 and x=3"]
        C8["Action: evaluate(3 * 2**2)"]
        C9["Observation: 12 ✅"]
        C10["Action: evaluate(3 * 3**2)"]
        C11["Observation: 27 ✅"]
        C12["Final Answer: At x=2: 12, At x=3: 27 ✅"]
    end

    A --> B1
    A --> C1
    B1 --> B2
    B2 --> B3
    B3 -->|No| B4
    B3 -->|Yes| B5

    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    C5 --> C6
    C6 --> C7
    C7 --> C8
    C8 --> C9
    C9 --> C10
    C10 --> C11
    C11 --> C12

    style B4 fill:#ff6b6b,color:#fff
    style B5 fill:#ffd93d,color:#333
    style C12 fill:#51cf66,color:#fff
    style CHATBOT fill:#fff5f5,stroke:#ff6b6b
    style AGENT fill:#f0fff4,stroke:#51cf66
```

## Where the Agent Wins

| Step | Chatbot | Agent | Why Agent Wins |
|------|---------|-------|----------------|
| **Equation solving** | Guesses roots, may miss one | `solve_equation` → exact symbolic solution | Sympy is provably correct |
| **Differentiation** | May misapply rules on complex expressions | `compute_derivative` → exact symbolic result | No human error possible |
| **Arithmetic** | Mental math errors on large numbers | `evaluate` → precise computation | Calculator vs brain |
| **Multi-step** | All errors compound | Each step verified independently | Error isolation |

## Where the Chatbot Wins (or ties)

| Scenario | Why |
|----------|-----|
| Simple factual math ("What is 2+2?") | LLM knows this from training data |
| Conceptual explanations ("What is a derivative?") | No computation needed |
| Word problems (understanding the question) | LLM's strength is language comprehension |

## Key Insight

> The agent doesn't replace the LLM's reasoning — it **augments** it with verified computation.
> The LLM still decides *what* to compute; the tools ensure *how* it's computed is correct.
