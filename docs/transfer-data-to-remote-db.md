# Перенос всех данных в удалённую БД (включая файлы)

Пошаговая инструкция: данные из `/data` и файлы в хранилище → удалённый PostgreSQL на сервере.

---

## Предварительно

В **config/.env** на вашем ПК должны быть указаны параметры **удалённой** БД:

```env
DB_HOST=IP_ВАШЕГО_СЕРВЕРА
DB_PORT=5432
DB_USER=root
DB_PASSWORD=ваш_пароль
DB_NAME=speaklearnplaybot
```

Проверка подключения:

```bash
uv run python -m scripts.check_db_connection
```

Должно вывести: `Подключение OK: (1,)`.

---

## Шаг 1. Создать таблицы в удалённой БД

Один раз создать все таблицы:

```bash
uv run python -m scripts.init_remote_db
```

---

## Шаг 2. Загрузить данные из папки /data в БД

Переносит в удалённую БД всё из `data/` (видео, квизы, фразы, песни и т.д.):

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

После шагов 1–3 у вас локально: удалённая БД заполнена + папка **storage/** с файлами.

---

## Шаг 4. Перенести папку storage на сервер

Если бот будет работать на сервере, папку **storage** нужно скопировать туда.

**С ПК (Windows) на Linux-сервер** (подставьте свой IP и путь на сервере):

```powershell
scp -r storage root@IP_СЕРВЕРА:/путь/к/проекту/
```

Или через **rsync** (если установлен, например в WSL):

```bash
rsync -avz storage/ root@IP_СЕРВЕРА:/путь/к/проекту/storage/
```

На сервере в `.env` указать путь к хранилищу, например:

```env
STORAGE_PATH=/путь/к/проекту/storage
```

---

## Краткий порядок команд

| Шаг | Команда |
|-----|--------|
| 1 | В `.env` указать удалённый DB_HOST, DB_PASSWORD и т.д. |
| 2 | `uv run python -m scripts.check_db_connection` — проверить подключение |
| 3 | `uv run python -m scripts.init_remote_db` — создать таблицы |
| 4 | `uv run python -m scripts.seed_data` — загрузить данные из /data в БД |
| 5 | `uv run python -m scripts.download_telegram_files` — скачать файлы ≤20 MB в storage |
| 6 | (по желанию) `uv run python -m scripts.download_telegram_files_user` — скачать большие файлы |
| 7 | Скопировать папку **storage** на сервер (scp/rsync) |

После этого в удалённой БД будут все данные, а файлы — в хранилище (локально и/или на сервере).
