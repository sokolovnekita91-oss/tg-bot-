"""
Crypto Analysis Telegram Bot
High-performance async bot with caching, connection pooling, and multi-language support
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import Database
from cache import CacheManager
from api_client import BybitClient
from scheduler import Scheduler
from handlers import router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("aiohttp").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, db: Database, cache: CacheManager, api: BybitClient, scheduler: Scheduler):
    logger.info("Starting bot...")
    await db.init()
    logger.info("Database initialized")
    
    logger.info("Preloading cache...")
    await cache.preload(api)
    logger.info("Cache preloaded")
    
    asyncio.create_task(cache.background_updater(api))
    asyncio.create_task(scheduler.run())
    
    logger.info("Bot started successfully!")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db = Database()
    cache = CacheManager()
    api = BybitClient()
    scheduler = Scheduler(bot=bot, db=db, cache=cache, api=api)

    dp["db"] = db
    dp["cache"] = cache
    dp["api"] = api
    dp["scheduler"] = scheduler

    dp.include_router(router)

    await on_startup(bot, db, cache, api, scheduler)

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await api.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())