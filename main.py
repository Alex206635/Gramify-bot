import logging
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from keep_alive import keep_alive

# Ativar o servidor web para manter o bot ativo
keep_alive()

# Configuração de log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Escopo de acesso para Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Autenticação com Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Gramify Emails").sheet1

# Lista para armazenar usuários que já enviaram e-mail
usuarios_registrados = set()

# Função de início
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Olá! Envie seu e-mail para participar do sorteio.")

# Função para receber e salvar o e-mail
def salvar_email(update: Update, context: CallbackContext):
    user = update.message.from_user
    email = update.message.text.strip()
    
    # Para evitar erro caso username seja None
    username = user.username if user.username else str(user.id)
    
    if username in usuarios_registrados:
        update.message.reply_text("⚠️ Você já enviou seu e-mail.")
        return
    
    # Validação simples de e-mail
    if "@" in email and "." in email:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        full_name = user.full_name if user.full_name else user.first_name
        spreadsheet.append_row([full_name, "@" + username if user.username else username, email, agora])
        usuarios_registrados.add(username)
        update.message.reply_text("✅ E-mail cadastrado com sucesso! Boa sorte!")
    else:
        update.message.reply_text("❌ Por favor, envie um e-mail válido.")

def main():
    updater = Updater("7671962811:AAH2HTkKPo7M3m2LLezx-WSC8-3p4UqDrco", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, salvar_email))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
