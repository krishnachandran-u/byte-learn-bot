import asyncio
import logging
import sys
from dotenv import load_dotenv
from os import getenv

load_dotenv()

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

import firebase_admin
from firebase_admin import credentials, firestore, db
from firebase_admin import firestore
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

data = {
    'name': 'adharsh',
}

doc_ref = db.collection('test_collection').document()

TOKEN = getenv('TOKEN')

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
"""Welcome! I'm ByteLearn Bot, a learning bot that delivers daily knowledge bites.
Want to learn something new? Just tell me a topic, and I'll send you interesting articles, videos, or other resources to get you started.
Ready to explore? Let's go!

/slots - Get a list of all slots
/newslot - Create a new slot
/editslot - Edit a slot
/deleteslot - Delete a slot
""")

@dp.message(Command('slots'))
async def command_slots_handler(message: Message) -> None:
    await message.answer("Here are the available slots")
    

async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == '__main__':
    doc_ref.set(data)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())