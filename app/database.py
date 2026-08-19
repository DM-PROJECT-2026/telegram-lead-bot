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


def get_recent_leads(path: Path, limit: int = 10) -> list[dict[str, object]]:
    """Возвращает последние заявки для администратора."""
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, phone, country, comment, created_at
            FROM leads
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_leads_count(path: Path, since_utc: str | None = None) -> int:
    """Возвращает общее количество заявок либо число заявок после заданной даты."""
    with sqlite3.connect(path) as conn:
        if since_utc:
            row = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE created_at >= ?", (since_utc,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM leads").fetchone()
    return int(row[0])
