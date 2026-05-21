"""
Fake Bot для запуска игр без Telegram: перехватывает send_message/edit_message
и сохраняет текст и кнопки в session.game_state["_api_last_screen"] для ответа API.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from games.base import GameSession


def _extract_buttons(reply_markup: InlineKeyboardMarkup | None) -> list[dict]:
    if reply_markup is None or not reply_markup.inline_keyboard:
        return []
    return [
        {"text": btn.text, "callback_data": btn.callback_data or ""}
        for row in reply_markup.inline_keyboard
        for btn in row
    ]


class FakeMessage:
    """Поддельное сообщение для start_game (нужны chat_id и message_id)."""
    def __init__(self, chat_id: int, message_id: int = 0, text: str = ""):
        self.chat = type("Chat", (), {"id": chat_id})()
        self.message_id = message_id
        self.text = text


class FakeCallbackQuery:
    """Поддельный CallbackQuery для handle_callback (нужны data и message)."""
    def __init__(self, data: str, message: FakeMessage):
        self.data = data
        self.message = message

    async def answer(self, text: str | None = None, show_alert: bool = False):
        """Игровой код вызывает callback.answer() — заглушка."""
        pass


class FakeBot:
    """
    Бот-заглушка: при send_message и edit_message_text сохраняет
    текст и кнопки. Если передан session — пишет в session.game_state["_api_last_screen"],
    иначе в self._last_screen (для start_game, когда сессия создаётся внутри игры).
    """
    def __init__(self, session: GameSession | None = None):
        self._session = session
        self._last_screen: dict | None = None

    def _store(self, text: str, reply_markup: InlineKeyboardMarkup | None):
        data = {"text": text, "buttons": _extract_buttons(reply_markup)}
        if self._session is not None:
            self._session.game_state["_api_last_screen"] = data
        else:
            self._last_screen = data

    def get_last_screen(self) -> dict | None:
        """Для start_game: после возврата из игры скопировать в session.game_state."""
        return self._last_screen

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str | None = None,
    ):
        self._store(text, reply_markup)
        return FakeMessage(chat_id=chat_id, message_id=1)

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str | None = None,
    ):
        self._store(text, reply_markup)
        return message_id
