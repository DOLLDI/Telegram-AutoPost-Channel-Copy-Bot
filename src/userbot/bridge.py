
import asyncio
from telethon.tl.types import Message
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv
from aiogram.types import FSInputFile
import tempfile
from src.database.models import get_db, BotSettings

load_dotenv('.env.userbot')

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CUSTOM_LINK = os.getenv('CUSTOM_LINK', '')

bot = Bot(token=BOT_TOKEN)

def get_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="approve_post_ext"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data="reject_post_ext")
            ]
        ]
    )

async def send_post_for_moderation(text, media=None):
    """Отправить пост админу с клавиатурой подтверждения"""
    reply_markup = get_confirm_keyboard()
    if media:
        mtype = media.get('type')
        file_path = media.get('file_path')
        caption = text if text else (CUSTOM_LINK or '\u200b')
        fs_file = FSInputFile(file_path)
        if mtype == 'photo':
            await bot.send_photo(chat_id=ADMIN_ID, photo=fs_file, caption=caption, reply_markup=reply_markup)
        elif mtype == 'video':
            await bot.send_video(chat_id=ADMIN_ID, video=fs_file, caption=caption, reply_markup=reply_markup)
        else:
            await bot.send_document(chat_id=ADMIN_ID, document=fs_file, caption=caption, reply_markup=reply_markup)
        try:
            os.remove(file_path)
        except Exception:
            pass
    else:
        safe_text = text if text else (CUSTOM_LINK or '\u200b')
        await bot.send_message(chat_id=ADMIN_ID, text=safe_text, reply_markup=reply_markup)

async def process_telethon_event(event):
    text = event.text or ''
    media = None
    mtype = None

    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(BotSettings).first()
        custom_link = settings.custom_link if settings and settings.custom_link else ''
        auto_posting = settings.auto_posting_enabled if settings else False
    finally:
        session.close()

    if getattr(event, 'photo', None):
        mtype = 'photo'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp.close()
        file_path = tmp.name
        await event.download_media(file=file_path)
        media = {'type': 'photo', 'file_path': file_path}
    elif getattr(event, 'video', None):
        mtype = 'video'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tmp.close()
        file_path = tmp.name
        await event.download_media(file=file_path)
        media = {'type': 'video', 'file_path': file_path}
    elif getattr(event, 'document', None):
        mtype = 'document'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
        tmp.close()
        file_path = tmp.name
        await event.download_media(file=file_path)
        media = {'type': 'document', 'file_path': file_path}

    if custom_link:
        if text:
            text += f"\n\n{custom_link}"
        else:
            text = custom_link

    orig_id = getattr(event, 'id', None)
    if orig_id:
        text = (text or '') + f"\n#orig:{orig_id}"

    if not text:
        text = '\u200b'

    if auto_posting and settings:
        try:
            from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
            target_channel_id = settings.target_channel_id
            orig_id = getattr(event, 'id', None)
            orig_channel_id = getattr(event.chat, 'id', None)
            orig_link = None
            if orig_id and orig_channel_id:
                orig_link = f"https://t.me/c/{abs(orig_channel_id)}/{orig_id}"
                reply_markup = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="📌 Оригинальный пост", url=orig_link)]]
                )
            else:
                reply_markup = None

            if media:
                mtype = media.get('type')
                file_path = media.get('file_path')
                fs_file = FSInputFile(file_path)
                if mtype == 'photo':
                    await bot.send_photo(chat_id=target_channel_id, photo=fs_file, caption=text, reply_markup=reply_markup)
                elif mtype == 'video':
                    await bot.send_video(chat_id=target_channel_id, video=fs_file, caption=text, reply_markup=reply_markup)
                else:
                    await bot.send_document(chat_id=target_channel_id, document=fs_file, caption=text, reply_markup=reply_markup)
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            else:
                await bot.send_message(chat_id=target_channel_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            print(f"[userbot] Ошибка автопостинга: {e}")
    else:
        await send_post_for_moderation(text, media=media)

async def close_bot():
    await bot.session.close()
