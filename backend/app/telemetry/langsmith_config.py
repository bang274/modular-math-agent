"""
LangSmith Configuration.

Person 5 owns this file.
Sets up LangSmith tracing for the entire agent pipeline.
"""

import os

from app.telemetry.logger import logger


def setup_langsmith(settings) -> None:
    """Configure LangSmith environment variables for tracing.

    LangChain/LangGraph automatically pick up these env vars.
    """
    if not settings.langchain_api_key:
        logger.info("[LangSmith] No API key configured, tracing disabled")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    logger.info(
        f"[LangSmith] Tracing enabled for project: {settings.langchain_project}"
    )
