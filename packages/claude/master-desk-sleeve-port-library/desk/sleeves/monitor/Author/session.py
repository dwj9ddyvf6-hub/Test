"""src/lib/tensor/session.ts (Author-desk@652db7af): New York calendar parts of an epoch-ms timestamp, the
source's own holiday / early-close lists, classifySession, intervalMs, completedDailyBars, formatEt."""
from datetime import datetime

from ....util import ET

HOLIDAYS = {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
            "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"}
EARLY_CLOSE = {"2026-11-27": 13 * 60, "2026-12-24": 13 * 60, "2027-11-26": 13 * 60}


def et_parts(ms):
    d = datetime.fromtimestamp(ms / 1000.0, tz=ET)
    return {"year": d.year, "month": d.month, "day": d.day, "hour": d.hour, "minute": d.minute, "second": d.second,
            "dow": (d.weekday() + 1) % 7, "ymd": "%04d-%02d-%02d" % (d.year, d.month, d.day)}


def is_weekend(p):
    return p["dow"] in (0, 6)


def is_holiday(p):
    return p["ymd"] in HOLIDAYS


def regular_close_minute(p):
    return EARLY_CLOSE.get(p["ymd"], 16 * 60)


def minutes_of_day(p):
    return p["hour"] * 60 + p["minute"]


def classify_session(ms):
    p = et_parts(ms)
    if is_weekend(p) or is_holiday(p):
        return "closed"
    m = minutes_of_day(p)
    close = regular_close_minute(p)
    if 4 * 60 <= m < 9 * 60 + 30:
        return "pre"
    if 9 * 60 + 30 <= m < close:
        return "regular"
    if close <= m < 20 * 60:
        return "post"
    return "closed"


def interval_ms(interval):
    return {"1m": 60000, "2m": 120000, "5m": 300000, "10m": 600000, "1h": 3600000, "60m": 3600000,
            "2h": 7200000, "4h": 14400000, "1d": 86400000, "1wk": 604800000}.get(interval, 300000)


def completed_daily_bars(bars, now_ms):
    if not bars:
        return bars
    today = et_parts(now_ms)
    p = et_parts(bars[-1]["t"])
    et_min = today["hour"] * 60 + today["minute"]
    rth = 1 <= today["dow"] <= 5 and et_min < 16 * 60
    if rth and p["ymd"] == today["ymd"]:
        return bars[:-1]
    return bars


def format_et(ms, with_time=True):
    p = et_parts(ms)
    if not with_time:
        return p["ymd"]
    return "%s %02d:%02d ET" % (p["ymd"], p["hour"], p["minute"])


def tag_session(ms):
    s = classify_session(ms)
    return "post" if s == "closed" else s


def admit_bars(raw, interval, now_ms):
    """bars.ts admitBars: positive OHLC, high / low containing open and close, volume >= 0, strictly increasing
    stamps; trailing bars not yet completed (now < t + interval) dropped."""
    ms = interval_ms(interval)
    out = []
    last_t = -1
    for b in raw:
        if not (b["o"] > 0 and b["h"] > 0 and b["l"] > 0 and b["c"] > 0):
            continue
        if b["h"] < max(b["o"], b["c"]) or b["l"] > min(b["o"], b["c"]):
            continue
        if b["v"] < 0:
            continue
        if b["t"] <= last_t:
            continue
        last_t = b["t"]
        out.append(b)
    while out and now_ms < out[-1]["t"] + ms:
        out.pop()
    return out
