"""Point-in-time earnings announcements for the Griffith PEAD candidates (event_research).

The source registered PEAD_1_0_0, MOMENTUM_PEAD_COMBINATION_1_0_0 and PEAD_SUE_20D_1_0_0 on a timestamped
consensus + actual lane (r4_candidate_evidence.normalize_earnings: Alpha Vantage EARNINGS rows -> eps_estimate,
eps_actual, event time, known time; surpriseFraction = (actual - estimate) / |estimate|; PEAD_SUE_20D needs at least
eight prior point-in-time surprises). Alpha Vantage needs a key the desk does not hold, so this producer serves the
same quantities from the best free public source — Nasdaq's earnings calendar, archived by date (api.nasdaq.com
/api/calendar/earnings?date=D: per reporter the reported EPS, the consensus EPS forecast, the analyst count and,
for the current days, the release time pre-market / after-hours): a named divergence of the three sleeves.

Cache: <root>/cache/griffith_earnings/<YYYY-MM-DD>.json, one calendar page per weekday. `job()` back-fills three
years once and refreshes the last few days every morning (the pages of recent days fill in as companies report);
`announcements()` reads the cache only; `refresh_today()` re-reads today's and the previous session's pages at the
open (the pre-market reporters' actuals)."""
import json
import os
import re
import time
from datetime import date, timedelta

from .. import calendar as cal
from ..data.http import get
from .earnings import HEADERS

URL = "https://api.nasdaq.com/api/calendar/earnings"
BACKFILL_DAYS = 3 * 366
REFRESH_DAYS = 5


def cache_dir(root):
    return os.path.join(root, "cache", "griffith_earnings")


def _num(x):
    if x in (None, "", "N/A", "--"):
        return None
    try:
        return float(re.sub(r"[$,()\s]", "", str(x))) * (-1 if str(x).strip().startswith("(") else 1)
    except ValueError:
        return None


def fetch_page(day, fetch=get):
    doc = fetch(URL, {"date": day}, headers=HEADERS, tries=3, timeout=30)
    rows = ((doc or {}).get("data") or {}).get("rows") or []
    out = []
    for r in rows:
        sym = str(r.get("symbol") or "").strip().upper()
        if not sym:
            continue
        out.append({"symbol": sym, "eps": _num(r.get("eps")), "consensus": _num(r.get("epsForecast")),
                    "estimates": _num(r.get("noOfEsts")), "time": r.get("time"),
                    "quarter": r.get("fiscalQuarterEnding")})
    return out


def _path(root, day):
    return os.path.join(cache_dir(root), f"{day}.json")


def store_page(root, day, rows, now):
    os.makedirs(cache_dir(root), exist_ok=True)
    tmp = _path(root, day) + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"date": day, "fetched_at": now, "rows": rows}, f)
    os.replace(tmp, _path(root, day))


def load_page(root, day):
    try:
        with open(_path(root, day)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def weekdays(start, end):
    d, out = start, []
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def job(root, now=None, fetch=get, max_pages=None, clock=time.time):
    """back-fill missing pages (BACKFILL_DAYS) and re-read the last REFRESH_DAYS weekdays."""
    now = now or clock()
    today = cal._as_date(now)
    days = weekdays(today - timedelta(days=BACKFILL_DAYS), today)
    recent = set(days[-REFRESH_DAYS:])
    todo = [d for d in reversed(days) if d in recent or load_page(root, d) is None]
    done, errors = 0, 0
    for d in todo[:max_pages] if max_pages else todo:
        try:
            store_page(root, d, fetch_page(d, fetch), clock())
            done += 1
        except Exception:
            errors += 1
    return {"pages": done, "errors": errors, "missing": sum(1 for d in days if load_page(root, d) is None)}


def refresh_today(root, now, fetch=get):
    """at the open: today's page (pre-market actuals) and the previous session's (after-hours actuals)."""
    d = cal._as_date(now)
    for day in (d.isoformat(), cal.prev_trading_day(d).isoformat()):
        try:
            store_page(root, day, fetch_page(day, fetch), now)
        except Exception:
            pass


def announcements(root, symbols, until_day, days=BACKFILL_DAYS):
    """{SYM: [{date, eps, consensus, time, quarter}] ascending} from the cached pages dated <= until_day."""
    want = set(symbols)
    end = date.fromisoformat(until_day)
    out = {}
    for d in weekdays(end - timedelta(days=days), end):
        page = load_page(root, d)
        for r in (page or {}).get("rows") or []:
            if r["symbol"] in want:
                out.setdefault(r["symbol"], []).append(dict(r, date=d))
    return out


def known_events(root, symbols, now):
    """announcements whose actual is public before this session's open: every report dated before today, and
    today's pre-market reports (point in time: an after-hours or untimed report of today waits for tomorrow)."""
    today = cal._as_date(now).isoformat()
    out = {}
    for sym, rows in announcements(root, symbols, today).items():
        keep = [r for r in rows if r["date"] < today or (r["date"] == today and r.get("time") == "time-pre-market")]
        keep = [r for r in keep if r.get("eps") is not None and r.get("consensus") is not None]
        if keep:
            out[sym] = keep
    return out
