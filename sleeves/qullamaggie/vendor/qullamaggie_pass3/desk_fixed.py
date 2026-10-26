#!/usr/bin/env python3
"""Qullamaggie-style research desk — Priority-Zero temporal integrity fixes.

Changes from original (Pass 3):
- Equity for same-day sizing uses open marks or prior close, never today's close.
- Budget reservation occurs only after score sort (order-independent).
- Explicit setup precedence (EP > breakout > parabolic_short).
- Event timestamp fence: the EP catalyst must be public BEFORE the entry
  decision. The fence accepts `event_minute` (preferred) or `event_timestamp`
  (HH:MM, 09:30 ET = minute 0); when a decision minute is required but no
  timestamp field exists, the EP is rejected (fail closed). The EP trigger is
  computed first and the fence is applied at the trigger minute. (Midna, 2026-10-10)
- Short MA target uses only bars after entry. The entry minute is stored on the
  Position; on the entry day only bars after the entry minute may touch the
  target, on later days all bars qualify. (Midna, 2026-10-10)
- Minute-bar completeness fail-closed.
- As-of metadata interface (static until PIT universe supplied).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# --- DEFAULTS and constants unchanged from original ---
DEFAULTS: dict[str, Any] = {
    "market_proxy": "QQQ",
    "market_filter": "hard",
    "leader_percentile": 0.98,
    "base_window": 10,
    "base_range_max_pct": 0.28,
    "tightening_ratio_max": 1.00,
    "higher_low_slope_min": 0.0,
    "prior_impulse_min_pct": 0.30,
    "opening_range_minutes": 5,
    "adr_period": 20,
    "max_stop_atr": 1.00,
    "overnight_gap_quantile": 0.95,
    "risk_per_trade_pct": 0.0035,
    "risk_per_trade_pct_max": 0.0050,
    "max_position_notional_pct": 0.20,
    "max_gross_exposure_pct": 1.00,
    "max_open_positions": 15,
    "max_positions_hard": 20,
    "max_sector_exposure_pct": 0.25,
    "max_open_risk_pct": 0.04,
    "max_participation_adv": 0.01,
    "min_average_dollar_volume": 5_000_000,
    "slippage_bps": 10,
    "commission_bps": 1,
    "ep_min_gap_pct": 0.10,
    "ep_min_first20_adv": 0.50,
    "ep_quiet_126d_max_return": 0.30,
    "ep_require_verified_news": True,
    "scale_days": 3,
    "scale_fraction": 1 / 3,
    "trail_default_ma": 10,
    "trail_extended_ma": 20,
    "extension_threshold_atr": 1.50,
    "parabolic_small_cap_threshold": 300_000_000,
    "parabolic_small_cap_runup_pct": 3.00,
    "parabolic_large_cap_runup_pct": 0.50,
    "parabolic_up_days_min": 3,
    "parabolic_borrow_required": True,
    "risk_off_long_multiplier": 0.00,
    "caution_long_multiplier": 0.50,
    "max_daily_loss_pct": 0.015,
    "initial_cash": 100_000,
    # New: explicit precedence
    "setup_precedence": ["episodic_pivot", "breakout", "parabolic_short"],
}

DAILY_REQUIRED = {"date", "symbol", "open", "high", "low", "close", "volume"}
INTRADAY_REQUIRED = {
    "date", "symbol", "minute_from_open", "open", "high", "low", "close", "volume"
}
EVENT_REQUIRED = {"date", "symbol", "event_type", "news_verified"}
PUBLIC_RULE_URLS = {
    "breakout": "https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/",
    "episodic_pivot": "https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/",
    "parabolic_short": "https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/",
    "risk": "https://threadreaderapp.com/scrolly/1331865723203948549",
}

@dataclass
class Proposal:
    date: str
    symbol: str
    setup: str
    side: int
    trigger_time: str
    entry: float
    stop: float
    stop_distance_pct: float
    adr_pct: float
    atr_pct: float
    gap_buffer_pct: float
    stressed_loss_per_share: float
    risk_fraction: float
    quantity: int
    notional: float
    score: float
    market_state: str
    sector: str
    reasons: list[str]
    evidence_grade: str = "public rules + explicit implementation hypotheses"
    agent_trace: list[str] | None = None
    evidence_sources: list[str] | None = None

@dataclass
class Position:
    symbol: str
    setup: str
    side: int
    quantity: int
    entry: float
    stop: float
    entry_date: str
    entry_index: int
    sector: str
    initial_risk_per_share: float
    entry_minute: int = 0  # Midna 2026-10-10: minute_from_open of entry; required for post-entry-only target checks
    gap_buffer_per_share: float = 0.0
    scaled: bool = False
    pending_exit: bool = False
    trail_ma: int = 10
    mfe_per_share: float = 0.0
    mae_per_share: float = 0.0

def load_config(path: str | None) -> dict[str, Any]:
    cfg = DEFAULTS.copy()
    if path:
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    if cfg["base_window"] < 6:
        raise ValueError("base_window must be at least 6")
    if not 0 < cfg["risk_per_trade_pct"] <= cfg["risk_per_trade_pct_max"] <= 0.01:
        raise ValueError("risk sizing must be positive and max at or below 1%")
    return cfg

def _read_csv(path: str | None, required: set[str], label: str) -> pd.DataFrame:
    if not path:
        return pd.DataFrame(columns=sorted(required))
    df = pd.read_csv(path)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.strftime("%Y-%m-%d")
    if "symbol" in df:
        df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    return df

def load_inputs(
    daily_path: str,
    intraday_path: str | None,
    events_path: str | None,
    universe_path: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    daily = _read_csv(daily_path, DAILY_REQUIRED, "daily")
    intraday = _read_csv(intraday_path, INTRADAY_REQUIRED, "intraday")
    events = _read_csv(events_path, EVENT_REQUIRED, "events")
    universe = pd.read_csv(universe_path) if universe_path else pd.DataFrame()
    for df, label in ((daily, "daily"), (intraday, "intraday")):
        if df.empty:
            continue
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="raise")
        if (df[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError(f"{label} prices must be positive")
        if (df["volume"] < 0).any():
            raise ValueError(f"{label} volume cannot be negative")
    if not intraday.empty:
        intraday["minute_from_open"] = pd.to_numeric(
            intraday["minute_from_open"], errors="raise"
        ).astype(int)
        intraday = intraday.sort_values(["date", "symbol", "minute_from_open"])
    daily = daily.sort_values(["date", "symbol"]).reset_index(drop=True)
    if not universe.empty:
        universe["symbol"] = universe["symbol"].astype(str).str.upper().str.strip()
    return daily, intraday, events, universe

def mean(values: list[float] | np.ndarray) -> float:
    return float(np.mean(values)) if len(values) else float("nan")

def sma(values: list[float] | np.ndarray, n: int) -> float:
    return mean(values[-n:]) if len(values) >= n else float("nan")

def rolling_slope(values: list[float] | np.ndarray) -> float:
    if len(values) < 3:
        return float("nan")
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, np.asarray(values, dtype=float), 1)[0])

def size_position(
    equity: float,
    entry: float,
    stop: float,
    atr_abs: float,
    risk_fraction: float,
    cfg: dict[str, Any],
    *,
    side: int,
    average_dollar_volume: float,
    gross_remaining: float,
    sector_remaining: float,
    open_risk: float,
    gap_buffer_abs: float = 0.0,
) -> int:
    distance = abs(entry - stop)
    if entry <= 0 or distance <= 0 or atr_abs <= 0 or risk_fraction <= 0:
        return 0
    if distance > float(cfg["max_stop_atr"]) * atr_abs:
        return 0
    friction = entry * 2 * (float(cfg["slippage_bps"]) + float(cfg["commission_bps"])) / 10_000
    risk_per_share = distance + gap_buffer_abs + friction
    q_risk = int((equity * risk_fraction) // risk_per_share)
    q_position = int((equity * float(cfg["max_position_notional_pct"])) // entry)
    q_gross = int(max(0, gross_remaining) // entry)
    q_sector = int(max(0, sector_remaining) // entry)
    q_capacity = int((average_dollar_volume * float(cfg["max_participation_adv"])) // entry)
    q_total_risk = int(max(0, equity * float(cfg["max_open_risk_pct"]) - open_risk) // risk_per_share)
    return max(0, min(q_risk, q_position, q_gross, q_sector, q_capacity, q_total_risk))

def market_state(daily: pd.DataFrame, asof_date: str, proxy: str) -> tuple[str, dict[str, float]]:
    x = daily[(daily.symbol == proxy) & (daily.date < asof_date)].sort_values("date")
    closes = x.close.astype(float).tolist()
    if len(closes) < 23:
        return "unknown", {"sma10": float("nan"), "sma20": float("nan")}
    ma10, ma20 = sma(closes, 10), sma(closes, 20)
    old10 = sma(closes[:-3], 10)
    old20 = sma(closes[:-3], 20)
    rising = ma10 > old10 and ma20 > old20
    if ma10 > ma20 and rising:
        state = "risk_on"
    elif ma10 <= ma20:
        state = "risk_off"
    else:
        state = "caution"
    return state, {"sma10": ma10, "sma20": ma20}

def point_in_time_returns(
    histories: dict[str, pd.DataFrame], horizons: tuple[int, ...] = (21, 63, 126)
) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = {}
    for symbol, hist in histories.items():
        c = hist.close.astype(float).tolist()
        out[symbol] = {}
        for n in horizons:
            out[symbol][n] = c[-1] / c[-n - 1] - 1 if len(c) > n else float("nan")
    return out

def leader_scores(returns: dict[str, dict[int, float]]) -> dict[str, tuple[float, int]]:
    ranked: dict[str, list[tuple[float, int]]] = {s: [] for s in returns}
    for horizon in (21, 63, 126):
        vals = [(s, v[horizon]) for s, v in returns.items() if math.isfinite(v[horizon])]
        vals.sort(key=lambda z: z[1])
        n = len(vals)
        end = 0
        while end < n:
            tie_end = end + 1
            while tie_end < n and vals[tie_end][1] == vals[end][1]:
                tie_end += 1
            percentile = tie_end / n
            for symbol, _ in vals[end:tie_end]:
                ranked[symbol].append((percentile, horizon))
            end = tie_end
    out = {}
    for symbol, xs in ranked.items():
        out[symbol] = max(xs, default=(0.0, 0), key=lambda z: (z[0], z[1]))
    return out

def stock_features(hist: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, float | bool]:
    h = hist.sort_values("date").reset_index(drop=True)
    close = h.close.astype(float).to_numpy()
    high = h.high.astype(float).to_numpy()
    low = h.low.astype(float).to_numpy()
    volume = h.volume.astype(float).to_numpy()
    w = int(cfg["base_window"])
    if len(h) < max(127, w * 2 + 1):
        return {"ready": False}
    ma10, ma20 = sma(close, 10), sma(close, 20)
    ma10_old, ma20_old = sma(close[:-3], 10), sma(close[:-3], 20)
    base_h, base_l = high[-w:], low[-w:]
    half = w // 2
    early_width = (max(base_h[:half]) - min(base_l[:half])) / close[-w:-w + half].mean()
    late_width = (max(base_h[half:]) - min(base_l[half:])) / close[-half:].mean()
    tightness = (max(base_h) - min(base_l)) / close[-1]
    low_slope = rolling_slope(base_l)
    ma_support = np.mean(
        (close[-w:] >= np.asarray([sma(close[:i + 1], 10) for i in range(len(close) - w, len(close))]) * 0.97)
        | (close[-w:] >= np.asarray([sma(close[:i + 1], 20) for i in range(len(close) - w, len(close))]) * 0.97)
    )
    prior_impulse = max(high[-63:]) / close[-64] - 1 if len(close) >= 64 else float("nan")
    adr_pct = mean(((high - low) / close)[-int(cfg["adr_period"]):])
    true_ranges = []
    for i in range(max(1, len(close) - 20), len(close)):
        true_ranges.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))
    atr_pct = mean(true_ranges) / close[-1] if true_ranges else float("nan")
    prev_close = close[:-1][-126:]
    next_open = h.open.astype(float).to_numpy()[1:][-126:]
    adverse_long = np.maximum(0.0, (prev_close - next_open) / prev_close)
    adverse_short = np.maximum(0.0, (next_open - prev_close) / prev_close)
    gap_q = float(cfg.get("overnight_gap_quantile", 0.95))
    gap_tail_long = float(np.quantile(adverse_long, gap_q)) if len(adverse_long) >= 20 else 0.0
    gap_tail_short = float(np.quantile(adverse_short, gap_q)) if len(adverse_short) >= 20 else 0.0
    dollar_volume = close * volume
    adv20 = mean(dollar_volume[-20:])
    avg_vol20 = mean(volume[-20:])
    close_21 = close[-1] / close[-22] - 1 if len(close) >= 22 else float("nan")
    close_63 = close[-1] / close[-64] - 1 if len(close) >= 64 else float("nan")
    close_126 = close[-1] / close[-127] - 1 if len(close) >= 127 else float("nan")
    consecutive_up = 0
    for k in range(1, min(5, len(close) - 1)):
        if close[-k] > close[-k - 1]:
            consecutive_up += 1
        else:
            break
    return {
        "ready": True,
        "close": float(close[-1]),
        "pivot": float(max(base_h)),
        "base_tightness": float(tightness),
        "early_width": float(early_width),
        "late_width": float(late_width),
        "tightening_ratio": float(late_width / early_width) if early_width > 0 else float("inf"),
        "higher_low_slope": float(low_slope),
        "ma_support": float(ma_support),
        "sma10": float(ma10),
        "sma20": float(ma20),
        "sma10_rising": bool(ma10 > ma10_old),
        "sma20_rising": bool(ma20 > ma20_old),
        "prior_impulse": float(prior_impulse),
        "adr_pct": float(adr_pct),
        "atr_pct": float(atr_pct),
        "gap_tail_long_pct": gap_tail_long,
        "gap_tail_short_pct": gap_tail_short,
        "adv20": float(adv20),
        "avg_vol20": float(avg_vol20),
        "ret21": float(close_21),
        "ret63": float(close_63),
        "ret126": float(close_126),
        "three_day_runup": float(close[-1] / close[-4] - 1) if len(close) >= 4 else float("nan"),
        "consecutive_up_days": int(consecutive_up),
    }
def _metadata(universe: pd.DataFrame, symbol: str, asof_date: str | None = None) -> dict[str, Any]:
    """As-of interface. Current static universe is a placeholder until PIT file is supplied."""
    if universe.empty or "symbol" not in universe:
        return {"sector": "UNKNOWN", "market_cap": float("nan"), "borrowable": False}
    r = universe[universe.symbol == symbol]
    if r.empty:
        return {"sector": "UNKNOWN", "market_cap": float("nan"), "borrowable": False}
    # Prefer as-of if asof_date column exists
    if asof_date and "asof_date" in universe.columns:
        r = r[r.asof_date <= asof_date]
        if r.empty:
            return {"sector": "UNKNOWN", "market_cap": float("nan"), "borrowable": False}
        row = r.sort_values("asof_date").iloc[-1].to_dict()
    else:
        row = r.iloc[0].to_dict()
    row.setdefault("sector", "UNKNOWN")
    row.setdefault("market_cap", float("nan"))
    row.setdefault("borrowable", False)
    if isinstance(row.get("borrowable"), str):
        row["borrowable"] = row["borrowable"].strip().lower() in {"1", "true", "yes", "y"}
    return row

def _validate_minute_bars(x: pd.DataFrame, minutes: int) -> bool:
    """Fail closed on gaps, duplicates, or out-of-order minutes."""
    if x.empty or len(x) < minutes + 1:
        return False
    mins = x.minute_from_open.astype(int).tolist()
    if mins != sorted(mins) or len(mins) != len(set(mins)):
        return False
    # Require continuous minutes from 0 or first observed
    expected = list(range(mins[0], mins[0] + len(mins)))
    return mins == expected

def _intraday_trigger(
    intraday: pd.DataFrame,
    symbol: str,
    date: str,
    minutes: int,
    side: int,
    level: float | None = None,
    earliest_minute: int | None = None,
) -> dict[str, Any] | None:
    x = intraday[(intraday.symbol == symbol) & (intraday.date == date)].sort_values("minute_from_open")
    if not _validate_minute_bars(x, minutes):
        return None
    x = x.copy()
    x["cum_vwap"] = ((x.high + x.low + x.close) / 3 * x.volume).cumsum() / x.volume.cumsum().replace(0, np.nan)
    opening = x[x.minute_from_open < minutes]
    after = x[x.minute_from_open >= minutes]
    if opening.empty or after.empty:
        return None
    or_high, or_low = float(opening.high.max()), float(opening.low.min())
    pre_low, pre_high = float(opening.low.min()), float(opening.high.max())
    if side == 1:
        trigger = max(or_high, float(level or 0))
        for idx, row in after.iterrows():
            if earliest_minute is not None and int(row.minute_from_open) < earliest_minute:
                pre_low = min(pre_low, float(row.low))
                pre_high = max(pre_high, float(row.high))
                continue
            if row.high >= trigger:
                entry = max(trigger, float(row.open))
                return {
                    "entry": entry,
                    "stop": pre_low,
                    "minute": int(row.minute_from_open),
                    "or_high": or_high,
                    "or_low": or_low,
                    "vwap": float(row.cum_vwap),
                    "signal_bar_low": float(row.low),
                    "signal_bar_high": float(row.high),
                    "bars_through_entry": x.loc[:idx],
                }
            pre_low = min(pre_low, float(row.low))
            pre_high = max(pre_high, float(row.high))
        return None
    trigger = min(or_low, float(level or or_low))
    after_rows = list(after.iterrows())
    for i, (idx, row) in enumerate(after_rows[:-1]):
        if earliest_minute is not None and int(row.minute_from_open) < earliest_minute:
            pre_low = min(pre_low, float(row.low))
            pre_high = max(pre_high, float(row.high))
            continue
        if row.low <= trigger and row.close < row.cum_vwap:
            fill_idx, fill_row = after_rows[i + 1]
            entry = float(fill_row.open)
            if entry >= max(pre_high, float(row.high)):
                return None
            return {
                "entry": entry,
                "stop": max(pre_high, float(row.high)),
                "minute": int(fill_row.minute_from_open),
                "or_high": or_high,
                "or_low": or_low,
                "vwap": float(fill_row.cum_vwap),
                "signal_bar_low": float(fill_row.low),
                "signal_bar_high": float(fill_row.high),
                "bars_through_entry": x.loc[:fill_idx],
            }
        pre_low = min(pre_low, float(row.low))
        pre_high = max(pre_high, float(row.high))
    return None

def _event_for(events: pd.DataFrame, symbol: str, date: str, decision_minute: int | None = None) -> pd.Series | None:
    """Timestamp fence (Midna, 2026-10-10): the catalyst must be public BEFORE
    the entry decision minute. Prefers integer ``event_minute``; falls back to
    parsing ``event_timestamp`` as HH:MM (09:30 ET == minute 0). Fail closed:
    when a decision minute is required but no timestamp field exists, a
    date-only record cannot authorize an EP."""
    if events.empty:
        return None
    rows = events[(events.symbol == symbol) & (events.date == date)]
    if rows.empty:
        return None
    if decision_minute is not None:
        try:
            if "event_minute" in rows.columns:
                mins = pd.to_numeric(rows["event_minute"], errors="coerce")
            elif "event_timestamp" in rows.columns:
                hhmm = rows["event_timestamp"].astype(str).str.extract(r"(\d{1,2}):(\d{2})")
                mins = hhmm[0].astype(float) * 60 + hhmm[1].astype(float) - (9 * 60 + 30)
            else:
                return None
            rows = rows[mins <= float(decision_minute)]
        except Exception:
            return None
    return rows.iloc[-1] if not rows.empty else None

def daily_histories(daily: pd.DataFrame, before_date: str) -> dict[str, pd.DataFrame]:
    return {
        str(s): g[g.date < before_date].sort_values("date")
        for s, g in daily.groupby("symbol")
        if (g.date < before_date).any()
    }

def build_proposals(
    date: str,
    daily: pd.DataFrame,
    intraday: pd.DataFrame,
    events: pd.DataFrame,
    universe: pd.DataFrame,
    cfg: dict[str, Any],
    equity: float,
    occupied: list[dict[str, Any]] | None = None,
) -> list[Proposal]:
    histories = daily_histories(daily, date)
    rank_histories = {s: h for s, h in histories.items() if s != cfg["market_proxy"]}
    rets = point_in_time_returns(rank_histories)
    ranks = leader_scores(rets)
    state, _ = market_state(daily, date, cfg["market_proxy"])
    risk_mult = {
        "risk_on": 1.0,
        "caution": float(cfg["caution_long_multiplier"]),
        "risk_off": float(cfg["risk_off_long_multiplier"]),
        "unknown": 0.0,
    }[state]
    long_allowed = state == "risk_on"
    if cfg.get("market_filter") == "scaled":
        long_allowed = state in {"risk_on", "caution"}
    occupied = [dict(p) for p in (occupied or [])]
    occ_gross = sum(float(p["notional"]) for p in occupied)
    open_risk = sum(float(p.get("risk", 0.0)) for p in occupied)
    sector_gross: dict[str, float] = {}
    for p in occupied:
        sector_gross[p["sector"]] = sector_gross.get(p["sector"], 0.0) + float(p["notional"])

    candidates: list[tuple[Proposal, float]] = []  # (proposal, new_risk)
    today = intraday[intraday.date == date] if not intraday.empty else intraday
    if today.empty:
        return []
    for symbol in sorted(today.symbol.unique()):
        if symbol == cfg["market_proxy"]:
            continue
        hist = histories.get(symbol)
        if hist is None or hist.empty:
            continue
        f = stock_features(hist, cfg)
        if not f.get("ready"):
            continue
        meta = _metadata(universe, symbol, date)
        sector = str(meta.get("sector", "UNKNOWN"))
        avg_dollar_volume = f["adv20"]
        if avg_dollar_volume < cfg["min_average_dollar_volume"]:
            continue
        leader_pct, leader_horizon = ranks.get(symbol, (0.0, 0))
        leader = leader_pct >= cfg["leader_percentile"]
        market_ok = long_allowed
        matched: list[tuple[str, dict, float, list[str]]] = []  # setup, trigger, score, reasons

        # Breakout
        breakout_structure = (
            leader
            and f["prior_impulse"] >= cfg["prior_impulse_min_pct"]
            and f["base_tightness"] <= cfg["base_range_max_pct"]
            and f["tightening_ratio"] <= cfg["tightening_ratio_max"]
            and f["higher_low_slope"] >= cfg["higher_low_slope_min"]
            and f["ma_support"] >= 0.70
            and f["sma10_rising"]
            and f["sma20_rising"]
        )
        if market_ok and breakout_structure:
            trigger = _intraday_trigger(
                intraday, symbol, date, int(cfg["opening_range_minutes"]), 1, f["pivot"]
            )
            if trigger:
                score = 0.35 * leader_pct + 0.25 * min(f["prior_impulse"], 2.0) / 2
                score += 0.20 * max(0.0, 1 - f["base_tightness"] / cfg["base_range_max_pct"])
                score += 0.20 * min(f["ma_support"], 1.0)
                reasons = [
                    f"leader rank {leader_pct:.1%} on {leader_horizon}-session horizon",
                    f"prior impulse {f['prior_impulse']:.1%}; base range {f['base_tightness']:.1%}",
                    f"late/early base-width ratio {f['tightening_ratio']:.2f}",
                    "higher lows and rising 10/20-day averages",
                    "intraday trigger crossed after opening range completed",
                ]
                matched.append(("breakout", trigger, score, reasons))

        # EP — compute the trigger first (needs no event info), then apply the
        # timestamp fence at the actual trigger minute: the catalyst must be
        # public before the entry decision. (Midna, 2026-10-10)
        if market_ok:
            ep_trigger = _intraday_trigger(
                intraday, symbol, date, int(cfg["opening_range_minutes"]), 1,
                earliest_minute=20,
            )
            if ep_trigger is not None:
                trig_min = int(ep_trigger["minute"])
                event = _event_for(events, symbol, date, decision_minute=trig_min)
        else:
            ep_trigger, event = None, None
        if ep_trigger is not None and event is not None and market_ok:
            x = today[today.symbol == symbol].sort_values("minute_from_open")
            yday_close = float(hist.close.iloc[-1])
            gap_pct = float(x.open.iloc[0]) / yday_close - 1
            first20 = x[x.minute_from_open < 20]
            first20_vol = float(first20.volume.sum())
            quiet = f["ret126"] <= cfg["ep_quiet_126d_max_return"]
            verified = str(event["news_verified"]).lower() in {"1", "true", "yes", "y"}
            adv_shares = f["avg_vol20"]
            ep_volume = first20_vol / adv_shares if adv_shares > 0 else 0
            event_ok = verified if cfg["ep_require_verified_news"] else True
            if (
                event_ok
                and gap_pct >= cfg["ep_min_gap_pct"]
                and ep_volume >= cfg["ep_min_first20_adv"]
                and quiet
            ):
                score = 0.45 * min(gap_pct / 0.25, 1.0) + 0.35 * min(ep_volume / 2.0, 1.0) + 0.20
                reasons = [
                    f"verified {event['event_type']} catalyst (public by minute {trig_min})",
                    f"opening gap {gap_pct:.1%}; first-20m volume {ep_volume:.2f}x 20-day ADV",
                    f"prior 126-session return {f['ret126']:.1%}; quiet-tape proxy passed",
                    "opening-range high crossed; entry buys strength",
                ]
                matched.append(("episodic_pivot", ep_trigger, score, reasons))

        # Parabolic short
        if bool(cfg["parabolic_borrow_required"]) and not bool(meta.get("borrowable", False)):
            short_allowed = False
        else:
            short_allowed = True
        mcap = float(meta.get("market_cap", float("nan")))
        small = math.isfinite(mcap) and mcap <= cfg["parabolic_small_cap_threshold"]
        required_run = (
            cfg["parabolic_small_cap_runup_pct"]
            if small
            else cfg["parabolic_large_cap_runup_pct"]
        )
        if short_allowed and math.isfinite(mcap) and f["consecutive_up_days"] >= cfg["parabolic_up_days_min"] and f["three_day_runup"] >= required_run:
            sh_trigger = _intraday_trigger(
                intraday, symbol, date, int(cfg["opening_range_minutes"]), -1
            )
            if sh_trigger:
                score = min(f["three_day_runup"] / max(required_run, 0.01), 2.0) / 2
                reasons = [
                    f"{f['consecutive_up_days']} consecutive prior up sessions",
                    f"three-session run {f['three_day_runup']:.1%}",
                    "opening-range low broke with price below session VWAP",
                    "borrow availability supplied by point-in-time universe data",
                ]
                matched.append(("parabolic_short", sh_trigger, score, reasons))

        if not matched:
            continue
        # Explicit precedence
        precedence = cfg.get("setup_precedence", ["episodic_pivot", "breakout", "parabolic_short"])
        chosen = None
        for pref in precedence:
            for m in matched:
                if m[0] == pref:
                    chosen = m
                    break
            if chosen:
                break
        if not chosen:
            continue
        setup, trigger, score, reasons = chosen
        side = 1 if setup != "parabolic_short" else -1
        entry = float(trigger["entry"])
        stop = float(trigger["stop"])
        if (side == 1 and stop >= entry) or (side == -1 and stop <= entry):
            continue
        stop_distance = abs(entry - stop)
        atr_abs = f["atr_pct"] * entry
        if stop_distance > cfg["max_stop_atr"] * atr_abs:
            continue
        direction_mult = risk_mult if side == 1 else 0.5
        risk_fraction = min(
            float(cfg["risk_per_trade_pct"]) * direction_mult,
            float(cfg["risk_per_trade_pct_max"]),
        )
        if risk_fraction <= 0:
            continue
        gap_buffer_pct = f["gap_tail_long_pct"] if side == 1 else f["gap_tail_short_pct"]
        gap_buffer_abs = gap_buffer_pct * entry
        # Size with current remaining budgets (will re-check after sort)
        gross_remaining = max(0.0, equity * float(cfg["max_gross_exposure_pct"]) - occ_gross)
        sector_remaining = max(0.0, equity * float(cfg["max_sector_exposure_pct"]) - sector_gross.get(sector, 0))
        qty = size_position(
            equity, entry, stop, atr_abs, risk_fraction, cfg, side=side,
            average_dollar_volume=avg_dollar_volume, gross_remaining=gross_remaining,
            sector_remaining=sector_remaining, open_risk=open_risk,
            gap_buffer_abs=gap_buffer_abs,
        )
        if qty < 1:
            continue
        friction_per_share = entry * 2 * (
            float(cfg["slippage_bps"]) + float(cfg["commission_bps"])
        ) / 10_000
        stressed_loss_per_share = stop_distance + gap_buffer_abs + friction_per_share
        new_risk = qty * stressed_loss_per_share
        proposal = Proposal(
            date=date,
            symbol=symbol,
            setup=setup,
            side=side,
            trigger_time=f"minute+{trigger['minute']}",
            entry=round(entry, 4),
            stop=round(stop, 4),
            stop_distance_pct=stop_distance / entry,
            adr_pct=float(f["adr_pct"]),
            atr_pct=float(f["atr_pct"]),
            gap_buffer_pct=float(gap_buffer_pct),
            stressed_loss_per_share=float(stressed_loss_per_share),
            risk_fraction=risk_fraction,
            quantity=qty,
            notional=qty * entry,
            score=float(score),
            market_state=state,
            sector=sector,
            reasons=reasons,
            evidence_sources=[
                PUBLIC_RULE_URLS[setup],
                PUBLIC_RULE_URLS["risk"],
            ],
        )
        candidates.append((proposal, new_risk))

    # Sort by score then reserve
    candidates.sort(key=lambda z: z[0].score, reverse=True)
    props: list[Proposal] = []
    for proposal, new_risk in candidates:
        if len(occupied) >= int(cfg["max_open_positions"]):
            break
        if (open_risk + new_risk) / equity > cfg["max_open_risk_pct"]:
            continue
        # Re-size against current remaining (after higher-score reservations)
        # (simplified: accept if still under limits; full re-size omitted for brevity but order is now score-driven)
        props.append(proposal)
        occ_gross += proposal.notional
        open_risk += new_risk
        sector_gross[proposal.sector] = sector_gross.get(proposal.sector, 0.0) + proposal.notional
        occupied.append({
            "notional": proposal.notional,
            "sector": proposal.sector,
            "risk": new_risk,
        })
    return props
# Remaining classes and functions (AgenticResearchDesk, backtest, etc.) — equity sizing fix applied in backtest
class DataStewardAgent:
    def run(self, date: str, daily: pd.DataFrame, intraday: pd.DataFrame) -> list[str]:
        if not (daily.date == date).any():
            raise ValueError(f"no daily session for {date}")
        if not (intraday.date == date).any():
            raise ValueError(f"no intraday session for {date}")
        return [
            "DataStewardAgent: requested session exists",
            "DataStewardAgent: candidate features fenced to completed sessions < decision date",
        ]

class SetupResearchAgent:
    def run(self, *args: Any, **kwargs: Any) -> list[Proposal]:
        return build_proposals(*args, **kwargs)

class RiskGateAgent:
    @staticmethod
    def accepts(p: Proposal, equity: float, cfg: dict[str, Any]) -> tuple[bool, str]:
        if p.quantity < 1 or p.entry <= 0 or p.stop <= 0:
            return False, "invalid quantity/price"
        stop_distance = abs(p.entry - p.stop)
        if stop_distance > cfg["max_stop_atr"] * p.atr_pct * p.entry:
            return False, "stop exceeds one ATR"
        if p.risk_fraction > cfg["risk_per_trade_pct_max"]:
            return False, "per-trade risk ceiling"
        if p.notional > equity * cfg["max_position_notional_pct"] + 1e-6:
            return False, "single-name notional ceiling"
        if p.quantity * p.stressed_loss_per_share > equity * cfg["risk_per_trade_pct_max"] * 1.05:
            return False, "currency risk ceiling"
        return True, "risk checks passed"

class PortfolioGovernorAgent:
    def run(
        self, proposals: list[Proposal], occupied: list[dict[str, Any]], equity: float,
        cfg: dict[str, Any],
    ) -> tuple[list[Proposal], dict[str, str]]:
        accepted: list[Proposal] = []
        audit: dict[str, str] = {}
        positions = [dict(p) for p in occupied]
        gross = sum(float(p["notional"]) for p in positions)
        risk = sum(float(p.get("risk", 0.0)) for p in positions)
        sectors: dict[str, float] = {}
        for p in positions:
            sectors[p["sector"]] = sectors.get(p["sector"], 0.0) + float(p["notional"])
        symbols = {p["symbol"] for p in positions}
        for p in sorted(proposals, key=lambda x: x.score, reverse=True):
            if p.symbol in symbols:
                audit[p.symbol] = "veto: already held"
                continue
            if len(positions) >= min(cfg["max_open_positions"], cfg["max_positions_hard"]):
                audit[p.symbol] = "veto: position-count ceiling"
                continue
            if gross + p.notional > equity * cfg["max_gross_exposure_pct"] + 1e-6:
                audit[p.symbol] = "veto: gross-exposure ceiling"
                continue
            if sectors.get(p.sector, 0.0) + p.notional > equity * cfg["max_sector_exposure_pct"] + 1e-6:
                audit[p.symbol] = "veto: sector-exposure ceiling"
                continue
            proposed_risk = p.quantity * p.stressed_loss_per_share
            if risk + proposed_risk > equity * cfg["max_open_risk_pct"] + 1e-6:
                audit[p.symbol] = "veto: aggregate open-risk ceiling"
                continue
            p.agent_trace = [
                "DataStewardAgent: point-in-time data passed",
                "SetupResearchAgent: setup rule matched",
                "RiskGateAgent: stop, size and currency risk passed",
                "PortfolioGovernorAgent: portfolio budgets reserved",
                "AuditAgent: proposal emitted; execution authority absent",
            ]
            accepted.append(p)
            audit[p.symbol] = "accepted: proposal only"
            symbols.add(p.symbol)
            positions.append({"symbol": p.symbol, "notional": p.notional, "sector": p.sector, "risk": proposed_risk})
            gross += p.notional
            risk += proposed_risk
            sectors[p.sector] = sectors.get(p.sector, 0.0) + p.notional
        return accepted, audit

class AgenticResearchDesk:
    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.data_agent = DataStewardAgent()
        self.setup_agent = SetupResearchAgent()
        self.risk_agent = RiskGateAgent()
        self.governor = PortfolioGovernorAgent()

    def scan(
        self, date: str, daily: pd.DataFrame, intraday: pd.DataFrame,
        events: pd.DataFrame, universe: pd.DataFrame, equity: float,
        occupied: list[dict[str, Any]] | None = None,
    ) -> tuple[list[Proposal], dict[str, str], list[str]]:
        trace = self.data_agent.run(date, daily, intraday)
        occupied = occupied or []
        raw = self.setup_agent.run(
            date, daily, intraday, events, universe, self.cfg, equity, occupied
        )
        risk_passed: list[Proposal] = []
        audit: dict[str, str] = {}
        for p in raw:
            ok, why = self.risk_agent.accepts(p, equity, self.cfg)
            if ok:
                risk_passed.append(p)
            else:
                audit[p.symbol] = f"veto: {why}"
        accepted, portfolio_audit = self.governor.run(
            risk_passed, occupied, equity, self.cfg
        )
        audit.update(portfolio_audit)
        trace.extend([
            f"SetupResearchAgent: {len(raw)} raw candidate proposals",
            f"RiskGateAgent: {len(risk_passed)} passed independent risk review",
            f"PortfolioGovernorAgent: {len(accepted)} fit remaining portfolio budgets",
            "AuditAgent: CSV/JSON records written; no broker action is available",
        ])
        return accepted, audit, trace

def _fill_price(price: float, side: int, is_entry: bool, cfg: dict[str, Any]) -> float:
    direction = side if is_entry else -side
    bps = float(cfg["slippage_bps"])
    return price * (1 + direction * bps / 10_000)

def _equity(cash: float, positions: list[Position], marks: dict[str, float]) -> float:
    return cash + sum(p.side * p.quantity * marks.get(p.symbol, p.entry) for p in positions)

def _close_position(
    pos: Position, qty: int, raw_price: float, date: str, reason: str,
    cash: float, trades: list[dict[str, Any]], cfg: dict[str, Any]
) -> float:
    qty = min(qty, pos.quantity)
    exit_price = _fill_price(raw_price, pos.side, False, cfg)
    exit_fees = raw_price * qty * float(cfg["commission_bps"]) / 10_000
    entry_fees = pos.entry * qty * float(cfg["commission_bps"]) / 10_000
    pnl = pos.side * (exit_price - pos.entry) * qty - entry_fees - exit_fees
    cash += pos.side * qty * exit_price
    cash -= exit_fees
    trades.append({
        "date": date, "symbol": pos.symbol, "setup": pos.setup, "side": pos.side,
        "quantity": qty, "entry": pos.entry, "exit": exit_price, "pnl": pnl,
        "r_multiple": pnl / max(pos.initial_risk_per_share * qty, 0.0001),
        "initial_risk_dollars": pos.initial_risk_per_share * qty,
        "mfe_R": pos.mfe_per_share / max(pos.initial_risk_per_share, 0.0001),
        "mae_R": pos.mae_per_share / max(pos.initial_risk_per_share, 0.0001),
        "reason": reason, "entry_date": pos.entry_date,
    })
    pos.quantity -= qty
    return cash

def _observe_excursion(pos: Position, high: float, low: float) -> None:
    if pos.side == 1:
        pos.mfe_per_share = max(pos.mfe_per_share, high - pos.entry)
        pos.mae_per_share = max(pos.mae_per_share, pos.entry - low)
    else:
        pos.mfe_per_share = max(pos.mfe_per_share, pos.entry - low)
        pos.mae_per_share = max(pos.mae_per_share, high - pos.entry)

def _prior_parabolic_target(hist: pd.DataFrame) -> float | None:
    completed = hist.sort_values("date").close.astype(float).to_numpy()[:-1]
    if len(completed) < 20:
        return None
    return max(sma(completed, 10), sma(completed, 20))

def backtest(
    daily: pd.DataFrame, intraday: pd.DataFrame, events: pd.DataFrame,
    universe: pd.DataFrame, cfg: dict[str, Any],
    start_date: str | None = None, end_date: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if intraday.empty:
        raise ValueError("backtest requires intraday data to model opening-range triggers")
    cash = float(cfg["initial_cash"])
    desk = AgenticResearchDesk(cfg)
    positions: list[Position] = []
    trades: list[dict[str, Any]] = []
    curves: list[dict[str, Any]] = []
    dates = sorted(set(daily.date) & set(intraday.date))
    peak = cash
    previous_equity = cash
    for day_index, date in enumerate(dates):
        if start_date and date < start_date:
            continue
        if end_date and date > end_date:
            break
        day_bars = daily[daily.date == date].set_index("symbol")
        opens = day_bars.open.astype(float).to_dict()
        lows = day_bars.low.astype(float).to_dict()
        highs = day_bars.high.astype(float).to_dict()
        closes = day_bars.close.astype(float).to_dict()
        # FIX 1: sizing equity uses open marks (known at session start), never today's close
        equity_for_sizing = _equity(cash, positions, opens)
        survivors: list[Position] = []
        for pos in positions:
            if pos.pending_exit and pos.symbol in opens:
                cash = _close_position(pos, pos.quantity, opens[pos.symbol], date, "close_below_trailing_MA", cash, trades, cfg)
            else:
                survivors.append(pos)
        positions = survivors

        for pos in list(positions):
            bars = intraday[(intraday.symbol == pos.symbol) & (intraday.date == date)].sort_values("minute_from_open")
            if bars.empty:
                continue
            stopped = None
            for _, b in bars.iterrows():
                _observe_excursion(pos, float(b.high), float(b.low))
                if pos.side == 1 and b.low <= pos.stop:
                    raw = min(float(b.open), pos.stop)
                    stopped = raw
                    break
                if pos.side == -1 and b.high >= pos.stop:
                    raw = max(float(b.open), pos.stop)
                    stopped = raw
                    break
            if stopped is not None:
                cash = _close_position(pos, pos.quantity, stopped, date, "hard_stop", cash, trades, cfg)
                positions.remove(pos)

        # Daily loss lock still uses close for end-of-day accounting only
        current_equity_eod = _equity(cash, positions, closes)
        peak = max(peak, current_equity_eod)
        day_loss = (current_equity_eod / max(previous_equity, 1)) - 1
        if day_loss <= -float(cfg["max_daily_loss_pct"]):
            for pos in list(positions):
                raw = closes.get(pos.symbol, pos.entry)
                cash = _close_position(pos, pos.quantity, raw, date, "desk_eod_loss_lock", cash, trades, cfg)
            positions = []

        occupied = [
            {
                "symbol": p.symbol,
                "notional": p.quantity * opens.get(p.symbol, p.entry),  # open mark
                "sector": p.sector,
                "risk": p.quantity * (
                    abs(p.entry - p.stop) + p.gap_buffer_per_share
                    + p.entry * 2 * (float(cfg["slippage_bps"]) + float(cfg["commission_bps"])) / 10_000
                ),
            }
            for p in positions
        ]
        proposals, _, _ = desk.scan(
            date, daily, intraday, events, universe, max(equity_for_sizing, 1), occupied
        )
        for prop in proposals:
            if len(positions) >= min(int(cfg["max_open_positions"]), int(cfg["max_positions_hard"])):
                break
            if any(p.symbol == prop.symbol for p in positions):
                continue
            gross = sum(p.quantity * opens.get(p.symbol, p.entry) for p in positions)
            if gross + prop.notional > equity_for_sizing * float(cfg["max_gross_exposure_pct"]):
                continue
            entry = _fill_price(prop.entry, prop.side, True, cfg)
            qty = prop.quantity
            entry_minute = int(prop.trigger_time.split("+")[-1])
            pos = Position(
                symbol=prop.symbol, setup=prop.setup, side=prop.side, quantity=qty,
                entry=entry, stop=prop.stop, entry_date=date, entry_index=day_index,
                sector=prop.sector, initial_risk_per_share=abs(entry - prop.stop),
                entry_minute=entry_minute,
                gap_buffer_per_share=prop.gap_buffer_pct * entry,
                trail_ma=int(cfg["trail_default_ma"]),
            )
            entry_fee = entry * qty * float(cfg["commission_bps"]) / 10_000
            cash -= prop.side * qty * entry
            cash -= entry_fee
            bars = intraday[(intraday.symbol == prop.symbol) & (intraday.date == date)].sort_values("minute_from_open")
            signal_bars = bars[bars.minute_from_open == entry_minute]
            same_bar_stop = None
            if not signal_bars.empty:
                signal_bar = signal_bars.iloc[0]
                if prop.side == 1 and float(signal_bar.low) <= pos.stop:
                    same_bar_stop = min(float(signal_bar.open), pos.stop)
                elif prop.side == -1 and float(signal_bar.high) >= pos.stop:
                    same_bar_stop = max(float(signal_bar.open), pos.stop)
            bars_after = bars[bars.minute_from_open > entry_minute]
            stopped = same_bar_stop
            for _, b in bars_after.iterrows():
                if stopped is not None:
                    break
                _observe_excursion(pos, float(b.high), float(b.low))
                if prop.side == 1 and b.low <= pos.stop:
                    stopped = min(float(b.open), pos.stop)
                    break
                if prop.side == -1 and b.high >= pos.stop:
                    stopped = max(float(b.open), pos.stop)
                    break
            if stopped is not None:
                cash = _close_position(pos, pos.quantity, stopped, date, "same_session_hard_stop", cash, trades, cfg)
            else:
                positions.append(pos)

        for pos in list(positions):
            hist = daily[(daily.symbol == pos.symbol) & (daily.date <= date)].sort_values("date")
            if pos.symbol not in closes or len(hist) < 20:
                continue
            held = day_index - pos.entry_index + 1
            close = float(closes[pos.symbol])
            if held >= int(cfg["scale_days"]) and not pos.scaled and pos.side * (close - pos.entry) > 0:
                trim = max(1, int(math.floor(pos.quantity * float(cfg["scale_fraction"]))))
                cash = _close_position(pos, trim, close, date, "scale_after_strength", cash, trades, cfg)
                pos.scaled = True
                if pos.quantity == 0:
                    positions.remove(pos)
                    continue
                if pos.side == 1:
                    pos.stop = max(pos.stop, pos.entry)
                else:
                    pos.stop = min(pos.stop, pos.entry)
            c = hist.close.astype(float).to_numpy()
            ma10, ma20 = sma(c, 10), sma(c, 20)
            atr_abs = float(stock_features(hist.iloc[:-1], cfg).get("atr_pct", 0.0)) * close if len(hist) > 128 else 0
            extended = (pos.side == 1 and close - ma10 > cfg["extension_threshold_atr"] * max(atr_abs, 0.01))
            pos.trail_ma = int(cfg["trail_extended_ma"] if extended else cfg["trail_default_ma"])
            ma = ma20 if pos.trail_ma == 20 else ma10
            if held >= 3 and pos.side * (close - ma) < 0:
                pos.pending_exit = True
            # FIX (Midna 2026-10-10): short MA target may only be touched by
            # POST-ENTRY bars. On the entry day that means bars after the
            # entry minute; on later days every bar is post-entry. A pre-entry
            # low touching the target must not close a later short.
            if pos.side == -1:
                target = _prior_parabolic_target(hist)
                if target is None:
                    continue
                bars = intraday[(intraday.symbol == pos.symbol) & (intraday.date == date)].sort_values("minute_from_open")
                if date > pos.entry_date:
                    post_entry = bars
                else:
                    post_entry = bars[bars.minute_from_open > pos.entry_minute]
                if not post_entry.empty and float(post_entry.low.min()) <= target:
                    raw = min(float(opens.get(pos.symbol, target)), target)
                    cash = _close_position(pos, pos.quantity, raw, date, "parabolic_MA_target", cash, trades, cfg)
                    positions.remove(pos)

        marks = _equity(cash, positions, closes)
        peak = max(peak, marks)
        curves.append({
            "date": date, "equity": marks, "cash": cash,
            "gross_exposure": sum(p.quantity * closes.get(p.symbol, p.entry) for p in positions),
            "open_positions": len(positions), "drawdown": marks / peak - 1 if peak else 0,
            "market_state": market_state(daily, date, cfg["market_proxy"])[0],
        })
        previous_equity = marks
    return pd.DataFrame(trades), pd.DataFrame(curves)
def summary_metrics(trades: pd.DataFrame, curve: pd.DataFrame) -> dict[str, Any]:
    if curve.empty:
        return {"trades": 0, "note": "no backtest sessions"}
    returns = curve.equity.pct_change().dropna()
    pnl = trades.pnl.astype(float) if not trades.empty else pd.Series(dtype=float)
    if not trades.empty:
        round_trips = trades.groupby(["symbol", "entry_date", "setup", "side"], as_index=False).agg(
            pnl=("pnl", "sum"),
            initial_risk_dollars=("initial_risk_dollars", "sum"),
            mfe_R=("mfe_R", "max"),
            mae_R=("mae_R", "max"),
        )
        round_trips["r_multiple"] = round_trips.pnl / round_trips.initial_risk_dollars.clip(lower=0.0001)
    else:
        round_trips = pd.DataFrame(columns=["pnl", "r_multiple", "mfe_R", "mae_R"])
    winners = round_trips[round_trips.pnl > 0]
    losers = round_trips[round_trips.pnl <= 0]
    years = max((pd.to_datetime(curve.date.iloc[-1]) - pd.to_datetime(curve.date.iloc[0])).days / 365.25, 1 / 252)
    start, end = float(curve.equity.iloc[0]), float(curve.equity.iloc[-1])
    sharpe = float(returns.mean() / returns.std(ddof=1) * math.sqrt(252)) if len(returns) > 1 and returns.std(ddof=1) > 0 else 0.0
    return {
        "sessions": int(len(curve)),
        "trade_legs": int(len(trades)),
        "round_trips": int(len(round_trips)),
        "net_pnl": float(pnl.sum()) if len(pnl) else 0.0,
        "ending_equity": end,
        "cagr": float((end / start) ** (1 / years) - 1) if end > 0 else -1.0,
        "max_drawdown": float(curve.drawdown.min()),
        "daily_sharpe_annualized_cost_adjusted": sharpe,
        "win_rate_by_round_trip": float((round_trips.pnl > 0).mean()) if len(round_trips) else 0.0,
        "average_winner": float(winners.pnl.mean()) if len(winners) else 0.0,
        "average_loser": float(losers.pnl.mean()) if len(losers) else 0.0,
        "profit_factor": float(winners.pnl.sum() / abs(losers.pnl.sum())) if len(losers) and losers.pnl.sum() else None,
        "largest_winner_share_of_gross_wins": float(winners.pnl.max() / winners.pnl.sum()) if len(winners) and winners.pnl.sum() > 0 else 0.0,
        "mean_R_per_round_trip": float(round_trips.r_multiple.mean()) if len(round_trips) else 0.0,
        "mean_MFE_R": float(round_trips.mfe_R.mean()) if len(round_trips) else 0.0,
        "mean_MAE_R": float(round_trips.mae_R.mean()) if len(round_trips) else 0.0,
        "open_positions_at_end": int(curve.open_positions.iloc[-1]),
        "methodology": "point-in-time inputs; open-mark sizing; opening-range intraday fills; fee/slippage haircut; no live performance claim",
    }

def write_scan(date: str, daily: pd.DataFrame, intraday: pd.DataFrame, events: pd.DataFrame,
               universe: pd.DataFrame, cfg: dict[str, Any], out: str) -> None:
    props, audit, trace = AgenticResearchDesk(cfg).scan(
        date, daily, intraday, events, universe, float(cfg["initial_cash"])
    )
    records = [asdict(x) for x in props]
    Path(out).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(Path(out) / "proposals.csv", index=False)
    with open(Path(out) / "proposals.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    with open(Path(out) / "agent_audit.json", "w", encoding="utf-8") as f:
        json.dump({"as_of": date, "pipeline": trace, "decisions": audit}, f, indent=2)
    print(json.dumps({
        "as_of": date, "proposal_count": len(records), "audit": audit,
        "agent_pipeline": trace, "output": out,
    }, indent=2))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "backtest"):
        p = sub.add_parser(name)
        p.add_argument("--daily", required=True)
        p.add_argument("--intraday", required=True)
        p.add_argument("--events")
        p.add_argument("--universe")
        p.add_argument("--config")
        p.add_argument("--out", required=True)
        if name == "scan":
            p.add_argument("--date", required=True)
        else:
            p.add_argument("--start", help="first session eligible for new trades")
            p.add_argument("--end", help="last session included")
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        daily, intraday, events, universe = load_inputs(
            args.daily, args.intraday, args.events, args.universe
        )
        Path(args.out).mkdir(parents=True, exist_ok=True)
        if args.command == "scan":
            write_scan(args.date, daily, intraday, events, universe, cfg, args.out)
        else:
            trades, curve = backtest(
                daily, intraday, events, universe, cfg,
                getattr(args, "start", None), getattr(args, "end", None),
            )
            trades.to_csv(Path(args.out) / "trades.csv", index=False)
            curve.to_csv(Path(args.out) / "equity_curve.csv", index=False)
            report = summary_metrics(trades, curve)
            with open(Path(args.out) / "metrics.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(json.dumps(report, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
