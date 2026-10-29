"""One name's daily bars -> its point-in-time window and features at session d, by the frozen spec (data, universe
eligible_on_d, tier, features, tilt) and with the reference scorer's own functions (engine_score_ref.py).

The inputs are cached bars as the hub stores them (dicts with t, o, h, l, c, v): `adj`, Alpaca's adjustment=all
daily bars, and `raw`, adjustment=raw. A daily bar's session is its UTC date (desk/data/cache.py _session).
  1. the sessions present in both series, trading days only, at or before d (one bar a session, the last copy);
  2. a bar is used only when its adjusted open, high, low and close are > 0, its raw close is > 0 and none is
     missing (data.bar_validity); its adjusted high and low are repaired (data.bar_repair);
  3. the bars split into segments wherever two consecutive bars are more than 45 calendar days apart, and the window
     is the current segment, which must end at d (data.segments);
  4. the features at d by the scorer: own_vol on the last 23 adjusted closes, atr_pct on the last 15 adjusted bars,
     dollar_volume_20 on the last 20 raw closes and volumes, momentum_6_1 on the segment's adjusted closes.
Adjusted prices enter only as ratios inside a window; raw close and raw volume only as the price floors and dv20.
Nothing here reads a file, the clock or the network."""
import datetime
import math

from .. import calendar as cal
from . import engine_score_ref as ref

GAP_DAYS = 45            # data.segments: a gap of more than 45 calendar days starts a new segment
MIN_BARS = 60            # universe.eligible_on_d: at least 60 bars in the current segment, d included


def session_of(bar):
    return datetime.datetime.fromtimestamp(float(bar["t"]), tz=datetime.timezone.utc).date().isoformat()


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _by_session(bars, session):
    out = {}
    for b in bars or ():
        try:
            d = session_of(b)
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            continue
        if d <= session and cal.is_trading_day(d):
            out[d] = b
    return out


def window(adj, raw, session):
    """(rows, None) or ([], reason): the current segment's valid bars through `session`, oldest first, each
    (session, open, high, low, close, raw close, raw volume) with the adjusted high and low repaired"""
    a, r = _by_session(adj, session), _by_session(raw, session)
    rows, bad = [], False
    for d in sorted(set(a) & set(r)):
        o, h, lo, c = (_num(a[d].get(k)) for k in ("o", "h", "l", "c"))
        rc = _num(r[d].get("c"))
        if None in (o, h, lo, c, rc) or min(o, h, lo, c, rc) <= 0:
            bad = bad or d == session
            continue
        h, lo = ref.repair_bar(o, h, lo, c)
        rows.append((d, o, h, lo, c, rc, _num(r[d].get("v"))))
    if not rows or rows[-1][0] != session:
        if bad:
            return [], "bad_session_bar"
        if session in a and session not in r:
            return [], "no_raw_session_bar"
        if session in r and session not in a:
            return [], "no_adjusted_session_bar"
        return [], "no_session_bar"
    start = 0
    for k in range(1, len(rows)):
        if (datetime.date.fromisoformat(rows[k][0]) - datetime.date.fromisoformat(rows[k - 1][0])).days > GAP_DAYS:
            start = k
    return rows[start:], None


def features(adj, raw, session):
    """(features, None) or (None, reason) for one name at session d"""
    rows, why = window(adj, raw, session)
    if why:
        return None, why
    if len(rows) < MIN_BARS:
        return None, "too_few_bars"
    o, h, lo, c, rc, rv = ([x[k] for x in rows] for k in range(1, 7))
    if any(v is None for v in rv[-20:]):
        return None, "volume_missing"
    own = ref.own_vol(c[-23:])
    atr = ref.atr_pct(o[-15:], h[-15:], lo[-15:], c[-15:])
    return {"session": session, "first": rows[0][0], "bars": len(rows), "close": rc[-1], "volume": rv[-1],
            "dv20": ref.dollar_volume_20(rc[-20:], rv[-20:]),
            "lrv1": own["lrv1"], "lrv5": own["lrv5"], "lrv22": own["lrv22"], "rv22": math.exp(own["lrv22"]),
            "atr_pct": atr, "log_atr_pct": math.log(atr) if atr > 0 else None,
            "mom6": ref.momentum_6_1(c)}, None


def ineligible(f):
    """None when the scorer's eligibility rule screens the name on d, else the first condition it fails"""
    vol = f.get("volume") or 0.0
    if ref.eligible(f["close"], vol, f["dv20"], f["bars"], f.get("atr_pct")):
        return None
    if not f["close"] >= 1:
        return "price_below_min"
    if not f["dv20"] >= 1e5:
        return "dv20_below_min"
    if not f["bars"] >= MIN_BARS:
        return "too_few_bars"
    if not vol > 0:
        return "no_volume"
    return "atr_nonpositive"
