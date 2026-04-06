"""
Comparison Runner — Runs 5 identical test cases on both Chatbot and Agent,
then prints a side-by-side comparison table.

=== TEAM: Design your 5 test cases below ===
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.agent.react_agent import ReActAgent
from src.tools.math_tools import TOOLS
from src.telemetry.metrics import PerformanceTracker


# ─── Test Cases ──────────────────────────────────────────────────────────────
# === TEAM: Replace these with your own 5 test cases ===

TEST_CASES = [
    {
        "id": 1,
        "query": "What is the derivative of x^3 + 5*x^2 - 3*x + 7?",
        "expected": "3*x**2 + 10*x - 3",
        "category": "calculus - derivative",
    },
    {
        "id": 2,
        "query": "Solve the equation 2*x + 5 = 13",
        "expected": "x = 4",
        "category": "algebra - linear",
    },
    {
        "id": 3,
        "query": "What is the integral of 6*x^2 + 4*x - 1?",
        "expected": "2*x**3 + 2*x**2 - x + C",
        "category": "calculus - integral",
    },
    {
        "id": 4,
        "query": "Calculate: (17 * 23) + (144 / 12) - sqrt(256)",
        "expected": "387",
        "category": "arithmetic",
    },
    {
        "id": 5,
        "query": "Solve x^2 - 5*x + 6 = 0, then find the derivative of x^3 at each solution.",
        "expected": "At x=2: 12, At x=3: 27",
        "category": "multi-step",
    },
]


# ─── Chatbot (no tools) ─────────────────────────────────────────────────────

class SimpleChatbot:
    def __init__(self, llm: OpenAIProvider):
        self.llm = llm
        self.tracker = PerformanceTracker()

    def ask(self, question: str) -> str:
        system = (
            "You are a math tutor. Answer the math question directly. "
            "Show work step-by-step, then give the final numerical answer."
        )
        result = self.llm.generate(prompt=question, system_prompt=system)
        self.tracker.track_request(
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        return result.get("content", "")


# ─── Runner ──────────────────────────────────────────────────────────────────

def run_comparison():
    load_dotenv()
    llm = OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    chatbot = SimpleChatbot(llm)

    agent_tracker = PerformanceTracker()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=7)

    results = []

    print("=" * 80)
    print("  🧪  COMPARISON: Chatbot vs ReAct Agent — 5 Test Cases")
    print("=" * 80)

    for tc in TEST_CASES:
        print(f"\n{'─' * 80}")
        print(f"  Test {tc['id']} [{tc['category']}]: {tc['query']}")
        print(f"  Expected: {tc['expected']}")
        print(f"{'─' * 80}")

        # Chatbot
        print("\n  💬 Chatbot answering...")
        chatbot_answer = chatbot.ask(tc["query"])
        chatbot_short = chatbot_answer[:150].replace("\n", " ")

        # Agent
        print("  🤖 Agent answering...")
        agent_answer = agent.run(tc["query"])
        agent_short = agent_answer[:150].replace("\n", " ")

        # Check if expected answer is in the response
        expected_lower = tc["expected"].lower()
        chatbot_correct = expected_lower in chatbot_answer.lower()
        agent_correct = expected_lower in agent_answer.lower()

        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "query": tc["query"][:50],
            "expected": tc["expected"],
            "chatbot_preview": chatbot_short,
            "agent_preview": agent_short,
            "chatbot_correct": chatbot_correct,
            "agent_correct": agent_correct,
        })

        print(f"\n  Chatbot: {chatbot_short}...")
        print(f"  Agent:   {agent_short}...")
        print(f"  Chatbot correct: {'✅' if chatbot_correct else '❌'}  |  Agent correct: {'✅' if agent_correct else '❌'}")

    # ── Summary Table ─────────────────────────────────────────────────────
    print("\n\n" + "=" * 80)
    print("  📊  RESULTS SUMMARY")
    print("=" * 80)
    print(f"\n  {'#':<4} {'Category':<22} {'Expected':<25} {'Chatbot':<10} {'Agent':<10} {'Winner':<10}")
    print(f"  {'─'*4} {'─'*22} {'─'*25} {'─'*10} {'─'*10} {'─'*10}")

    chatbot_wins = 0
    agent_wins = 0
    draws = 0

    for r in results:
        cb = "✅" if r["chatbot_correct"] else "❌"
        ag = "✅" if r["agent_correct"] else "❌"
        if r["chatbot_correct"] and not r["agent_correct"]:
            winner = "Chatbot"
            chatbot_wins += 1
        elif r["agent_correct"] and not r["chatbot_correct"]:
            winner = "Agent"
            agent_wins += 1
        elif r["agent_correct"] and r["chatbot_correct"]:
            winner = "Draw"
            draws += 1
        else:
            winner = "Neither"

        print(f"  {r['id']:<4} {r['category']:<22} {r['expected']:<25} {cb:<10} {ag:<10} {winner:<10}")

    print(f"\n  Chatbot wins: {chatbot_wins}  |  Agent wins: {agent_wins}  |  Draws: {draws}")

    # ── Performance ───────────────────────────────────────────────────────
    cb_summary = chatbot.tracker.get_summary()
    # Agent metrics are in the global tracker
    print(f"\n  Chatbot — Requests: {cb_summary.get('total_requests')}, "
          f"Tokens: {cb_summary.get('total_tokens')}, "
          f"Cost: ${cb_summary.get('total_cost_usd', 0):.4f}")

    print()


if __name__ == "__main__":
    run_comparison()
