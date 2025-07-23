from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")

def get_syncra_course():
    url = "https://api.syncra.me/v1/public/exchange/rates?apiKey=91b59641-818c-440e-b087-097cd9fc38c7"
    try:
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
    url = "https://api.rapira.net/market/symbol-thumb"
    try:
        response = requests.get(url)
        data = response.json()

        for item in data:
            if item.get("symbol") == "USDT/RUB":
                return f"📊 Rapier:\nКурс USDT/RUB: {item['close']}"
        return "❌ Не найден курс USDT/RUB от Rapier."
    except Exception as e:
        return f"⚠️ Ошибка при получении курса Rapier: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💸 Курс Syncra", callback_data="syncra")],
        [InlineKeyboardButton("📊 Курс Rapier", callback_data="rapier")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите источник курса:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
