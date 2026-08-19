"""Отправляет администратору уведомление о критическом сбое службы бота."""

from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from app.config import get_settings  # noqa: E402


def main() -> int:
    service_name = sys.argv[1] if len(sys.argv) > 1 else "telegram-lead-bot.service"
    settings = get_settings()
    payload = urlencode(
        {
            "chat_id": settings.admin_chat_id,
            "text": f"⚠️ Служба бота остановлена: {service_name}. Проверьте сервер.",
        }
    ).encode()
    request = Request(
        f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"Telegram вернул статус {response.status}")
    except Exception as error:
        print(f"Не удалось отправить уведомление о сбое: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
