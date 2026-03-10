import random
from aiogram import Bot, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from data.sentence_builder_questions import SENTENCE_QUESTIONS, SENTENCE_BUILDER_UI
from data.positive_feedback import POSITIVE_FEEDBACKS
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager


class PhraseConstructorGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="phrase_constructor")

    def get_display_name(self, lang: str) -> str:
        return "🧩 Составь фразу" if lang == "ru" else "🧩 Sentence Builder"

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
            game_state={
                "lang": lang,
                "current_phrase": [],
                "available_words": [],
                "correct_answer": "",
                "question_idx": 0  # Сохраняем индекс для надежного сброса
            }
        )

        await self._prepare_next_question(session)
        await self._send_question(bot, session, as_new_message=True)
        return session

    async def _prepare_next_question(self, session: GameSession):
        idx = random.randrange(len(SENTENCE_QUESTIONS))
        question = SENTENCE_QUESTIONS[idx]

        words = question["words"][:]
        random.shuffle(words)

        session.game_state["question_idx"] = idx
        session.game_state["available_words"] = words
        session.game_state["current_phrase"] = []
        session.game_state["correct_answer"] = question["answer"]
        session.game_state["level"] = question.get("level", "level_a1")
        session.game_state["level_title"] = question.get("level_title", "Уровень A1")

    async def _send_question(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        lang = session.game_state["lang"]
        ui_text = SENTENCE_BUILDER_UI.get(lang, SENTENCE_BUILDER_UI.get("en", {}))
        level_title = session.game_state.get("level_title", "Уровень A1")

        current_build = " ".join(session.game_state["current_phrase"])
        display_phrase = current_build if current_build else "..."

        text = (
            f"*{level_title}*\n\n"
            f"{ui_text.get('build_phrase', 'Build the phrase:')}\n`{display_phrase}`\n\n"
            f"{ui_text.get('choose_word', 'Choose a word:')}"
        )

        buttons = []
        available = session.game_state["available_words"]
        for i in range(0, len(available), 2):
            row = []
            for j in range(i, min(i + 2, len(available))):
                row.append(InlineKeyboardButton(text=available[j], callback_data=f"add_word:{j}"))
            buttons.append(row)

        controls = []
        if session.game_state["current_phrase"]:
            controls.append(InlineKeyboardButton(text=ui_text.get("reset_button", "⬅️ Reset"), callback_data="reset_phrase"))
            controls.append(InlineKeyboardButton(text=ui_text.get("done_button", "✅ Done"), callback_data="check_phrase"))

        if controls:
            buttons.append(controls)

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        if as_new_message:
            sent = await bot.send_message(session.chat_id, text, reply_markup=keyboard, parse_mode="Markdown")
            session.message_id = sent.message_id
        else:
            new_message_id = await safe_edit_message(bot, session.chat_id, session.message_id, text, reply_markup=keyboard,
                                    parse_mode="Markdown")
            session.message_id = new_message_id

    async def handle_callback(self, bot: Bot, session: GameSession, callback: CallbackQuery) -> GameSession:
        if callback.data.startswith("add_word:"):
            idx = int(callback.data.split(":")[1])
            available = session.game_state["available_words"]

            if 0 <= idx < len(available):
                word = available.pop(idx)  # Удаляем именно по индексу
                session.game_state["current_phrase"].append(word)
                await self._send_question(bot, session)
            await callback.answer()

        elif callback.data == "reset_phrase":
            idx = session.game_state["question_idx"]
            words = SENTENCE_QUESTIONS[idx]["words"][:]
            random.shuffle(words)

            session.game_state["available_words"] = words
            session.game_state["current_phrase"] = []
            await self._send_question(bot, session)
            await callback.answer()

        elif callback.data == "check_phrase":
            lang = session.game_state.get("lang", "en")
            ui_text = SENTENCE_BUILDER_UI.get(lang, SENTENCE_BUILDER_UI.get("en", {}))

            def normalize(s):
                for char in ".,!?":
                    s = s.replace(char, "")
                return s.lower().strip()
            user_phrase = normalize(" ".join(session.game_state["current_phrase"]))
            correct_phrase = normalize(session.game_state["correct_answer"])
            if user_phrase == correct_phrase:
                session.score += 1
                feedback_list = POSITIVE_FEEDBACKS.get(lang, POSITIVE_FEEDBACKS["en"])
                feedback_text = random.choice(feedback_list)
                feedback = f"✅ {feedback_text}"
            else:
                feedback = f"{ui_text.get('error_prefix', '❌ Error.\nCorrect:')} `{session.game_state['correct_answer']}`"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=ui_text.get("menu_button", "Menu"), callback_data="show_menu"),
                    InlineKeyboardButton(text=ui_text.get("next_button", "Next"), callback_data="next_step")
                ]
            ])
            await safe_edit_message(bot, session.chat_id, session.message_id, feedback, reply_markup=keyboard,
                                    parse_mode="Markdown")
            await callback.answer()

        elif callback.data == "next_step":
            session.current_question += 1
            await self._prepare_next_question(session)
            await self._send_question(bot, session)
            await callback.answer()

        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        await self._send_question(bot, session, as_new_message=True)

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            await bot.send_message(session.chat_id, f"Игра окончена! Счет: {session.score}")


game_registry.register(PhraseConstructorGame())
