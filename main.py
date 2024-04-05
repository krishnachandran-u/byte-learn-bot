import asyncio
import logging
import schedule
import sys
import time
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
from aiogram.methods import SendMessage

import firebase_admin
from firebase_admin import credentials, firestore, db
from firebase_admin import firestore
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

GOOGLE_API_KEY = getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro')

db = firestore.client()

TOKEN = getenv('TOKEN')

form_router = Router() 

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
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
/deleteslot slot_name - Delete a slot
/cancel - Cancel the current operation
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
    await message.answer(f"Here are the available slots:\n\n{reply}\nTo view the resources in a slot, type /viewslot slot_name")

@dp.message(Command('get'))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')
    slots = slots_ref.stream()
    reply = ""
    for doc in slots:
        data = doc.to_dict()
        day = int(data['day'])
        days = int(data['days'])
        response = model.generate_content(data['parts'][day] + f" give a detailed explanation of the topic in 200 words. it is learning content. the explanation should be scientific and clear. Strictly give two sentences as the output. The day number and the detailed explanation. stricly folllow the constraints. DONOT GIVE ME THE OUTPUT IN MARKDOWN FORMAT I REPEAT. Just use normal text")
        reply += f"{response.text}\n\n"

        day += 1

        slots_ref.document(doc.id).update({'day': day})

        if day == days:
            slots_ref.document(doc.id).delete()
    await message.answer(reply)
    

@dp.message(Command('viewslot'))
async def command_viewslot_handler(message: Message) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    slot_name = message.text.replace("/viewslot ", "", 1).strip()

    slots = slots_ref.stream()
    for doc in slots:
        data = doc.to_dict()
        if slot_name == data['name'] :
            reply = f"Name: {data['name']}\n\nPrompt: {data['prompt']}\n\nDays: {data['days']}\n"
            await message.answer(reply)
            return
    await message.answer("Slot not found")

class Form(StatesGroup):
    name = State()
    prompt = State()
    parts = State()
    days = State()

@form_router.message(Command('newslot'))
async def command_newslot_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Enter the name of the slot:")

@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    if(message.text == "/cancel"):
        await state.clear()
        await message.answer("Slot creation cancelled")
        return

    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    refined_name = message.text
    refined_name = ' '.join(refined_name.split())

    slots = slots_ref.stream()
    for doc in slots:
        data = doc.to_dict()
        if refined_name.strip() == data['name'] :
            await state.clear()
            await message.answer("Slot with this name already exists. Operation aborted")
            return

    await state.update_data(name=refined_name.strip())
    await state.set_state(Form.prompt)
    await message.answer("Enter the prompt for the slot:")

@form_router.message(Form.prompt)
async def process_prompt(message: Message, state: FSMContext) -> None:
    if(message.text == "/cancel"):
        await state.clear()
        await message.answer("Slot creation cancelled")
        return

    await state.update_data(prompt=message.text.strip())
    await state.set_state(Form.days)
    await message.answer("Enter the number of days for the slot:")

@form_router.message(Form.days)
async def process_days(message: Message, state: FSMContext) -> None:
    if(message.text == "/cancel"):
        await state.clear()
        await message.answer("Slot creation cancelled")
        return

    await state.update_data(days=message.text.strip())

    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    prompt = (await state.get_data())['prompt']
    days = int((await state.get_data())['days'])

    response = model.generate_content(prompt.strip() + f" split the given prompt into topics for {days} days and return topics as separate {days} strings separated by a nextlines. strings should not have double quotes and there should be exacly {days} strings. Topics should be long, very elaborate and specific . I repeat return topics as {days} strings separated by nextline strictly. In each line mention the day number. Dont include anything other than that in the reply and strictly obey the constraints. DONOT GIVE THE OUTPUT IN MARKDOWN FORMAT just in unformatted text with the contraints i mentioned early. I REPEAT GIVE {days} SEPARATE STRINGS NOTHING MORE. ONLY RETURN {days} . strings should not have double quotes around in .txt format. I REPEAT GIVE {days} SEPARATE STRINGS NOTHING MORE. I REPEAT GIVE {days} SEPARATE STRINGS NOTHING MORE. I REPEAT GIVE {days} SEPARATE STRINGS NOTHING MORE. I REPEAT GIVE {days} SEPARATE STRINGS NOTHING MORE")

    print(response.text)

    doc_ref = slots_ref.add({
        'name': (await state.get_data())['name'].strip(),
        'prompt': (await state.get_data())['prompt'].strip(),
        'parts': response.text.replace('"', "").replace("\n\n", "\n").split('\n') if response else [],
        'days': (await state.get_data())['days'].strip(),
        'day': 0
    })

    slot_id = doc_ref[1].id

    #Schedule the send_scheduled_message function to run every day at 6 AM
    #schedule.every().day.at("06:00").do(asyncio.create_task, send_scheduled_message(user_id, slot_id))
    #schedule.every(10).seconds.do(asyncio.create_task, send_scheduled_message(user_id, slot_id))

    #await send_scheduled_message(user_id, slot_id) # this works

    await message.answer("Slot created!")

    await state.clear()

@dp.message(Command('deleteslot'))
async def command_deleteslot_handler(message: Message) -> None:
    user_id = message.from_user.id
    slots_ref = db.collection('users').document(str(user_id)).collection('slots')

    slot_name = message.text.replace("/deleteslot ", "", 1).strip()

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
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())