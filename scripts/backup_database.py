"""Создаёт безопасную резервную копию SQLite-базы заявок."""

from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import sys


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "leads.db"
BACKUPS_DIR = PROJECT_DIR / "backups"
BACKUPS_TO_KEEP = 14


def main() -> int:
    """Создаёт копию через SQLite API и удаляет устаревшие бэкапы."""
    if not DATABASE_PATH.exists():
        print(f"База не найдена: {DATABASE_PATH}", file=sys.stderr)
        return 1

    BACKUPS_DIR.mkdir(mode=0o700, exist_ok=True)
    try:
        os.chmod(BACKUPS_DIR, 0o700)
    except OSError:
        pass

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUPS_DIR / f"leads_{timestamp}_UTC.db"

    try:
        with sqlite3.connect(DATABASE_PATH) as source, sqlite3.connect(backup_path) as destination:
            source.backup(destination)
        os.chmod(backup_path, 0o600)
    except sqlite3.Error as error:
        backup_path.unlink(missing_ok=True)
        print(f"Не удалось создать резервную копию: {error}", file=sys.stderr)
        return 1

    backups = sorted(BACKUPS_DIR.glob("leads_*_UTC.db"), reverse=True)
    for outdated_backup in backups[BACKUPS_TO_KEEP:]:
        outdated_backup.unlink()

    print(f"Резервная копия создана: {backup_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
