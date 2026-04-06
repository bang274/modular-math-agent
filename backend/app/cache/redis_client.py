"""
Redis Connection Manager.

Person 4 owns this file.
Handles: connection lifecycle, health check, graceful reconnection.
"""

from typing import Optional

import redis.asyncio as aioredis

from app.telemetry.logger import logger


class RedisManager:
    """Manages Redis connection lifecycle.

    Designed for graceful degradation — app works without Redis.
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def client(self) -> Optional[aioredis.Redis]:
        return self._client

    async def connect(self, settings) -> None:
        """Connect to Redis."""
        try:
            self._client = aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("[Redis] Connected successfully")
        except Exception as e:
            self._connected = False
            self._client = None
            logger.warning(f"[Redis] Connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
            self._connected = False
            logger.info("[Redis] Disconnected")

    async def health_check(self) -> bool:
        """Check if Redis is responsive."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            self._connected = False
            return False


# Global singleton
redis_manager = RedisManager()
