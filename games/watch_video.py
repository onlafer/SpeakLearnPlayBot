import random
from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from data.watch_video_data import VIDEO_LIST
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.localization import translator
from database.user_manager import user_manager


class WatchVideoGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="watch_video")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_wv_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        indices = list(range(len(VIDEO_LIST)))
        random.shuffle(indices)

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
                "video_queue": indices
            }
        )

        try:
            await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
        except Exception:
            pass

        await self._send_video(bot, session)
        return session

    async def _send_video(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        step = session.current_question
        queue = session.game_state.get("video_queue", [])

        if step >= len(queue):
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            return

        video_real_index = queue[step]
        video_data = VIDEO_LIST[video_real_index]
        
        btn_next = translator.get_text("game_wv_btn_next", lang)

        buttons = [
            [
                InlineKeyboardButton(text=btn_next, callback_data="next_video"),
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        menu_hint = translator.get_text("menu_hint", lang)

        caption_text = translator.get_text("game_wv_caption", lang).format(
            title=video_data["title"],
            menu_hint=menu_hint
        )

        video_id = video_data["video_id"]

        try:
            await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
        except Exception:
            pass

        try:
            sent_message = await bot.send_video(
                chat_id=session.chat_id,
                video=video_id,
                caption=caption_text,
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
            
        except Exception as e:
            error_msg = f"⚠️ Video Error: {str(e)[:100]}"
            print(f"CRITICAL VIDEO ERROR: {e}")
            
            sent_message = await bot.send_message(
                chat_id=session.chat_id,
                text=error_msg,
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        action = callback.data

        if action == "next_video":
            session.current_question += 1
            await self._send_video(bot, session)
            await callback.answer()

        elif action == "finish":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            lang = session.game_state.get("lang", "en")
            final_text = translator.get_text("game_wv_end_text", lang)

            try:
                await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
            except Exception:
                pass

            sent_message = await bot.send_message(
                chat_id=session.chat_id,
                text=final_text,
                parse_mode="Markdown",
                reply_markup=None
            )
            session.message_id = sent_message.message_id

    async def resume_game(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        resume_text = translator.get_text("game_wv_resume", lang)
        
        await bot.send_message(session.chat_id, resume_text)
        await self._send_video(bot, session)

game_registry.register(WatchVideoGame())
