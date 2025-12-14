import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    description = State()
    photos = State()
    price = State()


menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Продажа вещи")],
        [KeyboardButton(text="Помощь")],
        [KeyboardButton(text="Предложение услуги")]
    ],
    resize_keyboard=True
)


@dp.message(commands=["start"])
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите вариант:", reply_markup=menu)


@dp.message(lambda m: m.text in ["Продажа вещи", "Помощь", "Предложение услуги"])
async def start_form(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text, photos=[])
    await state.set_state(Form.description)
    await message.answer("Введите описание:")


@dp.message(Form.description)
async def get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Form.photos)
    await message.answer(
        "Отправьте фото (если есть).\n"
        "Когда закончите — напишите «Готово».\n"
        "Если фото нет — сразу напишите «Готово»."
    )


@dp.message(Form.photos)
async def get_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.photo:
        data["photos"].append(message.photo[-1].file_id)
        await state.update_data(photos=data["photos"])
        return

    if message.text and message.text.lower() == "готово":
        await state.set_state(Form.price)
        await message.answer("Укажите цену:")
        return

    await message.answer("Пожалуйста, отправьте фото или напишите «Готово».")


@dp.message(Form.price)
async def get_price(message: types.Message, state: FSMContext):
    data = await state.get_data()

    text = (
        f"📩 *Новая заявка*\n\n"
        f"📌 Тип: {data['type']}\n"
        f"📝 Описание: {data['description']}\n"
        f"💰 Цена: {message.text}\n"
        f"👤 От: @{message.from_user.username or message.from_user.id}"
    )

    await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

    for photo in data["photos"]:
        await bot.send_photo(ADMIN_ID, photo)

    await state.clear()
    await message.answer("✅ Заявка отправлена администратору", reply_markup=menu)


async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
