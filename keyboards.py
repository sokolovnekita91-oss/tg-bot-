"""Keyboard builders"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from texts import t
from config import ALL_CATEGORIES, BROADCAST_INTERVALS, POPULAR_COINS


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Главное меню - без кнопки графиков"""
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=t("btn_market", lang), callback_data="menu:market"),
        InlineKeyboardButton(text=t("btn_price", lang), callback_data="menu:price"),
    )
    b.row(
        InlineKeyboardButton(text=t("btn_news", lang), callback_data="menu:news"),
        InlineKeyboardButton(text=t("btn_settings", lang), callback_data="menu:settings"),
    )
    b.row(
        InlineKeyboardButton(text=t("btn_language", lang), callback_data="menu:language"),
    )
    return b.as_markup()


def language_kb(current: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=("✅ " if current=="ru" else "") + "🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text=("✅ " if current=="en" else "") + "🇬🇧 English", callback_data="lang:en"),
    )
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"))
    return b.as_markup()


def settings_kb(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t("btn_interval", lang), callback_data="settings:interval"))
    b.row(InlineKeyboardButton(text=t("btn_categories", lang), callback_data="settings:categories"))
    b.row(InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main_from_settings"))
    return b.as_markup()


def interval_kb(lang: str, current: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора интервала рассылки"""
    b = InlineKeyboardBuilder()
    btns = []
    for h, labels in BROADCAST_INTERVALS.items():
        mark = "✅ " if h == current else ""
        btns.append(InlineKeyboardButton(text=mark + labels[lang], callback_data=f"interval:{h}"))
    for i in range(0, len(btns), 3):
        b.row(*btns[i:i+3])
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu:settings"))
    return b.as_markup()


def categories_kb(lang: str, selected: set) -> InlineKeyboardMarkup:
    """Клавиатура выбора групп категорий"""
    b = InlineKeyboardBuilder()
    for gk, gd in ALL_CATEGORIES.items():
        cats = list(gd["items"].keys())
        sel_n = sum(1 for c in cats if c in selected)
        b.row(InlineKeyboardButton(
            text=gd[lang] + f" ({sel_n}/{len(cats)})",
            callback_data=f"catgroup:{gk}",
        ))
    total = len(selected)
    total_all = sum(len(g["items"]) for g in ALL_CATEGORIES.values())
    b.row(
        InlineKeyboardButton(text=t("btn_select_all", lang) + f" ({total_all})", callback_data="cat:all:1"),
        InlineKeyboardButton(text=t("btn_clear_all", lang), callback_data="cat:all:0"),
    )
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu:settings"))
    return b.as_markup()


def category_group_kb(lang: str, group_key: str, selected: set) -> InlineKeyboardMarkup:
    """Клавиатура категорий внутри группы"""
    b = InlineKeyboardBuilder()
    group = ALL_CATEGORIES[group_key]
    for ck, cd in group["items"].items():
        on = ck in selected
        b.row(InlineKeyboardButton(
            text=("✅ " if on else "⬜ ") + cd[lang],
            callback_data=f"cattoggle:{group_key}:{ck}",
        ))
    b.row(
        InlineKeyboardButton(text=t("btn_select_group", lang), callback_data=f"catgroup_all:{group_key}:1"),
        InlineKeyboardButton(text=t("btn_clear_group", lang), callback_data=f"catgroup_all:{group_key}:0"),
    )
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="settings:categories"))
    return b.as_markup()


def coins_kb(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора монеты + кнопка графика"""
    b = InlineKeyboardBuilder()
    
    # Кнопки с монетами
    btns = [InlineKeyboardButton(text=sym, callback_data=f"coin:{sym}") for sym in POPULAR_COINS]
    for i in range(0, len(btns), 5):
        b.row(*btns[i:i+5])
    
    # Кнопка графика (ТОЛЬКО ЗДЕСЬ!)
    b.row(InlineKeyboardButton(text="📊 График монеты", callback_data="menu:charts_instruction"))
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu:main"))
    
    return b.as_markup()


def back_main_kb(lang: str) -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:remove_and_show"))
    return b.as_markup()


def charts_instruction_kb(lang: str, bot_username: str = "TreeCapitalBot") -> InlineKeyboardMarkup:
    """Клавиатура для инструкции по графикам с кнопкой перехода"""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔗 Перейти к боту", url=f"https://t.me/{bot_username}"))
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu:price"))
    b.row(InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"))
    return b.as_markup()