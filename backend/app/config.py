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
    # Model IDs for different agents (Person 3/Person 5 naming)
    llm_model_reasoning: str = "llama-3.3-70b-versatile"
    llm_model_extraction: str = "llama-3.1-8b-instant"
    llm_model_classifier: str = "llama-3.1-8b-instant"
    
    # Granular model IDs (Person 1/Person 2 naming)
    llm_model_extractor: str = "llama-3.1-8b-instant"
    llm_model_planner: str = "llama-3.1-8b-instant"
    llm_model_coder: str = "llama-3.3-70b-versatile"
    llm_model_fixer: str = "llama-3.1-8b-instant"
    llm_model_aggregator: str = "llama-3.3-70b-versatile"

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

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    # ── GZip Compression ─────────────────────────────────────
    gzip_min_size: int = 500  # bytes — responses smaller than this skip compression

    # ── HuggingFace Spaces ───────────────────────────────────
    hf_space: bool = False

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def validate_keys(self) -> List[str]:
        """Check for missing API keys and return a list of warnings.

        Called at startup so the team immediately sees what's missing.
        """
        warnings: List[str] = []
        if not self.groq_api_key or self.groq_api_key.startswith("gsk_your"):
            warnings.append("GROQ_API_KEY is missing — LLM calls will fail")
        if not self.wolfram_alpha_app_id or "your_" in self.wolfram_alpha_app_id:
            warnings.append("WOLFRAM_ALPHA_APP_ID is missing — Tier 1 tool disabled")
        if not self.tavily_api_key or "your_" in self.tavily_api_key:
            warnings.append("TAVILY_API_KEY is missing — Tier 3 search disabled")
        if not self.langchain_api_key or "your_" in self.langchain_api_key:
            warnings.append("LANGCHAIN_API_KEY is missing — LangSmith tracing disabled")
        return warnings


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
