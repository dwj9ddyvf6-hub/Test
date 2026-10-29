"""The classic chart patterns the read's own four (patterns.py: a base, flags, double tops and bottoms, ascending and
descending triangles) do not draw, and the quality of every break the read states.

The patterns: head and shoulders and its inverse, triple tops and bottoms, the symmetrical triangle, rising, falling
and broadening (expanding) wedges, rectangles, rising and falling channels, bull and bear pennants, and the cup with
handle and its inverse. The detector is the study's (lab/src/patlib.py; its parameters and fields in lab/patterns.md;
self-tested and proven point in time there), ported line for line: Bulkowski's definitions (Encyclopedia of Chart
Patterns) made mechanical on the read's own 2-ATR zigzag. A swing counts from the session that confirmed it. Each
instance is known from one session (c0) and carries two lines, U above and L below; its break is the first close beyond
either after its last touch; Bulkowski's bust (less than 10% beyond the breakout price, then a close beyond the
pattern's far side) marks the break failed. The read takes the state at its last bar exactly as the study's table does
at a session: per pattern, the latest break or bust of the last 20 sessions, else the latest instance still forming
(scan; tests/test_read_patterns.py proves it point in time).

One stretch of bars is voted once. The read's four detectors keep their readings, as they are tuned and tested. An
instance on the bars of a reading that votes (one of the read's own pattern facts, or a new pattern read before it in
ORDER) is said as context and votes nothing, and so is a second neutral reading of one stretch; a pattern that points
a way may read bars only a neutral reading covers (a base with no advance before it votes nothing). A wedge's swings
are the wedge (call.reconcile, as a flag's drift is the flag).

Every break the read states carries its quality (quality): how many of the closes from the break on, the last five at
most, held beyond the level it broke (the study's NHELD), and whether the break session was a stretched spike.

Nothing here claims to predict: the study found no edge in any of these patterns alone, nor in a break's age or start
(docs/research/2026-10-19-patterns/PATTERNS.md, 2l and "Lindy"); the forward ledger measures them."""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from . import plan
from . import words as W
from .core import MINOR_K, Fact, atr_words, pct
from .geometry import point, seg

# ---- the study's parameters (lab/patterns.md, "How every pattern is read"; patlib.py), unchanged ----
TOL = 0.75                 # "equal" highs or lows, and a trendline touch: within 0.75 ATR
MINH = 3.5                 # minimum height of tops, bottoms, head and shoulders and cups (ATR)
MINW = 3.0                 # minimum height (widest part) of the two-line patterns (ATR)
TRI_GAP = (20, 200)        # triple top/bottom: sessions from the first to the third peak
HS_SPAN = (15, 200)        # head and shoulders: sessions from shoulder to shoulder
HS_SYM = (0.4, 2.5)        # head-to-right-shoulder time over left-shoulder-to-head time
HS_SHOULDERS, HS_NECK = 0.5, 0.3   # shoulders within half the height of each other and of the neckline's ends; each
                                   # shoulder at least 0.3 of the height over the neckline
SPAN2 = (20, 200)          # two-line patterns: sessions from the first to the fifth touch
CONV = 0.65                # converging: end width at most 0.65 of start width
PAR = (0.8, 1.25)          # parallel (channels): end width within 0.8..1.25 of start width
DIV = 2.0                  # diverging (broadening): end width at least twice the start width
CTOL = 0.25                # closes between the first and last touch may stray this far (ATR) beyond the lines
FORM = 20                  # a pattern stays "forming" at most 20 sessions (triangles and wedges: to the apex)
M = 20                     # a break (or its bust) stays on the table 20 sessions
NHELD = 5                  # held: closes beyond the breakout price among the last 5 since the break
BUST = 0.10                # Bulkowski's bust: less than 10% beyond the breakout price before the reversal
POLE_LEN, POLE_MIN, POLE_RATE = 15, 5.0, 0.5   # flagpole: 5+ ATR within 15 sessions, 0.5+ ATR a session
FLAG_LEN = (5, 15)                    # flag/pennant: 5 to 15 sessions after the pole's top
FLAG_RETRACE = 0.5                    # the flag gives back at most half the pole
FLAG_PAR, PEN_CONV, FLAG_SLOPE = (0.75, 1.33), 0.6, 0.05
CUP_LEN = (30, 325)                   # cup: 6 to 65 weeks lip to lip
HANDLE = (5, 20)                      # handle: 1 to 4 weeks
CUP_ROUND, CUP_POS, CUP_DEPTH = 0.4, (0.2, 0.8), 0.5
LOOK = FORM + 2 * M        # an instance shows at most this long after it became known (a break by its last forming
                           # session, a bust within M of the break, shown M more): nothing older can show at a bar

BIAS = {"tris": 0, "wr": -1, "wf": 1, "bro": 0, "rect": 0, "chu": 0, "chd": 0}   # the two-line patterns' expected break
CONVERGING = ("tris", "wr", "wf")

# ---- the read's patterns ----
# the order a stretch is read in: the patterns that point a way first (the reversals, then wedges and pennants), the
# ones that can break either way after; a later one on the same bars is said, not voted
ORDER = ("hs", "ihs", "tt", "tb", "cup", "icup", "wr", "wf", "penu", "pend", "tris", "bro", "rect", "chu", "chd")
CODES = frozenset(ORDER)
NAMES = {"hs": "head-and-shoulders top", "ihs": "inverse head and shoulders", "tt": "triple top", "tb": "triple bottom",
         "tris": "symmetrical triangle", "wr": "rising wedge", "wf": "falling wedge", "bro": "broadening formation",
         "rect": "rectangle", "chu": "rising channel", "chd": "falling channel", "penu": "bull pennant",
         "pend": "bear pennant", "cup": "cup with handle", "icup": "inverted cup with handle"}
KEY = {"hs": "pattern.hs", "ihs": "pattern.hs", "tt": "pattern.triple", "tb": "pattern.triple",
       "tris": "pattern.symmetrical", "wr": "pattern.wedge", "wf": "pattern.wedge", "bro": "pattern.broadening",
       "rect": "pattern.rectangle", "chu": "pattern.channel", "chd": "pattern.channel", "penu": "pattern.pennant",
       "pend": "pattern.pennant", "cup": "pattern.cup", "icup": "pattern.cup"}
EXPECT = {"hs": -1, "ihs": 1, "tt": -1, "tb": 1, "wr": -1, "wf": 1, "penu": 1, "pend": -1, "cup": 1, "icup": -1}
LINES = {"hs": ("the head's high", "the neckline"), "ihs": ("the neckline", "the head's low"),
         "tt": ("the highest top", "the lower of the two lows between the tops"),
         "tb": ("the higher of the two highs between the bottoms", "the lowest bottom"),
         "tris": ("the triangle's upper line", "the triangle's lower line"),
         "wr": ("the wedge's upper line", "the wedge's lower line"),
         "wf": ("the wedge's upper line", "the wedge's lower line"),
         "bro": ("the formation's upper line", "the formation's lower line"),
         "rect": ("the rectangle's top", "the rectangle's bottom"),
         "chu": ("the channel's upper line", "the channel's lower line"),
         "chd": ("the channel's upper line", "the channel's lower line"),
         "penu": ("the pennant's upper line", "the pennant's lower line"),
         "pend": ("the pennant's upper line", "the pennant's lower line"),
         "cup": ("the cup's right lip", "the middle of the cup"),
         "icup": ("the middle of the inverted cup", "the inverted cup's right lip")}
# the drawing's names for each pattern's two lines (upper, lower) and its named points (geometry: four words at most)
DRAW = {"hs": ("Head's high", "Neckline"), "ihs": ("Neckline", "Head's low"), "tt": ("Highest top", "Low between tops"),
        "tb": ("High between bottoms", "Lowest bottom"), "tris": ("Triangle upper line", "Triangle lower line"),
        "wr": ("Wedge upper line", "Wedge lower line"), "wf": ("Wedge upper line", "Wedge lower line"),
        "bro": ("Upper line", "Lower line"), "rect": ("Rectangle top", "Rectangle bottom"),
        "chu": ("Channel top", "Channel bottom"), "chd": ("Channel top", "Channel bottom"),
        "penu": ("Pennant top", "Pennant bottom"), "pend": ("Pennant top", "Pennant bottom"),
        "cup": ("Right lip", "Cup middle"), "icup": ("Cup middle", "Right lip")}
POINTS = {"hs": {0: "Left shoulder", 2: "Head", 4: "Right shoulder"},
          "ihs": {0: "Left shoulder", 2: "Head", 4: "Right shoulder"},
          "tt": {0: "First top", 2: "Second top", 4: "Third top"},
          "tb": {0: "First bottom", 2: "Second bottom", 4: "Third bottom"},
          "cup": {0: "Left lip", 2: "Right lip"}, "icup": {0: "Left lip", 2: "Right lip"},
          "penu": {0: "Pole start", 1: "Pole top"}, "pend": {0: "Pole start", 1: "Pole bottom"}}
LEARN = {"hs": "head_shoulders", "ihs": "inverse_head_shoulders", "tt": "triple_top", "tb": "triple_bottom",
         "tris": "symmetrical_triangle", "wr": "rising_wedge", "wf": "falling_wedge", "bro": "broadening",
         "rect": "rectangle", "chu": "channel_up", "chd": "channel_down", "penu": "pennant", "pend": "pennant",
         "cup": "cup_handle", "icup": "inverted_cup"}

# Strengths, on the read's own scale for the matching state of its own patterns (patterns.py). The data cannot rank
# them: no pattern held an edge alone in the study (PATTERNS.md 2l), so a new pattern weighs what its nearest kin in
# the read weighs. Forming: a possible top or bottom as the forming double (0.35), a wedge as the forming triangle
# (0.4), a pennant as the forming flag (0.5). Complete (a close through the line that completes it): a top or bottom
# as the confirmed double (0.7), a wedge as the triangle's break (0.65), a pennant as the flag's break (0.7). A break
# of a pattern that can go either way: the rectangle as the base's breakout and breakdown (by volume, below), the
# symmetrical triangle and the broadening formation as the triangle's break (0.65), a channel as a break of the swing
# structure (trend.swings, 0.5). Failed: as the base's failed breakout (0.5) and failed breakdown (0.45). The rarity
# each fact carries (the fixed ranking the standouts use before a session's roster shares exist) is likewise the read's
# own for the matching state: forming 0.35 (the double), a break 0.55 to 0.6 (the breakdown, the breakout), a failed
# break 0.5, a neutral reading 0.2 (the base).
FORMING = {"hs": 0.35, "ihs": 0.35, "tt": 0.35, "tb": 0.35, "cup": 0.35, "icup": 0.35, "wr": 0.4, "wf": 0.4,
           "penu": 0.5, "pend": 0.5}
BROKE = {"hs": 0.7, "ihs": 0.7, "tt": 0.7, "tb": 0.7, "cup": 0.7, "icup": 0.7, "wr": 0.65, "wf": 0.65, "penu": 0.7,
         "pend": 0.7, "tris": 0.65, "bro": 0.65, "chu": 0.5, "chd": 0.5}
VOL_CONFIRM = 1.4          # the read's (patterns.VOL_CONFIRM): a break on 1.4x average volume is confirmed by volume
RECT_BROKE = {(1, True): 0.8, (1, False): 0.55, (-1, True): 0.75, (-1, False): 0.5}   # the base's breakout/breakdown
FAILED = {-1: 0.5, 1: 0.45}

# The stretched spike. The study's data cannot decide a cut: over 32,702 pattern breaks on 612 roster names
# (2017-2026, every third name, the study's detector), no cut on the break session's close past the line or on its
# range, swept from the median to the top 2.5% of breaks, changed the next 5 or 10 sessions in both eras (|t| at most
# 2.1, signs unstable); a close further past the line only came back to the line less often within 5 sessions (73% in
# the lowest tenth, 20-24% in the highest). So the label uses the read's own lines rather than a new number: a close
# more than 1 ATR past the line is past the band in which the read's plan still buys a breakout (plan._breakouts, "ran
# past it"), and a range of 1.8 ATR or more is the size of the read's wide-range day (candles.py). Both together: 8.0%
# of the study's breaks, whose next 5 and 10 sessions matched the rest (|t| at most 0.5 in both eras).
STRETCH_ATR = 1.0
SPIKE_ATR = 1.8
PLAN_OFFSET = 0.1          # plan._breakouts sets a breakout's trigger 0.1 ATR over its line

# The same stretch of bars: two readings share at least SAME of the shorter one's bars. From the readings themselves:
# on 400 roster names, each read at 5 sessions 25 apart, 888 pairs of a new pattern and another pattern reading
# overlapped. They fall in two groups with a trough between: 56 share under a tenth of the shorter span (one pattern
# starts about where the other ends), and 812 share a fifth or more (median 0.76; 288 share 95% or more); 20 fall
# in 0.10-0.20. The cut sits in the middle of that trough; the data cannot choose within it (2% of the pairs).
SAME = 0.15

GLOSSARY = {
    "head_shoulders": ("Head and shoulders", "Three peaks, the middle one highest, over a neckline through the two "
                                             "lows between them; a close below the neckline completes the top, a "
                                             "close over the head voids it."),
    "inverse_head_shoulders": ("Inverse head and shoulders", "Three lows, the middle one lowest, under a neckline "
                                                             "through the two highs between them; a close above the "
                                                             "neckline completes the bottom, a close under the head "
                                                             "voids it."),
    "triple_top": ("Triple top", "Three highs at about the same level with two lows between them; a close below the "
                                 "lower of those lows confirms it."),
    "triple_bottom": ("Triple bottom", "Three lows at about the same level with two highs between them; a close above "
                                       "the higher of those highs confirms it."),
    "symmetrical_triangle": ("Symmetrical triangle", "Falling highs and rising lows that converge; the first close "
                                                     "outside either line is the break, either way."),
    "rising_wedge": ("Rising wedge", "Highs and lows both rising between two converging lines; a close below the "
                                     "lower line completes it."),
    "falling_wedge": ("Falling wedge", "Highs and lows both falling between two converging lines; a close above the "
                                       "upper line completes it."),
    "broadening": ("Broadening formation", "Higher highs and lower lows between two diverging lines, an expanding "
                                           "wedge; the first close outside either line is the break."),
    "rectangle": ("Rectangle", "A flat top and a flat bottom, each touched again; the first close outside either is "
                               "the break."),
    "channel_up": ("Rising channel", "Swings rising between two parallel lines; a close outside either line breaks "
                                     "the channel."),
    "channel_down": ("Falling channel", "Swings falling between two parallel lines; a close outside either line "
                                        "breaks the channel."),
    "pennant": ("Pennant", "A sharp move (the pole), then a short pause between converging lines on lighter volume; a "
                           "close out of the pause in the pole's direction completes it."),
    "cup_handle": ("Cup with handle", "A rounded dip between two highs at about the same level, then a shallow "
                                      "handle; a close above the right lip completes it."),
    "inverted_cup": ("Inverted cup with handle", "A rounded rise between two lows at about the same level, then a "
                                                 "shallow handle; a close below the right lip completes it."),
}
W.GLOSSARY.update(GLOSSARY)
# the plan engine names a pattern's measured move by its kind (plan._KIND): the three new patterns that feed plans
plan._KIND.update({"triple": "triple bottom", "cup": "cup with handle", "hs": "inverse head and shoulders"})


# ---- the swings: the read's zigzag (pivots.zigzag), with the session that confirmed each ----
class Swings:
    def __init__(self, i, p, k, c):
        self.i, self.p = np.array(i, dtype=np.int64), np.array(p, dtype=np.float64)
        self.k, self.c = np.array(k, dtype=np.int64), np.array(c, dtype=np.int64)


def zigzag(o, h, l, c, a, k=MINOR_K):
    """confirmed swings, oldest first, alternating: bar of the extreme, price, +1 high / -1 low, confirming bar. The
    read's pivots.zigzag on arrays (each session two ordered price events, high then low on a down day, else low then
    high; a leg's extreme is confirmed once price reverses k ATR, that session's ATR, from it or takes out the previous
    opposite swing); the open leg's extreme is not a swing"""
    I, P, KK, C = [], [], [], []
    start = next((i for i in range(len(a)) if np.isfinite(a[i]) and a[i]), None)    # pivots.zigzag's first ATR
    if start is None:
        return Swings(I, P, KK, C)
    d = 0
    hi = lo = hi_i = lo_i = None
    opp = opp_i = None
    for i in range(start, len(c)):
        thr = k * a[i]
        evs = ((h[i], 1), (l[i], -1)) if c[i] < o[i] else ((l[i], -1), (h[i], 1))
        for px, kind in evs:
            if d == 0:
                if hi is None or (kind == 1 and px > hi):
                    hi, hi_i = (px, i) if kind == 1 else (h[i], i)
                if lo is None or (kind == -1 and px < lo):
                    lo, lo_i = (px, i) if kind == -1 else (l[i], i)
                if kind == -1 and hi - px >= thr:
                    I.append(hi_i), P.append(hi), KK.append(1), C.append(i)
                    d, lo, lo_i, opp, opp_i = -1, px, i, None, None
                elif kind == 1 and px - lo >= thr:
                    I.append(lo_i), P.append(lo), KK.append(-1), C.append(i)
                    d, hi, hi_i, opp, opp_i = 1, px, i, None, None
                continue
            if d == 1:
                if kind == 1:
                    if px > hi:
                        hi, hi_i, opp, opp_i = px, i, None, None
                    continue
                if opp is None or px < opp:
                    opp, opp_i = px, i
                if hi - opp >= thr or (P and opp < P[-1]):
                    I.append(hi_i), P.append(hi), KK.append(1), C.append(i)
                    d, lo, lo_i, opp, opp_i = -1, opp, opp_i, None, None
            else:
                if kind == -1:
                    if px < lo:
                        lo, lo_i, opp, opp_i = px, i, None, None
                    continue
                if opp is None or px > opp:
                    opp, opp_i = px, i
                if opp - lo >= thr or (P and opp > P[-1]):
                    I.append(lo_i), P.append(lo), KK.append(-1), C.append(i)
                    d, hi, hi_i, opp, opp_i = 1, opp, opp_i, None, None
    return Swings(I, P, KK, C)


# ---- every instance, its break and its bust (patlib's Table.add) ----
class Book:
    """one name's bars as arrays and every pattern instance drawn on them, in the study's creation order"""

    def __init__(self, o, h, l, c, v, a):
        self.o, self.h, self.l, self.c, self.v, self.a = o, h, l, c, v, a
        self.n = len(c)
        self.insts = []

    @classmethod
    def of(cls, x):
        bs = x.bars
        arr = [np.array([float(b[k]) for b in bs], dtype=np.float64) for k in ("o", "h", "l", "c")]
        v = np.array([float(b.get("v") or 0.0) for b in bs], dtype=np.float64)
        a = np.array([np.nan if q is None else float(q) for q in x.atrs], dtype=np.float64)
        return cls(*arr, v, a)

    def add(self, code, c0, x_end, form_end, exp, u0, us, l0, ls, height, bias, ext_lo, ext_hi, x0, pts):
        """an instance known from session c0, lines U(x) = u0 + us (x - x_end) and L(x) = l0 + ls (x - x_end), its
        lowest low and highest high ext_lo, ext_hi. Its break is the first close beyond either line in (x_end, exp];
        it shows as forming on [c0, form_end] until then. Returns the break session or None"""
        n, c, h, l = self.n, self.c, self.h, self.l
        last = min(exp, n - 1)
        b = s = bp = f = None
        if last > x_end:
            xs = np.arange(x_end + 1, last + 1)
            U = u0 + us * (xs - x_end)
            L = l0 + ls * (xs - x_end)
            cc = c[xs]
            hit = (cc > U) | (cc < L)
            if hit.any():
                j = int(hit.argmax())
                b = int(xs[j])
                s = 1 if cc[j] > U[j] else -1
                bp = float(U[j] if s == 1 else L[j])
        if b is not None and bp > 0:
            e = min(b + M, n - 1)
            if e > b:
                xs = np.arange(b + 1, e + 1)
                if s == 1:
                    ext = np.maximum.accumulate(h[b:e + 1])[1:] / bp - 1.0
                    bust = (c[xs] < ext_lo) & (ext < BUST)
                else:
                    ext = 1.0 - np.minimum.accumulate(l[b:e + 1])[1:] / bp
                    bust = (c[xs] > ext_hi) & (ext < BUST)
                if bust.any():
                    f = int(xs[bust.argmax()])
        fe = min(form_end, last if b is None else b - 1)
        self.insts.append({"code": code, "od": len(self.insts), "c0": int(c0), "x0": int(x0), "x_end": int(x_end),
                           "fe": int(fe), "u0": float(u0), "us": float(us), "l0": float(l0), "ls": float(ls),
                           "height": float(height), "bias": bias, "ext_lo": float(ext_lo), "ext_hi": float(ext_hi),
                           "b": b, "s": s, "bp": bp, "f": f, "pts": pts})
        return b

    def shown(self, ins, t):
        """(class, event) the instance shows at bar t (1 broken, 0 forming; the event: its break, bust or detection
        session), or None"""
        b, f = ins["b"], ins["f"]
        if b is not None and ins["bp"] > 0:
            v0, v1 = max(b, ins["c0"]), min((b if f is None else f) + M, self.n - 1)
            if v0 <= t <= v1:
                return 1, (f if f is not None and t >= f else b)
        if ins["c0"] <= t <= ins["fe"]:
            return 0, ins["c0"]
        return None

    def state(self, ins, t):
        """the instance as it stands at bar t, from what is known at t only (a break or bust after t is not in it):
        its lines there, and the study's fields (form, up, dn, fail, since, hgt, tgt, held, brk, brr)"""
        c, a = self.c, self.a
        cls_, _ = self.shown(ins, t)
        st = {k: ins[k] for k in ("code", "c0", "x0", "x_end", "u0", "us", "l0", "ls", "height", "bias", "ext_lo",
                                  "ext_hi", "pts")}
        st.update(t=t, upper=ins["u0"] + ins["us"] * (t - ins["x_end"]),
                  lower=ins["l0"] + ins["ls"] * (t - ins["x_end"]), hgt=float(ins["height"] / a[t]))
        if cls_ == 0:
            bias = ins["bias"]
            line = st["upper"] if bias > 0 else st["lower"]
            st.update(state="form", fail=False, b=None, s=None, bp=None, f=None, since=None, held=None, of=None,
                      brk=None, brr=None,
                      tgt=float((line + bias * ins["height"] - c[t]) / a[t]) if bias else float("nan"))
            return st
        b, s, bp, f = ins["b"], ins["s"], ins["bp"], ins["f"]
        fail = f is not None and t >= f
        lo = max(t - NHELD + 1, b)
        ab = a[b - 1]
        st.update(state="up" if s == 1 else "dn", fail=fail, b=b, s=s, bp=bp, f=f if fail else None, since=t - b,
                  held=int((s * (c[lo:t + 1] - bp) > 0).sum()), of=t - lo + 1,
                  brk=float(s * (c[b] - bp) / ab), brr=float((self.h[b] - self.l[b]) / ab),
                  tgt=float("nan") if fail else float((bp + s * ins["height"] - c[t]) / a[t]))
        return st


class View:
    """the chart as drawn (sign +1) or upside down (sign -1): a bottom is the top of the mirrored chart"""

    def __init__(self, bk, Z, sign):
        self.sign = sign
        if sign > 0:
            self.h, self.l, self.c = bk.h, bk.l, bk.c
        else:
            self.h, self.l, self.c = -bk.l, -bk.h, -bk.c
        self.a, self.v = bk.a, bk.v
        if Z is not None:
            self.pi, self.pc, self.pp, self.pk = Z.i, Z.c, sign * Z.p, sign * Z.k

    def emit(self, bk, code, c0, x_end, form_end, exp, u0, us, l0, ls, height, bias, ext_lo, ext_hi, x0, pts):
        if self.sign > 0:
            return bk.add(code, c0, x_end, form_end, exp, u0, us, l0, ls, height, bias, ext_lo, ext_hi, x0, pts)
        return bk.add(code, c0, x_end, form_end, exp, -l0, -ls, -u0, -us, height, -bias, -ext_hi, -ext_lo, x0, pts)


# ---- tops and bottoms on the swings (drawn as tops; the mirror gives the bottoms) ----
def _triple(V, bk, j, A, code):
    if j < 5:
        return
    pp, pi = V.pp, V.pi
    H1, L1, H2, L2, H3, L0 = pp[j - 4], pp[j - 3], pp[j - 2], pp[j - 1], pp[j], pp[j - 5]
    tops = (H1, H2, H3)
    if max(tops) - min(tops) > TOL * A or not (TRI_GAP[0] <= pi[j] - pi[j - 4] <= TRI_GAP[1]):
        return
    neck, top = min(L1, L2), max(tops)
    hgt = top - neck
    if hgt < MINH * A or not L0 < neck:
        return
    c0 = int(V.pc[j])
    V.emit(bk, code, c0, int(pi[j]), c0 + FORM, c0 + FORM, top, 0.0, neck, 0.0, hgt, -1, neck, top, int(pi[j - 4]),
           tuple(int(q) for q in pi[j - 4:j + 1]))


def _hs(V, bk, j, A, code):
    if j < 5:
        return
    pp, pi = V.pp, V.pi
    LS, L1, HD, L2, RS, L0 = pp[j - 4], pp[j - 3], pp[j - 2], pp[j - 1], pp[j], pp[j - 5]
    iLS, iL1, iHD, iL2, iRS = (int(q) for q in pi[j - 4:j + 1])
    if HD - max(LS, RS) < TOL * A:
        return
    ns = (L2 - L1) / (iL2 - iL1)

    def neck(q):
        return L1 + ns * (q - iL1)
    hgt = HD - neck(iHD)
    if hgt < MINH * A or abs(LS - RS) > HS_SHOULDERS * hgt or abs(L2 - L1) > HS_SHOULDERS * hgt:
        return
    if min(LS - neck(iLS), RS - neck(iRS)) < HS_NECK * hgt:
        return
    if not (HS_SYM[0] <= (iRS - iHD) / (iHD - iLS) <= HS_SYM[1]) or not (HS_SPAN[0] <= iRS - iLS <= HS_SPAN[1]):
        return
    if not L0 < min(L1, L2):
        return
    c0 = int(V.pc[j])
    V.emit(bk, code, c0, iRS, c0 + FORM, c0 + FORM, HD, 0.0, neck(iRS), ns, hgt, -1, min(L1, L2), HD, iLS,
           (iLS, iL1, iHD, iL2, iRS))


def _pivot_patterns(bk, Z, lo):
    for sign, (chs, ctt) in ((1, ("hs", "tt")), (-1, ("ihs", "tb"))):
        V = View(bk, Z, sign)
        for j in range(len(Z.i)):
            if V.pk[j] != 1 or Z.c[j] < lo:
                continue
            A = bk.a[int(Z.c[j])]
            _hs(V, bk, j, A, chs)
            _triple(V, bk, j, A, ctt)


# ---- two-line patterns on the last five swings (three touches on one line, two on the other) ----
def _line(Z, idx, A, upper, x1):
    """the trendline over swings idx (two or three touches): (slope, value at bar x1, its change first to last touch
    in ATR, how far its middle touch pokes beyond it), or None. Touches all within TOL ATR of each other make a flat
    line, drawn level at the extreme touch. Otherwise the line runs through the first and last touches, and a middle
    touch must lie within TOL ATR of it; a sloped line whose ends differ by TOL ATR or less is neither: None"""
    xs, ps = Z.i[idx].astype(np.float64), Z.p[idx]
    if ps.max() - ps.min() <= TOL * A:
        return 0.0, (ps.max() if upper else ps.min()), 0.0, 0.0
    d = (ps[-1] - ps[0]) / A
    if abs(d) <= TOL:
        return None
    s = (ps[-1] - ps[0]) / (xs[-1] - xs[0])
    poke = 0.0
    if len(idx) == 3:
        dev = ps[1] - (ps[0] + s * (xs[1] - xs[0]))
        if abs(dev) > TOL * A:
            return None
        poke = max(0.0, dev if upper else -dev)
    return s, ps[-1] + s * (x1 - xs[-1]), d, poke


def _classify(dH, dL, r):
    fh, fl = dH == 0.0, dL == 0.0
    uh, dh, ul, dl = dH > TOL, dH < -TOL, dL > TOL, dL < -TOL
    if fh and fl:
        return "rect"
    if r <= CONV:
        if fh and ul:
            return "tria"
        if fl and dh:
            return "trid"
        if dh and ul:
            return "tris"
        if uh and ul:
            return "wr"
        if dh and dl:
            return "wf"
        return None
    if PAR[0] <= r <= PAR[1]:
        if uh and ul:
            return "chu"
        if dh and dl:
            return "chd"
        return None
    return "bro" if r >= DIV else None


def _twoline_patterns(bk, Z, lo):
    c, a = bk.c, bk.a
    for j in range(4, len(Z.i)):
        c0 = int(Z.c[j])
        if c0 < lo:
            continue
        q = np.arange(j - 4, j + 1)
        his, los = q[Z.k[q] == 1], q[Z.k[q] == -1]
        x0, x1 = int(Z.i[j - 4]), int(Z.i[j])
        span = x1 - x0
        if not (SPAN2[0] <= span <= SPAN2[1]):
            continue
        A = a[c0]
        U, L = _line(Z, his, A, True, x1), _line(Z, los, A, False, x1)
        if U is None or L is None:
            continue
        (su, uref, dH, pu), (sl, lref, dL, pl) = U, L
        w1 = uref - lref
        w0 = w1 + (su - sl) * (x0 - x1)
        if w0 <= 0 or w1 <= 0:
            continue
        code = _classify(dH, dL, w1 / w0)
        if code is None or code in ("tria", "trid"):        # the read's own ascending and descending triangles
            continue
        if code == "bro":                                    # a broadening formation needs three touches on each
            if j < 5 or x1 - Z.i[j - 5] > SPAN2[1]:          # line: the swing before the window joins the line
                continue                                     # that has two, and the six must still broaden
            q = np.arange(j - 5, j + 1)
            his, los = q[Z.k[q] == 1], q[Z.k[q] == -1]
            U, L = _line(Z, his, A, True, x1), _line(Z, los, A, False, x1)
            if U is None or L is None:
                continue
            (su, uref, dH, pu), (sl, lref, dL, pl) = U, L
            x0 = int(Z.i[j - 5])
            w1 = uref - lref
            w0 = w1 + (su - sl) * (x0 - x1)
            if w0 <= 0 or w1 <= 0 or _classify(dH, dL, w1 / w0) != "bro":
                continue
        lo_x, hi_x = Z.p[los].min(), Z.p[his].max()
        height = (w0 + w1) / 2 if code in ("chu", "chd") else hi_x - lo_x   # a channel's width; else highest
        if height < MINW * A:                                               # high less lowest low (Bulkowski)
            continue
        xs = np.arange(x0, x1 + 1)                           # closes stay inside, give or take CTOL ATR or what
        if ((c[xs] > uref + su * (xs - x1) + max(CTOL * A, pu)).any()       # the line's own middle touch pokes out
                or (c[xs] < lref + sl * (xs - x1) - max(CTOL * A, pl)).any()):
            continue
        exp = c0 + FORM
        if code in CONVERGING:
            exp = min(exp, int(np.floor(x1 + w1 * span / (w0 - w1))))
        bk.add(code, c0, x1, exp, exp, uref, su, lref, sl, height, BIAS[code], lo_x, hi_x, x0,
               tuple(int(i) for i in Z.i[q]))


# ---- flags and pennants: a steep pole, then a short, shallow pause (the read's own flags are patterns.py's; the
# study's are drawn here only because a pole whose flag broke draws no pennant after it) ----
def _flag_patterns(bk, lo):
    lo_n, hi_n = FLAG_LEN
    for sign, (cf, cp) in ((1, ("flagu", "penu")), (-1, ("flagd", "pend"))):
        V = View(bk, None, sign)
        h, l, v, a = V.h, V.l, V.v, V.a
        n = len(h)
        if n < POLE_LEN + hi_n + 2:
            continue
        nf = np.full(n, -1, dtype=np.int64)                  # sessions since the last highest high of [t-15, t]
        nf[hi_n:] = sliding_window_view(h, hi_n + 1)[:, ::-1].argmax(axis=1)
        pw = sliding_window_view(l, POLE_LEN)[:n - POLE_LEN]  # row p - POLE_LEN: the lows of [p - 15, p - 1]
        plo = np.full(n, np.nan)
        plo_i = np.full(n, -1, dtype=np.int64)
        plo[POLE_LEN:] = pw.min(axis=1)
        plo_i[POLE_LEN:] = pw.argmin(axis=1) + np.arange(n - POLE_LEN)
        pole = h - plo
        with np.errstate(invalid="ignore"):
            okpole = (pole >= POLE_MIN * a) & (pole >= POLE_RATE * a * (np.arange(n) - plo_i))
        done = set()
        for t in np.nonzero(nf >= lo_n)[0]:
            t = int(t)
            if t < lo - hi_n:                                # a pole's earlier flags (for `done`) start 15 back
                continue
            p = t - int(nf[t])
            if p < POLE_LEN or not okpole[p] or p in done:
                continue
            P, q = pole[p], int(plo_i[p])
            if l[p + 1:t + 1].min() < h[p] - FLAG_RETRACE * P:
                continue
            if v[p + 1:t + 1].mean() >= v[q:p + 1].mean():
                continue
            xs = np.arange(p - t, 1, dtype=np.float64)       # p..t, relative to t
            hs, ls_ = h[p:t + 1], l[p:t + 1]
            dx = xs - xs.mean()
            sxx = (dx * dx).sum()
            su, sl = (dx * hs).sum() / sxx, (dx * ls_).sum() / sxx
            uo, lo_ = (hs - su * xs).max(), (ls_ - sl * xs).min()
            wt = uo - lo_
            wp = wt + (su - sl) * (p - t)
            if wp <= 0 or wt <= 0:
                continue
            r = wt / wp
            if FLAG_PAR[0] <= r <= FLAG_PAR[1] and (su + sl) / 2 <= FLAG_SLOPE * a[t]:
                code = cf
            elif r <= PEN_CONV and su < 0 < sl:
                code = cp
            else:
                continue
            if V.emit(bk, code, t, t, t, t + 1, uo, su, lo_, sl, P, 1, ls_.min(), h[p], q, (q, p, t)) is not None:
                done.add(p)


# ---- cup with handle (drawn as the bullish cup; the mirror gives the inverted cup) ----
def _cup_patterns(bk, Z, lo):
    for sign, code in ((1, "cup"), (-1, "icup")):
        V = View(bk, Z, sign)
        h, l, c, a = V.h, V.l, V.c, V.a
        n = len(h)
        if n < CUP_LEN[0] + HANDLE[0] + 2:
            continue
        sel = np.nonzero(V.pk == 1)[0]
        hb, hp, hc = V.pi[sel], V.pp[sel], V.pc[sel]
        h5 = np.full(n, np.inf)
        h5[:n - HANDLE[0]] = sliding_window_view(h[1:], HANDLE[0]).max(axis=1)[:n - HANDLE[0]]
        for r in np.nonzero(h > h5)[0]:
            r = int(r)
            c0 = r + HANDLE[0]
            if r < CUP_LEN[0] or c0 >= n or c0 < lo:
                continue
            A, lip = a[c0], h[r]
            k = min(int(np.searchsorted(hb, r)), int(np.searchsorted(hc, c0, side="right"))) - 1
            while k >= 0 and hb[k] >= r - CUP_LEN[1] and hp[k] < lip - TOL * A:
                k -= 1
            if k < 0 or hb[k] < r - CUP_LEN[1]:
                continue
            il, left = int(hb[k]), hp[k]
            if left > lip + TOL * A or not (CUP_LEN[0] <= r - il <= CUP_LEN[1]):
                continue
            if h[il + 1:r].max() > max(left, lip):
                continue
            m = il + int(l[il:r + 1].argmin())
            bot = l[m]
            D = lip - bot
            if D < MINH * A or D > CUP_DEPTH * abs(lip) or (m < r and h[m:r].max() > lip):
                continue
            if not (CUP_POS[0] <= (m - il) / (r - il) <= CUP_POS[1]):
                continue
            if np.mean(c[il:r + 1] <= bot + D / 3) < CUP_ROUND:
                continue
            mid = bot + D / 2
            if l[r + 1:c0 + 1].min() < mid:
                continue
            end = r + HANDLE[1]
            V.emit(bk, code, c0, c0, end, end, lip, 0.0, mid, 0.0, D, 1, bot, max(left, lip), il, (il, m, r))


def fill(bk, lo=-1):
    """draw on the book's bars every instance known at session lo or later (all of them by default)"""
    Z = zigzag(bk.o, bk.h, bk.l, bk.c, bk.a)
    _pivot_patterns(bk, Z, lo)
    _twoline_patterns(bk, Z, lo)
    _flag_patterns(bk, lo)
    _cup_patterns(bk, Z, lo)
    return bk


def book(x, t=None):
    """the instances that can show at bar t (the last by default): every one known within LOOK sessions of it"""
    bk = Book.of(x)
    return fill(bk, (bk.n - 1 if t is None else t) - LOOK)


def void(st):
    """a break the way the pattern was not drawn to break: the pattern is void and the read says nothing of it"""
    exp = EXPECT.get(st["code"], 0)
    return bool(exp) and st["state"] != "form" and (1 if st["state"] == "up" else -1) != exp


def select(bk, t):
    """{code: its state at bar t}: per pattern the instance the study's table shows there, the latest break or bust
    of the last M sessions, else the latest instance still forming (class, then event, then creation order)"""
    best = {}
    for ins in bk.insts:
        if ins["code"] not in CODES:
            continue
        sh = bk.shown(ins, t)
        if sh is None:
            continue
        key = (sh[0], sh[1], ins["od"])
        if ins["code"] not in best or key > best[ins["code"]][0]:
            best[ins["code"]] = (key, ins)
    return {code: bk.state(ins, t) for code, (_, ins) in best.items()}


def scan(x, t=None):
    """{code: state} at bar t (the last by default), from bars through t only"""
    bk = book(x, t)
    return select(bk, bk.n - 1 if t is None else t)


# ---- the quality of a break ----
def quality(x, line, s, k):
    """a break's quality: of the closes from the break session k on, the last NHELD at most, how many held beyond
    `line` (s +1 above, -1 below); the break session's close past the line and its high-low range, in the ATR of the
    session before (the study's brk and brr); and whether that session was a stretched spike (STRETCH_ATR, SPIKE_ATR)"""
    lo = max(x.n - NHELD, k)
    held = sum(1 for j in range(lo, x.n) if s * (x.c[j] - line) > 0)
    a = (x.atrs[k - 1] if k >= 1 else None) or x.atr
    b = x.bars[k]
    brk = s * (x.c[k] - line) / a
    brr = (float(b["h"]) - float(b["l"])) / a
    return {"at": k, "since": x.n - 1 - k, "held": held, "held_of": x.n - lo, "brk": brk, "brr": brr,
            "stretched": brk > STRETCH_ATR and brr >= SPIKE_ATR}


def _past(v, what):
    return f"just past {what}" if v < 0.05 else f"{atr_words(v)} past {what}"


def quality_text(q, s):
    """the quality as a sentence: "4 of the 5 closes from the break on held above the level it broke, and the break
    session closed 0.6 ATR past it on a 1.4-ATR range." (the last five closes once the break is older)"""
    side = "above" if s > 0 else "below"
    spike = ": a stretched spike." if q["stretched"] else "."
    rng = f"on a {atr_words(q['brr'])} range".replace(" ATR range", "-ATR range")
    if q["held_of"] > 1:
        which = f"the {q['held_of']} closes from the break on" if q["since"] < q["held_of"] else \
            f"the last {q['held_of']} closes"
        return (f"{q['held']} of {which} held {side} the level it broke, and the break session closed "
                f"{_past(q['brk'], 'it')} {rng}{spike}")
    return f"The break session closed {_past(q['brk'], 'the line')} {rng}{spike}"


def quality_reading(q):
    """the quality in the one-line reading: ", held 4 of 5" (", stretched spike")"""
    return (f", held {q['held']} of {q['held_of']}" if q["held_of"] > 1 else "") + \
        (", stretched spike" if q["stretched"] else "")


# ---- the facts ----
def _same(a, b):
    """two spans of bars (first, last) are one stretch: the bars they share are at least SAME of the shorter one's"""
    inter = min(a[1], b[1]) - max(a[0], b[0]) + 1
    return inter > 0 and inter >= SAME * min(a[1] - a[0] + 1, b[1] - b[0] + 1)


def _cap(s):
    return s[:1].upper() + s[1:]


def _plan_data(x, st, side):
    """a bullish pattern's plan lines (plan._breakouts reads trigger, floor, target, kind and line), only where the
    trigger and the floor are real lines and Bulkowski defines the measured move: the triple bottom (its top, its
    lowest bottom), the cup with handle (its right lip, the handle's low) and the inverse head and shoulders (its
    neckline, the right shoulder's low), each with its height added to the break. The neckline may slope: it feeds a
    plan only while its rise over a breakout plan's window stays inside the 0.1 ATR the plan sets its trigger over the
    line (PLAN_OFFSET), so every close over the trigger is a close over the neckline. Wedges and pennants are drawn on
    sloping lines (a pennant's are fitted), and the rest can break either way: they feed no plan"""
    code = st["code"]
    if side <= 0 or code not in ("tb", "cup", "ihs"):
        return {}
    if st["state"] == "form":
        trig = st["upper"]
        if code == "ihs" and st["us"] * plan.WINDOW["breakout"] > PLAN_OFFSET * x.atr:
            return {}
    elif st["state"] == "up" and not st["fail"]:
        trig = st["bp"]
    else:
        return {}
    if code == "tb":
        floor, kind, line = st["lower"], "triple", "the top of its triple bottom"
    elif code == "cup":
        r = st["pts"][2]
        end = st["t"] if st["state"] == "form" else st["b"] - 1
        floor, kind, line = min(float(b["l"]) for b in x.bars[r + 1:end + 1]), "cup", "the right lip of its cup"
    else:
        floor, kind, line = float(x.bars[st["pts"][4]]["l"]), "hs", "the neckline of its inverse head and shoulders"
    return {"trigger": trig, "floor": floor, "target": trig + st["height"], "kind": kind, "line": line}


def _shape(x, st):
    """the pattern's drawing in words, with its sessions"""
    code, p = st["code"], st["pts"]
    w = x.when
    if code in ("hs", "ihs"):
        return (f"a head on {w(p[2])} between shoulders on {w(p[0])} and {w(p[4])}, "
                + ("over a neckline through the lows between them" if code == "hs" else
                   "under a neckline through the highs between them"))
    if code in ("tt", "tb"):
        return f"{'tops' if code == 'tt' else 'bottoms'} at about the same level on {w(p[0])}, {w(p[2])} and {w(p[4])}"
    if code in ("cup", "icup"):
        return (f"a rounded {'cup' if code == 'cup' else 'rise'} from {w(p[0])} to {w(p[2])}, then a handle "
                f"{'above' if code == 'cup' else 'under'} its middle")
    if code in ("penu", "pend"):
        q, top, _ = p
        gain = (float(x.bars[top]["h"]) / float(x.bars[q]["l"]) - 1.0) * 100.0 if code == "penu" else \
            (float(x.bars[top]["l"]) / float(x.bars[q]["h"]) - 1.0) * 100.0
        return (f"a {pct(gain, 0)} {'run' if code == 'penu' else 'fall'} from {w(q)} to {w(top)}, then a pause "
                f"between converging lines on lighter volume")
    what = {"tris": "highs falling and lows rising, converging", "wr": "highs and lows both rising, converging",
            "wf": "highs and lows both falling, converging", "bro": "highs rising and lows falling, widening",
            "rect": "a flat top and a flat bottom", "chu": "swings rising between parallel lines",
            "chd": "swings falling between parallel lines"}[code]
    return f"{what}, touched five times from {w(st['x0'])} to {w(st['x_end'])}" if code != "bro" else \
        f"{what}, touched six times from {w(st['x0'])} to {w(st['x_end'])}"


def _draw(x, st):
    """the instance's two lines, U(x) = u0 + us (x - x_end) and L(x) likewise, from its first touch to its break (or
    to the last bar while it forms)"""
    a, z = st["x0"], (st["b"] if st.get("b") is not None else st["t"])
    up, lo = DRAW[st["code"]]
    u = lambda q: st["u0"] + st["us"] * (q - st["x_end"])                           # noqa: E731
    l_ = lambda q: st["l0"] + st["ls"] * (q - st["x_end"])                          # noqa: E731
    return [seg(x, a, u(a), z, u(z), up, "pattern"), seg(x, a, l_(a), z, l_(z), lo, "pattern")]


def _points(x, st):
    """the sessions the pattern's words name, with its own names for them"""
    code, p = st["code"], st["pts"]
    if code in POINTS:
        out = [point(x, p[k], lab, "pattern") for k, lab in POINTS[code].items()]
    else:
        out = [point(x, st["x0"], "First touch", "pattern"), point(x, st["x_end"], "Last touch", "pattern")]
    if st.get("b") is not None:
        out.append(point(x, st["b"], "Breakout" if st["s"] == 1 else "Breakdown", "pattern"))
    if st.get("f") is not None:
        out.append(point(x, st["f"], "Failed break", "pattern"))
    return out


def _read(x, st):
    """the reading of one instance at the last bar, or None when the pattern is void (it broke the way it was not
    drawn to break, as the read drops a double top price has closed over)"""
    code = st["code"]
    name, art = NAMES[code], W.a(NAMES[code])
    exp = EXPECT.get(code, 0)
    up_w, lo_w = LINES[code]
    c = x.close
    shape = _shape(x, st)
    data = {"code": code, "span": (st["x0"], st["x_end"]), "name": name, "upper": st["upper"],
            "lower": st["lower"], "height": st["height"], "state": st["state"], "draw": _draw(x, st),
            "marks": _points(x, st)}
    learn = LEARN[code]
    if st["state"] == "form":
        if exp:
            line, words = (st["upper"], up_w) if exp > 0 else (st["lower"], lo_w)
            data.update(_plan_data(x, st, exp))
            if code in ("wr", "wf"):
                data["drift"] = "the wedge's rise" if code == "wr" else "the wedge's decline"
            head = (f"A possible {name}" if code in ("hs", "ihs", "tt", "tb", "cup", "icup") else _cap(art))
            text = (f"{_cap(art)}: {shape}. A daily close {'above' if exp > 0 else 'below'} {words} "
                    f"({pct(x.pct_of(line))}) completes it.")
            wrong = None
            if exp < 0:
                wl = st["upper"]
                wrong = (wl, up_w) if wl > c else None
            return Fact(KEY[code], "Pattern", "structure", exp, FORMING[code], head, text,
                        f"Pattern: {name} (forming)", learn, 0.35, data, wrong=wrong)
        text = (f"{_cap(art)}: {shape}. It can break either way: {up_w} sits at {pct(x.pct_of(st['upper']))} and "
                f"{lo_w} at {pct(x.pct_of(st['lower']))}.")
        return Fact(KEY[code], "Pattern", "structure", 0, 0.0, f"In {art}", text, f"Pattern: {name}", learn, 0.2, data)
    if void(st):
        return None
    s = 1 if st["state"] == "up" else -1
    b, bp = st["b"], st["bp"]
    rv = x.vol[b] / (x.vol50[b - 1] or 1)
    q = {"at": b, "since": st["since"], "held": st["held"], "held_of": st["of"], "brk": st["brk"], "brr": st["brr"],
         "stretched": st["brk"] > STRETCH_ATR and st["brr"] >= SPIKE_ATR}
    data.update(q, vol=rv, bp=bp)
    side_w, broke = ("above", "breakout") if s > 0 else ("below", "breakdown")
    words = up_w if s > 0 else lo_w
    level = f"{words} where it broke" if code in ("tris", "wr", "wf", "bro", "chu", "chd", "penu", "pend", "hs",
                                                   "ihs") else words   # a sloping line: its value at the break
    first = (f"{_cap(art)}: {shape}. {x.on(b, cap=True)} it closed {side_w} {words}, on {rv:.1f}x average volume. "
             + quality_text(q, s))
    # held, back inside and failed undone are all read against the level it broke (the breakout price), as the
    # study's held count is: a sloping line drawn on past the pattern is not a level price was ever tested at
    if st["fail"]:
        far = "lowest point" if s > 0 else "highest point"
        if s * (c - bp) > 0:
            return Fact(KEY[code], "Pattern", "structure", 0, 0.0, f"Back {side_w} {level}",
                        first + f" {x.on(st['f'], cap=True)} it closed past the pattern's {far} with less than a 10% "
                        f"move, and it has since closed back {side_w} the level it broke.",
                        f"Pattern: {name}, failed {broke} undone", learn, 0.2, data)
        side = -s
        wrong = (bp, level) if side < 0 and bp > c else None
        return Fact(KEY[code], "Pattern", "structure", side, FAILED[side], f"A failed {broke} from {art}",
                    first + f" {x.on(st['f'], cap=True)} it closed past the pattern's {far} with less than a 10% "
                    f"move: Bulkowski's failed {broke}, which traps {'buyers' if s > 0 else 'sellers'}.",
                    f"Pattern: failed {broke}, {name}", learn, 0.5, data, wrong=wrong)
    if s * (c - bp) <= 0:                                     # the last close is back inside: the break not held
        return Fact(KEY[code], "Pattern", "structure", 0, 0.0, f"Back inside {art}",
                    first + f" The last close is back {'under' if s > 0 else 'over'} the level it broke.",
                    f"Pattern: {name}, {broke} not held{quality_reading(q)}", learn, 0.2, data)
    if code == "rect":
        strength = RECT_BROKE[(s, rv >= VOL_CONFIRM)]
    else:
        strength = BROKE[code]
    data.update(_plan_data(x, st, s))
    if code in ("wr", "wf"):
        data["drift"] = "the wedge's rise" if code == "wr" else "the wedge's decline"
    head = f"Broke out of {art}" if s > 0 else f"Broke down from {art}"
    wrong = (bp, level) if s < 0 and bp > c else None
    return Fact(KEY[code], "Pattern", "structure", s, strength, head, first,
                f"Pattern: {broke}, {name} ({rv:.1f}x volume{quality_reading(q)})", learn,
                0.55 if exp else 0.6, data, wrong=wrong)


# Votes wait for evidence (the owner's rule, 2026-10-19: nothing arbitrary). The study found no pattern that holds alone
# against the next 1 to 60 sessions (PATTERNS.md 1, 2l), and random walks fire each of these on 0-5.3% of sessions,
# about their rate on real charts. Until a study shows one predicts, a new pattern is read and shown as context, votes
# nothing and draws no plan; setting the flag restores every vote and plan exactly as built
# (tests/test_read_patterns.py proves both).
FORMATIONS_VOTE = False
PLAN_FIELDS = ("trigger", "floor", "target", "drift")


def _as_context(f):
    data = {k: v for k, v in (f.data or {}).items() if k not in PLAN_FIELDS}
    return Fact(f.key, "Pattern", "context", f.side, 0.0, f.head, f.text, f.reading, f.learn, 0.0, data)


def facts(x, have=()):
    out = _facts(x, have)
    return out if FORMATIONS_VOTE else [_as_context(f) if f.cls != "context" else f for f in out]


def _facts(x, have=()):
    """the new patterns at the last bar, as facts, after the read's own pattern facts `have`. Each stretch of bars is
    voted once: a pattern on the bars of a reading that votes is said as context, and so is one that would add a
    second neutral reading of them; a pattern that votes may read bars only neutral readings cover (the read's base
    with no advance before it votes nothing). The read's own facts stay as they are. One fact per key"""
    st = scan(x)
    if not st:
        return []
    taken = [(f.data["span"], f.data.get("name") or f.head, bool(f.side)) for f in have
             if (f.data or {}).get("span")]
    keys, out = set(), []
    for code in ORDER:
        s = st.get(code)
        if s is None or KEY[code] in keys:
            continue
        f = _read(x, s)
        if f is None:
            continue
        keys.add(f.key)
        span = (s["x0"], s["x_end"])
        hits = [(nm, v) for sp, nm, v in taken if _same(span, sp)]
        other = None
        if hits and (not f.side or any(v for _, v in hits)):
            other = next((nm for nm, v in hits if v), hits[0][0])
        taken.append((span, NAMES[code], bool(f.side) and other is None))
        if other is not None:
            data = {k: v for k, v in f.data.items() if k not in ("trigger", "floor", "target", "drift")}
            f = Fact(f.key, "Pattern", "context", 0, 0.0, f"{_cap(W.a(NAMES[code]))}, read as its {other}",
                     f.text.rstrip(".") + f"; these bars are read once, as its {other}.",
                     f"Pattern: {NAMES[code]} (its {other})", f.learn, 0.0, dict(data, read_as=other))
        out.append(f)
    return out
