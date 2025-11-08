import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from datetime import datetime, timedelta

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Токен бота з змінної оточення
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не знайдено! Додайте його в Environment Variables на Render.com")

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Стани для FSM
class HomeworkStates(StatesGroup):
    choosing_subject = State()
    entering_homework = State()

# Розклад
SCHEDULE = {
    "Понеділок": [
        "(8:30 – 9:15) 📚 Укр. літ. (216)",
        "(9:25 – 10:10) 🎨 Мистецтво (207)",
        "(10:20 – 11:05) 📐 Алгебра (218)",
        "(11:25 – 12:10) 🧪 Хімія (315)",
        "(12:20 – 13:05) 🤸 Фіз-ра (216)",
        "(13:15 – 14:00) ⚛️ Фізика (316)",
        "(14:10 – 14:55) 🗣️ Гром. освіта (311)"
    ],
    "Вівторок": [
        "(8:30 – 9:15) 🇬🇧 Англ. мова (105/312)",
        "(9:25 – 10:10) 🇬🇧 Англ. мова (105/312)",
        "(10:20 – 11:05) 📏 Геометрія (218)",
        "(11:25 – 12:10) 🛡️ Історія Укр. (320)",
        "(12:20 – 13:05) ⚛️ Фізика (318)",
        "(13:15 – 14:00) 💰 Фін. гр. (313)",
        "(14:10 – 14:55) 🤸 Фіз-ра",
        "(15:05 – 15:50) 🇬🇧 Англ. мова"
    ],
    "Середа": [
        "(8:30 – 9:15) ✍️ Укр. мова (216)",
        "(9:25 – 10:10) 🌎 Географія (216)",
        "(10:20 – 11:05) 🇬🇧 Англ. мова (105/312)",
        "(11:25 – 12:10) 🌱 Біологія (112)",
        "(12:20 – 13:05) 🛡️ Історія Укр. (320)",
        "(13:15 – 14:00) 📐 Алгебра (218)"
    ],
    "Четвер": [
        "(8:30 – 9:15) ⚛️ Фізика (318)",
        "(9:25 – 10:10) ✍️ Укр. мова (218)",
        "(10:20 – 11:05) 📚 Укр. літ. (216)",
        "(11:25 – 12:10) 🗺️ Всесвітня історія (320)",
        "(12:20 – 13:05) 💻 Інформатика (221/317)",
        "(13:15 – 14:00) 🌎 Географія (220)",
        "(14:10 – 14:55) 🇬🇧 Англ. мова (105/312)",
        "(15:05 – 15:50) 🇬🇧 Англ. мова"
    ],
    "П'ятниця": [
        "(8:30 – 9:15) 🌱 Біологія (319)",
        "(9:25 – 10:10) 📖 Заруб. літ. (219)",
        "(10:20 – 11:05) 🇬🇧 Англ. мова (105/312)",
        "(11:25 – 12:10) 🤸 Фіз-ра",
        "(12:20 – 13:05) 🗣️ Гром. освіта (309)",
        "(13:15 – 14:00) 📏 Геометрія (218)"
    ]
}

# Список предметів
SUBJECTS = [
    "📚 Укр. літ.",
    "🎨 Мистецтво",
    "📐 Алгебра",
    "🧪 Хімія",
    "🤸 Фіз-ра",
    "⚛️ Фізика",
    "🗣️ Гром. освіта",
    "🇬🇧 Англ. мова",
    "📏 Геометрія",
    "🛡️ Історія Укр.",
    "💰 Фін. гр.",
    "✍️ Укр. мова",
    "🌎 Географія",
    "🌱 Біологія",
    "🗺️ Всесвітня історія",
    "💻 Інформатика",
    "📖 Заруб. літ."
]

# Словник для зберігання ДЗ {user_id: {subject: homework}}
homework_storage = {}

# Словник днів тижня
WEEKDAYS = {
    0: "Понеділок",
    1: "Вівторок",
    2: "Середа",
    3: "Четвер",
    4: "П'ятниця",
    5: "Субота",
    6: "Неділя"
}

def get_main_keyboard():
    """Головне меню"""
    keyboard = [
        [KeyboardButton(text="📝 Записати ДЗ")],
        [KeyboardButton(text="👀 Подивитися ДЗ")],
        [KeyboardButton(text="📅 Розклад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_subjects_keyboard():
    """Клавіатура з предметами"""
    keyboard = []
    for i in range(0, len(SUBJECTS), 2):
        row = []
        row.append(KeyboardButton(text=SUBJECTS[i]))
        if i + 1 < len(SUBJECTS):
            row.append(KeyboardButton(text=SUBJECTS[i + 1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="◀️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_view_homework_keyboard():
    """Клавіатура для перегляду ДЗ"""
    keyboard = [
        [KeyboardButton(text="📚 ДЗ по предмету")],
        [KeyboardButton(text="📆 ДЗ на завтра")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_delete_homework_keyboard(subject):
    """Inline клавіатура для видалення ДЗ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ ДЗ виконано", callback_data=f"delete_{subject}")]
    ])
    return keyboard

def get_tomorrow_day():
    """Повертає назву завтрашнього дня"""
    tomorrow = datetime.now() + timedelta(days=1)
    day_index = tomorrow.weekday()
    return WEEKDAYS.get(day_index, "Неділя")

def get_subjects_for_day(day_name):
    """Повертає список предметів на певний день"""
    if day_name not in SCHEDULE:
        return []
    
    subjects = []
    for lesson in SCHEDULE[day_name]:
        for subject in SUBJECTS:
            if subject in lesson:
                if subject not in subjects:
                    subjects.append(subject)
    return subjects

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обробник команди /start"""
    await message.answer(
        "👋 Привіт! Я бот для запису домашнього завдання.\n\n"
        "Виберіть дію:",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📝 Записати ДЗ")
async def write_homework(message: types.Message, state: FSMContext):
    """Початок запису ДЗ"""
    await message.answer(
        "Оберіть предмет:",
        reply_markup=get_subjects_keyboard()
    )
    await state.set_state(HomeworkStates.choosing_subject)

@dp.message(HomeworkStates.choosing_subject)
async def subject_chosen(message: types.Message, state: FSMContext):
    """Обробка вибору предмета"""
    if message.text == "◀️ Назад":
        await state.clear()
        await message.answer("Головне меню:", reply_markup=get_main_keyboard())
        return
    
    if message.text in SUBJECTS:
        await state.update_data(subject=message.text)
        await message.answer(
            f"Ви обрали: {message.text}\n\n"
            "Введіть домашнє завдання:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="◀️ Назад")]],
                resize_keyboard=True
            )
        )
        await state.set_state(HomeworkStates.entering_homework)
    else:
        await message.answer("❌ Будь ласка, оберіть предмет з клавіатури!")

@dp.message(HomeworkStates.entering_homework)
async def homework_entered(message: types.Message, state: FSMContext):
    """Збереження ДЗ"""
    if message.text == "◀️ Назад":
        await message.answer(
            "Оберіть предмет:",
            reply_markup=get_subjects_keyboard()
        )
        await state.set_state(HomeworkStates.choosing_subject)
        return
    
    data = await state.get_data()
    subject = data.get('subject')
    
    user_id = message.from_user.id
    if user_id not in homework_storage:
        homework_storage[user_id] = {}
    
    homework_storage[user_id][subject] = message.text
    
    await message.answer(
        f"✅ ДЗ з предмету {subject} збережено!\n\n"
        f"📝 Завдання: {message.text}",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@dp.message(F.text == "👀 Подивитися ДЗ")
async def view_homework(message: types.Message):
    """Перегляд ДЗ"""
    await message.answer(
        "Виберіть варіант перегляду:",
        reply_markup=get_view_homework_keyboard()
    )

@dp.message(F.text == "📚 ДЗ по предмету")
async def homework_by_subject(message: types.Message):
    """Показати ДЗ по предмету"""
    user_id = message.from_user.id
    
    if user_id not in homework_storage or not homework_storage[user_id]:
        await message.answer(
            "❌ Немає збережених завдань!",
            reply_markup=get_view_homework_keyboard()
        )
        return
    
    # Відправляємо кожне завдання окремо з кнопкою видалення
    for subject, homework in homework_storage[user_id].items():
        await message.answer(
            f"{subject}\n📝 {homework}",
            reply_markup=get_delete_homework_keyboard(subject)
        )

@dp.message(F.text == "📆 ДЗ на завтра")
async def homework_for_tomorrow(message: types.Message):
    """Показати ДЗ на завтра"""
    user_id = message.from_user.id
    tomorrow = get_tomorrow_day()
    
    if tomorrow == "Субота" or tomorrow == "Неділя":
        await message.answer(
            f"📅 Завтра {tomorrow} - вихідний день! 🎉",
            reply_markup=get_view_homework_keyboard()
        )
        return
    
    subjects_tomorrow = get_subjects_for_day(tomorrow)
    
    if user_id not in homework_storage or not homework_storage[user_id]:
        await message.answer(
            f"📅 Завтра {tomorrow}\n\n❌ Немає збережених завдань!",
            reply_markup=get_view_homework_keyboard()
        )
        return
    
    text = f"📅 ДЗ на завтра ({tomorrow}):\n\n"
    has_homework = False
    
    for subject in subjects_tomorrow:
        if subject in homework_storage[user_id]:
            text += f"{subject}\n📝 {homework_storage[user_id][subject]}\n\n"
            has_homework = True
    
    if not has_homework:
        text += "❌ Немає записаних завдань на завтра"
    
    await message.answer(text, reply_markup=get_view_homework_keyboard())

@dp.message(F.text == "📅 Розклад")
async def show_schedule(message: types.Message):
    """Показати розклад"""
    keyboard = [
        [KeyboardButton(text="📅 Понеділок"), KeyboardButton(text="📅 Вівторок")],
        [KeyboardButton(text="📅 Середа"), KeyboardButton(text="📅 Четвер")],
        [KeyboardButton(text="📅 П'ятниця")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    await message.answer(
        "Виберіть день тижня:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

@dp.message(F.text.startswith("📅 "))
async def show_day_schedule(message: types.Message):
    """Показати розклад на день"""
    day = message.text.replace("📅 ", "")
    
    if day in SCHEDULE:
        text = f"📅 Розклад на {day}:\n\n"
        text += "\n".join(SCHEDULE[day])
        await message.answer(text)
    else:
        await message.answer("❌ День не знайдено")

@dp.message(F.text == "◀️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    """Повернення в головне меню"""
    await state.clear()
    await message.answer(
        "Головне меню:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data.startswith("delete_"))
async def delete_homework(callback: types.CallbackQuery):
    """Видалення ДЗ"""
    subject = callback.data.replace("delete_", "")
    user_id = callback.from_user.id
    
    if user_id in homework_storage and subject in homework_storage[user_id]:
        del homework_storage[user_id][subject]
        await callback.message.edit_text(
            f"✅ ДЗ з предмету {subject} виконано та видалено!"
        )
    else:
        await callback.answer("❌ Завдання не знайдено")
    
    await callback.answer()

async def main():
    """Запуск бота"""
    print("🤖 Бот запущено!")
    print(f"🔑 Токен: {BOT_TOKEN[:10]}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())