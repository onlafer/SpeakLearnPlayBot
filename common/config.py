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
    """Путь к файлу SQLite (например data/bot.sqlite или /app/data/bot.sqlite в Docker)."""
    path: str

    @property
    def url(self) -> str:
        """Возвращает URL для подключения к SQLite (async через aiosqlite)."""
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
    ),
    storage=StorageConfig(
        root=normpath(getenv("STORAGE_PATH", "storage")),
    ),
)
