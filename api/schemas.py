"""Pydantic-схемы для API игр."""
from pydantic import BaseModel, Field


class ButtonSchema(BaseModel):
    text: str
    callback_data: str


class GameStateSchema(BaseModel):
    """Текущий экран игры: текст и кнопки."""
    text: str
    buttons: list[ButtonSchema] = Field(default_factory=list)


class GameInfoSchema(BaseModel):
    """Информация об игре для списка."""
    game_id: str
    name: str


class StartGameRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя (для API/веба — любой идентификатор)")
    lang: str | None = Field(None, description="Язык интерфейса (en, ru, ...). По умолчанию en")


class StartGameResponse(BaseModel):
    session_id: int | None = Field(None, description="ID сессии в БД (опционально)")
    game_id: str
    score: int = 0
    current_question: int = 0
    status: str = "in_progress"
    state: GameStateSchema = Field(..., description="Текущий экран: текст и кнопки")


class ActionRequest(BaseModel):
    user_id: int
    callback_data: str = Field(..., description="Значение кнопки (как в Telegram callback_data)")


class ActionResponse(BaseModel):
    game_id: str
    score: int
    current_question: int
    status: str = Field(..., description="in_progress | finished | cancelled")
    state: GameStateSchema | None = Field(None, description="Новый экран; при finish может быть итоговый текст")
    finished: bool = Field(False, description="True если игра завершена")


class CancelSessionRequest(BaseModel):
    user_id: int


class CurrentSessionResponse(BaseModel):
    game_id: str
    score: int
    current_question: int
    status: str
    state: GameStateSchema | None = Field(None, description="Последний экран игры")
