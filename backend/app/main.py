"""
Math AI Agent Pipeline — FastAPI Application Factory

Person 5 owns this file.
Handles: app creation, lifespan (startup/shutdown), CORS, middleware.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.router import api_router
from app.cache.redis_client import redis_manager
from app.db.database import db_manager
from app.telemetry.langsmith_config import setup_langsmith
from app.telemetry.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 Starting Math AI Agent Pipeline...")

    # Initialize LangSmith tracing
    setup_langsmith(settings)

    # Connect to Redis (graceful — app works without it)
    try:
        await redis_manager.connect(settings)
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable, caching disabled: {e}")

    # Initialize database
    try:
        await db_manager.init(settings)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

    logger.info(
        f"✅ App ready | env={settings.app_env} | "
        f"max_parallel={settings.max_parallel_problems}"
    )

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 Shutting down...")
    await redis_manager.disconnect()
    await db_manager.close()
    logger.info("👋 Goodbye!")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="Math AI Agent Pipeline",
        description=(
            "AI-powered math problem solver with multi-agent pipeline. "
            "Upload text or images of math problems and get step-by-step solutions."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ───────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


# Uvicorn entry point
app = create_app()
