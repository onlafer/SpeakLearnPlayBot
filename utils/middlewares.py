from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.user_manager import user_manager

class ActivityMiddleware(BaseMiddleware):
    """Мидлварь для отслеживания активности пользователя."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            # Обновляем активность
            await user_manager.update_activity(user.id)
            
        return await handler(event, data)
