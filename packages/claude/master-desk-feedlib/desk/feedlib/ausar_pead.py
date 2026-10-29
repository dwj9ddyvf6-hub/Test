"""Ausar PEAD producer — the earnings events the R19 PEAD option books (OPT_PEAD_*) need, which the source runtime
never produced (its snapshot carried no earnings_events / earnings_history; the books stayed blocked).

The research that defined the books (R18 options/causal_pead.py over independent/sources/earnings_events.parquet,
built by 01_nasdaq_backfill.py + 02_universe.py) took its events from Nasdaq's public earnings calendar
(api.nasdaq.com/api/calendar/earnings?date=YYYY-MM-DD; one row per company reporting on that date, with a
pre-market / after-hours / not-supplied time bucket) and its universe as the calendar symbols that are tradable US
equities. This module keeps that calendar forward and backward:

  calendar ...... every weekday from the first day of the fourth complete quarter before today's quarter through
                  today + AHEAD_DAYS, fetched once (dates from 3 days back on: re-fetched each run); each row's first
                  observation clock is kept (first_seen) and its exact JSON hashed (source_sha256)
  universe ...... calendar symbols that look like a US common-stock ticker (1-5 capitals) and, when the desk holds
                  Alpaca credentials, are active tradable Alpaca US equities (the research's intersection)
  events ........ (symbol, event_date) on exchange sessions, event_id "<symbol>:<event_date>";
                  first_published_at = the row's first observation; announcement_at = the calendar session's bound
                  for its bucket (after-hours: 16:00 ET of the event date; pre-market / not supplied: 00:00 ET of
                  the event date — the calendar gives the session and bucket, not the release clock)
  history ....... every event whose event+1 session close is known: surprise = close(t+1) / close(t-1) -
                  SPY close(t+1) / SPY close(t-1) on the desk's split-adjusted daily bars (causal_pead.py), usable at
                  the t+1 close; a backfilled event (first seen after its announcement bound) carries that bound as
                  its publication clock; one run fetches bars for at most 1,200 names (the next entries first, then
                  the newest unresolved events; a name without bars is asked again a week later)
  candidates .... events entering within the next sessions, pre-evaluated with the vendored evaluator's own
                  build_pead_event / pead_signal so the books fetch bars, quotes and chains only for passing names

The job `ausar_pead` (desk/sleeves/families/ausar_options.JOBS) runs it each evening after the close; the books read
<root>/cache/ausar_pead/pead.json through the feed `ausar_pead`."""
import hashlib
import json
import os
import re
import time
from datetime import date, datetime, timedelta, timezone

from .. import calendar as cal
from ..data.http import get
from ..util import ET, read_json, write_json_atomic
from ..vendor.ausar_r19 import r19_options as vo
from .earnings import HEADERS

URL = "https://api.nasdaq.com/api/calendar/earnings"
TICKER = re.compile(r"^[A-Z]{1,5}$")
AHEAD_DAYS = 10                  # calendar dates observed ahead of their announcements
REFRESH_BACK_DAYS = 3            # recent dates re-read each run (late additions keep their own first_seen)
PACE_S = 1.0                     # the research backfill's ~1 request / second politeness
BARS_N = 400                     # daily bars covering the five-quarter window (+ the 20-session event window)
BARS_BUDGET = 1200               # names whose bars one run fetches: the next entries first, then the newest unresolved
RETRY_S = 7 * 86400              # a name that returned no bars is asked again a week later
UTC_ISO = "%Y-%m-%dT%H:%M:%S+00:00"


def out_dir(root):
    return os.path.join(root, "cache", "ausar_pead")


def _iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(UTC_ISO)


def _sha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def window_start(today):
    """first day of the fourth complete quarter before `today`'s quarter (the prior-four-quarter history)."""
    q0 = date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
    y, m = q0.year, q0.month - 12
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, 1)


def announcement_bound(event_date, bucket):
    d = date.fromisoformat(event_date)
    if bucket == "time-after-hours":
        return datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET)
    return datetime(d.year, d.month, d.day, 0, 0, tzinfo=ET)


class Calendar:
    """the per-date calendar cache: {date: {"fetched_at", "rows": {symbol: {"row", "first_seen", "sha"}}}}."""

    def __init__(self, root, clock=time.time, fetch=get, sleep=time.sleep):
        self.path = os.path.join(out_dir(root), "calendar.json")
        self.clock, self.fetch, self.sleep = clock, fetch, sleep
        self.days = read_json(self.path, {}) or {}

    def save(self):
        write_json_atomic(self.path, self.days)

    def refresh(self, start, end, budget=None):
        """fetch every weekday in [start, end] not yet held, and those from today - REFRESH_BACK_DAYS on."""
        now = self.clock()
        today = datetime.fromtimestamp(now, tz=ET).date()
        d, n, errors = start, 0, []
        while d <= end:
            ds = d.isoformat()
            if d.weekday() < 5 and (ds not in self.days or d >= today - timedelta(days=REFRESH_BACK_DAYS)):
                if budget is not None and n >= budget:
                    break
                try:
                    doc = self.fetch(URL, {"date": ds}, headers=HEADERS, timeout=30, tries=3)
                    rows = (((doc or {}).get("data") or {}).get("rows")) or []
                    got = self.days.setdefault(ds, {"rows": {}})
                    seen = self.clock()
                    for r in rows:
                        sym = str(r.get("symbol") or "").strip().upper()
                        if not sym:
                            continue
                        have = got["rows"].get(sym)
                        if have is None:
                            got["rows"][sym] = {"row": r, "first_seen": seen, "sha": _sha(r)}
                        else:
                            have["row"] = r
                    got["fetched_at"] = seen
                except Exception as e:              # one date's failure is recorded; the next run retries it
                    errors.append(f"{ds}: {type(e).__name__}: {str(e)[:120]}")
                n += 1
                self.sleep(PACE_S)
            d += timedelta(days=1)
        return n, errors


def events(days, universe=None):
    """calendar rows -> raw events on exchange sessions (the research's (event_date, symbol) de-duplication)."""
    out = []
    for ds in sorted(days):
        if not cal.is_trading_day(date.fromisoformat(ds)):
            continue
        for sym, r in sorted((days[ds].get("rows") or {}).items()):
            if not TICKER.match(sym) or (universe is not None and sym not in universe):
                continue
            ann = announcement_bound(ds, (r.get("row") or {}).get("time"))
            first = datetime.fromtimestamp(float(r["first_seen"]), tz=ET)
            out.append({"event_id": f"{sym}:{ds}", "symbol": sym, "event_date": ds,
                        "time": (r.get("row") or {}).get("time"),
                        "first_published_at": first.isoformat(), "announcement_at": ann.isoformat(),
                        "observed_before_announcement": first <= ann, "source_sha256": r["sha"]})
    return out


def daily_rows(bars, today):
    """desk daily bars -> the evaluator's daily_bars rows (completed sessions strictly before `today`)."""
    from ..sleeves.families.ausar_options import daily_rows as rows_of
    return rows_of(bars, today)


def resolve(ev, stock, spy):
    """the research surprise of one event on {session: row} maps; None while t+1 is not complete."""
    d = date.fromisoformat(ev["event_date"])
    a, b = cal.prev_trading_day(d).isoformat(), cal.next_trading_day(d).isoformat()
    if ev["event_date"] not in stock or a not in stock or b not in stock or a not in spy or b not in spy:
        return None
    try:
        s = float(stock[b]["close"]) / float(stock[a]["close"]) - float(spy[b]["close"]) / float(spy[a]["close"])
    except (ZeroDivisionError, TypeError, ValueError):
        return None
    if s != s or s in (float("inf"), float("-inf")):
        return None
    avail = max(stock[b]["usable_after"], spy[b]["usable_after"])
    pub = ev["first_published_at"] if ev["observed_before_announcement"] else ev["announcement_at"]
    return {"event_id": ev["event_id"], "symbol": ev["symbol"], "event_date": ev["event_date"],
            "surprise": repr(s), "signal_available_at": avail, "first_published_at": pub,
            "source_sha256": ev["source_sha256"], "backfilled": not ev["observed_before_announcement"]}


def run(root, hub, clock=time.time, fetch=get, sleep=time.sleep, tradable=None, budget=None):
    """one producer run: calendar -> events -> resolved history + pre-evaluated candidates -> pead.json."""
    t0 = clock()
    now_dt = datetime.fromtimestamp(t0, tz=ET)
    today = now_dt.date()
    c = Calendar(root, clock=clock, fetch=fetch, sleep=sleep)
    n, errors = c.refresh(window_start(today), today + timedelta(days=AHEAD_DAYS), budget=budget)
    c.save()
    evs = events(c.days, tradable)
    prev = read_json(os.path.join(out_dir(root), "pead.json"), {}) or {}
    resolved = {h["event_id"]: h for h in prev.get("history") or []}
    # the bars' exclusive bound: after a session's close its daily bar is complete (the evening run resolves it)
    if cal.is_trading_day(today) and t0 < cal.session_close(today):
        session = today.isoformat()
    else:
        session = cal.next_trading_day(today).isoformat()
    lo = window_start(today).isoformat()
    recent = cal.prev_trading_day(today, 10).isoformat()
    no_bars = {k: v for k, v in (prev.get("no_bars") or {}).items() if t0 - float(v) < RETRY_S}
    need = sorted({e["symbol"] for e in evs if e["event_date"] >= recent})
    for e in sorted(evs, key=lambda e: e["event_date"], reverse=True):
        if len(need) >= BARS_BUDGET:
            break
        if e["event_id"] not in resolved and lo <= e["event_date"] < session and e["symbol"] not in no_bars \
                and e["symbol"] not in need:
            need.append(e["symbol"])
    bars = hub.bars("equity_split", "1d", need + ["SPY"], BARS_N) if need else {}
    no_bars.update({sym: t0 for sym in need if not bars.get(sym)})
    spy = {r["session"]: r for r in daily_rows(bars.get("SPY") or [], session)}
    for e in evs:
        if e["event_id"] in resolved or e["event_date"] >= session or e["event_date"] < lo:
            continue
        stock = {r["session"]: r for r in daily_rows(bars.get(e["symbol"]) or [], session)}
        h = resolve(e, stock, spy)
        if h:
            resolved[e["event_id"]] = h
    history = sorted((h for h in resolved.values() if h["event_date"] >= lo), key=lambda h: (h["event_date"], h["symbol"]))
    # candidates: events whose entry (event + 3 sessions) is still ahead or today, pre-evaluated as the books will
    calendar = {"all_sessions": _sessions(today), "session": session}
    snap = {"now": _iso(t0), "calendar": calendar, "daily_bars": {}}
    cands = []
    for e in evs:
        d = date.fromisoformat(e["event_date"])
        entry = cal.next_trading_day(d, 3).isoformat()
        if entry < session:
            continue
        row = dict(e, entry_session=entry)
        rows = daily_rows(bars.get(e["symbol"]) or [], session)
        snap["daily_bars"] = {e["symbol"]: rows, "SPY": daily_rows(bars.get("SPY") or [], session)}
        try:
            built = vo.build_pead_event({k: e[k] for k in ("event_id", "symbol", "event_date", "first_published_at",
                                                           "announcement_at", "source_sha256")}, snap)
            sig = vo.pead_signal(built, history, vo.stamp(snap["now"]))
            row.update(pre_pass=bool(sig["pass"]), surprise=built["surprise"], threshold=str(sig["threshold"]),
                       n_prior=sig["n_prior_resolved"])
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            row.update(pre_pass=None, pre_reason=str(exc)[:120])
        cands.append(row)
    doc = {"computed_at": _iso(clock()), "session": session, "window_start": lo, "calendar_requests": n,
           "calendar_errors": errors[-20:], "calendar_dates": len(c.days), "events": len(evs),
           "history": history, "candidates": cands, "universe_filter": "alpaca_tradable" if tradable else "ticker",
           "bars_requested": len(need), "no_bars": no_bars}
    write_json_atomic(os.path.join(out_dir(root), "pead.json"), doc)
    return {"requests": n, "errors": len(errors), "events": len(evs), "history": len(history),
            "candidates": len(cands), "passing": sum(1 for x in cands if x.get("pre_pass"))}


def _sessions(today):
    out, d = [], today - timedelta(days=700)
    end = today + timedelta(days=60)
    while d <= end:
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


_DOC = {}


def load(root):
    """the latest pead.json (re-read when its mtime changes)."""
    p = os.path.join(out_dir(root), "pead.json")
    try:
        m = os.path.getmtime(p)
    except OSError:
        return None
    if _DOC.get("path") != p or _DOC.get("mtime") != m:
        _DOC.update(path=p, mtime=m, doc=read_json(p, None))
    return _DOC.get("doc")
