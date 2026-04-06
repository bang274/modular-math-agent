"""
Chatbot Baseline — Plain GPT with NO tools.
This is the control group: it can only guess at math answers.
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class MathChatbot:
    """Simple chatbot that answers math questions using only the LLM's internal knowledge."""

    def __init__(self, llm: OpenAIProvider):
        self.llm = llm
        self.history = []

    def chat(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input})

        system_prompt = (
            "You are a math tutor. Answer the user's math question directly. "
            "Show your work step-by-step, then give the final answer. "
            "Be precise with calculations."
        )

        try:
            result = self.llm.generate(prompt=user_input, system_prompt=system_prompt)
        except Exception as e:
            logger.log_event("CHATBOT_ERROR", {"error": str(e)})
            return f"Error: {e}"

        content = result.get("content", "")
        tracker.track_request(
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        logger.log_event("CHATBOT_END", {"latency_ms": result.get("latency_ms", 0)})

        self.history.append({"input": user_input, "output": content})
        return content


def _make_llm() -> OpenAIProvider:
    load_dotenv()
    return OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def main():
    print("=" * 60)
    print("  💬  MATH CHATBOT (no tools — LLM only)")
    print("=" * 60)

    llm = _make_llm()
    bot = MathChatbot(llm)
    print(f"  Model: {llm.model_name}")
    print("  Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        response = bot.chat(user_input)
        print(f"\nChatbot: {response}\n")

    summary = tracker.get_summary()
    print("\n📊 Session:", summary)


if __name__ == "__main__":
    main()
