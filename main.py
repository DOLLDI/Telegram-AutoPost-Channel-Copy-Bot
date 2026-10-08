"""
Copyright User-bot v2: Userbot + Bot API
main.py — только aiogram-бот (админ-панель, подтверждения, настройки)
userbot_main.py — userbot (чтение исходного канала)
"""
from aiogram import Bot, Dispatcher
from src.handlers import commands
import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv('.env.userbot')

BOT_TOKEN = os.getenv('BOT_TOKEN')

def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(commands.router)
    print('Aiogram bot started')
    try:
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")

if __name__ == "__main__":
    main()
