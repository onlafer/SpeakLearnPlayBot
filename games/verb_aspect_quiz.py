from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.verb_aspect_quiz import VERB_ASPECT_QUESTIONS
from data.positive_feedback import POSITIVE_FEEDBACKS
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager


class VerbAspectQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="verb_aspect_quiz")

    def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        return translator.get_text("game_va_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=-1,
            score=0,
            game_state={"lang": lang}
        )

        await self._send_theory(bot, session)
        return session

    async def _send_theory(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        theory_text = translator.get_text("game_va_theory", lang)
        btn_text = translator.get_text("game_va_btn_ready", lang)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=btn_text, callback_data="start_quiz")]
            ]
        )
        new_message_id = await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=theory_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        session.message_id = new_message_id

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        resume_text = translator.get_text("game_va_resume", lang)
        
        await bot.send_message(session.chat_id, resume_text)
        
        if session.current_question == -1:
             await self._send_theory(bot, session)
        else:
             await self._send_question(bot, session, as_new_message=True)

    async def _send_question(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state.get("lang", "en")
        question_index = session.current_question
        question = VERB_ASPECT_QUESTIONS[question_index]
        
        buttons = []
        for option in question["options"]:
            callback_data = f"answer:{question_index}:{option}"
            buttons.append([InlineKeyboardButton(text=option, callback_data=callback_data)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Перевод названия уровня (сложности)
        level_text = translator.get_text(question["level"], lang)
        menu_hint = translator.get_text("menu_hint", lang)
        
        question_text = f"**{level_text}**\n\n{question['text']}\n\n{menu_hint}"

        if as_new_message:
             sent_message = await bot.send_message(
                chat_id=session.chat_id, text=question_text, parse_mode="Markdown", reply_markup=keyboard
            )
             session.message_id = sent_message.message_id
        else:
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=question_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            session.message_id = new_message_id

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        lang = session.game_state.get("lang", "en")

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
                warning_text = translator.get_text("game_va_already_answered", lang)
                await callback.answer(warning_text, show_alert=True)
                return session

            question = VERB_ASPECT_QUESTIONS[question_index]
            correct_answer = question["correct_answer"]
            
            # Получаем объяснение на языке пользователя, fallback на английский
            explanation = question["explanation"].get(lang, question["explanation"].get("en"))

            if user_answer == correct_answer:
                session.score += 1
                random_praise = random.choice(POSITIVE_FEEDBACKS.get(lang, [])) # Можно тоже перевести, если они есть в словаре
                
                feedback_template = translator.get_text("game_va_feedback_correct", lang)
                feedback_text = feedback_template.format(praise=random_praise, explanation=explanation)
                
                await callback.answer("Correct!", show_alert=False)
            else:
                feedback_template = translator.get_text("game_va_feedback_incorrect", lang)
                feedback_text = feedback_template.format(correct=correct_answer, explanation=explanation)
                
                await callback.answer("Incorrect.", show_alert=False)

            is_last_question = (session.current_question + 1) >= len(VERB_ASPECT_QUESTIONS)
            
            btn_finish = translator.get_text("game_va_btn_finish", lang)
            btn_next = translator.get_text("game_va_btn_next", lang)
            btn_menu = translator.get_text("game_va_btn_menu", lang)

            if is_last_question:
                next_button = InlineKeyboardButton(text=btn_finish, callback_data="finish")
            else:
                next_button = InlineKeyboardButton(text=btn_next, callback_data="next_question")

            menu_button = InlineKeyboardButton(text=btn_menu, callback_data="show_menu")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

            level_text = translator.get_text(question["level"], lang)

            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=f"**{level_text}**\n\n{question['text']}\n\n{feedback_text}",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            session.message_id = new_message_id

        elif action == "next_question":
            session.current_question += 1
            await self._send_question(bot, session)
            await callback.answer()

        elif action == "finish":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            lang = session.game_state.get("lang", "en")
            total_questions = len(VERB_ASPECT_QUESTIONS)
            
            final_text_template = translator.get_text("game_va_end_text", lang)
            final_text = final_text_template.format(score=session.score, total=total_questions)

            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=final_text,
                parse_mode="Markdown",
                reply_markup=None,
            )
            session.message_id = new_message_id

game_registry.register(VerbAspectQuiz())
