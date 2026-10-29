"""Yahoo spark daily closes — the Sable desk's close-only screen series (autopilot-desk @48e8f90f
src/lib/market/provider.ts loadSparkDailyCloses, src/lib/desk/ledger-core.mjs dropOpenBar), read the same way:

  GET {query1|query2}.finance.yahoo.com/v7/finance/spark?symbols=<20 per batch>&range=6mo&interval=1d
  pairs (time, close) with a finite time and close > 0; the open bar dropped as the source dropped it
  (dropOpenBar(pairs, nowSec, 86400): keep bars stamped at or before the start of the previous UTC day);
  price = meta.regularMarketPrice || the last kept close; prevClose = meta.previousClose || chartPreviousClose;
  a symbol's series is reused for 5 minutes (DAILY_SPARK_CACHE_MS).

Returns {SYMBOL: {"symbol", "price", "prevClose", "times": [epoch s], "closes": [...]}}; a failed batch leaves its
symbols absent (the source moved on to the next batch)."""
import math
import time

from ..data.http import get

ORIGINS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
BATCH = 20                       # screen-core.mjs SCREEN_BATCH
CACHE_S = 300                    # DAILY_SPARK_CACHE_MS
_CACHE = {}


def drop_open_bar(pairs, now_sec, interval_sec=86400):
    """ledger-core.mjs dropOpenBar: completed bars only, then those stamped <= the last closed slot's start."""
    last_closed_start = math.floor(now_sec / interval_sec) * interval_sec - interval_sec
    return [p for p in pairs if p[0] <= last_closed_start]


def parse(payload, now_sec):
    out = {}
    for row in ((payload or {}).get("spark") or {}).get("result") or []:
        resp = (row.get("response") or [None])[0]
        if not resp:
            continue
        meta = resp.get("meta") or {}
        sym = str(meta.get("symbol") or row.get("symbol") or "").upper()
        if not sym:
            continue
        times = [float(t) for t in (resp.get("timestamp") or []) if t is not None]
        closes = ((resp.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        pairs = []
        for k in range(min(len(times), len(closes))):
            c = closes[k]
            if math.isfinite(times[k]) and c is not None and float(c) > 0:
                pairs.append((times[k], float(c)))
        done = drop_open_bar(pairs, now_sec, 86400)
        rmp = meta.get("regularMarketPrice")
        price = float(rmp) if (rmp is not None and float(rmp) != 0) else (done[-1][1] if done else None)
        prev = meta.get("previousClose") or meta.get("chartPreviousClose")
        out[sym] = {"symbol": sym, "price": price, "prevClose": float(prev) if prev else None,
                    "times": [t for t, _ in done], "closes": [c for _, c in done]}
    return out


def spark(symbols, now=None, fetch=get, rng="6mo"):
    now = float(now if now is not None else time.time())
    uniq = list(dict.fromkeys(str(s).strip().upper() for s in symbols if s))
    out, pending = {}, []
    for s in uniq:
        hit = _CACHE.get((rng, s))
        if hit and now - hit[0] < CACHE_S:
            out[s] = hit[1]
        else:
            pending.append(s)
    for i in range(0, len(pending), BATCH):
        batch = pending[i:i + BATCH]
        for origin in ORIGINS:
            try:
                doc = fetch(origin + "/v7/finance/spark", {"symbols": ",".join(batch), "range": rng, "interval": "1d"})
            except Exception:
                continue
            got = parse(doc, now)
            if not got:
                continue
            for s, series in got.items():
                _CACHE[(rng, s)] = (now, series)
                out[s] = series
            break
    return out


def feed(feeds, sleeve, now, arg):
    """FEED producer: the asking sleeve's spark symbols (sleeve.spark_symbols(now))."""
    syms = sleeve.spark_symbols(now) if hasattr(sleeve, "spark_symbols") else list(sleeve.CONFIG.universe)
    return spark(syms, now)


# -- the intraday screen: loadSparkMetas (provider.ts) — range 1d, interval 5m, the meta kept ------------------------
META_CACHE_S = 60                # SPARK_CACHE_MS
_META = {}


def parse_metas(payload, now_sec):
    """sparkClosesFromResponse (screen-core.mjs): finite time and close > 0, then the open 5-minute slot dropped;
    the response meta is kept whole with sparkTimes / sparkCloses."""
    out = {}
    for row in ((payload or {}).get("spark") or {}).get("result") or []:
        resp = (row.get("response") or [None])[0]
        meta = (resp or {}).get("meta")
        sym = str((meta or {}).get("symbol") or row.get("symbol") or "").upper()
        if not sym or not resp or not meta:
            continue
        times = resp.get("timestamp") or []
        closes = ((resp.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        bars = []
        for k in range(min(len(times), len(closes))):
            t, c = times[k], closes[k]
            if t is None or c is None:
                continue
            t, c = float(t), float(c)
            if math.isfinite(t) and c > 0:
                bars.append((t, c))
        done = drop_open_bar(bars, now_sec, 300)
        out[sym] = dict(meta, symbol=sym, sparkTimes=[t for t, _ in done], sparkCloses=[c for _, c in done])
    return out


def metas(symbols, now=None, fetch=get):
    now = float(now if now is not None else time.time())
    uniq = list(dict.fromkeys(str(s).strip().upper() for s in symbols if s))
    out, pending = {}, []
    for s in uniq:
        hit = _META.get(s)
        if hit and now - hit[0] < META_CACHE_S:
            out[s] = hit[1]
        else:
            pending.append(s)
    for i in range(0, len(pending), BATCH):
        batch = pending[i:i + BATCH]
        for origin in ORIGINS:
            try:
                doc = fetch(origin + "/v7/finance/spark", {"symbols": ",".join(batch), "range": "1d", "interval": "5m"})
            except Exception:
                continue
            got = parse_metas(doc, now)
            if not got:
                continue
            for s, m in got.items():
                _META[s] = (now, m)
                out[s] = m
            break
    return out


def feed_metas(feeds, sleeve, now, arg):
    syms = sleeve.spark_symbols(now) if hasattr(sleeve, "spark_symbols") else list(sleeve.CONFIG.universe)
    return metas(syms, now)
