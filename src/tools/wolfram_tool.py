"""
Person 2 — Wolfram Alpha Tool (Tier 1)
First-choice tool: sends the math question to Wolfram Alpha's API
and returns the computed result.

=== TEAM (Person 2): Get a free App ID at https://developer.wolframalpha.com ===

Dependencies:
  pip install wolframalpha
"""

import os
from typing import Optional

try:
    import wolframalpha
    HAS_WOLFRAM = True
except ImportError:
    wolframalpha = None
    HAS_WOLFRAM = False

from src.telemetry.logger import logger


# ─── Tool Function ───────────────────────────────────────────────────────────

def wolfram_query(query: str) -> str:
    """
    Send a math query to Wolfram Alpha and return the primary result.

    Input: a natural-language or symbolic math query, e.g. 'derivative of x^3 + 2x'
    Returns: the computed answer as a string, or an error message.

    === TEAM (Person 2): Tune which 'pods' you extract from the response ===
    """
    if not HAS_WOLFRAM:
        return "Error: wolframalpha package not installed. Run: pip install wolframalpha"

    app_id = os.getenv("WOLFRAM_APP_ID", "")
    if not app_id or app_id == "your_wolfram_app_id_here":
        return "Error: WOLFRAM_APP_ID not set in .env file."

    try:
        client = wolframalpha.Client(app_id)
        res = client.query(query)

        logger.log_event("WOLFRAM_QUERY", {"query": query})

        # Try to get the primary result
        # === TEAM (Person 2): Customize pod selection for your use case ===
        pods = list(res.pods) if hasattr(res, 'pods') else []

        if not pods:
            logger.log_event("WOLFRAM_NO_RESULT", {"query": query})
            return f"Wolfram Alpha returned no results for: {query}"

        # Look for the "Result" or "Solution" pod first
        for pod in pods:
            if pod.title and pod.title.lower() in ("result", "solution", "solutions",
                                                      "exact result", "decimal approximation"):
                texts = []
                for sub in pod.subpods:
                    if sub.plaintext:
                        texts.append(sub.plaintext)
                if texts:
                    answer = " | ".join(texts)
                    logger.log_event("WOLFRAM_RESULT", {"pod": pod.title, "answer": answer[:200]})
                    return f"Wolfram [{pod.title}]: {answer}"

        # Fallback: return the first pod with text
        for pod in pods:
            for sub in pod.subpods:
                if sub.plaintext and pod.title.lower() != "input":
                    logger.log_event("WOLFRAM_RESULT", {"pod": pod.title, "answer": sub.plaintext[:200]})
                    return f"Wolfram [{pod.title}]: {sub.plaintext}"

        return f"Wolfram Alpha could not compute: {query}"

    except Exception as e:
        logger.error(f"Wolfram Alpha error: {e}")
        return f"Wolfram Alpha error: {e}"


# ─── Tool Registration ───────────────────────────────────────────────────────

WOLFRAM_TOOL = {
    "name": "wolfram_alpha",
    "description": (
        "Query Wolfram Alpha for a math computation. "
        "Best for: derivatives, integrals, equation solving, limits, series, and exact arithmetic. "
        "Input: a math query string (natural language or symbolic). "
        "Example: wolfram_alpha(derivative of x^3 + 2x) or wolfram_alpha(solve x^2 - 4 = 0). "
        "This is the most reliable tool — try it FIRST before other tools."
    ),
    "function": wolfram_query,
}
