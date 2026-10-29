"""Midna's daily panel (src/lib/equity/context-feed.ts @ paper-desk 68315288, blob b590e868 — identical on the lector
and entire refs): the swing basket plus the market names, Yahoo daily bars (range 2y), aligned to SPY's completed
sessions. Read by the liquid-momentum book (context.ts) and the forward lab scan (forward-scan.ts).

  universe   the swing basket quant-research/Author-research/shadow/swing_basket_v1.json (blob 2f27182c, vendored as
             desk/vendor/universes/old_desk/universe_swing_basket_v1.json — the same blob)
  EXTRA      SPY QQQ IWM SMH GLD TLT USO UUP BTC-USD HYG IEF ^VIX ^VIX3M
  bar        {close, adj (adjclose, else close), high (else close), low?, open?, volume (else 0)}; dated in New York
  dropPartial  SPY / ^VIX: a bar dated today before the close is dropped; bars after the last completed session too
  toPanel    asOf = SPY's last completed session; clock = SPY dates <= asOf; every other series aligned to the clock
             (a missing session = zeros); vixLast / vixPrev = the last two completed ^VIX closes; vixCloses aligned

Named divergences: the bars are the desk's Yahoo daily bars (BarCache; a session's bar is final 15 minutes after the
close, Midna kept the bar from the close itself; rows Yahoo prints without an open/high/low are dropped by the desk
provider, Midna kept them with open/low unset); range=2y is reproduced as the sessions dated after the same calendar
day two years before the pass (Yahoo's own boundary) — the context-bars.json cache and its 18 h / 30 min refresh
rule (plumbing) are the desk cache."""
import json
import os
from datetime import date, datetime

from ..sleeves.midna import common as M
from ..util import ET

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor")
BASKET_FILE = os.path.join(VENDOR, "universes", "old_desk", "universe_swing_basket_v1.json")
EXTRA = ["SPY", "QQQ", "IWM", "SMH", "GLD", "TLT", "USO", "UUP", "BTC-USD", "HYG", "IEF", "^VIX", "^VIX3M"]
BARS_N = 540


def swing_universe():
    raw = json.load(open(BASKET_FILE))
    return list(dict.fromkeys(raw.get("symbols") or []))


def ymd_of(t):
    return datetime.fromtimestamp(float(t), tz=ET).date().isoformat()


def to_bars(desk_bars, start=None):
    """desk Yahoo bars -> context-feed.ts Bar rows {date, close, adj, high, low, open, volume}, sorted by date."""
    out = {}
    for b in desk_bars or []:
        close = b.get("c")
        if close is None or not close > 0:
            continue
        d = ymd_of(b["t"])
        if start is not None and d <= start:
            continue
        hi, lo, op, vol, adj = b.get("h"), b.get("l"), b.get("o"), b.get("v"), b.get("ac")
        out[d] = {"date": d, "close": float(close),
                  "adj": float(adj) if adj is not None and adj > 0 else float(close),
                  "high": float(hi) if hi is not None and hi > 0 else float(close),
                  "low": float(lo) if lo is not None and lo > 0 else None,
                  "open": float(op) if op is not None and op > 0 else None,
                  "volume": float(vol) if vol is not None and vol > 0 else 0.0}
    return [out[k] for k in sorted(out)]


def drop_partial(bars, now):
    if not bars:
        return bars
    p = M.et_parts(now)
    if bars[-1]["date"] == p["ymd"] and p["minutes"] < M.session_close_minutes(p["ymd"]):
        return bars[:-1]
    completed = M.last_completed_session(now)
    return [b for b in bars if b["date"] <= completed]


def align(clock, bars):
    by = {b["date"]: b for b in bars}
    out = []
    for d in clock:
        b = by.get(d)
        if b is None:
            out.append({"close": 0.0, "adj": 0.0, "high": 0.0, "volume": 0.0, "low": None, "open": None})
        else:
            out.append({"close": b["close"], "adj": b["adj"], "high": b["high"], "low": b["low"], "open": b["open"],
                        "volume": b["volume"]})
    return out


def to_panel(series_bars, universe, now):
    """context-feed.ts toPanel over {sym: Bar rows}."""
    spy = drop_partial(series_bars.get("SPY") or [], now)
    if not spy:
        return None
    as_of = spy[-1]["date"]
    clock = [b["date"] for b in spy if b["date"] <= as_of]
    series = {}
    for sym, bars in series_bars.items():
        if sym == "^VIX":
            continue
        series[sym] = align(clock, bars)
    vix = drop_partial(series_bars.get("^VIX") or [], now)
    by = {b["date"]: b["close"] for b in vix}
    return {"asOf": as_of, "clock": clock, "series": series,
            "vixLast": vix[-1]["close"] if vix else None, "vixPrev": vix[-2]["close"] if len(vix) >= 2 else None,
            "vixCloses": [by.get(d, 0.0) for d in clock], "universe": list(universe)}


def window_start(now):
    d = date.fromisoformat(M.et_ymd(now))
    try:
        return date(d.year - 2, d.month, d.day).isoformat()
    except ValueError:                                  # 29 February
        return date(d.year - 2, d.month, 28).isoformat()


def build(hub, now, n=BARS_N):
    universe = swing_universe()
    syms = list(dict.fromkeys(universe + EXTRA))
    got = hub.bars("yahoo", "1d", syms, n)
    start = window_start(now)
    rows = {s: to_bars(got.get(s), start) for s in syms}
    return to_panel(rows, universe, now)


def feed_panel(feeds, sleeve, now, arg=None):
    return build(feeds.hub, now)
