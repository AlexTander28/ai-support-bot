from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from app.models import DecisionType, SupportDecision, SupportStats


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    category TEXT NOT NULL,
    confidence REAL NOT NULL,
    decision TEXT NOT NULL,
    answer TEXT,
    source TEXT,
    reason TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS handoffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE REFERENCES messages(id),
    status TEXT NOT NULL DEFAULT 'open',
    manager_comment TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_decision ON messages(decision);
CREATE INDEX IF NOT EXISTS idx_messages_category ON messages(category);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as connection:
            await connection.executescript(SCHEMA)
            await connection.commit()

    async def log_decision(self, user_id: int, decision: SupportDecision) -> int:
        created_at = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self.path) as connection:
            cursor = await connection.execute(
                """INSERT INTO messages
                (user_id, question, category, confidence, decision, answer, source, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id, decision.question, decision.category.value,
                    decision.confidence, decision.decision.value, decision.answer,
                    decision.source, decision.reason, created_at,
                ),
            )
            message_id = int(cursor.lastrowid)
            if decision.decision is DecisionType.HANDOFF:
                await connection.execute(
                    "INSERT INTO handoffs (message_id, created_at) VALUES (?, ?)",
                    (message_id, created_at),
                )
            await connection.commit()
        return message_id

    async def get_stats(self) -> SupportStats:
        async with aiosqlite.connect(self.path) as connection:
            total_row = await (await connection.execute("SELECT COUNT(*) FROM messages")).fetchone()
            decision_rows = await (await connection.execute(
                "SELECT decision, COUNT(*) FROM messages GROUP BY decision"
            )).fetchall()
            category_rows = await (await connection.execute(
                "SELECT category, COUNT(*) FROM messages GROUP BY category"
            )).fetchall()
        by_decision = {item.value: 0 for item in DecisionType}
        by_decision.update({name: count for name, count in decision_rows})
        return SupportStats(
            total=int(total_row[0]),
            by_decision=by_decision,
            by_category={name: count for name, count in category_rows},
        )

    async def list_open_handoffs(self, limit: int = 10) -> list[tuple]:
        async with aiosqlite.connect(self.path) as connection:
            cursor = await connection.execute(
                """SELECT h.id, m.user_id, m.question, m.category, m.confidence, m.reason
                FROM handoffs h JOIN messages m ON m.id = h.message_id
                WHERE h.status = 'open' ORDER BY h.id DESC LIMIT ?""",
                (limit,),
            )
            return await cursor.fetchall()

    async def resolve_handoff(self, handoff_id: int, manager_comment: str) -> bool:
        resolved_at = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self.path) as connection:
            cursor = await connection.execute(
                """UPDATE handoffs
                SET status = 'resolved', manager_comment = ?, resolved_at = ?
                WHERE id = ? AND status = 'open'""",
                (manager_comment, resolved_at, handoff_id),
            )
            await connection.commit()
            return cursor.rowcount == 1
