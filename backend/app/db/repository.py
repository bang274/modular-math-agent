"""
Database Repository — CRUD operations.

Person 4 owns this file.
"""

import json
from typing import Any, Dict, List, Optional

from app.db.database import db_manager
from app.telemetry.logger import logger


class SessionRepository:
    """CRUD operations for solve sessions."""

    async def save_session(
        self,
        session_id: str,
        status: str,
        upload_type: str,
        total_problems: int,
        solved_count: int = 0,
        failed_count: int = 0,
        cached_count: int = 0,
        total_latency_ms: int = 0,
        raw_text: Optional[str] = None,
    ) -> bool:
        """Save or update a session record."""
        try:
            db = await db_manager.get_connection()
            await db.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, status, upload_type, total_problems, solved_count,
                 failed_count, cached_count, total_latency_ms, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, status, upload_type, total_problems,
                 solved_count, failed_count, cached_count, total_latency_ms, raw_text),
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"[DB] Error saving session: {e}")
            return False

    async def save_solution(
        self,
        session_id: str,
        problem_id: int,
        content: str,
        result: Dict[str, Any],
    ) -> bool:
        """Save a problem and its solution."""
        try:
            db = await db_manager.get_connection()

            # Save problem
            await db.execute(
                """
                INSERT OR REPLACE INTO problems (id, session_id, content, difficulty)
                VALUES (?, ?, ?, ?)
                """,
                (problem_id, session_id, content,
                 result.get("difficulty", "unknown")),
            )

            # Save solution
            await db.execute(
                """
                INSERT OR REPLACE INTO solutions
                (session_id, problem_id, steps_json, final_answer, confidence,
                 solve_route, tools_used, latency_ms, cache_hit, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    problem_id,
                    json.dumps(result.get("steps", []), ensure_ascii=False),
                    result.get("final_answer", ""),
                    result.get("confidence", 0.0),
                    result.get("tool_trace", {}).get("route", ""),
                    json.dumps(result.get("tool_trace", {}).get("tools_used", [])),
                    result.get("tool_trace", {}).get("latency_ms", 0),
                    result.get("tool_trace", {}).get("cache_hit", False),
                    result.get("error"),
                ),
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"[DB] Error saving solution: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID with all its solutions."""
        try:
            db = await db_manager.get_connection()

            async with db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                session = dict(row)

            # Get solutions
            async with db.execute(
                """
                SELECT p.content, s.*
                FROM solutions s
                JOIN problems p ON p.session_id = s.session_id AND p.id = s.problem_id
                WHERE s.session_id = ?
                ORDER BY s.problem_id
                """,
                (session_id,),
            ) as cursor:
                solutions = [dict(row) async for row in cursor]

            session["solutions"] = solutions
            return session

        except Exception as e:
            logger.error(f"[DB] Error getting session: {e}")
            return None

    async def get_history(
        self, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated session history."""
        try:
            db = await db_manager.get_connection()
            offset = (page - 1) * page_size

            # Get total count
            async with db.execute("SELECT COUNT(*) FROM sessions") as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0

            # Get sessions
            async with db.execute(
                """
                SELECT s.id, s.created_at, s.status, s.total_problems,
                       s.solved_count, s.total_latency_ms,
                       (SELECT content FROM problems WHERE session_id = s.id LIMIT 1) as preview
                FROM sessions s
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset),
            ) as cursor:
                sessions = [dict(row) async for row in cursor]

            return {
                "sessions": sessions,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"[DB] Error getting history: {e}")
            return {"sessions": [], "total": 0, "page": page, "page_size": page_size}


# Global instance
session_repo = SessionRepository()
