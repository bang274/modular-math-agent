"""
Prompt Cache — Semantic caching for math problem solutions.

Person 4 owns this file.
Uses SHA256 hash of normalized problem content as cache key.
"""

import hashlib
import json
import re
from typing import Any, Dict, Optional

from app.cache.redis_client import redis_manager
from app.config import get_settings
from app.telemetry.logger import logger


class PromptCache:
    """Semantic prompt cache using Redis.

    Strategy:
    1. Normalize problem content (strip whitespace, normalize LaTeX)
    2. SHA256 hash → cache key
    3. Store/retrieve JSON solution data
    4. TTL: 24h (configurable)
    """

    KEY_PREFIX = "math:cache:"

    def _normalize(self, content: str) -> str:
        """Normalize problem content for consistent hashing.

        Rules:
        1. Strip leading/trailing whitespace
        2. Collapse multiple spaces
        3. Normalize LaTeX spacing
        4. Lowercase non-LaTeX parts
        """
        text = content.strip()
        text = re.sub(r'\s+', ' ', text)
        # Normalize LaTeX spacing: \frac { x } { y } → \frac{x}{y}
        text = re.sub(r'\s*\{\s*', '{', text)
        text = re.sub(r'\s*\}\s*', '}', text)
        # Normalize common variations
        text = text.replace('\\left(', '(').replace('\\right)', ')')
        text = text.replace('\\left[', '[').replace('\\right]', ']')
        return text

    def _make_key(self, content: str) -> str:
        """Generate Redis key from problem content."""
        normalized = self._normalize(content)
        content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{self.KEY_PREFIX}{content_hash}"

    async def get(self, content: str) -> Optional[Dict[str, Any]]:
        """Look up cached solution for a problem.

        Args:
            content: Problem content string.

        Returns:
            Cached solution dict, or None if not found.
        """
        if not redis_manager.is_connected:
            return None

        try:
            key = self._make_key(content)
            data = await redis_manager.client.get(key)

            if data:
                result = json.loads(data)
                # Increment hit count
                await redis_manager.client.hincrby(f"{key}:meta", "hits", 1)
                logger.debug(f"[Cache] HIT: {key[:30]}...")
                return result

            return None

        except Exception as e:
            logger.warning(f"[Cache] GET error: {e}")
            return None

    async def set(self, content: str, solution: Dict[str, Any]) -> bool:
        """Store a solution in cache.

        Args:
            content: Problem content string.
            solution: Solution data to cache.

        Returns:
            True if successfully cached.
        """
        if not redis_manager.is_connected:
            return False

        settings = get_settings()

        try:
            key = self._make_key(content)
            data = json.dumps(solution, ensure_ascii=False)

            await redis_manager.client.set(
                key,
                data,
                ex=settings.redis_cache_ttl_seconds,
            )

            # Store metadata
            await redis_manager.client.hset(f"{key}:meta", mapping={
                "hits": 0,
                "content_preview": content[:100],
            })
            await redis_manager.client.expire(
                f"{key}:meta",
                settings.redis_cache_ttl_seconds,
            )

            logger.debug(f"[Cache] SET: {key[:30]}... TTL={settings.redis_cache_ttl_seconds}s")
            return True

        except Exception as e:
            logger.warning(f"[Cache] SET error: {e}")
            return False

    async def delete(self, content: str) -> bool:
        """Delete a cached solution (manual invalidation)."""
        if not redis_manager.is_connected:
            return False

        try:
            key = self._make_key(content)
            await redis_manager.client.delete(key, f"{key}:meta")
            return True
        except Exception as e:
            logger.warning(f"[Cache] DELETE error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not redis_manager.is_connected:
            return {"status": "disconnected"}

        try:
            info = await redis_manager.client.info("keyspace")
            keys_count = await redis_manager.client.dbsize()
            return {
                "status": "connected",
                "total_keys": keys_count,
                "info": info,
            }
        except Exception:
            return {"status": "error"}
