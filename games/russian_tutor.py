from aiogram import Bot
from aiogram.types import Message, CallbackQuery
import os
from dotenv import load_dotenv


from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from data.russian_tutor import SYSTEM_PROMPT
from utils.gigachat_ai import get_ai_tutor_response


class RussianTutorGame(BaseGame):
    def __init__(self):
        """Initializes the game."""
        super().__init__(game_id="russian_tutor", display_name="🤖 AI Russian Tutor")

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        """Starts a new game session."""
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

        start_text = (
            "Hello! I am your personal AI tutor for the Russian language.\n\n"
            "You can ask me any questions about grammar, ask me to check your text, "
            "or just chat for practice.\n\n"
            "Type your first message to begin. To end the lesson, send the /menu command."
        )

        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text="Starting the 'AI Russian Tutor' game...",
            reply_markup=None,
        )

        sent_message = await bot.send_message(chat_id=session.chat_id, text=start_text)
        session.message_id = sent_message.message_id

        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        """Resumes an interrupted session."""
        await bot.send_message(
            session.chat_id,
            "Let's continue our Russian lesson! I'm ready for your questions.",
        )

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        """Handles inline button presses."""
        await callback.answer("This game is controlled by text messages.")
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
        session.status = GameStatus.FINISHED
        final_text = (
            "Lesson finished! I hope you've learned something new. "
            "Come back whenever you want to practice more!\n\n"
            "To choose another game, use the /menu command."
        )
        await bot.send_message(chat_id=session.chat_id, text=final_text)


game_registry.register(RussianTutorGame())
