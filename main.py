import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")


def get_syncra_course():
    try:
        url = "https://api.syncra.me/v1/public/exchange/rates?apiKey=91b59641-818c-440e-b087-097cd9fc38c7"
        response = requests.get(url)
        data = response.json()
        rates = data.get("value", [])
        buy_rate = sell_rate = None
        for rate in rates:
            if rate["currencyFrom"] == 643 and rate["currencyTo"] == 10001:
                buy_rate = rate["rate"]
            elif rate["currencyFrom"] == 10001 and rate["currencyTo"] == 643:
                sell_rate = rate["rate"]
        if buy_rate and sell_rate:
            return f"💸 Syncra:\nПокупка USDT за ₽: {buy_rate}\nПродажа USDT за ₽: {sell_rate}"
        else:
            return "❌ Не удалось получить курс от Syncra."
    except Exception as e:
        return f"⚠️ Ошибка при получении курса Syncra: {e}"


def get_rapier_course():
    try:
        url = "https://api.rapira.net/market/symbol-thumb"
        response = requests.get(url)
        data = response.json()
        for item in data:
            if item.get("symbol") == "USDT/RUB":
                return f"📊 Rapier:\nКурс USDT/RUB: {item['close']}"
        return "❌ Курс USDT/RUB от Rapier не найден."
    except Exception as e:
        return f"⚠️ Ошибка при получении курса Rapier: {e}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💸 Курс Syncra", callback_data="syncra")],
        [InlineKeyboardButton("📊 Курс Rapier", callback_data="rapier")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите источник курса:", reply_markup=reply_markup)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "syncra":
        text = get_syncra_course()
    elif query.data == "rapier":
        text = get_rapier_course()
    else:
        text = "Неизвестная команда."

    await query.edit_message_text(text=text)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
