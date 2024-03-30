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

TOKEN = getenv('TOKEN')
USERID = 0

dp = Dispatcher()

slots_ref = db.collection('users').document(str(USERID)).collection('slots')

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    global USERID
    USERID = message.from_user.id
    await message.answer(
"""Welcome! I'm ByteLearn Bot, a learning bot that delivers daily knowledge bites.
Want to learn something new? Just tell me a topic, and I'll send you interesting articles, videos, or other resources to get you started.
Ready to explore? Let's go!

/slots - Get a list of all slots
/viewslot slot_name - View resources in a slot
/newslot - Create a new slot
/editslot - Edit a slot
/deleteslot - Delete a slot
""")
        
@dp.message(Command('slots'))
async def command_slots_handler(message: Message) -> None:
    global USERID
    global slots_ref

    slots_ref = db.collection('users').document(str(USERID)).collection('slots')
    slots = slots_ref.stream()
    reply = ""
    for doc in slots:
        data = doc.to_dict()
        reply += f"{data['name']}\n"  
    await message.answer(f"Here are the available slots:\n{reply}To view the resources in a slot, type /viewslot slot_name")

@dp.message(Command('viewslot'))
async def command_viewslot_handler(message: Message) -> None:
    global USERID
    global slots_ref

    slot_name = message.text.split(' ')[1]

    slots = slots_ref.stream()
    for doc in slots:
        data = doc.to_dict()
        if slot_name == data['name'] :
            reply = ""
            for k, v in data.items():
                reply += (f"{k}: {v}\n") 
            await message.answer(reply)
            return
    else :
        await message.answer("Slot not found")


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())