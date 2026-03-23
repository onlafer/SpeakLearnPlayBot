import random

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from data.verb_tests_data import VERB_TESTS_QUESTIONS
from games.base import BaseGame, GameSession, GameStatus
from games.game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager

QUESTIONS_PER_ROUND = 10  # можно изменить


class VerbTestsQuiz(BaseGame):
    def __init__(self):
        super().__init__(game_id="verb_tests_quiz")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_verb_tests_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        # Перемешиваем все вопросы и берём первые QUESTIONS_PER_ROUND
        all_questions = VERB_TESTS_QUESTIONS.copy()
        random.shuffle(all_questions)
        round_questions = all_questions[:QUESTIONS_PER_ROUND]

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
                "questions": round_questions,
                "total": len(round_questions)
            }
        )
        await self._send_question(bot, session)
        return session

    async def _send_question(self, bot: Bot, session: GameSession):
        lang = session.game_state["lang"]
        q_index = session.current_question
        question_data = session.game_state["questions"][q_index]

        # Текст вопроса с темой
        theme = question_data["theme"]
        question_text = question_data["question"]
        options = question_data["options"]

        # Формируем кнопки
        buttons = []
        for i, opt in enumerate(options):
            callback_data = f"vt_answer:{q_index}:{i}"
            buttons.append([InlineKeyboardButton(text=opt, callback_data=callback_data)])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Добавляем подсказку меню
        menu_hint = translator.get_text("menu_hint", lang)
        full_text = f"*{theme}*\n\n{question_text}\n\n{menu_hint}"

        await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=full_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def handle_callback(self, bot: Bot, session: GameSession, callback: CallbackQuery) -> GameSession:
        action, *data = callback.data.split(":")
        lang = session.game_state["lang"]

        if action == "vt_answer":
            q_index_str, answer_index_str = data
            q_index = int(q_index_str)
            answer_index = int(answer_index_str)

            if q_index != session.current_question:
                await callback.answer(
                    translator.get_text("game_verb_tests_already_answered", lang),
                    show_alert=True
                )
                return session

            question_data = session.game_state["questions"][q_index]
            correct_index = question_data["correct"]
            options = question_data["options"]

            if answer_index == correct_index:
                session.score += 1
                feedback = translator.get_text("game_verb_tests_correct", lang)
                await callback.answer("✅", show_alert=False)
            else:
                correct_answer = options[correct_index]
                feedback = translator.get_text("game_verb_tests_incorrect", lang).format(correct=correct_answer)
                await callback.answer("❌", show_alert=False)

            # Определяем, последний ли это вопрос
            is_last = (q_index + 1) >= session.game_state["total"]

            if is_last:
                next_text = translator.get_text("game_verb_tests_finish", lang)
                next_callback = "finish"
            else:
                next_text = translator.get_text("game_verb_tests_next", lang)
                next_callback = "next_question"

            menu_text = translator.get_text("game_verb_tests_menu", lang)

            buttons = [
                [
                    InlineKeyboardButton(text=menu_text, callback_data="show_menu"),
                    InlineKeyboardButton(text=next_text, callback_data=next_callback)
                ]
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            # Обновляем сообщение: добавляем фидбек
            original_text = callback.message.text
            new_text = f"{original_text}\n\n{feedback}"

            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=new_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
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

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state["lang"]
        resume_text = translator.get_text("game_verb_tests_resume", lang)
        await bot.send_message(session.chat_id, resume_text)
        await self._send_question(bot, session)

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            lang = session.game_state["lang"]
            total = session.game_state["total"]
            score = session.score
            end_text = translator.get_text("game_verb_tests_end", lang).format(score=score, total=total)
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=end_text,
                reply_markup=None,
                parse_mode="Markdown"
            )


game_registry.register(VerbTestsQuiz())