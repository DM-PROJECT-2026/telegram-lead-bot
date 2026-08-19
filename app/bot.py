"""Сборка Telegram-приложения."""
import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters
from app.config import DATABASE_PATH, Settings
from app.database import init_database
from app.handlers import NAME, PHONE, COUNTRY, COMMENT, CONFIRMATION, start, name, phone, country, comment, confirm, restart, cancel, show_recent_leads, show_stats, unexpected

logger = logging.getLogger(__name__)

async def error_handler(update: object, context) -> None:
    logger.exception("Необработанная ошибка при обработке %s", update, exc_info=context.error)

def create_application(settings: Settings) -> Application:
    init_database(DATABASE_PATH)
    dialog = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)],
            CONFIRMATION: [
                CallbackQueryHandler(lambda u, c: confirm(u, c, settings), pattern="^confirm$"),
                CallbackQueryHandler(restart, pattern="^restart$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app = Application.builder().token(settings.bot_token).build()
    app.add_handler(dialog)
    app.add_handler(CommandHandler("leads", lambda update, context: show_recent_leads(update, context, settings)))
    app.add_handler(CommandHandler("stats", lambda update, context: show_stats(update, context, settings)))
    app.add_handler(MessageHandler(filters.ALL, unexpected))
    app.add_error_handler(error_handler)
    return app
