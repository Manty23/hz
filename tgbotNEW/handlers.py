from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from utils.openai_utils import generate_questions, generate_full_ent_questions
from utils.statistics import user_statistics, can_generate_questions, increment_generation_counter
from states import TestState
from keyboards import (
    get_main_menu_keyboard,
    get_obligatory_subjects_keyboard,
    get_profile_subjects_keyboard_1,
    get_profile_subjects_keyboard_2,
    get_answer_keyboard,
    get_end_test_keyboard,
    ReplyKeyboardBuilder, KeyboardButton
)
import logging
logger = logging.getLogger(__name__)


# Предметы (теперь могут быть определены здесь или в keyboards.py, в зависимости от использования)
OBLIGATORY_SUBJECTS = ["Мат. грамотность", "История Казахстана", "Грамотность чтения"]
PROFILE_SUBJECTS = ["Математика", "Физика", "География", "Информатика", "Биология", "Химия", "Иностранный язык", "Основы права", "Творческий экзамен"]


async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"👋 Добро пожаловать, {message.from_user.first_name}! 🚀\n\nВыберите раздел:",
        reply_markup=await get_main_menu_keyboard()
    )

async def cmd_help(message: types.Message) -> None:
    help_text = (
        "ℹ️ <b>Информация о боте для подготовки к ЕНТ</b> 📚\n\n"
        "Этот бот разработан, чтобы помочь вам эффективно подготовиться к Единому Национальному Тестированию (ЕНТ).\n\n"
        "<b>Основные разделы и команды:</b>\n"
        "1️⃣ <b>📖 Обязательные предметы:</b>\n"
        "   - Выберите этот раздел, чтобы начать тестирование по обязательным предметам: Математическая грамотность, История Казахстана и Грамотность чтения.\n"
        "   - После выбора предмета бот сгенерирует для вас 5 тестовых вопросов.\n\n"
        "2️⃣ <b>🧪 Профильные предметы:</b>\n"
        "   - В этом разделе вы можете выбрать два профильных предмета, по которым хотите пройти тестирование.\n"
        "   - Доступные профильные предметы: Математика, Физика, География, Информатика, Биология, Химия, Иностранный язык, Основы права, Творческий экзамен.\n\n"
        "<b>Как пользоваться ботом:</b>\n"
        "➡️ Используйте кнопки меню для навигации между разделами.\n"
        "➡️ После выбора предмета вам будут предложены тестовые вопросы с вариантами ответов (A, B, C, D).\n"
        "➡️ Отправьте боту букву, соответствующую вашему выбору.\n"
        "➡️ По завершении теста вы увидите свой результат.\n\n"
        "<b>Дополнительные команды:</b>\n"
        "➡️ /start - Запускает бота и отображает основное меню.\n"
        "➡️ 🔄 Пройти ещё раз - Позволяет начать новый тест после завершения предыдущего.\n"
        "➡️ 💎 Premium (в разработке) - Информация о Premium-подписке с расширенными возможностями.\n\n"
        "Если у вас возникнут вопросы или предложения по работе бота, пожалуйста, обратитесь к разработчику."
    )
    await message.answer(help_text, parse_mode="HTML")


async def handle_obligatory_subjects(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите обязательный предмет:", reply_markup=await get_obligatory_subjects_keyboard())
    await state.set_state(TestState.subject)
    await state.update_data(test_type="obligatory")


async def handle_select_obligatory(callback: types.CallbackQuery, state: FSMContext) -> None:
    subject = callback.data.split(":")[1]
    await callback.answer(f"Выбран обязательный предмет: {subject}", show_alert=False)
    await state.update_data(subject=subject)
    await callback.message.edit_text(f"Выбран обязательный предмет: {subject}\n⏳ Начинаем генерацию вопросов...")
    # Предполагается, что объект 'client' (OpenAI) доступен через state или dp
    client = state.bot['openai_client']
    user_id = callback.from_user.id
    if client:
        await generate_questions(client, user_id, state, subject=subject)
    else:
        await callback.message.answer("⚠️ Ошибка: Клиент OpenAI не инициализирован.")


async def handle_profile_subjects(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите первый профильный предмет:", reply_markup=await get_profile_subjects_keyboard_1())
    await state.set_state(TestState.profile_subject_1)
    await state.update_data(selected_profile_subjects=[])
    await state.update_data(test_type="profile")


async def handle_select_profile_1(callback: types.CallbackQuery, state: FSMContext) -> None:
    subject_1 = callback.data.split(":")[1]
    await callback.answer(f"Выбран первый профильный предмет: {subject_1}", show_alert=False)
    await state.update_data(profile_subject_1=subject_1, selected_profile_subjects=[subject_1])
    await callback.message.edit_text(f"Выбран первый профильный предмет: {subject_1}\nВыберите второй профильный предмет:")
    await callback.message.edit_reply_markup(reply_markup=await get_profile_subjects_keyboard_2(subject_1))
    await state.set_state(TestState.profile_subject_2)


async def handle_select_profile_2(callback: types.CallbackQuery, state: FSMContext) -> None:
    subject_2 = callback.data.split(":")[1]
    data = await state.get_data()
    subject_1 = data.get("profile_subject_1")
    if subject_1 and subject_2 != subject_1:
        await callback.answer(f"Выбраны профильные предметы: {subject_1} и {subject_2}", show_alert=False)
        await state.update_data(profile_subject_2=subject_2, selected_profile_subjects=[subject_1, subject_2])
        await callback.message.edit_text(
            f"Выбраны профильные предметы: {subject_1} и {subject_2}\n⏳ Начинаем генерацию вопросов...")
        client = state.bot['openai_client'] # Исправленная строка
        user_id = callback.from_user.id
        if client:
            await generate_questions(client, user_id, state, subject_1=subject_1, subject_2=subject_2)
        else:
            await callback.message.answer("⚠️ Ошибка: Клиент OpenAI не инициализирован.")
    elif not subject_1:
        await callback.answer("Пожалуйста, сначала выберите первый профильный предмет.", show_alert=True)
    else:
        await callback.answer("Вы не можете выбрать один и тот же предмет дважды.", show_alert=True)


async def handle_answer(message: types.Message, state: FSMContext) -> None:
    user_answer = message.text.upper()
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == TestState.full_ent_process:
        current_subject = data.get("full_ent_current_subject")
        current_question_index = data.get("full_ent_current_question_index", 1) - 1 # Adjust index to match the question number
        if current_subject and data.get("full_ent_questions", {}).get(current_subject) and current_question_index < len(data["full_ent_questions"][current_subject]):
            user_answers = data.get("full_ent_user_answers", {})
            if current_subject not in user_answers:
                user_answers[current_subject] = {}
            user_answers[current_subject][current_question_index] = user_answer
            await state.update_data(full_ent_user_answers=user_answers)
            await send_next_full_ent_question(message, state) # Эта функция должна быть реализована здесь
        else:
            await message.answer("⚠️ Произошла ошибка при обработке вашего ответа.")
    elif current_state == TestState.subject: # Handle answers for obligatory/profile subjects (single test)
        if "all_questions" in data and data["all_questions"]:
            answers = data.get("answers", [])
            answers.append(user_answer)
            await state.update_data(answers=answers)
            await send_next_question(message, state) # Эта функция должна быть реализована здесь
        else:
            await message.answer("Пожалуйста, выберите предмет и начните тест.")
    else:
        await message.answer("Пожалуйста, выберите раздел для начала тестирования.")


async def handle_restart_test(message: types.Message, state: FSMContext) -> None:
    await state.set_data({})
    await cmd_start(message, state)


async def handle_menu(message: types.Message, state: FSMContext) -> None:
    await cmd_start(message, state)


async def cmd_stats(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if user_id in user_statistics:
        stats = user_statistics[user_id]
        report = f"📊 <b>Ваша статистика:</b>\n"
        report += f"Всего пройдено тестов: {stats.get('tests_passed', 0)}\n\n"
        if "scores" in stats and stats["scores"]:
            report += "<b>Средний балл по предметам:</b>\n"
            for subject, scores in stats["scores"].items():
                if scores:
                    average_score = sum(scores) / len(scores)
                    report += f"  - {subject}: {average_score:.2f}%\n"
                else:
                    report += f"  - {subject}: Тесты еще не пройдены.\n"
        else:
            report += "Статистика по предметам пока отсутствует.\n"
        await message.answer(report)
    else:
        await message.answer("📊 Статистика пока отсутствует. Пройдите хотя бы один тест.")

async def handle_start_full_ent(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите первый профильный предмет для пробного ЕНТ:", reply_markup=await get_profile_subjects_keyboard_1())
    await state.set_state(TestState.profile_subject_1_full)
    await state.update_data(full_ent_subjects={})

async def handle_select_profile_1_full(callback: types.CallbackQuery, state: FSMContext) -> None:
    subject_1 = callback.data.split(":")[1]
    await callback.answer(f"Выбран первый профильный предмет: {subject_1}", show_alert=False)
    await state.update_data(full_ent_subjects={"profile1": subject_1})
    await callback.message.edit_text(
        f"Выбран первый профильный предмет: {subject_1}\nВыберите второй профильный предмет для пробного ЕНТ:")
    await callback.message.edit_reply_markup(reply_markup=await get_profile_subjects_keyboard_2(subject_1))
    await state.set_state(TestState.profile_subject_2_full)

async def handle_select_profile_2_full(callback: types.CallbackQuery, state: FSMContext) -> None:
    subject_2 = callback.data.split(":")[1]
    data = await state.get_data()
    subject_1 = data.get("full_ent_subjects", {}).get("profile1")
    if subject_1 and subject_2 != subject_1:
        await callback.answer(f"Выбраны профильные предметы: {subject_1} и {subject_2}", show_alert=False)
        await state.update_data(full_ent_subjects={"profile1": subject_1, "profile2": subject_2})
        await callback.message.edit_text(
            f"Выбраны профильные предметы: {subject_1} и {subject_2}\n⏳ Начинаем генерацию вопросов для пробного ЕНТ...")
        client = state.bot.get('openai_client')
        user_id = callback.from_user.id
        if client:
            await generate_full_ent_questions(client, user_id, state, subject_1=subject_1, subject_2=subject_2)
        else:
            await callback.message.answer("⚠️ Ошибка: Клиент OpenAI не инициализирован.")
    elif not subject_1:
        await callback.answer("Пожалуйста, сначала выберите первый профильный предмет.", show_alert=True)
    else:
        await callback.answer("Вы не можете выбрать один и тот же предмет дважды.", show_alert=True)

async def handle_full_ent_start_subject(message: types.Message, state: FSMContext) -> None:
    chosen_subject = message.text
    data = await state.get_data()
    subjects_map = {
        "История Казахстана": "history",
        "Математическая грамотность": "math_literacy",
        "Грамотность чтения": "reading_literacy",
        data.get("full_ent_subjects", {}).get("profile1"): "profile1",
        data.get("full_ent_subjects", {}).get("profile2"): "profile2",
    }
    subject_key = next((key for name, key in subjects_map.items() if name == chosen_subject), None)

    if subject_key and data.get("full_ent_questions") and data.get("full_ent_questions").get(subject_key):
        await state.update_data(full_ent_current_subject=subject_key)
        await state.update_data(full_ent_current_question_index=0)
        await state.set_state(TestState.full_ent_process)
        await send_next_full_ent_question(message, state) # Реализовать здесь
    else:
        await message.answer("⚠️ Пожалуйста, выберите предмет из предложенной клавиатуры.")

    async def is_full_ent_start_subject(message: types.Message, state: FSMContext) -> bool:
        if await state.get_state() == TestState.full_ent_start_subject:
            data = await state.get_data()
            profile_subject_1 = data.get("full_ent_subjects", {}).get("profile1")
            profile_subject_2 = data.get("full_ent_subjects", {}).get("profile2")
            valid_texts = ["История Казахстана", "Математическая грамотность", "Грамотность чтения"]
            if profile_subject_1:
                valid_texts.append(profile_subject_1)
            if profile_subject_2:
                valid_texts.append(profile_subject_2)
            return message.text in valid_texts
        return False

async def send_next_question(message: Message, state: FSMContext, generated_subjects: list = None) -> None:
    data = await state.get_data()
    current_question_index = data.get("current_question_index", 0)
    current_subject_index = data.get("current_subject_index", 0)
    all_questions = data.get("all_questions", [])
    selected_profile_subjects = data.get("selected_profile_subjects", [])
    subject = data.get("subject")  # Для обязательных предметов

    subjects_list_for_display = generated_subjects if generated_subjects else (selected_profile_subjects if selected_profile_subjects else [subject] if subject else [])

    if current_subject_index < len(all_questions):
        current_subject_questions = all_questions[current_subject_index]
        if current_question_index < len(current_subject_questions):
            question = current_subject_questions[current_question_index]
            subject_name = ""
            if current_subject_index < len(subjects_list_for_display):
                subject_name = subjects_list_for_display[current_subject_index]
            elif subject:
                subject_name = subject

            await message.answer(
                f"<b>Предмет: {subject_name}</b>\n<b>Вопрос {current_question_index + 1}/{len(current_subject_questions)}:</b>\n{question}",
                reply_markup=await get_answer_keyboard()
            )
            await state.update_data(current_question_index=current_question_index + 1)
        else:
            await state.update_data(current_subject_index=current_subject_index + 1, current_question_index=0)
            await send_next_question(message, state, generated_subjects=generated_subjects)
    else:
        await process_test_results(message, state, generated_subjects=generated_subjects)

async def process_test_results(message: Message, state: FSMContext, generated_subjects: list = None) -> None:
    data = await state.get_data()
    all_correct_answers = data.get("all_correct_answers", [])
    answers = data.get("answers", [])
    selected_profile_subjects = data.get("selected_profile_subjects", [])
    test_type = data.get("test_type")
    results_text = "<b>🎉 Результаты теста! 🎉</b>\n\n"
    total_correct = 0
    total_questions = 0
    answer_index = 0

    subjects_list_for_display = generated_subjects if generated_subjects else selected_profile_subjects if selected_profile_subjects else [data.get("subject")] if data.get("subject") else []

    for i, correct_answers_subject in enumerate(all_correct_answers):
        subject_correct_count = 0
        subject_total_questions = len(correct_answers_subject)
        total_questions += subject_total_questions
        subject_name = subjects_list_for_display[i] if i < len(subjects_list_for_display) else f"Предмет {i+1}"
        results_text += f"<b>Предмет: {subject_name}</b>\n"
        for correct_answer in correct_answers_subject:
            user_answer = answers[answer_index].upper() if answer_index < len(answers) else ""
            is_correct = user_answer == correct_answer.upper()
            if is_correct:
                subject_correct_count += 1
                total_correct += 1
                results_text += f"- ✅ Ваш ответ: {user_answer}, Правильный: {correct_answer}\n"
            else:
                results_text += f"- ❌ Ваш ответ: {user_answer}, Правильный: {correct_answer}\n"
            answer_index += 1
        percentage = (subject_correct_count / subject_total_questions) * 100 if subject_total_questions > 0 else 0
        results_text += f"Итого по предмету {subject_name}: {subject_correct_count}/{subject_total_questions} ({percentage:.2f}%)\n\n"

        # Обновление статистики для каждого предмета
        user_id = message.from_user.id
        if user_id not in user_statistics:
            user_statistics[user_id] = {"tests_passed": 0, "scores": {}}
        if subject_name not in user_statistics[user_id]["scores"]:
            user_statistics[user_id]["scores"][subject_name] = []
        user_statistics[user_id]["scores"][subject_name].append(percentage)

    overall_percentage = (total_correct / total_questions) * 100 if total_questions > 0 else 0
    results_text += f"\n<b>Общий итог:</b> {total_correct}/{total_questions} ({overall_percentage:.2f}%)\n"

    await message.answer(results_text, reply_markup=await get_end_test_keyboard())
    user_statistics[user_id]["tests_passed"] = user_statistics[user_id].get("tests_passed", 0) + 1
    logger.info(f"Статистика пользователя {user_id}: {user_statistics[user_id]}")

async def cmd_premium(message: types.Message, state: FSMContext) -> None:
    premium_info = (
        "🚀 <b>Premium подписка для подготовки к ЕНТ</b> 💎\n\n"
        "Оформите Premium и получите неограниченный доступ к генерации вопросов и увеличьте количество вопросов за тест до 10!\n\n"
        "Способы подключения (в разработке):\n"
        "    - ...\n"
        "    - ...\n\n"
        "Следите за обновлениями!"
    )
    await message.answer(premium_info, parse_mode="HTML")


async def send_next_full_ent_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    current_subject = data.get("full_ent_current_subject")
    current_question_index = data.get("full_ent_current_question_index", 0)
    all_questions = data.get("full_ent_questions", {})
    subjects_map = {
        "history": "История Казахстана",
        "math_literacy": "Математическая грамотность",
        "reading_literacy": "Грамотность чтения",
        "profile1": data.get("full_ent_subjects", {}).get("profile1", "Профильный предмет 1"),
        "profile2": data.get("full_ent_subjects", {}).get("profile2", "Профильный предмет 2"),
    }

    if current_subject and current_subject in all_questions:
        questions = all_questions[current_subject]
        if current_question_index < len(questions):
            question = questions[current_question_index]
            subject_name = subjects_map.get(current_subject, "Неизвестный предмет")
            await message.answer(
                f"<b>Предмет: {subject_name}</b>\n<b>Вопрос {current_question_index + 1}/{len(questions)}:</b>\n{question}",
                reply_markup=await get_answer_keyboard(),
            )
            await state.update_data(full_ent_current_question_index=current_question_index + 1)
        else:
            # Вопросы по текущему предмету закончились, предлагаем выбрать следующий
            await state.update_data(full_ent_current_question_index=0)
            await send_full_ent_next_subject_choice(message, state)
    else:
        await message.answer("⚠️ Произошла ошибка при получении следующего вопроса.")

async def send_full_ent_next_subject_choice(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    finished_subjects = data.get("full_ent_user_answers", {}).keys()
    available_subjects = {
        "history": "История Казахстана",
        "math_literacy": "Математическая грамотность",
        "reading_literacy": "Грамотность чтения",
        "profile1": data.get("full_ent_subjects", {}).get("profile1"),
        "profile2": data.get("full_ent_subjects", {}).get("profile2"),
    }
    keyboard_builder = ReplyKeyboardBuilder()
    remaining_subjects = {key: name for key, name in available_subjects.items() if
                          key not in finished_subjects and name is not None}

    if remaining_subjects:
        for key, name in remaining_subjects.items():
            keyboard_builder.button(text=name)
        keyboard_builder.adjust(2)
        await message.answer(
            "Тестирование по текущему предмету завершено. Выберите следующий предмет или нажмите 'Завершить пробный ЕНТ'.",
            reply_markup=keyboard_builder.row(KeyboardButton(text="Завершить пробный ЕНТ")).as_markup(
                resize_keyboard=True, one_time_keyboard=True),
        )
        await state.set_state(TestState.full_ent_process)  # Stay in the process state for choosing next subject
    else:
        await process_full_ent_results(message, state)

async def process_full_ent_results(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    all_correct_answers = data.get("full_ent_correct_answers", {})
    user_answers = data.get("full_ent_user_answers", {})
    subjects_map = {
        "history": "История Казахстана",
        "math_literacy": "Математическая грамотность",
        "reading_literacy": "Грамотность чтения",
        "profile1": data.get("full_ent_subjects", {}).get("profile1", "Профильный предмет 1"),
        "profile2": data.get("full_ent_subjects", {}).get("profile2", "Профильный предмет 2"),
    }
    num_questions = {"history": 20, "math_literacy": 10, "reading_literacy": 10, "profile1": 40, "profile2": 40}
    total_correct = 0
    total_questions = 0
    results_text = "<b>🎉 Результаты пробного ЕНТ! 🎉</b>\n\n"

    for subject_key, correct_answers in all_correct_answers.items():
        subject_name = subjects_map.get(subject_key, "Неизвестный предмет")
        user_subject_answers = user_answers.get(subject_key, {})
        correct_count = 0
        questions_count = num_questions.get(subject_key, 0)
        total_questions += questions_count

        results_text += f"<b>{subject_name}:</b>\n"
        for i in range(questions_count):
            correct_answer = correct_answers[i] if i < len(correct_answers) else None
            user_answer = user_subject_answers.get(i)
            if correct_answer and user_answer == correct_answer:
                correct_count += 1
                total_correct += 1
                results_text += f"  Вопрос {i + 1}: ✅ (Ваш ответ: {user_answer})\n"
            elif correct_answer:
                results_text += f"  Вопрос {i + 1}: ❌ (Ваш ответ: {user_answer if user_answer else 'Нет ответа'}, Правильный ответ: {correct_answer})\n"
            else:
                results_text += f"  Вопрос {i + 1}: ❓ (Правильный ответ не найден)\n"

        score_percent = (correct_count / questions_count) * 100 if questions_count > 0 else 0
        results_text += f"  Результат: {correct_count}/{questions_count} ({score_percent:.2f}%)\n\n"

    overall_score = (total_correct / total_questions) * 100 if total_questions > 0 else 0
    results_text += f"\n<b>Общий результат: {total_correct}/{total_questions} ({overall_score:.2f}%)</b>\n"

    await message.answer(results_text, reply_markup=await get_end_test_keyboard(), parse_mode="HTML")
    await state.set_data({})  # Clear state after the test

async def cmd_premium(message: types.Message, state: FSMContext) -> None:
    premium_info = (
        "🚀 <b>Premium подписка для подготовки к ЕНТ</b> 💎\n\n"
        "Оформите Premium и получите неограниченный доступ к генерации вопросов и увеличьте количество вопросов за тест до 10!\n\n"
        "Способы подключения (в разработке):\n"
        "    - ...\n"
        "    - ...\n\n"
        "Следите за обновлениями!"
    )
    await message.answer(premium_info, parse_mode="HTML")

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_help, Command(commands=["help"]))
    dp.message.register(cmd_premium, Command(commands=["premium"]))
    dp.message.register(handle_obligatory_subjects, lambda message: message.text == "📖 Обязательные предметы")
    dp.callback_query.register(handle_select_obligatory, lambda callback: callback.data.startswith("obligatory:"))
    dp.message.register(handle_profile_subjects, lambda message: message.text == "🧪 Профильные предметы")
    dp.callback_query.register(handle_select_profile_1, lambda callback: callback.data.startswith("profile1:"))
    dp.callback_query.register(handle_select_profile_2, lambda callback: callback.data.startswith("profile2:"))
    dp.message.register(handle_answer, lambda message: message.text.upper() in ("A", "B", "C", "D"))
    dp.message.register(handle_restart_test, lambda message: message.text == "🔄 Пройти ещё раз")
    dp.message.register(handle_menu, lambda message: message.text == "☰ Меню")
    dp.message.register(cmd_stats, lambda message: message.text == "📊 Статистика")
    dp.message.register(handle_start_full_ent, lambda message: message.text == "🧪 Пробный ЕНТ")
    dp.callback_query.register(handle_select_profile_1_full, lambda callback: callback.data.startswith("profile1:"))
    dp.callback_query.register(handle_select_profile_2_full, lambda callback: callback.data.startswith("profile2:"))
    dp.message.register(handle_full_ent_start_subject, lambda message: message.text.in_(["История Казахстана", "Математическая грамотность", "Грамотность чтения"] + PROFILE_SUBJECTS), StateFilter(TestState.full_ent_start_subject))