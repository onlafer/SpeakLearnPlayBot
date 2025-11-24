from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from gigachat.models import MessagesRole

from utils.localization import translator
from database.user_manager import user_manager

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from data.russian_tutor import SYSTEM_PROMPT
from utils.gigachat_ai import get_ai_tutor_response
from utils.bot_helpers import safe_edit_message

async def get_user_language(user_id: int) -> str:
    """Gets user language with a fallback to 'en'."""
    user = await user_manager.get_user(user_id)
    return user.language if user else "en"

class RussianTutorGame(BaseGame):
    def __init__(self):
        """Initializes the game."""
        super().__init__(game_id="russian_tutor")

    def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        return translator.get_text("game_russian_tutor_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        """Starts a new game session."""
        lang = await get_user_language(user_id) # Получаем язык
        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            game_state={
                "history": [{"role": MessagesRole.SYSTEM, "content": SYSTEM_PROMPT}]
            },
        )

        start_text = translator.get_text("game_russian_tutor_start_text", lang)
        starting_text = translator.get_text("game_russian_tutor_starting", lang)

        new_message_id = await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=starting_text,
            reply_markup=None,
        )
        session.message_id = new_message_id

        sent_message = await bot.send_message(chat_id=session.chat_id, text=start_text)
        session.message_id = sent_message.message_id

        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        """Resumes an interrupted session."""
        lang = await get_user_language(session.user_id) # Получаем язык
        resume_text = translator.get_text("game_russian_tutor_resume_text", lang)
        await bot.send_message(session.chat_id, resume_text)

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        """Handles inline button presses."""
        lang = await get_user_language(session.user_id)
        callback_text = translator.get_text("game_russian_tutor_callback_text", lang)
        await callback.answer(callback_text)
        return session

    async def handle_message(
        self, bot: Bot, session: GameSession, message: Message
    ) -> GameSession:
        """Handles a text message from the user."""
        user_text = message.text
        session.game_state["history"].append(
            {"role": MessagesRole.USER, "content": user_text}
        )
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")
        ai_response = await get_ai_tutor_response(session.game_state["history"])
        session.game_state["history"].append(
            {"role": MessagesRole.ASSISTANT, "content": ai_response}
        )
        await bot.send_message(chat_id=session.chat_id, text=ai_response)
        return session

    async def end_game(self, bot: Bot, session: GameSession):
        """Ends the game session."""
        lang = await get_user_language(session.user_id)
        session.status = GameStatus.FINISHED
        final_text = translator.get_text("game_russian_tutor_end_text", lang)
        await bot.send_message(chat_id=session.chat_id, text=final_text)

game_registry.register(RussianTutorGame())
