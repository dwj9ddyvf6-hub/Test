"""EDGAR public-float market cap for rule_1d_cyan_smallcap — the old desk/mcap_edgar.py (research definition,
v4.mjs edgar4): log10(EntityPublicFloat x C[t] / C[float end]), the float being the latest SEC XBRL
EntityPublicFloat (USD, > $1M) whose period end lies in [bar - 730d, bar - 290d], the ratio taken on
split-adjusted closes (the close at / just before the float's end, and at / before the bar). Fail closed:
no CIK, no qualifying frame or a missing price -> None (the caller skips the signal).

Ticker -> CIK: SEC company_tickers.json, cached 31 days (the old desk rebuilt its static map from the same
file); companyfacts per CIK cached 7 days (a stale cache beats nothing). Prices: the genome's split-adjusted
daily bars (the old fetched Alpaca adjustment=split bars from the float's end - 20 days)."""
import json
import math
import os
import time
from datetime import date, datetime, timedelta, timezone

from ..data.http import get
from ..util import read_json, write_json_atomic

LAG_DAYS = 290
MAX_AGE_DAYS = 730
MIN_FLOAT_USD = 1e6
FACTS_TTL_DAYS = 7
MAP_TTL_DAYS = 31


def _dir(root, *parts):
    d = os.path.join(root, "cache", "mcap", *parts)
    os.makedirs(d, exist_ok=True)
    return d


def cik_map(root, now=None, fetch=get):
    """{TICKER: 10-digit CIK} from SEC company_tickers.json (cached)."""
    now = now or time.time()
    path = os.path.join(_dir(root), "ticker_cik.json")
    m = read_json(path, None)
    if m and now - os.path.getmtime(path) < MAP_TTL_DAYS * 86400:
        return m
    try:
        raw = fetch("https://www.sec.gov/files/company_tickers.json")
        fresh = {str(r["ticker"]).upper(): "%010d" % int(r["cik_str"]) for r in (raw or {}).values()}
        if fresh:
            write_json_atomic(path, fresh)
            return fresh
    except Exception:
        pass
    return m or {}


def cik_for(m, sym):
    s = sym.upper()
    return m.get(s) or m.get(s.replace(".", "-")) or m.get(s.replace("-", "."))


def float_frames(root, cik, now=None, fetch=get):
    """[(end_iso, val_usd)] EntityPublicFloat frames, ascending; [] on miss."""
    now = now or time.time()
    path = os.path.join(_dir(root, "facts"), f"CIK{cik}.json")
    facts = None
    if os.path.exists(path) and now - os.path.getmtime(path) < FACTS_TTL_DAYS * 86400:
        facts = read_json(path, None)
    if facts is None:
        try:
            raw = fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        except Exception:
            raw = None
        if raw:
            facts = raw
            write_json_atomic(path, raw)
        else:
            facts = read_json(path, None)                  # stale beats nothing
    try:
        units = facts["facts"]["dei"]["EntityPublicFloat"]["units"]["USD"]
    except Exception:
        return []
    out = []
    for f in units:
        try:
            end, val = f["end"][:10], float(f["val"])
        except Exception:
            continue
        if val > MIN_FLOAT_USD and end:
            out.append((end, val))
    out.sort()
    return out


def log_mcap(sym, bar_date, cmap, frames_fn, closes):
    """(log10 mcap | None, detail). closes: [(date_iso, split-adjusted close)] ascending."""
    try:
        bd = date.fromisoformat(bar_date)
    except (ValueError, TypeError, AttributeError):
        return None, f"malformed bar_date {bar_date!r} (fail closed)"
    cik = cik_for(cmap, sym)
    if not cik:
        return None, "no CIK for ticker"
    frames = frames_fn(cik)
    if not frames:
        return None, f"no EntityPublicFloat frames (CIK {cik})"
    lo = (bd - timedelta(days=MAX_AGE_DAYS)).isoformat()
    hi = (bd - timedelta(days=LAG_DAYS)).isoformat()
    elig = [(e, v) for e, v in frames if lo <= e <= hi]
    if not elig:
        return None, f"no float frame with end in [{lo},{hi}] ({len(frames)} frames total)"
    end, val = elig[-1]
    start = (date.fromisoformat(end) - timedelta(days=20)).isoformat()
    bars = [(d, c) for d, c in closes if d >= start and c > 0]
    if not bars:
        return None, "no split-adjusted bars"
    px_end = px_today = None
    for d, c in bars:
        if d <= end:
            px_end = c
        else:
            break
    for d, c in bars:
        if d <= bar_date:
            px_today = c
        else:
            break
    if not px_end or not px_today:
        return None, f"price missing (end={end}, px_end={px_end}, px_today={px_today})"
    mcap = val * px_today / px_end
    if not (mcap > 0) or not math.isfinite(mcap):
        return None, "non-positive market cap"
    return math.log10(mcap), f"float ${val:,.0f} end={end} CIK={cik} px {px_end:.2f}->{px_today:.2f}"
