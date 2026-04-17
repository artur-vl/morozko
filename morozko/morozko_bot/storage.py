from __future__ import annotations

import sqlite3
from pathlib import Path


class LeadStorage:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS lead_links (
                    telegram_user_id INTEGER PRIMARY KEY,
                    lead_id INTEGER NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get_lead_id(self, telegram_user_id: int) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT lead_id FROM lead_links WHERE telegram_user_id = ?",
                (telegram_user_id,),
            ).fetchone()
            return int(row[0]) if row else None

    def upsert_lead_id(self, telegram_user_id: int, lead_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lead_links (telegram_user_id, lead_id)
                VALUES (?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    lead_id = excluded.lead_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (telegram_user_id, lead_id),
            )
