"""
Tests for database repository module.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.db.database import DatabaseManager, db_manager
from app.db.repository import SessionRepository


async def _init_db(tmp_path):
    settings = SimpleNamespace(database_url=f"sqlite+aiosqlite:///{tmp_path / 'module4_test.db'}")
    await db_manager.init(settings)


async def _close_db():
    await db_manager.close()


def test_save_and_get_session_with_solution(tmp_path):
    async def scenario():
        await _init_db(tmp_path)
        try:
            repo = SessionRepository()
            session_id = "session-1"

            saved = await repo.save_session(
                session_id=session_id,
                status="completed",
                upload_type="text",
                total_problems=1,
                solved_count=1,
                failed_count=0,
                cached_count=0,
                total_latency_ms=123,
                raw_text="x + 1 = 2",
            )
            assert saved is True

            result = {
                "difficulty": "easy",
                "steps": [{"step": 1, "description": "subtract 1", "latex": "x=1"}],
                "final_answer": "x = 1",
                "confidence": 0.95,
                "tool_trace": {
                    "route": "llm_direct",
                    "tools_used": ["llm"],
                    "latency_ms": 88,
                    "cache_hit": False,
                },
                "error": None,
            }

            solution_saved = await repo.save_solution(
                session_id=session_id,
                problem_id=1,
                content="x + 1 = 2",
                result=result,
            )
            assert solution_saved is True

            session = await repo.get_session(session_id)
            assert session is not None
            assert session["id"] == session_id
            assert session["status"] == "completed"
            assert session["total_problems"] == 1
            assert len(session["solutions"]) == 1

            sol = session["solutions"][0]
            assert sol["problem_id"] == 1
            assert sol["content"] == "x + 1 = 2"
            assert sol["final_answer"] == "x = 1"
            assert sol["solve_route"] == "llm_direct"
            assert sol["error"] is None
        finally:
            await _close_db()

    asyncio.run(scenario())


def test_get_history_pagination(tmp_path):
    async def scenario():
        await _init_db(tmp_path)
        try:
            repo = SessionRepository()

            for idx in range(3):
                await repo.save_session(
                    session_id=f"session-{idx}",
                    status="completed",
                    upload_type="text",
                    total_problems=1,
                    solved_count=1,
                    failed_count=0,
                    cached_count=0,
                    total_latency_ms=10,
                    raw_text=f"q-{idx}",
                )
                await repo.save_solution(
                    session_id=f"session-{idx}",
                    problem_id=1,
                    content=f"problem-{idx}",
                    result={
                        "difficulty": "easy",
                        "steps": [],
                        "final_answer": "ok",
                        "confidence": 0.8,
                        "tool_trace": {
                            "route": "llm_direct",
                            "tools_used": [],
                            "latency_ms": 5,
                            "cache_hit": False,
                        },
                        "error": None,
                    },
                )

            page_1 = await repo.get_history(page=1, page_size=2)
            page_2 = await repo.get_history(page=2, page_size=2)

            assert page_1["total"] == 3
            assert len(page_1["sessions"]) == 2
            assert page_1["page"] == 1

            assert page_2["total"] == 3
            assert len(page_2["sessions"]) == 1
            assert page_2["page"] == 2
        finally:
            await _close_db()

    asyncio.run(scenario())


def test_save_session_returns_false_on_error():
    async def scenario():
        repo = SessionRepository()

        with patch("app.db.repository.db_manager") as mock_db_manager:
            mock_db_manager.get_connection = AsyncMock(side_effect=RuntimeError("db down"))
            ok = await repo.save_session(
                session_id="s",
                status="completed",
                upload_type="text",
                total_problems=1,
            )

        assert ok is False

    asyncio.run(scenario())


def test_save_solution_returns_false_on_error():
    async def scenario():
        repo = SessionRepository()

        with patch("app.db.repository.db_manager") as mock_db_manager:
            mock_db_manager.get_connection = AsyncMock(side_effect=RuntimeError("db down"))
            ok = await repo.save_solution(
                session_id="s",
                problem_id=1,
                content="x",
                result={},
            )

        assert ok is False

    asyncio.run(scenario())


def test_get_session_returns_none_when_missing(tmp_path):
    async def scenario():
        await _init_db(tmp_path)
        try:
            repo = SessionRepository()
            session = await repo.get_session("unknown-session")
            assert session is None
        finally:
            await _close_db()

    asyncio.run(scenario())


def test_database_manager_get_connection_before_init_raises():
    async def scenario():
        manager = DatabaseManager()
        try:
            await manager.get_connection()
            assert False, "Expected RuntimeError when DB is not initialized"
        except RuntimeError as exc:
            assert "Database not initialized" in str(exc)

    asyncio.run(scenario())


def test_database_manager_lifecycle_and_health(tmp_path):
    async def scenario():
        manager = DatabaseManager()
        settings = SimpleNamespace(database_url=f"sqlite+aiosqlite:///{tmp_path / 'db_manager_test.db'}")

        await manager.init(settings)
        assert manager.is_connected is True
        assert await manager.health_check() is True

        await manager.close()
        assert manager.is_connected is False
        assert await manager.health_check() is False

    asyncio.run(scenario())
