"""REA gap-build forecasters, work package WP2 (rea_matrix rows, 2026-10-27): the vendor forecaster rows the first vendor
batch (adapters/vendors.py) left deferred. DISCOVERY-ONLY: each is a hypothesis registered for the Factory search and
holdout to grade; none is promoted, none carries an edge claim. Daily closed bars; clean-room from the teardown cited
on each row (scratchpad vendors/*.md, study/fw.md); where a constant is unpublished the desk's choice is named here.

Per-name (a value per bar of one name; 0/1 or signed event flags are 0 on a quiet bar, never NaN after warm-up)
  ChartsLector (lector-systems.md §3; CL4, CL5)
    lector.2b         2B Breakout Confirm: close >= EMA10 >= EMA20 >= SMA50 and close >= the PRIOR 20-bar high (the
                      exclusive reading: bars t-20..t-1, today left out); 0/1
    lector.naive20    the kill-test control: close > the prior 20-bar high; 0/1
    lector.xatr_2c    xATR = ((c - SMA50) / SMA50) / (ATR14 / c) in tier 2C (7 <= xATR < 11), carry; 0/1
    lector.xatr_2d    tier 2D (xATR >= 11), exhausted: an avoid arm (sign -1); 0/1
    lector.xatr_4c    tier 4C (xATR < -7): an avoid arm (sign -1); 0/1
  Linda Raschke (linda_raschke.md §3; LR1, LR3, LR4)
    rsc.pf3           PF3 on daily bars: M = C - C[t-2], F = SMA3 - SMA10, S = SMA16(F); +1 when dM, dF and dS are all
                      > 1e-9, -1 when all < -1e-9, else 0 (a steady ramp is 0; the Gaussian null aligns 24.22%)
    rsc.rotation      rotation flag: |S| / ATR14(Wilder) <= 0.15 and >= 2 sign flips among the last 6 slopes of F; 0/1
    rsc.holygrail     Holy Grail: ADX14 > 30 and the trend side (+DI > -DI) retraces to EMA20 (low <= EMA20 for the
                      long; the short is the desk's mirror); +1 / -1 / 0. The book's buy-stop above the prior high is
                      the next bar's fill, not part of the closed-bar signal
    rsc.turtle        Turtle Soup, failed 20-day break: the low breaks the lowest low of the prior 20 bars, that low is
                      >= 4 sessions old, and the close is back above it (long, +1); the high mirror is -1. The book's
                      "buy-stop 5-10 ticks above" has no daily-bar meaning: the close back above the old low is the
                      desk's choice
  LuxAlgo structure (luxalgo.md §3 SPEC; C15 C16 C17 C18 C21 C48), swing length 5 (the internal-structure default)
    lux.bos           break of structure: close beyond the last confirmed swing in the trend's direction: +1 / -1 / 0
    lux.choch         change of character: the first break against the trend: +1 / -1 / 0
    lux.fvg           three-candle fair value gap (bull: low[t] > high[t-2]; bear: high[t] < low[t-2]); the net of open
                      zones, (bull - bear) / (bull + bear), a zone open until a wick touches it (C17 "touch") or
                      closes through it (inverse), 50 sessions at most (desk choice); in [-1, 1]
    lux.fvg_atr       the same with a minimum gap of 0.5 ATR14 (C48)
    lux.fvg_half      mitigation at the 50% line (C17), lux.fvg_full at the far edge
    lux.fvg_dist      signed distance in ATR14 from the close to the nearest open zone's midpoint, clipped to +-10;
                      NaN with no open zone (abstains)
    lux.ifvg          inverse FVG: a close through the far side of an open zone (a bull gap closed under: -1; a bear gap
                      closed over: +1)
    lux.bos_fvg       the SPEC's long candidate: a bull FVG (0.5 ATR minimum) formed on or after the last bullish break
                      is mitigated by a wick while the trend is up and the close holds the zone: +1; mirror -1
    lux.ob            order blocks (C18): the last opposite candle (within 10 bars) before a displacement candle with a
                      body >= 1.5 ATR14; the zone is that candle's range, volume graded by v / mean(v, 20) (capped at
                      3), dead on a close through, 50 sessions at most; the readout (graded bull - bear) / (bull + bear)
                      is the desk's
  EzAlgo (ezalgo.md; C74; no sweep, gap size or rating published: every threshold is the desk's)
    ez.sweepgap       an ict.c2 sweep followed on the same bar or within 3 bars by an inverse FVG in the sweep's
                      direction (a bull sweep + a bear gap closed over): +1; mirror -1
  AlgoPoint (algopoint.md §3; C42)
    ap.stadapt        SuperTrend whose multiplier follows ap.regime S by linear interpolation through (S 0 -> 5.0,
                      0.4 -> 4.1, 0.7 -> 2.9, 1.0 -> 2.0); Pine-style final bands, flip on close; ATR is the 14-day
                      mean true range (the period is unpublished); the trend, +1 / -1
    ap.st3            the control arm: the same with a fixed 3.0 multiplier
  MarketCipher (marketcipher.md §3 SPEC; C54)
    mc.wt             WaveTrend: ap = hlc3, esa = EMA(ap, 10), d = EMA(|ap - esa|, 10), ci = (ap - esa) / (0.015 d),
                      WT1 = EMA(ci, 21), WT2 = SMA(WT1, 4); +1 when WT1 crosses over WT2 at WT1 <= -53, -1 when it
                      crosses under at WT1 >= 53 (the SPEC's desk levels), else 0
  Bybit (bybit-apk.md §5; V-bybit-2): the no-move band
    byb.atr_band5/20  the share of the last 40 COMPLETED outcomes (at least 20) in which the path from a close stayed
                      inside close +- 2 ATR14 (every high and low) for the next 5 / 20 sessions: an empirical P(no
                      move). The multiplier 2 and the 40-outcome window are the desk's; the label (band_stay) is below
  GridScalper EA (gridscalperea.md §3, DeepSeekAI.mqh:457-505; V-gs-1), closed bars, no news term
    gs.five           buy = 0.3[RSI14 < 30] + 0.2[MACD > signal] + 0.3[EMA20 > EMA50 > EMA200] + 0.1[c > EMA200]; sell
                      the mirror (the MACD and EMA200 terms are 'else'); the score is buy - sell, in [-1, 1]
    gs.five_sig       the EA's rule: +1 when buy > sell and buy > 0.4, -1 when sell > buy and sell > 0.4, else 0
    gs.ema, gs.rsi    the two arms: EMA alignment alone (+1 / -1 / 0), RSI alone ([RSI < 30] - [RSI > 70])
  Zerith MACD grid (zerith-macd-grid.md §3; V-zerith-1), the daily proxy of the H4 gate
    zer.macd200       a MACD(12,26,9) main-over-signal cross at this close while the close is over EMA200: +1; the
                      mirror under EMA200: -1
  QuantCharts QANTRADING (quantcharts.md §3; V-qc-2)
    qc.locstreak      (p1 + p2) / 2: p1 the name's own frequency of an up next day from the same location bin (the close's
                      place in its 20-day close range, five bins), p2 from the same signed streak bin (clipped to +-5),
                      each from outcomes known at the decision (at least 30 in the bin). The encoding is the desk's
                      (the vendor's is unpublished); abstains until both bins have 30 outcomes
  GEXRADAR (gexradar.md; A97)
    gex.entropy20     diversity = H / log2(20): the Shannon entropy of the last 20 daily returns in 20 equal bins over
                      their own min..max (the bin range is unpublished: the desk's)

Index context (one value per session, the same for every name; family "index", scored in the search's market lane).
Extra inputs ride in the market dict as {session: close} or bars arrays: qqq iwm rsp hyg lqd tlt xly xlp bnd. A forecaster
whose ETFs are absent abstains; none is ever a constant.
    tjr.smt_qqq/iwm   SMT divergence (tjr.md §5; C83): SPY and the fund, a new 20-day closing extreme (against the prior
                      20 closes) in one and not the other: +1 at the lows (bullish), -1 at the highs (bearish)
    oft3r.macro5      the macro pillar (study/fw.md: scripts/macro_pillar.py): five ratio trends RSP/SPY .25, HYG/LQD
                      .15, IWM/SPY .15, SPY/TLT .15, XLY/XLP .10, each 0.5 sign(r - SMA200) + 0.5 sign(SMA200 - its
                      value 20 sessions ago), the weighted mean renormalised over the components present. The 10Y-2Y
                      leg is left out (FRED is barred in a fitted model)
    oft3r.macro5_rv   the same series against realized volatility (sign -1)
    composer.dualmom  the homepage symphony (composer.md): hold SPY while its 20-day return > 2%, else BND: +1 / -1

Labels used by tests (pure, read bars i+1 onward only): band_stay (the Bybit label) and straddle (V-gs-3).

Deferred (REGISTRY.md): tv.rating (the 26-vote rule table lives in the open-source Pine library, not in the teardown),
the factor zoo, the double / opening-gap FVG variants, the inflationary flag, the V-gs-3 forecaster."""
import numpy as np
import pandas as pd
from scipy.signal import lfilter

from .. import Forecaster, Laws, Ledger
from .. import data as D
from . import vendors as V
from ._common import atr, ema, lag, market, market_series, ret, roll, rsi, true_range, wilder, wrap

INF = float("inf")
UP = ("up_excess_5", "up_excess_20")
UP20 = ("up_excess_20",)
NM = ("no_move_5", "no_move_20")
ETFS = ("qqq", "iwm", "rsp", "hyg", "lqd", "tlt", "xly", "xlp", "bnd")
PATHS = {"fn": "desk.forecast.adapters.vendors2"}

# id: (sign, bounds, warmup, abstains, targets, kind, family, contexts, source, ledger extras)
_N = "all"
SPEC = {
    "lector.2b": (1, (0.0, 1.0), 49, False, UP20, "rule", "lector", _N, "lector-systems.md §3 (CL4)",
                  {"decisive_test": "beats lector.naive20 on up_excess_20 after BH and the 2023+ holdout"}),
    "lector.naive20": (1, (0.0, 1.0), 20, False, UP20, "rule", "lector", _N, "lector-systems.md §5 (CL4 control)", {}),
    "lector.xatr_2c": (1, (0.0, 1.0), 49, False, UP20, "rule", "lector", _N, "lector-systems.md §3 (CL5)", {}),
    "lector.xatr_2d": (-1, (0.0, 1.0), 49, False, UP20, "rule", "lector", _N, "lector-systems.md §3 (CL5)",
                       {"holdable": "veto (an avoid gate)"}),
    "lector.xatr_4c": (-1, (0.0, 1.0), 49, False, UP20, "rule", "lector", _N, "lector-systems.md §3 (CL5)",
                       {"holdable": "veto (an avoid gate)"}),
    "rsc.pf3": (1, (-1.0, 1.0), 25, False, UP, "score", "raschke", _N, "linda_raschke.md §3 (LR1)",
                {"speed_decay": "Raschke's ~2.5-day holding tendency (machine transcription only)"}),
    "rsc.rotation": (1, (0.0, 1.0), 40, False, NM, "rule", "raschke", _N, "linda_raschke.md §3 (LR3)", {}),
    "rsc.holygrail": (1, (-1.0, 1.0), 28, False, UP, "score", "raschke", _N, "linda_raschke.md §3 (LR4, AIQ 1997)", {}),
    "rsc.turtle": (1, (-1.0, 1.0), 20, False, UP, "score", "raschke", _N, "linda_raschke.md §3 (LR4, TradingMarkets 2003)",
                   {}),
    "lux.bos": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 SPEC (C15)", {}),
    "lux.choch": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 SPEC (C15)", {}),
    "lux.fvg": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 SPEC (C16, C17 touch)", {}),
    "lux.fvg_atr": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 (C16, C48 0.5 ATR minimum)", {}),
    "lux.fvg_half": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 (C17 50% mitigation)", {}),
    "lux.fvg_full": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 (C17 full mitigation)", {}),
    "lux.fvg_dist": (1, (-10.0, 10.0), 20, True, UP, "score", "luxalgo", _N, "luxalgo.md §3 (C17 distance feature)", {}),
    "lux.ifvg": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 (C21 inverse FVG)", {}),
    "lux.bos_fvg": (1, (-1.0, 1.0), 20, False, UP, "score", "luxalgo", _N, "luxalgo.md §3 SPEC (C15, C16)", {}),
    "lux.ob": (1, (-1.0, 1.0), 33, False, UP, "score", "luxalgo", _N, "quantumalgo.md / luxalgo.md (C18); readout the desk's",
               {}),
    "ez.sweepgap": (1, (-1.0, 1.0), 20, False, UP, "score", "ezalgo", _N, "ezalgo.md §3 (C74); thresholds the desk's", {}),
    "ap.stadapt": (1, (-1.0, 1.0), 64, False, UP, "score", "algopoint", _N, "algopoint.md §3 (C42)",
                   {"decisive_test": "beats ap.st3 (fixed 3.0x) in the same search run"}),
    "ap.st3": (1, (-1.0, 1.0), 14, False, UP, "score", "algopoint", _N, "algopoint.md §3 (C42 control arm)", {}),
    "mc.wt": (1, (-1.0, 1.0), 40, False, UP, "score", "marketcipher", _N, "marketcipher.md §3 SPEC (C54)", {}),
    "byb.atr_band5": (1, (0.0, 1.0), 37, False, ("no_move_5",), "score", "bybit", _N, "bybit-apk.md §5 (V-bybit-2)", {}),
    "byb.atr_band20": (1, (0.0, 1.0), 52, False, ("no_move_20",), "score", "bybit", _N, "bybit-apk.md §5 (V-bybit-2)", {}),
    "gs.five": (1, (-1.0, 1.0), 200, False, UP[:1], "score", "gridscalper", _N, "gridscalperea.md §3 (V-gs-1)", {}),
    "gs.five_sig": (1, (-1.0, 1.0), 200, False, UP[:1], "score", "gridscalper", _N, "gridscalperea.md §3 (V-gs-1)", {}),
    "gs.ema": (1, (-1.0, 1.0), 199, False, UP[:1], "score", "gridscalper", _N, "gridscalperea.md §5 (V-gs-1 arm)", {}),
    "gs.rsi": (1, (-1.0, 1.0), 14, False, UP[:1], "score", "gridscalper", _N, "gridscalperea.md §5 (V-gs-1 arm)", {}),
    "zer.macd200": (1, (-1.0, 1.0), 200, False, UP[:1], "score", "zerith", _N, "zerith-macd-grid.md §3 (V-zerith-1)", {}),
    "qc.locstreak": (1, (0.0, 1.0), 0, True, UP[:1], "score", "quantcharts", _N, "quantcharts.md §3, §5 (V-qc-2)", {}),
    "gex.entropy20": (1, (0.0, 1.0), 20, False, ("realized_vol_20",), "score", "gexradar", _N, "gexradar.md (A97)", {}),
}
MKT_SPEC = {   # market-lane context forecasters
    "tjr.smt_qqq": (1, (-1.0, 1.0), ("spy_ret_5", "spy_ret_20"), ("SPY", "QQQ"), "tjr.md §5 (C83)"),
    "tjr.smt_iwm": (1, (-1.0, 1.0), ("spy_ret_5", "spy_ret_20"), ("SPY", "IWM"), "tjr.md §5 (C83)"),
    "oft3r.macro5": (1, (-1.0, 1.0), ("spy_ret_20", "spy_ret_60"), ("SPY", "RSP", "HYG", "LQD", "IWM", "TLT", "XLY", "XLP"),
                     "study/fw.md macro_pillar (V-oft3r-2)"),
    "oft3r.macro5_rv": (-1, (-1.0, 1.0), ("spy_rv_20",), ("SPY", "RSP", "HYG", "LQD", "IWM", "TLT", "XLY", "XLP"),
                        "study/fw.md macro_pillar (V-oft3r-2)"),
    "composer.dualmom": (1, (-1.0, 1.0), ("spy_ret_20", "rel_spy_bnd_20"), ("SPY",), "composer.md (C116)"),
}

NOTE = ("DISCOVERY-ONLY (REA gap build WP2): a hypothesis for the Factory search and the 2023+ holdout to grade; "
        "no edge is claimed and nothing is promoted")


def _ledger(extra):
    kw = dict(payer="unknown (vendor claim unverified)", speed_decay="vendor horizon 1-20 sessions",
              decisive_test="BH over the run + walk-forward + same-sign 2023+ holdout, net of costs")
    kw.update(extra)
    return Ledger(**kw)


FORECASTERS = tuple(
    Forecaster(id=k, version="rea-wp2-1", kind=kd, owner_module="desk.forecast.adapters.vendors2",
               family="vendor." + fam, targets=t, contexts_declared=cx,
               laws=Laws(bounded=bd, warmup=w, abstains=ab, costed="own_name_cs_impact"),
               inputs=("daily bars",), grade="NEW", evidence=(src,), sign=sg, note=NOTE, ledger=_ledger(lk))
    for k, (sg, bd, w, ab, t, kd, fam, cx, src, lk) in SPEC.items()) + tuple(
    Forecaster(id=k, version="rea-wp2-1", kind="score", owner_module="desk.forecast.adapters.vendors2", family="index",
               targets=t, contexts_declared=("market",),
               laws=Laws(bounded=bd, warmup=0, abstains=True, costed="index: SPY 1 bp + 2 bp auction"),
               inputs=inp, grade="NEW", evidence=(src,), sign=sg, note=NOTE,
               ledger=_ledger({"access_pit": "closed daily bars of " + "/".join(inp),
                               "holdable": "index context; SPY / ETF paper only"}))
    for k, (sg, bd, t, inp, src) in MKT_SPEC.items())


# ---------------------------------------------------------------- helpers
def _ema0(x, span):
    """the recursive EMA from bar 0 (no NaN prefix); the caller masks its own warm-up"""
    x = np.asarray(x, float)
    if not len(x):
        return x
    a = 2.0 / (span + 1)
    return lfilter([a], [1, -(1 - a)], x, zi=[(1 - a) * x[0]])[0]


def _nan_before(x, k):
    x = np.array(x, float)
    x[:k] = np.nan
    return x


def _sign(x, eps=1e-9):
    x = np.asarray(x, float)
    return np.where(x > eps, 1.0, np.where(x < -eps, -1.0, 0.0))


def _flag(cond, valid):
    return np.where(valid, np.asarray(cond, float), np.nan)


def _prior_max(x, n):
    return lag(roll(x, n, "max"))


def _prior_min(x, n):
    return lag(roll(x, n, "min"))


def _dmi(h, l, c, n=14):
    """(+DI, -DI, ADX), Wilder smoothing (adapters/vendors._adx's arithmetic with the DIs kept)"""
    up, dn = np.r_[0.0, np.diff(h)], -np.r_[0.0, np.diff(l)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = wilder(true_range(h, l, c), n)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi, mdi = 100 * wilder(pdm, n) / tr, 100 * wilder(mdm, n) / tr
        dx = np.where(pdi + mdi > 0, 100 * np.abs(pdi - mdi) / (pdi + mdi), 0.0)
    adx = wilder(np.nan_to_num(dx), n)
    adx[:2 * n] = np.nan
    return pdi, mdi, adx


# ---------------------------------------------------------------- structure: BOS / CHoCH / FVG (C15-C21, C48, C74)
def smc(o, h, l, c, a14, L=5, min_atr=0.0, mode="touch", age=50):
    """One pass over closed bars; every output at t reads bars 0..t only.
    swings: a pivot high at p is confirmed at p + L (strictly above the L bars before, at least the L after); a break is
    a close beyond the last confirmed, unbroken swing; trend 0 until the first break; the first break is a BOS.
    FVG zones form at t (bull low[t] > high[t-2], gap >= min_atr * ATR) and are open until mitigated by `mode`: touch =
    a wick reaches the near edge, half = the midpoint, full = the far edge; a close through the far edge is the inverse
    FVG (the zone dies). Returns a dict of arrays: bos, choch, net, dist (NaN: no open zone), bosfvg, ifvg."""
    n = len(c)
    bos, choch, net = np.zeros(n), np.zeros(n), np.zeros(n)
    bosfvg, ifvg = np.zeros(n), np.zeros(n)
    dist = np.full(n, np.nan)
    hl = ll = None
    trend, up_idx, dn_idx = 0, -1, -1
    zones = []                               # [dir, bot, top, formed at]
    for t in range(n):
        if hl is not None and c[t] > hl:
            if trend == -1:
                choch[t] = 1.0
            else:
                bos[t] = 1.0
            trend, up_idx, hl = 1, t, None
        elif ll is not None and c[t] < ll:
            if trend == 1:
                choch[t] = -1.0
            else:
                bos[t] = -1.0
            trend, dn_idx, ll = -1, t, None
        p = t - L
        if p >= L:
            if h[p] > h[p - L:p].max() and h[p] >= h[p + 1:t + 1].max():
                hl = h[p]
            if l[p] < l[p - L:p].min() and l[p] <= l[p + 1:t + 1].min():
                ll = l[p]
        keep = []
        for z in zones:
            d, bot, top, g = z
            if t - g > age:
                continue
            if d > 0:
                inv = c[t] < bot
                lvl = {"touch": top, "half": 0.5 * (bot + top), "full": bot}[mode]
                hit = l[t] <= lvl
            else:
                inv = c[t] > top
                lvl = {"touch": bot, "half": 0.5 * (bot + top), "full": top}[mode]
                hit = h[t] >= lvl
            if inv:
                ifvg[t] += -d
                continue
            if hit:
                if d > 0 and trend == 1 and g >= up_idx >= 0 and min_atr > 0:
                    bosfvg[t] += 1.0
                elif d < 0 and trend == -1 and g >= dn_idx >= 0 and min_atr > 0:
                    bosfvg[t] -= 1.0
                continue
            keep.append(z)
        zones = keep
        if t >= 2:
            gap_up, gap_dn = l[t] - h[t - 2], l[t - 2] - h[t]
            need = min_atr * a14[t] if min_atr > 0 else 0.0
            if min_atr > 0 and not np.isfinite(need):
                pass
            elif gap_up > need and gap_up > 0:
                zones.append([1, h[t - 2], l[t], t])
            elif gap_dn > need and gap_dn > 0:
                zones.append([-1, h[t], l[t - 2], t])
        if zones:
            nb = sum(1 for z in zones if z[0] > 0)
            net[t] = (nb - (len(zones) - nb)) / len(zones)
            z = min(zones, key=lambda z: abs(0.5 * (z[1] + z[2]) - c[t]))
            if np.isfinite(a14[t]) and a14[t] > 0:
                dist[t] = np.clip((0.5 * (z[1] + z[2]) - c[t]) / a14[t], -10, 10)
    np.clip(ifvg, -1, 1, out=ifvg)
    np.clip(bosfvg, -1, 1, out=bosfvg)
    return {"bos": bos, "choch": choch, "net": net, "dist": dist, "bosfvg": bosfvg, "ifvg": ifvg}


def order_blocks(o, h, l, c, v, a14, disp=1.5, back=10, age=50):
    """graded net pressure of live order blocks: at a displacement candle (body >= disp * ATR14) the last opposite candle
    within `back` bars becomes a zone [low, high] weighted by min(v / mean(v, 20), 3) (1 when volume is missing); a zone
    dies on a close through its far side or after `age` sessions; returns (bull - bear) / (bull + bear), 0 with none"""
    n = len(c)
    vm = roll(v, 20, "mean")
    out = np.zeros(n)
    zones = []                               # [dir, low, high, weight, formed]
    for t in range(n):
        zones = [z for z in zones if t - z[4] <= age and not ((z[0] > 0 and c[t] < z[1]) or (z[0] < 0 and c[t] > z[2]))]
        body = c[t] - o[t]
        if np.isfinite(a14[t]) and a14[t] > 0 and abs(body) >= disp * a14[t]:
            d = 1 if body > 0 else -1
            for k in range(t - 1, max(t - back, 0) - 1, -1):
                if (c[k] < o[k]) if d > 0 else (c[k] > o[k]):
                    w = min(v[k] / vm[k], 3.0) if np.isfinite(v[k]) and np.isfinite(vm[k]) and vm[k] > 0 else 1.0
                    zones.append([d, l[k], h[k], w, t])
                    break
        b = sum(z[3] for z in zones if z[0] > 0)
        r = sum(z[3] for z in zones if z[0] < 0)
        out[t] = (b - r) / (b + r) if b + r > 0 else 0.0
    return out


def sweep_c2(h, l, c):
    """ict.c2 (adapters/vendors.fn): +1 a bull sweep (low under the prior low, close back over it), -1 the bear one"""
    pl, ph = lag(l), lag(h)
    b2 = (l < pl) & (c > pl)
    s2 = (h > ph) & (c < ph)
    out = np.where(b2 & ~s2, 1.0, np.where(s2 & ~b2, -1.0, 0.0))
    out[:1] = 0.0
    return out


# ---------------------------------------------------------------- SuperTrend (C42)
KNOTS_S, KNOTS_M = (0.0, 0.4, 0.7, 1.0), (5.0, 4.1, 2.9, 2.0)


def adaptive_mult(S):
    return np.interp(S, KNOTS_S, KNOTS_M)


def supertrend(h, l, c, a, mult):
    """Pine-style SuperTrend from the first bar where ATR and the multiplier are finite; the trend, +1 up / -1 down (NaN
    before). Final bands only tighten unless the prior close broke them; the trend flips on a close beyond the final band"""
    n = len(c)
    out = np.full(n, np.nan)
    mult = np.broadcast_to(np.asarray(mult, float), (n,))
    ok = np.isfinite(a) & np.isfinite(mult)
    if not ok.any():
        return out
    s = int(np.argmax(ok))
    hl2 = 0.5 * (h + l)
    ub, lb = hl2 + mult * a, hl2 - mult * a
    fub, flb, trend = ub[s], lb[s], 1.0
    out[s] = trend
    for i in range(s + 1, n):
        if not ok[i]:
            continue
        fub = ub[i] if (ub[i] < fub or c[i - 1] > fub) else fub
        flb = lb[i] if (lb[i] > flb or c[i - 1] < flb) else flb
        if trend < 0:
            trend = 1.0 if c[i] > fub else -1.0
        else:
            trend = -1.0 if c[i] < flb else 1.0
        out[i] = trend
    return out


def regime_S(h, l, c):
    """ap.regime's S (adapters/vendors.fn), the same arithmetic"""
    adxn = V._clip01((V._adx(h, l, c) - 15) / 20)
    vr = V._clip01(atr(h, l, c, 14) / atr(h, l, c, 50) - 0.5)
    dc = np.abs(np.r_[np.nan, np.diff(c)])
    er = np.abs(c - lag(c, 10)) / roll(dc, 10, "sum")
    er = np.where(np.isfinite(er), np.clip(er, 0, 1), np.where(np.isfinite(roll(dc, 10, "sum")), 0.0, np.nan))
    dirn = np.sign(c - lag(c, 20))
    sg = np.sign(np.r_[np.nan, np.diff(c)])
    cons = roll((sg == dirn).astype(float), 20, "mean")
    cons[~np.isfinite(dirn)] = np.nan
    S = 0.30 * adxn + 0.30 * vr + 0.25 * er + 0.15 * cons
    S[:64] = np.nan
    return S


# ---------------------------------------------------------------- WaveTrend (C54)
def wavetrend(h, l, c, ch=10, avg=21, sig=4):
    ap = (h + l + c) / 3
    esa = _ema0(ap, ch)
    d = _ema0(np.abs(ap - esa), ch)
    with np.errstate(invalid="ignore", divide="ignore"):
        ci = (ap - esa) / (0.015 * d)
    if len(ci):
        ci[0] = 0.0                       # the seed bar: 0 / 0 (float noise otherwise)
    wt1 = _ema0(np.nan_to_num(ci, nan=0.0, posinf=0.0, neginf=0.0), avg)
    wt2 = roll(wt1, sig, "mean")
    return wt1, wt2


# ---------------------------------------------------------------- the no-move band (V-bybit-2) and the straddle label
def band_stay(h, l, c, a14, H, k=2.0):
    """the label: 1 when every high and low over the next H sessions stays inside close +- k * ATR14 at i, else 0; NaN
    when the path is short (reads bars i+1..i+H only)"""
    n = len(c)
    out = np.full(n, np.nan)
    for i in range(n - H):
        if not np.isfinite(a14[i]):
            continue
        out[i] = float(h[i + 1:i + H + 1].max() <= c[i] + k * a14[i] and l[i + 1:i + H + 1].min() >= c[i] - k * a14[i])
    return out


def straddle(h, l, c, a14, H, k=2.0):
    """V-gs-3 label: +1 / -1 when the high reaches c + k ATR (resp. the low c - k ATR) first within H sessions, 0 when
    neither does; a bar that does both is 0 (order unknown on daily bars). Reads bars i+1..i+H only"""
    n = len(c)
    out = np.full(n, np.nan)
    for i in range(n - H):
        if not np.isfinite(a14[i]):
            continue
        up, dn = c[i] + k * a14[i], c[i] - k * a14[i]
        out[i] = 0.0
        for j in range(i + 1, i + H + 1):
            u, d = h[j] >= up, l[j] <= dn
            if u or d:
                out[i] = 0.0 if (u and d) else (1.0 if u else -1.0)
                break
    return out


def atr_band(h, l, c, a14, H, k=2.0, win=40, minn=20):
    stay = band_stay(h, l, c, a14, H, k)
    known = lag(stay, H)                     # the outcome of the close H sessions ago is known only now
    return roll(known, win, "mean", minp=minn)


# ---------------------------------------------------------------- QANTRADING location x streak (V-qc-2)
def locstreak(c, minn=30):
    n = len(c)
    out = np.full(n, np.nan)
    if n < 2:
        return out
    mx, mn = roll(c, 20, "max"), roll(c, 20, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.where(mx > mn, (c - mn) / (mx - mn), 0.5)
    loc = np.where(np.isfinite(mx), np.minimum((pos * 5).astype(int), 4), -1)
    st = np.clip(V._streak(c), -5, 5).astype(int) + 5
    nl, ul = np.zeros(5), np.zeros(5)
    ns, us = np.zeros(11), np.zeros(11)
    for t in range(1, n):
        up = float(c[t] > c[t - 1])          # the outcome of t-1 is known at t
        if loc[t - 1] >= 0:
            nl[loc[t - 1]] += 1
            ul[loc[t - 1]] += up
        if t - 1 >= 1:
            ns[st[t - 1]] += 1
            us[st[t - 1]] += up
        if loc[t] >= 0 and nl[loc[t]] >= minn and ns[st[t]] >= minn:
            out[t] = 0.5 * (ul[loc[t]] / nl[loc[t]] + us[st[t]] / ns[st[t]])
    return out


# ---------------------------------------------------------------- GEXRADAR entropy (A97)
def entropy20(c, n=20, bins=20):
    r = ret(c)
    out = np.full(len(c), np.nan)
    if len(r) <= n:
        return out
    w = np.lib.stride_tricks.sliding_window_view(r[1:], n)          # windows of r[t-n+1..t], t = n..len-1
    mn, mx = w.min(axis=1), w.max(axis=1)
    span = mx - mn
    with np.errstate(invalid="ignore", divide="ignore"):
        idx = np.where(span[:, None] > 0, np.floor((w - mn[:, None]) / span[:, None] * bins), 0.0)
    idx = np.clip(idx, 0, bins - 1).astype(int)
    cnt = (idx[:, :, None] == np.arange(bins)[None, None, :]).sum(axis=1) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        hh = -np.nansum(np.where(cnt > 0, cnt * np.log2(cnt), 0.0), axis=1)
    out[n:] = hh / np.log2(bins)
    return out


# ---------------------------------------------------------------- the per-name function
def fn(b, m):
    o, h, l, c, v = (np.asarray(b[k], float) for k in ("o", "h", "l", "c", "v"))
    n = len(c)
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        a14 = atr(h, l, c, 14)
        # ChartsLector
        e10, e20, s50 = ema(c, 10), ema(c, 20), roll(c, 50, "mean")
        ph20 = _prior_max(h, 20)
        ok = np.isfinite(e10) & np.isfinite(e20) & np.isfinite(s50) & np.isfinite(ph20)
        out["lector.2b"] = _flag((c >= e10) & (e10 >= e20) & (e20 >= s50) & (c >= ph20), ok)
        out["lector.naive20"] = _flag(c > ph20, np.isfinite(ph20))
        x = ((c - s50) / s50) / (a14 / c)
        okx = np.isfinite(x)
        out["lector.xatr_2c"] = _flag((x >= 7) & (x < 11), okx)
        out["lector.xatr_2d"] = _flag(x >= 11, okx)
        out["lector.xatr_4c"] = _flag(x < -7, okx)
        # Raschke
        M = c - lag(c, 2)
        F = roll(c, 3, "mean") - roll(c, 10, "mean")
        S = roll(F, 16, "mean")
        dM, dF, dS = (np.r_[np.nan, np.diff(z)] for z in (M, F, S))
        sM, sF, sS = _sign(dM), _sign(dF), _sign(dS)
        pf = np.where((sM > 0) & (sF > 0) & (sS > 0), 1.0, np.where((sM < 0) & (sF < 0) & (sS < 0), -1.0, 0.0))
        out["rsc.pf3"] = np.where(np.isfinite(dS) & np.isfinite(dM), pf, np.nan)
        aw = wilder(true_range(h, l, c), 14)
        sg = np.where(np.isfinite(dF), _sign(np.nan_to_num(dF)), 0.0)
        pair = (sg[1:] * sg[:-1] < 0).astype(float)
        fl = roll(np.r_[0.0, pair], 5, "sum")        # pairs (k-1, k) for the 6 slopes ending at t: k = t-4..t
        okr = np.isfinite(S) & np.isfinite(fl) & (np.arange(n) >= 40) & (aw > 0)
        out["rsc.rotation"] = _flag((np.abs(S) / aw <= 0.15) & (fl >= 2), okr)
        pdi, mdi, adx = _dmi(h, l, c)
        e20r = ema(c, 20)
        okh = np.isfinite(adx) & np.isfinite(e20r)
        long_ = (adx > 30) & (pdi > mdi) & (l <= e20r)
        short_ = (adx > 30) & (mdi > pdi) & (h >= e20r)
        out["rsc.holygrail"] = np.where(okh, long_.astype(float) - short_.astype(float), np.nan)
        pl, ph = _prior_min(l, 20), _prior_max(h, 20)
        age_lo, age_hi = np.full(n, np.nan), np.full(n, np.nan)
        if n > 20:
            win_l = np.lib.stride_tricks.sliding_window_view(l[:-1], 20)         # bars t-20..t-1 at row t-20
            win_h = np.lib.stride_tricks.sliding_window_view(h[:-1], 20)
            age_lo[20:] = 20 - (19 - np.argmin(win_l[:, ::-1], axis=1))          # most recent occurrence of the min
            age_hi[20:] = 20 - (19 - np.argmax(win_h[:, ::-1], axis=1))
        tl = (l < pl) & (c > pl) & (age_lo >= 4)
        ts = (h > ph) & (c < ph) & (age_hi >= 4)
        out["rsc.turtle"] = np.where(np.isfinite(pl), tl.astype(float) - ts.astype(float), np.nan)
        # structure
        W = 20
        base = smc(o, h, l, c, a14)
        atrz = smc(o, h, l, c, a14, min_atr=0.5)
        half = smc(o, h, l, c, a14, mode="half")
        full = smc(o, h, l, c, a14, mode="full")
        for k, z in (("lux.bos", base["bos"]), ("lux.choch", base["choch"]), ("lux.fvg", base["net"]),
                     ("lux.fvg_atr", atrz["net"]), ("lux.fvg_half", half["net"]), ("lux.fvg_full", full["net"]),
                     ("lux.fvg_dist", base["dist"]), ("lux.ifvg", base["ifvg"]), ("lux.bos_fvg", atrz["bosfvg"])):
            out[k] = _nan_before(z, W)
        out["lux.ob"] = _nan_before(order_blocks(o, h, l, c, v, a14), 33)
        sw = sweep_c2(h, l, c)
        near = np.zeros(n)
        bull_sw, bear_sw = np.zeros(n), np.zeros(n)
        for j in range(4):
            bull_sw[j:] = np.maximum(bull_sw[j:], (sw[:n - j] > 0).astype(float))
            bear_sw[j:] = np.maximum(bear_sw[j:], (sw[:n - j] < 0).astype(float))
        ifv = base["ifvg"]
        near = np.where((ifv > 0) & (bull_sw > 0), 1.0, np.where((ifv < 0) & (bear_sw > 0), -1.0, 0.0))
        out["ez.sweepgap"] = _nan_before(near, W)
        # SuperTrend
        Sg = regime_S(h, l, c)
        out["ap.stadapt"] = supertrend(h, l, c, a14, adaptive_mult(Sg))
        out["ap.st3"] = supertrend(h, l, c, a14, 3.0)
        # WaveTrend
        wt1, wt2 = wavetrend(h, l, c)
        x1, y1 = lag(wt1), lag(wt2)
        cross_up = (x1 <= y1) & (wt1 > wt2) & (wt1 <= -53)
        cross_dn = (x1 >= y1) & (wt1 < wt2) & (wt1 >= 53)
        out["mc.wt"] = _nan_before(cross_up.astype(float) - cross_dn.astype(float), 40)
        # Bybit
        out["byb.atr_band5"] = atr_band(h, l, c, a14, 5)
        out["byb.atr_band20"] = atr_band(h, l, c, a14, 20)
        # GridScalper
        r14 = rsi(c, 14)
        macd = _ema0(c, 12) - _ema0(c, 26)
        hist = macd - _ema0(macd, 9)
        e50, e200 = ema(c, 50), ema(c, 200)
        bull = (e20 > e50) & (e50 > e200)
        bear = (e20 < e50) & (e50 < e200)
        buy = 0.3 * (r14 < 30) + 0.2 * (hist > 0) + 0.3 * bull + 0.1 * (c > e200)
        sell = 0.3 * (r14 > 70) + 0.2 * (hist <= 0) + 0.3 * bear + 0.1 * (c <= e200)
        ok5 = np.isfinite(e200) & np.isfinite(r14)
        out["gs.five"] = np.where(ok5, buy - sell, np.nan)
        out["gs.five_sig"] = np.where(ok5, np.where((buy > sell) & (buy > 0.4), 1.0,
                                                    np.where((sell > buy) & (sell > 0.4), -1.0, 0.0)), np.nan)
        out["gs.ema"] = np.where(np.isfinite(e200), bull.astype(float) - bear.astype(float), np.nan)
        out["gs.rsi"] = np.where(np.isfinite(r14), (r14 < 30).astype(float) - (r14 > 70).astype(float), np.nan)
        # Zerith
        hp = lag(hist)
        zc = ((hp <= 0) & (hist > 0) & (c > e200)).astype(float) - ((hp >= 0) & (hist < 0) & (c < e200)).astype(float)
        out["zer.macd200"] = np.where(np.isfinite(e200) & np.isfinite(hp), zc, np.nan)
        out["qc.locstreak"] = locstreak(c)
        out["gex.entropy20"] = entropy20(c)
    return out


# ---------------------------------------------------------------- the index context series
def _etf(mkt, key):
    """one ETF's closes as a Series by session: a bars dict (guarded), a Series or a {session: close} dict; None if absent"""
    if mkt is None or key not in mkt or mkt[key] is None:
        return None
    x = mkt[key]
    if isinstance(x, pd.Series):
        s = x.astype(float)
    elif isinstance(x, dict) and "c" in x and "d" in x:
        if all(k in x for k in ("o", "h", "l", "v")):
            ok = D.guard(x)
        else:
            c = np.asarray(x["c"], float)
            ok = np.isfinite(c) & (c > 0)
        s = pd.Series(np.asarray(x["c"], float)[ok], index=np.asarray(x["d"])[ok])
    else:
        s = market_series(mkt, key)
    s = s[np.isfinite(s.to_numpy()) & (s.to_numpy() > 0)]
    return s[~s.index.duplicated(keep="last")].sort_index()


MACRO = (("rsp", "spy", 0.25), ("hyg", "lqd", 0.15), ("iwm", "spy", 0.15), ("spy", "tlt", 0.15), ("xly", "xlp", 0.10))


def trend_signal(ratio, n=200, lagk=20):
    s = ratio.rolling(n, min_periods=n).mean()
    return 0.5 * np.sign(ratio - s) + 0.5 * np.sign(s - s.shift(lagk))


def smt(a, b, n=20):
    """SMT divergence of two close series on their common sessions: a new n-session closing extreme (against the prior n
    closes) in one and not the other; +1 at the lows, -1 at the highs; NaN before n + 1 common sessions"""
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    j.columns = ["a", "b"]
    hi = j.shift(1).rolling(n, min_periods=n).max()
    lo = j.shift(1).rolling(n, min_periods=n).min()
    hia, hib = j["a"] > hi["a"], j["b"] > hi["b"]
    loa, lob = j["a"] < lo["a"], j["b"] < lo["b"]
    v = (loa ^ lob).astype(float) - (hia ^ hib).astype(float)
    return v.where(hi["a"].notna())


def series(m, mkt=None):
    """the session series of every index forecaster (index = session), computed once per run"""
    spy = m["spy"]
    etf = {"spy": spy}
    for k in ETFS:
        s = _etf(mkt, k) if mkt is not None and k in mkt else m.get(k)
        if s is not None:
            etf[k] = s
    out = {}
    for k in ("qqq", "iwm"):
        if k in etf:
            out[f"tjr.smt_{k}"] = smt(spy, etf[k])
    sig, wts = {}, {}
    for num, den, w in MACRO:
        if num in etf and den in etf:
            ratio = (etf[num] / etf[den]).replace([np.inf, -np.inf], np.nan).dropna()
            sig[f"{num}/{den}"] = trend_signal(ratio)
            wts[f"{num}/{den}"] = w
    if sig:
        df = pd.DataFrame(sig)
        w = pd.Series(wts)
        ok = df.notna()
        den = (ok * w).sum(axis=1)
        comp = (df.fillna(0.0) * w).sum(axis=1) / den.where(den > 0)
        out["oft3r.macro5"] = comp
        out["oft3r.macro5_rv"] = comp
    r20 = spy.pct_change(20)
    out["composer.dualmom"] = pd.Series(np.where(r20.notna(), np.where(r20 > 0.02, 1.0, -1.0), np.nan), index=spy.index)
    return out


_NAME_IDS = [f.id for f in FORECASTERS if f.family != "index"]
_name_compute = wrap(fn, _NAME_IDS)


def compute(a, mkt, m=None, ser=None):
    out = _name_compute(a, mkt, m=m)
    n = len(a["c"])
    if ser is None:
        ser = series(m if m is not None else market(mkt), mkt)
    d = np.asarray(a["d"])
    for k in MKT_SPEC:
        s = ser.get(k)
        x = pd.Series(d).map(s).to_numpy(float) if s is not None else np.full(n, np.nan)
        out[k] = np.where(np.isfinite(x), x, np.nan)
    return out
