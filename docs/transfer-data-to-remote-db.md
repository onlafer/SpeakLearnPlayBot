# Перенос всех данных на сервер (SQLite + файлы)

Пошаговая инструкция: данные из `/data` и файлы в хранилище → локальный файл SQLite и папка storage (для копирования на сервер).

---

## Предварительно

В **config/.env** задайте путь к БД (по умолчанию — локальный файл):

```env
DB_PATH=data/bot.sqlite
```

Проверка подключения:

```bash
uv run python -m scripts.check_db_connection
```

Должно вывести: `Подключение OK: (1,)`.

---

## Шаг 1. Создать таблицы в БД

Один раз создать все таблицы:

```bash
uv run python -m scripts.init_remote_db
```

---

## Шаг 2. Загрузить данные из папки /data в БД

Переносит в БД всё из `data/` (видео, квизы, фразы, песни и т.д.):

```bash
uv run python -m scripts.seed_data
```

При повторном запуске уже заполненные таблицы пропускаются.

---

## Шаг 3. Скачать файлы из Telegram в папку storage

Записей в БД уже есть (file_id), но сами файлы нужно сохранить на диск.

**Файлы до 20 MB:**

```bash
uv run python -m scripts.download_telegram_files
```

**Файлы больше 20 MB** (через аккаунт пользователя, Telethon):

1. В `config/.env` добавить TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_DOWNLOAD_CHAT_ID.
2. Переслать нужные файлы в один чат в том же порядке, что в БД.
3. Запустить:

```bash
uv run python -m scripts.download_telegram_files_user
```

После шагов 1–3 у вас локально: файл БД `data/bot.sqlite` заполнен + папка **storage/** с файлами.

---

## Шаг 4. Перенести данные на сервер

Скопируйте на сервер:

- папку **storage/**
- файл БД **data/bot.sqlite** (или каталог **data/** целиком)

**С ПК (Windows) на Linux-сервер** (подставьте свой IP и путь на сервере):

```powershell
scp -r storage data root@IP_СЕРВЕРА:/путь/к/проекту/
```

Или через **rsync** (например в WSL):

```bash
rsync -avz storage/ root@IP_СЕРВЕРА:/путь/к/проекту/storage/
rsync -avz data/ root@IP_СЕРВЕРА:/путь/к/проекту/data/
```

На сервере в `.env` укажите пути:

```env
DB_PATH=/путь/к/проекту/data/bot.sqlite
STORAGE_PATH=/путь/к/проекту/storage
```

---

## Краткий порядок команд

| Шаг | Команда |
|-----|--------|
| 1 | В `.env` указать `DB_PATH=data/bot.sqlite` (или свой путь) |
| 2 | `uv run python -m scripts.check_db_connection` — проверить подключение |
| 3 | `uv run python -m scripts.init_remote_db` — создать таблицы |
| 4 | `uv run python -m scripts.seed_data` — загрузить данные из /data в БД |
| 5 | `uv run python -m scripts.download_telegram_files` — скачать файлы ≤20 MB в storage |
| 6 | (по желанию) `uv run python -m scripts.download_telegram_files_user` — скачать большие файлы |
| 7 | Скопировать **storage** и **data** (или `data/bot.sqlite`) на сервер (scp/rsync) |

После этого на сервере будут актуальные данные БД и файлы в хранилище.
