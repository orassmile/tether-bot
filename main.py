import os
import requests
import logging
import sqlite3
from contextlib import closing
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# ----------------- ENV -----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Если задан TARGET_CHAT_ID — шлём только туда (канал/группа/личка).
# Если НЕ задан — шлём всем пользователям, которые запускали /start или /buy (храним их в БД).
try:
    TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
except ValueError:
    TARGET_CHAT_ID = 0

DB_PATH = os.getenv("SUBSCRIBERS_DB", "subscribers.db")

# ----------------- БД подписчиков -----------------
def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER PRIMARY KEY
            )
        """)

def add_subscriber(chat_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO subscribers(chat_id) VALUES (?)", (chat_id,))

def get_all_subscribers():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
    return [r[0] for r in rows]

# ----------------- Логика получения курсов -----------------
def get_syncra_buy_rate():
    try:
        url = "https://api.syncra.me/v1/public/exchange/rates?apiKey=91b59641-818c-440e-b087-097cd9fc38c7"
        response = requests.get(url, timeout=10)
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
        response = requests.get(url, timeout=10)
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

# ----------------- UI -----------------
def refresh_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]])

# ----------------- Хэндлеры -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and not TARGET_CHAT_ID:
        add_subscriber(update.effective_chat.id)

    keyboard = [[InlineKeyboardButton("💵 Курс покупка USDT", callback_data="buy_rate")]]
    await update.message.reply_text("Нажмите кнопку ниже, чтобы получить курс:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in ["refresh", "buy_rate"]:
        message = build_course_message()
        await query.message.reply_text(text=message, reply_markup=refresh_keyboard())

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and not TARGET_CHAT_ID:
        add_subscriber(update.effective_chat.id)

    message = build_course_message()
    await update.message.reply_text(text=message, reply_markup=refresh_keyboard())

async def set_menu(application: Application):
    commands = [BotCommand("buy", "Покупка USDT за ₽")]
    await application.bot.set_my_commands(commands)

# ----------------- Автопостинг -----------------
async def push_rates(context: ContextTypes.DEFAULT_TYPE):
    """Каждые 30 минут отправляет курсы:
       - если TARGET_CHAT_ID задан — только туда;
       - иначе — всем из таблицы subscribers.
    """
    try:
        text = build_course_message()

        if TARGET_CHAT_ID:
            await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=text, reply_markup=refresh_keyboard())
            return

        subscribers = get_all_subscribers()
        if not subscribers:
            return

        for chat_id in subscribers:
            try:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=refresh_keyboard())
            except Exception as e:
                logging.warning(f"Не удалось отправить в {chat_id}: {e}")
    except Exception as e:
        logging.exception(f"Auto-broadcast error: {e}")

# ----------------- Запуск -----------------
def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(CommandHandler("buy", buy_command))

    application.post_init = set_menu

    # каждые 30 минут; первый запуск — сразу
    application.job_queue.run_repeating(callback=push_rates, interval=600, first=0)

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
# trigger redeploy
