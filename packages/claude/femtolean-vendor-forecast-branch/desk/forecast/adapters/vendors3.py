"""Vendor forecasters, package vendor-forecast (2026-10-27): the rows the earlier REA packages left deferred or rejected, now
buildable under owner ruling LIC-02 (every torn-down vendor may be installed, reverse engineered and replicated). DISCOVERY-ONLY:
each is a hypothesis registered for the Factory search and the 2023+ holdout to grade; none is promoted, none carries an edge
claim. Daily closed bars, point in time, no constant that is not the vendor's own number (named on its row).

Sources (read in full; the vendors' own code is on disk):
  CH  /home/user/chartslector/tv-indicators/<file>.txt   ChartsLector's public Pine repo (ChartsLector/TV-Indicators)
  GZ  /home/user/quant-research-critical/gainzalgo-study/gainzalgo_replica.pine   the study's behavioural replica
  TV  TradingView Technical Ratings: Pine library jDWyb5PG (description) + Help Center "Technical ratings" (vote table)

Per-name (a value per bar of one name)
  GainzAlgo (GZ:34-60, C25, REGISTRY gainzalgo.rulegate)
    gainzalgo.rulegate  +1 buy / -1 sell / 0: an opposite-colour candle closing beyond the prior open, body / true range
                        > 0.5, RSI14 < 50 (buy) or > 50 (sell), close under (over) close[5], alternating signals only
  ChartsLector one-month RS (CH 1-Month Relative Strength.txt:15-31, 52-63; CL3)
    lector.rs26/78/156  RS = close / SPY close; percentile = (count of the last N RS values strictly under today's) / (N-1)
                        x 100, today included (the vendor's array code); N = 26, 78, 156 (his published set)
    lector.rs_run15     1 when the percentile has been > 50 for 15 sessions in a row (alertLen)
    lector.rs_12of15    1 when it was > 50 on at least 12 of the 15 sessions before today (percentile50limitDays)
  ChartsLector Relative Robustness Rotation (CH Relative Robustness Rotation.txt, CL7)
    lector.rrr_ratio    blended RS-Ratio - 100:   0.6 R(15,21) + 0.4 R(26,34),  R(a,b) = 100 EMA(RS,a) / EMA(EMA(RS,a),b)
    lector.rrr_mom      adjusted blended RS-Momentum - 100: 0.6 M(8,15) + 0.4 M(15,26) of the blended ratio, plus
                        0.10 tanh(acceleration z) (the vendor's bounded correction); RS = 100 close / SPY close
    lector.rrr_q        quadrant: Leading +1, Improving +0.5, Weakening -0.5, Lagging -1 (lines at 100)
  ChartsLector NVARS (CH Normalized Volatility Adjusted Relative Strength.txt:76-145, 161-163)
    lector.nvars        (sum 50 of (c - c[1]) / ATR14 of the name - the same of SPY) / RMS100 of itself
    lector.nvars_fs     +1 when the fast SMA8 of NVARS is above the slow SMA20, -1 below
  ChartsLector Candle Stage Analysis (CH Candles Stage Analysis.txt:25-110, 91-110 priority), CL2/CL5
    lector.stg_1a 1b 2a 2b 2c 2d 3a 3b 4a 4b 4c   0/1 flags of the vendor's stage ladder (Wilder ATR14, xATR in the
                        ATR-percent mode); one stage per bar by his priority 2D, 2C, 4C, 3A, 3B, 2A/2B, 4A/4B, 1A, 1B
  ChartsLector Unfilled Close-Adjusted Gaps (CH Unfilled Close-Adjusted Gaps.txt:20-112)
    lector.cgap         (open gap-ups - open gap-downs) / (their sum): gaps are low > close[1] or high < close[1], closed by a
                        close through the far side, tightened by closes inside, 80 sessions at most, 100 at most
    lector.cgap_dist    (the nearest active boundary - close) / ATR14, NaN with no open gap (abstains)
  ChartsLector Calibrated RSI Position Zones (CH Calibrated RSI Position Zones.txt:219-440)
    lector.crsi_z       z of the logit-smoothed RSI14 around its 42-EMA centre, sigma = sqrt(EMA63 of the squared residual)
    lector.crsi_cont    +1 strong long continuation, -1 strong short continuation (re-entry through +-2 sigma, tail
                        confirmed at the 10th / 90th percentile of 126, price trend and momentum regime and centre slope agree)
    lector.crsi_early   +1 early bullish reversal / -1 early bearish   lector.crsi_mr  mean-reversion long / short
    lector.crsi_ctr     countertrend long bounce / short pullback
  TradingView Technical Ratings (TV; V-survey-2)
    tv.osc / tv.ma / tv.rating   mean of the 11 oscillator votes / 15 MA votes / their mean, each vote +1 / 0 / -1
  GridScalper (V-gs-3)
    gs.straddle5        the share of the last 40 completed outcomes (at least 20) in which the high reached close + 2 ATR14 or
                        the low reached close - 2 ATR14 within 5 sessions (the straddle label of vendors2.straddle)

  Vibe-Trading factor zoo (MIT; V-vibe-4): 30 ported formulas, the first ten per-name ones of each library by a rule fixed before
    any score (see ZOO): a101.* (Kakushadze 101 alphas), gtja.* (GTJA191), qlib.* (Qlib Alpha158). The ids and formulas are in ZOO
    and each carries its file in `evidence`; the cross-sectional ones (rank, scale, industry) wait for the xs lane

Index context (one value per session; family "index")
  lector.vmr / lector.vmr3   VIX Mood Ring composite 0.35 VIX + 0.25 VIX/VIX3M + 0.25 SKEW + 0.15 VVIX, each through the
                        vendor's piecewise score (CH Market Action Pulse & VIX Mood Ring.txt:544-629); vmr needs all four,
                        vmr3 renormalises over the three the desk always holds (VVIX comes from Cboe's public csv)
  lector.vmr_rv / lector.vmr_risk   the same composite against realized volatility (sign -1) / RAM's VMR risk with the
                        divergence floors (lines 818-831: backwardation 95, complacency 75, whipsaw 80, panic easing 40,
                        all clear 10)
  lector.pulse        Market Action Pulse state 0..5 (lines 225-375; needs a health ETF (qqqe, else rsp) and Nasdaq/NYSE
                        advancers and decliners: abstains without them)
  lector.ram          RAM v0.2 (lines 803-877): 0.35 pulse + 0.30 breadth + 0.20 VMR + 0.15 target risk over the families
                        present, renormalised
  composer.dualmom12_1  Antonacci dual momentum on SPY and BND: +1 when SPY's 12-1 month return beats BND's and is positive,
                        else -1 (composer.md C116; the 12-1 form is the textbook one, the teardown shows the 20-day switch)

Deferred (REGISTRY.md): EM Gaussian-mixture regime (needs its 42 KB mixture code ported with a convergence rule), LoD Intraday
Entry and 30 min Pivot (intraday), COT (CFTC feed), NYSE TICK cycle (TICK feed), the double / opening-gap FVG (LuxAlgo PAC is
invite-only: no source on disk)."""
import numpy as np
import pandas as pd

from .. import Forecaster, Laws, Ledger
from . import vendors2 as V2
from ._common import atr as _atr_mean, ema, lag, market as _market, roll, rsi, true_range, wilder, wrap  # noqa: F401
from ._common import on

UP = ("up_excess_5", "up_excess_20")
UP20 = ("up_excess_20",)
RV = ("realized_vol_20",)
PATHS = {"fn": "desk.forecast.adapters.vendors3"}
_N = "all"
_e0, _nb, _flag, _sign = V2._ema0, V2._nan_before, V2._flag, V2._sign


# ---------------------------------------------------------------- specs
# id: (sign, bounds, warmup, abstains, targets, source, extras)
SPEC = {
    "gainzalgo.rulegate": (1, (-1.0, 1.0), 15, False, UP, "GZ gainzalgo_replica.pine:34-60 (C25)", {}),
    "lector.rs26": (1, (0.0, 100.0), 25, False, UP20, "CH 1-Month Relative Strength.txt:15-31 (CL3)", {}),
    "lector.rs78": (1, (0.0, 100.0), 77, False, UP20, "CH 1-Month Relative Strength.txt:15-31 (CL3, N 78)", {}),
    "lector.rs156": (1, (0.0, 100.0), 155, False, UP20, "CH 1-Month Relative Strength.txt:15-31 (CL3, N 156)", {}),
    "lector.rs_run15": (1, (0.0, 1.0), 40, False, UP20, "CH 1-Month Relative Strength.txt:52-56 (CL3 alert)", {}),
    "lector.rs_12of15": (1, (0.0, 1.0), 40, False, UP20, "CH 1-Month Relative Strength.txt:58-64 (CL3 alert)", {}),
    "lector.rrr_ratio": (1, (-1e18, 1e18), 130, False, UP20, "CH Relative Robustness Rotation.txt (CL7)", {}),
    "lector.rrr_mom": (1, (-1e18, 1e18), 130, False, UP20, "CH Relative Robustness Rotation.txt (CL7)", {}),
    "lector.rrr_q": (1, (-1.0, 1.0), 130, False, UP20, "CH Relative Robustness Rotation.txt (CL7)", {}),
    "lector.nvars": (1, (-1e18, 1e18), 150, False, UP20, "CH Normalized Volatility Adjusted Relative Strength.txt:76-145", {}),
    "lector.nvars_fs": (1, (-1.0, 1.0), 175, False, UP20, "CH Normalized Volatility Adjusted Relative Strength.txt:152-163", {}),
    "lector.stg_1a": (1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:52,105", {}),
    "lector.stg_1b": (1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:67,107", {}),
    "lector.stg_2a": (1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:101-102", {}),
    "lector.stg_2b": (1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:48,101-102 (CL4, strict ladder)", {}),
    "lector.stg_2c": (1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:58,93 (CL5)", {}),
    "lector.stg_2d": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:59,91 (CL5)",
                      {"holdable": "veto (an avoid gate)"}),
    "lector.stg_3a": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:65,97", {}),
    "lector.stg_3b": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:66,99", {}),
    "lector.stg_4a": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:103-104", {}),
    "lector.stg_4b": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:49,103-104", {}),
    "lector.stg_4c": (-1, (0.0, 1.0), 50, False, UP20, "CH Candles Stage Analysis.txt:62,95 (CL5)",
                      {"holdable": "veto (an avoid gate)"}),
    "lector.cgap": (1, (-1.0, 1.0), 14, False, UP, "CH Unfilled Close-Adjusted Gaps.txt:20-112", {}),
    "lector.cgap_dist": (1, (-1e18, 1e18), 14, True, UP, "CH Unfilled Close-Adjusted Gaps.txt:48-62, 93-108", {}),
    "lector.crsi_z": (-1, (-1e18, 1e18), 200, False, UP, "CH Calibrated RSI Position Zones.txt:232-251", {}),
    "lector.crsi_cont": (1, (-1.0, 1.0), 200, False, UP, "CH Calibrated RSI Position Zones.txt:379-389", {}),
    "lector.crsi_early": (1, (-1.0, 1.0), 200, False, UP, "CH Calibrated RSI Position Zones.txt:393-403", {}),
    "lector.crsi_mr": (1, (-1.0, 1.0), 200, False, UP, "CH Calibrated RSI Position Zones.txt:407-419", {}),
    "lector.crsi_ctr": (1, (-1.0, 1.0), 200, False, UP, "CH Calibrated RSI Position Zones.txt:422-432", {}),
    "tv.osc": (1, (-1.0, 1.0), 60, False, UP, "TV Technical Ratings Help Center, 11 oscillator votes (V-survey-2)", {}),
    "tv.ma": (1, (-1.0, 1.0), 200, False, UP, "TV Technical Ratings Help Center, 15 MA votes (V-survey-2)", {}),
    "tv.rating": (1, (-1.0, 1.0), 200, False, UP, "TV Pine library jDWyb5PG calcRatingAll (V-survey-2)", {}),
    "gs.straddle5": (1, (0.0, 1.0), 45, False, RV, "gridscalperea.md §5 (V-gs-3)", {}),
}

# Vibe-Trading factor zoo (MIT; agent/src/factors/zoo/<library>/<file>.py; V-vibe-4). Pre-registered selection rule, fixed before
# any score: the first ten per-name (no cross-sectional rank / scale / industry / vwap term) formulas of each library in file
# order, skipping exact or near-exact duplicates of one already taken (gtja191 004 = alpha101 021 but for a >= 1 edge; 005 =
# alpha101 026); qlib158 is its ten K-shape features plus ROC20. The multiple-testing count is the point; expect nulls.
ZOO = {   # id: (warmup, file, formula)
    "a101.006": (10, "alpha101/alpha_006.py", "-1 * correlation(open, volume, 10)"),
    "a101.007": (67, "alpha101/alpha_007.py", "(adv20<volume) ? (-ts_rank(abs(delta(close,7)),60) * sign(delta(close,7))) : -1"),
    "a101.009": (5, "alpha101/alpha_009.py", "0<ts_min(d1,5) ? d1 : (ts_max(d1,5)<0 ? d1 : -d1), d1 = delta(close,1)"),
    "a101.012": (1, "alpha101/alpha_012.py", "sign(delta(volume,1)) * (-1 * delta(close,1))"),
    "a101.021": (20, "alpha101/alpha_021.py", "Kakushadze #21 band-and-volume ladder (+-1)"),
    "a101.023": (20, "alpha101/alpha_023.py", "(sum(high,20)/20 < high) ? -1 * delta(high,2) : 0"),
    "a101.024": (200, "alpha101/alpha_024.py", "delta(sma100,100)/delay(close,100) <= 0.05 ? -(close - ts_min(close,100)) : -delta(close,3)"),
    "a101.026": (10, "alpha101/alpha_026.py", "-1 * ts_max(correlation(ts_rank(volume,5), ts_rank(high,5), 5), 3)"),
    "a101.035": (33, "alpha101/alpha_035.py", "ts_rank(volume,32) * (1 - ts_rank(close+high-low,16)) * (1 - ts_rank(returns,32))"),
    "a101.043": (39, "alpha101/alpha_043.py", "ts_rank(volume/adv20,20) * ts_rank(-1*delta(close,7),8)"),
    "gtja.002": (2, "gtja191/alpha_002.py", "-1 * delta(((close-low)-(high-close))/(high-low), 1)"),
    "gtja.003": (7, "gtja191/alpha_003.py", "sum over 6 of close - (close>delay ? min(low,delay) : max(high,delay)), 0 if unchanged"),
    "gtja.009": (30, "gtja191/alpha_009.py", "SMA(((high+low)/2-(delay(high)+delay(low))/2)*(high-low)/volume, 7, 2)"),
    "gtja.011": (6, "gtja191/alpha_011.py", "sum(((close-low)-(high-close))/(high-low)*volume, 6)"),
    "gtja.014": (5, "gtja191/alpha_014.py", "close - delay(close,5)"),
    "gtja.015": (1, "gtja191/alpha_015.py", "open/delay(close,1) - 1"),
    "gtja.018": (5, "gtja191/alpha_018.py", "close/delay(close,5)"),
    "gtja.019": (5, "gtja191/alpha_019.py", "5-day change over delay (down) or over close (up), 0 if equal"),
    "gtja.020": (6, "gtja191/alpha_020.py", "(close-delay(close,6))/delay(close,6) * 100"),
    "gtja.021": (11, "gtja191/alpha_021.py", "regression slope of mean(close,6) on a 6-bar sequence"),
    "qlib.kmid": (0, "qlib158/kmid.py", "(close-open)/open"),
    "qlib.klen": (0, "qlib158/klen.py", "(high-low)/open"),
    "qlib.kmid2": (0, "qlib158/kmid2.py", "(close-open)/(high-low)"),
    "qlib.kup": (0, "qlib158/kup.py", "(high - max(open,close))/open"),
    "qlib.kup2": (0, "qlib158/kup2.py", "(high - max(open,close))/(high-low)"),
    "qlib.klow": (0, "qlib158/klow.py", "(min(open,close) - low)/open"),
    "qlib.klow2": (0, "qlib158/klow2.py", "(min(open,close) - low)/(high-low)"),
    "qlib.ksft": (0, "qlib158/ksft.py", "(2*close-high-low)/open"),
    "qlib.ksft2": (0, "qlib158/ksft2.py", "(2*close-high-low)/(high-low)"),
    "qlib.roc20": (20, "qlib158/roc20.py", "delay(close,20)/close"),
}
for _k, (_w, _f, _fm) in ZOO.items():
    SPEC[_k] = (1, (-1e300, 1e300), _w, _k == "a101.026", UP, "Vibe-Trading zoo " + _f + ": " + _fm + " (V-vibe-4, MIT)", {})
MKT_SPEC = {   # id: (sign, bounds, targets, inputs, source)
    "lector.vmr": (1, (0.0, 100.0), ("spy_ret_20", "spy_ret_60"), ("VIX", "VIX3M", "SKEW", "VVIX"),
                   "CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10)"),
    "lector.vmr3": (1, (0.0, 100.0), ("spy_ret_20", "spy_ret_60"), ("VIX", "VIX3M", "SKEW"),
                    "CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10, VVIX leg renormalised away)"),
    "lector.vmr_rv": (-1, (0.0, 100.0), ("spy_rv_20",), ("VIX", "VIX3M", "SKEW"),
                      "CH Market Action Pulse & VIX Mood Ring.txt:544-629 (CL10)"),
    "lector.vmr_risk": (-1, (0.0, 100.0), ("spy_ret_20", "spy_rv_20"), ("VIX", "VIX3M", "SKEW"),
                        "CH Market Action Pulse & VIX Mood Ring.txt:818-831 (CL9)"),
    "lector.pulse": (1, (0.0, 5.0), ("spy_ret_20", "spy_ret_60"), ("health ETF", "advancers", "decliners"),
                     "CH Market Action Pulse & VIX Mood Ring.txt:225-375 (CL8)"),
    "lector.ram": (-1, (0.0, 100.0), ("spy_ret_20", "spy_rv_20"), ("VIX", "VIX3M", "SKEW"),
                   "CH Market Action Pulse & VIX Mood Ring.txt:803-877 (CL9)"),
    "composer.dualmom12_1": (1, (-1.0, 1.0), ("spy_ret_20",), ("SPY", "BND"), "composer.md (C116, 12-1 form)"),
}
NOTE = ("DISCOVERY-ONLY (vendor-forecast package, LIC-02): a hypothesis for the Factory search and the 2023+ holdout to "
        "grade; no edge is claimed and nothing is promoted")


def _ledger(extra):
    kw = dict(payer="unknown (vendor claim unverified)", speed_decay="vendor horizon 1-20 sessions",
              decisive_test="BH over the run + walk-forward + same-sign 2023+ holdout, net of costs")
    kw.update(extra)
    return Ledger(**kw)


def _fam(k):
    return "vendor." + k.split(".")[0]


FORECASTERS = tuple(
    Forecaster(id=k, version="vf-1", kind="rule" if bd == (0.0, 1.0) else "score",
               owner_module="desk.forecast.adapters.vendors3", family=_fam(k), targets=t, contexts_declared=_N,
               laws=Laws(bounded=bd, warmup=w, abstains=ab, costed="own_name_cs_impact"),
               inputs=("daily bars",) + (("SPY close",) if k.startswith(("lector.rs", "lector.rrr", "lector.nvars")) else ()),
               grade="NEW", evidence=(src,), sign=sg, note=NOTE, ledger=_ledger(lk))
    for k, (sg, bd, w, ab, t, src, lk) in SPEC.items()) + tuple(
    Forecaster(id=k, version="vf-1", kind="score", owner_module="desk.forecast.adapters.vendors3", family="index",
               targets=t, contexts_declared=("market",),
               laws=Laws(bounded=bd, warmup=0, abstains=True, costed="index: SPY 1 bp + 2 bp auction"),
               inputs=inp, grade="NEW", evidence=(src,), sign=sg, note=NOTE,
               ledger=_ledger({"access_pit": "closed daily values of " + "/".join(inp),
                               "holdable": "index context; SPY / ETF paper only"}))
    for k, (sg, bd, t, inp, src) in MKT_SPEC.items())


# ---------------------------------------------------------------- numeric helpers (bars 0..t only)
def _win(x, n):
    return np.lib.stride_tricks.sliding_window_view(np.asarray(x, float), n)


def pct_rank_incl(x, n):
    """CH 1-Month RS:23-31: the percentile of today's value among the last n values (today included) by the vendor's array
    code: index of today's value in the ascending sort (the count strictly under it) / (n - 1) x 100; NaN when a NaN is in
    the window or before n values"""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _win(x, n)
    less = (w < w[:, -1:]).sum(axis=1)
    out[n - 1:] = np.where(np.isfinite(w).all(axis=1), less / (n - 1) * 100.0, np.nan)
    return out


def pct_rank_prior(x, n):
    """Pine ta.percentrank: the share of the previous n values that are <= today's value, x 100 (today excluded)"""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    w = _win(x, n + 1)
    le = (w[:, :-1] <= w[:, -1:]).sum(axis=1)
    out[n:] = np.where(np.isfinite(w).all(axis=1), le / n * 100.0, np.nan)
    return out


def wma(x, n):
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        wt = np.arange(1, n + 1, dtype=float)
        out[n - 1:] = _win(x, n) @ (wt / wt.sum())
    return out


def lin_slope(x, n):
    """OLS slope per bar over the last n values (Pine linreg(x,n,0) - linreg(x,n,1))"""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        i = np.arange(n) - (n - 1) / 2.0
        out[n - 1:] = _win(x, n) @ (i / (i @ i))
    return out


def _sub(n, idx, arr):
    out = np.full(n, np.nan)
    out[idx] = arr
    return out


def _ta_atr(h, l, c, n=14):
    """Pine ta.atr: RMA of the true range"""
    return wilder(true_range(h, l, c), n)


def _cross_up(x, level):
    p = lag(x)
    return (p <= level) & (x > level)


def _cross_dn(x, level):
    p = lag(x)
    return (p >= level) & (x < level)


# ---------------------------------------------------------------- GainzAlgo (GZ:34-60)
def gainz_rule(o, h, l, c, stab=0.5, rsi_idx=50, delta=5, rsi_len=14, no_repeat=True):
    n = len(c)
    out = np.full(n, np.nan)
    tr = true_range(h, l, c)
    r = rsi(c, rsi_len)
    po, pc = lag(o), lag(c)
    with np.errstate(invalid="ignore", divide="ignore"):
        stable = (tr > 0) & (np.abs(c - o) / tr > stab)
    bull = (pc < po) & (c > o) & (c > po)
    bear = (pc > po) & (c < o) & (c < po)
    cd = lag(c, delta)
    raw_buy = bull & stable & (r < rsi_idx) & (c < cd)
    raw_sell = bear & stable & (r > 100 - rsi_idx) & (c > cd)
    last = 0
    start = rsi_len + 1
    for t in range(start, n):
        ok_b = raw_buy[t] and (not no_repeat or last != 1)
        ok_s = raw_sell[t] and (not no_repeat or last != -1)
        v = 0.0
        if ok_b and not ok_s:
            v, last = 1.0, 1
        elif ok_s and not ok_b:
            v, last = -1.0, -1
        out[t] = v
    return out


# ---------------------------------------------------------------- relative strength family
def rrr(rs):
    """CH Relative Robustness Rotation.txt: (blended RS-Ratio, adjusted blended RS-Momentum) of an RS line (100 c / SPY)"""
    def ratio(a, b):
        sm = _e0(rs, a)
        return 100.0 * sm / _e0(sm, b)
    r = 0.6 * ratio(15, 21) + 0.4 * ratio(26, 34)

    def mom(a, b):
        sm = _e0(r, a)
        return 100.0 * sm / _e0(sm, b)
    mb = 0.6 * mom(8, 15) + 0.4 * mom(15, 26)
    ch1 = np.r_[np.nan, np.diff(r)]
    chl = (r - lag(r, 5)) / 5.0
    vol = np.full(len(r), np.nan)
    if len(r) > 20:
        vol[20:] = _win(ch1[1:], 20).std(axis=1)               # population stdev of the last 20 one-period changes
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(np.isfinite(vol) & (vol > 1e-12), (ch1 - chl) / (vol + 1e-12), np.nan)
    adj = np.nan_to_num(0.10 * np.tanh(np.clip(z, -20, 20)), nan=0.0)
    return r, mb + adj


def nvars(c, a, sc, sa, lookback=50, norm=100, fast=8, slow=20):
    """CH NVARS:76-163 on aligned series (the name and SPY); returns (rs, fast-over-slow sign)"""
    with np.errstate(invalid="ignore", divide="ignore"):
        ni = np.where(sa > 0, np.r_[np.nan, np.diff(sc)] / sa, np.nan)
        nc = np.where(a > 0, np.r_[np.nan, np.diff(c)] / a, np.nan)
    raw = roll(nc, lookback, "sum") - roll(ni, lookback, "sum")
    rms = np.sqrt(roll(raw * raw, norm, "mean"))
    with np.errstate(invalid="ignore", divide="ignore"):
        rs = np.where(np.isfinite(rms) & (rms > 0), raw / rms, np.nan)
    f, s = roll(rs, fast, "mean"), roll(rs, slow, "mean")
    return rs, np.where(np.isfinite(f) & np.isfinite(s), _sign(f - s), np.nan)


# ---------------------------------------------------------------- stage ladder (CH Candles Stage Analysis.txt)
STAGES = ("1a", "1b", "2a", "2b", "2c", "2d", "3a", "3b", "4a", "4b", "4c")


def stages(o, h, l, c):
    e10, e20, s50 = ema(c, 10), ema(c, 20), roll(c, 50, "mean")
    a = _ta_atr(h, l, c, 14)
    with np.errstate(invalid="ignore", divide="ignore"):
        x = np.where((a != 0) & (s50 != 0), ((c - s50) / s50) / (a / c), np.nan)
    spread = np.maximum(np.maximum(e10, e20), s50) - np.minimum(np.minimum(e10, e20), s50)
    e10up = e10 >= lag(e10)
    up_al = (c >= e10) & (e10 >= e20) & (e20 >= s50)
    dn_al = (c < e20) & (e10 < e20) & (e20 < s50)
    bo = c >= lag(roll(h, 20, "max"))
    bd = c < lag(roll(l, 20, "min"))
    basing = (np.abs(c - s50) < 1.0 * a) & (spread < 1.5 * a)
    below = (c > e20) & (c < s50) & (e20 > e10) & (e20 < s50)
    ext_bull, exh_bull = up_al & (x >= 7) & (x < 11), up_al & (x >= 11)
    ext_bear = dn_al & (x < -7)
    fade_a = (c >= s50) & (e10 >= e20) & ((c < e10) | ~e10up)
    fade_b = ~ext_bear & (c >= s50) & (e10 < e20)
    mean_rev = ~up_al & ~dn_al & ~(basing | below) & (c > e20) & (e10 >= e20)
    code = np.select([exh_bull, ext_bull, ext_bear, fade_a, fade_b, up_al & bo, up_al, dn_al & bd, dn_al, basing | below,
                      mean_rev], [6, 5, 11, 7, 8, 4, 3, 10, 9, 1, 2], default=12)
    names = {"1a": 1, "1b": 2, "2a": 3, "2b": 4, "2c": 5, "2d": 6, "3a": 7, "3b": 8, "4a": 9, "4b": 10, "4c": 11}
    ok = np.isfinite(s50) & np.isfinite(a) & np.isfinite(x) & np.isfinite(bo.astype(float))
    ok &= np.isfinite(lag(roll(h, 20, "max"))) & np.isfinite(lag(e10))
    return {k: np.where(ok, (code == v).astype(float), np.nan) for k, v in names.items()}


# ---------------------------------------------------------------- unfilled close-adjusted gaps
def close_gaps(h, l, c, a14, lookback=80, max_gaps=100):
    """CH Unfilled Close-Adjusted Gaps.txt: a gap-up is low > close[1] (zone close[1]..low), a gap-down high < close[1];
    a later close through the far side removes it, a later close inside tightens the near boundary to that close; removed
    after `lookback` sessions; the oldest dropped over `max_gaps`. Returns (net, distance in ATR to the nearest boundary)"""
    n = len(c)
    net, dist = np.zeros(n), np.full(n, np.nan)
    gaps = []                                  # [dir, lower, upper, active_lower, active_upper, start]
    for t in range(n):
        if t >= 1 and np.isfinite(c[t - 1]):
            pc = c[t - 1]
            keep = []
            for g in gaps:
                d, lo, up, al, au, s = g
                if t - s > lookback or (d == 1 and t > s and c[t] < lo) or (d == -1 and t > s and c[t] > up):
                    continue
                if t > s and lo < c[t] < up:
                    if d == 1 and c[t] < au:
                        g[4] = c[t]
                    if d == -1 and c[t] > al:
                        g[3] = c[t]
                keep.append(g)
            gaps = keep
            if l[t] > pc:
                gaps.append([1, pc, l[t], pc, l[t], t])
            elif h[t] < pc:
                gaps.append([-1, h[t], pc, h[t], pc, t])
            # a bar cannot be both; the vendor adds a new gap before the sweep, which leaves it untouched (not a future bar)
            while len(gaps) > max_gaps:
                gaps.pop(0)
        if gaps:
            nu = sum(1 for g in gaps if g[0] > 0)
            net[t] = (nu - (len(gaps) - nu)) / len(gaps)
            if np.isfinite(a14[t]) and a14[t] > 0:
                lines = [g[4] if g[0] > 0 else g[3] for g in gaps]
                j = min(lines, key=lambda v: abs(v - c[t]))
                dist[t] = (j - c[t]) / a14[t]
    return net, dist


# ---------------------------------------------------------------- calibrated RSI (CH Calibrated RSI Position Zones.txt)
def crsi_classes(long_re, short_re, trend, bull_reg, bear_reg, rising, falling):
    """CH Calibrated RSI Position Zones.txt:378-432: the four classes of a re-entry, long +1 / short -1, in the vendor's order
    (continuation, early reversal, mean reversion, countertrend; each takes what the earlier ones left)"""
    s_long = long_re & (trend == 1) & bull_reg & rising
    s_short = short_re & (trend == -1) & bear_reg & falling
    e_long = long_re & ~s_long & bear_reg & rising
    e_short = short_re & ~s_short & bull_reg & falling
    m_long = long_re & ~s_long & ~e_long & (trend >= 0) & ~falling
    m_short = short_re & ~s_short & ~e_short & (trend <= 0) & ~rising
    c_long = long_re & ~s_long & ~e_long & ~m_long
    c_short = short_re & ~s_short & ~e_short & ~m_short
    f = lambda a, b: a.astype(float) - b.astype(float)      # noqa: E731
    return {"cont": f(s_long, s_short), "early": f(e_long, e_short), "mr": f(m_long, m_short), "ctr": f(c_long, c_short)}


def crsi(c, h, l, rsi_len=14, sm=3, fast=42, slow=126, sig_len=63, rank_len=126, dead=0.10, z_in=1.0, z_out=2.0, z_ext=2.75,
         slope_len=10, slope_sm=3, slope_dead=0.05, trend_len=200, trend_n=10, lo_t=10.0, hi_t=90.0):
    n = len(c)
    raw = rsi(c, rsi_len)
    idx = np.flatnonzero(np.isfinite(raw))
    nan = np.full(n, np.nan)
    res = {k: nan.copy() for k in ("z", "cont", "early", "mr", "ctr")}
    if len(idx) < 60:
        return res
    s = idx[0]
    r = raw[s:]
    p = np.clip(r / 100.0, 0.001, 0.999)
    lg = _e0(np.log(p / (1 - p)), sm)
    mu_f, mu_s = _e0(lg, fast), _e0(lg, slow)
    fres = lg - mu_f
    sig_f = np.sqrt(np.maximum(_e0(fres * fres, sig_len), 1e-6))
    z = fres / sig_f
    zsig = _e0(z, 3)
    zrank = pct_rank_prior(z, rank_len)
    sres = lg - mu_s
    sig_s = np.sqrt(np.maximum(_e0(sres * sres, slow), 1e-6))
    reg = (mu_f - mu_s) / sig_s
    bull_reg, bear_reg = reg > dead, reg < -dead
    sl = lin_slope(mu_f, slope_len)
    score = _e0(np.nan_to_num(sl * (slope_len - 1) / sig_s), slope_sm)
    rising, falling = score > slope_dead, score < -slope_dead
    cc = c[s:]
    tema = _e0(cc, trend_len)
    tslope = tema - lag(tema, trend_n)
    trend = np.where((cc > tema) & (tslope > 0), 1, np.where((cc < tema) & (tslope < 0), -1, 0))
    zr1 = lag(zrank)
    long_re = _cross_up(z, -z_out) & (zr1 <= lo_t) & (zsig > lag(zsig))
    short_re = _cross_dn(z, z_out) & (zr1 >= hi_t) & (zsig < lag(zsig))
    cls = crsi_classes(long_re, short_re, trend, bull_reg, bear_reg, rising, falling)
    ok = np.isfinite(z) & np.isfinite(zr1) & np.isfinite(score) & np.isfinite(tslope)
    for k, x in cls.items():
        res[k][s:] = np.where(ok, x, np.nan)
    res["z"][s:] = z
    return res


# ---------------------------------------------------------------- TradingView technical ratings
def _stoch_k(h, l, c, n):
    hh, ll = roll(h, n, "max"), roll(l, n, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(hh > ll, 100.0 * (c - ll) / (hh - ll), np.nan)


def _vote(buy, sell):
    return np.asarray(buy, bool).astype(float) - np.asarray(sell, bool).astype(float)


def tv_votes(o, h, l, c, v):
    """(oscillator votes (11, n), MA votes (15, n)), each +1 / 0 / -1. The conditions are TradingView's Help Center table;
    where the table leaves a trend or a displacement open the desk's reading is named in the comment."""
    n = len(c)
    osc = []
    r = rsi(c, 14)
    osc.append(_vote((r < 30) & (r > lag(r)), (r > 70) & (r < lag(r))))
    k = roll(_stoch_k(h, l, c, 14), 3, "mean")
    d = roll(k, 3, "mean")
    osc.append(_vote((k < 20) & (d < 20) & (k > d), (k > 80) & (d > 80) & (k < d)))
    tp = (h + l + c) / 3
    md = roll(tp, 20, "mean")
    dev = np.array(pd.Series(tp).rolling(20, min_periods=20).apply(lambda w: np.abs(w - w.mean()).mean(), raw=True))
    with np.errstate(invalid="ignore", divide="ignore"):
        cci = (tp - md) / (0.015 * dev)
    osc.append(_vote((cci < -100) & (cci > lag(cci)), (cci > 100) & (cci < lag(cci))))
    pdi, mdi, adx = V2._dmi(h, l, c)
    osc.append(_vote((pdi > mdi) & (adx > 20) & (adx > lag(adx)), (pdi < mdi) & (adx > 20) & (adx < lag(adx))))
    hl2 = (h + l) / 2
    ao = roll(hl2, 5, "mean") - roll(hl2, 34, "mean")
    a1, a2 = lag(ao), lag(ao, 2)
    # desk reading of "turns upward while positive for two bars": positive now and last bar, rising now, falling before
    osc.append(_vote(((ao > 0) & (a1 <= 0)) | ((ao > 0) & (a1 > 0) & (ao > a1) & (a1 < a2)),
                     ((ao < 0) & (a1 >= 0)) | ((ao < 0) & (a1 < 0) & (ao < a1) & (a1 > a2))))
    mom = c - lag(c, 10)
    osc.append(_vote(mom > lag(mom), mom < lag(mom)))
    macd = _e0(c, 12) - _e0(c, 26)
    sig = _e0(macd, 9)
    osc.append(_vote(macd > sig, macd < sig))
    rr = rsi(c, 14)
    hh, ll = roll(rr, 14, "max"), roll(rr, 14, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        sr = np.where(hh > ll, 100.0 * (rr - ll) / (hh - ll), np.nan)
    sk = roll(sr, 3, "mean")
    sd = roll(sk, 3, "mean")
    s50 = roll(c, 50, "mean")
    # the table says "buy in a downtrend / sell in an uptrend" without a trend definition: close vs SMA50 is the desk's
    osc.append(_vote((c < s50) & (sk < 20) & (sd < 20) & (sk > sd), (c > s50) & (sk > 80) & (sd > 80) & (sk < sd)))
    hh14, ll14 = roll(h, 14, "max"), roll(l, 14, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        wr = np.where(hh14 > ll14, -100.0 * (hh14 - c) / (hh14 - ll14), np.nan)
    osc.append(_vote((wr < -80) & (wr > lag(wr)), (wr > -20) & (wr < lag(wr))))
    e13 = ema(c, 13)
    bull, bear = h - e13, l - e13
    up_t, dn_t = e13 > lag(e13), e13 < lag(e13)         # trend: the slope of the EMA13 (the table does not define it)
    osc.append(_vote(up_t & (bear < 0) & (bear > lag(bear)), dn_t & (bull > 0) & (bull < lag(bull))))
    pc = lag(c)
    bp = c - np.minimum(l, pc)
    trg = np.maximum(h, pc) - np.minimum(l, pc)
    with np.errstate(invalid="ignore", divide="ignore"):
        avg = [roll(bp, w, "sum") / roll(trg, w, "sum") for w in (7, 14, 28)]
    uo = 100.0 * (4 * avg[0] + 2 * avg[1] + avg[2]) / 7.0
    osc.append(_vote(uo > 70, uo < 30))
    ma = []
    for w in (10, 20, 30, 50, 100, 200):
        ma.append(_vote(c > roll(c, w, "mean"), c < roll(c, w, "mean")))
        ma.append(_vote(c > ema(c, w), c < ema(c, w)))
    hull = wma(2 * wma(c, 4) - wma(c, 9), 3)
    ma.append(_vote(c > hull, c < hull))
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = roll(c * v, 20, "sum") / roll(v, 20, "sum")
    ma.append(_vote(c > vw, c < vw))
    conv = (roll(h, 9, "max") + roll(l, 9, "min")) / 2
    base = (roll(h, 26, "max") + roll(l, 26, "min")) / 2
    sa = (conv + base) / 2
    sb = (roll(h, 52, "max") + roll(l, 52, "min")) / 2        # the leading spans at today's bar (not displaced: PIT)
    ma.append(_vote((sa > sb) & (base > sa) & (conv > base) & (c > conv), (sa < sb) & (base < sa) & (conv < base) & (c < conv)))
    ok_o = np.isfinite(np.vstack([r, k, d, cci, adx, ao, mom, macd, sk, sd, wr, bull, uo, lag(r), lag(cci), lag(adx),
                                  lag(mom), lag(wr), lag(bear), lag(bull), a2])).all(axis=0)
    return np.vstack(osc), np.vstack(ma), ok_o


def straddle_rate(h, l, c, a14, H=5, k=2.0, win=40, minn=20):
    lab = V2.straddle(h, l, c, a14, H, k)
    known = lag(np.abs(lab), H)
    return roll(known, win, "mean", minp=minn)


# ---------------------------------------------------------------- the Vibe-Trading zoo (agent/src/factors/base.py semantics)
def _sdiv(a, b, eps=1e-12):
    """base.safe_div: a / (b + eps sign(b)), NaN where b is 0 or NaN"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b + eps * np.sign(b)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = a / d
    return np.where((d == 0) | ~np.isfinite(r), np.nan, r)


def _delta(x, k):
    return np.asarray(x, float) - lag(x, k)


def _ts_rank(x, n):
    """base.ts_rank: the last value's average-tie rank share in its n-window; NaN with any NaN in the window"""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = _win(x, n)
    last = w[:, -1:]
    less = (w < last).sum(axis=1)
    eq = (w == last).sum(axis=1)
    out[n - 1:] = np.where(np.isfinite(w).all(axis=1), (less + 0.5 * (eq + 1)) / n, np.nan)
    return out


def _ts_corr(x, y, n):
    r = pd.Series(np.asarray(x, float)).rolling(n, min_periods=n).corr(pd.Series(np.asarray(y, float))).to_numpy()
    return np.where(np.isfinite(r), r, np.nan)


def _ts_std(x, n):
    return pd.Series(np.asarray(x, float)).rolling(n, min_periods=n).std(ddof=1).to_numpy()


def _tern(cond, a, b):
    """base _where_ternary: the chosen branch, NaN where it is not finite"""
    out = np.where(cond, a, b)
    return np.where(np.isfinite(out), out, np.nan)


def zoo(o, h, l, c, v):
    z = {}
    adv20 = roll(v, 20, "mean")
    z["a101.006"] = -1.0 * _ts_corr(o, v, 10)
    d7 = _delta(c, 7)
    e7 = (-1.0 * _ts_rank(np.abs(d7), 60)) * np.sign(d7)
    z["a101.007"] = np.where(np.isfinite(adv20), _tern(adv20 < v, e7, -1.0), np.nan)
    d1 = _delta(c, 1)
    mn5, mx5 = roll(d1, 5, "min"), roll(d1, 5, "max")
    z["a101.009"] = np.where(np.isfinite(mn5) & np.isfinite(mx5), _tern(mn5 > 0, d1, _tern(mx5 < 0, d1, -1.0 * d1)), np.nan)
    z["a101.012"] = np.sign(_delta(v, 1)) * (-1.0 * d1)
    m8, s8, m2 = roll(c, 8, "mean"), _ts_std(c, 8), roll(c, 2, "mean")
    vadv = _sdiv(v, adv20)
    z["a101.021"] = np.where(np.isfinite(m8) & np.isfinite(s8) & np.isfinite(m2) & np.isfinite(vadv),
                             np.where((m8 + s8) < m2, -1.0, np.where(m2 < (m8 - s8), 1.0, np.where(vadv >= 1.0, 1.0, -1.0))), np.nan)
    mh = roll(h, 20, "mean")
    z["a101.023"] = np.where(np.isfinite(mh), _tern(mh < h, -1.0 * _delta(h, 2), 0.0 * c), np.nan)
    m100 = roll(c, 100, "mean")
    x24 = _sdiv(_delta(m100, 100), lag(c, 100))
    z["a101.024"] = np.where(np.isfinite(x24), _tern(x24 <= 0.05, -1.0 * (c - roll(c, 100, "min")), -1.0 * _delta(c, 3)), np.nan)
    z["a101.026"] = -1.0 * roll(_ts_corr(_ts_rank(v, 5), _ts_rank(h, 5), 5), 3, "max")
    ret = c / lag(c) - 1.0
    z["a101.035"] = _ts_rank(v, 32) * (1.0 - _ts_rank(c + h - l, 16)) * (1.0 - _ts_rank(ret, 32))
    z["a101.043"] = _ts_rank(_sdiv(v, adv20), 20) * _ts_rank(-1.0 * _delta(c, 7), 8)
    # GTJA191
    raw = _sdiv((c - l) - (h - c), h - l)
    z["gtja.002"] = -1.0 * _delta(raw, 1)
    pc = lag(c)
    up, dn = c > pc, c < pc
    ref = np.where(up, np.minimum(l, pc), np.where(dn, np.maximum(h, pc), c))
    move = np.where(up | dn, c - ref, 0.0)
    move = np.where(np.isfinite(c) & np.isfinite(pc), move, np.nan)
    z["gtja.003"] = roll(move, 6, "sum")
    mid = (h + l) / 2.0
    x9 = (mid - lag(mid)) * _sdiv(h - l, v)
    ok9 = np.isfinite(x9)
    z["gtja.009"] = np.where(ok9, _ewm_alpha(np.nan_to_num(x9), 2.0 / 7.0), np.nan)
    z["gtja.011"] = roll(raw * v, 6, "sum")
    z["gtja.014"] = _delta(c, 5)
    z["gtja.015"] = _sdiv(o, pc) - 1.0
    z["gtja.018"] = _sdiv(c, lag(c, 5))
    p5 = lag(c, 5)
    z["gtja.019"] = np.where(np.isfinite(c) & np.isfinite(p5),
                             np.where(c < p5, _sdiv(c - p5, p5), np.where(c > p5, _sdiv(c - p5, c), 0.0)), np.nan)
    p6 = lag(c, 6)
    z["gtja.020"] = _sdiv(c - p6, p6) * 100.0
    z["gtja.021"] = lin_slope(roll(c, 6, "mean"), 6)
    # qlib158
    z["qlib.kmid"] = _sdiv(c - o, o)
    z["qlib.klen"] = _sdiv(h - l, o)
    z["qlib.kmid2"] = _sdiv(c - o, h - l)
    top, bot = np.maximum(o, c), np.minimum(o, c)
    z["qlib.kup"] = _sdiv(h - top, o)
    z["qlib.kup2"] = _sdiv(h - top, h - l)
    z["qlib.klow"] = _sdiv(bot - l, o)
    z["qlib.klow2"] = _sdiv(bot - l, h - l)
    z["qlib.ksft"] = _sdiv(2.0 * c - h - l, o)
    z["qlib.ksft2"] = _sdiv(2.0 * c - h - l, h - l)
    z["qlib.roc20"] = _sdiv(lag(c, 20), c)
    return z


def _ewm_alpha(x, alpha):
    """pandas ewm(alpha, adjust=False).mean(): y0 = x0, y = alpha x + (1 - alpha) y_prev (the GTJA SMA(x, n, m))"""
    return pd.Series(np.asarray(x, float)).ewm(alpha=alpha, adjust=False).mean().to_numpy()


# ---------------------------------------------------------------- the per-name function
def fn(b, m):
    o, h, l, c, v = (np.asarray(b[k], float) for k in ("o", "h", "l", "c", "v"))
    n = len(c)
    out = {}
    out["gainzalgo.rulegate"] = gainz_rule(o, h, l, c)
    # relative strength to SPY
    spy = on(b["d"], m["spy"]) if "d" in b and "spy" in m else np.full(n, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        rs = np.where((spy > 0) & np.isfinite(spy), c / spy, np.nan)
    pcs = {}
    for N, key in ((26, "lector.rs26"), (78, "lector.rs78"), (156, "lector.rs156")):
        pcs[N] = pct_rank_incl(rs, N)
        out[key] = pcs[N]
    p = pcs[26]
    above = np.where(np.isfinite(p), p > 50, False)
    run = np.zeros(n)
    for t in range(n):
        run[t] = (run[t - 1] + 1 if t else 1) if above[t] else 0
    cnt = np.zeros(n)
    ab = above.astype(float)
    for j in range(1, 16):
        cnt[j:] += ab[:n - j]
    okp = np.isfinite(lag(p, 15))
    out["lector.rs_run15"] = np.where(np.isfinite(p), (run >= 15).astype(float), np.nan)
    out["lector.rs_12of15"] = np.where(np.isfinite(p) & okp, (cnt >= 12).astype(float), np.nan)
    # rotation + NVARS on the rows where the SPY value exists
    idx = np.flatnonzero(np.isfinite(rs))
    for k in ("lector.rrr_ratio", "lector.rrr_mom", "lector.rrr_q", "lector.nvars", "lector.nvars_fs"):
        out[k] = np.full(n, np.nan)
    if len(idx) > 140:
        r, mo = rrr(100.0 * rs[idx])
        warm = np.arange(len(idx)) < 130
        r, mo = np.where(warm, np.nan, r), np.where(warm, np.nan, mo)
        out["lector.rrr_ratio"] = _sub(n, idx, r - 100.0)
        out["lector.rrr_mom"] = _sub(n, idx, mo - 100.0)
        q = np.where(r >= 100, np.where(mo >= 100, 1.0, -0.5), np.where(mo >= 100, 0.5, -1.0))
        out["lector.rrr_q"] = _sub(n, idx, np.where(np.isfinite(r) & np.isfinite(mo), q, np.nan))
    sa = on(b["d"], m["spy_atr"]) if "spy_atr" in m and "d" in b else np.full(n, np.nan)
    sc = spy
    ok = np.isfinite(sa) & np.isfinite(sc)
    idn = np.flatnonzero(ok)
    if len(idn) > 160:
        a = _ta_atr(h, l, c, 14)[idn]
        rsv, fs = nvars(c[idn], a, sc[idn], sa[idn])
        rsv, fs = _nb(rsv, 150), _nb(fs, 175)
        out["lector.nvars"] = _sub(n, idn, rsv)
        out["lector.nvars_fs"] = _sub(n, idn, fs)
    # stage ladder, gaps, calibrated RSI
    st = stages(o, h, l, c)
    for k, x in st.items():
        out["lector.stg_" + k] = x
    a14 = _ta_atr(h, l, c, 14)
    net, dist = close_gaps(h, l, c, a14)
    out["lector.cgap"] = _nb(net, 14)
    out["lector.cgap_dist"] = _nb(dist, 14)
    cr = crsi(c, h, l)
    for k, x in (("z", "lector.crsi_z"), ("cont", "lector.crsi_cont"), ("early", "lector.crsi_early"),
                 ("mr", "lector.crsi_mr"), ("ctr", "lector.crsi_ctr")):
        out[x] = _nb(cr[k], 200)
    # TradingView ratings
    osc, mav, ok_o = tv_votes(o, h, l, c, v)
    vo = np.where(ok_o, osc.mean(axis=0), np.nan)
    okm = np.isfinite(np.vstack([roll(c, 200, "mean"), ema(c, 200), roll(c, 52, "max")])).all(axis=0)
    ok_ma = okm & (np.arange(n) >= 200)
    vm = np.where(ok_ma, mav.mean(axis=0), np.nan)
    out["tv.osc"] = _nb(vo, 60)
    out["tv.ma"] = vm
    out["tv.rating"] = np.where(np.isfinite(vo) & np.isfinite(vm), 0.5 * (vo + vm), np.nan)
    out["gs.straddle5"] = straddle_rate(h, l, c, a14)
    for k, x in zoo(o, h, l, c, v).items():
        out[k] = _nb(x, ZOO[k][0])
    return out


_NAME_IDS = [f.id for f in FORECASTERS if f.family != "index"]
_name_compute = wrap(fn, _NAME_IDS)


# ---------------------------------------------------------------- market inputs
def market3(mkt):
    """CM.market(mkt) plus what the vendors3 forecasters read: SPY's ATR14 (Pine ta.atr of the guarded bars)"""
    from .. import data as D
    m = _market(mkt)
    s = mkt["spy"]
    if isinstance(s, dict) and all(k in s for k in ("o", "h", "l", "c", "d")):
        ok = D.guard(s)
        h, l, c = (np.asarray(s[k], float)[ok] for k in ("h", "l", "c"))
        m["spy_atr"] = pd.Series(_ta_atr(h, l, c, 14), index=np.asarray(s["d"])[ok])
    return m


# ---------------------------------------------------------------- VIX Mood Ring (CH Market Action Pulse & VIX Mood Ring.txt)
def score_vix(x):
    x = np.asarray(x, float)
    s = np.select([x < 13, x < 17, x < 20, x < 25, x < 32],
                  [100.0, 100 - (x - 13) * 15 / 4, 85 - (x - 17) * 15 / 3, 70 - (x - 20) * 10 / 5, 60 - (x - 25) * 40 / 7],
                  default=20 - np.minimum(20.0, (x - 32) * 2.5))
    return np.where(np.isfinite(x), np.clip(s, 0, 100), np.nan)


def score_term(r):
    r = np.asarray(r, float)
    s = np.select([r < 0.85, r < 0.95, r < 1.0],
                  [80 + np.minimum(20.0, (0.85 - r) * 100), 80 - (r - 0.85) * 22 / 0.10, 58 - (r - 0.95) * 28 / 0.05],
                  default=30 - np.minimum(30.0, (r - 1.0) * 300))
    return np.where(np.isfinite(r), np.clip(s, 0, 100), np.nan)


def score_vvix(x):
    x = np.asarray(x, float)
    s = np.select([x < 85, x < 100, x < 115, x < 130],
                  [100.0, 90 - (x - 85) * 20 / 15, 70 - (x - 100) * 15 / 15, 55 - (x - 115) * 20 / 15],
                  default=35 - np.minimum(35.0, (x - 130) * 2.0))
    return np.where(np.isfinite(x), np.clip(s, 0, 100), np.nan)


def score_skew(x):
    x = np.asarray(x, float)
    s = np.select([x < 115, x < 130, x < 145], [100.0, 82 - (x - 115) * 16 / 15, 66 - (x - 130) * 25 / 15],
                  default=41 - np.minimum(41.0, (x - 145) * 2.0))
    return np.where(np.isfinite(x), np.clip(s, 0, 100), np.nan)


def mood_ring(vix, vix3m, skew, vvix=None):
    """(composite with all four legs, composite renormalised over the legs present, divergence code) per session.
    Divergence: 0 none, 1 complacency trap, 2 backwardation, 3 panic easing, 4 whipsaw risk, 5 all clear (lines 718-760)"""
    vix, vix3m, skew = (np.asarray(x, float) for x in (vix, vix3m, skew))
    vv = np.full(len(vix), np.nan) if vvix is None else np.asarray(vvix, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        term = np.where(vix3m != 0, vix / vix3m, np.nan)
    sc = {"v": (score_vix(vix), 0.35), "t": (score_term(term), 0.25), "s": (score_skew(skew), 0.25),
          "x": (score_vvix(vv), 0.15)}
    full = np.where(np.all([np.isfinite(s) for s, _ in sc.values()], axis=0),
                    sum(s * w for s, w in sc.values()), np.nan)
    num = sum(np.where(np.isfinite(s), s * w, 0.0) for s, w in sc.values())
    den = sum(np.where(np.isfinite(s), w, 0.0) for s, w in sc.values())
    part = np.where((den > 0) & np.isfinite(sc["v"][0]) & np.isfinite(sc["t"][0]) & np.isfinite(sc["s"][0]), num / den, np.nan)
    comp = (np.isfinite(vix) & np.isfinite(skew)) & ((vix < 17) & (skew > 145) | ((lag(vix, 2) < vix) & (lag(skew, 2) > skew)))
    back = np.isfinite(term) & (term >= 1.0)
    resolved = np.isfinite(term) & np.isfinite(lag(term)) & (term < 1.0) & (lag(term) >= 1.0)
    hot = np.isfinite(vv) & (vv >= 101)
    whip = np.isfinite(vix) & np.isfinite(lag(vix)) & (vix < lag(vix)) & hot
    clear = np.isfinite(vix) & np.isfinite(term) & np.isfinite(vv) & np.isfinite(skew) & (vix < 17) & (term < 0.95) & \
        (vv < 100) & (skew < 130)
    div = np.select([comp, back, resolved, whip, clear], [1, 2, 3, 4, 5], default=0)
    return full, part, div


FLOOR = {0: 0.0, 1: 75.0, 2: 95.0, 3: 40.0, 4: 80.0, 5: 10.0}


def vmr_risk(composite, div):
    base = np.where(np.isfinite(composite), np.clip(100.0 - composite, 0, 100), np.nan)
    fl = np.vectorize(FLOOR.get)(div).astype(float)
    return np.where(np.isfinite(base), np.maximum(base, fl), np.where(div > 0, fl, np.nan))


# ---------------------------------------------------------------- Market Action Pulse + RAM (lines 225-375, 803-877)
def mcclellan(adv, dec, fast=19, slow=39, msi=10, zlen=63):
    """(summation, MSI EMA, previous MSI EMA, previous summation, oscillator, z) per observation, the vendor's recursion:
    EMAs seeded with the first net-advance value, summation = cumulative oscillator, a missing day skips the update"""
    n = len(adv)
    S = {k: np.full(n, np.nan) for k in ("sum", "msi", "msi_prev", "sum_prev", "osc", "z")}
    ef = es = osc = summ = msiv = None
    win = []
    af, asl, am = 2.0 / (fast + 1), 2.0 / (slow + 1), 2.0 / (msi + 1)
    prev_sum = prev_msi = None
    z = np.nan
    for t in range(n):
        a, d = adv[t], dec[t]
        if np.isfinite(a) and np.isfinite(d) and a + d != 0:
            net = 1000.0 * (a - d) / (a + d)
            ef = net if ef is None else ef + af * (net - ef)
            es = net if es is None else es + asl * (net - es)
            osc = ef - es
            prev_sum, prev_msi = summ, msiv
            summ = osc if summ is None else summ + osc
            msiv = summ if msiv is None else msiv + am * (summ - msiv)
            win.append(osc)
            if len(win) > zlen:
                win.pop(0)
            if len(win) == zlen:
                mu = sum(win) / zlen
                sd = max(sum(x * x for x in win) / zlen - mu * mu, 0.0) ** 0.5
                z = (osc - mu) / sd if sd > 0 else np.nan
            else:
                z = np.nan
        if osc is not None:
            S["sum"][t], S["msi"][t], S["osc"][t], S["z"][t] = summ, msiv, osc, z
            S["sum_prev"][t] = np.nan if prev_sum is None else prev_sum
            S["msi_prev"][t] = np.nan if prev_msi is None else prev_msi
    return S


def zweig_thrust(adv, dec, ma=10, lo=0.40, hi=0.615, within=10):
    """CL6: the 10-day mean of adv / (adv + dec) rising from under 0.40 to over 0.615 within 10 sessions: 0/1 per session"""
    adv, dec = np.asarray(adv, float), np.asarray(dec, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = adv / (adv + dec)
    s = roll(r, ma, "mean")
    out = np.where(np.isfinite(s), 0.0, np.nan)
    for t in range(len(s)):
        if np.isfinite(s[t]) and s[t] > hi:
            w = s[max(0, t - within):t]
            if np.isfinite(w).any() and np.nanmin(w) < lo:
                out[t] = 1.0
    return out


def pulse(dates, c, adv, dec):
    """Market Action Pulse state 0..5 (RED..GREEN) per session from the health ETF's closes and the breadth counts"""
    n = len(c)
    e3, e5, e10, e20 = (_e0(c, k) for k in (3, 5, 10, 20))
    c1 = lag(c)
    above5 = (c > e5) & (e5 > lag(e5))
    dbuy = (c > e10) & (c > e20) & (e10 > e20)
    brk = (c1 < lag(e3)) & (lag(e3) < lag(e5)) & (c > e5) & (e3 < e5) & (e5 < e10)
    strong = (c1 < c) & (c > e5) & (e5 > e20) & (e20 < e10)
    wk = pd.to_datetime(pd.Series(dates)).dt.strftime("%G-%V").to_numpy()
    wbuy = np.zeros(n, bool)
    closes, cur = [], None
    for t in range(n):
        if cur is not None and wk[t] != wk[t - 1]:
            closes.append(c[t - 1])
        recent = closes[-9:] + [c[t]]
        r20 = closes[-19:] + [c[t]]
        if len(recent) == 10 and len(r20) == 20:
            s10, s20 = sum(recent) / 10, sum(r20) / 20
            wbuy[t] = c[t] > s10 and c[t] > s20 and s10 > s20
        cur = t
    M = mcclellan(adv, dec)
    up = (M["sum"] > M["msi"]) & (M["msi"] > M["msi_prev"])
    att = ~up & (M["sum"] > M["sum_prev"]) & (M["osc"] > 0)
    oscok = M["osc"] < 50.0
    all_y = above5 & dbuy & wbuy
    any_y = above5 | dbuy | wbuy
    state = np.select([up & all_y, oscok & ((brk & wbuy) | (strong & wbuy)), up, att & any_y, ~up & ~att & any_y],
                      [5, 4, 3, 2, 1], default=0).astype(float)
    ok = np.isfinite(M["osc"]) & np.isfinite(M["msi_prev"]) & np.isfinite(M["sum_prev"]) & (np.arange(n) >= 20)
    return np.where(ok, state, np.nan), M["z"]


def target_risk(c, hi252, e5, e10, e20):
    with np.errstate(invalid="ignore", divide="ignore"):
        dist = np.maximum(0.0, 100.0 * (hi252 - c) / hi252)
    prox = np.clip(100.0 - dist * (100.0 / 15.0), 0, 100)
    trend = 25.0 * (c < e5) + 30.0 * (c < e10) + 45.0 * (c < e20)
    return np.clip(0.55 * prox + 0.45 * trend, 0, 100)


def ram(map_risk, breadth_risk, vmr_r, tgt_risk):
    fam = ((0.35, map_risk), (0.30, breadth_risk), (0.20, vmr_r), (0.15, tgt_risk))
    num = sum(np.where(np.isfinite(x), w * x, 0.0) for w, x in fam)
    den = sum(np.where(np.isfinite(x), w, 0.0) for w, x in fam)
    return np.where(den > 0, np.clip(num / np.where(den > 0, den, 1.0), 0, 100), np.nan)


MAP_RISK = {5: 10.0, 4: 20.0, 3: 40.0, 2: 60.0, 1: 80.0, 0: 95.0}


# ---------------------------------------------------------------- the index series
def _ser(mkt, key):
    if mkt is None or key not in mkt or mkt[key] is None:
        return None
    return V2._etf(mkt, key)


def series(m, mkt=None):
    out = {}
    spy = m["spy"]
    idx = spy.index

    def al(name):
        s = m.get(name)
        if s is None and mkt is not None and name in mkt:
            s = V2._etf(mkt, name) if name not in ("vvix", "adv", "dec") else pd.Series(mkt[name], dtype=float)
        return None if s is None else s.reindex(idx).to_numpy(float)
    vix, v3, sk, vv = (al(k) for k in ("vix", "vix3m", "skew", "vvix"))
    if vix is not None and v3 is not None and sk is not None:
        full, part, div = mood_ring(vix, v3, sk, vv)
        risk = vmr_risk(part, div)
        for k, x in (("lector.vmr", full), ("lector.vmr3", part), ("lector.vmr_rv", part)):
            out[k] = pd.Series(x, index=idx)
        out["lector.vmr_risk"] = pd.Series(risk, index=idx)
        vr = risk
    else:
        vr = np.full(len(idx), np.nan)
    adv, dec = al("adv"), al("dec")
    health = None
    for k in ("qqqe", "rsp"):
        s = m.get(k)
        if s is None and mkt is not None and k in mkt:
            s = V2._etf(mkt, k)
        if s is not None:
            health = s.reindex(idx)
            break
    mp = bz = tg = np.full(len(idx), np.nan)
    if health is not None and adv is not None and dec is not None and health.notna().all():
        st, z = pulse(idx.to_numpy(), health.to_numpy(float), adv, dec)
        out["lector.pulse"] = pd.Series(st, index=idx)
        mp = np.vectorize(lambda x: MAP_RISK.get(int(x), np.nan) if np.isfinite(x) else np.nan)(st).astype(float)
        bz = np.where(np.isfinite(z), np.clip(50.0 - 22.5 * z, 0, 100), np.nan)
    if health is not None:
        hc = health.to_numpy(float)
        if np.isfinite(hc).all():
            hi = roll(hc, 252, "max", minp=1)           # closes stand in for the vendor's 252-day highs
            tg = target_risk(hc, hi, ema(hc, 5), ema(hc, 10), ema(hc, 20))
    if np.isfinite(vr).any() or np.isfinite(mp).any() or np.isfinite(tg).any():
        out["lector.ram"] = pd.Series(ram(mp, bz, vr, tg), index=idx)
    bnd = _ser(mkt, "bnd") if mkt is not None else m.get("bnd")
    if bnd is not None:
        b = bnd.reindex(idx)
        r1 = lambda s: s.shift(21) / s.shift(252) - 1.0           # noqa: E731  12-1 month, today never enters
        rs_, rb = r1(spy), r1(b)
        sig = np.where(rs_.notna() & rb.notna(), np.where((rs_ > rb) & (rs_ > 0), 1.0, -1.0), np.nan)
        out["composer.dualmom12_1"] = pd.Series(sig, index=idx)
    return out


_SER = {}


def compute(a, mkt, m=None, ser=None):
    out = _name_compute(a, mkt, m=m if m is not None else market3(mkt))
    n = len(a["c"])
    if ser is None:
        mm = m if m is not None else market3(mkt)
        hit = _SER.get(id(mm))
        if mkt is None and hit is not None and hit[0] is mm:       # the deep search passes one m for every name
            ser = hit[1]
        else:
            ser = series(mm, mkt)
            if mkt is None:
                _SER.clear()
                _SER[id(mm)] = (mm, ser)
    d = np.asarray(a["d"])
    for k in MKT_SPEC:
        s = ser.get(k)
        x = pd.Series(d).map(s).to_numpy(float) if s is not None else np.full(n, np.nan)
        out[k] = np.where(np.isfinite(x), x, np.nan)
    return out
