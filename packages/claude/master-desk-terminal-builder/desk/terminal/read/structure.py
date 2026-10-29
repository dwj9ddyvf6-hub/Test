"""Price structure: the nearest floor and ceiling and how many kinds of level stack there, a retest of a level the
name broke out from, a reclaim or loss of the 20 and 50-day averages, and where price sits in the retracement of its
one-year swing (and whether the 200-day sits in the same band)."""
from .core import Fact, atr_words, pct

STRONG = 2.0                     # an area this heavy (a tested swing, or a swing and an average) is a real floor or ceiling
NEAR = 3.0                       # read floors and ceilings within 3 ATR of the close


def _list(labels):
    labels = list(labels)
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + " and " + labels[-1]


def _atr(x, price):
    d = abs(x.at_atr(price))
    return "right at the close" if d < 0.1 else atr_words(d)


def strong(a):
    return a.anchored or a.weight >= STRONG


def _separate(a):
    """the separate levels in an area: each member once, a cleared swing high and its breakout level one level (one
    event), a round number none (no kind: Area.confluence)"""
    return len([m for m in a.members if m.family != "round" and not (m.family in ("swing", "swing_major")
                                                                     and m.i in a._twin)])


def _meet(a):
    """how many levels of how many kinds meet in an area, in words: "5 levels (3 kinds) meet\""""
    k, m = a.confluence, _separate(a)
    return f"{m} level{'s' if m != 1 else ''} ({k} kind{'s' if k != 1 else ''}) meet"


def floors(x, deepest=3.0):
    """strong areas centred at or under the close (within 0.1 ATR), nearest first, no deeper than `deepest` ATR"""
    atr, c = x.atr, x.close
    return [a for a in reversed(x.areas) if a.price <= c + 0.1 * atr and strong(a) and (c - a.hi) / atr <= deepest]


def ceilings(x):
    """strong areas centred over the close (by more than 0.1 ATR), nearest first"""
    atr, c = x.atr, x.close
    return [a for a in x.areas if a.price > c + 0.1 * atr and strong(a)]


def facts(x):
    out = []
    if not x.atr or not x.areas:
        return out
    c, atr = x.close, x.atr
    inside = [a for a in x.areas if a.lo - 0.2 * atr <= c <= a.hi + 0.2 * atr and a.price <= c + 0.1 * atr
              and strong(a)]
    below = [a for a in floors(x, NEAR) if a.hi < c - 0.2 * atr][:1]
    above = [a for a in ceilings(x) if c < a.lo and (a.lo - c) / atr <= NEAR][:1]   # wholly above it (A-A4)
    if inside:
        a = max(inside, key=lambda z: z.weight)
        out.append(Fact("levels.on", "Levels", "structure", 1, min(0.8, 0.35 + 0.1 * a.confluence),
                        "Sitting on stacked support" if a.confluence >= 2 else "Sitting on support",
                        f"Price sits on {_list(a.labels(3))}"
                        + (f", where {_meet(a)}." if a.confluence >= 2 else "."),
                        f"Levels: on support ({a.confluence} kinds stacked)", "stack", 0.3 + 0.1 * a.confluence,
                        {"lo": a.lo, "hi": a.hi, "confluence": a.confluence, "levels": _separate(a)},
                        "it sits on stacked support" if a.confluence >= 2 else "it sits on support"))
    if below:
        a = below[0]
        d = x.pct_of(a.hi)
        # sitting on support already: this floor is the next one under it, never "the nearest" beside "sits on"
        # (NE on 2026-10-26 read "Support −5.3% below" beside "Sitting on support")
        nxt = bool(inside)
        out.append(Fact("levels.floor", "Levels", "structure", 1, min(0.5, 0.15 + 0.08 * a.confluence),
                        f"{'Next support' if nxt else 'Support'} {pct(d)} below",
                        f"The {'next floor under it' if nxt else 'nearest floor'} is {pct(d)} below ({_atr(x, a.hi)})"
                        + (f", where {_meet(a)}" if a.confluence >= 2 else "") + f": {_list(a.labels(3))}.",
                        f"{'Next' if nxt else 'Nearest'} support: {pct(d)} "
                        f"({a.confluence} kind{'s' if a.confluence != 1 else ''})", "support",
                        0.1 * a.confluence, {"lo": a.lo, "hi": a.hi, "confluence": a.confluence,
                                             "levels": _separate(a)},
                        f"support sits {pct(d).lstrip('−')} below"))
    if above:
        a = above[0]
        d = x.pct_of(max(a.lo, c))
        tight = (a.lo - c) / atr <= 1.0
        out.append(Fact("levels.ceiling", "Levels", "structure", -1 if tight else 0, 0.35 if tight else 0.0,
                        f"Resistance {pct(d)} above",
                        f"The nearest ceiling is {pct(d)} above ({_atr(x, a.lo)})"
                        + (f", where {_meet(a)}" if a.confluence >= 2 else "") + f": {_list(a.labels(3))}"
                        + (": little room before sellers have stepped in before." if tight else "."),
                        f"Nearest resistance: {pct(d)} ({a.confluence} kind{'s' if a.confluence != 1 else ''})",
                        "resistance", 0.1 * a.confluence, {"lo": a.lo, "hi": a.hi, "confluence": a.confluence,
                                                           "levels": _separate(a)},
                        f"resistance sits {pct(d).lstrip('+')} overhead",
                        wrong=(a.hi, "the top of that resistance") if tight else None))
    out += _retest(x)
    out += _averages(x)
    out += _fib_year(x)
    return out


def _retest(x):
    """a close within half an ATR above a former high that price broke out above in the last 30 sessions (its latest
    breakout: a level that failed once and broke out again is read from the second: the audit's A7)"""
    from .levels import last_cross
    for lv in x.levels:
        if lv.family != "breakout" or lv.i is None:
            continue
        crossed = last_cross(x.bars, lv)
        if crossed is None or x.n - 1 - crossed > 30 or crossed == x.n - 1:
            continue
        dist = (x.close - lv.price) / x.atr
        low_touch = min(float(b["l"]) for b in x.bars[-5:])
        if -0.2 <= dist <= 0.5 and low_touch <= lv.price + 0.3 * x.atr:
            return [Fact("levels.retest", "Levels", "structure", 1, 0.55, "Retesting its breakout level",
                         f"It broke out above {lv.label.replace(' breakout level', ' high')} and has come back to test it "
                         "from above: old resistance acting as new support.", "Levels: retesting the breakout level",
                         "retest", 0.5, {"level": lv.price})]
    return []


def _averages(x):
    out = []
    for nd, series in ((20, x.sma20), (50, x.sma50)):
        if series[-1] is None or series[-4] is None:
            continue
        now_above = x.close > series[-1]
        was_above = x.c[-4] > series[-4]
        if now_above and not was_above:
            out.append(Fact(f"levels.reclaim{nd}", "Levels", "structure", 1, 0.35 if nd == 50 else 0.2,
                            f"Reclaimed its {nd}-day average",
                            f"It closed back above its {nd}-day average in the last three sessions.",
                            f"{nd}-day average: reclaimed", "moving_average", 0.35))
        elif was_above and not now_above:
            out.append(Fact(f"levels.reclaim{nd}", "Levels", "structure", -1, 0.35 if nd == 50 else 0.2,
                            f"Lost its {nd}-day average", f"It closed below its {nd}-day average in the last three sessions.",
                            f"{nd}-day average: lost", "moving_average", 0.35, {}, "",
                            (series[-1], f"the {nd}-day average")))
        elif now_above:
            touched = min(float(b["l"]) for b in x.bars[-3:]) <= series[-1] + 0.25 * x.atr
            rising = series[-1] > series[-6]
            if touched and rising:
                out.append(Fact(f"levels.bounce{nd}", "Levels", "structure", 1, 0.4 if nd == 50 else 0.3,
                                f"Holding its rising {nd}-day",
                                f"It dipped to its rising {nd}-day average in the last three sessions and held above it.",
                                f"{nd}-day average: tested and held", "moving_average", 0.4))
    return out


def _fib_year(x):
    """the retracement of the one-year swing: the 252-session low to high (or high to low), the band price sits in,
    and whether the 200-day average sits in that band"""
    yr = x.bars[-252:]
    if len(yr) < 200:
        return []
    off = x.n - len(yr)
    hi_i = max(range(len(yr)), key=lambda j: float(yr[j]["h"])) + off
    lo_i = min(range(len(yr)), key=lambda j: float(yr[j]["l"])) + off
    hi, lo = float(x.bars[hi_i]["h"]), float(x.bars[lo_i]["l"])
    if hi <= lo:
        return []
    rising = lo_i < hi_i
    gave = (hi - x.close) / (hi - lo) if rising else (x.close - lo) / (hi - lo)
    bands = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    k = next((i for i in range(len(bands) - 1) if gave < bands[i + 1]), len(bands) - 2)
    lo_b, hi_b = bands[k], bands[k + 1]
    m200 = x.sma200[-1]
    in_band = False
    if m200 is not None:
        g200 = (hi - m200) / (hi - lo) if rising else (m200 - lo) / (hi - lo)
        in_band = lo_b <= g200 < hi_b
    band = f"{lo_b * 100:g}–{hi_b * 100:g}%"
    if rising:
        side = 1 if gave <= 0.382 else 0 if gave <= 0.618 else -1
        strength = 0.3 if gave <= 0.236 else 0.2 if side > 0 else 0.0 if side == 0 else 0.35
        text = (f"The rise ran {x.when(lo_i)} to {x.when(hi_i)}; price is inside the {band} retracement band"
                + (", where the 200-day average also sits." if in_band else "."))
        head = (f"Gave back {gave * 100:.0f}% of its one-year rise" if gave > 0.02 else "At the top of its one-year rise")
        if side < 0:
            text += " Past 62% the rise is in doubt."
    else:
        side = -1 if gave <= 0.382 else 0 if gave <= 0.618 else 1
        strength = 0.3 if side < 0 else 0.0 if side == 0 else 0.3
        text = (f"The fall ran {x.when(hi_i)} to {x.when(lo_i)}; price is inside the {band} band"
                + (", where the 200-day average also sits." if in_band else "."))
        head = f"Recovered {gave * 100:.0f}% of its one-year fall"
    # context, not a vote: the year's high and low and the close between them are the 52-week range's reading (the
    # trend kind); voted here too, one observation counted as two kinds on 779 reads of 2026-10-16
    return [Fact("levels.fib_year", "Levels", "context", side, strength, head, text,
                 f"One-year swing: {gave * 100:.0f}% {'given back' if rising else 'recovered'} ({band} band"
                 + (", the 200-day in it)" if in_band else ")"),
                 "fibonacci", 0.35 if in_band else 0.15, {"gave": gave, "rising": rising, "in_band": in_band})]
