"""
LLM Provider — Groq API via LangChain.

Provides configured ChatGroq instances for different pipeline stages.
All team members use these factory functions instead of creating LLM instances directly.
"""

from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import get_settings


def get_reasoning_llm() -> ChatGroq:
    """LLM for reasoning, solving, and aggregation tasks.
    Uses the most capable model (placeholder — team will set in .env).
    """
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_reasoning,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
        max_retries=2,
    )


def get_extraction_llm() -> ChatGroq:
    """LLM for input extraction and OCR tasks.
    Uses a fast model optimized for structured output.
    """
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_extraction,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=4096,
        max_retries=2,
    )


def get_classifier_llm() -> ChatGroq:
    """LLM for difficulty classification.
    Uses a lightweight model since classification is simple.
    """
    settings = get_settings()
    return ChatGroq(
        model=settings.llm_model_classifier,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=512,
        max_retries=2,
    )


@lru_cache()
def get_default_llm() -> ChatGroq:
    """Default LLM instance (cached). Use for one-off calls."""
    return get_reasoning_llm()
