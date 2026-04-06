"""
Classifier Node — Difficulty classification.

Person 3 owns this file.
Routes each problem to easy or hard branch based on LLM classification.
"""

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_planner_llm

from app.llm.prompts import CLASSIFIER_SYSTEM_PROMPT
from app.llm.parser import parse_json_response
from app.telemetry.logger import logger


async def classifier_node(state: AgentState) -> Dict[str, Any]:
    """Classify each problem as easy or hard.

    Classification criteria:
    - Easy (score < 0.6): basic arithmetic, simple algebra, theory, direct formulas
    - Hard (score >= 0.6): calculus, complex algebra, differential equations, numerical

    Returns:
        Updated state with difficulty set for each problem,
        and easy_problems / hard_problems lists populated.
    """
    problems = state.get("problems", [])

    if not problems:
        return {"easy_problems": [], "hard_problems": []}

    llm = get_planner_llm()

    easy_ids: List[int] = []
    hard_ids: List[int] = []

    updated_problems = []

    for problem in problems:
        # Skip if already cached
        if problem.get("cache_hit"):
            logger.info(f"[Classifier] Problem {problem['id']} is cached, skipping")
            updated_problems.append(problem)
            continue

        try:
            messages = [
                SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
                HumanMessage(content=f"Classify this math problem:\n\n{problem['content']}"),
            ]

            response = await llm.ainvoke(messages)
            parsed = parse_json_response(response.content)

            if parsed:
                difficulty = parsed.get("difficulty", "hard")
                score = float(parsed.get("score", 0.7))
                reasoning = parsed.get("reasoning", "")
            else:
                # Default to hard if classification fails (safer)
                difficulty = "hard"
                score = 0.7
                reasoning = "Classification failed, defaulting to hard"

            logger.info(
                f"[Classifier] Problem {problem['id']}: "
                f"{difficulty} (score={score:.2f}) — {reasoning}"
            )

            problem_copy = {**problem}
            problem_copy["difficulty"] = difficulty
            problem_copy["difficulty_score"] = score
            updated_problems.append(problem_copy)

            if difficulty == "easy":
                easy_ids.append(problem["id"])
            else:
                hard_ids.append(problem["id"])

        except Exception as e:
            logger.warning(
                f"[Classifier] Error classifying problem {problem['id']}: {e}. "
                f"Defaulting to hard."
            )
            problem_copy = {**problem}
            problem_copy["difficulty"] = "hard"
            problem_copy["difficulty_score"] = 0.7
            updated_problems.append(problem_copy)
            hard_ids.append(problem["id"])

    logger.info(
        f"[Classifier] Results: {len(easy_ids)} easy, {len(hard_ids)} hard"
    )

    return {
        "problems": updated_problems,
        "easy_problems": easy_ids,
        "hard_problems": hard_ids,
    }
