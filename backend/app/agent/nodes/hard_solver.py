"""
Hard Solver Node — Multi-tier solving for complex problems.

Person 3 owns this file.
Implements: Wolfram Alpha → Python Sandbox (retry 3x) → Web Search fallback.
"""

import time
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.config import get_settings
from app.llm.provider import get_reasoning_llm
from app.llm.prompts import PYTHON_CODEGEN_PROMPT
from app.llm.parser import extract_python_code
from app.tools.wolfram import WolframAlphaTool
from app.tools.python_executor import PythonExecutorTool
from app.tools.web_search import WebSearchTool
from app.telemetry.logger import logger


async def hard_solver_node(state: AgentState) -> Dict[str, Any]:
    """Solve hard problems using tiered tool strategy.

    Tier 1: Wolfram Alpha (exact symbolic math)
      ↓ fail
    Tier 2: Python Sandbox (LLM generates code, max 3 retries)
      ↓ fail
    Tier 3: Web Search (last resort fallback)

    First successful result is used. All tool outputs are passed
    to the aggregator for final formatting.

    Returns:
        Updated state with results for hard problems.
    """
    hard_ids = state.get("hard_problems", [])
    problems = state.get("problems", [])
    results = dict(state.get("results", {}))
    ws_messages = list(state.get("ws_messages", []))
    settings = get_settings()

    if not hard_ids:
        return {"results": results}

    wolfram = WolframAlphaTool()
    python_exec = PythonExecutorTool()
    web_search = WebSearchTool()
    llm = get_reasoning_llm()

    for problem_id in hard_ids:
        problem = next((p for p in problems if p["id"] == problem_id), None)
        if not problem:
            continue

        # Skip if already cached
        if problem.get("cache_hit"):
            continue

        start_time = time.time()
        logger.info(f"[HardSolver] Solving problem {problem_id}: {problem['content'][:100]}")

        ws_messages.append({
            "type": "solving_problem",
            "data": {"problem_id": problem_id, "status": "in_progress", "route": "hard"},
        })

        tools_used = []
        tool_outputs = {}
        solved = False
        final_output = ""
        errors = []

        # ── Tier 1: Wolfram Alpha ────────────────────────────
        logger.info(f"[HardSolver] Problem {problem_id} → Tier 1: Wolfram Alpha")
        wolfram_result = await wolfram.safe_execute(problem["content"])

        ws_messages.append({
            "type": "tool_called",
            "data": {
                "problem_id": problem_id,
                "tool": "wolfram_alpha",
                "success": wolfram_result.success,
            },
        })

        if wolfram_result.success:
            tools_used.append("wolfram_alpha")
            tool_outputs["wolfram"] = wolfram_result.output
            final_output = wolfram_result.output
            solved = True
            logger.info(f"[HardSolver] Problem {problem_id} solved by Wolfram!")
        else:
            errors.append(f"Wolfram: {wolfram_result.error}")
            logger.info(f"[HardSolver] Wolfram failed: {wolfram_result.error}")

            # ── Tier 2: Python Sandbox (with retries) ────────
            max_retries = settings.python_sandbox_max_retries
            error_context = ""

            for attempt in range(1, max_retries + 1):
                logger.info(
                    f"[HardSolver] Problem {problem_id} → Tier 2: Python "
                    f"(attempt {attempt}/{max_retries})"
                )

                # Generate Python code via LLM
                code_prompt = PYTHON_CODEGEN_PROMPT.format(
                    problem=problem["content"],
                    error_context=error_context,
                )
                try:
                    code_response = await llm.ainvoke([
                        HumanMessage(content=code_prompt)
                    ])
                    code = extract_python_code(code_response.content)
                except Exception as e:
                    errors.append(f"Python codegen error: {e}")
                    continue

                if not code:
                    errors.append(f"Python attempt {attempt}: failed to generate code")
                    continue

                # Execute the code
                python_result = await python_exec.safe_execute(code)

                ws_messages.append({
                    "type": "tool_called",
                    "data": {
                        "problem_id": problem_id,
                        "tool": "python_executor",
                        "attempt": attempt,
                        "success": python_result.success,
                    },
                })

                if python_result.success:
                    tools_used.append("python_executor")
                    tool_outputs["python"] = python_result.output
                    tool_outputs["python_code"] = code
                    final_output = python_result.output
                    solved = True
                    logger.info(
                        f"[HardSolver] Problem {problem_id} solved by Python "
                        f"(attempt {attempt})!"
                    )
                    break
                else:
                    # Feed error back for next retry
                    error_context = (
                        f"The previous code attempt failed with this error:\n"
                        f"```\n{python_result.error}\n```\n"
                        f"Previous code:\n```python\n{code}\n```\n"
                        f"Fix the error and try again."
                    )
                    errors.append(f"Python attempt {attempt}: {python_result.error}")
                    logger.info(
                        f"[HardSolver] Python attempt {attempt} failed: "
                        f"{python_result.error}"
                    )

            # ── Tier 3: Web Search (last resort) ─────────────
            if not solved:
                logger.info(
                    f"[HardSolver] Problem {problem_id} → Tier 3: Web Search"
                )
                search_result = await web_search.safe_execute(
                    f"solve {problem['content']}"
                )

                ws_messages.append({
                    "type": "tool_called",
                    "data": {
                        "problem_id": problem_id,
                        "tool": "web_search",
                        "success": search_result.success,
                    },
                })

                if search_result.success:
                    tools_used.append("web_search")
                    tool_outputs["search"] = search_result.output
                    final_output = search_result.output
                    solved = True
                    logger.info(
                        f"[HardSolver] Problem {problem_id} solved by web search!"
                    )
                else:
                    errors.append(f"Search: {search_result.error}")

        # ── Store result ─────────────────────────────────────
        latency = int((time.time() - start_time) * 1000)

        # Determine the route taken
        if "wolfram_alpha" in tools_used:
            route = "wolfram"
        elif "python_executor" in tools_used:
            route = "python_sandbox"
        elif "web_search" in tools_used:
            route = "fallback_search"
        else:
            route = "failed"

        results[problem_id] = {
            "final_answer": final_output,
            "tools_used": tools_used,
            "tool_outputs": tool_outputs,
            "solve_route": route,
            "solved": solved,
            "confidence": 0.95 if "wolfram_alpha" in tools_used else
                         0.80 if "python_executor" in tools_used else
                         0.50 if "web_search" in tools_used else 0.0,
            "errors": errors,
            "latency_ms": latency,
            "error": None if solved else "All solving tiers failed",
        }

        ws_messages.append({
            "type": "problem_solved" if solved else "error",
            "data": {
                "problem_id": problem_id,
                "route": route,
                "solved": solved,
            },
        })

    return {"results": results, "ws_messages": ws_messages}
