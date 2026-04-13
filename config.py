"""
Bot configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8201164468:AAHiZa-596PyZvA2iRjdkQiGI0dTqjTTjXA")

# Bybit API (primary - 3000 req/min FREE)
BYBIT_BASE_URL = "https://api.bybit.com"

# Fear & Greed (alternative.me - free)
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"

# RSS News Feeds (бесплатно, без ключей)
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://cryptonews.com/news/feed/",
    "https://bitcoinist.com/feed/",
    "https://cryptopotato.com/feed/",
    "https://www.newsbtc.com/feed/",
]

# Cache
CACHE_TTL = 30
CACHE_UPDATE_INTERVAL = 25

# DB
DB_PATH = "crypto_bot.db"
DB_POOL_SIZE = 10

# Concurrency
MAX_CONCURRENT_REQUESTS = 15
SCHEDULER_INTERVAL = 60

# Defaults
DEFAULT_LANGUAGE = "ru"
DEFAULT_INTERVAL = 0

BROADCAST_INTERVALS = {
    0:  {"ru": "Отключено",       "en": "Disabled"},
    2:  {"ru": "Каждые 2 часа",   "en": "Every 2 hours"},
    4:  {"ru": "Каждые 4 часа",   "en": "Every 4 hours"},
    6:  {"ru": "Каждые 6 часов",  "en": "Every 6 hours"},
    12: {"ru": "Каждые 12 часов", "en": "Every 12 hours"},
    24: {"ru": "Каждые 24 часа",  "en": "Every 24 hours"},
}

ALL_CATEGORIES = {
    "prices": {
        "ru": "📊 Цены и рынок",
        "en": "📊 Prices & Market",
        "items": {
            "top10":        {"ru": "Топ-10 монет (24ч)",      "en": "Top-10 coins (24h)"},
            "top25":        {"ru": "Топ-25 монет (24ч)",      "en": "Top-25 coins (24h)"},
            "market_cap":   {"ru": "Общая капитализация",     "en": "Total market cap"},
            "volume_24h":   {"ru": "Объём торгов 24ч",        "en": "24h Trading volume"},
            "active_coins": {"ru": "Активных монет",          "en": "Active coins count"},
            "new_ath":      {"ru": "Новые ATH",               "en": "New ATH coins"},
            "near_ath":     {"ru": "Близко к ATH",            "en": "Near ATH coins"},
        },
    },
    "sentiment": {
        "ru": "😱 Настроение",
        "en": "😱 Sentiment",
        "items": {
            "fear_greed": {"ru": "Индекс страха/жадности", "en": "Fear & Greed Index"},
        },
    },
    "movers": {
        "ru": "🚀 Движение цен",
        "en": "🚀 Price Movers",
        "items": {
            "movers_1h_up":    {"ru": "Топ-3 роста за 1ч",    "en": "Top-3 gainers 1h"},
            "movers_1h_down":  {"ru": "Топ-3 падения за 1ч",  "en": "Top-3 losers 1h"},
            "movers_24h_up":   {"ru": "Топ-3 роста за 24ч",   "en": "Top-3 gainers 24h"},
            "movers_24h_down": {"ru": "💥 Топ-3 падения 24ч", "en": "💥 Top-3 losers 24h"},
            "movers_7d_up":    {"ru": "Топ-3 роста за 7д",    "en": "Top-3 gainers 7d"},
            "movers_7d_down":  {"ru": "Топ-3 падения за 7д",  "en": "Top-3 losers 7d"},
            "high_volume":     {"ru": "Высокий объём",         "en": "High volume coins"},
            "anomaly_volume":  {"ru": "Аномальный объём",      "en": "Anomaly volume"},
        },
    },
    "altcoins": {
        "ru": "💎 Альткоины",
        "en": "💎 Altcoins",
        "items": {
            "alt_top":     {"ru": "Топ альткоинов",        "en": "Top altcoins"},
            "alt_gainers": {"ru": "Растущие альткоины",    "en": "Alt gainers"},
            "alt_losers":  {"ru": "Падающие альткоины",    "en": "Alt losers"},
        },
    },
    "macro": {
        "ru": "⭐ Макро данные",
        "en": "⭐ Macro Data",
        "items": {
            "btc_dominance":     {"ru": "Доминирование BTC",      "en": "BTC Dominance"},
            "eth_dominance":     {"ru": "Доминирование ETH",      "en": "ETH Dominance"},
            "total_volume":      {"ru": "Общий объём рынка",      "en": "Total market volume"},
            "defi_volume":       {"ru": "Объём DeFi",             "en": "DeFi Volume"},
            "stablecoin_supply": {"ru": "Эмиссия стейблкоинов",   "en": "Stablecoin Supply"},
            "btc_etf_flow":      {"ru": "Приток/отток BTC ETF",   "en": "BTC ETF Flow"},
            "eth_etf_flow":      {"ru": "Приток/отток ETH ETF",   "en": "ETH ETF Flow"},
            "open_interest":     {"ru": "Открытый интерес",       "en": "Open Interest"},
        },
    },
}

# Проверенный список монет, которые есть на Bybit
POPULAR_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "MATIC", "SHIB",
    "AVAX", "TRX", "LINK", "LTC", "NEAR", "ATOM", "ALGO", "VET", "FIL", "SAND",
    "MANA", "AXS", "EGLD", "THETA", "ONE", "CHZ", "ENJ", "ZEC", "DASH", "XLM",
    "EOS", "KSM", "COMP", "AAVE", "UNI", "CAKE", "SUSHI", "CRV", "SNX", "YFI",
    "MKR", "ZRX", "BAT", "OMG", "QTUM", "NEO", "WAVES", "ICX", "ONT", "CELR",
    "BAND", "KAVA", "STX", "RSR", "OXT", "CVC", "LRC", "DYDX", "ENS", "FXS",
    "LDO", "RPL", "SSV", "PENDLE", "AGIX", "OCEAN", "FET", "RNDR", "GRT", "ARB",
    "OP", "APT", "SUI", "BLUR", "SEI", "TIA", "INJ", "JTO", "PYTH", "JUP",
    "WIF", "BONK", "PEPE", "FLOKI", "NOT", "TON"
]