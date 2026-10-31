"""Vendor-method forecasters, clean-room from the published definitions in scratchpad vendors/*.md (§3 "Methods",
§5 rows marked backtestable now) and vendors/_muse_root.md GENOME. No vendor code, data or parameter fitting: where a
vendor leaves a constant unpublished the desk's choice is named here. Daily bars only (the desk's 5-minute/1-hour
history is too short for an intraday search; the intraday variants are deferred in REGISTRY.md).

Chaikin Power Gauge, the 5 technical factors (chaikin.md §9, powergauge.html):
  chk.cmf21         Chaikin money flow: sum(MFM v, 21) / sum(v, 21), MFM = ((c - l) - (h - c)) / (h - l), 0 when h = l
  chk.dema_roc42    "Price Trend ROC": the 42-session change of (c / DEMA200 - 1); DEMA = 2 EMA - EMA(EMA)
  chk.vol30_90      "Volume Trend": mean volume 30 / mean volume 90 - 1
  chk.px_dema200    "Price Strength": c / DEMA200 - 1
  chk.rs126         "RS vs S&P 500, 6 months": c / c[-126] - SPY / SPY[-126]
  chk.tech5         the five, each as tanh of its own 252-session z score, averaged (vendor weights are sealed:
                    equal weights is the desk's choice)
  chk.trendclip     close under DEMA200 (the trend clip as a veto, F-CHK-2): sign -1
ScalpFlip EA v1.9 (scalpflip-ea.md §3, mq5:527-585), on the last closed daily bar:
  sf.fade           -sign(c - o); a doji (body <= 10% of range: the EA's doji test is unpublished, desk choice) is 0
  sf.smart          SMART mode: bull = 2[c > SMA20] + 2[RSI14 < 30], bear = 2[c < SMA20] + 2[RSI14 > 70] (the
                    volume term is off by default); bullish candle: -1 if bear >= 3, +1 if bull >= 3, else -1 (fade);
                    bearish: +1 if bull >= 3, -1 if bear >= 3, else +1; doji 0
QuantCharts / QANTRADING (quantcharts.md §3 time model):
  qc.streak         the signed count of consecutive higher (+) or lower (-) closes ending at d, clipped to +-20;
                    a reversal forecaster (sign -1)
ICT C2 + CISD (ict2023trader-indicators.md §3), daily as the HTF and the LTF (the 1H leg is deferred):
  ict.c2            +1 if l < l[-1] and c > l[-1] (sweep and reclaim of the prior low); -1 for the mirror; 0 else
  ict.c2cisd        +1 on the first bar within 5 after a bullish C2 whose close exceeds the CISD level (the highest
                    open of the consecutive down-candle run, up to 10 bars, before the C2 bar; fallback the C2 bar's
                    high if it is green, else its open), the C2 low unbroken; -1 for the mirror; 0 else
Edgeful daily variants (edgeful.md §3; the intraday ORB/IB reports are deferred):
  eg.gapfill        an unfilled opening gap at the close: -(o / c[-1] - 1) when the day's range never reached the prior
                    close, else 0 (a forecast of the fill), clipped to +-1
  eg.pdr_break      prior-day-range break at the close: +1 above the prior high, -1 below the prior low, 0 inside
CorrectionScope AI v1 (correctionscope-ai.md §3, ind.mq5 L141-197, MIT):
  cs.correction     P = 0.35 div + 0.25 volDrop + 0.20 candle + 0.15 waveExt + 0.05 volPressure, in an up-wave
                    (the last confirmed 3-bar swing low >= 5 bars back, RSI14 > 60) -P, in a down-wave (mirror,
                    RSI14 < 40) +P, else 0. div = clip(-/+ (RSI - RSI[-4]) / 20, 0, 1); volDrop = clip((SMA20 v - v) /
                    SMA20 v, 0, 1); candle = 1 opposite engulfing, 0.5 doji (body <= 0.2 range); waveExt =
                    clip(wave length / ATR14 / 4, 0, 1); volPressure = clip(ATR14 / c x 5, 0, 1)
AlgoPoint regime score (algopoint.md §3):
  ap.regime         S = 0.30 ADXnorm + 0.30 volratio + 0.25 ER + 0.15 consistency in [0, 1]; ADXnorm = clip((ADX14 -
                    15) / 20, 0, 1); volratio = clip(ATR14 / ATR50 - 0.5, 0, 1) (normalisation unpublished, desk
                    choice); ER = |c - c[-10]| / sum |dc| over 10; consistency = share of the last 20 daily changes
                    with the sign of c - c[-20]. Targets realized vol (trend vs chop)
  ap.trend          S x sign(c - c[-20]) (trend continuation)
SqueezeMetrics per-ticker suite (squeezemetrics.md §2):
  sm.P              mean(ret, 21) / ADM21, ADM21 = mean(|ret|, 21); in [-1, 1]
  sm.V              ADM21 - mean(ADM21, 21) (volatility trend); targets realized vol
Others from §5 rows marked backtestable now:
  vol.garch         GEXRADAR's fixed-parameter GARCH(1,1): s2_t = w + 0.08 r_t^2 + 0.90 s2_{t-1}, variance targeting
                    w = 0.02 var252; value 0.5 ln s2 (a log-vol forecast); targets realized vol
  risk.semidev      Danelfin "Low Risk": sqrt(mean(min(r, 0)^2, 500)); sign -1
  sr.hi52           Stock Rover sentiment leg (George-Hwang): c / max(h, 252)
  tai.pct           Zeiierman Trading Activity Index: ln(c v)'s percentile within its own trailing 252; targets
                    realized vol
  alt.antichase     AltIndex anti-chase: r126 >= +100% (a veto, sign -1)"""
import numpy as np
import pandas as pd

from .. import Forecaster, Laws, Ledger
from ._common import atr, ema, lag, market, ret, roll, rsi, wilder, wrap

INF = float("inf")
UP = ("up_excess_5", "up_excess_20")
UPL = ("up_excess_20", "up_excess_60")
RV = ("realized_vol_20",)
SPEC = {   # id: (sign, bounds, warmup, abstains, targets, source)
    "chk.cmf21": (1, (-1.0, 1.0), 21, False, UPL, "chaikin.md §9"),
    "chk.dema_roc42": (1, (-INF, INF), 241, False, UPL, "chaikin.md §9"),
    "chk.vol30_90": (1, (-1.0, INF), 90, False, UPL, "chaikin.md §9"),
    "chk.px_dema200": (1, (-INF, INF), 199, False, UPL, "chaikin.md §9"),
    "chk.rs126": (1, (-INF, INF), 126, False, UPL, "chaikin.md §9"),
    "chk.tech5": (1, (-1.0, 1.0), 494, True, UPL, "chaikin.md §5 F-CHK-1"),
    "chk.trendclip": (-1, (0.0, 1.0), 199, False, UPL, "chaikin.md §5 F-CHK-2"),
    "sf.fade": (1, (-1.0, 1.0), 0, False, UP, "scalpflip-ea.md §3, §5"),
    "sf.smart": (1, (-1.0, 1.0), 19, False, UP, "scalpflip-ea.md §3"),
    "qc.streak": (-1, (-20.0, 20.0), 1, False, UP, "quantcharts.md §3, §5"),
    "ict.c2": (1, (-1.0, 1.0), 1, False, UP, "ict2023trader-indicators.md §3, §5"),
    "ict.c2cisd": (1, (-1.0, 1.0), 1, False, UP, "ict2023trader-indicators.md §3, §5"),
    "eg.gapfill": (1, (-1.0, 1.0), 1, False, UP, "edgeful.md §3, §5 (daily variant)"),
    "eg.pdr_break": (1, (-1.0, 1.0), 1, False, UP, "edgeful.md §3 (daily ORB/prior-range analogue)"),
    "cs.correction": (1, (-1.0, 1.0), 22, False, UP, "correctionscope-ai.md §3, §5"),
    "ap.regime": (1, (0.0, 1.0), 64, False, RV, "algopoint.md §3, §5"),
    "ap.trend": (1, (-1.0, 1.0), 64, False, UP, "algopoint.md §3, §5"),
    "sm.P": (1, (-1.0, 1.0), 21, True, ("up_excess_20",), "squeezemetrics.md §2, §5"),
    "sm.V": (1, (-INF, INF), 42, False, RV, "squeezemetrics.md §2, §5"),
    "vol.garch": (1, (-INF, INF), 252, False, RV, "gexradar.md §5"),
    "risk.semidev": (-1, (0.0, INF), 500, False, UPL, "danelfin.md §5 F-DAN-3"),
    "sr.hi52": (1, (0.0, INF), 251, False, UPL, "stockrover.md §5 F-SR-1"),
    "tai.pct": (1, (0.0, 1.0), 251, False, RV, "zeiierman.md §5"),
    "alt.antichase": (-1, (0.0, 1.0), 0, False, UPL, "altindex.md §5"),
}
FORECASTERS = tuple(
    Forecaster(id=k, version="p2-1", kind="rule" if bd == (0.0, 1.0) and k.endswith(("clip", "chase")) else "score",
               owner_module="desk.forecast.adapters.vendors", family="vendor." + k.split(".")[0], targets=t,
               laws=Laws(bounded=bd, warmup=w, abstains=ab, costed="own_name_cs_impact"),
               inputs=("daily bars", "SPY"), grade="NEW", evidence=(src,), sign=sg,
               ledger=Ledger(payer="unknown (vendor claim unverified)", speed_decay="vendor horizon 1-60 sessions",
                             decisive_test="BH over the run + walk-forward + same-sign 2023+ holdout, net of costs"))
    for k, (sg, bd, w, ab, t, src) in SPEC.items())


def _clip01(x):
    return np.clip(x, 0.0, 1.0)


def _z_tanh(x, n=252):
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (x - roll(x, n, "mean")) / roll(x, n, "std")
    return np.tanh(np.where(np.isfinite(z), z, np.nan))


def _streak(c):
    d = np.sign(np.r_[0.0, np.diff(c)])
    out = np.zeros(len(c))
    for i in range(1, len(c)):
        if d[i] > 0:
            out[i] = out[i - 1] + 1 if out[i - 1] > 0 else 1
        elif d[i] < 0:
            out[i] = out[i - 1] - 1 if out[i - 1] < 0 else -1
    return np.clip(out, -20, 20)


def _cisd(o, h, l, c, c2):
    n = len(c)
    out = np.zeros(n)
    for j in np.flatnonzero(c2 != 0):
        s = int(c2[j])
        k, lv = j - 1, None
        run = []
        while k >= 0 and len(run) < 10 and ((c[k] < o[k]) if s > 0 else (c[k] > o[k])):
            run.append(o[k])
            k -= 1
        if run:
            lv = max(run) if s > 0 else min(run)
        else:
            lv = (h[j] if c[j] > o[j] else o[j]) if s > 0 else (l[j] if c[j] < o[j] else o[j])
        ext = l[j] if s > 0 else h[j]
        for t in range(j + 1, min(n, j + 6)):
            if (s > 0 and l[t] < ext) or (s < 0 and h[t] > ext):
                break
            if (s > 0 and c[t] > lv) or (s < 0 and c[t] < lv):
                if out[t] == 0:
                    out[t] = s
                break
    return out


def _last_swing(lows, highs):
    """(index of the last confirmed 3-bar swing low, of swing high) at each bar; a swing at i confirms at i + 1"""
    n = len(lows)
    sl = np.zeros(n, bool)
    sh = np.zeros(n, bool)
    sl[1:-1] = (lows[1:-1] < lows[:-2]) & (lows[1:-1] < lows[2:])
    sh[1:-1] = (highs[1:-1] > highs[:-2]) & (highs[1:-1] > highs[2:])
    idx = np.arange(n, dtype=float)
    cl = pd.Series(np.where(np.r_[False, sl[:-1]], idx - 1, np.nan)).ffill().to_numpy()
    ch = pd.Series(np.where(np.r_[False, sh[:-1]], idx - 1, np.nan)).ffill().to_numpy()
    return cl, ch


def _correction(o, h, l, c, v):
    n = len(c)
    r14 = rsi(c, 14)
    a14 = atr(h, l, c, 14)
    slope = r14 - lag(r14, 4)
    vs = roll(v, 20, "mean")
    with np.errstate(invalid="ignore", divide="ignore"):
        vdrop = _clip01((vs - v) / vs)
        volp = _clip01(a14 / c * 5)
    cl, ch = _last_swing(l, h)
    out = np.zeros(n)
    rng_ = h - l
    body = np.abs(c - o)
    doji = body <= 0.2 * rng_
    for t in range(n):
        if not (np.isfinite(r14[t]) and np.isfinite(a14[t]) and np.isfinite(slope[t]) and np.isfinite(vs[t])):
            out[t] = np.nan
            continue
        up = np.isfinite(cl[t]) and t - cl[t] >= 5 and r14[t] > 60
        dn = np.isfinite(ch[t]) and t - ch[t] >= 5 and r14[t] < 40
        if up == dn:
            continue
        if up:
            i = int(cl[t])
            wave = np.max(h[i:t + 1]) - l[i]
            div = _clip01(-slope[t] / 20)
            eng = c[t] < o[t] and c[t - 1] > o[t - 1] and o[t] >= c[t - 1] and c[t] <= o[t - 1]
        else:
            i = int(ch[t])
            wave = h[i] - np.min(l[i:t + 1])
            div = _clip01(slope[t] / 20)
            eng = c[t] > o[t] and c[t - 1] < o[t - 1] and o[t] <= c[t - 1] and c[t] >= o[t - 1]
        cand = 1.0 if eng else (0.5 if doji[t] else 0.0)
        ext = _clip01(wave / a14[t] / 4) if a14[t] > 0 else 0.0
        p = 0.35 * div + 0.25 * vdrop[t] + 0.20 * cand + 0.15 * ext + 0.05 * volp[t]
        out[t] = -p if up else p
    return out


def _adx(h, l, c, n=14):
    up, dn = np.r_[0.0, np.diff(h)], -np.r_[0.0, np.diff(l)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    from ._common import true_range
    tr = wilder(true_range(h, l, c), n)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi, mdi = 100 * wilder(pdm, n) / tr, 100 * wilder(mdm, n) / tr
        dx = np.where(pdi + mdi > 0, 100 * np.abs(pdi - mdi) / (pdi + mdi), 0.0)
    adx = wilder(np.nan_to_num(dx), n)
    adx[:2 * n] = np.nan
    return adx


def fn(b, m):
    from scipy.signal import lfilter
    d, o, h, l, c, v = (b["d"], b["o"], b["h"], b["l"], b["c"], b["v"])
    n = len(c)
    r = ret(c)
    out = {}
    rng_ = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        mfm = np.where(rng_ > 0, ((c - l) - (h - c)) / rng_, 0.0)
        out["chk.cmf21"] = np.clip(roll(mfm * v, 21, "sum") / roll(v, 21, "sum"), -1, 1)   # running-sum round-off
        e1 = ema(c, 200)
        e2 = ema(np.nan_to_num(e1, nan=c[0] if n else 0.0), 200)
        dema = 2 * e1 - e2
        dema[:199] = np.nan
        pxd = c / dema - 1
        out["chk.px_dema200"] = pxd
        out["chk.dema_roc42"] = pxd - lag(pxd, 42)
        out["chk.vol30_90"] = roll(v, 30, "mean") / roll(v, 90, "mean") - 1
        spy126 = pd.Series(np.asarray(d)).map(m["spy126"]).to_numpy(float)
        out["chk.rs126"] = ret(c, 126) - spy126
        five = np.vstack([_z_tanh(out[k]) for k in ("chk.cmf21", "chk.dema_roc42", "chk.vol30_90", "chk.px_dema200",
                                                    "chk.rs126")])
        out["chk.tech5"] = np.where(np.isfinite(five).all(axis=0), five.mean(axis=0), np.nan)
        out["chk.trendclip"] = np.where(np.isfinite(dema), (c < dema).astype(float), np.nan)
        body = np.abs(c - o)
        doji = body <= 0.1 * rng_
        out["sf.fade"] = np.where(doji, 0.0, -np.sign(c - o))
        sma = roll(c, 20, "mean")
        r14 = rsi(c, 14)
        bull = 2 * (c > sma) + 2 * (r14 < 30)
        bear = 2 * (c < sma) + 2 * (r14 > 70)
        sm_ = np.where(c > o, np.where(bear >= 3, -1.0, np.where(bull >= 3, 1.0, -1.0)),
                       np.where(bull >= 3, 1.0, np.where(bear >= 3, -1.0, 1.0)))
        sm_ = np.where(doji, 0.0, sm_)
        sm_[:19] = np.nan
        out["sf.smart"] = sm_
        st = _streak(c)
        st[:1] = np.nan
        out["qc.streak"] = st
        pl, ph = lag(l), lag(h)
        b2 = (l < pl) & (c > pl)
        s2 = (h > ph) & (c < ph)
        c2 = np.where(b2 & ~s2, 1.0, np.where(s2 & ~b2, -1.0, 0.0))
        c2[:1] = np.nan
        out["ict.c2"] = c2
        cc = _cisd(o, h, l, c, np.nan_to_num(c2))
        cc[:1] = np.nan
        out["ict.c2cisd"] = cc
        pc = lag(c)
        gap = o / pc - 1
        unf = np.where(gap > 0, l > pc, np.where(gap < 0, h < pc, False))
        gf = np.clip(np.where(unf, -gap, 0.0), -1, 1)
        gf[:1] = np.nan
        out["eg.gapfill"] = gf
        pb = np.where(c > ph, 1.0, np.where(c < pl, -1.0, 0.0))
        pb[:1] = np.nan
        out["eg.pdr_break"] = pb
        out["cs.correction"] = _correction(o, h, l, c, v)
        adxn = _clip01((_adx(h, l, c) - 15) / 20)
        vr = _clip01(atr(h, l, c, 14) / atr(h, l, c, 50) - 0.5)
        dc = np.abs(np.r_[np.nan, np.diff(c)])
        er = np.abs(c - lag(c, 10)) / roll(dc, 10, "sum")
        er = np.where(np.isfinite(er), np.clip(er, 0, 1), np.where(np.isfinite(roll(dc, 10, "sum")), 0.0, np.nan))
        dirn = np.sign(c - lag(c, 20))
        sg = np.sign(np.r_[np.nan, np.diff(c)])
        cons = roll((sg == dirn).astype(float), 20, "mean")
        cons[~np.isfinite(dirn)] = np.nan
        S = 0.30 * adxn + 0.30 * vr + 0.25 * er + 0.15 * cons
        S[:64] = np.nan
        out["ap.regime"] = S
        out["ap.trend"] = S * dirn
        adm = roll(np.abs(r), 21, "mean")
        out["sm.P"] = np.clip(np.where(adm > 0, roll(r, 21, "mean") / adm, np.nan), -1, 1)
        out["sm.V"] = adm - roll(adm, 21, "mean")
        r2 = np.nan_to_num(r) ** 2
        var252 = roll(r, 252, "var")
        g = np.full(n, np.nan)
        if n > 252:
            w = 0.02 * var252[252:]
            x = w + 0.08 * r2[252:]
            g[252:] = lfilter([1.0], [1.0, -0.90], x, zi=[0.90 * var252[252]])[0]
        out["vol.garch"] = 0.5 * np.log(np.where(g > 0, g, np.nan))
        out["risk.semidev"] = np.sqrt(roll(np.minimum(r, 0) ** 2, 500, "mean", minp=499))
        out["sr.hi52"] = c / roll(h, 252, "max")
        ldv = np.log(np.where(c * v > 0, c * v, np.nan))
        tai = np.array(pd.Series(ldv).rolling(252, min_periods=252).rank(pct=True).to_numpy())
        out["tai.pct"] = tai
        out["alt.antichase"] = np.where(np.isfinite(ret(c, 126)), (ret(c, 126) >= 1.0).astype(float), 0.0)
    return out


compute = wrap(fn, [f.id for f in FORECASTERS])
