import asyncio
import httpx
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

async def test_parallel_solve():
    """Verify that multiple problems are solved in parallel."""
    print("🚀 Starting Parallelism Test...")

    # Generate 5 diverse problems
    problems = [
        "1. Solve 2x + 5 = 15",
        "2. Solve x^2 - 4 = 0",
        "3. Find the derivative of x^3",
        "4. Calculate 123 * 456",
        "5. What is the square root of 144?"
    ]

    request_data = {
        "text": "\n".join(problems)
    }

    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"📡 Sending 5 problems in one request...")
        try:
            response = await client.post(f"{BASE_URL}/solve", json=request_data)
            response.raise_for_status()
            data = response.json()
            
            end_time = time.time()
            total_duration = (end_time - start_time) * 1000
            
            print(f"\n✅ Parallel Results Received ({total_duration:.2f}ms):")
            print(f"Solved: {data['solved_count']}/{data['total_problems']}")
            
            # If solved in parallel, total_duration should be much less than 5 * single_problem_duration
            # (assuming each problem takes ~1-2s, total should be ~2-3s, not 10s)
            print(f"Server-reported total latency: {data['total_latency_ms']}ms")
            
            if data['total_problems'] > 0:
                avg_per_problem = data['total_latency_ms'] / data['total_problems']
                print(f"Average time per problem: {avg_per_problem:.2f}ms")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    asyncio.run(test_parallel_solve())
