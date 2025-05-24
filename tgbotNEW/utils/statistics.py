import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Временное хранилище статистики в памяти (для простоты примера)
user_statistics = {}
FREE_GENERATE_LIMIT = 4
GENERATE_WINDOW = timedelta(days=1)

async def get_user_statistics():
    """Асинхронная функция для получения статистики пользователей (например, из БД)"""
    return user_statistics

async def is_premium_user(user_id: int):
    """Асинхронная функция для проверки, является ли пользователь премиум-пользователем"""
    stats = await get_user_statistics()
    return stats.get(user_id, {}).get("is_premium", False)

async def can_generate_questions(user_id: int) -> bool:
    """Проверяет, может ли пользователь генерировать вопросы (с учетом лимитов)"""
    if await is_premium_user(user_id):
        return True
    stats = await get_user_statistics()
    user_data = stats.get(user_id, {})
    last_generations = user_data.get("last_generations", [])
    now = datetime.now()
    within_window = [gen_time for gen_time in last_generations if now - gen_time < GENERATE_WINDOW]
    return len(within_window) < FREE_GENERATE_LIMIT

async def increment_generation_counter(user_id: int) -> None:
    """Увеличивает счетчик генераций вопросов для пользователя"""
    if await is_premium_user(user_id):
        return
    stats = await get_user_statistics()
    user_data = stats.get(user_id, {})
    last_generations = user_data.get("last_generations", [])
    last_generations.append(datetime.now())
    # Оставляем только генерации за последний день
    now = datetime.now()
    updated_generations = [gen_time for gen_time in last_generations if now - gen_time < GENERATE_WINDOW]
    user_data["last_generations"] = updated_generations
    stats[user_id] = user_data
    logger.info(f"Счетчик генераций пользователя {user_id} обновлен: {updated_generations}")

async def update_premium_status(user_id: int, is_premium: bool) -> None:
    """Обновляет статус премиум-пользователя"""
    stats = await get_user_statistics()
    user_data = stats.get(user_id, {})
    user_data["is_premium"] = is_premium
    stats[user_id] = user_data
    logger.info(f"Статус Premium пользователя {user_id} обновлен: {is_premium}")

async def reset_daily_generation_counter(user_id: int) -> None:
    """Сбрасывает счетчик ежедневных генераций пользователя"""
    stats = await get_user_statistics()
    user_data = stats.get(user_id, {})
    user_data["last_generations"] = []
    stats[user_id] = user_data
    logger.info(f"Счетчик генераций пользователя {user_id} сброшен.")

async def clear_user_statistics(user_id: int) -> None:
    """Удаляет статистику пользователя"""
    stats = await get_user_statistics()
    if user_id in stats:
        del stats[user_id]
        logger.info(f"Статистика пользователя {user_id} удалена.")

# Пример использования (необязательно включать в финальную версию, если вы не тестируете здесь)
# async def main():
#     user_id = 123
#     print(f"Может генерировать (начало): {await can_generate_questions(user_id)}")
#     for _ in range(5):
#         if await can_generate_questions(user_id):
#             await increment_generation_counter(user_id)
#             print(f"Генерация. Осталось: {FREE_GENERATE_LIMIT - len(user_statistics.get(user_id, {}).get('last_generations', []))}")
#         else:
#             print("Лимит генераций исчерпан.")
#             break
#     print(f"Может генерировать (после): {await can_generate_questions(user_id)}")
#     await update_premium_status(user_id, True)
#     print(f"Может генерировать (после Premium): {await can_generate_questions(user_id)}")
#     await reset_daily_generation_counter(user_id)
#     print(f"Может генерировать (после сброса): {await can_generate_questions(user_id)}")
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())