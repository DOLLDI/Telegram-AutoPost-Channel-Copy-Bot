from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.keyboards.keyboards import (
    main_menu_keyboard, settings_menu_keyboard, auto_posting_toggle_keyboard,
    channel_selection_keyboard, link_settings_keyboard, confirm_post_keyboard, cancel_keyboard
)
from src.database.models import get_db, BotSettings, PendingPost, PostHistory
from src.config import ADMIN_ID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "toggle_auto_posting")
async def toggle_auto_posting_callback(callback: types.CallbackQuery):
    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings:
            await callback.answer("Настройки не найдены", show_alert=True)
            return
        settings.auto_posting_enabled = not settings.auto_posting_enabled
        session.commit()
        status = "включён" if settings.auto_posting_enabled else "выключен"
        await callback.message.edit_text(
            f"Автопостинг {status}.",
            reply_markup=auto_posting_toggle_keyboard(settings.auto_posting_enabled)
        )
        await callback.answer(f"Автопостинг {status}")
    finally:
        session.close()

@router.message(F.text == "🔄 Автопостинг")
async def show_auto_posting_status(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа")
        return
    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings:
            await message.answer("Настройки не найдены")
            return
        status = "включён" if settings.auto_posting_enabled else "выключен"
        await message.answer(
            f"Автопостинг {status}.",
            reply_markup=auto_posting_toggle_keyboard(settings.auto_posting_enabled)
        )
    finally:
        session.close()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.message.delete()

@router.callback_query(F.data == "settings_channels")
async def settings_channels(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=channel_selection_keyboard()
    )

@router.callback_query(F.data == "settings_links")
async def settings_links(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔗 Управление ссылками:",
        reply_markup=link_settings_keyboard()
    )

@router.callback_query(F.data == "settings_stats")
async def settings_stats(callback: types.CallbackQuery):
    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(BotSettings).first()
        posts_count = session.query(PostHistory).count()
        pending_count = session.query(PendingPost).count()
        auto_posting = "Включён" if settings and settings.auto_posting_enabled else "Выключен"
        text = (
            f"<b>Статистика:</b>\n"
            f"Автопостинг: <b>{auto_posting}</b>\n"
            f"Опубликовано постов: <b>{posts_count}</b>\n"
            f"Ожидает модерации: <b>{pending_count}</b>"
        )
        await callback.message.edit_text(text, reply_markup=settings_menu_keyboard(), parse_mode="HTML")
    finally:
        session.close()

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚙️ Меню настроек:",
        reply_markup=settings_menu_keyboard()
    )

@router.callback_query(F.data == "approve_post_ext")
async def approve_post_ext(callback: types.CallbackQuery):
    """Публикация поста, пришедшего напрямую от userbot (без id)"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return True
    await callback.answer("Пост опубликован!", show_alert=False)
    db = get_db()
    session = db.get_session()
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings or not settings.target_channel_id:
            await callback.answer("❌ Не настроен канал назначения!", show_alert=True)
            return True
        src = callback.message
        import re
        orig_text = src.caption if src.caption else (src.text or "\u200b")
        orig_msg_id = None
        m = re.search(r'#orig:(\d+)', orig_text)
        if m:
            orig_msg_id = m.group(1)
        if not orig_msg_id:
            orig_msg_id = str(callback.message.message_id)
        def channel_id_for_link(cid):
            cid = str(cid)
            if cid.startswith('-100'):
                return cid[4:]
            return cid.lstrip('-')
        original_post_url = None
        if settings and settings.source_channel_id and orig_msg_id:
            ch_id = channel_id_for_link(settings.source_channel_id)
            original_post_url = f"https://t.me/c/{ch_id}/{orig_msg_id}"
        buttons = []
        if original_post_url:
            buttons.append(types.InlineKeyboardButton(text="📌 Оригинальный пост", url=original_post_url))
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
        text_for_channel = re.sub(r'\n?#orig:\d+', '', orig_text).strip()
        if not text_for_channel:
            text_for_channel = '\u200b'
        bot = callback.bot
        if src.photo:
            photo = src.photo[-1]
            await bot.send_photo(chat_id=settings.target_channel_id, photo=photo.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.video:
            await bot.send_video(chat_id=settings.target_channel_id, video=src.video.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.document:
            await bot.send_document(chat_id=settings.target_channel_id, document=src.document.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.audio:
            await bot.send_audio(chat_id=settings.target_channel_id, audio=src.audio.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.animation:
            await bot.send_animation(chat_id=settings.target_channel_id, animation=src.animation.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.voice:
            await bot.send_voice(chat_id=settings.target_channel_id, voice=src.voice.file_id, caption=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        elif src.video_note:
            await bot.send_video_note(chat_id=settings.target_channel_id, video_note=src.video_note.file_id, reply_markup=reply_markup)
        elif src.sticker:
            await bot.send_sticker(chat_id=settings.target_channel_id, sticker=src.sticker.file_id, reply_markup=reply_markup)
        elif src.location:
            await bot.send_location(chat_id=settings.target_channel_id, latitude=src.location.latitude, longitude=src.location.longitude, reply_markup=reply_markup)
        elif src.contact:
            await bot.send_contact(chat_id=settings.target_channel_id, phone_number=src.contact.phone_number, first_name=src.contact.first_name, reply_markup=reply_markup)
        elif src.poll:
            await bot.send_message(chat_id=settings.target_channel_id, text=text_for_channel if text_for_channel else "📊 Опрос из оригинального поста", parse_mode="HTML", reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id=settings.target_channel_id, text=text_for_channel, parse_mode="HTML", reply_markup=reply_markup)
        try:
            await src.delete()
        except Exception:
            pass
        try:
            await callback.message.answer("✅ Пост опубликован!", reply_markup=main_menu_keyboard())
        except Exception:
            pass
    finally:
        session.close()
    return True


@router.callback_query(F.data == "reject_post_ext")
async def reject_post_ext(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return True
    await callback.answer("Пост отклонён", show_alert=False)
    try:
        await callback.message.delete()
        await callback.message.answer("⏭️ Пост отклонён.", reply_markup=main_menu_keyboard())
    except Exception:
        pass
    return True



class SettingsStates(StatesGroup):
    """States for settings"""
    waiting_for_source_channel = State()
    waiting_for_target_channel = State()
    waiting_for_custom_link = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 Добро пожаловать в бот для пересылки постов!\n\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав на это действие")
        return
    await message.answer(
        "⚙️ Меню настроек:",
        reply_markup=settings_menu_keyboard()
    )


@router.message(F.text == "❓ Помощь")
async def help_menu(message: types.Message):
    help_text = """❓ Справка и часто задаваемые вопросы:\n\n1️⃣ Как настроить каналы?\n- Перейдите в Настройки → Изменить каналы\n- Следуйте инструкциям бота\n\n2️⃣ Как добавить уникальную ссылку?\n- Перейдите в Настройки → Изменить ссылки\n- Введите свою ссылку (например, реферальную)\n\n3️⃣ Что такое автопостинг?\n- Это режим автоматической пересылки постов без вашего подтверждения\n- Включите/выключите в главном меню\n\n4️⃣ Как получать уведомления?\n- При выключенном автопостинге вы будете получать уведомления на каждый новый пост\n- Вы сможете подтвердить или отклонить пересылку\n\n5️⃣ Как ссылка добавляется в пост?\n- Уникальная ссылка добавляется снизу сообщения\n- Ссылка на оригинальный пост добавляется в виде кнопки\n\n6️⃣ Как изменить ID канала?\n- ID канала можно найти просмотром переписки с BotFather\n- Введите ID в формате: -100XXX или другой ID\n\nЕсли у вас есть вопросы, свяжитесь с администратором."""
    await message.answer(help_text, reply_markup=main_menu_keyboard())


@router.message(SettingsStates.waiting_for_target_channel)
async def process_target_channel(message: types.Message, state: FSMContext):
    """Process target channel ID"""
    try:
        channel_id = int(message.text)
        db = get_db()
        session = db.get_session()
        try:
            settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
            if not settings:
                settings = BotSettings(
                    admin_id=ADMIN_ID,
                    source_channel_id=0,
                    target_channel_id=channel_id
                )
                session.add(settings)
            else:
                settings.target_channel_id = channel_id
            session.commit()
            await message.answer(f"✅ Канал назначения изменен!\n\nТекущий source_channel_id: {settings.source_channel_id}\nТекущий target_channel_id: {settings.target_channel_id}")
        finally:
            session.close()
        await state.clear()
        await message.answer(
            "⚙️ Меню настроек:",
            reply_markup=settings_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID канала")


@router.message(SettingsStates.waiting_for_source_channel)
async def process_source_channel(message: types.Message, state: FSMContext):
    """Process source channel ID"""
    try:
        channel_id = int(message.text)
        db = get_db()
        session = db.get_session()
        try:
            settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
            if not settings:
                settings = BotSettings(
                    admin_id=ADMIN_ID,
                    source_channel_id=channel_id,
                    target_channel_id=0
                )
                session.add(settings)
            else:
                settings.source_channel_id = channel_id
            session.commit()
            await message.answer(f"✅ Исходный канал изменен!\n\nТекущий source_channel_id: {settings.source_channel_id}\nТекущий target_channel_id: {settings.target_channel_id}")
        finally:
            session.close()
        await state.clear()
        await message.answer(
            "⚙️ Меню настроек:",
            reply_markup=settings_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID канала")


@router.callback_query(F.data == "edit_custom_link")
async def edit_custom_link(callback: types.CallbackQuery, state: FSMContext):
    """Edit custom link"""
    await state.set_state(SettingsStates.waiting_for_custom_link)
    await callback.message.edit_text(
        "🔗 Введите уникальную ссылку:",
        reply_markup=cancel_keyboard()
    )


@router.message(SettingsStates.waiting_for_custom_link)
async def process_custom_link(message: types.Message, state: FSMContext):
    """Process custom link"""
    link = message.text
    db = get_db()
    session = db.get_session()
    
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings:
            settings = BotSettings(
                admin_id=ADMIN_ID,
                source_channel_id=0,
                target_channel_id=0,
                custom_link=link
            )
            session.add(settings)
        else:
            settings.custom_link = link
        
        session.commit()
        await message.answer("✅ Ссылка изменена!")
    finally:
        session.close()
    
    await state.clear()
    await message.answer(
        "⚙️ Меню настроек:",
        reply_markup=settings_menu_keyboard()
    )


@router.callback_query(F.data == "delete_custom_link")
async def delete_custom_link(callback: types.CallbackQuery):
    """Delete custom link"""
    db = get_db()
    session = db.get_session()
    
    try:
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if settings:
            settings.custom_link = ""
            session.commit()
        
        await callback.answer("✅ Ссылка удалена!")
    finally:
        session.close()
    
    await callback.message.edit_text(
        "🔗 Управление ссылками:\n\nСсылка не установлена",
        reply_markup=link_settings_keyboard()
    )



@router.callback_query(F.data.startswith("approve_post_"))
async def approve_post(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if not data[-1].isdigit():
        return
    post_id = int(data[-1])
    """Approve and copy post"""
    post_id = int(callback.data.split("_")[-1])
    db = get_db()
    session = db.get_session()
    try:
        pending_post = session.query(PendingPost).filter_by(id=post_id).first()
        if not pending_post:
            await callback.answer("❌ Пост не найден!")
            return
        settings = session.query(BotSettings).filter_by(admin_id=ADMIN_ID).first()
        if not settings:
            await callback.answer("❌ Настройки не найдены!")
            return
        bot = callback.bot
        try:
            channel_num = str(abs(pending_post.channel_id))[3:]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                text="📌 Оригинальный пост",
                url=f"https://t.me/c/{channel_num}/{pending_post.message_id}"
            )]])
            caption_text = pending_post.content or ""
            if pending_post.has_media:
                sent_message = await bot.copy_message(
                    chat_id=settings.target_channel_id,
                    from_chat_id=pending_post.channel_id,
                    message_id=pending_post.message_id,
                    caption=caption_text if caption_text else None,
                    reply_markup=keyboard
                )
            else:
                sent_message = await bot.send_message(
                    chat_id=settings.target_channel_id,
                    text=caption_text if caption_text else "📄 Текстовое сообщение",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            history = PostHistory(
                original_message_id=pending_post.message_id,
                original_channel_id=pending_post.channel_id,
                reposted_message_id=sent_message.message_id,
                target_channel_id=settings.target_channel_id,
                original_link=f"https://t.me/c/{channel_num}/{pending_post.message_id}"
            )
            session.add(history)
            pending_post.status = 'approved'
            session.commit()
            await callback.message.edit_text(
                f"✅ Пост одобрен и переслан!\n\n{pending_post.content[:200]}..."
            )
            logger.info(f"✅ Пост {pending_post.message_id} одобрен и скопирован")
            await callback.answer("✅ Пост успешно скопирован!")
        except Exception as e:
            logger.error(f"❌ Ошибка при копировании поста: {e}")
            await callback.answer(f"❌ Ошибка при копировании: {str(e)}")
    finally:
        session.close()



@router.callback_query(F.data.startswith("reject_post_"))
async def reject_post(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if not data[-1].isdigit():
        return
    post_id = int(data[-1])
    """Reject post"""
    post_id = int(callback.data.split("_")[-1])
    db = get_db()
    session = db.get_session()
    try:
        pending_post = session.query(PendingPost).filter_by(id=post_id).first()
        if not pending_post:
            await callback.answer("❌ Пост не найден!")
            return
        pending_post.status = 'rejected'
        session.commit()
        await callback.message.edit_text(
            f"❌ Пост отклонен!\n\n{pending_post.content[:200]}..."
        )
        logger.info(f"❌ Пост {pending_post.message_id} отклонен")
        await callback.answer("❌ Пост отклонен!")
    finally:
        session.close()


@router.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    """Cancel action"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "change_source_channel")
async def change_source_channel(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_source_channel)
    await callback.message.edit_text(
        "Введите ID исходного канала:",
        reply_markup=cancel_keyboard()
    )

@router.callback_query(F.data == "change_target_channel")
async def change_target_channel(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_target_channel)
    await callback.message.edit_text(
        "Введите ID канала назначения:",
        reply_markup=cancel_keyboard()
    )
