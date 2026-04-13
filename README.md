# 🚀 Crypto Analyst Telegram Bot

High-performance async crypto analysis bot built with **aiogram 3.x**, **aiosqlite**, **aiohttp**, and **asyncio**.

---

## ⚡ Performance Features

| Feature | Details |
|---|---|
| **Async everywhere** | aiogram 3.x, aiosqlite, aiohttp — zero blocking I/O |
| **DB connection pool** | 10 persistent SQLite connections via `asyncio.Queue` |
| **WAL mode + indexes** | Fast reads even under concurrent load |
| **API semaphore** | Max 10 concurrent CoinGecko requests — no rate-limit floods |
| **Smart cache** | 30s TTL, preloaded at startup, background refresh every 25s |
| **Cache stampede prevention** | Per-key asyncio locks (double-check locking pattern) |
| **Concurrent broadcasts** | `asyncio.gather()` + semaphore for 30+ simultaneous users |
| **Retry logic** | Auto-retry on 429 (Retry-After header), 503, timeouts |

---

## 🛠 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN
```

Or edit `config.py` directly:
```python
BOT_TOKEN = "YOUR_TOKEN_HERE"
```

### 3. Run
```bash
python bot.py
```

---

## 📋 Bot Commands

| Command | Action |
|---|---|
| `/start` | Start bot, show main menu |
| `/menu` | Show main menu |

---

## 🗂 Project Structure

```
crypto_bot/
├── bot.py          # Entry point, startup, polling
├── config.py       # All settings, coin lists, categories
├── database.py     # Async SQLite with connection pool
├── api_client.py   # CoinGecko API client with semaphore
├── cache.py        # TTL cache with background refresh
├── analyzer.py     # Market data formatter/analyzer
├── keyboards.py    # All inline keyboard builders
├── handlers.py     # All message & callback handlers
├── scheduler.py    # Background broadcast scheduler
├── texts.py        # Multilanguage strings (RU/EN)
└── requirements.txt
```

---

## 📊 Category Groups

| Group | Categories |
|---|---|
| 📊 Prices & Market | Top 10/25/50/100, Market cap, 24h volume, Active coins, New ATH, Near ATH |
| 😱 Sentiment | Fear & Greed Index |
| 🚀 Price Movers | Top gainers/losers 1h/24h/7d, High volume, Anomaly volume |
| 💎 Altcoins | Top altcoins, Alt gainers, Alt losers |

---

## 🌐 APIs Used

- **CoinGecko** — Market data, prices, coins (free tier supported)
- **Alternative.me** — Fear & Greed Index

---

## 🔧 Configuration

Edit `config.py` to change:
- `CACHE_TTL` — Cache lifetime (default 30s)
- `CACHE_UPDATE_INTERVAL` — Background refresh interval (default 25s)
- `DB_POOL_SIZE` — SQLite connection pool size (default 10)
- `MAX_CONCURRENT_REQUESTS` — API semaphore limit (default 10)
- `SCHEDULER_INTERVAL` — How often scheduler runs in seconds (default 60)
- `COINGECKO_API_KEY` — Optional Pro API key for higher rate limits

---

## 📦 CoinGecko Rate Limits

Free tier: ~30 calls/min. The bot is optimized to use **1 API call per cache miss** (fetches global + markets + fear_greed in parallel). With 30s caching, this means at most ~2 calls/min under normal load.

For heavy usage, get a free CoinGecko API key at https://www.coingecko.com/en/api and set `COINGECKO_API_KEY` in your `.env`.
