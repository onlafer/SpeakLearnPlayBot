"""Вспомогательные функции для работы с ботом."""

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest


async def safe_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> int:
    """
    Безопасно редактирует сообщение. Если сообщение не найдено, отправляет новое.
    
    Returns:
        int: ID сообщения (либо существующего, либо нового)
    """
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        return message_id
    except TelegramBadRequest as e:
        if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower():
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return sent_message.message_id
        raise


