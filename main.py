import logging
import os
import pandas as pd
import platform

import config

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler

TELEGRAM_TOKEN = '7543065788:AAHUAEP6qAXokUoCdIZZtx6Q5E5Mo_AZeFA'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

iccid_ip_map = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in config.users:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Бот для проверки доступности сим карты.\n\n"
                                            "Для проверки сим карты отправьте номер указанный на боковой части карты рядом со штрих кодом. Номер не должен содержать пробелов. "
                                            "Только цифры отправленные подряд. \n\n Для карты на картинке корректный запрос на проверку номера будет следующий: 89701201469007113583\n"
                                            "\n Возможные ответы:\n 1. Симкарта доступна ✅\n2. Симкарта недоступна ❌\n3. Указан неверный номер\n\n"
                                            "В случае если ответ не получен, повторите запрос повторно. Если симкарта не доступна, возможно она установлена не корректно. Повторите запрос после того как карта будет установлена корректно")
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('intro.jpeg', 'rb'))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Вы не можете использовать бота. Обратитесь к администратору.")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = get_ip_by_number(update.message.text)

    if ip is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Указан нверный номер. Повторите снова")
        return
    else:
        result = ping_ip(ip)
        if (result):
            await send_result(update, context, "Симкарта " + update.message.text + " доступна ✅")
        else:
            await send_result(update, context, "Симкарта " + update.message.text + " недоступна ❌")


async def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE, resultText):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)
    except Exception as e:
        print("Retry send message")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)


def get_ip_by_number(number):
    return iccid_ip_map.get(number)


def ping_ip(ip):
    for i in range(3):
        if try_ping_ip(ip):
            return True
    return False


def try_ping_ip(ip):
    response = 0
    if platform.system() == 'Windows':
        response = os.system("ping -n 1 " + ip)
    else:
        response = os.system("ping -c 1 " + ip)

    if response == 0:
        return True
    else:
        return False


def parse_excel(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path, dtype=str)

    # Ensure the required columns exist
    if not {'ICCID', 'IP'}.issubset(df.columns):
        raise ValueError("Missing required columns: ICCID and IP")

    # Create a dictionary mapping ICCID to IP
    iccid_ip_map = dict(zip(df['ICCID'], df['IP']))

    return iccid_ip_map


if __name__ == '__main__':

    iccid_ip_map = parse_excel('iccid_ip.xlsx')

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    textHandler = MessageHandler(filters.Chat(config.users), text_handler)
    application.add_handler(textHandler)

    try:
        application.run_polling()
    except Exception as e:
        print("Trying to start one more time")
        application.run_polling()
