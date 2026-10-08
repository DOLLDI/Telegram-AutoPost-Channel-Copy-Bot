from aiogram import Router, types, Bot
from aiogram.types import Message
from src.database.models import get_db, BotSettings, PostHistory, PendingPost
from src.keyboards.keyboards import confirm_post_keyboard
from src.config import ADMIN_ID
import logging

router = Router()
logger = logging.getLogger(__name__)


async def should_track_message(message: Message, source_channel_id: int) -> bool:
    """Check if message should be tracked"""
    if message.chat.id != source_channel_id:
        return False
    
    if message.new_chat_members or message.left_chat_member:
        return False
    
    return True


async def format_message_with_link(message: Message, custom_link: str) -> tuple[str, list]:
    """Format message text and prepare keyboard with links"""
    text = ""
    buttons = []

    if message.caption:
        text = message.caption
    elif message.text:
        text = message.text

    if custom_link:
        if text:
            text += f"\n\n{custom_link}"
        else:
            text = custom_link

    if not text:
        text = "\u200b" 

    original_link = f"https://t.me/c/{abs(message.chat.id)}/{message.message_id}"
    buttons.append(types.InlineKeyboardButton(
        text="📌 Оригинальный пост",
        url=original_link
    ))

    logger.info(f"[format_message_with_link] Итоговый текст для поста: {repr(text)}")

    return text, buttons


async def copy_message_with_media(
    bot: Bot,
    source_message: Message,
    target_channel_id: int,
    text: str,
    buttons: list
) -> int:
    """Copy message maintaining all media and formatting"""
    
    reply_markup = None
    if buttons:
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    
    if source_message.photo:
        photo = source_message.photo[-1]
        sent_message = await bot.send_photo(
            chat_id=target_channel_id,
            photo=photo.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.document:
        sent_message = await bot.send_document(
            chat_id=target_channel_id,
            document=source_message.document.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.video:
        sent_message = await bot.send_video(
            chat_id=target_channel_id,
            video=source_message.video.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.audio:
        sent_message = await bot.send_audio(
            chat_id=target_channel_id,
            audio=source_message.audio.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.animation:
        sent_message = await bot.send_animation(
            chat_id=target_channel_id,
            animation=source_message.animation.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.voice:
        sent_message = await bot.send_voice(
            chat_id=target_channel_id,
            voice=source_message.voice.file_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif source_message.video_note:
        sent_message = await bot.send_video_note(
            chat_id=target_channel_id,
            video_note=source_message.video_note.file_id,
            reply_markup=reply_markup
        )
    elif source_message.sticker:
        sent_message = await bot.send_sticker(
            chat_id=target_channel_id,
            sticker=source_message.sticker.file_id,
            reply_markup=reply_markup
        )
    elif source_message.location:
        sent_message = await bot.send_location(
            chat_id=target_channel_id,
            latitude=source_message.location.latitude,
            longitude=source_message.location.longitude,
            reply_markup=reply_markup
        )
    elif source_message.contact:
        sent_message = await bot.send_contact(
            chat_id=target_channel_id,
            phone_number=source_message.contact.phone_number,
            first_name=source_message.contact.first_name,
            reply_markup=reply_markup
        )
    elif source_message.poll:
        sent_message = await bot.send_message(
            chat_id=target_channel_id,
            text=text if text else "📊 Опрос из оригинального поста",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        sent_message = await bot.send_message(
            chat_id=target_channel_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return sent_message.message_id


@router.channel_post()
async def handle_channel_message(message: Message, bot: Bot):
    """Handle incoming channel messages"""
    
    db = get_db()
    session = db.get_session()
    
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings:
            logger.warning(f"No settings found for admin {ADMIN_ID}")
            return

        if message.chat.id != settings.source_channel_id:
            return

        if not await should_track_message(message, settings.source_channel_id):
            return
        
        text, buttons = await format_message_with_link(message, settings.custom_link)

        if settings.auto_posting_enabled:
            try:
                channel_num = str(abs(message.chat.id))[3:]
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                    text="📌 Оригинальный пост",
                    url=f"https://t.me/c/{channel_num}/{message.message_id}"
                )]])

                if message.photo:
                    photo = message.photo[-1]
                    sent_message = await bot.send_photo(
                        chat_id=settings.target_channel_id,
                        photo=photo.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.video:
                    sent_message = await bot.send_video(
                        chat_id=settings.target_channel_id,
                        video=message.video.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.document:
                    sent_message = await bot.send_document(
                        chat_id=settings.target_channel_id,
                        document=message.document.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.audio:
                    sent_message = await bot.send_audio(
                        chat_id=settings.target_channel_id,
                        audio=message.audio.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.animation:
                    sent_message = await bot.send_animation(
                        chat_id=settings.target_channel_id,
                        animation=message.animation.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.voice:
                    sent_message = await bot.send_voice(
                        chat_id=settings.target_channel_id,
                        voice=message.voice.file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                elif message.video_note:
                    sent_message = await bot.send_video_note(
                        chat_id=settings.target_channel_id,
                        video_note=message.video_note.file_id,
                        reply_markup=keyboard
                    )
                elif message.sticker:
                    sent_message = await bot.send_sticker(
                        chat_id=settings.target_channel_id,
                        sticker=message.sticker.file_id,
                        reply_markup=keyboard
                    )
                elif message.location:
                    sent_message = await bot.send_location(
                        chat_id=settings.target_channel_id,
                        latitude=message.location.latitude,
                        longitude=message.location.longitude,
                        reply_markup=keyboard
                    )
                elif message.contact:
                    sent_message = await bot.send_contact(
                        chat_id=settings.target_channel_id,
                        phone_number=message.contact.phone_number,
                        first_name=message.contact.first_name,
                        reply_markup=keyboard
                    )
                elif message.poll:
                    sent_message = await bot.send_message(
                        chat_id=settings.target_channel_id,
                        text=text if text else "📊 Опрос из оригинального поста",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    sent_message = await bot.send_message(
                        chat_id=settings.target_channel_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )

                post_history = PostHistory(
                    original_message_id=message.message_id,
                    original_channel_id=message.chat.id,
                    reposted_message_id=sent_message.message_id,
                    target_channel_id=settings.target_channel_id,
                    original_link=f"https://t.me/c/{channel_num}/{message.message_id}"
                )
                session.add(post_history)
                session.commit()

                logger.info(f"Auto-posted message {message.message_id} to {settings.target_channel_id}")
                return 
            except Exception as e:
                logger.error(f"Error auto-posting message: {e}")
        else:
            has_media = bool(
                message.photo or message.video or message.audio or 
                message.document or message.animation or message.voice or 
                message.video_note or message.sticker or message.location or 
                message.contact or message.poll
            )
            
            pending_post = PendingPost(
                message_id=message.message_id,
                channel_id=message.chat.id,
                content=text,
                has_media=has_media
            )
            session.add(pending_post)
            session.commit()
            
            notification_text = f"📬 Новый пост из канала #{message.chat.id}:\n\n{text}"
            
            try:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=notification_text,
                    reply_markup=confirm_post_keyboard(pending_post.id),
                    parse_mode="HTML"
                )
                logger.info(f"Sent notification for message {message.message_id} to admin")
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    except Exception as e:
        logger.error(f"Error handling channel message: {e}")
    finally:
        session.close()


@router.edited_channel_post()
async def handle_edited_channel_message(message: Message, bot: Bot):
    """Handle edited channel messages"""
    
    db = get_db()
    session = db.get_session()
    
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        
        if not settings or message.chat.id != settings.source_channel_id:
            return
        
        post_history = session.query(PostHistory).filter_by(
            original_message_id=message.message_id,
            original_channel_id=message.chat.id
        ).first()
        
        if not post_history:
            return
        
        text, buttons = await format_message_with_link(message, settings.custom_link)
        
        try:
            reply_markup = None
            if buttons:
                reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
            
            await bot.edit_message_caption(
                chat_id=post_history.target_channel_id,
                message_id=post_history.reposted_message_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            logger.info(f"Updated reposted message {post_history.reposted_message_id}")
        except Exception as e:
            logger.warning(f"Could not edit message: {e}")
    
    except Exception as e:
        logger.error(f"Error handling edited message: {e}")
    finally:
        session.close()
