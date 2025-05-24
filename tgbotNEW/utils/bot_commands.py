# utils/bot_commands.py
from aiogram import Bot
from aiogram.types import BotCommand

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="ℹ️ Информация"),
        BotCommand(command="premium", description="💎 Premium")
    ]
    await bot.set_my_commands(commands)