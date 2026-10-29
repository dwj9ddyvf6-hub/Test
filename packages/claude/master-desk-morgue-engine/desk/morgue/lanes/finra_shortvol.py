"""B52, FINRA's per-name daily short-sale volume as a stored history (DEEP studies need years of it; the DIX only keeps the day).

FINRA posts one file a trading day (FNQC consolidated: symbol, short volume, total volume). The Morgue parses it for the DIX
(map_dix.parse_fnqc); this lane keeps EVERY name's pair for each day under state/morgue/shortvol/<date>.json.gz so a per-name
series can be read back, and backfills older days a few files a run at the host's pace (cdn.finra.org, 0.1 s a request, the
desk's data layer). A stored day is never rewritten. Roughly 11,000 names a day is about 70 KB gzipped, so a year of files is
under 20 MB; rotation keeps KEEP_DAYS.

Point in time: a file for day D posts after D's close, so history(..., before=D') returns only days strictly before D'.

short_pressure is Prospero's published sign logic with the desk's own measures (the vendor publishes none): a rising price
under heavy short demand is resilience, not weakness. Measures, all OURS and labelled: demand = the mean short ratio of the last
20 sessions and its z against the name's earlier history; resilience = the 20-session return and the volume trend. FINRA's terms
restrict robots, databases and trade-prediction models; the owner accepted that with full information (DAT-09) and the risk is
carried in the registry (R1)."""
import gzip
import json
import math
import os
from datetime import timedelta

from ... import calendar as cal
from ...data import http
from .. import fetch, map_dix, state_path

DIR = "shortvol"
KEEP_DAYS = 800
SOURCE = "FINRA FNQC daily short-sale volume files, kept per name"
DELAY = "a day's file posts after that day's close; the history is read for later sessions only"
RECENT = 20
MIN_DAYS = 60


def _file(root, day):
    return state_path(root, os.path.join(DIR, f"{day}.json.gz"))


def days(root):
    try:
        return sorted(n[:-8] for n in os.listdir(state_path(root, DIR)) if n.endswith(".json.gz"))
    except OSError:
        return []


def store_day(root, day, data):
    """keep one day's {symbol: (short, total)} -> True, or False when that day is stored already or `data` is empty"""
    p = _file(root, day)
    if os.path.exists(p) or not data:
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
        json.dump({"date": day, "names": {k: [round(v[0], 1), round(v[1], 1)] for k, v in data.items()}}, fh,
                  separators=(",", ":"))
    os.replace(tmp, p)
    gone = days(root)[:-KEEP_DAYS]
    for d in gone:
        try:
            os.remove(_file(root, d))
        except OSError:
            pass
    return True


def read_day(root, day):
    try:
        with gzip.open(_file(root, day), "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, EOFError):
        return None


def fetch_day(day, getter=None):
    """one day's FNQC text, or None when FINRA has no file for it (its CDN answers 403 or 404 for a day not posted); any other
    refusal or transport failure is raised, not read as 'no file'"""
    try:
        return fetch.text(fetch.FNQC.format(yyyymmdd=day.strftime("%Y%m%d")), getter, timeout=45, tries=2)
    except http.HttpError as e:
        if e.status in (403, 404):
            return None
        raise


def backfill(root, end, getter=None, want=260, max_new=25):
    """walk back from `end` (a date; its own file may not be posted yet) over trading days, fetching the days not yet stored until
    `want` days are held or `max_new` files were fetched this run -> {"new","held","missing","error"}; a refusal stops the run
    and is reported, it does not become a gap"""
    held = set(days(root))
    new, missing, error = 0, [], None
    d, seen = end, 0
    while seen < want + 10 and len(held) < want and new < max_new:
        if cal.is_trading_day(d):
            seen += 1
            iso = d.isoformat()
            if iso not in held:
                try:
                    text = fetch_day(d, getter)
                except http.HttpError as e:
                    error = f"{type(e).__name__}: {str(e)[:100]}"
                    break
                data = map_dix.parse_fnqc(text) if text else {}
                if data and store_day(root, iso, data):
                    new += 1
                    held.add(iso)
                else:
                    missing.append(iso)
        d -= timedelta(days=1)
    return {"new": new, "held": len(held), "missing": missing, "error": error}


def history(root, symbol, before, n=300):
    """[(date, short, total)] ascending for one name over the stored days strictly before `before` (an ISO date), the last n"""
    sym = map_dix.norm(symbol)
    out = []
    for d in [x for x in days(root) if x < before][-n:]:
        doc = read_day(root, d)
        v = ((doc or {}).get("names") or {}).get(sym)
        if v and v[1] > 0:
            out.append((d, float(v[0]), float(v[1])))
    return out


def _mean(xs):
    return sum(xs) / len(xs)


def short_pressure(hist, bars, as_of=None):
    """Prospero's Short Pressure with the desk's measures. hist: [(date, short, total)] ascending; bars: [{"date","c","v"}]
    ascending (completed sessions). -> a stamped dict: demand (mean ratio of the last 20), demand_z (against the earlier days),
    ret_20, vol_trend (mean volume of the last 5 over the last 20), label absorbed / pressed / light / neutral, and score = demand_z
    signed by the 20-day return when demand is high (z >= 1), else 0. no_data with the reason under 60 days or without bars."""
    def no(why):
        return {"status": "no_data", "reason": why, "as_of": as_of, "source": SOURCE, "delay": DELAY}
    if len(hist) < MIN_DAYS:
        return no(f"{len(hist)} stored days of short volume, {MIN_DAYS} needed")
    ratios = [s / t for _, s, t in hist]
    recent, base = ratios[-RECENT:], ratios[:-RECENT]
    mu = _mean(base)
    sd = math.sqrt(_mean([(x - mu) ** 2 for x in base]))
    demand = _mean(recent)
    z = None if sd <= 0 else (demand - mu) / sd
    last = hist[-1][0]
    by = [b for b in bars if b.get("date") and b["date"] <= last]
    if len(by) < RECENT + 1 or by[-1]["date"] != last or not by[-RECENT - 1]["c"]:
        return no("fewer than 21 daily bars ending on the last short-volume day")
    ret = by[-1]["c"] / by[-RECENT - 1]["c"] - 1.0
    vols = [b["v"] for b in by[-RECENT:] if b.get("v") is not None]
    vt = (_mean(vols[-5:]) / _mean(vols)) if len(vols) == RECENT and _mean(vols) > 0 else None
    if z is None:
        return no("the earlier short ratio never varied: no baseline spread")
    high = z >= 1.0
    label = ("absorbed" if ret > 0 else "pressed") if high else ("light" if z <= -1.0 else "neutral")
    return {"status": "ok", "as_of": as_of or last, "source": SOURCE, "delay": DELAY, "demand": round(demand, 4),
            "demand_z": round(z, 3), "ret_20": round(ret, 4), "vol_trend": (None if vt is None else round(vt, 3)),
            "label": label, "score": round(z * (1 if ret > 0 else -1), 3) if high else 0.0, "days": len(hist),
            "measures": "the desk's own: the vendor publishes the sign logic and no formula"}
