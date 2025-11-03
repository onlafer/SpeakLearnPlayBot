"""Start command handler."""

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.main_menu import get_main_menu
from games.session_manager import session_manager

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    session = session_manager.get_session(message.from_user.id)
    text = (
        "👋 Welcome to SpeakLearnPlayBot!\n\n"
        "⬆️ Lets improve your Russian by chatting\n\n"
        "Select a game from the menu:"
    )

    sent_message = await message.answer(text, reply_markup=get_main_menu(session))
    if session:
        session.menu_message_id = sent_message.message_id


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Handle /menu command."""
    session = session_manager.get_session(message.from_user.id)
    text = "📋 Game menu:"
    sent_message = await message.answer(text, reply_markup=get_main_menu(session))
    if session:
        session.menu_message_id = sent_message.message_id


@router.callback_query(lambda c: c.data == "show_menu")
async def handle_show_menu_callback(callback: CallbackQuery):
    """
    Handles the 'Menu' button press from within a game.
    Does NOT cancel the game. Just shows the main menu.
    """
    await callback.answer()

    session = session_manager.get_session(callback.from_user.id)
    await callback.message.edit_text(
        text="📋 Main menu:",
        reply_markup=get_main_menu(session)
    )
