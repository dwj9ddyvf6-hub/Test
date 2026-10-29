"""Wave setups, executed the way a wave trader executes them: Echo Analysis' method (his newsletter, 2026-09-07 to
2026-10-18; docs/research/2026-10-18-terminal/ECHO_WAVES.md). Elliott wave picks the swing to measure, Fibonacci
gives the zone, the 50 and 200-day averages and old structure add confluence, volume and time say whether a pullback
is done, and the buy is the reaction at the zone, not the level. Every setup names where it is wrong.

  wave 2   after five clean waves up (wave 1), a pullback in three waves into the 0.618-0.786 of wave 1 (0.5 to
           0.786 at the widest; 0.886 can hold but marks a weak advance; under the start of wave 1 the count dies)
  wave 4   after waves 1 to 3, a pullback into the 0.382-0.5 of wave 3 (0.236-0.5) that stays over the wave-1 high
  A*       inside a wave 3, a smaller wave 1 and wave 2: the end of that wave 2 is the entry into wave 3 of 3, the
           strongest move on the chart; it is wrong under the start of the smaller wave 1

A pullback that is too shallow, too quick for the advance before it, in one leg rather than three, or on rising
selling volume is not done (his WYFI, 2026-09-20): the read waits for the zone.

Noise. A pattern search finds patterns in noise. Requiring the pushes to carry more volume than the pullbacks (his
volume grammar) halved the clean wave-2 setups found on random walks with random volume (8.2% to 4.2% of 400) while
keeping 8.3% of the real roster (10.3% before), 2026-10-16: real charts show it twice as often as noise.

Degrees. The swings a reader sees are the waves: a wave's top is a high price has not passed since, its start the
earliest low from which the advance reads as five clean waves. Sub-waves are read inside a leg at the size that
first splits it into five or more legs (2.5 down to 1 ATR), so a wave reads as the five a trader would count on it."""
from . import pivots
from .levels import FAMILY, TESTED
from .words import join

SUB_K = (2.5, 2.0, 1.5, 1.0)            # sub-wave swing sizes, coarse to fine, in ATR
LOOKBACK = 160                           # a wave 1 starts within 160 sessions of its top
TOP_WITHIN = 120                         # and its top is within the last 120 sessions
W2 = {"wide": 0.5, "lo": 0.618, "hi": 0.786, "deep": 0.886}
W4 = {"wide": 0.236, "lo": 0.382, "hi": 0.5}  # wave 4 of wave 3: 0.236-0.5, most often 0.382-0.5, over wave 1's high
W3_MIN = 1.618                           # a wave 3 reaches 1.618 times wave 1, his primary measure: at 1.272 the
                                         # read found wave 4 in 1.75% of random walks against 2.39% of real names;
                                         # at 1.618, 1.00% against 2.17% (2026-10-16)
QUICK = 0.25                             # a pullback shorter than a quarter of the advance's sessions is too quick
MIN_QUALITY = 0.6                        # a wave 1 reads as five at least this textbook (quality)
MIN_W1 = 12                              # a wave 1 spans 12 sessions or more: five legs in a week are noise, his
MIN_LEG = 2                              # waves run for weeks; and each of its legs takes 2 sessions or more


MIN_ATR = 12                             # and it travels 12 ATR or more: his waves are big moves. Random walks make
                                         # small fives all the time; at 12 ATR the read finds a clean wave 2 on 3.5% of
                                         # 400 of them against 14.7% of the real roster (2026-10-16), at 0 ATR 11% vs 24%


class Degree:
    """the counting rules of one timeframe's bars"""
    def __init__(self, min_leg, min_w1, lookback, top_within, min_atr, min_n):
        self.min_leg, self.min_w1, self.lookback, self.top_within = min_leg, min_w1, lookback, top_within
        self.min_atr, self.min_n = min_atr, min_n


# daily: the rules above. Weekly (his higher timeframe, CELH and TE): a one-bar leg is a week of trading (CELH's
# wave-1 gap of Feb 2025), a wave 1 takes 8 weeks or more and 8 weekly ATR (a week's range is wider), starts within 5
# years of its top, its top within 2 years
DEGREES = {"daily": Degree(MIN_LEG, MIN_W1, LOOKBACK, TOP_WITHIN, MIN_ATR, 120),
           "weekly": Degree(1, 8, 260, 104, 8, 60)}
WEEKLY_MIN = 60                          # weekly bars a weekly read needs (about 14 months; 1,300 daily bars give 260)


def weekly_ctx(x, bars):
    """the weekly chart built from the daily bars (all of them: up to five years), read at the weekly degree, or None"""
    from . import ta
    from .core import Ctx
    wk = ta.weekly([b for b in bars if b.get("c") is not None])
    if len(wk) < WEEKLY_MIN:
        return None
    xw = Ctx(x.sym, wk, degree="weekly")
    if not xw.atr:
        return None
    return xw


def weekly_facts(xw):
    """the weekly count's facts, each its own (his higher timeframe first): "Weekly: ...", "On the weekly chart: ..."
    in the family Weekly wave, keys wave.w.*"""
    if xw is None:
        return []
    out = []
    for f in facts(xw):
        f.key = "wave.w." + f.key.split(".", 1)[1]
        f.family = "Weekly wave"
        f.head = "Weekly: " + (f.head if f.head.startswith("A*") else f.head[0].lower() + f.head[1:])
        # the head says weekly: the text does not say it again (the language diet: read/diet.py)
        f.reading = "Weekly " + (f.reading if f.reading.startswith("Elliott") else
                                 f.reading[0].lower() + f.reading[1:]) if f.reading else f.reading
        f.clause = f.clause + " on the weekly chart" if f.clause else ""
        out.append(f)
    return out


def deg(x):
    return DEGREES[getattr(x, "degree", "daily")]


def _seq(x, a, b, up, k):
    """the alternating swings of the leg a -> b (sessions) at k ATR: [(i, price)] from its start to its end"""
    lo_key, hi_key = ("l", "h") if up else ("h", "l")
    start, end = (a, float(x.bars[a][lo_key])), (b, float(x.bars[b][hi_key]))
    pv = pivots.zigzag(x.bars[a:b + 1], x.atrs[a:b + 1], k)
    want_first = "H" if up else "L"
    out = [start]
    for p in pv:
        gi = a + p.i
        if gi <= a or gi >= b:
            continue
        want = want_first if len(out) % 2 == 1 else ("L" if want_first == "H" else "H")
        if p.kind == want:
            out.append((gi, p.price))
        elif len(out) > 1:                                  # the same kind again: keep the more extreme
            better = p.price > out[-1][1] if p.kind == "H" else p.price < out[-1][1]
            prev_kind = "L" if want == "H" else "H"
            if p.kind == prev_kind and better:
                out[-1] = (gi, p.price)
    if len(out) % 2 == 0:                                   # the last interior swing runs with the end: drop it
        out.pop()
    out.append(end)
    return out


def _volume_on_pushes(x, seq):
    push, pull = [], []
    for j in range(len(seq) - 1):
        span = x.vol[seq[j][0] + 1:seq[j + 1][0] + 1]
        (push if j % 2 == 0 else pull).extend(span)
    if not push or not pull:
        return True
    return sum(push) / len(push) > sum(pull) / len(pull)


def _five(seq, up, min_leg=MIN_LEG):
    """five clean waves: an odd count of five or more legs, each of MIN_LEG sessions or more, every pullback above the
    start and above the one before (a staircase), the last pullback above the first push's top (no overlap), wave 3
    not the shortest of five"""
    s = 1 if up else -1
    pr = [p for _, p in seq]
    n = len(pr) - 1
    if n < 5 or n % 2 == 0:
        return False
    if any(b - a < min_leg for (a, _), (b, _) in zip(seq, seq[1:])):
        return False
    pulls = pr[2:n:2]
    pushes = pr[1:n + 1:2]
    if any((q - pr[0]) * s <= 0 for q in pulls):
        return False
    if any((b - a) * s <= 0 for a, b in zip(pulls, pulls[1:])) or any((b - a) * s <= 0 for a, b in zip(pushes, pushes[1:])):
        return False
    if (pulls[-1] - pr[1]) * s <= 0:
        return False
    if n == 5:
        w = [abs(pr[i + 1] - pr[i]) for i in range(5)]
        if w[2] < w[0] and w[2] < w[4]:
            return False
    return True


def _near(r, lo, hi):
    """1 inside [lo, hi], falling off with the relative distance outside it"""
    if lo <= r <= hi:
        return 1.0
    d = (lo - r) / lo if r < lo else (r - hi) / hi
    return max(0.0, 1.0 - d)


def quality(imp):
    """how textbook a five reads (0 to 1): wave 2 retraces 0.382-0.786 of wave 1, wave 4 0.236-0.5 of wave 3, wave 3
    reaches 1 to 2.618 of wave 1 and is the longest, the pushes carry the volume. Longer counts (an extended wave
    inside) score on the volume alone, at most 0.75"""
    pr = [p for _, p in imp["seq"]]
    n = len(pr) - 1
    vol = 1.0 if imp["volume_on_pushes"] else 0.5
    if imp["kind"] != "five":
        return 0.0
    if n != 5:
        return 0.75 * vol
    w = [abs(pr[i + 1] - pr[i]) for i in range(5)]
    terms = [_near(w[1] / w[0], 0.382, 0.786), _near(w[3] / w[2], 0.236, 0.5), _near(w[2] / w[0], 1.0, 2.618),
             1.0 if w[2] >= max(w[0], w[4]) else 0.5, vol]
    return sum(terms) / len(terms)


def impulse(x, a, b, up=True):
    """the leg a -> b read one degree down: {"kind": "five" | "three" | "one" | "other", "legs", "seq", "k",
    "volume_on_pushes"}. It is read at the coarsest size that splits it into five legs or more; when that reading is
    no clean five, the swings are searched for the count he would draw (best_five). A leg that never reaches five
    reads as the most legs it shows"""
    best, other = None, None
    for k in SUB_K:
        seq = _seq(x, a, b, up, k)
        n = len(seq) - 1
        if n >= 5:
            if _five(seq, up, deg(x).min_leg):
                return {"kind": "five", "legs": n, "seq": seq, "k": k, "volume_on_pushes": _volume_on_pushes(x, seq)}
            other = {"kind": "other", "legs": n, "seq": seq, "k": k, "volume_on_pushes": _volume_on_pushes(x, seq)}
            break
        if best is None or n > len(best[0]) - 1:
            best = (seq, k)
    found = best_five(x, a, b) if up else None
    if found:
        return found
    if other:
        return other
    seq, k = best
    n = len(seq) - 1
    return {"kind": "three" if n == 3 else "one" if n == 1 else "other", "legs": n, "seq": seq, "k": k,
            "volume_on_pushes": _volume_on_pushes(x, seq)}


SEARCH_K = 1.0                           # the swing lows a count may take its waves 2 and 4 from


def _top(x, a, b):
    return max(range(a, b + 1), key=lambda i: float(x.bars[i]["h"]))


def _bottom(x, a, b):
    return min(range(a, b + 1), key=lambda i: float(x.bars[i]["l"]))


def best_five(x, a, b):
    """the count he would draw on the advance a -> b when no single swing size shows a clean five: waves 2 and 4 chosen
    among its swing lows (at SEARCH_K ATR), waves 1 and 3 the highest highs between them, every point the true extreme
    of its span (WYFI, 2026: the May wiggles sit inside wave 3). Of the counts that keep the impulse rules, the most
    textbook one (quality), or None"""
    if b - a < 5:
        return None
    pv = pivots.zigzag(x.bars[a:b + 1], x.atrs[a:b + 1], SEARCH_K)
    lows = [a + p.i for p in pv if p.kind == "L" and 0 < p.i < b - a]
    if _top(x, a, b) != b or _bottom(x, a, b) != a:
        return None
    best = None
    for j, l2 in enumerate(lows):
        h1 = _top(x, a, l2)
        if not a < h1 < l2:
            continue
        for l4 in lows[j + 1:]:
            h3 = _top(x, l2, l4)
            if not l2 < h3 < l4 or _bottom(x, h1, h3) != l2 or _bottom(x, h3, b) != l4:
                continue
            seq = [(a, float(x.bars[a]["l"])), (h1, float(x.bars[h1]["h"])), (l2, float(x.bars[l2]["l"])),
                   (h3, float(x.bars[h3]["h"])), (l4, float(x.bars[l4]["l"])), (b, float(x.bars[b]["h"]))]
            if not _five(seq, True, deg(x).min_leg):
                continue
            imp = {"kind": "five", "legs": 5, "seq": seq, "k": SEARCH_K, "volume_on_pushes": _volume_on_pushes(x, seq)}
            q = quality(imp)
            if best is None or q > best[0]:
                best = (q, imp)
    return best[1] if best else None


def _pullback_seq(x, a, up=True):
    """the swings of the pullback from session a to its extreme so far (against `up`) at the coarsest size (2.5 down
    to 1 ATR) that splits it into three legs or more, or None (one straight leg at every size)"""
    if x.n - 1 - a < 2:
        return None
    low_i = min(range(a, x.n), key=lambda i: float(x.bars[i]["l"])) if up else \
        max(range(a, x.n), key=lambda i: float(x.bars[i]["h"]))
    if low_i <= a:
        return None
    for k in SUB_K:
        seq = _seq(x, a, low_i, not up, k)
        if len(seq) - 1 >= 3:
            return seq
    return None


def pullback_shape(x, a, up=True):
    """the pullback read like an advance, at the size that shows its legs (_pullback_seq): "three" (A, B, C: a
    zigzag whose A and C subdivide still reads as three at its own size), "five" (five clean waves against the trend:
    only wave A), "complex" (more), or "one" (one straight leg at every size)"""
    seq = _pullback_seq(x, a, up)
    if seq is None:
        return "one", 1
    n = len(seq) - 1
    if n == 3:
        return "three", 3
    return ("five" if n == 5 and _five(seq, not up, deg(x).min_leg) else "complex"), n


def _start_candidates(x, top_i):
    """lows before the top from which the advance has no lower low on its way: oldest first"""
    lo_from = max(0, top_i - deg(x).lookback)
    pv = pivots.zigzag(x.bars[lo_from:top_i + 1], x.atrs[lo_from:top_i + 1], 1.0)
    cands = [(lo_from + p.i, p.price) for p in pv if p.kind == "L" and lo_from + p.i < top_i]
    out = []
    for i, px in cands:
        if all(float(b["l"]) >= px for b in x.bars[i + 1:top_i + 1]):
            out.append((i, px))
    return out


def wave2(x):
    """the wave-2 setup on the most recent five-wave advance whose top price has not passed since, or None.
    {"kind", "start", "start_i", "top", "top_i", "zone": (lo, hi), "wide", "deep", "dead", "status", "shape",
    "traps", "r_now", "r_min", "sessions": (advance, pullback), "impulse"}"""
    if x.n < 60 or not x.atr:
        return None
    highs = [float(b["h"]) for b in x.bars]
    tops = [p for p in x.minor if p.kind == "H" and p.confirmed and x.n - 1 - p.i <= deg(x).top_within]
    for top in reversed(tops):
        if max(highs[top.i + 1:], default=0.0) > top.price:
            continue                                         # price has passed it: not the top of the advance
        best = None
        for start_i, start in _start_candidates(x, top.i):
            if min(x.c[top.i:]) <= start:
                continue                                     # a close under the start: no wave 1 from it
            if top.i - start_i < deg(x).min_w1 or top.price - start < deg(x).min_atr * x.atr:
                continue                                     # too short or too small to be a wave at this degree
            imp = impulse(x, start_i, top.i, up=True)
            if not imp["volume_on_pushes"]:
                continue                                     # his volume grammar: the pushes carry the volume
            q = quality(imp)
            if q >= MIN_QUALITY and (best is None or q > best[0]):
                best = (q, start_i, start, imp)
        if best:
            q, start_i, start, imp = best
            out = _wave2_read(x, start_i, start, top.i, top.price, imp)
            out["quality"] = q
            return out
    return None


def _wave2_read(x, start_i, start, top_i, top, imp):
    w1 = top - start
    lvl = {k: top - v * w1 for k, v in W2.items()}
    low_since = min(float(b["l"]) for b in x.bars[top_i + 1:]) if top_i + 1 < x.n else top
    r_min, r_now = (top - low_since) / w1, (top - x.close) / w1
    if r_now < W2["lo"]:                         # above the zone it names: the reaction once the low reached it (C-C3)
        status = "reacted" if r_min >= W2["lo"] else "above"
    elif r_now <= W2["hi"]:
        status = "in"
    elif r_now <= W2["deep"]:
        status = "deep"
    else:
        status = "below"
    shape, legs = pullback_shape(x, top_i, up=True)
    adv, pb = top_i - start_i, x.n - 1 - top_i
    traps = []
    if r_min < W2["wide"]:
        traps.append("too shallow")
    if shape == "one":
        traps.append("one leg")
    if shape == "five":
        traps.append("five down")
    if pb < QUICK * adv:
        traps.append("too quick")
    seg = range(top_i + 1, x.n)
    down = sum(x.vol[i] for i in seg if x.c[i] < x.c[i - 1])
    upv = sum(x.vol[i] for i in seg if x.c[i] > x.c[i - 1])
    mean_pb = sum(x.vol[i] for i in seg) / max(1, len(seg))
    mean_adv = sum(x.vol[start_i + 1:top_i + 1]) / max(1, adv)
    if down > upv and mean_pb > mean_adv:
        traps.append("selling volume rising")
    return {"kind": "wave 2", "start": start, "start_i": start_i, "top": top, "top_i": top_i,
            "zone": (lvl["hi"], lvl["lo"]), "wide": lvl["wide"], "deep": lvl["deep"], "dead": start,
            "status": status, "shape": shape, "pullback_legs": legs, "traps": traps, "r_now": r_now,
            "r_min": r_min, "sessions": (adv, pb), "impulse": imp}


def larger(x, s):
    """his A* (the 1-2, 1-2): the smaller wave 1 of a wave-2 setup starts at the low of a larger wave 2, so the setup
    is wave 2 of wave 3 and its end starts wave 3 of 3, the strongest move on a chart. The larger wave 1 is a clean
    five by the same rules, at least as long as the smaller, its top not passed before the smaller wave 1 began; the
    larger wave 2 retraced 0.5 to 1 of it and ended at the smaller wave 1's start. -> {"start", "start_i", "top",
    "top_i", "r", "quality"} or None"""
    st_i, st = s["start_i"], s["start"]
    span = s["top_i"] - st_i
    highs = [float(b["h"]) for b in x.bars]
    tops = {p.i: p for p in x.minor + x.major
            if p.kind == "H" and p.confirmed and p.i < st_i and st_i - p.i <= deg(x).lookback}
    for i in sorted(tops, reverse=True):
        top = tops[i]
        if max(highs[i + 1:st_i + 1], default=0.0) > top.price:
            continue                                         # not the top of what came before the smaller wave 1
        if min(float(b["l"]) for b in x.bars[i:st_i + 1]) < st - 1e-9:
            continue                                         # the larger wave 2 ends where the smaller wave 1 starts
        best = None
        for s_i, s_px in _start_candidates(x, i):
            if i - s_i < max(deg(x).min_w1, span) or s_px >= st or top.price - s_px < deg(x).min_atr * x.atr:
                continue                                     # a larger wave 1 is a wave 1: as long and as big
            r = (top.price - st) / (top.price - s_px)
            if not 0.5 <= r < 1.0:
                continue
            imp = impulse(x, s_i, i, up=True)
            if imp["kind"] != "five" or not imp["volume_on_pushes"]:
                continue
            q = quality(imp)
            if q >= MIN_QUALITY and (best is None or q > best[0]):
                best = (q, s_i, s_px, r)
        if best:
            q, s_i, s_px, r = best
            return {"start": s_px, "start_i": s_i, "top": top.price, "top_i": i, "r": r, "quality": q}
    return None


FIVE_NEAR = 10                           # the fifth wave's high within the last 10 sessions
FIVE_RSI_GAP = 2.0                       # and its RSI at least 2 points under the third's


def five_done(x):
    """his wave-5 exhaustion (the WYFI top): price within an ATR of a high made in the last FIVE_NEAR sessions, the
    advance into it a clean five (quality 0.75 or more, volume on the pushes, MIN_W1 sessions or more), and the
    fifth wave's high made on weaker momentum than the third's (RSI). -> {"start", "start_i", "top", "top_i",
    "rsi3", "rsi5", "quality"} or None"""
    if x.n < deg(x).min_n or not x.atr:
        return None
    top_i = max(range(x.n - FIVE_NEAR, x.n), key=lambda i: float(x.bars[i]["h"]))
    top = float(x.bars[top_i]["h"])
    if x.close < top - x.atr or max(float(b["h"]) for b in x.bars[top_i + 1:] or [x.bars[top_i]]) > top:
        return None
    best = None
    for s_i, s_px in _start_candidates(x, top_i):
        if top_i - s_i < deg(x).min_w1:
            continue
        imp = impulse(x, s_i, top_i, up=True)
        if imp["kind"] != "five" or imp["legs"] != 5 or not imp["volume_on_pushes"]:
            continue
        q = quality(imp)
        if q >= 0.75 and (best is None or q > best[0]):
            best = (q, s_i, s_px, imp)
    if not best:
        return None
    q, s_i, s_px, imp = best
    i3 = imp["seq"][3][0]
    r3, r5 = x.rsi[i3], max((x.rsi[i] for i in range(imp["seq"][4][0], top_i + 1) if x.rsi[i] is not None),
                            default=None)
    if r3 is None or r5 is None or r5 > r3 - FIVE_RSI_GAP:
        return None
    return {"start": s_px, "start_i": s_i, "top": top, "top_i": top_i, "rsi3": r3, "rsi5": r5, "quality": q,
            "w3_i": i3, "seq": imp["seq"]}


def _three_up(seq, min_leg=MIN_LEG):
    """waves 1, 2 and 3 up: three legs of MIN_LEG sessions or more, wave 2 retracing 0.382 to 0.886 of wave 1 and
    holding over its start, wave 3 at least W3_MIN times wave 1 (and so the longest)"""
    if len(seq) != 4 or any(b - a < min_leg for (a, _), (b, _) in zip(seq, seq[1:])):
        return False
    p0, p1, p2, p3 = (q for _, q in seq)
    w1, w2, w3 = p1 - p0, p1 - p2, p3 - p2
    return w1 > 0 and p2 > p0 and 0.382 <= w2 / w1 <= 0.886 and w3 >= W3_MIN * w1


def wave4(x):
    """the wave-4 setup on the most recent advance whose top price has not passed since and that reads as waves 1, 2
    and 3 (at the coarsest swing size that splits it into three legs or more, the pushes carrying the volume), or None.
    {"kind", "start", "start_i", "w1_top", "w2_low", "top", "top_i", "zone", "wide", "dead", "status", "shape", "traps",
    "r_now", "r_min", "sessions", "seq", "ext"}"""
    if x.n < 60 or not x.atr:
        return None
    highs = [float(b["h"]) for b in x.bars]
    tops = [p for p in x.minor if p.kind == "H" and p.confirmed and x.n - 1 - p.i <= deg(x).top_within]
    for top in reversed(tops):
        if max(highs[top.i + 1:], default=0.0) > top.price:
            continue
        best = None
        for s_i, _ in _start_candidates(x, top.i):
            if top.i - s_i < deg(x).min_w1:
                continue
            seq = next((q for q in (_seq(x, s_i, top.i, True, k) for k in SUB_K) if len(q) - 1 >= 3), None)
            if seq is None or not _three_up(seq, deg(x).min_leg) or not _volume_on_pushes(x, seq):
                continue
            ext = (seq[3][1] - seq[2][1]) / (seq[1][1] - seq[0][1])
            if best is None or ext > best[0]:
                best = (ext, seq)
        if best:
            return _wave4_read(x, best[1], best[0])
    return None


def _wave4_read(x, seq, ext):
    (s_i, start), (_, w1_top), (w2_i, w2_low), (top_i, top) = seq
    w3 = top - w2_low
    low_since = min(float(b["l"]) for b in x.bars[top_i + 1:]) if top_i + 1 < x.n else top
    r_min, r_now = (top - low_since) / w3, (top - x.close) / w3
    if min(x.c[top_i:]) <= w1_top:
        status = "below"                                     # a close under the wave-1 high: wave 4 overlapped 1
    elif r_now < W4["lo"]:                       # above the zone it names: the reaction once the low reached it (C-C3)
        status = "reacted" if r_min >= W4["lo"] else "above"
    elif r_now <= W4["hi"]:
        status = "in"
    else:
        status = "deep"
    shape, legs = pullback_shape(x, top_i, up=True)
    adv, pb = top_i - w2_i, x.n - 1 - top_i
    traps = []
    if r_min < W4["wide"]:
        traps.append("shallow for a wave 4")
    if shape == "one":
        traps.append("one leg")
    if shape == "five":
        traps.append("five down")
    if pb < QUICK * adv:
        traps.append("too quick")
    seg = range(top_i + 1, x.n)
    down = sum(x.vol[i] for i in seg if x.c[i] < x.c[i - 1])
    upv = sum(x.vol[i] for i in seg if x.c[i] > x.c[i - 1])
    mean_pb = sum(x.vol[i] for i in seg) / max(1, len(seg))
    mean_adv = sum(x.vol[w2_i + 1:top_i + 1]) / max(1, adv)
    if down > upv and mean_pb > mean_adv:
        traps.append("selling volume rising")
    return {"kind": "wave 4", "start": start, "start_i": s_i, "w1_top": w1_top, "w2_low": w2_low, "top": top,
            "top_i": top_i, "zone": (top - W4["hi"] * w3, top - W4["lo"] * w3), "wide": top - W4["wide"] * w3,
            "dead": w1_top, "status": status, "shape": shape, "pullback_legs": legs, "traps": traps, "r_now": r_now,
            "r_min": r_min, "sessions": (adv, pb), "seq": seq, "ext": ext}


def _longest_is_three(s):
    """a five-count whose wave 3 is its longest leg (the usual extension); False for an extended first or fifth"""
    pr = [q for _, q in s["impulse"]["seq"]]
    if len(pr) != 6:
        return True
    w = [abs(pr[i + 1] - pr[i]) for i in range(5)]
    return w[2] >= max(w[0], w[4])


def _readings(x):
    """the wave-2 and wave-4 setups, once per read. When one top reads both as a completed five and as waves 1 to 3,
    the count with the extended third wins (his "wave 3 is never the shortest", and most often the longest): a
    five whose fifth or first is its longest leg gives way to the wave 4"""
    if getattr(x, "_waves", None) is None:
        s2, s4 = wave2(x), wave4(x)
        if s2 and s4 and s2["top_i"] == s4["top_i"]:
            if _longest_is_three(s2):
                s4 = None
            else:
                s2 = None
        x._waves = (s2, s4)
    return x._waves


# ---- reading a setup into facts and a plan ----------------------------------------------------------------------

AT_ZONE = {"in": "in", "reacted": "up from", "deep": "under"}
TRAP_WORDS = {"too shallow": "it has not reached the 0.5 retracement", "one leg": "it is one straight leg",
              "shallow for a wave 4": "it has not reached the 0.236 retracement of wave 3",
              "two legs": "it has two legs, a third to come", "five down": "it fell in five waves, only wave A",
              "too quick": "it is too quick for the advance before it",
              "selling volume rising": "selling volume is rising"}


def _averages(x):
    """the averages a zone can sit on, by name: the 50 and 200-day and the 50 and 200-week on a daily chart (the weekly
    ones from all the bars the read was given, x.wk_avg); a weekly chart's own 50 and 200 bars are the weekly ones"""
    if getattr(x, "degree", "daily") == "weekly":
        return (("the 50-week average", x.sma50[-1]), ("the 200-week average", x.sma200[-1]))
    w = getattr(x, "wk_avg", None) or {}
    return (("the 50-day average", x.sma50[-1]), ("the 200-day average", x.sma200[-1]),
            ("the 50-week average", w.get(50)), ("the 200-week average", w.get(200)))


def confluence(x, lo, hi):
    """the independent reasons inside the zone [lo, hi] (a quarter ATR either side): [(kind, words)]; the zone's own
    retracement is not counted here. The 50 and 200-day and 50 and 200-week averages, old structure (a tested swing,
    a retested breakout, a 52-week extreme) and another swing's retracement"""
    pad = 0.25 * x.atr
    a, b = lo - pad, hi + pad
    out = []
    for words, v in _averages(x):
        if v and a <= v <= b:
            out.append(("average", words))
    for ar in x.areas:
        if ar.hi >= a and ar.lo <= b:                    # old structure: an anchoring kind, never an average (the
            order = sorted(ar.members, key=lambda m: (-ar.kinds.get(FAMILY[m.family], 0), -m.weight))  # 200-week)
            m = next((m for m in order if FAMILY[m.family] not in ("average", "round")
                      and ar.kinds.get(FAMILY[m.family], 0) >= TESTED), None)
            if m:
                out.append(("structure", m.label))
                break
    for lv in x.levels:
        if lv.family == "fib" and a <= lv.price <= b:
            out.append(("fib", lv.label))
            break
    return out


def _c_equals_a(x, s):
    """wave C equal to wave A, projected from B, when the pullback reads as A, B and C at its own size: the price, or
    None"""
    if s["shape"] != "three":
        return None
    seq = _pullback_seq(x, s["top_i"], up=True)
    if not seq or len(seq) < 3:
        return None
    a_end, b_end = seq[1][1], seq[2][1]
    return b_end - (s["top"] - a_end)


def read2(x):
    """the wave-2 setup with its confluence: the setup dict plus "conf" [(kind, words)], or None"""
    s = getattr(x, "_wave2", "unset")
    if s == "unset":
        s = _readings(x)[0]
        if s:
            lo, hi = s["zone"]
            conf = confluence(x, lo, hi)
            c = _c_equals_a(x, s)
            if c is not None and lo - 0.25 * x.atr <= c <= hi + 0.25 * x.atr:
                conf.insert(0, ("fib", "wave C equal to wave A"))
            s["conf"] = conf
            s["larger"] = larger(x, s)
        x._wave2 = s
    return s


def read4(x):
    """the wave-4 setup with its confluence, or None"""
    s = getattr(x, "_wave4", "unset")
    if s == "unset":
        s = _readings(x)[1]
        if s:
            s["conf"] = confluence(x, *s["zone"])
        x._wave4 = s
    return s


def facts(x):
    return _wave2_facts(x) + _wave4_facts(x) + _five_facts(x)


SUB = ("1", "2", "3", "4", "5")                      # the five waves inside a count's first wave, drawn as its legs


def _kind(x):
    return "weekly_wave" if getattr(x, "degree", "daily") == "weekly" else "wave"


def _legs(x, seq, labels):
    """a count's legs as segments between its own swings (geometry.seg)"""
    from .geometry import seg
    labels = labels if len(labels) == len(seq) - 1 else [f"Leg {k + 1}" for k in range(len(seq) - 1)]
    return [seg(x, a, pa, b, pb, lab, _kind(x)) for (a, pa), (b, pb), lab in zip(seq, seq[1:], labels)]


def _pullback(x, top_i, label):
    """the pullback since a count's top, to its lowest low so far, as one segment; None while there is none"""
    from .geometry import seg
    if top_i + 1 >= x.n:
        return None
    lo = min(range(top_i + 1, x.n), key=lambda i: float(x.bars[i]["l"]))
    return seg(x, top_i, float(x.bars[top_i]["h"]), lo, float(x.bars[lo]["l"]), label, _kind(x)), lo


def _wave2_geometry(x, s):
    """(draw, marks) of a wave-2 count: wave 1's five legs, the pullback since its top, the larger count (A*)"""
    from .geometry import point, seg
    k = _kind(x)
    draw = _legs(x, s["impulse"]["seq"], SUB)
    marks = [point(x, s["start_i"], "Wave 1 start", k), point(x, s["top_i"], "Wave 1 top", k)]
    pb = _pullback(x, s["top_i"], "Wave 2")
    if pb:
        draw.append(pb[0])
        marks.append(point(x, pb[1], "Wave 2 low", k))
    big = s.get("larger")
    if big:
        draw += [seg(x, big["start_i"], big["start"], big["top_i"], big["top"], "Larger wave 1", k),
                 seg(x, big["top_i"], big["top"], s["start_i"], s["start"], "Larger wave 2", k)]
        marks += [point(x, big["start_i"], "Larger wave start", k), point(x, big["top_i"], "Larger wave top", k)]
    return draw, marks


def _wave4_geometry(x, s):
    """(draw, marks) of a wave-4 count: waves 1 to 3 and the pullback since wave 3's top"""
    from .geometry import point
    k = _kind(x)
    (i0, _), (i1, _), (i2, _), (i3, _) = s["seq"]
    draw = _legs(x, s["seq"], ("Wave 1", "Wave 2", "Wave 3"))
    marks = [point(x, i0, "Wave 1 start", k), point(x, i1, "Wave 1 top", k), point(x, i2, "Wave 2 low", k),
             point(x, i3, "Wave 3 top", k)]
    pb = _pullback(x, s["top_i"], "Wave 4")
    if pb:
        draw.append(pb[0])
        marks.append(point(x, pb[1], "Wave 4 low", k))
    return draw, marks


def _five_geometry(x, d):
    """(draw, marks) of a finished five: its five legs, its start, the third wave's top and the fifth's"""
    from .geometry import point
    k = _kind(x)
    return (_legs(x, d["seq"], SUB),
            [point(x, d["start_i"], "Wave 1 start", k), point(x, d["w3_i"], "Wave 3 top", k),
             point(x, d["top_i"], "Wave 5 top", k)])


def _wave4_facts(x):
    from .core import Fact, pct
    s = read4(x) if x.n >= deg(x).min_n else None
    if not s:
        return []
    when, p = x.when, lambda v: pct(x.pct_of(v))
    lo, hi = s["zone"]
    adv = pct((s["top"] / s["start"] - 1) * 100.0, 0)
    traps = [t for t in s["traps"] if t in TRAP_WORDS]
    draw, marks = _wave4_geometry(x, s)
    if len(traps) >= 2 and s["status"] in ("above", "in", "reacted", "deep"):
        n = len(traps)
        return [Fact("wave.trap", "Elliott wave", "context", -1, min(0.7, 0.3 + 0.1 * n), "A pullback that is not done",
                     f"The pullback from the {when(s['top_i'])} high is not done: "
                     f"{join([TRAP_WORDS[t] for t in traps])}. A wave 4 usually unfolds in three waves and reaches the "
                     f"0.382–0.5 of wave 3 ({p(hi)} to {p(lo)}).",
                     f"Elliott wave: pullback not done ({n} warning signs)", "wave_trap", 0.6,
                     {"traps": traps, "zone": [lo, hi], "draw": draw, "marks": marks},
                     "the pullback does not look done")]
    if s["status"] in ("in", "reacted", "deep"):
        conf = s.get("conf") or []
        three = s["shape"] == "three"
        lighter = "selling volume rising" not in s["traps"]
        strength = 0.45 + 0.1 * min(2, len(conf)) + (0.1 if three else 0.0) - (0.15 if s["status"] == "deep" else 0.0)
        where = {"in": "has reached", "reacted": "turned up from", "deep": "is under"}[s["status"]]
        bits = [b for b in (("in three waves" if three else ""), ("on lighter volume" if lighter else ""),
                            (f"with {' and '.join(w for _, w in conf[:2])} in the same place" if conf else "")) if b]
        head = {"in": "Wave 4 in its buy zone", "reacted": "Wave 4 turning up from its zone",
                "deep": "A deep wave 4"}[s["status"]]
        return [Fact("wave.setup4", "Elliott wave", "structure", 1, round(min(0.85, strength), 2), head,
                     f"Waves 1 to 3 up from {when(s['start_i'])} to {when(s['top_i'])} ({adv}; wave 3 is "
                     f"{s['ext']:.1f} times wave 1). The pullback {where} the 0.382–0.5 zone of wave 3 ({p(hi)} to "
                     f"{p(lo)})" + (", " + ", ".join(bits) if bits else "") + ". The count is wrong on a close "
                     f"under the wave-1 high ({p(s['w1_top'])}): wave 4 never overlaps wave 1.",
                     f"Elliott wave: wave 4 {AT_ZONE[s['status']]} the zone ({len(conf) + 1} confluences)", "wave4",
                     0.7,
                     {"zone": [lo, hi], "status": s["status"], "conf": len(conf) + 1, "draw": draw, "marks": marks},
                     {"in": "it is in its wave-4 buy zone", "reacted": "it is turning up from its wave-4 zone",
                      "deep": "it is in a deep wave 4"}[s["status"]])]
    if s["status"] == "above":
        return [Fact("wave.zone4", "Elliott wave", "context", 0, 0.0, "Wave 4 still above its zone",
                     f"Waves 1 to 3 up from {when(s['start_i'])} to {when(s['top_i'])} ({adv}). A wave-4 pullback "
                     f"usually ends in the 0.382–0.5 zone of wave 3 ({p(hi)} to {p(lo)}), over the wave-1 high.",
                     "Elliott wave: the wave-4 zone is below", "wave4", 0.3,
                     {"zone": [lo, hi], "draw": draw, "marks": marks})]
    return []


def _five_facts(x):
    from .core import Fact, pct
    d = five_done(x) if x.n >= deg(x).min_n else None
    if not d:
        return []
    when, p = x.when, lambda v: pct(x.pct_of(v))
    w = d["top"] - d["start"]
    lo, hi = d["top"] - 0.618 * w, d["top"] - 0.382 * w
    return [Fact("wave.five", "Elliott wave", "structure", -1, 0.5, "Five waves up look complete",
                 f"Five clean waves up from {when(d['start_i'])} to {when(d['top_i'])} "
                 f"({pct((d['top'] / d['start'] - 1) * 100.0, 0)}), and the fifth wave's high came on weaker momentum "
                 f"than the third's (RSI {d['rsi5']:.0f} against {d['rsi3']:.0f} on {when(d['w3_i'])}). A finished "
                 f"five is usually followed by a pullback, often to the 0.382–0.618 of the advance ({p(hi)} to "
                 f"{p(lo)}): the buy is the next wave 2, not this high.",
                 "Elliott wave: a finished five", "wave_five", 0.6,
                 {"zone": [lo, hi], "rsi3": d["rsi3"], "rsi5": d["rsi5"], "top": d["top"],
                  "draw": _five_geometry(x, d)[0], "marks": _five_geometry(x, d)[1]},
                 "five waves up look complete",
                 wrong=(d["top"], "the fifth wave's high") if d["top"] > x.close else None)]


def _wave2_facts(x):
    from .core import Fact, pct
    s = read2(x) if x.n >= deg(x).min_n else None
    if not s:
        return []
    when, p = x.when, lambda v: pct(x.pct_of(v))
    lo, hi = s["zone"]
    adv = pct((s["top"] / s["start"] - 1) * 100.0, 0)
    traps = [t for t in s["traps"] if t in TRAP_WORDS]
    head_of = f"the {when(s['start_i'])}–{when(s['top_i'])} advance"
    draw, marks = _wave2_geometry(x, s)
    # the trap is context: on a pullback still above its zone its signs ("too shallow", "too quick") restate that it
    # is fresh and short of the zone, which the status already says (the audit's C-M3); a deep pullback with the signs
    # is a trap too (C-M1)
    if len(traps) >= 2 and s["status"] in ("above", "in", "reacted", "deep"):
        n = len(traps)
        return [Fact("wave.trap", "Elliott wave", "context", -1, min(0.7, 0.3 + 0.1 * n), "A pullback that is not done",
                     f"The pullback from the {when(s['top_i'])} high is not done: "
                     f"{join([TRAP_WORDS[t] for t in traps])}. A wave 2 usually unfolds in three waves and reaches the "
                     f"0.618–0.786 of {head_of} ({p(hi)} to {p(lo)}).",
                     f"Elliott wave: pullback not done ({n} warning signs)", "wave_trap", 0.6,
                     {"traps": traps, "zone": [lo, hi], "draw": draw, "marks": marks},
                     "the pullback does not look done")]
    if s["status"] in ("in", "reacted", "deep"):
        conf = s.get("conf") or []
        three = s["shape"] == "three"
        lighter = "selling volume rising" not in s["traps"]
        strength = 0.4 + (0.15 if s.get("quality", 0) >= 0.85 else 0.0) + 0.1 * min(2, len(conf)) + \
            (0.1 if three else 0.0) - (0.15 if s["status"] == "deep" else 0.0)
        where = {"in": "has reached", "reacted": "turned up from", "deep": "is under"}[s["status"]]
        bits = [b for b in (("in three waves" if three else ""), ("on lighter volume" if lighter else ""),
                            (f"with {' and '.join(w for _, w in conf[:2])} in the same place" if conf else "")) if b]
        head = {"in": "Wave 2 in its buy zone", "reacted": "Wave 2 turning up from its zone",
                "deep": "A deep wave 2"}[s["status"]]
        big = s.get("larger")
        astar = ""
        if big:
            head, strength = "A* setup: wave 2 of wave 3", strength + 0.1
            astar = (f" It is the second wave of a larger wave 3: five waves up from {when(big['start_i'])} to "
                     f"{when(big['top_i'])} and a pullback of {big['r']:.2f} of them to the {when(s['start_i'])} low "
                     "came first, so the end of this wave 2 starts wave 3 of 3, the strongest move a chart makes.")
        return [Fact("wave.setup", "Elliott wave", "structure", 1, round(min(0.85, strength), 2), head,
                     f"Five clean waves up from {when(s['start_i'])} to {when(s['top_i'])} ({adv}, wave 1). The "
                     f"pullback {where} the 0.618–0.786 zone of that advance ({p(hi)} to {p(lo)})"
                     + (", " + ", ".join(bits) if bits else "") + "." + astar + f" The count is wrong under the start "
                     f"of wave 1 ({p(s['start'])}); a close over the wave-1 high ({p(s['top'])}) says wave 3 is under "
                     "way.",
                     f"Elliott wave: wave 2 {AT_ZONE[s['status']]} the zone ({len(conf) + 1} confluences)",
                     "wave2", 0.7, {"zone": [lo, hi], "status": s["status"], "conf": len(conf) + 1, "draw": draw,
                                    "marks": marks},
                     {"in": "it is in its wave-2 buy zone", "reacted": "it is turning up from its wave-2 zone",
                      "deep": "it is in a deep wave 2"}[s["status"]])]
    if s["status"] == "above":
        return [Fact("wave.zone", "Elliott wave", "context", 0, 0.0, "Wave 2 still above its zone",
                     f"Five clean waves up from {when(s['start_i'])} to {when(s['top_i'])} ({adv}). A wave-2 pullback "
                     f"usually ends in the 0.618–0.786 zone ({p(hi)} to {p(lo)}).",
                     "Elliott wave: the wave-2 zone is below", "wave2", 0.3,
                     {"zone": [lo, hi], "draw": draw, "marks": marks})]
    return []


def plans(x):
    """the wave plans the setups earn: a reaction buy in the wave-2 or wave-4 zone, a pullback to it, or a buy after
    the reaction came; [] when the read says the pullback is not done or the lines do not pay"""
    return _plans2(x) + _plans4(x)


def _plans4(x):
    from . import plan as P
    s = read4(x) if x.n >= deg(x).min_n else None
    if not s or s["status"] == "below" or len([t for t in s["traps"] if t in TRAP_WORDS]) >= 2:
        return []
    atr, c = x.atr, x.close
    lo, hi = s["zone"]
    w3 = s["top"] - s["w2_low"]
    low_since = min(float(b["l"]) for b in x.bars[s["top_i"] + 1:])
    deep = (s["top"] - 0.618 * w3, "the 0.618 retracement of wave 3")       # past it a wave 4 is suspect
    w1 = (s["w1_top"], "the wave-1 high")          # his hard line (the wave-4 fact says it never overlaps)
    deep = [deep] if deep[0] > s["w1_top"] else []
    if s["status"] == "reacted":
        if c - hi > 1.0 * atr:
            return []
        form, mode = "now", "level"
        zlo, cap, w4_end = max(hi - 0.15 * atr, c - 1.0 * atr), c + P.CAP_ATR * atr, low_since
        lines = [(low_since, "the wave-4 low")] + deep + [w1]
    elif s["status"] in ("in", "deep"):
        form, mode = "now", "reaction"
        zlo = (lo if s["status"] == "in" else max(s["w1_top"], c - 1.0 * atr)) - 0.15 * atr
        cap, w4_end = max(c, hi) + 0.35 * atr, min(low_since, c)
        lines = (deep if s["status"] == "in" else []) + [w1]
    else:
        if (c - hi) / atr > P.PULLBACK_ATR:
            return []
        form, mode = "pullback", "reaction"
        zlo, cap, w4_end = lo - 0.15 * atr, hi + 0.15 * atr, (lo + hi) / 2
        lines = deep + [w1]
    span = s["top"] - s["start"]                              # waves 1 to 3
    marks = [(s["top"] - 0.1 * atr, ["the wave-3 high"])]
    aims = [(w4_end + 0.618 * span - 0.1 * atr, ["wave 5's usual reach, 0.618 of waves 1 to 3"]),
            (w4_end + span - 0.1 * atr, ["waves 1 to 3 repeated from wave 4"])]
    why = [f"the 0.382–0.5 retracement of wave 3 ({x.when(s['seq'][2][0])}–{x.when(s['top_i'])})"] + \
        [w for _, w in (s.get("conf") or [])]
    return _build(x, form, mode, zlo, cap, lines, marks, aims, why, "wave4", s["top_i"])


def _plans2(x):
    from . import plan as P
    s = read2(x) if x.n >= deg(x).min_n else None
    if not s or s["status"] == "below" or len([t for t in s["traps"] if t in TRAP_WORDS]) >= 2:
        return []
    atr, c = x.atr, x.close
    lo, hi = s["zone"]
    buf = max(0.25 * atr, 0.003 * c)
    low_since = min(float(b["l"]) for b in x.bars[s["top_i"] + 1:])
    w1 = s["top"] - s["start"]
    deep_line, start = s["deep"], s["start"]
    if s["status"] == "reacted":
        if c - hi > 1.0 * atr:
            return []
        form, mode = "now", "level"
        zlo, cap = max(hi - 0.15 * atr, c - 1.0 * atr), c + P.CAP_ATR * atr
        lines = [(low_since, "the wave-2 low"), (deep_line, "the 0.886 retracement of wave 1"),
                 (start, "the start of wave 1")]
        w2_end = low_since
    elif s["status"] in ("in", "deep"):
        form, mode = "now", "reaction"
        zlo = (deep_line if s["status"] == "deep" else lo) - 0.15 * atr
        cap = max(c, hi) + 0.35 * atr
        lines = ([(deep_line, "the 0.886 retracement of wave 1")] if s["status"] == "in" and not s.get("larger")
                 else []) + [(start, "the start of wave 1")]        # A*: his stop is under the start of the smaller 1
        w2_end = min(low_since, c)
    else:                                                     # above the zone: wait for it
        if (c - hi) / atr > P.PULLBACK_ATR:
            return []
        form, mode = "pullback", "reaction"
        zlo, cap = lo - 0.15 * atr, hi + 0.15 * atr
        lines = [(deep_line, "the 0.886 retracement of wave 1"), (start, "the start of wave 1")]
        w2_end = (lo + hi) / 2
    # wave 3 aims at the 1.618 extension of wave 1 from the end of wave 2 (his trend-based tool); the wave-1 high
    # on the way is where wave 3 is confirmed. His trim is at the first overhead level (_build)
    big = s.get("larger")
    if big:                                                   # A*: wave 3 of 3 aims at the larger wave 3's reach
        reach = (s["start"] + 1.618 * (big["top"] - big["start"]) - 0.1 * atr,
                 ["the 1.618 extension of the larger wave 1, wave 3 of 3's reach"])
    else:
        reach = (w2_end + 1.618 * w1 - 0.1 * atr, ["the 1.618 extension, wave 3's usual reach"])
    marks = [(s["top"] - 0.1 * atr, ["the wave-1 high"])]
    why = [f"the 0.618–0.786 retracement of the {x.when(s['start_i'])}–{x.when(s['top_i'])} advance"] + \
        [w for _, w in (s.get("conf") or [])]
    return _build(x, form, mode, zlo, cap, lines, marks, [reach], why, "wave2", s["top_i"])


TRIM = 0.2                               # his management: the first overhead level takes 10-20% off, never the
                                         # whole ("I would of only trimmed 10-20%"); the rest rides to the second
                                         # target (Author archive study of his trades, 2026-08-16)


def _build(x, form, mode, zlo, cap0, lines, marks, aims, why, source, top_i):
    """the first out line, nearest first, that leaves a plan: a line under every close the pullback made since the top
    (top_i), risk at most 3 ATR (the cap pulled down to fit, so only the lower part of the zone is bought; a cap pulled
    under the close makes the buy a pullback), reward to the first target 1R or more, an honest stop
    (plan.pays_its_risk).
    The first target is his trim: the first overhead level 1R or more up (an area of the desk's levels, or a mark of
    the count: the wave-1 or wave-3 high), in reach of the hold, its odds before the out at least plan.ODDS_MIN; the
    rest rides to the wave's aim (marks and aims:
    [(price, words)]). With an aim past the first target the plan takes a fifth off there and holds the rest (TRIM)"""
    from . import plan as P
    atr, buf = x.atr, max(0.25 * x.atr, 0.003 * x.close)
    traded = float(x.bars[-1]["h"])
    low_close = min(x.c[top_i + 1:]) if top_i + 1 < x.n else x.close
    overhead = [(a.lo - 0.1 * atr, a.labels(3)) for a in x.areas if a.weight >= 1.0]
    for line, words in lines:
        if line > low_close:
            continue                                     # the pullback closed under it: already broken (C-C2)
        out, cap = line - buf, cap0
        if out <= 0 or out >= zlo:
            continue
        risk = cap - out
        if risk > P.MAX_RISK_ATR * atr:
            cap = out + P.MAX_RISK_ATR * atr
            if cap <= zlo:
                continue
            risk = cap - out
        f = form
        if f == "now" and cap < x.close:                 # the buy now sits under the close: a pullback to it (C-C1)
            if (x.close - cap) / atr > P.PULLBACK_ATR:
                continue
            f = "pullback"
        ts = sorted((t for t in overhead + marks + aims if t[0] >= cap + P.MIN_R * risk and t[0] > traded),
                    key=lambda t: t[0])                  # none the read's own session already traded (bs1 item 4)
        if not ts:
            continue
        t1, w_1 = ts[0]
        n = P.horizon(x, cap, t1, out)
        if not P.pays_its_risk(x, cap, t1, out):
            continue
        if not P.in_reach(x, cap, t1, out):
            return []                                    # the first target needs longer than the hold (C-C4)
        later = sorted(((q, w) for q, w in aims if q >= t1 + max(0.5 * risk, atr)), key=lambda t: t[0])
        t2, w_2 = later[0] if later else (None, [])
        pl = P.Plan(f, zlo, cap, out, t1, t2, None, n, P.WINDOW[f], why, words, w_1, w_2, source,
                    P.p_reach(x, cap, P.WINDOW[f]) if f == "pullback" else 1.0)
        pl.mode, pl.trim = mode, (TRIM if t2 is not None else None)
        return [pl] if pl.r >= P.MIN_R and pl.out < pl.zone_lo < pl.zone_hi < pl.t1 else []
    return []


BEAR_PATTERNS = ("pattern.breakdown", "pattern.triangle", "pattern.flag")


def reframe(x, fs):
    """inside a clean wave-2 pullback (a five-wave wave 1 at quality 0.75 or more, the pullback in three waves
    and inside its zone, fewer than two trap signs) a bearish pattern whose level lies within the pullback is the
    correction's own C wave, which usually runs past the end of A: it stays in the read as context, not against.
    Below the 0.886, or with the trap signs, nothing changes"""
    s = read2(x) if x.n >= deg(x).min_n else None
    if not s or s["status"] not in ("in", "reacted") or s["shape"] != "three" or \
            s.get("quality", 0) < 0.75 or len([t for t in s["traps"] if t in TRAP_WORDS]) >= 2:
        return fs
    for f in fs:
        level = (f.data or {}).get("trigger")
        if f.key in BEAR_PATTERNS and f.side < 0 and level is not None and s["deep"] <= level <= s["top"]:
            f.side, f.strength = 0, 0.0
            f.text = f.text.rstrip(".") + ": inside this wave-2 pullback it reads as wave C, which usually runs past " \
                                         "the end of wave A."
            f.clause = ""
    return fs
