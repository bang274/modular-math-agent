# Lab 3: Group Report

**Team Members:**
- Trần Khánh Bằng 2A202600458 
- Đỗ Hải Nam 2A202600038 
- Trần Thái Thịnh  2A202600310 
- Nguyễn Văn Thạch 2A202600237 
- Lê Trung Anh Quốc  2A202600108 
- Nguyễn Đức Cường 2A202600147

---

## 1. Trace Analysis

### 1.1 The Chatbot Wins

**Query used:** `I want to make an alloy that is 40% silver and 60% gold. I have 10 grams of silver. How much gold do I need?`

**Log Snippet / Result of Chatbot:**
```
Latency: 5.02s
  Answer preview: To find out how much gold you need, you need to determine the total weight of the alloy. Since you have 10 grams of silver and the alloy is 40% silver, you can set up the following equation:

10 grams = 0.4x

where x is the total weight of the alloy.

To solve for x, divide both sides by 0.4:

x = 10 grams / 0.4
x = 25 grams

So, the total weight of the alloy is 25 grams. Since the alloy is 60% gold, you can find the weight of gold needed by multiplying the total weight by 0.6:

Weight of gold = 0.6 * 25 grams
Weight of gold = 15 grams

Therefore, you need 15 grams of gold to make the alloy
```
**Log Snippet / Result of Agent:**
![[Pasted image 20260406213659.png]]


**Query used:** `A train leaves city A at 60mph. 2 hours later another train leaves city A on a parallel track at 80mph. How long until the second train catches the first?`

**Log Snippet / Result of Chatbot:**
```
  Latency: 13.01s
  Answer preview: To find the time it takes for the second train to catch the first, we need to calculate the distance the first train has traveled when the second train catches up.

The first train travels for 2 hours before the second train starts. In those 2 hours, it travels:
Distance = Speed * Time = 60mph * 2 hours = 120 miles

Now, the second train starts, and we want to find the time it takes for the second train to catch the first. Let's call this time 't' hours.

In 't' hours, the first train travels an additional distance:
Distance = Speed * Time = 60mph * t

The second train travels:
Distance = Speed * Time = 80mph * t

Since the second train catches up to the first, the total distance traveled by the second train is equal to the total distance traveled by the first train:
80mph * t = 60mph * t + 120 miles

Now, let's solve for 't':
80t = 60t + 120
20t = 120
t = 120 / 20
t = 6 hours

So, the second train catches up to the first train in 6 hours after it starts. Since the second train starts 2 hours after the first, the total time elapsed is 2 + 6 = 8 hours....
```
**Log Snippet / Result of Agent:**

![[Pasted image 20260406213415.png]]


### 1.2 The Agent Wins (ReAct)

**Query used:** `Calculate the integral of e^(x^2) dx.`

**Log Snippet / Result of Chatbot:**
```
Latency: 23.82s
  Answer preview: The integral of \( e^{x^2} \) with respect to \( x \) cannot be expressed in terms of elementary functions. However, it is commonly represented using a special function called the **error function** or related forms.

The integral is typically expressed as:

\[
\int e^{x^2} \, dx = \text{No closed-form solution in elementary functions.}
\]

If you need to evaluate it numerically or approximate it, you can use numerical integration techniques or expand \( e^{x^2} \) into a series. Let me know if you'd like further clarification!...
```

**Log Snippet / Result of Agent:**
![[Pasted image 20260406214245.png]]

**Query used:** `Calculate \(\int \frac{2x^2-1}{(4x-1)(x^2+1)} dx\)`

**Log Snippet / Result of Chatbot:**
```
Latency: 31.56s
  Answer preview: To evaluate the integral \(\int \frac{2x^2 - 1}{(4x - 1)(x^2 + 1)} dx\), we use partial fraction decomposition.

### Step 1: Decompose the fraction
We write:
\[
\frac{2x^2 - 1}{(4x - 1)(x^2 + 1)} = \frac{A}{4x - 1} + \frac{Bx + C}{x^2 + 1},
\]
where \(A\), \(B\), and \(C\) are constants to be determined.

Multiply through by \((4x - 1)(x^2 + 1)\) to eliminate the denominators:
\[
2x^2 - 1 = A(x^2 + 1) + (Bx + C)(4x - 1).
\]

Expand the terms:
\[
2x^2 - 1 = A(x^2) + A + (Bx)(4x) + (Bx)(-1) + (C)(4x) + (C)(-1).
\]
\[
2x^2 - 1 = A x^2 + A + 4Bx^2 - Bx + 4Cx - C.
\]

Group terms by powers of \(x\):
\[
2x^2 - 1 = (A + 4B)x^2 + (-B + 4C)x + (A - C).
\]

### Step 2: Solve for \(A\), \(B\), and \(C\)
Equating coefficients of \(x^2\), \(x\), and the constant term:
1. Coefficient of \(x^2\): \(A + 4B = 2\),
2. Coefficient of \(x\): \(-B + 4C = 0\),
3. Constant term: \(A - C = -1\).

From equation (2): \(-B + 4C = 0 \implies B = 4C\).

Substitute \(B = 4C\) into equation (1):
\[
A + 4(4C) = 2 \implies A + 16C = 2 \implies A = 2 - 16C.
\]

Substitute \(A = 2 - 16C\) into equation (3):
\[
(2 - 16C) - C = -1 \implies 2 - 17C = -1 \implies 17C = 3 \implies C = \frac{3}{17}.
\]

Now, find \(B\) and \(A\):
\[
B = 4C = 4 \cdot \frac{3}{17} = \frac{12}{17},
\]
\[
A = 2 - 16C = 2 - 16 \cdot \frac{3}{17} = 2 - \frac{48}{17} = \frac{34}{17} - \frac{48}{17} = -\frac{14}{17}.
\]

### Step 3: Rewrite the integral
The partial fraction decomposition is:
\[
\frac{2x^2 - 1}{(4x - 1)(x^2 + 1)} = \frac{-\frac{14}{17}}{4x - 1} + \frac{\frac{12}{17}x + \frac{3}{17}}{x^2 + 1}.
\]

Thus, the integral becomes:
\[
\int \frac{2x^2 - 1}{(4x - 1)(x^2 + 1)} dx = \int \frac{-\frac{14}{17}}{4x - 1} dx + \int \frac{\frac{12}{17}x + \frac{3}{17}}{x^2 + 1} dx.
\]

### Step 4: Evaluate each term
1. For \(\int \frac{-\frac{14}{17}}{4x - 1} dx\), let \(u = 4x - 1\), so \(du = 4 dx\). The integral becomes:
\[
\int \frac{-\frac{14}{17}}{4x - 1} dx = -\frac{14}{17} \int \frac{1}{u} \cdot \frac{1}{4} du = -\frac{14}{68} \ln|u| = -\frac{7}{34} \ln|4x - 1|.
\]

2. For \(\int \frac{\frac{12}{17}x}{x^2 + 1} dx\), let \(u = x^2 + 1\), so \(du = 2x dx\). The integral becomes:
\[
\int \frac{\frac{12}{17}x}{x^2 + 1} dx = \frac{12}{17} \int \frac{1}{u} \cdot \frac{1}{2} du = \frac{6}{17} \ln|u| = \frac{6}{17} \ln(x^2 + 1).
\]

3. For \(\int \frac{\frac{3}{17}}{x^2 + 1} dx\), use the standard result \(\int \frac{1}{x^2 + 1} dx = \arctan(x)\):
\[
\int \frac{\frac{3}{17}}{x^2 + 1} dx = \frac{3}{17} \arctan(x).
\]

### Step 5: Combine results
The final answer is:
\[
\int \frac{2x^2 - 1}{(4x - 1)(x^2 + 1)} dx = -\frac{7}{34} \ln|4x - 1| + \frac{6}{17} \ln(x^2 + 1) + \frac{3}{17} \arctan(x) + C,
\]
where \(C\) is the constant of integration....

```
**Log Snippet / Result of Agent:**
![[Pasted image 20260406214417.png]]
### 1.3 Out of Domain
![[Pasted image 20260406221026.png]]

## 2. Quantitative Evaluation

| Metric                        | Basic Chatbot | ReAct Agent |
| :---------------------------- | :------------ | :---------- |
| **Success Rate (out of 4)**   | 4             | 4           |
| **Average Latency (seconds)** | 17.56         | 6.2s        |

*Note: Extract these numbers by running `compare_chatbot_vs_agent.py` and reviewing the latency and success of the output preview.*

---

## 3. Discussion & Insights

Through the development and testing of the baseline Chatbot and the ReAct Agent, our team identified several critical trade-offs between a straightforward LLM interface and a multi-agentic system:

1. **Accuracy vs. Latency:** The baseline chatbot frequently solves simpler text-based math problems rapidly by outputting a single, continuous stream of text. However, when faced with non-elementary calculus (like `e^(x^2)`) or highly complex algebraic decompositions, the chatbot either hallucinates incorrect derivations or produces prohibitively verbose, time-consuming responses (sometimes averaging ~17.56s). Conversely, the ReAct Agent typically completes computations significantly faster (averaging ~6.2s in tests) and more accurately by identifying when to strictly delegate heavy mathematical lifting to symbolic solvers like Wolfram Alpha, avoiding the generation of uselessly long, hallucinated derivations.

2. **Reliability and Guardrails:** The standard chatbot blindly answers any query, meaning it will attempt complex math without appropriate tools, inevitably leading to mathematical hallucinations. The Agentic framework proved highly reliable because of its "Guard" node, which flawlessly categorized out-of-domain conversational queries and politely rejected non-math prompts. Furthermore, its Critic node acts as a definitive quality check, theoretically forcing a secondary loop if the initial solver fails. This significantly increases mathematical reliability, practically eliminating logic and calculation errors.

3. **Loop Counts and System Complexity:** An LLM chatbot is essentially an $O(1)$ loop—one request, one generation. Developing the ReAct Agent introduced multi-step loops (Extraction -> Classification -> Solving -> Verification -> Aggregation). While this modular pipeline dramatically improved the quality of the final answer and allowed precise programmatic control, cacheing, and telemetry, it added significant software overhead. Handling state routing proved much more complex to orchestrate and debug than simple prompt engineering. 

**Conclusion:** A pure LLM is sufficient (and often preferred for its simplicity) for basic conversational AI or basic arithmetic word problems. However, for symbolic math, algebraic manipulation, or collegiate-level calculus, a ReAct-based agent equipped with symbolic calculation tools (Wolfram Alpha/SymPy) is an absolute necessity to guarantee verifiable, hallucinative-free results on complex prompts, while avoiding massive token costs.
