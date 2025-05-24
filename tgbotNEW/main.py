import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import BOT_TOKEN, OPENAI_API_KEY
from handlers import register_handlers
from openai import OpenAI
from aiogram.fsm.storage.memory import MemoryStorage
from utils.bot_commands import set_bot_commands
from aiogram.client.default import DefaultBotProperties

async def main():
    logging.basicConfig(level=logging.INFO)
    storage = MemoryStorage()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) 
    dp = Dispatcher(storage=storage)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        dp['openai_client'] = client
    except Exception as e:
        logging.error(f"Ошибка инициализации OpenAI: {e}")
        return

    register_handlers(dp)
    await set_bot_commands(bot)

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())