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
    # TODO добавить более подробную инструкцию
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Бот для проверки доступности сим карты. Для начала работы отправьте номер телефона для проверки")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = get_ip_by_number(update.message.text)

    if ip is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Неверный номер. Повторите снова")
        return
    else:
        result = ping_ip(ip)
        if (result):
            await send_result(update, context, "Симкарта доступна ✅")
        else:
            await send_result(update, context, "Симкарта недоступна ❌")


def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE, resultText):
    try:
        context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)
    except Exception as e:
        print("Retry send message")
        context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)

def get_ip_by_number(number):
    return iccid_ip_map.get(number)


def ping_ip(ip):
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

    application.run_polling()
