from telethon import TelegramClient, events
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('.env.userbot')

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
USER_SESSION = os.getenv('USER_SESSION', 'anon')
SOURCE_CHANNEL_ID = int(os.getenv('SOURCE_CHANNEL_ID'))

client = TelegramClient(USER_SESSION, API_ID, API_HASH)

def register_userbot_handler(on_new_post):
    @client.on(events.NewMessage(chats=SOURCE_CHANNEL_ID))
    async def handler(event):
        await on_new_post(event)

from src.userbot.bridge import close_bot

async def start_userbot():
    await client.start()
    print('Userbot started')
    try:
        await client.run_until_disconnected()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await client.disconnect()
        await close_bot()
