# Запуск PostgreSQL на Linux-сервере

Чеклист действий для поднятия БД на сервере и подключения бота.

---

## Вариант A: PostgreSQL как системный сервис (apt/dnf)

### 1. Установить PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
```

### 2. Запустить и включить автозапуск

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

### 3. Создать пользователя и базу (под ваши .env)

Замените `root` и `your_strong_password` и `speaklearnplaybot` на свои значения из `config/.env`:

```bash
sudo -u postgres psql -c "CREATE USER root WITH PASSWORD 'your_strong_password';"
sudo -u postgres psql -c "CREATE DATABASE speaklearnplaybot OWNER root;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE speaklearnplaybot TO root;"
```

Для PostgreSQL 15+ также выдать право на схему public:

```bash
sudo -u postgres psql -d speaklearnplaybot -c "GRANT ALL ON SCHEMA public TO root;"
sudo -u postgres psql -d speaklearnplaybot -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO root;"
```

### 4. Разрешить подключения снаружи (если бот на другой машине)

**4.1.** Настроить `listen_addresses` в `postgresql.conf`:

```bash
# Путь часто: /etc/postgresql/16/main/postgresql.conf или /var/lib/pgsql/data/postgresql.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf
```

**4.2.** В `pg_hba.conf` добавить строку для вашего IP или сети (вместо `0.0.0.0/0` лучше указать IP бота):

```bash
# Пример: разрешить парольные подключения с любой сети (для продакшена сузьте диапазон)
echo "host    speaklearnplaybot    root    0.0.0.0/0    scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
```

**4.3.** Перезапустить PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 5. Файрвол (если включён)

```bash
# Ubuntu (ufw)
sudo ufw allow 5432/tcp
sudo ufw reload

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

### 6. Проверка с сервера

```bash
psql -h localhost -U root -d speaklearnplaybot -c "SELECT 1;"
```

---

## Вариант B: PostgreSQL в Docker на сервере

### 1. Установить Docker (если ещё нет)

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# выйти и зайти в сессию или: newgrp docker
```

### 2. Запустить контейнер PostgreSQL

Подставьте свои `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (как в .env):

```bash
docker volume create pgdata

docker run -d \
  --name postgres-bot \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=your_strong_password \
  -e POSTGRES_DB=speaklearnplaybot \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  --restart unless-stopped \
  postgres:16-alpine
```

### 3. Проверка

```bash
docker ps
docker exec -it postgres-bot psql -U root -d speaklearnplaybot -c "SELECT 1;"
```

### 4. Файрвол

Тот же шаг, что в варианте A (п. 5): открыть порт 5432/tcp.

---

## Подключение бота к БД на сервере

### Если бот запускается на той же машине

В `config/.env` на машине с ботом:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=root
DB_PASSWORD=your_strong_password
DB_NAME=speaklearnplaybot
```

### Если бот на другой машине (ПК или другой сервер)

В `config/.env` на машине с ботом:

```env
DB_HOST=IP_ВАШЕГО_СЕРВЕРА
DB_PORT=5432
DB_USER=root
DB_PASSWORD=your_strong_password
DB_NAME=speaklearnplaybot
```

После первого запуска бота выполнить миграции и сид данных:

```bash
uv run alembic upgrade head
uv run python -m scripts.seed_data
```

---

## Краткий чеклист (без деталей)

- [ ] Установить PostgreSQL (пакетами или Docker).
- [ ] Запустить сервис/контейнер и включить автозапуск.
- [ ] Создать пользователя и БД (логин/пароль/имя БД как в .env).
- [ ] Разрешить подключения: `listen_addresses`, `pg_hba.conf` (или только localhost, если бот на той же машине).
- [ ] Открыть порт 5432 в файрволе (если нужен доступ снаружи).
- [ ] Проверить подключение: `psql -h ... -U ... -d ... -c "SELECT 1;"`.
- [ ] В боте в `config/.env` указать `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
- [ ] Запустить миграции и сид: `alembic upgrade head`, `python -m scripts.seed_data`.
