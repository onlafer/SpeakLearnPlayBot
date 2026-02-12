# База данных на сервере (SQLite)

Бот использует **SQLite**: отдельный сервер БД не нужен.

## Локально

По умолчанию файл БД: `data/bot.sqlite`. Путь задаётся в `config/.env`:

```env
DB_PATH=data/bot.sqlite
```

Убедитесь, что каталог `data/` существует и доступен для записи (он создаётся автоматически при первом запуске).

## В Docker

В `docker-compose.yml` для бота задаётся:

- `DB_PATH=/app/data/bot.sqlite`
- том `bot_data` для каталога `/app/data`

Файл БД сохраняется между перезапусками контейнера.

## На Linux-сервере без Docker

1. Разместите проект на сервере.
2. В `.env` укажите путь к файлу БД, например:
   ```env
   DB_PATH=/var/lib/speaklearnplaybot/data/bot.sqlite
   ```
3. Создайте каталог и дайте права пользователю, от которого запускается бот:
   ```bash
   sudo mkdir -p /var/lib/speaklearnplaybot/data
   sudo chown YOUR_USER:YOUR_USER /var/lib/speaklearnplaybot/data
   ```
4. Запустите бота; при первом запуске таблицы создадутся автоматически (или выполните `uv run python -m scripts.init_remote_db` и `uv run python -m scripts.seed_data` по инструкции в [transfer-data-to-remote-db.md](transfer-data-to-remote-db.md)).

Отдельная установка PostgreSQL или иной СУБД не требуется.
