import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class SmokeError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project smoke checks before deploying the bot.",
    )
    parser.add_argument(
        "--env-file",
        default="config/.env",
        help="Path to the .env file relative to the project root.",
    )
    parser.add_argument(
        "--profile",
        choices=("quick", "models", "full"),
        default="quick",
        help="quick=env/import/db, models=quick+local models+ollama, full=models+telegram API",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path.resolve()


def print_result(status: str, title: str, details: str) -> None:
    print(f"[{status}] {title}: {details}")


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise SmokeError(f"Env file not found: {env_path}")
    load_dotenv(env_path, override=True)


def check_required_env() -> None:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise SmokeError("BOT_TOKEN is empty")

    admin_list_raw = os.getenv("ADMIN_LIST", "").strip()
    if not admin_list_raw:
        raise SmokeError("ADMIN_LIST is empty")

    try:
        admin_list = json.loads(admin_list_raw)
    except json.JSONDecodeError as exc:
        raise SmokeError(f"ADMIN_LIST is not valid JSON: {exc}") from exc

    if not isinstance(admin_list, list):
        raise SmokeError("ADMIN_LIST must be a JSON list")

    db_host = os.getenv("DB_HOST", "").strip()
    db_path = os.getenv("DB_PATH", "data/bot.sqlite").strip()
    storage_path = os.getenv("STORAGE_PATH", "storage").strip()

    if db_host:
        required = ("DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
        missing = [name for name in required if not os.getenv(name, "").strip()]
        if missing:
            raise SmokeError(f"PostgreSQL mode is enabled but missing: {', '.join(missing)}")
    else:
        sqlite_path = resolve_path(db_path)
        print_result("INFO", "SQLite path", str(sqlite_path))
        print_result("INFO", "SQLite dir", str(sqlite_path.parent))

    print_result("INFO", "Storage path", str(resolve_path(storage_path)))


def check_python_imports() -> None:
    import main as bot_main
    import api.main as api_main

    if not hasattr(bot_main, "main"):
        raise SmokeError("Bot entrypoint 'main.main' not found")
    if not hasattr(api_main, "app"):
        raise SmokeError("API entrypoint 'api.main.app' not found")


async def check_database() -> None:
    from database.base import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(text("SELECT 1"))
        if result.scalar() != 1:
            raise SmokeError("Database probe returned an unexpected value")


def check_f5_files_only() -> None:
    from utils.hf_tts import CKPT_FILE, VOCAB_FILE, VOICES

    required_files = [
        Path(CKPT_FILE),
        Path(VOCAB_FILE),
        Path(VOICES["male"]["audio"]),
        Path(VOICES["female"]["audio"]),
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise SmokeError("Missing F5-TTS files:\n- " + "\n- ".join(missing))


async def check_f5_inference() -> None:
    from utils.hf_tts import async_text_to_speech_f5

    audio = await async_text_to_speech_f5(
        "Привет, это короткий тест.",
        voice="female",
        use_accent=False,
    )
    if audio is None or audio.getbuffer().nbytes == 0:
        raise SmokeError("F5-TTS returned an empty audio buffer")


async def check_whisper_load() -> None:
    from utils.voice_recognition import get_whisper_model

    model = await asyncio.to_thread(get_whisper_model)
    if model is None:
        raise SmokeError("Whisper model was not initialized")


async def check_ollama() -> None:
    import aiohttp

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{host}/api/tags") as response:
                if response.status != 200:
                    body = await response.text()
                    raise SmokeError(f"Ollama returned {response.status}: {body[:200]}")
    except aiohttp.ClientError as exc:
        raise SmokeError(f"Cannot reach Ollama at {host}: {exc}") from exc


async def check_telegram_api() -> None:
    from aiogram import Bot

    token = os.getenv("BOT_TOKEN", "").strip()
    bot = Bot(token=token)
    try:
        me = await bot.get_me()
    finally:
        await bot.session.close()

    print_result("INFO", "Telegram bot", f"@{me.username} ({me.id})")


async def run_check(title: str, check, *args) -> bool:
    try:
        result = check(*args)
        if asyncio.iscoroutine(result):
            await result
        print_result("PASS", title, "ok")
        return True
    except Exception as exc:
        print_result("FAIL", title, str(exc))
        return False


async def main() -> int:
    args = parse_args()
    env_path = resolve_path(args.env_file)

    load_ok = await run_check("Env file", load_env_file, env_path)
    if not load_ok:
        return 1

    checks = [
        ("Required env", check_required_env),
        ("Python imports", check_python_imports),
        ("Database", check_database),
    ]

    if args.profile in {"models", "full"}:
        checks.extend(
            [
                ("F5 files", check_f5_files_only),
                ("Whisper load", check_whisper_load),
                ("F5 inference", check_f5_inference),
                ("Ollama", check_ollama),
            ]
        )

    if args.profile == "full":
        checks.append(("Telegram API", check_telegram_api))

    failed = False
    for title, check in checks:
        ok = await run_check(title, check)
        failed = failed or not ok

    if failed:
        print("\nSmoke check finished with errors.")
        return 1

    print(f"\nSmoke check passed with profile '{args.profile}'.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
