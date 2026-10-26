"""Shared plumbing for the quant_research family: daily bar frames from the hub, session helpers, NAV and the
sells-first target rebalance used by the weekly / monthly allocation sleeves."""
import math
import sys
import types
from datetime import date, timedelta

import numpy as np
import pandas as pd

from ... import calendar as cal
from ...contract import Intent, OrderSpec

SOURCE_REPO = "quant-research-critical"
SOURCE_COMMIT = "0be4c57569e363d052bd23564cf0664697439927"
SIXAI = "research/2026-10-08-six-strategy-reconstruction/source.zip.parts :: "


def session_date(t):
    """the ET session date of a daily bar stamp (00:00 or 09:30 ET stamps alike)."""
    return cal._as_date(float(t) + 6 * 3600)


def frame(bars):
    """hub daily bars -> DataFrame o h l c v (+ ac when present) on a naive session-date index."""
    if not bars:
        return None
    d = pd.DataFrame(bars)
    d.index = pd.DatetimeIndex([pd.Timestamp(session_date(t)) for t in d.t.values])
    d = d[~d.index.duplicated(keep="last")].sort_index()
    cols = [k for k in ("o", "h", "l", "c", "v", "vw", "ac") if k in d]
    return d[cols].astype(float)


def daily(hub, source, syms, n, batch=True):
    """{sym: frame} from the hub; a batch first, then one request per symbol the batch did not return."""
    out = {}
    syms = list(dict.fromkeys(syms))
    if batch and syms:
        got = hub.bars(source, "1d", syms, n) or {}
        for s in syms:
            f = frame(got.get(s))
            if f is not None and len(f):
                out[s] = f
    for s in syms:
        if s in out:
            continue
        f = frame((hub.bars(source, "1d", [s], n) or {}).get(s))
        if f is not None and len(f):
            out[s] = f
    return out


def last_friday_before(session):
    """the latest trading Friday strictly before `session` (None if it was a holiday week)."""
    d = cal._as_date(session) - timedelta(days=1)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d if cal.is_trading_day(d) else None


def nav(view):
    """cash plus held shares at the bid (else last / ask / average cost)."""
    total = float(view.cash)
    for inst, p in (view.positions or {}).items():
        sym = inst.split(":", 1)[1] if ":" in inst else inst
        q = (view.quotes or {}).get(sym) or {}
        px = q.get("bid") or q.get("last") or q.get("ask") or p.get("avg") or 0.0
        total += float(p["qty"]) * float(px)
    return total


def held(view):
    return {i.split(":", 1)[1]: float(p["qty"]) for i, p in (view.positions or {}).items()
            if i.startswith("EQ:") and abs(float(p["qty"])) > 1e-12}


def rebalance(view, target, key, reason, window_s=1800, rel_tol=1e-4):
    """target shares {sym: qty} as "target" intents, sells before buys (buys once no sell is outstanding). A
    difference under 0.01% of the position (fill rounding) is not a trade."""
    pos = held(view)
    syms = sorted(set(pos) | set(target))

    def tol(s):
        return max(1e-6, rel_tol * max(abs(pos.get(s, 0.0)), abs(target.get(s, 0.0))))
    sells = [s for s in syms if pos.get(s, 0.0) > target.get(s, 0.0) + tol(s)]
    legs = sells or [s for s in syms if pos.get(s, 0.0) < target.get(s, 0.0) - tol(s)]
    pending = {str(o.get("inst", "")).split(":", 1)[-1] for o in ((view.extra or {}).get("pending_orders") or [])
               if abs(float(o.get("vqty") or 0)) - abs(float(o.get("filled_v") or 0)) > 1e-6}
    out = []
    for s in legs:
        if s in pending:
            continue
        out.append(Intent("target", s, side="long", qty=round(float(target.get(s, 0.0)), 6),
                          signal_key=f"{key}:{s}:{'sell' if sells else 'buy'}", reason=reason,
                          order=OrderSpec(window_s=window_s)))
    return out, bool(legs)


def install_calendar_shim():
    """pandas_market_calendars is not installed: a stand-in backed by desk.calendar (NYSE sessions) so vendored
    modules that import it load. The decision paths that use it are named in each module."""
    if "pandas_market_calendars" in sys.modules:
        return
    m = types.ModuleType("pandas_market_calendars")

    class _Cal:
        def __init__(self, name):
            self.name = name

        def schedule(self, start_date, end_date):
            d, e, rows = pd.Timestamp(start_date).date(), pd.Timestamp(end_date).date(), []
            while d <= e:
                if cal.is_trading_day(d):
                    rows.append((pd.Timestamp(d), pd.Timestamp(cal.session_open(d), unit="s", tz="UTC"),
                                 pd.Timestamp(cal.session_close(d), unit="s", tz="UTC")))
                d += timedelta(days=1)
            return pd.DataFrame([(o, c) for _, o, c in rows], index=pd.DatetimeIndex([r[0] for r in rows]),
                                columns=["market_open", "market_close"])

        def valid_days(self, start_date, end_date):
            return self.schedule(start_date, end_date).index.tz_localize("UTC")

    m.get_calendar = lambda name="NYSE": _Cal(name)
    m.get_calendar_names = lambda: ["NYSE", "NASDAQ"]
    sys.modules["pandas_market_calendars"] = m


# --------------------------------------------------------------------------------------------- the six-AI panels
SPECIAL_CLOSURES = {"2018-12-05", "2025-01-09"}     # NYSE national days of mourning (absent from desk.calendar)
JUNETEENTH_OPEN = {"2016-06-20", "2017-06-19", "2018-06-19", "2019-06-19", "2020-06-19", "2021-06-18"}
# (desk.calendar closes Juneteenth in every year; NYSE first closed for it in 2022)


def is_session(d):
    """an NYSE session as the reconstruction panel's calendar has it (data/calendar.csv)."""
    d = cal._as_date(d)
    iso = d.isoformat()
    if iso in JUNETEENTH_OPEN:
        return True
    return cal.is_trading_day(d) and iso not in SPECIAL_CLOSURES


def sessions_between(a, b):
    """exchange sessions in [a, b] (the reconstruction panel's calendar: desk.calendar less the special closures)."""
    d, e, out = cal._as_date(a), cal._as_date(b), []
    while d <= e:
        if is_session(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def prev_session(d):
    d = cal._as_date(d) - timedelta(days=1)
    while not is_session(d):
        d -= timedelta(days=1)
    return d.isoformat()


def panel(frames, syms, upto, n_rows):
    """the reconstruction panel's arrays from hub daily bars: rows = the last n_rows sessions through `upto`,
    columns = syms; open / close / high / low / volume / vwap float64 with NaN where unobserved, and the validity
    mask (finite positive ordered OHLC, finite non-negative volume: build_panel's split-adjusted check)."""
    days = sessions_between(cal._as_date(upto) - timedelta(days=int(n_rows * 1.6) + 20), upto)[-n_rows:]
    idx = pd.DatetimeIndex(days)
    out = {k: np.full((len(days), len(syms)), np.nan) for k in ("open", "close", "high", "low", "volume", "vwap")}
    for j, s in enumerate(syms):
        f = frames.get(s)
        if f is None or not len(f):
            continue
        f = f.reindex(idx)
        for k, c in (("open", "o"), ("close", "c"), ("high", "h"), ("low", "l"), ("volume", "v"), ("vwap", "vw")):
            if c in f:
                out[k][:, j] = f[c].astype(float).values
    o, h, l, c, v = (out[k] for k in ("open", "high", "low", "close", "volume"))
    with np.errstate(invalid="ignore"):
        valid = np.isfinite(o) & np.isfinite(h) & np.isfinite(l) & np.isfinite(c) & (o > 0) & (h > 0) & (l > 0) & \
            (c > 0) & np.isfinite(v) & (v >= 0) & (h >= np.maximum.reduce([o, l, c])) & \
            (l <= np.minimum.reduce([o, h, c]))
    out["valid"] = valid
    out["dates"] = np.array(days)
    return out


def eligibility(close, volume, valid, history_sessions=252, liquidity_sessions=20, min_dollar_volume=10_000_000,
                min_price=5.0):
    """data/build_panel.py eligibility(): 252 complete prior valid sessions, prior-20 mean split close x volume of at
    least $10M, current valid close of at least $5 (every roster name is an equity candidate)."""
    n, m = close.shape
    valid_int = valid.astype(np.int64)
    count_cum = np.vstack([np.zeros((1, m), dtype=np.int64), np.cumsum(valid_int, axis=0)])
    prior_count = np.zeros((n, m), dtype=np.int64)
    if n > history_sessions:
        prior_count[history_sessions:] = count_cum[history_sessions:n] - count_cum[:n - history_sessions]
    history_ok = prior_count == history_sessions
    dollar = np.where(valid, close * volume, 0.)
    dollar_cum = np.vstack([np.zeros((1, m)), np.cumsum(dollar, axis=0)])
    mean_dollar = np.full((n, m), np.nan)
    if n > liquidity_sessions:
        sums = dollar_cum[liquidity_sessions:n] - dollar_cum[:n - liquidity_sessions]
        counts = count_cum[liquidity_sessions:n] - count_cum[:n - liquidity_sessions]
        mean_dollar[liquidity_sessions:] = np.where(counts == liquidity_sessions, sums / liquidity_sessions, np.nan)
    with np.errstate(invalid="ignore"):
        return valid & history_ok & (mean_dollar >= min_dollar_volume) & (close >= min_price)


def target_shares(view, weights, px_side="ask"):
    """weights {sym: w} of the sleeve's NAV -> shares at the live quote; None when a needed quote is missing."""
    total = nav(view)
    out = {}
    for s, w in weights.items():
        if w <= 0:
            out[s] = 0.0
            continue
        q = (view.quotes or {}).get(s) or {}
        px = q.get(px_side) or q.get("last")
        if not px:
            return None
        out[s] = w * total / float(px)
    return out
