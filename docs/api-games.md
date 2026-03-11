# API игр (FastAPI)

Во все игры можно играть по HTTP API — те же сценарии, что в Telegram, доступны для веб-интерфейса и других клиентов.

## Запуск API

```bash
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Или:

```bash
uv run python -m api
```

Документация (Swagger): **http://localhost:8000/docs**

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/games?lang=en` | Список игр с названиями на выбранном языке |
| POST | `/api/games/{game_id}/start` | Запуск игры, возвращает первый экран (текст + кнопки) |
| POST | `/api/sessions/action` | Нажатие кнопки: `user_id`, `callback_data` |
| GET | `/api/sessions/current?user_id=...` | Текущая сессия и последний экран (восстановление после перезагрузки) |
| POST | `/api/sessions/cancel` | Отмена текущей игры |

## Пример для веба

1. **Список игр:** `GET /api/games?lang=ru`
2. **Старт игры:** `POST /api/games/translate_word_quiz/start` с телом `{"user_id": 123, "lang": "ru"}`  
   Ответ: `state.text`, `state.buttons` (массив `{text, callback_data}`), `score`, `status`.
3. **Нажатие кнопки:** `POST /api/sessions/action` с телом `{"user_id": 123, "callback_data": "select_category:0"}`  
   Ответ: новый `state`, обновлённый `score`, при завершении `finished: true`.
4. **Восстановление:** при перезагрузке страницы — `GET /api/sessions/current?user_id=123` и отобразить `state`.

Значение `callback_data` для кнопок совпадает с Telegram (например `select_case:nominative`, `answer:0:вариант`, `next_question`, `finish`, `show_menu`).

## Игры с голосом

Игры с голосовым вводом (речь, пение и т.п.) через API поддерживаются только по кнопкам; шаги с голосом в вебе нужно реализовать отдельно (запись аудио и отдельный эндпоинт при необходимости).
