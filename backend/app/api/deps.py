"""
Dependency Injection — shared deps for FastAPI routes.

Person 5 owns this file.
"""

from fastapi import Request, HTTPException

from app.cache.redis_client import redis_manager
from app.cache.rate_limiter import rate_limiter
from app.db.database import db_manager


async def check_rate_limit(request: Request) -> None:
    """Rate limiting dependency."""
    client_ip = request.client.host if request.client else "unknown"
    allowed = await rate_limiter.is_allowed(client_ip)
    if not allowed:
        remaining = await rate_limiter.get_remaining(client_ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": str(rate_limiter.window_seconds),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Window": str(rate_limiter.window_seconds),
            },
        )


def get_redis():
    """Get Redis client (may be None if Redis is down)."""
    return redis_manager.client


def get_db():
    """Get database manager."""
    return db_manager
