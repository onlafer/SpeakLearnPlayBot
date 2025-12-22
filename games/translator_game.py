from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR_LIB = True
except ImportError:
    HAS_TRANSLATOR_LIB = False

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager

SUPPORTED_LANGUAGES = [
    ("ar", "lang_ar"),
    ("zh-CN", "lang_zh"),
    ("en", "lang_en"),
    ("fr", "lang_fr"),
    ("fa", "lang_fa"),
    ("es", "lang_es"),
    ("vi", "lang_vi"),
    ("ja", "lang_ja"),
]


class TranslatorGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="translator_game")

    def get_display_name(self, lang: str) -> str:
        """Возвращает локализованное название игры."""
        return translator.get_text("game_translator_name", lang)

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
            game_state={"ui_lang": lang, "target_lang": None}
        )
        
        await self._send_language_selection(bot, session)
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        ui_lang = session.game_state.get("ui_lang", "en")
        target_lang = session.game_state.get("target_lang")

        if not target_lang:
            await self._send_language_selection(bot, session, as_new_message=True)
        else:
            resume_text = translator.get_text("game_translator_resume", ui_lang)
            await bot.send_message(session.chat_id, resume_text)

    async def _send_language_selection(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        ui_lang = session.game_state.get("ui_lang", "en")
        
        buttons = []
        for code, label_key in SUPPORTED_LANGUAGES:
            label = translator.get_text(label_key, ui_lang)
            buttons.append([
                InlineKeyboardButton(text=label, callback_data=f"set_trans_lang:{code}")
            ])

        btn_menu_text = translator.get_text("game_speech_practice_button_menu", ui_lang) 
        if not btn_menu_text or btn_menu_text.startswith("game_"):
            btn_menu_text = "Menu"
            
        buttons.append([InlineKeyboardButton(text=btn_menu_text, callback_data="finish_translation")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = translator.get_text("game_translator_select_lang", ui_lang)

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
            session.message_id = new_message_id

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        ui_lang = session.game_state.get("ui_lang", "en")
        action, *data = callback.data.split(":")

        if action == "set_trans_lang":
            target_code = data[0]
            session.game_state["target_lang"] = target_code
            
            lang_name = target_code
            for code, key in SUPPORTED_LANGUAGES:
                if code == target_code:
                    lang_name = translator.get_text(key, ui_lang)
                    break
            
            confirm_text = translator.get_text("game_translator_lang_set", ui_lang).format(lang=lang_name)
            
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=confirm_text,
                parse_mode="Markdown",
                reply_markup=None
            )
            await callback.answer()
            
        elif action == "finish_translation":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)
            await callback.answer()

        return session

    async def handle_message(self, bot: Bot, session: GameSession, message: Message) -> GameSession:
        ui_lang = session.game_state.get("ui_lang", "en")
        target_lang = session.game_state.get("target_lang")

        if message.text and message.text.startswith("/"):
            return session

        if not target_lang:
            await self._send_language_selection(bot, session, as_new_message=True)
            return session
        
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")

        translation_result = ""
        
        if HAS_TRANSLATOR_LIB:
            try:
                translator_service = GoogleTranslator(source='auto', target=target_lang)
                translation_result = translator_service.translate(message.text)
            except Exception as e:
                print(f"Translator error: {e}")
                translation_result = None
        else:
            translation_result = "Error: 'deep_translator' library is not installed."

        if translation_result:
            lang_label = target_lang
            for code, key in SUPPORTED_LANGUAGES:
                if code == target_lang:
                    lang_label = translator.get_text(key, ui_lang)
                    break

            response_text = translator.get_text("game_translator_result", ui_lang).format(
                original=message.text,
                lang=lang_label,
                translation=translation_result
            )
            
            await message.reply(response_text, parse_mode="Markdown")
        else:
            error_text = translator.get_text("game_translator_error", ui_lang)
            await message.reply(error_text)

        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        """Завершает сессию перевода."""
        if send_message:
            ui_lang = session.game_state.get("ui_lang", "en")
            
            end_text = translator.get_text("game_translator_end", ui_lang)
            
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=end_text,
                parse_mode="Markdown",
                reply_markup=None
            )


game_registry.register(TranslatorGame())
