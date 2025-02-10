import logging
import os
import pandas as pd
import platform


from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler

TELEGRAM_TOKEN = '7543065788:AAHUAEP6qAXokUoCdIZZtx6Q5E5Mo_AZeFA'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

iccid_ip_map = {}
users = []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if users == [] or str(update.effective_user.id) in users:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Бот для проверки доступности SIM.\n\n"
                                            "Для проверки отправьте крайние 6 цифр SIM до последней цифры. "
                                            "\n\nДля карты на картинке корректный запрос на проверку номера будет следующий: 711358\n"
                                            "\n Возможные ответы:\n1. SIM доступна ✅\n2. SIM недоступна ❌\n3. SIM не найдена\n\n"
                                            "В случае если ответ не получен, повторите запрос.")
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('intro.jpeg', 'rb'))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Вы не можете использовать бота. Обратитесь к администратору.")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = get_ip_by_number(update.message.text)

    if ip is None:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="SIM №" + update.message.text + " не найдена, проверьте правильность отправляемого № SIM((Указываем крайние 6 цифр до последней цифры)")
        return
    else:
        result = ping_ip(ip)
        if (result):
            await send_result(update, context, "SIM №" + update.message.text + " доступна ✅")
        else:
            await send_result(update, context, "SIM №" + update.message.text + " недоступна ❌")


async def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE, resultText):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)
    except Exception as e:
        print("Retry send message")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=resultText)


def get_ip_by_number(number):
    return iccid_ip_map.get(number)


def ping_ip(ip):
    for i in range(4):
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
    iccid_ip_map = {iccid[-7:-1]: ip for iccid, ip in zip(df['ICCID'], df['IP'])}

    return iccid_ip_map


def parse_chat_ids(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path, dtype=str)

    # Ensure the required column exists
    if 'Чат ID' not in df.columns:
        raise ValueError("Missing required column: Чат ID")

    # Return the list of chat IDs
    return df['Чат ID'].tolist()


if __name__ == '__main__':

    iccid_ip_map = parse_excel('settings/iccid_ip.xls')
    users = parse_chat_ids('settings/users.xls')

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    textHandler = MessageHandler(filters.TEXT, text_handler)
    application.add_handler(textHandler)

    try:
        application.run_polling()
    except Exception as e:
        print("Trying to start one more time")
        application.run_polling()
