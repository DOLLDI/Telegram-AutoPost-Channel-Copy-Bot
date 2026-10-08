import asyncio
from src.userbot.userbot import client, register_userbot_handler, start_userbot
from src.userbot.bridge import process_telethon_event

if __name__ == "__main__":
    register_userbot_handler(process_telethon_event)
    asyncio.run(start_userbot())
