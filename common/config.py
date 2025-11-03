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
class Config:
    bot: BotConfig


CONFIG = Config(
    bot=BotConfig(
        token=getenv("BOT_TOKEN"),
        admin_list=loads(getenv("ADMIN_LIST")),
    ),
)
