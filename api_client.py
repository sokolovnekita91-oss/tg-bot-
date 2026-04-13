"""
Bybit API client + RSS News — primary data source
"""
import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Optional
import aiohttp
import feedparser

from config import BYBIT_BASE_URL, FEAR_GREED_URL, MAX_CONCURRENT_REQUESTS, RSS_FEEDS

logger = logging.getLogger(__name__)


class BybitClient:
    def __init__(self):
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            timeout = aiohttp.ClientTimeout(total=15, connect=8)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
            logger.info("Created new aiohttp session")
        return self._session

    async def _get(self, path: str, params: dict = None, retries: int = 3) -> Optional[dict]:
        url = f"{BYBIT_BASE_URL}{path}"
        async with self._semaphore:
            for attempt in range(retries):
                try:
                    session = await self._get_session()
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            if data.get("retCode") == 0:
                                return data.get("result", {})
                            else:
                                logger.error(f"Bybit error: {data.get('retMsg')} for {path}")
                                return None
                        elif resp.status == 429:
                            logger.warning(f"Bybit rate limit, waiting 5s...")
                            await asyncio.sleep(5)
                        else:
                            logger.error(f"Bybit HTTP {resp.status} for {path}")
                            await asyncio.sleep(2 ** attempt)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on {path}, attempt {attempt+1}/{retries}")
                    await asyncio.sleep(2)
                except aiohttp.ClientError as e:
                    logger.error(f"Client error {path}: {e}")
                    if self._session and not self._session.closed:
                        await self._session.close()
                    self._session = None
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Unexpected error {path}: {e}", exc_info=True)
                    await asyncio.sleep(2)
        return None

    async def get_tickers(self, category: str = "spot") -> Optional[list]:
        result = await self._get("/v5/market/tickers", {"category": category})
        if result:
            return result.get("list", [])
        return None

    async def get_ticker(self, symbol: str) -> Optional[dict]:
        result = await self._get("/v5/market/tickers", {"category": "spot", "symbol": symbol})
        if result:
            lst = result.get("list", [])
            return lst[0] if lst else None
        return None

    async def get_ticker_binance(self, symbol: str) -> Optional[dict]:
        """Binance резервный источник"""
        try:
            session = await self._get_session()
            async with session.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "lastPrice": data.get("lastPrice"),
                        "price24hPcnt": float(data.get("priceChangePercent", 0)) / 100,
                        "turnover24h": float(data.get("quoteVolume", 0)),
                        "highPrice24h": data.get("highPrice"),
                        "lowPrice24h": data.get("lowPrice"),
                        "symbol": symbol
                    }
                return None
        except Exception as e:
            logger.error(f"Binance error for {symbol}: {e}")
            return None

    async def get_open_interest(self, symbol: str = "BTCUSDT", interval: str = "1d") -> Optional[dict]:
        result = await self._get("/v5/market/open-interest", {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": interval,
            "limit": 1,
        })
        if result:
            lst = result.get("list", [])
            return lst[0] if lst else None
        return None

    async def get_fear_greed(self) -> Optional[dict]:
        try:
            session = await self._get_session()
            async with session.get(FEAR_GREED_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                logger.error(f"Fear & Greed status: {resp.status}")
        except Exception as e:
            logger.error(f"Fear & Greed error: {e}")
        return None

    async def get_crypto_news(self, limit: int = 5) -> Optional[list]:
        news_list = []
        for feed_url in RSS_FEEDS:
            try:
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                for entry in feed.entries[:3]:
                    source = feed_url.split("//")[1].split("/")[0] if "//" in feed_url else "Crypto News"
                    source = source.replace("www.", "").replace(".com", "").replace(".ru", "")
                    time_str = "Недавно"
                    published = entry.get("published", "")
                    if published:
                        try:
                            from email.utils import parsedate_to_datetime
                            dt = parsedate_to_datetime(published)
                            time_str = dt.strftime("%H:%M %d.%m")
                        except:
                            pass
                    title = entry.get("title", "Без заголовка")
                    title = title.replace("\n", " ").strip()
                    if len(title) > 100:
                        title = title[:97] + "..."
                    news_list.append({
                        "title": title,
                        "url": entry.get("link", ""),
                        "time": time_str,
                        "source": source.capitalize()
                    })
            except Exception as e:
                logger.error(f"RSS parse error for {feed_url}: {e}")
                continue
        
        seen_urls = set()
        unique_news = []
        for item in news_list:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                unique_news.append(item)
        
        random.shuffle(unique_news)
        logger.info(f"Got {len(unique_news)} unique news articles")
        return unique_news[:limit]

    async def fetch_all_data(self) -> dict:
        logger.info("Fetching all Bybit data concurrently...")
        results = await asyncio.gather(
            self.get_tickers("spot"),
            self.get_tickers("linear"),
            self.get_fear_greed(),
            self.get_open_interest("BTCUSDT"),
            return_exceptions=True,
        )
        spot     = results[0] if not isinstance(results[0], Exception) else None
        linear   = results[1] if not isinstance(results[1], Exception) else None
        fg       = results[2] if not isinstance(results[2], Exception) else None
        oi       = results[3] if not isinstance(results[3], Exception) else None

        logger.info(
            f"fetch_all done: spot={'OK '+str(len(spot)) if spot else 'FAIL'}, "
            f"linear={'OK '+str(len(linear)) if linear else 'FAIL'}, "
            f"fg={'OK' if fg else 'FAIL'}, oi={'OK' if oi else 'FAIL'}"
        )
        return {
            "spot": spot,
            "linear": linear,
            "fear_greed": fg,
            "open_interest": oi,
            "timestamp": time.time(),
        }

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Session closed")