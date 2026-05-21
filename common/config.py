from os import getenv
from os.path import normpath
from json import loads
from dataclasses import dataclass

from typing import List, Union

from dotenv import find_dotenv, load_dotenv


__all__ = ("CONFIG",)

DEFAULT_ENV_PATH = "config\\.env"

load_dotenv(find_dotenv(DEFAULT_ENV_PATH))


@dataclass
class BotConfig:
    token: str
    admin_list: Union[List[int], str]
    webapp_url: str


@dataclass
class DatabaseConfig:
    """Путь к файлу SQLite или параметры подключения к PostgreSQL."""
    path: str
    host: str = None
    port: str = None
    user: str = None
    password: str = None
    name: str = None

    @property
    def url(self) -> str:
        """Возвращает URL для подключения к БД (SQLite или PostgreSQL)."""
        if self.host:
            # Использовать PostgreSQL (asyncpg)
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            # Использовать SQLite (aiosqlite)
            p = normpath(self.path).replace("\\", "/")
            return f"sqlite+aiosqlite:///{p}"


@dataclass
class StorageConfig:
    """Локальное хранилище файлов (бесплатно, без облаков)."""
    root: str  # корневая папка (напр. storage или /app/storage)


@dataclass
class Config:
    bot: BotConfig
    database: DatabaseConfig
    storage: StorageConfig


CONFIG = Config(
    bot=BotConfig(
        token=getenv("BOT_TOKEN"),
        admin_list=loads(getenv("ADMIN_LIST")),
        webapp_url=getenv("WEBAPP_URL", "http://127.0.0.1:8001/streak"),
    ),
    database=DatabaseConfig(
        path=normpath(getenv("DB_PATH", "data/bot.sqlite")),
        host=getenv("DB_HOST"),
        port=getenv("DB_PORT", "5432"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASSWORD"),
        name=getenv("DB_NAME"),
    ),
    storage=StorageConfig(
        root=normpath(getenv("STORAGE_PATH", "storage")),
    ),
)
