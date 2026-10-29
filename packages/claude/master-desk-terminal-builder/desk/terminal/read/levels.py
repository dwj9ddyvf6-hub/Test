"""Price levels: where buyers or sellers turned price before, where the averages run, where the retracements, the
open gaps and the heaviest trading sit. Every level comes from the name's own completed daily bars. Levels within
half a day's range (0.5 ATR) merge into one area; an area that several independent kinds of evidence share (a tested
swing low, a rising average, a retracement) is a stronger floor or ceiling than any one of them, which is what a
trader means by levels that stack. Prices stay inside the desk: the page shows distances in % and ATR."""
import contextvars
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime

from ...util import ET
from . import ta

Level = namedtuple("Level", "price family weight label i")      # i: the bar it dates from (None for an average)

# how much one level of each kind counts (Osler 2000, Kavajecz & Odders-White 2004, Bulkowski; the research notes in
# docs/research/2026-10-18-terminal/SETUPS_V2.md): tested swings, retested breakouts and the 52-week extremes 2; one
# swing, an untested breakout, the 50 and 200-day averages, anchored VWAP and the heaviest-traded price 1; the 20-day
# average, retracements, open gaps and round numbers 0.5 (practitioner tools without measured support). An area counts
# each kind once: its weight is the sum over the kinds present, so ten touches of one kind never outvote three kinds.
AT_EXTREME_ATR = 0.1             # a close this near a 52-week high is at it: the high is no level over it (A1), and
                                 # the trend may say no seller from the past year is above it
WEIGHT = {"swing_major": 1.0, "swing": 0.5, "breakout": 1.0, "ma200": 1.0, "ma50": 1.0, "ma20": 0.5, "fib": 0.5,
          "vwap": 1.0, "gap": 0.5, "volume": 1.0, "high52": 2.0, "low52": 2.0, "round": 0.5,
          "ma200w": 2.0, "ma50w": 1.0}
# the weekly averages are Echo's (his newsletter 2: "a 200 week moving average carries far more weight than a 50 day";
# the 200-week is in 41 of his X posts, the 50-week in 12): the 200-week anchors a floor as a 52-week extreme does
FAMILY = {"swing_major": "swing", "swing": "swing", "breakout": "breakout", "ma200": "average", "ma50": "average",
          "ma20": "average", "fib": "retracement", "vwap": "vwap", "gap": "gap", "volume": "volume",
          "high52": "range", "low52": "range", "round": "round", "ma200w": "average", "ma50w": "average"}
TESTED = 2.0                 # a swing area tested twice or more, or a breakout level retested, counts 2
MERGE_ATR, SPAN_ATR = 0.5, 1.0
LOOKBACK = 250


def _date(bars, i):
    return datetime.fromtimestamp(float(bars[i]["t"]), tz=ET)


_CITED = contextvars.ContextVar("cited", default=None)


@contextmanager
def citing():
    """{words: ISO session}: every bar the read names in its words while the block runs, by the words it was named in
    (when, and the month a breakout level is named by); the first naming of a phrase wins. The chart's marks are the
    published words' citations (read/geometry.py)"""
    log = {}
    token = _CITED.set(log)
    try:
        yield log
    finally:
        _CITED.reset(token)


def _cite(words, bars, i):
    log = _CITED.get()
    if log is not None and words not in log:
        log[words] = _date(bars, i).date().isoformat()


def when(bars, i):
    """bar i's session in words: "Oct 3", and "Nov 3, 2025" when it falls in a year before the last bar's"""
    t = _date(bars, i)
    s = t.strftime("%b ") + str(t.day)
    s = s if t.year == _date(bars, -1).year else f"{s}, {t.year}"
    _cite(s, bars, i)
    return s


def _month(bars, i):
    t = _date(bars, i)
    s = t.strftime("%B") + ("" if t.year == _date(bars, -1).year else f" {t.year}")
    _cite(f"the {s} breakout level", bars, i)
    return s


def collect(bars, atrs, minor, major, close=None, weekly=None, unit="day"):
    """[Level] from the last LOOKBACK sessions: swing points (major and minor degree), former highs price has since
    cleared (the breakout levels), the 20, 50 and 200-day averages (the 20, 50 and 200-week on weekly bars: `unit`)
    and the 50 and 200-week averages (`weekly`, {50: price, 200: price}), the retracements of the last major swing,
    the average price paid since the last major low and high, unfilled gaps, the heaviest-traded price and the 52-week
    range"""
    n = len(bars)
    if n < 30:
        return []
    close = float(bars[-1]["c"]) if close is None else close
    lo_i = max(0, n - LOOKBACK)
    out = []
    seen = set()
    for degree, piv in (("swing_major", major), ("swing", minor)):
        for p in piv:
            if p.i < lo_i or not p.confirmed or (p.i, p.kind) in seen:
                continue
            seen.add((p.i, p.kind))
            kind = "low" if p.kind == "L" else "high"
            out.append(Level(p.price, degree, WEIGHT[degree], f"the {when(bars, p.i)} {kind}", p.i))
            if p.kind == "H" and close > p.price and max(float(b["c"]) for b in bars[p.i + 1:]) > p.price:
                out.append(Level(p.price, "breakout", WEIGHT["breakout"],
                                 f"the {_month(bars, p.i)} breakout level", p.i))
    cs = ta.closes(bars)
    for nd, fam in ((20, "ma20"), (50, "ma50"), (200, "ma200")):
        m = ta.sma(cs, nd)[-1]
        if m is not None:
            out.append(Level(m, fam, WEIGHT[fam], f"the {nd}-{unit} average", None))
    for nw, fam in ((50, "ma50w"), (200, "ma200w")):
        m = (weekly or {}).get(nw)
        if m is not None:
            out.append(Level(m, fam, WEIGHT[fam], f"the {nw}-week average", None))
    recent = [p for p in major if p.i >= lo_i]
    for p0, p1 in zip(recent[-3:-1], recent[-2:]):         # the last completed major swing and the one in progress
        span = p1.price - p0.price
        what = "rise" if span > 0 else "drop"
        for f in (0.382, 0.5, 0.618):
            out.append(Level(p1.price - f * span, "fib", WEIGHT["fib"] * (1.0 if f == 0.382 else 1.2),
                             f"the {f * 100:g}% retracement of the {when(bars, p0.i)}–{when(bars, p1.i)} {what}",
                             p1.i))
    for kind in ("L", "H"):
        p = next((q for q in reversed(major) if q.kind == kind and q.confirmed and lo_i <= q.i <= n - 6), None)
        if p:
            v = ta.avwap(bars, p.i)[-1]
            if v is not None:
                out.append(Level(v, "vwap", WEIGHT["vwap"],
                                 f"the average price paid since the {when(bars, p.i)} {'low' if kind == 'L' else 'high'}",
                                 p.i))
    out += gaps(bars, lo_i)
    v = poc(bars[-120:], atrs[-1])
    if v is not None:
        out.append(Level(v, "volume", WEIGHT["volume"], "the most-traded price of six months", None))
    step = _round_step(close)
    if step:
        k0 = int(close // step)
        for k in range(k0 - 2, k0 + 4):
            if k > 0:
                out.append(Level(k * step, "round", WEIGHT["round"], "a round number", None))
    yr = bars[-252:]
    hi_i = max(range(len(yr)), key=lambda j: float(yr[j]["h"])) + n - len(yr)
    lw_i = min(range(len(yr)), key=lambda j: float(yr[j]["l"])) + n - len(yr)
    # an extreme is a level once price has left it (the audit's A-A1: XOM read "sitting on the 52-week high" it
    # printed that session): the high once it sits more than 0.1 ATR over the close, the low once a confirmed swing
    # low marks it
    atr = (atrs[-1] if atrs else None) or 0.0
    if float(bars[hi_i]["h"]) > close + AT_EXTREME_ATR * atr:
        out.append(Level(float(bars[hi_i]["h"]), "high52", WEIGHT["high52"], "the 52-week high", hi_i))
    if any(p.kind == "L" and p.confirmed and p.i == lw_i for p in list(minor) + list(major)):
        out.append(Level(float(bars[lw_i]["l"]), "low52", WEIGHT["low52"], "the 52-week low", lw_i))
    return out


def _round_step(price):
    """the round-number spacing traders watch at this price: 5 under 100, 50 under 1,000, 500 under 10,000"""
    import math
    if price <= 0:
        return None
    return 10 ** math.floor(math.log10(price)) / 2


def gaps(bars, lo_i=0):
    """unfilled gaps: a session that opened and stayed beyond the one before (its low above the prior high, or its
    high below the prior low) that later sessions have not closed back through; the level is the gap's far edge, the
    price a fill reaches"""
    out = []
    for i in range(max(1, lo_i), len(bars)):
        p, b = bars[i - 1], bars[i]
        if float(b["l"]) > float(p["h"]):
            edge = float(p["h"])
            if all(float(x["l"]) > edge for x in bars[i + 1:]):
                out.append(Level(edge, "gap", WEIGHT["gap"], f"the open gap of {when(bars, i)}", i))
        elif float(b["h"]) < float(p["l"]):
            edge = float(p["l"])
            if all(float(x["h"]) < edge for x in bars[i + 1:]):
                out.append(Level(edge, "gap", WEIGHT["gap"], f"the open gap of {when(bars, i)}", i))
    return out


def poc(bars, atr):
    """the price where the most volume traded: each session's volume spread evenly over its range, in bins of half
    an ATR (a volume profile's point of control)"""
    if not bars or not atr:
        return None
    w = atr * 0.5
    base = min(float(b["l"]) for b in bars)
    bins = {}
    for b in bars:
        lo, hi, v = float(b["l"]), float(b["h"]), float(b.get("v") or 0)
        a, z = int((lo - base) / w), int((hi - base) / w)
        share = v / (z - a + 1)
        for k in range(a, z + 1):
            bins[k] = bins.get(k, 0.0) + share
    if not bins:
        return None
    k = max(bins, key=lambda j: (bins[j], -j))
    return base + (k + 0.5) * w


def last_cross(bars, lv):
    """the session of the latest close from under the level to over it, after the level's own session, or None"""
    cs = [float(b["c"]) for b in bars]
    hits = [j for j in range(lv.i + 1, len(cs)) if cs[j] > lv.price >= cs[j - 1]]
    return hits[-1] if hits else None


def retested(bars, lv, atr):
    """a breakout level price came back to and held: since its latest breakout it closed an ATR over the level, a low
    then came back within 0.3 ATR of it, and no close fell more than 0.25 ATR under it (the audit's A3: any low near
    the level after the first close over it counted, failed breakouts included)"""
    j = last_cross(bars, lv)
    if j is None:
        return False
    after = bars[j:]
    if any(float(b["c"]) < lv.price - 0.25 * atr for b in after):
        return False
    away = next((k for k, b in enumerate(after) if float(b["c"]) >= lv.price + atr), None)
    return away is not None and any(float(b["l"]) <= lv.price + 0.3 * atr for b in after[away + 1:])


class Area:
    """levels that sit together: a floor below price or a ceiling above it. Its weight sums each kind once (the
    kind's heaviest member); a swing kind tested at two separate sessions or more, or a breakout level price has come
    back to and held, counts TESTED. An area is anchored when it holds a kind worth TESTED (a tested swing, a retested
    breakout, a 52-week extreme): the floors a plan may buy at"""

    def __init__(self, members, bars=None, atr=None):
        self.members = sorted(members, key=lambda m: -m.weight)
        ps = [m.price for m in members]
        self.lo, self.hi = min(ps), max(ps)
        swing_i = {m.i for m in members if m.family in ("swing", "swing_major")}
        # a cleared swing high and its breakout level are one event: one kind, the swing (the audit's A-A2)
        self._twin = {m.i for m in members if m.family == "breakout" and m.i in swing_i}
        by = {}
        for m in members:
            f = self.kind_of(m)
            by[f] = max(by.get(f, 0.0), m.weight)
        swings = sorted({m.i for m in members if m.family in ("swing", "swing_major") and m.i is not None})
        tests = 0
        last = -99
        for i in swings:
            if i - last >= 5:
                tests, last = tests + 1, i
        self.touches = tests
        if tests >= 2:
            by["swing"] = TESTED
        if bars is not None and atr:
            for lv in (m for m in members if m.family == "breakout"):
                if retested(bars, lv, atr):
                    by[self.kind_of(lv)] = TESTED
                    break
        self.kinds = by
        self.families = set(by)
        self.weight = sum(by.values())
        self.anchored = any(v >= TESTED for v in by.values())
        wsum = sum(m.weight for m in members)
        self.price = sum(m.price * m.weight for m in members) / wsum

    def kind_of(self, m):
        """the kind a member counts as: its family's, a breakout level twinned with its own swing high a swing"""
        return "swing" if m.family == "breakout" and m.i in self._twin else FAMILY[m.family]

    @property
    def confluence(self):
        return len(self.families - {"round"})

    def labels(self, k=3):
        """up to k members' names, heaviest kind first, one of each kind before a second of any; a cleared swing high
        is named once, as its breakout level"""
        order = [m for m in sorted(self.members, key=lambda m: (-self.kinds.get(self.kind_of(m), 0), -m.weight))
                 if m.family != "round" and not (m.family in ("swing", "swing_major") and m.i in self._twin)]
        out, kinds = [], set()
        for m in order:
            if self.kind_of(m) not in kinds and m.label not in out:
                kinds.add(self.kind_of(m))
                out.append(m.label)
        out += [m.label for m in order if m.label not in out]
        return list(dict.fromkeys(out))[:k] or ["a round number"]

    def __repr__(self):
        return f"Area({self.lo:.2f}-{self.hi:.2f} w={self.weight:.1f} {sorted(self.families)})"


def areas(levels, atr, bars=None):
    """levels merged into areas, lowest first: a level joins the area below it while it sits within MERGE_ATR of that
    area's top and the area stays within SPAN_ATR"""
    out, cur = [], []
    for lv in sorted(levels, key=lambda x: x.price):
        if cur and (lv.price - cur[-1].price > MERGE_ATR * atr or lv.price - cur[0].price > SPAN_ATR * atr):
            out.append(Area(cur, bars, atr))
            cur = []
        cur.append(lv)
    if cur:
        out.append(Area(cur, bars, atr))
    return out


PIVOT_KINDS = ("classic", "fibonacci", "woodie", "camarilla")


def pivot_points(prev, kind="classic"):
    """the next session's pivot levels from the prior completed bar {h, l, c}: classic (P = HLC/3; R1/S1 = 2P - L/H;
    R2/S2 = P +- range; R3/S3 = H + 2(P - L), L - 2(H - P)), fibonacci (P +- 0.382, 0.618, 1.0 of the range), woodie (P =
    (H + L + 2C)/4, then R1/S1/R2/S2 as classic) and camarilla (C +- range x 1.1/12, /6, /4, /2). A context table for
    the card: it feeds no plan (practitioner levels without a measured weight, like the round numbers' 0.5)"""
    h, l, c = (float(prev[k]) for k in ("h", "l", "c"))
    rng = h - l
    if kind == "classic":
        p = (h + l + c) / 3.0
        return {"P": p, "R1": 2 * p - l, "S1": 2 * p - h, "R2": p + rng, "S2": p - rng,
                "R3": h + 2 * (p - l), "S3": l - 2 * (h - p)}
    if kind == "fibonacci":
        p = (h + l + c) / 3.0
        return {"P": p, "R1": p + 0.382 * rng, "S1": p - 0.382 * rng, "R2": p + 0.618 * rng, "S2": p - 0.618 * rng,
                "R3": p + rng, "S3": p - rng}
    if kind == "woodie":
        p = (h + l + 2 * c) / 4.0
        return {"P": p, "R1": 2 * p - l, "S1": 2 * p - h, "R2": p + rng, "S2": p - rng}
    if kind == "camarilla":
        out = {}
        for i, div in enumerate((12.0, 6.0, 4.0, 2.0), 1):
            out[f"R{i}"], out[f"S{i}"] = c + rng * 1.1 / div, c - rng * 1.1 / div
        return out
    raise ValueError(f"unknown pivot kind: {kind}")
