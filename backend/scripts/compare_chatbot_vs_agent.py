"""
Master test script to compare Chatbot vs ReAct Agent.
"""
import asyncio
import time
import sys
import os
import uuid
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.provider import get_default_llm
from app.agent.graph import run_agent_pipeline

TEST_CASES = [
    "I want to make an alloy that is 40% silver and 60% gold. I have 10 grams of silver. How much gold do I need?",
    "Calculate the integral of x^2 * sin(x) dx.",
    "A train leaves city A at 60mph. 2 hours later another train leaves city A on a parallel track at 80mph. How long until the second train catches the first?",
    "Find the roots of the polynomial x^5 - 5x^4 + 10x^3 - 10x^2 + 5x - 1 = 0.",
]

async def run_chatbot(prompt: str):
    llm = get_default_llm()
    start = time.time()
    try:
        response = await llm.ainvoke(prompt)
        content = response.content
    except Exception as e:
        content = f"Error: {e}"
    latency = time.time() - start
    return content, latency

async def run_agent(prompt: str):
    session_id = str(uuid.uuid4())
    start = time.time()
    try:
        state = await run_agent_pipeline(text=prompt, session_id=session_id)
        if "final_results" in state and len(state["final_results"]) > 0:
            content = state["final_results"][0].get("final_answer", "No answer found")
        else:
            content = "No final result."
    except Exception as e:
        content = f"Error: {e}"
    latency = time.time() - start
    return content, latency

async def main():
    print("=" * 60)
    print("  🧪  DEMO MODE — Chatbot vs ReAct Agent")
    print("=" * 60)

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'─' * 60}")
        print(f"  Test Case {i}: {test}")
        print(f"{'─' * 60}")
        
        print("\n  [1] Running Baseline Chatbot...")
        cb_res, cb_lat = await run_chatbot(test)
        print(f"  Latency: {cb_lat:.2f}s")
        print(f"  Answer preview: {cb_res[:200]}...")

        print("\n  [2] Running ReAct Math Agent...")
        ag_res, ag_lat = await run_agent(test)
        print(f"  Latency: {ag_lat:.2f}s")
        print(f"  Answer preview: {ag_res[:200]}...")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
