from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from data.texts_game_data import TEXTS_GAME_CONTENT
from database.user_manager import user_manager
from utils.bot_helpers import safe_edit_message
from utils.localization import translator

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry


class TextsGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="texts")

    @staticmethod
    def _lang(s: GameSession) -> str:
        return s.game_state.get("lang", "en")

    @staticmethod
    def _idx(s: GameSession) -> int:
        return s.game_state.get("current_text_index", 0)

    def _content(self, s: GameSession) -> dict:
        return TEXTS_GAME_CONTENT[self._idx(s)]

    @staticmethod
    def _results_button(lang: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=translator.get_text("game_speech_practice_button_results", lang),
            callback_data="texts_show_results",
        )

    async def _show(self, bot: Bot, s: GameSession, text: str, markup: InlineKeyboardMarkup | None, as_new: bool = False):
        if as_new:
            msg = await bot.send_message(s.chat_id, text, reply_markup=markup)
            s.message_id = msg.message_id
            return
        s.message_id = await safe_edit_message(
            bot=bot,
            chat_id=s.chat_id,
            message_id=s.message_id,
            text=text,
            reply_markup=markup,
        )

    async def _finish(self, bot: Bot, s: GameSession):
        s.status = GameStatus.FINISHED
        await self.end_game(bot, s)

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_texts_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        s = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=0,
            score=0,
            game_state={
                "lang": user.language if user else "en",
                "current_text_index": 0,
                "phase": "reading",
                "question_index": 0,
                "text_correct": 0,
                "text_wrong": 0,
                "total_correct": 0,
                "total_wrong": 0,
                "answered_current": False,
            },
        )
        await self._render_reading(bot, s)
        return s

    async def resume_game(self, bot: Bot, s: GameSession):
        phase = s.game_state.get("phase", "reading")
        if phase == "quiz" and s.game_state.get("answered_current"):
            q_idx = s.game_state.get("question_index", 0)
            content = self._content(s)
            if q_idx < len(content["questions"]):
                question = content["questions"][q_idx]
                correct = question["correct_index"]
                await self._render_question_result(bot, s, question, correct, as_new=True)
                return

        render = {
            "reading": self._render_reading,
            "quiz": self._render_question,
            "summary": self._render_text_summary,
            "results": self._render_results,
        }.get(phase, self._render_reading)
        await render(bot, s, as_new=True)

    async def handle_message(self, bot: Bot, s: GameSession, message: Message) -> GameSession:
        await bot.send_message(s.chat_id, translator.get_text("game_texts_use_buttons", self._lang(s)))
        return s

    async def handle_callback(self, bot: Bot, s: GameSession, callback: CallbackQuery) -> GameSession:
        s.message_id = callback.message.message_id
        action = callback.data or ""
        if action.startswith("texts_answer:"):
            await self._on_answer(bot, s, callback)
            return s

        handlers = {
            "texts_prev": self._on_prev,
            "texts_next": self._on_next,
            "texts_read": self._on_read,
            "texts_next_question": self._on_next_question,
            "texts_show_results": self._on_show_results,
            "texts_back_to_texts": self._on_back_to_texts,
        }
        handler = handlers.get(action)
        if handler:
            await handler(bot, s)
        await callback.answer()
        return s

    async def _on_prev(self, bot: Bot, s: GameSession):
        if s.game_state["phase"] == "reading" and self._idx(s) > 0:
            s.game_state["current_text_index"] -= 1
        await self._render_reading(bot, s)

    async def _on_next(self, bot: Bot, s: GameSession):
        if s.game_state["phase"] != "reading":
            return
        if self._idx(s) < len(TEXTS_GAME_CONTENT) - 1:
            s.game_state["current_text_index"] += 1
        await self._render_reading(bot, s)

    async def _on_read(self, bot: Bot, s: GameSession):
        s.game_state.update({"phase": "quiz", "question_index": 0, "text_correct": 0, "text_wrong": 0, "answered_current": False})
        await self._render_question(bot, s)

    async def _on_answer(self, bot: Bot, s: GameSession, callback: CallbackQuery):
        if s.game_state.get("phase") != "quiz" or s.game_state.get("answered_current"):
            await callback.answer()
            return

        chosen = int((callback.data or "0").split(":")[1])
        q_idx = s.game_state["question_index"]
        questions = self._content(s)["questions"]
        if q_idx >= len(questions):
            s.game_state["phase"] = "summary"
            await self._render_text_summary(bot, s)
            await callback.answer()
            return
        question = questions[q_idx]
        correct = question["correct_index"]
        ok = chosen == correct

        s.game_state["answered_current"] = True
        key = "correct" if ok else "wrong"
        s.game_state[f"text_{key}"] += 1
        s.game_state[f"total_{key}"] += 1
        await callback.answer(translator.get_text(f"game_texts_feedback_{key}", self._lang(s)))
        await self._render_question_result(bot, s, question, correct)

    async def _on_next_question(self, bot: Bot, s: GameSession):
        s.game_state["question_index"] += 1
        s.game_state["answered_current"] = False
        if s.game_state["question_index"] >= len(self._content(s)["questions"]):
            s.game_state["phase"] = "summary"
            await self._render_text_summary(bot, s)
        else:
            await self._render_question(bot, s)

    async def _on_show_results(self, bot: Bot, s: GameSession):
        s.game_state["phase"] = "results"
        await self._render_results(bot, s)

    async def _on_back_to_texts(self, bot: Bot, s: GameSession):
        s.game_state["phase"] = "reading"
        s.game_state["question_index"] = 0
        s.game_state["answered_current"] = False
        await self._render_reading(bot, s)

    async def end_game(self, bot: Bot, s: GameSession, send_message: bool = True):
        if not send_message:
            return
        total = len(TEXTS_GAME_CONTENT)
        text = translator.get_text("game_texts_end_text", self._lang(s)).format(
            total_correct=s.game_state.get("total_correct", 0),
            total_wrong=s.game_state.get("total_wrong", 0),
            completed=min(self._idx(s) + 1, total),
            total=total,
        )
        text += f"\n\n{translator.get_text('menu_hint', self._lang(s))}"
        await self._show(bot, s, text, markup=None)

    def _reading_keyboard(self, idx: int, lang: str) -> InlineKeyboardMarkup:
        top = []
        if idx > 0:
            top.insert(0, InlineKeyboardButton(text=translator.get_text("game_texts_back_button", lang), callback_data="texts_prev"))
        if idx < len(TEXTS_GAME_CONTENT) - 1:
            top.append(InlineKeyboardButton(text=translator.get_text("game_texts_next_text_button", lang), callback_data="texts_next"))
        rows = []
        if top:
            rows.append(top)
        rows.append(
            [
                InlineKeyboardButton(
                    text=translator.get_text("game_texts_read_button", lang),
                    callback_data="texts_read",
                )
            ]
        )
        return InlineKeyboardMarkup(
            inline_keyboard=rows
        )

    async def _render_reading(self, bot: Bot, s: GameSession, as_new: bool = False):
        lang, idx, content = self._lang(s), self._idx(s), self._content(s)
        text = translator.get_text("game_texts_reading_screen", lang).format(
            current=idx + 1,
            total=len(TEXTS_GAME_CONTENT),
            title=content["title"],
            text=content["text"],
        )
        text += f"\n\n{translator.get_text('menu_hint', lang)}"
        await self._show(bot, s, text, self._reading_keyboard(idx, lang), as_new)

    async def _render_question(self, bot: Bot, s: GameSession, as_new: bool = False):
        lang, idx = self._lang(s), self._idx(s)
        q_idx, content = s.game_state.get("question_index", 0), self._content(s)
        if q_idx >= len(content["questions"]):
            s.game_state["phase"] = "summary"
            await self._render_text_summary(bot, s, as_new=as_new)
            return
        question = content["questions"][q_idx]
        buttons = [[InlineKeyboardButton(text=opt, callback_data=f"texts_answer:{i}")] for i, opt in enumerate(question["options"])]
        text = translator.get_text("game_texts_question_screen", lang).format(
            text_number=idx + 1,
            total_texts=len(TEXTS_GAME_CONTENT),
            question_number=q_idx + 1,
            total_questions=len(content["questions"]),
            question=question["question"],
        )
        text += f"\n\n{translator.get_text('menu_hint', lang)}"
        await self._show(bot, s, text, InlineKeyboardMarkup(inline_keyboard=buttons), as_new)

    async def _render_question_result(self, bot: Bot, s: GameSession, question: dict, correct_index: int, as_new: bool = False):
        lang = self._lang(s)
        current_question_index = s.game_state.get("question_index", 0)
        total_questions = len(self._content(s)["questions"])
        is_last_question = current_question_index >= total_questions - 1

        text = translator.get_text("game_texts_answer_result", lang).format(
            text_number=self._idx(s) + 1,
            question_number=current_question_index + 1,
            question=question["question"],
            correct=question["options"][correct_index],
        )
        text += f"\n\n{translator.get_text('menu_hint', lang)}"

        if is_last_question:
            button = self._results_button(lang)
        else:
            button = InlineKeyboardButton(
                text=translator.get_text("game_texts_next_question_button", lang),
                callback_data="texts_next_question",
            )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[button]]
        )
        await self._show(bot, s, text, keyboard, as_new=as_new)

    async def _render_text_summary(self, bot: Bot, s: GameSession, as_new: bool = False):
        lang, idx, total = self._lang(s), self._idx(s), len(TEXTS_GAME_CONTENT)
        text = translator.get_text("game_texts_text_summary", lang).format(
            current=idx + 1,
            total=total,
            correct=s.game_state.get("text_correct", 0),
            wrong=s.game_state.get("text_wrong", 0),
        )
        text += f"\n\n{translator.get_text('menu_hint', lang)}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [self._results_button(lang)],
            ]
        )
        await self._show(bot, s, text, keyboard, as_new)

    async def _render_results(self, bot: Bot, s: GameSession, as_new: bool = False):
        lang = self._lang(s)
        total = len(TEXTS_GAME_CONTENT)
        text = translator.get_text("game_texts_end_text", lang).format(
            total_correct=s.game_state.get("total_correct", 0),
            total_wrong=s.game_state.get("total_wrong", 0),
            completed=min(self._idx(s) + 1, total),
            total=total,
        )
        text += f"\n\n{translator.get_text('menu_hint', lang)}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=translator.get_text("game_texts_back_button", lang),
                        callback_data="texts_back_to_texts",
                    )
                ]
            ]
        )
        await self._show(bot, s, text, keyboard, as_new)


game_registry.register(TextsGame())