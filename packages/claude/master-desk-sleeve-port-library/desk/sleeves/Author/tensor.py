"""Author Tensor library — line-by-line ports of Author-desk @652db7af src/lib/tensor/{math,indicators,session,bars,
vector-structure}.ts (blobs: docs/receipts/parity/Author_tensor.json). Bars are dicts {t (epoch ms), o, h, l, c, v,
session}; None stands for the sources' null. Same IEEE-754 operations in the same order, so the values match the
TypeScript bit for bit (proved under Node 22: docs/receipts/parity/Author_tensor.json; its harness left with the
green engine on 2026-10-26)."""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from ..jsport import js_round
from ..v8math import pow as v8pow

TZ = ZoneInfo("America/New_York")
INF = float("inf")


def _fin(v):
    return v is not None and isinstance(v, (int, float)) and math.isfinite(v)


# -- math.ts ---------------------------------------------------------------------------------------------------------
def ema(values, length):
    out = [None] * len(values)
    if not (length > 0) or len(values) < length:
        return out
    k = 2 / (length + 1)
    prev = None
    seed = 0.0
    count = 0
    for i, v in enumerate(values):
        if v is None or not math.isfinite(v):
            continue
        if prev is None:
            seed += v
            count += 1
            if count == length:
                prev = seed / length
                out[i] = prev
        else:
            prev = v * k + prev * (1 - k)
            out[i] = prev
    return out


def sma(values, length):
    out = [None] * len(values)
    s = 0.0
    n = 0
    window = []
    for i, v in enumerate(values):
        window.append(v)
        if v is not None:
            s += v
            n += 1
        if len(window) > length:
            old = window.pop(0)
            if old is not None:
                s -= old
                n -= 1
        if len(window) == length and n == length:
            out[i] = s / length
    return out


def stdev(values, length):
    out = [None] * len(values)
    for i in range(length - 1, len(values)):
        s = 0.0
        n = 0
        for j in range(i - length + 1, i + 1):
            v = values[j]
            if v is None:
                n = -1
                break
            s += v
            n += 1
        if n != length:
            continue
        mean = s / length
        acc = 0.0
        for j in range(i - length + 1, i + 1):
            d = values[j] - mean
            acc += d * d
        out[i] = math.sqrt(acc / length)
    return out


def wilder(values, length):
    out = [None] * len(values)
    prev = None
    seed = 0.0
    count = 0
    for i, v in enumerate(values):
        if v is None:
            continue
        if prev is None:
            seed += v
            count += 1
            if count == length:
                prev = seed / length
                out[i] = prev
        else:
            prev = (prev * (length - 1) + v) / length
            out[i] = prev
    return out


def linreg_endpoint(values, length):
    out = [None] * len(values)
    for i in range(length - 1, len(values)):
        sx = sy = sxy = sxx = 0.0
        ok = True
        x0 = (length - 1) / 2
        for k in range(length):
            y = values[i - length + 1 + k]
            if y is None:
                ok = False
                break
            x = k - x0
            sx += x
            sy += y
            sxy += x * y
            sxx += x * x
        if not ok:
            continue
        mean_y = sy / length
        cov = sxy / length
        var_x = sxx / length
        beta = 0 if var_x == 0 else cov / var_x
        out[i] = mean_y + beta * ((length - 1) / 2)
    return out


def _at(values, j):
    """values[j] with JS out-of-range = undefined (None)."""
    return values[j] if 0 <= j < len(values) else None


def highest(values, length, i):
    mx = -INF
    for j in range(i - length + 1, i + 1):
        v = _at(values, j)
        if v is None:
            return None
        if v > mx:
            mx = v
    return mx if math.isfinite(mx) else None


def lowest(values, length, i):
    mn = INF
    for j in range(i - length + 1, i + 1):
        v = _at(values, j)
        if v is None:
            return None
        if v < mn:
            mn = v
    return mn if math.isfinite(mn) else None


def last_finite(values):
    for v in reversed(values):
        if v is not None and math.isfinite(v):
            return v
    return None


# -- indicators.ts ---------------------------------------------------------------------------------------------------
def series(bars, key):
    return [b[key] for b in bars]


def true_range(bars):
    out = [None] * len(bars)
    for i, b in enumerate(bars):
        if i == 0:
            out[i] = b["h"] - b["l"]
            continue
        prev = bars[i - 1]["c"]
        out[i] = max(b["h"] - b["l"], abs(b["h"] - prev), abs(b["l"] - prev))
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
    out[length] = 100 if loss == 0 else 100 - 100 / (1 + gain / loss)
    for i in range(length + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = d if d > 0 else 0
        l = -d if d < 0 else 0
        gain = (gain * (length - 1) + g) / length
        loss = (loss * (length - 1) + l) / length
        out[i] = 100 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def macd(closes, fast=12, slow=26, signal=9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [None if ef[i] is None or es[i] is None else ef[i] - es[i] for i in range(len(closes))]
    sig = ema(line, signal)
    hist = [None if v is None or sig[i] is None else v - sig[i] for i, v in enumerate(line)]
    return {"line": line, "signal": sig, "hist": hist}


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


# -- session.ts -------------------------------------------------------------------------------------------------------
HOLIDAYS = {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
            "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"}
EARLY_CLOSE = {"2026-11-27": 13 * 60, "2026-12-24": 13 * 60, "2027-11-26": 13 * 60}


def et_parts(ms):
    d = datetime.fromtimestamp(math.floor(ms / 1000), tz=TZ)
    return {"year": d.year, "month": d.month, "day": d.day, "hour": d.hour, "minute": d.minute, "second": d.second,
            "dow": (d.weekday() + 1) % 7, "ymd": f"{d.year}-{d.month:02d}-{d.day:02d}"}


def minutes_of_day(p):
    return p["hour"] * 60 + p["minute"]


def classify_session(ms):
    p = et_parts(ms)
    if p["dow"] in (0, 6) or p["ymd"] in HOLIDAYS:
        return "closed"
    m = minutes_of_day(p)
    close = EARLY_CLOSE.get(p["ymd"], 16 * 60)
    if 4 * 60 <= m < 9 * 60 + 30:
        return "pre"
    if 9 * 60 + 30 <= m < close:
        return "regular"
    if close <= m < 20 * 60:
        return "post"
    return "closed"


def is_signal_session(kind):
    return kind in ("pre", "regular")


INTERVAL_MS = {"1m": 60_000, "2m": 120_000, "5m": 300_000, "10m": 600_000, "1h": 3_600_000, "60m": 3_600_000,
               "2h": 7_200_000, "4h": 14_400_000, "1d": 86_400_000, "1wk": 604_800_000}


def interval_ms(interval):
    return INTERVAL_MS.get(interval, 300_000)


def completed_daily_bars(bars, now):
    """completedDailyBars: drop a still-forming regular-session daily bar."""
    if not bars:
        return bars
    today = et_parts(now)
    p = et_parts(bars[-1]["t"])
    et_min = today["hour"] * 60 + today["minute"]
    rth = 1 <= today["dow"] <= 5 and et_min < 16 * 60
    if rth and p["ymd"] == today["ymd"]:
        return bars[:-1]
    return bars


# -- bars.ts ------------------------------------------------------------------------------------------------------------
def admit_bars(raw, interval, now):
    ms = interval_ms(interval)
    cleaned = []
    last_t = -1
    for b in raw:
        if not (b["o"] > 0 and b["h"] > 0 and b["l"] > 0 and b["c"] > 0):
            continue
        if b["h"] < max(b["o"], b["c"]) or b["l"] > min(b["o"], b["c"]):
            continue
        if b["v"] < 0:
            continue
        if b["t"] <= last_t:
            continue
        last_t = b["t"]
        cleaned.append(b)
    while cleaned and now < cleaned[-1]["t"] + ms:
        cleaned.pop()
    return cleaned


def keep_signal_tape(bars):
    return [b for b in bars if b.get("session") in ("pre", "regular")]


def tag_session(t):
    s = classify_session(t)
    return "post" if s == "closed" else s


# -- vector-structure.ts ----------------------------------------------------------------------------------------------
def _pivot_high(bars, i, r):
    if i < r or i + r >= len(bars):
        return False
    mid = bars[i]["h"]
    for j in range(i - r, i + r + 1):
        if j != i and bars[j]["h"] >= mid:
            return False
    return True


def _pivot_low(bars, i, r):
    if i < r or i + r >= len(bars):
        return False
    mid = bars[i]["l"]
    for j in range(i - r, i + r + 1):
        if j != i and bars[j]["l"] <= mid:
            return False
    return True


def build_zones(bars, atr):
    zones = []
    radius = 3
    for i in range(radius, len(bars) - radius):
        a = atr[i]
        if a is None or a <= 0:
            continue
        if _pivot_high(bars, i, radius):
            zones.append({"id": f"A-s-{js_int(bars[i]['t'])}", "polarity": "supply", "low": bars[i]["h"] - 0.55 * a,
                          "high": bars[i]["h"] + 0.55 * a, "mid": bars[i]["h"], "strength": 0.48, "model": "A",
                          "confirmedAt": bars[i + radius]["t"]})
        if _pivot_low(bars, i, radius):
            zones.append({"id": f"A-d-{js_int(bars[i]['t'])}", "polarity": "demand", "low": bars[i]["l"] - 0.55 * a,
                          "high": bars[i]["l"] + 0.55 * a, "mid": bars[i]["l"], "strength": 0.48, "model": "A",
                          "confirmedAt": bars[i + radius]["t"]})
    last = len(bars) - 1
    window = bars[max(0, last - 149):]
    last_atr = atr[last] if last >= 0 else None
    if len(window) >= 40 and last_atr is not None:
        cell = max(0.25 * last_atr, window[-1]["c"] * 0.001)
        min_p = min(b["l"] for b in window)
        max_p = max(b["h"] for b in window)
        bins = max(8, math.ceil((max_p - min_p) / cell))
        dens = [0.0] * bins
        for idx, b in enumerate(window):
            age = len(window) - 1 - idx
            w = v8pow(0.5, age / 75)
            lo = max(0, math.floor((b["l"] - min_p) / cell))
            hi = min(bins - 1, math.floor((b["h"] - min_p) / cell))
            for k in range(lo, hi + 1):
                dens[k] += w
        ranked = sorted(({"d": d, "i": i} for i, d in enumerate(dens)), key=lambda r: -r["d"])
        ci = math.floor(len(ranked) * 0.22)
        cutoff = ranked[ci]["d"] if ci < len(ranked) else INF
        last_c = bars[last]["c"]

        def add_c(polarity, idxs):
            if not idxs:
                return
            lo = min_p + min(idxs) * cell
            hi = min_p + (max(idxs) + 1) * cell
            if abs(((lo + hi) / 2) - last_c) > 5 * last_atr:
                return
            zones.append({"id": f"C-{polarity}-{idxs[0]}", "polarity": polarity, "low": lo, "high": hi,
                          "mid": (lo + hi) / 2, "strength": 0.55, "model": "C", "confirmedAt": bars[last]["t"]})
        supply = [r["i"] for r in ranked if r["d"] >= cutoff and min_p + r["i"] * cell >= last_c][:3]
        demand = [r["i"] for r in ranked if r["d"] >= cutoff and min_p + (r["i"] + 1) * cell <= last_c][:3]
        add_c("supply", supply)
        add_c("demand", demand)
    merged = []
    for z in zones:
        hit = next((m for m in merged if m["polarity"] == z["polarity"] and not (z["high"] < m["low"] or
                                                                                  z["low"] > m["high"])), None)
        if hit:
            hit["low"] = min(hit["low"], z["low"])
            hit["high"] = max(hit["high"], z["high"])
            hit["mid"] = (hit["low"] + hit["high"]) / 2
            hit["strength"] = min(1, hit["strength"] + 0.12)
            if hit["model"] != z["model"]:
                hit["model"] = "AC"
        else:
            merged.append(dict(z))
    return merged[-12:]


def js_int(x):
    """`${n}` of an integral epoch-ms number."""
    return str(int(x)) if float(x).is_integer() else repr(x)


__all__ = ["ema", "sma", "stdev", "wilder", "linreg_endpoint", "highest", "lowest", "last_finite", "series",
           "true_range", "rsi", "macd", "relative_volume", "et_parts", "minutes_of_day", "classify_session",
           "is_signal_session", "interval_ms", "completed_daily_bars", "admit_bars", "keep_signal_tape",
           "tag_session", "build_zones", "js_round"]
