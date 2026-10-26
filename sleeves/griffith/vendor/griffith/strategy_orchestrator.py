"""Coordinates the three immutable scanner families over common evidence."""

from __future__ import annotations

from statistics import median
from typing import Any

from strategy_system import LeadersRest, LocationFirst, Parallax, ema_series, return_n, valid_bars, wilder_atr


SECTOR_GROUPS = {
    "XLK": "AAPL ADBE AMD AVGO CDNS CRM CRWD CSCO DDOG IBM INTC INTU LRCX MDB MSFT MU NOW NVDA ORCL PANW PLTR QCOM SMCI SNOW TEAM TXN ZS",
    "XLF": "AXP BAC BLK CME GS HOOD JPM MA MS PYPL SQ V WFC",
    "XLE": "CVX XOM",
    "XLY": "ABNB AMZN BKNG CCL DKNG ETSY F GM HD LOW LULU MCD NKE RIVN SBUX TGT TSLA UBER",
    "XLP": "CL COST KO MDLZ PG WBA WMT",
    "XLV": "ABBV AMGN BIIB BMY CVS GILD ISRG JNJ LLY MRK MRNA PFE TMO UNH VRTX",
    "XLI": "BA CAT DAL DE FDX GE HON MMM UPS",
    "XLU": "CEG DUK",
    "XLC": "CHTR CMCSA DIS GOOG GOOGL META NFLX RBLX ROKU SNAP SPOT T VZ",
    "XLB": "FCX LIN",
}
SECTOR_FOR = {symbol: proxy for proxy, symbols in SECTOR_GROUPS.items() for symbol in symbols.split()}
PROXIES = ["SPY", "QQQ", "IWM", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]


def ratio_series(left_raw: list[dict[str, Any]], right_raw: list[dict[str, Any]]) -> list[float]:
    left = {bar["t"]: float(bar["c"]) for bar in valid_bars(left_raw)}
    right = {bar["t"]: float(bar["c"]) for bar in valid_bars(right_raw)}
    keys = sorted(set(left) & set(right))
    return [left[key] / right[key] for key in keys if right[key] > 0]


def field_sleeve(proxy_raw: list[dict[str, Any]], spy_raw: list[dict[str, Any]], all_long_returns: list[float]) -> str:
    ratios = ratio_series(proxy_raw, spy_raw)
    proxy = valid_bars(proxy_raw)
    if len(ratios) < 127 or len(proxy) < 70:
        return "UNAVAILABLE"
    rs10, rs20, rs126 = return_n(ratios, 10), return_n(ratios, 20), return_n(ratios, 126)
    e50 = ema_series([float(bar["c"]) for bar in proxy], 50)
    slope = 100 * (float(e50[-1]) / float(e50[-21]) - 1)
    percentile = sum(value <= float(rs126) for value in all_long_returns) / max(1, len(all_long_returns))
    relative_low = ratios[-1] <= min(ratios[-20:])
    price, ema50 = float(proxy[-1]["c"]), float(e50[-1])
    if relative_low and float(rs20) < 0 and slope < 0: return "WATERFALL"
    if percentile <= 0.45 and float(rs20) > 0 and float(rs10) >= -0.25 and slope >= -0.5: return "TURN"
    if percentile <= 0.40 and float(rs20) <= 0: return "TROUGH"
    if float(rs20) > 0 and float(rs126) > 0 and float(rs10) >= -0.5 and price >= ema50: return "TREND"
    if float(rs20) <= 0 and slope < 0: return "TROUGH"
    return "TURN"


def parallax_regime(histories: dict[str, list[dict[str, Any]]]) -> tuple[str, dict[int, float]]:
    contexts = []
    for raw in histories.values():
        bars = valid_bars(raw)
        if len(bars) < 61: continue
        closes = [float(bar["c"]) for bar in bars]
        atr_value = wilder_atr(bars)
        contexts.append({"daily": 100 * (closes[-1] / closes[-2] - 1), "r5": return_n(closes, 5), "r20": return_n(closes, 20), "r60": return_n(closes, 60), "atr": 100 * float(atr_value) / closes[-1]})
    benchmarks = {period: median([float(item[f"r{period}"]) for item in contexts]) if contexts else 0 for period in (5, 20, 60)}
    if len(contexts) < 3: return "UNCERTAIN", benchmarks
    b = median([item["daily"] for item in contexts])
    p20 = sum(item["r20"] > 0 for item in contexts) / len(contexts)
    a = median([item["atr"] for item in contexts])
    values = [item["r20"] for item in contexts]
    d = max(values) - min(values)
    if b <= -1.5 and p20 < .30 and a >= 5: regime = "PANIC"
    elif b > 1.2 and p20 < .45 and a >= 4: regime = "REFLEXIVE_REBOUND"
    elif a >= 7 or d >= 14: regime = "HIGH_VOLATILITY_DELEVERAGING"
    elif b > 0 and p20 >= .60 and a < 5: regime = "ORDERLY_RISK_ON"
    elif b > 0 and p20 < .60: regime = "NARROW_RISK_ON"
    else: regime = "RANGE_BOUND"
    return regime, benchmarks


class ThreeStrategyOrchestrator:
    def __init__(self) -> None:
        self.parallax, self.leaders, self.location = Parallax(), LeadersRest(), LocationFirst()

    def evaluate(
        self,
        universe: list[str],
        daily: dict[str, list[dict[str, Any]]],
        intraday15: dict[str, list[dict[str, Any]]],
        prices: dict[str, float],
        *,
        location_symbols: set[str] | None = None,
    ) -> list[Any]:
        spy = daily.get("SPY", [])
        regime, benchmarks = parallax_regime({symbol: daily.get(symbol, []) for symbol in universe})
        long_returns = [float(value) for proxy in PROXIES if proxy != "SPY" for value in [return_n(ratio_series(daily.get(proxy, []), spy), 126)] if value is not None]
        sleeves = {proxy: field_sleeve(daily.get(proxy, []), spy, long_returns) for proxy in PROXIES if proxy != "SPY"}
        decisions = []
        etfs = set(PROXIES)
        for symbol in universe:
            raw = daily.get(symbol, [])
            proxy = SECTOR_FOR.get(symbol, "SPY")
            sleeve = "TURN" if proxy == "SPY" else sleeves.get(proxy, "UNAVAILABLE")
            decisions.append(self.parallax.evaluate(symbol, raw, benchmark_returns=benchmarks, field_sleeve=sleeve, regime=regime, corrected=False))
            decisions.append(self.parallax.evaluate(symbol, raw, benchmark_returns=benchmarks, field_sleeve=sleeve, regime=regime, corrected=True))
            decisions.append(self.leaders.evaluate(symbol, raw, spy, corrected=False, is_etf=symbol in etfs))
            decisions.append(self.leaders.evaluate(symbol, raw, spy, corrected=True, is_etf=symbol in etfs))
            # Location-First/Deep-Reset is only meaningful when the caller has
            # actually captured 15-minute evidence for this symbol.  Omitting
            # the lane avoids manufacturing an all-universe UNAVAILABLE row;
            # Parallax and LeadersRest remain full-universe scans.
            if location_symbols is None or symbol in location_symbols:
                decisions.append(self.location.evaluate(symbol, raw, intraday15.get(symbol, []), prices.get(symbol, 0), corrected=False))
                decisions.append(self.location.evaluate(symbol, raw, intraday15.get(symbol, []), prices.get(symbol, 0), corrected=True))
        return decisions
