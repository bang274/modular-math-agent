"""
Math AI Agent Pipeline — FastAPI Application Factory

Person 5 owns this file.
Handles: app creation, lifespan (startup/shutdown), CORS, middleware, error handling.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.router import api_router
from app.api.middleware import RequestIDMiddleware, TimingMiddleware
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

    # Validate API keys — warn early, don't crash
    key_warnings = settings.validate_keys()
    for w in key_warnings:
        logger.warning(f"⚠️  CONFIG: {w}")
    if key_warnings:
        logger.warning(
            f"⚠️  {len(key_warnings)} config warning(s) — "
            f"copy .env.example to .env and fill in your keys"
        )

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
        f"max_parallel={settings.max_parallel_problems} | "
        f"rate_limit={settings.rate_limit_requests}/{settings.rate_limit_window_seconds}s"
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
        version="1.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    # ── Middleware (order matters: last added = first executed) ──
    # CORS must be outermost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )
    # GZip responses above gzip_min_size bytes
    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_min_size)
    # Request ID tracking
    app.add_middleware(RequestIDMiddleware)
    # Process time measurement
    app.add_middleware(TimingMiddleware)

    # ── Global Exception Handler ─────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Return consistent JSON for unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"[Unhandled Error] {request.method} {request.url.path} "
            f"request_id={request_id} error={exc}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": str(exc) if settings.app_debug else "An unexpected error occurred",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    # ── Routes ───────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


# Uvicorn entry point
app = create_app()
