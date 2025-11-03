# SpeakLearnPlayBot - Адаптивный телеграм бот с играми

Полностью адаптивный Telegram бот на aiogram с системой игр и голосового распознавания.

## Установка

1. Установка uv (если не установлен):
```bash
pip install uv
```

2. Установка зависимостей:
```bash
uv sync
```

2. Создайте файл `.env` по пути `/config/.env`:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_LIST=[123456789]
```

3. Запустите бота:
```bash
uv run main.py
```
