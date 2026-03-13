from aiogram import Bot
from aiogram.types import Message, CallbackQuery
import re
import asyncio

from utils.localization import translator
from database.user_manager import user_manager

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from data.russian_tutor import SYSTEM_PROMPT
from utils.ollama_ai import get_ollama_response
from utils.bot_helpers import safe_edit_message


async def animate_loading(bot: Bot, chat_id: int, message_id: int, loading_text: str):
    """Animate loading message with cycling emojis while waiting for AI."""
    loading_emojis = ["⏳", "🔄", "✨", "🤔", "📚"]
    emoji_index = 0
    
    while True:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{loading_emojis[emoji_index]} {loading_text}..."
            )
        except:
            pass
        
        emoji_index = (emoji_index + 1) % len(loading_emojis)
        await asyncio.sleep(0.8)


def markdown_to_html(text: str) -> str:
    """Convert markdown formatting to Telegram HTML."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* -> <i>text</i> (single asterisks)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Code: `text` -> <code>text</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Strikethrough: ~~text~~ -> <s>text</s>
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    return text

async def get_user_language(user_id: int) -> str:
    """Gets user language with a fallback to 'en'."""
    user = await user_manager.get_user(user_id)
    return user.language if user else "en"

class RussianTutorGame(BaseGame):
    def __init__(self):
        """Initializes the game."""
        super().__init__(game_id="russian_tutor")

    def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        return translator.get_text("game_russian_tutor_name", lang)

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        """Starts a new game session."""
        lang = await get_user_language(user_id)
        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            game_state={
                "history": [{"role": "system", "content": SYSTEM_PROMPT}]
            },
        )

        start_text = translator.get_text("game_russian_tutor_start_text", lang)
        starting_text = translator.get_text("game_russian_tutor_starting", lang)

        new_message_id = await safe_edit_message(
            bot=bot,
            chat_id=session.chat_id,
            message_id=session.message_id,
            text=starting_text,
            reply_markup=None,
        )
        session.message_id = new_message_id

        sent_message = await bot.send_message(chat_id=session.chat_id, text=start_text)
        session.message_id = sent_message.message_id

        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        """Resumes an interrupted session."""
        lang = await get_user_language(session.user_id)
        resume_text = translator.get_text("game_russian_tutor_resume_text", lang)
        await bot.send_message(session.chat_id, resume_text)

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        """Handles inline button presses."""
        lang = await get_user_language(session.user_id)
        callback_text = translator.get_text("game_russian_tutor_callback_text", lang)
        await callback.answer(callback_text)
        return session

    async def handle_message(
        self, bot: Bot, session: GameSession, message: Message
    ) -> GameSession:
        """Handles a text message from the user."""
        user_text = message.text
        session.game_state["history"].append(
            {"role": "user", "content": user_text}
        )
        
        # Animated loading message
        loading_text = translator.get_text("game_russian_tutor_thinking", await get_user_language(session.user_id))
        
        loading_msg = await bot.send_message(
            chat_id=session.chat_id,
            text=f"⏳ {loading_text}..."
        )
        
        # Start animation in background
        animation_task = asyncio.create_task(
            animate_loading(bot, session.chat_id, loading_msg.message_id, loading_text)
        )
        
        # Get AI response (animation runs in parallel)
        ai_response = await get_ollama_response(session.game_state["history"])
        
        # Stop animation
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass
        
        # Delete loading message and send actual response
        try:
            await bot.delete_message(session.chat_id, loading_msg.message_id)
        except:
            pass
        
        # Convert markdown to HTML for proper formatting in Telegram
        formatted_response = markdown_to_html(ai_response)
        session.game_state["history"].append(
            {"role": "assistant", "content": ai_response}
        )
        await bot.send_message(
            chat_id=session.chat_id,
            text=formatted_response,
            parse_mode="HTML"
        )
        return session

    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        """Ends the game session."""
        session.status = GameStatus.FINISHED

        if send_message:
            lang = await get_user_language(session.user_id)
            final_text = translator.get_text("game_russian_tutor_end_text", lang)
            await bot.send_message(chat_id=session.chat_id, text=final_text)

game_registry.register(RussianTutorGame())
