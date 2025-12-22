from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from aiogram import Bot
from aiogram.types import Message, CallbackQuery

class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"

@dataclass
class GameSession:
    user_id: int
    chat_id: int
    message_id: int
    game_id: str
    status: GameStatus
    current_question: int = 0
    score: int = 0
    game_state: dict = field(default_factory=dict)
    
class BaseGame(ABC):
    """Abstract base class for all games."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id

    @abstractmethod
    async def get_display_name(self, lang: str) -> str:
        """Returns the localized name of the game."""
        pass

    @abstractmethod
    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        """Starts the game and returns the initial session state."""
        pass

    @abstractmethod
    async def handle_callback(self, bot: Bot, session: GameSession, callback: CallbackQuery) -> GameSession:
        """Handles user's inline button presses during the game."""
        pass

    @abstractmethod
    async def resume_game(self, bot: Bot, session: GameSession):
        """Resumes an existing game from the last known state."""
        pass

    @abstractmethod
    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        """Cleans up and ends the game session."""
        pass
