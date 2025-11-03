from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from games.base import GameStatus

def get_main_menu(session=None):
    """Get main menu keyboard, dynamically showing buttons based on session status."""
    buttons = []
    if session and session.status == GameStatus.IN_PROGRESS:
        buttons.append(
            [InlineKeyboardButton(text="▶️ Continue the game", callback_data="continue_game")]
        )
        buttons.append(
            [InlineKeyboardButton(text="❌ Cancel the game", callback_data="cancel_game")]
        )
    else:
        buttons.append(
            [InlineKeyboardButton(text="🎮 Select a game", callback_data="show_games")]
        )
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)
