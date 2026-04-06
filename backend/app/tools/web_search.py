"""
Web Search Tool (Tavily) — Tier 3 / fallback solver.

Person 2 owns this file.
Uses Tavily Search API for web-based math knowledge lookup.
"""

from typing import List, Optional

from app.config import get_settings
from app.tools.base import BaseTool, ToolResult
from app.telemetry.logger import logger

try:
    from tavily import AsyncTavilyClient
    HAS_TAVILY = True
except ImportError:
    HAS_TAVILY = False


class WebSearchTool(BaseTool):
    """Tavily web search for math solutions and formulas.

    Priority: TIER 3 — last resort fallback.
    Also used by easy solver when LLM needs additional context.
    """

    name = "web_search"
    description = (
        "Search the web for math solutions, formulas, or concepts. "
        "Best for: looking up formulas, finding solution methods."
    )

    def __init__(self):
        self.settings = get_settings()

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Search the web using Tavily API.

        Args:
            query: Natural language search query.
            max_results: Maximum number of results (default: 5).

        Returns:
            ToolResult with search results summary.
        """
        if not HAS_TAVILY:
            return ToolResult(
                success=False,
                error="Tavily package not installed. Run: pip install tavily-python",
            )

        if not self.settings.tavily_api_key:
            return ToolResult(
                success=False,
                error="Tavily API key not configured",
            )

        max_results = kwargs.get("max_results", 5)

        # Optimize query for math search
        search_query = self._build_math_query(query)
        logger.info(f"[Search] Query: {search_query}")

        try:
            client = AsyncTavilyClient(api_key=self.settings.tavily_api_key)
            response = await client.search(
                query=search_query,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
            )

            return self._parse_results(response)

        except Exception as e:
            logger.error(f"[Search] Error: {e}")
            return ToolResult(success=False, error=f"Search failed: {str(e)}")

    def _build_math_query(self, query: str) -> str:
        """Optimize query for math-related web search."""
        # Add math-specific keywords if not present
        math_keywords = ["solve", "calculate", "formula", "math", "equation"]
        has_math_keyword = any(kw in query.lower() for kw in math_keywords)

        if not has_math_keyword:
            return f"math solve {query}"
        return query

    def _parse_results(self, response: dict) -> ToolResult:
        """Parse Tavily search response into a useful result."""
        results = response.get("results", [])
        answer = response.get("answer", "")

        if not results and not answer:
            return ToolResult(
                success=False,
                error="No relevant search results found",
            )

        # Build structured output
        output_parts = []

        if answer:
            output_parts.append(f"Direct Answer: {answer}")

        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "")
            content = result.get("content", "")[:500]  # Limit content length
            url = result.get("url", "")
            output_parts.append(f"\n[{i}] {title}\n{content}\nSource: {url}")

        output = "\n".join(output_parts)

        # Collect raw data for potential downstream use
        raw = {
            "answer": answer,
            "results": [
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "score": r.get("score", 0),
                }
                for r in results
            ],
        }

        logger.info(f"[Search] Found {len(results)} results, has_answer={bool(answer)}")
        return ToolResult(
            success=True,
            output=output,
            raw_data=raw,
        )
