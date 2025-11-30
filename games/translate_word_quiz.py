from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.translate_word_quiz import WORD_DICTIONARIES
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager

QUESTIONS_PER_ROUND = 8


class TranslateWordQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="translate_word_quiz")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_tw_name", lang)

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
        await self._send_category_selection(bot, session)
        return session

    async def _send_category_selection(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        buttons = []
        row = []
        for index, dictionary in enumerate(WORD_DICTIONARIES):
            button = InlineKeyboardButton(
                text=dictionary["category_icon"],
                callback_data=f"select_category:{index}",
            )
            row.append(button)
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        text = translator.get_text("game_tw_choose_category", lang)
        
        new_message_id = await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=text,
            reply_markup=keyboard,
        )
        session.message_id = new_message_id

    async def _start_quiz_round(self, bot: Bot, session: GameSession):
        category_index = session.game_state["category_index"]
        all_words = WORD_DICTIONARIES[category_index]["words"]
        random.shuffle(all_words)
        session.game_state["round_words"] = all_words[:QUESTIONS_PER_ROUND]
        session.current_question = 0
        await self._send_question(bot, session)

    async def _send_question(
        self, bot: Bot, session: GameSession, as_new_message: bool = False
    ):
        lang = session.game_state.get("lang", "en")
        question_index = session.current_question
        word_pair = session.game_state["round_words"][question_index]
        category_index = session.game_state["category_index"]
        
        # Получаем перевод категории
        cat_key = WORD_DICTIONARIES[category_index]["category_key"]
        category_name = translator.get_text(cat_key, lang)
        
        # Определяем слова
        russian_word = word_pair["russian_word"]
        # Берем перевод на язык пользователя, если нет - английский
        user_word = word_pair["translations"].get(lang, word_pair["translations"].get("en"))
        menu_hint = translator.get_text("menu_hint", lang)

        translate_to_russian = random.choice([True, False])
        
        if translate_to_russian:
            question_word = user_word
            correct_answer = russian_word
            session.game_state["correct_answer"] = correct_answer
            prompt = translator.get_text("game_tw_prompt_to_ru", lang)
        else:
            question_word = russian_word
            correct_answer = user_word
            session.game_state["correct_answer"] = correct_answer
            prompt = translator.get_text("game_tw_prompt_from_ru", lang)

        all_words_in_category = WORD_DICTIONARIES[category_index]["words"]
        wrong_options = []
        while len(wrong_options) < 3:
            random_word_pair = random.choice(all_words_in_category)
            if translate_to_russian:
                wrong_word = random_word_pair["russian_word"]
            else:
                wrong_word = random_word_pair["translations"].get(lang, random_word_pair["translations"].get("en"))
                
            if wrong_word != correct_answer and wrong_word not in wrong_options:
                wrong_options.append(wrong_word)
                
        options = wrong_options + [correct_answer]
        random.shuffle(options)
        
        buttons = []
        for option in options:
            buttons.append(
                [InlineKeyboardButton(text=option, callback_data=f"answer:{option}")]
            )
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        cat_label = translator.get_text("game_tw_category_label", lang).format(category_name=category_name)
        question_text = f"**{cat_label}**\n\n{prompt}\n\n**{question_word}**\n\n{menu_hint}"
        
        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id,
                text=question_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
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
        action, *data = callback.data.split(":")

        if action == "select_category":
            category_index = int(data[0])
            session.game_state["category_index"] = category_index
            await self._start_quiz_round(bot, session)
            await callback.answer()

        elif action == "answer":
            user_answer = data[0]
            correct_answer = session.game_state.get("correct_answer")

            question_index = session.current_question
            word_pair = session.game_state["round_words"][question_index]
            
            w_ru = word_pair["russian_word"]
            w_user = word_pair["translations"].get(lang, word_pair["translations"].get("en"))
            full_translation = f"{w_user} - {w_ru}"

            if user_answer == correct_answer:
                session.score += 1
                feedback_text = translator.get_text("game_tw_feedback_correct", lang).replace("{pair}", full_translation)
                await callback.answer("Correct!", show_alert=False)
            else:
                feedback_text = translator.get_text("game_tw_feedback_incorrect", lang).replace("{pair}", full_translation)
                await callback.answer("Incorrect.", show_alert=False)

            is_last_question = (session.current_question + 1) >= QUESTIONS_PER_ROUND
            
            btn_next = translator.get_text("game_tw_btn_next", lang)
            btn_results = translator.get_text("game_tw_btn_results", lang)
            btn_menu = translator.get_text("game_tw_btn_menu", lang)

            if is_last_question:
                next_button = InlineKeyboardButton(text=btn_results, callback_data="finish")
            else:
                next_button = InlineKeyboardButton(text=btn_next, callback_data="next_question")

            menu_button = InlineKeyboardButton(text=btn_menu, callback_data="show_menu")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button, next_button]])

            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=callback.message.text + f"\n\n{feedback_text}",
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
            category_index = session.game_state.get("category_index", 0)
            
            cat_key = WORD_DICTIONARIES[category_index]["category_key"]
            category_name = translator.get_text(cat_key, lang)
            
            final_text = translator.get_text("game_tw_end_text", lang).format(
                category=category_name,
                score=session.score,
                total=QUESTIONS_PER_ROUND
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

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        resume_text = translator.get_text("game_tw_resume", lang)
        await bot.send_message(session.chat_id, resume_text)
        
        if session.current_question == -1:
            await self._send_category_selection(bot, session)
        else:
            loading_text = translator.get_text("game_tw_loading", lang)
            await bot.send_message(session.chat_id, loading_text)
            await self._send_question(bot, session, as_new_message=True)

game_registry.register(TranslateWordQuiz())
