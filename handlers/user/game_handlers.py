from aiogram import F, Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from games.base import GameStatus
from games.game_registry import game_registry
from games.session_manager import session_manager
from keyboards.main_menu import get_main_menu
from utils.localization import translator
from database.user_manager import user_manager

from games import (
    russian_tutor,
    translate_word_quiz,
    speech_practice_quiz,
    verb_tense_quiz,
    verb_aspect_quiz,
    translator_game,
)


router = Router()


async def get_user_language(user_id: int) -> str:
    """Вспомогательная функция для получения языка пользователя с fallback на 'en'."""
    user = await user_manager.get_user(user_id)
    return user.language if user else "en"


async def _get_dynamic_keyboard(lang: str):
    """Generate keyboard with localized game names."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    games = game_registry.get_all_games()
    buttons = []

    for game_id, game in games.items():
        buttons.append(
            [
                InlineKeyboardButton(
                    # Получаем переведенное имя у каждого объекта игры
                    text=game.get_display_name(lang),
                    callback_data=f"start_game_{game_id}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=translator.get_text("back_button", lang), callback_data="show_menu"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def _cancel_game_logic(user_id: int, bot: Bot, lang: str):
    """Core logic for cancelling a game."""
    if await session_manager.has_active_session(user_id):
        session = await session_manager.get_session(user_id)
        game = game_registry.get_game(session.game_id)

        if game:
            await game.end_game(bot, session)

        await session_manager.end_session(user_id)
        return translator.get_text("game_cancelled_success", lang)
    else:
        return translator.get_text("no_active_game_to_cancel", lang)


@router.callback_query(lambda c: c.data == "show_games")
async def show_games_list(callback: CallbackQuery):
    """Show list of available games."""
    lang = await get_user_language(callback.from_user.id)
    # Передаем язык в обновленную функцию
    keyboard = await _get_dynamic_keyboard(lang)
    await callback.message.edit_text(
        translator.get_text("choose_game_prompt", lang), reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("start_game_"))
async def start_game(callback: CallbackQuery, bot: Bot):
    """Start a specific game."""
    lang = await get_user_language(callback.from_user.id)
    game_id = callback.data.split("start_game_")[-1]
    game = game_registry.get_game(game_id)

    if not game:
        await callback.answer(
            translator.get_text("game_not_found_error", lang), show_alert=True
        )
        return

    if await session_manager.has_active_session(callback.from_user.id):
        await callback.answer(
            translator.get_text("active_game_exists_error", lang),
            show_alert=True,
        )
        return

    try:
        session = await game.start_game(bot, callback.from_user.id, callback.message)
        await session_manager.start_session(session)
        await callback.answer()
    except Exception as e:
        error_text = translator.get_text("game_start_error", lang).format(error=e)
        await callback.answer(error_text, show_alert=True)
        if await session_manager.has_active_session(callback.from_user.id):
            await session_manager.end_session(callback.from_user.id)


@router.message(Command("cancel"))
async def handle_cancel_command(message: Message, bot: Bot):
    """Handles the /cancel command."""
    lang = await get_user_language(message.from_user.id)
    response_text = await _cancel_game_logic(message.from_user.id, bot, lang)
    await message.answer(response_text)


@router.callback_query(lambda c: c.data == "cancel_game")
async def handle_cancel_callback(callback: CallbackQuery, bot: Bot):
    """Handles the 'cancel' inline button."""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    session = await session_manager.get_session(user_id)

    response_text = await _cancel_game_logic(user_id, bot, lang)
    await callback.answer(
        text=translator.get_text("game_cancelled_notice", lang), show_alert=False
    )

    updated_keyboard = get_main_menu(lang=lang, session=None)
    main_menu_text = translator.get_text("main_menu_title", lang)
    final_text = f"{response_text}\n\n{main_menu_text}"

    try:
        await callback.message.edit_text(text=final_text, reply_markup=updated_keyboard)
        if hasattr(session, "menu_message_id"):
            session.menu_message_id = None
    except Exception:
        await callback.message.answer(text=final_text, reply_markup=updated_keyboard)


@router.callback_query(lambda c: c.data == "continue_game")
async def handle_continue_callback(callback: CallbackQuery, bot: Bot):
    """Handles the 'continue_game' button press."""
    lang = await get_user_language(callback.from_user.id)
    session = await session_manager.get_session(callback.from_user.id)
    if not session or session.status != GameStatus.IN_PROGRESS:
        await callback.answer(
            translator.get_text("no_active_game_to_continue", lang), show_alert=True
        )
        return

    game = game_registry.get_game(session.game_id)
    if game:
        await callback.message.delete()
        await game.resume_game(bot, session)
    else:
        await callback.answer(
            translator.get_text("game_logic_not_found_error", lang), show_alert=True
        )
        await session_manager.end_session(callback.from_user.id)

    await callback.answer()


@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot):
    """Handles voice messages and routes them to the active game session."""
    lang = await get_user_language(message.from_user.id)
    session = await session_manager.get_session(message.from_user.id)
    if session and session.status == GameStatus.IN_PROGRESS:
        game = game_registry.get_game(session.game_id)
        if game and hasattr(game, "handle_voice_message"):
            updated_session = await game.handle_voice_message(bot, session, message)

            if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
                await session_manager.end_session(message.from_user.id)
            else:
                await session_manager.update_session(
                    message.from_user.id, updated_session
                )
        else:
            await message.reply(translator.get_text("voice_input_not_supported", lang))
    else:
        await message.reply(translator.get_text("start_speech_game_prompt", lang))


@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot):
    """Handles all text messages and routes them to the active game session if it exists."""
    lang = await get_user_language(message.from_user.id)
    session = await session_manager.get_session(message.from_user.id)

    if session and session.status == GameStatus.IN_PROGRESS:
        game = game_registry.get_game(session.game_id)

        if game and hasattr(game, "handle_message"):
            updated_session = await game.handle_message(bot, session, message)
            if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
                await session_manager.end_session(message.from_user.id)
            else:
                await session_manager.update_session(
                    message.from_user.id, updated_session
                )
        else:
            await message.reply(translator.get_text("game_uses_buttons_prompt", lang))
    else:
        pass


@router.callback_query()
async def handle_game_callback(callback: CallbackQuery, bot: Bot):
    """Handle all callbacks during active games."""
    lang = await get_user_language(callback.from_user.id)
    session = await session_manager.get_session(callback.from_user.id)
    if not session:
        await callback.message.edit_text(
            translator.get_text("session_expired_menu_text", lang)
        )
        await callback.answer(
            translator.get_text("session_expired_alert", lang),
            show_alert=True,
        )
        return

    game = game_registry.get_game(session.game_id)
    if not game:
        await callback.answer(
            translator.get_text("game_logic_not_found_error", lang), show_alert=True
        )
        await session_manager.end_session(callback.from_user.id)
        return

    updated_session = await game.handle_callback(bot, session, callback)
    if updated_session.status in [GameStatus.FINISHED, GameStatus.CANCELLED]:
        await session_manager.end_session(callback.from_user.id)
    else:
        await session_manager.update_session(callback.from_user.id, updated_session)
