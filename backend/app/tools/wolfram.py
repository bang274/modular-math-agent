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

    name = "wolfram"

    description = (
        "Query Wolfram Alpha for symbolic math computation. "
        "Best for: integrals, derivatives, equations, limits, series."
    )

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://www.wolframalpha.com/api/v1/llm-api"

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Send a math query to Wolfram Alpha and parse the result.

        Args:
            query: Math expression in natural language or LaTeX-like syntax.

        Returns:
            ToolResult with the computed answer.
        """
        if not self.settings.wolfram_alpha_app_id:
            logger.error("[Wolfram] WOLFRAM_ALPHA_APP_ID is not configured in .env!")
            return ToolResult(
                success=False,
                error="Wolfram Alpha API key not configured",
            )


        # Tier 1.5: Use LLM to translate/clean query for Wolfram Alpha
        translated_query = await self._translate_query(query)
        logger.info(f"[Wolfram] Original: {query}")
        logger.info(f"[Wolfram] Translated: {translated_query}")
        
        # Final cleanup (strip LaTeX if LLM missed it) 
        clean_query = self._prepare_query(translated_query)


        params = {
            "input": clean_query,
            "appid": self.settings.wolfram_alpha_app_id,
        }


        try:
            async with httpx.AsyncClient(
                timeout=self.settings.wolfram_timeout_seconds
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                result_text = response.text

            # Check if Wolfram failed to interpret the query
            # The LLM API returns 200 OK with a failure message in text
            failure_indicators = [
                "Wolfram|Alpha did not understand your input",
                "Wolfram Alpha did not understand your input",
                "Wolfram|Alpha doesn't know how to interpret",
                "No results found",
            ]
            
            is_success = True
            error_msg = None
            
            if any(indicator in result_text for indicator in failure_indicators):
                is_success = False
                error_msg = "Wolfram could not interpret the query."
                logger.warning(f"[Wolfram] Interpretation failure: {result_text[:100]}")

            logger.info(f"[Wolfram] Result success={is_success}: {result_text[:200]}")
            return ToolResult(
                success=is_success,
                output=result_text,
                error=error_msg,
                raw_data={"result": result_text},
            )

        except httpx.TimeoutException:
            logger.warning(f"[Wolfram] Timeout for query: {clean_query}")
            return ToolResult(
                success=False,
                error="Wolfram Alpha request timed out",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[Wolfram] HTTP error: {e.response.status_code} - {e.response.text}")
            return ToolResult(
                success=False,
                error=f"Wolfram Alpha HTTP error: {e.response.status_code}\n{e.response.text}",
            )
        except Exception as e:
            logger.error(f"[Wolfram] Unexpected error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _translate_query(self, query: str) -> str:
        """Use LLM to translate math problem into Wolfram Alpha syntax."""
        from app.llm.provider import get_planner_llm
        from app.llm.prompts import WOLFRAM_QUERY_PROMPT
        from langchain_core.messages import HumanMessage
        
        llm = get_planner_llm()
        prompt = WOLFRAM_QUERY_PROMPT.format(content=query)
        
        try:
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip().replace("\"", "")
        except Exception as e:
            logger.warning(f"[Wolfram] Query translation failed: {e}")
            return query

    def _prepare_query(self, query: str) -> str:
        """Manual backup cleanup for Wolfram Alpha."""

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

