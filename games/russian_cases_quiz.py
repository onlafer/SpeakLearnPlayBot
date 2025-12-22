from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.russian_cases_quiz_data import (
    NOMINATIVE_CASE_QUESTIONS,
    GENITIVE_CASE_QUESTIONS,
    DATIVE_CASE_QUESTIONS,
    ACCUSATIVE_CASE_QUESTIONS,
    INSTRUMENTAL_CASE_QUESTIONS,
    PREPOSITIONAL_CASE_QUESTIONS,
)
from data.positive_feedback import POSITIVE_FEEDBACKS
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager

# Карта для доступа к вопросам по ключу
CASE_QUESTIONS_MAP = {
    "nominative": NOMINATIVE_CASE_QUESTIONS,
    "genitive": GENITIVE_CASE_QUESTIONS,
    "dative": DATIVE_CASE_QUESTIONS,
    "accusative": ACCUSATIVE_CASE_QUESTIONS,
    "instrumental": INSTRUMENTAL_CASE_QUESTIONS,
    "prepositional": PREPOSITIONAL_CASE_QUESTIONS,
}

class RussianCasesQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="russian_cases_quiz")

    def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        return translator.get_text("game_rc_name", lang)

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
            game_state={"lang": lang, "selected_case": None}
        )

        await self._send_case_selection(bot, session)
        return session

    async def _send_case_selection(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state.get("lang", "en")
        text = translator.get_text("game_rc_select_case", lang)
        menu_hint = translator.get_text("menu_hint", lang)
        full_text = f"{text}\n\n{menu_hint}"
        
        buttons = [
            [InlineKeyboardButton(text=translator.get_text("case_nominative", lang), callback_data="select_case:nominative")],
            [InlineKeyboardButton(text=translator.get_text("case_genitive", lang), callback_data="select_case:genitive")],
            [InlineKeyboardButton(text=translator.get_text("case_dative", lang), callback_data="select_case:dative")],
            [InlineKeyboardButton(text=translator.get_text("case_accusative", lang), callback_data="select_case:accusative")],
            [InlineKeyboardButton(text=translator.get_text("case_instrumental", lang), callback_data="select_case:instrumental")],
            [InlineKeyboardButton(text=translator.get_text("case_prepositional", lang), callback_data="select_case:prepositional")]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id,
                text=full_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
        else:
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=full_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            session.message_id = new_message_id

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        resume_text = translator.get_text("game_rc_resume", lang)
        
        await bot.send_message(session.chat_id, resume_text)
        
        if session.game_state.get("selected_case") is None:
             await self._send_case_selection(bot, session, as_new_message=True)
        else:
             await self._send_question(bot, session, as_new_message=True)

    async def _send_question(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state.get("lang", "en")
        selected_case = session.game_state.get("selected_case")
        questions = CASE_QUESTIONS_MAP[selected_case]
        
        question_index = session.current_question
        question = questions[question_index]
        
        buttons = []
        for option in question["options"]:
            callback_data = f"answer:{question_index}:{option}"
            buttons.append([InlineKeyboardButton(text=option, callback_data=callback_data)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
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

        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: синхронизируем ID сообщения из колбэка
        # Это заставляет бота редактировать именно ту панель, на которой нажата кнопка
        session.message_id = callback.message.message_id

        if callback.data.startswith("select_case:"):
            case_id = callback.data.split(":")[1]
            session.game_state["selected_case"] = case_id
            session.current_question = 0
            await self._send_question(bot, session)
            await callback.answer()
            return session

        action, *data = callback.data.split(":")

        if action == "answer":
            question_index_str, user_answer = data
            question_index = int(question_index_str)

            if question_index != session.current_question:
                warning_text = translator.get_text("game_rc_already_answered", lang)
                await callback.answer(warning_text, show_alert=True)
                return session

            selected_case = session.game_state.get("selected_case")
            questions = CASE_QUESTIONS_MAP[selected_case]
            question = questions[question_index]
            
            correct_answer = question["correct_answer"]
            explanation = question["explanation"].get(lang, question["explanation"].get("en"))

            if user_answer == correct_answer:
                session.score += 1
                random_praise = random.choice(POSITIVE_FEEDBACKS.get(lang, ["Great!"]))
                
                feedback_template = translator.get_text("game_rc_feedback_correct", lang)
                feedback_text = feedback_template.format(praise=random_praise, explanation=explanation)
                
                await callback.answer("Correct!", show_alert=False)
            else:
                feedback_template = translator.get_text("game_rc_feedback_incorrect", lang)
                feedback_text = feedback_template.format(correct=correct_answer, explanation=explanation)
                
                await callback.answer("Incorrect.", show_alert=False)

            is_last_question = (session.current_question + 1) >= len(questions)
            
            btn_finish = translator.get_text("game_rc_btn_finish", lang)
            btn_next = translator.get_text("game_rc_btn_next", lang)
            btn_menu = translator.get_text("game_rc_btn_menu", lang)

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
            selected_case = session.game_state.get("selected_case")
            questions = CASE_QUESTIONS_MAP[selected_case]
            total_questions = len(questions)
            
            final_text_template = translator.get_text("game_rc_end_text", lang)
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

game_registry.register(RussianCasesQuiz())
