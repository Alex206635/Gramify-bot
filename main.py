import logging
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from flask import Flask
import threading
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "Bot Gramefy está ativo!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

GOOGLE_CREDS_JSON = 'credentials.json'
SPREADSHEET_NAME = 'Gramefy Emails'
WORKSHEET_NAME = 'Emails'
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def connect_google_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_JSON, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    return sheet

def email_exists(sheet, email):
    try:
        emails = sheet.col_values(1)
        return email.lower() in [e.lower() for e in emails]
    except Exception as e:
        logger.error(f"Erro ao verificar emails na planilha: {e}")
        return False

def save_email(sheet, email, username, user_id, timestamp):
    try:
        sheet.append_row([email, username, user_id, timestamp])
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar email: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie seu e-mail para participar do sorteio.\n"
        "Eu vou salvar seu e-mail e garantir que não tenha duplicados."
    )

async def salvar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    email = update.message.text.strip()

    if not EMAIL_REGEX.fullmatch(email):
        await update.message.reply_text("❌ E-mail inválido. Por favor, envie um e-mail válido.")
        return

    sheet = context.bot_data.get('sheet')
    if not sheet:
        await update.message.reply_text("⚠️ Erro ao acessar a base de dados, tente mais tarde.")
        return

    if email_exists(sheet, email):
        await update.message.reply_text("⚠️ Esse e-mail já foi enviado antes.")
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    saved = save_email(sheet, email, user.username or user.first_name, user.id, timestamp)
    if saved:
        await update.message.reply_text("✅ E-mail salvo com sucesso! Boa sorte no sorteio!")
    else:
        await update.message.reply_text("⚠️ Ocorreu um erro ao salvar seu e-mail. Tente novamente.")

def main():
    sheet = connect_google_sheet()

    TOKEN = '7671962811:AAH2HTkKPo7M3m2LLezx-WSC8-3p4UqDrco'

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.bot_data['sheet'] = sheet

    app_bot.add_handler(CommandHandler('start', start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), salvar_email))

    threading.Thread(target=run_flask).start()

    app_bot.run_polling()

if __name__ == '__main__':
    main()
