"""The verified public event timestamps FREE_OPT_RELEASE_V1 reads (the Aurelia source desk's run() always passed
events=[]: no release calendar existed in its tree). Built from the official public schedules and cached by a job.

  sources  FRED's release calendar (fred.stlouisfed.org/releases/calendar?rid=<id>&y=<year>: the St. Louis Fed's
           schedule of each agency's release dates and times, in US Central time, mirroring BLS's — bls.gov refuses
           automated requests): the Consumer Price Index (rid 10) and the Employment Situation (rid 50), 08:30 ET;
           the Federal Reserve's FOMC meeting calendar (federalreserve.gov/monetarypolicy/fomccalendars.htm): the
           policy statement at 2:00 pm ET on the last day of each scheduled meeting (notation votes and unscheduled
           meetings are not scheduled releases and are skipped).
  event    {"name", "release_at" (ISO, UTC), "session" (the ET trading session that holds the straddle into the
           release: the last session that opens before it — the previous trading day for an 08:30 ET release, the
           same day for the 2:00 pm FOMC statement), "verified": True (parsed from the official schedule page, never
           inferred), "source" (the URL), "source_sha256" (the fetched page)}.
  job      release_calendar (desk/sleeves/families/femto_specs.JOBS): this year's and next year's pages, parsed and
           written to cache/release_calendar.json atomically; a page that fails keeps that page's last events.
  feed     release_events: the cached events ([] until the job has written them)."""
import hashlib
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic

FRED = "https://fred.stlouisfed.org/releases/calendar?rid={rid}&y={year}"
FOMC = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
RELEASES = {10: "CPI", 50: "Employment Situation"}
CT = ZoneInfo("America/Chicago")
FILE = os.path.join("cache", "release_calendar.json")
_DAY = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+([A-Z][a-z]+ \d{1,2}, \d{4})")
_TIME = re.compile(r"(\d{1,2}:\d{2}\s*[ap]m)")
_LINK = re.compile(r'href="/release\?rid=(\d+)"[^>]*>([^<]+)<')


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def session_of(ts):
    """the trading session that holds a straddle into a release at `ts`: the last session that opens before it. A
    release before a day's open (CPI and the Employment Situation at 08:30 ET) or on a closed day belongs to the
    previous trading session; one during or after a session (the FOMC statement at 2:00 pm ET) to that session."""
    d = cal._as_date(float(ts))
    if cal.is_trading_day(d) and float(ts) >= cal.session_open(d):
        return d.isoformat()
    return cal.prev_trading_day(d).isoformat()


def parse_fred(html, rid, name):
    """FRED's calendar page of one release -> [{"name", "release_at"}] (its times are US Central)."""
    out, day = [], None
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html or "", re.S):
        m = _DAY.search(row)
        if m:
            day = datetime.strptime(m.group(1), "%B %d, %Y").date()
            continue
        t, a = _TIME.search(row), _LINK.search(row)
        if day is None or not t or not a or a.group(1) != str(rid):
            continue
        local = datetime.strptime("%s %s" % (day.isoformat(), t.group(1).replace(" ", "")), "%Y-%m-%d %I:%M%p")
        at = local.replace(tzinfo=CT).astimezone(timezone.utc)
        out.append({"name": name, "release_at": at.isoformat()})
    return out


def _month(name):
    return datetime.strptime(name.strip()[:3], "%b").month


def parse_fomc(html):
    """the Fed's FOMC calendar page -> [{"name": "FOMC statement", "release_at"}]: 2:00 pm ET on each scheduled
    meeting's last day (a meeting across two months, e.g. "Jan/Feb" "31-1", ends in the second)."""
    out = []
    heads = list(re.finditer(r"(\d{4}) FOMC Meetings", html or ""))
    for i, h in enumerate(heads):
        year = int(h.group(1))
        seg = html[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(html)]
        months = re.findall(r'fomc-meeting__month[^>]*>\s*<strong>([^<]*)</strong>', seg)
        dates = re.findall(r'fomc-meeting__date[^>]*>([^<]*)<', seg)
        for mon, d in zip(months, dates):
            m = re.fullmatch(r"\s*(\d{1,2})(?:-(\d{1,2}))?\*?\s*", d)
            if not m:                                        # "(notation vote)", "(unscheduled)": not a release
                continue
            first, last = int(m.group(1)), int(m.group(2) or m.group(1))
            parts = [p for p in mon.split("/") if p.strip()]
            month = _month(parts[-1] if (len(parts) > 1 and last < first) else parts[0])
            at = datetime(year, month, last, 14, 0, tzinfo=ET).astimezone(timezone.utc)
            out.append({"name": "FOMC statement", "release_at": at.isoformat()})
    return out


def build(pages, previous=None):
    """pages: {url: html | None (the fetch failed)} -> the calendar document {"events", "sources"}; a failed page
    keeps that page's events from `previous`."""
    events, sources = [], {}
    prev = (previous or {}).get("events") or []
    for url, html in pages.items():
        if html is None:
            kept = [e for e in prev if e.get("source") == url]
            sources[url] = {"ok": False, "kept": len(kept)}
            events += kept
            continue
        if url.startswith(FOMC):
            got = parse_fomc(html)
        else:
            rid = int(re.search(r"rid=(\d+)", url).group(1))
            got = parse_fred(html, rid, RELEASES.get(rid, "release %d" % rid))
        h = _sha(html)
        sources[url] = {"ok": True, "events": len(got), "sha256": h}
        for e in got:
            ts = datetime.fromisoformat(e["release_at"]).timestamp()
            events.append(dict(e, session=session_of(ts), verified=True, source=url, source_sha256=h))
    seen, uniq = set(), []
    for e in sorted(events, key=lambda e: (e["release_at"], e["name"])):
        k = (e["name"], e["release_at"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return {"events": uniq, "sources": sources}


def urls(now):
    y = datetime.fromtimestamp(float(now), tz=ET).year
    return [FRED.format(rid=rid, year=yy) for rid in RELEASES for yy in (y, y + 1)] + [FOMC]


def job(root, now, fetch=None):
    """fetch every page, build, write cache/release_calendar.json; -> a summary."""
    if fetch is None:
        from ..data.http import get

        def fetch(url):
            return get(url, as_text=True, timeout=30)
    path = os.path.join(root, FILE)
    previous = read_json(path, {}) or {}
    pages = {}
    for url in urls(now):
        try:
            pages[url] = fetch(url) or None
        except Exception:
            pages[url] = None
    doc = build(pages, previous)
    doc["fetched_at"] = datetime.fromtimestamp(float(now), tz=timezone.utc).isoformat()
    write_json_atomic(path, doc)
    return {"events": len(doc["events"]), "sources_ok": sum(1 for s in doc["sources"].values() if s["ok"]),
            "sources": len(doc["sources"])}


def load(root):
    """the cached events ([] until the job has written them)."""
    return list((read_json(os.path.join(root, FILE), {}) or {}).get("events") or [])
