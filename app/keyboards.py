from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить заявку", callback_data="confirm")],
        [InlineKeyboardButton("🔄 Заполнить заново", callback_data="restart")],
    ])

