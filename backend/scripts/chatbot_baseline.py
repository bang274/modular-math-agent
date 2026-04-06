"""
Chatbot Baseline script.
This represents the naive approach without tools.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.provider import get_default_llm

async def main():
    if len(sys.argv) < 2:
        question = "Solve x^2 - 5x + 6 = 0"
    else:
        question = sys.argv[1]
    
    print(f"Chatbot Question: {question}")
    llm = get_default_llm()
    response = await llm.ainvoke(question)
    print(f"Answer:\n{response.content}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
