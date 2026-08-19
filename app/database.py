"""Работа с SQLite."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

def init_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                country TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def save_lead(path: Path, *, telegram_user_id: int, username: str | None,
              name: str, phone: str, country: str, comment: str) -> str:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(path) as conn:
        conn.execute("""
            INSERT INTO leads
            (telegram_user_id, username, name, phone, country, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (telegram_user_id, username, name, phone, country, comment, created_at))
    return created_at

