"""Логика диалога с пользователем."""
from datetime import datetime, timezone
import logging
import re
import sqlite3
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from app.config import DATABASE_PATH, Settings
from app.database import get_leads_count, get_recent_leads, save_lead
from app.keyboards import confirmation_keyboard

logger = logging.getLogger(__name__)
NAME, PHONE, COUNTRY, COMMENT, CONFIRMATION = range(5)
PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{5,30}$")

def valid_text(text: str) -> bool:
    return bool(text.strip()) and len(text.strip()) <= 500

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Здравствуйте! Я помогу оставить заявку.\n\n"
        "Продолжая заполнение, вы соглашаетесь на обработку указанных данных "
        "для связи по заявке. Подробнее: /privacy\n\nКак вас зовут?"
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not valid_text(value):
        await update.message.reply_text("Введите имя текстом (до 500 символов).")
        return NAME
    context.user_data["name"] = value
    await update.message.reply_text("Введите номер телефона.")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not PHONE_PATTERN.fullmatch(value):
        await update.message.reply_text("Введите номер: 5–30 символов, цифры, +, скобки или дефис.")
        return PHONE
    context.user_data["phone"] = value
    await update.message.reply_text("Из какой вы страны?")
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not valid_text(value):
        await update.message.reply_text("Введите страну текстом (до 500 символов).")
        return COUNTRY
    context.user_data["country"] = value
    await update.message.reply_text("Оставьте комментарий или кратко опишите ваш запрос.")
    return COMMENT

async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not valid_text(value):
        await update.message.reply_text("Введите комментарий текстом (до 500 символов).")
        return COMMENT
    context.user_data["comment"] = value
    await summary(update, context)
    return CONFIRMATION

def lead_text(lead: dict) -> str:
    return (
        f"<b>Имя:</b> {escape(lead['name'])}\n"
        f"<b>Телефон:</b> {escape(lead['phone'])}\n"
        f"<b>Страна:</b> {escape(lead['country'])}\n"
        f"<b>Комментарий:</b> {escape(lead['comment'])}"
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Проверьте заявку:</b>\n\n" + lead_text(context.user_data),
        parse_mode=ParseMode.HTML, reply_markup=confirmation_keyboard()
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings) -> int:
    query = update.callback_query
    await query.answer()
    lead, user = context.user_data, update.effective_user
    if not user or not all(key in lead for key in ("name", "phone", "country", "comment")):
        await query.edit_message_text("Данные заявки не найдены. Начните заново: /start")
        return ConversationHandler.END
    try:
        created_at = save_lead(DATABASE_PATH, telegram_user_id=user.id, username=user.username,
                               name=lead["name"], phone=lead["phone"],
                               country=lead["country"], comment=lead["comment"])
    except sqlite3.Error:
        logger.exception("Не удалось сохранить заявку пользователя %s", user.id)
        await query.edit_message_text("Не удалось сохранить заявку. Попробуйте позже.")
        return ConversationHandler.END

    admin_text = (
        "<b>Новая заявка</b>\n\n" + lead_text(lead) +
        f"\n\n<b>Telegram ID:</b> {user.id}"
        f"\n<b>Username:</b> {('@' + escape(user.username)) if user.username else 'не указан'}"
        f"\n<b>Создана (UTC):</b> {created_at}"
    )
    try:
        await context.bot.send_message(settings.admin_chat_id, admin_text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Заявка сохранена, но уведомление администратору не отправлено")
    logger.info("Заявка пользователя %s сохранена", user.id)
    context.user_data.clear()
    await query.edit_message_text("Спасибо! Ваша заявка успешно отправлена.")
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("Начнём заново. Как вас зовут?")
    return NAME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Заполнение отменено. Чтобы начать снова, отправьте /start.")
    return ConversationHandler.END


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает пользователю краткую политику обработки данных."""
    await update.message.reply_text(
        "<b>Обработка данных</b>\n\n"
        "Бот получает имя, телефон, страну и комментарий только для обработки вашей "
        "заявки и связи с вами. Данные хранятся в защищённой базе владельца бота и "
        "не передаются третьим лицам без законного основания.\n\n"
        "Чтобы отозвать заявку или задать вопрос о данных, обратитесь к владельцу бота.",
        parse_mode=ParseMode.HTML,
    )

async def unexpected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте ответ обычным текстом или /cancel.")
    return ConversationHandler.END


def _is_admin(update: Update, settings: Settings) -> bool:
    user = update.effective_user
    return bool(user and user.id == settings.admin_chat_id)


async def show_recent_leads(
    update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings
) -> None:
    """Показывает администратору последние десять заявок."""
    if not _is_admin(update, settings):
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    try:
        leads = get_recent_leads(DATABASE_PATH)
    except sqlite3.Error:
        logger.exception("Не удалось получить список заявок")
        await update.message.reply_text("Не удалось получить заявки. Попробуйте позже.")
        return

    if not leads:
        await update.message.reply_text("Подтверждённых заявок пока нет.")
        return

    lines = ["<b>Последние заявки:</b>"]
    for lead in leads:
        comment = str(lead["comment"])
        short_comment = comment[:120] + ("…" if len(comment) > 120 else "")
        lines.append(
            f"\n<b>#{lead['id']} — {escape(str(lead['name']))}</b>\n"
            f"{escape(str(lead['phone']))}, {escape(str(lead['country']))}\n"
            f"{escape(short_comment)}\n"
            f"<i>{escape(str(lead['created_at']))}</i>"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def show_stats(
    update: Update, context: ContextTypes.DEFAULT_TYPE, settings: Settings
) -> None:
    """Показывает администратору количество заявок за всё время и за сегодня."""
    if not _is_admin(update, settings):
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    today_utc = datetime.now(timezone.utc).date().isoformat()
    try:
        total = get_leads_count(DATABASE_PATH)
        today = get_leads_count(DATABASE_PATH, since_utc=today_utc)
    except sqlite3.Error:
        logger.exception("Не удалось получить статистику заявок")
        await update.message.reply_text("Не удалось получить статистику. Попробуйте позже.")
        return

    await update.message.reply_text(
        f"<b>Статистика заявок</b>\n\nВсего: {total}\nСегодня (UTC): {today}",
        parse_mode=ParseMode.HTML,
    )
