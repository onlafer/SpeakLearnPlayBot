"""
Скачивает файлы из Telegram по file_id и сохраняет в хранилище (storage/).
Запуск: uv run python -m scripts.download_telegram_files

Нужен BOT_TOKEN в config/.env. Для записей в FileModel, у которых есть file_id
(Telegram), но файл ещё не на диске (storage_path вида telegram_cache/...),
скачивает файл через Bot API и сохраняет в storage, обновляя storage_path.
После этого можно передать папку storage другому пользователю вместе с дампом БД.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot
from sqlalchemy import select

from common.config import CONFIG
from database.base import async_session_maker
from database.models import FileModel
from utils.file_storage import get_root, save_file


# Лимит размера файла для скачивания через Telegram Bot API (~20 MB)
TELEGRAM_DOWNLOAD_LIMIT_BYTES = 20 * 1024 * 1024

# расширение по типу, если Telegram не вернул путь с расширением
EXT_BY_TYPE = {
    "video": "mp4",
    "document": "bin",
    "audio": "ogg",
    "voice": "ogg",
}


async def download_all() -> None:
    bot = Bot(token=CONFIG.bot.token)
    try:
        async with async_session_maker() as session:
            r = await session.execute(
                select(FileModel).where(
                    FileModel.file_id.isnot(None),
                    FileModel.storage_path.like("telegram_cache/%"),
                )
            )
            rows = r.scalars().all()
        if not rows:
            print("Нет записей с file_id и плейсхолдером telegram_cache/ — нечего скачивать.")
            return

        root = get_root()
        print(f"Хранилище: {root}")
        print(f"Скачиваю {len(rows)} файлов...")

        skipped_big = 0
        for i, row in enumerate(rows):
            try:
                tg_file = await bot.get_file(row.file_id)
                # Telegram Bot API не даёт скачивать файлы > 20 MB
                if getattr(tg_file, "file_size", None) and tg_file.file_size > TELEGRAM_DOWNLOAD_LIMIT_BYTES:
                    size_mb = tg_file.file_size / (1024 * 1024)
                    print(f"  [{i+1}/{len(rows)}] {row.key} пропуск: файл {size_mb:.1f} MB (лимит Bot API 20 MB)")
                    skipped_big += 1
                    continue

                path_from_tg = tg_file.file_path or ""
                ext = Path(path_from_tg).suffix.lstrip(".") if path_from_tg else EXT_BY_TYPE.get(row.file_type, "bin")
                if not ext:
                    ext = EXT_BY_TYPE.get(row.file_type, "bin")
                relative_path = f"{row.file_type}s/{row.key}.{ext}"

                file_bytes = await bot.download_file(tg_file.file_path)
                if isinstance(file_bytes, bytes):
                    data = file_bytes
                elif hasattr(file_bytes, "read"):
                    data = file_bytes.read()
                else:
                    data = b"".join([chunk async for chunk in file_bytes])

                save_file(relative_path, data)
                async with async_session_maker() as session:
                    r = await session.get(FileModel, row.id)
                    if r:
                        r.storage_path = relative_path
                        await session.commit()
                print(f"  [{i+1}/{len(rows)}] {row.key} -> {relative_path}")
            except Exception as e:
                err_text = str(e).lower()
                if "too big" in err_text or "file is too big" in err_text:
                    skipped_big += 1
                    print(f"  [{i+1}/{len(rows)}] {row.key} пропуск: файл слишком большой (лимит Bot API 20 MB)")
                else:
                    print(f"  [{i+1}/{len(rows)}] {row.key} ОШИБКА: {e}")

        if skipped_big:
            print(f"\nПропущено больших файлов: {skipped_big}. Они остаются с file_id — бот по-прежнему может отправлять их из кеша Telegram.")

        print("Готово.")
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(download_all())


if __name__ == "__main__":
    main()
