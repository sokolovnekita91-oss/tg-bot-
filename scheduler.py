"""Background scheduler for broadcasts"""
import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import SCHEDULER_INTERVAL
from database import Database
from cache import CacheManager
from api_client import BybitClient
from analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, bot: Bot, db: Database, cache: CacheManager, api: BybitClient):
        self.bot   = bot
        self.db    = db
        self.cache = cache
        self.api   = api
        self._sem  = asyncio.Semaphore(10)

    async def run(self):
        logger.info("Scheduler started")
        while True:
            try:
                await asyncio.sleep(SCHEDULER_INTERVAL)
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    async def _tick(self):
        now   = int(time.time())
        users = await self.db.get_users_to_notify(now)
        if not users:
            return
        logger.info(f"Broadcasting to {len(users)} users")
        spot       = self.cache.get("spot")
        linear     = self.cache.get("linear")
        fear_greed = self.cache.get("fear_greed")
        oi         = self.cache.get("open_interest")
        if not spot:
            data   = await self.api.fetch_all_data()
            spot   = data.get("spot")
            linear = data.get("linear")
            fear_greed = data.get("fear_greed")
            oi     = data.get("open_interest")
        if not spot:
            logger.warning("No market data for broadcast")
            return
        tasks = [self._send(u, spot, linear, fear_greed, oi, now) for u in users]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send(self, user, spot, linear, fg, oi, now):
        async with self._sem:
            uid  = user["user_id"]
            lang = user["language"]
            try:
                selected = await self.db.get_user_categories(uid)
                if not selected:
                    return
                analyzer = MarketAnalyzer(spot, linear, fg, oi, lang)
                report   = analyzer.build_report(selected)
                await self.bot.send_message(uid, report, parse_mode="HTML")
                await self.db.update_last_sent(uid, now)
            except TelegramForbiddenError:
                logger.info(f"User {uid} blocked bot — disabling")
                await self.db.disable_user(uid)
            except TelegramBadRequest as e:
                logger.error(f"Bad request for {uid}: {e}")
            except Exception as e:
                logger.error(f"Failed to send to {uid}: {e}")