from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    """Main menu keyboard"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Автопостинг")],
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return kb


def settings_menu_keyboard():
    """Settings menu with inline buttons"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📺 Изменить каналы", callback_data="settings_channels")],
            [InlineKeyboardButton(text="🔗 Изменить ссылки", callback_data="settings_links")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="settings_stats")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_main")]
        ]
    )
    return kb


def auto_posting_toggle_keyboard(is_enabled: bool):
    """Auto posting toggle keyboard"""
    status = "✅ Включить" if not is_enabled else "❌ Выключить"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=status, callback_data="toggle_auto_posting")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_main")]
        ]
    )
    return kb


def channel_selection_keyboard():
    """Channel selection keyboard"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Изменить исходный канал", callback_data="change_source_channel")],
            [InlineKeyboardButton(text="📤 Изменить канал назначения", callback_data="change_target_channel")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_settings")]
        ]
    )
    return kb


def link_settings_keyboard():
    """Link settings keyboard"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать ссылку", callback_data="edit_custom_link")],
            [InlineKeyboardButton(text="🗑️ Удалить ссылку", callback_data="delete_custom_link")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_settings")]
        ]
    )
    return kb


def confirm_post_keyboard(post_id: int):
    """Confirm post keyboard"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_post_{post_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_post_{post_id}")
            ]
        ]
    )
    return kb


def cancel_keyboard():
    """Cancel keyboard"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )
    return kb
