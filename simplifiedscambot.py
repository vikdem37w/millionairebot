from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from dotenv import load_dotenv
import os
import asyncio 
import json
import random
import time

load_dotenv()
token=os.getenv("BOT")
dp = Dispatcher()
form_router = Router()
if token:
    bot = Bot(token)
questions = json.load(open("whocanbeamillionairetho.json"))
last_interaction = time.time()
online = False
loop = asyncio.new_event_loop()

class Form(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    q7 = State()
    q8 = State()
    q9 = State()
    q10 = State()
    q11 = State()
    q12 = State()
    q13 = State()
    q14 = State()
    q15 = State()
qid = 0
qlist = [Form.q1, Form.q2, Form.q3, Form.q4, Form.q5, Form.q6, Form.q7, Form.q8, Form.q9, Form.q10, Form.q11, Form.q12, Form.q13, Form.q14, Form.q15]
reward = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000]

async def timeout(callback: types.CallbackQuery, state: FSMContext):
    global last_interaction
    global online
    while online:
        now = time.time()
        if now - last_interaction > 600:
            await state.clear()
            builder = InlineKeyboardBuilder()
            builder.button(text=f"Begin anew", callback_data="start")
            if callback.message:
                await callback.message.answer(text="It's been a while, no? \nTo upkeep server availability, we're forced to end your session prematurely. \nPreviously earned money is lost. \nTo begin anew, press the button below.", reply_markup=builder.as_markup())
            online = False
        await asyncio.sleep(0.1)

@dp.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext) -> None:
    await bot.send_photo(
        chat_id=msg.chat.id,
        photo=FSInputFile("cantaloupe.jpg") #until i get a proper photo, this atrocity shall plague the prod
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Begin", callback_data="start")
    await msg.answer(text=f"Greetings, contestant! \nWelcome to this barely legal and totally not copyright infringing game show! \nIf you don't know the rules, type /rules \nPress the button below to begin.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "begin_again", StateFilter(None))
async def begin_again_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        global online
        global last_interaction
        online = True
        asyncio.create_task(timeout(callback, state))
        last_interaction = time.time()
        global questions
        global round
        round = 1
        await callback.message.answer("Another round, then? Good luck!")
        online = True
        await asyncio.sleep(1)
        questions = json.load(open("whocanbeamillionairetho.json"))
        await q_handler(callback, state, Form.q1)

async def q_handler(callback: types.CallbackQuery, state: FSMContext, qx: State) -> None:
    if callback.message:
        global round
        await state.set_state(qx)
        global qid
        qid = random.randint(0, len(questions)-1)
        builder = InlineKeyboardBuilder()
        scramble = list(range(4))
        random.shuffle(scramble)
        for i in scramble:
            builder.button(text=f"{questions[qid]['options'][i]}", callback_data=f"{questions[qid]['options'][i]}")
        builder.adjust(2, 2)
        await callback.message.answer(text=f"Round {round}; Reward - {reward[round-1]}₴ \n{questions[qid]['question']}", reply_markup=builder.as_markup())
        await state.update_data(answer=questions[qid]["answer"])
        questions.pop(qid)
        await state.set_state(qx)

async def loss_response(callback: types.CallbackQuery, state: FSMContext, qindex: int) -> None:
    if callback.message:
        q = f"q{qindex}"
        global online
        online = False
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Try again", callback_data="begin_again")
        await callback.message.answer(text=f"You lost, you got to question {qindex}")
        if qindex > 10:
            await asyncio.sleep(1)
            await callback.message.answer(text="But, since you performed well enough, we'll let you keep 32k₴")
        elif qindex > 5:
            await asyncio.sleep(1)
            await callback.message.answer(text="But, as a nice gesture, we'll let you keep 1 000₴")
        await asyncio.sleep(1)
        await callback.message.answer(text=f"Want to try again?", reply_markup=builder.as_markup())

@form_router.callback_query(F.data == "start", StateFilter(None))
async def start_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        global round
        global online
        global last_interaction
        online = True
        asyncio.create_task(timeout(callback, state))
        last_interaction = time.time()
        await callback.message.answer("Alright! Starting off strong with Round 1")
        round = 1
        await asyncio.sleep(1)
        await q_handler(callback, state, Form.q1)
        
response = [
    "Good, you have 100₴, time for the next question",
    "200₴, moving on to Round 3",
    "300₴, time for Round 4",
    "500₴, hope you aren't cheating, because we're moving on to Round 5",
    "Round 6 incoming, raising up the stakes to a crisp double thousand.",
    "Round 7, doubling up the bounty to 4000₴",
    "Round 8, doubling up to 8000₴",
    "Round 9, keeping the doubling, bounty's now 16k₴",
    "Round 10, raising the stakes to 32k₴",
    "32k locked in, if you lose you'll keep the stuff you got now. Round 11!",
    "64k in the pocket, and a great chance to get that up to 125k₴! Round 12 coming up.",
    "Bringing it up to 250k! Round 13 incoming.",
    "Stakes at half a million! The show nears the end, and we'll see whether our dear contestant returns with a lot of money, an even bigger lot of money, or... with a lot smaller but still lot of money.",
    "Last question! If you win, you get a MILLION! Yet, if you lose, you get... 32k₴. Round 15, hit it!"
]

round = 1
@form_router.callback_query(StateFilter(*qlist))
async def q_response(callback: types.CallbackQuery, state: FSMContext) -> None:
    global qlist, round
    if callback.message:
        global last_interaction
        last_interaction = time.time()
        data = await state.get_data()
        answer = data.get("answer")

        if callback.data == answer:
            if round <= 14:
                await callback.message.answer(text=response[round-1])
            if round == 13:
                await asyncio.sleep(2)
            elif round == 15:
                global online
                online = False
                await callback.message.answer("YOU DID IT! A great sum of a 1 000 000₴ is now in your hands. Congrats!")
                builder = InlineKeyboardBuilder()
                builder.button(text=f"Get another million", callback_data="begin_again")
                await asyncio.sleep(1)
                await callback.message.answer(text=f"Surely you don't want another million, do you?", reply_markup=builder.as_markup())
                await state.clear()
            if round < 15:
                round += 1
                await asyncio.sleep(1)
                await q_handler(callback, state, qlist[round-1])
        else:
            if round == 14:
                await callback.message.answer("A smaller lot it is.")
                await asyncio.sleep(1)
            elif round == 15:
                await callback.message.answer("Aww, so close!")
                await asyncio.sleep(1)
            await loss_response(callback, state, round)
            await state.clear()

@dp.message(Command("rules"))
async def rules_handler(msg: types.Message) -> None:
    await msg.answer(text="Rules are simple: \n — Answer up to 15 questions \n — Questions have 4 options, where only one is correct \n — If you answer correctly, you move on to the next round \n — If you don't, you lose and get a certain amount of money, depending on which round you lost on: \n     — nothing if you lost on rounds 1-5\n     — 1000₴ on rounds 6-10\n     — 32k₴ on rounds 11-15\n — There are 15 rounds total; if you pass all 15, you get a million ₴.\n — Also, there's a 10 minute timeout timer,which could be reset by pressing a button or saying anything, after which your session is removed and kept money is lost, so don't take too long! (not implemented yet)")
photo_response = [
    "That's... one beautiful picture, but this is not an art gallery, this is a game show! Now, please, answer.",
    "Since when could you send pictures? To a game show host no less?",
    "For security reasons, we don't send pictures to the editors to include them in the live stream. Refrain from sending them."
]
text_response = [
    "That's great and all, but we have a game show to play.",
    "Your input will be cut from the live stream, so stick to pressing the buttons.",
    "We did not provide microphones for the contestants, so your babble won't be heard by the audience."
]
nodata_response = [
    "Uhh, anyway, back to the show!",
    "That's great, but back to the questions!",
    "Sure, now, please focus."
]

@dp.message(F.photo)
async def photo_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=photo_response[random.randint(0, 2)])
    last_interaction = time.time()

@dp.message(F.text)
async def text_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=text_response[random.randint(0, 2)])
    last_interaction = time.time()

@dp.message()
async def nodata_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=nodata_response[random.randint(0, 2)])
    last_interaction = time.time()

async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)

asyncio.run(main())