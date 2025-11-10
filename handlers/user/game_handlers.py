from aiogram import F, Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from games.base import GameStatus
from games.game_registry import game_registry
from games.session_manager import session_manager
from keyboards.main_menu import get_main_menu

from games import (
    russian_tutor,
    translate_word_quiz,
    speech_practice_quiz,
    verb_tense_quiz,
    verb_aspect_quiz,
)


router = Router()


def _get_dynamic_keyboard():
    """Generate keyboard based on available games."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    games = game_registry.get_all_games()
    buttons = []

    for game_id, game in games.items():
        buttons.append(
            [
                InlineKeyboardButton(
                    text=game.display_name, callback_data=f"start_game_{game_id}"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def _cancel_game_logic(user_id: int, bot: Bot):
    """Core logic for cancelling a game."""
    if session_manager.has_active_session(user_id):
        session = session_manager.get_session(user_id)
        game = game_registry.get_game(session.game_id)

        if game:
            await game.end_game(bot, session)

        session_manager.end_session(user_id)
        return "✅ Your game progress has been cancelled."
    else:
        return "You don't have an active game to cancel."


@router.callback_query(lambda c: c.data == "show_games")
async def show_games_list(callback: CallbackQuery):
    """Show list of available games."""
    keyboard = _get_dynamic_keyboard()
    await callback.message.edit_text(
        "🎮 Choose a game to start:", reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("start_game_"))
async def start_game(callback: CallbackQuery, bot: Bot):
    """Start a specific game."""
    game_id = callback.data.split("start_game_")[-1]
    game = game_registry.get_game(game_id)

    if not game:
        await callback.answer("Sorry, this game could not be found.", show_alert=True)
        return

    if session_manager.has_active_session(callback.from_user.id):
        await callback.answer(
            "You already have an active game. Please finish or /cancel it first.",
            show_alert=True,
        )
        return

    try:

        session = await game.start_game(bot, callback.from_user.id, callback.message)
        session_manager.start_session(session)
        await callback.answer()
    except Exception as e:
        await callback.answer(
            f"An error occurred while starting the game: {e}", show_alert=True
        )
        if session_manager.has_active_session(callback.from_user.id):
            session_manager.end_session(callback.from_user.id)


@router.message(Command("cancel"))
async def handle_cancel_command(message: Message, bot: Bot):
    """Handles the /cancel command."""
    response_text = await _cancel_game_logic(message.from_user.id, bot)
    await message.answer(response_text)


@router.callback_query(lambda c: c.data == "cancel_game")
async def handle_cancel_callback(callback: CallbackQuery, bot: Bot):
    """Handles the 'cancel' inline button."""
    user_id = callback.from_user.id
    session = session_manager.get_session(user_id)

    response_text = await _cancel_game_logic(user_id, bot)
    await callback.answer(text="Game cancelled.", show_alert=False)

    updated_keyboard = get_main_menu(session=None)
    final_text = f"{response_text}\n\n📋 Main menu:"

    try:
        if (
            hasattr(session, "menu_message_id")
            and session.menu_message_id == callback.message.message_id
        ):
            await callback.message.edit_text(
                text=final_text, reply_markup=updated_keyboard
            )
        else:
            await callback.message.answer(
                text=final_text, reply_markup=updated_keyboard
            )
        if hasattr(session, "menu_message_id"):
            session.menu_message_id = None
    except Exception:
        await callback.message.answer(text=final_text, reply_markup=updated_keyboard)


@router.callback_query(lambda c: c.data == "continue_game")
async def handle_continue_callback(callback: CallbackQuery, bot: Bot):
    """Handles the 'continue_game' button press."""
    session = session_manager.get_session(callback.from_user.id)
    if not session or session.status != GameStatus.IN_PROGRESS:
        await callback.answer("No active game to continue.", show_alert=True)
        return

    game = game_registry.get_game(session.game_id)
    if game:
        await callback.message.delete()
        await game.resume_game(bot, session)
    else:
        await callback.answer("Error: Could not find the game logic.", show_alert=True)
        session_manager.end_session(callback.from_user.id)

    await callback.answer()


@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot):
    """Handles voice messages and routes them to the active game session."""
    session = session_manager.get_session(message.from_user.id)
    if session and session.status == GameStatus.IN_PROGRESS:
        game = game_registry.get_game(session.game_id)
        if game and hasattr(game, "handle_voice_message"):
            updated_session = await game.handle_voice_message(bot, session, message)

            if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
                session_manager.end_session(message.from_user.id)
            else:
                session_manager.update_session(message.from_user.id, updated_session)
        else:
            await message.reply("This game doesn't support voice input.")
    else:
        await message.reply(
            "To practice your speech, please start a 'Speech Practice' game from the /menu."
        )


@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot):
    """
    Handles all text messages and routes them to the active game session if it exists.
    This is the key handler for chat-based games like RussianTutorGame.
    """
    session = session_manager.get_session(message.from_user.id)

    if session and session.status == GameStatus.IN_PROGRESS:
        game = game_registry.get_game(session.game_id)

        if game and hasattr(game, "handle_message"):

            updated_session = await game.handle_message(bot, session, message)

            if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
                session_manager.end_session(message.from_user.id)
            else:
                session_manager.update_session(message.from_user.id, updated_session)
        else:

            await message.reply(
                "This game is controlled by buttons. To exit, use the /cancel command."
            )
    else:

        pass


@router.callback_query()
async def handle_game_callback(callback: CallbackQuery, bot: Bot):
    """Handle all callbacks during active games."""
    session = session_manager.get_session(callback.from_user.id)
    if not session:

        await callback.message.edit_text(
            "Your gaming session seems to have expired. Please start over from /menu."
        )
        await callback.answer(
            "It seems your game session has expired. Please start a new one.",
            show_alert=True,
        )
        return

    game = game_registry.get_game(session.game_id)
    if not game:
        await callback.answer(
            "An error occurred: the game logic could not be found.", show_alert=True
        )
        session_manager.end_session(callback.from_user.id)
        return

    updated_session = await game.handle_callback(bot, session, callback)

    if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
        session_manager.end_session(callback.from_user.id)
    else:
        session_manager.update_session(callback.from_user.id, updated_session)
