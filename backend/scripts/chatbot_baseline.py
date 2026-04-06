"""
Chatbot Baseline — A simple LLM wrapper with NO tool access.
This serves as the control group to compare against the ReAct Agent.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Use httpx so we don't depend on external packages
import httpx

class Chatbot:
    """
    Simple chatbot that directly forwards user queries to the LLM via GitHub Models API.
    No tools, no reasoning loop — just prompt in, answer out.
    """

    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set. Please set it in .env")

        self.history = []

    def chat(self, user_input: str) -> str:
        system_prompt = (
            "You are a helpful assistant. Answer the user's question directly "
            "and concisely. If you don't know something, say so."
        )

        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=data)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            content = f"Error: {e}"

        self.history.append({"input": user_input, "output": content})
        return content


# ─── Standalone runner ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  💬  CHATBOT BASELINE (GitHub Models, no tools, no reasoning)")
    print("=" * 60)

    try:
        bot = Chatbot()
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        sys.exit(1)

    print("\nUsing provider: GitHub Models (gpt-4o)")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
            
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        start_t = time.time()
        response = bot.chat(user_input)
        latency = (time.time() - start_t) * 1000
        print(f"\nChatbot: {response}")
        print(f"\n[Latency: {latency:.2f}ms]\n")


if __name__ == "__main__":
    main()
