"""SATY PORT — bar plumbing: session filtering, session-open-
anchored aggregation, period aggregation, and the completed-bar
warp mapping (SPEC §2, §6).

Bar contract (the whole saty_* family): a bar is a dict
  {"t": open time, "end": close time, "open", "high", "low",
   "close", "volume"}
with t/end timezone-aware datetimes in America/New_York, sorted
ascending. Inputs are CLOSED bars only (SPEC §1 rule 1): a
forming bar is the caller's problem and must never be passed in
as if final. Raw intraday inputs missing "end" get one stamped
by with_end() from their known duration.

Session windows (SPEC §2.2): extended = 04:00-20:00 ET,
regular (RTH) = 09:30-16:00 ET. Aggregation is anchored to the
session OPEN (an RTH hourly bar is 09:30-10:30, never the
wall-clock 09:00-10:00) — trap T5.

Warp mapping (SPEC §6 — the port's one deliberate divergence
from the oscillator original, whose lookahead_on warp leaks the
forming HTF bar): at any signal bar, the warped value is the
source value of the LAST COMPLETED source bar, i.e. the latest
source bar whose close time is <= the signal bar's close time.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

SESSION_WINDOWS = {
    "extended": (time(4, 0), time(20, 0)),
    "regular": (time(9, 30), time(16, 0)),
}

# ATR Levels mode -> period timeframe (SPEC §5.1; original's
# Day|Multiday|Swing|Position|Long-term -> D|W|M|3M|12M).
MODE_TO_PERIOD = {
    "Day": "D",
    "Multiday": "W",
    "Swing": "M",
    "Position": "3M",
    "Long-term": "12M",
}


def close_time(bar):
    """A bar's completion time: its stamped "end" if present,
    else its open time (callers stamp ends via with_end)."""
    end = bar.get("end")
    return end if end is not None else bar["t"]


def with_end(bars, minutes):
    """Stamp "end" = t + minutes on bars that lack one (raw
    fixed-duration inputs, e.g. 1-minute SIP bars). Returns new
    dicts; inputs are not mutated."""
    out = []
    for b in bars:
        nb = dict(b)
        if nb.get("end") is None:
            nb["end"] = nb["t"] + timedelta(minutes=minutes)
        out.append(nb)
    return out


def filter_session(bars, basis):
    """Keep intraday bars whose OPEN time falls inside the basis
    window on their ET date. Bars spanning a full day or more
    (daily bars) pass through untouched: for them the basis is
    provenance (how they were built), not a filter — SPEC §2.2.
    Unknown basis raises: a silent default here is exactly the
    session mixup trap T3 guards."""
    if basis not in SESSION_WINDOWS:
        raise ValueError(f"unknown session basis: {basis!r}")
    start, end = SESSION_WINDOWS[basis]
    out = []
    for b in bars:
        span = close_time(b) - b["t"]
        if span >= timedelta(days=1):
            out.append(b)
            continue
        tt = b["t"].time()
        if start <= tt < end:
            out.append(b)
    return out


def _merge(bucket_bars, t_open, t_end):
    return {
        "t": t_open,
        "end": t_end,
        "open": bucket_bars[0]["open"],
        "high": max(b["high"] for b in bucket_bars),
        "low": min(b["low"] for b in bucket_bars),
        "close": bucket_bars[-1]["close"],
        "volume": sum(b.get("volume") or 0.0 for b in bucket_bars),
    }


def aggregate(bars, minutes, anchor="09:30"):
    """Aggregate intraday bars into `minutes`-sized bars anchored
    at the session open (anchor "HH:MM" ET, per ET date). Bucket
    index = floor((open - anchor) / minutes); bars before the
    anchor form pre-anchor buckets deterministically. The output
    bar's "end" is its last constituent bar's close time (the
    moment the aggregated bar actually completed), its "t" the
    bucket start. Callers filter the session first
    (filter_session) — aggregation never drops bars silently."""
    ah, am = (int(x) for x in anchor.split(":"))
    anchor_t = time(ah, am)
    buckets = {}
    order = []
    for b in bars:
        d = b["t"].date()
        anchor_dt = datetime.combine(d, anchor_t, tzinfo=ET)
        idx = int((b["t"] - anchor_dt).total_seconds()
                  // (minutes * 60))
        key = (d, idx)
        if key not in buckets:
            buckets[key] = (anchor_dt + timedelta(minutes=idx * minutes),
                            [])
            order.append(key)
        buckets[key][1].append(b)
    out = []
    for key in order:
        t_open, members = buckets[key]
        out.append(_merge(members, t_open, close_time(members[-1])))
    return out


def aggregate_daily(bars):
    """Aggregate intraday bars into daily bars by ET date.
    Output t = midnight ET of the date; end = last constituent
    close time. Under the extended basis the constituents span
    04:00-20:00; under regular, 09:30-16:00 — the daily bar's
    basis is whichever bars the caller filtered in (SPEC §2.2:
    a regular-basis daily is BUILT from RTH bars, never taken
    from the vendor's full-session daily bar)."""
    days = {}
    order = []
    for b in bars:
        d = b["t"].date()
        if d not in days:
            days[d] = []
            order.append(d)
        days[d].append(b)
    out = []
    for d in order:
        members = days[d]
        bar = _merge(members, datetime.combine(d, time(0, 0),
                                               tzinfo=ET),
                     close_time(members[-1]))
        bar["date"] = d.isoformat()
        out.append(bar)
    return out


def period_key(d, period):
    """The period identity of an ET date: D -> the date itself;
    W -> the Monday of its week (TradingView weekly bars start
    Monday); M -> year-month; 3M -> calendar quarter
    (Jan/Apr/Jul/Oct); 12M -> calendar year."""
    if period == "D":
        return d.isoformat()
    if period == "W":
        monday = d - timedelta(days=d.weekday())
        return monday.isoformat() + "W"
    if period == "M":
        return f"{d.year:04d}-{d.month:02d}"
    if period == "3M":
        return f"{d.year:04d}Q{(d.month - 1) // 3 + 1}"
    if period == "12M":
        return f"{d.year:04d}"
    raise ValueError(f"unknown period: {period!r}")


def aggregate_periods(daily_bars, period):
    """Aggregate daily bars into period bars (D/W/M/3M/12M).
    Each output bar carries "period" (its period_key) and spans
    its constituent dailies. Input dailies must all share one
    session basis — mixing bases inside a run is forbidden
    (SPEC §3); the caller owns that, the basis is stamped on
    outputs by the consuming component."""
    groups = {}
    order = []
    for b in daily_bars:
        d = b["t"].date()
        key = period_key(d, period)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(b)
    out = []
    for key in order:
        members = groups[key]
        bar = _merge(members, members[0]["t"],
                     close_time(members[-1]))
        bar["period"] = key
        out.append(bar)
    return out


def completed_map(source_bars, target_bars):
    """For each target bar, the index of the last COMPLETED
    source bar (source close time <= target close time), or
    None when no source bar has completed yet. Both inputs
    sorted ascending. This is SPEC §6's non-leaking warp rule
    as an index map; identity when the timeframes are equal."""
    out = []
    j = -1
    for tb in target_bars:
        tc = close_time(tb)
        while (j + 1 < len(source_bars)
               and close_time(source_bars[j + 1]) <= tc):
            j += 1
        out.append(j if j >= 0 else None)
    return out


def align_values(source_bars, source_values, target_bars):
    """Map a per-source-bar series onto target bars by the
    completed-bar rule. Returns one value per target bar
    (None before the first source bar completes)."""
    idx = completed_map(source_bars, target_bars)
    return [source_values[j] if j is not None else None
            for j in idx]
