import asyncio
import httpx
import json
import os
import sys

# Add backend to path to import schemas if needed
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

BASE_URL = "http://localhost:8000/api/v1"

async def test_full_pipeline():
    """Verify that the model-specialized pipeline works as expected."""
    print("🚀 Starting System Workflow Test...")

    # Combine an easy and a hard problem
    problems = (
        "1. Solve for x: 2x + 10 = 20\n"
        "2. Find the integral of cos(x)^2 from 0 to pi"
    )

    request_data = {
        "text": problems
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"📡 Sending request to {BASE_URL}/solve...")
        try:
            response = await client.post(f"{BASE_URL}/solve", json=request_data)
            response.raise_for_status()
            data = response.json()
            
            print("\n✅ API Response Received:")
            print(f"Session ID: {data['session_id']}")
            print(f"Status: {data['status']}")
            print(f"Total Problems: {data['total_problems']}")
            print(f"Latency: {data['total_latency_ms']}ms")

            for result in data['results']:
                pid = result['problem_id']
                diff = result['difficulty']
                route = result['tool_trace']['route']
                answer = result['final_answer']
                
                print(f"\n--- Problem {pid} ({diff.upper()}) ---")
                print(f"Content: {result['original'][:50]}...")
                print(f"Route taken: {route}")
                print(f"Tools used: {result['tool_trace']['tools_used']}")
                print(f"Final Answer: {answer}")
                
                # Verify logic
                if pid == 1:
                    print("🔍 Check Easy Logic: should use llm_direct" if route == 'llm_direct' else "⚠️ Unexpected route for Easy")
                if pid == 2:
                    print("🔍 Check Hard Logic: should use wolfram or python_sandbox" if route in ['wolfram', 'python_sandbox'] else "⚠️ Unexpected route for Hard")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e}")
            if e.response:
                print(f"Response Detail: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    asyncio.run(test_full_pipeline())
