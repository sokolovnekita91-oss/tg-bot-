"""
In-memory cache with TTL, preload and background auto-refresh
"""
import asyncio
import logging
import time
from typing import Any, Optional

from config import CACHE_TTL, CACHE_UPDATE_INTERVAL

logger = logging.getLogger(__name__)


class CacheEntry:
    __slots__ = ("value", "expires_at")
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class CacheManager:
    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def get(self, key: str) -> Optional[Any]:
        e = self._store.get(key)
        if e and time.monotonic() < e.expires_at:
            return e.value
        return None

    def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        self._store[key] = CacheEntry(value, ttl)

    def is_fresh(self, key: str) -> bool:
        e = self._store.get(key)
        return bool(e and time.monotonic() < e.expires_at)

    async def get_or_fetch(self, key: str, fetch_fn, ttl: int = CACHE_TTL) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        async with self._lock(key):
            cached = self.get(key)
            if cached is not None:
                return cached
            try:
                value = await fetch_fn()
                if value is not None:
                    self.set(key, value, ttl)
                return value
            except Exception as e:
                logger.error(f"Cache fetch error for {key}: {e}")
                return None

    async def preload(self, api):
        logger.info("Preloading market data from Bybit...")
        try:
            data = await api.fetch_all_data()
            self._store_all(data)
            logger.info("Bybit data preloaded OK")
        except Exception as e:
            logger.error(f"Preload failed: {e}")

    def _store_all(self, data: dict):
        if data.get("spot"):
            self.set("spot", data["spot"], CACHE_TTL)
        if data.get("linear"):
            self.set("linear", data["linear"], CACHE_TTL)
        if data.get("fear_greed"):
            self.set("fear_greed", data["fear_greed"], CACHE_TTL)
        if data.get("open_interest"):
            self.set("open_interest", data["open_interest"], CACHE_TTL)
        self.set("last_update", time.time(), CACHE_TTL * 10)

    async def background_updater(self, api):
        logger.info("Background cache updater started")
        while True:
            await asyncio.sleep(CACHE_UPDATE_INTERVAL)
            try:
                data = await api.fetch_all_data()
                self._store_all(data)
                logger.debug("Cache refreshed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background update failed: {e}")
