"""The odds engine: how often a setup like this one has paid, on the desk's own split-adjusted daily bars.

SCOPE (InfinityBlade, 2026-10-26, PLAN.md Phase 1 #2, #9, #10, Phase 3 #16a):
  Surface   this module, job `terminal_odds` (desk/jobs.py), an additive `odds` block on the edition's setups and
            watching rows (desk/terminal/__init__.py), web/terminal/odds.js (the probability box).
  Constraints  closed bars only; a setup is seen at the close of its signal bar and bought at the NEXT bar's open;
            the record's own exits (calls.resolve_reads): the out line is a daily close at or under it, sold at the
            next open; the target is an intraday high, sold at max(open, target); on the fill bar only the out line
            is checked; the out line comes first on a bar that does both; time stop at the call's own session count.
            Inputs: Alpaca SIP split-adjusted daily bars and the Cboe VIX file only (FINRA and SqueezeMetrics are
            allowed by the owner, 2026-10-26/27; this engine reads neither).
  Outcome   per card: P(T1 before the out line) for its own setup type, regime and geometry, with n, the 95% Wilson
            interval, the base rate of random entries in the same names under the same exits (edge vs random), the
            last five results, P(T2 | T1), level odds (test / hold / days to touch) and the target-depth curve;
            plus an analog line: the nearest sixth of past states. Under 30 cases the block says validation pending.
  Proof     tests/test_terminal_odds.py (fixture paths with hand-known outcomes, a no-look-ahead test, Wilson by hand).
  Edges     history: the cache's bars (SPY from 2018, most names from 2023). A historical setup is the module's own
            detector of the read's form (pullback / 21-day reclaim / breakout / turn / fear-day pullback), not the full
            34-module read replayed point-in-time (Pattern engine 1); the block says so ("method").

Every rate is a frequency over resolved past cases, never a forecast of this name; percent figures only, no price."""
import json
import math
import os
from datetime import date, datetime, timezone

import numpy as np

from ..util import write_json_atomic

VERSION = "odds-1"
T = 40                         # forward bars kept per case: the record's TIME_STOP_MAX
MIN_N = 30                     # under this many resolved cases a rate reads "validation pending"
CAP_PER_TYPE = 30000           # most recent cases kept per type (memory and runtime bound)
EPISODE = 10                   # a name's case of one type starts again only this many bars after the last
RANDOM_EVERY = 25              # the random pool: about one bar in this many per name, seeded
DEFAULT = {"out": 1.5, "t1": 2.0, "t2": 3.5, "ts": 20}   # ATR geometry when a card brings none
DEPTHS = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
STRETCH_ATR = 2.0              # a first target farther than this from the buy is flagged
TYPES = ("pullback", "reclaim21", "breakout", "turn", "fear_pullback")
LABEL = {"pullback": "pullback in an uptrend", "reclaim21": "close back over the 21-day average",
         "breakout": "breakout on volume", "turn": "turn up from a low", "fear_pullback": "fear-day pullback",
         "random": "random entry"}
REGIMES = ("Risk-on", "Mixed", "Risk-off")
Z = 1.96
METHOD = ("Past cases from the desk's daily bars: each found by this setup type's rule at a daily close, bought at "
          "the next open, sold on a close under the out line (at the next open) or at the target, out line first.")


# ---------------------------------------------------------------- arithmetic
def wilson(k, n, z=Z):
    """the 95% Wilson interval of k hits in n: (lo, hi), or (None, None) with n = 0"""
    if n <= 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, mid - half), min(1.0, mid + half)


def ema(x, n):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    a = 2.0 / (n + 1)
    out[n - 1] = np.mean(x[:n])
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def sma(x, n):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        c = np.cumsum(np.insert(x, 0, 0.0))
        out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def atr(h, l, c, n=14):
    """Wilder's average true range, seeded with the simple mean of the first n ranges"""
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    tr = np.insert(tr, 0, h[0] - l[0])
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(c)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def arrays(bars):
    """daily bars -> dict of numpy arrays and their session dates (ISO)"""
    o = np.array([float(b["o"]) for b in bars])
    h = np.array([float(b["h"]) for b in bars])
    l = np.array([float(b["l"]) for b in bars])
    c = np.array([float(b["c"]) for b in bars])
    v = np.array([float(b.get("v") or 0) for b in bars])
    d = [datetime.fromtimestamp(float(b["t"]), timezone.utc).date().isoformat() for b in bars]
    return {"o": o, "h": h, "l": l, "c": c, "v": v, "d": d}


def indicators(a):
    a["e21"], a["e50"], a["s200"] = ema(a["c"], 21), ema(a["c"], 50), sma(a["c"], 200)
    a["atr"] = atr(a["h"], a["l"], a["c"])
    a["v20"] = sma(a["v"], 20)
    return a


# ---------------------------------------------------------------- the setup rules, at the close of bar i (no later bar)
def _up(a, i):
    return (a["e50"][i] > a["s200"][i] and a["c"][i] > a["e50"][i] and i >= 5 and a["e50"][i] > a["e50"][i - 5])


def detect(a, i, spy_red=None):
    """the setup types bar i shows at its close, from bars 0..i only. spy_red: True when the market fund closed red
    on that session (the owner's fear-day rule needs the name and its fund both red)"""
    if i < 200 or not np.isfinite(a["atr"][i]) or not np.isfinite(a["s200"][i]) or a["atr"][i] <= 0:
        return []
    c, h, l, e21, k = a["c"], a["h"], a["l"], a["e21"], a["atr"][i]
    out = []
    up = _up(a, i)
    pull = up and l[i] <= e21[i] + 0.25 * k and c[i] >= e21[i] - 0.5 * k and h[i - 10:i].max() >= e21[i] + 1.5 * k
    recl = (c[i] > a["e50"][i] and a["e50"][i] > a["e50"][i - 5] and c[i - 1] < e21[i - 1] and c[i] > e21[i])
    if pull:
        out.append("pullback")
    if recl:
        out.append("reclaim21")
    if (c[i] > h[i - 20:i].max() and c[i] > a["e50"][i] and np.isfinite(a["v20"][i - 1])
            and a["v"][i] > 1.5 * a["v20"][i - 1]):
        out.append("breakout")
    if l[i - 10:i + 1].min() <= l[i - 60:i + 1].min() and c[i] > h[i - 5:i].max() and c[i] < a["s200"][i]:
        out.append("turn")
    if (pull or recl) and spy_red and c[i] < c[i - 1]:
        out.append("fear_pullback")
    return out


def features(a, i, spy_c=None):
    """the analog's state at the close of bar i: distance from the 21-day in ATR, its slope, 20-day return, ATR %,
    distance under the 1-year high, 20-day strength against SPY"""
    c, k = a["c"], a["atr"][i]
    rs = 0.0
    if spy_c is not None and i >= 20 and spy_c[i - 20] > 0:
        rs = (c[i] / c[i - 20]) - (spy_c[i] / spy_c[i - 20])
    return [(c[i] - a["e21"][i]) / k, (a["e21"][i] - a["e21"][i - 5]) / k, c[i] / c[i - 20] - 1, k / c[i],
            c[i] / a["h"][max(0, i - 251):i + 1].max() - 1, rs]


def path(a, i):
    """the forward path after bar i, in ATRs from the next open: shape (T, 4) o/h/l/c, NaN past the last bar"""
    p = np.full((T, 4), np.nan, dtype=np.float32)
    if i + 1 >= len(a["c"]):
        return None
    e, k = a["o"][i + 1], a["atr"][i]
    j = min(len(a["c"]), i + 1 + T)
    for col, key in enumerate("ohlc"):
        p[: j - i - 1, col] = (a[key][i + 1:j] - e) / k
    return p


# ---------------------------------------------------------------- the record's exits, on many paths at once
def simulate(P, out, t1, t2=None, ts=20, risk=None):
    """P: (N, T, 4) paths in ATRs from the fill; out, t1 (and t2): positive ATR distances below / above the fill;
    ts: the time stop in held bars. -> dict of arrays (N,): resolved, hit (t1 first), r (in units of out), t1_day,
    t2_after_t1, mfe, mae, touch (any high >= t1 by ts), close_beyond (any close >= t1 by ts). The fill bar checks the
    out line only (calls.resolve_reads); after it the out line (a close at or under) comes before the target"""
    N = P.shape[0]
    o, h, l, c = P[..., 0], P[..., 1], P[..., 2], P[..., 3]
    out = np.broadcast_to(np.asarray(out, float), (N,))           # one geometry, or one per case
    # R in the plan's own risk (calls.risk_unit: set before the outcome, never the fill's distance to the out line)
    rk = np.broadcast_to(np.asarray(out if risk is None else risk, float), (N,))
    t1 = np.broadcast_to(np.asarray(t1, float), (N,))
    if t2 is not None:
        t2 = np.broadcast_to(np.asarray(t2, float), (N,))
    live = np.ones(N, bool)
    resolved = np.zeros(N, bool)
    hit = np.zeros(N, bool)
    r = np.full(N, np.nan)
    day = np.full(N, np.nan)
    pend_out = np.zeros(N, bool)
    mfe = np.zeros(N)
    mae = np.zeros(N)
    last = min(ts, T - 1)
    for k in range(0, last + 1):
        ok = live & np.isfinite(c[:, k])
        # a close under the out line on the bar before: sold at this open
        so = ok & pend_out
        r[so] = o[so, k] / rk[so]
        resolved[so], live[so] = True, False
        ok &= ~so
        mfe[ok] = np.maximum(mfe[ok], h[ok, k])
        mae[ok] = np.minimum(mae[ok], l[ok, k])
        if k > 0:
            th = ok & (c[:, k] > -out) & (h[:, k] >= t1)
            r[th] = np.maximum(o[th, k], t1[th]) / rk[th]
            hit[th], resolved[th], live[th], day[th] = True, True, False, k
            ok &= ~th
        po = ok & (c[:, k] <= -out)
        pend_out |= po
        if k >= 1 and k == last:
            tsx = ok & ~po
            r[tsx] = c[tsx, k] / rk[tsx]
            resolved[tsx], live[tsx] = True, False
    # P(T2 | T1): after the T1 bar, a high at t2 before a close at the out line, within the same time stop
    t2_after = np.zeros(N, bool)
    if t2 is not None and hit.any():
        ks = np.arange(T)[None, :]
        after = (ks >= np.nan_to_num(day, nan=T)[:, None]) & (ks <= last)
        up = after & (np.nan_to_num(h, nan=-np.inf) >= t2[:, None])
        dn = after & (np.nan_to_num(c, nan=np.inf) <= -out[:, None])
        fu = np.where(up.any(axis=1), np.argmax(up, axis=1), T + 1)
        fd = np.where(dn.any(axis=1), np.argmax(dn, axis=1), T + 1)
        t2_after = hit & (fu <= T) & (fu <= fd)
    upto = slice(1, last + 1)
    touch = (np.nan_to_num(h[:, upto], nan=-np.inf) >= t1[:, None]).any(axis=1)
    close_beyond = (np.nan_to_num(c[:, upto], nan=-np.inf) >= t1[:, None]).any(axis=1)
    return {"resolved": resolved, "hit": hit, "r": r, "t1_day": day, "t2_after_t1": t2_after, "mfe": mfe,
            "mae": mae, "touch": touch, "close_beyond": close_beyond}


def level_odds(P, level, ts, below):
    """a level `level` ATRs from the fill (positive): below=True a support (the out line): test = a low at it,
    break = a close at or under it; else a target: test = a high at it. -> (P(test), P(hold | test) or None,
    median sessions to the first test)"""
    seg = P[:, : ts + 1]
    if below:
        tested = np.nan_to_num(seg[..., 2], nan=np.inf) <= -level
        broke = np.nan_to_num(seg[..., 3], nan=np.inf) <= -level
    else:
        tested = np.nan_to_num(seg[..., 1], nan=-np.inf) >= level
        broke = None
    t_any = tested.any(axis=1)
    first = np.argmax(tested, axis=1)
    n = len(P)
    if n == 0:
        return None, None, None
    pt = float(t_any.mean())
    hold = None
    if broke is not None and t_any.sum() > 0:
        hold = float(1 - (broke.any(axis=1) & t_any).sum() / t_any.sum())
    days = float(np.median(first[t_any])) if t_any.any() else None
    return pt, hold, days


# ---------------------------------------------------------------- the pool of past cases
def regime_series(spy, vix, part):
    """{date: Risk-on | Mixed | Risk-off}: the badge's rule (market.badge: three quarters of the checks pass = Risk-on,
    a quarter or fewer = Risk-off) over four checks the history can rebuild point-in-time: SPY over its 50-day, the
    50-day over the 200-day, VIX under 20, and over half the names above their own 50-day. vix, part: {date: value}"""
    out = {}
    e50, s200 = sma(spy["c"], 50), sma(spy["c"], 200)
    for i, d in enumerate(spy["d"]):
        checks = []
        if np.isfinite(e50[i]):
            checks.append(spy["c"][i] > e50[i])
        if np.isfinite(s200[i]):
            checks.append(e50[i] > s200[i])
        if d in vix:
            checks.append(vix[d] < 20)
        if d in part:
            checks.append(part[d] > 0.5)
        if len(checks) < 3:
            continue
        s = sum(checks) / len(checks)
        out[d] = "Risk-on" if s >= 0.75 else "Risk-off" if s <= 0.25 else "Mixed"
    return out


def read_vix(path_csv):
    vix = {}
    try:
        with open(path_csv) as f:
            next(f)
            for line in f:
                p = line.strip().split(",")
                if len(p) >= 5:
                    m, dd, y = p[0].split("/")
                    vix[f"{y}-{m}-{dd}"] = float(p[4])
    except (OSError, ValueError, StopIteration):
        pass
    return vix


def build_pool(bars_by_sym, spy_bars, vix, seed=7, cap=CAP_PER_TYPE):
    """every name's past cases: {type: {"P": (N,T,4), "F": (N,6), "date": [...], "sym": [...], "regime": [...]}},
    'random' the seeded random-entry pool. Each case's features and regime are those of its signal bar only."""
    spy = arrays(spy_bars)
    spy_c = dict(zip(spy["d"], spy["c"]))
    spy_red = {spy["d"][i]: spy["c"][i] < spy["c"][i - 1] for i in range(1, len(spy["c"]))}
    names = {}
    above = {}
    for sym, bars in bars_by_sym.items():
        if not bars or len(bars) < 260:
            continue
        a = indicators(arrays(bars))
        names[sym] = a
        for i, d in enumerate(a["d"]):
            if np.isfinite(a["e50"][i]):
                t = above.setdefault(d, [0, 0])
                t[0] += a["c"][i] > a["e50"][i]
                t[1] += 1
    part = {d: x / n for d, (x, n) in above.items() if n >= 50}
    reg = regime_series(spy, vix, part)
    rng = np.random.default_rng(seed)
    acc = {t: [] for t in TYPES + ("random",)}
    for sym in sorted(names):
        a = names[sym]
        sc = np.array([spy_c.get(d, np.nan) for d in a["d"]])
        lastk = {}
        draws = rng.random(len(a["c"]))
        for i in range(200, len(a["c"]) - 1):
            d = a["d"][i]
            types = detect(a, i, spy_red.get(d))
            if draws[i] < 1.0 / RANDOM_EVERY and np.isfinite(a["atr"][i]) and a["atr"][i] > 0:
                types = types + ["random"]
            for t in types:
                if t != "random" and i - lastk.get(t, -10 ** 9) < EPISODE:
                    continue
                p = path(a, i)
                if p is None:
                    continue
                lastk[t] = i
                acc[t].append((d, sym, reg.get(d), p, features(a, i, sc)))
    pool = {}
    for t, rows in acc.items():
        rows.sort(key=lambda x: x[0])
        rows = rows[-cap:]
        pool[t] = {"date": [x[0] for x in rows], "sym": [x[1] for x in rows], "regime": [x[2] for x in rows],
                   "P": np.stack([x[3] for x in rows]) if rows else np.zeros((0, T, 4), np.float32),
                   "F": np.array([x[4] for x in rows], dtype=float) if rows else np.zeros((0, 6))}
    return pool, reg


def _sel(pool_t, regime=None, before=None, ts=20):
    """indices of cases in a regime whose time stop had passed by `before` (ISO date): resolved by then"""
    d = pool_t.get("_d")
    if d is None:
        d = pool_t["_d"] = np.array(pool_t["date"], dtype="U10")
        pool_t["_r"] = np.array([x or "" for x in pool_t["regime"]], dtype="U8")
    m = np.ones(len(d), bool)
    if regime:
        m &= pool_t["_r"] == regime
    if before:
        m &= d < before
    return np.nonzero(m)[0]


def _rate(sim, idx):
    res = sim["resolved"][idx]
    n = int(res.sum())
    k = int(sim["hit"][idx][res].sum())
    return k, n


# ---------------------------------------------------------------- per card
def card_geometry(rec):
    """a read record (prices) -> ATR distances from its buy (the cap; a trigger buy, the trigger), and its time stop"""
    k = float(rec.get("atr") or 0)
    if k <= 0:
        return None
    buy = float(rec["trigger"]) if rec.get("trigger") is not None else float(rec["zone"][1])
    g = {"out": (buy - float(rec["out"])) / k, "t1": (float(rec["t1"]) - buy) / k,
         "t2": (float(rec["t2"]) - buy) / k if rec.get("t2") else None,
         "ts": min(2 * int(rec.get("sessions") or 10), T - 1)}
    if g["out"] <= 0 or g["t1"] <= 0:
        return None
    return g


def setup_type(rec, fear_state=None):
    """the record's form as one of the pool's types; a pullback whose fear-day rule has come is a fear-day pullback"""
    form = rec.get("form")
    if form in ("now", "pullback"):
        return "fear_pullback" if fear_state == "came" else "pullback"
    if form in ("breakout", "turn"):
        return form
    return None


def odds_for(pool, rec, regime, as_of, feats=None, fear_state=None):
    """the card's odds block (see SCOPE), or None when the card has no type or geometry"""
    typ = setup_type(rec, fear_state)
    if not typ or typ not in pool:
        return None
    g = card_geometry(rec)
    if not g:
        return None
    pt, pr = pool[typ], pool["random"]
    s = simulate(pt["P"], g["out"], g["t1"], g["t2"], g["ts"])
    sr = simulate(pr["P"], g["out"], g["t1"], None, g["ts"])
    idx = _sel(pt, regime, as_of)
    k, n = _rate(s, idx)
    kr, nr = _rate(sr, _sel(pr, regime, as_of))
    lo, hi = wilson(k, n)
    res = idx[s["resolved"][idx]]
    hits = res[s["hit"][res]]
    rate = k / n if n else None
    base = kr / nr if nr else None
    block = {"v": VERSION, "type": LABEL[typ], "regime": regime, "n": n, "hits": k,
             "rate": _p(rate), "lo": _p(lo), "hi": _p(hi), "base": _p(base),
             "lift": _p(rate - base) if rate is not None and base is not None else None,
             "pending": n < MIN_N,
             "mean_r": round(float(np.nanmean(s["r"][res])), 2) if n else None,
             "se_r": round(float(np.nanstd(s["r"][res]) / math.sqrt(n)), 2) if n > 1 else None,
             "days": round(float(np.median(s["t1_day"][hits])), 1) if len(hits) else None,
             "touch": _p(float(s["touch"][res].mean())) if n else None,
             "close_beyond": _p(float(s["close_beyond"][res].mean())) if n else None,
             "mfe": round(float(np.median(s["mfe"][res])), 2) if n else None,
             "mae": round(float(np.median(s["mae"][res])), 2) if n else None,
             "window": [pt["date"][idx[0]], pt["date"][idx[-1]]] if len(idx) else None,
             "last5": ["W" if s["hit"][j] else "L" for j in res[-5:]],
             "t1_atr": round(g["t1"], 2), "out_atr": round(g["out"], 2),
             "stretch": g["t1"] > STRETCH_ATR, "method": METHOD}
    if g["t2"] and len(hits):
        block["t2_given_t1"] = _p(float(s["t2_after_t1"][hits].mean()))
        block["t2_n"] = int(len(hits))
    sub = pt["P"][res] if len(res) else pt["P"][:0]
    lv = []
    for name, dist, below in (("out line", g["out"], True), ("first target", g["t1"], False),
                              ("second target", g["t2"], False)):
        if dist is None or len(sub) == 0:
            continue
        p_test, hold, days = level_odds(sub, dist, g["ts"], below)
        lv.append({"level": name, "test": _p(p_test), "hold": _p(hold), "days": days})
    block["levels"] = lv
    curve = []
    for d in DEPTHS:
        sd = simulate(sub, g["out"], d, None, g["ts"]) if len(sub) else None
        if sd is not None:
            curve.append({"atr": d, "rate": _p(float(sd["hit"].mean()))})
    block["depth"] = curve
    if feats is not None and len(pt["F"]):
        block["analog"] = analog(pt, s, sr, pr, regime, as_of, feats)
    block["sentence"] = sentence(block)
    return block


def _p(x):
    return None if x is None else round(100 * float(x), 1)


def analog(pt, s, sr, pr, regime, as_of, feats):
    """the nearest sixth of past cases of this type (by their state, median/MAD-scaled) -> {n, rate, base, lift,
    sentence}; base: the random pool in the same regime under the same exits"""
    idx = _sel(pt, None, as_of)
    idx = idx[s["resolved"][idx]]
    if len(idx) < 6:
        return {"n": len(idx), "rate": None, "base": None, "lift": None, "sentence": None}
    F = pt["F"][idx]
    key = ("_scale", len(idx))
    if pt.get("_scale_key") != key:                  # median / MAD of the eligible cases, kept across cards
        med = np.nanmedian(F, axis=0)
        mad = np.nanmedian(abs(F - med), axis=0) * 1.4826
        mad[mad == 0] = 1.0
        pt["_scale_key"], pt["_scale"] = key, (med, mad)
    med, mad = pt["_scale"]
    x = (np.array(feats, dtype=float) - med) / mad
    Z_ = (F - med) / mad
    dist = np.nansum((Z_ - x) ** 2, axis=1)
    near = idx[np.argsort(dist)[: max(1, len(idx) // 6)]]
    k, n = int(s["hit"][near].sum()), len(near)
    kr, nr = _rate(sr, _sel(pr, regime, as_of))
    rate, base = k / n, (kr / nr if nr else None)
    out = {"n": n, "rate": _p(rate), "base": _p(base), "lift": _p(rate - base) if base is not None else None}
    out["sentence"] = (f"In {n} past setups most like this one, the first target came before the out line "
                       f"{out['rate']:g}% of the time" + (f" (random entries: {out['base']:g}%)." if base is not None else "."))
    return out


def sentence(b):
    if not b["n"]:
        return "No past cases of this setup in this market yet."
    s = (f"{b['type'].capitalize()}, {b['regime'] or 'any'} market: first target before the out line in "
         f"{b['hits']} of {b['n']} past cases ({b['rate']:g}%")
    s += f"; random entries {b['base']:g}%)." if b["base"] is not None else ")."
    if b["pending"]:
        s += " Too few cases to rely on (validation pending under 30)."
    return s


# ---------------------------------------------------------------- the job
def folder(root):
    return os.path.join(root, "state", "terminal")


def run(root, bars_by_sym, spy_bars, vix, records, regime_now, as_of, fear_by_sym=None, feats_by_sym=None):
    """the nightly odds: the pool from every name's bars, then one block per current read record. Writes
    state/terminal/odds.json {as_of, v, regime, generated_at, cards: {sym: block}, types: {type: summary}}"""
    pool, _ = build_pool(bars_by_sym, spy_bars, vix)
    cards = {}
    for sym, rec in records.items():
        if rec.get("as_of") != as_of:
            continue
        b = odds_for(pool, rec, regime_now, as_of, (feats_by_sym or {}).get(sym), (fear_by_sym or {}).get(sym))
        if b:
            cards[sym] = b
    types = {}
    for t in TYPES:
        s = simulate(pool[t]["P"], DEFAULT["out"], DEFAULT["t1"], DEFAULT["t2"], DEFAULT["ts"])
        sr = simulate(pool["random"]["P"], DEFAULT["out"], DEFAULT["t1"], None, DEFAULT["ts"])
        row = {}
        for rg in REGIMES:
            k, n = _rate(s, _sel(pool[t], rg, as_of))
            kr, nr = _rate(sr, _sel(pool["random"], rg, as_of))
            lo, hi = wilson(k, n)
            row[rg] = {"n": n, "hits": k, "rate": _p(k / n) if n else None, "lo": _p(lo), "hi": _p(hi),
                       "base": _p(kr / nr) if nr else None, "pending": n < MIN_N}
        types[t] = {"label": LABEL[t], "by_regime": row}
    doc = {"v": VERSION, "as_of": as_of, "regime": regime_now, "default": DEFAULT, "cards": cards, "types": types,
           "cases": {t: len(pool[t]["date"]) for t in pool}, "method": METHOD}
    write_json_atomic(os.path.join(folder(root), "odds.json"), doc)
    return doc


PUBLIC = {"v", "type", "regime", "n", "hits", "rate", "lo", "hi", "base", "lift", "pending", "mean_r", "se_r", "days",
          "touch", "close_beyond", "mfe", "mae", "window", "last5", "t1_atr", "out_atr", "stretch", "method",
          "t2_given_t1", "t2_n", "levels", "depth", "analog", "sentence"}
LEVEL_KEYS = {"level", "test", "hold", "days"}
DEPTH_KEYS = {"atr", "rate"}
ANALOG_KEYS = {"n", "rate", "base", "lift", "sentence"}


def public(block):
    """the block as the edition may carry it (no price: ATR distances and percent only)"""
    if not block:
        return None
    return {k: v for k, v in block.items() if k in PUBLIC}
