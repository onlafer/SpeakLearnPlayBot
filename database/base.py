from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from common.config import CONFIG


class Base(DeclarativeBase):
    pass


# Создаем движок для async подключения к PostgreSQL
engine = create_async_engine(
    CONFIG.database.url,
    echo=False,  # Установите True для отладки SQL запросов
    future=True,
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Получить async сессию БД."""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Инициализировать БД - создать все таблицы."""
    # Импортируем модели, чтобы они были зарегистрированы в Base.metadata
    from database.models import GameSessionModel, UserModel  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

