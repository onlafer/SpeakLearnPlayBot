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


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @property
    def url(self) -> str:
        """Возвращает URL для подключения к PostgreSQL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class Config:
    bot: BotConfig
    database: DatabaseConfig


CONFIG = Config(
    bot=BotConfig(
        token=getenv("BOT_TOKEN"),
        admin_list=loads(getenv("ADMIN_LIST")),
    ),
    database=DatabaseConfig(
        host=getenv("DB_HOST", "localhost"),
        port=int(getenv("DB_PORT", "5432")),
        user=getenv("DB_USER", "postgres"),
        password=getenv("DB_PASSWORD", ""),
        database=getenv("DB_NAME", "speaklearnplaybot"),
    ),
)
