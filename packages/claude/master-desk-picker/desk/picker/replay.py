"""Setup definitions and their replay (PICKER.md, families A and B; the coordinator's three candidates).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module and model.py; tools/picker_replay.py writes the report (docs/research/picker-replay.md, .json).
  Constraints  a definition is a pure function of bars 0..i (closed) and the market context of session i; a swing
            point counts only once it is confirmed (PIVOT bars after it, all at or before i); the plan comes from real
            levels only (no fallback: no resistance above, no plan); bought at the next open; the record's exits
            (desk/terminal/odds.simulate: a close at or under the stop line sells at the next open; the target is an
            intraday high; the fill bar checks the stop only; the stop first on a bar that does both; time stop).
            Sleeves are never backtested: only the Best Setups picker learns from history (AGENTS.md).
            Reads no FINRA or SqueezeMetrics data (both allowed by the owner, 2026-10-26/27; not inputs here).
  Outcome   every case of every definition with its plan (ATR distances), outcome, and a point-in-time feature row.
  Proof     tests/test_picker_replay.py (pivots confirmed only after PIVOT bars; plans from levels; no look-ahead).
  Edges     history = the split-adjusted daily cache (most names from 2023); the full 34-module read is too slow to run
            at every bar (0.13 s a call): its facts are added as features on a sample (tools/picker_replay.py --facts).

Definitions (each returns a plan dict or None; the conditions it checked ride along as features):
  A0  uptrend pullback to a rising 21- or 50-day average
  A1  A0 into real swing support: the average within 0.5 ATR of a confirmed swing low or a prior breakout level
  A2  A1 on a fear day: the name and SPY both close red (the owner's fear-day rule, fear.py)
  A3  A1 on a VIX spike: VIX up 10% or more on the day, or above 22
  B0  deep reset: 35-80% under the 1-year high, a bottom in the last 120 sessions and a confirmed higher low after it
  B1  B0 with a reclaim of the 50-day in the last 5 sessions
  B2  B0 with a close over the base line (the highest high between the bottom and the higher low)
  B3  B1 or B2 with up-volume over down-volume (10 sessions) and 20-day strength over SPY improving
  C0  sweep and reclaim: a low under a confirmed swing low in the last 3 sessions and a close back over it"""
import zlib

import numpy as np

from ..terminal import odds as O

PIVOT = 3                      # a swing low / high: the extreme of PIVOT bars on each side, known PIVOT bars later
STOP_PAD = 0.25                # the stop line sits this many ATRs under the level (a close through the level)
MIN_T1_ATR = 0.75              # a target nearer than this to the buy is not a target
TS = 20                        # time stop in sessions for the replay
DEFS = ("A0", "A1", "A2", "A3", "B0", "B1", "B2", "B3", "C0")
FAMILY = {"A0": "A", "A1": "A", "A2": "A", "A3": "A", "B0": "B", "B1": "B", "B2": "B", "B3": "B", "C0": "C"}


# ---------------------------------------------------------------- point-in-time swings
def pivots(a):
    """(lows, highs): lists of (index, price), each confirmed PIVOT bars after it: index + PIVOT is the first bar at
    which the swing is known"""
    l, h, n = a["l"], a["h"], len(a["c"])
    lows, highs = [], []
    for j in range(PIVOT, n - PIVOT):
        w = slice(j - PIVOT, j + PIVOT + 1)
        if l[j] == l[w].min():
            lows.append((j, float(l[j])))
        if h[j] == h[w].max():
            highs.append((j, float(h[j])))
    return lows, highs


def known(swings, i):
    """the swings confirmed by the close of bar i"""
    return [s for s in swings if s[0] + PIVOT <= i]


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    up, dn = np.maximum(d, 0), np.maximum(-d, 0)
    au, ad = np.full(len(c), np.nan), np.full(len(c), np.nan)
    if len(c) > n:
        au[n], ad[n] = up[1:n + 1].mean(), dn[1:n + 1].mean()
        for i in range(n + 1, len(c)):
            au[i] = (au[i - 1] * (n - 1) + up[i]) / n
            ad[i] = (ad[i - 1] * (n - 1) + dn[i]) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 - 100 / (1 + au / ad)


def adx(h, l, c, n=14):
    up = np.diff(h, prepend=h[0])
    dn = -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]

    def w(x):
        out = np.full(len(x), np.nan)
        if len(x) > n:
            out[n] = x[1:n + 1].sum()
            for i in range(n + 1, len(x)):
                out[i] = out[i - 1] - out[i - 1] / n + x[i]
        return out
    atr_, p, m = w(tr), w(pdm), w(ndm)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi, ndi = 100 * p / atr_, 100 * m / atr_
        dx = 100 * abs(pdi - ndi) / (pdi + ndi)
    out = np.full(len(c), np.nan)
    s = np.where(np.isfinite(dx))[0]
    if len(s) > n:
        st = s[0]
        out[st + n - 1] = np.nanmean(dx[st:st + n])
        for i in range(st + n, len(c)):
            out[i] = (out[i - 1] * (n - 1) + dx[i]) / n
    return out


def prepare(bars):
    a = O.indicators(O.arrays(bars))
    a["s50"] = O.sma(a["c"], 50)
    a["rsi"] = rsi(a["c"])
    a["adx"] = adx(a["h"], a["l"], a["c"])
    e12, e26 = O.ema(a["c"], 12), O.ema(a["c"], 26)
    macd = e12 - e26
    a["macdh"] = macd - O.ema(np.nan_to_num(macd), 9)
    a["v50"] = O.sma(a["v"], 50)
    a["atr50"] = O.sma(np.nan_to_num(a["atr"]), 50)
    a["lows"], a["highs"] = pivots(a)
    return a


# ---------------------------------------------------------------- levels and the plan
def resistances(a, i, above):
    """resistance prices over `above` known at i: confirmed swing highs of the last year and the 1-year high"""
    hs = [p for j, p in known(a["highs"], i) if j >= i - 252 and p > above]
    yh = float(a["h"][max(0, i - 251):i + 1].max())
    if yh > above:
        hs.append(yh)
    return sorted(set(round(x, 6) for x in hs))


def plan_from(a, i, support, kind):
    """the plan at the close of bar i from a support price: stop line under it, T1 the nearest resistance at least
    MIN_T1_ATR above the close, T2 the next one (or None). None when no resistance stands above (no fallback)"""
    c, k = float(a["c"][i]), float(a["atr"][i])
    stop = support - STOP_PAD * k
    if stop >= c:
        return None
    rs = [x for x in resistances(a, i, c) if x - c >= MIN_T1_ATR * k]
    if not rs:
        return None
    t1 = rs[0]
    t2 = rs[1] if len(rs) > 1 else None
    return {"support": support, "kind": kind, "stop": stop, "t1": t1, "t2": t2, "rr": (t1 - c) / (c - stop)}


def _uptrend(a, i):
    lows, highs = known(a["lows"], i)[-2:], known(a["highs"], i)[-2:]
    hhhl = len(lows) == 2 and len(highs) == 2 and lows[1][1] > lows[0][1] and highs[1][1] > highs[0][1]
    return (a["c"][i] > a["s200"][i] and a["e50"][i] > a["e50"][i - 10]), hhhl


def family_a(a, i):
    """A0/A1 at bar i -> (plan or None, conditions)"""
    c, k = float(a["c"][i]), float(a["atr"][i])
    up, hhhl = _uptrend(a, i)
    if not up:
        return None, {}
    cands = []
    for name, ma in (("ma21", a["e21"]), ("ma50", a["e50"])):
        if ma[i] > ma[i - 5] and ma[i] <= c and c - ma[i] <= 1.0 * k:
            cands.append((name, float(ma[i])))
    if not cands:
        return None, {}
    off_high = a["h"][i - 20:i + 1].max() - c >= 1.5 * k
    if not off_high:
        return None, {}
    lows = [p for j, p in known(a["lows"], i) if j >= i - 120 and p <= c]
    bo = [p for j, p in known(a["highs"], i) if i - 120 <= j <= i - 10 and p <= c and c - p <= 1.5 * k]
    name, ma = max(cands, key=lambda x: x[1])
    conf = [p for p in lows + bo if abs(p - ma) <= 0.5 * k]
    swing = bool(conf)
    support = max(conf) if swing and max(conf) <= c else ma
    pl = plan_from(a, i, min(support, ma) if swing else ma, name)
    cond = {"hhhl": hhhl, "ma21": name == "ma21", "swing_confluence": swing, "breakout_level": bool(
        [p for p in bo if abs(p - ma) <= 0.5 * k])}
    return pl, cond


def family_b(a, i, spy_c=None):
    """B0..B3 at bar i -> (plan or None, conditions)"""
    c, k = float(a["c"][i]), float(a["atr"][i])
    hi = float(a["h"][max(0, i - 251):i + 1].max())
    dd = 1 - c / hi
    if not 0.35 <= dd <= 0.80:
        return None, {}
    w = slice(max(0, i - 120), i + 1)
    bot_i = max(0, i - 120) + int(np.argmin(a["l"][w]))
    bot = float(a["l"][bot_i])
    hls = [(j, p) for j, p in known(a["lows"], i) if j > bot_i + PIVOT and p >= bot * 1.03]
    if bot_i > i - 10 or not hls:
        return None, {}
    hl_i, hl = hls[-1]
    base = float(a["h"][bot_i:hl_i + 1].max())
    recl50 = any(a["c"][j] > a["s50"][j] and a["c"][j - 1] <= a["s50"][j - 1] for j in range(i - 4, i + 1))
    over_base = c > base and a["c"][i - 1] <= base
    upv = a["v"][i - 9:i + 1][np.diff(a["c"][i - 10:i + 1]) > 0].sum()
    dnv = a["v"][i - 9:i + 1][np.diff(a["c"][i - 10:i + 1]) < 0].sum()
    rs_up = False
    if spy_c is not None and np.isfinite(spy_c[i - 20]) and np.isfinite(spy_c[i - 40]):
        rs_now = c / a["c"][i - 20] - spy_c[i] / spy_c[i - 20]
        rs_then = a["c"][i - 20] / a["c"][i - 40] - spy_c[i - 20] / spy_c[i - 40]
        rs_up = rs_now > rs_then
    div = False
    lows2 = [(j, p) for j, p in known(a["lows"], i) if j >= bot_i - 60]
    if len(lows2) >= 2:
        (j1, p1), (j2, p2) = lows2[-2], lows2[-1]
        div = p2 <= p1 * 1.02 and a["rsi"][j2] > a["rsi"][j1] + 3
    pl = plan_from(a, i, hl, "higher_low")
    cond = {"reclaim50": recl50, "over_base": over_base, "upvol": upv > dnv, "rs_improving": rs_up,
            "divergence": div, "below_falling_200": a["c"][i] < a["s200"][i] and a["s200"][i] < a["s200"][i - 20],
            "base_len": hl_i - bot_i, "drawdown": dd}
    return pl, cond


def family_c(a, i):
    """C0 at bar i -> (plan or None, conditions): a low under a confirmed swing low in the last 3 sessions, closed back
    over it"""
    c = float(a["c"][i])
    sweep_low = float(a["l"][i - 2:i + 1].min())
    lv = [p for j, p in known(a["lows"], i - 3) if j >= i - 120 and sweep_low < p < c]
    if not lv:
        return None, {}
    p = max(lv)
    return plan_from(a, i, sweep_low, "sweep"), {"swept_level": p}


def define(a, i, ctx):
    """every definition that fires at bar i -> {def: plan}; ctx: {spy_red, vix, vix_prev, spy_c}"""
    out, conds = {}, {}
    if i < 260 or not np.isfinite(a["atr"][i]) or a["atr"][i] <= 0 or not np.isfinite(a["s200"][i]):
        return out, conds
    pa, ca = family_a(a, i)
    if pa:
        conds.update({"a_" + k: v for k, v in ca.items()})
        out["A0"] = pa
        if ca.get("swing_confluence"):
            out["A1"] = pa
            red = ctx.get("spy_red") and a["c"][i] < a["c"][i - 1]
            if red:
                out["A2"] = pa
            v, vp = ctx.get("vix"), ctx.get("vix_prev")
            if v is not None and vp and (v / vp - 1 >= 0.10 or v > 22):
                out["A3"] = pa
    pb, cb = family_b(a, i, ctx.get("spy_c"))
    if pb:
        conds.update({"b_" + k: v for k, v in cb.items()})
        out["B0"] = pb
        if cb["reclaim50"]:
            out["B1"] = pb
        if cb["over_base"]:
            out["B2"] = pb
        if (cb["reclaim50"] or cb["over_base"]) and cb["upvol"] and cb["rs_improving"]:
            out["B3"] = pb
    pc, cc = family_c(a, i)
    if pc:
        out["C0"] = pc
    return out, conds


# ---------------------------------------------------------------- features at bar i (closed bars only)
FEATURES = ("dist_e21", "dist_e50", "dist_s200", "slope_e50", "slope_s200", "adx", "rsi", "rsi_slope5", "macdh",
            "ret5", "ret20", "ret60", "ret120", "rs20", "rs60", "dd_high", "up_from_low", "rvol", "vol_trend",
            "updown_vol", "atr_pct", "atr_ratio", "range10", "clv", "lower_wick", "red_day", "gap", "rr",
            "t1_atr", "stop_atr", "spy_ret5", "spy_above50", "vix", "vix_chg5", "breadth", "regime_on",
            "regime_off", "fear_day", "spy_ret1")


def features(a, i, plan, ctx):
    c, k, h, l, o = a["c"], float(a["atr"][i]), a["h"], a["l"], a["o"]
    rng = h[i] - l[i]
    spy_c = ctx.get("spy_c")

    def rs(n):
        if spy_c is None or not np.isfinite(spy_c[i - n]) or spy_c[i - n] <= 0:
            return 0.0
        return c[i] / c[i - n] - spy_c[i] / spy_c[i - n]
    upv = a["v"][i - 19:i + 1][np.diff(c[i - 20:i + 1]) > 0].sum()
    dnv = a["v"][i - 19:i + 1][np.diff(c[i - 20:i + 1]) < 0].sum()
    reg = ctx.get("regime")
    f = [(c[i] - a["e21"][i]) / k, (c[i] - a["e50"][i]) / k, (c[i] - a["s200"][i]) / k,
         (a["e50"][i] - a["e50"][i - 10]) / k, (a["s200"][i] - a["s200"][i - 20]) / k,
         a["adx"][i], a["rsi"][i], a["rsi"][i] - a["rsi"][i - 5], a["macdh"][i] / k,
         c[i] / c[i - 5] - 1, c[i] / c[i - 20] - 1, c[i] / c[i - 60] - 1, c[i] / c[i - 120] - 1, rs(20), rs(60),
         c[i] / h[max(0, i - 251):i + 1].max() - 1, c[i] / l[max(0, i - 251):i + 1].min() - 1,
         a["v"][i] / a["v20"][i - 1] if a["v20"][i - 1] else np.nan, a["v20"][i] / a["v50"][i] if a["v50"][i] else np.nan,
         np.log((upv + 1) / (dnv + 1)), k / c[i], k / a["atr50"][i] if a["atr50"][i] else np.nan,
         (h[i - 9:i + 1].max() - l[i - 9:i + 1].min()) / k,
         ((c[i] - l[i]) - (h[i] - c[i])) / rng if rng > 0 else 0.0,
         (min(o[i], c[i]) - l[i]) / rng if rng > 0 else 0.0, float(c[i] < c[i - 1]), (o[i] - c[i - 1]) / k,
         plan["rr"], (plan["t1"] - c[i]) / k, (c[i] - plan["stop"]) / k,
         ctx.get("spy_ret5", 0.0), float(ctx.get("spy_above50", 0)), ctx.get("vix") or np.nan,
         ctx.get("vix_chg5", 0.0), ctx.get("breadth", np.nan), float(reg == "Risk-on"), float(reg == "Risk-off"),
         float(bool(ctx.get("spy_red")) and c[i] < c[i - 1]), ctx.get("spy_ret1", 0.0)]
    return [float(x) if x is not None else np.nan for x in f]


def market(spy_bars, vix, breadth):
    """per-session market context from SPY, VIX and breadth (share of names over their own 50-day)"""
    s = O.arrays(spy_bars)
    e50 = O.sma(s["c"], 50)
    reg = O.regime_series(s, vix, breadth)
    out = {}
    for i, d in enumerate(s["d"]):
        if i < 6:
            continue
        dates = s["d"]
        v = vix.get(d)
        v5 = vix.get(dates[i - 5])
        vp = vix.get(dates[i - 1])
        out[d] = {"spy_red": s["c"][i] < s["c"][i - 1], "spy_ret5": s["c"][i] / s["c"][i - 5] - 1,
                  "spy_ret1": s["c"][i] / s["c"][i - 1] - 1,
                  "spy_above50": bool(np.isfinite(e50[i]) and s["c"][i] > e50[i]), "vix": v, "vix_prev": vp,
                  "vix_chg5": (v / v5 - 1) if v and v5 else 0.0, "breadth": breadth.get(d, np.nan),
                  "regime": reg.get(d)}
    return out, dict(zip(s["d"], s["c"]))


MAX_ATR_MOVE = 30.0           # a bar more than this many ATRs from the fill is a data break (an unadjusted split,
                               # a bad print), not a trade: such a path is left out and counted, never scored


FEAR_SPY = -0.01               # a market fear day for the baselines: SPY down 1% or more on the session


def clean(p):
    v = p[np.isfinite(p)]
    return v.size == 0 or float(np.abs(v).max()) <= MAX_ATR_MOVE


def cases(sym, bars, mkt, spy_close, seed=0, random_every=O.RANDOM_EVERY):
    """every definition's cases for one name: list of dicts {def, sym, date, P (T,4), out, t1, t2, rr, feats, conds,
    regime}; plus random entries (def 'R') at seeded bars, with no plan of their own"""
    if not bars or len(bars) < 300:
        return []
    a = prepare(bars)
    spy_c = np.array([spy_close.get(d, np.nan) for d in a["d"]])
    rng = np.random.default_rng(zlib.crc32(sym.encode()) + seed)
    draws = rng.random(len(a["c"]))
    out, last = [], {}
    for i in range(260, len(a["c"]) - 1):
        d = a["d"][i]
        ctx = dict(mkt.get(d) or {})
        ctx["spy_c"] = spy_c
        fired, conds = define(a, i, ctx)
        p = None
        for name, pl in fired.items():
            if i - last.get(name, -10 ** 9) < O.EPISODE:
                continue
            p = p if p is not None else O.path(a, i)
            if p is None or not clean(p):
                break
            last[name] = i
            e, k = a["o"][i + 1], a["atr"][i]
            row = {"def": name, "sym": sym, "date": d, "P": p, "out": (e - pl["stop"]) / k, "t1": (pl["t1"] - e) / k,
                   "t2": (pl["t2"] - e) / k if pl["t2"] else np.nan, "rr": pl["rr"],
                   "risk": (a["c"][i] - pl["stop"]) / k, "regime": ctx.get("regime"),
                   "feats": features(a, i, pl, ctx), "conds": conds}
            out.append(row)
        if draws[i] < 1.0 / random_every:
            pr = O.path(a, i)
            if pr is not None and clean(pr):
                up = bool(a["c"][i] > a["s200"][i] and a["e50"][i] > a["e50"][i - 10])
                out.append({"def": "R", "sym": sym, "date": d, "P": pr, "regime": ctx.get("regime"), "up": up,
                            "fear": bool(ctx.get("spy_ret1", 0.0) <= FEAR_SPY)})
    return out
