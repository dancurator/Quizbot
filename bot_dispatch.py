import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from aiogram import F
from database import get_quiz_index, update_quiz_index, get_user_score, update_user_score
from API import API_TOKEN
from quiz_data import quiz_data

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"R_{option}" if option == right_answer else f"W_{option}")
        )

    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data.contains("R_"))
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, 
        message_id=callback.message.message_id, 
        reply_markup=None,
        text=f"{callback.message.text}\n\nВаш ответ: {callback.data[2:]}"
    )

    await callback.message.answer("Верно!")
    # Обновление номера текущего вопроса в базе данных
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)
    # Обновление очков
    scores = await get_user_score(callback.from_user.id)
    scores += 1
    await update_user_score(callback.from_user.id, scores)


    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data.contains("W_"))
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, 
        message_id=callback.message.message_id, 
        reply_markup=None,
        text=f"{callback.message.text}\n\nВаш ответ: {callback.data[2:]}"
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)


    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await update_user_score(user_id, 0)
    await get_question(message, user_id)




# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

# Хэндлер для статистики
@dp.message(F.text == "Статистика")
@dp.message(Command("statistics"))
async def statistics(message: types.Message):
    await message.answer("Ваша статистика:")
    scores = await get_user_score(message.from_user.id)
    await message.answer(f"{scores}/10. {'Отлично!' if scores >= 7 else 'Попробуйте еще!'}")
