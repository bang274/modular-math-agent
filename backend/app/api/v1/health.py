"""
Health Check Endpoint.

Person 5 owns this file.
"""

from fastapi import APIRouter

from app.cache.redis_client import redis_manager
from app.db.database import db_manager
from app.models.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health: API, Redis, Database."""
    redis_ok = await redis_manager.health_check()
    db_ok = await db_manager.health_check()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        redis_connected=redis_ok,
        db_connected=db_ok,
    )
