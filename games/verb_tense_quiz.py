from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.verb_tense_quiz import VERB_TENSE_QUESTIONS
from data.positive_feedback import POSITIVE_FEEDBACKS
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager


class VerbTenseQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="verb_tense_quiz")

    def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        return translator.get_text("game_vt_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=0,
            score=0,
            game_state={"lang": lang}
        )
        await self._send_question(bot, session)
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        resume_text = translator.get_text("game_vt_resume", lang)
        
        await bot.send_message(session.chat_id, resume_text)
        await self._send_question(bot, session, as_new_message=True)

    async def _send_question(
        self, bot: Bot, session: GameSession, as_new_message: bool = False
    ):
        lang = session.game_state.get("lang", "en")
        question_index = session.current_question
        question = VERB_TENSE_QUESTIONS[question_index]
        
        buttons = []
        for option in question["options"]:
            callback_data = f"answer:{question_index}:{option}"
            buttons.append(
                [InlineKeyboardButton(text=option, callback_data=callback_data)]
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Перевод названия уровня (Level)
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
        """Handles both answering a question and moving to the next one."""
        lang = session.game_state.get("lang", "en")
        action, *data = callback.data.split(":")

        if action == "answer":
            question_index_str, user_answer = data
            question_index = int(question_index_str)

            if question_index != session.current_question:
                warning_text = translator.get_text("game_vt_already_answered", lang)
                await callback.answer(warning_text, show_alert=True)
                return session

            question = VERB_TENSE_QUESTIONS[question_index]
            correct_answer = question["correct_answer"]
            
            # Объяснение на языке пользователя
            explanation = question["explanation"].get(lang, question["explanation"].get("en"))

            if user_answer == correct_answer:
                session.score += 1
                random_praise = random.choice(POSITIVE_FEEDBACKS.get(lang, [])) # Можно перевести при желании
                
                feedback_template = translator.get_text("game_vt_feedback_correct", lang)
                feedback_text = feedback_template.format(praise=random_praise, explanation=explanation)
                
                await callback.answer("Correct!", show_alert=False)
            else:
                feedback_template = translator.get_text("game_vt_feedback_incorrect", lang)
                feedback_text = feedback_template.format(correct=correct_answer, explanation=explanation)
                
                await callback.answer("Incorrect.", show_alert=False)

            is_last_question = (session.current_question + 1) >= len(
                VERB_TENSE_QUESTIONS
            )
            
            btn_finish = translator.get_text("game_vt_btn_finish", lang)
            btn_next = translator.get_text("game_vt_btn_next", lang)
            btn_menu = translator.get_text("game_vt_btn_menu", lang)

            if is_last_question:
                next_button = InlineKeyboardButton(
                    text=btn_finish, callback_data="finish"
                )
            else:
                next_button = InlineKeyboardButton(
                    text=btn_next, callback_data="next_question"
                )

            menu_button = InlineKeyboardButton(text=btn_menu, callback_data="show_menu")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=f"{callback.message.text}\n\n{feedback_text}",
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
        """Sends the final score message and cleans up."""
        if send_message:
            lang = session.game_state.get("lang", "en")
            total_questions = len(VERB_TENSE_QUESTIONS)
            
            final_text = translator.get_text("game_vt_end_text", lang).format(
                score=session.score, total=total_questions
            )
            
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=final_text,
                parse_mode="Markdown",
                reply_markup=None,
            )
            session.message_id = new_message_id


game_registry.register(VerbTenseQuiz())
