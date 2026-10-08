import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Admin ID
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID not found in .env file")

SOURCE_CHANNEL_ID = int(os.getenv('SOURCE_CHANNEL_ID', 0))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID', 0))

DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')
