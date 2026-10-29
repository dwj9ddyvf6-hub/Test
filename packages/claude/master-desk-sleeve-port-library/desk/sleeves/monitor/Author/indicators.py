"""src/lib/tensor/indicators.ts (Author-desk@652db7af): series, trueRange, rsi, stochRsi, aroon, adx, macd,
waveTrend, obv, squeeze, utBot, strat, relativeVolume, sessionVwap, moneyFlow — line for line."""
from .. import js
from . import session
from .tmath import ema, highest, linreg_endpoint, lowest, sma, stdev, wilder


def series(bars, key):
    return [b[key] for b in bars]


def true_range(bars):
    out = [None] * len(bars)
    for i, b in enumerate(bars):
        if i == 0:
            out[i] = b["h"] - b["l"]
            continue
        prev = bars[i - 1]["c"]
        out[i] = js.js_max(b["h"] - b["l"], abs(b["h"] - prev), abs(b["l"] - prev))
    return out


def rsi(closes, length):
    out = [None] * len(closes)
    if len(closes) <= length:
        return out
    gain = 0.0
    loss = 0.0
    for i in range(1, length + 1):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gain += d
        else:
            loss -= d
    gain /= length
    loss /= length
    out[length] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    for i in range(length + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = d if d > 0 else 0
        l = -d if d < 0 else 0
        gain = (gain * (length - 1) + g) / length
        loss = (loss * (length - 1) + l) / length
        out[i] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def stoch_rsi(closes, rsi_len=14, stoch_len=14, k_len=3, d_len=3):
    r = rsi(closes, rsi_len)
    raw = [None] * len(closes)
    for i in range(len(r)):
        if r[i] is None:
            continue
        hi = highest(r, stoch_len, i)
        lo = lowest(r, stoch_len, i)
        if hi is None or lo is None or hi == lo:
            if hi is not None and lo is not None:
                raw[i] = 50.0
            continue
        raw[i] = (r[i] - lo) / (hi - lo) * 100
    k = sma(raw, k_len)
    d = sma(k, d_len)
    return {"k": k, "d": d}


def aroon(bars, length=14):
    up = [None] * len(bars)
    down = [None] * len(bars)
    for i in range(length, len(bars)):
        hi_i = lo_i = i
        for j in range(i - length, i + 1):
            if bars[j]["h"] >= bars[hi_i]["h"]:
                hi_i = j
            if bars[j]["l"] <= bars[lo_i]["l"]:
                lo_i = j
        up[i] = (100 * (length - (i - hi_i))) / length
        down[i] = (100 * (length - (i - lo_i))) / length
    return {"up": up, "down": down}


def adx(bars, length=14):
    n = len(bars)
    plus_dm = [None] * n
    minus_dm = [None] * n
    tr = true_range(bars)
    for i in range(1, n):
        up = bars[i]["h"] - bars[i - 1]["h"]
        down = bars[i - 1]["l"] - bars[i]["l"]
        plus_dm[i] = up if (up > down and up > 0) else 0
        minus_dm[i] = down if (down > up and down > 0) else 0
    sm_tr = wilder(tr, length)
    sm_p = wilder(plus_dm, length)
    sm_m = wilder(minus_dm, length)
    plus_di = [None] * n
    minus_di = [None] * n
    dx = [None] * n
    for i in range(n):
        if sm_tr[i] is None or sm_tr[i] == 0 or sm_p[i] is None or sm_m[i] is None:
            continue
        plus_di[i] = (100 * sm_p[i]) / sm_tr[i]
        minus_di[i] = (100 * sm_m[i]) / sm_tr[i]
        den = plus_di[i] + minus_di[i]
        dx[i] = 0 if den == 0 else (100 * abs(plus_di[i] - minus_di[i])) / den
    return {"plusDI": plus_di, "minusDI": minus_di, "adx": wilder(dx, length)}


def macd(closes, fast=12, slow=26, signal=9):
    ef = ema(closes, fast)
    es = ema(closes, slow)
    line = [None if (ef[i] is None or es[i] is None) else ef[i] - es[i] for i in range(len(closes))]
    sig = ema(line, signal)
    hist = [None if (v is None or sig[i] is None) else v - sig[i] for i, v in enumerate(line)]
    return {"line": line, "signal": sig, "hist": hist}


def wave_trend(bars, ch=10, avg=21, smooth=4):
    hlc3 = [(b["h"] + b["l"] + b["c"]) / 3 for b in bars]
    esa = ema(hlc3, ch)
    dev = [None if esa[i] is None else abs(v - esa[i]) for i, v in enumerate(hlc3)]
    d = ema(dev, ch)
    ci = []
    for i, v in enumerate(hlc3):
        if esa[i] is None or d[i] is None or d[i] == 0:
            ci.append(None)
        else:
            ci.append((v - esa[i]) / (0.015 * d[i]))
    wt1 = ema(ci, avg)
    wt2 = sma(wt1, smooth)
    return {"wt1": wt1, "wt2": wt2}


def obv(bars):
    out = [None] * len(bars)
    acc = 0.0
    for i, b in enumerate(bars):
        if i == 0:
            acc = b["v"]
        elif b["c"] > bars[i - 1]["c"]:
            acc += b["v"]
        elif b["c"] < bars[i - 1]["c"]:
            acc -= b["v"]
        out[i] = acc
    return out


def squeeze(bars, length, mom_len):
    closes = series(bars, "c")
    mid = sma(closes, length)
    sd = stdev(closes, length)
    atr = wilder(true_range(bars), length)
    n = len(bars)
    bb_u = [None if (mid[i] is None or sd[i] is None) else mid[i] + 2 * sd[i] for i in range(n)]
    bb_l = [None if (mid[i] is None or sd[i] is None) else mid[i] - 2 * sd[i] for i in range(n)]
    kc_u = [None if (mid[i] is None or atr[i] is None) else mid[i] + 2 * atr[i] for i in range(n)]
    kc_l = [None if (mid[i] is None or atr[i] is None) else mid[i] - 2 * atr[i] for i in range(n)]
    squeezed = []
    for i in range(n):
        if bb_u[i] is None or kc_u[i] is None or bb_l[i] is None or kc_l[i] is None:
            squeezed.append(False)
        else:
            squeezed.append(bb_u[i] < kc_u[i] and bb_l[i] > kc_l[i])
    highs = series(bars, "h")
    lows = series(bars, "l")
    src = []
    for i, c in enumerate(closes):
        hh = highest(highs, length, i)
        ll = lowest(lows, length, i)
        if hh is None or ll is None or mid[i] is None:
            src.append(None)
            continue
        a = ((hh + ll) / 2 + mid[i]) / 2
        src.append(c - a)
    mom = linreg_endpoint(src, mom_len)
    return {"bbUpper": bb_u, "bbMid": mid, "bbLower": bb_l, "kcUpper": kc_u, "kcLower": kc_l,
            "squeezed": squeezed, "mom": mom}


def ut_bot(bars, atr_len=10, sensitivity=1):
    atr = wilder(true_range(bars), atr_len)
    n = len(bars)
    stop = [None] * n
    dr = [None] * n
    for i in range(n):
        if atr[i] is None:
            continue
        n_loss = sensitivity * atr[i]
        close = bars[i]["c"]
        if i == 0 or stop[i - 1] is None or dr[i - 1] is None:
            stop[i] = close - n_loss
            dr[i] = 1
            continue
        ps = stop[i - 1]
        pc = bars[i - 1]["c"]
        if close > ps and pc > ps:
            stop[i] = js.js_max(ps, close - n_loss)
            dr[i] = 1
        elif close < ps and pc < ps:
            stop[i] = js.js_min(ps, close + n_loss)
            dr[i] = -1
        elif close > ps:
            stop[i] = close - n_loss
            dr[i] = 1
        else:
            stop[i] = close + n_loss
            dr[i] = -1
    return {"stop": stop, "dir": dr}


def strat(bars):
    out = [None] * len(bars)
    for i in range(1, len(bars)):
        b, p = bars[i], bars[i - 1]
        inside = b["h"] < p["h"] and b["l"] > p["l"]
        outside = b["h"] > p["h"] and b["l"] < p["l"]
        up = b["h"] > p["h"] and b["l"] >= p["l"]
        down = b["l"] < p["l"] and b["h"] <= p["h"]
        if inside:
            out[i] = "1"
        elif outside:
            out[i] = "3"
        elif up:
            out[i] = "2U"
        elif down:
            out[i] = "2D"
    return out


def relative_volume(bars, length=20):
    out = [None] * len(bars)
    for i in range(length, len(bars)):
        s = 0.0
        ok = True
        for j in range(i - length, i):
            if bars[j]["v"] < 0:
                ok = False
                break
            s += bars[j]["v"]
        if not ok or s == 0:
            continue
        out[i] = bars[i]["v"] / (s / length)
    return out


def session_vwap(bars):
    out = [None] * len(bars)
    day = ""
    pv = 0.0
    vol = 0.0
    for i, b in enumerate(bars):
        key = session.et_parts(b["t"])["ymd"]
        if key != day:
            day = key
            pv = 0.0
            vol = 0.0
        typical = (b["h"] + b["l"] + b["c"]) / 3
        pv += typical * b["v"]
        vol += b["v"]
        out[i] = pv / vol if vol > 0 else None
    return out


def money_flow(bars):
    out = [None] * len(bars)
    acc = 0.0
    for i, b in enumerate(bars):
        typical = (b["h"] + b["l"] + b["c"]) / 3
        p = bars[i - 1] if i > 0 else None
        prev = (p["h"] + p["l"] + p["c"]) / 3 if p else typical
        if typical > prev:
            acc += b["v"]
        elif typical < prev:
            acc -= b["v"]
        out[i] = acc
    return out
