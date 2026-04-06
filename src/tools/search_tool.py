"""
Person 4 — Search Tool (Tier 3)
Last-resort tool: searches the internet for math formulas, procedures, or
similar solved problems when Wolfram and Python both fail.

=== TEAM (Person 4): Get a free API key at https://tavily.com ===

Alternative: use SerpApi, Google Custom Search, or DuckDuckGo.
"""

import os
from typing import Optional

try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ImportError:
    TavilyClient = None
    HAS_TAVILY = False

from src.telemetry.logger import logger


# ─── Tool Function ───────────────────────────────────────────────────────────

def search_math(query: str) -> str:
    """
    Search the internet for a math formula, solution method, or similar problem.

    Input: a search query string describing what you need.
    Returns: a summary of the top search results.

    === TEAM (Person 4): Tune the search parameters and result formatting ===
    """
    if not HAS_TAVILY:
        return _fallback_message(query)

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key or api_key == "your_tavily_api_key_here":
        return "Error: TAVILY_API_KEY not set in .env file."

    try:
        client = TavilyClient(api_key=api_key)

        # Math-focused search
        # === TEAM (Person 4): Adjust search_depth, include_domains, etc. ===
        response = client.search(
            query=f"math solution: {query}",
            search_depth="advanced",  # "basic" or "advanced"
            max_results=3,
            include_domains=[
                "mathway.com",
                "wolframalpha.com",
                "symbolab.com",
                "math.stackexchange.com",
                "en.wikipedia.org",
            ],
        )

        logger.log_event("SEARCH_QUERY", {"query": query})

        results = response.get("results", [])
        if not results:
            logger.log_event("SEARCH_NO_RESULT", {"query": query})
            return f"No search results found for: {query}"

        # Format results
        formatted = []
        for i, r in enumerate(results[:3], 1):
            title = r.get("title", "No title")
            content = r.get("content", "")[:300]
            url = r.get("url", "")
            formatted.append(f"[{i}] {title}\n    {content}\n    Source: {url}")

        answer = "\n\n".join(formatted)
        logger.log_event("SEARCH_RESULT", {"count": len(results), "preview": answer[:200]})
        return f"Search results:\n\n{answer}"

    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search error: {e}"


def _fallback_message(query: str) -> str:
    """Message when tavily is not installed."""
    return (
        "Error: tavily-python not installed. Run: pip install tavily-python\n"
        "Alternative: Person 4 can implement a different search backend "
        "(SerpApi, Google Custom Search, or DuckDuckGo)."
    )


# ─── Tool Registration ───────────────────────────────────────────────────────

SEARCH_TOOL = {
    "name": "search_web",
    "description": (
        "Search the internet for a math formula, solution procedure, or similar solved problem. "
        "Use this ONLY as a last resort when wolfram_alpha and run_python both failed. "
        "Input: a descriptive query about the math problem you need help with. "
        "Example: search_web(how to solve integral of 1/(1+x^2) using trigonometric substitution)"
    ),
    "function": search_math,
}
