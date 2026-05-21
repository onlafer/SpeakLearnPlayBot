import random
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from data.reading_comprehension_data import READING_TEXTS
from games.base import BaseGame, GameSession, GameStatus
from games.game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager
from utils.ollama_ai import is_answer_correct  # Используем локальную нейросеть

TEXTS_PER_GAME = 2  # сколько текстов за одну игру (можно 1, 2 или больше)
QUESTIONS_PER_TEXT = 6  # у каждого текста по 6 вопросов


async def check_answer_with_ai(question: str, user_answer: str, expected_answers: list) -> bool:
    """Проверяет ответ пользователя через локальную нейросеть."""
    from utils.ollama_ai import is_answer_correct
    return await is_answer_correct(question, user_answer, expected_answers)


class ReadingComprehensionQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="reading_comprehension_quiz")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_reading_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        # Выбираем случайные тексты
        all_texts = READING_TEXTS.copy()
        random.shuffle(all_texts)
        selected_texts = all_texts[:TEXTS_PER_GAME]

        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=0,   # индекс вопроса в общем списке
            score=0,
            game_state={
                "lang": lang,
                "texts": selected_texts,
                "current_text_index": 0,
                "total_questions": len(selected_texts) * QUESTIONS_PER_TEXT,
                "questions_asked": [],   # список уже заданных вопросов (object)
            }
        )
        await self._send_text_and_first_question(bot, session)
        return session

    async def _send_text_and_first_question(self, bot: Bot, session: GameSession):
        """Отправляет текст и затем первый вопрос."""
        lang = session.game_state["lang"]
        idx = session.game_state["current_text_index"]
        text_data = session.game_state["texts"][idx]
        text = text_data["text"]
        title = text_data.get("title", "Текст")

        # Отправляем текст
        await bot.send_message(
            chat_id=session.chat_id,
            text=f"*{title}*\n\n{text}",
            parse_mode="Markdown"
        )
        # Затем задаём первый вопрос
        await self._send_question(bot, session)

    async def _send_question(self, bot: Bot, session: GameSession):
        lang = session.game_state["lang"]
        text_idx = session.game_state["current_text_index"]
        q_index = session.current_question % QUESTIONS_PER_TEXT
        question_data = session.game_state["texts"][text_idx]["questions"][q_index]
        question = question_data["question"]

        # Сохраняем эталонные ответы для проверки
        session.game_state["current_question_data"] = question_data

        # Кнопка "Пропустить"
        skip_btn = InlineKeyboardButton(
            text=translator.get_text("game_reading_skip", lang),
            callback_data="skip_question"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[skip_btn]])

        await bot.send_message(
            chat_id=session.chat_id,
            text=f"*Вопрос {session.current_question + 1}/{session.game_state['total_questions']}*\n\n{question}\n\n{translator.get_text('game_reading_instruction', lang)}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def handle_message(self, bot: Bot, session: GameSession, message: Message) -> GameSession:
        lang = session.game_state["lang"]
        user_answer = message.text.strip()
        question_data = session.game_state["current_question_data"]
        question = question_data["question"]
        expected_answers = question_data["answers"]

        # Проверка через нейросеть
        is_correct = await check_answer_with_ai(question, user_answer, expected_answers)

        if is_correct:
            session.score += 1
            await message.reply(translator.get_text("game_reading_correct", lang))
        else:
            # Показываем эталонный ответ (первый из списка)
            correct_example = expected_answers[0]
            await message.reply(
                translator.get_text("game_reading_wrong", lang).format(correct=correct_example)
            )

        # Переход к следующему вопросу
        session.current_question += 1
        if session.current_question >= session.game_state["total_questions"]:
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
        else:
            # Если закончились вопросы текущего текста, переключаем текст
            if session.current_question % QUESTIONS_PER_TEXT == 0:
                session.game_state["current_text_index"] += 1
                await self._send_text_and_first_question(bot, session)
            else:
                await self._send_question(bot, session)
        return session

    async def handle_callback(self, bot: Bot, session: GameSession, callback: CallbackQuery) -> GameSession:
        if callback.data == "skip_question":
            lang = session.game_state["lang"]
            # Пропускаем вопрос (не засчитываем)
            session.current_question += 1
            if session.current_question >= session.game_state["total_questions"]:
                session.status = GameStatus.FINISHED
                await self.end_game(bot, session)
            else:
                if session.current_question % QUESTIONS_PER_TEXT == 0:
                    session.game_state["current_text_index"] += 1
                    await self._send_text_and_first_question(bot, session)
                else:
                    await self._send_question(bot, session)
            await callback.answer(translator.get_text("game_reading_skipped", lang))
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state["lang"]
        await bot.send_message(session.chat_id, translator.get_text("game_reading_resume", lang))
        await self._send_question(bot, session)

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            lang = session.game_state["lang"]
            score = session.score
            total = session.game_state["total_questions"]
            await bot.send_message(
                chat_id=session.chat_id,
                text=translator.get_text("game_reading_end", lang).format(score=score, total=total),
                parse_mode="Markdown"
            )


game_registry.register(ReadingComprehensionQuiz())