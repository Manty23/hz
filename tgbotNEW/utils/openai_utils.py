import logging
from openai import OpenAI
import asyncio
from states import TestState
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def generate_questions(client: OpenAI, user_id: int, state: FSMContext, subject: str = None, subject_1: str = None, subject_2: str = None) -> None:
    is_premium = await is_premium_user(user_id)
    num_questions = 10 if is_premium else 5
    subjects_to_generate = []

    if subject:
        subjects_to_generate.append(subject)
    elif subject_1 and subject_2:
        subjects_to_generate.extend([subject_1, subject_2])

    if not subjects_to_generate:
        await state.bot.send_message(user_id, "⚠️ Пожалуйста, выберите предмет для начала теста.", show_alert=True)
        return

    if not is_premium and not await can_generate_questions(user_id):
        premium_info = (
            "🚀 <b>Хотите больше возможностей? Оформите Premium подписку!</b>\n\n"
            "💎 <b>Преимущества Premium:</b>\n"
            "    - Увеличенное количество вопросов за тест (10 вместо 5).\n"
            "    - Неограниченное количество генераций вопросов в день.\n\n"
            "Чтобы узнать больше о Premium и способах подключения, нажмите /premium (раздел в разработке)."
        )
        await state.bot.send_message(
            user_id,
            f"⚠️ Достигнут лимит бесплатных генераций вопросов на сегодня (4 раза).\n\n{premium_info}",
            reply_markup=await get_main_menu_keyboard()
        )
        return

    all_questions_combined = []
    all_correct_answers_combined = []
    generated_subjects = []

    try:
        for sub in subjects_to_generate:
            prompt = (
                f"Сгенерируй {num_questions} тестовых вопросов по предмету '{sub}' для подготовки к ЕНТ. "
                "Каждый вопрос должен иметь 4 варианта ответа (A, B, C, D) и один правильный. "
                "Формат:\n\nВопрос: ...\nA) ...\nB) ...\nC) ...\nD) ...\nПравильный ответ: X\n\n"
                "Вопросы должны быть разного уровня сложности."
            )
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Сгенерированные вопросы по {sub}:\n{generated_text}")

            question_blocks = [block.strip() for block in generated_text.split("\n\n") if block.strip()]
            subject_questions = []
            subject_correct_answers = []
            for block in question_blocks:
                lines = [line.strip() for line in block.split("\n") if line.strip()]
                if len(lines) < 6:
                    continue
                question_text = "\n".join(lines[:-1])
                correct_answer = lines[-1].split(":")[-1].strip().upper()
                if correct_answer in ("A", "B", "C", "D"):
                    subject_questions.append(question_text)
                    subject_correct_answers.append(correct_answer)

            all_questions_combined.append(subject_questions)
            all_correct_answers_combined.append(subject_correct_answers)
            generated_subjects.append(sub)

        await state.update_data(
            all_questions=all_questions_combined,
            all_correct_answers=all_correct_answers_combined,
            current_question_index=0,
            current_subject_index=0,
            answers=[]
        )
        await send_next_question(state.bot, state, user_id, generated_subjects=generated_subjects)
        if not is_premium:
            await increment_generation_counter(user_id)

    except Exception as e:
        logger.error(f"Ошибка при генерации вопросов: {e}")
        await state.bot.send_message(
            user_id,
            "⚠️ Произошла ошибка при генерации вопросов. Попробуйте позже.",
            reply_markup=await get_main_menu_keyboard()
        )

async def generate_full_ent_questions(client: OpenAI, user_id: int, state: FSMContext, subject_1: str,
                                      subject_2: str) -> None:
    is_premium = await is_premium_user(user_id)
    num_questions = {"history": 20, "math_literacy": 10, "reading_literacy": 10, "profile1": 40, "profile2": 40}
    subjects = {
        "history": "История Казахстана",
        "math_literacy": "Математическая грамотность",
        "reading_literacy": "Грамотность чтения",
        "profile1": subject_1,
        "profile2": subject_2,
    }
    all_questions = {}
    all_correct_answers = {}

    await state.bot.send_message(user_id, "⏳ Идет генерация вопросов для пробного ЕНТ. Это может занять некоторое время...")

    try:
        for key, subject_name in subjects.items():
            prompt = (
                f"Сгенерируй {num_questions[key]} тестовых вопросов по предмету '{subject_name}' для подготовки к ЕНТ. "
                "Каждый вопрос должен иметь 4 варианта ответа (A, B, C, D) и один правильный. "
                "Формат:\n\nВопрос: ...\nA) ...\nB) ...\nC) ...\nD) ...\nПравильный ответ: X\n\n"
                "Вопросы должны быть разного уровня сложности."
            )
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Сгенерированные вопросы по {subject_name}:\n{generated_text}")

            question_blocks = [block.strip() for block in generated_text.split("\n\n") if block.strip()]
            subject_questions = []
            subject_correct_answers = []
            for block in question_blocks:
                lines = [line.strip() for line in block.split("\n") if line.strip()]
                if len(lines) < 6:
                    continue
                question_text = "\n".join(lines[:-1])
                correct_answer = lines[-1].split(":")[-1].strip().upper()
                if correct_answer in ("A", "B", "C", "D"):
                    subject_questions.append(question_text)
                    subject_correct_answers.append(correct_answer)

            all_questions[key] = subject_questions
            all_correct_answers[key] = subject_correct_answers

        await state.update_data(full_ent_questions=all_questions)
        await state.update_data(full_ent_correct_answers=all_correct_answers)
        await state.set_state(TestState.full_ent_start_subject)
        await send_full_ent_start_subject_choice(state.bot, state, user_id)

    except Exception as e:
        logger.error(f"Ошибка при генерации вопросов для полного ЕНТ: {e}")
        await state.bot.send_message(
            user_id,
            "⚠️ Произошла ошибка при генерации вопросов для пробного ЕНТ. Попробуйте позже.",
            reply_markup=await get_main_menu_keyboard()
        )

# Эти функции теперь должны быть импортированы из других модулей
async def get_main_menu_keyboard():
    # ... (реализация в keyboards.py)
    pass

async def can_generate_questions(user_id: int):
    # ... (реализация в utils/statistics.py)
    pass

async def increment_generation_counter(user_id: int):
    # ... (реализация в utils/statistics.py)
    pass

async def send_next_question(bot: Bot, state: FSMContext, user_id: int, generated_subjects: list = None):
    # ... (реализация в handlers.py)
    pass

async def send_full_ent_start_subject_choice(bot: Bot, state: FSMContext, user_id: int):
    # ... (реализация в handlers.py)
    pass

async def is_premium_user(user_id: int):
    # ... (реализация в utils/statistics.py)
    user_statistics = await get_user_statistics()
    return user_statistics.get(user_id, {}).get("is_premium", False)

async def get_user_statistics():
    # ... (реализация для получения статистики, например, из базы данных или памяти)
    return {}