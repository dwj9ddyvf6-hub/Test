"""Signal Prism daily scanner — line-by-line ports of Author-desk @652db7af src/lib/prism/{kernel,engines,predicates,
physics,ascend,scan,catalog}.ts (signal-prism-kernel/3.1.0-wave0, the nine engines: Vector, Meridian, Cascade,
Threshold, Fissure, Dread, Reverb, Zenith, Strata). V8's Math.log / exp / log1p / pow / ** come from
desk/sleeves/v8math.py so every number matches the TypeScript bit for bit. Parity: tools/parity/Author_book.py."""
import math
import re
from datetime import datetime, timezone

from ..jsport import js_round
from ..v8math import exp as vexp, log as vlog, log1p as vlog1p, pow as vpow
from . import tensor as T

INF = float("inf")
MIN_RR = 1.5
SWING_HALF_ATR = 0.55
MAX_SWING_WIDTH_ATR = 1.25
PIVOT_RADIUS = 3
CUSUM_K = 0.5
CUSUM_H = 4
SQRT2 = 1.4142135623730951


def finite(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)


def mean(xs):
    if not xs:
        return None
    acc = 0.0
    for x in xs:
        acc = acc + x
    return acc / len(xs)


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def clamp(n, a, b):
    return min(b, max(a, n))


def volume_state(v):
    if not finite(v):
        return "MISSING"
    if v == 0:
        return "ZERO"
    if v < 0:
        return "PROVIDER_GAP"
    return "PRESENT"


def candle_shape(bar):
    rng = (bar["h"] - bar["l"]) or 1e-9
    return {"clv": (bar["c"] - bar["l"]) / rng, "body": abs(bar["c"] - bar["o"]) / rng,
            "upper": (bar["h"] - max(bar["o"], bar["c"])) / rng, "lower": (min(bar["o"], bar["c"]) - bar["l"]) / rng,
            "bull": bar["c"] >= bar["o"]}


def close_location(bar):
    return candle_shape(bar)["clv"]


def upper_wick(bar):
    return candle_shape(bar)["upper"]


def bullish_rejection(bar):
    s = candle_shape(bar)
    return s["bull"] and s["lower"] >= 0.35 and s["clv"] >= 0.55


def erf(x):
    a1, a2, a3, a4, a5, p = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429, 0.3275911
    sign = -1 if x < 0 else 1
    t = 1 / (1 + p * abs(x))
    y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * vexp(-x * x)
    return sign * y


def norm_cdf(x):
    return 0.5 * (1 + erf(x / SQRT2))


def log_returns(closes):
    out = [None] * len(closes)
    for i in range(1, len(closes)):
        if closes[i] > 0 and closes[i - 1] > 0:
            out[i] = vlog(closes[i] / closes[i - 1])
    return out


def robust_sigma(returns, lookback=40):
    sample = [v for v in returns if finite(v)][-lookback:]
    if len(sample) < 8:
        return None
    med = median(sample)
    mad = median([abs(v - med) for v in sample])
    if mad > 0:
        return 1.4826 * mad
    m = mean([vpow(v - med, 2) for v in sample])
    rms = math.sqrt(m if m is not None else 0)
    return rms if rms > 0 else None


def yang_zhang_sigma(bars, lookback=22):
    start = max(1, len(bars) - lookback)
    overnight, oc, rs = [], [], []
    for i in range(start, len(bars)):
        prev, b = bars[i - 1], bars[i]
        if prev["c"] <= 0 or b["o"] <= 0 or b["c"] <= 0 or b["h"] <= 0 or b["l"] <= 0:
            continue
        overnight.append(vpow(vlog(b["o"] / prev["c"]), 2))
        oc.append(vpow(vlog(b["c"] / b["o"]), 2))
        log_hl = vlog(b["h"] / b["l"])
        log_co = vlog(b["c"] / b["o"])
        rs.append(log_hl * (log_hl - log_co))
    if len(overnight) < 8:
        return None
    n = len(overnight)
    w = 0.34 / (1.34 + (n + 1) / (n - 1))
    v_over = mean(overnight) or 0
    v_oc = mean(oc) or 0
    v_rs = mean(rs) or 0
    v = v_over + w * v_oc + (1 - w) * v_rs
    return math.sqrt(v) if v > 0 else None


def atr_at(tr, length, end):
    sl = [v for v in tr[max(0, end - length + 1):end + 1] if finite(v)]
    return mean(sl) if len(sl) == length else None


def causal_pivots(bars, radius=PIVOT_RADIUS):
    out = []
    for i in range(radius, len(bars) - radius):
        is_low = is_high = True
        for j in range(i - radius, i + radius + 1):
            if j == i:
                continue
            if bars[j]["l"] < bars[i]["l"]:
                is_low = False
            if bars[j]["h"] > bars[i]["h"]:
                is_high = False
        known = i + radius
        if is_low:
            out.append({"kind": "LOW", "index": i, "knownIndex": known, "price": bars[i]["l"], "t": bars[i]["t"]})
        if is_high:
            out.append({"kind": "HIGH", "index": i, "knownIndex": known, "price": bars[i]["h"], "t": bars[i]["t"]})
    return out


def make_zone(kind, anchor, atr, sources, half=SWING_HALF_ATR):
    low = anchor - half * atr
    high = anchor + half * atr
    width = (high - low) / max(atr, 1e-9)
    valid = high > low and finite(low) and finite(high) and low > 0
    return {"kind": kind, "low": low, "high": high, "anchor": anchor, "widthAtr": width, "sources": sources,
            "valid": valid, "actionable": valid and width <= MAX_SWING_WIDTH_ATR}


def cluster_zones(pivots, atr, kind):
    pool = [p for p in pivots if p["kind"] == ("LOW" if kind == "DEMAND" else "HIGH")]
    used = set()
    zones = []
    for p in pool:
        if p["index"] in used:
            continue
        group = [q for q in pool if abs(q["price"] - p["price"]) <= 0.55 * atr]
        for q in group:
            used.add(q["index"])
        anchor = median([g["price"] for g in group])
        zones.append(make_zone(kind, anchor, atr, [g["index"] for g in group]))
    ref = pool[-1]["price"] if pool else 0
    return sorted(zones, key=lambda z: abs(z["anchor"] - ref))


def participation_at(bars, end, lookback=20):
    cur = bars[end]
    if cur["volumeState"] != "PRESENT":
        return {"signedSigma": None, "surpriseSigma": None, "confirmed": False, "state": cur["volumeState"]}
    rets = log_returns([b["c"] for b in bars])
    sigma = robust_sigma(rets[:end + 1])
    sigma = 0.01 if sigma is None else sigma
    r = rets[end] if rets[end] is not None else 0
    q = norm_cdf(r / max(sigma, 1e-9))
    signed, log_vol = [], []
    for i in range(max(1, end - lookback), end):
        if bars[i]["volumeState"] != "PRESENT":
            continue
        qi = norm_cdf((rets[i] if rets[i] is not None else 0) / max(sigma, 1e-9))
        signed.append(bars[i]["v"] * (2 * qi - 1))
        log_vol.append(vlog1p(bars[i]["v"]))
    cur_signed = cur["v"] * (2 * q - 1)
    med_s = median(signed)
    mad_s = None if med_s is None else median([abs(v - med_s) for v in signed])
    signed_sigma = (cur_signed - med_s) / (1.4826 * mad_s) if (med_s is not None and mad_s is not None and mad_s > 0) \
        else None
    med_v = median(log_vol)
    mad_v = None if med_v is None else median([abs(v - med_v) for v in log_vol])
    surprise = (vlog1p(cur["v"]) - med_v) / (1.4826 * mad_v) if (med_v is not None and mad_v is not None and mad_v > 0) \
        else None
    confirmed = (signed_sigma if signed_sigma is not None else -INF) >= 0.5 or \
        (surprise if surprise is not None else -INF) >= 0
    return {"signedSigma": signed_sigma, "surpriseSigma": surprise, "confirmed": confirmed, "state": cur["volumeState"]}


def permutation_entropy(values, end, window=32):
    start = max(2, end - window + 1)
    counts = {}
    n = 0
    for i in range(start, end + 1):
        a, b, c = values[i - 2], values[i - 1], values[i]
        if not all(finite(x) for x in (a, b, c)):
            continue
        trio = (a, b, c)
        order = "".join(str(k) for k in sorted([0, 1, 2], key=lambda k: trio[k]))
        counts[order] = counts.get(order, 0) + 1
        n += 1
    if n < 8:
        return {"h": None, "compression": None}
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * vlog(p)
    norm = h / vlog(6)
    return {"h": norm, "compression": clamp(1 - norm, 0, 1)}


def completed_cusum(returns, sigma):
    up = down = 0.0
    events = []
    if not sigma or sigma <= 0:
        return {"up": 0, "down": 0, "events": events}
    for i in range(1, len(returns)):
        r = returns[i]
        if not finite(r):
            continue
        z = r / sigma
        up = max(0, up + z - CUSUM_K)
        down = max(0, down - z - CUSUM_K)
        if up > CUSUM_H:
            events.append({"dir": "UP", "index": i})
            up = 0
        if down > CUSUM_H:
            events.append({"dir": "DOWN", "index": i})
            down = 0
    return {"up": up, "down": down, "events": events}


def long_geometry(entry, invalidation, target):
    risk = entry - invalidation
    reward = target - entry
    rr = reward / risk if risk > 0 else None
    ok = finite(entry) and finite(invalidation) and finite(target) and invalidation < entry and target > entry and \
        rr is not None and rr >= MIN_RR
    return {"entry": entry, "invalidation": invalidation, "target": target, "rr": rr, "complete": ok}


def anti_chase_facts(close, open_, prev_close, atr, zone_high, trigger, shape, day_sigma, rr, participation):
    if not atr or atr <= 0:
        return {"pass": False, "reasons": ["ATR_UNAVAILABLE"]}
    reasons = []
    d_zone = 0 if zone_high is None else max(0, close - zone_high) / atr
    d_trig = 0 if trigger is None else max(0, close - trigger) / atr
    gap = max(0, open_ - prev_close) / atr
    day_move = abs(vlog(close / prev_close)) / day_sigma if (day_sigma and day_sigma > 0) else 0
    if d_zone > 1:
        reasons.append("ZONE_DISTANCE")
    if d_trig > 0.75:
        reasons.append("TRIGGER_DISTANCE")
    if gap > 1:
        reasons.append("GAP")
    if day_move > 2:
        reasons.append("DAY_MOVE")
    if shape["upper"] > 0.45 and shape["clv"] < 0.55:
        reasons.append("REJECTION_BAR")
    if rr is None or rr < MIN_RR:
        reasons.append("REWARD_RISK_BELOW_1_5")
    breakout = participation and shape["clv"] >= 0.65 and shape["upper"] <= 0.25 and \
        (rr if rr is not None else 0) >= MIN_RR and d_zone <= 1 and d_trig <= 0.75
    ok = len(reasons) == 0 or (breakout and "REWARD_RISK_BELOW_1_5" not in reasons and "REJECTION_BAR" not in reasons)
    return {"pass": ok, "reasons": reasons, "dZone": d_zone, "dTrig": d_trig, "gap": gap, "dayMove": day_move,
            "breakout": breakout}


def path_efficiency(closes):
    if len(closes) < 3 or closes[0] <= 0:
        return None
    net = abs(vlog(closes[-1] / closes[0]))
    path = 0.0
    for i in range(1, len(closes)):
        if closes[i] > 0 and closes[i - 1] > 0:
            path += abs(vlog(closes[i] / closes[i - 1]))
    return net / path if path > 0 else None


def theil_sen(xs, ys):
    if len(xs) < 3:
        return None
    slopes = []
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx = xs[j] - xs[i]
            if dx == 0:
                continue
            slopes.append((ys[j] - ys[i]) / dx)
    return median(slopes)


def _utc(t):
    return datetime.fromtimestamp(math.floor(t / 1000), tz=timezone.utc)


def _iso_week(d):
    """kernel.ts isoWeek(d) on the UTC calendar date."""
    import datetime as _dt
    t = _dt.date(d.year, d.month, d.day)
    day = t.isoweekday()
    t = t + _dt.timedelta(days=4 - day)
    y = _dt.date(t.year, 1, 1)
    return math.ceil(((t - y).days + 1) / 7)


def weekly_from_daily(bars):
    weeks = []
    bucket = []
    key = ""
    for b in bars:
        d = _utc(b["t"])
        k = f"{d.year}-{_iso_week(d)}"
        if k != key and bucket:
            weeks.append(_collapse(bucket))
            bucket = []
        key = k
        bucket.append(b)
    if bucket:
        weeks.append(_collapse(bucket))
    return weeks


def _collapse(xs):
    first, last = xs[0], xs[-1]
    v = 0.0
    for b in xs:
        v = v + (b["v"] if b["volumeState"] == "PRESENT" else 0)
    return {"t": last["t"], "o": first["o"], "h": max(b["h"] for b in xs), "l": min(b["l"] for b in xs),
            "c": last["c"], "v": v,
            "volumeState": "PRESENT" if any(b["volumeState"] == "PRESENT" for b in xs) else last["volumeState"]}


def poc_from_bars(bars, period=40, bins=24):
    usable = [b for b in bars[-period:] if b["volumeState"] == "PRESENT" and b["v"] > 0]
    if len(usable) < 8:
        return None
    low = min(b["l"] for b in usable)
    high = max(b["h"] for b in usable)
    if high <= low:
        return (low + high) / 2
    step = (high - low) / bins
    vol = [0.0] * bins
    for b in usable:
        mid = (b["h"] + b["l"]) / 2
        idx = int(clamp(math.floor((mid - low) / step), 0, bins - 1))
        vol[idx] += b["v"]
    best = 0
    for i in range(1, bins):
        if vol[i] > vol[best]:
            best = i
    return low + (best + 0.5) * step


def _ymd_key(t):
    d = _utc(t)
    return f"{d.year}-{d.month}-{d.day}"


def residual_against(inst, bench):
    empty = {"last": None, "beta": None, "state": "ABSENT", "series": [None] * len(inst)}
    if len(inst) < 16 or len(bench) < 16:
        return empty
    bmap = {}
    for b in bench:
        bmap[_ymd_key(b["t"])] = b["c"]
    paired = []
    for i in range(1, len(inst)):
        ci, pi = inst[i]["c"], inst[i - 1]["c"]
        cb, pb = bmap.get(_ymd_key(inst[i]["t"])), bmap.get(_ymd_key(inst[i - 1]["t"]))
        if not (ci > 0 and pi > 0 and cb and pb and cb > 0 and pb > 0):
            continue
        paired.append({"ri": vlog(ci / pi), "rb": vlog(cb / pb), "i": i})
    if len(paired) < 12:
        return empty
    window = paired[-40:]
    beta = theil_sen([p["rb"] for p in window], [p["ri"] for p in window])
    if beta is None or not math.isfinite(beta):
        return empty
    series = [None] * len(inst)
    last = None
    for p in paired:
        r = p["ri"] - beta * p["rb"]
        series[p["i"]] = r
        last = r
    return {"last": last, "beta": beta, "state": "PRESENT", "series": series}


def build_snapshot(raw, bench=None):
    if len(raw) < 2:
        return None
    bars = [{"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"],
             "volumeState": volume_state(b["v"])} for b in raw]
    i = len(bars) - 1
    closes = [b["c"] for b in raw]
    tr = T.true_range(raw)
    atr_series = [atr_at(tr, 14, idx) for idx in range(len(tr))]
    atr = atr_series[i]
    rets = log_returns(closes)
    robust = robust_sigma(rets)
    yz = yang_zhang_sigma(bars)
    sigma_one = yz if yz is not None else robust
    sigma_five = None if sigma_one is None else sigma_one * math.sqrt(5)
    emas = {p: T.ema(closes, p) for p in (5, 8, 12, 13, 20, 21, 34, 50, 55, 200)}
    pivots = causal_pivots(bars)
    demand = cluster_zones(pivots, atr, "DEMAND") if atr else []
    supply = cluster_zones(pivots, atr, "SUPPLY") if atr else []
    return {"bars": bars, "closes": closes, "i": i, "cur": bars[i], "prev": bars[i - 1], "atr": atr,
            "atrSeries": atr_series, "sigmaOne": sigma_one, "sigmaFive": sigma_five, "robustSigma": robust,
            "ema": emas, "rsi14": T.rsi(closes, 14), "macd": T.macd(closes), "pivots": pivots, "demand": demand,
            "supply": supply, "participation": participation_at(bars, i), "entropy": permutation_entropy(closes, i),
            "cusum": completed_cusum(rets, robust), "shape": candle_shape(bars[i]),
            "residual": residual_against(bars, bench or [])}


def nearest_zone(zones, price):
    s = sorted(zones, key=lambda z: abs(z["anchor"] - price))
    return s[0] if s else None


def empty_geom():
    return {"zoneLow": None, "zoneHigh": None, "trigger": None, "invalidation": None, "target": None, "rr": None,
            "widthAtr": None, "actionable": False}


def geom_from_zone(zone, entry, atr, target):
    if not zone or not atr:
        return empty_geom()
    inv = zone["low"] - 0.65 * atr if zone["kind"] == "DEMAND" else zone["low"] - 0.35 * atr
    tgt = target if target is not None else zone["high"] + 1.6 * atr
    g = long_geometry(entry, inv, tgt)
    return {"zoneLow": zone["low"], "zoneHigh": zone["high"], "trigger": zone["high"], "invalidation": inv,
            "target": tgt, "rr": g["rr"], "widthAtr": zone["widthAtr"], "actionable": zone["actionable"] and g["complete"]}


def _at(arr, i):
    return arr[i] if 0 <= i < len(arr) else None


# -- engines.ts ----------------------------------------------------------------------------------------------------------
def _hit(scanner, lane, event, flags, native_phase, note, next_condition, geometry, conflicts=None, observed_at=None,
         failed=False, force_active=None):
    missing = [k for k, v in flags.items() if not v]
    vals = list(flags.values())
    active = force_active if force_active is not None else all(bool(v) for v in vals)
    ready = not active and len(missing) == 1
    formed = not active and not ready and len(missing) <= 3 and any(bool(v) for v in vals)
    discovered = not active and not ready and not formed and any(bool(v) for v in vals)
    return {"scannerId": scanner, "lane": lane, "event": event, "nativePhase": native_phase, "active": active,
            "ready": ready, "formed": formed, "discovered": discovered, "failed": failed, "note": note,
            "nextCondition": next_condition, "missing": missing, "geometry": geometry, "conflicts": conflicts or [],
            "observedAt": observed_at, "coords": []}


def _next_of(missing, fallback):
    if missing:
        return "Need " + re.sub(r"([A-Z])", r" \1", missing[0]).lower() + "."
    return fallback


def _miss(flags):
    return [k for k, v in flags.items() if not v]


def run_vector(s):
    cur, prev = s["cur"], s["prev"]
    demand = nearest_zone(s["demand"], cur["c"])
    supply = nearest_zone(s["supply"], cur["c"])
    ups = sorted([z for z in s["supply"] if z["low"] > cur["c"]], key=lambda z: z["low"])
    next_supply = ups[0] if ups else None
    part = s["participation"]["confirmed"]
    demand_touch = bool(demand and cur["l"] <= demand["high"] and cur["h"] >= demand["low"])
    rejection = bullish_rejection(cur)
    close_at_anchor = bool(demand and cur["c"] >= demand["anchor"])
    prior_below = bool(demand and prev["c"] < demand["low"])
    traverse = bool(demand and prior_below and cur["c"] >= demand["high"])
    crossed = bool(supply and prev["c"] <= supply["high"] and cur["c"] > supply["high"])
    accept = s["shape"]["clv"] >= 0.65 and s["shape"]["upper"] <= 0.3
    demand_broken = bool(demand and cur["c"] < demand["low"] - (s["atr"] or 0) * 0.15)
    dflags = {"demandTouch": demand_touch, "bullishRejection": rejection, "closeAtOrAboveAnchor": close_at_anchor,
              "participationConfirmed": part}
    rflags = {"previousBelowZone": prior_below, "fullTraversal": traverse, "participationConfirmed": part}
    cflags = {"crossedSupply": crossed, "acceptedMorphology": accept, "participationConfirmed": part}
    defense_on = (not demand_broken) and all(dflags.values())
    reclaim_on = (not demand_broken) and all(rflags.values())
    clear_on = all(cflags.values())
    g_def = geom_from_zone(demand, cur["c"], s["atr"], next_supply["low"] if next_supply else None)
    g_sup = geom_from_zone(supply, cur["c"], s["atr"], next_supply["high"] if next_supply else None)
    ct = cur["t"]
    return [
        _hit("vector", "DEMAND_DEFENSE", "DEMAND_DEFENSE_ACCEPTED", dflags,
             "DEMAND_FAILED" if demand_broken else "DEFENSE_ACTIVE" if defense_on else "TESTING" if demand_touch
             else "APPROACHING" if demand else "PASS",
             "Survival-weighted demand field. Defense is a visit with declining impact, not a touch count.",
             "Demand failed — wait for a child reclaim episode." if demand_broken
             else _next_of(_miss(dflags), "Demand defended."),
             g_def, failed=demand_broken, force_active=defense_on, observed_at=ct if defense_on else None),
        _hit("vector", "DEMAND_RECLAIM", "DEMAND_RECLAIM_ACCEPTED", rflags,
             "DEMAND_FAILED" if demand_broken else "RECLAIM_ACTIVE" if reclaim_on
             else "RECLAIM_IN_PROGRESS" if (prior_below and demand and cur["c"] >= demand["anchor"])
             else "CONTACT" if demand else "PASS",
             "Broken demand stays terminal. A child reclaim must traverse the frozen zone from below.",
             _next_of(_miss(rflags), "Zone reclaimed."), g_def, force_active=reclaim_on,
             observed_at=ct if reclaim_on else None),
        _hit("vector", "SUPPLY_CLEARANCE", "SUPPLY_CLEARANCE_ACCEPTED", cflags,
             "CLEARANCE_ACTIVE" if clear_on else "SUPPLY_TESTING" if supply else "PASS",
             "Polarity transition: declining rejection at supply, then acceptance above the frozen edge.",
             _next_of(_miss(cflags), "Supply cleared."), g_sup,
             conflicts=["supply still rejecting"] if (rejection and not s["shape"]["bull"]) else [],
             force_active=clear_on, observed_at=ct if clear_on else None),
    ]


def run_meridian(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    e50, e200 = s["ema"][50][i], s["ema"][200][i]
    e50p, e200p = _at(s["ema"][50], i - 1), _at(s["ema"][200], i - 1)
    boundary = e200 if e200 is not None else e50
    prior_b = e200p if e200p is not None else e50p
    bullish_b = bool(boundary and cur["c"] >= boundary)
    prior_bull = bool(prior_b and prev["c"] >= prior_b)
    last_up = next((e for e in reversed(s["cusum"]["events"]) if e["dir"] == "UP"), None)
    transition_up = bool(last_up and i - last_up["index"] <= 5 and bullish_b and not prior_bull)
    location_ready = bool(boundary and cur["c"] >= boundary * 0.985)
    interaction = location_ready and bool(s["atr"] and boundary and cur["l"] <= boundary + s["atr"] * 0.35)
    reclaim = bool(boundary and prev["c"] < boundary and cur["c"] >= boundary)
    hold = bool(interaction and boundary and cur["c"] >= boundary and s["shape"]["clv"] >= 0.58)
    mom = (s["macd"]["hist"][i] if s["macd"]["hist"][i] is not None else 0) > 0
    rflags = {"bullishBoundary": bullish_b, "transitionUp": transition_up, "locationReady": location_ready,
              "acceptedInteraction": reclaim or hold, "momentumOrParticipation": mom or s["participation"]["confirmed"]}
    regime_on = all(rflags.values())
    look = s["bars"][max(0, i - 8):]
    fear_low = min(b["l"] for b in look)
    fear_anchor = boundary if boundary is not None else cur["c"]
    res = s["residual"]
    residual_shock = res["state"] == "PRESENT" and any(r is not None and r <= -0.02 for r in res["series"][-8:])
    if res["state"] == "PRESENT" and res["last"] is not None:
        fear_exc = res["last"] / max(s["sigmaOne"] if s["sigmaOne"] is not None else 0.01, 1e-6)
    elif s["sigmaFive"] and fear_anchor > 0:
        fear_exc = vlog(fear_low / fear_anchor) / s["sigmaFive"]
    else:
        fear_exc = None
    fear_extreme = (fear_exc is not None and fear_exc <= -0.75) or residual_shock
    progress = (cur["c"] - look[0]["c"]) / s["atr"] if s["atr"] else 0
    absorption = bool(fear_extreme and progress >= -0.25 and s["shape"]["clv"] >= 0.6 and s["participation"]["confirmed"])
    fear_recovery = bool(boundary and ((prev["c"] < boundary and cur["c"] >= boundary) or
                                       (interaction and cur["c"] >= boundary)))
    ss = s["participation"]["surpriseSigma"]
    vacuum = fear_recovery and (ss if ss is not None else INF) <= -0.5
    fflags = {"absorption": absorption, "recovery": fear_recovery, "vacuumBounce": vacuum}
    fear_on = absorption and fear_recovery and not vacuum
    ups = [z for z in s["supply"] if z["low"] > cur["c"]]
    nz = nearest_zone(ups, cur["c"])
    g = geom_from_zone(nearest_zone(s["demand"], cur["c"]), cur["c"], s["atr"], nz["low"] if nz else None)
    ct = cur["t"]
    return [
        _hit("meridian", "REGIME_TRANSITION", "REGIME_TRANSITION_ACCEPTED", rflags,
             "TRANSITION_ACCEPTED" if regime_on else "BOUNDARY_INTERACTION" if interaction
             else "LOCATION_READY" if location_ready else "TRANSITION_UP" if transition_up
             else "REGIME_ELIGIBLE" if bullish_b else "REGIME_LOST",
             "Hierarchical process change. Residual vs the broad tape when present; CUSUM + frozen boundary — not a "
             "SuperTrend badge.", _next_of(_miss(rflags), "Regime accepted."), g, force_active=regime_on,
             observed_at=ct if regime_on else None),
        _hit("meridian", "FEAR_RECOVERY", "FEAR_RECOVERY_ACCEPTED", fflags,
             "RECOVERY_HOLD" if fear_on else "VACUUM_BOUNCE" if vacuum else "ABSORPTION_WATCH" if absorption
             else "FEAR_EXCURSION" if fear_extreme else "QUIET",
             "Idiosyncratic shock (residual when the benchmark is present) then declining adverse impact. Vacuum bounce "
             "is rejected.",
             "Low-effort bounce — not absorption." if vacuum else _next_of(_miss(fflags), "Fear recovered."), g,
             force_active=fear_on, observed_at=ct if fear_on else None),
    ]


def run_cascade(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]

    def at(idx):
        return [_at(s["ema"][p], idx) for p in (8, 13, 21, 55)]
    now, prv = at(i), at(i - 1)
    ready = all(v is not None for v in now)
    e55, p55 = now[3], prv[3]
    stacking = (int(now[0] > now[1]) + int(now[1] > now[2]) + int(now[2] > now[3])) if ready else 0
    width = (max(now) - min(now)) / s["atr"] if (ready and s["atr"]) else None
    coiled = width is not None and width <= 0.85
    reclaim = bool(e55 is not None and p55 is not None and prev["c"] <= p55 and cur["c"] > e55)
    open_dist = abs(cur["o"] - e55) / s["atr"] if (e55 is not None and s["atr"]) else 99
    gap = max(0, cur["o"] - prev["c"]) / s["atr"] if s["atr"] else 99
    prior_vol = [b["v"] for b in s["bars"][-5:-1] if b["volumeState"] == "PRESENT"]
    base_vol = [b["v"] for b in s["bars"][-25:-5] if b["volumeState"] == "PRESENT"]
    dry = len(prior_vol) > 0 and len(base_vol) > 0 and (median(prior_vol) or 0) <= (median(base_vol) or 0)
    morph = s["shape"]["clv"] >= 0.6 and s["shape"]["upper"] <= 0.35
    topology = stacking >= 2 or coiled
    rflags = {"reclaim": reclaim, "controlledOpen": open_dist <= 0.35, "nonTeleport": gap < 0.75, "pullbackDry": dry,
              "acceptedMorphology": morph, "topologyReady": topology}
    reclaim_on = all(rflags.values())
    expansion = None
    for idx in range(max(58, i - 8), i):
        r, p = at(idx), at(idx - 1)
        if not all(v is not None for v in r) or not all(v is not None for v in p):
            continue
        ordered = r[0] > r[1] and r[1] > r[2] and r[2] > r[3]
        delta = r[0] - r[3] - (p[0] - p[3])
        if ordered and delta > 0:
            expansion = idx
    if now[2] is not None and e55 is not None:
        support = max(now[2], e55)
    else:
        support = now[2] if now[2] is not None else e55
    retest = bool(support is not None and s["atr"] and cur["l"] <= support + s["atr"] * 0.25 and
                  cur["l"] >= support - s["atr"] * 0.35)
    accepted = bool(support is not None and cur["c"] > support and s["shape"]["clv"] >= 0.6)
    exhausted = s["shape"]["upper"] > 0.45 and s["shape"]["clv"] < 0.5
    pflags = {"expansionObserved": expansion is not None, "retestInBand": retest, "acceptedClose": accepted,
              "pullbackDry": dry, "exhausted": exhausted}
    pull_on = pflags["expansionObserved"] and retest and accepted and dry and not exhausted
    band = {"kind": "DEMAND", "low": e55 - 0.35 * s["atr"], "high": e55 + 0.2 * s["atr"], "anchor": e55, "widthAtr": 0.55,
            "sources": [], "valid": True, "actionable": True} if (e55 is not None and s["atr"]) else None
    g = geom_from_zone(band, cur["c"], s["atr"], None)
    ct = cur["t"]
    return [
        _hit("ravel", "EMA55_RECLAIM", "EMA55_RECLAIM_ACCEPTED", rflags,
             "SCALE_PROPAGATION_ACCEPTED" if reclaim_on else "COILED" if coiled else "ORDERED_EXPANSION" if stacking >= 3
             else "TRANSITIONING" if stacking >= 1 else "DISORDERED",
             "Trend front across 8/13/21/55. A gap through 55 is not a reclaim.",
             _next_of(_miss(rflags), "EMA55 accepted."), g, force_active=reclaim_on,
             observed_at=ct if reclaim_on else None),
        _hit("ravel", "EXPANSION_PULLBACK", "CONTROLLED_PULLBACK_RETEST_ACCEPTED", pflags,
             "CONTROLLED_PULLBACK_REACCELERATION" if pull_on else "MATURE_OR_EXHAUSTING" if exhausted
             else "EXPANSION_WATCH" if expansion is not None else "QUIET",
             "Slow scale holds while the fast surface contracts into frozen support.",
             _next_of(_miss(pflags), "Pullback accepted."), g, force_active=pull_on,
             observed_at=ct if pull_on else None),
    ]


def run_threshold(s):
    i, cur, bars = s["i"], s["cur"], s["bars"]
    breach = None
    boundary = None
    for idx in range(i, max(20, i - 40) - 1, -1):
        window = bars[idx - 20:idx]  # idx >= 20 throughout the loop, so the JS slice never wraps
        if len(window) < 20:
            continue
        cand = max(b["h"] for b in window)
        if bars[idx - 1]["c"] <= cand and bars[idx]["c"] > cand:
            breach = idx
            boundary = cand
            break
    if boundary is None and i >= 20:
        boundary = max(b["h"] for b in bars[i - 20:i])
    atr = s["atr"]
    press_end = breach if breach is not None else i
    press_bars = [b for b in bars[max(0, press_end - 30):press_end] if b["h"] >= boundary - atr * 0.35 and
                  b["c"] <= boundary] if (boundary is not None and atr) else []
    pressing = len(press_bars) >= 3 and boundary is not None and cur["c"] < boundary
    qualified = False
    if breach is not None and atr:
        bar, prior = bars[breach], bars[breach - 1]
        gap_atr = max(0, bar["o"] - prior["c"]) / atr
        ss = s["participation"]["surpriseSigma"]
        qualified = gap_atr <= 1 and close_location(bar) >= 0.65 and upper_wick(bar) <= 0.3 and \
            (ss if ss is not None else 0) >= 0
    returned = bool(boundary is not None and atr and cur["c"] < boundary - atr * 0.15)
    outside = bool(boundary is not None and cur["c"] > boundary and s["shape"]["clv"] >= 0.6)
    later = bool(breach is not None and boundary is not None and i > breach and
                 any(b["l"] <= boundary and b["c"] >= boundary for b in bars[breach + 1:i + 1]))
    dflags = {"breachObserved": breach is not None, "breachQualified": qualified,
              "returnedThrough": returned and breach == i, "outsideAcceptance": outside}
    rflags = {"breachObserved": breach is not None, "laterRetestObserved": later,
              "returnedThrough": returned and later}
    direct_on = dflags["breachObserved"] and qualified and not dflags["returnedThrough"] and outside
    retest_on = rflags["breachObserved"] and later and not rflags["returnedThrough"]
    band = {"kind": "SUPPLY", "low": boundary, "high": boundary + 0.25 * atr, "anchor": boundary, "widthAtr": 0.25,
            "sources": [], "valid": True, "actionable": True} if (boundary is not None and atr) else None
    highs = sorted([p for p in s["pivots"] if p["kind"] == "HIGH" and boundary is not None and p["price"] > boundary],
                   key=lambda p: p["price"])
    nh = highs[0] if highs else None
    g = geom_from_zone(band, cur["c"], atr, nh["price"] if nh else None)
    ct = cur["t"]
    return [
        _hit("breakline", "DIRECT_ACCEPTANCE", "ACCEPTED_DIRECT", dflags,
             "ACCEPTED_DIRECT" if direct_on else "PRESSING" if pressing else "BREACH_WATCH" if breach is not None
             else "BASE",
             "Boundary is fit from bars strictly before the breach. Acceptance is a race, not a candle.",
             "Pressure building — wait for qualified close beyond the frozen boundary." if pressing
             else _next_of(_miss(dflags), "Direct acceptance."), g, force_active=direct_on,
             failed=returned and breach is not None and not later, observed_at=ct if direct_on else None),
        _hit("breakline", "RETEST_ACCEPTANCE", "ACCEPTED_RETEST", rflags,
             "ACCEPTED_RETEST" if retest_on else "RETEST_IN_PROGRESS" if later
             else "AWAITING_RETEST" if breach is not None else "NO_BREACH",
             "Retest is a later typed event tied to the frozen origin. It cannot be inferred from the snapshot alone.",
             _next_of(_miss(rflags), "Retest accepted."), g, force_active=retest_on,
             observed_at=ct if retest_on else None),
    ]


def run_fissure(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    e5, e12, e34, e50 = s["ema"][5][i], s["ema"][12][i], s["ema"][34][i], s["ema"][50][i]
    p34, p50 = _at(s["ema"][34], i - 1), _at(s["ema"][50], i - 1)
    hourly = bool(e34 is not None and e50 is not None and e34 > e50 and cur["c"] > e34)
    cloud_now = abs(e34 - e50) if (e34 is not None and e50 is not None) else 0
    cloud_prev = abs(p34 - p50) if (p34 is not None and p50 is not None) else 0
    eflags = {"hourlyBullish": hourly, "cloudGrowing": cloud_now > cloud_prev,
              "boundedGrowth": cloud_now <= cloud_prev * 2.4 + (s["atr"] or 0) * 0.01,
              "participationConfirmed": s["participation"]["confirmed"]}
    mid = (e5 + e12) / 2 if (e5 is not None and e12 is not None) else None
    p5, p12 = _at(s["ema"][5], i - 1), _at(s["ema"][12], i - 1)
    prior_mid = (p5 + p12) / 2 if (p5 is not None and p12 is not None) else mid
    fflags = {"priorBelowMid": bool(prior_mid is not None and prev["c"] < prior_mid),
              "reclaimMid": bool(mid is not None and cur["c"] >= mid),
              "participationConfirmed": s["participation"]["confirmed"]}
    expand_on = all(eflags.values())
    fast_on = all(fflags.values())
    band = {"kind": "DEMAND", "low": mid - 0.3 * s["atr"], "high": mid + 0.2 * s["atr"], "anchor": mid, "widthAtr": 0.5,
            "sources": [], "valid": True, "actionable": True} if (mid is not None and s["atr"]) else None
    g = geom_from_zone(band, cur["c"], s["atr"], e34)
    ct = cur["t"]
    return [
        _hit("ripster", "CLOUD_REGIME_EXPANSION", "RIPSTER_CLOUD_ALIGNMENT_ACCEPTED", eflags,
             "CLOUD_REGIME_EXPANSION_ACCEPTED" if expand_on else "CLOUD_ORDERED" if hourly else "CLOUD_COMPRESSED",
             "Daily cloud lattice. 10m/1h clocks are ABSENT on a daily-only tape — not invented.",
             _next_of(_miss(eflags), "Cloud expansion accepted."), g, force_active=expand_on,
             observed_at=ct if expand_on else None),
        _hit("ripster", "FAST_CLOUD_PULLBACK", "RIPSTER_FAST_CLOUD_RECLAIM_ACCEPTED", fflags,
             "FAST_CLOUD_PULLBACK_REACCELERATION" if fast_on else "FAST_TOUCH" if (mid and prev["c"] < mid)
             else "NO_PULLBACK",
             "Controlled 5/12 midpoint reclaim inside an established slow cloud.",
             _next_of(_miss(fflags), "Fast cloud reclaimed."), g, force_active=fast_on,
             observed_at=ct if fast_on else None),
    ]


def _ema_like(values, length):
    out = [None] * len(values)
    k = 2 / (length + 1)
    prev = None
    seed = 0.0
    n = 0
    for i, v in enumerate(values):
        if prev is None:
            seed += v
            n += 1
            if n == length:
                prev = seed / length
                out[i] = prev
        else:
            prev = v * k + prev * (1 - k)
            out[i] = prev
    return out


def run_dread(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    weekly = weekly_from_daily(s["bars"])
    wc = [b["c"] for b in weekly]
    need = len(weekly) >= 12
    w8 = _ema_like(wc, 8) if need else []
    w20 = _ema_like(wc, 20) if need else []
    wi = len(weekly) - 1
    now_bull = bool(need and _at(w8, wi) is not None and _at(w20, wi) is not None and w8[wi] > w20[wi] and
                    weekly[wi]["c"] > w20[wi])
    prior_bull = bool(need and wi >= 1 and _at(w8, wi - 1) is not None and _at(w20, wi - 1) is not None and
                      w8[wi - 1] > w20[wi - 1])
    frozen = poc_from_bars(s["bars"][:max(8, i - 5)], 40)
    live = poc_from_bars(s["bars"], 40)
    poc = frozen if frozen is not None else live
    flip = {"priorNotBull": not prior_bull, "nowBull": now_bull, "followThrough": cur["c"] > prev["c"]}
    recl = {"priorBelowValue": bool(poc is not None and prev["c"] < poc),
            "closeAtOrAboveValue": bool(poc is not None and cur["c"] >= poc),
            "dailySupport": bool(poc is not None and cur["l"] <= poc and cur["c"] >= poc),
            "followThrough": cur["c"] > prev["c"]}
    fail = {"priorBear": not prior_bull, "nowBull": now_bull,
            "valueReclaim": bool(poc is not None and cur["c"] >= poc and prev["c"] < poc)}
    flip_on, poc_on, fail_on = all(flip.values()), all(recl.values()), all(fail.values())
    band = {"kind": "DEMAND", "low": poc - 0.4 * s["atr"], "high": poc + 0.25 * s["atr"], "anchor": poc, "widthAtr": 0.65,
            "sources": [], "valid": True, "actionable": True} if (poc is not None and s["atr"]) else None
    g = geom_from_zone(band, cur["c"], s["atr"], None)
    ct = cur["t"]
    return [
        _hit("panic", "BULL_FLIP_COMMITMENT", "PANIC_BULL_FLIP_ACCEPTED", flip,
             "CLOSED_FLIP_COMMITTED" if flip_on else "CONTINUATION" if now_bull else "MATURE" if prior_bull
             else "PROVISIONAL_OR_BEAR",
             "Weekly flip is a close-time transition, not a current EMA reading. POC is frozen from prior weeks.",
             _next_of(_miss(flip), "Flip committed.") if need else "Need more weekly history.", g,
             force_active=flip_on, observed_at=ct if flip_on else None),
        _hit("panic", "POC_VALUE_RECLAIM", "PANIC_POC_CONFIRMATION_ACCEPTED", recl,
             "POC_VALUE_RECLAIM_ACCEPTED" if poc_on else "VALUE_TEST" if poc else "POC_ABSENT",
             "A moving current POC cannot generate a retroactive reclaim.",
             _next_of(_miss(recl), "Value reclaimed."), g, force_active=poc_on, observed_at=ct if poc_on else None),
        _hit("panic", "FAILED_BEAR_FLIP_RECLAIM", "FAILED_BEAR_RECLAIM", fail,
             "FAILED_BEAR_FLIP_RECLAIM" if fail_on else "NO_FAILED_BEAR",
             "Failed-bear recovery stays an active hypothesis — not terminalized as a loss.",
             _next_of(_miss(fail), "Failed-bear reclaimed."), g, force_active=fail_on,
             observed_at=ct if fail_on else None),
    ]


def run_reverb(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    swing = s["bars"][max(0, i - 40):]
    hi = max(b["h"] for b in swing)
    lo = min(b["l"] for b in swing)
    fib = hi - 0.618 * (hi - lo)
    e50, e200 = s["ema"][50][i], s["ema"][200][i]
    atr = s["atr"] if s["atr"] is not None else cur["c"] * 0.02
    at_fib = abs(cur["c"] - fib) <= 0.35 * atr
    at50 = e50 is not None and abs(cur["c"] - e50) <= 0.35 * atr
    at200 = e200 is not None and abs(cur["c"] - e200) <= 0.45 * atr
    lows = [p for p in s["pivots"] if p["kind"] == "LOW"][-6:]
    cluster = len(lows) >= 2 and abs(lows[-1]["price"] - lows[-2]["price"]) <= 0.55 * atr
    sen = theil_sen([p["index"] for p in lows], [p["price"] for p in lows])
    sen_line = lows[0]["price"] + sen * (i - lows[0]["index"]) if (sen is not None and lows) else None
    at_sen = sen_line is not None and abs(cur["c"] - sen_line) <= 0.4 * atr
    families = len([x for x in (at_fib, at50 or at200, cluster, at_sen) if x])
    recovery = cur["c"] > prev["c"] and cur["c"] >= prev["o"] and (at_fib or at50 or cluster)
    e21, e55 = s["ema"][21][i], s["ema"][55][i]
    path_bull = bool(e21 is not None and e55 is not None and e21 > e55 and cur["c"] > e21)
    h_now = s["macd"]["hist"][i]
    h_prev = _at(s["macd"]["hist"], i - 1)
    pflags = {"bullishPath": path_bull, "pathBoundary": bool(e21 and abs(cur["l"] - e21) <= 0.4 * atr),
              "retestObserved": bool(e21 and prev["l"] <= e21 and cur["c"] >= e21),
              "momentumConfirmed": (h_now if h_now is not None else 0) > (h_prev if h_prev is not None else 0)}
    conf_on = recovery and families >= 2
    path_on = all(pflags.values())
    zone = {"kind": "DEMAND", "low": min(fib, e50 if e50 is not None else fib) - 0.15 * atr,
            "high": max(fib, e50 if e50 is not None else fib) + 0.15 * atr, "anchor": fib, "widthAtr": 0.7,
            "sources": [], "valid": True,
            "actionable": abs((e50 if e50 is not None else fib) - fib) / atr <= 1.25}
    g = geom_from_zone(zone, cur["c"], atr, hi)
    ct = cur["t"]
    return [
        _hit("lattice", "CONFLUENCE_RECLAIM_ACCEPTED", "CONFLUENCE_RECLAIM_ACCEPTED",
             {"recoveryObserved": recovery, "twoFamilies": families >= 2},
             "CONFLUENCE_RECLAIM_ACCEPTED" if conf_on else "OVERLAP" if families >= 2
             else "SINGLE_FAMILY" if families == 1 else "NONE",
             "Independence is genealogy, not a count of similar averages. Disjoint intervals stay disjoint.",
             "Need a second independent support family." if families < 2 else "Confluence reclaimed." if recovery
             else "Need completed recovery at the overlap.", g, force_active=conf_on,
             observed_at=ct if conf_on else None),
        _hit("lattice", "PATH_RETEST_ACCEPTED", "PATH_RETEST_ACCEPTED", pflags,
             "PATH_RETEST_ACCEPTED" if path_on else "PATH_CANDIDATE" if path_bull else "NO_PATH",
             "Persistent swing path. A revision updates the same hypothesis — it does not mint a new setup.",
             _next_of(_miss(pflags), "Path retest accepted."), g, force_active=path_on,
             observed_at=ct if path_on else None),
    ]


def run_zenith(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    lows = [p for p in s["pivots"] if p["kind"] == "LOW" and p["knownIndex"] <= i]
    last_two = lows[-2:]
    regular = hidden = False
    if len(last_two) == 2:
        a, b = last_two
        ra, rb = s["rsi14"][a["index"]], s["rsi14"][b["index"]]
        if ra is not None and rb is not None:
            regular = b["price"] < a["price"] and rb > ra
            hidden = b["price"] > a["price"] and rb < ra
    demand = nearest_zone(s["demand"], cur["c"])
    structural = bool(demand and cur["l"] <= demand["high"])
    sweep = bool(demand and cur["l"] <= demand["low"] and cur["c"] >= demand["anchor"])
    recovery = cur["c"] > prev["c"]
    h_now, h_prev = s["macd"]["hist"][i], _at(s["macd"]["hist"], i - 1)
    accel = (h_now if h_now is not None else 0) > (h_prev if h_prev is not None else 0)
    e50, e55 = s["ema"][50][i], s["ema"][55][i]
    trend_hold = bool((e50 is not None and cur["l"] <= e50 + (s["atr"] or 0) * 0.2 and cur["c"] >= e50) or
                      (e55 is not None and cur["c"] >= e55))
    rflags = {"causalDivergence": regular, "structuralZone": structural,
              "sweepOrReclaim": sweep or (structural and recovery), "acceleration": accel}
    hflags = {"causalDivergence": hidden, "structuralZone": structural or trend_hold, "trendSupportHeld": trend_hold,
              "acceleration": accel}
    rev_on, hid_on = all(rflags.values()), all(hflags.values())
    ups = [z for z in s["supply"] if z["low"] > cur["c"]]
    nz = nearest_zone(ups, cur["c"])
    g = geom_from_zone(demand, cur["c"], s["atr"], nz["low"] if nz else None)
    ct = cur["t"]
    return [
        _hit("apex", "REGULAR_REVERSAL", "REVERSAL_RESOLUTION_ACCEPTED", rflags,
             "REVERSAL_RESOLUTION_ACCEPTED" if rev_on else "DIVERGENCE_FORMED" if regular else "NO_DIVERGENCE",
             "Factor-decoupled regular reversal. Oscillator rarity is context — it is not a second vote.",
             "No structural support — Zenith will not invent one." if not structural
             else _next_of(_miss(rflags), "Reversal resolved."), g, force_active=rev_on,
             observed_at=ct if rev_on else None),
        _hit("apex", "HIDDEN_CONTINUATION", "HIDDEN_CONTINUATION_ACCEPTED", hflags,
             "HIDDEN_CONTINUATION_ACCEPTED" if hid_on else "HIDDEN_FORMED" if hidden else "NO_HIDDEN",
             "Higher low inside a held residual trend. Correlated oscillators are not independent evidence.",
             _next_of(_miss(hflags), "Hidden continuation accepted."), g, force_active=hid_on,
             observed_at=ct if hid_on else None),
    ]


def run_strata(s):
    i, cur, prev = s["i"], s["cur"], s["prev"]
    look = s["bars"][max(0, i - 20):]
    atr = s["atr"] if s["atr"] is not None else cur["c"] * 0.02
    base = look[:4]
    origin = len(base) == 4 and all(b["h"] - b["l"] < 1.1 * atr for b in base)
    o_low = min(b["l"] for b in base) if origin else None
    o_high = max(b["h"] for b in base) if origin else None
    departure = bool(o_low is not None and cur["c"] - look[0]["c"] > 1.4 * atr)
    first_return = bool(departure and o_high is not None and cur["l"] <= o_high + 0.15 * atr and cur["c"] >= prev["c"])
    demand = nearest_zone(s["demand"], cur["c"])
    touch = bool(demand and cur["l"] <= demand["high"])
    ss = s["participation"]["surpriseSigma"]
    vacuum = s["shape"]["lower"] >= 0.55 and (ss if ss is not None else 0) < -0.5
    absorption = bool(touch and s["shape"]["lower"] >= 0.3 and s["participation"]["confirmed"] and
                      cur["c"] >= (cur["h"] + cur["l"]) / 2 and not vacuum)
    hold = cur["c"] > prev["c"] and demand is not None and cur["c"] >= demand["high"]
    aflags = {"absorption": absorption, "holdOrReclaim": hold,
              "participationConfirmed": s["participation"]["confirmed"], "vacuumBounce": vacuum}
    dflags = {"demandOrigin": origin, "impulsiveDeparture": departure, "firstControlledReturn": first_return,
              "holdOrReclaim": cur["c"] >= prev["c"], "participationConfirmed": s["participation"]["confirmed"]}
    abs_on = absorption and hold and s["participation"]["confirmed"] and not vacuum
    dep_on = all(dflags.values())
    if o_low is not None and o_high is not None:
        zone = {"kind": "DEMAND", "low": o_low, "high": o_high, "anchor": (o_low + o_high) / 2,
                "widthAtr": (o_high - o_low) / atr, "sources": [], "valid": True,
                "actionable": (o_high - o_low) / atr <= 1.25}
    else:
        zone = demand
    g = geom_from_zone(zone, cur["c"], atr, None)
    ct = cur["t"]
    return [
        _hit("strata", "ABSORPTION_RECLAIM", "ABSORPTION_RECLAIM_ACCEPTED", aflags,
             "ABSORPTION_RECLAIM_ACCEPTED" if abs_on else "VACUUM_BOUNCE" if vacuum else "ABSORBING" if absorption
             else "AT_DEMAND" if touch else "AWAY",
             "Absorption is effort versus progress. A low-participation bounce is VACUUM_BOUNCE.",
             "Vacuum bounce — not demand." if vacuum else _next_of(_miss(aflags), "Absorption accepted."), g,
             force_active=abs_on, observed_at=ct if abs_on else None),
        _hit("strata", "DEPARTURE_RETEST", "DEPARTURE_RETEST_ACCEPTED", dflags,
             "DEPARTURE_RETEST_ACCEPTED" if dep_on else "FIRST_RETURN" if first_return else "DEPARTED" if departure
             else "ORIGIN_FORMED" if origin else "NO_ORIGIN",
             "Four-bar origin freezes. First controlled return is measured against origin-time ATR.",
             _next_of(_miss(dflags), "Departure retest accepted."), g, force_active=dep_on,
             observed_at=ct if dep_on else None),
    ]


def run_all_engines(s):
    out = []
    for fn in (run_vector, run_meridian, run_cascade, run_threshold, run_fissure, run_dread, run_reverb, run_zenith,
               run_strata):
        out += fn(s)
    return out


def snapshot_anti_chase(s, g):
    return anti_chase_facts(s["cur"]["c"], s["cur"]["o"], s["prev"]["c"], s["atr"], g["zoneHigh"], g["trigger"],
                            s["shape"], s["robustSigma"], g["rr"], s["participation"]["confirmed"])


# -- physics.ts ----------------------------------------------------------------------------------------------------------
def coord(name, value, unit):
    num = isinstance(value, (int, float)) and not isinstance(value, bool)
    if value is None or (num and not math.isfinite(value)):
        state = "ABSENT"
    elif num and abs(value) < 1e-12:
        state = "SPARSE"
    else:
        state = "PRESENT"
    return {"name": name, "value": js_round(value * 1000) / 1000 if (num and finite(value)) else value, "unit": unit,
            "state": state}


def field_mass(price, anchors, bw):
    if price <= 0 or not anchors or bw <= 0:
        return None
    keys = []
    for a in anchors:
        k = js_round(vlog(a) * 1e4)
        if k not in keys:
            keys.append(k)
    uniq = [vexp(k / 1e4) for k in keys]
    mass = 0.0
    lp = vlog(price)
    h2 = 2 * bw * bw
    for a in uniq:
        if a <= 0:
            continue
        mass += vexp(-vpow(lp - vlog(a), 2) / h2)
    return mass


def defense_elasticity(rec, pen, bars_to):
    if not all(finite(x) for x in (rec, pen, bars_to)):
        return None
    return rec / (max(0.1, pen) * max(1, bars_to))


def impact_elasticity(pen, effort):
    if not finite(pen) or not finite(effort):
        return None
    return pen / max(0.1, effort)


def auction_race(bars, boundary, sigma, frm, to, kappa=0.35):
    if sigma <= 0:
        return {"accept": 0, "reject": 0, "outsideFrac": None}
    accept = reject = 0.0
    outside = n = 0
    for i in range(frm, to + 1):
        den = bars[i]["c"] * sigma
        x = (bars[i]["c"] - boundary) / (den if den else sigma)
        accept = max(0, accept + x - kappa)
        reject = max(0, reject - x - kappa)
        if bars[i]["c"] > boundary:
            outside += 1
        n += 1
    return {"accept": accept, "reject": reject, "outsideFrac": outside / n if n else None}


def confluence_surprisal(real_k, real_w, nulls):
    if not nulls:
        return None
    beat = len([x for x in nulls if x["k"] >= real_k and x["w"] <= real_w])
    return -vlog((1 + beat) / (len(nulls) + 1))


def divergence_surprisal(u, v, priors):
    if len(priors) < 6:
        return None
    beat = len([p for p in priors if p["u"] <= u and p["v"] >= v])
    return -vlog((1 + beat) / (len(priors) + 1))


def change_concentration(events, i):
    last = next((e for e in reversed(events) if e["dir"] == "UP"), None)
    if not last:
        return {"age": None, "intensity": 0, "recent": False}
    age = i - last["index"]
    cluster = len([e for e in events if e["dir"] == "UP" and i - e["index"] <= 8])
    return {"age": age, "intensity": cluster, "recent": age <= 5}


def zone_visit(s, zone):
    if not zone or not s["atr"]:
        return {"visits": 0, "lastPenetration": None, "barsToRecover": None, "recovery": None}
    visits = 0
    in_zone = False
    touch = -1
    worst = 0.0
    recover_bars = None
    recovery = None
    for i in range(max(1, s["i"] - 40), s["i"] + 1):
        b = s["bars"][i]
        touching = b["l"] <= zone["high"] and b["h"] >= zone["low"]
        if touching and not in_zone:
            visits += 1
            in_zone = True
            touch = i
            worst = max(0, (zone["low"] - b["l"]) / s["atr"])
        elif touching:
            worst = max(worst, max(0, (zone["low"] - b["l"]) / s["atr"]))
        elif in_zone and b["c"] > zone["high"]:
            recover_bars = i - touch
            recovery = (b["c"] - zone["low"]) / s["atr"]
            in_zone = False
    return {"visits": visits, "lastPenetration": worst or None, "barsToRecover": recover_bars, "recovery": recovery}


def origin_mass(base_duration, base_contraction, departure_eff, residual_dep, participation_q, zone_width):
    if zone_width <= 0 or base_duration <= 0:
        return None
    contraction = 1 / max(0.15, base_contraction)
    dep = departure_eff if departure_eff is not None else 0.35
    resid = max(0, residual_dep if residual_dep is not None else 0.35)
    part = max(0.15, participation_q if participation_q is not None else 0.35)
    return (base_duration * contraction * dep * resid * part) / zone_width


def scale_front(now, prior, price, periods=(8, 13, 21, 55), gamma=0.5):
    depth = advancing = 0
    d1 = []
    for i, p in enumerate(periods):
        a, b = now[i], prior[i]
        if a is None or b is None or price <= 0:
            d1.append(0)
            continue
        deriv = vpow(p, gamma) * ((a - b) / price)
        d1.append(deriv)
        if deriv > 0:
            depth = p
            advancing += 1
    return {"depth": depth, "advancing": advancing, "velocity": advancing / len(periods), "d1": d1}


def topology_energy(now, lagged):
    gaps, lg = [], []
    for i in range(len(now) - 1):
        if now[i] is None or now[i + 1] is None or lagged[i] is None or lagged[i + 1] is None:
            continue
        gaps.append(now[i] - now[i + 1])
        lg.append(lagged[i] - lagged[i + 1])
    if not gaps:
        return None
    acc = 0.0
    for a, b in zip(gaps, lg):
        acc += vpow(a - b, 2)
    return math.sqrt(acc)


def hysteresis_path(evidence, rho=0.85, H=4):
    L = 0.0
    path = []
    for e in evidence:
        L = max(-H, min(H, rho * L + e))
        path.append(L)
    last = path[-1] if path else 0
    return {"L": last, "path": path, "committedBull": last >= H - 1, "committedBear": last <= -(H - 1),
            "provisional": 0 < last < H - 1}


def cloud_innovation(d_fast, d_slow, beta):
    if not all(math.isfinite(x) for x in (d_fast, d_slow, beta)):
        return None
    return d_fast - beta * d_slow


def approach_cycles(bars, boundary, atr, frm, to):
    cycles = 0
    in_touch = False
    last_depart = -99
    depths = []
    worst = 0.0
    for i in range(frm, to + 1):
        b = bars[i]
        touching = b["h"] >= boundary - 0.35 * atr and b["c"] <= boundary
        if touching:
            worst = max(worst, max(0, (boundary - b["l"]) / atr))
            if not in_touch and i - last_depart >= 2:
                cycles += 1
                in_touch = True
        elif in_touch:
            depths.append(worst)
            worst = 0.0
            in_touch = False
            last_depart = i
    if in_touch and worst > 0:
        depths.append(worst)
    contraction = depths[-1] / max(0.05, depths[0]) if len(depths) >= 2 else None
    return {"cycles": cycles, "depths": depths, "contraction": contraction}


def departure_quality(bars, origin, atr):
    if origin < 0 or origin >= len(bars) - 1 or atr <= 0:
        return None
    start = bars[origin]["l"]
    last = min(len(bars) - 1, origin + 6)
    end = bars[last]["c"]
    exc = (end - start) / atr
    path = 0.0
    for i in range(origin + 1, last + 1):
        path += abs(bars[i]["c"] - bars[i - 1]["c"]) / atr
    return {"excursion": exc, "efficiency": abs(exc) / path if path > 0 else None}


def weighted_field_mass(price, anchors, bw):
    if price <= 0 or not anchors or bw <= 0:
        return None
    lp = vlog(price)
    h2 = 2 * bw * bw
    mass = 0.0
    for a in anchors:
        if a["price"] <= 0 or a["weight"] <= 0:
            continue
        mass += a["weight"] * vexp(-vpow(lp - vlog(a["price"]), 2) / h2)
    return mass


def bocd_run_length(residuals, hazard=1 / 40):
    xs = [v for v in residuals if v is not None and math.isfinite(v)][-80:]
    if len(xs) < 12:
        return {"runLength": None, "concentration": None}
    mu = mean(xs) or 0
    m2 = mean([vpow(x - mu, 2) for x in xs])
    sd = math.sqrt(m2 if m2 is not None else 0) or 0.01
    run = 1
    for i in range(1, len(xs)):
        z = abs((xs[i] - mu) / sd)
        p_same = vexp(-0.5 * z * z)
        run = 1 if p_same < hazard else run + 1
    return {"runLength": run, "concentration": 1 / max(1, run)}


# -- ascend.ts -----------------------------------------------------------------------------------------------------------
def _coordinates(s, hit):
    i, cur = s["i"], s["cur"]
    demand = nearest_zone(s["demand"], cur["c"])
    visit = zone_visit(s, demand)
    elast = defense_elasticity(visit["recovery"] if visit["recovery"] is not None else 0,
                               visit["lastPenetration"] if visit["lastPenetration"] is not None else 0,
                               visit["barsToRecover"] if visit["barsToRecover"] is not None else 0)
    ss = s["participation"]["signedSigma"]
    impact = impact_elasticity(visit["lastPenetration"] if visit["lastPenetration"] is not None else 0,
                               max(0.1, -(ss if ss is not None else 0)))
    res = s["residual"]
    change = change_concentration(s["cusum"]["events"], i)
    E = s["ema"]
    now = [E[8][i], E[13][i], E[21][i], E[55][i]]
    prior = [_at(E[8], i - 1), _at(E[13], i - 1), _at(E[21], i - 1), _at(E[55], i - 1)]
    lagged = [_at(E[8], i - 3), _at(E[13], i - 3), _at(E[21], i - 3), _at(E[55], i - 3)] if i >= 4 else prior
    front = scale_front(now, prior, cur["c"])
    energy = topology_energy(now, lagged)
    sig = s["sigmaOne"] if s["sigmaOne"] is not None else 0.02
    d_mass = field_mass(cur["c"], [z["anchor"] for z in s["demand"]], sig)
    s_mass = field_mass(cur["c"], [z["anchor"] for z in s["supply"]], sig)
    anchors = []
    for z in s["demand"]:
        q = departure_quality(s["bars"], z["sources"][0] if z["sources"] else i - 8,
                              s["atr"] if s["atr"] is not None else 1)
        eff = q["efficiency"] if (q and q["efficiency"] is not None) else 0.4
        anchors.append({"price": z["anchor"], "weight": max(0.15, eff)})
    weighted = weighted_field_mass(cur["c"], anchors, sig)
    rs_unit = "bench-sigma" if res["state"] == "PRESENT" else "absent"
    sid = hit["scannerId"]
    if sid == "vector":
        return [coord("demandMass", weighted if weighted is not None else d_mass, "field"),
                coord("supplyMass", s_mass, "field"), coord("elasticity", elast, "ratio"),
                coord("visits", visit["visits"], "count"), coord("penetration", visit["lastPenetration"], "ATR"),
                coord("residual", res["last"], rs_unit)]
    if sid == "strata":
        look = s["bars"][max(0, i - 20):max(0, i - 16)]
        atr = s["atr"] if s["atr"] is not None else 1
        ranges = [(b["h"] - b["l"]) / atr for b in look]
        contraction = (sum_left(ranges) / len(ranges)) if ranges else 1
        mass = origin_mass(len(look) or 4, contraction, path_efficiency(s["closes"][max(0, i - 12):]),
                           abs(res["last"]) / s["sigmaOne"] if (res["last"] is not None and s["sigmaOne"]) else None,
                           s["participation"]["surpriseSigma"], demand["widthAtr"] if demand else 1)
        return [coord("originMass", mass, "field"), coord("impactElasticity", impact, "ratio"),
                coord("originVisits", visit["visits"], "count"), coord("vacuum", "VACUUM" in hit["nativePhase"], "boolean"),
                coord("participation", s["participation"]["signedSigma"], "sigma"),
                coord("residual", res["last"], rs_unit)]
    if sid == "meridian":
        run = bocd_run_length(res["series"])
        return [coord("residual", res["last"], rs_unit),
                coord("beta", res["beta"], "Theil-Sen" if res["state"] == "PRESENT" else "absent"),
                coord("cusumAge", change["age"], "bars"), coord("changeIntensity", change["intensity"], "count"),
                coord("runLength", run["runLength"], "bars"), coord("entropy", s["entropy"]["h"], "nats")]
    if sid == "ravel":
        return [coord("frontDepth", front["depth"], "ema"), coord("frontVelocity", front["velocity"], "fraction"),
                coord("topologyEnergy", energy, "norm"), coord("compression", s["entropy"]["compression"], "rank")]
    if sid == "breakline":
        g = hit["geometry"]
        boundary = g["trigger"] if g["trigger"] is not None else g["zoneLow"]
        race = auction_race(s["bars"], boundary, s["sigmaOne"], max(0, i - 12), i) \
            if (boundary is not None and s["sigmaOne"]) else {"accept": 0, "reject": 0, "outsideFrac": None}
        appr = approach_cycles(s["bars"], boundary, s["atr"], max(0, i - 30), i) \
            if (boundary is not None and s["atr"]) else {"cycles": 0, "contraction": None}
        return [coord("accept", race["accept"], "accumulator"), coord("reject", race["reject"], "accumulator"),
                coord("outsideFrac", race["outsideFrac"], "fraction"), coord("approachCycles", appr["cycles"], "count"),
                coord("rejectionContraction", appr["contraction"], "ratio"),
                coord("compression", s["entropy"]["compression"], "rank")]
    if sid == "ripster":
        e5, e12, e21, e34, e50 = E[5][i], E[12][i], E[21][i], E[34][i], E[50][i]
        p5, p12, p34, p50 = _at(E[5], i - 1), _at(E[12], i - 1), _at(E[34], i - 1), _at(E[50], i - 1)
        fast = e5 - e12 if (e5 is not None and e12 is not None) else None
        slow = e34 - e50 if (e34 is not None and e50 is not None) else None
        d_fast = e5 - e12 - (p5 - p12) if None not in (e5, e12, p5, p12) else None
        d_slow = e34 - e50 - (p34 - p50) if None not in (e34, e50, p34, p50) else None
        innov = cloud_innovation(d_fast, d_slow, 0.6) if (d_fast is not None and d_slow is not None) else None
        e20 = E[20][i]
        ordered = (int(e5 > e12) + int(e21 > (e20 if e20 is not None else e21)) + int(e34 > e50)) \
            if None not in (e5, e12, e21, e34, e50) else 0
        return [coord("fastGap", fast, "price"), coord("slowGap", slow, "price"), coord("fastInnovation", innov, "price"),
                coord("cloudOrder", ordered, "count"), coord("mtfClocks", "ABSENT on daily tape", "enum"),
                coord("participation", s["participation"]["signedSigma"], "sigma")]
    if sid == "panic":
        weekly = weekly_from_daily(s["bars"])
        ev = []
        for k, b in enumerate(weekly):
            if k == 0:
                ev.append(0)
            elif b["c"] > weekly[k - 1]["c"] and b["c"] > b["o"]:
                ev.append(1)
            elif b["c"] < weekly[k - 1]["c"] and b["c"] < b["o"]:
                ev.append(-1)
            else:
                ev.append(0)
        Hh = hysteresis_path(ev)
        return [coord("hysteresis", Hh["L"], "L"), coord("committedBull", Hh["committedBull"], "boolean"),
                coord("residual", res["last"], rs_unit), coord("weeklyClock", "derived from daily", "enum"),
                coord("participation", s["participation"]["signedSigma"], "sigma")]
    if sid == "lattice":
        def families_at(end):
            window = s["bars"][max(0, end - 40):end + 1]
            if len(window) < 8:
                return {"k": 0, "w": 9}
            hi = max(b["h"] for b in window)
            lo = min(b["l"] for b in window)
            atr = s["atr"] if s["atr"] is not None else cur["c"] * 0.02
            fib = hi - 0.618 * (hi - lo)
            e50 = E[50][end]
            at_fib = abs(s["bars"][end]["c"] - fib) <= 0.35 * atr
            at50 = e50 is not None and abs(s["bars"][end]["c"] - e50) <= 0.35 * atr
            return {"k": int(at_fib) + int(at50), "w": abs((e50 if e50 is not None else fib) - fib) / atr}
        real = families_at(i)
        nulls = []
        shift = 8
        while shift <= 80 and i - shift > 40:
            nulls.append(families_at(i - shift))
            shift += 8
        return [coord("demandMass", d_mass, "field"),
                coord("confluenceSurprisal", confluence_surprisal(real["k"], real["w"], nulls), "nats"),
                coord("families", real["k"], "count"), coord("pathBull", "PATH" in hit["nativePhase"], "boolean"),
                coord("entropy", s["entropy"]["h"], "nats")]
    if sid == "apex":
        lows = [p for p in s["pivots"] if p["kind"] == "LOW" and p["knownIndex"] <= i][-8:]
        priors = []
        for k in range(1, len(lows)):
            a, b = lows[k - 1], lows[k]
            if not s["sigmaOne"] or a["price"] <= 0:
                continue
            ra, rb = s["rsi14"][a["index"]], s["rsi14"][b["index"]]
            if ra is None or rb is None:
                continue
            priors.append({"u": vlog(b["price"] / a["price"]) / s["sigmaOne"], "v": rb - ra})
        last = priors[-1] if priors else None
        sur = divergence_surprisal(last["u"], last["v"], priors[:-1]) if last else None
        h_now, h_prev = s["macd"]["hist"][i], _at(s["macd"]["hist"], i - 1)
        return [coord("surprisal", sur, "nats"), coord("residual", res["last"], rs_unit),
                coord("beta", res["beta"], "Theil-Sen" if res["state"] == "PRESENT" else "absent"),
                coord("structuralMass", d_mass, "field"),
                coord("acceleration", (h_now if h_now is not None else 0) - (h_prev if h_prev is not None else 0), "macd")]
    return [coord("demandMass", d_mass, "field"), coord("supplyMass", s_mass, "field"),
            coord("entropy", s["entropy"]["h"], "nats")]


def sum_left(xs):
    acc = 0.0
    for x in xs:
        acc = acc + x
    return acc


def _refine(s, hit, coords):
    if hit["active"] or hit["failed"]:
        return hit["nativePhase"]

    def num(name):
        c = next((x for x in coords if x["name"] == name), None)
        v = c["value"] if c else None
        return v if (isinstance(v, (int, float)) and not isinstance(v, bool)) else None

    def flag(name):
        c = next((x for x in coords if x["name"] == name), None)
        return bool(c) and c["value"] is True
    sid, ph = hit["scannerId"], hit["nativePhase"]
    if sid == "vector" and ph == "TESTING":
        e = num("elasticity")
        if e is not None and e > 0.8:
            return "DEFENSE_STRENGTHENING"
        if e is not None and e < 0.25:
            return "DEFENSE_DEPLETING"
    if sid == "breakline" and ph == "PRESSING":
        a, r = num("accept"), num("reject")
        if a is not None and r is not None and a > r:
            return "PRESSING_ACCEPT_LEADS"
        if a is not None and r is not None and r > a:
            return "PRESSING_REJECT_LEADS"
    if sid == "ravel" and ph in ("COILED", "TRANSITIONING"):
        v, e = num("frontVelocity"), num("topologyEnergy")
        if v is not None and v >= 0.75 and (e if e is not None else 0) > 0:
            return "IGNITING"
    if sid == "meridian" and ph == "LOCATION_READY":
        age = num("cusumAge")
        if age is not None and age <= 5:
            return "CHANGE_CONCENTRATED"
    if sid == "panic" and ph == "PROVISIONAL_OR_BEAR":
        if flag("committedBull"):
            return "CLOSED_FLIP_COMMITTED"
        L = num("hysteresis")
        if L is not None and 0 < L < 3:
            return "PROVISIONAL_FLIP"
    if sid == "ripster" and ph == "CLOUD_COMPRESSED":
        o = num("cloudOrder")
        if o is not None and o >= 2:
            return "CLOUD_ORDERING"
    if sid == "strata" and ph == "ORIGIN_FORMED":
        m = num("originMass")
        if m is not None and m > 2:
            return "HIGH_MASS_ORIGIN"
    return ph


def ascend_hit(s, hit):
    coords = _coordinates(s, hit)
    return dict(hit, coords=coords, nativePhase=_refine(s, hit, coords))


# -- catalog.ts / scan.ts ------------------------------------------------------------------------------------------------
IDENTITIES = {"vector": ("Vector", "ledger"), "meridian": ("Meridian", "ledger"), "ravel": ("Cascade", "ledger"),
              "breakline": ("Threshold", "ledger"), "ripster": ("Fissure", "ledger"), "panic": ("Dread", "ledger"),
              "lattice": ("Reverb", "wheel"), "apex": ("Zenith", "wheel"), "strata": ("Strata", "wheel")}
MIN_BARS = 55
QUIET = {"PASS", "QUIET", "NO_PATH", "NO_DIVERGENCE", "NO_HIDDEN", "NO_ORIGIN", "NO_FAILED_BEAR", "NO_BREACH",
         "NO_PULLBACK", "AWAY", "POC_ABSENT", "PROVISIONAL_OR_BEAR", "DISORDERED", "BASE"}
GRADE_RANK = {"S": 0, "A": 1, "B": 2, "C": 3, "PASS": 4}


def _grade(active, ready, formed, failed, anti, actionable):
    if failed and not active:
        return "PASS"
    if active and anti and actionable:
        return "S"
    if active or ready:
        return "A"
    if formed:
        return "B"
    return "C"


def _phase(active, ready, formed, failed, anti):
    if failed and not active:
        return "FAILED"
    if active and anti:
        return "ACTIVE"
    if active or ready:
        return "READY"
    if formed:
        return "FORMING"
    return "DISCOVERED"


def scan_prism_symbol(symbol, bars, bench=None):
    if len(bars) < MIN_BARS:
        return {"symbol": symbol, "coverage": "unavailable",
                "reason": f"Need {MIN_BARS} completed daily bars (have {len(bars)}).", "barCount": len(bars),
                "completedBarAt": bars[-1]["t"] if bars else None, "close": bars[-1]["c"] if bars else None,
                "episodes": []}
    snap = build_snapshot(bars, bench)
    if not snap:
        return {"symbol": symbol, "coverage": "quarantined", "reason": "Kernel could not build a causal snapshot.",
                "barCount": len(bars), "completedBarAt": bars[-1]["t"], "close": bars[-1]["c"], "episodes": []}
    episodes = []
    for h in run_all_engines(snap):
        if h["failed"] and not h["active"] and not h["ready"] and not h["formed"] and not h["discovered"]:
            continue
        if not h["active"] and not h["ready"] and not h["formed"] and not h["discovered"]:
            continue
        if h["nativePhase"] in QUIET and not h["active"]:
            continue
        name, service = IDENTITIES[h["scannerId"]]
        risen = ascend_hit(snap, h)
        chase = snapshot_anti_chase(snap, risen["geometry"])
        grade = _grade(risen["active"], risen["ready"], risen["formed"], risen["failed"], chase["pass"],
                       risen["geometry"]["actionable"])
        phase = _phase(risen["active"], risen["ready"], risen["formed"], risen["failed"], chase["pass"])
        ct = snap["cur"]["t"]
        episodes.append({"symbol": symbol, "scannerId": risen["scannerId"], "publicName": name, "service": service,
                         "lane": risen["lane"], "event": risen["event"], "grade": grade, "phase": phase,
                         "nativePhase": risen["nativePhase"], "note": risen["note"],
                         "nextCondition": risen["nextCondition"], "close": snap["cur"]["c"], "completedBarAt": ct,
                         "missing": risen["missing"], "geometry": risen["geometry"], "antiChase": chase["pass"],
                         "clocks": {"economicAt": ct, "knownAt": ct, "observedAt": risen["observedAt"],
                                    "evaluatedAt": ct},
                         "conflicts": risen["conflicts"], "movement": "NEW", "coords": risen["coords"]})
    episodes.sort(key=lambda e: (GRADE_RANK[e["grade"]], e["publicName"]))
    return {"symbol": symbol, "coverage": "usable", "reason": None, "barCount": len(bars),
            "completedBarAt": snap["cur"]["t"], "close": snap["cur"]["c"], "episodes": episodes}
