"""The Griffith / Ledge desk's own daily tape: Alpaca IEX, raw (unadjusted) daily bars.

The source runtime (agentic-trading-desk agentic_runtime.bounded_bars -> app.Alpaca.bars) asked Alpaca for
`timeframe=1Day, feed=iex, adjustment=raw, limit=550` over the last 900 days and stored them as the SCOPE evidence
(scope_runtime ADJUSTMENT_MODE "raw-alpaca-v1") that every Griffith decision reads: the three-strategy scanners and
the R4 parallel / tournament candidates. Volumes are therefore IEX-only and prices unadjusted — the liquidity floors
and momentum ranks the source computed are on that tape, so this producer serves exactly that tape (never a
consolidated or adjusted substitute) whenever Alpaca credentials exist. Without them the desk still runs the
sleeves on the best free public tape — Yahoo completed daily bars (split-adjusted OHLC, consolidated volume) — and
labels it (`source` = "yahoo"): a named divergence of every Griffith sleeve (IEX-only volume and raw prices differ
from the consolidated, split-adjusted series for liquidity floors, ranks, and across splits).

The tape covers the frozen SCOPE universe (desk/vendor/griffith/universe.txt, 552 names; BTC-USD / ETH-USD are the
source's accounting-only rows and never had bars). Only universe names were ever stored as evidence (the source
fetched the sector proxies XLB / XLC / XLY with each shard but never stored them, so the decisions never saw them).
Bars are cached per symbol (BarCache source "alpaca_iex_raw") and refreshed incrementally once per session; a
session's IEX daily bar is admitted once IEX's extended trading for it has ended (close + 75 min) — the next
morning's premarket decision always sees it final."""
import os
from datetime import datetime, timezone

from .. import calendar as cal
from ..util import parse_ts

SRC = "alpaca_iex_raw"
HISTORY = 550            # config.three_strategy.daily_history_bars (agentic_runtime.daily_history_limit)
DAYS = 900               # bounded_bars(..., "1Day", limit, days=900)
FINAL_AFTER_CLOSE_S = 4500
ACCOUNTING_ONLY = ("BTC-USD", "ETH-USD")
_UNIVERSE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "griffith",
                         "universe.txt")


def universe():
    """the frozen SCOPE manifest, in its own order (AA .. ZM)."""
    return open(_UNIVERSE, "rb").read().decode("utf-8").splitlines()


def tape_symbols():
    return [s for s in universe() if s not in ACCOUNTING_ONLY]


def iso(t):
    """epoch -> the Alpaca bar timestamp string the source compared and sorted (e.g. 2026-10-15T04:00:00Z)."""
    return datetime.fromtimestamp(float(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_of(t):
    """the ET session date an Alpaca daily bar (stamped 00:00 ET, in UTC) belongs to."""
    return cal._as_date(float(t) + 12 * 3600)


def last_final_session(now):
    d = cal._as_date(now)
    if cal.is_trading_day(d) and now >= cal.session_close(d) + FINAL_AFTER_CLOSE_S:
        return d
    return cal.prev_trading_day(d)


def raw_rows(bars):
    """desk bars (epoch t) -> the source's raw bar dicts {t: ISO string, o, h, l, c, v}."""
    return [{"t": iso(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]} for b in bars]


def iex_daily(hub, symbols, now, n=HISTORY, days=DAYS):
    """{SYM: [completed IEX raw daily bars, epoch t]} for every symbol the venue returns (needs Alpaca keys)."""
    if hub is None or getattr(hub, "alpaca", None) is None:
        raise RuntimeError("Alpaca IEX daily bars need Alpaca credentials (the source's feed=iex, adjustment=raw tape)")
    want = last_final_session(now)
    start_full = now - days * 86400
    out, todo = {}, []
    for s in symbols:
        cached = hub.cache.read(SRC, "1d", s)
        cov = hub.cache.covered_from(SRC, "1d", s)
        deep = cov is not None and cov <= start_full + 86400
        if cached and deep and session_of(cached[-1]["t"]) >= want:
            out[s] = cached[-n:]
        else:
            todo.append((s, cached if deep else []))
    groups = {}
    for s, cached in todo:
        groups.setdefault(int((cached[-1]["t"] if cached else start_full) // 86400), []).append(s)
    for day, syms in sorted(groups.items()):
        for i in range(0, len(syms), 100):
            batch = syms[i:i + 100]
            got = hub.alpaca.c.stock_bars(batch, "1Day", start=iso(day * 86400), end=iso(now), feed="iex",
                                          adjustment="raw")
            for s in batch:
                rows = [{"t": parse_ts(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                        for b in (got.get(s) or [])]
                rows = [b for b in rows if session_of(b["t"]) <= want]
                hub.cache.want_depth(SRC, "1d", [s], n + 100)
                out[s] = hub.cache.merge(SRC, "1d", s, rows)[-n:]
            hub.cache.mark_covered(SRC, "1d", batch, start_full)
    return {s: bl for s, bl in out.items() if bl}


def feed(feeds, sleeve, now, arg=None):
    """FEED griffith_iex_1d — {"session", "bars": {SYM: [epoch bars]}, "missing"} for the asking sleeve's decision
    pass; {"skipped": True} on its other passes. One load per final session, shared by every Griffith sleeve."""
    wants = getattr(sleeve, "wants_tape", None)
    if wants is not None and not wants(now):
        return {"skipped": True}
    memo = feeds.hub.__dict__.setdefault("_griffith_tape", {})
    key = last_final_session(now).isoformat()
    if key not in memo:
        symbols = tape_symbols()
        if getattr(feeds.hub, "alpaca", None) is not None:
            bars, source = iex_daily(feeds.hub, symbols, now), SRC
        else:                       # the free public substitute (named divergence), never a silent mix of the two
            got = feeds.hub.bars("yahoo", "1d", symbols, HISTORY)
            bars = {s: [b for b in bl if session_of(b["t"] - 8 * 3600) <= cal._as_date(key)]
                    for s, bl in got.items() if bl}
            source = "yahoo"
        memo.clear()
        memo[key] = {"session": key, "source": source, "bars": {s: bl for s, bl in bars.items() if bl},
                     "missing": sorted(set(symbols) - set(bars))}
    return memo[key]
