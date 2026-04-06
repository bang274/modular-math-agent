"""
Math AI Agent Pipeline — Configuration

Centralized settings loaded from environment variables via Pydantic BaseSettings.
All team members import settings from here.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── LLM (Groq) ──────────────────────────────────────────
    groq_api_key: str = ""
    llm_model_reasoning: str = "PLACEHOLDER_REASONING_MODEL_ID"
    llm_model_extraction: str = "PLACEHOLDER_EXTRACTION_MODEL_ID"
    llm_model_classifier: str = "PLACEHOLDER_CLASSIFIER_MODEL_ID"

    # ── Wolfram Alpha ────────────────────────────────────────
    wolfram_alpha_app_id: str = ""
    wolfram_timeout_seconds: int = 10

    # ── Tavily Search ────────────────────────────────────────
    tavily_api_key: str = ""

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    redis_cache_ttl_seconds: int = 86400  # 24 hours

    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/math_agent.db"

    # ── LangSmith ────────────────────────────────────────────
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "math-ai-agent"

    # ── Pipeline Limits ──────────────────────────────────────
    max_parallel_problems: int = 5
    max_upload_size_mb: int = 10
    python_sandbox_timeout_seconds: int = 5
    python_sandbox_max_retries: int = 3

    # ── HuggingFace Spaces ───────────────────────────────────
    hf_space: bool = False

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
