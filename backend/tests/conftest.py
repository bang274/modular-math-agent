"""
Test Configuration & Fixtures.

Shared fixtures for all tests — mock Redis, mock LLM, test client.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.config import Settings


@pytest.fixture
def settings():
    """Test settings with dummy values."""
    return Settings(
        groq_api_key="test-key",
        wolfram_alpha_app_id="test-wolfram",
        tavily_api_key="test-tavily",
        redis_url="redis://localhost:6379/0",
        database_url="sqlite+aiosqlite:///./test_data/test.db",
        langchain_tracing_v2=False,
        app_debug=True,
    )


@pytest.fixture
def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app):
    """Async test client for testing async endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable responses."""
    mock = AsyncMock()
    mock.ainvoke.return_value = MagicMock(
        content='{"problems": [{"id": 1, "content": "x^2 + 1 = 0"}]}'
    )
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.ping.return_value = True
    return mock
