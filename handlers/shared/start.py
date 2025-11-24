"""Start command handler."""

from aiogram import Router
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from keyboards.main_menu import get_main_menu
from keyboards.language_selection import get_language_keyboard
from keyboards.settings_keyboard import get_settings_keyboard
from games.session_manager import session_manager
from database.user_manager import user_manager
from utils.bot_helpers import safe_edit_message
from utils.localization import translator


router = Router()


async def get_user_language(user_id: int) -> str:
    """Вспомогательная функция для получения языка пользователя с fallback на 'en'."""
    user = await user_manager.get_user(user_id)
    return user.language if user else "en"


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    user = await user_manager.get_user(message.from_user.id)
    lang = user.language if user else "en"

    if not user:
        try:
            photo = FSInputFile("static/images/welcome_image.jpg")
            await message.answer_photo(photo)
        except Exception as e:
            print(f"Ошибка при отправке изображения: {e}")

        welcome_text = translator.get_text("start_new_user_welcome", "en")
        await message.answer(
            welcome_text, reply_markup=get_language_keyboard(lang=lang)
        )
        return

    session = await session_manager.get_session(message.from_user.id)
    text = translator.get_text("start_existing_user_welcome", lang)

    sent_message = await message.answer(text, reply_markup=get_main_menu(lang, session))
    if session:
        session.menu_message_id = sent_message.message_id


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Handle /menu command."""
    lang = await get_user_language(message.from_user.id)
    session = await session_manager.get_session(message.from_user.id)
    text = translator.get_text("main_menu_title", lang)
    sent_message = await message.answer(text, reply_markup=get_main_menu(lang, session))
    if session:
        session.menu_message_id = sent_message.message_id


@router.callback_query(lambda c: c.data == "show_menu")
async def handle_show_menu_callback(callback: CallbackQuery):
    """Handles the 'Menu' button press."""
    await callback.answer()
    lang = await get_user_language(callback.from_user.id)
    session = await session_manager.get_session(callback.from_user.id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=translator.get_text("main_menu_title", lang),
        reply_markup=get_main_menu(lang, session),
    )


@router.callback_query(lambda c: c.data == "show_settings")
async def handle_show_settings(callback: CallbackQuery):
    """Shows the settings menu."""
    await callback.answer()
    lang = await get_user_language(callback.from_user.id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=translator.get_text("settings_menu_title", lang),
        reply_markup=get_settings_keyboard(lang),
    )


@router.callback_query(lambda c: c.data == "change_language")
async def handle_change_language(callback: CallbackQuery):
    """Shows the language selection menu."""
    await callback.answer()
    lang = await get_user_language(callback.from_user.id)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=translator.get_text("change_language_prompt", lang),
        reply_markup=get_language_keyboard(lang=lang, show_back_button=True),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("set_language:"))
async def handle_language_selection(callback: CallbackQuery):
    """Handle language selection."""
    lang = callback.data.split(":")[-1]
    await user_manager.update_language(callback.from_user.id, lang)

    await callback.answer(translator.get_text("language_selected_notice", lang))

    session = await session_manager.get_session(callback.from_user.id)
    text = translator.get_text("start_existing_user_welcome", lang)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=get_main_menu(lang, session),
    )
