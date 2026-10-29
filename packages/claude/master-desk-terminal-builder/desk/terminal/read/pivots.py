"""Swing points: the turns a trader marks on a chart, found the way directional-change research defines them (Merrill
1977; Guillaume et al. 1997; Glattfelder, Dupuis & Olsen 2011). Each session is read as two ordered price events
(open, high, low, close for a down day; open, low, high, close otherwise). A leg's extreme becomes a confirmed swing
only once price has reversed k ATR from it (the ATR of the confirming session, so nothing is known before it
happens) or has taken out the previous opposite swing. While a leg is open its deepest counter-move is tracked, so the
next leg starts from the true extreme. Every confirmed swing is the most extreme price between its neighbours, swings
alternate high and low, and a later session never relabels an earlier one. The open leg's extreme is carried last,
marked tentative."""
from collections import namedtuple

Pivot = namedtuple("Pivot", "i price kind confirmed")         # kind "H" or "L"; i: the session of the extreme


def _events(bars, start):
    for i in range(start, len(bars)):
        b = bars[i]
        h, l = float(b["h"]), float(b["l"])
        if float(b["c"]) < float(b["o"]):
            yield i, h, "h"
            yield i, l, "l"
        else:
            yield i, l, "l"
            yield i, h, "h"


def zigzag(bars, atrs, k):
    """[Pivot] alternating H and L, oldest first, the open leg's extreme last (confirmed False)"""
    start = next((i for i, a in enumerate(atrs) if a), None)
    if not bars or start is None:
        return []
    out = []
    d = 0
    hi = lo = hi_i = lo_i = None
    opp = opp_i = None
    for i, px, kind in _events(bars, start):
        thr = k * atrs[i]
        if d == 0:
            if hi is None or (kind == "h" and px > hi):
                hi, hi_i = (px, i) if kind == "h" else (float(bars[i]["h"]), i)
            if lo is None or (kind == "l" and px < lo):
                lo, lo_i = (px, i) if kind == "l" else (float(bars[i]["l"]), i)
            if kind == "l" and hi - px >= thr:
                out.append(Pivot(hi_i, hi, "H", True))
                d, lo, lo_i, opp, opp_i = -1, px, i, None, None
            elif kind == "h" and px - lo >= thr:
                out.append(Pivot(lo_i, lo, "L", True))
                d, hi, hi_i, opp, opp_i = 1, px, i, None, None
            continue
        if d == 1:
            if kind == "h":
                if px > hi:
                    hi, hi_i, opp, opp_i = px, i, None, None
                continue
            if opp is None or px < opp:
                opp, opp_i = px, i
            last_lo = out[-1].price if out else None
            if hi - opp >= thr or (last_lo is not None and opp < last_lo):
                out.append(Pivot(hi_i, hi, "H", True))
                d, lo, lo_i, opp, opp_i = -1, opp, opp_i, None, None
        else:
            if kind == "l":
                if px < lo:
                    lo, lo_i, opp, opp_i = px, i, None, None
                continue
            if opp is None or px > opp:
                opp, opp_i = px, i
            last_hi = out[-1].price if out else None
            if opp - lo >= thr or (last_hi is not None and opp > last_hi):
                out.append(Pivot(lo_i, lo, "L", True))
                d, hi, hi_i, opp, opp_i = 1, opp, opp_i, None, None
    if d == 1:
        out.append(Pivot(hi_i, hi, "H", False))
    elif d == -1:
        out.append(Pivot(lo_i, lo, "L", False))
    return out


def structure(pivots):
    """'up' (higher highs and higher lows), 'down' (lower highs and lower lows) or 'range', from the last two
    confirmed highs and lows; None with fewer than two of each"""
    hs = [p.price for p in pivots if p.kind == "H" and p.confirmed][-2:]
    ls = [p.price for p in pivots if p.kind == "L" and p.confirmed][-2:]
    if len(hs) < 2 or len(ls) < 2:
        return None
    if hs[1] > hs[0] and ls[1] > ls[0]:
        return "up"
    if hs[1] < hs[0] and ls[1] < ls[0]:
        return "down"
    return "range"
