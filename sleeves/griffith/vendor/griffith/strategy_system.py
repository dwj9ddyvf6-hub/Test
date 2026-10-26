"""Versioned implementation of the Three-Strategy Desk specification.

This module is independent of canonical Tensor. It evaluates immutable market
snapshots and emits versioned decisions; broker execution lives downstream.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def valid_bars(raw: list[dict[str, Any]]) -> list[dict[str, float | str]]:
    result = []
    for item in raw:
        try:
            o, h, l, c, v = (float(item[key]) for key in ("o", "h", "l", "c", "v"))
            if o <= 0 or h <= 0 or l <= 0 or c <= 0 or v < 0 or h < max(o, c) or l > min(o, c):
                continue
            result.append({"t": str(item["t"]), "o": o, "h": h, "l": l, "c": c, "v": v})
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(result, key=lambda bar: str(bar["t"]))


def sma(values: list[float], period: int) -> float | None:
    return sum(values[-period:]) / period if len(values) >= period else None


def ema_series(values: list[float], period: int, first_close_seed: bool = False) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if not values:
        return output
    k = 2 / (period + 1)
    if first_close_seed:
        output[0] = values[0]
        start = 1
    elif len(values) >= period:
        output[period - 1] = sum(values[:period]) / period
        start = period
    else:
        return output
    for index in range(start, len(values)):
        output[index] = k * values[index] + (1 - k) * float(output[index - 1])
    return output


def wilder_atr(bars: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(bars) <= period:
        return None
    tr = []
    for index in range(1, len(bars)):
        current, previous = bars[index], bars[index - 1]
        tr.append(max(float(current["h"]) - float(current["l"]), abs(float(current["h"]) - float(previous["c"])), abs(float(current["l"]) - float(previous["c"]))))
    value = sum(tr[:period]) / period
    for current in tr[period:]:
        value = ((period - 1) * value + current) / period
    return value


def wilder_rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    gain = sum(max(change, 0) for change in changes[:period]) / period
    loss = sum(max(-change, 0) for change in changes[:period]) / period
    for change in changes[period:]:
        gain = ((period - 1) * gain + max(change, 0)) / period
        loss = ((period - 1) * loss + max(-change, 0)) / period
    return 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)


def macd(values: list[float]) -> tuple[float | None, float | None, list[float | None]]:
    fast, slow = ema_series(values, 12), ema_series(values, 26)
    line = [float(a) - float(b) if a is not None and b is not None else None for a, b in zip(fast, slow)]
    available = [value for value in line if value is not None]
    signal_available = ema_series(available, 9)
    signal: list[float | None] = [None] * (len(line) - len(available)) + signal_available
    histogram = [float(a) - float(b) if a is not None and b is not None else None for a, b in zip(line, signal)]
    return line[-1], signal[-1], histogram


def return_n(values: list[float], sessions: int) -> float | None:
    return 100 * (values[-1] / values[-1 - sessions] - 1) if len(values) > sessions else None


def content_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class StrategyDecision:
    decisionId: str
    strategyId: str
    scannerVersion: str
    symbol: str
    asOf: str
    evidenceHash: str
    status: str
    score: float | None
    engine: str | None = None
    setupClass: str | None = None
    entryReference: float | None = None
    invalidationReference: float | None = None
    horizonSessions: int = 0
    reasonCodes: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


def decision(strategy: str, version: str, symbol: str, as_of: str, status: str, score: float | None, *, engine: str | None = None, setup: str | None = None, entry: float | None = None, invalidation: float | None = None, horizon: int = 0, reasons: list[str] | None = None, metrics: dict[str, Any] | None = None) -> StrategyDecision:
    evidence = {"strategy": strategy, "version": version, "symbol": symbol, "asOf": as_of, "metrics": metrics or {}}
    digest = content_hash(evidence)
    return StrategyDecision(
        decisionId=f"{strategy}:{symbol}:{as_of}:{digest[:16]}", strategyId=strategy,
        scannerVersion=version, symbol=symbol, asOf=as_of, evidenceHash=digest,
        status=status, score=score, engine=engine, setupClass=setup,
        entryReference=entry, invalidationReference=invalidation,
        horizonSessions=horizon, reasonCodes=tuple(reasons or []), metrics=metrics or {},
    )


class LeadersRest:
    STRATEGY = "LEADERS_REST"

    def evaluate(self, symbol: str, raw: list[dict[str, Any]], spy_raw: list[dict[str, Any]], *, corrected: bool = True, is_etf: bool = False, active_event: bool = False) -> StrategyDecision:
        version = "LR_1_1_0_CORRECTED" if corrected else "LR_1_0_0_EXACT"
        bars, spy = valid_bars(raw), valid_bars(spy_raw)
        minimum = 253 if corrected else 70
        as_of = str(bars[-1]["t"]) if bars else "unavailable"
        if len(bars) < minimum or len(spy) < minimum:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["INSUFFICIENT_HISTORY"], horizon=15)
        if is_etf or active_event:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["ETF_EXCLUDED" if is_etf else "ACTIVE_EVENT"], horizon=15)
        closes = [float(bar["c"]) for bar in bars]
        spy_closes = [float(bar["c"]) for bar in spy]
        price = closes[-1]
        e21, e50, e200 = ema_series(closes, 21)[-1], ema_series(closes, 50)[-1], ema_series(closes, 200)[-1]
        e50_prior = ema_series(closes, 50)[-11]
        spy_e50 = ema_series(spy_closes, 50)
        spy_e200 = ema_series(spy_closes, 200)[-1]
        span = min(252, len(closes) - 1)
        mom = closes[-22] / closes[-1 - span] - 1
        spy_mom = spy_closes[-22] / spy_closes[-1 - min(252, len(spy_closes) - 1)] - 1
        rs_spy = mom - spy_mom if spy_mom is not None else (mom if not corrected else None)
        slope50 = (float(e50) - float(e50_prior)) / float(e50_prior)
        spy_slope = (float(spy_e50[-1]) - float(spy_e50[-11])) / float(spy_e50[-11])
        regime_dead = (spy_closes[-1] < float(spy_e50[-1]) and spy_slope < 0) or (spy_closes[-1] < float(spy_e200) and spy_mom < -0.04) or (spy_mom < -0.04 and spy_slope < 0)
        high52 = max(float(bar["h"]) for bar in bars[-253:])
        off52 = (high52 - price) / high52
        adv20 = mean([float(bar["c"]) * float(bar["v"]) for bar in bars[-20:]])
        if price < 10 and adv20 < 20_000_000:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["PRICE_LIQUIDITY_FLOOR"], horizon=15)
        leader = off52 <= 0.25 and slope50 >= 0 and float(rs_spy) > 0 and (price >= float(e50) or (price >= float(e21) and slope50 >= 0))
        high20 = max(float(bar["h"]) for bar in bars[-20:])
        pullback = (high20 - price) / high20
        range15 = max(float(bar["h"]) for bar in bars[-15:]) - min(float(bar["l"]) for bar in bars[-15:])
        prior_range20 = max(float(bar["h"]) for bar in bars[-35:-15]) - min(float(bar["l"]) for bar in bars[-35:-15])
        range_ratio = range15 / prior_range20 if prior_range20 > 0 else None
        contraction = range_ratio is not None and range_ratio <= 0.60 and 0.02 <= off52 <= 0.18
        rest = 0.03 <= pullback <= 0.12 or contraction
        rsi14 = wilder_rsi(closes)
        dry = mean([float(bar["v"]) for bar in bars[-10:]]) <= mean([float(bar["v"]) for bar in bars[-20:]])
        chase = float(rsi14) > 68 or (off52 < 0.015 and (range_ratio is None or range_ratio > 0.85))
        status = "WAIT"
        reasons: list[str] = []
        if regime_dead: reasons.append("SPY_REGIME_DEAD")
        elif not leader: reasons.append("NOT_LEADER")
        elif chase and not rest: status, reasons = "AVOID", ["CHASE"]
        elif rest and 48 <= float(rsi14) <= 68: status, reasons = "SETUP", ["LEADER_REST"]
        elif rest and float(rsi14) < 48: reasons = ["REST_RSI_WEAK"]
        else: reasons = ["NO_REST"]
        mom_n, rs_n = clip(mom / 0.80, 0, 1), clip(float(rs_spy) / 0.40, 0, 1)
        near_n = clip(1 - off52 / 0.25, 0, 1)
        rsi_n = 1 if 48 <= float(rsi14) <= 68 else 0.45 if rest and float(rsi14) < 48 else 0
        score = clip(round(32 * mom_n + 18 * rs_n + 15 * near_n + 25 * int(rest) + 8 * rsi_n + 2 * int(dry), 1), 1, 100)
        metrics = {"price": price, "ema21": e21, "ema50": e50, "ema200": e200, "mom12_1": mom, "rsSpy": rs_spy, "off52": off52, "pullback": pullback, "rangeRatio": range_ratio, "rsi14": rsi14, "dry": dry, "atr14": wilder_atr(bars), "adv20": adv20, "leader": leader, "rest": rest, "regimeDead": regime_dead}
        return decision(self.STRATEGY, version, symbol, as_of, status, score, setup="REST", entry=price, horizon=15, reasons=reasons, metrics=metrics)


class LocationFirst:
    STRATEGY = "foliotend-location-first-swing"

    def evaluate(self, symbol: str, daily_raw: list[dict[str, Any]], intraday_raw: list[dict[str, Any]], quote: float, *, corrected: bool = True) -> StrategyDecision:
        version = "LF_2_1_0_CORRECTED" if corrected else "LF_2_0_0_EXACT"
        bars, intraday = valid_bars(daily_raw), valid_bars(intraday_raw)
        as_of = str(bars[-1]["t"]) if bars else "unavailable"
        if len(bars) < 60 or len(intraday) < 2 or quote <= 0:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["INSUFFICIENT_EVIDENCE"], horizon=15)
        closes = [float(bar["c"]) for bar in bars]
        e21 = ema_series(closes, 21, first_close_seed=not corrected)[-1]
        e50_series = ema_series(closes, 50, first_close_seed=not corrected)
        e50 = e50_series[-1]
        l12 = min(float(bar["l"]) for bar in bars[-12:])
        atr14, rsi14 = wilder_atr(bars), wilder_rsi(closes)
        _, _, hist = macd(closes)
        recent = [float(value) for value in hist[-6:] if value is not None]
        lift = len(recent) == 6 and sum(recent[index] > recent[index - 1] for index in range(3, 6)) >= 2 and recent[-1] > recent[-4] and recent.index(min(recent)) >= 2
        swing = bars[-60:]
        low_index = min(range(len(swing)), key=lambda index: float(swing[index]["l"]))
        high_index = max(range(len(swing)), key=lambda index: float(swing[index]["h"]))
        fibs: list[tuple[str, float]] = []
        if low_index < high_index:
            low, high = float(swing[low_index]["l"]), float(swing[high_index]["h"])
            fibs = [("FIB50", high - 0.5 * (high - low)), ("FIB61.8", high - 0.618 * (high - low)), ("FIB78.6", high - 0.786 * (high - low))]
        on21 = abs(quote - float(e21)) / float(e21) <= 0.02
        relation12 = (quote - l12) / l12
        on12 = (-0.01 <= relation12 <= 0.04) if corrected else relation12 <= 0.04
        on_fib = [(name, level) for name, level in fibs if abs(quote - level) / level <= 0.025]
        supports = ([('EMA21', float(e21))] if on21 else []) + ([('L12', l12)] if on12 else []) + on_fib
        shelf = min(supports, key=lambda item: (abs(quote - item[1]), {"EMA21": 0, "FIB50": 1, "FIB61.8": 1, "FIB78.6": 1, "L12": 2}.get(item[0], 3))) if supports else None
        under50 = quote < (float(e50) if corrected else 1.008 * float(e50))
        near = relation12 <= 0.06 or on21
        latest, previous = intraday[-1], intraday[-2]
        atr15 = wilder_atr(intraday) or max(float(latest["h"]) - float(latest["l"]), quote * 0.002)
        trigger = None
        if shelf:
            level = shelf[1]
            if float(latest["l"]) <= level + 0.5 * atr15 and float(latest["c"]) >= level: trigger = "SUPPORT_HOLD"
            elif float(previous["c"]) < level <= float(latest["c"]): trigger = "SUPPORT_RECLAIM"
            elif float(latest["c"]) >= level and (float(latest["c"]) >= float(latest["o"]) or float(latest["h"]) - float(latest["l"]) <= atr15): trigger = "CONTROLLED_PULLBACK"
        rvol20 = float(bars[-1]["v"]) / mean([float(bar["v"]) for bar in bars[-21:-1]]) if mean([float(bar["v"]) for bar in bars[-21:-1]]) else None
        stop = min(shelf[1] - 0.5 * float(atr14), 0.99 * l12) if shelf and corrected else None
        risk = quote - float(stop) if stop is not None else None
        highs = sorted({float(bar["h"]) for bar in bars[-60:] if float(bar["h"]) > quote})
        target = highs[0] if highs else None
        rr = (target - quote) / risk if target and risk and risk > 0 else None
        gates = under50 and bool(shelf) and near and float(rsi14) <= 55 and lift and quote <= 1.03 * float(shelf[1]) and rvol20 is not None and rvol20 < 2.2 and bool(trigger) and risk is not None and 0.02 * quote <= risk <= 0.08 * quote and rr is not None and rr >= 1.6
        setup = "A" if gates and float(rsi14) < 50 and quote <= 0.92 * max(float(bar["h"]) for bar in swing) else None
        status = "BUY" if setup else "WAIT"
        reasons = ["LOCATION_FIRST_A"] if setup else ["GATES_INCOMPLETE"]
        metrics = {"price": quote, "ema21": e21, "ema50": e50, "l12": l12, "atr14": atr14, "rsi14": rsi14, "macdLift": lift, "supportType": shelf[0] if shelf else None, "support": shelf[1] if shelf else None, "trigger": trigger, "rvol20": rvol20, "stop": stop, "target": target, "rewardRisk": rr}
        return decision(self.STRATEGY, version, symbol, as_of, status, 100 if setup else 0, setup=setup, entry=quote, invalidation=stop, horizon=15, reasons=reasons, metrics=metrics)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class Parallax:
    STRATEGY = "PARALLAX"

    def evaluate(self, symbol: str, raw: list[dict[str, Any]], *, benchmark_returns: dict[int, float], field_sleeve: str, regime: str, risk_board: str = "NORMAL", corrected: bool = False) -> StrategyDecision:
        version = "PX_1_3_0_CHALLENGER" if corrected else "PX_1_3_0_EXACT"
        bars = valid_bars(raw)
        as_of = str(bars[-1]["t"]) if bars else "unavailable"
        if len(bars) < 70 or field_sleeve in {"UNAVAILABLE", "WATERFALL"}:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["INSUFFICIENT_OR_FIELD_UNAVAILABLE"], horizon=10)
        closes = [float(bar["c"]) for bar in bars]
        returns = {period: return_n(closes, period) for period in (5, 20, 60)}
        residual = {period: float(returns[period]) - float(benchmark_returns.get(period, 0)) for period in returns}
        atr14 = float(wilder_atr(bars))
        atr_pct = 100 * atr14 / closes[-1]
        rsi14 = float(wilder_rsi(closes))
        e20, e50 = ema_series(closes, 20)[-1], ema_series(closes, 50)[-1]
        path = sum(abs(closes[index] - closes[index - 1]) for index in range(len(closes) - 19, len(closes)))
        pe20 = abs(closes[-1] - closes[-21]) / path if path else 0
        close_location = (closes[-1] - float(bars[-1]["l"])) / max(float(bars[-1]["h"]) - float(bars[-1]["l"]), 1e-12)
        d20, shock = (closes[-1] - float(e20)) / atr14, float(returns[5]) / atr_pct
        rvol = float(bars[-1]["v"]) / mean([float(bar["v"]) for bar in bars[-21:-1]]) if mean([float(bar["v"]) for bar in bars[-21:-1]]) else None
        _, _, histogram = macd(closes)
        h = [value for value in histogram if value is not None]
        macd_repair = len(h) >= 2 and h[-1] > h[-2]
        engines: dict[str, float] = {}
        engines["DRIFT"] = clip(40 + 1.4 * residual[20] + 0.45 * residual[60] + 22 * pe20 + (10 if closes[-1] >= float(e50) else -10) + (8 if d20 <= 1.75 else -12) + (5 if rvol is None or 0.65 <= rvol < 2.2 else -8), 0, 100)
        engines["DISLOCATION"] = clip(35 + 13 * max(0, -shock - 1) + 20 * close_location + 10 * int(rsi14 < 45) + 8 * int(macd_repair) + (5 if rvol is None or rvol < 2.2 else -10), 0, 100)
        high20 = max(float(bar["h"]) for bar in bars[-21:-1])
        windows = [(max(float(bar["h"]) for bar in bars[index - 19:index + 1]) - min(float(bar["l"]) for bar in bars[index - 19:index + 1])) / float(bars[index - 19]["c"]) for index in range(19, len(bars))]
        comp_pct = 100 * sum(value <= windows[-1] for value in windows[-252 if corrected else 0:]) / len(windows[-252 if corrected else 0:])
        engines["COMPRESSION"] = clip(35 + 1.25 * max(0, 30 - comp_pct) + clip(residual[20], -10, 20) + (15 if 0.97 * high20 <= closes[-1] <= 1.02 * high20 else 0) + (8 if rvol is None or rvol < 2.2 else -5), 0, 100)
        boundary = min(float(bar["l"]) for bar in bars[-22:-2])
        reclaim = float(bars[-2]["l"]) < boundary and float(bars[-2]["c"]) < boundary and closes[-1] >= boundary and close_location >= 0.55
        engines["RECLAIM"] = clip(30 + 42 * int(reclaim) + 15 * close_location + clip(residual[20], -8, 15) + (8 if rvol is None or rvol < 2.2 else -8), 0, 100)
        allowed = {"TREND": {"DRIFT", "COMPRESSION"}, "TURN": {"DISLOCATION", "RECLAIM", "COMPRESSION"}, "TROUGH": {"DISLOCATION", "RECLAIM"}}.get(field_sleeve, set())
        if not allowed:
            return decision(self.STRATEGY, version, symbol, as_of, "UNAVAILABLE", None, reasons=["NO_ALLOWED_ENGINE"], horizon=10)
        preferred = {"TREND": "DRIFT", "TURN": "RECLAIM", "TROUGH": "DISLOCATION"}.get(field_sleeve)
        engine = max(allowed, key=lambda item: engines[item] + (6 if item == preferred else 0))
        base = engines[engine]
        penalties = 1.5 * max(0, atr_pct - 4) + (8 if rvol is not None and rvol < 0.5 else 2) + (8 if abs(shock) > 3 else 2) + (12 if d20 > 2 else 10 if rvol is not None and rvol >= 2.2 else 0) + 5
        opportunity = round(clip(base - penalties, -100, 100))
        status = "WAIT"
        if rvol is not None and rvol >= 2.8: status = "AVOID"
        elif regime in {"PANIC", "HIGH_VOLATILITY_DELEVERAGING"} or field_sleeve == "TROUGH" or risk_board == "DEFENSIVE": status = "WAIT"
        elif opportunity >= 48: status = "BUY"
        metrics = {"returns": returns, "residual": residual, "atrPct": atr_pct, "rsi14": rsi14, "pe20": pe20, "closeLocation": close_location, "d20": d20, "shock": shock, "rvol": rvol, "compressionPct": comp_pct, "high20": high20, "compressionLow": min(float(bar["l"]) for bar in bars[-20:]), "fieldSleeve": field_sleeve, "regime": regime, "riskBoard": risk_board, "engineScores": engines, "netOpportunity": opportunity}
        return decision(self.STRATEGY, version, symbol, as_of, status, opportunity, engine=engine, entry=closes[-1], horizon=10, reasons=[f"{engine}_{status}"], metrics=metrics)
