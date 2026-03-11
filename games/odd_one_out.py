import random

from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from data.odd_one_out_data import ODD_ONE_OUT_QUESTIONS
from data.positive_feedback import POSITIVE_FEEDBACKS
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager

QUESTIONS_PER_ROUND = 5


def escape_markdown_v1(text: str) -> str:
    """Escape special characters for Telegram Markdown (v1)."""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f"\\{char}")
    return text


class OddOneOutGame(BaseGame):

    def __init__(self):
        super().__init__(game_id="odd_one_out")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_ooo_name", lang)

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

        await self._send_level_selection(bot, session, as_new_message=True)
        return session

    async def _send_level_selection(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state.get("lang", "en")
        title = self.get_display_name(lang)
        text = translator.get_text("game_ooo_select_level", lang)
        menu_hint = translator.get_text("menu_hint", lang)

        full_text = f"*{escape_markdown_v1(title)}*\n\n{text}\n\n_{menu_hint}_"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="A1 (Elementary)", callback_data="ooo_set_level_a1")],
            [InlineKeyboardButton(text="A2 (Pre-Intermediate)", callback_data="ooo_set_level_a2")],
            [InlineKeyboardButton(text="B1 (Intermediate)", callback_data="ooo_set_level_b1")],
        ])

        if as_new_message:
            sent = await bot.send_message(session.chat_id, full_text, reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = sent.message_id
        else:
            new_message_id = await safe_edit_message(bot, session.chat_id, session.message_id, full_text,
                                                      reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = new_message_id

    async def _send_question(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state.get("lang", "en")
        questions = session.game_state.get("questions", [])
        question = questions[session.current_question]

        display_words = list(question["words"])
        random.shuffle(display_words)

        title = self.get_display_name(lang)
        text_template = translator.get_text("game_ooo_question_text", lang)
        body = text_template.format(num=session.current_question + 1, total=len(questions))
        menu_hint = translator.get_text("menu_hint", lang)

        full_text = f"*{escape_markdown_v1(title)}*\n\n{body}\n\n_{menu_hint}_"

        buttons = [[InlineKeyboardButton(text=w, callback_data=f"ooo_ans_{w}")] for w in display_words]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        if as_new_message:
            sent = await bot.send_message(session.chat_id, full_text, reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = sent.message_id
        else:
            new_message_id = await safe_edit_message(bot, session.chat_id, session.message_id, full_text,
                                                    reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = new_message_id

    async def handle_callback(self, bot: Bot, session: GameSession, callback: CallbackQuery) -> GameSession:
        # Синхронизируем ID сообщения из колбэка
        session.message_id = callback.message.message_id

        data = callback.data
        lang = session.game_state.get("lang", "en")

        if data.startswith("ooo_set_level_"):
            level = data.replace("ooo_set_level_", "")
            all_q = [q for q in ODD_ONE_OUT_QUESTIONS if q["level"] == level]
            session.game_state["questions"] = random.sample(all_q, min(len(all_q), QUESTIONS_PER_ROUND))
            session.current_question = 0
            await self._send_question(bot, session)

        elif data.startswith("ooo_ans_"):
            selected = data.replace("ooo_ans_", "")
            questions = session.game_state.get("questions", [])
            question = questions[session.current_question]
            explanation = question["explanation"].get(lang, question["explanation"]["en"])

            title = self.get_display_name(lang)
            header = f"*{escape_markdown_v1(title)}*\n\n"

            if selected == question["correct_answer"]:
                session.score += 1
                feedback = random.choice(POSITIVE_FEEDBACKS.get(lang, POSITIVE_FEEDBACKS["en"]))
                result_text = f"{header}✅ {feedback}\n\n_{explanation}_"
            else:
                wrong_template = translator.get_text("game_rc_feedback_incorrect", lang)
                feedback = wrong_template.format(
                    correct=question["correct_answer"],
                    explanation=explanation
                )
                result_text = f"{header}{feedback}"

            is_last = session.current_question >= len(questions) - 1
            nav_text = translator.get_text("game_rc_btn_finish" if is_last else "game_rc_btn_next", lang)
            nav_call = "ooo_finish" if is_last else "ooo_next"

            # Add menu hint after every question
            menu_hint = translator.get_text("menu_hint", lang)
            result_text += f"\n\n_{menu_hint}_"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=nav_text, callback_data=nav_call)]])
            new_message_id = await safe_edit_message(bot, session.chat_id, session.message_id, result_text,
                                                    reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = new_message_id

        elif data == "ooo_next":
            session.current_question += 1
            await self._send_question(bot, session)

        elif data == "ooo_finish":
            await self.end_game(bot, session)

        await callback.answer()
        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        session.status = GameStatus.FINISHED
        if send_message:
            lang = session.game_state.get("lang", "en")
            total = len(session.game_state.get("questions", []))
            final_text = translator.get_text("game_rc_end_text", lang).format(score=session.score, total=total)

            await safe_edit_message(bot, session.chat_id, session.message_id, final_text,
                                    reply_markup=None, parse_mode="Markdown")

    async def resume_game(self, bot: Bot, session: GameSession):
        if session.current_question == -1:
            await self._send_level_selection(bot, session, as_new_message=True)
        else:
            await self._send_question(bot, session, as_new_message=True)


game_registry.register(OddOneOutGame())