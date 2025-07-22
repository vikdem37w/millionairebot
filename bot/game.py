from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from bot import settings, db_operations, init
from bot.middlewares import Userware
from openai import OpenAI
import logging
import asyncio
import random
import time
import datetime as dt

asyncio.run(settings.setup_logger())
logger = logging.getLogger(__name__)
token, aitoken = settings.get_token()
dp = Dispatcher()
form_router = Router()
dp.message.middleware(Userware())
dp.callback_query.middleware(Userware())

if token:
    bot = Bot(token)
last_interaction = time.time()


class Form(StatesGroup):
    q = State()
    addq = State()
    addo1 = State()
    addo2 = State()
    addo3 = State()
    addo4 = State()
    adda = State()


qid = 0
qlist = Form.q
reward = [
    0,
    100,
    200,
    300,
    500,
    1000,
    2000,
    4000,
    8000,
    16000,
    32000,
    64000,
    125000,
    250000,
    500000,
    1000000,
]
round = 1
asyncio.run(init.setup_db())
try:
    client = OpenAI(api_key=aitoken)
except Exception as e:
    logger.error(f"AI key error raised: {e}")


async def timeout(callback: types.CallbackQuery, state: FSMContext):
    global last_interaction, flavorcarryover
    while await state.get_state() == Form.q:
        now = time.time()
        if now - last_interaction > 600:
            data = await state.get_data()
            await data["lifelinetxt"].delete()
            await data["qtxt"].delete()
            if data["phonetxt"]:
                await data["phonetxt"].delete()
            if data["audiencetxt"]:
                await data["audiencetxt"].delete()
            await state.clear()
            builder = InlineKeyboardBuilder()
            builder.button(text="Begin anew", callback_data="start")
            if callback.message:
                f1 = await callback.message.answer(
                    text="It's been a while, no?", reply_markup=ReplyKeyboardRemove()
                )
                f2 = await callback.message.answer(
                    text="To upkeep server availability, we're forced to end your session prematurely. "
                    "\nPreviously earned money is lost. \nTo begin anew, press the button below.",
                    reply_markup=builder.as_markup(),
                )
                flavorcarryover = [f1, f2]
            await state.clear()
        await asyncio.sleep(1)


@dp.message(CommandStart())
async def cmd_start(msg: types.Message, username) -> None:
    global photo, greeting
    photo = await bot.send_photo(chat_id=msg.chat.id, photo=FSInputFile("wwtbam.jpg"))
    builder = InlineKeyboardBuilder()
    builder.button(text="Begin", callback_data="start")
    chat_id = msg.chat.id
    greeting = await msg.answer(
        text=f"""Greetings, {username}! 
Welcome to this barely legal and totally not copyright infringing game show! 
If you don't know the rules, type /rules 
To view the leaderboard, type /leaderboard 
Press the button below to begin.""",
        reply_markup=builder.as_markup(),
    )
    admin = await settings.is_admin(username)
    await db_operations.add_user(username, chat_id, admin)
    if admin == "admin":
        admintxt = await msg.answer(
            text="Oh, we have some staffmen here. Just a reminder, you can add questions via /addquestion."
        )
        await asyncio.sleep(7)
        await admintxt.delete()


@dp.callback_query(F.data == "begin_again", StateFilter(None))
async def begin_again(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        global last_interaction, questions, round, flavorcarryover
        for i in flavorcarryover:
            await i.delete()
        await state.set_state(Form.q)
        asyncio.create_task(timeout(callback, state))
        last_interaction = time.time()
        round = 1
        builder = ReplyKeyboardBuilder()
        builder.button(text="50/50")
        builder.button(text="Phone a friend")
        builder.button(text="Ask the audience")
        await state.update_data(
            fiftyfiftyused=False,
            phoneafriendused=False,
            asktheaudienceused=False,
            phonetxt=None,
            audiencetxt=None,
        )
        flavor = await callback.message.answer(
            "Another round, then? Good luck!", reply_markup=builder.as_markup()
        )
        await asyncio.sleep(0.5)
        lifelinetxt = await callback.message.answer(
            text="Remember to use your lifelines, as you won't get a star sticker for not using them!",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(lifelinetxt=lifelinetxt)
        await asyncio.sleep(0.5)
        questions = await db_operations.get_questions()
        await q_handler(callback, state, Form.q)
        await asyncio.sleep(2)
        await flavor.delete()


async def q_handler(
    callback: types.CallbackQuery, state: FSMContext, qx: State
) -> None:
    if callback.message:
        global round, qid
        await state.set_state(qx)
        qid = random.randint(0, len(questions) - 1)
        builder = InlineKeyboardBuilder()
        scramble = list(range(4))
        random.shuffle(scramble)
        for i in scramble:
            builder.button(
                text=f"{questions[qid][1][i]}", callback_data=f"{questions[qid][1][i]}"
            )
        builder.adjust(2, 2)
        qtxt = await callback.message.answer(
            text=f"Round {round}; Reward - {reward[round]}₴ \n{questions[qid][0]}",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(
            answer=questions[qid][2],
            question=questions[qid][0],
            options=questions[qid][1],
            qtxt=qtxt,
        )
        questions.pop(qid)


async def loss_response(
    callback: types.CallbackQuery, state: FSMContext, qindex: int, username
) -> None:
    if callback.message:
        global flavorcarryover
        data = await state.get_data()
        await data["lifelinetxt"].delete()
        flavorcarryover = []
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.button(text="Try again", callback_data="begin_again")
        flavor = await callback.message.answer(
            text=f"You lost, you got to question {qindex}",
            reply_markup=ReplyKeyboardRemove(),
        )
        flavorcarryover.append(flavor)
        if qindex > 10:
            await asyncio.sleep(1)
            performance = await callback.message.answer(
                text="But, since you performed well enough, we'll let you keep 32k₴"
            )
            flavorcarryover.append(performance)
        elif qindex > 5:
            await asyncio.sleep(1)
            performance = await callback.message.answer(
                text="But, as a nice gesture, we'll let you keep 1 000₴"
            )
            flavorcarryover.append(performance)
        logger.info(
            f"{username} lost the game on round {qindex} at {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await db_operations.stats_up(username, qindex - 1, "loss")
        await asyncio.sleep(1)
        beginagain = await callback.message.answer(
            text="Want to try again?", reply_markup=builder.as_markup()
        )
        flavorcarryover.append(beginagain)


@form_router.callback_query(F.data == "start", StateFilter(None))
async def start_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        global round, last_interaction, questions, photo, greeting
        try:
            if photo and greeting:
                await photo.delete()
                await greeting.delete()
                photo = None
                greeting = None
            else:
                for i in flavorcarryover:
                    await i.delete()
        except Exception as e:
            logger.error(f"Photo stall detected: {e}")
        await state.set_state(Form.q)
        asyncio.create_task(timeout(callback, state))
        last_interaction = time.time()
        builder = ReplyKeyboardBuilder()
        builder.button(text="50/50")
        builder.button(text="Phone a friend")
        builder.button(text="Ask the audience")
        await state.update_data(
            fiftyfiftyused=False,
            phoneafriendused=False,
            asktheaudienceused=False,
            phonetxt=None,
            audiencetxt=None,
        )
        flavor = await callback.message.answer("Alright, starting off with Round 1!")
        round = 1
        await asyncio.sleep(0.5)
        lifelinetxt = await callback.message.answer(
            text="Remember to use your lifelines, as you won't get a star sticker for not using them!",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(lifelinetxt=lifelinetxt)
        await asyncio.sleep(0.5)
        questions = await db_operations.get_questions()
        await q_handler(callback, state, Form.q)
        await asyncio.sleep(4)
        await flavor.delete()


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
    "Stakes at half a million! The show nears the end, and we'll see whether our dear contestant returns with a lot of money, "
    "an even bigger lot of money, or... with a lot smaller but still lot of money.",
    "Last question! If you win, you get a MILLION! Yet, if you lose, you get... 32k₴. Round 15, hit it!",
]


@dp.message(F.text == "50/50", StateFilter(Form.q))
async def fiftyfifty(msg: types.Message, state: FSMContext) -> None:
    global last_interaction
    last_interaction = time.time()
    data = await state.get_data()
    await bot.delete_message(msg.chat.id, msg.message_id)
    if not data["fiftyfiftyused"]:
        await state.update_data(fiftyfiftyused=True)
        builder = InlineKeyboardBuilder()
        for i in range(2):
            if data["options"][0] != data["answer"]:
                data["options"].pop(0)
            else:
                data["options"].pop(1)
        builder.button(
            text=f"{data['options'][0]}", callback_data=f"{data['options'][0]}"
        )
        builder.button(
            text=f"{data['options'][1]}", callback_data=f"{data['options'][1]}"
        )
        builder.adjust(1, 1)
        qtxt = data["qtxt"]
        await qtxt.delete()
        qtxt = await msg.answer(
            text="50/50 lifeline used, options split even!",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(qtxt=qtxt)
    else:
        flavor = await msg.answer(
            text="Oh no, you can't use 50/50 again, sweetie, lifelines are one-time-use."
        )
        await asyncio.sleep(5)
        await flavor.delete()


@dp.message(F.text == "Phone a friend", StateFilter(Form.q))
async def phoneafriend(msg: types.Message, state: FSMContext) -> None:
    global last_interaction
    last_interaction = time.time()
    data = await state.get_data()
    await bot.delete_message(msg.chat.id, msg.message_id)
    if not data["phoneafriendused"]:
        await state.update_data(phoneafriendused=True)
        flavor = await msg.answer(
            text="Phone a friend lifeline used! Calling your friend..."
        )
        await asyncio.sleep(5)
        await flavor.delete()
        try:
            response = client.responses.create(
                model="gpt-3.5-turbo",
                input="Your friend has just used a Phone a friend lifeline on a game show, and has decided to call you. "
                f"The question is: {data['question']}. The options are: {data['options']}. Respond with a short answer, "
                "giving them some information on the answer without saying the answer outright. "
                "The answer must be helpful and help eliminate at least one option, "
                "with the answer only revealed with enough context known by the contestant to answer the question.",
            )
            phonetxt = await msg.answer(
                text=f"And they responded with: {response.output_text}"
            )
            await state.update_data(phonetxt=phonetxt)
        except Exception as e:
            logger.error(f"Phone a friend AI error raised: {e}")
            flavor = await msg.answer(
                text="Line's dead, your dear friend did not pick up. They got something better to do, I guess."
            )
            await asyncio.sleep(5)
            await flavor.delete()
    else:
        flavor = await msg.answer(
            text="Oh no, you can't call your friend again, honey, lifelines are one-time-use."
        )
        await asyncio.sleep(5)
        await flavor.delete()


@dp.message(F.text == "Ask the audience", StateFilter(Form.q))
async def asktheaudience(msg: types.Message, state: FSMContext) -> None:
    global last_interaction
    last_interaction = time.time()
    data = await state.get_data()
    await bot.delete_message(msg.chat.id, msg.message_id)
    if not data["asktheaudienceused"]:
        await state.update_data(asktheaudienceused=True)
        flavor = await msg.answer(
            text="Ask the audience lifeline used! Voting in progress..."
        )
        await asyncio.sleep(5)
        await flavor.delete()
        try:
            response = client.responses.create(
                model="gpt-3.5-turbo",
                input="A contestant has used an Ask the audience lifeline on a game show, and the audience is voting on the answer. "
                f"The question is: {data['question']}. The options are: {data['options']}. Respond with the options and the votes, "
                "example: Moth: 40%, Roach: 10%, Fly:30%, Japanese beetle: 20%.",
            )

            audiencetxt = await msg.answer(
                text=f"And the votes are in: {response.output_text}"
            )
            await state.update_data(audiencetxt=audiencetxt)
        except Exception as e:
            logger.error(f"Ask the audience AI error raised: {e}")
            flavor = await msg.answer(
                text="Our vote counting system ran into an issue, so the votes have been invalidated. "
                "You'll have to answer without the audience's help"
            )
            await asyncio.sleep(5)
            await flavor.delete()
    else:
        flavor = await msg.answer(
            text="Oh, the audience is recovering from the last vote! You can't ask them for another!"
        )
        await asyncio.sleep(5)
        await flavor.delete()


@form_router.callback_query(StateFilter(Form.q))
async def q_response(
    callback: types.CallbackQuery, state: FSMContext, username
) -> None:
    global qlist, round, last_interaction, flavorcarryover
    if callback.message:
        last_interaction = time.time()
        data = await state.get_data()
        qtxt = data["qtxt"]
        await qtxt.delete()
        answer = data.get("answer")
        if data["phonetxt"]:
            await data["phonetxt"].delete()
            await state.update_data(phonetxt=None)
        if data["audiencetxt"]:
            await data["audiencetxt"].delete()
            await state.update_data(audiencetxt=None)
        if callback.data == answer:
            if round <= 14:
                builder = ReplyKeyboardBuilder()
                data = await state.get_data()
                flavor = await callback.message.answer(text=response[round - 1])
            if round == 13:
                await asyncio.sleep(4)
            elif round == 14:
                await asyncio.sleep(2)
            elif round == 15:
                await data["lifelinetxt"].delete()
                await state.clear()
                flavorcarryover = []
                flavor = await callback.message.answer(
                    "YOU DID IT! A great sum of a 1 000 000₴ is now in your hands. Congrats!",
                    reply_markup=ReplyKeyboardRemove(),
                )
                flavorcarryover.append(flavor)
                username = callback.from_user.username if callback.from_user else "NULL"
                logger.info(
                    f"{username} won the game at {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await db_operations.stats_up(username, 15, "win")
                builder = InlineKeyboardBuilder()
                builder.button(text="Get another million", callback_data="begin_again")
                await asyncio.sleep(1)
                beginagain = await callback.message.answer(
                    text="Surely you don't want another million, do you?",
                    reply_markup=builder.as_markup(),
                )
                flavorcarryover.append(beginagain)
                await state.clear()
            if round < 15:
                round += 1
                await asyncio.sleep(3)
                await flavor.delete()
                await q_handler(callback, state, Form.q)
        else:
            if round == 14:
                flavor = await callback.message.answer("A smaller lot it is.")
                await asyncio.sleep(2)
                await flavor.delete()
            elif round == 15:
                flavor = await callback.message.answer("Aww, so close!")
                await asyncio.sleep(2)
                await flavor.delete()
            await loss_response(callback, state, round, username)
            await state.clear()


@dp.message(Command("rules"))
async def rules_handler(msg: types.Message) -> None:
    global last_interaction
    last_interaction = time.time()
    await msg.answer(
        text="""Rules are simple: 
 — Answer up to 15 questions 
 — Questions have 4 options, where only one is correct 
 — If you answer correctly, you move on to the next round 
 — If you don't, you lose and get a certain amount of money, depending on which round you lost on: 
     — nothing if you lost on rounds 1-5
     — 1000₴ on rounds 6-10
     — 32k₴ on rounds 11-15
 — There are 15 rounds total; if you pass all 15, you get a million ₴.
 — Also, there's a 10 minute timeout timer (which could be reset by pressing a button, typing or sending anything),"""
        "after which your session is removed and kept money is lost, so don't leave the show early! \
    \n — Also, you have access to lifelines: 50/50, Phone a friend, and Ask the audience. They're one-time-use, though, so don't spend them willy-nilly!"
    )


@dp.message(Command("leaderboard"))
async def leaderboard_handler(msg: types.Message, username) -> None:
    global last_interaction
    last_interaction = time.time()
    await msg.answer(text=await db_operations.fill_leaderboard(username))


@dp.message(Command("addquestion"))
async def addquestion(msg: types.Message, state: FSMContext, username) -> None:
    global last_interaction
    last_interaction = time.time()
    admin = await settings.is_admin(username)
    if admin == "admin":
        await state.set_state(Form.addq)
        await msg.answer(text="Enter the question:")
    else:
        await msg.answer(
            text="I'd love to help you add a question, yet, for security reasons, only staff have permission to do so. "
            "Maybe consider filling out a job application at the front desk?"
        )


@form_router.message(Form.addq)
async def addoption1(msg: types.Message, state: FSMContext) -> None:
    await state.update_data(question=msg.text)
    await state.set_state(Form.addo1)
    await msg.answer(text="Enter the first option:")


@form_router.message(Form.addo1)
async def addoption2(msg: types.Message, state: FSMContext) -> None:
    await state.update_data(option1=msg.text)
    await state.set_state(Form.addo2)
    await msg.answer(text="Enter the second option:")


@form_router.message(Form.addo2)
async def addoption3(msg: types.Message, state: FSMContext) -> None:
    await state.update_data(option2=msg.text)
    await state.set_state(Form.addo3)
    await msg.answer(text="Enter the third option:")


@form_router.message(Form.addo3)
async def addoption4(msg: types.Message, state: FSMContext) -> None:
    await state.update_data(option3=msg.text)
    await state.set_state(Form.addo4)
    await msg.answer(text="Enter the fourth option:")


@form_router.message(Form.addo4)
async def addanswer(msg: types.Message, state: FSMContext) -> None:
    await state.update_data(option4=msg.text)
    await state.set_state(Form.adda)
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    for i in range(4):
        builder.button(
            text=f"{data[f'option{i+1}']}", callback_data=f"{data[f'option{i+1}']}"
        )
    builder.adjust(2, 2)
    await msg.answer(text="Select an answer:", reply_markup=builder.as_markup())


@form_router.callback_query(Form.adda)
async def finishquestion(
    callback: types.CallbackQuery, state: FSMContext, username
) -> None:
    if callback.message:
        await state.update_data(answer=callback.data)
        data = await state.get_data()
        logger.info(
            f"{username} added a question: \"{data['question']}\" with options {data['option1']}, {data['option2']}, {data['option3']}, {data['option4']} and answer {data['answer']}"
        )
        await db_operations.commit_question(
            data["question"],
            [data["option1"], data["option2"], data["option3"], data["option4"]],
            data["answer"],
        )
        await settings.json_question(
            data["question"],
            [data["option1"], data["option2"], data["option3"], data["option4"]],
            data["answer"],
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="Start", callback_data="start")
        await callback.message.answer(
            text="Question added. Click here to start the game.",
            reply_markup=builder.as_markup(),
        )
        await state.clear()


photo_response = [
    "That's... one beautiful picture, but this is not an art gallery, this is a game show! Now, please, answer.",
    "Since when could you send pictures? To a game show host no less?",
    "For security reasons, we don't send pictures to the editors to include them in the live stream. Refrain from sending them.",
]
sticker_response = [
    "Showing off, are ya? Well, the audience can't see them anyway.",
    "Great sticker! Now, please, answer the question.",
    "We'll edit that out. Answer, please.",
]
text_response = [
    "That's great and all, but we have a game show to play.",
    "Your input will be cut from the live stream, so stick to pressing the buttons.",
    "We did not provide microphones for the contestants, so your babble won't be heard by the audience.",
]
nodata_response = [
    "Uhh, anyway, back to the show!",
    "That's great, but back to the questions!",
    "Sure, now, please focus.",
]


@dp.message(F.photo)
async def photo_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=photo_response[random.randint(0, 2)])
    last_interaction = time.time()


@dp.message(F.sticker)
async def sticker_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=sticker_response[random.randint(0, 2)])
    last_interaction = time.time()


@dp.message(
    F.text,
    StateFilter(None),
    ~F.text.in_(["50/50", "Phone a friend", "Ask the audience"]),
)
@dp.message(
    F.text,
    StateFilter(Form.q),
    ~F.text.in_(["50/50", "Phone a friend", "Ask the audience"]),
)
async def text_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=text_response[random.randint(0, 2)])
    last_interaction = time.time()


@dp.message(
    StateFilter(None), ~F.text.in_(["50/50", "Phone a friend", "Ask the audience"])
)
@dp.message(
    StateFilter(Form.q), ~F.text.in_(["50/50", "Phone a friend", "Ask the audience"])
)
async def nodata_handler(msg: types.Message) -> None:
    global last_interaction
    await msg.answer(text=nodata_response[random.randint(0, 2)])
    last_interaction = time.time()


async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)
