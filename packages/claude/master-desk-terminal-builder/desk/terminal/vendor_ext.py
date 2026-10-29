"""The vendor terminal package (owner ruling LIC-02, 2026-10-27: every torn-down vendor may be installed, replicated
and used). Each function ports one vendor feature from its teardown (docs/research/rea_status_vendor-terminal.csv names
the row, the teardown line and the test) and computes it from data the desk holds, closed bars only, point in time.
A block is {"status": "ok", ...} or {"status": "no_data", "reason": <one line>}; nothing is a constant or a default.

  card (context.py merges them under setups[].context and picker.<lane>[].context)
    heikin_read   C222   Heikin-Ashi colour, run and flat bottom
    stoch_rsi     C125   Stochastic RSI %K and %D with its zone
    pivots        C126   classic, Fibonacci, Woodie and Camarilla levels of the next session, in % from the close
    atr_range     C2     the last session's range as a share of the prior bar's ATR(14), and the cloud trend label
    falsifier     V-tensor-3  the one price that voids the plan, and how long the read stands
  options (strip.options_block merges them into each structure)
    ev_rank       C138   expected value on the name's own measured finish distribution, ranked by EV / max loss
    pnl_grid      OTT / OptionScout P&L grid of a structure over price and date
  market (edition key `vendor`)
    emp_move      CX-sg-5  the one-day and five-day move by VIX tercile from SPY's own history, graded on a holdout year
    em_decay      V-azrael-5  the share of the day's expected move that remains, and the week's range
    zweig         CL6    Zweig breadth thrust over the roster's advancers and decliners
    straddle      FN-2   QuantData's Caliper verdict on the 30-day straddle, from stored IV30
    regime        FN-1   the intraday regime and its hold probability, from the stored transition table"""
import math
import random
from datetime import date

from .. import calendar as cal
from .read import levels as _levels
from .read import ta


def nd(reason, **kw):
    return dict({"status": "no_data", "reason": reason}, **kw)


def _n(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _r(x, k=2):
    return None if x is None else round(x + 0.0, k)


def _closed(bars):
    return [b for b in bars or () if isinstance(b, dict) and all(_n(b.get(k)) is not None for k in ("o", "h", "l", "c"))]


# ---- C222 Heikin-Ashi -------------------------------------------------------------------------------------------------
def heikin_read(bars):
    """the last Heikin-Ashi candle's colour (up: close over open), how many candles in a row share it, and whether it has
    no lower wick (up) or no upper wick (down): the smooth trend Heikin-Ashi charts are read for. Display only"""
    bs = _closed(bars)
    if len(bs) < 4:
        return nd(f"Needs 4 daily bars, has {len(bs)}")
    ha = ta.heikin_ashi(bs)
    col = lambda h: "up" if h["c"] > h["o"] + 1e-12 else "down" if h["c"] < h["o"] - 1e-12 else "flat"
    last = col(ha[-1])
    run = 0
    for h in reversed(ha):
        if col(h) != last or last == "flat":
            break
        run += 1
    h = ha[-1]
    flat_bottom = last == "up" and abs(h["l"] - h["o"]) <= 1e-9 * max(1.0, abs(h["o"]))
    flat_top = last == "down" and abs(h["h"] - h["o"]) <= 1e-9 * max(1.0, abs(h["o"]))
    return {"status": "ok", "color": last, "run": run, "flat_bottom": bool(flat_bottom or flat_top)}


# ---- C125 Stochastic RSI ----------------------------------------------------------------------------------------------
def stoch_rsi(bars):
    """Stochastic RSI (14, 14, 3, 3) at the last close: %K, %D, the zone (over 80 stretched, under 20 washed out), whether
    %K just crossed %D, and the RSI(14) itself (the vendor's chart panel)"""
    cs = ta.closes(_closed(bars))
    if len(cs) < 14 + 14 + 3 + 3:
        return nd(f"Needs 34 daily closes, has {len(cs)}")
    k, d = ta.stoch_rsi(cs, 14, 14, 3, 3)
    if k[-1] is None or d[-1] is None:
        return nd("No RSI range to read")
    zone = "over 80" if k[-1] > 80 else "under 20" if k[-1] < 20 else "between 20 and 80"
    return {"status": "ok", "k": _r(k[-1], 1), "d": _r(d[-1], 1), "zone": zone, "rsi": _r(ta.rsi(cs, 14)[-1], 1),
            "cross": "up" if k[-1] > d[-1] and k[-2] is not None and d[-2] is not None and k[-2] <= d[-2] else
            "down" if k[-1] < d[-1] and k[-2] is not None and d[-2] is not None and k[-2] >= d[-2] else None}


# ---- C126 pivot points ------------------------------------------------------------------------------------------------
def pivots(bars):
    """the four pivot tables for the session after the last completed bar, each level in % from that bar's close"""
    bs = _closed(bars)
    if len(bs) < 2:
        return nd("Needs a completed daily bar")
    last = bs[-1]
    c = float(last["c"])
    if c <= 0:
        return nd("No close")
    out = {"status": "ok", "from": cal._as_date(float(last["t"])).isoformat(),
           "for": cal.next_trading_day(cal._as_date(float(last["t"])), 1).isoformat()}
    for kind in _levels.PIVOT_KINDS:
        lv = _levels.pivot_points({"h": last["h"], "l": last["l"], "c": last["c"]}, kind)
        out[kind] = {k: _r(100.0 * (v / c - 1.0), 2) for k, v in lv.items()}
    return out


# ---- C2 ATR range consumption -----------------------------------------------------------------------------------------
RANGE_LOW, RANGE_HIGH = 70.0, 90.0           # Saty ATR Levels: green up to 70% of the ATR covered, red from 90%


def atr_range(bars):
    """the last completed session's high-to-low range as a share of the ATR(14) frozen at the prior close (Saty ATR
    Levels' range gauge: low up to 70%, high from 90%), and where the close sits against his two EMA clouds (5-12 and
    34-50): above both, below both or between"""
    bs = _closed(bars)
    if len(bs) < 60:
        return nd(f"Needs 60 daily bars, has {len(bs)}")
    atr = ta.atr(bs, 14)
    unit = atr[-2]
    if not unit:
        return nd("No ATR to measure the range by")
    pct = round((float(bs[-1]["h"]) - float(bs[-1]["l"])) / unit * 100.0, 6)
    cs = ta.closes(bs)
    e = {n: ta.ema(cs, n)[-1] for n in (5, 12, 34, 50)}
    c = cs[-1]
    fast, slow = (e[5], e[12]), (e[34], e[50])
    trend = ("above both clouds" if c > max(fast) and c > max(slow) else
             "below both clouds" if c < min(fast) and c < min(slow) else "between the clouds")
    return {"status": "ok", "pct": _r(pct, 0), "band": "low" if pct <= RANGE_LOW else "high" if pct >= RANGE_HIGH else "mid",
            "trend": trend, "as_of": cal._as_date(float(bs[-1]["t"])).isoformat()}


# ---- V-tensor-3 the "changes if" line ---------------------------------------------------------------------------------
FALSIFY = {
    "now": "a daily close under the stop",
    "pullback": "a daily close under the stop",
    "breakout": "a daily close under the stop before any close over the trigger",
    "turn": "a daily close back under the stop: the reclaim failed",
    "reaction": "a daily close under the stop",
}


def falsifier(plan, form=None, as_of=None):
    """the one price condition that voids the plan, in the plan's own numbers (% from the read's close), and how long the
    read stands: until the next completed bar (FolioTend / Tensor: signal lifetimes and a "CHANGES IF" line on every
    read). The sentence carries no number: the page prices `at` (and `trigger_at`) as it prices the plan"""
    if not isinstance(plan, dict) or _n(plan.get("out")) is None:
        return nd("No plan to falsify")
    if form is None:
        form = "breakout" if plan.get("trigger") is not None else "now"
    form = "reaction" if plan.get("mode") == "reaction" and form not in ("breakout", "turn") else form
    if form not in FALSIFY:
        return nd("No plan to falsify")
    out = {"status": "ok", "form": form, "text": FALSIFY[form], "at": float(plan["out"])}
    if form in ("breakout", "turn") and _n(plan.get("trigger")) is not None:
        out["trigger_at"] = float(plan["trigger"])
    if as_of:
        d = as_of if isinstance(as_of, date) else date.fromisoformat(str(as_of))
        out["valid_through"] = cal.next_trading_day(d, 1).isoformat()
    return out


# ---- C138 expected value and ranking ------------------------------------------------------------------------------------
EV_MIN_N = 60                                # fewest past windows behind a measured distribution (strip.TOUCH_MIN_N)


def _payoff(legs, s):
    return sum((1.0 if side == "buy" else -1.0) * max(s - float(k), 0.0) for side, k in legs)


def ev_rank(structures, spot, bars, days, min_n=EV_MIN_N):
    """Option Alpha's Expected Value ranking on the name's OWN measured distribution (not a lognormal): the structure's
    payoff at expiry on every past window of `days` sessions of the name's closes (the spot moved by that window's
    return), less the debit, averaged over the windows: ev (per share), ev_ratio = ev / max loss, ev_win = the share of
    windows that paid more than the debit, ev_n the windows, ev_rank 1 = the best ratio. Returns new structure dicts;
    with fewer than min_n windows each carries ev None and its reason"""
    structures = [dict(s) for s in structures or ()]
    cs = [float(b["c"]) for b in bars or () if isinstance(b, dict) and _n(b.get("c"))]
    days = int(days or 0)
    spot = _n(spot)
    n = len(cs) - days
    if not structures:
        return []
    if days < 1 or not spot or spot <= 0 or n < min_n:
        for s in structures:
            s.update(ev=None, ev_reason=f"{max(n, 0)} past windows of {max(days, 0)} sessions; needs {min_n}")
        return structures
    rets = [cs[i + days] / cs[i] for i in range(n) if cs[i] > 0]
    for s in structures:
        debit, loss = _n(s.get("debit")), _n(s.get("max_loss"))
        legs = s.get("legs") or []
        if debit is None or not loss or loss <= 0 or not legs:
            s.update(ev=None, ev_reason="no priced structure")
            continue
        pl = [_payoff(legs, spot * r) - debit for r in rets]
        ev = sum(pl) / len(pl)
        s.update(ev=round(ev, 2), ev_ratio=round(ev / loss, 3), ev_n=len(pl),
                 ev_win=round(sum(1 for x in pl if x > 1e-9) / len(pl), 3))
    ranked = sorted((s for s in structures if s.get("ev") is not None), key=lambda s: -s["ev_ratio"])
    for i, s in enumerate(ranked, 1):
        s["ev_rank"] = i
    return structures


# ---- the options P&L grid -----------------------------------------------------------------------------------------------
PNL_MOVES = (-15.0, -10.0, -5.0, -2.5, 0.0, 2.5, 5.0, 10.0, 15.0)
PNL_STEPS = 4                                # columns: the entry and four more dates up to the expiry


def pnl_grid(structure, spot, quotes, moves=PNL_MOVES, steps=PNL_STEPS):
    """the structure's profit or loss over price and date, as a multiple of the amount risked (the debit): rows are the
    spot moved by `moves` %, columns the sessions left from today to the expiry; each leg is priced by Black-Scholes at
    its own quoted IV, held flat (OptionStrat / Options Trading Toolbox / OptionScout's P&L grid), the expiry column
    is the plain payoff. 0 = break even, -1 = the whole debit lost"""
    from . import strip
    st = structure or {}
    T, calls = _n((quotes or {}).get("t")), (quotes or {}).get("calls") or []
    debit, spot = _n(st.get("debit")), _n(spot)
    legs = st.get("legs") or []
    if not T or T <= 0 or not spot or not debit or debit <= 0 or not legs:
        return nd("No priced structure to draw")
    iv = {}
    for side, k in legs:
        row = next((c for c in calls if isinstance(c, (list, tuple)) and len(c) == 4 and abs(c[0] - float(k)) < 1e-9), None)
        if row is None or not _n(row[3]) or row[3] <= 0:
            return nd("A leg has no quoted IV")
        iv[k] = float(row[3])
    sessions = T * 252.0
    cols = [{"left": int(round(sessions * (1.0 - j / steps)))} for j in range(steps + 1)]
    rows = []
    for m in moves:
        s = spot * (1.0 + m / 100.0)
        cells = []
        for j in range(steps + 1):
            t = T * (1.0 - j / steps)
            v = sum((1.0 if side == "buy" else -1.0) * (max(s - float(k), 0.0) if t <= 0 else strip.bs_call(s, float(k), t, iv[k]))
                    for side, k in legs)
            cells.append(round((v - debit) / debit + 0.0, 3))
        rows.append({"move": m, "cells": cells})
    return {"status": "ok", "risked": debit, "cols": cols, "rows": rows,
            "method": "Black-Scholes at each leg's quoted IV, held flat; the last column is the payoff at expiry"}


# ---- CX-sg-5 the empirical one-day and five-day move ------------------------------------------------------------------
SQRT252 = 15.874507866387544
EMP_MIN = 600                                # fewest sessions with a VIX close and five sessions after them
EMP_TARGET = 68                              # the band is the 68% quantile (one standard deviation's share)
BUCKETS = ("low", "mid", "high")
VIX_MAX_AGE = 5                              # a VIX close older than this many days stands for no session


def quantile(xs, q):
    """the nearest-rank quantile: the ceil(q n)-th smallest value; None for an empty list"""
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[max(0, min(len(xs) - 1, math.ceil(round(q * len(xs), 9)) - 1))]


def _vix_map(vix_doc, upto):
    ds, cl = (vix_doc or {}).get("dates") or [], (vix_doc or {}).get("close") or []
    return {d: float(c) for d, c in zip(ds, cl) if c is not None and d <= upto and _n(c)}


def _bucket(v, c1, c2):
    return "low" if v <= c1 else "mid" if v <= c2 else "high"


def _fit(rows):
    """rows [(vix, |1d| %, |5d| %)] -> (c1, c2, {bucket: (n, d1, d5)}) with terciles of the VIX over the rows"""
    vs = [r[0] for r in rows]
    c1, c2 = quantile(vs, 1 / 3), quantile(vs, 2 / 3)
    out = {}
    for b in BUCKETS:
        g = [r for r in rows if _bucket(r[0], c1, c2) == b]
        out[b] = (len(g), quantile([r[1] for r in g], EMP_TARGET / 100), quantile([r[2] for r in g], EMP_TARGET / 100))
    return c1, c2, out


def emp_move(spy_bars, vix_doc, as_of, holdout=252):
    """SpotGamma's "implied 1-day / 5-day move from decades of history, not a simple IV formula", from the desk's own
    history: the 68% quantile of SPY's absolute one- and five-session move, by the tercile of the VIX close at the start
    of the move, beside VIX / 15.87. The same fit with the last `holdout` sessions held out (and a five-session gap before
    them) is graded on those sessions: cover1_pct and cover5_pct, the share whose move stayed inside the band (68 if the
    band is right). Bars and VIX closes after as_of are never read"""
    upto = as_of if isinstance(as_of, str) else as_of.isoformat()
    bs = [b for b in spy_bars or () if isinstance(b, dict) and _n(b.get("c")) and cal._as_date(float(b["t"])).isoformat() <= upto]
    vm = _vix_map(vix_doc, upto)
    if not bs or not vm:
        return nd("No SPY history or no VIX closes")
    ds = [cal._as_date(float(b["t"])).isoformat() for b in bs]
    cs = [float(b["c"]) for b in bs]
    rows = []                                                # (t, vix, |1d|, |5d|) for every session with 5 after it
    for i in range(len(cs) - 5):
        v = vm.get(ds[i])
        if v is not None and cs[i] > 0:
            rows.append((i, v, abs(cs[i + 1] / cs[i] - 1) * 100.0, abs(cs[i + 5] / cs[i] - 1) * 100.0))
    if len(rows) < EMP_MIN:
        return nd(f"{len(rows)} sessions with a VIX close and five sessions after them; needs {EMP_MIN}")
    c1, c2, fit = _fit([r[1:] for r in rows])
    out = {"status": "ok", "as_of": ds[-1], "since": ds[rows[0][0]], "n": len(rows), "target_pct": EMP_TARGET,
           "buckets": [{"name": b, "lo": None if b == "low" else _r(c1 if b == "mid" else c2, 2),
                        "hi": None if b == "high" else _r(c1 if b == "low" else c2, 2), "n": fit[b][0],
                        "d1_pct": _r(fit[b][1], 2), "d5_pct": _r(fit[b][2], 2)} for b in BUCKETS],
           "method": f"The {EMP_TARGET}% quantile of SPY's absolute one- and five-session move by VIX tercile, "
                     f"{ds[rows[0][0]][:4]} to {ds[-1][:4]}"}
    v_now = None
    for k in range(len(ds) - 1, -1, -1):                     # the latest VIX close on or before the last bar, within days
        if ds[k] in vm:
            v_now = vm[ds[k]] if (cal._as_date(float(bs[-1]["t"])) - date.fromisoformat(ds[k])).days <= VIX_MAX_AGE else None
            break
    if v_now is not None:
        b = _bucket(v_now, c1, c2)
        out["today"] = {"vix": _r(v_now, 2), "bucket": b, "d1_pct": _r(fit[b][1], 2), "d5_pct": _r(fit[b][2], 2),
                        "vix_em_pct": _r(v_now / SQRT252, 2)}
    start = len(rows) - holdout
    if holdout and start >= EMP_MIN // 2:
        tr = [r[1:] for r in rows if r[0] < rows[start][0] - 5]
        ho = rows[start:]
        if len(tr) >= EMP_MIN // 2:
            h1, h2, hfit = _fit(tr)
            n1 = n5 = 0
            for _, v, d1, d5 in ho:
                b = _bucket(v, h1, h2)
                n1 += 1 if d1 <= hfit[b][1] + 1e-12 else 0
                n5 += 1 if d5 <= hfit[b][2] + 1e-12 else 0
            out["holdout"] = {"n": len(ho), "from": ds[ho[0][0]], "to": ds[ho[-1][0]], "target_pct": EMP_TARGET,
                              "cover1_pct": _r(100.0 * n1 / len(ho), 1), "cover5_pct": _r(100.0 * n5 / len(ho), 1)}
    return out


# ---- V-azrael-5 clock decay and the weekly range --------------------------------------------------------------------------
SESSION_MIN = 390
CLOCK = ((0, "09:30"), (120, "11:30"), (240, "13:30"), (330, "15:00"))


def em_decay(t1, t2):
    """The 15.87 Rule's clock decay: the change, in %, of the move still to come between two times that are t1 and t2
    minutes from the close: sqrt(t2 / t1) - 1 (11:30 to 13:30, 270 to 150 minutes: -25.5%)"""
    if not t1 or t1 <= 0 or t2 is None or t2 < 0:
        return None
    return round(100.0 * (math.sqrt(t2 / t1) - 1.0), 4)


def weekly_em(em):
    """the week's expected move in %: the day's times the square root of five sessions"""
    em = _n(em)
    return None if em is None else em * math.sqrt(5.0)


def move_clock(em, minute=None):
    """the share of the day's expected move still to come at each hour (EM x sqrt(minutes left / 390)) and the week's range
    (EM x sqrt 5). rows: {at, left_pct (of the day's move, in % of price), decay_pct (from the open)}; now: the same at
    the minute since the open"""
    em = _n(em)
    if em is None or em <= 0:
        return nd("No expected move")
    def row(m, at):
        left = SESSION_MIN - m
        return {"at": at, "left_pct": _r(em * math.sqrt(left / SESSION_MIN), 3), "decay_pct": _r(em_decay(SESSION_MIN, left), 2)}
    out = {"status": "ok", "em_pct": _r(em, 2), "week_pct": _r(weekly_em(em), 3), "rows": [row(m, at) for m, at in CLOCK]}
    if minute is not None and 0 <= minute <= SESSION_MIN:
        out["now"] = dict(row(int(minute), "now"), minute=int(minute))
    return out


# ---- FN-2 the straddle richness verdict (QuantData's Caliper, quantdata.md section 12, chunk @1,151,888) -------------------
CAL_FLOOR, CAL_K, CAL_DRAWS, CAL_SEED = 20, 6, 1000, 7
STRADDLE_K = math.sqrt(2.0 / math.pi)        # an at-the-money straddle costs about 0.8 x spot x sigma x sqrt(T)


def _midrank(xs, v):
    return (sum(1 for x in xs if x < v) + 0.5 * sum(1 for x in xs if x == v)) / len(xs)


def caliper(today, pool, outcomes=(), floor=CAL_FLOOR, k_floor=CAL_K, draws=CAL_DRAWS, seed=CAL_SEED):
    """today's straddle / spot against `pool`, the matched past values: f = its rank in the pool (ties at half) and a 5%
    to 95% band [lo, hi] from `draws` bootstrap resamples of the pool (seed 7). VERY RICH when f >= .85 and lo > .85; RICH
    f >= .70 and lo > .70; VERY CHEAP f <= .15 and hi < .15; CHEAP f <= .30 and hi < .30; else FAIR, leaning rich or cheap
    when f clears .70 or .30 but the band does not. A pool under 20 gives no verdict. A firm verdict is withheld unless at
    least 6 matured look-alikes (`outcomes`: [(straddle / spot, |close move| / expected move)], those above the pool's
    70th percentile for a rich verdict, below its 30th for a cheap one) back it; it reports how often they stayed inside
    the expected move and the median of that ratio"""
    xs = sorted(float(x) for x in pool or () if _n(x) is not None)
    today = _n(today)
    if today is None or len(xs) < floor:
        return nd(f"{len(xs)} matched past values; needs {floor}")
    f = _midrank(xs, today)
    rng = random.Random(seed)
    draw = sorted(_midrank(s, today) for s in ([xs[rng.randrange(len(xs))] for _ in xs] for _ in range(draws)))
    lo, hi = quantile(draw, 0.05), quantile(draw, 0.95)
    if f >= 0.85 and lo > 0.85:
        word = "VERY RICH"
    elif f >= 0.70 and lo > 0.70:
        word = "RICH"
    elif f <= 0.15 and hi < 0.15:
        word = "VERY CHEAP"
    elif f <= 0.30 and hi < 0.30:
        word = "CHEAP"
    else:
        word = "FAIR (leaning rich)" if f >= 0.70 else "FAIR (leaning cheap)" if f <= 0.30 else "FAIR"
    out = {"status": "ok", "verdict": word, "f": _r(f, 3), "lo": _r(lo, 3), "hi": _r(hi, 3), "n": len(xs)}
    if word in ("VERY RICH", "RICH", "VERY CHEAP", "CHEAP"):
        rich = word.endswith("RICH")
        cut = quantile(xs, 0.70 if rich else 0.30)
        sub = [r for e, r in outcomes or () if _n(e) is not None and _n(r) is not None and (e > cut if rich else e < cut)]
        if len(sub) < k_floor:
            return nd(f"{len(sub)} matured look-alikes; a {word.lower()} verdict needs {k_floor}")
        out.update(k=len(sub), inside_pct=_r(100.0 * sum(1 for r in sub if r < 1.0) / len(sub), 1),
                   median_ratio=_r(quantile(sub, 0.5), 2))
    return out


def straddle_block(iv_hist, spy_bars, as_of, horizon=21):
    """SPY's 30-day straddle / spot against its own stored history: each stored IV30 [[session, iv]] stands for a
    straddle of 0.8 x iv x sqrt(30 / 365) of the spot (the chain's quotes are not kept, so this is the IV30 form of the
    straddle, said in the method), matched on nothing but the name (no regime or read minute is stored). The outcome
    of a past reading is SPY's absolute move over the next `horizon` sessions against that expected move. No verdict
    under 20 stored sessions, and none for a firm word without 6 matured look-alikes"""
    upto = as_of if isinstance(as_of, str) else as_of.isoformat()
    ivs = sorted((str(e[0]), float(e[1])) for e in iv_hist or () if isinstance(e, (list, tuple)) and len(e) == 2
                 and _n(e[1]) and e[1] > 0 and str(e[0]) <= upto)
    if len(ivs) < 2:
        return nd(f"{len(ivs)} stored IV30 sessions; needs {CAL_FLOOR + 1}")
    k = STRADDLE_K * math.sqrt(30.0 / 365.0)
    close = {cal._as_date(float(b["t"])).isoformat(): float(b["c"]) for b in spy_bars or () if _n(b.get("c"))}
    days = sorted(d for d in close if d <= upto)
    pos = {d: i for i, d in enumerate(days)}
    today_d, today_iv = ivs[-1]
    pool, outcomes = [], []
    for d, v in ivs[:-1]:
        e = k * v
        pool.append(e)
        i = pos.get(d)
        if i is not None and i + horizon < len(days):
            outcomes.append((e, abs(close[days[i + horizon]] / close[d] - 1.0) / e))
    r = caliper(k * today_iv, pool, outcomes)
    if r["status"] != "ok":
        return r
    return dict(r, today_pct=_r(100.0 * k * today_iv, 2), as_of=today_d,
                method="30-day IV straddle (0.8 x IV30 x sqrt(30/365)) against every stored session; outcome: the next "
                       f"{horizon} sessions' absolute move against it")


# ---- FN-1 the intraday regime and its hold probability ------------------------------------------------------------------------
CLASSES = ("Grind", "Hostile", "Pin", "Transition")
READS = (15, 60, 120, 180, 240, 300)         # minutes after the open: 9:45, 10:30, 11:30, 12:30, 13:30, 14:30 ET
HORIZONS = (30, 60, 90, 120, "close")
TOD_SEED, TOD_DRAWS, TOD_LOW_N, TOD_WIDE = 7, 1000, 25, 0.30


def intraday_class(range_pct, net_pct, em, minute):
    """the desk's own four-state reading of the session so far (the vendor's classifier is server side): measured against
    the move funded by now (EM x sqrt(minute / 390)): Hostile (range over 1.2 x funded), Pin (range under 0.6 x and the net
    move from the prior close under 0.3 x), Grind (a one-way day: net at least 0.6 of the range and at least 0.5 x
    funded), else Transition. None before minute 15 or without an expected move. Constants fixed here, not fitted"""
    em, rng, net = _n(em), _n(range_pct), _n(net_pct)
    if em is None or em <= 0 or rng is None or net is None or minute is None or minute < READS[0]:
        return None
    f = em * math.sqrt(min(float(minute), SESSION_MIN) / SESSION_MIN)
    if rng >= 1.2 * f:
        return "Hostile"
    if rng <= 0.6 * f and abs(net) <= 0.3 * f:
        return "Pin"
    if rng > 0 and abs(net) >= 0.6 * rng and abs(net) >= 0.5 * f:
        return "Grind"
    return "Transition"


def hold_table(sessions):
    """sessions: [{"date", "at": {minute after the open: class}}] (5-minute marks, 390 = the close) -> {"sessions", "rows":
    {"<class>@<read minute>": {"<horizon>": {n, hold, lo, hi, low_sample}}}}: the share of sessions still in the same
    class 30, 60, 90 and 120 minutes later and at the close, with add-one smoothing over the four classes, a 90% band
    from a session-block bootstrap (1,000 draws, seed 7), and low_sample when n < 25 or the band is wider than 0.30"""
    counts = {}
    for s in sessions or ():
        at = s.get("at") or {}
        for r in READS:
            c0 = at.get(r)
            if c0 not in CLASSES:
                continue
            for h in HORIZONS:
                c1 = at.get(SESSION_MIN if h == "close" else r + h)
                if c1 in CLASSES and (h == "close" or r + h <= SESSION_MIN):
                    counts.setdefault((c0, r, str(h)), []).append(1 if c1 == c0 else 0)
    rows = {}
    for (c0, r, h), same in sorted(counts.items()):
        n = len(same)
        rng = random.Random(TOD_SEED)
        draw = sorted((sum(same[rng.randrange(n)] for _ in range(n)) + 1) / (n + len(CLASSES)) for _ in range(TOD_DRAWS))
        lo, hi = quantile(draw, 0.05), quantile(draw, 0.95)
        rows.setdefault(f"{c0}@{r}", {})[h] = {"n": n, "hold": _r((sum(same) + 1) / (n + len(CLASSES)), 4),
                                               "lo": _r(lo, 4), "hi": _r(hi, 4), "low_sample": bool(n < TOD_LOW_N or hi - lo > TOD_WIDE)}
    return {"sessions": len(sessions or ()), "rows": rows,
            "method": "Counted transitions, add-one smoothing, session-block bootstrap (1,000 draws, seed 7, 90% band)"}


def session_marks(bars5, prev_close, em):
    """one session's 5-minute bars (completed, from 09:30 ET) -> {minute after the open: class} at every mark from minute
    15 to the close (390), the range and net move measured from the prior close; {} for a part session (under 70 bars)
    or without an expected move"""
    em, pv = _n(em), _n(prev_close)
    if not bars5 or len(bars5) < 70 or not em or em <= 0 or not pv or pv <= 0:
        return {}
    open_t = float(bars5[0]["t"])
    hi, lo, out = None, None, {}
    for b in bars5:
        h, l = float(b["h"]), float(b["l"])
        hi, lo = (h if hi is None else max(hi, h)), (l if lo is None else min(lo, l))
        minute = int(round((float(b["t"]) + 300.0 - open_t) / 60.0))
        c = intraday_class((hi - lo) / pv * 100.0, abs(float(b["c"]) - pv) / pv * 100.0, em, minute)
        if c is not None and minute <= SESSION_MIN:
            out[minute] = c
    return out


def tod_sessions(bars5, daily_close, vix_doc):
    """[{"date", "at": session_marks}] for every session in the 5-minute bars that has a prior daily close and a VIX close
    on that prior day (the expected move is that VIX / 15.87)"""
    vm = _vix_map(vix_doc, "9999-12-31")
    days = {}
    for b in bars5 or ():
        days.setdefault(cal._as_date(float(b["t"])).isoformat(), []).append(b)
    closes = sorted(daily_close or {})
    out = []
    for d in sorted(days):
        prior = [x for x in closes if x < d]
        if not prior or prior[-1] not in vm:
            continue
        at = session_marks(days[d], daily_close[prior[-1]], vm[prior[-1]] / SQRT252)
        if at:
            out.append({"date": d, "at": at})
    return out


TOD_PATH = ("state", "terminal", "regime_tod.json")


def tod_table(root, bars5, daily_close, vix_doc, as_of):
    """(table, reason): the stored transition table when it was counted at as_of, else counted from the 5-minute bars (a
    list, or a function that returns it) and stored. (None, why) with no 5-minute bars or no complete session in them"""
    import json
    import os
    from ..util import write_json_atomic
    path = os.path.join(root, *TOD_PATH)
    try:
        with open(path) as f:
            hit = json.load(f)
        if hit.get("as_of") == as_of and isinstance(hit.get("table"), dict):
            return hit["table"], None
    except (OSError, ValueError):
        pass
    ses = tod_sessions(bars5() if callable(bars5) else bars5, daily_close, vix_doc)     # a callable: read the bars only on a miss
    if not ses:
        return None, "No complete session of 5-minute SPY bars in the cache"
    table = hold_table(ses)
    try:
        write_json_atomic(path, {"as_of": as_of, "table": table})
    except OSError:
        pass
    return table, None


def regime(range_pct, net_pct, em, minute, table):
    """the intraday regime panel: today's class from the session so far and, from the stored transition table, how often
    sessions in this class at this read minute were still in it later (None table: says so)"""
    cls = intraday_class(range_pct, net_pct, em, minute)
    if cls is None:
        return nd("The session is under 15 minutes old, or there is no expected move or range yet")
    rm = max(r for r in READS if r <= minute)
    out = {"status": "ok", "word": cls, "minute": int(minute), "read": rm}
    if not table or not isinstance(table.get("rows"), dict):
        out["hold"] = nd("No transition table stored yet: it is counted from SPY's 5-minute history")
        return out
    row = (table["rows"] or {}).get(f"{cls}@{rm}")
    if not row:
        out["hold"] = nd(f"No stored session read {cls} at minute {rm}")
        return out
    out["hold"] = {"status": "ok", "sessions": table.get("sessions"), "method": table.get("method"),
                   "rows": [dict(row[str(h)], minutes=str(h)) for h in HORIZONS if str(h) in row]}
    return out


# ---- the edition block --------------------------------------------------------------------------------------------------------
EXPRESS_KEYS = {"ev", "ev_ratio", "ev_n", "ev_win", "ev_rank", "ev_reason", "pnl"}     # strip.options_block's structures
_PLAIN = {"status", "reason"}
ALLOWED = {
    "": {"as_of", "emp", "clock", "zweig", "straddle", "regime"},
    "emp": _PLAIN | {"as_of", "since", "n", "target_pct", "buckets", "today", "holdout", "method"},
    "emp.buckets[]": {"name", "lo", "hi", "n", "d1_pct", "d5_pct"},
    "emp.today": {"vix", "bucket", "d1_pct", "d5_pct", "vix_em_pct"},
    "emp.holdout": {"n", "from", "to", "target_pct", "cover1_pct", "cover5_pct"},
    "clock": _PLAIN | {"em_pct", "week_pct", "rows", "now"},
    "clock.rows[]": {"at", "left_pct", "decay_pct"},
    "clock.now": {"at", "left_pct", "decay_pct", "minute"},
    "zweig": _PLAIN | {"word", "ema10", "fired", "since", "n", "as_of"},
    "straddle": _PLAIN | {"verdict", "f", "lo", "hi", "n", "k", "inside_pct", "median_ratio", "today_pct", "as_of", "method"},
    "regime": _PLAIN | {"word", "minute", "read", "hold"},
    "regime.hold": _PLAIN | {"sessions", "method", "rows"},
    "regime.hold.rows[]": {"minutes", "n", "hold", "lo", "hi", "low_sample"},
}
EXPRESS_ALLOWED = {
    "pnl": _PLAIN | {"risked", "cols", "rows", "method"},
    "pnl.cols[]": {"left"},
    "pnl.rows[]": {"move", "cells"},
}


def build(spy_bars, vix_doc, strip, zbt, iv_spy, table, today):
    """the edition's `vendor` block: the market-wide pieces of the package, each with its own status. strip is the
    edition's market strip (its expected move, session minute, range and SPY's move); zbt the roster read's Zweig state;
    iv_spy SPY's stored IV30 [[session, iv]]; table the stored regime transition table or None"""
    as_of = today if isinstance(today, str) else today.isoformat()
    strip = strip if isinstance(strip, dict) else {}
    mv, day, ag = (strip.get(k) if isinstance(strip.get(k), dict) else {} for k in ("move", "day", "agree"))
    em = mv.get("em_pct") if mv.get("status") == "ok" else None
    minute = mv.get("minute")
    out = {"as_of": as_of, "emp": emp_move(spy_bars, vix_doc, as_of), "clock": move_clock(em, minute),
           "zweig": zbt if isinstance(zbt, dict) else nd("No breadth run yet for this session: the roster read has to finish first"),
           "straddle": straddle_block(iv_spy, spy_bars, as_of)}
    if day.get("status") == "ok" and ag.get("status") == "ok" and em and minute:
        out["regime"] = regime(day.get("range_pct"), abs(ag.get("spy_pct") or 0.0), em, minute, table)
    else:
        out["regime"] = nd("The session has not opened, or there is no expected move yet")
    return out
