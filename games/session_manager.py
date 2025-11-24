from sqlalchemy import select, delete

from .base import GameStatus, GameSession
from database.models import GameSessionModel
from database.base import async_session_maker


class SessionManager:
    """Менеджер сессий с хранением в PostgreSQL."""
    
    def _model_to_session(self, model: GameSessionModel) -> GameSession:
        """Преобразует модель БД в объект GameSession."""
        return GameSession(
            user_id=model.user_id,
            chat_id=model.chat_id,
            message_id=model.message_id,
            game_id=model.game_id,
            status=GameStatus(model.status),
            current_question=model.current_question,
            score=model.score,
            game_state=model.game_state or {},
        )
    
    def _session_to_model(self, session: GameSession) -> dict:
        """Преобразует объект GameSession в словарь для БД."""
        return {
            "user_id": session.user_id,
            "chat_id": session.chat_id,
            "message_id": session.message_id,
            "game_id": session.game_id,
            "status": session.status.value,
            "current_question": session.current_question,
            "score": session.score,
            "game_state": session.game_state,
        }

    async def start_session(self, session: GameSession):
        """Создает новую сессию в БД."""
        async with async_session_maker() as db_session:
            # Проверяем, есть ли уже активная сессия для этого пользователя
            existing = await db_session.execute(
                select(GameSessionModel).where(
                    GameSessionModel.user_id == session.user_id,
                    GameSessionModel.status == GameStatus.IN_PROGRESS.value
                )
            )
            existing_session = existing.scalar_one_or_none()
            
            if existing_session:
                # Обновляем существующую сессию
                for key, value in self._session_to_model(session).items():
                    setattr(existing_session, key, value)
            else:
                # Создаем новую сессию
                db_session.add(GameSessionModel(**self._session_to_model(session)))
            
            await db_session.commit()

    async def get_session(self, user_id: int) -> GameSession | None:
        """Получает активную сессию пользователя из БД."""
        async with async_session_maker() as db_session:
            result = await db_session.execute(
                select(GameSessionModel).where(
                    GameSessionModel.user_id == user_id,
                    GameSessionModel.status == GameStatus.IN_PROGRESS.value
                )
            )
            model = result.scalar_one_or_none()
            if model:
                return self._model_to_session(model)
            return None

    async def has_active_session(self, user_id: int) -> bool:
        """Checks if a user has a game that is currently in progress."""
        session = await self.get_session(user_id)
        return session is not None and session.status == GameStatus.IN_PROGRESS

    async def update_session(self, user_id: int, session: GameSession):
        """Обновляет сессию в БД."""
        async with async_session_maker() as db_session:
            result = await db_session.execute(
                select(GameSessionModel).where(
                    GameSessionModel.user_id == user_id,
                    GameSessionModel.status == GameStatus.IN_PROGRESS.value
                )
            )
            model = result.scalar_one_or_none()
            
            if model:
                for key, value in self._session_to_model(session).items():
                    setattr(model, key, value)
                await db_session.commit()
    
    async def end_session(self, user_id: int):
        """Удаляет активную сессию пользователя из БД."""
        async with async_session_maker() as db_session:
            await db_session.execute(
                delete(GameSessionModel).where(
                    GameSessionModel.user_id == user_id,
                    GameSessionModel.status == GameStatus.IN_PROGRESS.value
                )
            )
            await db_session.commit()

session_manager = SessionManager()
