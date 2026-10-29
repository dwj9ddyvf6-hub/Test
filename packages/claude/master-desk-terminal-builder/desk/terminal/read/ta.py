"""The indicators the desk's chart read measures, one definition each, in the conventions public charts use
(TradingView, StockCharts): simple and exponential averages (an EMA seeds on the simple average of its first window),
Wilder's smoothing for RSI, ATR and ADX, MACD 12/26/9, Bollinger 20/2 on the population deviation, on-balance volume
and anchored VWAP. Inputs are ascending lists of completed daily bars {t, o, h, l, c, v}; every output aligns with its
input, None until a value exists."""
import math

from ... import calendar as cal


def closes(bars):
    return [float(b["c"]) for b in bars]


def sma(xs, n):
    out, s = [None] * len(xs), 0.0
    for i, x in enumerate(xs):
        s += x
        if i >= n:
            s -= xs[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def _seeded(xs, n, step):
    """a recursive average seeded on the simple average of the first n values present"""
    out, prev, seed, k = [None] * len(xs), None, 0.0, 0
    for i, x in enumerate(xs):
        if x is None:
            continue
        if prev is None:
            seed, k = seed + x, k + 1
            if k == n:
                prev = out[i] = seed / n
        else:
            prev = out[i] = step(prev, x)
    return out


def ema(xs, n):
    a = 2.0 / (n + 1)
    return _seeded(xs, n, lambda p, x: p + a * (x - p))


def rma(xs, n):
    """Wilder's smoothing"""
    return _seeded(xs, n, lambda p, x: (p * (n - 1) + x) / n)


def true_range(bars):
    out = []
    for i, b in enumerate(bars):
        h, l = float(b["h"]), float(b["l"])
        if i == 0:
            out.append(h - l)
        else:
            pc = float(bars[i - 1]["c"])
            out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def atr(bars, n=14):
    return rma(true_range(bars), n)


def rsi(xs, n=14):
    gains, losses = [None], [None]
    for p, x in zip(xs, xs[1:]):
        d = x - p
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    g, l = rma(gains, n), rma(losses, n)
    out = [None] * len(xs)
    for i in range(len(xs)):
        if g[i] is not None and l[i] is not None:
            out[i] = 100.0 if l[i] == 0 else 100.0 - 100.0 / (1.0 + g[i] / l[i])
    return out


def macd(xs, fast=12, slow=26, signal=9):
    """(line, signal, histogram)"""
    f, s = ema(xs, fast), ema(xs, slow)
    line = [None if a is None or b is None else a - b for a, b in zip(f, s)]
    sig = ema(line, signal)
    hist = [None if a is None or b is None else a - b for a, b in zip(line, sig)]
    return line, sig, hist


def adx(bars, n=14):
    """(ADX, +DI, -DI), Wilder's"""
    pdm, mdm = [None], [None]
    for p, b in zip(bars, bars[1:]):
        up, dn = float(b["h"]) - float(p["h"]), float(p["l"]) - float(b["l"])
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
    str_, sp, sm = rma(true_range(bars), n), rma(pdm, n), rma(mdm, n)   # TradingView's ta.dmi: TR from the first bar
    pdi, mdi, dx = [None] * len(bars), [None] * len(bars), [None] * len(bars)
    for i in range(len(bars)):
        if str_[i] and sp[i] is not None and sm[i] is not None:
            pdi[i], mdi[i] = 100.0 * sp[i] / str_[i], 100.0 * sm[i] / str_[i]
            den = pdi[i] + mdi[i]
            dx[i] = 0.0 if den == 0 else 100.0 * abs(pdi[i] - mdi[i]) / den
    return rma(dx, n), pdi, mdi


def bollinger(xs, n=20, k=2.0):
    """(middle, upper, lower, width): width = (upper - lower) / middle"""
    mid = sma(xs, n)
    up, lo, wd = [None] * len(xs), [None] * len(xs), [None] * len(xs)
    for i in range(n - 1, len(xs)):
        w = xs[i - n + 1:i + 1]
        m = mid[i]
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        up[i], lo[i] = m + k * sd, m - k * sd
        wd[i] = (up[i] - lo[i]) / m if m else None
    return mid, up, lo, wd


def obv(bars):
    out, acc = [], 0.0
    for i, b in enumerate(bars):
        if i:
            c, pc = float(b["c"]), float(bars[i - 1]["c"])
            acc += float(b.get("v") or 0) * (1 if c > pc else -1 if c < pc else 0)
        out.append(acc)
    return out


def avwap(bars, start):
    """the volume-weighted average price from bar `start` on (None before it): each session at its own VWAP when the
    bar carries one, else at its typical price"""
    out, pv, vv = [None] * len(bars), 0.0, 0.0
    for i in range(max(0, start), len(bars)):
        b = bars[i]
        v = float(b.get("v") or 0)
        px = b.get("vw")                                              # the session's own VWAP when the feed has it
        pv += v * (float(px) if px else (float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0)
        vv += v
        out[i] = pv / vv if vv else None
    return out


def linreg(ys):
    """(slope per step, R squared) of a least-squares line through ys"""
    n = len(ys)
    if n < 3:
        return None, None
    mx, my = (n - 1) / 2.0, sum(ys) / n
    sxx = sum((i - mx) ** 2 for i in range(n))
    sxy = sum((i - mx) * (y - my) for i, y in enumerate(ys))
    syy = sum((y - my) ** 2 for y in ys)
    b = sxy / sxx
    return b, (1.0 if syy == 0 else (sxy * sxy) / (sxx * syy))


def pct_rank(xs, x):
    """the share of xs at or below x, 0..1 (None for an empty list)"""
    xs = [v for v in xs if v is not None]
    return (sum(1 for v in xs if v <= x) / len(xs)) if xs else None


def session_of(b):
    return cal._as_date(float(b["t"]))


def weekly(bars):
    """daily bars rolled into weeks (Monday to Friday), each {t, o, h, l, c, v, first, last}: indexes of its days"""
    out = []
    for i, b in enumerate(bars):
        d = session_of(b)
        wk = d.isocalendar()[:2]
        if out and out[-1]["_wk"] == wk:
            w = out[-1]
            w["h"], w["l"], w["c"] = max(w["h"], float(b["h"])), min(w["l"], float(b["l"])), float(b["c"])
            w["v"] += float(b.get("v") or 0)
            w["last"] = i
        else:
            out.append({"_wk": wk, "t": b["t"], "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                        "c": float(b["c"]), "v": float(b.get("v") or 0), "first": i, "last": i})
    for w in out:
        del w["_wk"]
    return out


def stochastic(bars, n=14, smooth=3):
    """slow %K: the close's place in the n-session range, averaged over `smooth` sessions, 0..100"""
    raw = [None] * len(bars)
    for i in range(n - 1, len(bars)):
        w = bars[i - n + 1:i + 1]
        hi, lo = max(float(b["h"]) for b in w), min(float(b["l"]) for b in w)
        raw[i] = 50.0 if hi == lo else 100.0 * (float(bars[i]["c"]) - lo) / (hi - lo)
    out = [None] * len(bars)
    for i in range(len(bars)):
        w = raw[i - smooth + 1:i + 1] if i >= smooth - 1 else []
        if len(w) == smooth and None not in w:
            out[i] = sum(w) / smooth
    return out


def mfi(bars, n=14):
    """money flow index: RSI's cousin weighted by volume, 0..100"""
    tp = [(float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0 for b in bars]
    out = [None] * len(bars)
    for i in range(n, len(bars)):
        pos = neg = 0.0
        for j in range(i - n + 1, i + 1):
            f = tp[j] * float(bars[j].get("v") or 0)
            if tp[j] > tp[j - 1]:
                pos += f
            elif tp[j] < tp[j - 1]:
                neg += f
        out[i] = 100.0 if neg == 0 else 100.0 - 100.0 / (1.0 + pos / neg)
    return out


def cci(bars, n=20):
    """commodity channel index: the typical price's distance from its average in units of mean deviation"""
    tp = [(float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0 for b in bars]
    out = [None] * len(bars)
    for i in range(n - 1, len(bars)):
        w = tp[i - n + 1:i + 1]
        m = sum(w) / n
        md = sum(abs(x - m) for x in w) / n
        out[i] = 0.0 if md == 0 else (tp[i] - m) / (0.015 * md)
    return out


def _sma_present(xs, n):
    """a simple average over n values that are all present, None otherwise"""
    out = [None] * len(xs)
    for i in range(n - 1, len(xs)):
        w = xs[i - n + 1:i + 1]
        if None not in w:
            out[i] = sum(w) / n
    return out


def stoch_rsi(xs, rsi_n=14, stoch_n=14, k=3, d=3):
    """(%K, %D): the stochastic of the RSI over `stoch_n` sessions, %K its `k`-session average, %D the `d`-session average
    of %K, all 0..100 (TradingView's Stoch RSI; a window in which the RSI does not move reads 50, as stochastic() does)"""
    r = rsi(xs, rsi_n)
    raw = [None] * len(xs)
    for i in range(len(xs)):
        w = r[i - stoch_n + 1:i + 1] if i >= stoch_n - 1 else []
        if len(w) == stoch_n and None not in w:
            hi, lo = max(w), min(w)
            raw[i] = 50.0 if hi == lo else 100.0 * (r[i] - lo) / (hi - lo)
    kk = _sma_present(raw, k)
    return kk, _sma_present(kk, d)


def heikin_ashi(bars):
    """Heikin-Ashi candles aligned with the bars, each {o, h, l, c}: close = (o+h+l+c)/4, open = the average of the
    previous candle's open and close (the first bar's own open and close), high and low the extremes of the bar and
    those two"""
    out, po, pc = [], None, None
    for b in bars:
        o, h, l, c = (float(b[k]) for k in ("o", "h", "l", "c"))
        hc = (o + h + l + c) / 4.0
        ho = (o + c) / 2.0 if po is None else (po + pc) / 2.0
        out.append({"o": ho, "h": max(h, ho, hc), "l": min(l, ho, hc), "c": hc})
        po, pc = ho, hc
    return out
