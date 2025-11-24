from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.localization import translator


def get_settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Returns the settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text=translator.get_text(
                    "change_language_button", lang
                ),
                callback_data="change_language",
            )
        ],
        [
            InlineKeyboardButton(
                text=translator.get_text("back_button", lang),
                callback_data="show_menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
