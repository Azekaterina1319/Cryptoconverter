import logging
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
import requests

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для состояний диалога
SELECT_BASE_CURRENCY, SELECT_TARGET_CURRENCY, INPUT_AMOUNT = range(3)

# Клавиатуры
currency_keyboard = ReplyKeyboardMarkup([['USD', 'EUR', 'RUB']], resize_keyboard=True)
cancel_keyboard = ReplyKeyboardMarkup([['/cancel']], resize_keyboard=True)

# Конфигурация
TOKEN = "Ваш токен с Телеграмм"
EXCHANGE_API_KEY = "Ваш API ключ"
API_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/"

# Данные пользователя (временное хранилище)
user_data = {}


async def start(update, context):
    """Начало работы, предлагает выбрать исходную валюту"""
    await update.message.reply_text(
        "💰 *Конвертер валют* 💰\n"
        "Выберите исходную валюту:",
        reply_markup=currency_keyboard,
        parse_mode="Markdown"
    )
    return SELECT_BASE_CURRENCY


async def select_base_currency(update, context):
    """Обработка выбора исходной валюты"""
    user_data['base_currency'] = update.message.text
    await update.message.reply_text(
        "Теперь выберите валюту для конвертации:",
        reply_markup=currency_keyboard
    )
    return SELECT_TARGET_CURRENCY


async def select_target_currency(update, context):
    """Обработка выбора целевой валюты"""
    user_data['target_currency'] = update.message.text
    await update.message.reply_text(
        "Введите сумму для конвертации:",
        reply_markup=cancel_keyboard
    )
    return INPUT_AMOUNT


async def convert_amount(update, context):
    """Конвертация суммы"""
    try:
        amount = float(update.message.text)
        base = user_data['base_currency']
        target = user_data['target_currency']

        response = requests.get(f"{API_URL}{base}/{target}/{amount}")
        data = response.json()

        if data['result'] == 'success':
            await update.message.reply_text(
                f"💱 Результат:\n"
                f"{amount} {base} = {data['conversion_result']} {target}\n"
                f"Курс: 1 {base} = {data['conversion_rate']} {target}",
                reply_markup=currency_keyboard
            )
        else:
            await update.message.reply_text("Ошибка при конвертации")

        return SELECT_BASE_CURRENCY
    except ValueError:
        await update.message.reply_text("Введите корректное число!")
        return INPUT_AMOUNT


async def cancel(update, context):
    """Отмена операции"""
    await update.message.reply_text(
        "Операция отменена. Начните заново /start",
        reply_markup=currency_keyboard
    )
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_BASE_CURRENCY: [MessageHandler(filters.Regex('^(USD|EUR|RUB)$'), select_base_currency)],
            SELECT_TARGET_CURRENCY: [MessageHandler(filters.Regex('^(USD|EUR|RUB)$'), select_target_currency)],
            INPUT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, convert_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
