"""
FastAPI-приложение для доступа к играм по API.
Запуск: uv run python -m api.main  (порт 8001)
Документация: http://127.0.0.1:8001/docs  (на Windows используйте 127.0.0.1, не 0.0.0.0)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация БД при старте API."""
    await init_db()
    print("\n  Документация API: http://127.0.0.1:8001/docs")
    print("  (в браузере вводите 127.0.0.1, не 0.0.0.0)\n")
    yield
    # shutdown при необходимости


app = FastAPI(
    title="Speak Learn Play — Games API",
    description="API для игры в те же игры, что и в Telegram-боте. Для веб-интерфейса и внешних клиентов.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",   # Swagger UI
    redoc_url="/redoc", # ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "Speak Learn Play Games API",
        "docs": "/docs",
        "api": "/api/games",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8001, reload=True)
