"""
Aggregator Node — Result synthesis and LaTeX formatting.

Person 3 owns this file.
Collects all tool results and produces final formatted solutions.
"""

import time
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_aggregator_llm

from app.llm.prompts import AGGREGATOR_SYSTEM_PROMPT
from app.llm.parser import parse_json_response
from app.telemetry.logger import logger


async def aggregator_node(state: AgentState) -> Dict[str, Any]:
    """Aggregate and format all solving results.

    For each problem:
    1. Collect tool outputs from results dict
    2. Send to aggregator LLM for reasoning + LaTeX formatting
    3. Produce final step-by-step solution

    Returns:
        Updated state with final_results list.
    """
    problems = state.get("problems", [])
    results = state.get("results", {})
    cache_hits = state.get("cache_hits", {})
    ws_messages = list(state.get("ws_messages", []))

    llm = get_aggregator_llm()

    final_results: List[Dict[str, Any]] = []
    total_latency = 0

    for problem in problems:
        pid = problem["id"]

        # Check if cached
        if pid in cache_hits:
            cached = cache_hits[pid]
            final_results.append({
                "problem_id": pid,
                "original": problem["content"],
                "difficulty": problem.get("difficulty", "unknown"),
                **cached,
                "tool_trace": {
                    "route": "cached",
                    "tools_used": [],
                    "attempts": 0,
                    "cache_hit": True,
                    "latency_ms": 0,
                    "errors": [],
                },
            })
            continue

        # Get solving result
        result = results.get(pid)
        if not result:
            final_results.append({
                "problem_id": pid,
                "original": problem["content"],
                "difficulty": problem.get("difficulty", "unknown"),
                "steps": [],
                "final_answer": "",
                "confidence": 0.0,
                "error": "No result produced",
                "tool_trace": {
                    "route": "failed",
                    "tools_used": [],
                    "attempts": 0,
                    "cache_hit": False,
                    "latency_ms": 0,
                    "errors": ["No solving result"],
                },
            })
            continue

        # Use LLM to aggregate and format
        try:
            start = time.time()

            history = state.get("chat_history", [])[-5:]
            history_str = json.dumps(history, indent=2) if history else "None"

            aggregate_prompt = (
                f"Problem: {problem['content']}\n\n"
                f"CHAT HISTORY:\n{history_str}\n\n"
                f"Solving route: {result.get('solve_route', 'unknown')}\n"
                f"Tools used: {result.get('tools_used', [])}\n\n"
            )
# ... rest of tool output logic ...
            # Include tool outputs
            tool_outputs = result.get("tool_outputs", {})
            if tool_outputs:
                for tool_name, output in tool_outputs.items():
                    aggregate_prompt += f"--- {tool_name} output ---\n{output}\n\n"
            elif result.get("final_answer"):
                aggregate_prompt += f"Answer: {result['final_answer']}\n\n"

            if result.get("steps"):
                aggregate_prompt += f"Steps: {result['steps']}\n\n"

            if result.get("search_context"):
                aggregate_prompt += f"Search context: {result['search_context']}\n\n"

            aggregate_prompt += (
                "Please synthesize a well-formatted step-by-step solution with LaTeX."
            )

            messages = [
                SystemMessage(content=AGGREGATOR_SYSTEM_PROMPT),
                HumanMessage(content=aggregate_prompt),
            ]


            response = await llm.ainvoke(messages)
            parsed = parse_json_response(response.content)

            agg_latency = int((time.time() - start) * 1000)

            if parsed:
                steps = parsed.get("steps", [])
                final_answer = parsed.get("final_answer", result.get("final_answer", ""))
                confidence = parsed.get("confidence", result.get("confidence", 0.5))
            else:
                # Fallback: use raw result
                steps = result.get("steps", [])
                final_answer = result.get("final_answer", "")
                confidence = result.get("confidence", 0.5)

            solve_latency = result.get("latency_ms", 0)
            total_latency += solve_latency + agg_latency

            # Collect any images from tool results
            images = []
            if result.get("tool_outputs_raw"):
                # If we have tool outputs, extract images from them
                for t_res in result["tool_outputs_raw"].values():
                    if hasattr(t_res, "images") and t_res.images:
                        images.extend(t_res.images)
            elif result.get("images"):
                images.extend(result["images"])

            final_results.append({
                "problem_id": pid,
                "original": problem["content"],
                "difficulty": problem.get("difficulty", "unknown"),
                "steps": steps,
                "final_answer": final_answer,
                "confidence": confidence,
                "images": images,
                "error": result.get("error"),
                "tool_trace": {
                    "route": result.get("solve_route", "unknown"),
                    "tools_used": result.get("tools_used", []),
                    "attempts": len(result.get("errors", [])) + 1,
                    "cache_hit": False,
                    "latency_ms": solve_latency + agg_latency,
                    "errors": result.get("errors", []),
                },
            })


        except Exception as e:
            logger.error(f"[Aggregator] Error aggregating problem {pid}: {e}")
            final_results.append({
                "problem_id": pid,
                "original": problem["content"],
                "difficulty": problem.get("difficulty", "unknown"),
                "steps": [],
                "final_answer": result.get("final_answer", ""),
                "confidence": result.get("confidence", 0.0),
                "error": str(e),
                "tool_trace": {
                    "route": result.get("solve_route", "unknown"),
                    "tools_used": result.get("tools_used", []),
                    "attempts": 1,
                    "cache_hit": False,
                    "latency_ms": result.get("latency_ms", 0),
                    "errors": [str(e)],
                },
            })

    # Determine overall status
    solved_count = sum(1 for r in final_results if not r.get("error"))
    failed_count = sum(1 for r in final_results if r.get("error"))
    cached_count = sum(1 for r in final_results if r.get("tool_trace", {}).get("cache_hit"))

    if failed_count == 0:
        status = "completed"
    elif solved_count > 0:
        status = "partial"
    else:
        status = "failed"

    ws_messages.append({
        "type": "all_complete",
        "data": {
            "status": status,
            "total": len(final_results),
            "solved": solved_count,
            "failed": failed_count,
            "cached": cached_count,
        },
    })

    logger.info(
        f"[Aggregator] Done: {solved_count} solved, {failed_count} failed, "
        f"{cached_count} cached, {total_latency}ms total"
    )

    return {
        "final_results": final_results,
        "status": status,
        "total_latency_ms": total_latency,
        "cached_count": cached_count,
        "ws_messages": ws_messages,
    }
