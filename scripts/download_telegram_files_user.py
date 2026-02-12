"""
Скачивание файлов >20 MB через аккаунт пользователя (Telethon, MTProto).
Лимит Bot API — 20 MB; через пользовательский аккаунт можно скачивать до ~2 GB.

Как использовать:
1. Получить API_ID и API_HASH: https://my.telegram.org/apps
2. Добавить в config/.env:
   TELEGRAM_API_ID=12345
   TELEGRAM_API_HASH=your_hash
   TELEGRAM_DOWNLOAD_CHAT_ID=@your_channel или -1001234567890
3. Переслать/отправить все нужные файлы в один чат (канал или «Избранное»)
   в том же порядке, что в БД (сначала watch_video_0, ..., потом sing_along и т.д.).
4. Запуск: uv run python -m scripts.download_telegram_files_user
   При первом запуске введёте номер телефона и код из Telegram.

Скрипт берёт из БД записи FileModel с storage_path=telegram_cache/...,
получает сообщения с медиа из указанного чата по порядку и сохраняет файлы в storage.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from common.config import CONFIG
from database.base import async_session_maker
from database.models import FileModel
from utils.file_storage import get_root, save_file

EXT_BY_TYPE = {"video": "mp4", "document": "bin", "audio": "ogg", "voice": "ogg"}


def _get_telethon_config():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    chat = os.getenv("TELEGRAM_DOWNLOAD_CHAT_ID") or os.getenv("TELEGRAM_DOWNLOAD_CHAT")
    if not api_id or not api_hash:
        print(
            "Нужны TELEGRAM_API_ID и TELEGRAM_API_HASH в config/.env (получить: https://my.telegram.org/apps)"
        )
        sys.exit(1)
    if not chat:
        print(
            "Нужен TELEGRAM_DOWNLOAD_CHAT_ID в config/.env (например @channel или -1001234567890)"
        )
        sys.exit(1)
    return int(api_id), api_hash.strip(), chat.strip()


async def download_via_user_client() -> None:
    api_id, api_hash, chat_id = _get_telethon_config()

    try:
        from telethon import TelegramClient
        from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
    except ImportError:
        print("Установите Telethon: uv add telethon")
        sys.exit(1)

    async with async_session_maker() as session:
        r = await session.execute(
            select(FileModel)
            .where(
                FileModel.file_id.isnot(None),
                FileModel.storage_path.like("telegram_cache/%"),
            )
            .order_by(FileModel.id)
        )
        rows = r.scalars().all()

    if not rows:
        print("Нет записей с telegram_cache/ — нечего скачивать.")
        return

    root = get_root()
    session_file = Path.cwd() / "config" / "telethon_download.session"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        str(session_file),
        api_id,
        api_hash,
        system_version="4.16.30",
    )
    await client.start()
    print(f"Чат: {chat_id}. Сообщений с медиа в БД ожидается: {len(rows)}")

    try:
        entity = await client.get_entity(chat_id)
        messages_with_media = []
        async for msg in client.iter_messages(entity):
            if not msg.media:
                continue
            if isinstance(msg.media, (MessageMediaDocument, MessageMediaPhoto)):
                messages_with_media.append(msg)
            if len(messages_with_media) >= len(rows):
                break

        # Порядок: последнее сообщение в чате = первое в списке (iter_messages идёт от новых к старым)
        messages_with_media = list(reversed(messages_with_media))[: len(rows)]

        if len(messages_with_media) < len(rows):
            print(
                f"В чате найдено {len(messages_with_media)} медиа, в БД ожидается {len(rows)}. "
                "Отправьте/перешлите файлы в том же порядке, что в БД."
            )

        for i, row in enumerate(rows):
            if i >= len(messages_with_media):
                print(f"  [{i+1}/{len(rows)}] {row.key} — нет сообщения, пропуск")
                continue
            msg = messages_with_media[i]
            ext = EXT_BY_TYPE.get(row.file_type, "bin")
            relative_path = f"{row.file_type}s/{row.key}.{ext}"
            full_path = root / relative_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                await client.download_media(msg.media, file=str(full_path))
                async with async_session_maker() as session:
                    r = await session.get(FileModel, row.id)
                    if r:
                        r.storage_path = relative_path
                        await session.commit()
                print(f"  [{i+1}/{len(rows)}] {row.key} -> {relative_path}")
            except Exception as e:
                print(f"  [{i+1}/{len(rows)}] {row.key} ОШИБКА: {e}")
    finally:
        await client.disconnect()

    print("Готово.")


def main() -> None:
    asyncio.run(download_via_user_client())


if __name__ == "__main__":
    main()
