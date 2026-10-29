"""Divergences: price and momentum disagreeing at two swing points, read on seven gauges (RSI, the MACD line and its
histogram, on-balance volume, money flow, the stochastic and CCI), daily and weekly.

  regular bullish   price makes a lower low, the gauge a higher low: selling is losing force
  hidden bullish    price makes a higher low, the gauge a lower low: buyers stepped in earlier, the uptrend resumes
  regular bearish   price makes a higher high, the gauge a lower high: buying is losing force
  hidden bearish    price makes a lower high, the gauge a higher high: sellers stepped in earlier, the downtrend resumes

Swing points here are local turns (the lowest low or highest high of the five sessions either side, confirmed by
three sessions after), so a divergence is known three sessions after its second swing, never before. A later close
through the second swing (under its low, over its high) ends it: the force the divergence measured did not hold."""
from collections import namedtuple

from . import ta

Swing = namedtuple("Swing", "i price kind")
Div = namedtuple("Div", "kind side i0 i1 gauges")          # side +1 bullish / -1 bearish; gauges: names agreeing

LEFT, RIGHT = 5, 3
MIN_GAP, MAX_GAP = 5, 60
FRESH = 10                                                  # the second swing within the last 10 sessions (2 weeks)
NAMES = ("RSI", "MACD", "MACD histogram", "on-balance volume", "money flow", "stochastic", "CCI")


def swings(bars, left=LEFT, right=RIGHT):
    """local turns of the lows and the highs, oldest first"""
    out = []
    for i in range(left, len(bars) - right):
        lo, hi = float(bars[i]["l"]), float(bars[i]["h"])
        w = bars[i - left:i + right + 1]
        if lo == min(float(b["l"]) for b in w) and all(float(b["l"]) > lo for b in bars[i + 1:i + right + 1]):
            out.append(Swing(i, lo, "L"))
        if hi == max(float(b["h"]) for b in w) and all(float(b["h"]) < hi for b in bars[i + 1:i + right + 1]):
            out.append(Swing(i, hi, "H"))
    return out


def gauges(bars):
    cs = ta.closes(bars)
    line, _, hist = ta.macd(cs)
    return dict(zip(NAMES, (ta.rsi(cs), line, hist, ta.obv(bars), ta.mfi(bars), ta.stochastic(bars), ta.cci(bars))))


def _val(series, i):
    w = [v for v in series[max(0, i - 1):i + 2] if v is not None]   # the gauge's turn may lead or lag by a session
    return w


MIN_GAUGES = 3                       # three of the seven gauges must agree: one gauge alone is noise


def find(bars, fresh=FRESH):
    """[Div] whose second swing is within `fresh` sessions of the last bar; one per kind, the gauges that agree.
    Each kind is read in its textbook setting: a regular bullish divergence where RSI was low (40 or under) at the
    first swing, a regular bearish one where it was high (60 or over), a hidden bullish one in a rising 50-period
    average, a hidden bearish one in a falling one"""
    sw = swings(bars)
    g = gauges(bars)
    n = len(bars)
    rsi = g["RSI"]
    m50 = ta.sma(ta.closes(bars), 50)

    def setting(kind, a, b):
        if kind == "regular bullish":
            return rsi[a.i] is not None and rsi[a.i] <= 40
        if kind == "regular bearish":
            return rsi[a.i] is not None and rsi[a.i] >= 60
        if m50[b.i] is None or m50[b.i - 5] is None:
            return False
        rising = m50[b.i] > m50[b.i - 5]
        return rising if kind == "hidden bullish" else not rising
    out = []
    for kind_sw, (reg, hid) in (("L", ("regular bullish", "hidden bullish")), ("H", ("regular bearish", "hidden bearish"))):
        pts = [s for s in sw if s.kind == kind_sw]
        if len(pts) < 2:
            continue
        b = pts[-1]
        if n - 1 - b.i > fresh + RIGHT:
            continue
        for a in reversed(pts[:-1]):
            if not (MIN_GAP <= b.i - a.i <= MAX_GAP):
                continue
            low = kind_sw == "L"
            between = bars[a.i + 1:b.i]
            if low and between and min(float(x["l"]) for x in between) < min(a.price, b.price):
                continue                                         # a lower swing between them: not a pair
            if not low and between and max(float(x["h"]) for x in between) > max(a.price, b.price):
                continue
            price_lower = b.price < a.price
            after = [float(x["c"]) for x in bars[b.i + 1:]]
            if (low and any(c < b.price for c in after)) or (not low and any(c > b.price for c in after)):
                break                                            # a close through the second swing: the signal failed
            for kind, want in ((reg, "lower" if low else "higher"), (hid, "higher" if low else "lower")):
                p_ok = (price_lower if want == "lower" else b.price > a.price)
                if not p_ok or not setting(kind, a, b):
                    continue
                agree = []
                for name, series in g.items():
                    va, vb = _val(series, a.i), _val(series, b.i)
                    if not va or not vb:
                        continue
                    ga, gb = (min(va), min(vb)) if low else (max(va), max(vb))
                    if (gb > ga) if want == "lower" else (gb < ga):
                        agree.append(name)
                if len(agree) >= MIN_GAUGES:
                    out.append(Div(kind, 1 if low else -1, a.i, b.i, tuple(agree)))
            break                                                # the nearest valid pair only
    return out
