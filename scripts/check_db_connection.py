"""Проверка подключения к БД. Запуск: uv run python -m scripts.check_db_connection"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from database.base import async_session_maker


async def check():
    try:
        async with async_session_maker() as session:
            r = await session.execute(text("SELECT 1"))
            print("Подключение OK:", r.scalar())
    except Exception as e:
        print("Ошибка подключения:", e)
        sys.exit(1)


def main():
    asyncio.run(check())


if __name__ == "__main__":
    main()
