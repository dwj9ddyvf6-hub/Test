"""Deterministic OHLCV corpora for the monitor parity harnesses: regime-switching daily / intraday paths that
reach the states the monitors look for (trends, pullbacks to the averages, compressions, range breaks, washouts
and reclaims, double bottoms / tops, gaps, dry and heavy volume), on real session timestamps."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk import calendar as cal

ET = ZoneInfo("America/New_York")


def sessions(end, n):
    """n trading days of the desk calendar ending at `end` (inclusive, rolled back to a trading day)."""
    d = date.fromisoformat(end) if isinstance(end, str) else end
    while not cal.is_trading_day(d):
        d -= timedelta(days=1)
    out = []
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


REGIMES = ("up", "down", "range", "squeeze", "crash", "melt", "chop")


def path(rnd, n, px=None, regime_len=(8, 45)):
    """closes + OHLCV for n bars; regimes switch every 8-45 bars."""
    px = px or rnd.choice((rnd.uniform(2, 15), rnd.uniform(15, 120), rnd.uniform(120, 900)))
    out, left, reg = [], 0, "range"
    base_vol = rnd.uniform(2e5, 8e6)
    for i in range(n):
        if left <= 0:
            reg = rnd.choice(REGIMES)
            left = rnd.randint(*regime_len)
        left -= 1
        drift, vol = {"up": (0.004, 0.015), "down": (-0.004, 0.015), "range": (0.0, 0.012),
                      "squeeze": (0.0, 0.004), "crash": (-0.02, 0.03), "melt": (0.012, 0.02),
                      "chop": (0.0, 0.028)}[reg]
        r = rnd.gauss(drift, vol)
        if rnd.random() < 0.02:
            r += rnd.choice((-1, 1)) * rnd.uniform(0.04, 0.15)
        o = px * (1 + rnd.gauss(0, vol / 2.5))
        c = max(0.05, px * (1 + r))
        hi = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = base_vol * rnd.lognormvariate(0, 0.45) * (2.5 if abs(r) > 2.5 * vol else 1.0) * (
            0.5 if reg == "squeeze" else 1.0)
        out.append([o, hi, lo, c, float(int(v))])
        px = c
    return out


def shape_tail(rnd, rows):
    """bend the last bars into a state monitors watch for (a breakout, a breakdown, a double bottom, a pullback to
    the 20-bar mean, an oversold flush, a flat compression) — or leave the path alone."""
    kind = rnd.choice(("none", "none", "breakout", "breakdown", "double_bottom", "double_top", "pullback", "flush",
                       "flat", "reclaim"))
    n = len(rows)
    if n < 30:
        return rows, kind
    closes = [r[3] for r in rows]
    if kind == "breakout":
        hi = max(r[1] for r in rows[-21:-1])
        c = hi * rnd.uniform(1.001, 1.05)
        rows[-1] = [rows[-2][3], c * 1.004, rows[-2][3] * 0.997, c, rows[-1][4] * rnd.choice((0.8, 1.5, 3.0))]
    elif kind == "breakdown":
        lo = min(r[2] for r in rows[-21:-1])
        c = lo * rnd.uniform(0.95, 0.999)
        rows[-1] = [rows[-2][3], rows[-2][3] * 1.003, c * 0.996, c, rows[-1][4] * rnd.choice((0.8, 1.5, 3.0))]
    elif kind in ("double_bottom", "double_top"):
        k = rnd.randint(8, 25)
        j = n - 1 - rnd.randint(4, 6)
        i = max(4, j - k)
        if kind == "double_bottom":
            lv = min(r[2] for r in rows[i - 4:i + 5]) * 0.98
            for idx in (i, j):
                rows[idx][2] = lv * rnd.uniform(0.995, 1.005)
                rows[idx][3] = max(rows[idx][3], rows[idx][2])
                rows[idx][0] = max(rows[idx][0], rows[idx][2])
        else:
            hv = max(r[1] for r in rows[i - 4:i + 5]) * 1.02
            for idx in (i, j):
                rows[idx][1] = hv * rnd.uniform(0.995, 1.005)
                rows[idx][3] = min(rows[idx][3], rows[idx][1])
                rows[idx][0] = min(rows[idx][0], rows[idx][1])
    elif kind == "pullback":
        m = sum(closes[-20:]) / 20
        c = m * rnd.uniform(0.985, 1.02)
        rows[-1] = [rows[-1][0], max(rows[-1][0], c) * 1.003, min(rows[-1][0], c) * 0.997, c, rows[-1][4]]
    elif kind == "flush":
        for idx in range(n - rnd.randint(3, 7), n):
            c = rows[idx - 1][3] * rnd.uniform(0.94, 0.985)
            rows[idx] = [rows[idx - 1][3], rows[idx - 1][3] * 1.002, c * 0.99, c, rows[idx][4] * 1.6]
    elif kind == "flat":
        base = closes[-25]
        for idx in range(n - 25, n):
            c = base * (1 + rnd.gauss(0, 0.002))
            o = base * (1 + rnd.gauss(0, 0.002))
            rows[idx] = [o, max(o, c) * 1.001, min(o, c) * 0.999, c, rows[idx][4] * 0.6]
    elif kind == "reclaim":
        lo = min(r[2] for r in rows[-21:-1])
        c = lo * rnd.uniform(1.0, 1.03)
        rows[-1] = [lo * 0.995, max(c, lo) * 1.004, lo * 0.99, c, rows[-1][4] * 1.3]
    return rows, kind


def daily_bars(rnd, n, end="2026-09-30", decimals=None, shape=True):
    """[{t (session 09:30 ET epoch, the Yahoo daily stamp), o, h, l, c, v}] on desk-calendar sessions."""
    days = sessions(end, n)
    rows = path(rnd, n)
    kind = "none"
    if shape:
        rows, kind = shape_tail(rnd, rows)
    dec = decimals if decimals is not None else rnd.choice((2, 2, 3, 4))
    out = []
    for d, (o, h, l, c, v) in zip(days, rows):
        t = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET).timestamp()
        h, l = max(h, o, c), min(l, o, c)
        out.append({"t": t, "o": round(o, dec), "h": round(h, dec), "l": round(l, dec), "c": round(c, dec), "v": v})
    return out, kind


def intraday_bars(rnd, n, step_min=5, end="2026-09-30", rth_only=True, decimals=None, start_px=None):
    """RTH (09:30-16:00 ET) intraday bars of `step_min` minutes, oldest first, ending on `end`'s close."""
    per = 390 // step_min
    ndays = n // per + 2
    days = sessions(end, ndays)
    rows = path(rnd, ndays * per, px=start_px, regime_len=(10, 80))
    dec = decimals if decimals is not None else rnd.choice((2, 2, 3, 4))
    out, k = [], 0
    for d in days:
        for j in range(per):
            t = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET).timestamp() + j * step_min * 60
            o, h, l, c, v = rows[k]
            k += 1
            out.append({"t": t, "o": round(o, dec), "h": round(max(h, o, c), dec), "l": round(min(l, o, c), dec),
                        "c": round(c, dec), "v": float(int(v / 50))})
    return out[-n:]


def utc(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
