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


def _extract_clean_answer(raw_text: str) -> str:
    """Extract the core math answer from raw Wolfram Alpha output.

    Wolfram LLM API returns verbose text with images, Riemann sums,
    Wolfram Language code, etc. This extracts just the key result.
    """
    import re

    if not raw_text or len(raw_text) < 5:
        return raw_text

    # If the raw text is short and clean, just return it
    if len(raw_text) < 100 and "\n" not in raw_text:
        return raw_text

    lines = raw_text.split("\n")
    # Lines to skip (noise from Wolfram)
    skip_patterns = [
        r"^Query:",
        r"^Wolfram\|?Alpha",
        r"^Visual representation",
        r"^image:",
        r"^https?://",
        r"^Wolfram Language",
        r"^Plot\[",
        r"^Riemann sum",
        r"^left sum",
        r"^right sum",
        r"^midpoint",
        r"^\(assuming",
    ]

    useful_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(re.match(pat, line, re.IGNORECASE) for pat in skip_patterns):
            continue
        useful_lines.append(line)

    if not useful_lines:
        return raw_text.split("\n")[0] if raw_text else ""

    # Prioritize lines with "=" (these contain the actual answer)
    answer_lines = [l for l in useful_lines if "=" in l and "http" not in l]
    if answer_lines:
        # Pick the most specific answer line (usually the shortest with "=")
        best = min(answer_lines, key=len)
        # Clean up Wolfram notation
        best = re.sub(r"\s*≈\s*[\d.]+", "", best)  # Remove decimal approximation
        # Extract just the RHS of ": result = answer"
        if ": " in best:
            best = best.split(": ", 1)[1]
        return best.strip()

    return useful_lines[0]


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

    # ── Handle Case: No math found/Extraction Error ────────────────
    if not problems and state.get("extraction_error"):
        logger.info("[Aggregator] Returning friendly 'No Math Found' response.")
        return {
            "status": "success",
            "final_results": [],
            "aggregator_error": None,
            "ws_messages": ws_messages + [{
                "type": "final_answer",
                "data": {
                    "text": state["extraction_error"],
                    "results": []
                }
            }]
        }

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
                "error": "Rất tiếc, tôi gặp khó khăn khi xử lý bài toán này (không có kết quả từ công cụ).",
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

            # Include tool outputs with cleanup hints
# ... rest of tool output logic ...
            # Include tool outputs
            tool_outputs = result.get("tool_outputs", {})
            if tool_outputs:
                for tool_name, output in tool_outputs.items():
                    # Truncate very long outputs to avoid prompt overflow
                    truncated = output[:2000] if isinstance(output, str) else str(output)[:2000]
                    aggregate_prompt += f"--- {tool_name} raw output ---\n{truncated}\n\n"
            elif result.get("final_answer"):
                aggregate_prompt += f"Answer: {result['final_answer'][:1000]}\n\n"

            if result.get("steps"):
                aggregate_prompt += f"Steps: {result['steps']}\n\n"

            if result.get("search_context"):
                aggregate_prompt += f"Search context: {result['search_context'][:1000]}\n\n"

            aggregate_prompt += (
                "IMPORTANT: Extract the core mathematical result from the tool output above. "
                "Ignore image URLs, Wolfram Language code, Riemann sums, and website links. "
                "Create a clean step-by-step solution with Vietnamese descriptions and proper LaTeX. "
                "Return ONLY valid JSON."
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
                # Fallback: extract key result from raw tool output
                raw_answer = result.get("final_answer", "")
                final_answer = _extract_clean_answer(raw_answer)
                steps = result.get("steps", [])
                if not steps and final_answer:
                    steps = [
                        {"step": 1, "description": "Đề bài", "latex": problem["content"]},
                        {"step": 2, "description": "Kết quả tính toán", "latex": final_answer},
                    ]
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
                "error": "Rất tiếc, đã có lỗi kết xuất kết quả từ hệ thống.",
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
