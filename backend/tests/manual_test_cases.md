# Manual Test Cases: Chatbot vs Agent

## Chatbot Wins (Simple Conversational or Meta)
1. "Hi there! What can you do?"
   - **Expectation**: Guard recognizes greeting. Returns a friendly introduction about being the Math Final Boss.
2. "Who created you?"
   - **Expectation**: Guard recognizes rejected/meta question. Responds politely that it only handles mathematics.

## Agent Wins (Complex Mathematics)
3. "Evaluate the integral: \int_0^1 e^{x^2} dx"
   - **Expectation**: Guard passes. Extractor extracts. Classifier routes to HardSolver. HardSolver uses Wolfram Alpha to compute the non-elementary integral (yields result with `erfi`). Aggregator formats nicely.
4. "Find the eigenvalues of the matrix [[1, 2], [3, 4]]"
   - **Expectation**: Guard passes. Extractor extracts. Classifier routes to HardSolver. HardSolver uses Python code or Wolfram Alpha to find eigenvalues. Aggregator formats nicely.

## Out of Scope / Sensitive
5. "Give me a recipe for chocolate chip cookies."
   - **Expectation**: Guard recognizes rejected topic. Responds that it is restricted to mathematics.
