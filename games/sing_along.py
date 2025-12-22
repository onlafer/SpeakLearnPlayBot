from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from data.sing_along_data import SING_ALONG_SONGS
from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager


class SingAlongGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="sing_along")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_sa_name", lang)

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
            game_state={"lang": lang}
        )

        try:
            await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
        except Exception:
            pass

        await self._send_song(bot, session)
        return session

    async def _send_song(self, bot: Bot, session: GameSession):
        lang = session.game_state.get("lang", "en")
        song_index = session.current_question
        
        if song_index >= len(SING_ALONG_SONGS):
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            return

        song_data = SING_ALONG_SONGS[song_index]
        
        btn_lyrics = translator.get_text("game_sa_btn_lyrics", lang)
        btn_minus = translator.get_text("game_sa_btn_minus", lang)
        btn_next = translator.get_text("game_sa_btn_next", lang)
        # btn_menu = translator.get_text("game_sa_btn_menu", lang)

        buttons = [
            [
                InlineKeyboardButton(text=btn_lyrics, callback_data=f"get_lyrics:{song_index}"),
                InlineKeyboardButton(text=btn_minus, callback_data=f"get_minus:{song_index}")
            ],
            [
                InlineKeyboardButton(text=btn_next, callback_data="next_song"),
            ]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        menu_hint = translator.get_text("menu_hint", lang)

        caption_text = translator.get_text("game_sa_caption", lang).format(
            title=song_data["title"],
            menu_hint=menu_hint
        )

        audio_id = song_data["full_audio_id"]

        try:
            await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
        except Exception:
            pass

        try:
            sent_message = await bot.send_audio(
                chat_id=session.chat_id,
                audio=audio_id,
                caption=caption_text,
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
            
        except Exception as e:
            error_msg = f"⚠️ Audio Error: {str(e)[:100]}"
            print(f"CRITICAL AUDIO ERROR: {e}")

            sent_message = await bot.send_message(
                chat_id=session.chat_id,
                text=error_msg,
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        lang = session.game_state.get("lang", "en")
        action, *data = callback.data.split(":")

        if action == "get_lyrics":
            song_index = int(data[0])
            song_data = SING_ALONG_SONGS[song_index]
            header = translator.get_text("game_sa_lyrics_title", lang).format(title=song_data["title"])
            text = f"**{header}**\n\n{song_data['lyrics']}"

            btn_back = translator.get_text("back_button", lang) or "🔙 Back"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_back, callback_data="back_to_song")]
            ])

            try:
                await bot.delete_message(chat_id=session.chat_id, message_id=session.message_id)
            except Exception:
                pass

            sent_message = await bot.send_message(
                chat_id=session.chat_id, 
                text=text, 
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
            await callback.answer()

        elif action == "get_minus":
            song_index = int(data[0])
            song_data = SING_ALONG_SONGS[song_index]
            caption = translator.get_text("game_sa_minus_caption", lang).format(title=song_data["title"])
            audio_id = song_data["minus_audio_id"]

            try:
                await bot.send_audio(
                    chat_id=session.chat_id,
                    audio=audio_id,
                    caption=caption
                )
            except Exception:
                await callback.answer("⚠️ Minus track error.", show_alert=True)
            await callback.answer()

        elif action == "next_song":
            session.current_question += 1
            await self._send_song(bot, session)
            await callback.answer()
            
        elif action == "back_to_song":
            await self._send_song(bot, session)
            await callback.answer()

        elif action == "finish":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            lang = session.game_state.get("lang", "en")
            final_text = translator.get_text("game_sa_end_text", lang)

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
        resume_text = translator.get_text("game_sa_resume", lang)
        
        await bot.send_message(session.chat_id, resume_text)
        await self._send_song(bot, session)

game_registry.register(SingAlongGame())
