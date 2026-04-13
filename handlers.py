"""
Bot handlers
"""
import logging
import aiohttp
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from texts import t
from keyboards import (
    main_menu_kb, language_kb, settings_kb, interval_kb,
    categories_kb, category_group_kb, coins_kb, back_main_kb,
    charts_instruction_kb,
)
from analyzer import MarketAnalyzer, fmt_price, fmt_num, fmt_pct, safe_float, DIV
from config import ALL_CATEGORIES, BROADCAST_INTERVALS, POPULAR_COINS
from database import Database
from cache import CacheManager
from api_client import BybitClient

logger = logging.getLogger(__name__)
router = Router()


async def get_user_lang(user_id: int, db: Database) -> str:
    user = await db.get_user(user_id)
    return user["language"] if user else "ru"


async def get_all_data(cache: CacheManager, api: BybitClient) -> tuple:
    spot = cache.get("spot")
    linear = cache.get("linear")
    fear_greed = cache.get("fear_greed")
    oi = cache.get("open_interest")
    if not spot:
        logger.info("Cache miss — fetching from Bybit")
        data = await api.fetch_all_data()
        spot, linear = data.get("spot"), data.get("linear")
        fear_greed, oi = data.get("fear_greed"), data.get("open_interest")
        if spot:
            cache.set("spot", spot)
        if linear:
            cache.set("linear", linear)
        if fear_greed:
            cache.set("fear_greed", fear_greed)
        if oi:
            cache.set("open_interest", oi)
    return spot, linear, fear_greed, oi


async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif "query is too old" in str(e):
            await callback.message.answer(text, reply_markup=reply_markup)
        else:
            logger.error(f"Edit error: {e}")
    except TelegramRetryAfter as e:
        logger.warning(f"Flood control, waiting {e.retry_after}s")
    except Exception as e:
        logger.error(f"Unexpected edit error: {e}")


async def delete_msg(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, **kw):
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username or "")
    lang = user["language"]
    hint = (
        "\n\n⚠️ <b>Ни одна категория не выбрана.</b>\nПерейдите в ⚙️ Настройки → 📋 Категории."
        if lang == "ru" else
        "\n\n⚠️ <b>No categories selected.</b>\nGo to ⚙️ Settings → 📋 Categories."
    )
    await message.answer(t("welcome", lang) + hint, reply_markup=main_menu_kb(lang))


@router.message(Command("menu"))
async def cmd_menu(message: Message, db: Database, **kw):
    await delete_msg(message)
    lang = await get_user_lang(message.from_user.id, db)
    await message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    await delete_msg(callback.message)
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "menu:remove_and_show")
async def cb_remove_and_show(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "menu:charts_instruction")
async def cb_charts_instruction(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    text = t("charts_instruction_title", lang) + t("charts_instruction_text", lang)
    await safe_edit_message(callback, text, charts_instruction_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "menu:news")
async def cb_news(callback: CallbackQuery, db: Database, api: BybitClient, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    try:
        await callback.answer("⏳ Загружаю новости..." if lang == "ru" else "⏳ Loading news...")
    except:
        pass
    
    try:
        news = await api.get_crypto_news(limit=5)
        if not news:
            await callback.message.answer(t("no_news", lang), reply_markup=back_main_kb(lang))
            await delete_msg(callback.message)
            return
        text = t("news_header", lang)
        for item in news:
            title = item.get("title", "Без заголовка")
            url = item.get("url", "")
            time_str = item.get("time", "Недавно")
            source = item.get("source", "Crypto News")
            text += f"📌 <b>{title}</b>\n📰 {source} | 🕐 {time_str}\n🔗 <a href='{url}'>Читать</a>\n\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        news_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:news_remove")]
        ])
        await callback.message.answer(text, reply_markup=news_kb, disable_web_page_preview=True)
        await delete_msg(callback.message)
    except Exception as e:
        logger.error(f"News error: {e}")
        await callback.message.answer(t("error", lang), reply_markup=back_main_kb(lang))
        await delete_msg(callback.message)


@router.callback_query(F.data == "menu:news_remove")
async def cb_news_remove(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "menu:market")
async def cb_market(callback: CallbackQuery, db: Database, cache: CacheManager, api: BybitClient, **kw):
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user["language"]
    selected = await db.get_user_categories(callback.from_user.id)
    if not selected:
        try:
            await callback.answer(
                "⚠️ Нет категорий! Настройки → Категории" if lang == "ru"
                else "⚠️ No categories! Settings → Categories",
                show_alert=True,
            )
        except:
            pass
        return
    
    try:
        await callback.answer("⏳ Загружаю..." if lang == "ru" else "⏳ Loading...")
    except:
        pass
    
    try:
        spot, linear, fg, oi = await get_all_data(cache, api)
        if not spot:
            await callback.message.answer(t("no_data", lang), reply_markup=back_main_kb(lang))
            await delete_msg(callback.message)
            return
        analyzer = MarketAnalyzer(spot, linear, fg, oi, lang)
        report = analyzer.build_report(selected)
        await callback.message.answer(report, reply_markup=back_main_kb(lang))
        await delete_msg(callback.message)
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        await callback.message.answer(t("error", lang), reply_markup=back_main_kb(lang))
        await delete_msg(callback.message)


@router.callback_query(F.data == "menu:price")
async def cb_price_menu(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    await safe_edit_message(callback, t("choose_coin", lang), coins_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("coin:"))
async def cb_coin_price(callback: CallbackQuery, db: Database, cache: CacheManager, api: BybitClient, **kw):
    symbol = callback.data.split(":", 1)[1]
    bybit_sym = f"{symbol}USDT"
    lang = await get_user_lang(callback.from_user.id, db)
    
    try:
        spot = cache.get("spot")
        ticker = None
        
        if spot:
            for item in spot:
                if item.get("symbol") == bybit_sym:
                    ticker = item
                    break
        
        if not ticker:
            ticker = await api.get_ticker(bybit_sym)
        
        if not ticker or not ticker.get("lastPrice"):
            await safe_edit_message(
                callback,
                f"❌ Данные для {symbol} временно недоступны.\n\nПопробуйте другую монету.",
                back_main_kb(lang)
            )
            return
        
        price = fmt_price(ticker.get("lastPrice"))
        pct24 = safe_float(ticker.get("price24hPcnt"), 0) * 100
        vol_usd = fmt_num(ticker.get("turnover24h"))
        high24 = fmt_price(ticker.get("highPrice24h"))
        low24 = fmt_price(ticker.get("lowPrice24h"))
        arrow = "🟢" if pct24 >= 0 else "🔴"
        
        text = (
            f"💰 <b>{symbol} / USDT</b>  {arrow}\n"
            f"{DIV}\n"
            f"💵 {'Цена' if lang=='ru' else 'Price'}:      <code>${price}</code>\n"
            f"📊 {'Изм. 24ч' if lang=='ru' else '24h Change'}: <b>{fmt_pct(pct24)}</b>\n"
            f"📦 {'Объём 24ч' if lang=='ru' else '24h Volume'}: <code>${vol_usd}</code>\n"
            f"🔺 {'Макс. 24ч' if lang=='ru' else '24h High'}:  <code>${high24}</code>\n"
            f"🔻 {'Мин. 24ч' if lang=='ru' else '24h Low'}:   <code>${low24}</code>\n"
            f"{DIV}\n"
            f"<i>Bybit Spot</i>\n\n"
            f"📊 Для графика нажмите кнопку 'График монеты' ниже"
        )
        
        await safe_edit_message(callback, text, back_main_kb(lang))
        
    except Exception as e:
        logger.error(f"Coin price error {symbol}: {e}")
        await safe_edit_message(callback, t("error", lang), back_main_kb(lang))
    
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    await safe_edit_message(callback, t("settings_menu", lang), settings_kb(lang))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data == "settings:interval")
async def cb_interval_menu(callback: CallbackQuery, db: Database, **kw):
    user = await db.get_or_create_user(callback.from_user.id)
    lang, cur = user["language"], user["interval"]
    cur_label = BROADCAST_INTERVALS.get(cur, BROADCAST_INTERVALS[0])[lang]
    await safe_edit_message(
        callback,
        t("choose_interval", lang) + "\n" + t("current_interval", lang, interval=cur_label),
        interval_kb(lang, cur),
    )
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("interval:"))
async def cb_set_interval(callback: CallbackQuery, db: Database, **kw):
    hours = int(callback.data.split(":")[1])
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user["language"]
    await db.set_interval(callback.from_user.id, hours)
    try:
        await callback.answer(t("interval_set", lang))
    except:
        pass
    await safe_edit_message(callback, t("settings_menu", lang), settings_kb(lang))


@router.callback_query(F.data == "settings:categories")
async def cb_categories(callback: CallbackQuery, db: Database, **kw):
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user["language"]
    selected = await db.get_user_categories(callback.from_user.id)
    await safe_edit_message(callback, t("categories_menu", lang), categories_kb(lang, selected))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("catgroup:"))
async def cb_cat_group(callback: CallbackQuery, db: Database, **kw):
    group_key = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user["language"]
    selected = await db.get_user_categories(callback.from_user.id)
    group = ALL_CATEGORIES.get(group_key)
    if not group:
        try:
            await callback.answer()
        except:
            pass
        return
    await safe_edit_message(callback, group[lang], category_group_kb(lang, group_key, selected))
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("cattoggle:"))
async def cb_toggle_cat(callback: CallbackQuery, db: Database, **kw):
    _, group_key, cat_key = callback.data.split(":")
    lang = await get_user_lang(callback.from_user.id, db)
    new_state = await db.toggle_category(callback.from_user.id, cat_key)
    try:
        await callback.answer(t("cat_added", lang) if new_state else t("cat_removed", lang))
    except:
        pass
    selected = await db.get_user_categories(callback.from_user.id)
    await safe_edit_message(callback, ALL_CATEGORIES[group_key][lang], category_group_kb(lang, group_key, selected))


@router.callback_query(F.data.startswith("catgroup_all:"))
async def cb_group_all(callback: CallbackQuery, db: Database, **kw):
    _, group_key, en_str = callback.data.split(":")
    enabled = bool(int(en_str))
    lang = await get_user_lang(callback.from_user.id, db)
    await db.set_group_categories(callback.from_user.id, group_key, enabled)
    try:
        await callback.answer(t("group_selected", lang) if enabled else t("group_cleared", lang))
    except:
        pass
    selected = await db.get_user_categories(callback.from_user.id)
    await safe_edit_message(callback, ALL_CATEGORIES[group_key][lang], category_group_kb(lang, group_key, selected))


@router.callback_query(F.data.startswith("cat:all:"))
async def cb_all_cats(callback: CallbackQuery, db: Database, **kw):
    enabled = bool(int(callback.data.split(":")[2]))
    lang = await get_user_lang(callback.from_user.id, db)
    await db.set_all_categories(callback.from_user.id, enabled)
    try:
        await callback.answer(t("all_selected", lang) if enabled else t("all_cleared", lang))
    except:
        pass
    selected = await db.get_user_categories(callback.from_user.id)
    await safe_edit_message(callback, t("categories_menu", lang), categories_kb(lang, selected))


@router.callback_query(F.data == "menu:main_from_settings")
async def cb_main_from_settings(callback: CallbackQuery, db: Database, **kw):
    lang = await get_user_lang(callback.from_user.id, db)
    await delete_msg(callback.message)
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    try:
        await callback.answer()
    except:
        pass


# ── LANGUAGE SWITCH HANDLERS ───────────────────────────────────────────────────

@router.callback_query(F.data == "menu:language")
async def cb_language_menu(callback: CallbackQuery, db: Database, **kw):
    user = await db.get_or_create_user(callback.from_user.id)
    lang = user["language"]
    
    await safe_edit_message(
        callback,
        t("choose_language", lang),
        reply_markup=language_kb(lang)
    )
    try:
        await callback.answer()
    except:
        pass


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_lang(callback: CallbackQuery, db: Database, **kw):
    new_lang = callback.data.split(":")[1]
    
    # Сохраняем язык в БД
    await db.set_language(callback.from_user.id, new_lang)
    
    # Отвечаем на callback
    try:
        await callback.answer(t("language_set", new_lang))
    except:
        pass
    
    # Отправляем НОВОЕ сообщение с главным меню на новом языке
    await callback.message.answer(
        t("main_menu", new_lang),
        reply_markup=main_menu_kb(new_lang)
    )
    
    # Удаляем старое сообщение (где была кнопка выбора языка)
    try:
        await callback.message.delete()
    except:
        pass


@router.message()
async def fallback(message: Message, db: Database, **kw):
    await delete_msg(message)
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username or "")
    await message.answer(t("main_menu", user["language"]), reply_markup=main_menu_kb(user["language"]))