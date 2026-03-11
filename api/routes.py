"""
Маршруты API для игр.
Игры запускаются через FakeBot; состояние экрана сохраняется в session.game_state["_api_last_screen"].
"""
from fastapi import APIRouter, HTTPException, Depends

from games.base import GameStatus
from games.game_registry import game_registry
from games.session_manager import session_manager
from games import (
    russian_tutor,
    translate_word_quiz,
    speech_practice_quiz,
    sing_along,
    watch_video,
    verb_tense_quiz,
    verb_aspect_quiz,
    russian_cases_quiz,
    translator_game,
)
from api.fake_bot import FakeBot, FakeMessage, FakeCallbackQuery
from api.schemas import (
    GameInfoSchema,
    GameStateSchema,
    ButtonSchema,
    StartGameRequest,
    StartGameResponse,
    ActionRequest,
    ActionResponse,
    CancelSessionRequest,
    CurrentSessionResponse,
)

router = APIRouter(prefix="/api", tags=["games"])


def _state_from_session(session) -> GameStateSchema | None:
    """Берёт последний экран из game_state (заполняется FakeBot)."""
    last = session.game_state.get("_api_last_screen")
    if not last:
        return None
    return GameStateSchema(
        text=last["text"],
        buttons=[ButtonSchema(**b) for b in last["buttons"]],
    )


@router.get("/games", response_model=list[GameInfoSchema])
async def list_games(lang: str = "en"):
    """Список всех игр с локализованными названиями."""
    games = game_registry.get_all_games()
    result = []
    for gid, game in games.items():
        name = game.get_display_name(lang)
        result.append(GameInfoSchema(game_id=gid, name=name))
    return result


@router.post("/games/{game_id}/start", response_model=StartGameResponse)
async def start_game(game_id: str, body: StartGameRequest):
    """
    Запуск игры. Возвращает первый экран (текст и кнопки).
    Для веба: сохраняйте user_id на клиенте и передавайте его в последующие action.
    """
    game = game_registry.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game not found: {game_id}")

    if await session_manager.has_active_session(body.user_id):
        raise HTTPException(
            status_code=409,
            detail="У пользователя уже есть активная игра. Сначала отмените её (POST /api/sessions/cancel).",
        )

    fake_message = FakeMessage(chat_id=body.user_id, message_id=0)
    fake_bot = FakeBot(session=None)  # игра создаёт session сама; экран сохраняем в fake_bot
    session = await game.start_game(fake_bot, body.user_id, fake_message)
    if body.lang:
        session.game_state["lang"] = body.lang
    last = fake_bot.get_last_screen()
    if last:
        session.game_state["_api_last_screen"] = last
    await session_manager.start_session(session)

    state = _state_from_session(session)
    if not state:
        raise HTTPException(status_code=500, detail="Game did not produce initial state")

    return StartGameResponse(
        game_id=session.game_id,
        score=session.score,
        current_question=session.current_question,
        status=session.status.value,
        state=state,
    )


@router.post("/sessions/action", response_model=ActionResponse)
async def session_action(body: ActionRequest):
    """
    Выполнить действие в текущей игре (нажатие кнопки).
    callback_data — строка как у Telegram (например select_case:nominative или answer:0:вариант).
    """
    session = await session_manager.get_session(body.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Нет активной сессии. Запустите игру через POST /api/games/{game_id}/start.")

    game = game_registry.get_game(session.game_id)
    if not game:
        await session_manager.end_session(body.user_id)
        raise HTTPException(status_code=404, detail="Игра не найдена.")

    fake_bot = FakeBot(session)
    fake_callback = FakeCallbackQuery(
        data=body.callback_data,
        message=FakeMessage(chat_id=session.chat_id, message_id=session.message_id),
    )
    updated = await game.handle_callback(fake_bot, session, fake_callback)

    if updated.status in (GameStatus.FINISHED, GameStatus.CANCELLED):
        await session_manager.end_session(body.user_id)
        state = _state_from_session(updated)
        return ActionResponse(
            game_id=updated.game_id,
            score=updated.score,
            current_question=updated.current_question,
            status=updated.status.value,
            state=state,
            finished=True,
        )

    await session_manager.update_session(body.user_id, updated)
    state = _state_from_session(updated)
    return ActionResponse(
        game_id=updated.game_id,
        score=updated.score,
        current_question=updated.current_question,
        status=updated.status.value,
        state=state,
        finished=False,
    )


@router.post("/sessions/cancel")
async def cancel_session(body: CancelSessionRequest):
    """Отменить текущую игру пользователя."""
    if not await session_manager.has_active_session(body.user_id):
        return {"ok": True, "message": "Нет активной сессии."}
    await session_manager.end_session(body.user_id)
    return {"ok": True, "message": "Игра отменена."}


@router.get("/sessions/current", response_model=CurrentSessionResponse | None)
async def get_current_session(user_id: int):
    """
    Текущая сессия и последний экран (для восстановления после перезагрузки страницы).
    Если сессии нет — 404.
    """
    session = await session_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Нет активной сессии.")
    state = _state_from_session(session)
    return CurrentSessionResponse(
        game_id=session.game_id,
        score=session.score,
        current_question=session.current_question,
        status=session.status.value,
        state=state,
    )
