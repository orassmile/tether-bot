
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")  # API-ключ берём из переменной окружения

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

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💸 Курс Syncra", callback_data='syncra')],
        [InlineKeyboardButton("📊 Курс Rapier", callback_data='rapier')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите источник курса:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'syncra':
        message = get_syncra_course()
    elif query.data == 'rapier':
        message = get_rapier_course()
    else:
        message = "❓ Неизвестная команда."

    query.edit_message_text(text=message)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
