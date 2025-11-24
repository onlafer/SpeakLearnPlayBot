from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from games.base import GameStatus
from utils.localization import translator

def get_main_menu(lang: str, session=None) -> InlineKeyboardMarkup:
    """Get main menu keyboard, dynamically showing buttons based on session status."""
    buttons = []
    if session and session.status == GameStatus.IN_PROGRESS:
        buttons.append([
            InlineKeyboardButton(
                text=translator.get_text("continue_game_button", lang),
                callback_data="continue_game"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=translator.get_text("cancel_game_button", lang),
                callback_data="cancel_game"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text=translator.get_text("select_game_button", lang),
                callback_data="show_games"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text=translator.get_text("settings_button", lang),
            callback_data="show_settings"
        )
    ])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)
