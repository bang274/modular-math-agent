"""
Cache Node — Redis cache check and store.

Person 4 owns this file.
Integrates with LangGraph as pre-solve (check) and post-solve (store) nodes.
"""

from typing import Any, Dict

from app.agent.state import AgentState
from app.cache.prompt_cache import PromptCache
from app.telemetry.logger import logger


async def cache_check_node(state: AgentState) -> Dict[str, Any]:
    """Check Redis cache for previously solved problems.

    For each extracted problem, compute cache key and look up.
    If found, mark as cache_hit and add to cache_hits dict.

    Returns:
        Updated state with cache_hits and modified problems.
    """
    problems = state.get("problems", [])

    if not problems:
        return {"cache_hits": {}, "cached_count": 0}

    cache = PromptCache()
    cache_hits: Dict[int, Dict[str, Any]] = {}
    updated_problems = []

    for problem in problems:
        try:
            cached_result = await cache.get(problem["content"])

            if cached_result:
                logger.info(f"[Cache] HIT for problem {problem['id']}")
                cache_hits[problem["id"]] = cached_result
                problem_copy = {**problem}
                problem_copy["cache_hit"] = True
                updated_problems.append(problem_copy)
            else:
                logger.debug(f"[Cache] MISS for problem {problem['id']}")
                updated_problems.append(problem)

        except Exception as e:
            logger.warning(f"[Cache] Error checking cache for problem {problem['id']}: {e}")
            updated_problems.append(problem)

    logger.info(f"[Cache] {len(cache_hits)}/{len(problems)} cache hits")

    return {
        "problems": updated_problems,
        "cache_hits": cache_hits,
        "cached_count": len(cache_hits),
    }


async def cache_store_node(state: AgentState) -> Dict[str, Any]:
    """Store solved results in Redis cache for future use.

    Only stores successfully solved problems that were not already cached.

    Returns:
        Unchanged state (side-effect only: writes to Redis).
    """
    problems = state.get("problems", [])
    final_results = state.get("final_results", [])

    if not final_results:
        return {}

    cache = PromptCache()
    stored = 0

    for result in final_results:
        pid = result.get("problem_id")
        # Don't re-cache already cached results
        if result.get("tool_trace", {}).get("cache_hit", False):
            continue

        # Only cache successful results with good confidence
        if result.get("error") or result.get("confidence", 0) < 0.5:
            continue

        # Find the original problem content
        problem = next((p for p in problems if p["id"] == pid), None)
        if not problem:
            continue

        try:
            cache_data = {
                "steps": result.get("steps", []),
                "final_answer": result.get("final_answer", ""),
                "confidence": result.get("confidence", 0.0),
            }
            cached_ok = await cache.set(problem["content"], cache_data)
            if cached_ok:
                stored += 1
            else:
                logger.warning(f"[Cache] Failed to store result for problem {pid}")
        except Exception as e:
            logger.warning(f"[Cache] Error storing result for problem {pid}: {e}")

    logger.info(f"[Cache] Stored {stored} new results in cache")
    return {}
