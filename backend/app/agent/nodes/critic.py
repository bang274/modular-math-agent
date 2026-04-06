"""
Critic Node — Mathematical Self-Reflection & Verification.

Uses an LLM to critique solving attempts before they reach the aggregator.
If a result fails the logic check, it can trigger a sub-loop to re-solve.
"""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_aggregator_llm
from app.llm.prompts import CRITIC_SYSTEM_PROMPT
from app.telemetry.logger import logger


async def critic_node(state: AgentState) -> Dict[str, Any]:
    """Verify solving results and decide if revision is needed."""
    problems = state.get("problems", [])
    results = state.get("results", {})
    
    # We only critique problems that have been 'solved' but not yet aggregated
    llm = get_aggregator_llm()  # Using aggregator for reasoning
    
    updated_results = dict(results)
    needs_revision = []

    for pid, res in results.items():
        # If it's already an error, no point critiquing
        if res.get("error"):
            continue
            
        problem = next((p for p in problems if p["id"] == pid), None)
        if not problem:
            continue

        logger.info(f"[Critic] Verifying problem {pid}...")
        
        # Prepare context for critic
        context = (
            f"Problem: {problem['content']}\n\n"
            f"Solve Route: {res.get('solve_route')}\n"
            f"Final Answer: {res.get('final_answer')}\n"
            f"Steps: {res.get('steps')}\n"
            f"Tool Outputs: {json.dumps(res.get('tool_outputs', {}))}\n"
        )

        try:
            response = await llm.ainvoke([
                SystemMessage(content=CRITIC_SYSTEM_PROMPT),
                HumanMessage(content=context)
            ])
            
            # Parse JSON verdict
            from app.llm.parser import parse_json_response
            critique = parse_json_response(response.content)
            
            if critique:
                verdict = critique.get("verdict", "pass")
                res["critic_verdict"] = verdict
                res["critic_reason"] = critique.get("reason", "")
                
                if verdict == "fail" and res.get("critique_count", 0) < 1:
                    logger.warning(f"[Critic] Problem {pid} FAILED: {critique.get('reason')}")
                    res["critique_count"] = res.get("critique_count", 0) + 1
                    res["feedback"] = critique.get("feedback", "")
                    needs_revision.append(pid)
                else:
                    logger.info(f"[Critic] Problem {pid} PASSED.")
            
            updated_results[pid] = res
            
        except Exception as e:
            logger.error(f"[Critic] Error: {e}")
            continue

    return {
        "results": updated_results,
        "needs_revision": needs_revision,
        "ws_messages": [
            {
                "type": "critic_check", 
                "data": {"count": len(results), "failed": len(needs_revision)}
            }
        ]
    }
