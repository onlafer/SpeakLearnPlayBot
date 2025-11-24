import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from common.bot_commands import bot_private_commands
from common.config import CONFIG
from handlers.shared import router as common_router
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main bot function."""
    # Инициализируем БД
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully!")
    
    bot = Bot(
        token=CONFIG.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=bot_private_commands,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    logger.info("Bot started successfully!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Bot is shutting down...")
        await bot.session.close()
        logger.info("Bot session closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
