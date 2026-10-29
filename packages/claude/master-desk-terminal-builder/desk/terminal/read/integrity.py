"""A price history the read can trust. The read uses split-adjusted daily bars; a spin-off or a re-listing is not a
split, and the feed leaves it in as a one-day step that no trader lived through. HON's spin-off left a -51% step on
2026-06-29, and the read called it "declining stage, -57%". WOLF's re-listing left a +1,726% step on 2025-09-29.
Midna's engine review, 2026-10-18, found both.

The rule: a one-day close-to-close drop of STEP (40%) or more, or a jump of JUMP (100%) or more, is a corporate action
when it printed on light volume (under VOL_MULT, 5 times, the 20-session median), the session opened at the step
(OPEN_TOL) and price never traded back to the close before it. A heuristic: on 2026-10-16 it took out HON's and
MDU's spin-offs, CCXI's zero-volume step and WOLF's re-listing; CAR's -48% and QUBT's -41% opened near the prior close
and traded down, real moves the open test keeps. The vendor's corporate-action feed is the principled source. The
most recent such step is handled:
  - with 260 sessions or more after it, the read starts after it (a re-listing is a new security);
  - else a drop scales the prices before it by the step, as vendors adjust a spin-off;
  - else (a jump with a short history after it) the read starts after it too, and is too short to read.
A crash on heavy volume is a real move and stays: PRIM's -50% on 2026-05-06 printed at 20 times its median."""
import math

STEP = 0.40                             # a drop of 40% or more
JUMP = 1.00                             # a jump of 100% or more: a re-listing or an unadjusted reverse split. Jumps of
                                        # 40-100% on busy names were real news (IBRX, RGTI, OPEN on 2026-10-16)
VOL_MULT = 5.0
OPEN_TOL = 0.15                         # a corporate action reprices at the open: the open's own step, in log terms, is
                                        # within 0.15 of the session's (spin-offs HON 0.055, MDU 0.040, VYX 0.020, CCXI
                                        # 0.006; the crashes CAR 0.562 and QUBT 0.374: the audit's C-C5)
MIN_AFTER = 260                         # compose.read's minimum history
PRICE_KEYS = ("o", "h", "l", "c")


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return 0.0 if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def find(bars):
    """the most recent corporate-action step: (index of the first bar after it, its ratio) or None"""
    closes = [float(b["c"]) if b.get("c") is not None else None for b in bars]
    for i in range(len(bars) - 1, 20, -1):
        p, c = closes[i - 1], closes[i]
        if not p or not c:
            continue
        r = c / p
        if (r < 1 and 1 - r < STEP) or (r >= 1 and r - 1 < JUMP):
            continue
        med = _median([float(b.get("v") or 0) for b in bars[i - 20:i]])
        if med and float(bars[i].get("v") or 0) >= VOL_MULT * med:
            continue                                     # heavy volume: a real move
        o = float(bars[i].get("o") or 0)
        if o > 0 and abs(math.log(o / p) - math.log(r)) > OPEN_TOL:
            continue                                     # the open did not carry the step: it traded there, a move
        later = [x for x in closes[i:] if x is not None]
        if (r < 1 and max(later) >= p) or (r > 1 and min(later) <= p):
            continue                                     # it traded back: a real move
        return i, r
    return None


def clean(bars):
    """(bars, note): the bars the read should use and what was done, or (bars, None) when nothing needed doing"""
    hit = find(bars)
    if not hit:
        return bars, None
    i, r = hit
    note = {"t": bars[i]["t"], "step": round((r - 1) * 100, 1)}
    if len(bars) - i >= MIN_AFTER or r > 1:
        return bars[i:], dict(note, kind="cut", i=0)
    out = []
    for b in bars[:i]:
        nb = dict(b)
        for k in PRICE_KEYS:
            if nb.get(k) is not None:
                nb[k] = float(nb[k]) * r
        out.append(nb)
    return out + list(bars[i:]), dict(note, kind="scaled", i=i)


def fact(x, note):
    """the read's line on what was done (context: it moves no evidence), or None"""
    if not note:
        return None
    from datetime import datetime
    from ...util import ET
    from .core import Fact
    step = f"{'+' if note['step'] > 0 else '−'}{abs(note['step']):.0f}%"
    did = "the prices before it are scaled to it" if note["kind"] == "scaled" else "the read starts there"
    t, last = datetime.fromtimestamp(float(note["t"]), tz=ET), datetime.fromtimestamp(float(x.bars[-1]["t"]), tz=ET)
    on = "on " + t.strftime("%b ") + str(t.day) + ("" if t.year == last.year else f", {t.year}")
    return Fact("data.adjusted", "Data", "context", 0, 0.0, "Price history adjusted",
                f"A one-day step of {step} on light volume {on}, never traded back, is the mark of a spin-off or a "
                f"re-listing, not a move: {did}.", f"Price history: the {step} step {on} is a corporate action; {did}")
