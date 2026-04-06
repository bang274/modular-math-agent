"""
Database Manager — SQLite with aiosqlite for async operations.

Person 4 owns this file.
Handles: connection lifecycle, table creation, migrations.
"""

import os
from typing import Optional

import aiosqlite

from app.telemetry.logger import logger


class DatabaseManager:
    """Manages SQLite database lifecycle."""

    def __init__(self):
        self._db: Optional[aiosqlite.Connection] = None
        self._db_path: str = ""

    @property
    def is_connected(self) -> bool:
        return self._db is not None

    async def init(self, settings) -> None:
        """Initialize database and create tables."""
        # Extract path from URL (sqlite+aiosqlite:///./data/math_agent.db)
        db_url = settings.database_url
        self._db_path = db_url.replace("sqlite+aiosqlite:///", "")

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)

        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row

        # Enable WAL mode for better concurrent reads
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")

        await self._create_tables()
        logger.info(f"[DB] Initialized at {self._db_path}")

    async def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processing',
                upload_type TEXT,
                total_problems INTEGER DEFAULT 0,
                solved_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                cached_count INTEGER DEFAULT 0,
                total_latency_ms INTEGER DEFAULT 0,
                raw_text TEXT,
                raw_image_b64 TEXT
            );

            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                original_text TEXT,
                source TEXT DEFAULT 'text',
                difficulty TEXT DEFAULT 'unknown',
                PRIMARY KEY (session_id, id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS solutions (
                session_id TEXT NOT NULL,
                problem_id INTEGER NOT NULL,
                steps_json TEXT,
                final_answer TEXT,
                confidence REAL DEFAULT 0.0,
                solve_route TEXT,
                tools_used TEXT,
                latency_ms INTEGER DEFAULT 0,
                cache_hit BOOLEAN DEFAULT FALSE,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, problem_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_created
                ON sessions(created_at DESC);
        """)
        await self._db.commit()

    async def get_connection(self) -> aiosqlite.Connection:
        """Get the database connection."""
        if not self._db:
            raise RuntimeError("Database not initialized")
        return self._db

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("[DB] Closed")

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if not self._db:
            return False
        try:
            async with self._db.execute("SELECT 1") as cursor:
                await cursor.fetchone()
            return True
        except Exception:
            return False


# Global singleton
db_manager = DatabaseManager()
