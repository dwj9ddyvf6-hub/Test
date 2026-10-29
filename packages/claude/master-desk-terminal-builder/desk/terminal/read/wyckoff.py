"""Wyckoff's events, the ones a daily chart shows plainly: a spring (a quick break under a trading range's floor that
closes back inside, shaking out weak holders), an upthrust (the same over the ceiling), a sign of strength (a wide,
heavy up day rising out of the range) and a selling or buying climax (a huge-volume, wide day after a long fall or
rise that stops the move). Each is read in the last ten sessions.

Unproven detectors describe; they do not vote. The selling climax and the sign of strength are found and shown in the
open card with side 0: the research ledger grades the selling climax C (eyes/DEEP evidence.csv R00113-R00115: it lags
equally volatile names, a warning if anything, and fails lens g, fine volatility matching), and a close over the prior
session's high, which a sign of strength needs, is a grade-A small-cap warning (R00039-R00042, theme T02: short-term
strength fades). Neither is a reason to buy."""
import math

from . import ta, wyckoff_phase
from .core import Fact, pct

RANGE_MIN = 20                # the trading range: the 20 to 60 sessions before the event
FLAT_ATR = 1.5                # and flat: its closes' fitted line moves 1.5 ATR or less (22 of 36 springs on
                              # 2026-10-16 followed a window that fell 2.5 ATR or more)
FRESH = 10


def _tested(w, level, a, low=True):
    """sessions that came within half an ATR of the level, at least five sessions apart"""
    hits, last = 0, -99
    for i, b in enumerate(w):
        px = float(b["l"]) if low else float(b["h"])
        if abs(px - level) <= 0.5 * a and i - last >= 5:
            hits, last = hits + 1, i
    return hits


def _range(x, end, n=40):
    """(ceiling, floor) of the trading range before bar `end`: no taller than 6 ATR, its floor and ceiling each
    tested at least twice; None otherwise"""
    w = x.bars[max(0, end - n):end]
    if len(w) < RANGE_MIN:
        return None
    hi, lo = max(float(b["h"]) for b in w), min(float(b["l"]) for b in w)
    a = x.atrs[end - 1] or x.atr
    if hi - lo > 6 * a or _tested(w, lo, a) < 2 or _tested(w, hi, a, low=False) < 2:
        return None
    cs = [float(b["c"]) for b in w]
    slope, _ = ta.linreg([math.log(v) for v in cs])
    if abs(math.exp(slope * (len(cs) - 1)) - 1.0) * cs[0] > FLAT_ATR * a:
        return None                               # a channel, not a range: its fitted line moves (the audit's B-H6)
    return hi, lo


def facts(x):
    out = []
    if x.n < 80 or not x.atr:
        return out
    for i in range(x.n - 1, x.n - 1 - FRESH, -1):
        r = _range(x, i)
        if not r:
            continue
        hi, lo = r
        b = x.bars[i]
        a = x.atrs[i - 1] or x.atr
        bl, bh, bc = float(b["l"]), float(b["h"]), float(b["c"])
        later = x.c[i + 1:]
        if lo - 1.0 * a <= bl < lo and bc > lo and all(c > lo for c in later):
            ago = x.n - 1 - i
            out.append(Fact("wyckoff.spring", "Wyckoff", "structure", 1, 0.6, "A shakeout that failed (spring)",
                            f"{x.on(i, cap=True)} it broke "
                            "under the floor of its trading range and closed back inside: sellers were flushed out, a "
                            "Wyckoff spring.", "Wyckoff: spring under the range floor", "spring", 0.7,
                            {"floor": bl, "range_lo": lo, "range_hi": hi, "ago": ago}))
            break
        if hi < bh <= hi + 1.0 * a and bc < hi and all(c < hi for c in later):
            ago = x.n - 1 - i
            out.append(Fact("wyckoff.upthrust", "Wyckoff", "structure", -1, 0.6, "A breakout that failed (upthrust)",
                            f"{x.on(i, cap=True)} it poked "
                            "over the ceiling of its trading range and closed back inside: buyers were trapped, a "
                            "Wyckoff upthrust.", "Wyckoff: upthrust over the range ceiling", "upthrust", 0.7,
                            {"ceiling": bh, "range_lo": lo, "range_hi": hi, "ago": ago},
                            wrong=(bh, "the upthrust's high")))
            break
    for i in range(x.n - 1, x.n - 1 - FRESH, -1):
        b, p = x.bars[i], x.bars[i - 1]
        a = x.atrs[i - 1] or x.atr
        rng = float(b["h"]) - float(b["l"])
        rv = x.vol[i] / (x.vol50[i - 1] or 1)
        cl = (float(b["c"]) - float(b["l"])) / rng if rng else 0.5
        prior = x.c[max(0, i - 60):i]
        if not prior:
            continue
        fall = (x.c[i - 1] / max(prior) - 1.0) * 100.0
        rise = (x.c[i - 1] / min(prior) - 1.0) * 100.0
        ago = x.n - 1 - i
        when = x.on(i, cap=True)
        if rv >= 2.5 and rng >= 2 * a and fall <= -15 and cl >= 0.5:
            out.append(Fact("wyckoff.climax", "Wyckoff", "structure", 0, 0.0, "A selling climax",
                            f"{when}, after a {pct(fall, 0)} fall, it traded {rv:.1f}x its average volume on a wide day "
                            "and closed off the low: panic selling.",
                            "Wyckoff: selling climax", "selling_climax", 0.65, {"rv": rv, "fall": fall, "ago": ago}))
            break
        if rv >= 2.5 and rng >= 2 * a and rise >= 30 and cl <= 0.5:
            out.append(Fact("wyckoff.climax", "Wyckoff", "structure", -1, 0.5, "A buying climax",
                            f"{when}, after a {pct(rise, 0)} rise, it traded {rv:.1f}x its average volume on a wide day "
                            "and closed off the high: a buying frenzy that often marks the top.",
                            "Wyckoff: buying climax", "buying_climax", 0.65, {"rv": rv, "rise": rise, "ago": ago}))
            break
        r = _range(x, i)
        if r and rv >= 1.5 and rng >= 1.5 * a and cl >= 0.7 and float(b["c"]) > (r[0] + r[1]) / 2 \
                and float(b["c"]) > float(p["h"]):
            out.append(Fact("wyckoff.sos", "Wyckoff", "structure", 0, 0.0, "A sign of strength",
                            f"{when} it rose out of its trading range on a wide day with {rv:.1f}x average volume, "
                            "closing near the high: demand taking over, a Wyckoff sign of strength.",
                            "Wyckoff: sign of strength", "sign_of_strength", 0.5, {"rv": rv, "ago": ago}))
            break
    return out + wyckoff_phase.facts(x, out)         # the phase and effort versus result (wyckoff_phase.py)
