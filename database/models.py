from sqlalchemy import Integer, String, JSON, BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from games.base import GameStatus


class UserModel(Base):
    """Модель для хранения пользователей в БД."""
    
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)


class GameSessionModel(Base):
    """Модель для хранения игровых сессий в БД."""
    
    __tablename__ = "game_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    message_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    game_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=GameStatus.IN_PROGRESS.value
    )
    current_question: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    game_state: Mapped[dict] = mapped_column(JSON, default=dict)
