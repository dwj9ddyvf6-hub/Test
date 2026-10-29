"""The Fear-Day Buy List: the Best Setups picker on fear days (PICKER.md; scratchpad engine/EVIDENCE.md).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module, its params file (config/picker/fearday_params.json), the edition's `picker` block
            (desk/terminal/__init__.py merges ALLOWED under it) and the page's drawing of it (web/terminal/brief.js).
  Constraints  pure functions of closed daily bars up to `as_of` (truncating later bars never changes an answer);
            the feature formulas are the research's (xcheck/novel.py, xcheck/new10/new10.py), copied; no reward-to-risk
            and no win odds anywhere (owner/coordinator 2026-10-27: P x R:R ran opposite to realized R and the odds model
            was 16-26 points miscalibrated out of sample); no trailing stop, no profit cap (E1); no price or dollar-
            volume floor: liquidity is a label (owner, 2026-10-27).
  Outcome   on a fear day, the top UP names (buy lane), the top RESET names (watch lane) and the top names in the thin
            quintiles (micro/nano lane), each with features, why-lines, vetoes and a plan; on a calm day nothing and
            WAIT_TEXT.
  Proof     tests/test_picker_fearday.py (hand-built bars with known answers); the edition validates.
  Edges     reverse-split history is not kept by the desk (cache/corp_actions.json holds 14 days of held names): that
            veto reads no_data unless a caller passes splits. Every threshold is provisional until the study fills the
            params file.

Market state (SPY): fear = SPY return <= fear.spy_drop, or SPY under its 50-day, or a vol spike (SPY 20-day realized
vol above vol_spike_mult x its 252-day median; the VIX the same way when a VIX series is passed). Bull = SPY above a
200-day that is higher than 20 sessions before. State calm / fear_bull / fear_bear (fear when the 200-day is unknown).

Name states: UP = close > 200d, 50d > 200d, 50d > 50d ten sessions before. RESET = at least 35% under the 252-day high
and within 10% of the 252-day low. Tier = quintile of the 20-day median dollar volume across the day's names
(1 thinnest .. 5 most liquid), a label only.

Vetoes (the avoid-money study, scratchpad/xcheck/avoid/RESULTS.md; each a named function -> (fired, why)): the six
replicated warnings (fresh pump in nano, dead-cat bounce, close >= 1.6x the 50-day, new listing, a +25% day in 20
sessions, MFI >= 75 in nano) and three penalty-only signals (stretched, company-specific decline, repeat surges; and
repeat reverse splits, no_data without split history). Every fired signal is a score penalty; a name is dropped only at
drop_at (4) or more; with SPY under its 200-day the veto is off. The small-cap 20-day-loser veto is gone (it flipped
sign). bad print (a close/prior close above 3 or below 0.33, not on 3x volume, in the last 260 sessions) makes a name
no_data.

Features (higher = better after the weight's sign): UP F3, N1, N7, MOM126 (close / close 126 sessions before - 1);
RESET -F7, F6, -N5. Score = |weight|-weighted average of the features' percentile ranks within the state and day
(a missing feature is left out of that name's average), minus penalties.

Plan: buy at the next open, hold `hold` sessions (time exit), a disaster stop at stop_atr x ATR(14) under the close
(a level), size = equal risk: weight % = risk_pct / (20-day daily vol x sqrt(hold)), capped at max_weight_pct.
Capacity (information, never a filter): 5% of the 20-day median dollar volume. Cost: round trip = the Corwin-Schultz
spread (20-day mean, from highs and lows) + 2 x impact_k x daily vol x sqrt(size / 20-day median dollar volume)."""
import copy
import datetime as dt
import hashlib
import json
import math
import os

import numpy as np
import pandas as pd

from .. import calendar as cal
from ..util import ET

WAIT_TEXT = "No edge today — wait"
PARAMS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config",
                           "picker", "fearday_params.json")
LABELS = {"F3": "Pullback deeper than its own usual", "N1": "Pullback that is the market's, not the company's",
          "N7": "Gap-downs bought back (10 sessions)", "MOM126": "Six-month gain",
          "F7": "10-day return vs SPY", "F6": "Selling volume vs the month before",
          "N5": "Move after the fear day, net of beta"}
STATE_WORDS = {"calm": "Calm", "fear": "Fear day", "fear_bull": "Fear day in a bull market",
               "fear_bear": "Fear day in a falling market"}
VETO_WORDS = {"new_listing": "new listing", "spike_day": "A +25% day in 20 sessions",
              "pump_nano": "Fresh pump (nano)", "dead_cat": "Dead-cat bounce", "far_above_50d": "1.6x the 50-day",
              "mfi_nano": "Money flow 75+ (nano)", "stretched": "Stretched over the 50-day",
              "idio_decline": "Company-specific decline", "surge": "Repeat volume surges",
              "reverse_splits": "Repeat reverse splits"}
CARD = {"symbol", "lane", "rank", "tier", "tier_word", "state", "score", "close", "features", "why", "vetoes",
        "penalty", "plan", "context", "lens"}   # context: desk/terminal/pickcard.py adds it (its keys ride in the edition's ALLOWED);
                                        # lens: desk/picker/lens.py (the lens keys ride in the edition's ALLOWED)
PLAN = {"entry", "entry_day", "hold", "exit", "exit_by", "stop", "stop_atr", "stop_pct", "atr", "weight_pct",
        "risk_pct", "max_usd", "size_usd", "cost_pct", "spread_pct", "impact_pct", "trail", "target"}
# the public contract of the block (desk/terminal/__init__.py merges it under `picker`)
ALLOWED = {
    "": {"kind", "as_of", "state", "label", "text", "why", "buy", "watch", "small", "vetoed", "no_data", "n",
         "provisional"},
    "n": {"universe", "up", "reset", "vetoed", "no_data"},
    "vetoed[]": {"symbol", "reasons"},
    "no_data[]": {"symbol", "reason"},
    **{f"{lane}[]": CARD for lane in ("buy", "watch", "small")},
    **{f"{lane}[].plan": PLAN for lane in ("buy", "watch", "small")},
    **{f"{lane}[].features[]": {"key", "label", "value", "median", "pct", "z"} for lane in ("buy", "watch", "small")},
    **{f"{lane}[].vetoes[]": {"name", "status", "grade", "why"} for lane in ("buy", "watch", "small")},
}


def _merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


FIT_PATH = os.path.join(os.path.dirname(PARAMS_PATH), "fearday_fit.json")


def fit_hash(obj):
    """sha256 of a JSON-able object's canonical text (sorted keys, no spaces): the content hash the fit file carries"""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def load_params(path=PARAMS_PATH, fit_path=FIT_PATH):
    """the base parameters with the frozen fit laid over them (config/picker/fearday_fit.json: the values learned on
    discovery data, the holdout's verdict per group, a content hash over both). A fit file whose hash does not match its
    content is not applied: the base parameters stay and `fit_error` says why. `provisional_groups` lists the groups no
    holdout has confirmed; `provisional` is true while any remains"""
    with open(path, encoding="utf-8") as f:
        base = json.load(f)
    base["fit"] = None
    if fit_path and os.path.exists(fit_path):
        with open(fit_path, encoding="utf-8") as f:
            fit = json.load(f)
        body = {k: fit[k] for k in ("params", "status") if k in fit}
        if fit.get("content_sha256") == fit_hash(body) and fit.get("params_sha256") == fit_hash(fit.get("params")):
            base = _merge(base, fit["params"])
            done = {g for g, v in (fit.get("status") or {}).items() if v == "confirmed"}
            base["provisional_groups"] = [g for g in base.get("provisional_groups", ()) if g not in done]
            base["fit"] = {"content_sha256": fit["content_sha256"], "params_sha256": fit["params_sha256"],
                           "status": fit.get("status")}
        else:
            base["fit_error"] = "fit file hash mismatch: not applied"
    base["provisional"] = bool(base.get("provisional_groups"))
    return base


CONFIG = load_params()


def _day(b):
    return dt.datetime.fromtimestamp(float(b["t"]), ET).date().isoformat()


def _series(bars):
    df = pd.DataFrame([{"d": _day(b), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                        "c": float(b["c"]), "v": float(b.get("v") or 0.0)}
                       for b in bars or () if b.get("c") is not None])
    return df.drop_duplicates("d", keep="last").reset_index(drop=True) if len(df) else df


def _cut(bars, as_of):
    return [b for b in bars or () if b.get("c") is not None and _day(b) <= as_of]


# ---- market state ------------------------------------------------------------------------------------------------
def _spy(spy_bars):
    s = _series(spy_bars)
    return s.set_index("d")["c"] if len(s) else pd.Series(dtype=float)


def market_state(spy_bars, vix=None, as_of=None, params=None):
    """{"state", "fear", "bull", "why"} at as_of (default SPY's last session) from SPY's closes; vix
    {"dates", "close"} adds the VIX spike the same way"""
    p = params or CONFIG
    fp, bp = p["fear"], p["bull"]
    s = _spy(spy_bars)
    if as_of:
        s = s[s.index <= as_of]
    if len(s) < 2:
        return {"state": "calm", "fear": False, "bull": None, "why": ["no_spy"], "as_of": None}
    r = s.pct_change()
    why = []
    if r.iloc[-1] <= fp["spy_drop"]:
        why.append("spy_drop")
    ma = s.rolling(fp["below_ma"]).mean()
    if pd.notna(ma.iloc[-1]) and s.iloc[-1] < ma.iloc[-1]:
        why.append("below_50d")
    vol = r.rolling(fp["vol_window"]).std()
    med = vol.rolling(fp["vol_median_window"], min_periods=fp["vol_median_window"] // 2).median()
    if pd.notna(med.iloc[-1]) and vol.iloc[-1] > fp["vol_spike_mult"] * med.iloc[-1]:
        why.append("vol_spike")
    if vix and vix.get("dates"):
        vx = pd.Series(vix["close"], index=vix["dates"], dtype=float)
        vx = vx[vx.index <= s.index[-1]]
        vm = vx.rolling(fp["vol_median_window"], min_periods=fp["vol_median_window"] // 2).median().shift(1)
        if len(vx) and pd.notna(vm.iloc[-1]) and vx.iloc[-1] > fp["vol_spike_mult"] * vm.iloc[-1]:
            why.append("vix_spike")
    m200 = s.rolling(bp["ma"]).mean()
    then = m200.shift(bp["rising_lookback"])
    bull = None if pd.isna(then.iloc[-1]) else bool(s.iloc[-1] > m200.iloc[-1] and m200.iloc[-1] > then.iloc[-1])
    fear = bool(why)
    state = "calm" if not fear else ("fear" if bull is None else ("fear_bull" if bull else "fear_bear"))
    return {"state": state, "fear": fear, "bull": bull, "why": why, "as_of": s.index[-1]}


# ---- per-name frame (the research's formulas) ---------------------------------------------------------------------
def frame(bars, spy_bars, params=None):
    """a DataFrame over the name's sessions with its state and features; row i uses bars 0..i only"""
    return frame_df(_series(bars), _spy(spy_bars), params)


def frame_df(g, s, params=None):
    """frame() from the name's daily DataFrame g (d, o, h, l, c, v; one row per session, sorted) and SPY's closes s
    (a Series indexed by the ISO date): the fit (desk/picker/fit.py) calls it once per name over its whole history, and
    row i still uses sessions 0..i only"""
    p = params or CONFIG
    spyr = s.pct_change()
    fearday = (spyr <= p["fear"]["spy_drop"]) | (s < s.rolling(p["fear"]["below_ma"]).mean())  # novel.py's
    c, h, l, o, v = g.c, g.h, g.l, g.o, g.v
    r = c.pct_change()
    sp = g.d.map(spyr).astype(float)
    fd = g.d.map(fearday).fillna(False).astype(bool)
    cov = (r * sp).rolling(60).mean() - r.rolling(60).mean() * sp.rolling(60).mean()
    beta = cov / sp.rolling(60).var()
    up_p, rs_p = p["up"], p["reset"]
    m50 = c.rolling(up_p["ma_fast"]).mean()
    m200 = c.rolling(up_p["ma_slow"]).mean()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    up = (c > m200) & (m50 > m200) & (m50 > m50.shift(up_p["rising_lookback"]))
    hi252 = h.rolling(rs_p["window"]).max()
    lo252 = l.rolling(rs_p["window"]).min()
    reset = (c <= hi252 * (1 - rs_p["below_high"])) & (c <= lo252 * (1 + rs_p["near_low"]))
    f = pd.DataFrame({"d": g.d, "o": o, "h": h, "l": l, "c": c, "v": v, "r": r, "beta": beta, "m50": m50,
                      "m200": m200, "atr": atr, "fear": fd})
    f["state"] = np.where(up, "UP", np.where(reset, "RESET", ""))
    pb = (h.rolling(20).max() - c) / atr
    f["F3"] = (pb - pb.rolling(252).median()) / pb.rolling(252).std()
    sp5 = g.d.map(s.pct_change(5)).astype(float)
    r5 = c.pct_change(5)
    f["F4"] = (r5 - beta * sp5).abs() / r5.abs().replace(0, np.nan)
    dvol = v.where(r < 0, 0.0)
    f["F6"] = dvol.rolling(10).sum() / (dvol.shift(10).rolling(30).sum() / 3).replace(0, np.nan)
    f["F7"] = c.pct_change(10) - g.d.map(s.pct_change(10)).astype(float)
    f["N1"] = f["F3"] * (1 - f["F4"].clip(0, 1))
    fear2 = fd.shift(2).fillna(False).astype(bool)
    sp2 = g.d.map(s.pct_change(2)).astype(float)
    f["N5"] = (c.pct_change(2) - beta.shift(2) * sp2).where(fear2)
    f["N7"] = ((o < l.shift()) & (c > o)).astype(float).rolling(10).sum()
    f["MOM126"] = c / c.shift(126) - 1
    f["r5"], f["r20"] = r5, c.pct_change(20)
    f["vol20"] = r.rolling(20).std()
    f["dv20"] = (c * v).rolling(20).median()
    f["cs"] = corwin_schultz(h, l).rolling(20, min_periods=5).mean()
    return f


def corwin_schultz(h, l):
    """the Corwin-Schultz (2012) bid-ask spread estimate from two sessions' highs and lows, floored at 0"""
    k = 3 - 2 * math.sqrt(2)
    b = np.log(h / l) ** 2
    beta = b + b.shift(1)
    gamma = np.log(pd.concat([h, h.shift(1)], axis=1).max(axis=1) / pd.concat([l, l.shift(1)], axis=1).min(axis=1)) ** 2
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    return (2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))).clip(lower=0)


# ---- guards and vetoes: each (frame, i, ...) -> (True | False | None for no data, why) ---------------------------
def bad_print(fr, i, params=None):
    """a close/prior close above 3 or below 0.33 on volume not above 3x its prior 20-day median, in the last 260
    sessions (the avoid study's guard)"""
    bp = (params or CONFIG)["bad_print"]
    jump = fr["c"] / fr["c"].shift(1)
    vmed = fr["v"].shift(1).rolling(bp["vol_median"], min_periods=1).median()
    bad = ((jump > bp["up"]) | (jump < bp["down"])) & ~(fr["v"] > bp["vol_mult"] * vmed)
    return bool(bad.iloc[max(0, i - bp["window"] + 1):i + 1].any())


def _vp(params, name):
    return (params or CONFIG)["vetoes"][name]


def _nano(tier, params):
    return tier in _vp(params, "nano_tiers") or str(tier).lower() == "nano"


def _volx(fr, i, mult, med):
    m = fr["v"].shift(1).rolling(med, min_periods=10).median().iloc[i]
    return pd.notna(m) and m > 0 and fr["v"].iloc[i] >= mult * m


def veto_new_listing(fr, i, params=None):
    return (i + 1 < _vp(params, "new_listing")["sessions"]), "new listing"


def veto_spike_day(fr, i, params=None):
    vp = _vp(params, "spike_day")
    x = fr["r"].iloc[max(0, i - vp["window"] + 1):i + 1]
    return bool((x >= vp["day"]).any()), "a +25% day in the last 20 sessions"


def veto_pump_nano(fr, i, tier, params=None):
    vp = _vp(params, "pump_nano")
    if tier is None:
        return None, "no tier"
    r5 = fr["r5"].iloc[i]
    return bool(_nano(tier, params) and pd.notna(r5) and r5 >= vp["r5"] and
                _volx(fr, i, vp["vol_mult"], vp["vol_median"])), "a fresh pump in a nano name"


def veto_dead_cat(fr, i, params=None):
    vp = _vp(params, "dead_cat")
    if i < vp["high_window"]:
        return None, "too few sessions"
    c = fr["c"]
    hi = c.iloc[i - vp["high_window"] + 1:i + 1].max()
    r5 = c.iloc[i] / c.iloc[i - vp["bounce_days"]] - 1
    return bool(c.iloc[i] <= vp["of_high"] * hi and r5 >= vp["bounce"]), "a dead-cat bounce"


def veto_far_above_50d(fr, i, params=None):
    m50 = fr["m50"].iloc[i]
    if pd.isna(m50):
        return None, "no 50-day"
    return bool(fr["c"].iloc[i] >= _vp(params, "far_above_50d")["mult"] * m50), "close 1.6x the 50-day or more"


def mfi(fr, n=14):
    tp = (fr["h"] + fr["l"] + fr["c"]) / 3
    mf = tp * fr["v"]
    pos = mf.where(tp > tp.shift(1), 0.0).rolling(n).sum()
    neg = mf.where(tp < tp.shift(1), 0.0).rolling(n).sum()
    out = 100 - 100 / (1 + pos / neg.replace(0, np.nan))
    return out.where(~((neg == 0) & (pos > 0)), 100.0)


def veto_mfi_nano(fr, i, tier, params=None):
    vp = _vp(params, "mfi_nano")
    if tier is None:
        return None, "no tier"
    m = mfi(fr.iloc[:i + 1], vp["n"]).iloc[-1]
    return bool(_nano(tier, params) and pd.notna(m) and m >= vp["mfi"]), "money flow 75 or more in a nano name"


def veto_stretched(fr, i, params=None):
    m50 = fr["m50"].iloc[i]
    if pd.isna(m50):
        return None, "no 50-day"
    return bool(fr["c"].iloc[i] / m50 - 1 >= _vp(params, "stretched")["above_50d"]), "stretched over the 50-day"


def veto_idio_decline(fr, i, params=None):
    vp = _vp(params, "idio_decline")
    f4, r5 = fr["F4"].iloc[i], fr["r5"].iloc[i]
    if pd.isna(f4) or pd.isna(r5):
        return None, "no beta"
    return bool(r5 <= vp["r5"] and f4 >= vp["share"]), "the 5-day decline is mostly company-specific"


def veto_surge(fr, i, params=None):
    vp = _vp(params, "surge")
    vmed = fr["v"].shift(1).rolling(vp["vol_median"], min_periods=10).median()
    hit = (fr["r"].abs() >= vp["move"]) & (fr["v"] >= vp["vol_mult"] * vmed)
    return bool(hit.iloc[max(0, i - vp["window"] + 1):i + 1].sum() >= vp["days"]), "repeat volume surges"


def veto_reverse_splits(fr, i, splits, params=None):
    vp = _vp(params, "reverse_splits")
    if splits is None:
        return None, "no split history in the desk"
    today = dt.date.fromisoformat(fr["d"].iloc[i])
    since = (today - dt.timedelta(days=int(365.25 * vp["years"]))).isoformat()
    n = sum(1 for x in splits if since <= x["ex"] <= today.isoformat() and float(x["num"]) < float(x["den"]))
    return n >= vp["count"], "repeat reverse splits"


def warnings(fr, i, tier, splits=None, params=None):
    """{name: (fired, why)} for every warning and penalty signal"""
    return {"new_listing": veto_new_listing(fr, i, params), "spike_day": veto_spike_day(fr, i, params),
            "pump_nano": veto_pump_nano(fr, i, tier, params), "dead_cat": veto_dead_cat(fr, i, params),
            "far_above_50d": veto_far_above_50d(fr, i, params), "mfi_nano": veto_mfi_nano(fr, i, tier, params),
            "stretched": veto_stretched(fr, i, params), "idio_decline": veto_idio_decline(fr, i, params),
            "surge": veto_surge(fr, i, params), "reverse_splits": veto_reverse_splits(fr, i, splits, params)}


def judge(res, spy_ok, params=None):
    """-> (drop, penalty, marks): every fired signal counts toward drop_at and costs its penalty; with SPY under its
    200-day the veto is off (the edge reverses there: the avoid study's M6) and nothing is dropped or penalised"""
    vp = (params or CONFIG)["vetoes"]
    marks, fired, pen = [], [], 0.0
    for name, (f, why) in res.items():
        kind = "warning" if name in vp["warnings"] else "penalty"
        status = "no_data" if f is None else ("pass" if not f else ("off" if not spy_ok else kind))
        if f and spy_ok:
            fired.append(name)
            pen += vp["warning_penalty"] if kind == "warning" else vp["penalty"]
        marks.append({"name": name, "status": status, "grade": kind, "why": why})
    drop = len(fired) >= vp["drop_at"]
    return (fired if drop else []), (0.0 if drop else pen), marks


# ---- the list ----------------------------------------------------------------------------------------------------
def _f(x, nd=4):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), nd)


def plan_for(p, lane=None, tier=None):
    """the plan parameters of one card: the base plan, then the fitted overrides of its lane ("lane:buy") and its tier
    group ("tier:liquid"), where the data supported them (config plan_by)"""
    pp = dict(p["plan"])
    by = p.get("plan_by") or {}
    groups = p["tiers"].get("groups") or {}
    keys = ([f"lane:{lane}"] if lane else []) + [f"tier:{g}" for g, ts in groups.items() if tier in ts]
    for k in keys:
        pp.update(by.get(k) or {})
    return pp


def _plan(fr, i, as_of, p, lane=None, tier=None):
    pp = plan_for(p, lane, tier)
    c, atr, vol, dv = (float(fr[k].iloc[i]) for k in ("c", "atr", "vol20", "dv20"))
    stop = c - pp["stop_atr"] * atr if pp.get("stop_atr") is not None else None
    w = min(pp["risk_pct"] / (vol * math.sqrt(pp["hold"])), pp["max_weight_pct"]) if vol > 0 else 0.0
    size = w / 100 * pp["book_usd"]
    spread = float(fr["cs"].iloc[i]) if pd.notna(fr["cs"].iloc[i]) else 0.0
    impact = pp["impact_k"] * vol * math.sqrt(size / dv) if dv > 0 else None
    return {"entry": "next open", "entry_day": cal.next_trading_day(as_of).isoformat(), "hold": pp["hold"],
            "exit": "time", "exit_by": cal.next_trading_day(as_of, pp["hold"]).isoformat(),
            "stop": None if stop is None else round(stop, 2), "stop_atr": pp.get("stop_atr"),
            "stop_pct": None if stop is None else _f((stop / c - 1) * 100, 2), "atr": _f(atr),
            "weight_pct": round(w, 2), "risk_pct": pp["risk_pct"], "max_usd": round(pp["adv_cap"] * dv),
            "size_usd": round(size), "cost_pct": _f((spread + 2 * impact) * 100 if impact is not None else None, 3),
            "spread_pct": _f(spread * 100, 3), "impact_pct": _f(impact * 100 if impact is not None else None, 3),
            "trail": None, "target": None}


def _standing(col, sym, weight, med, sd):
    """where the name stands on one factor today, in the factor's favourable direction (the weight's sign): pct = the
    share of today's candidates in this state it beats, z = its gap to the median in spreads of those candidates (None
    when they do not differ). Both are of today's names only, never a probability"""
    sg = 1.0 if weight > 0 else -1.0
    v, xs = sg * col[sym], (sg * col).dropna()
    z = sg * (col[sym] - med) / sd if sd and math.isfinite(sd) else None
    return {"pct": int(round(100.0 * float((xs < v).sum()) / len(xs))) if len(xs) else None, "z": _f(z, 2)}


def gather(universe, spy, as_of, out, splits=None, params=None):
    """the names that can be on the list at as_of, fear day or not: -> ({"UP": [...], "RESET": [...]}, tiers). Each
    candidate {"sym", "fr", "i", "tier", "marks", "pen"}: a valid, non-dropped name in that state. `out` (the block being
    built, or a scratch dict with the lists vetoed and no_data and the count n) receives the vetoed, the no_data and the
    universe count. The forward tests' random-name control draws from exactly this pool (desk/forward/ft05.py)"""
    p = params or CONFIG
    out.setdefault("vetoed", [])
    out.setdefault("no_data", [])
    out.setdefault("n", {})
    rows = []
    for sym in sorted(universe):
        bars = _cut(universe[sym], as_of)
        if not bars or _day(bars[-1]) != as_of:
            out["no_data"].append({"symbol": sym, "reason": "no bar for the session"})
            continue
        fr = frame(bars, spy, p)
        i = len(fr) - 1
        if bad_print(fr, i, p):
            out["no_data"].append({"symbol": sym, "reason": "bad print"})
            continue
        rows.append((sym, fr, i))
    # tiers: quintiles of the 20-day median dollar volume across the day's names (a label)
    dv = pd.Series({s: fr["dv20"].iloc[i] for s, fr, i in rows}, dtype=float).dropna()
    q = p["tiers"]["quintiles"]
    tiers = {s: int(min(q, math.ceil(x * q))) for s, x in dv.rank(pct=True).items()}
    out["n"]["universe"] = len(rows)
    lane = p["tiers"]["small_lane"]
    spy_s = _spy(spy)
    ma = spy_s.rolling(p["vetoes"]["off_below_spy_ma"]).mean()
    spy_ok = not (pd.notna(ma.iloc[-1]) and spy_s.iloc[-1] < ma.iloc[-1])
    cands = {"UP": [], "RESET": []}
    for sym, fr, i in rows:
        tier = tiers.get(sym)
        res = warnings(fr, i, tier, (splits or {}).get(sym) if splits is not None else None, p)
        hard, pen, marks = judge(res, spy_ok, p)
        if hard:
            out["vetoed"].append({"symbol": sym, "reasons": [VETO_WORDS[h] for h in hard]})
            continue
        st = fr["state"].iloc[i]
        if st in cands:
            cands[st].append({"sym": sym, "fr": fr, "i": i, "tier": tier, "marks": marks, "pen": pen})
    out["n"].update(up=len(cands["UP"]), reset=len(cands["RESET"]), vetoed=len(out["vetoed"]),
                    no_data=len(out["no_data"]))
    return cands, tiers


def pick(universe, spy_bars, as_of=None, vix=None, splits=None, params=None, keep=None):
    """-> the edition's `picker` block. universe {sym: daily bars}; splits {sym: [{"ex","num","den"}]} or None. keep: a dict
    that receives the day's candidates ("cands", "tiers": gather()'s) so a caller that wants the pool does not gather twice"""
    p = params or CONFIG
    spy = _cut(spy_bars, as_of) if as_of else list(spy_bars or ())
    m = market_state(spy, vix=vix, params=p)
    as_of = m["as_of"]
    out = {"kind": "fearday", "as_of": as_of, "state": m["state"], "label": STATE_WORDS[m["state"]],
           "text": WAIT_TEXT if not m["fear"] else STATE_WORDS[m["state"]], "why": m["why"], "buy": [], "watch": [],
           "small": [], "vetoed": [], "no_data": [], "n": {"universe": 0, "up": 0, "reset": 0, "vetoed": 0,
                                                            "no_data": 0},
           "provisional": bool(p.get("provisional"))}
    if not m["fear"] or as_of is None:
        return out
    cands, tiers = gather(universe, spy, as_of, out, splits, p)
    if keep is not None:
        keep.update(cands=cands, tiers=tiers)
    lane = p["tiers"]["small_lane"]
    small = []
    for st, lane_name in (("UP", "buy"), ("RESET", "watch")):
        cs = cands[st]
        if not cs:
            continue
        w = p["weights"][st]
        vals = pd.DataFrame({k: [float(x["fr"][k].iloc[x["i"]]) for x in cs] for k in w}, index=[x["sym"] for x in cs])
        ranks = pd.DataFrame({k: (np.sign(wk) * vals[k]).rank(pct=True) for k, wk in w.items()})
        absw = pd.Series({k: abs(wk) for k, wk in w.items()})
        score = (ranks * absw).sum(axis=1, min_count=1) / ranks.notna().mul(absw).sum(axis=1).replace(0, np.nan)
        med = vals.median()
        sd = vals.std(ddof=0)
        cards = []
        for x in cs:
            sc = score.get(x["sym"])
            if pd.isna(sc):
                continue
            fr, i = x["fr"], x["i"]
            feats = [{"key": k, "label": LABELS[k], "value": _f(vals.at[x["sym"], k]), "median": _f(med[k]),
                      **_standing(vals[k], x["sym"], w[k], med[k], sd[k])} for k in w]
            top = sorted((k for k in w if pd.notna(ranks.at[x["sym"], k])), key=lambda k: -ranks.at[x["sym"], k])[:2]
            why = [f"{LABELS[k]}: {vals.at[x['sym'], k]:.2f} vs today's median {med[k]:.2f}" +
                   (" (lower is better)" if w[k] < 0 else "") for k in top]
            cards.append({"symbol": x["sym"], "lane": lane_name, "tier": x["tier"],
                          "tier_word": p["tiers"]["words"].get(str(x["tier"])) if x["tier"] else None, "state": st,
                          "score": round(float(sc) - x["pen"], 4), "close": _f(fr["c"].iloc[i]), "features": feats,
                          "why": why, "vetoes": x["marks"], "penalty": round(x["pen"], 4),
                          "plan": _plan(fr, i, as_of, p, "small" if x["tier"] in lane else lane_name, x["tier"]), "_dv": float(fr["dv20"].iloc[i] or 0)})
        cards.sort(key=lambda c_: (-c_["score"], -c_["_dv"], c_["symbol"]))
        thin = [c_ for c_ in cards if c_["tier"] in lane]
        main = [c_ for c_ in cards if c_["tier"] not in lane]
        out[lane_name] = main[:p["top_n"]]
        small += thin
    small.sort(key=lambda c_: (-c_["score"], -c_["_dv"], c_["symbol"]))
    out["small"] = [dict(c_, lane="small") for c_ in small[:p["top_n"]]]
    for lane_name in ("buy", "watch", "small"):
        for k, c_ in enumerate(out[lane_name], 1):
            c_.pop("_dv", None)
            c_["rank"] = k
    return out
