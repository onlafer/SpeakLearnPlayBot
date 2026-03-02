from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from common.config import CONFIG


class Base(DeclarativeBase):
    pass


# Для SQLite: создать директорию файла БД, если её нет
_db_path = Path(CONFIG.database.path)
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    CONFIG.database.url,
    echo=False,
    future=True,
)

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
    from database.models import (
    FileModel,
    GameSessionModel,
    PositiveFeedbackModel,
    RussianCaseQuestionModel,
    RussianTutorPromptModel,
    SingAlongSongModel,
    SpeechPracticeCategoryModel,
    SpeechPracticeItemModel,
    TranslateWordCategoryModel,
    TranslateWordModel,
    UserModel,
    VerbAspectQuestionModel,
    VerbTenseQuestionModel,
    WatchVideoModel,
)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

