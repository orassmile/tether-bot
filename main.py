import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


def get_syncra_buy_rate():
    try:
        url = "https://api.syncra.me/v1/public/exchange/rates?apiKey=91b59641-818c-440e-b087-097cd9fc38c7"
        response = requests.get(url)
        data = response.json()
        for rate in data.get("value", []):
            if rate["currencyFrom"] == 643 and rate["currencyTo"] == 10001:
                return round(float(rate["rate"]), 2)
        return "недоступен"
    except Exception as e:
        return f"ошибка ({e})"


def get_rapira_buy_rate():
    try:
        url = "https://api.rapira.net/market/symbol-thumb"
        response = requests.get(url)
        data = response.json()
        for item in data:
            if item.get("symbol") == "USDT/RUB":
                return round(float(item["close"]), 2)
        return "недоступен"
    except Exception as e:
        return f"ошибка ({e})"


def build_course_message():
    syncra = get_syncra_buy_rate()
    rapira = get_rapira_buy_rate()

    try:
        if isinstance(syncra, (int, float)) and isinstance(rapira, (int, float)):
            spread = round(((syncra - rapira) / rapira) * 100, 2)
            spread_str = f"{spread}%"
        else:
            spread_str = "недоступен"
    except Exception as e:
        spread_str = f"ошибка ({e})"

    return f"""Покупка USDT за ₽:
Syncra: {syncra}
Rapira: {rapira}
Спред: {spread_str}"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💵 Курс покупка USDT", callback_data="buy_rate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажмите кнопку ниже, чтобы получить курс:", reply_markup=reply_markup)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in ["refresh", "buy_rate"]:
        message = build_course_message()
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(text=message, reply_markup=reply_markup)



async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = build_course_message()
    keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=message, reply_markup=reply_markup)


async def set_menu(application):
    commands = [
        BotCommand("buy", "Покупка USDT за ₽"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(CommandHandler("buy", buy_command))

    application.post_init = set_menu

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
