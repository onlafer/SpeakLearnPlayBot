import html
from difflib import SequenceMatcher

from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
import random
import re

from data.speech_practice_quiz_data import SPEECH_PRACTICE_DATA
from utils.voice_recognition import recognize_speech_from_bytes
from utils.text_to_speech import text_to_speech
from utils.localization import translator
from database.user_manager import user_manager
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message

QUESTIONS_PER_ROUND = 5


async def get_user_language(user_id: int) -> str:
    user = await user_manager.get_user(user_id)
    return user.language if user else "en"


class SpeechPracticeQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="speech_practice_quiz")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_speech_practice_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        lang = await get_user_language(user_id)
        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=-1,
            score=0,
            game_state={"lang": lang, "last_voice_id": None},
        )
        await self._send_category_selection(bot, session)
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = await self._get_session_language(session)
        resume_text = translator.get_text("game_speech_practice_resume_text", lang)
        await bot.send_message(session.chat_id, resume_text)
        if session.current_question == -1:
            await self._send_category_selection(bot, session, as_new_message=True)
        else:
            await self._send_question(bot, session, is_new_round_step=True)

    async def _send_category_selection(
        self, bot: Bot, session: GameSession, as_new_message: bool = False
    ):
        lang = await self._get_session_language(session)
        
        await self._cleanup_previous_voice(bot, session)

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
        text = translator.get_text("game_speech_practice_choose_category", lang)

        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id, text=text, reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
        else:
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=text,
                reply_markup=keyboard,
            )
            if new_message_id:
                session.message_id = new_message_id
            else:
                sent_message = await bot.send_message(
                     chat_id=session.chat_id, text=text, reply_markup=keyboard
                )
                session.message_id = sent_message.message_id

    async def _start_quiz_round(self, bot: Bot, session: GameSession):
        category_index = session.game_state["category_index"]
        all_items = SPEECH_PRACTICE_DATA[category_index]["items"]
        random.shuffle(all_items)
        session.game_state["round_items"] = all_items[:QUESTIONS_PER_ROUND]
        session.current_question = 0
        await self._send_question(bot, session, is_new_round_step=True)

    async def _cleanup_previous_voice(self, bot: Bot, session: GameSession):
        last_voice_id = session.game_state.get("last_voice_id")
        if last_voice_id:
            try:
                await bot.delete_message(chat_id=session.chat_id, message_id=last_voice_id)
            except Exception:
                pass
            session.game_state["last_voice_id"] = None

    async def _send_question(
        self, bot: Bot, session: GameSession, is_new_round_step: bool = False
    ):
        item_index = session.current_question
        item_text = session.game_state["round_items"][item_index]
        category_index = session.game_state["category_index"]
        session.game_state["current_item"] = item_text
        lang = await self._get_session_language(session)
        category_name = self._get_category_name(category_index, lang)

        text = self._format_question_text(
            category_name=category_name,
            item_text=item_text,
            lang=lang,
            include_menu_hint=True,
        )

        if is_new_round_step:
            if session.message_id:
                try:
                    await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
                except Exception:
                    pass
            
            await self._cleanup_previous_voice(bot, session)

            tts_lang = "ru"
            
            await bot.send_chat_action(chat_id=session.chat_id, action="upload_voice")
            
            voice_bytes = await text_to_speech(item_text, lang=tts_lang)
            voice_msg = await bot.send_voice(
                chat_id=session.chat_id,
                voice=BufferedInputFile(voice_bytes.read(), filename="pronunciation.ogg")
            )
            session.game_state["last_voice_id"] = voice_msg.message_id

            sent_message = await bot.send_message(
                chat_id=session.chat_id, 
                text=text, 
                parse_mode="Markdown"
            )
            session.message_id = sent_message.message_id

        else:
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=None,
            )
            if not new_message_id:
                sent_msg = await bot.send_message(
                    chat_id=session.chat_id, text=text, parse_mode="Markdown"
                )
                session.message_id = sent_msg.message_id

    async def handle_voice_message(
        self, bot: Bot, session: GameSession, message: Message
    ) -> GameSession:
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")
        lang = await self._get_session_language(session)

        voice_file = await bot.get_file(message.voice.file_id)
        voice_bytes = await bot.download_file(voice_file.file_path)
        recognized_text = await recognize_speech_from_bytes(voice_bytes, language="ru-RU")
        original_text = session.game_state.get("current_item", "")

        try:
            await message.delete()
        except Exception:
            pass

        clean_original = re.sub(r"[^\w\s]", "", original_text).lower().strip()
        clean_recognized = re.sub(r"[^\w\s]", "", recognized_text or "").lower().strip()

        similarity = 0.0
        if clean_original and clean_recognized:
            matcher = SequenceMatcher(None, clean_original, clean_recognized)
            similarity = matcher.ratio()

        safe_original = original_text
        safe_recognized = recognized_text or "..."

        if recognized_text and similarity >= 0.95:
            session.score += 1
            template = translator.get_text("game_speech_practice_feedback_perfect", lang)
            feedback_text = template.format(
                recognized=safe_recognized
            )

        elif recognized_text and similarity >= 0.90:
            session.score += 1
            template = translator.get_text("game_speech_practice_feedback_close", lang)
            feedback_text = template.format(
                target=safe_original,
                recognized=safe_recognized
            )

        elif recognized_text:
            template = translator.get_text("game_speech_practice_feedback_good_try", lang)
            feedback_text = template.format(
                target=safe_original,
                recognized=safe_recognized
            )
        else:
            feedback_text = translator.get_text(
                "game_speech_practice_feedback_unrecognized", lang
            )

        is_last_question = (session.current_question + 1) >= QUESTIONS_PER_ROUND
        
        if is_last_question:
            next_button = InlineKeyboardButton(
                text=translator.get_text("game_speech_practice_button_results", lang),
                callback_data="finish_speech",
            )
        else:
            next_button = InlineKeyboardButton(
                text=translator.get_text("game_speech_practice_button_next", lang),
                callback_data="next_speech_item",
            )

        menu_button = InlineKeyboardButton(
            text=translator.get_text("game_speech_practice_button_menu", lang),
            callback_data="show_menu",
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

        category_index = session.game_state["category_index"]
        category_name = self._get_category_name(category_index, lang)

        question_text = self._format_question_text(
            category_name=category_name,
            item_text=original_text,
            lang=lang,
            include_menu_hint=True,
        )

        full_text = f"{question_text}\n\n{feedback_text}"

        new_message_id = await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=full_text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        
        if new_message_id:
             session.message_id = new_message_id
        else:
             sent = await bot.send_message(
                 chat_id=session.chat_id, 
                 text=full_text, 
                 parse_mode="Markdown",
                 reply_markup=keyboard
             )
             session.message_id = sent.message_id

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
            await self._send_question(bot, session, is_new_round_step=True)
            await callback.answer()

        elif action == "finish_speech":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        await self._cleanup_previous_voice(bot, session)
        
        if send_message:
            lang = await self._get_session_language(session)
            final_text = translator.get_text("game_speech_practice_end_text", lang).format(
                score=session.score, total=QUESTIONS_PER_ROUND
            )
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=final_text,
                parse_mode="Markdown",
                reply_markup=None,
            )

    async def _get_session_language(self, session: GameSession) -> str:
        lang = session.game_state.get("lang")
        if not lang:
            lang = await get_user_language(session.user_id)
            session.game_state["lang"] = lang
        return lang

    def _format_question_text(
        self,
        category_name: str,
        item_text: str,
        lang: str,
        include_menu_hint: bool = True,
    ) -> str:
        safe_category = category_name
        safe_item = item_text

        category_label = translator.get_text(
            "game_speech_practice_category_label", lang
        ).format(category_name=safe_category)
        
        pronounce_prompt = translator.get_text(
            "game_speech_practice_pronounce_prompt", lang
        )
        record_hint = translator.get_text("game_speech_practice_record_hint", lang)
        menu_hint = translator.get_text("menu_hint", lang)

        parts = [
            f"*{category_label}*",
            pronounce_prompt,
            f"*{safe_item}*",
            f"_{record_hint}_",
        ]
        if include_menu_hint:
            parts.append(menu_hint)
        return "\n\n".join(parts)

    def _get_category_name(self, category_index: int, lang: str) -> str:
        category_key = SPEECH_PRACTICE_DATA[category_index]["category_key"]
        return translator.get_text(category_key, lang)

game_registry.register(SpeechPracticeQuiz())
