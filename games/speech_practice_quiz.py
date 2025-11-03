from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import random
import re

from data.speech_practice_quiz import SPEECH_PRACTICE_DATA
from utils.voice_recognition import recognize_speech_from_bytes
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry

QUESTIONS_PER_ROUND = 5


class SpeechPracticeQuiz(BaseGame):
    def __init__(self):
        super().__init__(
            game_id="speech_practice_quiz", display_name="🎤 Speech Practice"
        )

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
        await self._send_category_selection(bot, session)
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        await bot.send_message(
            session.chat_id, "Ok, let's continue your speech practice!"
        )
        if session.current_question == -1:
            await self._send_category_selection(bot, session, as_new_message=True)
        else:
            await self._send_question(bot, session, as_new_message=True)

    async def _send_category_selection(
        self, bot: Bot, session: GameSession, as_new_message: bool = False
    ):
        buttons = []
        row = []
        for index, category in enumerate(SPEECH_PRACTICE_DATA):
            button = InlineKeyboardButton(
                text=category["category_icon"], callback_data=f"select_category:{index}"
            )
            row.append(button)
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = "Please choose a category for speech practice:"
        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id, text=text, reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
        else:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=text,
                reply_markup=keyboard,
            )

    async def _start_quiz_round(self, bot: Bot, session: GameSession):
        category_index = session.game_state["category_index"]
        all_items = SPEECH_PRACTICE_DATA[category_index]["items"]
        random.shuffle(all_items)
        session.game_state["round_items"] = all_items[:QUESTIONS_PER_ROUND]
        session.current_question = 0
        await self._send_question(bot, session)

    async def _send_question(
        self, bot: Bot, session: GameSession, as_new_message: bool = False
    ):
        item_index = session.current_question
        item_text = session.game_state["round_items"][item_index]
        category_index = session.game_state["category_index"]
        category_name = SPEECH_PRACTICE_DATA[category_index]["category_name"]
        session.game_state["current_item"] = item_text
        text = (
            f"**Category: {category_name}**\n\n"
            f"Please pronounce the following:\n\n"
            f"**{item_text}**\n\n"
            "_(Press and hold the 🎙 microphone button to record your voice.)_\n\n"
            f"_To select a different game, send `/menu`._"
        )
        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id, text=text, parse_mode="Markdown"
            )
            session.message_id = sent_message.message_id
        else:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=None,
            )

    async def handle_voice_message(
        self, bot: Bot, session: GameSession, message: Message
    ) -> GameSession:
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")

        voice_file = await bot.get_file(message.voice.file_id)
        voice_bytes = await bot.download_file(voice_file.file_path)
        recognized_text = await recognize_speech_from_bytes(voice_bytes)
        original_text = session.game_state.get("current_item", "")

        try:
            await message.delete()
        except Exception:
            pass

        clean_original = re.sub(r"[^\w\s]", "", original_text).lower()
        clean_recognized = re.sub(r"[^\w\s]", "", recognized_text or "").lower()

        if recognized_text and clean_recognized == clean_original:
            session.score += 1
            feedback_text = f"✅ Excellent! You said it perfectly."
        elif recognized_text:
            feedback_text = (
                f"🤔 Good try! Here's the target:\n`{original_text}`\n\n"
                f"Here's what I heard:\n`{recognized_text}`"
            )
        else:
            feedback_text = (
                "😕 Sorry, I couldn't understand what you said. Please try again."
            )

        is_last_question = (session.current_question + 1) >= QUESTIONS_PER_ROUND

        if is_last_question:
            next_button = InlineKeyboardButton(
                text="🏁 See Results", callback_data="finish_speech"
            )
        else:
            next_button = InlineKeyboardButton(
                text="➡️ Next", callback_data="next_speech_item"
            )

        menu_button = InlineKeyboardButton(text="📋 Menu", callback_data="show_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

        category_index = session.game_state["category_index"]
        category_name = SPEECH_PRACTICE_DATA[category_index]["category_name"]

        question_text = (
            f"**Category: {category_name}**\n\n"
            f"Please pronounce the following:\n\n"
            f"**{original_text}**\n\n"
            "_(Press and hold the 🎙 microphone button to record your voice.)_"
        )

        full_text = f"{question_text}\n\n{feedback_text}"

        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=full_text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

        return session

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        action, *data = callback.data.split(":")

        if action == "select_category":
            category_index = int(data[0])
            session.game_state["category_index"] = category_index
            await self._start_quiz_round(bot, session)
            await callback.answer()

        elif action == "next_speech_item":
            session.current_question += 1
            await self._send_question(bot, session)
            await callback.answer()

        elif action == "finish_speech":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession):
        final_text = (
            f"🎉 **Speech Practice Complete!** 🎉\n\n"
            f"You pronounced **{session.score}** out of **{QUESTIONS_PER_ROUND}** items correctly.\n\n"
            "Amazing work! Keep practicing!"
            "Choose another category or game from the /menu."
        )
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=final_text,
            parse_mode="Markdown",
            reply_markup=None,
        )


game_registry.register(SpeechPracticeQuiz())