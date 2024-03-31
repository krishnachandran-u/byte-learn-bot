import asyncio
import logging
import sys
from dotenv import load_dotenv
from os import getenv

load_dotenv()

from aiogram import Bot, Dispatcher, Router, types, F, html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.markdown import hbold

import firebase_admin
from firebase_admin import credentials, firestore, db
from firebase_admin import firestore
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

TOKEN = getenv('TOKEN')

form_router = Router() 

dp = Dispatcher()
dp.include_router(form_router)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
"""Welcome! I'm ByteLearn Bot, a learning bot that delivers daily knowledge bites.
Want to learn something new? Just tell me a topic, and I'll send you interesting articles, videos, or other resources to get you started.
Ready to explore? Let's go!

/slots - Get a list of all slots
/viewslot slot_name - View resources in a slot
/newslot - Create a new slot
/editslot - Edit a slot
/deleteslot slot_name - Delete a slot
""")
        
@dp.message(Command('slots'))
async def command_slots_handler(message: Message) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')
    slots = slots_ref.stream()
    reply = ""
    for doc in slots:
        data = doc.to_dict()
        reply += f"{data['name']}\n"  
    await message.answer(f"Here are the available slots:\n{reply}To view the resources in a slot, type /viewslot slot_name")

@dp.message(Command('viewslot'))
async def command_viewslot_handler(message: Message) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    slot_name = message.text.split(' ')[1]

    slots = slots_ref.stream()
    for doc in slots:
        data = doc.to_dict()
        if slot_name == data['name'] :
            reply = ""
            for k, v in data.items():
                reply += (f"{k.capitalize()}: {v}\n") 
            await message.answer(reply)
            return
    await message.answer("Slot not found")

class Form(StatesGroup):
    name = State()
    prompt = State()
    days = State()

@form_router.message(Command('newslot'))
async def command_newslot_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    await state.set_state(Form.name)
    await message.answer("Enter the name of the slot:")

@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.prompt)
    await message.answer("Enter the prompt for the slot:")

@form_router.message(Form.prompt)
async def process_prompt(message: Message, state: FSMContext) -> None:
    await state.update_data(prompt=message.text)
    await state.set_state(Form.days)
    await message.answer("Enter the number of days for the slot:")

@form_router.message(Form.days)
async def process_days(message: Message, state: FSMContext) -> None:
    await state.update_data(days=message.text)

    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    slots_ref.add({
        'name': (await state.get_data())['name'],
        'prompt': (await state.get_data())['prompt'],
        'days': (await state.get_data())['days']
    })

    await message.answer("Slot created!")

@dp.message(Command('deleteslot'))
async def command_deleteslot_handler(message: Message) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    slot_name = message.text.split(' ')[1]

    slots = slots_ref.stream()

    for doc in slots:
        data = doc.to_dict()
        if slot_name == data['name'] :
            doc_ref = slots_ref.document(doc.id)
            doc_ref.delete()
            await message.answer(f"Slot {slot_name} deleted")
            return
    await message.answer("Slot not found")

async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())