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

if __name__ == "__main__":
    print('starting bot')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", startCommand))

    app.add_error_handler(error)

    print('polling')
    app.run_polling(poll_interval=3)