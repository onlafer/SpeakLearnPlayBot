from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from enums.languages import Language
from utils.localization import translator


def get_language_keyboard(
    lang: str, show_back_button: bool = False
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для выбора языка.

    :param show_back_button: Если True, будет добавлена кнопка "Назад".
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="🇸🇦 Arabic", callback_data=f"set_language:{Language.AR.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇨🇳 Chinese", callback_data=f"set_language:{Language.ZH.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇬🇧 English", callback_data=f"set_language:{Language.EN.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇫🇷 French", callback_data=f"set_language:{Language.FR.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇮🇷 Persian", callback_data=f"set_language:{Language.FA.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇪🇸 Spanish", callback_data=f"set_language:{Language.ES.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇻🇳 Vietnamese", callback_data=f"set_language:{Language.VI.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇯🇵 Japanese", callback_data=f"set_language:{Language.JA.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇷🇺 Russian", callback_data=f"set_language:{Language.RU.value}"
            )
        ],
    ]

    if show_back_button:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=translator.get_text("back_button", lang),
                    callback_data="show_settings",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

