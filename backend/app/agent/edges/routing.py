from typing import List, Literal, Union

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
) -> Union[str, List[str]]:
    """Route after classification based on problem difficulties.

    Returns which solver(s) to run (can be multiple for parallel execution).
    """
    easy_ids = state.get("easy_problems", [])
    hard_ids = state.get("hard_problems", [])

    has_easy = len(easy_ids) > 0
    has_hard = len(hard_ids) > 0

    if has_easy and has_hard:
        logger.info("[Router] Both easy and hard problems found: Branching parallel solvers")
        return ["easy_solver", "hard_solver"]
    elif has_easy:
        logger.info("[Router] Routing to EasySolver")
        return "easy_solver"
    elif has_hard:
        logger.info("[Router] Routing to HardSolver")
        return "hard_solver"
    else:
        logger.warning("[Router] No problems classified, skipping to aggregator")
        return "aggregator"

