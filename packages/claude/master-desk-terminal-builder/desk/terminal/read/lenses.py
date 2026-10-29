"""The eight lenses and Conviction 8 on the board's cards and watching rows (ldr1, LDR-1's phase 4; the design is
LEADR_DESIGN.md and the test RESULTS_LDR.md, both 2026-10-26).

After Leadr's workflow every name moves through four stages, Qualify, Conviction, Trigger and Validate, and its
conviction is read through eight lenses of the desk's own evidence: Strength, Shape, Volume, Trend, Levels, Group,
Supply and Market. A lens is green (confirmed: its inputs average 0.6 or more), neutral, red (one of the two red flags
the pre-registered test kept: a wide-range up day in small, micro and nano, and a wide low-of-day stop, the session's
top tenth of ChartsLector's stop distance in the name's tier) or short of data, never guessed. Beside them Conviction
8 recreates Leadr's documented 8-category score as its own indicator, credited "after Leadr's 8-category design": the
category and leaf weights of the dossier (the owner's direction of 2026-10-26, for this personal desk), our own
formula for each leaf, missing where the desk has no input; a category below 60% of its leaf weight with data is
insufficient, it is confirmed when half or more of its leaves with data score 60 or more, the score is the weighted
mean of the sufficient categories, and a name qualifies on Leadr's public filters and 5 of 8 confirmed. The weights
stay in this file: the page gets the score, its check and each category's score, never a weight.

Both are context. No take, plan or board place moves on them: LDR-1 found no order that beats the board's.

  inputs(x, fs, bars, plan)   at read time (compose._read), the record's `lens`: one name's measures from its read's
                              facts and bars. What ranks a measure against the session's other reads, and the market,
                              wait for the edition
  Board(records, ...)         at edition time: the session's reads by tier, the weather, the engine's screen and the
                              desk's bars; Board.block(...) is one card's or watching row's public `lens`:
      stage, word, tone       the stage it reached (Qualify, Conviction, Trigger, Validate), its state in words and
                              its tone (up, warn, down, neutral)
      states, n, red          the eight lenses in order (C confirmed, N neutral, R red flag, I no data), how many are
                              confirmed, and the red flags that fired, by name
      c8, ok, cats, c8st      Conviction 8 (0-100), its check, each category's score (null short of data) and state
                              (C confirmed, N not, I insufficient)
Percentiles are shares within the session and tier over the session's reads (the average rank over the count, as the
test took them), on MIN_XS reads or more. Nothing here reads the network, a file or the clock."""
import math
from bisect import bisect_left, bisect_right

from ... import calendar as cal
from . import clx, indicators
from .ta import session_of

V = 1                                # the record's `lens` layout: an edition skips a record of another
LENSES = ("Strength", "Shape", "Volume", "Trend", "Levels", "Group", "Supply", "Market")
CONFIRM = 0.6                        # a lens with data is confirmed at this mean of its inputs
READY = 5                            # Conviction's "Ready": this many confirmed and no red flag
S3 = ("small", "micro", "nano")
MIN_XS = 20                          # a share of the session needs this many of its reads in the tier
WIDE_UP, WIDE_LOD = "Wide-range up day", "Wide low-of-day stop"      # the two red flags LDR-1 kept (R5)
LOD_CUT = 0.9                        # the stop distance's top tenth in the session and tier
EXT = ("rs63", "rsq", "rss", "resil", "rs21", "rng", "top3", "sprd", "lod")         # measures ranked at edition time
BREADTH_DAYS = 160                   # the sessions of advancers and decliners the McClellan oscillator runs over
PUBLIC = {"stage", "word", "tone", "states", "n", "red", "c8", "ok", "cats", "c8st"}   # setups[] / watching[] lens

# Conviction 8: the documented categories, their weights and their leaves' (each category's leaves sum to 100)
C8 = (
    ("relative_strength", 15, (("rsMarket", 20), ("rsGrowth", 10), ("rsSector", 15), ("peerRank", 15), ("rsLine", 15),
                               ("downsideResilience", 15), ("longMomentum", 10))),
    ("price_action", 18, (("trendStructure", 20), ("baseQuality", 20), ("volContraction", 15),
                          ("pullbackQuality", 15), ("technicalRespect", 10), ("stageDevelopment", 10),
                          ("extension", 10))),
    ("volume_participation", 15, (("relVolume", 20), ("dollarVolTrend", 10), ("accDist", 20),
                                  ("volPriceAgreement", 20), ("pullbackVolume", 15), ("participationBreadth", 10),
                                  ("expansionReadiness", 5))),
    ("trend_alignment", 12, (("emaPosition", 15), ("emaSlope", 15), ("dailyWeeklyAgreement", 25),
                             ("stageAlignment", 15), ("htfLevelPosition", 15), ("weeklyAccExhaustion", 15))),
    ("support_resistance", 12, (("supportProximity", 20), ("roomToResistance", 20), ("levelSignificance", 20),
                                ("srConversion", 15), ("tradeGeometry", 20), ("chasePenalty", 5))),
    ("sector_leadership", 10, (("sectorStrength", 15), ("industryStrength", 15), ("capitalRotation", 20),
                               ("stockLeadership", 20), ("peerConfirmation", 10), ("themeSympathy", 15),
                               ("crowding", 5))),
    ("institutional_positioning", 8, (("instOwnership", 15), ("instActivity", 10), ("insiderActivity", 10),
                                      ("optionsPositioning", 25), ("dealerPositioning", 15), ("darkPool", 15),
                                      ("shortPositioning", 10))),
    ("market_context", 10, (("marketRegime", 20), ("marketBreadth", 20), ("indexAccDist", 15),
                            ("breakoutFollowThrough", 15), ("riskAppetite", 10), ("sectorRotation", 10),
                            ("macroEventRisk", 5), ("indexConfirmation", 5))),
)
LEAVES = tuple(k for _, _, leaves in C8 for k, _ in leaves)
COVERAGE_FLOOR, LEAF_PASS, QUALIFY_MIN = 60.0, 60.0, 5
QUAD = {"Leading": 1.0, "Improving": 2 / 3, "Weakening": 1 / 3, "Lagging": 0.0}   # ChartsLector's rotation quadrants
OFFENCE, DEFENCE = ("XLK", "XLY", "XLC", "SMH", "XLF", "XLI"), ("XLU", "XLP", "XLV", "XLRE")
SECTOR_NAME = {"XLE": "Energy", "XLF": "Financials", "XLV": "Health care", "XLI": "Industrials", "XLB": "Materials",
               "XLP": "Staples", "XLU": "Utilities", "XLY": "Discretionary", "XLK": "Tech", "XLC": "Communication",
               "XLRE": "Real estate", "SMH": "Semis"}                  # market.SECTORS: the edition's sector list


# ---------------------------------------------------------------------------------------------------- small helpers
def _ok(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _num(v):
    """a number, a true or false as 1 or 0, or None"""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    return float(v) if _ok(v) else None


def _clip(v, lo=0.0, hi=1.0):
    return None if v is None else min(hi, max(lo, v))


def _r(v, k=4):
    return None if v is None else round(v, k)


def _mean(xs, need=2):
    """the mean of the inputs present when at least `need` are, else None"""
    got = [v for v in xs if v is not None]
    return sum(got) / len(got) if len(got) >= need else None


def share(sorted_vals, v):
    """v's share of the sorted values: its average rank over the count, (0, 1] (pandas rank(pct=True))"""
    lo, hi = bisect_left(sorted_vals, v), bisect_right(sorted_vals, v)
    return (lo + (hi - lo + 1) / 2.0) / len(sorted_vals)


def quantile(sorted_vals, q):
    """numpy's linear quantile of sorted values"""
    p = q * (len(sorted_vals) - 1)
    i = math.floor(p)
    j = min(i + 1, len(sorted_vals) - 1)
    return sorted_vals[i] + (sorted_vals[j] - sorted_vals[i]) * (p - i)


def _median(xs):
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


def _facts(fs):
    """({key: (side, strength)}, {key: data}): the strongest fact of each key (the later of a tie) and each key's
    data fields, the later fact's where two hold one (the test's read_wide)"""
    best, data = {}, {}
    for f in fs:
        v = abs(f.side * f.strength)
        if f.key not in best or v >= best[f.key][2]:
            best[f.key] = (f.side, f.strength, v)
        if f.data:
            data.setdefault(f.key, {}).update(f.data)
    return best, data


# ---------------------------------------------------------------------------------------------------- read time
def _aligned(bars, other):
    """the other series' closes on each of these bars' sessions (None where it has none)"""
    by = {session_of(b): float(b["c"]) for b in other or () if b.get("c") is not None}
    return [by.get(session_of(b)) for b in bars]


def _ema(xs, span):
    """pandas ewm(span, adjust=False, min_periods=span): seeded on the first value, None for the first span - 1"""
    a, out, prev = 2.0 / (span + 1.0), [], None
    for t, v in enumerate(xs):
        prev = v if prev is None else a * v + (1.0 - a) * prev
        out.append(prev if t + 1 >= span else None)
    return out


def measures(bars, spy=None):
    """the bar measures of LDR-1's table at the last bar (ldr_build.row_features): every window inside these bars,
    the split-adjusted daily bars the read was given (its volume in today's shares)"""
    o_ = {}
    n = len(bars)
    if n < 2:
        return o_
    h, l, c = ([float(b[k]) for b in bars] for k in ("h", "l", "c"))
    v = [float(b.get("v") or 0.0) for b in bars]
    i = n - 1
    tr = [h[0] - l[0]] + [max(h[t] - l[t], abs(h[t] - c[t - 1]), abs(l[t] - c[t - 1])) for t in range(1, n)]
    atr14 = sum(tr[i - 13:i + 1]) / 14.0 if i >= 13 else None          # the simple mean of 14 true ranges
    if spy:
        sp = _aligned(bars, spy)
        if i >= 60 and all(x and x > 0 for x in sp[max(0, i - 251):i + 1]):
            m = max(c[t] / sp[t] for t in range(max(0, i - 251), i + 1))
            o_["rsl"] = (c[i] / sp[i]) / m - 1.0 if m > 0 else None          # the RS line against its 52-week high
        if i >= 63:
            s, k = 0.0, 0
            for t in range(i - 62, i + 1):
                if sp[t - 1] and sp[t] and sp[t - 1] > 0 and sp[t] > 0 and sp[t] / sp[t - 1] - 1.0 < 0:
                    s += (c[t] / c[t - 1] - 1.0) - (sp[t] / sp[t - 1] - 1.0)
                    k += 1
            if k >= 10:
                o_["resil"] = s / k                                         # beating SPY on its down days
    if atr14 and atr14 > 0:
        if i >= 9:
            o_["rng"] = (max(h[i - 9:i + 1]) - min(l[i - 9:i + 1])) / atr14
        o_["lod_atr"] = (c[i] - l[i]) / atr14
        if i >= 19:
            o_["pb"] = (max(c[i - 19:i + 1]) - c[i]) / atr14
        o_["atr14_pct"] = atr14 / c[i]
    for k, w in (("v50", 50), ("v5", 5), ("v20", 20), ("v250", 250)):
        if i >= w - 1:
            o_[k] = sum(v[i - w + 1:i + 1]) / w
    for k, w in (("top3", 60), ("top3_20", 20)):
        if i >= w - 1 and sum(v[i - w + 1:i + 1]) > 0:
            o_[k] = sum(sorted(v[i - w + 1:i + 1])[-3:]) / sum(v[i - w + 1:i + 1])
    if i >= 59:
        dv = [c[t] * v[t] for t in range(i - 59, i + 1)]
        m60 = _median(dv)
        if m60 > 0:
            o_["dv_trend"] = _median(dv[-20:]) / m60
    if i >= 49:
        o_["adv_sh"] = sum(v[i - 49:i + 1]) / 50.0
    for span in (10, 20, 50, 200):
        e = _ema(c, span)
        o_[f"e{span}"] = c[i] / e[i] - 1.0 if e[i] else None
        back = {50: 10, 200: 20}.get(span)
        if back and i - back >= 0 and e[i] is not None and e[i - back] is not None:
            o_[f"e{span}_up"] = 1.0 if e[i] > e[i - back] else 0.0
    if i >= 25:                                                          # a 20-session closing high five sessions back
        k = i - 5
        if c[k] >= max(c[k - 19:k]):
            o_["ft"] = 1 if c[i] >= c[k] else 0
    o_["age"] = i                                                        # sessions before this one
    return o_


def lod_stop(bars):
    """ChartsLector's P1 at the last session, the cautions' own measure (read/clx.py): his stop under the session's
    low in % of the close, on the read's window"""
    h, l, c = ([float(b[k]) for b in bars] for k in ("h", "l", "c"))
    return clx.lod_stop(h, l, c, clx.ema_r(clx.true_range(h, l, c), 14, 1.0 / 14.0)) if len(c) >= 2 else None


def tier_of(close, bars):
    """the analysis engine's tier on these bars, its reference scorer's rule restated (the read never loads the
    engine): liquid at a close of 5 or more and a 20-session median dollar volume of 20 million or more, else small at
    5 million, micro at 1 million, nano at 0.1 million; the median is the mean of the two middle values, and a
    split-adjusted close times its volume is the dollar volume traded"""
    if len(bars) < 20:
        return None
    dv = sorted(float(b["c"]) * float(b.get("v") or 0.0) for b in bars[-20:])
    dv = (dv[9] + dv[10]) / 2.0
    return ("liquid" if close >= 5 and dv >= 20e6 else "small" if dv >= 5e6 else "micro" if dv >= 1e6 else
            "nano" if dv >= 1e5 else None)


_STACK = {(1, 0.8): 1.0, (1, 0.45): 0.85, (1, 0.3): 0.65, (-1, 0.3): 0.35, (-1, 0.45): 0.15, (-1, 0.8): 0.0}


def _stack(side, strength):
    """trend.stack's seven readings as 0..1 (read/trend.py: 0.8 every average, 0.45 a pullback or bounce, 0.3 back
    above or below)"""
    if side == 0:
        return 0.5
    return next((v for (sd, st), v in _STACK.items() if side == sd and abs(round(strength, 2) - st) < 0.02), None)


def _sel(conds, default=None):
    """the value of the first true condition, else default (numpy's select)"""
    return next((v for ok, v in conds if ok), default)


def _lt(a, b):
    return a is not None and b is not None and a < b


def _le(a, b):
    return a is not None and b is not None and a <= b


def _ge(a, b):
    return a is not None and b is not None and a >= b


def _gt(a, b):
    return a is not None and b is not None and a > b


def inputs(x, fs, bars, plan=None):
    """the record's `lens` (the module docstring), or None when it cannot be measured: {"v", "t" the tier, "x" the
    measures the edition ranks, "a" the lenses' own inputs (0-1), "c" Conviction 8's leaves measured here (0-100,
    None for the edition's and the missing), "q" Leadr's filters but the tier, "w" a wide-range up candle,
    "f" the sector fund, "ft" a breakout five sessions back holding (1) or not (0)}"""
    try:
        return _inputs(x, fs, bars, plan)
    except (ArithmeticError, KeyError, TypeError, ValueError, IndexError):   # a lens costs nothing but itself
        return None


def _inputs(x, fs, bars, plan):
    best, data = _facts(fs)
    side = lambda k: best[k][0] if k in best else None              # noqa: E731
    stren = lambda k: best[k][1] if k in best else None             # noqa: E731
    dat = lambda k, f: _num((data.get(k) or {}).get(f))             # noqa: E731
    ex = x.extra or {}
    m = measures(bars, ex.get("spy") or (x.index_bars if x.index_sym == "SPY" else None))
    close, a = x.close, x.atr
    rsq = indicators.rs(x, ex.get("qqq")).get(63) if ex.get("qqq") else None
    sec = ex.get("sector") or {}
    raw = {"rs63": dat("trend.vs_spy", "rs63"), "rsq": rsq, "rss": dat("trend.vs_sector", "rs63"),
           "resil": m.get("resil"), "rs21": dat("trend.vs_spy", "rs21"), "rng": m.get("rng"), "top3": m.get("top3"),
           "sprd": dat("ctx.spread", "spread_pct"), "lod": lod_stop(x.bars)}
    # the lenses' own inputs (LDR-1's ldr_lens.lenses): each 0..1, None without its reading
    pbm, pbw, all_up = (dat("trend.htf", k) for k in ("pbm", "pbw", "all_up"))
    m_dn, w_dn = dat("trend.htf", "m_dn"), dat("trend.htf", "w_dn")
    pull = None if pbm is None else (1.0 if pbm == 1 or pbw == 1 else 0.6 if all_up == 1 else
                                     0.0 if m_dn == 1 and w_dn == 1 else 0.4)
    rank = dat("vola.atr", "rank")
    acc = side("vol.accdist")
    ls, lst = side("vol.leg"), stren("vol.leg")
    leg = None if ls is None else (1.0 if ls == 1 and abs(round(lst, 2) - 0.45) < 0.02 else
                                   0.0 if ls == -1 and abs(round(lst, 2) - 0.45) < 0.02 else 0.5)
    stk_side = side("trend.stack")
    parts = (data.get("trend.cl") or {}).get("parts") or {}
    st = dat("trend.stage", "stage")
    on = side("levels.on") == 1
    fl_hi, fl_conf = dat("levels.floor", "hi"), dat("levels.floor", "confluence")
    dist = (close - fl_hi) / a if fl_hi is not None and a else None
    conf = dat("levels.on", "confluence") if on else (fl_conf if _le(dist, 1.0) else 0.0)
    r = getattr(plan, "r", None) if plan is not None and getattr(plan, "form", "wait") != "wait" else None
    d50 = dat("vola.stretch", "d50_atr")
    fund = None
    sb = [float(b["c"]) for b in sec.get("bars") or () if b.get("c") is not None]
    if len(sb) >= 200:                                                   # the sector fund over its averages
        m50, m200 = sum(sb[-50:]) / 50, sum(sb[-200:]) / 200
        fund = 1.0 if sb[-1] > m50 and sb[-1] > m200 else 0.0 if sb[-1] < m200 else 0.5
    own = {"pull": pull, "calm": None if rank is None else 1.0 - rank,
           "dist": None if acc is None else (1.0 if acc == -1 else 0.5),
           "leg": leg, "stk": None if stk_side is None else _stack(stk_side, stren("trend.stack")),
           "s50": _num(parts.get("s50s150")),
           "stg": {2: 1.0, 1: 0.5, 3: 0.25, 4: 0.0}.get(st),
           "sup": 1.0 if _ge(conf, 3) else 0.75 if _ge(conf, 2) else 0.5 if _ge(conf, 1) else 0.25,
           "rr": None if r is None else _clip((r - 1.0) / 2.0),
           "ext": None if d50 is None else (0.5 if d50 < 0 else _clip(1.0 - (d50 - 1.0) / 4.0)),
           "age": _clip((m["age"] - 250.0) / 500.0) if "age" in m else None, "fund": fund}
    leaves = _leaves(x, best, data, m, side, dat, close, a, st, stk_side, on, r, d50)
    q = (_gt(m.get("adv_sh"), 500_000) and _ge(m.get("atr14_pct"), 0.02) and _ge(m.get("e50"), -0.03)
         and _ge(m.get("e200"), -0.03) and (st is None or st in (1, 2)))
    out = {"v": V, "t": tier_of(close, bars), "x": {k: _r(v, 6) for k, v in raw.items() if v is not None},
           "a": {k: _r(v) for k, v in own.items() if v is not None}, "c": [_r(leaves.get(k), 2) for k in LEAVES],
           "q": bool(q)}
    if side("candle.wide") == 1:
        out["w"] = 1
    if sec.get("sym"):
        out["f"] = sec["sym"]
    if m.get("ft") is not None:
        out["ft"] = m["ft"]
    return out


def _leaves(x, best, data, m, side, dat, close, a, st, stk_side, on, r, d50):
    """Conviction 8's leaves this read measures (LDR-1's ldr_lens.c8_leaves; LEADR_DESIGN.md Part B lists each)"""
    L = {"rsLine": None if m.get("rsl") is None else 100 * _clip(1.0 + m["rsl"] / 0.20)}
    sw, lvl = side("trend.swings"), dat("trend.swings", "level")
    L["trendStructure"] = _sel([(sw == 1 and lvl is None, 100.0), (sw == 1, 70.0), (sw == 0, 50.0),
                                (sw == -1 and lvl is not None, 20.0), (sw == -1, 0.0)])
    trig, flo = dat("pattern.base", "trigger"), dat("pattern.base", "floor")
    if trig is not None and trig > 0:
        L["baseQuality"] = None if flo is None else min(
            100.0, _clip(100.0 - 4.0 * (trig - flo) / trig * 100.0, 0, 100) +
            20.0 * (dat("pattern.base", "near_top") == 1))
    else:
        L["baseQuality"] = 0.0
    sq = dat("vola.squeeze", "rank")
    L["volContraction"] = None if sq is None else 100 * (1.0 - sq)
    pb = m.get("pb")
    pq = _sel([(_ge(pb, 1) and _le(pb, 3), 100.0), (_lt(pb, 1), 60.0), (_gt(pb, 3) and _le(pb, 5), 50.0),
               (_gt(pb, 5), 10.0)])
    L["pullbackQuality"] = pq if stk_side == 1 else (0.0 if stk_side is not None else None)
    resp = sum(1 for k in ("levels.bounce20", "levels.bounce50", "levels.retest", "levels.reclaim20",
                           "levels.reclaim50") if side(k) == 1)
    L["technicalRespect"] = 100.0 if resp >= 2 else 60.0 if resp == 1 else 0.0
    w30 = dat("trend.htf", "w30_dist")
    s2 = 100.0 if _le(w30, 15) else 70.0 if _le(w30, 30) else 40.0
    L["stageDevelopment"] = {2: s2, 1: 40.0, 3: 20.0, 4: 0.0}.get(st)
    L["extension"] = None if d50 is None else (70.0 if d50 < 0 else _clip(100 - 20 * max(0.0, d50 - 1), 0, 100))
    rv = dat("vol.last", "rv")
    L["relVolume"] = None if rv is None else _clip(50 * rv, 0, 100)
    dvt = m.get("dv_trend")
    L["dollarVolTrend"] = None if dvt is None else _clip(100 * (dvt - 0.5), 0, 100)
    acc, dist = dat("vol.accdist", "acc"), dat("vol.accdist", "dist")
    L["accDist"] = None if acc is None else (100 * acc / (acc + dist) if dist is not None and acc + dist > 0 else 50.0)
    ud = dat("vol.updown", "ratio")
    L["volPriceAgreement"] = None if ud is None else _clip(50 * ud, 0, 100)
    v5, v50 = m.get("v5"), m.get("v50")
    r5 = v5 / v50 if v5 is not None and v50 else None
    L["pullbackVolume"] = (None if r5 is None else 100 * _clip(1.5 - r5)) if _ge(pb, 0.5) else None
    t20 = m.get("top3_20")
    L["participationBreadth"] = None if t20 is None else 100 * _clip((0.5 - t20) / 0.35)
    L["expansionReadiness"] = None if r5 is None else 100 * _clip((1.2 - r5) / 0.6)
    e = [m.get(f"e{k}") for k in (10, 20, 50, 200)]
    L["emaPosition"] = None if e[3] is None else 25.0 * sum(1 for v in e if _gt(v, 0))
    u50, u200 = m.get("e50_up"), m.get("e200_up")
    L["emaSlope"] = None if u50 is None or u200 is None else 50 * u50 + 50 * u200
    ups = [dat("trend.htf", k) for k in ("d_up", "w_up", "m_up")]
    L["dailyWeeklyAgreement"] = None if None in ups else 100 * sum(ups) / 3.0
    L["stageAlignment"] = _sel([(st == 2 and stk_side == 1, 100.0), (st == 2, 70.0), (st == 1, 40.0), (st == 3, 20.0),
                                (st == 4, 0.0)])
    oh, ol = dat("trend.range52", "off_hi"), dat("trend.range52", "off_lo")
    if oh is not None and ol is not None and oh > -100 and ol > -100:
        hi, lo = 1.0 / (1.0 + oh / 100.0), 1.0 / (1.0 + ol / 100.0)
        L["htfLevelPosition"] = 100 * _clip((1.0 - lo) / (hi - lo)) if hi - lo > 0 else None
    w10, sig = dat("trend.htf", "w10_dist"), (x.sigma / x.close * 100.0 if x.sigma and x.close else None)
    z = w10 / (sig * math.sqrt(5.0)) if w10 is not None and sig else None
    L["weeklyAccExhaustion"] = None if z is None else (40.0 if z < 0 else _clip(100 - 50 * max(0.0, z - 1), 0, 100))
    fl_hi = dat("levels.floor", "hi")
    dist = (close - fl_hi) / a if fl_hi is not None and a else None
    L["supportProximity"] = 100.0 if on else (0.0 if dist is None else 100.0 if dist <= 1 else
                                              100 - 40 * (dist - 1) if dist <= 3 else 0.0)
    ce = dat("levels.ceiling", "lo")
    up = (ce - close) / a if ce is not None and a else None
    L["roomToResistance"] = 100.0 if up is None else _clip(100 * (up - 0.5) / 3.5, 0, 100)
    conf = dat("levels.on", "confluence") if on else dat("levels.floor", "confluence")
    L["levelSignificance"] = 100.0 if _ge(conf, 3) else 66.0 if _ge(conf, 2) else 33.0 if _ge(conf, 1) else 0.0
    L["srConversion"] = 100.0 if side("levels.retest") == 1 else (
        70.0 if side("levels.reclaim20") == 1 or side("levels.reclaim50") == 1 else 0.0)
    L["tradeGeometry"] = None if r is None else 100 * _clip((r - 1.0) / 2.0)
    la = m.get("lod_atr")
    L["chasePenalty"] = None if la is None else 100 * _clip((1.5 - la) / 0.85)
    n7 = dat("trend.cl", "n")
    L["stockLeadership"] = None if n7 is None else 100 * n7 / 7.0
    v20, v250 = m.get("v20"), m.get("v250")
    L["crowding"] = None if v20 is None or not v250 else 100 * _clip(1.5 - v20 / v250)
    return L


def breadth(acc, bars, days=BREADTH_DAYS):
    """adds one name's advances and declines over its last `days` sessions to acc {session: [advancers, decliners]}
    (LDR-1's universe breadth: a close over the one before advances, under it declines, a change under 1e-6 neither).
    The roster job runs it over every stock it reads"""
    xs = [b for b in bars or () if b.get("c") is not None][-(days + 1):]
    for a, b in zip(xs, xs[1:]):
        p, c = float(a["c"]), float(b["c"])
        if p > 0 and abs(c / p - 1.0) >= 1e-6:
            acc.setdefault(session_of(b).isoformat(), [0, 0])[0 if c > p else 1] += 1


def mcclellan(acc, as_of):
    """the ratio-adjusted McClellan oscillator at as_of over breadth()'s counts (LDR-1's can_mkt A4): RANA = 1000
    (A - D) / (A + D), the EMA of 19 sessions (0.10) less the EMA of 39 (0.05), each seeded on the simple mean of
    its first 19 or 39 values; None without 39 sessions through as_of"""
    days = sorted(d for d in acc if d <= as_of and sum(acc[d]) > 0)
    if len(days) < 39 or days[-1] != as_of:
        return None
    rana = [1000.0 * (acc[d][0] - acc[d][1]) / sum(acc[d]) for d in days]

    def ema(n, a):
        e = sum(rana[:n]) / n
        for v in rana[n:]:
            e += a * (v - e)
        return e
    return round(ema(19, 0.10) - ema(39, 0.05), 3)


ZBT_LOW, ZBT_HIGH, ZBT_WINDOW, ZBT_EMA = 0.40, 0.615, 10, 10


def zbt_fires(emas, window=ZBT_WINDOW, lo=ZBT_LOW, hi=ZBT_HIGH):
    """the indexes at which Zweig's breadth thrust fires over a series of 10-session EMAs of the advancing share: the EMA
    crosses up through `hi` having been under `lo` at some point in the `window` sessions before"""
    out = []
    for t in range(1, len(emas)):
        if emas[t] is None or emas[t - 1] is None or not (emas[t] > hi >= emas[t - 1]):
            continue
        prior = [e for e in emas[max(0, t - window):t] if e is not None]
        if prior and min(prior) < lo:
            out.append(t)
    return out


def zweig_thrust(acc, as_of):
    """Zweig's Breadth Thrust at as_of over breadth()'s counts: the 10-session EMA (seeded on the simple mean of its first
    ten) of advancers / (advancers + decliners), and the latest session at which it climbed from under 0.40 to over
    0.615 within 10 sessions. word: Thrust (fired in the last 10 sessions), Washed out (EMA under 0.40), Recovering (it
    was under 0.40 in the last 10 sessions and is not over 0.615), else Neutral. None without ten sessions through as_of"""
    days = sorted(d for d in acc if d <= as_of and sum(acc[d]) > 0)
    if len(days) < ZBT_EMA or days[-1] != as_of:
        return None
    share = [acc[d][0] / float(sum(acc[d])) for d in days]
    a = 2.0 / (ZBT_EMA + 1)
    e = sum(share[:ZBT_EMA]) / ZBT_EMA
    emas = [None] * (ZBT_EMA - 1) + [e]
    for v in share[ZBT_EMA:]:
        e += a * (v - e)
        emas.append(e)
    fires = zbt_fires(emas)
    last = len(days) - 1
    since = last - fires[-1] if fires else None
    recent = [x for x in emas[-ZBT_WINDOW:] if x is not None]
    if since is not None and since <= ZBT_WINDOW:
        word = "Thrust"
    elif emas[-1] < ZBT_LOW:
        word = "Washed out"
    elif recent and min(recent) < ZBT_LOW and emas[-1] <= ZBT_HIGH:
        word = "Recovering"
    else:
        word = "Neutral"
    return {"status": "ok", "word": word, "ema10": round(emas[-1], 4), "fired": days[fires[-1]] if fires else None,
            "since": since, "n": len(days), "as_of": as_of}


# ---------------------------------------------------------------------------------------------------- edition time
def market_of(spy, qqq=None, iwm=None, as_of=None):
    """the session's weather from the index funds' daily bars through as_of: {"up200", "rising", "ddc", "q50", "i50"}
    (LDR-1's regime and distribution-day columns: SPY over its 200-day and the 200-day over its value 20 sessions
    before; SPY's distribution days, a fall of 0.2% or more on higher volume, active for 25 sessions unless a close 5%
    over it came since; QQQ and IWM over their 50-day)"""
    def cut(bars):
        return [b for b in bars or () if b.get("c") is not None
                and (as_of is None or session_of(b).isoformat() <= as_of)]
    out = {}
    s = cut(spy)
    c = [float(b["c"]) for b in s]
    if len(c) >= 220:
        m0, m20 = sum(c[-200:]) / 200, sum(c[-220:-20]) / 200
        out.update(up200=1.0 if c[-1] > m0 else 0.0, rising=1.0 if m0 > m20 else 0.0)
    if len(c) >= 26:
        v = [float(b.get("v") or 0.0) for b in s]
        t = len(c) - 1
        dd = [k for k in range(t - 24, t + 1) if c[k] / c[k - 1] - 1.0 <= -0.002 and v[k] > v[k - 1]]
        out["ddc"] = sum(1 for k in dd if not any(c[j] >= 1.05 * c[k] for j in range(k + 1, t + 1)))
    for key, bars in (("q50", qqq), ("i50", iwm)):
        xs = [float(b["c"]) for b in cut(bars)]
        if len(xs) >= 50:
            out[key] = 1.0 if xs[-1] > sum(xs[-50:]) / 50 else 0.0
    return out


def _dash_ok(dash, as_of):
    return isinstance(dash, dict) and dash.get("as_of") == as_of


class Board:
    """the edition's view of the session: every read's measures by session and tier, the weather, the engine's screen
    and the desk's bars. records {symbol: record}; engine(symbol) -> its screen row or None; market: the edition's
    market block; dash: market.json (cache/terminal/dash, the last edition's); daily {symbol: daily bars}; mco: the
    roster job's McClellan oscillator, {as_of, value} (reads.json)"""

    def __init__(self, records, engine=None, market=None, dash=None, daily=None, mco=None):
        self.recs = {s: r for s, r in (records or {}).items() if isinstance(r, dict) and r.get("as_of")
                     and isinstance(r.get("lens"), dict) and r["lens"].get("v") == V}
        self.engine = engine or (lambda s: None)
        self.market, self.dash, self.daily, self.mco = market or {}, dash, daily or {}, mco
        self.xs, self.ft, self._mkt = {}, {}, {}
        for r in self.recs.values():
            lx = r["lens"]
            d = self.xs.setdefault((r["as_of"], lx.get("t")), {})
            for k, v in (lx.get("x") or {}).items():
                if _ok(v):
                    d.setdefault(k, []).append(v)
            if lx.get("ft") in (0, 1):
                f = self.ft.setdefault(r["as_of"], [0, 0])
                f[0], f[1] = f[0] + 1, f[1] + lx["ft"]
        for d in self.xs.values():
            for k in d:
                d[k].sort()

    def _share(self, as_of, tier, key, v):
        vals = (self.xs.get((as_of, tier)) or {}).get(key) or []
        return share(vals, v) if v is not None and len(vals) >= MIN_XS else None

    def weather(self, as_of):
        """the session's market inputs, once a session"""
        if as_of not in self._mkt:
            w = market_of(self.daily.get("SPY"), self.daily.get("QQQ"), self.daily.get("IWM"), as_of)
            mk = self.market if self.market.get("as_of") == as_of else {}
            part = next((c for c in mk.get("chips") or () if c.get("id") == "participation"), None)
            if part and _ok(part.get("bar")):
                w["br"] = float(part["bar"])
            f = self.ft.get(as_of)
            if f and f[0] >= MIN_XS:
                w["ft"] = f[1] / f[0]
            if isinstance(self.mco, dict) and self.mco.get("as_of") == as_of and _ok(self.mco.get("value")):
                w["mco"] = float(self.mco["value"])
            if _dash_ok(self.dash, as_of):
                rk = self.dash.get("risk") or {}
                if rk.get("of"):
                    w["risk"] = rk["on"] / rk["of"]
                quads = {f_.get("sym"): QUAD.get(f_.get("quad")) for f_ in (self.dash.get("rotation") or {}).get(
                    "funds") or ()}
                w["quad"] = {k: q for k, q in quads.items() if q is not None}
                off = [quads.get(s) for s in OFFENCE if quads.get(s) is not None]
                dfn = [quads.get(s) for s in DEFENCE if quads.get(s) is not None]
                if off and dfn:                                     # offence leading or improving, against defence
                    w["rot"] = 0.5 * (1 + sum(q >= 0.5 for q in off) / len(off) - sum(q >= 0.5 for q in dfn) / len(dfn))
            if mk.get("sectors"):
                w["sec"] = {s["name"]: s["pts"] for s in mk["sectors"] if _ok(s.get("pts"))}
            if "calendar" in mk:
                w["ev"] = _event_soon(mk.get("calendar"), as_of)
            self._mkt[as_of] = w
        return self._mkt[as_of]

    def read(self, sym):
        """{"states", "n", "red", "ready", "c8", "ok", "cats", "c8st", "tier"} for the name's latest read, or None"""
        rec = self.recs.get(sym)
        if not rec:
            return None
        lx, as_of = rec["lens"], rec["as_of"]
        tier, X, A = lx.get("t"), lx.get("x") or {}, lx.get("a") or {}
        s3 = tier in S3
        pc = lambda k: self._share(as_of, tier, k, X.get(k))           # noqa: E731
        w = self.weather(as_of)
        mom = _num((self.engine(sym) or {}).get("mom6_pct"))           # the engine's momentum share, as tested
        resil, rest, tight, quiet, spread = pc("resil"), pc("rs21"), pc("rng"), pc("top3"), pc("sprd")
        lod_vals = (self.xs.get((as_of, tier)) or {}).get("lod") or []
        lod = X.get("lod")
        red_lod = lod is not None and len(lod_vals) >= MIN_XS and lod >= quantile(lod_vals, LOD_CUT)
        red_wide = s3 and lx.get("w") == 1
        fund = lx.get("f")
        sec_rank = None
        if fund and w.get("sec") and SECTOR_NAME.get(fund) in w["sec"]:
            sec_rank = share(sorted(w["sec"].values()), w["sec"][SECTOR_NAME[fund]])
        quad = (w.get("quad") or {}).get(fund) if fund else None
        reg = None
        if "up200" in w:
            reg = (1.0 if w["rising"] else 0.6) if w["up200"] else (0.4 if w["rising"] else 0.0)
        g = {"Strength": _mean([mom, resil, None if rest is None or not s3 else 1.0 - rest]),
             "Shape": _mean([A.get("pull"), None if tight is None else 1.0 - tight, A.get("calm")]),
             "Volume": _mean([A.get("dist") if s3 else None, A.get("leg"), None if quiet is None else 1.0 - quiet]),
             "Trend": _mean([A.get("stk"), A.get("s50"), A.get("stg")]),
             "Levels": _mean([A.get("sup"), A.get("rr"), A.get("ext")]),
             "Group": _mean([A.get("fund"), sec_rank, quad]),
             "Supply": _mean([A.get("age"), None if spread is None else 1.0 - spread], 2),
             "Market": _mean([reg, w.get("br"), None if w.get("mco") is None else float(w["mco"] >= 0)])}
        reds = {"Shape": [WIDE_UP] if red_wide else [], "Levels": [WIDE_LOD] if red_lod else []}
        states = "".join("R" if reds.get(k) else "I" if g[k] is None else "C" if g[k] >= CONFIRM else "N"
                         for k in LENSES)
        n = states.count("C")
        out = {"states": states, "n": n, "red": [f for k in LENSES for f in reds.get(k, ())], "tier": tier,
               "ready": n >= READY and "R" not in states, "as_of": as_of}
        out.update(self._c8(lx, tier, w, {"rsMarket": pc("rs63"), "rsGrowth": pc("rsq"), "rsSector": pc("rss"),
                                          "downsideResilience": resil, "longMomentum": mom,
                                          "sectorStrength": sec_rank, "capitalRotation": quad, "marketRegime": reg}))
        return out

    def _c8(self, lx, tier, w, got):
        """Conviction 8 (LDR-1's ldr_lens.c8_frame) on the read's leaves and the session's"""
        ddc = w.get("ddc")
        edition = {k: None if v is None else 100.0 * v for k, v in got.items()}
        edition["marketRegime"] = None if got["marketRegime"] is None else {1.0: 100.0, 0.6: 60.0, 0.4: 40.0}.get(
            got["marketRegime"], 0.0)
        edition.update(marketBreadth=None if w.get("br") is None else 100.0 * w["br"],
                       indexAccDist=None if ddc is None else 100.0 if ddc <= 2 else 60.0 if ddc <= 4 else
                       30.0 if ddc <= 5 else 0.0,
                       breakoutFollowThrough=None if w.get("ft") is None else 100.0 * w["ft"],
                       riskAppetite=None if w.get("risk") is None else 100.0 * w["risk"],
                       sectorRotation=None if w.get("rot") is None else 100.0 * w["rot"],
                       macroEventRisk=None if w.get("ev") is None else 0.0 if w["ev"] else 100.0,
                       indexConfirmation=None if w.get("q50") is None or w.get("i50") is None else
                       50.0 * w["q50"] + 50.0 * w["i50"])
        mine = dict(zip(LEAVES, lx.get("c") or ()))
        num = den = 0.0
        cats, st, n8 = [], "", 0
        for _, W, leaves in C8:
            have = [(edition[k] if k in edition else mine.get(k), wt) for k, wt in leaves]
            have = [(v, wt) for v, wt in have if v is not None]
            cov = sum(wt for _, wt in have)
            sc = sum(v * wt for v, wt in have) / cov if cov > 0 else None
            if cov < COVERAGE_FLOOR:
                cats.append(None)
                st += "I"
                continue
            conf = sum(1 for v, _ in have if v >= LEAF_PASS) >= math.ceil(len(have) / 2.0)
            n8 += conf
            st += "C" if conf else "N"
            cats.append(round(sc))
            num, den = num + W * sc, den + W
        ok = bool(lx.get("q")) and tier in ("liquid", "small") and n8 >= QUALIFY_MIN
        return {"c8": round(num / den) if den else None, "ok": ok, "cats": cats, "c8st": st, "n8": n8}

    def block(self, sym, pub, rec, call=None, liquid=None):
        """one card's or watching row's public `lens` (the module docstring), or None without a measured read. pub: the
        read the card or row shows (its plan); rec: the name's latest record; call: the card's call (None on a
        watching row); liquid: whether the name's latest read clears the board's bar"""
        try:
            got = self.read(sym)
            if not got or not pub:
                return None
            stage, word, tone = self.stage(sym, pub, rec, call, got, liquid)
        except Exception:                                   # noqa: BLE001  (a lens never stops the edition)
            return None
        out = {"stage": stage, "word": word, "tone": tone, "states": got["states"], "n": got["n"], "red": got["red"],
               "ok": got["ok"], "cats": got["cats"], "c8st": got["c8st"]}
        if got["c8"] is not None:
            out["c8"] = got["c8"]
        return out

    def stage(self, sym, pub, rec, call, got, liquid=None):
        """(stage, word, tone): the latest of the four stages the name reached (LEADR_DESIGN.md section 2). Validate:
        its call filled (whatever its lenses read today, which the ring shows); else Qualify: the engine's loser veto
        is not in force, no spike, the board's liquidity bar, a buy plan whose take is not Against; Conviction: Ready,
        five lenses or more confirmed and no red flag; Trigger: the plan waits for its buy"""
        from .. import board as boardmod
        if call and call.get("status") == "open" and call.get("filled"):
            return ("Validate",) + self.validate(sym, call, got["tier"], rec)
        if (self.engine(sym) or {}).get("veto_applied"):
            return "Qualify", "Vetoed by the loser screen", "down"
        if boardmod.spiked(rec):
            return "Qualify", "A spike: wait for a pullback", "warn"
        if liquid is False:
            return "Qualify", "Under the board's liquidity bar", "neutral"
        if pub.get("form") not in ("now", "pullback", "breakout") or (pub.get("gut") or {}).get("word") == "Against":
            return "Qualify", "No buy plan", "neutral"
        if not got["ready"]:
            return ("Conviction", "Flagged", "down") if got["red"] else ("Conviction", "Building", "neutral")
        return ("Trigger",) + self.trigger(sym, rec, call)

    def trigger(self, sym, rec, call):
        """(word, tone) of a plan waiting for its buy: in its buy zone, triggered, or how far, in % of the last close
        (the face's own unit: plain.BANNED keeps ATR off it). A card's levels are its call's, scaled to today's bars
        after a split; a watching row's are its latest read's"""
        bars = [b for b in self.daily.get(sym) or () if b.get("c") is not None]
        if call:
            from .. import calls as callbook
            f = callbook.split_factor(dict(call), bars) or 1.0   # a copy: it can set ref_close
            cap, trig = call["zone"][1] * f, None if call.get("trigger") is None else call["trigger"] * f
        elif rec and rec.get("zone"):
            cap, trig = rec["zone"][1], rec.get("trigger")
        else:
            return "Waiting for its buy", "warn"
        last = float(bars[-1]["c"]) if bars else (rec or {}).get("close")
        if not last:
            return "Waiting for its buy", "warn"
        if trig is not None:
            if last > trig:
                return "Triggered: it buys at the next open", "up"
            return f"Watching: {(trig / last - 1) * 100:.1f}% to the trigger", "warn"
        if last <= cap:
            return "In the buy zone", "up"
        up = (last / cap - 1) * 100
        return "Watching: " + (f"{up:.1f}%" if up >= 0.05 else "under 0.1%") + " over the buy zone", "warn"

    def validate(self, sym, call, tier, rec):
        """(word, tone) of a filled call (LEADR_DESIGN.md section 5). On the close that bought (the fill is its next
        open): V2 volume (liquid, at least its 50-day average; small, micro and nano, at most three times it), V3 no
        spike (a gain of at most twice the read's typical daily move) and V5 it beat SPY; while held, V4 no close back
        under the trigger in the three sessions after it. Validated: V2, V3 and V5 held and V4 has not failed;
        Failed: V4 failed; Holding: anything else, and a plan bought in its zone, which has no trigger to check"""
        bars = [b for b in self.daily.get(sym) or () if b.get("c") is not None]
        days = [cal._as_date(float(b["t"])).isoformat() for b in bars]
        if call.get("trigger") is None or call["filled"] not in days:
            return "Holding", "warn"
        t = days.index(call["filled"]) - 1
        if t < 51:
            return "Holding", "warn"
        from .. import calls as callbook
        f = callbook.split_factor(dict(call), bars) or 1.0   # a copy: it can set ref_close
        c = [float(b["c"]) for b in bars]
        v = [float(b.get("v") or 0.0) for b in bars]
        if any(c[k] < call["trigger"] * f for k in range(t + 1, min(t + 4, len(c)))):
            return "Failed: it closed back under the trigger", "down"
        v50 = sum(v[t - 50:t]) / 50.0
        rv = v[t] / v50 if v50 > 0 else None
        ret = c[t] / c[t - 1] - 1.0
        spy = {cal._as_date(float(b["t"])).isoformat(): float(b["c"]) for b in self.daily.get("SPY") or ()
               if b.get("c") is not None}
        sp0, sp1 = spy.get(days[t - 1]), spy.get(days[t])
        sig, px = (rec or {}).get("sigma"), (rec or {}).get("close")
        v2 = rv is not None and (rv >= 1.0 if tier == "liquid" else rv <= 3.0)
        v3 = bool(sig and px) and ret <= 2.0 * sig / px
        v5 = bool(sp0 and sp1) and ret >= sp1 / sp0 - 1.0
        return ("Validated", "up") if v2 and v3 and v5 else ("Holding", "warn")


def _event_soon(calendar, as_of):
    """whether a scheduled release (the market block's calendar) falls within the two sessions after as_of"""
    d = cal.next_trading_day(cal._as_date(as_of))
    last = cal.next_trading_day(d).isoformat()
    return any(str(e.get("at") or "")[:10] <= last for e in calendar or () if e.get("at"))
