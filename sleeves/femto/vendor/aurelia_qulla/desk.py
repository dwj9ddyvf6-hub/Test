#!/usr/bin/env python3
"""Qullamaggie-style research desk: point-in-time scans, proposals and event-driven backtests.

The engine is intentionally deterministic. It transforms user-supplied, point-in-time
OHLCV/event data into auditable proposals and backtest ledgers. It has no brokerage
connectivity or order-routing code.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


DEFAULTS: dict[str, Any] = {
    "market_proxy": "QQQ",
    "market_filter": "hard",                  # 10SMA > 20SMA and both rising
    "leader_percentile": 0.98,                 # top 1-2% in any 1/3/6 month horizon
    "base_window": 10,                         # post-2026 book summary: ~1-3 weeks
    "base_range_max_pct": 0.28,                 # inference; parameter for robustness tests
    "tightening_ratio_max": 1.00,               # late-half width / early-half width
    "higher_low_slope_min": 0.0,
    "prior_impulse_min_pct": 0.30,              # 30%+ prior 1-3 month move
    "opening_range_minutes": 5,
    "entry_fill_policy": "next_trade_open",     # manual alert workflow; OHLCV latency proxy
    "adr_period": 20,
    "max_stop_atr": 1.00,                       # skip if structural stop > 1 daily ATR
    "overnight_gap_quantile": 0.95,
    "risk_per_trade_pct": 0.0035,               # desk research default, 0.35% of equity
    "risk_per_trade_pct_max": 0.0050,
    "max_position_notional_pct": 0.20,          # conservative end of 20-25% public range
    "max_gross_exposure_pct": 1.00,
    "max_open_positions": 15,
    "max_positions_hard": 20,
    "max_sector_exposure_pct": 0.25,             # desk guardrail; inferred
    "max_open_risk_pct": 0.04,                   # desk guardrail; inferred
    "max_participation_adv": 0.01,                # capacity proxy; inferred
    "min_average_dollar_volume": 5_000_000,
    "slippage_bps": 10,
    "commission_bps": 1,
    "ep_min_gap_pct": 0.10,
    "ep_min_first20_adv": 0.50,                  # inferred confirmation threshold
    "ep_quiet_126d_max_return": 0.30,
    "ep_require_verified_news": True,
    "scale_days": 3,
    "scale_fraction": 1 / 3,
    "trail_default_ma": 10,
    "trail_extended_ma": 20,
    "extension_threshold_atr": 1.50,             # inferred choice between 10/20DMA
    "parabolic_small_cap_threshold": 300_000_000,
    "parabolic_small_cap_runup_pct": 3.00,       # +300% in the prior 3-4 sessions
    "parabolic_large_cap_runup_pct": 0.50,       # +50% over a short accelerating run
    "parabolic_up_days_min": 3,
    "parabolic_borrow_required": True,
    "risk_off_long_multiplier": 0.00,
    "caution_long_multiplier": 0.50,
    "max_daily_loss_pct": 0.015,                 # desk containment; not attributed to K
    "initial_cash": 100_000,
}


DAILY_REQUIRED = {"date", "symbol", "open", "high", "low", "close", "volume"}
INTRADAY_REQUIRED = {
    "date", "symbol", "minute_from_open", "open", "high", "low", "close", "volume",
    "bar_status", "expected_last_minute",
}
EVENT_REQUIRED = {"date", "symbol", "event_type", "news_verified", "public_timestamp", "source_url"}
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
    security_id: str
    reasons: list[str]
    evidence_grade: str = "public rules + explicit implementation hypotheses"
    agent_trace: list[str] | None = None
    evidence_sources: list[str] | None = None
    borrow_fee_bps: float = 0.0
    borrow_timestamp: str | None = None


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
    gap_buffer_per_share: float = 0.0
    scaled: bool = False
    pending_exit: bool = False
    trail_ma: int = 10
    mfe_per_share: float = 0.0
    mae_per_share: float = 0.0
    entry_minute: int = 0
    security_id: str = ""
    borrow_fee_bps: float = 0.0
    accrued_borrow_cost: float = 0.0


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
    for df, label in ((daily, "daily"),):
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
        intraday["expected_last_minute"] = pd.to_numeric(
            intraday["expected_last_minute"], errors="raise"
        ).astype(int)
        intraday["bar_status"] = intraday.bar_status.astype(str).str.upper().str.strip()
        if not intraday.bar_status.isin({"TRADE", "NO_TRADE", "HALT"}).all():
            raise ValueError("intraday bar_status must be TRADE, NO_TRADE, or HALT")
        traded = intraday.bar_status == "TRADE"
        for c in ("open", "high", "low", "close", "volume"):
            intraday[c] = pd.to_numeric(intraday[c], errors="coerce")
        if intraday.loc[traded, ["open", "high", "low", "close", "volume"]].isna().any().any():
            raise ValueError("TRADE rows require finite OHLCV values")
        if (intraday.loc[traded, ["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError("intraday prices must be positive on TRADE rows")
        if (intraday.loc[traded, "volume"] <= 0).any():
            raise ValueError("TRADE rows require positive volume")
        quiet = ~traded
        if intraday.loc[quiet, ["open", "high", "low", "close"]].notna().any().any():
            raise ValueError("NO_TRADE/HALT rows must not contain forward-filled OHLC prices")
        if intraday.loc[quiet, "volume"].fillna(0).ne(0).any():
            raise ValueError("NO_TRADE/HALT rows must have zero or missing volume")
        if (intraday.expected_last_minute < intraday.minute_from_open).any():
            raise ValueError("expected_last_minute cannot precede an observed minute")
        for (date, symbol), group in intraday.groupby(["date", "symbol"], sort=False):
            _validate_intraday_group(group, str(symbol), str(date))
        intraday = intraday.sort_values(["date", "symbol", "minute_from_open"])
    daily = daily.sort_values(["date", "symbol"]).reset_index(drop=True)
    if not universe.empty:
        universe["symbol"] = universe["symbol"].astype(str).str.upper().str.strip()
        if "valid_from" in universe:
            universe["valid_from"] = pd.to_datetime(universe["valid_from"], errors="raise").dt.strftime("%Y-%m-%d")
        if "valid_to" in universe:
            universe["valid_to"] = pd.to_datetime(universe["valid_to"], errors="coerce").dt.strftime("%Y-%m-%d")
    if not events.empty:
        events["public_timestamp"] = pd.to_datetime(events.public_timestamp, errors="coerce", utc=True)
    daily = _attach_security_ids(daily, universe)
    intraday = _attach_security_ids(intraday, universe)
    events = _attach_security_ids(events, universe)
    return daily, intraday, events, universe


def _attach_security_ids(frame: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    """Map each dated ticker alias to its point-in-time permanent security ID."""
    out = frame.copy()
    if out.empty:
        out["security_id"] = pd.Series(dtype=str)
        return out
    out["security_id"] = out.symbol.astype(str)
    if universe.empty or not {"symbol", "security_id", "valid_from"}.issubset(universe.columns):
        return out
    for symbol, ix in out.groupby("symbol", sort=False).groups.items():
        records = universe[universe.symbol == symbol].copy()
        if records.empty:
            continue
        records["valid_from"] = pd.to_datetime(records.valid_from, errors="coerce").dt.strftime("%Y-%m-%d")
        if "valid_to" in records:
            records["valid_to"] = pd.to_datetime(records.valid_to, errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            records["valid_to"] = None
        records = records.dropna(subset=["valid_from"]).sort_values("valid_from")
        starts = records.valid_from.tolist()
        ends = records.valid_to.tolist()
        ids = records.security_id.astype(str).tolist()
        for row_ix in ix:
            row_date = str(out.at[row_ix, "date"])
            j = int(np.searchsorted(starts, row_date, side="right") - 1)
            if j >= 0 and (pd.isna(ends[j]) or ends[j] >= row_date):
                out.at[row_ix, "security_id"] = ids[j]
    return out


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
    borrow_qty_cap: int | None = None,
) -> int:
    """Risk-first integer share sizing; returns 0 when any hard limit binds."""
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
    limits = [q_risk, q_position, q_gross, q_sector, q_capacity, q_total_risk]
    if borrow_qty_cap is not None:
        limits.append(max(0, int(borrow_qty_cap)))
    return max(0, min(limits))


def market_state(daily: pd.DataFrame, asof_date: str, proxy: str) -> tuple[str, dict[str, float]]:
    """Use the last fully completed proxy session before asof_date."""
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
    """Return best horizon percentile and its horizon; ties are resolved conservatively."""
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
    # Match Kullamägi's published TC2000 definition: mean(H/L) - 1,
    # expressed as a percent. This differs from (H-L)/close and from ATR.
    adr_n = int(cfg["adr_period"])
    adr_pct = mean((high[-adr_n:] / low[-adr_n:]) - 1.0)
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


def _metadata(universe: pd.DataFrame, symbol: str, asof_date: str) -> dict[str, Any]:
    """Return only security metadata whose effective interval covers asof_date.

    Static symbol-only rows are deliberately not treated as historical truth. They
    may still identify the symbol, but cannot authorize a market-cap bucket,
    sector constraint, or borrow decision in a historical replay.
    """
    default = {
        "sector": "UNKNOWN", "market_cap": float("nan"), "borrowable": False,
        "security_id": symbol, "metadata_valid": False,
    }
    if universe.empty or "symbol" not in universe or "valid_from" not in universe:
        return default
    r = universe[universe.symbol == symbol].copy()
    if r.empty:
        return default
    r["valid_from"] = pd.to_datetime(r["valid_from"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "valid_to" not in r:
        r["valid_to"] = None
    r["valid_to"] = pd.to_datetime(r["valid_to"], errors="coerce").dt.strftime("%Y-%m-%d")
    valid = r[(r.valid_from <= asof_date) & (r.valid_to.isna() | (r.valid_to >= asof_date))]
    if valid.empty:
        return default
    row = valid.sort_values("valid_from").iloc[-1].to_dict()
    row.setdefault("sector", "UNKNOWN")
    row.setdefault("market_cap", float("nan"))
    row.setdefault("borrowable", False)
    if not row.get("security_id") or pd.isna(row.get("security_id")):
        row["security_id"] = symbol
    row["metadata_valid"] = True
    if isinstance(row.get("borrowable"), str):
        row["borrowable"] = row["borrowable"].strip().lower() in {"1", "true", "yes", "y"}
    return row


def _session_timestamp(date: str, minute_from_open: int = 0) -> pd.Timestamp:
    """Start-labelled U.S. regular-session minute in UTC (09:30 America/New_York)."""
    local = pd.Timestamp(date).tz_localize(ZoneInfo("America/New_York"))
    return (local + pd.Timedelta(minutes=570 + int(minute_from_open))).tz_convert("UTC")


def _borrow_snapshot(meta: dict[str, Any], decision_timestamp: pd.Timestamp) -> dict[str, Any] | None:
    """Only accept a confirmed, sized locate quote timestamped before submission."""
    required = {"borrow_available_at", "borrow_shares", "borrow_fee_bps", "locate_confirmed"}
    if not required.issubset(meta):
        return None
    if str(meta.get("locate_confirmed", "")).strip().lower() not in {"1", "true", "yes", "y"}:
        return None
    ts = pd.to_datetime(meta.get("borrow_available_at"), errors="coerce", utc=True)
    if pd.isna(ts) or ts > decision_timestamp:
        return None
    try:
        shares = int(float(meta.get("borrow_shares")))
        fee = float(meta.get("borrow_fee_bps"))
    except (TypeError, ValueError):
        return None
    if shares <= 0 or not math.isfinite(fee) or fee < 0:
        return None
    return {"borrow_shares": shares, "borrow_fee_bps": fee, "borrow_available_at": ts}


def _resolve_setup_matches(matches: list[tuple[Any, ...]]) -> tuple[Any, ...] | None:
    """Explicit collision policy: emit only an unambiguous, single-family signal."""
    return matches[0] if len(matches) == 1 else None


def _allocate_candidates(
    candidates: list[Proposal], sizing_inputs: dict[str, dict[str, Any]],
    occupied: list[dict[str, Any]], equity: float, cfg: dict[str, Any],
) -> list[Proposal]:
    """Reserve portfolio limits by score and stable security ID, never ticker order."""
    allocated: list[Proposal] = []
    allocation_occupied = [dict(p) for p in occupied]
    gross_used = sum(float(p["notional"]) for p in allocation_occupied)
    risk_used = sum(float(p.get("risk", 0.0)) for p in allocation_occupied)
    sector_used: dict[str, float] = {}
    for p in allocation_occupied:
        sector_used[p["sector"]] = sector_used.get(p["sector"], 0.0) + float(p["notional"])
    symbols = {str(p.get("security_id", p.get("symbol", ""))) for p in allocation_occupied}
    max_positions = min(int(cfg["max_open_positions"]), int(cfg["max_positions_hard"]))
    for p in sorted(candidates, key=lambda x: (-x.score, x.security_id)):
        if p.security_id in symbols or len(allocation_occupied) >= max_positions:
            continue
        limits = sizing_inputs[p.security_id]
        qty = size_position(
            equity, p.entry, p.stop, limits["atr_abs"], p.risk_fraction, cfg,
            side=p.side, average_dollar_volume=limits["average_dollar_volume"],
            gross_remaining=equity * float(cfg["max_gross_exposure_pct"]) - gross_used,
            sector_remaining=equity * float(cfg["max_sector_exposure_pct"]) - sector_used.get(p.sector, 0.0),
            open_risk=risk_used, gap_buffer_abs=limits["gap_buffer_abs"],
            borrow_qty_cap=limits["borrow_qty_cap"],
        )
        risk_dollars = qty * p.stressed_loss_per_share
        if qty < 1 or risk_used + risk_dollars > equity * float(cfg["max_open_risk_pct"]) + 1e-6:
            continue
        p.quantity = qty
        p.notional = qty * p.entry
        allocated.append(p)
        gross_used += p.notional
        risk_used += risk_dollars
        sector_used[p.sector] = sector_used.get(p.sector, 0.0) + p.notional
        allocation_occupied.append({"symbol": p.symbol, "notional": p.notional, "sector": p.sector, "risk": risk_dollars})
        symbols.add(p.security_id)
    return allocated


def _snapshot_occupied(
    positions: list[Position], marks: dict[str, float], cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    """Freeze open-session exposure before any intraday exits can release budget."""
    out = []
    for p in positions:
        mark = float(marks.get(p.security_id or p.symbol, p.entry))
        friction = p.entry * 2 * (float(cfg["slippage_bps"]) + float(cfg["commission_bps"])) / 10_000
        risk_per_share = abs(p.entry - p.stop) + p.gap_buffer_per_share + friction
        out.append({
            "symbol": p.symbol, "security_id": p.security_id or p.symbol,
            "notional": p.quantity * mark, "sector": p.sector,
            "risk": p.quantity * risk_per_share,
        })
    return out


def _first_intraday_exit(
    bars: pd.DataFrame, side: int, stop: float, target: float | None = None,
    start_minute: int = 0,
) -> tuple[float, str, int] | None:
    """Replay exits in bar order; when stop and target share a bar, assume stop first."""
    if bars.empty:
        return None
    x = bars.copy()
    symbol = str(x.symbol.iloc[0])
    date = str(x.date.iloc[0])
    x = _validate_intraday_group(x, symbol, date)
    x = x[x.bar_status == "TRADE"]
    for _, bar in x[x.minute_from_open >= int(start_minute)].iterrows():
        op, hi, lo = float(bar.open), float(bar.high), float(bar.low)
        stop_hit = lo <= stop if side == 1 else hi >= stop
        target_hit = target is not None and (hi >= target if side == 1 else lo <= target)
        if stop_hit:
            fill = min(op, stop) if side == 1 else max(op, stop)
            return fill, "hard_stop", int(bar.minute_from_open)
        if target_hit:
            fill = max(op, target) if side == 1 else min(op, target)
            return fill, "parabolic_MA_target", int(bar.minute_from_open)
    return None


def _validate_intraday_group(frame: pd.DataFrame, symbol: str, date: str) -> pd.DataFrame:
    """Require explicit, complete start-labelled minute coverage from 09:30 ET.

    NO_TRADE rows are explicit empty exchange minutes, never forward-filled bars.
    The expected last minute comes from the session-calendar coverage manifest.
    """
    x = frame[(frame.symbol == symbol) & (frame.date == date)].copy()
    if x.empty:
        return x
    mins = pd.to_numeric(x.minute_from_open, errors="raise").astype(int).tolist()
    if "expected_last_minute" in x:
        ends = pd.to_numeric(x.expected_last_minute, errors="raise").astype(int).unique()
        if len(ends) != 1:
            raise ValueError(f"intraday session-end declaration varies for {symbol} {date}")
        expected_last = int(ends[0])
    else:
        # Direct helper calls without a manifest can detect internal holes only.
        expected_last = max(mins)
    if mins != list(range(expected_last + 1)):
        raise ValueError(
            f"intraday coverage for {symbol} {date} must be unique, ordered, and complete through minute {expected_last}"
        )
    if "bar_status" not in x:
        x["bar_status"] = "TRADE"
    else:
        x["bar_status"] = x.bar_status.astype(str).str.upper().str.strip()
    if not x.bar_status.isin({"TRADE", "NO_TRADE", "HALT"}).all():
        raise ValueError("intraday bar_status must be TRADE, NO_TRADE, or HALT")
    trade = x.bar_status == "TRADE"
    if x.loc[trade, ["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError(f"TRADE rows require finite OHLCV values for {symbol} {date}")
    if (x.loc[trade, "high"] < x.loc[trade, ["open", "close", "low"]].max(axis=1)).any() or (x.loc[trade, "low"] > x.loc[trade, ["open", "close", "high"]].min(axis=1)).any():
        raise ValueError(f"invalid OHLC envelope for {symbol} {date}")
    quiet = ~trade
    if x.loc[quiet, ["open", "high", "low", "close"]].notna().any().any():
        raise ValueError(f"NO_TRADE/HALT rows cannot carry forward-filled prices for {symbol} {date}")
    if x.loc[quiet, "volume"].fillna(0).ne(0).any():
        raise ValueError(f"NO_TRADE/HALT rows must have zero or missing volume for {symbol} {date}")
    return x


def _intraday_trigger(
    intraday: pd.DataFrame,
    symbol: str,
    date: str,
    minutes: int,
    side: int,
    level: float | None = None,
    earliest_minute: int | None = None,
    entry_fill_policy: str = "next_trade_open",
) -> dict[str, Any] | None:
    x = _validate_intraday_group(intraday, symbol, date)
    if x.empty:
        return None
    expected_last = int(x.expected_last_minute.iloc[0]) if "expected_last_minute" in x else int(x.minute_from_open.max())
    if expected_last < minutes:
        return None
    x = x[x.bar_status == "TRADE"].copy()
    if x.empty:
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
        if entry_fill_policy not in {"next_trade_open", "signal_bar_trigger"}:
            raise ValueError(f"unsupported long entry_fill_policy: {entry_fill_policy}")
        trigger = max(or_high, float(level or 0))
        after_rows = list(after.iterrows())
        for i, (idx, row) in enumerate(after_rows):
            if earliest_minute is not None and int(row.minute_from_open) < earliest_minute:
                pre_low = min(pre_low, float(row.low))
                pre_high = max(pre_high, float(row.high))
                continue
            if row.high >= trigger:
                pre_low = min(pre_low, float(row.low))
                pre_high = max(pre_high, float(row.high))
                if entry_fill_policy == "signal_bar_trigger":
                    fill_idx, fill_row = idx, row
                    entry = max(trigger, float(row.open))
                else:
                    # Kullamägi explicitly answered that he does not use buy-stop
                    # orders. With minute OHLC data, model a human-observed trigger
                    # with a marketable order at the next eligible trade bar's open.
                    # If price has fallen back below the trigger by then, skip it.
                    if i + 1 >= len(after_rows):
                        continue
                    fill_idx, fill_row = after_rows[i + 1]
                    entry = float(fill_row.open)
                    if entry < trigger:
                        continue
                return {
                    "entry": entry,
                    "stop": pre_low,
                    "minute": int(fill_row.minute_from_open),
                    "signal_minute": int(row.minute_from_open),
                    "or_high": or_high,
                    "or_low": or_low,
                    "vwap": float(fill_row.cum_vwap),
                    "signal_bar_low": float(row.low),
                    "signal_bar_high": float(row.high),
                    "bars_through_entry": x.loc[:fill_idx],
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
        # A parabolic short requires a break of the opening range, plus price below
        # contemporaneous VWAP. Fill at the next bar's open, after confirmation.
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


def _event_for(
    events: pd.DataFrame, security_id: str, decision_timestamp: str | pd.Timestamp,
    max_age_hours: float = 36.0,
) -> pd.Series | None:
    """Latest sourced public catalyst available by the decision time, within 36h."""
    if events.empty or "public_timestamp" not in events or "source_url" not in events:
        return None
    cutoff = pd.Timestamp(decision_timestamp)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    identity_column = "security_id" if "security_id" in events.columns else "symbol"
    rows = events[events[identity_column].astype(str) == str(security_id)].copy()
    rows["public_timestamp"] = pd.to_datetime(rows.public_timestamp, errors="coerce", utc=True)
    rows = rows[rows.public_timestamp.notna() & (rows.public_timestamp <= cutoff)]
    rows = rows[rows.public_timestamp >= cutoff - pd.Timedelta(hours=max_age_hours)]
    rows = rows[rows.source_url.notna() & rows.source_url.astype(str).str.strip().ne("")]
    if rows.empty:
        return None
    return rows.sort_values("public_timestamp").iloc[-1]


def daily_histories(daily: pd.DataFrame, before_date: str) -> dict[str, pd.DataFrame]:
    identity_column = "security_id" if "security_id" in daily.columns else "symbol"
    return {
        str(s): g[g.date < before_date].sort_values("date")
        for s, g in daily.groupby(identity_column)
        if (g.date < before_date).any()
    }


def _eligible_security_ids(universe: pd.DataFrame, asof_date: str) -> set[str]:
    """Point-in-time listed/security-master universe used for cross-sectional ranks."""
    if universe.empty or not {"security_id", "valid_from"}.issubset(universe.columns):
        return set()
    u = universe.copy()
    u["valid_from"] = pd.to_datetime(u.valid_from, errors="coerce").dt.strftime("%Y-%m-%d")
    if "valid_to" not in u:
        u["valid_to"] = None
    u["valid_to"] = pd.to_datetime(u.valid_to, errors="coerce").dt.strftime("%Y-%m-%d")
    active = u[(u.valid_from <= asof_date) & (u.valid_to.isna() | (u.valid_to >= asof_date))]
    return set(active.security_id.dropna().astype(str))


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
    id_column = "security_id" if "security_id" in daily.columns else "symbol"
    proxy_ids = set(daily.loc[daily.symbol == cfg["market_proxy"], id_column].astype(str))
    eligible_ids = _eligible_security_ids(universe, date)
    rank_histories = {
        s: h for s, h in histories.items()
        if str(s) in eligible_ids and str(s) not in proxy_ids
    }
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
    # Copy the portfolio snapshot: scan-time budget reservations must not mutate
    # the caller's live/backtest position state.
    occupied = [dict(p) for p in (occupied or [])]
    occ_gross = sum(float(p["notional"]) for p in occupied)
    open_risk = sum(float(p.get("risk", 0.0)) for p in occupied)
    sector_gross: dict[str, float] = {}
    for p in occupied:
        sector_gross[p["sector"]] = sector_gross.get(p["sector"], 0.0) + float(p["notional"])

    props: list[Proposal] = []
    sizing_inputs: dict[str, dict[str, Any]] = {}
    today = intraday[intraday.date == date] if not intraday.empty else intraday
    if today.empty:
        return props
    for symbol in sorted(today.symbol.unique()):
        if symbol == cfg["market_proxy"]:
            continue
        meta = _metadata(universe, symbol, date)
        if not meta.get("metadata_valid") or not meta.get("security_id"):
            continue
        security_id = str(meta.get("security_id", symbol))
        hist = histories.get(security_id)
        if hist is None or hist.empty:
            continue
        f = stock_features(hist, cfg)
        if not f.get("ready"):
            continue
        sector = str(meta.get("sector", "UNKNOWN"))
        avg_dollar_volume = f["adv20"]
        if avg_dollar_volume < cfg["min_average_dollar_volume"]:
            continue
        leader_pct, leader_horizon = ranks.get(security_id, (0.0, 0))
        leader = leader_pct >= cfg["leader_percentile"]
        market_ok = long_allowed
        setup_matches: list[tuple[Any, ...]] = []

        # Breakout: strong prior leg, leader, tight/contracting base, moving-average
        # support. Exact numeric tightness and contraction thresholds are hypotheses.
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
            breakout_trigger = _intraday_trigger(
                intraday, symbol, date, int(cfg["opening_range_minutes"]), 1, f["pivot"],
                entry_fill_policy=str(cfg["entry_fill_policy"]),
            )
            if breakout_trigger:
                breakout_score = 0.35 * leader_pct + 0.25 * min(f["prior_impulse"], 2.0) / 2
                breakout_score += 0.20 * max(0.0, 1 - f["base_tightness"] / cfg["base_range_max_pct"])
                breakout_score += 0.20 * min(f["ma_support"], 1.0)
                breakout_reasons = [
                    f"leader rank {leader_pct:.1%} on {leader_horizon}-session horizon",
                    f"prior impulse {f['prior_impulse']:.1%}; base range {f['base_tightness']:.1%}",
                    f"late/early base-width ratio {f['tightening_ratio']:.2f}",
                    "higher lows and rising 10/20-day averages",
                    "intraday trigger crossed after opening range completed",
                ]
                setup_matches.append(("breakout", 1, breakout_trigger, breakout_score, breakout_reasons, None))

        # Episodic pivot: verified event/news + >=10% gap + large first-20m volume,
        # with a relatively quiet six-month pre-event tape.
        # A gap catalyst must already be public when the regular session opens.
        event = _event_for(events, security_id, _session_timestamp(date, 0))
        if event is not None and market_ok:
            x = today[today.symbol == symbol].sort_values("minute_from_open")
            yday_close = float(hist.close.iloc[-1])
            today_open = daily[(daily[id_column].astype(str) == security_id) & (daily.date == date)]
            if today_open.empty:
                continue
            # The official session open is known at the decision time. The first
            # emitted trade bar may be absent when the opening minute has no print.
            gap_pct = float(today_open.open.iloc[0]) / yday_close - 1
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
                ep_trigger = _intraday_trigger(
                    intraday, symbol, date, int(cfg["opening_range_minutes"]), 1,
                    earliest_minute=20,
                    entry_fill_policy=str(cfg["entry_fill_policy"]),
                )
                if ep_trigger:
                    ep_score = 0.45 * min(gap_pct / 0.25, 1.0) + 0.35 * min(ep_volume / 2.0, 1.0) + 0.20
                    ep_reasons = [
                        f"verified {event['event_type']} catalyst",
                        f"opening gap {gap_pct:.1%}; first-20m volume {ep_volume:.2f}x 20-day ADV",
                        f"prior 126-session return {f['ret126']:.1%}; quiet-tape proxy passed",
                        "opening-range high crossed; entry buys strength",
                    ]
                    setup_matches.append(("episodic_pivot", 1, ep_trigger, ep_score, ep_reasons, None))

        # Parabolic short: short only after a multi-day extreme run, on ORL failure
        # plus a below-VWAP close. The borrower/locate flag is a mandatory input.
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
                borrow = _borrow_snapshot(meta, _session_timestamp(date, int(sh_trigger["minute"])))
                if borrow is not None:
                    short_score = min(f["three_day_runup"] / max(required_run, 0.01), 2.0) / 2
                    short_reasons = [
                        f"{f['consecutive_up_days']} consecutive prior up sessions",
                        f"three-session run {f['three_day_runup']:.1%}",
                        "opening-range low broke with price below session VWAP",
                        "time-stamped locate and fee quote available before submission",
                    ]
                    setup_matches.append(("parabolic_short", -1, sh_trigger, short_score, short_reasons, borrow))

        resolved = _resolve_setup_matches(setup_matches)
        if resolved is None:
            continue
        setup, side, trigger, score, reasons, borrow = resolved
        entry = float(trigger["entry"])
        stop = float(trigger["stop"])
        if (side == 1 and stop >= entry) or (side == -1 and stop <= entry):
            continue
        stop_distance = abs(entry - stop)
        # Later reporting calls this average daily true range (ADTR); the original
        # public setup essay uses ADR/ATR language. We use ATR as the hard gate.
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
        gross_remaining = max(0.0, equity * float(cfg["max_gross_exposure_pct"]) - occ_gross)
        sector_remaining = max(0.0, equity * float(cfg["max_sector_exposure_pct"]) - sector_gross.get(sector, 0))
        gap_buffer_pct = f["gap_tail_long_pct"] if side == 1 else f["gap_tail_short_pct"]
        gap_buffer_abs = gap_buffer_pct * entry
        qty = size_position(
            equity, entry, stop, atr_abs, risk_fraction, cfg, side=side,
            average_dollar_volume=avg_dollar_volume, gross_remaining=gross_remaining,
            sector_remaining=sector_remaining, open_risk=open_risk,
            gap_buffer_abs=gap_buffer_abs,
            borrow_qty_cap=borrow["borrow_shares"] if borrow is not None else None,
        )
        if qty < 1:
            continue
        if len(occupied) >= int(cfg["max_open_positions"]):
            continue
        friction_per_share = entry * 2 * (
            float(cfg["slippage_bps"]) + float(cfg["commission_bps"])
        ) / 10_000
        stressed_loss_per_share = stop_distance + gap_buffer_abs + friction_per_share
        new_risk = qty * stressed_loss_per_share
        if (open_risk + new_risk) / equity > cfg["max_open_risk_pct"]:
            continue
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
                security_id=str(meta.get("security_id", symbol)),
                reasons=reasons,
                evidence_sources=[
                    PUBLIC_RULE_URLS[setup],
                    PUBLIC_RULE_URLS["risk"],
                ] + (
                    [str(event.get("source_url"))]
                    if setup == "episodic_pivot" and event is not None
                    and pd.notna(event.get("source_url")) else []
                ),
            )
        if borrow is not None:
            proposal.borrow_fee_bps = float(borrow["borrow_fee_bps"])
            proposal.borrow_timestamp = borrow["borrow_available_at"].isoformat()
        props.append(proposal)
        sizing_inputs[security_id] = {
            "atr_abs": atr_abs,
            "average_dollar_volume": avg_dollar_volume,
            "gap_buffer_abs": gap_buffer_abs,
            "borrow_qty_cap": borrow["borrow_shares"] if borrow is not None else None,
        }

    return _allocate_candidates(props, sizing_inputs, occupied, equity, cfg)


class DataStewardAgent:
    """Checks the requested decision time and enforces a point-in-time data fence."""
    def run(self, date: str, daily: pd.DataFrame, intraday: pd.DataFrame) -> list[str]:
        if not (daily.date == date).any():
            raise ValueError(f"no daily session for {date}")
        if not (intraday.date == date).any():
            raise ValueError(f"no intraday session for {date}")
        # Candidate histories use strict date < decision date. Current-day daily
        # close/high/low are never available to pre-open candidate selection.
        return [
            "DataStewardAgent: requested session exists",
            "DataStewardAgent: candidate features fenced to completed sessions < decision date",
        ]


class SetupResearchAgent:
    """Runs the transparent breakout, EP and parabolic pattern rules."""
    def run(self, *args: Any, **kwargs: Any) -> list[Proposal]:
        return build_proposals(*args, **kwargs)


class RiskGateAgent:
    """Independent veto pass; it cannot add risk or modify a stop."""
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
    """Applies position, gross, sector and open-risk limits in score order."""
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
        symbols = {str(p.get("security_id", p.get("symbol", ""))) for p in positions}
        for p in sorted(proposals, key=lambda x: x.score, reverse=True):
            if p.security_id in symbols:
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
            symbols.add(p.security_id)
            positions.append({"symbol": p.symbol, "security_id": p.security_id,
                              "notional": p.notional, "sector": p.sector, "risk": proposed_risk})
            gross += p.notional
            risk += proposed_risk
            sectors[p.sector] = sectors.get(p.sector, 0.0) + p.notional
        return accepted, audit


class AgenticResearchDesk:
    """Bounded multi-agent orchestration; all trade decisions remain inspectable rules."""
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
    # side +1 long, -1 short. Entry trades in side direction; exit trades against it.
    direction = side if is_entry else -side
    bps = float(cfg["slippage_bps"])
    return price * (1 + direction * bps / 10_000)


def _equity(cash: float, positions: list[Position], closes: dict[str, float]) -> float:
    return cash + sum(p.side * p.quantity * closes.get(p.security_id or p.symbol, p.entry) for p in positions)


def _close_position(
    pos: Position, qty: int, raw_price: float, date: str, reason: str,
    cash: float, trades: list[dict[str, Any]], cfg: dict[str, Any]
) -> float:
    qty = min(qty, pos.quantity)
    exit_price = _fill_price(raw_price, pos.side, False, cfg)
    exit_fees = raw_price * qty * float(cfg["commission_bps"]) / 10_000
    entry_fees = pos.entry * qty * float(cfg["commission_bps"]) / 10_000
    borrow_cost = pos.accrued_borrow_cost * (qty / max(pos.quantity, 1))
    pnl = pos.side * (exit_price - pos.entry) * qty - entry_fees - exit_fees - borrow_cost
    # Exit action is opposite the position side: selling a long adds cash,
    # covering a short consumes cash.
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
        "borrow_cost": borrow_cost,
    })
    pos.quantity -= qty
    pos.accrued_borrow_cost -= borrow_cost
    return cash


def _observe_excursion(pos: Position, high: float, low: float) -> None:
    if pos.side == 1:
        pos.mfe_per_share = max(pos.mfe_per_share, high - pos.entry)
        pos.mae_per_share = max(pos.mae_per_share, pos.entry - low)
    else:
        pos.mfe_per_share = max(pos.mfe_per_share, pos.entry - low)
        pos.mae_per_share = max(pos.mae_per_share, high - pos.entry)


def _prior_parabolic_target(hist: pd.DataFrame) -> float | None:
    """Nearest 10/20-day target from input containing completed sessions only."""
    completed = hist.sort_values("date").close.astype(float).to_numpy()
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
        identity_column = "security_id" if "security_id" in daily.columns else "symbol"
        day_bars = daily[daily.date == date].set_index(identity_column)
        closes = day_bars.close.astype(float).to_dict()
        opens = day_bars.open.astype(float).to_dict()
        # EOD moving-average exits signalled yesterday are executed at today's open.
        survivors: list[Position] = []
        for pos in positions:
            security_id = pos.security_id or pos.symbol
            if pos.pending_exit and security_id in opens:
                cash = _close_position(pos, pos.quantity, opens[security_id], date, "close_below_trailing_MA", cash, trades, cfg)
            else:
                survivors.append(pos)
        positions = survivors
        equity_open = _equity(cash, positions, opens)
        peak = max(peak, equity_open)
        open_loss = equity_open / max(previous_equity, 1.0) - 1
        open_loss_lock = open_loss <= -float(cfg["max_daily_loss_pct"])
        if open_loss_lock:
            # This desk-level guard uses only opening marks and executes at the open.
            for pos in list(positions):
                security_id = pos.security_id or pos.symbol
                if security_id in opens:
                    cash = _close_position(pos, pos.quantity, opens[security_id], date, "desk_open_loss_lock", cash, trades, cfg)
            positions = []

        # Freeze the opening portfolio budget before any session stop or target can
        # release capacity. In particular, a 10:00 stop cannot finance a 09:40 entry.
        occupied = _snapshot_occupied(positions, opens, cfg)
        proposals: list[Proposal] = []
        if not open_loss_lock:
            proposals, _, _ = desk.scan(
                date, daily, intraday, events, universe, max(equity_open, 1), occupied
            )

        # Existing-position exits are replayed in minute order after the opening
        # allocation snapshot is frozen. Stop wins if stop and target are both
        # inside the same OHLC bar because the true trade sequence is unknowable.
        for pos in list(positions):
            security_id = pos.security_id or pos.symbol
            if security_id not in opens or security_id not in closes:
                raise ValueError(f"missing daily opening/closing record for held security {security_id} on {date}")
            bars = intraday[(intraday.security_id == security_id) & (intraday.date == date)] if "security_id" in intraday else intraday[(intraday.symbol == pos.symbol) & (intraday.date == date)]
            if bars.empty:
                raise ValueError(f"missing intraday sequence for held security {security_id} on {date}")
            prior = daily[(daily[identity_column] == security_id) & (daily.date < date)].sort_values("date")
            target = _prior_parabolic_target(prior) if pos.side == -1 else None
            exit_event = _first_intraday_exit(bars, pos.side, pos.stop, target)
            for _, bar in bars.iterrows():
                if bar.bar_status != "TRADE":
                    continue
                _observe_excursion(pos, float(bar.high), float(bar.low))
                if exit_event is not None and int(bar.minute_from_open) >= exit_event[2]:
                    break
            if exit_event is not None:
                price, reason, _ = exit_event
                cash = _close_position(pos, pos.quantity, price, date, reason, cash, trades, cfg)
                positions.remove(pos)

        # Orders were budgeted in score order; actual fills are replayed by trigger
        # time, with a stable security identifier for simultaneous signals.
        for prop in sorted(proposals, key=lambda p: (int(p.trigger_time.split("+")[-1]), p.security_id)):
            if len(positions) >= min(int(cfg["max_open_positions"]), int(cfg["max_positions_hard"])):
                break
            if any((p.security_id or p.symbol) == prop.security_id for p in positions):
                continue
            gross_at_open = sum(p.quantity * opens.get(p.security_id or p.symbol, p.entry) for p in positions)
            if gross_at_open + prop.notional > max(equity_open, 1) * float(cfg["max_gross_exposure_pct"]):
                continue
            entry = _fill_price(prop.entry, prop.side, True, cfg)
            qty = prop.quantity
            entry_minute = int(prop.trigger_time.split("+")[-1])
            pos = Position(
                symbol=prop.symbol, setup=prop.setup, side=prop.side, quantity=qty,
                entry=entry, stop=prop.stop, entry_date=date, entry_index=day_index,
                sector=prop.sector, initial_risk_per_share=abs(entry - prop.stop),
                gap_buffer_per_share=prop.gap_buffer_pct * entry,
                trail_ma=int(cfg["trail_default_ma"]), entry_minute=entry_minute,
                security_id=prop.security_id, borrow_fee_bps=prop.borrow_fee_bps,
            )
            entry_fee = entry * qty * float(cfg["commission_bps"]) / 10_000
            cash -= prop.side * qty * entry
            cash -= entry_fee
            bars = intraday[(intraday.security_id == prop.security_id) & (intraday.date == date)] if "security_id" in intraday else intraday[(intraday.symbol == prop.symbol) & (intraday.date == date)]
            prior = daily[(daily[identity_column] == prop.security_id) & (daily.date < date)].sort_values("date")
            target = _prior_parabolic_target(prior) if prop.side == -1 else None
            exit_event = _first_intraday_exit(bars, prop.side, pos.stop, target, start_minute=entry_minute)
            for _, bar in bars[bars.minute_from_open >= entry_minute].iterrows():
                if bar.bar_status != "TRADE":
                    continue
                _observe_excursion(pos, float(bar.high), float(bar.low))
                if exit_event is not None and int(bar.minute_from_open) >= exit_event[2]:
                    break
            if exit_event is not None:
                price, reason, _ = exit_event
                cash = _close_position(pos, pos.quantity, price, date, f"same_session_{reason}", cash, trades, cfg)
            else:
                positions.append(pos)

        # EOD management: take one-third off after day 3 on a profitable trade,
        # move residual stop to breakeven, then trail a 10/20-day SMA.
        for pos in list(positions):
            security_id = pos.security_id or pos.symbol
            hist = daily[(daily[identity_column] == security_id) & (daily.date <= date)].sort_values("date")
            if security_id not in closes or len(hist) < 20:
                continue
            held = day_index - pos.entry_index + 1
            close = float(closes[security_id])
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
            # The breach is observed at close and the exit is queued for next open.
            if held >= 3 and pos.side * (close - ma) < 0:
                pos.pending_exit = True
            if pos.side == -1 and pos.borrow_fee_bps > 0:
                borrow_cost = pos.quantity * close * pos.borrow_fee_bps / 10_000 / 360
                cash -= borrow_cost
                pos.accrued_borrow_cost += borrow_cost

        marks = _equity(cash, positions, closes)
        peak = max(peak, marks)
        curves.append({
            "date": date, "equity": marks, "cash": cash,
            "gross_exposure": sum(p.quantity * closes.get(p.security_id or p.symbol, p.entry) for p in positions),
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
        "methodology": "point-in-time inputs; opening-range intraday fills; fee/slippage haircut; no live performance claim",
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
