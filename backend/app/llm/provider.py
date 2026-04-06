"""
LLM Provider — Groq API via LangChain.

Provides configured ChatGroq instances for different pipeline stages.
All team members use these factory functions instead of creating LLM instances directly.
"""

from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import get_settings


def get_extractor_llm() -> ChatGroq:
    """LLM for input extraction and OCR tasks."""
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_extractor,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=4096,
    )


def get_planner_llm() -> ChatGroq:
    """LLM for difficulty classification and routing."""
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_planner,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=512,
    )


def get_coder_llm() -> ChatGroq:
    """LLM for generating Python code in the sandbox."""
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_coder,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
    )


def get_fixer_llm() -> ChatGroq:
    """LLM for debugging and fixing Python code errors."""
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_fixer,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
    )


def get_aggregator_llm() -> ChatGroq:
    """LLM for final reasoning, synthesis, and formatting."""
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_aggregator,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
    )


@lru_cache()
def get_default_llm() -> ChatGroq:
    """Default LLM instance (cached). Use for one-off calls."""
    return get_aggregator_llm()

