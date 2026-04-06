"""
Rate Limiter — Redis-based API rate limiting.

Person 4 owns this file.
Uses sliding window counter pattern.
"""

import time
from typing import Dict, List, Optional

from app.cache.redis_client import redis_manager
from app.telemetry.logger import logger


class RateLimiter:
    """Rate limiter with Redis sliding window and local memory fallback.

    Default: 30 requests per minute per IP.
    """

    KEY_PREFIX = "math:rate:"

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Local fallback storage: {identifier: [timestamps]}
        self._local_history: Dict[str, List[float]] = {}

    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit."""
        if not redis_manager.is_connected:
            return self._is_allowed_local(identifier)

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
            logger.warning(f"[RateLimit] Redis error: {e}, falling back to local memory")
            return self._is_allowed_local(identifier)

    def _is_allowed_local(self, identifier: str) -> bool:
        """In-memory sliding window fallback."""
        now = time.time()
        
        if identifier not in self._local_history:
            self._local_history[identifier] = []
            
        # Clean old timestamps
        self._local_history[identifier] = [
            t for t in self._local_history[identifier] 
            if now - t < self.window_seconds
        ]
        
        if len(self._local_history[identifier]) >= self.max_requests:
            logger.warning(f"[RateLimit-Local] {identifier} exceeded {self.max_requests} req/min")
            return False
            
        self._local_history[identifier].append(now)
        return True

    async def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        if not redis_manager.is_connected:
            now = time.time()
            history = self._local_history.get(identifier, [])
            active = [t for t in history if now - t < self.window_seconds]
            return max(0, self.max_requests - len(active))

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
