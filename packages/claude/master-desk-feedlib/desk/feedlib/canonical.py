"""The canonical Tensor 1H feed — production FolioTend's input (the old desk's desk/canonical_bars.py, its
contract kept): the Yahoo chart API (query1, then query2), 60-minute bars of the regular session only
(includePrePost=false), open-anchored at :30 (09:30 ... 15:30 ET; the 15:30 bar is the closing stub; on a
13:00-close session Yahoo appends one 13:00 stub, served as delivered), range=1y, OHLC exactly as delivered
(no adjclose), volume passed through untouched (missing / non-finite / negative -> 0: production consumes
Yahoo's hourly volume as is, so parity requires it).

Production parse: rows with a non-positive integer timestamp, a non-finite or non-positive OHLC, high < max(o, c)
or low > min(o, c) are dropped; a duplicated timestamp keeps the last row; ascending. Completed bars only
(t + 3600 <= now).

The cached series is served with no provider call while it already ends at the newest completed bar a session
could have printed by now (the desk calendar: holidays print nothing, early closes end at the 13:00 stub);
otherwise the full year is fetched and REPLACES the cache wholesale (Yahoo revises prints between fetches; the
served series is always one Yahoo snapshot, never a splice). A failed fetch serves the cached series (a stale
canonical series beats a non-canonical one); with no cache the symbol has no bars (callers fail closed —
never an Alpaca substitute)."""
import json
import math
import os
from datetime import datetime, timedelta

from .. import calendar as cal
from ..util import ET, write_json_atomic

ORIGINS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
PARAMS = {"range": "1y", "interval": "60m", "includePrePost": "false", "events": "div,splits",
          "includeAdjustedClose": "false"}
HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0 (compatible; FolioTendVector/1.0; chart-generator)"}
BAR_S = 3600


def session_opens(day):
    """the bar open times one session prints: 09:30 ... 15:30 ET, or on an early close 09:30 / 10:30 / 11:30 and
    the 13:00 stub; nothing on a weekend or holiday."""
    if not cal.is_trading_day(day):
        return []
    base = datetime(day.year, day.month, day.day, 9, 30, tzinfo=ET)
    if cal.close_minutes(day) < 16 * 60:
        stub = datetime(day.year, day.month, day.day, 13, 0, tzinfo=ET)
        return [int((base + timedelta(hours=k)).timestamp()) for k in range(3)] + [int(stub.timestamp())]
    return [int((base + timedelta(hours=k)).timestamp()) for k in range(7)]


def latest_completed_open(now):
    day = cal._as_date(now)
    for back in range(0, 15):
        for t in reversed(session_opens(day - timedelta(days=back))):
            if t + BAR_S <= now:
                return t
    return None


def _pos_int(x):
    return int(x) if isinstance(x, (int, float)) and float(x).is_integer() and x > 0 else None


def _fin_pos(x):
    return float(x) if isinstance(x, (int, float)) and math.isfinite(x) and x > 0 else None


def _fin_nonneg(x):
    return float(x) if isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 else None


def parse(payload, symbol):
    """production parseYahooReplicaHistory semantics for 1h."""
    result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
    if not result or not result.get("meta"):
        raise ValueError("payload missing chart.result[0].meta")
    if str(result["meta"].get("symbol", "")).upper() != symbol.upper():
        raise ValueError("symbol mismatch: %r vs %r" % (result["meta"].get("symbol"), symbol))
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    ts = result.get("timestamp") or []
    n = len(ts)

    def col(name):
        c = quote.get(name) or []
        return list(c) + [None] * max(0, n - len(c))

    o_, h_, l_, c_, v_ = col("open"), col("high"), col("low"), col("close"), col("volume")
    by = {}
    for i, raw in enumerate(ts):
        t = _pos_int(raw)
        o, h, l, c = _fin_pos(o_[i]), _fin_pos(h_[i]), _fin_pos(l_[i]), _fin_pos(c_[i])
        if t is None or None in (o, h, l, c) or h < max(o, c) or l > min(o, c):
            continue
        v = _fin_nonneg(v_[i])
        by[t] = {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v if v is not None else 0}
    return [by[t] for t in sorted(by)]


def completed(bars, now):
    return [b for b in bars if int(b["t"]) + BAR_S <= now]


class Canonical:
    def __init__(self, root, getter=None, clock=None):
        self.dir = os.path.join(root, "canonical", "1h")
        self.getter = getter
        self.clock = clock
        self.status = {}

    def _path(self, sym):
        return os.path.join(self.dir, sym.upper().replace("/", "_").replace(".", "_").replace("^", "") + ".json")

    def _read(self, sym):
        try:
            with open(self._path(sym)) as f:
                d = json.load(f)
            return d.get("bars") if isinstance(d, dict) else None
        except (OSError, ValueError):
            return None

    def _fetch(self, sym):
        from ..data.http import get
        last = None
        for origin in ORIGINS:
            try:
                if self.getter is not None:
                    return self.getter(sym)
                return get(f"{origin}/v8/finance/chart/{sym}", dict(PARAMS), headers=HEADERS)
            except Exception as e:                         # the next origin, then fail
                last = e
        raise RuntimeError(f"all Yahoo origins failed for {sym}: {last!r}")

    def bars(self, sym, now):
        sym = sym.upper()
        cached = self._read(sym)
        newest = latest_completed_open(now)
        if cached and (newest is None or int(cached[-1]["t"]) >= newest):
            self.status[sym] = "cache"
            return completed(cached, now)
        try:
            fresh = completed(parse(self._fetch(sym), sym), now)
        except Exception as e:
            self.status[sym] = "stale_cache" if cached else "error: %s" % str(e)[:120]
            return completed(cached, now) if cached else []
        if not fresh:
            self.status[sym] = "stale_cache" if cached else "empty"
            return completed(cached, now) if cached else []
        write_json_atomic(self._path(sym), {"bars": fresh, "fetched_at": now, "last_bar_t": int(fresh[-1]["t"])})
        self.status[sym] = "fetch"
        return fresh
