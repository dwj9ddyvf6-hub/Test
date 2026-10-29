"""Request-driven warm: fetch exactly the (symbol, timeframe) pairs consumers asked for, each ONCE, in batches.
1Day/1Hour/1Week equities come from the canonical engine store (0 API calls; Lazarus' pipeline already fetched them);
everything else from Alpaca multi-symbol endpoints (<=100 symbols per call), written in muse's BarCache format."""
import os, json, time, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from . import secrets, netguard
from .data import DataHub, Missing
import sys as _s; _s.path.insert(0, "/workspace/desk2/vendor/silicon")
from runtime.models import Bar
DATA = "https://data.alpaca.markets"
CANON = {"1Day": "1d", "1Hour": "1h", "1Week": "1wk"}
STATS = dict(alpaca_calls=0, canon_symbols=0, bars_written=0)

def _get(url):
    STATS["alpaca_calls"] += 1
    rq = urllib.request.Request(url, headers={**secrets.headers("TEST_MWJW"), "User-Agent": "md2"})
    return json.loads(netguard.urlopen_read(rq, timeout=30, total=50))

def _iso(ts): return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def canon_rows(hub, sym, tf):
    b = hub.equity(sym, CANON[tf])
    if isinstance(b, Missing): return b
    if tf in ("1Day", "1Week"):   # Alpaca convention: daily/weekly bar t = session date 04:00Z (ET midnight); engine t = open time
        ts = [datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT04:00:00Z") for t in b.t]
    else: ts = [_iso(t) for t in b.t]
    return [Bar(t=t, o=float(o), h=float(h), l=float(l), c=float(c), v=float(v)) for t, o, h, l, c, v in zip(ts, b.o, b.h, b.l, b.c, b.v)]

def alpaca_multi(syms, tf, days, crypto=False, feed="sip"):
    out = {s: [] for s in syms}; start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i in range(0, len(syms), 100):
        chunk = syms[i:i + 100]; tok = None
        while True:
            q = dict(symbols=",".join(chunk), timeframe=tf, start=start, limit=10000)
            if not crypto: q["feed"] = feed; q["adjustment"] = "raw"
            if tok: q["page_token"] = tok
            path = "/v1beta3/crypto/us/bars" if crypto else "/v2/stocks/bars"
            r = _get(f"{DATA}{path}?{urllib.parse.urlencode(q)}")
            for s, rows in (r.get("bars") or {}).items():
                out[s] += [Bar(t=x["t"], o=float(x["o"]), h=float(x["h"]), l=float(x["l"]), c=float(x["c"]), v=float(x.get("v", 0))) for x in rows]
            tok = r.get("next_page_token")
            if not tok: break
    return out

DAYS = {"1Min": 3, "3Min": 5, "5Min": 30, "10Min": 30, "15Min": 30, "60Min": 60, "1Hour": 60, "4Hour": 90, "240Min": 90, "1Day": 600, "1Week": 2000}
TFMAP = {"60Min": "1Hour", "240Min": "4Hour", "10Min": "10Min", "3Min": "3Min"}

INTRADAY_DEADLINE_S = 120   # whole intraday top-up
INTRADAY = {"1Min", "3Min", "5Min", "10Min", "15Min", "60Min", "1Hour"}
def intraday(cache, requests, days=2):
    """per-pass RTH top-up: only the intraday stock timeframes consumers asked for, batched (<=100 symbols/call)."""
    by = {}
    for sym, tf in requests:
        if tf in INTRADAY and sym.isalpha() and sym.isupper(): by.setdefault(tf, []).append(sym)
    # E18: the timeframes are fetched CONCURRENTLY (network-bound; bounded to 4 in flight, well under Alpaca's 200/min) and
    # written by this one thread (single writer). One failing timeframe no longer aborts the others (was: first error -> return).
    from concurrent.futures import ThreadPoolExecutor
    n = 0; errs = []
    def fetch(item):
        tf, syms = item
        try: return tf, alpaca_multi(sorted(set(syms)), TFMAP.get(tf, tf), days), None
        except Exception as e: return tf, None, f"{tf} {type(e).__name__}"
    # stuck-desk fix 2026-10-28 (Trader t220u): bounded wait - a hung timeframe is abandoned (reported as an error), never joined forever
    # (the old `with ThreadPoolExecutor` exit waited for every worker; ex.map had no timeout)
    from concurrent.futures import TimeoutError as FutTimeout
    import time as _t
    ex = ThreadPoolExecutor(max_workers=min(4, max(1, len(by)))); t_end = _t.time() + INTRADAY_DEADLINE_S
    try:
        futs = [(item[0], ex.submit(fetch, item)) for item in sorted(by.items())]
        for tf0, fu in futs:
            try: tf, got, err = fu.result(timeout=max(0.1, t_end - _t.time()))
            except FutTimeout: errs.append(f"{tf0} deadline {INTRADAY_DEADLINE_S}s"); continue
            if err: errs.append(err); continue
            for s, rows in got.items():
                if rows: n += cache.write_bars(s, tf, rows)
    finally: ex.shutdown(wait=False, cancel_futures=True)
    out = dict(bars=n, calls=STATS["alpaca_calls"])
    if errs: out["error"] = "; ".join(errs)
    return out

def warm(cache, requests, hub=None):
    hub = hub or DataHub(); by_tf = {}
    for sym, tf in requests:
        if tf in CANON and not any(c in sym for c in "/-^") and os.path.exists(f"{hub.engine}/{CANON[tf]}/{sym}.csv"):
            rows = canon_rows(hub, sym, tf)
            if not isinstance(rows, Missing): STATS["canon_symbols"] += 1; STATS["bars_written"] += cache.write_bars(sym, tf, rows); continue
        by_tf.setdefault(tf, []).append(sym)
    for tf, syms in by_tf.items():
        crypto = [s for s in syms if "/" in s]; stocks = [s for s in syms if s.isalpha() and s.isupper()]
        atf = TFMAP.get(tf, tf); deep = 310 if ("SPY" in stocks and tf == "5Min") else DAYS.get(tf, 30)
        for group, is_c in ((stocks, False), (crypto, True)):
            if not group: continue
            try: got = alpaca_multi(group, atf, deep, crypto=is_c)
            except Exception as e: print(f"warm {tf} {len(group)} syms failed: {type(e).__name__} {e}"[:200]); continue
            for s, rows in got.items():
                if rows: STATS["bars_written"] += cache.write_bars(s, tf, rows)
    return dict(STATS)
