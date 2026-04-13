"""
Multilanguage text strings for the bot
"""

TEXTS = {
    "welcome": {
        "ru": "👋 <b>Добро пожаловать в Crypto Analyst Bot!</b>\n\nВыберите действие:",
        "en": "👋 <b>Welcome to Crypto Analyst Bot!</b>\n\nChoose an action:",
    },
    "main_menu": {
        "ru": "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        "en": "🏠 <b>Main Menu</b>\n\nChoose an action:",
    },
    "btn_market": {"ru": "📊 Анализ рынка", "en": "📊 Market Analysis"},
    "btn_price": {"ru": "📈 Цена монеты", "en": "📈 Coin Price"},
    "btn_charts": {"ru": "📊 Графики", "en": "📊 Charts"},
    "btn_news": {"ru": "📰 Криптоновости", "en": "📰 Crypto News"},
    "btn_settings": {"ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "btn_language": {"ru": "🌐 Language / Язык", "en": "🌐 Language / Язык"},
    "btn_back": {"ru": "◀️ Назад", "en": "◀️ Back"},
    "btn_main_menu": {"ru": "🏠 Главное меню", "en": "🏠 Main Menu"},

    # News
    "news_header": {
        "ru": "📰 <b>Криптоновости</b>\n\n",
        "en": "📰 <b>Crypto News</b>\n\n",
    },
    "no_news": {
        "ru": "❌ Новости временно недоступны. Попробуйте позже.",
        "en": "❌ News temporarily unavailable. Please try later.",
    },

    # Language
    "choose_language": {
        "ru": "🌐 <b>Выберите язык:</b>",
        "en": "🌐 <b>Choose language:</b>",
    },
    "language_set": {
        "ru": "✅ Язык изменён на <b>Русский</b>",
        "en": "✅ Language changed to <b>English</b>",
    },

    # Market analysis
    "no_data": {
        "ru": "❌ Данные недоступны. Попробуйте позже.",
        "en": "❌ Data unavailable. Please try later.",
    },
    "no_categories": {
        "ru": "⚠️ У вас не выбрано ни одной категории!\nПожалуйста, выберите категории в <b>Настройках</b>.",
        "en": "⚠️ You have no categories selected!\nPlease choose categories in <b>Settings</b>.",
    },
    "error": {
        "ru": "❌ Произошла ошибка. Попробуйте позже.",
        "en": "❌ An error occurred. Please try later.",
    },

    # Price
    "choose_coin": {
        "ru": "📈 <b>Выберите монету:</b>",
        "en": "📈 <b>Choose a coin:</b>",
    },

    # Settings
    "settings_menu": {
        "ru": "⚙️ <b>Настройки</b>\n\nВыберите раздел:",
        "en": "⚙️ <b>Settings</b>\n\nChoose a section:",
    },
    "btn_interval": {"ru": "⏰ Периодичность рассылки", "en": "⏰ Broadcast interval"},
    "btn_categories": {"ru": "📋 Управление категориями", "en": "📋 Manage categories"},
    "choose_interval": {
        "ru": "⏰ <b>Выберите периодичность рассылки:</b>",
        "en": "⏰ <b>Choose broadcast interval:</b>",
    },
    "interval_set": {
        "ru": "✅ Периодичность обновлена",
        "en": "✅ Interval updated",
    },
    "current_interval": {
        "ru": "Текущая: <b>{interval}</b>",
        "en": "Current: <b>{interval}</b>",
    },

    # Categories
    "categories_menu": {
        "ru": "📋 <b>Управление категориями</b>\n\nВыберите группу:",
        "en": "📋 <b>Manage Categories</b>\n\nChoose a group:",
    },
    "btn_select_all": {"ru": "✅ Выбрать все категории", "en": "✅ Select all categories"},
    "btn_clear_all": {"ru": "⬜ Очистить все категории", "en": "⬜ Clear all categories"},
    "btn_select_group": {"ru": "✅ Выбрать все", "en": "✅ Select all"},
    "btn_clear_group": {"ru": "⬜ Очистить все", "en": "⬜ Clear all"},
    "cat_added": {"ru": "✅ Категория добавлена", "en": "✅ Category added"},
    "cat_removed": {"ru": "❌ Категория убрана", "en": "❌ Category removed"},
    "all_selected": {"ru": "✅ Все категории выбраны", "en": "✅ All categories selected"},
    "all_cleared": {"ru": "⬜ Все категории очищены", "en": "⬜ All categories cleared"},
    "group_selected": {"ru": "✅ Группа выбрана", "en": "✅ Group selected"},
    "group_cleared": {"ru": "⬜ Группа очищена", "en": "⬜ Group cleared"},

    # Charts instruction
    "charts_instruction_title": {
        "ru": "📊 <b>Как посмотреть график монеты</b>\n\n",
        "en": "📊 <b>How to view coin chart</b>\n\n"
    },
    "charts_instruction_text": {
        "ru": """
📈 <b>Инструкция:</b>
1️⃣ Нажмите кнопку "🔗 Перейти к боту" внизу
2️⃣ Введите команду: <code>fc НАЗВАНИЕ_МОНЕТЫ ТАЙМФРЕЙМ</code>

<b>📋 Примеры:</b>
• <code>fc BTC 1h</code> — график Bitcoin, 1 час
• <code>fc ETH 4h</code> — график Ethereum, 4 часа
• <code>fc SOL 1d</code> — график Solana, 1 день

<b>⏱ Таймфреймы:</b>
<code>1m</code> <code>5m</code> <code>15m</code> <code>30m</code> <code>1h</code> <code>4h</code> <code>1d</code> <code>1w</code>
""",
        "en": """
📈 <b>Instruction:</b>
1️⃣ Click "🔗 Go to bot" button below
2️⃣ Enter command: <code>fc COIN_NAME TIMEFRAME</code>

<b>📋 Examples:</b>
• <code>fc BTC 1h</code> — Bitcoin chart, 1 hour
• <code>fc ETH 4h</code> — Ethereum chart, 4 hours
• <code>fc SOL 1d</code> — Solana chart, 1 day

<b>⏱ Timeframes:</b>
<code>1m</code> <code>5m</code> <code>15m</code> <code>30m</code> <code>1h</code> <code>4h</code> <code>1d</code> <code>1w</code>
"""
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Get translated string"""
    entry = TEXTS.get(key, {})
    text = entry.get(lang) or entry.get("ru") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text