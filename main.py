"""Точка входа."""
import logging
from app.bot import create_application
from app.config import get_settings

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    try:
        app = create_application(get_settings())
    except ValueError as error:
        logging.error("Ошибка настройки: %s", error)
        return
    logging.info("Бот запущен и ожидает сообщения")
    app.run_polling()

if __name__ == "__main__":
    main()

