"""
Market data analyzer — Bybit data → beautiful Telegram messages
"""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_price(p) -> str:
    if p is None: return "N/A"
    try:
        p = float(p)
    except: return "N/A"
    if p >= 10000:  return f"{p:,.0f}"
    if p >= 1000:   return f"{p:,.2f}"
    if p >= 1:      return f"{p:.4f}"
    if p >= 0.01:   return f"{p:.6f}"
    return f"{p:.8f}"

def fmt_num(n) -> str:
    if n is None: return "N/A"
    try: n = float(n)
    except: return "N/A"
    if abs(n) >= 1_000_000_000_000: return f"{n/1_000_000_000_000:.2f}T"
    if abs(n) >= 1_000_000_000:     return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:         return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:             return f"{n/1_000:.1f}K"
    return f"{n:.2f}"

def fmt_pct(p) -> str:
    if p is None: return "N/A"
    try: p = float(p)
    except: return "N/A"
    arrow = "🔺" if p >= 0 else "🔻"
    sign  = "+" if p >= 0 else ""
    return f"{arrow} {sign}{p:.2f}%"

def progress_bar(value: int, width: int = 10) -> str:
    filled = max(0, min(width, int(value / 100 * width)))
    return "█" * filled + "░" * (width - filled)

def fear_greed_label(v: int, lang: str) -> str:
    if v <= 25: return "😱 Экстремальный страх" if lang == "ru" else "😱 Extreme Fear"
    if v <= 46: return "😰 Страх"               if lang == "ru" else "😰 Fear"
    if v <= 54: return "😐 Нейтрально"           if lang == "ru" else "😐 Neutral"
    if v <= 75: return "🤑 Жадность"             if lang == "ru" else "🤑 Greed"
    return         "🚀 Экстр. жадность"          if lang == "ru" else "🚀 Extreme Greed"

DIV  = "─" * 28
DIV2 = "═" * 28


# ── Bybit ticker helpers ───────────────────────────────────────────────────────

def safe_float(val, default=None):
    try: return float(val)
    except: return default

def build_spot_index(spot: list) -> dict:
    idx = {}
    for t in spot:
        s = t.get("symbol", "")
        if s.endswith("USDT") and not s.endswith("PERP"):
            sym = s[:-4]
            idx[sym] = t
    return idx

def build_linear_index(linear: list) -> dict:
    idx = {}
    for t in linear:
        s = t.get("symbol", "")
        if s.endswith("USDT"):
            sym = s[:-4]
            idx[sym] = t
    return idx

def ticker_price(t: dict) -> Optional[float]:
    return safe_float(t.get("lastPrice"))

def ticker_pct24(t: dict) -> Optional[float]:
    return safe_float(t.get("price24hPcnt")) and safe_float(t.get("price24hPcnt")) * 100

def ticker_volume(t: dict) -> Optional[float]:
    return safe_float(t.get("turnover24h"))

def ticker_ath(t: dict) -> Optional[float]:
    return safe_float(t.get("highPrice24h"))


# ── Main analyzer ─────────────────────────────────────────────────────────────

class MarketAnalyzer:
    STABLES = {"USDT","USDC","BUSD","DAI","TUSD","FRAX","USDP","LUSD","GUSD","SUSD","USDD"}
    MAJORS  = {"BTC","ETH"}

    def __init__(self, spot: list, linear: list, fear_greed: dict, open_interest: dict, lang: str = "ru"):
        self.spot   = spot   or []
        self.linear = linear or []
        self.fg     = fear_greed
        self.oi     = open_interest
        self.lang   = lang
        self.L = lang

        self.spot_idx   = build_spot_index(self.spot)
        self.linear_idx = build_linear_index(self.linear)

        self.ranked = sorted(
            [
                (sym, t) for sym, t in self.spot_idx.items()
                if sym not in self.STABLES
                and safe_float(t.get("turnover24h"), 0) > 0
            ],
            key=lambda x: safe_float(x[1].get("turnover24h"), 0),
            reverse=True,
        )
        self.altcoins = [(s, t) for s, t in self.ranked if s not in self.MAJORS and s not in self.STABLES]

    def build_report(self, selected: set) -> str:
        from config import ALL_CATEGORIES
        if not selected:
            return "⚠️ Нет выбранных категорий" if self.L == "ru" else "⚠️ No categories selected"

        now = datetime.now(timezone.utc).strftime("%H:%M %d.%m.%Y")
        header = (
            f"📊 Анализ рынка — {now} UTC\n{DIV2}\n"
            if self.L == "ru" else
            f"📊 Market Analysis — {now} UTC\n{DIV2}\n"
        )
        parts = [header]

        groups = [
            ("prices",    "📊 Цены и рынок"   if self.L=="ru" else "📊 Prices & Market"),
            ("sentiment", "😱 Настроение"     if self.L=="ru" else "😱 Sentiment"),
            ("movers",    "🚀 Движение цен"   if self.L=="ru" else "🚀 Price Movers"),
            ("altcoins",  "💎 Альткоины"      if self.L=="ru" else "💎 Altcoins"),
            ("macro",     "⭐ Макро данные"   if self.L=="ru" else "⭐ Macro Data"),
        ]

        for group_key, group_label in groups:
            group_cats = list(ALL_CATEGORIES[group_key]["items"].keys())
            active = [c for c in group_cats if c in selected]
            if not active:
                continue
            section_parts = []
            for cat in active:
                r = self._render(cat)
                if r:
                    section_parts.append(r)
            if section_parts:
                parts.append(f"\n{group_label}\n{DIV}")
                parts.extend(section_parts)

        text = "\n".join(parts).strip()
        if len(text) > 4000:
            text = text[:3950] + "\n<i>...truncated</i>"
        return text

    def _render(self, cat: str) -> Optional[str]:
        try:
            L = self.L
            r = self.ranked
            if   cat == "top10":        return self._top_n(10)
            elif cat == "top25":        return self._top_n(25)
            elif cat == "market_cap":   return self._market_cap()
            elif cat == "volume_24h":   return self._volume_24h()
            elif cat == "active_coins": return self._active_coins()
            elif cat == "new_ath":      return self._new_ath()
            elif cat == "near_ath":     return self._near_ath()
            elif cat == "fear_greed":   return self._fear_greed()
            elif cat == "movers_1h_up":    return self._movers_by("price1hPcnt",  True,  3, "🔺 Топ роста 1ч"    if L=="ru" else "🔺 Top gainers 1h")
            elif cat == "movers_1h_down":  return self._movers_by("price1hPcnt",  False, 3, "🔻 Топ падения 1ч"  if L=="ru" else "🔻 Top losers 1h")
            elif cat == "movers_24h_up":   return self._movers_by("price24hPcnt", True,  3, "🔺 Топ роста 24ч"   if L=="ru" else "🔺 Top gainers 24h")
            elif cat == "movers_24h_down": return self._movers_by("price24hPcnt", False, 3, "💥 Топ падения 24ч" if L=="ru" else "💥 Top losers 24h")
            elif cat == "movers_7d_up":    return self._movers_7d(True)
            elif cat == "movers_7d_down":  return self._movers_7d(False)
            elif cat == "high_volume":     return self._high_volume()
            elif cat == "anomaly_volume":  return self._anomaly_volume()
            elif cat == "alt_top":         return self._alt_top()
            elif cat == "alt_gainers":     return self._alt_gainers()
            elif cat == "alt_losers":      return self._alt_losers()
            elif cat == "btc_dominance":   return self._btc_dominance()
            elif cat == "eth_dominance":   return self._eth_dominance()
            elif cat == "total_volume":    return self._total_volume()
            elif cat == "defi_volume":     return self._defi_volume()
            elif cat == "stablecoin_supply": return self._stablecoin_supply()
            elif cat == "btc_etf_flow":    return self._etf_note("BTC")
            elif cat == "eth_etf_flow":    return self._etf_note("ETH")
            elif cat == "open_interest":   return self._open_interest()
        except Exception as e:
            logger.error(f"Error rendering {cat}: {e}", exc_info=True)
        return None

    # ── Category renderers (БЕЗ HTML ТЕГОВ) ────────────────────────────────────

    def _top_n(self, n: int) -> str:
        L = self.L
        label = f"📊 Топ-{n} монет по объёму" if L=="ru" else f"📊 Top-{n} by volume"
        lines = [label]
        for i, (sym, t) in enumerate(self.ranked[:n], 1):
            price = fmt_price(t.get("lastPrice"))
            pct   = safe_float(t.get("price24hPcnt"), 0) * 100
            arrow = "🟢" if pct >= 0 else "🔴"
            lines.append(
                f"{arrow} {i:>2}. {sym:<7}  ${price}  {fmt_pct(pct)}"
            )
        return "\n".join(lines)

    def _market_cap(self) -> str:
        L = self.L
        total_vol = sum(safe_float(t.get("turnover24h"), 0) for _, t in self.ranked)
        label = "🏦 Общий объём рынка (24ч)" if L=="ru" else "🏦 Total market volume (24h)"
        return f"{label}\n💵 ${fmt_num(total_vol)}"

    def _volume_24h(self) -> str:
        L = self.L
        total = sum(safe_float(t.get("turnover24h"), 0) for _, t in self.ranked)
        label = "📦 Объём торгов 24ч (Bybit)" if L=="ru" else "📦 24h Trading Volume (Bybit)"
        return f"{label}\n💵 ${fmt_num(total)}"

    def _active_coins(self) -> str:
        L = self.L
        n = len(self.spot_idx)
        label = "🪙 Торгуемых пар (Bybit)" if L=="ru" else "🪙 Tradable pairs (Bybit)"
        return f"{label}\n📈 {n:,}"

    def _new_ath(self) -> str:
        L = self.L
        new_aths = []
        for sym, t in self.ranked:
            lp  = safe_float(t.get("lastPrice"))
            h24 = safe_float(t.get("highPrice24h"))
            if lp and h24 and lp >= h24 * 0.999:
                new_aths.append((sym, t))
        label = "🏆 Новые 24ч максимумы" if L=="ru" else "🏆 New 24h highs"
        if not new_aths:
            return f"{label}\n{'Нет' if L=='ru' else 'None'}"
        lines = [label]
        for sym, t in new_aths[:6]:
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  ⭐ {sym}  ${price}")
        return "\n".join(lines)

    def _near_ath(self) -> str:
        L = self.L
        near = []
        for sym, t in self.ranked:
            lp  = safe_float(t.get("lastPrice"))
            h24 = safe_float(t.get("highPrice24h"))
            if lp and h24 and h24 > 0:
                diff = (h24 - lp) / h24 * 100
                if 0.1 < diff <= 5:
                    near.append((sym, t, diff))
        label = "📍 Близко к 24ч максимуму" if L=="ru" else "📍 Near 24h high"
        if not near:
            return f"{label}\n{'Нет' if L=='ru' else 'None'}"
        lines = [label]
        for sym, t, diff in near[:5]:
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  🎯 {sym}  ${price}  -{diff:.1f}% от пика")
        return "\n".join(lines)

    def _fear_greed(self) -> str:
        L = self.L
        label = "😱 Индекс страха и жадности" if L=="ru" else "😱 Fear & Greed Index"
        if not self.fg:
            return f"{label}\n{'Нет данных' if L=='ru' else 'No data'}"
        try:
            d = self.fg.get("data", [{}])[0]
            v = int(d.get("value", 0))
            lbl = fear_greed_label(v, L)
            bar = progress_bar(v)
            return f"{label}\n{bar}  {v}/100\n{lbl}"
        except Exception as e:
            logger.error(f"Fear greed render: {e}")
            return None

    def _movers_by(self, field: str, top: bool, n: int, label: str) -> str:
        valid = [
            (sym, t) for sym, t in self.ranked
            if safe_float(t.get(field)) is not None
        ]
        sorted_c = sorted(valid, key=lambda x: safe_float(x[1].get(field), 0), reverse=top)[:n]
        lines = [label]
        for sym, t in sorted_c:
            pct   = safe_float(t.get(field), 0) * 100
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  {'🔺' if pct>=0 else '🔻'} {sym}  ${price}  {fmt_pct(pct)}")
        return "\n".join(lines) if len(lines) > 1 else None

    def _movers_7d(self, top: bool) -> str:
        L = self.L
        label = ("🔺 Топ роста 7д (≈24ч)" if top else "🔻 Топ падения 7д (≈24ч)") if L=="ru" else \
                ("🔺 Top gainers 7d (≈24h)" if top else "🔻 Top losers 7d (≈24h)")
        return self._movers_by("price24hPcnt", top, 3, label)

    def _high_volume(self) -> str:
        L = self.L
        label = "📊 Высокий объём (топ-5)" if L=="ru" else "📊 High volume (top-5)"
        lines = [label]
        for sym, t in self.ranked[:5]:
            vol = fmt_num(t.get("turnover24h"))
            lines.append(f"  💰 {sym}  ${vol}")
        return "\n".join(lines)

    def _anomaly_volume(self) -> str:
        L = self.L
        label = "🚨 Аномальный объём" if L=="ru" else "🚨 Anomaly volume"
        anomalies = []
        for sym, t in self.ranked:
            vol   = safe_float(t.get("turnover24h"), 0)
            price = safe_float(t.get("lastPrice"), 0)
            if price > 0 and vol > 500_000_000:
                anomalies.append((sym, t, vol))
        if not anomalies:
            return None
        lines = [label]
        for sym, t, vol in anomalies[:5]:
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  🚨 {sym}  ${price}  vol: ${fmt_num(vol)}")
        return "\n".join(lines)

    def _alt_top(self) -> str:
        L = self.L
        label = "💎 Топ альткоинов (объём)" if L=="ru" else "💎 Top altcoins (volume)"
        lines = [label]
        for sym, t in self.altcoins[:10]:
            price = fmt_price(t.get("lastPrice"))
            pct   = safe_float(t.get("price24hPcnt"), 0) * 100
            arrow = "🟢" if pct >= 0 else "🔴"
            lines.append(f"  {arrow} {sym}  ${price}  {fmt_pct(pct)}")
        return "\n".join(lines)

    def _alt_gainers(self) -> str:
        L = self.L
        label = "🚀 Растущие альты (24ч)" if L=="ru" else "🚀 Alt gainers (24h)"
        sorted_a = sorted(self.altcoins, key=lambda x: safe_float(x[1].get("price24hPcnt"), 0), reverse=True)[:5]
        lines = [label]
        for sym, t in sorted_a:
            pct   = safe_float(t.get("price24hPcnt"), 0) * 100
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  🔺 {sym}  ${price}  {fmt_pct(pct)}")
        return "\n".join(lines)

    def _alt_losers(self) -> str:
        L = self.L
        label = "📉 Падающие альты (24ч)" if L=="ru" else "📉 Alt losers (24h)"
        sorted_a = sorted(self.altcoins, key=lambda x: safe_float(x[1].get("price24hPcnt"), 0))[:5]
        lines = [label]
        for sym, t in sorted_a:
            pct   = safe_float(t.get("price24hPcnt"), 0) * 100
            price = fmt_price(t.get("lastPrice"))
            lines.append(f"  🔻 {sym}  ${price}  {fmt_pct(pct)}")
        return "\n".join(lines)

    def _btc_dominance(self) -> str:
        L = self.L
        label = "₿ Доминирование BTC" if L=="ru" else "₿ BTC Dominance"
        btc = self.spot_idx.get("BTC")
        if not btc:
            return None
        btc_vol   = safe_float(btc.get("turnover24h"), 0)
        total_vol = sum(safe_float(t.get("turnover24h"), 0) for _, t in self.ranked)
        if not total_vol:
            return None
        dom = btc_vol / total_vol * 100
        bar = progress_bar(int(dom))
        return f"{label}\n{bar}  {dom:.1f}%"

    def _eth_dominance(self) -> str:
        L = self.L
        label = "Ξ Доминирование ETH" if L=="ru" else "Ξ ETH Dominance"
        eth = self.spot_idx.get("ETH")
        if not eth:
            return None
        eth_vol   = safe_float(eth.get("turnover24h"), 0)
        total_vol = sum(safe_float(t.get("turnover24h"), 0) for _, t in self.ranked)
        if not total_vol:
            return None
        dom = eth_vol / total_vol * 100
        bar = progress_bar(int(dom))
        return f"{label}\n{bar}  {dom:.1f}%"

    def _total_volume(self) -> str:
        L = self.L
        label = "🌐 Общий объём рынка" if L=="ru" else "🌐 Total Market Volume"
        spot_vol   = sum(safe_float(t.get("turnover24h"), 0) for _, t in self.ranked)
        linear_vol = sum(safe_float(t.get("turnover24h"), 0) for t in self.linear)
        lines = [label]
        lines.append(f"  Spot:    ${fmt_num(spot_vol)}")
        lines.append(f"  Futures: ${fmt_num(linear_vol)}")
        lines.append(f"  Total:   ${fmt_num(spot_vol + linear_vol)}")
        return "\n".join(lines)

    def _defi_volume(self) -> str:
        L = self.L
        label = "🏦 Объём DeFi-токенов" if L=="ru" else "🏦 DeFi Token Volume"
        DEFI = {"UNI","AAVE","CRV","COMP","SUSHI","1INCH","MKR","SNX","YFI","CAKE","GRT","LDO","RPL"}
        vol = sum(safe_float(self.spot_idx[s].get("turnover24h"), 0) for s in DEFI if s in self.spot_idx)
        return f"{label}\n  ${fmt_num(vol)}"

    def _stablecoin_supply(self) -> str:
        L = self.L
        label = "💵 Объём стейблкоинов (24ч)" if L=="ru" else "💵 Stablecoin Volume (24h)"
        STABLES = ["USDT","USDC","BUSD","DAI","TUSD"]
        lines = [label]
        for s in STABLES:
            t = self.spot_idx.get(s)
            if t:
                vol = fmt_num(t.get("turnover24h"))
                lines.append(f"  {s}: ${vol}")
        return "\n".join(lines) if len(lines) > 1 else None

    def _etf_note(self, asset: str) -> str:
        L = self.L
        label = f"📋 {asset} ETF" + (" потоки" if L=="ru" else " Flows")
        note = (
            "⚠️ Данные ETF недоступны через Bybit.\nПроверяйте на farside.co.uk"
            if L=="ru" else
            "⚠️ ETF flow data not available via Bybit.\nCheck farside.co.uk"
        )
        return f"{label}\n{note}"

    def _open_interest(self) -> str:
        L = self.L
        label = "📊 Открытый интерес (BTC)" if L=="ru" else "📊 Open Interest (BTC)"
        if not self.oi:
            btc_lin = self.linear_idx.get("BTC")
            if btc_lin:
                oi_val = safe_float(btc_lin.get("openInterest"))
                price  = safe_float(btc_lin.get("lastPrice"))
                if oi_val and price:
                    oi_usd = oi_val * price
                    return f"{label}\n  ${fmt_num(oi_usd)}"
            return None
        try:
            oi_val = safe_float(self.oi.get("openInterest"))
            btc    = self.linear_idx.get("BTC")
            price  = safe_float(btc.get("lastPrice")) if btc else None
            oi_usd = oi_val * price if (oi_val and price) else None
            lines  = [label]
            if oi_usd:
                lines.append(f"  ${fmt_num(oi_usd)}")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"OI render: {e}")
            return None