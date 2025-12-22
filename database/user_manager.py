"""Менеджер для работы с пользователями."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserModel
from database.base import async_session_maker


class UserManager:
    """Менеджер пользователей для работы с БД."""
    
    async def get_user(self, user_id: int) -> UserModel | None:
        """Получить пользователя из БД."""
        async with async_session_maker() as db_session:
            result = await db_session.execute(
                select(UserModel).where(UserModel.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_or_create_user(self, user_id: int, default_language: str = "en") -> UserModel:
        """Получить пользователя или создать нового."""
        import time
        
        user = await self.get_user(user_id)
        if user:
            return user

        async with async_session_maker() as db_session:
            new_user = UserModel(
                user_id=user_id,
                language=default_language,
                created_at=int(time.time())
            )
            db_session.add(new_user)
            await db_session.commit()
            await db_session.refresh(new_user)
            return new_user
    
    async def update_language(self, user_id: int, language: str):
        """Обновить язык пользователя."""
        async with async_session_maker() as db_session:
            result = await db_session.execute(
                select(UserModel).where(UserModel.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.language = language
                await db_session.commit()
            else:
                import time
                new_user = UserModel(
                    user_id=user_id,
                    language=language,
                    created_at=int(time.time())
                )
                db_session.add(new_user)
                await db_session.commit()


user_manager = UserManager()


