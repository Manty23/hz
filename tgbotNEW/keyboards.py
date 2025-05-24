from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

OBLIGATORY_SUBJECTS = ["Математическая грамотность", "История Казахстана", "Грамотность чтения"]
PROFILE_SUBJECTS = ["Математика", "Физика", "География", "Информатика", "Биология", "Химия", "Иностранный язык",
                    "Основы права", "Творческий экзамен"]


async def get_obligatory_subjects_keyboard() -> InlineKeyboardMarkup:
    """Inline-клавиатура для выбора обязательных предметов"""
    builder = InlineKeyboardBuilder()
    for subject in OBLIGATORY_SUBJECTS:
        builder.add(InlineKeyboardButton(text=f"📚 {subject}", callback_data=f"obligatory:{subject}"))
    builder.adjust(2)
    return builder.as_markup()


async def get_profile_subjects_keyboard_1() -> InlineKeyboardMarkup:
    """Inline-клавиатура для выбора первого профильного предмета"""
    builder = InlineKeyboardBuilder()
    for subject in PROFILE_SUBJECTS:
        builder.add(InlineKeyboardButton(text=f"🧪 {subject}", callback_data=f"profile1:{subject}"))
    builder.adjust(2)
    return builder.as_markup()


async def get_profile_subjects_keyboard_2(excluded_subject: str) -> InlineKeyboardMarkup:
    """Inline-клавиатура для выбора второго профильного предмета (исключая первый)"""
    builder = InlineKeyboardBuilder()
    available_subjects = [s for s in PROFILE_SUBJECTS if s != excluded_subject]
    for subject in available_subjects:
        builder.add(InlineKeyboardButton(text=f"🔬 {subject}", callback_data=f"profile2:{subject}"))
    builder.adjust(2)
    return builder.as_markup()


async def get_answer_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура вариантов ответов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="A"), KeyboardButton(text="B")],
            [KeyboardButton(text="C"), KeyboardButton(text="D")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def get_end_test_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура после завершения теста"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Пройти ещё раз")],
            [KeyboardButton(text="☰ Меню")]
        ],
        resize_keyboard=True
    )


async def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура основного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Обязательные предметы")],
            [KeyboardButton(text="🧪 Профильные предметы")],
            [KeyboardButton(text="🧪 Пробный ЕНТ")]
        ],
        resize_keyboard=True
    )