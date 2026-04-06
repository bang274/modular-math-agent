"""
ReAct Agent Runner — GPT + math tools (sympy).
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.agent.react_agent import ReActAgent
from src.tools.math_tools import TOOLS
from src.telemetry.metrics import tracker


def _make_llm() -> OpenAIProvider:
    load_dotenv()
    return OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def main():
    print("=" * 60)
    print("  🤖  MATH ReAct AGENT (GPT + sympy tools)")
    print("=" * 60)

    llm = _make_llm()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=7)

    print(f"  Model: {llm.model_name}")
    print(f"  Tools: {', '.join(t['name'] for t in TOOLS)}")
    print("  Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        response = agent.run(user_input)
        print(f"\nAgent: {response}\n")

    summary = tracker.get_summary()
    print("\n📊 Session:", summary)


if __name__ == "__main__":
    main()
