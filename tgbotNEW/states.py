from aiogram.fsm.state import State, StatesGroup

class TestState(StatesGroup):
    subject = State()  # Состояние выбора обязательного предмета
    profile_subject_1 = State()  # Состояние выбора первого профильного предмета
    profile_subject_2 = State()  # Состояние выбора второго профильного предмета
    question = State()  # Состояние во время теста (отображение вопроса)
    answer = State()  # Состояние ожидания ответа пользователя
    results = State()  # Состояние отображения результатов

    full_ent_start = State() # Начало пробного ЕНТ
    full_ent_profile_subject_1 = State() # Выбор первого профильного для ЕНТ
    full_ent_profile_subject_2 = State() # Выбор второго профильного для ЕНТ
    full_ent_start_subject = State() # Выбор первого предмета для сдачи в пробном ЕНТ
    full_ent_process = State() # Процесс сдачи пробного ЕНТ
    full_ent_results = State() # Результаты пробного ЕНТ