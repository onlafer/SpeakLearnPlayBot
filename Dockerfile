# Dockerfile для запуска бота (production)
FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для whisper/ffmpeg (голосовое распознавание)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Приложение ожидает config/.env с BOT_TOKEN, DB_*, ADMIN_LIST, GIGACHAT_CREDENTIALS
# Передавайте переменные через -e или монтируйте config/.env
CMD ["python", "main.py"]
