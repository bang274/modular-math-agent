"""
Easy Solver Node — Direct LLM solving for simple problems.

Person 3 owns this file.
Handles: basic arithmetic, simple algebra, theory questions.
Falls back to web search if LLM confidence is low.
"""

import time
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_reasoning_llm
from app.llm.prompts import EASY_SOLVER_SYSTEM_PROMPT
from app.llm.parser import parse_json_response
from app.tools.web_search import WebSearchTool
from app.telemetry.logger import logger


async def easy_solver_node(state: AgentState) -> Dict[str, Any]:
    """Solve easy problems using direct LLM reasoning.

    Flow:
    1. LLM attempts to solve directly
    2. If confidence < 0.7 or needs_search=True → call web search
    3. Combine results and return

    Returns:
        Updated state with results for easy problems.
    """
    easy_ids = state.get("easy_problems", [])
    problems = state.get("problems", [])
    results = dict(state.get("results", {}))
    ws_messages = list(state.get("ws_messages", []))

    if not easy_ids:
        return {"results": results}

    llm = get_reasoning_llm()
    search_tool = WebSearchTool()

    for problem_id in easy_ids:
        problem = next((p for p in problems if p["id"] == problem_id), None)
        if not problem:
            continue

        # Skip if already cached
        if problem.get("cache_hit"):
            continue

        start_time = time.time()
        logger.info(f"[EasySolver] Solving problem {problem_id}: {problem['content'][:100]}")

        ws_messages.append({
            "type": "solving_problem",
            "data": {"problem_id": problem_id, "status": "in_progress", "route": "easy"},
        })

        try:
            # Step 1: LLM direct solve
            messages = [
                SystemMessage(content=EASY_SOLVER_SYSTEM_PROMPT),
                HumanMessage(content=f"Solve this problem:\n\n{problem['content']}"),
            ]

            response = await llm.ainvoke(messages)
            parsed = parse_json_response(response.content)

            tools_used = ["llm_direct"]
            search_result = None

            if parsed:
                confidence = float(parsed.get("confidence", 0.5))
                needs_search = parsed.get("needs_search", False)

                # Step 2: Web search fallback if low confidence
                if confidence < 0.7 or needs_search:
                    logger.info(
                        f"[EasySolver] Problem {problem_id} confidence={confidence:.2f}, "
                        f"trying web search"
                    )
                    search_result = await search_tool.safe_execute(problem["content"])
                    if search_result.success:
                        tools_used.append("web_search")

                latency = int((time.time() - start_time) * 1000)

                results[problem_id] = {
                    "steps": parsed.get("steps", []),
                    "final_answer": parsed.get("final_answer", ""),
                    "confidence": confidence,
                    "tools_used": tools_used,
                    "solve_route": "llm_direct",
                    "search_context": search_result.output if search_result and search_result.success else None,
                    "latency_ms": latency,
                    "error": None,
                }
            else:
                # Parsing failed — try web search as fallback
                logger.warning(f"[EasySolver] Parse failed for problem {problem_id}")
                search_result = await search_tool.safe_execute(problem["content"])

                latency = int((time.time() - start_time) * 1000)
                results[problem_id] = {
                    "steps": [],
                    "final_answer": response.content[:500] if response else "",
                    "confidence": 0.3,
                    "tools_used": ["llm_direct", "web_search"],
                    "solve_route": "web_search",
                    "search_context": search_result.output if search_result.success else None,
                    "latency_ms": latency,
                    "error": "LLM output parsing failed",
                }

            ws_messages.append({
                "type": "problem_solved",
                "data": {"problem_id": problem_id, "route": "easy"},
            })

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"[EasySolver] Error on problem {problem_id}: {e}")
            results[problem_id] = {
                "steps": [],
                "final_answer": "",
                "confidence": 0.0,
                "tools_used": [],
                "solve_route": "easy",
                "latency_ms": latency,
                "error": str(e),
            }

    return {"results": results, "ws_messages": ws_messages}
