from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random

from data.translate_word_quiz import WORD_DICTIONARIES
from data.positive_feedback import positive_feedbacks
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry

# Количество вопросов в одном раунде
QUESTIONS_PER_ROUND = 8


class TranslateWordQuiz(BaseGame):
    def __init__(self):
        super().__init__(
            game_id="translate_word_quiz", display_name="🌐 Translate the Word"
        )

    # Этап 1: Показываем категории
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

    async def _send_category_selection(self, bot: Bot, session: GameSession):
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
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text="Please choose a category:",
            reply_markup=keyboard,
        )

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
        question_index = session.current_question
        word_pair = session.game_state["round_words"][question_index]
        category_index = session.game_state["category_index"]
        translate_from_english = random.choice([True, False])
        if translate_from_english:
            question_word = word_pair["english_word"]
            correct_answer = word_pair["russian_word"]
            session.game_state["correct_answer"] = correct_answer
            prompt = "Translate this word to Russian:"
        else:
            question_word = word_pair["russian_word"]
            correct_answer = word_pair["english_word"]
            session.game_state["correct_answer"] = correct_answer
            prompt = "Translate this word to English:"
        all_words_in_category = WORD_DICTIONARIES[category_index]["words"]
        wrong_options = []
        while len(wrong_options) < 3:
            random_word_pair = random.choice(all_words_in_category)
            wrong_word = random_word_pair[
                "russian_word" if translate_from_english else "english_word"
            ]
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
        question_text = f"**Category: {WORD_DICTIONARIES[category_index]['category_name']}**\n\n{prompt}\n\n**{question_word}**"
        if question_index == 0 or as_new_message:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=question_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=question_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )

    # Обработка всех нажатий
    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        action, *data = callback.data.split(":")

        if action == "select_category":
            category_index = int(data[0])
            session.game_state["category_index"] = category_index
            await self._start_quiz_round(bot, session)
            await callback.answer()

        elif action == "answer":
            user_answer = data[0]
            correct_answer = session.game_state.get("correct_answer")

            # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ НАЧИНАЕТСЯ ЗДЕСЬ ---

            # 1. Получаем всю пару слов для текущего вопроса из сессии
            question_index = session.current_question
            word_pair = session.game_state["round_words"][question_index]
            full_translation = (
                f"{word_pair['english_word']} - {word_pair['russian_word']}"
            )

            if user_answer == correct_answer:
                session.score += 1
                # 2. Добавляем полную пару слов к сообщению о правильном ответе
                feedback_text = f"✅ {random.choice(positive_feedbacks)} Correct!\n\n*{full_translation}*"
                await callback.answer("Correct!", show_alert=False)
            else:
                # 3. Меняем сообщение о неправильном ответе, чтобы оно сразу показывало правильную пару
                feedback_text = (
                    f"❌ Not quite. The correct translation is:\n\n*{full_translation}*"
                )
                await callback.answer("Incorrect.", show_alert=False)

            # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ ЗАКАНЧИВАЕТСЯ ЗДЕСЬ ---

            is_last_question = (session.current_question + 1) >= QUESTIONS_PER_ROUND
            if is_last_question:
                next_button = InlineKeyboardButton(
                    text="🏁 See Results", callback_data="finish"
                )
            else:
                next_button = InlineKeyboardButton(
                    text="➡️ Next Word", callback_data="next_question"
                )

            menu_button = InlineKeyboardButton(
                text="📋 Menu", callback_data="show_menu"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[menu_button, next_button]]
            )

            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=callback.message.text + f"\n\n{feedback_text}",
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
        category_index = session.game_state.get("category_index", 0)
        category_name = WORD_DICTIONARIES[category_index]["category_name"]
        final_text = (
            f"🎉 **Round Complete!** 🎉\n\n"
            f"Category: **{category_name}**\n"
            f"Your score: **{session.score}** out of **{QUESTIONS_PER_ROUND}**.\n\n"
            "Choose another category or game from the /menu."
        )
        await bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=final_text,
            parse_mode="Markdown",
            reply_markup=None,
        )

    async def resume_game(self, bot: Bot, session: GameSession):
        """Resumes the quiz from the last known state."""
        await bot.send_message(session.chat_id, "Ok, let's continue translating words!")
        if session.current_question == -1:
            await self._send_category_selection(bot, session)
        else:
            sent_message = await bot.send_message(
                session.chat_id, "Loading your question..."
            )
            session.message_id = sent_message.message_id
            await self._send_question(bot, session, as_new_message=True)


game_registry.register(TranslateWordQuiz())
