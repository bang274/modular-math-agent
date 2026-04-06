"""
Tests for cache module.
"""

import json
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.agent.nodes.cache_node import cache_check_node, cache_store_node
from app.cache.prompt_cache import PromptCache
from app.cache.rate_limiter import RateLimiter
from app.cache.redis_client import RedisManager


class TestPromptCache:
    @pytest.fixture
    def cache(self):
        return PromptCache()

    def test_normalize_strips_whitespace(self, cache):
        result = cache._normalize("  x + 1  ")
        assert result == "x + 1"

    def test_normalize_collapses_spaces(self, cache):
        result = cache._normalize("x  +  1")
        assert result == "x + 1"

    def test_normalize_latex_braces(self, cache):
        result = cache._normalize("\\frac { 1 } { 2 }")
        assert result == "\\frac{1}{2}"

    def test_make_key_consistent(self, cache):
        """Same content should produce same key."""
        key1 = cache._make_key("x^2 + 1")
        key2 = cache._make_key("x^2 + 1")
        assert key1 == key2

    def test_make_key_different_content(self, cache):
        """Different content should produce different keys."""
        key1 = cache._make_key("x^2 + 1")
        key2 = cache._make_key("x^3 + 1")
        assert key1 != key2

    def test_make_key_normalized(self, cache):
        """Equivalent content with different spacing should match."""
        key1 = cache._make_key("x + 1")
        key2 = cache._make_key("  x  +  1  ")
        assert key1 == key2

    def test_normalize_replaces_latex_delimiters(self, cache):
        result = cache._normalize(r"\left( x + 1 \right) + \left[ y \right]")
        assert result == "( x + 1 ) + [ y ]"


class TestPromptCacheAsync:
    @pytest.fixture
    def cache(self):
        return PromptCache()

    @pytest.mark.asyncio
    async def test_get_returns_none_when_disconnected(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            result = await cache.get("x + 1")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_cached_result_on_hit(self, cache):
        payload = {"steps": [{"step": 1}], "final_answer": "2", "confidence": 0.9}
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.return_value = json.dumps(payload)

            result = await cache.get("x + 1")

            assert result == payload
            assert mock_redis.client.hincrby.await_count == 1

    @pytest.mark.asyncio
    async def test_get_returns_none_on_error(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.side_effect = RuntimeError("redis error")

            result = await cache.get("x + 1")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_on_cache_miss_without_meta_update(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.return_value = None

            result = await cache.get("x + 1")

            assert result is None
            assert mock_redis.client.hincrby.await_count == 0

    @pytest.mark.asyncio
    async def test_set_returns_false_when_disconnected(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            ok = await cache.set("x + 1", {"final_answer": "2"})
            assert ok is False

    @pytest.mark.asyncio
    async def test_set_stores_data_with_ttl_and_metadata(self, cache):
        settings = SimpleNamespace(redis_cache_ttl_seconds=123)
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis, patch(
            "app.cache.prompt_cache.get_settings",
            return_value=settings,
        ):
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()

            ok = await cache.set("x + 1", {"final_answer": "2", "confidence": 0.8})

            assert ok is True
            assert mock_redis.client.set.await_count == 1
            _, kwargs = mock_redis.client.set.await_args
            assert kwargs["ex"] == 123
            assert mock_redis.client.hset.await_count == 1
            _, hset_kwargs = mock_redis.client.hset.await_args
            assert hset_kwargs["mapping"]["hits"] == 0
            assert hset_kwargs["mapping"]["content_preview"] == "x + 1"
            assert mock_redis.client.expire.await_count == 1

    @pytest.mark.asyncio
    async def test_set_returns_false_on_error(self, cache):
        settings = SimpleNamespace(redis_cache_ttl_seconds=60)
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis, patch(
            "app.cache.prompt_cache.get_settings",
            return_value=settings,
        ):
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.set.side_effect = RuntimeError("cannot set")

            ok = await cache.set("x + 1", {"final_answer": "2"})

            assert ok is False

    @pytest.mark.asyncio
    async def test_delete_behaviors(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            assert await cache.delete("x + 1") is False

        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            assert await cache.delete("x + 1") is True
            assert mock_redis.client.delete.await_count == 1

    @pytest.mark.asyncio
    async def test_delete_returns_false_on_error(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.delete.side_effect = RuntimeError("delete failed")

            assert await cache.delete("x + 1") is False

    @pytest.mark.asyncio
    async def test_get_stats_behaviors(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            assert await cache.get_stats() == {"status": "disconnected"}

        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.info.return_value = {"db0": {"keys": 2}}
            mock_redis.client.dbsize.return_value = 2

            result = await cache.get_stats()

            assert result["status"] == "connected"
            assert result["total_keys"] == 2

    @pytest.mark.asyncio
    async def test_get_stats_returns_error_on_exception(self, cache):
        with patch("app.cache.prompt_cache.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.info.side_effect = RuntimeError("stats failed")

            assert await cache.get_stats() == {"status": "error"}


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_is_allowed_fail_open_when_disconnected(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            assert await limiter.is_allowed("1.2.3.4") is True

    @pytest.mark.asyncio
    async def test_is_allowed_sets_ttl_on_first_request(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.incr.return_value = 1

            allowed = await limiter.is_allowed("1.2.3.4")

            assert allowed is True
            assert mock_redis.client.expire.await_count == 1

    @pytest.mark.asyncio
    async def test_is_allowed_does_not_reset_ttl_after_first_request(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.incr.side_effect = [1, 2]

            assert await limiter.is_allowed("1.2.3.4") is True
            assert await limiter.is_allowed("1.2.3.4") is True
            assert mock_redis.client.expire.await_count == 1

    @pytest.mark.asyncio
    async def test_is_allowed_returns_false_when_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.incr.return_value = 3

            allowed = await limiter.is_allowed("1.2.3.4")

            assert allowed is False

    @pytest.mark.asyncio
    async def test_is_allowed_returns_true_on_redis_error(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.incr.side_effect = RuntimeError("redis down")

            assert await limiter.is_allowed("1.2.3.4") is True

    @pytest.mark.asyncio
    async def test_get_remaining_behaviors(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = False
            assert await limiter.get_remaining("1.2.3.4") == 5

        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.return_value = "2"
            assert await limiter.get_remaining("1.2.3.4") == 3

    @pytest.mark.asyncio
    async def test_get_remaining_returns_max_when_key_absent(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.return_value = None

            assert await limiter.get_remaining("1.2.3.4") == 5

    @pytest.mark.asyncio
    async def test_get_remaining_returns_max_on_error(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        with patch("app.cache.rate_limiter.redis_manager") as mock_redis:
            mock_redis.is_connected = True
            mock_redis.client = AsyncMock()
            mock_redis.client.get.side_effect = RuntimeError("read failed")

            assert await limiter.get_remaining("1.2.3.4") == 5


class TestRedisManager:
    @pytest.mark.asyncio
    async def test_connect_success_sets_connected(self):
        manager = RedisManager()
        settings = SimpleNamespace(redis_url="redis://localhost:6379/0", redis_password="")

        mock_client = AsyncMock()
        mock_client.ping.return_value = True

        with patch("app.cache.redis_client.aioredis.from_url", return_value=mock_client):
            await manager.connect(settings)

        assert manager.is_connected is True
        assert manager.client is mock_client
        assert mock_client.ping.await_count == 1

    @pytest.mark.asyncio
    async def test_connect_failure_resets_state_and_raises(self):
        manager = RedisManager()
        settings = SimpleNamespace(redis_url="redis://localhost:6379/0", redis_password="")

        with patch("app.cache.redis_client.aioredis.from_url", side_effect=RuntimeError("down")):
            with pytest.raises(RuntimeError):
                await manager.connect(settings)

        assert manager.is_connected is False
        assert manager.client is None

    @pytest.mark.asyncio
    async def test_disconnect_clears_client(self):
        manager = RedisManager()
        manager._client = AsyncMock()
        manager._connected = True

        await manager.disconnect()

        assert manager.is_connected is False
        assert manager.client is None

    @pytest.mark.asyncio
    async def test_disconnect_handles_client_close_error(self):
        manager = RedisManager()
        manager._client = AsyncMock()
        manager._connected = True
        manager._client.aclose.side_effect = RuntimeError("close failed")

        await manager.disconnect()

        assert manager.is_connected is False
        assert manager.client is None

    @pytest.mark.asyncio
    async def test_health_check_behaviors(self):
        manager = RedisManager()
        assert await manager.health_check() is False

        manager._client = AsyncMock()
        manager._client.ping.return_value = True
        assert await manager.health_check() is True

        manager._client.ping.side_effect = RuntimeError("unreachable")
        assert await manager.health_check() is False
        assert manager.is_connected is False


class TestCacheNodes:
    @pytest.mark.asyncio
    async def test_cache_check_node_with_no_problems_returns_defaults(self):
        result = await cache_check_node({"problems": []})
        assert result == {"cache_hits": {}, "cached_count": 0}

    @pytest.mark.asyncio
    async def test_cache_check_node_tracks_hits_and_marks_problems(self):
        state = {
            "problems": [
                {"id": 1, "content": "x + 1"},
                {"id": 2, "content": "x + 2"},
            ]
        }

        cache_instance = AsyncMock()
        cache_instance.get = AsyncMock(
            side_effect=[
                {"steps": [{"step": 1}], "final_answer": "2", "confidence": 0.9},
                None,
            ]
        )

        with patch("app.agent.nodes.cache_node.PromptCache", return_value=cache_instance):
            result = await cache_check_node(state)

        assert result["cached_count"] == 1
        assert 1 in result["cache_hits"]
        assert result["problems"][0]["cache_hit"] is True
        assert result["problems"][1].get("cache_hit") is None

    @pytest.mark.asyncio
    async def test_cache_check_node_handles_cache_errors(self):
        state = {"problems": [{"id": 1, "content": "x + 1"}]}

        cache_instance = AsyncMock()
        cache_instance.get = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("app.agent.nodes.cache_node.PromptCache", return_value=cache_instance):
            result = await cache_check_node(state)

        assert result["cached_count"] == 0
        assert result["cache_hits"] == {}

    @pytest.mark.asyncio
    async def test_cache_store_node_stores_only_valid_new_results(self):
        state = {
            "problems": [
                {"id": 1, "content": "x + 1"},
                {"id": 2, "content": "x + 2"},
                {"id": 3, "content": "x + 3"},
                {"id": 4, "content": "x + 4"},
            ],
            "final_results": [
                {
                    "problem_id": 1,
                    "error": None,
                    "confidence": 0.9,
                    "steps": [],
                    "final_answer": "ok",
                    "tool_trace": {"cache_hit": True},
                },
                {
                    "problem_id": 2,
                    "error": "solver failed",
                    "confidence": 0.9,
                    "steps": [],
                    "final_answer": "",
                    "tool_trace": {"cache_hit": False},
                },
                {
                    "problem_id": 3,
                    "error": None,
                    "confidence": 0.4,
                    "steps": [],
                    "final_answer": "low",
                    "tool_trace": {"cache_hit": False},
                },
                {
                    "problem_id": 4,
                    "error": None,
                    "confidence": 0.95,
                    "steps": [{"step": 1}],
                    "final_answer": "good",
                    "tool_trace": {"cache_hit": False},
                },
            ],
        }

        cache_instance = AsyncMock()
        cache_instance.set = AsyncMock(return_value=True)

        with patch("app.agent.nodes.cache_node.PromptCache", return_value=cache_instance):
            result = await cache_store_node(state)

        assert result == {}
        assert cache_instance.set.await_count == 1
        args, _ = cache_instance.set.await_args
        assert args[0] == "x + 4"
        assert args[1]["final_answer"] == "good"

    @pytest.mark.asyncio
    async def test_cache_store_node_noop_without_results(self):
        state = {"problems": [{"id": 1, "content": "x + 1"}], "final_results": []}

        with patch("app.agent.nodes.cache_node.PromptCache") as mock_cache:
            result = await cache_store_node(state)

        assert result == {}
        mock_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_store_node_skips_when_problem_not_found(self):
        state = {
            "problems": [{"id": 1, "content": "x + 1"}],
            "final_results": [
                {
                    "problem_id": 99,
                    "error": None,
                    "confidence": 0.9,
                    "steps": [{"step": 1}],
                    "final_answer": "ok",
                    "tool_trace": {"cache_hit": False},
                }
            ],
        }

        cache_instance = AsyncMock()
        cache_instance.set = AsyncMock(return_value=True)

        with patch("app.agent.nodes.cache_node.PromptCache", return_value=cache_instance):
            result = await cache_store_node(state)

        assert result == {}
        cache_instance.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_store_node_logs_warning_when_cache_set_fails(self):
        state = {
            "problems": [{"id": 1, "content": "x + 1"}],
            "final_results": [
                {
                    "problem_id": 1,
                    "error": None,
                    "confidence": 0.9,
                    "steps": [{"step": 1}],
                    "final_answer": "ok",
                    "tool_trace": {"cache_hit": False},
                }
            ],
        }

        cache_instance = AsyncMock()
        cache_instance.set = AsyncMock(return_value=False)

        with patch("app.agent.nodes.cache_node.PromptCache", return_value=cache_instance), patch(
            "app.agent.nodes.cache_node.logger.warning"
        ) as mock_warning:
            result = await cache_store_node(state)

        assert result == {}
        assert cache_instance.set.await_count == 1
        assert mock_warning.called
