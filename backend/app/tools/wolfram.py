"""
Wolfram Alpha Tool — Tier 1 solver for symbolic math.

Person 2 owns this file.
Uses Wolfram Alpha API for exact symbolic computation.
"""

import asyncio
from typing import Optional

import httpx

from app.config import get_settings
from app.tools.base import BaseTool, ToolResult
from app.telemetry.logger import logger


class WolframAlphaTool(BaseTool):
    """Wolfram Alpha API wrapper for symbolic math computation.

    Priority: TIER 1 — first choice for hard math problems.
    Rate limit: ~2000 calls/month on free plan.
    """

    name = "wolfram_alpha"
    description = (
        "Query Wolfram Alpha for symbolic math computation. "
        "Best for: integrals, derivatives, equations, limits, series."
    )

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.wolframalpha.com/v2/query"

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Send a math query to Wolfram Alpha and parse the result.

        Args:
            query: Math expression in natural language or LaTeX-like syntax.

        Returns:
            ToolResult with the computed answer.
        """
        if not self.settings.wolfram_alpha_app_id:
            return ToolResult(
                success=False,
                error="Wolfram Alpha API key not configured",
            )

        # Clean LaTeX for Wolfram Alpha
        clean_query = self._prepare_query(query)
        logger.info(f"[Wolfram] Query: {clean_query}")

        params = {
            "input": clean_query,
            "appid": self.settings.wolfram_alpha_app_id,
            "format": "plaintext",
            "output": "json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.wolfram_timeout_seconds
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

            return self._parse_response(data)

        except httpx.TimeoutException:
            logger.warning(f"[Wolfram] Timeout for query: {clean_query}")
            return ToolResult(
                success=False,
                error="Wolfram Alpha request timed out",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[Wolfram] HTTP error: {e.response.status_code}")
            return ToolResult(
                success=False,
                error=f"Wolfram Alpha HTTP error: {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"[Wolfram] Unexpected error: {e}")
            return ToolResult(success=False, error=str(e))

    def _prepare_query(self, query: str) -> str:
        """Convert LaTeX-style query to Wolfram Alpha-friendly format."""
        # Basic LaTeX → Wolfram conversions
        replacements = {
            "\\int": "integrate",
            "\\frac": "",
            "\\sqrt": "sqrt",
            "\\sin": "sin",
            "\\cos": "cos",
            "\\tan": "tan",
            "\\ln": "ln",
            "\\log": "log",
            "\\pi": "pi",
            "\\infty": "infinity",
            "\\lim": "limit",
            "\\sum": "sum",
            "\\cdot": "*",
            "\\times": "*",
            "\\div": "/",
            "\\left": "",
            "\\right": "",
            "\\,": " ",
            "\\;": " ",
            "\\quad": " ",
        }
        result = query
        for latex, wolfram in replacements.items():
            result = result.replace(latex, wolfram)

        # Remove remaining backslashes and curly braces
        result = result.replace("{", "(").replace("}", ")")
        result = result.replace("\\", "")
        return result.strip()

    def _parse_response(self, data: dict) -> ToolResult:
        """Parse Wolfram Alpha JSON response.

        Extracts the most relevant result pod (usually 'Result' or 'Solution').
        """
        query_result = data.get("queryresult", {})

        if not query_result.get("success", False):
            # Check for didyoumeans suggestions
            tips = query_result.get("tips", {}).get("text", "")
            return ToolResult(
                success=False,
                error=f"Wolfram could not interpret the query. {tips}",
                raw_data=data,
            )

        pods = query_result.get("pods", [])
        if not pods:
            return ToolResult(
                success=False,
                error="No results returned from Wolfram Alpha",
                raw_data=data,
            )

        # Priority: Result > Solution > Exact result > first non-Input pod
        priority_titles = ["Result", "Solution", "Exact result", "Solutions"]
        result_text = ""

        for title in priority_titles:
            for pod in pods:
                if pod.get("title", "").lower() == title.lower():
                    subpods = pod.get("subpods", [])
                    if subpods:
                        result_text = subpods[0].get("plaintext", "")
                        if result_text:
                            break
            if result_text:
                break

        # Fallback: first non-Input pod
        if not result_text:
            for pod in pods:
                if pod.get("title", "").lower() != "input":
                    subpods = pod.get("subpods", [])
                    if subpods:
                        result_text = subpods[0].get("plaintext", "")
                        if result_text:
                            break

        if not result_text:
            return ToolResult(
                success=False,
                error="No interpretable result from Wolfram Alpha",
                raw_data=data,
            )

        # Collect all pods for raw_data
        all_results = {}
        for pod in pods:
            title = pod.get("title", "unknown")
            subpods = pod.get("subpods", [])
            all_results[title] = [sp.get("plaintext", "") for sp in subpods]

        logger.info(f"[Wolfram] Result: {result_text[:200]}")
        return ToolResult(
            success=True,
            output=result_text,
            raw_data=all_results,
        )
