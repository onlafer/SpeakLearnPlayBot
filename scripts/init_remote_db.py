"""Создание таблиц в БД (локальной или удалённой). Запуск: uv run python -m scripts.init_remote_db"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import init_db


def main():
    asyncio.run(init_db())
    print("Таблицы созданы. Дальше: uv run python -m scripts.seed_data")


if __name__ == "__main__":
    main()
