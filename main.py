import os
from dotenv import load_dotenv
from typing import Final
from telegram import Update, error
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes 

load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = "@byte_learn_bot"

async def startCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm a bot that helps you learn.")

def handle_response(text: str) -> str:
    if(text == 'hi'):
        return 'Hello!'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text
    response: str = handle_response(text)
    await update.message.reply_text(response)

if __name__ == "__main__":
    print('starting bot')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Text, handle_message))

    app.add_error_handler(error)

    print('polling')
    app.run_polling(poll_interval=3)