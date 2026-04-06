"""
Rate Limiter — Redis-based API rate limiting.

Person 4 owns this file.
Uses sliding window counter pattern.
"""

from typing import Optional

from app.cache.redis_client import redis_manager
from app.telemetry.logger import logger


class RateLimiter:
    """Redis-based rate limiter using sliding window.

    Default: 30 requests per minute per IP.
    """

    KEY_PREFIX = "math:rate:"

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            identifier: Usually client IP address.

        Returns:
            True if request is allowed, False if rate limited.
        """
        if not redis_manager.is_connected:
            # If Redis is down, allow all requests (fail-open)
            return True

        key = f"{self.KEY_PREFIX}{identifier}"

        try:
            current = await redis_manager.client.incr(key)

            if current == 1:
                # First request in window — set TTL
                await redis_manager.client.expire(key, self.window_seconds)

            if current > self.max_requests:
                logger.warning(f"[RateLimit] {identifier} exceeded {self.max_requests} req/min")
                return False

            return True

        except Exception as e:
            logger.warning(f"[RateLimit] Error: {e}, allowing request")
            return True

    async def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        if not redis_manager.is_connected:
            return self.max_requests

        key = f"{self.KEY_PREFIX}{identifier}"
        try:
            current = await redis_manager.client.get(key)
            if current is None:
                return self.max_requests
            return max(0, self.max_requests - int(current))
        except Exception:
            return self.max_requests


# Global rate limiter instance
rate_limiter = RateLimiter()
