from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.verb_aspect_quiz import VERB_ASPECT_QUESTIONS, VERB_ASPECT_THEORY
from data.positive_feedback import positive_feedbacks
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry

class VerbAspectQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="verb_aspect_quiz", display_name="📖 Test: Verb Aspects")

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=-1,
            score=0,
        )

        await self._send_theory(bot, session)
        return session

    async def _send_theory(self, bot: Bot, session: GameSession):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ I'm ready, let's start!", callback_data="start_quiz")]
            ]
        )
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=VERB_ASPECT_THEORY,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def resume_game(self, bot: Bot, session: GameSession):
        await bot.send_message(session.chat_id, "Ok, let's continue with the Verb Aspect test!")
        await self._send_question(bot, session, as_new_message=True)

    async def _send_question(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        question_index = session.current_question
        question = VERB_ASPECT_QUESTIONS[question_index]
        buttons = []
        for option in question["options"]:
            callback_data = f"answer:{question_index}:{option}"
            buttons.append([InlineKeyboardButton(text=option, callback_data=callback_data)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        question_text = f"**{question['level']}**\n\n{question['text']}"

        if as_new_message:
             sent_message = await bot.send_message(
                chat_id=session.chat_id, text=question_text, parse_mode="Markdown", reply_markup=keyboard
            )
             session.message_id = sent_message.message_id
        else:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=question_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:

        if callback.data == "start_quiz":
            session.current_question = 0
            await self._send_question(bot, session)
            await callback.answer()
            return session

        action, *data = callback.data.split(":")

        if action == "answer":
            question_index_str, user_answer = data
            question_index = int(question_index_str)

            if question_index != session.current_question:
                await callback.answer("This question has already been answered.", show_alert=True)
                return session

            question = VERB_ASPECT_QUESTIONS[question_index]
            correct_answer = question["correct_answer"]
            explanation = question["explanation"]

            if user_answer == correct_answer:
                session.score += 1
                random_praise = random.choice(positive_feedbacks)
                feedback_text = f"✅ {random_praise} Your answer is correct.\n\n_{explanation}_"
                await callback.answer("Correct!", show_alert=False)
            else:
                feedback_text = f"❌ Not quite. The correct answer is *{correct_answer}*.\n\n_{explanation}_"
                await callback.answer("Incorrect.", show_alert=False)

            is_last_question = (session.current_question + 1) >= len(VERB_ASPECT_QUESTIONS)
            if is_last_question:
                next_button = InlineKeyboardButton(text="🏁 Finish Test", callback_data="finish")
            else:
                next_button = InlineKeyboardButton(text="➡️ Next Question", callback_data="next_question")

            menu_button = InlineKeyboardButton(text="📋 Menu", callback_data="show_menu")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=f"**{question['level']}**\n\n{question['text']}\n\n{feedback_text}",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )

        elif action == "next_question":
            session.current_question += 1
            await self._send_question(bot, session)
            await callback.answer()

        elif action == "finish":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession):
        total_questions = len(VERB_ASPECT_QUESTIONS)
        final_text = (
            "🎉 **Aspects Test Complete!** 🎉\n\n"
            f"You scored {session.score} out of {total_questions}.\n\n"
            "Great job! Select another game from the /menu to keep practicing."
            "Choose another category or game from the /menu."
        )
        try:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=final_text,
                parse_mode="Markdown",
                reply_markup=None,
            )
        except Exception:
            await bot.send_message(
                chat_id=session.chat_id, text=final_text, parse_mode="Markdown"
            )

game_registry.register(VerbAspectQuiz())
