"""Komar Momentum public-proxy screen — line-by-line ports of Author-desk @a4fc436c src/lib/komar/{types,math,proxies,
screen,size}.ts (komar-momentum@0.1.0, mmts-public-proxy-a/b@0.1.0; the library scripts/rebuild-komar.mjs ran over
the desk universe each session). Bars are dicts {date, o, h, l, c, v}; None stands for null. Parity:
tools/parity/Author_komar.py."""
import math

INF = float("inf")
SLOPE_LOOKBACK = 5
MIN_ADR = 0.04
MIN_ABOVE_52W_LOW = 0.7
MIN_DOLLAR_VOLUME = 20_000_000
RISK_FRAC = 0.005
RISK_FRAC_CEILING = 0.01
MAX_POSITION_PCT = 0.35


# -- math.ts -----------------------------------------------------------------------------------------------------------
def ema(values, length):
    out = [None] * len(values)
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


def slope(series, i, lookback):
    a = series[i] if 0 <= i < len(series) else None
    j = i - lookback
    b = series[j] if 0 <= j < len(series) else None
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b)


def adr(highs, lows, n=20):
    if len(highs) < n or len(lows) < n:
        return None
    s = 0.0
    for i in range(len(highs) - n, len(highs)):
        mid = (highs[i] + lows[i]) / 2
        if not (mid > 0):
            return None
        s += (highs[i] - lows[i]) / mid
    return s / n


def clamp01(n):
    """Math.max(0, Math.min(1, n)): NaN stays NaN (Python's min/max would not)."""
    if n != n:
        return n
    return max(0.0, min(1.0, n))


def _mean(xs):
    acc = 0.0
    for x in xs:
        acc = acc + x
    return acc / len(xs) if xs else float("nan")


# -- proxies.ts --------------------------------------------------------------------------------------------------------
def proxy_a(close, ema21, sma10, ema21_slope):
    if ema21 is None or sma10 is None or ema21_slope is None:
        return None
    above = close > ema21
    up = ema21_slope > 0
    ten = sma10 > ema21
    if above and up and ten:
        return "green"
    if not above and not up and not ten:
        return "red"
    return "yellow"


def proxy_b(ema8, ema21, ema8_slope, ema21_slope):
    if ema8 is None or ema21 is None or ema8_slope is None or ema21_slope is None:
        return None
    stacked = ema8 > ema21
    both_up = ema8_slope > 0 and ema21_slope > 0
    both_down = ema8_slope < 0 and ema21_slope < 0
    if stacked and both_up:
        return "green"
    if not stacked and both_down:
        return "red"
    return "yellow"


def color_history(bars, lookback=SLOPE_LOOKBACK):
    closes = [b["c"] for b in bars]
    e8, s10, e21 = ema(closes, 8), sma(closes, 10), ema(closes, 21)
    rows = []
    for i, bar in enumerate(bars):
        s8 = slope(e8, i, lookback)
        s21 = slope(e21, i, lookback)
        rows.append({"date": bar["date"], "close": bar["c"], "ema8": e8[i], "sma10": s10[i], "ema21": e21[i],
                     "ema8Slope": s8, "ema21Slope": s21, "proxyA": proxy_a(bar["c"], e21[i], s10[i], s21),
                     "proxyB": proxy_b(e8[i], e21[i], s8, s21), "effectiveA": None, "effectiveB": None})
    for i in range(1, len(rows)):
        rows[i]["effectiveA"] = rows[i - 1]["proxyA"]
        rows[i]["effectiveB"] = rows[i - 1]["proxyB"]
    return rows


# -- screen.ts ---------------------------------------------------------------------------------------------------------
def _empty(symbol, reject):
    return {"symbol": symbol, "close": 0, "adr": 0, "dollarVolume": 0, "above52wLow": 0, "distFromHigh": 1,
            "ema8": None, "ema21": None, "ema65": None, "ema200": None, "rs20": None, "tightness": 0, "dryVolume": 0,
            "nearPivot": 0, "stopPct": None, "setup": "none", "score": 0,
            "parts": {"technical": 0, "setup": 0, "fundamental": 0, "story": 0, "trigger": 0, "risk": 0},
            "tier": "reject", "reject": reject, "note": "Missing bars."}


def _rng(hs, ls):
    return (max(hs) if hs else -INF) - (min(ls) if ls else INF)


def _count_up_days(closes):
    n = 0
    i = len(closes) - 1
    while i > 0 and closes[i] > closes[i - 1]:
        n += 1
        i -= 1
    return n


def _ma_order(close, e8, e21, e65, e200):
    n = 0
    if e8 is not None and close > e8:
        n += 1
    if e8 is not None and e21 is not None and e8 > e21:
        n += 1
    if e21 is not None and e65 is not None and e21 > e65:
        n += 1
    if e65 is not None and e200 is not None and e65 > e200:
        n += 1
    return n / 4


def _classify_setup(tightness, dry, near, dist):
    if dist > 0.18:
        return "none"
    if tightness >= 0.45 and dry >= 0.2 and near >= 0.94:
        return "tight_breakout"
    if tightness >= 0.3 and near >= 0.9:
        return "large_base"
    return "none"


def inspect_name(symbol, bars, qqq_return20):
    reject = []
    if len(bars) < 80:
        return _empty(symbol, ["missing_bars"])
    last = bars[-1]
    closes = [b["c"] for b in bars]
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    vols = [b["v"] for b in bars]
    e8, e21, e65, e200 = ema(closes, 8), ema(closes, 21), ema(closes, 65), ema(closes, 200)
    ema8, ema21, ema65, ema200 = e8[-1], e21[-1], e65[-1], e200[-1]
    year = bars[-252:]
    low52 = min(b["l"] for b in year)
    high52 = max(b["h"] for b in year)
    above52 = last["c"] / low52 - 1 if low52 > 0 else 0
    dist = (high52 - last["c"]) / high52 if high52 > 0 else 1
    adr20 = adr(highs, lows, 20)
    dollar_volume = _mean([b["c"] * b["v"] for b in bars[-50:]])
    ret20 = last["c"] / bars[len(bars) - 21]["c"] - 1 if len(bars) > 20 else None
    rs20 = ret20 - qqq_return20 if (ret20 is not None and qqq_return20 is not None) else ret20
    if not (last["c"] > 5):
        reject.append("price")
    if not (dollar_volume >= MIN_DOLLAR_VOLUME):
        reject.append("dollar_volume")
    if adr20 is None or adr20 < MIN_ADR:
        reject.append("adr")
    if above52 < MIN_ABOVE_52W_LOW:
        reject.append("below_52w_low_70")
    if ema65 is None or last["c"] <= ema65:
        reject.append("below_ema65")
    if ema8 is None or ema21 is None or ema8 <= ema21:
        reject.append("ema8_below_ema21")
    range10 = _rng(highs[-10:], lows[-10:])
    range40 = _rng(highs[-40:], lows[-40:])
    tightness = clamp01(1 - range10 / range40) if range40 > 0 else 0
    vol5 = _mean(vols[-5:])
    vol50 = _mean(vols[-50:])
    dry = clamp01(1 - vol5 / vol50) if vol50 > 0 else 0
    high20 = max(highs[-20:])
    near = clamp01(1 - (high20 - last["c"]) / high20) if high20 > 0 else 0
    base_low = min(lows[-10:])
    stop_pct = (last["c"] - base_low) / last["c"] if last["c"] > 0 else None
    setup = _classify_setup(tightness, dry, near, dist)
    up_days = _count_up_days(closes)
    trigger_ready = near >= 0.98 and up_days < 3
    technical = clamp01(0.4 * clamp01((rs20 if rs20 is not None else 0) / 0.15)
                        + 0.3 * _ma_order(last["c"], ema8, ema21, ema65, ema200) + 0.3 * (1 - dist))
    setup_score = clamp01(0.45 * tightness + 0.25 * dry + 0.3 * near)
    trigger = 0.8 if trigger_ready else 0.4 if near > 0.95 else 0.1
    risk = 0 if stop_pct is None else 1 if 0.03 <= stop_pct <= 0.05 else 0.5 if stop_pct <= 0.07 else 0
    parts = {"technical": technical, "setup": setup_score, "fundamental": 0, "story": 0, "trigger": trigger,
             "risk": risk}
    score = 0.25 * parts["technical"] + 0.25 * parts["setup"] + 0.15 * parts["fundamental"] + \
        0.15 * parts["story"] + 0.1 * parts["trigger"] + 0.1 * parts["risk"]
    return {"symbol": symbol, "close": last["c"], "adr": adr20 if adr20 is not None else 0,
            "dollarVolume": dollar_volume, "above52wLow": above52, "distFromHigh": dist, "ema8": ema8, "ema21": ema21,
            "ema65": ema65, "ema200": ema200, "rs20": rs20, "tightness": tightness, "dryVolume": dry,
            "nearPivot": near, "stopPct": stop_pct, "setup": setup, "score": score, "parts": parts, "tier": "reject",
            "reject": reject, "note": (f"Hard gate: {', '.join(reject)}." if reject
                                       else "Passed technical gates. Fundamentals and story unknown."),
            "triggerReady": trigger_ready, "upDays": up_days, "pivot": high20, "baseLow": base_low}


PORT_ONLY = ("triggerReady", "upDays", "pivot", "baseLow")   # carried for the sleeve; not fields of the source


def classify_tier(candidate, effective_b):
    c = dict(candidate)
    if c["reject"]:
        c["tier"] = "reject"
        return c
    if effective_b == "red":
        c["tier"] = "reject"
        c["reject"] = ["red_market"]
        c["note"] = "Red proxy B. No new long growth entries."
        return c
    p = c["parts"]
    strong = p["technical"] >= 0.55 and p["setup"] >= 0.45 and p["risk"] >= 0.5 and c["stopPct"] is not None \
        and c["stopPct"] <= 0.07
    if effective_b == "green" and strong:
        c["tier"] = "A"
        c["note"] = "Technical-only A. Fundamentals and story unknown, so this cannot be S."
        return c
    c["tier"] = "B"
    c["note"] = "Yellow market. Watch or starter quality only." if effective_b == "yellow" else \
        "Passed gates. Setup incomplete or not exceptional. Fundamentals unknown."
    return c


# -- size.ts -----------------------------------------------------------------------------------------------------------
def plan_ticket(symbol, tier, price, stop_pct, desk_equity, deployed=False):
    risk_frac = min(RISK_FRAC, RISK_FRAC_CEILING)
    sp = stop_pct if (stop_pct and stop_pct > 0) else 0.05
    risk_dollars = desk_equity * risk_frac
    per_share = price * sp
    raw = math.floor(risk_dollars / per_share) if per_share > 0 else 0
    max_shares = math.floor((desk_equity * MAX_POSITION_PCT) / price)
    shares = max(0, min(raw, max_shares))
    pos = (shares * price) / desk_equity if price > 0 else 0
    return {"symbol": symbol, "tier": tier, "riskFrac": risk_frac, "stopPct": sp, "shares": shares,
            "positionPct": pos, "quantity": 0,
            "reason": "Sleeve is still undeployed. Planned shares are research only." if deployed
            else "Quantity is zero. Undeployed research candidate. Planned shares are not an order."}


TIER_RANK = {"S": 0, "A": 1, "B": 2, "reject": 3}


def rank(classified):
    """rebuild-komar.mjs: S, A, B, reject; higher score first within a tier (stable)."""
    return sorted(classified, key=lambda c: (TIER_RANK[c["tier"]], -c["score"]))
