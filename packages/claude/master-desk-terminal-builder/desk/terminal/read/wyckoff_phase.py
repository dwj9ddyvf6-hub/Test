"""Wyckoff's phase and his law of effort versus result, read mechanically from the published method:

  R. Bogomazov and M. Lipsett, "The Wyckoff Method: A Tutorial" (Wyckoff Analytics; StockCharts ChartSchool), its
  accumulation and distribution schematics edited by H. O. Pruden; Pruden, The Three Skills of Top Trading (Wiley,
  2007), the same schematics.

The phase. A trading range after a decline (accumulation) or an advance (distribution), read by the events already in
it, each the tutorial's own definition turned into a comparison, with no number of its own:
  A  the prior move stops: a selling (buying) climax, the read's own (wyckoff.py), then the automatic rally (reaction):
     the first confirmed minor swing after it, whose extreme sets the range's other side ("the lows of the SC and the ST
     and the high of the AR set the boundaries of the TR")
  B  the range builds a cause: from a secondary test, the next confirmed swing, back in the climax's area (within the
     read's level distance of its extreme) on less volume and a narrower spread than the climax ("volume and spread
     should shrink as price approaches the SC area")
  C  the test: a spring (a low under the floor, a close back inside: "takes price below the low of the TR and then
     reverses to close within the TR"), or in distribution an upthrust after distribution over the ceiling
  D  the winning side: a sign of strength (the read's own, wyckoff.py) after the spring, or one that closes over the
     ceiling without a spring ("springs ... are not required elements"); in distribution its mirror, a sign of weakness
  E  the range left: a close beyond it after D ("Phase E: the stock leaves the TR")
A close beyond the range that is not the schematic's (a close under an accumulation's floor, over its ceiling before
a sign of strength) ends the reading, as does a secondary test away from the climax's area or on heavier volume. The
phase reads the events the read already names (the spring and the upthrust vote as their own facts; the climax and the
sign of strength are described, voting nothing: wyckoff.py), so it informs and does not vote (class context); a phase
that has chosen its side (C to E) carries that side for the record.

Effort versus result ("Divergences between volume and price often signal a change in the direction of a price trend";
the tutorial's third law). The read's own volume line (volume.py, vol.last: heavy buying or selling is 1.8 times the
50-day volume on a move of an ATR or more) leaves two of its cells unread: heavy volume that does not move price, and
a move of an ATR or more on light volume, light being as far under the average as heavy is over it (1/1.8, the read's
log-symmetric convention for volume ratios, volume.py's 1.25 and 0.8). Neither the study's data nor the law gives a
number; these are the read's. Heavy volume with little progress counts on a level after a move, by the read's candle
rule (candles.py): on a floor after a fall, buyers absorbing the selling; at a ceiling after a rise, sellers absorbing
the buying. A wide move on light volume is said and casts no vote."""
import dataclasses
from . import pivots
from . import words as W
from .core import MINOR_K, Fact, atr_words, pct
from .levels import LOOKBACK

# the read's own climax and sign of strength (wyckoff.py), the same numbers, so the phase's events are the events the
# read already names. The tutorial gives none ("heavy volume and wide spreads at the SC"); these predate this round and
# are not re-derived here
CLIMAX_RV, CLIMAX_RANGE, CLIMAX_FALL, CLIMAX_RISE, CLIMAX_WINDOW = 2.5, 2.0, -15.0, 30.0, 60
SOS_RV, SOS_RANGE, SOS_CLOSE = 1.5, 1.5, 0.7
# the read's own heavy-volume and move lines (volume.py, vol.last) and their log-symmetric light; neither the study's
# data nor the law decides them
HEAVY, MOVE = 1.8, 1.0
LIGHT = 1.0 / HEAVY

PHASE_WORDS = {("accumulation", "A"): "the decline stopping", ("accumulation", "B"): "building a cause",
               ("accumulation", "C"): "the test of supply", ("accumulation", "D"): "demand in control",
               ("accumulation", "E"): "the markup", ("distribution", "A"): "the advance stopping",
               ("distribution", "B"): "building a cause", ("distribution", "C"): "the test of demand",
               ("distribution", "D"): "supply in control", ("distribution", "E"): "the markdown"}


def _bar(x, i):
    b = x.bars[i]
    return float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])


def _climax(x, i):
    """+1 a selling climax, -1 a buying climax, 0 neither: the read's own rule (wyckoff.py), on the sessions to i"""
    if i < 1 or x.vol50[i - 1] is None:
        return 0
    o, h, l, c = _bar(x, i)
    a = x.atrs[i - 1] or x.atrs[i]
    rng = h - l
    if not rng or not a:
        return 0
    rv = x.vol[i] / (x.vol50[i - 1] or 1)
    cl = (c - l) / rng
    prior = x.c[max(0, i - CLIMAX_WINDOW):i]
    if rv < CLIMAX_RV or rng < CLIMAX_RANGE * a or not prior:
        return 0
    if (x.c[i - 1] / max(prior) - 1.0) * 100.0 <= CLIMAX_FALL and cl >= 0.5:
        return 1
    if (x.c[i - 1] / min(prior) - 1.0) * 100.0 >= CLIMAX_RISE and cl <= 0.5:
        return -1
    return 0


def _strength(x, j, mid, side):
    """the read's own sign of strength (wyckoff.py) on session j against the range's middle; side -1, its mirror,
    a sign of weakness"""
    if x.vol50[j - 1] is None:
        return False
    o, h, l, c = _bar(x, j)
    a = x.atrs[j - 1] or x.atrs[j]
    rng = h - l
    if not rng or not a:
        return False
    rv = x.vol[j] / (x.vol50[j - 1] or 1)
    cl = (c - l) / rng
    po, ph, pl, pc = _bar(x, j - 1)
    if rv < SOS_RV or rng < SOS_RANGE * a:
        return False
    if side > 0:
        return cl >= SOS_CLOSE and c > mid and c > ph
    return cl <= 1.0 - SOS_CLOSE and c < mid and c < pl


def _swings(x, end):
    """the read's minor swings confirmed by session `end` (pivots.zigzag on the sessions to it)"""
    piv = x.minor if end == x.n - 1 else pivots.zigzag(x.bars[:end + 1], x.atrs[:end + 1], MINOR_K)
    return [p for p in piv if p.confirmed]


def _state(x, s, side, piv, upto):
    """the range a climax at s opens, read through session `upto`: a dict, its phase None before the automatic rally
    (reaction), "void" once the schematic is broken"""
    from .candles import NEAR_ATR                               # the read's level distance (candles.py)
    kind = "accumulation" if side > 0 else "distribution"
    st = {"kind": kind, "side": side, "climax": s, "phase": None, "void": False, "ar": None, "st": None,
          "spring": None, "sos": None, "left": None}
    ar = next((p for p in piv if p.kind == ("H" if side > 0 else "L") and s < p.i <= upto), None)
    stop = ar.i if ar else upto
    lows = [float(b["l"]) for b in x.bars[s:stop + 1]]
    highs = [float(b["h"]) for b in x.bars[s:stop + 1]]
    if side > 0:
        floor, ceiling = min(lows), (ar.price if ar else None)
    else:
        floor, ceiling = (ar.price if ar else None), max(highs)
    st.update(floor=floor, ceiling=ceiling)
    if ar is None:
        return st
    st["ar"] = ar.i
    test = next((p for p in piv if p.kind == ("L" if side > 0 else "H") and ar.i < p.i <= upto), None)
    if test is None:
        for j in range(ar.i + 1, upto + 1):                     # before the test: the range must hold
            c = x.c[j]
            tol = NEAR_ATR * (x.atrs[j] or x.atrs[upto])
            if (side > 0 and (c > ceiling or c < floor - tol)) or (side < 0 and (c < floor or c > ceiling + tol)):
                st["void"] = True
                return st
        st["phase"] = "A"
        return st
    tol = NEAR_ATR * (x.atrs[test.i] or x.atrs[upto])
    edge = floor if side > 0 else ceiling
    so, sh, sl, sc = _bar(x, s)
    to, th, tl, tc = _bar(x, test.i)
    if abs(test.price - edge) > tol or x.vol[test.i] >= x.vol[s] or (th - tl) >= (sh - sl):
        st["void"] = True                                       # not a secondary test of the climax's area
        return st
    st["st"] = test.i
    if side > 0:
        floor = min(floor, test.price)
    else:
        ceiling = max(ceiling, test.price)
    st.update(floor=floor, ceiling=ceiling)
    mid = (floor + ceiling) / 2.0
    phase = "B"
    for j in range(test.i + 1, upto + 1):
        o, h, l, c = _bar(x, j)
        if side > 0:
            if phase in ("B", "C"):
                if c < floor:
                    st["void"] = True
                    return st
                if phase == "B" and l < floor and c > floor:
                    st["spring"], phase = j, "C"
                    continue
                if _strength(x, j, mid, 1) and (phase == "C" or c > ceiling):
                    st["sos"], phase = j, "D"
                elif c > ceiling:
                    st["void"] = True                           # out of the range with no sign of strength
                    return st
            else:
                if c < floor:
                    st["void"] = True
                    return st
                if c > ceiling and j != st["sos"]:
                    st["left"] = st["left"] or j
                    phase = "E"
                elif c <= ceiling:
                    phase = "D"
        else:
            if phase in ("B", "C"):
                if c > ceiling:
                    st["void"] = True
                    return st
                if phase == "B" and h > ceiling and c < ceiling:
                    st["spring"], phase = j, "C"                # the upthrust after distribution
                    continue
                if _strength(x, j, mid, -1) and (phase == "C" or c < floor):
                    st["sos"], phase = j, "D"
                elif c < floor:
                    st["void"] = True
                    return st
            else:
                if c > ceiling:
                    st["void"] = True
                    return st
                if c < floor and j != st["sos"]:
                    st["left"] = st["left"] or j
                    phase = "E"
                elif c >= floor:
                    phase = "D"
    st["phase"] = phase
    return st


def phase(x, end=None):
    """the Wyckoff phase at session `end` (the last by default) from the sessions to it, or None: a dict with the
    range's kind, side (+1 accumulation, -1 distribution), phase, its events' sessions and its floor and ceiling"""
    end = x.n - 1 if end is None else end
    if end < 80 or not x.atrs[end]:
        return None
    piv = _swings(x, end)
    tr = None
    for i in range(max(CLIMAX_WINDOW, end - LOOKBACK + 1), end + 1):
        side = _climax(x, i)
        if not side:
            continue
        if tr is not None:
            st = _state(x, tr[0], tr[1], piv, i - 1)
            c = x.c[i]
            inside = (st["floor"] is not None and c >= st["floor"]) if side > 0 else \
                (st["ceiling"] is not None and c <= st["ceiling"])
            if not st["void"] and st["phase"] and tr[1] == side and inside:
                continue                                        # a heavy test that closed inside the live range
        tr = (i, side)
    if tr is None:
        return None
    st = _state(x, tr[0], tr[1], piv, end)
    if st["void"] or not st["phase"]:
        return None
    return st


def _phase_fact(x, st):
    acc = st["kind"] == "accumulation"
    ph = st["phase"]
    side = st["side"] if ph in ("C", "D", "E") else 0
    w = x.when
    ev = [f"{'a selling' if acc else 'a buying'} climax on {w(st['climax'])}",
          f"an automatic {'rally' if acc else 'reaction'} to {w(st['ar'])}"]
    if st["st"] is not None:
        ev.append(f"a secondary test on {w(st['st'])} on lighter volume")
    if st["spring"] is not None:
        ev.append(f"{'a spring' if acc else 'an upthrust'} on {w(st['spring'])} "
                  f"{'under its floor' if acc else 'over its ceiling'} that closed back inside")
    if st["sos"] is not None:
        ev.append(f"a sign of {'strength' if acc else 'weakness'} on {w(st['sos'])}")
    if st["left"] is not None:
        ev.append(f"a close {'over' if acc else 'under'} the range on {w(st['left'])}")
    rng = f"{pct(x.pct_of(st['floor']))} to {pct(x.pct_of(st['ceiling']))}"
    text = (f"Since {ev[0]}, it has traded in a range from {rng}: {W.join(ev[1:])}. That is Wyckoff {st['kind']}, "
            f"phase {ph}, {PHASE_WORDS[(st['kind'], ph)]}.")
    last = {"A": "automatic " + ("rally" if acc else "reaction"), "B": "secondary test",
            "C": "spring" if acc else "upthrust", "D": "sign of " + ("strength" if acc else "weakness"),
            "E": "left the range"}[ph]
    when_last = {"A": st["ar"], "B": st["st"], "C": st["spring"], "D": st["sos"], "E": st["left"]}[ph]
    reading = f"Wyckoff: {st['kind']}, phase {ph} ({last} {w(when_last)})"
    wrong = None
    if side > 0:
        lo = min(st["floor"], float(x.bars[st["spring"]]["l"])) if st["spring"] is not None else st["floor"]
        wrong = (lo, "the bottom of the range") if lo < x.close else None
    elif side < 0:
        hi = max(st["ceiling"], float(x.bars[st["spring"]]["h"])) if st["spring"] is not None else st["ceiling"]
        wrong = (hi, "the top of the range") if hi > x.close else None
    data = {k: st[k] for k in ("kind", "phase", "climax", "ar", "st", "spring", "sos", "left", "floor", "ceiling")}
    return Fact("wyckoff.phase", "Wyckoff", "context", side, 0.0, f"Wyckoff {st['kind']}, phase {ph}", text, reading,
                "wyckoff_phase", 0.0, data, f"it is in phase {ph} of a Wyckoff {st['kind']}", wrong)


def effort(x, prior=()):
    """the last session's effort against its result: heavy volume that did not move price, on a level after a move
    (a vote, the volume class), or a move of an ATR or more on light volume (said, no vote); none on a session the
    read's own Wyckoff events read (`prior`: wyckoff.py's facts)"""
    from .candles import NEAR_ATR, PRIOR_ATR                    # the read's own candle rule (candles.py)
    from .candlesticks import _level
    if x.n < 60 or not x.vol50[-1] or not x.atr:
        return []
    if any(f.family == "Wyckoff" and f.data.get("ago") == 0 for f in prior):
        return []
    n = x.n - 1
    rv = x.vol[-1] / x.vol50[-1]
    move = (x.c[-1] - x.c[-2]) / (x.atrs[-2] or x.atr)
    chg = (x.c[-1] / x.c[-2] - 1.0) * 100.0
    o, h, l, c = _bar(x, n)
    when = x.on(n, cap=True)
    if rv >= HEAVY and abs(move) < MOVE:
        before = (x.c[-2] - x.c[-12]) / x.atr if x.n >= 12 else 0.0
        if before <= -PRIOR_ATR:
            side, area = 1, _level(x, l, n, True, NEAR_ATR)
        elif before >= PRIOR_ATR:
            side, area = -1, _level(x, h, n, False, NEAR_ATR)
        else:
            return []
        if area is None or (side < 0 and h <= x.close):
            return []
        where = W.join(area.labels(2))
        who = "buyers absorbing the selling" if side > 0 else "sellers absorbing the buying"
        return [Fact("wyckoff.effort", "Wyckoff", "volume", side, min(0.8, 0.3 + 0.15 * rv),
                     f"Heavy volume, little progress at {area.labels(1)[0]}",
                     f"{when} it traded {rv:.1f}x its average volume yet closed {pct(chg)} from the session before "
                     f"({atr_words(move)}), at {where}, after {'falling' if side > 0 else 'rising'} "
                     f"{atr_words(before)} in the ten sessions before: effort without result, {who}.",
                     f"Effort and result {x.when(n)}: {rv:.1f}x volume, {pct(chg)} at {area.labels(1)[0]}",
                     "effort_result", 0.5, {"rv": rv, "move": move, "chg": chg, "before": before,
                                            "level": area.labels(2)},
                     f"heavy volume did not move it at {area.labels(1)[0]}",
                     (h, "the high of that session") if side < 0 else None)]
    if rv <= LIGHT and abs(move) >= MOVE:
        return [Fact("wyckoff.result", "Wyckoff", "context", 0, 0.0, "A wide move on light volume",
                     f"{when} it moved {pct(chg)} ({atr_words(move)}) on {rv:.1f}x its average volume: more result "
                     "than effort, a move the volume does not confirm.",
                     f"Effort and result {x.when(n)}: {pct(chg)} on {rv:.1f}x volume", "effort_result", 0.0,
                     {"rv": rv, "move": move, "chg": chg})]
    return []


# Votes wait for evidence (the owner's rule, 2026-10-19: nothing arbitrary): effort against result is read and shown
# as context and votes nothing until a study shows it predicts; setting the flag restores its vote exactly as built.
EFFORT_VOTE = False


def facts(x, prior=()):
    out = _facts(x, prior)
    if EFFORT_VOTE:
        return out
    return [dataclasses.replace(f, cls="context", strength=0.0, rarity=0.0, clause="", wrong=None)
            if f.cls != "context" else f for f in out]


def _facts(x, prior=()):
    """the phase and the session's effort against its result (`prior`: wyckoff.py's facts for this read)"""
    out = []
    st = phase(x)
    if st:
        out.append(_phase_fact(x, st))
    return out + effort(x, prior)


W.GLOSSARY.update({
    "wyckoff_phase": ("Wyckoff phases", "A trading range after a fall (accumulation) or a rise (distribution) runs "
                                        "through phases: A stops the move, B builds a cause inside the range, C "
                                        "tests it (a spring under the floor, an upthrust over the ceiling), D shows "
                                        "the side in control, E leaves the range (Wyckoff, as Wyckoff Analytics "
                                        "draws his schematics)."),
    "effort_result": ("Effort versus result", "Wyckoff's third law: volume is the effort, the move its result. Heavy "
                                              "volume that barely moves price, or a wide move on light volume, means "
                                              "the two disagree, which often comes before the trend stops or turns."),
})
