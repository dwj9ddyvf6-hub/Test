"""The QLD timing book's daily history — Midna's src/lib/felipe/live.ts fetchDaily / loadSeries (@ entire 43f08f96),
ported: Yahoo's daily chart from 1990-01-01 (period1 631152000) to now, events div,splits; a row needs a positive
close and a positive adjclose; factor = adjclose / close scales open / high / low (a missing one is the close);
high = max(high, open, adj, low), low = min(low, open, adj), close = adj; the ET date of each stamp, the last row per
date. Kept in cache/midna/qld_daily.json and re-fetched once it is 12 hours old or QQQ has 200 rows or fewer (the
felipe cache's rule); a failed fetch keeps the cached series."""
import os
import time
from datetime import datetime

from ..data.http import get
from ..util import ET, read_json, write_json_atomic

SYMBOLS = ("QQQ", "QLD")
MAX_AGE_S = 12 * 3600


def parse_daily(body):
    res = (((body or {}).get("chart") or {}).get("result") or [None])[0] or {}
    stamps = res.get("timestamp") or []
    ind = res.get("indicators") or {}
    q = (ind.get("quote") or [{}])[0] or {}
    adj = ((ind.get("adjclose") or [{}])[0] or {}).get("adjclose") or []
    rows = {}
    closes = q.get("close") or []
    for i, t in enumerate(stamps):
        close = closes[i] if i < len(closes) else None
        a = adj[i] if i < len(adj) else None
        if close is None or not close > 0 or a is None or not a > 0:
            continue
        f = a / close

        def pick(k):
            arr = q.get(k) or []
            v = arr[i] if i < len(arr) else None
            return (v if v is not None else close) * f
        o, h, lo = pick("open"), pick("high"), pick("low")
        d = datetime.fromtimestamp(int(t), tz=ET).date().isoformat()
        rows[d] = {"date": d, "open": o, "high": max(h, o, a, lo), "low": min(lo, o, a), "close": a}
    return [rows[k] for k in sorted(rows)]


def fetch_daily(sym, now, getter=get):
    body = getter(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                  {"interval": "1d", "period1": 631152000, "period2": int(now), "events": "div,splits"})
    return parse_daily(body)


def load(root, now, getter=get):
    path = os.path.join(root, "cache", "midna", "qld_daily.json")
    doc = read_json(path, {}) or {}
    series = doc.get("series") or {}
    fresh = now - float(doc.get("fetched_at") or 0) < MAX_AGE_S and len(series.get("QQQ") or []) > 200 and \
        all(series.get(s) for s in SYMBOLS)
    if fresh:
        return series
    got = {}
    for s in SYMBOLS:
        try:
            got[s] = fetch_daily(s, now, getter)
        except Exception:                                  # noqa: BLE001 — keep the cached series
            got[s] = series.get(s) or []
    if all(got.get(s) for s in SYMBOLS):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_json_atomic(path, {"fetched_at": now, "series": got})
    return got


def feed_qld(feeds, sleeve, now, arg=None):
    eng = getattr(sleeve, "engine", None)
    root = eng.root if eng is not None else os.path.dirname(os.path.dirname(feeds.hub.cache.root))
    return load(root, now if now else time.time())
