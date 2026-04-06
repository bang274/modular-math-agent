"""
Routing Edges — Conditional edge functions for LangGraph.

Person 3 owns this file.
Defines routing logic between nodes in the agent graph.
"""

from typing import Literal

from app.agent.state import AgentState
from app.telemetry.logger import logger


def route_after_extraction(state: AgentState) -> Literal["cache_check", "error_end"]:
    """Route after extraction: proceed to cache check or end with error."""
    problems = state.get("problems", [])
    error = state.get("extraction_error")

    if not problems or error:
        logger.warning(f"[Router] Extraction failed or no problems: {error}")
        return "error_end"

    return "cache_check"


def route_after_cache(state: AgentState) -> Literal["classifier", "aggregator"]:
    """Route after cache check.

    If ALL problems are cached, skip solving and go to aggregator.
    Otherwise, proceed to classifier for solving.
    """
    problems = state.get("problems", [])
    cache_hits = state.get("cache_hits", {})

    # Check if all problems are cached
    all_cached = all(p["id"] in cache_hits for p in problems)

    if all_cached:
        logger.info("[Router] All problems cached, skipping to aggregator")
        return "aggregator"

    return "classifier"


def route_after_classifier(
    state: AgentState,
) -> Literal["easy_solver", "hard_solver", "both_solvers"]:
    """Route after classification based on problem difficulties.

    Returns which solver(s) to run.
    """
    easy_ids = state.get("easy_problems", [])
    hard_ids = state.get("hard_problems", [])

    has_easy = len(easy_ids) > 0
    has_hard = len(hard_ids) > 0

    if has_easy and has_hard:
        return "both_solvers"
    elif has_easy:
        return "easy_solver"
    else:
        return "hard_solver"
