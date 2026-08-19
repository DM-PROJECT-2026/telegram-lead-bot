"""Логика диалога с пользователем."""
import logging
import re
import sqlite3
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from app.config import DATABASE_PATH, Settings
from app.database import save_lead
from app.keyboards import confirmation_keyboard

logger = logging.getLogger(__name__)
NAME, PHONE, COUNTRY, COMMENT, CONFIRMATION = range(5)
PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{5,30}$")

def valid_text(text: str) -> bool:
    return bool(text.strip()) and len(text.strip()) <= 500

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Здравствуйте! Я помогу оставить заявку.\n\nКак вас зовут?")
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

async def unexpected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Пожалуйста, отправьте ответ обычным текстом или /cancel.")
    return ConversationHandler.END
