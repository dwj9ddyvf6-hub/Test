#!/usr/bin/env python3
"""Research-only Spectral Echo Drift feature builder and event replay.

The module expects normalized dollar prices and top-10 MBP snapshots. It does
not download data, trade live, or substitute bars for historical depth.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.signal import detrend, find_peaks
from scipy.signal.windows import dpss


LEVELS = range(10)
TZ = "America/New_York"


@dataclass(frozen=True)
class Config:
    sample_every: int = 12
    window_minutes: int = 128
    min_period_minutes: int = 2
    max_period_minutes: int = 20
    coherence_enter: float = 0.82
    coherence_exit: float = 0.65
    min_lag: int = 2
    max_lag: int = 5
    min_lag_corr: float = 0.10
    attention_z_enter: float = 1.0
    risk_fraction: float = 0.004
    max_notional_fraction: float = 0.10
    max_book_participation: float = 0.05
    max_hold_minutes: int = 30
    max_daily_loss_fraction: float = 0.012
    latency_ms: int = 250
    max_book_staleness_ms: int = 1_000
    fee_bps_per_side: float = 2.5
    fee_per_share_per_side: float = 0.0
    starting_nav: float = 100_000.0
    tick_size: float = 0.01


def _depth_columns(prefix: str, field: str) -> list[str]:
    return [f"{prefix}_{field}_{level:02d}" for level in LEVELS]


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _to_et(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="coerce").dt.tz_convert(TZ)


def weighted_imbalance(bid_sizes: np.ndarray, ask_sizes: np.ndarray) -> np.ndarray:
    """Near-touch weighted signed depth imbalance for one or more snapshots."""
    bids = np.asarray(bid_sizes, dtype=float)
    asks = np.asarray(ask_sizes, dtype=float)
    if bids.shape != asks.shape or bids.shape[-1] != 10:
        raise ValueError("bid_sizes and ask_sizes must have matching shape (..., 10)")
    weights = np.exp(-0.22 * np.arange(10, dtype=float))
    denom = bids + asks + 1e-9
    per_level = np.divide(bids - asks, denom, out=np.zeros_like(denom), where=denom > 0)
    return np.sum(per_level * weights, axis=-1) / weights.sum()


def _clean_book(lob: pd.DataFrame) -> pd.DataFrame:
    """Normalize timestamps and reject incomplete or structurally broken books."""
    price_cols = _depth_columns("bid", "px") + _depth_columns("ask", "px")
    size_cols = _depth_columns("bid", "sz") + _depth_columns("ask", "sz")
    required = ["ts_event", "symbol", "sequence", *price_cols, *size_cols]
    _require_columns(lob, required, "LOB data")
    book = lob.copy()
    book["ts_event"] = _to_et(book["ts_event"])
    book["sequence"] = pd.to_numeric(book["sequence"], errors="coerce")
    book = book.dropna(subset=["ts_event", "symbol", "sequence"]).copy()
    book["symbol"] = book["symbol"].astype(str).str.upper()
    local_time = book["ts_event"].dt.time
    book = book[(local_time >= pd.Timestamp("09:30").time()) & (local_time < pd.Timestamp("16:00").time())]
    book = book.replace([np.inf, -np.inf], np.nan).dropna(subset=price_cols + size_cols).copy()
    bid_prices = book[_depth_columns("bid", "px")].to_numpy(dtype=float)
    ask_prices = book[_depth_columns("ask", "px")].to_numpy(dtype=float)
    sizes = book[size_cols].to_numpy(dtype=float)
    book["session_date"] = book["ts_event"].dt.date
    if book.duplicated(["symbol", "session_date", "sequence"], keep=False).any():
        raise ValueError("Duplicate sequence numbers within symbol/session; resolve feed ordering before replay")
    mask = (
        np.all(bid_prices > 0, axis=1)
        & np.all(ask_prices > 0, axis=1)
        & (ask_prices[:, 0] > bid_prices[:, 0])
        & np.all(np.diff(bid_prices, axis=1) < 0, axis=1)
        & np.all(np.diff(ask_prices, axis=1) > 0, axis=1)
        & np.all(sizes >= 0, axis=1)
    )
    book = book.loc[mask].sort_values(["symbol", "ts_event", "sequence"], kind="mergesort").reset_index(drop=True)
    if book.empty:
        raise ValueError("No valid regular-session, complete, uncrossed MBP-10 updates remain")
    return book


def _katz_dimension(prices: np.ndarray) -> float:
    x = np.asarray(prices, dtype=float)
    if len(x) < 3 or not np.all(np.isfinite(x)):
        return np.nan
    path = float(np.abs(np.diff(x)).sum())
    diameter = float(np.max(np.abs(x - x[0])))
    if path <= 0 or diameter <= 0:
        return 1.0
    n = len(x) - 1
    denominator = math.log10(n) + math.log10(diameter / path)
    if denominator <= 0:
        return 2.0
    value = math.log10(n) / denominator
    return float(np.clip(value, 1.0, 2.0))


def _spectral_stats(imbalance: np.ndarray, returns: np.ndarray, cfg: Config) -> dict:
    """Multi-taper coherence, selected peaks, entropy, and causal lead/lag.

    Positive lag means price returns lead changes in depth pressure by that
    many one-minute bars. The fixed window includes only data through time t.
    """
    x = np.asarray(imbalance, dtype=float)
    r = np.asarray(returns, dtype=float)
    n = cfg.window_minutes
    empty = {
        "coherence": np.nan, "entropy": np.nan, "lag_bars": np.nan,
        "lag_corr": np.nan, "peak_frequencies": [], "peak_phases": [],
        "peak_coherences": [], "peak_powers": [], "phase_spectrum": [],
        "phase_frequencies": [],
    }
    if len(x) != n or len(r) != n or not np.all(np.isfinite(x)) or not np.all(np.isfinite(r)):
        return empty

    x = detrend(x, type="linear")
    r = detrend(r, type="linear")
    tapers = dpss(n, NW=3.0, Kmax=5, sym=False)
    X = np.fft.rfft(tapers * x[None, :], axis=1)
    R = np.fft.rfft(tapers * r[None, :], axis=1)
    sxx = np.mean(np.abs(X) ** 2, axis=0)
    srr = np.mean(np.abs(R) ** 2, axis=0)
    sxr = np.mean(X * np.conjugate(R), axis=0)
    coh = np.clip(np.abs(sxr) ** 2 / (sxx * srr + 1e-15), 0.0, 1.0)
    freq = np.fft.rfftfreq(n, d=1.0)  # cycles per one-minute bar
    band = np.flatnonzero(
        (freq >= 1.0 / cfg.max_period_minutes)
        & (freq <= 1.0 / cfg.min_period_minutes)
    )
    if len(band) < 3:
        return empty

    band_power = sxx[band]
    local, _ = find_peaks(band_power)
    candidates = band[local]
    if len(candidates) < 3:
        return empty
    ordered = candidates[np.argsort(sxx[candidates])[::-1]]
    chosen: list[int] = []
    for idx in ordered:
        if all(abs(int(idx) - prior) >= 2 for prior in chosen):
            chosen.append(int(idx))
        if len(chosen) == 3:
            break
    if len(chosen) < 3:
        return empty

    powers = sxx[chosen]
    weights = powers / (powers.sum() + 1e-15)
    p = band_power / (band_power.sum() + 1e-15)
    entropy = float(-np.sum(p * np.log(p + 1e-15)) / np.log(len(p)))
    peak_coh = coh[chosen]

    dx = np.diff(np.asarray(imbalance, dtype=float))
    price_returns = np.asarray(returns, dtype=float)[1:]
    lag_values: list[tuple[int, float]] = []
    for lag in range(cfg.max_lag + 1):
        if lag == 0:
            a, b = price_returns, dx
        else:
            a, b = price_returns[:-lag], dx[lag:]
        if len(a) < 20 or np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
            continue
        corr = float(np.corrcoef(a, b)[0, 1])
        if np.isfinite(corr):
            lag_values.append((lag, corr))
    if not lag_values:
        return empty
    lag, lag_corr = max(lag_values, key=lambda item: item[1])
    return {
        "coherence": float(np.average(peak_coh, weights=weights)),
        "entropy": entropy,
        "lag_bars": int(lag),
        "lag_corr": float(lag_corr),
        "peak_frequencies": [float(freq[i]) for i in chosen],
        "peak_phases": [float(np.angle(sxr[i])) for i in chosen],
        "peak_coherences": [float(coh[i]) for i in chosen],
        "peak_powers": [float(sxx[i]) for i in chosen],
        "phase_spectrum": [float(v) for v in np.angle(sxr[band])],
        "phase_frequencies": [float(v) for v in freq[band]],
    }


def _attention_z(counts: pd.Series, lookback: int = 60, min_history: int = 30) -> pd.Series:
    values = np.log1p(counts.to_numpy(dtype=float))
    result = np.full(len(values), np.nan)
    for i in range(len(values)):
        hist = values[max(0, i - lookback):i]
        if len(hist) < min_history:
            continue
        med = float(np.median(hist))
        mad = float(np.median(np.abs(hist - med)))
        result[i] = (values[i] - med) / (1.4826 * mad + 0.25)
    return pd.Series(result, index=counts.index)


def build_features(lob: pd.DataFrame, posts: pd.DataFrame, cfg: Config = Config()) -> pd.DataFrame:
    """Build point-in-time 1-minute SED features from MBP-10 updates + posts."""
    lob_required = [
        "ts_event", "symbol", "sequence",
        *_depth_columns("bid", "px"), *_depth_columns("ask", "px"),
        *_depth_columns("bid", "sz"), *_depth_columns("ask", "sz"),
    ]
    post_required = ["observed_at", "symbol", "post_id", "author_id", "is_repost"]
    _require_columns(lob, lob_required, "LOB data")
    _require_columns(posts, post_required, "X post data")

    book = _clean_book(lob)
    bid_px = _depth_columns("bid", "px")
    ask_px = _depth_columns("ask", "px")
    bid_sz = _depth_columns("bid", "sz")
    ask_sz = _depth_columns("ask", "sz")
    valid = book.copy()
    valid["minute"] = valid["ts_event"].dt.floor("min")
    valid["session_date"] = valid["ts_event"].dt.date
    valid["mid"] = (valid["bid_px_00"] + valid["ask_px_00"]) / 2.0

    def first_last_stats(group: pd.DataFrame) -> pd.Series:
        first, last = group.iloc[0], group.iloc[-1]
        result = {
            "mid_open": float(first["mid"]), "mid_high": float(group["mid"].max()),
            "mid_low": float(group["mid"].min()), "mid_close": float(last["mid"]),
            "bid_open": float(first["bid_px_00"]), "ask_open": float(first["ask_px_00"]),
            "bid_close": float(last["bid_px_00"]), "ask_close": float(last["ask_px_00"]),
            "spread_close": float(last["ask_px_00"] - last["bid_px_00"]),
            "book_updates": int(len(group)),
            "ts_minute_end": group["ts_event"].max().floor("min") + pd.Timedelta(minutes=1),
        }
        return pd.Series(result)

    minute = (
        valid.groupby(["symbol", "minute"], sort=False, observed=True)
        .apply(first_last_stats, include_groups=False)
        .reset_index()
    )

    sample_no = valid.groupby(["symbol", "session_date"], sort=False).cumcount()
    sampled = valid.loc[sample_no % cfg.sample_every == 0].copy()
    sampled["imbalance"] = weighted_imbalance(sampled[bid_sz].to_numpy(), sampled[ask_sz].to_numpy())
    sampled_minute = (
        sampled.groupby(["symbol", "minute"], as_index=False, sort=False)
        .agg(imbalance=("imbalance", "mean"), sampled_updates=("imbalance", "size"))
    )
    features = minute.merge(sampled_minute, on=["symbol", "minute"], how="inner", validate="one_to_one")

    post_frame = posts.copy()
    post_frame["observed_at"] = _to_et(post_frame["observed_at"])
    post_frame = post_frame.dropna(subset=["observed_at", "symbol", "post_id", "author_id"]).copy()
    post_frame["symbol"] = post_frame["symbol"].astype(str).str.upper()
    post_frame["minute"] = post_frame["observed_at"].dt.floor("min")
    post_frame = post_frame.sort_values("observed_at", kind="mergesort")
    repost = post_frame["is_repost"].astype(str).str.lower().isin({"true", "1", "yes"})
    non_reposts = post_frame.loc[~repost].drop_duplicates(["symbol", "post_id"])
    raw_counts = (
        non_reposts.groupby(["symbol", "minute"], as_index=False, sort=False)
        .agg(post_count_raw=("post_id", "nunique"))
    )
    filtered_posts = non_reposts.drop_duplicates(["symbol", "minute", "author_id"])
    counts = (
        filtered_posts.groupby(["symbol", "minute"], as_index=False, sort=False)
        .agg(post_count=("post_id", "nunique"))
    )
    features = features.merge(raw_counts, on=["symbol", "minute"], how="left", validate="one_to_one")
    features = features.merge(counts, on=["symbol", "minute"], how="left", validate="one_to_one")
    features["post_count_raw"] = features["post_count_raw"].fillna(0).astype(int)
    features["post_count"] = features["post_count"].fillna(0).astype(int)
    features = features.sort_values(["symbol", "minute"]).reset_index(drop=True)

    frames = []
    for _, group in features.groupby("symbol", sort=False):
        g = group.copy().reset_index(drop=True)
        minute_delta = g["minute"].diff().dt.total_seconds().div(60)
        contiguous = minute_delta.eq(1)
        g["return_1m"] = np.log(g["mid_close"] / g["mid_close"].shift(1)).where(contiguous)
        contiguous_3m = minute_delta.eq(1) & minute_delta.shift(1).eq(1) & minute_delta.shift(2).eq(1)
        g["return_3m"] = np.log(g["mid_close"] / g["mid_close"].shift(3)).where(contiguous_3m)
        prev = g["mid_close"].shift(1)
        true_range = pd.concat(
            [g["mid_high"] - g["mid_low"], (g["mid_high"] - prev).abs(), (g["mid_low"] - prev).abs()], axis=1
        ).max(axis=1)
        g["atr_20"] = true_range.rolling(20, min_periods=20).mean()
        g["fractal_dim"] = np.nan
        for i in range(31, len(g)):
            if contiguous.iloc[i-30:i+1].all():
                g.loc[i, "fractal_dim"] = _katz_dimension(g.loc[i-31:i, "mid_close"].to_numpy())
        low = g["mid_low"]
        pivot = low.where(
            (low < low.shift(1)) & (low < low.shift(2)) & (low < low.shift(-1)) & (low < low.shift(-2))
        )
        # A pivot is usable only after its two right-hand bars have completed.
        g["fractal_low"] = pivot.shift(2).ffill()
        g["attention_z"] = _attention_z(g["post_count"])
        g["coherence"] = np.nan
        g["entropy"] = np.nan
        g["lag_bars"] = np.nan
        g["lag_corr"] = np.nan
        g["peak_frequencies"] = None
        g["peak_phases"] = None
        g["peak_coherences"] = None
        g["peak_powers"] = None
        g["phase_spectrum"] = None
        g["phase_frequencies"] = None
        for i in range(cfg.window_minutes - 1, len(g)):
            start = i - cfg.window_minutes + 1
            window = g.iloc[start:i + 1]
            if not window["minute"].diff().dropna().eq(pd.Timedelta(minutes=1)).all():
                continue
            if window["return_1m"].isna().any():
                continue
            stats = _spectral_stats(window["imbalance"].to_numpy(), window["return_1m"].to_numpy(), cfg)
            for key, value in stats.items():
                g.at[i, key] = value
        phase_drift = np.full(len(g), np.nan)
        for i in range(1, len(g)):
            previous_freqs = g.at[i - 1, "phase_frequencies"]
            previous_phase = g.at[i - 1, "phase_spectrum"]
            current_freqs = g.at[i, "peak_frequencies"]
            current_phase = g.at[i, "peak_phases"]
            current_power = g.at[i, "peak_powers"]
            if not all(isinstance(v, list) and len(v) > 0 for v in (previous_freqs, previous_phase, current_freqs, current_phase, current_power)):
                continue
            prior_by_freq = {round(float(f), 12): float(p) for f, p in zip(previous_freqs, previous_phase)}
            keys = [round(float(f), 12) for f in current_freqs]
            if not all(key in prior_by_freq for key in keys):
                continue
            delta = np.angle(np.exp(1j * (np.asarray(current_phase) - np.asarray([prior_by_freq[key] for key in keys]))))
            weights = np.asarray(current_power, dtype=float)
            phase_drift[i] = float(np.average(np.abs(delta), weights=weights))
        g["phase_drift_rad"] = phase_drift
        g["realized_vol_20m"] = np.sqrt(g["return_1m"].pow(2).rolling(20, min_periods=20).sum())
        g["x_velocity_posts_per_min"] = g["post_count"].astype(float)
        g["phase_vol_corr_20m"] = g["phase_drift_rad"].rolling(20, min_periods=15).corr(g["realized_vol_20m"])
        g["phase_x_corr_20m"] = g["phase_drift_rad"].rolling(20, min_periods=15).corr(g["x_velocity_posts_per_min"])
        g["entropy_falling"] = (g["entropy"] < g["entropy"].shift(1)) & (g["entropy"].shift(1) < g["entropy"].shift(2))
        g["signal_core"] = (
            (g["coherence"] > cfg.coherence_enter)
            & (g["lag_bars"] >= cfg.min_lag)
            & (g["lag_bars"] <= cfg.max_lag)
            & (g["lag_corr"] >= cfg.min_lag_corr)
            & g["entropy_falling"].fillna(False)
            & (g["imbalance"] > 0)
            & (g["return_3m"] > 0)
        )
        g["signal_social"] = g["signal_core"] & (g["attention_z"] >= cfg.attention_z_enter)
        g["known_at"] = g["ts_minute_end"]
        frames.append(g)
    if not frames:
        raise ValueError("No valid regular-session LOB minutes remained after quality checks")
    return pd.concat(frames, ignore_index=True).sort_values(["known_at", "symbol"]).reset_index(drop=True)


def walk_book(row: pd.Series, side: str, shares: int) -> tuple[float, int]:
    """Sweep the displayed top ten levels; return VWAP and filled shares."""
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if shares <= 0:
        return np.nan, 0
    px_prefix = "ask" if side == "buy" else "bid"
    sz_prefix = px_prefix
    remaining = int(shares)
    notional = 0.0
    filled = 0
    for level in LEVELS:
        px = float(row[f"{px_prefix}_px_{level:02d}"])
        size = max(0, int(float(row[f"{sz_prefix}_sz_{level:02d}"])))
        take = min(remaining, size)
        notional += take * px
        filled += take
        remaining -= take
        if remaining == 0:
            break
    return (notional / filled if filled else np.nan), filled


def _stop_price(feature: pd.Series, entry_mid: float, cfg: Config) -> float:
    atr = float(feature.get("atr_20", np.nan))
    dimension = float(feature.get("fractal_dim", np.nan))
    if not np.isfinite(atr) or atr <= 0:
        return np.nan
    if not np.isfinite(dimension):
        dimension = 1.5
    multiplier = 1.0 + 0.75 * (float(np.clip(dimension, 1.0, 2.0)) - 1.0)
    volatility_stop = entry_mid - multiplier * atr
    pivot = float(feature.get("fractal_low", np.nan))
    structural_stop = pivot - 0.1 * atr if np.isfinite(pivot) and pivot < entry_mid else volatility_stop
    stop = max(structural_stop, volatility_stop)
    return stop if stop < entry_mid else np.nan


def _first_event_at_or_after(group: pd.DataFrame, timestamp: pd.Timestamp, start: int = 0) -> int | None:
    pos = int(group["ts_event"].searchsorted(timestamp, side="left"))
    pos = max(pos, start)
    return pos if pos < len(group) else None


def _session_event_bounds(group: pd.DataFrame, session_date) -> tuple[int, int] | None:
    dates = group["ts_event"].dt.date.to_numpy()
    left = int(np.searchsorted(dates, session_date, side="left"))
    right = int(np.searchsorted(dates, session_date, side="right"))
    return (left, right) if left < right else None


def _next_completed_exit(features: pd.DataFrame, symbol: str, entry_time: pd.Timestamp, cfg: Config) -> tuple[pd.Timestamp, str]:
    later = features[(features["symbol"] == symbol) & (features["known_at"] > entry_time)]
    collapse = later.loc[later["coherence"] < cfg.coherence_exit, "known_at"]
    candidates: list[tuple[pd.Timestamp, str]] = []
    if len(collapse):
        candidates.append((collapse.iloc[0], "coherence_collapse"))
    candidates.append((entry_time + pd.Timedelta(minutes=cfg.max_hold_minutes), "time_stop"))
    eod = entry_time.normalize() + pd.Timedelta(hours=15, minutes=55)
    candidates.append((eod, "session_close"))
    return min(candidates, key=lambda item: item[0])


def event_backtest(
    features: pd.DataFrame,
    lob: pd.DataFrame,
    cfg: Config = Config(),
    model: str = "social",
) -> tuple[pd.DataFrame, dict]:
    """Conservative one-position, long-only event replay using marketable fills.

    Signals are known at minute close. Orders arrive after `latency_ms`; entries
    and exits sweep the then-current historical top-ten book. This is a research
    simulator, not an order router. It fails on incomplete fills.
    """
    if model not in {"core", "social"}:
        raise ValueError("model must be 'core' or 'social'")
    signal_col = "signal_core" if model == "core" else "signal_social"
    _require_columns(features, [signal_col, "symbol", "known_at", "coherence", "attention_z", "atr_20", "fractal_dim", "fractal_low"], "features")
    _require_columns(lob, ["ts_event", "symbol", "sequence", *_depth_columns("bid", "px"), *_depth_columns("ask", "px"), *_depth_columns("bid", "sz"), *_depth_columns("ask", "sz")], "LOB data")

    book = _clean_book(lob)
    feature_frame = features.copy().sort_values(["known_at", "symbol"])
    candidates = feature_frame.loc[feature_frame[signal_col].fillna(False)].copy()
    candidates = candidates.sort_values(["known_at", "coherence", "attention_z", "symbol"], ascending=[True, False, False, True])
    candidates = candidates[candidates["known_at"].dt.time < pd.Timestamp("15:50").time()]
    # One event per minute: when several tickers trigger simultaneously, take
    # the strongest coherence first, then highest attention surprise.
    candidates = candidates.drop_duplicates("known_at", keep="first")
    by_symbol = {s: g.reset_index(drop=True) for s, g in book.groupby("symbol", sort=False)}
    nav = float(cfg.starting_nav)
    busy_until: pd.Timestamp | None = None
    active_day = None
    day_start_nav = nav
    day_pnl = 0.0
    records: list[dict] = []
    latency = pd.Timedelta(milliseconds=cfg.latency_ms)

    for _, signal in candidates.iterrows():
        symbol = str(signal["symbol"])
        signal_time = pd.Timestamp(signal["known_at"])
        trade_day = signal_time.date()
        if active_day != trade_day:
            active_day = trade_day
            day_start_nav = nav
            day_pnl = 0.0
        if day_pnl <= -cfg.max_daily_loss_fraction * day_start_nav:
            continue
        entry_due = signal_time + latency
        if busy_until is not None and entry_due < busy_until:
            continue
        symbol_book = by_symbol.get(symbol)
        if symbol_book is None:
            continue
        bounds = _session_event_bounds(symbol_book, trade_day)
        if bounds is None:
            continue
        session_start, session_end = bounds
        entry_idx = _first_event_at_or_after(symbol_book, entry_due, start=session_start)
        if entry_idx is None or entry_idx >= session_end:
            continue
        entry_row = symbol_book.iloc[entry_idx]
        if (pd.Timestamp(entry_row["ts_event"]) - entry_due).total_seconds() * 1000 > cfg.max_book_staleness_ms:
            continue
        entry_mid = (float(entry_row["bid_px_00"]) + float(entry_row["ask_px_00"])) / 2.0
        stop = _stop_price(signal, entry_mid, cfg)
        if not np.isfinite(stop) or stop >= entry_mid:
            continue
        risk_budget = nav * cfg.risk_fraction
        risk_shares = math.floor(risk_budget / max(float(entry_row["ask_px_00"]) - stop, cfg.tick_size))
        notional_shares = math.floor(nav * cfg.max_notional_fraction / float(entry_row["ask_px_00"]))
        top10_ask = sum(max(0, int(float(entry_row[f"ask_sz_{i:02d}"]))) for i in LEVELS)
        depth_shares = math.floor(top10_ask * cfg.max_book_participation)
        requested = min(risk_shares, notional_shares, depth_shares)
        if requested <= 0:
            continue
        entry_vwap, filled = walk_book(entry_row, "buy", requested)
        if filled != requested or not np.isfinite(entry_vwap):
            continue
        actual_risk_per_share = entry_vwap - stop
        if actual_risk_per_share <= 0:
            continue
        risk_capped = math.floor(risk_budget / actual_risk_per_share)
        if risk_capped < requested:
            requested = risk_capped
            if requested <= 0:
                continue
            entry_vwap, filled = walk_book(entry_row, "buy", requested)
            if filled != requested or not np.isfinite(entry_vwap):
                continue

        # Earliest scheduled exit: structural stop trigger, coherence collapse,
        # time stop, or regular-session close. Stops execute only after latency.
        collapse_or_time, exit_reason = _next_completed_exit(feature_frame, symbol, signal_time, cfg)
        triggers: list[tuple[pd.Timestamp, str, bool]] = [(collapse_or_time, exit_reason, True)]
        future = symbol_book.iloc[entry_idx + 1:session_end]
        stop_hits = future.loc[future["bid_px_00"].astype(float) <= stop, "ts_event"]
        if len(stop_hits):
            triggers.append((pd.Timestamp(stop_hits.iloc[0]), "fractal_vol_stop", True))
        trigger_time, exit_reason, use_latency = min(triggers, key=lambda item: item[0])
        exit_due = trigger_time + (latency if use_latency else pd.Timedelta(0))
        exit_idx = _first_event_at_or_after(symbol_book, exit_due, start=entry_idx + 1)
        if exit_idx is None or exit_idx >= session_end:
            exit_idx = session_end - 1
        if exit_idx <= entry_idx:
            continue
        exit_row = symbol_book.iloc[exit_idx]
        exit_vwap, exit_filled = walk_book(exit_row, "sell", filled)
        if exit_filled != filled or not np.isfinite(exit_vwap):
            # Do not discard an unexitable position: record a hard data/capacity
            # failure and value the remainder at the deepest displayed bid.
            exit_vwap, exit_filled = _partial_liquidation_value(exit_row, filled)
            exit_reason = "unfilled_exit_depth"
        entry_notional = entry_vwap * filled
        exit_notional = exit_vwap * exit_filled
        gross = exit_notional - entry_notional
        fees = cfg.fee_per_share_per_side * (filled + exit_filled)
        fees += (cfg.fee_bps_per_side / 10_000.0) * (entry_notional + exit_notional)
        net = gross - fees
        nav += net
        day_pnl += net
        busy_until = pd.Timestamp(exit_row["ts_event"])
        records.append({
            "symbol": symbol, "model": model, "signal_time": signal_time.isoformat(),
            "entry_time": pd.Timestamp(entry_row["ts_event"]).isoformat(),
            "exit_time": pd.Timestamp(exit_row["ts_event"]).isoformat(),
            "shares": int(filled), "entry_vwap": float(entry_vwap),
            "exit_vwap": float(exit_vwap), "initial_stop": float(stop),
            "coherence": float(signal["coherence"]), "lag_bars": int(signal["lag_bars"]),
            "lag_corr": float(signal["lag_corr"]), "entropy": float(signal["entropy"]),
            "phase_drift_rad": float(signal.get("phase_drift_rad", np.nan)),
            "realized_vol_20m": float(signal.get("realized_vol_20m", np.nan)),
            "x_velocity_posts_per_min": float(signal.get("x_velocity_posts_per_min", np.nan)),
            "phase_vol_corr_20m": float(signal.get("phase_vol_corr_20m", np.nan)),
            "phase_x_corr_20m": float(signal.get("phase_x_corr_20m", np.nan)),
            "attention_count_raw": int(signal.get("post_count_raw", 0)),
            "attention_count_filtered": int(signal.get("post_count", 0)),
            "attention_z": float(signal.get("attention_z", np.nan)),
            "gross_pnl": float(gross), "fees": float(fees), "net_pnl": float(net),
            "net_return_bps_on_entry": float(10_000 * net / entry_notional),
            "exit_reason": exit_reason, "nav_after": float(nav),
        })
    trades = pd.DataFrame(records)
    session_days = feature_frame["known_at"].dt.date.unique()
    return trades, summarize_trades(trades, cfg.starting_nav, session_days=session_days)


def _partial_liquidation_value(row: pd.Series, shares: int) -> tuple[float, int]:
    """Value any unfillable tail at a punitive price below the deepest bid."""
    vwap, filled = walk_book(row, "sell", shares)
    if filled == shares:
        return vwap, filled
    remaining = shares - filled
    last_bid = float(row["bid_px_09"])
    spread = max(float(row["ask_px_00"]) - float(row["bid_px_00"]), 0.01)
    penalty = last_bid - 5.0 * spread
    total_value = (vwap * filled if filled else 0.0) + penalty * remaining
    return total_value / shares, shares


def _moving_block_mean_ci(values: np.ndarray, reps: int = 2000, block_len: int = 5, seed: int = 4107) -> list[float] | None:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    rng = np.random.default_rng(seed)
    block_len = min(block_len, len(x))
    means = np.empty(reps, dtype=float)
    for b in range(reps):
        indices: list[int] = []
        while len(indices) < len(x):
            start = int(rng.integers(0, len(x)))
            indices.extend((start + offset) % len(x) for offset in range(block_len))
        means[b] = x[np.asarray(indices[:len(x)])].mean()
    return [float(v) for v in np.quantile(means, [0.025, 0.975])]


def summarize_trades(
    trades: pd.DataFrame,
    starting_nav: float,
    session_days: Iterable | None = None,
) -> dict:
    if trades.empty:
        return {"status": "no_trades", "trade_count": 0, "starting_nav": starting_nav}
    pnl = trades["net_pnl"].astype(float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    exits = pd.to_datetime(trades["exit_time"], utc=True).dt.tz_convert(TZ)
    trade_day = exits.dt.date
    daily = trades.assign(_day=trade_day, _pnl=pnl).groupby("_day")["_pnl"].sum()
    days = sorted(set(session_days if session_days is not None else daily.index))
    daily = daily.reindex(days, fill_value=0.0)
    nav_curve = starting_nav + daily.cumsum()
    peak = pd.concat([pd.Series([starting_nav]), nav_curve.reset_index(drop=True)], ignore_index=True).cummax()
    dd = (pd.concat([pd.Series([starting_nav]), nav_curve.reset_index(drop=True)], ignore_index=True) / peak - 1.0).min()
    daily_returns = daily.to_numpy(dtype=float) / starting_nav
    daily_sd = float(np.std(daily_returns, ddof=1)) if len(daily_returns) > 1 else 0.0
    daily_sharpe = float(np.mean(daily_returns) / daily_sd * math.sqrt(252)) if daily_sd > 0 else None
    pnl_ci = _moving_block_mean_ci(daily_returns)
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    return {
        "status": "computed_from_supplied_data_not_yet_quality_certified",
        "trade_count": int(len(trades)),
        "starting_nav": float(starting_nav),
        "ending_nav": float(starting_nav + pnl.sum()),
        "net_pnl": float(pnl.sum()),
        "net_return_pct": float(100 * pnl.sum() / starting_nav),
        "win_rate": float((pnl > 0).mean()),
        "mean_net_pnl_per_trade": float(pnl.mean()),
        "median_net_return_bps": float(trades["net_return_bps_on_entry"].median()),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else None,
        "max_drawdown_pct": float(100 * dd),
        "session_count": int(len(daily)),
        "annualized_daily_sharpe": daily_sharpe,
        "mean_daily_return_ci95": pnl_ci,
        "mean_daily_return_ci_method": "5-session circular moving-block bootstrap; omitted under 20 sessions",
        "unfilled_exit_depth_count": int((trades["exit_reason"] == "unfilled_exit_depth").sum()),
        "fee_total": float(trades["fees"].sum()),
        "gross_to_net_retention": float(pnl.sum() / trades["gross_pnl"].sum()) if trades["gross_pnl"].sum() else None,
    }


def run(lob_path: Path, posts_path: Path, out: Path, model: str, cfg: Config = Config()) -> dict:
    if not lob_path.exists() or not posts_path.exists():
        raise FileNotFoundError("Both an historical MBP-10 parquet and point-in-time X posts parquet are required")
    out.mkdir(parents=True, exist_ok=True)
    lob = pd.read_parquet(lob_path)
    posts = pd.read_parquet(posts_path)
    features = build_features(lob, posts, cfg)
    trades, metrics = event_backtest(features, lob, cfg, model=model)
    features.to_parquet(out / f"features_{model}.parquet", index=False)
    trades.to_csv(out / f"trades_{model}.csv", index=False)
    metrics["model"] = model
    metrics["config"] = asdict(cfg)
    (out / f"metrics_{model}.json").write_text(json.dumps(metrics, indent=2, allow_nan=False))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lob", required=True, type=Path, help="MBP-10 event parquet")
    parser.add_argument("--posts", required=True, type=Path, help="point-in-time X post parquet")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--model", choices=["core", "social"], default="social")
    parser.add_argument("--nav", type=float, default=Config.starting_nav)
    parser.add_argument("--latency-ms", type=int, default=Config.latency_ms)
    parser.add_argument("--fee-bps-per-side", type=float, default=Config.fee_bps_per_side)
    args = parser.parse_args()
    cfg = Config(starting_nav=args.nav, latency_ms=args.latency_ms, fee_bps_per_side=args.fee_bps_per_side)
    result = run(args.lob, args.posts, args.out, args.model, cfg)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
