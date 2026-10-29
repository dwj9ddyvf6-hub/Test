"""ChartsLector's four grade-A warnings on a read's own daily bars. Each is the DEEP study's own definition, ported
line for line from the code that measured it (eyes/DEEP/vfl/src/vfl_clx_lib.py; CLX_BRIEF.md blocks F, G, H and P1),
so a caution says what the study measured and nothing else:

  lod_stop   P1: the stop under the session's low, 100 (c - l + 0.1 A) / c, in % of the close; A is the ATR14 of the
             session before (his stop is the low of day less 0.1 ATR)
  gapfill+   G: the close removed more down gaps than up gaps (his unfilled close-adjusted gaps: 80 bars, a gap gone
             once a close crosses its far edge)
  stg+6      F: his candle stage entered 2D, an advance over a rising stack of the 10 and 20-day EMAs and the 50-day
             SMA stretched 11 or more ATR% units over the 50-day
  crsi_ext-  H: his calibrated RSI's z crossed up through 2.75 (the onset of his upper extreme zone)

readings(bars) -> {"lod_stop": the last session's value or None, and for each event the sessions since it fired
                   within the last WINDOW sessions (0 = the last session) or None}
The events count WINDOW sessions back, as the analysis engine's own study of them did (work_ENG eng_2_22: fired on
d-4..d). Context only: nothing here votes, and a read is the same with or without it."""
import math

WINDOW = 5
NAN = float("nan")
ST_2D = 6                                  # his stage codes: 1 1A, 2 1B, 3 2A, 4 2B, 5 2C, 6 2D, 7 3A, 8 3B, 9 4A ...


def _isnan(x):
    return x is None or x != x


def true_range(h, l, c):
    return [h[t] - l[t] if t == 0 else max(h[t] - l[t], abs(h[t] - c[t - 1]), abs(l[t] - c[t - 1]))
            for t in range(len(c))]


def ema_r(x, n, alpha):
    """seeded with the mean of its first n defined values; an undefined input restarts it (NaN there)"""
    out, cnt, s, y = [NAN] * len(x), 0, 0.0, 0.0
    for t, v in enumerate(x):
        if _isnan(v):
            cnt, s = 0, 0.0
            continue
        if cnt < n:
            s += v
            cnt += 1
            if cnt == n:
                y = s / n
                out[t] = y
        else:
            y = y + alpha * (v - y)
            out[t] = y
    return out


def sma(x, n):
    out = [NAN] * len(x)
    for t in range(n - 1, len(x)):
        w = x[t - n + 1:t + 1]
        if not any(_isnan(v) for v in w):
            out[t] = sum(w) / n
    return out


def _xup(a, level, t):
    return t >= 1 and not (_isnan(a[t]) or _isnan(a[t - 1])) and a[t] > level and a[t - 1] <= level


def lod_stop(h, l, c, atr):
    """P1 at the last session: 100 (c - (l - 0.1 A)) / c with A the ATR14 of the session before; None undefined"""
    t = len(c) - 1
    if t < 1 or _isnan(atr[t - 1]):
        return None
    risk = c[t] - (l[t] - 0.1 * atr[t - 1])
    return risk * 100.0 / c[t] if risk > 0 else None


def gapfill(h, l, c):
    """G: per session +1 when the close removed more down gaps than up gaps, -1 the reverse, else 0"""
    gaps, out = [], [0] * len(c)                       # [lower, upper, start, direction]
    for t in range(len(c)):
        if t >= 1:
            if l[t] > c[t - 1]:
                gaps.append([c[t - 1], l[t], t, 1])
            elif h[t] < c[t - 1]:
                gaps.append([h[t], c[t - 1], t, -1])
        up_gone = down_gone = 0
        keep = []
        for g in gaps:
            lo, hi, start, d = g
            if start < t:
                if t - start > 80:
                    continue
                if d == 1 and c[t] < lo:
                    up_gone += 1
                    continue
                if d == -1 and c[t] > hi:
                    down_gone += 1
                    continue
            keep.append(g)
        gaps = keep[-100:]                             # his cap (cannot bind: at most 81 live gaps)
        out[t] = 1 if down_gone > up_gone else -1 if up_gone > down_gone else 0
    return out


def _stage_of(ct, e10, e20, s50, a, x, e10up, hh, ll):
    """his candle stage at one session: the first true line of his priority table (CLX_BRIEF block F)"""
    sp = max(e10, e20, s50) - min(e10, e20, s50)
    up = ct >= e10 >= e20 >= s50
    dn = ct < e20 and e10 < e20 < s50
    if up and x >= 11.0:
        return 6                                       # 2D
    if up and 7.0 <= x < 11.0:
        return 5                                       # 2C
    if dn and x < -7.0:
        return 11                                      # 4C
    if ct >= s50 and e10 >= e20 and (ct < e10 or not e10up):
        return 7                                       # 3A
    if ct >= s50 and e10 < e20:
        return 8                                       # 3B
    if up and ct >= hh:
        return 4                                       # 2B
    if up:
        return 3                                       # 2A
    if dn and ct < ll:
        return 10                                      # 4B
    if dn:
        return 9                                       # 4A
    if (abs(ct - s50) < 1.0 * a and sp < 1.5 * a) or (e20 < ct < s50 and e10 < e20 < s50):
        return 1                                       # 1A
    if ct > e20 and e10 >= e20:
        return 2                                       # 1B
    return 12                                          # NA


def stage_entries(h, l, c, atr):
    """F: per session the stage it entered (its code when it differs from the session before's, both defined), else 0"""
    e10, e20, s50 = ema_r(c, 10, 2.0 / 11.0), ema_r(c, 20, 2.0 / 21.0), sma(c, 50)
    stg, out = [None] * len(c), [0] * len(c)
    for t in range(len(c)):
        if t < 20 or _isnan(s50[t]) or _isnan(atr[t]) or _isnan(e10[t]) or _isnan(e20[t]):
            continue
        a = atr[t]
        ratio = a / c[t] * 100.0
        x = ((c[t] / s50[t] - 1.0) / ratio) * 100.0 if ratio != 0.0 else NAN
        hh, ll = max(h[t - 20:t]), min(l[t - 20:t])
        e10up = not _isnan(e10[t - 1]) and e10[t] >= e10[t - 1]
        stg[t] = _stage_of(c[t], e10[t], e20[t], s50[t], a, x, e10up, hh, ll)
        if stg[t - 1] is not None and stg[t - 1] != stg[t]:
            out[t] = stg[t]
    return out


def crsi_z(c):
    """H: his calibrated RSI's z: the logit of RSI14 smoothed by EMA3, less its EMA42, over the root of EMA63 of the
    squared difference"""
    up, dn = [NAN] * len(c), [NAN] * len(c)
    for t in range(1, len(c)):
        d = c[t] - c[t - 1]
        up[t], dn[t] = max(d, 0.0), max(-d, 0.0)
    g, ls = ema_r(up, 14, 1.0 / 14.0), ema_r(dn, 14, 1.0 / 14.0)
    lg = [NAN] * len(c)
    for t in range(len(c)):
        if _isnan(g[t]) or _isnan(ls[t]):
            continue
        rsi = 100.0 if ls[t] == 0.0 else 0.0 if g[t] == 0.0 else 100.0 * g[t] / (g[t] + ls[t])
        p = min(max(rsi / 100.0, 0.001), 0.999)
        lg[t] = math.log(p / (1.0 - p))
    lc = ema_r(lg, 3, 2.0 / 4.0)
    mu = ema_r(lc, 42, 2.0 / 43.0)
    sq = [NAN if _isnan(a) or _isnan(b) else (a - b) ** 2 for a, b in zip(lc, mu)]
    var = ema_r(sq, 63, 2.0 / 64.0)
    return [NAN if _isnan(v) else (lc[t] - mu[t]) / math.sqrt(max(v, 1e-6)) for t, v in enumerate(var)]


def _since(fired):
    """the sessions since the latest firing within the last WINDOW sessions (0 = the last), else None"""
    n = len(fired)
    for k in range(min(WINDOW, n)):
        if fired[n - 1 - k]:
            return k
    return None


def readings(bars):
    """{lod_stop, gapfill+, stg+6, crsi_ext-} on the read's daily bars (see the module docstring)"""
    h = [float(b["h"]) for b in bars]
    l = [float(b["l"]) for b in bars]
    c = [float(b["c"]) for b in bars]
    if len(c) < 2:
        return {"lod_stop": None, "gapfill+": None, "stg+6": None, "crsi_ext-": None}
    atr = ema_r(true_range(h, l, c), 14, 1.0 / 14.0)
    z = crsi_z(c)
    return {"lod_stop": lod_stop(h, l, c, atr),
            "gapfill+": _since([v == 1 for v in gapfill(h, l, c)]),
            "stg+6": _since([v == ST_2D for v in stage_entries(h, l, c, atr)]),
            "crsi_ext-": _since([_xup(z, 2.75, t) for t in range(len(z))])}
