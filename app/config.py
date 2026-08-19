"""Загрузка настроек из .env."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "leads.db"

@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_chat_id: int

def get_settings() -> Settings:
    load_dotenv(PROJECT_DIR / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not token:
        raise ValueError("Не найден BOT_TOKEN. Создайте .env по образцу .env.example.")
    try:
        return Settings(token, int(admin_id))
    except ValueError as error:
        raise ValueError("ADMIN_CHAT_ID должен быть числовым Telegram ID.") from error

