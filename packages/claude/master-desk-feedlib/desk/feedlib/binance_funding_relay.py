"""Binance USD-M funding for the R19 crypto books while Binance's own endpoint refuses this host.

fapi.binance.com answers HTTP 451 ("restricted location") to US hosts, and the R19 crypto wrapper then carried the
source's blocker FUNDING_SOURCE_HTTP_451 on 51 of its 63 books: every family conditioned on the sign of the latest
settled funding rate (negative_funding_squeeze, absorption_negative_funding, absorption_nonnegative_funding,
breakdown_base, crowded_long_failure, basis_repair) never entered. The quantity itself is public: CoinGecko's keyless
derivatives endpoint relays each Binance (Futures) perpetual's current funding rate (in percent; 744 USDT perpetuals
on 2026-10-16, including ADAUSDT, ENJUSDT and LINKUSDT, the books' three symbols). Its per-exchange endpoint is 20x
smaller but rounds to 0.001% (ADAUSDT -0.000346% read 0.0: the sign these books test), so the full list is read.

A settled rate is the interval's estimate at its end. The job `binance_funding_relay` samples the relay in the last
nine minutes before each UTC 4-hour boundary and keeps, for each symbol, its last estimate before that symbol's own
settlement instants (the interval, 4 h or 8 h, read from Binance's public monthly archive, data.binance.vision).
records() turns an estimate into a settled-funding record once its settlement has passed: received_at is the
settlement instant at the earliest (the moment the estimate is the settled value), observed_public_endpoint true.

Named divergences from the source's capture (r19_crypto_data.py read fapi /fundingRate): the settled rate is the
relayed estimate seconds-to-minutes before settlement, not Binance's settlement record, so a rate within a hair of
zero can carry the other sign; and the receipt is the settlement instant, not an HTTP response after it. Binance's
own endpoint, when it answers, always wins. Not an alternate venue: the relayed number is Binance's own rate."""
import io
import json
import os
import time
import zipfile
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

RELAY_URL = "https://api.coingecko.com/api/v3/derivatives"
ARCHIVE = "https://data.binance.vision/data/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip"
PATH = os.path.join("cache", "binance_funding_relay.json")
MARKET = "Binance (Futures)"
WINDOW_S = 9 * 60                   # sample in the last nine minutes before a boundary
KEEP = 60                           # settled records kept per symbol


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_settlement(now, hours):
    step = int(hours) * 3600
    return (int(now) // step + 1) * step


def interval_hours(symbol, now, fetch=None):
    """the symbol's funding interval from Binance's public monthly archive (last month's file): 4 or 8 hours."""
    from ..data.http import get
    fetch = fetch or (lambda url: get(url, timeout=30, tries=2, as_bytes=True))
    d = datetime.fromtimestamp(now, tz=timezone.utc)
    y, m = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    raw = fetch(ARCHIVE.format(s=symbol, m="%04d-%02d" % (y, m)))
    z = zipfile.ZipFile(io.BytesIO(raw))
    rows = z.read(z.namelist()[0]).decode().strip().splitlines()
    hours = [int(r.split(",")[1]) for r in rows[1:] if r.count(",") >= 2]
    return max(set(hours), key=hours.count) if hours else 8


def sample(root, symbols, now, fetch=None, interval=None):
    """one relay read: each symbol's estimate kept as pending for its next settlement when that settlement is within
    WINDOW_S. Returns the symbols sampled."""
    from ..data.http import get
    fetch = fetch or (lambda: get(RELAY_URL, {"include_tickers": "unexpired"}, timeout=60, tries=2))
    path = os.path.join(root, PATH)
    st = read_json(path, {}) or {}
    _promote(st, now)              # settled estimates first: a 4 h symbol's next sample would overwrite its pending one
    ints = st.setdefault("intervals", {})
    due = []
    for s in symbols:
        if s not in ints:
            try:
                ints[s] = (interval or interval_hours)(s, now)
            except Exception:
                continue
        if next_settlement(now, ints[s]) - now <= WINDOW_S:
            due.append(s)
    if not due:
        write_json_atomic(path, st)
        return []
    rows = fetch() or []
    rates = {r.get("symbol"): r.get("funding_rate") for r in rows
             if isinstance(r, dict) and r.get("market") == MARKET and r.get("contract_type") == "perpetual"}
    pend = st.setdefault("pending", {})
    got = []
    for s in due:
        v = rates.get(s)
        if v is None:
            continue
        pend[s] = {"settle_at": next_settlement(now, ints[s]), "rate": float(v) / 100.0, "observed_at": now}
        got.append(s)
    _promote(st, now)
    write_json_atomic(path, st)
    return got


def _promote(st, now):
    for s, p in list((st.get("pending") or {}).items()):
        if now >= p["settle_at"]:
            recs = st.setdefault("records", {}).setdefault(s, [])
            if not recs or recs[-1]["settle_at"] != p["settle_at"]:
                recs.append(dict(p))
                del recs[:-KEEP]
            st["pending"].pop(s)


def records(root, symbol, now):
    """the symbol's settled-funding records as the R19 evaluator reads them (oldest first)."""
    st = read_json(os.path.join(root, PATH), {}) or {}
    _promote(st, now)
    out = []
    for r in (st.get("records") or {}).get(symbol, []):
        out.append({"symbol": symbol, "settled_at": _iso(r["settle_at"]), "rate": "%.10f" % r["rate"],
                    "received_at": _iso(max(r["settle_at"], r["observed_at"])), "observed_public_endpoint": True,
                    "source": "coingecko relay of Binance (Futures) funding_rate, estimate observed %s"
                              % _iso(r["observed_at"])})
    return out


def job(engine, now=None):
    from ..sleeves.families import r19_crypto as F
    now = now or time.time()
    syms = sorted({u for s in F.sleeves() if (s.CONFIG.params or {}).get("family") not in
                   ("breakout_base", "absorption_base") for u in (s.CONFIG.universe or ())})
    got = sample(engine.root, syms, now)
    return {"symbols": syms, "sampled": got}
