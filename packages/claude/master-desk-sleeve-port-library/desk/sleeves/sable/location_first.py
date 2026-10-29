"""Location-first Repair v2.1.0 — line-by-line port of autopilot-desk @48e8f90f (Sable):

  src/lib/scanner/location-first-repair.mjs   blob 5377c97f  evaluate() / chooseShelf() / deskActionOf()
  src/lib/scanner/location-first-desk.mjs     blob 0b1c5417  resultToDeskRow() / buildLocationFirstScan() /
                                                             runLocationFirstUniverse()'s two-pass funnel
  src/lib/scanner/leaders-rest-core.mjs       blob 5df6186e  evaluateLeaders() (the funnel's leaders shortlist)
  src/lib/scanner/desk-core.mjs               blob 1b5f9041  candidateCap() / fillCap() / radarCap()

Pure functions over plain dicts (the sources' field names), JS number semantics (desk/sleeves/jsport.py).
Parity: tools/parity/sable_location_first.py drives the original modules under Node on the same inputs."""
import math

from ..jsport import INF, at, gt, jmax, jmin, jor, js_round, lsum, num, number

LOCATION_FIRST_VERSION = "2.1.0"
LOCATION_FIRST_ID = "LOCATION_FIRST_REPAIR"
LOCATION_FIRST_SOURCE = "location-first"
DEEP_OHLC_CAP = 48
DESK_SCANNER = "desk"
DESK_BUY_TIERS = ("S", "A", "B")
DESK_BUY_ACTIONS = ("SETUP", "WATCH")
RADAR_DEFAULT = 36
DESK_FILL_DEFAULT = 7

DEFAULTS = {
    "minimumBars": 70, "swingLookback": 60, "ema21Period": 21, "ema50Period": 50, "rsiPeriod": 14, "atrPeriod": 14,
    "macdFastPeriod": 12, "macdSlowPeriod": 26, "macdSignalPeriod": 9, "lowLookback": 12, "macdLiftWindowBars": 4,
    "on21Pct": 0.02, "near12Pct": 0.04, "fibPct": 0.025, "confluencePct": 0.025, "maxShelfExtensionPct": 0.03,
    "rsiMin": 28, "rsiMax": 52, "highQualityRsiMin": 40, "highQualityRsiMax": 52, "ema50SlopeLookback": 10,
    "ema50CollapsePct": -0.015, "washLookback": 20, "washMinPct": 0.08, "maxLiveBuys": 7, "stopAtrMultiple": 0.5,
    "resistanceClusterPct": 0.015, "maxPriorResistanceLevels": 3,
}


def _first(*xs):
    """a ?? b ?? c (None = null/undefined)."""
    for x in xs:
        if x is not None:
            return x
    return None


# -- indicators (location-first-repair.mjs) --------------------------------------------------------------------
def ema_series(closes, period):
    if not isinstance(closes, list) or len(closes) < period:
        return []
    k = 2 / (period + 1)
    seed = 0
    for i in range(period):
        seed += closes[i]
    seed /= period
    out = [None] * len(closes)
    out[period - 1] = seed
    for i in range(period, len(closes)):
        out[i] = (closes[i] - out[i - 1]) * k + out[i - 1]
    return out


def wilder_rsi(closes, period=14):
    if not isinstance(closes, list) or len(closes) <= period:
        return []
    out = [None] * len(closes)
    gain = 0
    loss = 0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gain += d
        else:
            loss -= d
    gain /= period
    loss /= period
    out[period] = 100 if loss == 0 else 100 - 100 / (1 + gain / loss)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        gain = (gain * (period - 1) + max(d, 0)) / period
        loss = (loss * (period - 1) + max(-d, 0)) / period
        out[i] = 100 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def wilder_atr(bars, period=14):
    if not isinstance(bars, list) or len(bars) < period + 1:
        return []
    tr = []
    for i in range(len(bars)):
        high = num(bars[i].get("high"))
        low = num(bars[i].get("low"))
        if i == 0:
            tr.append(high - low if high is not None and low is not None else None)
            continue
        prev = num(bars[i - 1].get("close"))
        if high is None or low is None or prev is None:
            tr.append(None)
            continue
        tr.append(max(high - low, abs(high - prev), abs(low - prev)))
    out = [None] * len(bars)
    seed = [n for n in tr[1:period + 1] if n is not None]
    if len(seed) < period:
        return out
    atr = lsum(seed) / period
    out[period] = atr
    for i in range(period + 1, len(bars)):
        if tr[i] is None:
            continue
        atr = (atr * (period - 1) + tr[i]) / period
        out[i] = atr
    return out


def macd_histogram_series(closes, fast=12, slow=26, signal=9):
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    macd = [(ema_fast[i] - ema_slow[i]) if (at(ema_fast, i) is not None and at(ema_slow, i) is not None) else None
            for i in range(len(closes))]
    valid, index_map = [], []
    for i, m in enumerate(macd):
        if m is not None:
            valid.append(m)
            index_map.append(i)
    sig = ema_series(valid, signal)
    hist = [None] * len(closes)
    for j in range(len(valid)):
        if j >= len(sig) or sig[j] is None:
            continue
        hist[index_map[j]] = valid[j] - sig[j]
    return hist


def normalize_bars(raw=None):
    rows, seen = [], set()
    for bar in raw if isinstance(raw, list) else []:
        bar = bar or {}
        time = number(_first(bar.get("time"), bar.get("at"), bar.get("t")))
        close = num(_first(bar.get("close"), bar.get("c")))
        open_ = num(_first(bar.get("open"), bar.get("o")))
        open_ = _first(open_, close)
        high = _first(num(_first(bar.get("high"), bar.get("h"))), close)
        low = _first(num(_first(bar.get("low"), bar.get("l"))), close)
        volume = num(_first(bar.get("volume"), bar.get("v")))
        if not math.isfinite(time) or not gt(close, 0) or not gt(high, 0) or not gt(low, 0):
            continue
        if high < low:
            continue
        if time in seen:
            continue
        seen.add(time)
        rows.append({"time": time, "open": open_ if gt(open_, 0) else close, "high": high, "low": low, "close": close,
                     "volume": volume if volume is not None and volume >= 0 else 0})
    rows.sort(key=lambda r: r["time"])
    return rows


def fib_levels(bars, lookback=60):
    window = bars[-lookback:] if lookback else bars[:]
    if len(window) < 10:
        return []
    high = low = None
    high_i = low_i = -1
    for i, b in enumerate(window):
        if high is None or b["high"] >= high:
            high, high_i = b["high"], i
        if low is None or b["low"] <= low:
            low, low_i = b["low"], i
    if not (high > low) or low_i >= high_i:
        return []
    span = high - low
    return [{"kind": "FIB50", "price": high - span * 0.5, "weight": 3},
            {"kind": "FIB618", "price": high - span * 0.618, "weight": 4},
            {"kind": "FIB786", "price": high - span * 0.786, "weight": 2}]


def distance_pct(price, level):
    if not gt(price, 0) or not gt(level, 0):
        return None
    return abs(price - level) / price


def limit_for(kind, config):
    if kind == "EMA21":
        return config["on21Pct"]
    if kind == "LOW12":
        return config["near12Pct"]
    return config["fibPct"]


def choose_shelf(price, levels, config=DEFAULTS):
    candidates = []
    for level in levels:
        dist = distance_pct(price, level["price"])
        if dist is None:
            continue
        limit = limit_for(level["kind"], config)
        if level["kind"] == "LOW12":
            if (price - level["price"]) / level["price"] > config["near12Pct"] and dist > config["near12Pct"]:
                continue
        elif dist > config["on21Pct"] and dist > limit:
            continue
        kinds = [o["kind"] for o in levels
                 if o["kind"] != level["kind"] and distance_pct(price, o["price"]) is not None
                 and abs(o["price"] - level["price"]) / price <= config["confluencePct"]]
        score = level["weight"] + len(kinds) * 4 - dist * 100
        candidates.append(dict(level, distancePct=dist, confluenceKinds=kinds, candidateScore=score))
    candidates.sort(key=lambda c: (-c["candidateScore"], c["distancePct"]))
    winner = candidates[0] if candidates else None
    if winner is None:
        return None
    if winner["distancePct"] > limit_for(winner["kind"], config):
        return None
    return winner


def prior_resistance(bars, price, config=DEFAULTS):
    out = []
    highs = sorted(b["high"] for b in bars[:-1] if b["high"] > price)
    for high in highs:
        if any(abs(kept - high) / high <= config["resistanceClusterPct"] for kept in out):
            continue
        out.append(high)
        if len(out) >= config["maxPriorResistanceLevels"]:
            break
    return out


def score_of(shelf, recently_lifting, strong_repair, high_quality_rsi, rsi_up, under50, not_chasing,
             structural_breakdown, liquidity_ok):
    confluence = len(shelf.get("confluenceKinds") or []) if shelf else 0
    location = min(35, 15 + confluence * 5 + (8 if shelf["kind"] == "EMA21" else 3)) if shelf else 0
    repair = 18 if recently_lifting else 0
    if strong_repair:
        repair += 7
    if high_quality_rsi:
        repair += 5
    if rsi_up:
        repair += 3
    repair = min(30, repair)
    structure = 15 if (under50 and structural_breakdown is not True) else 0
    anti_chase = 15 if not_chasing else 0
    context = 0 if liquidity_ok is False else 5
    return min(100, location + repair + structure + anti_chase + context)


def public_reason(status, under50=None, shelf=None, recently_lifting=None, rsi=None, collapsing50=None, washed=None,
                  making_new_lows=None):
    if status == "UNAVAILABLE":
        return "Required daily market evidence is missing or invalid."
    if collapsing50:
        return "50-day is collapsing. That's a downtrend, not a shakeout."
    if status == "NOT_A_BUY":
        if not under50:
            return "Already back above the 50-day average. Not a buy at this price."
        if rsi is not None and rsi > 52:
            return "RSI is too high for this support repair."
        return "This setup failed a hard location, structure, liquidity, event, or RSI rule."
    if making_new_lows:
        return "Still printing new lows. Wait for the hold after the wash."
    if washed is False and under50:
        return "No real wash. A 2% drift is not fear."
    if status == "BUY_NOW":
        kind = (shelf or {}).get("kind")
        where = ("near the 21-day average" if kind == "EMA21" else
                 "near the 12-day low" if kind == "LOW12" else "near established support")
        lift = ", with MACD recently lifting over multiple sessions" if recently_lifting else ""
        return f"{where}, still under the 50-day average{lift}."
    if shelf:
        return "Support is nearby. Repair evidence is not complete at this price. Wait."
    if under50:
        return "Still under the 50-day average. Wait for the 21-day, the 12-day low, or Fibonacci support."
    return "Support or repair evidence is not complete at the current price."


def evaluate(inp=None):
    """location-first-repair.mjs evaluate(input)."""
    inp = inp or {}
    cfg_in = inp.get("config")
    config = dict(DEFAULTS, **(cfg_in if isinstance(cfg_in, dict) else {}))
    symbol = str(_first(inp.get("symbol"), inp.get("ticker"), "")).strip().upper()
    bars = normalize_bars(inp.get("bars"))
    reasons = []

    def unavailable(code):
        return {"symbol": symbol, "status": "UNAVAILABLE", "setup": None, "priority": None, "score": None,
                "reasonCodes": [code], "publicReason": public_reason("UNAVAILABLE"),
                "metrics": {"price": None, "ema21": None, "ema50": None, "rsi14": None, "atr14": None, "shelf": None},
                "plan": {"entryPrice": None, "stopPrice": None, "stopDistancePct": None, "priorResistance": []},
                "version": LOCATION_FIRST_VERSION}

    if not symbol:
        return unavailable("DATA_INSUFFICIENT_OR_INVALID")
    if len(bars) < config["minimumBars"]:
        return unavailable("DATA_INSUFFICIENT_OR_INVALID")
    last = bars[-1]
    live = num(inp.get("regularSessionPrice"))
    price = live if gt(live, 0) else last["close"]
    if not gt(price, 0):
        return unavailable("REGULAR_SESSION_PRICE_UNAVAILABLE")

    closes = [b["close"] for b in bars]
    ema21s = ema_series(closes, config["ema21Period"])
    ema50s = ema_series(closes, config["ema50Period"])
    rsis = wilder_rsi(closes, config["rsiPeriod"])
    atrs = wilder_atr(bars, config["atrPeriod"])
    hists = macd_histogram_series(closes, config["macdFastPeriod"], config["macdSlowPeriod"], config["macdSignalPeriod"])
    ema21, ema50, rsi14, prev_rsi, atr14 = at(ema21s, -1), at(ema50s, -1), at(rsis, -1), at(rsis, -2), at(atrs, -1)
    last4h, last4a = hists[-4:], atrs[-4:]
    if any(n is None or not math.isfinite(n) for n in (ema21, ema50, rsi14, atr14)) or \
            any(n is None for n in last4h) or any(not gt(n, 0) for n in last4a):
        return unavailable("INDICATORS_UNAVAILABLE")
    norm = [h / last4a[i] for i, h in enumerate(last4h)]
    deltas = [norm[1] - norm[0], norm[2] - norm[1], norm[3] - norm[2]]
    positive_steps = len([d for d in deltas if d > 0])
    net_lift = norm[3] - norm[0]
    recently_lifting = positive_steps >= 2 and net_lift > 0
    strong_repair = all(d > 0 for d in deltas) and norm[0] < 0

    low12 = jmin(b["low"] for b in bars[-config["lowLookback"]:])
    levels = [{"kind": "EMA21", "price": ema21, "weight": 5}, {"kind": "LOW12", "price": low12, "weight": 3}]
    levels += fib_levels(bars, config["swingLookback"])
    for row in inp.get("externalSupports") if isinstance(inp.get("externalSupports"), list) else []:
        p = num((row or {}).get("price"))
        w = number((row or {}).get("weight"))
        lv = {"kind": "EXTERNAL", "price": p, "weight": w if w > 0 else 3}
        if gt(p, 0):
            levels.append(lv)
    shelf = choose_shelf(price, levels, config)
    under50 = price <= ema50
    slope_lb = max(5, jor(number(config["ema50SlopeLookback"]), 10))
    e50_prev = at(ema50s, -(1 + int(slope_lb)))
    ema50_slope = (ema50 - e50_prev) / e50_prev if gt(e50_prev, 0) else 0
    collapsing50 = ema50_slope < jor(number(config["ema50CollapsePct"]), -0.015)
    wash_n = max(10, jor(number(config["washLookback"]), 20))
    high20 = jmax(b["high"] for b in bars[-int(wash_n):])
    wash_pct = (high20 - price) / high20 if high20 > 0 else 0
    washed = wash_pct >= jor(number(config["washMinPct"]), 0.08)
    prior_lows = [b["low"] for b in bars[-12:-1]]
    prior_low = jmin(prior_lows) if prior_lows else low12
    making_new_lows = last["low"] <= prior_low * 1.001
    recent = bars[-20:]
    vol_present = any(number(b["volume"]) > 0 for b in recent)
    adv_usd = None
    if vol_present:
        s = 0
        for b in recent:
            v = number(b["volume"])
            s = s + b["close"] * jor(v, 0)
        adv_usd = s / len(recent)
    tombstone = vol_present and price < 3 and adv_usd < 2_000_000
    healthy_rsi = config["rsiMin"] <= rsi14 <= config["rsiMax"]
    high_quality_rsi = config["highQualityRsiMin"] <= rsi14 <= config["highQualityRsiMax"]
    not_chasing = bool(shelf) and (price - shelf["price"]) / shelf["price"] <= config["maxShelfExtensionPct"]
    ctx = inp.get("marketContext") if isinstance(inp.get("marketContext"), dict) else {}
    event_blocked = ctx.get("eventBlocked") is True
    structural_breakdown = ctx.get("structuralBreakdown") is True
    liquidity_ok = False if tombstone else ctx.get("liquidityOk")
    ohlc_rich = len([b for b in bars if b["high"] > b["low"] * 1.0001]) >= 20

    if event_blocked:
        reasons.append("EVENT_BLOCKED")
    if structural_breakdown:
        reasons.append("STRUCTURAL_BREAKDOWN")
    if liquidity_ok is False:
        reasons.append("LIQUIDITY_UNACCEPTABLE")
    if tombstone:
        reasons.append("TOMBSTONE_LIQUIDITY")
    if not under50:
        reasons.append("ABOVE_50_DAY")
    if collapsing50:
        reasons.append("COLLAPSING_50")
    if rsi14 > config["rsiMax"]:
        reasons.append("RSI_OUTSIDE_REPAIR_BAND")
    hard_reject = event_blocked or structural_breakdown or liquidity_ok is False or not under50 or \
        rsi14 > config["rsiMax"] or collapsing50 or tombstone
    if not shelf:
        reasons.append("NO_VALID_SUPPORT_SHELF")
    if shelf and not not_chasing:
        reasons.append("EXTENDED_FROM_SHELF")
    if rsi14 < config["rsiMin"]:
        reasons.append("RSI_OUTSIDE_REPAIR_BAND")
    if not recently_lifting:
        reasons.append("MACD_NOT_RECENTLY_LIFTING")
    if not ohlc_rich:
        reasons.append("OHLC_INCOMPLETE")
    if not washed:
        reasons.append("NO_WASH")
    if making_new_lows:
        reasons.append("STILL_PRINTING_NEW_LOWS")
    location_ok = bool(shelf) and not_chasing
    eligible = (not hard_reject) and location_ok and healthy_rsi and recently_lifting and ohlc_rich and washed and \
        not making_new_lows
    score = score_of(shelf, recently_lifting, strong_repair, high_quality_rsi,
                     prev_rsi is not None and rsi14 > prev_rsi, under50, not_chasing, structural_breakdown,
                     liquidity_ok)
    s_coil = eligible and (shelf or {}).get("kind") == "EMA21" and high_quality_rsi and strong_repair
    setup = "S_COIL" if s_coil else ("A_WASHOUT" if eligible else None)
    priority = "S" if (s_coil and score >= 80) else ("A" if (eligible and setup == "A_WASHOUT" and score >= 68) else
                                                      ("B" if eligible else None))
    if hard_reject:
        status = "NOT_A_BUY"
    elif priority in ("S", "A"):
        status = "BUY_NOW"
    else:
        status = "WAIT"
    stop = shelf["price"] - config["stopAtrMultiple"] * atr14 if shelf else None
    resistance = prior_resistance(bars, price, config)
    seen = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return {
        "symbol": symbol, "status": status, "setup": setup, "priority": priority, "score": score,
        "reasonCodes": seen,
        "publicReason": public_reason(status, under50, shelf, recently_lifting, rsi14, collapsing50, washed,
                                      making_new_lows),
        "metrics": {
            "price": price, "ema21": ema21, "ema50": ema50, "rsi14": rsi14, "atr14": atr14,
            "normalizedMacdHistogram": norm[3], "normalizedMacdLift": net_lift, "macdPositiveSteps": positive_steps,
            "low12": low12, "under50": under50, "recentlyLifting": recently_lifting, "strongRepair": strong_repair,
            "ohlcRich": ohlc_rich, "ema50Slope": ema50_slope, "washPct": wash_pct, "washed": washed,
            "makingNewLows": making_new_lows, "collapsing50": collapsing50,
            "shelf": ({"kind": shelf["kind"], "price": shelf["price"], "distancePct": shelf["distancePct"],
                       "confluenceKinds": shelf["confluenceKinds"]} if shelf else None),
        },
        "plan": {"entryPrice": price if eligible else None, "stopPrice": stop,
                 "stopDistancePct": (price - stop) / price if (stop is not None and price > 0) else None,
                 "priorResistance": resistance},
        "version": LOCATION_FIRST_VERSION, "algorithmId": LOCATION_FIRST_ID,
    }


def desk_action_of(result, kind="stock", etf_only=False):
    is_etf = str(kind).lower() == "etf"
    if not result:
        return {"action": None, "tier": None}
    if result["status"] == "UNAVAILABLE":
        return {"action": None, "tier": None, "reason": result["publicReason"]}
    if result["status"] == "NOT_A_BUY":
        return {"action": "PRESSURE", "tier": None, "reason": result["publicReason"], "floor": None}
    if result["status"] == "BUY_NOW" and is_etf and not etf_only:
        return {"action": "WATCH", "tier": "A", "reason": "ETF is context. Stock book first.", "floor": "etf"}
    if result["status"] == "BUY_NOW":
        return {"action": "SETUP", "tier": "S" if result["priority"] == "S" else "A", "reason": result["publicReason"],
                "floor": None}
    return {"action": "WATCH", "tier": "B" if result["priority"] == "B" else "A", "reason": result["publicReason"],
            "floor": None}


# -- desk-core.mjs caps ------------------------------------------------------------------------------------------
def candidate_cap(mandate):
    n = number((mandate or {}).get("maxPositions"))
    if n == 2:
        return DESK_FILL_DEFAULT
    if math.isfinite(n) and n > 0:
        return int(max(1, min(12, js_round(n))))
    return DESK_FILL_DEFAULT


def fill_cap(mandate):
    return candidate_cap(mandate)


def radar_cap(mandate):
    fill = fill_cap(mandate)
    n = number((mandate or {}).get("radarCap"))
    if math.isfinite(n) and n > 0:
        return int(max(fill, min(48, js_round(n))))
    return max(RADAR_DEFAULT, fill)


def is_buy_side_candidate(row):
    if not row:
        return False
    return str(_first(row.get("tier"), "")) in DESK_BUY_TIERS and str(_first(row.get("action"), "")) in DESK_BUY_ACTIONS


# -- location-first-desk.mjs ---------------------------------------------------------------------------------------
def is_etf_ticker(ticker, kind, etf_tickers):
    return str(kind or "").lower() == "etf" or str(ticker or "").upper() in etf_tickers


def bars_from_daily_closes(times=None, closes=None):
    times, closes = times or [], closes or []
    out = []
    for i in range(min(len(times), len(closes))):
        t, c = number(times[i]), number(closes[i])
        if not math.isfinite(t) or not c > 0:
            continue
        out.append({"time": t, "open": c, "high": c, "low": c, "close": c, "volume": 0})
    return out


def result_to_desk_row(result, quote, mandate, etf_tickers):
    if not result or not result.get("symbol"):
        return None
    ticker = str(result["symbol"]).upper()
    quote = quote or {}
    etf = is_etf_ticker(ticker, quote.get("kind"), etf_tickers)
    mapped = desk_action_of(result, "etf" if etf else "stock",
                            (mandate or {}).get("assetClass") == "etfs" or (mandate or {}).get("allowStocks") is False)
    if not mapped["action"]:
        return None
    bar_at = number(_first(quote.get("locationFirstAt"), quote.get("completedBarAt"), 0))
    daily_bar_at = bar_at if (math.isfinite(bar_at) and bar_at != 0) else None
    m = result.get("metrics") or {}
    shelf = m.get("shelf")
    price = m.get("price") if gt(number(m.get("price")), 0) else (number(quote.get("price"))
                                                                   if gt(number(quote.get("price")), 0) else None)
    return {
        "ticker": ticker, "kind": "etf" if etf else "stock", "source": DESK_SCANNER, "origin": LOCATION_FIRST_SOURCE,
        "tier": mapped["tier"], "action": mapped["action"], "score": jor(number(result.get("score")), 0),
        "support": "holding" if shelf else "untested",
        "location": "extended" if mapped["action"] == "PRESSURE" else "favorable",
        "momentum": "improving" if m.get("recentlyLifting") else "neutral", "volume": "confirming",
        "antiChase": "blocked" if (shelf and (m["price"] - shelf["price"]) / shelf["price"] > 0.03) else "clear",
        "freshness": "fresh", "floor": mapped.get("floor"), "reason": mapped.get("reason"), "loc52": None,
        "dailyBarAt": daily_bar_at, "price": price, "ema21": _first(m.get("ema21")), "ema50": _first(m.get("ema50")),
        "rsiDaily": _first(m.get("rsi14")), "shelfKind": (shelf or {}).get("kind"),
        "shelfPrice": shelf["price"] if (shelf and gt(number(shelf.get("price")), 0)) else None,
        "locationFirst": result["status"], "paperBuy": False, "paperSell": False,
    }


def _cmp_key_setups(row):
    order = {"SETUP": 0, "WATCH": 1}
    return (order.get(row["action"], 9), 1 if row["kind"] == "etf" else 0, -(row.get("score") or 0))


def build_location_first_scan(results, quotes, mandate, etf_tickers, now_ms=None, completed_bar_at=None):
    """buildLocationFirstScan(): candidates (SETUP stocks first, capped live buys, then the rest, radar cap),
    pressure, hands (the first fill-cap SETUP stocks)."""
    setups, pressure = [], []
    for result in results:
        ticker = str((result or {}).get("symbol") or "").upper()
        q = quotes.get(ticker) or {"ticker": ticker, "kind": "etf" if is_etf_ticker(ticker, None, etf_tickers) else "stock"}
        row = result_to_desk_row(result, q, mandate, etf_tickers)
        if not row:
            continue
        (pressure if row["action"] == "PRESSURE" else setups).append(row)
    setups = sorted(setups, key=lambda r: _cmp_key_setups(r) + (_JsStr(r["ticker"]),))
    pressure = sorted(pressure, key=lambda r: (-(r.get("score") or 0), _JsStr(r["ticker"])))
    cap = radar_cap(mandate)
    hands = fill_cap(mandate)
    stock_setups = [r for r in setups if r["action"] == "SETUP" and r["kind"] != "etf"]
    live_cap = int(jor(number(DEFAULTS["maxLiveBuys"]), 7))
    live_buys = stock_setups[:live_cap]
    rest = [r for r in setups if not (r["action"] == "SETUP" and r["kind"] != "etf")]
    cands = [dict(r, rank=i + 1) for i, r in enumerate((live_buys + rest)[:cap])]
    return {
        "source": LOCATION_FIRST_SOURCE, "origin": LOCATION_FIRST_SOURCE,
        "status": "ready" if results else "unavailable", "completedBarAt": completed_bar_at,
        "candidates": cands, "pressure": pressure[:12], "rejected": max(0, len(setups) - len(cands)),
        "scanned": len(results), "fillCap": hands, "radarCap": cap,
        "hands": [{"ticker": r["ticker"], "action": r["action"], "tier": r["tier"], "score": r["score"], "rank": i + 1,
                   "origin": LOCATION_FIRST_SOURCE} for i, r in enumerate(stock_setups[:hands])],
        "missing": [] if results else ["Location-first needs 70 completed daily bars. No synthetic tape."],
        "version": LOCATION_FIRST_VERSION, "masterMerged": False,
    }


class _JsStr:
    """String.prototype.localeCompare for the plain ASCII tickers the scan sorts (ICU root collation orders ASCII
    letters case-insensitively first; tickers are upper-case alphanumerics, '.', '-', '^', '=')."""
    __slots__ = ("s",)

    def __init__(self, s):
        self.s = s

    def _k(self):
        return _locale_key(self.s)

    def __lt__(self, other):
        return self._k() < other._k()

    def __eq__(self, other):
        return self._k() == other._k()


def _locale_key(s):
    # ICU root collation: punctuation < digits < letters (case-insensitive primary, lower before upper tertiary)
    prim = []
    for ch in s:
        if ch.isalpha():
            prim.append((2, ch.lower()))
        elif ch.isdigit():
            prim.append((1, ch))
        else:
            prim.append((0, ch))
    return (prim, [0 if c.islower() else 1 for c in s])


# -- leaders-rest-core.mjs (the funnel's leaders shortlist) ----------------------------------------------------------
LEADERS_MIN_BARS = 70
LEADERS_MIN_PRICE = 10
LEADERS_MIN_ADV_USD = 20_000_000
RSI_HAND_MIN, RSI_HAND_MAX = 48, 68
OFF52_MAX = 0.25
PULLBACK_MIN, PULLBACK_MAX = 0.03, 0.12


def closes_of(bars):
    out = []
    for b in bars if isinstance(bars, list) else []:
        c = number((b or {}).get("close"))
        if c > 0:
            out.append(c)
    return out


def r_skip(closes, from_ago, to_ago):
    n = len(closes)
    ia, ib = n - 1 - from_ago, n - 1 - to_ago
    a = closes[ia] if 0 <= ia < n else None
    b = closes[ib] if 0 <= ib < n else None
    if not gt(a, 0) or not gt(b, 0):
        return None
    return b / a - 1


def momentum_skip_month(closes):
    skip = 21
    if not isinstance(closes, list) or len(closes) < skip + 40:
        return None
    span = min(252, len(closes) - 1)
    return r_skip(closes, span, skip)


def ema_slope(closes, period, lookback=10):
    s = ema_series(closes, period)
    a, b = at(s, -1), at(s, -(1 + lookback))
    if not gt(a, 0) or not gt(b, 0):
        return None
    return (a - b) / b


def high_of(bars, n):
    h = 0
    lst = bars if isinstance(bars, list) else []
    for b in (lst[-n:] if n else lst[:]):
        x = number((b or {}).get("high"))
        if x > h:
            h = x
    return h if h > 0 else None


def adv_usd(bars, n=20):
    s, count = 0, 0
    for b in (bars if isinstance(bars, list) else [])[-n:]:
        px, vol = number(b.get("close")), number(b.get("volume"))
        if px > 0 and vol >= 0:
            s += px * vol
            count += 1
    return s / count if count else 0


def range_ratio(bars):
    lst = bars if isinstance(bars, list) else []
    if len(lst) < 40:
        return None

    def span(w):
        h, lo = 0, INF
        for b in w:
            hi, low = number(b.get("high")), number(b.get("low"))
            if hi > h:
                h = hi
            if low > 0 and low < lo:
                lo = low
        return h - lo if (h > 0 and lo < INF) else None

    a, b = span(lst[-15:]), span(lst[-35:-15])
    if not gt(b, 0) or a is None:
        return None
    return a / b


def vol_dry(bars):
    lst = bars if isinstance(bars, list) else []

    def avg(n):
        w = lst[-n:]
        if not w:
            return None
        s = 0
        for b in w:
            v = number(b.get("volume"))
            s = s + jor(v, 0)
        return s / len(w)

    a, b = avg(10), avg(20)
    if a is None or b is None or not b > 0:
        return False
    return a <= b


def evaluate_leaders(inp=None):
    """leaders-rest-core.mjs evaluateLeaders(input) — used here only to rank the funnel's leaders shortlist."""
    inp = inp or {}
    symbol = str(inp.get("symbol") or "").upper()
    bars = inp.get("bars") if isinstance(inp.get("bars"), list) else []
    closes = closes_of(bars)
    session = num(inp.get("regularSessionPrice"))
    last = session if gt(session, 0) else _first(at(closes, -1))
    spy_mom = num(inp.get("spyMomentum"))
    event_blocked = inp.get("eventBlocked") is True
    regime_dead = inp.get("regimeDead") is True
    if len(closes) < LEADERS_MIN_BARS or not gt(last, 0):
        return {"symbol": symbol, "status": "UNAVAILABLE", "action": None, "score": 0,
                "reason": "Need 70 completed daily bars.", "metrics": {"price": last, "bars": len(closes)}}
    e21 = at(ema_series(closes, 21), -1)
    e50 = at(ema_series(closes, 50), -1)
    slope50 = ema_slope(closes, 50, 10)
    rsi = at(wilder_rsi(closes, 14), -1)
    mom = momentum_skip_month(closes)
    hi52 = high_of(bars, min(252, len(bars)))
    off52 = (hi52 - last) / hi52 if (gt(hi52, 0) and last > 0) else None
    hi20 = high_of(bars, 20)
    pullback = (hi20 - last) / hi20 if (gt(hi20, 0) and last > 0) else None
    contraction = range_ratio(bars)
    dry = vol_dry(bars)
    dollar = adv_usd(bars, 20)
    rs_spy = mom - spy_mom if (mom is not None and spy_mom is not None) else mom
    cheap = last < LEADERS_MIN_PRICE and dollar < LEADERS_MIN_ADV_USD
    falling50 = slope50 is not None and slope50 < 0
    above_rising = gt(e50, 0) and (last >= e50 or (gt(e21, 0) and last >= e21 and not falling50))
    leader_zone = off52 is not None and off52 <= OFF52_MAX
    beats_spy = rs_spy is None or rs_spy > 0
    rsi_hand = rsi is not None and RSI_HAND_MIN <= rsi <= RSI_HAND_MAX
    rest = (pullback is not None and PULLBACK_MIN <= pullback <= PULLBACK_MAX) or \
        (contraction is not None and contraction <= 0.6 and off52 is not None and 0.02 <= off52 <= 0.18)
    chase = (rsi is not None and rsi > RSI_HAND_MAX) or \
        (off52 is not None and off52 < 0.015 and (contraction is None or contraction > 0.85))
    metrics = {"price": last, "ema21": e21, "ema50": e50, "ema50Slope": slope50, "rsi14": rsi, "momentum": mom,
               "rsSpy": rs_spy, "off52": off52, "pullback": pullback, "contraction": contraction, "volDry": dry,
               "advUsd": dollar,
               "shelfKind": ("50-day" if (gt(e50, 0) and e50 * 0.985 <= last <= e50 * 1.025) else
                             "21-day" if gt(e21, 0) else "rest"),
               "shelfPrice": e50 if (gt(e50, 0) and last >= e50 * 0.97) else e21}
    if event_blocked:
        return {"symbol": symbol, "status": "SKIP", "action": None, "score": 0, "reason": "Event in window.",
                "metrics": metrics}
    if cheap:
        return {"symbol": symbol, "status": "SKIP", "action": None, "score": 0,
                "reason": "Below $10 without real dollar volume.", "metrics": metrics}
    if regime_dead:
        return {"symbol": symbol, "status": "DEAD", "action": None, "score": 0, "reason": "Regime off. No new risk.",
                "metrics": metrics}
    mom_n = max(0, min(1, (mom if mom is not None else 0) / 0.8))
    rs_n = max(0, min(1, (rs_spy if rs_spy is not None else 0) / 0.4))
    near_n = 0 if off52 is None else max(0, min(1, 1 - off52 / OFF52_MAX))
    rest_n = 1 if rest else 0
    rsi_n = 1 if rsi_hand else (0.45 if (rest and rsi is not None and rsi < RSI_HAND_MIN) else 0)
    score = max(1, min(100, js_round(32 * mom_n + 18 * rs_n + 15 * near_n + 25 * rest_n + 8 * rsi_n +
                                     (2 if dry else 0))))
    if not leader_zone or falling50 or not beats_spy or not above_rising:
        reason = ("50-day still falling. Not a leader rest." if falling50 else
                  "Not beating SPY on skip-month momentum." if not beats_spy else
                  "Too far from the 52-week high. Laggard." if not leader_zone else "Not on a rising 50-day.")
        return {"symbol": symbol, "status": "WAIT", "action": "WATCH", "score": score, "reason": reason,
                "metrics": metrics}
    if chase and not rest:
        return {"symbol": symbol, "status": "CHASE", "action": "PRESSURE", "score": score,
                "reason": "Already left the rest. Do not chase last.", "metrics": metrics}
    if rest and rsi_hand:
        return {"symbol": symbol, "status": "REST", "action": "SETUP", "score": score,
                "reason": "Leader that rested. Buy the rest, not last.", "metrics": metrics}
    if rest and rsi is not None and rsi < RSI_HAND_MIN:
        return {"symbol": symbol, "status": "WAIT", "action": "WATCH", "score": score,
                "reason": "Rest is forming. RSI still soft.", "metrics": metrics}
    return {"symbol": symbol, "status": "WAIT", "action": "WATCH", "score": score,
            "reason": "Leader. Waiting for a 3–12% rest or a tight range.", "metrics": metrics}


# -- runLocationFirstUniverse(): the two-pass funnel, on data the caller already holds --------------------------------
def shortlist(prelim, leaders):
    """the deep-OHLC shortlist: the 48 best under-50 location-first reads (lifting, then on a shelf, then score) plus
    the 48 best leaders reads (SETUP / WATCH / WAIT, by score) plus SPY and QQQ."""
    def lf_rank(row):
        m = (row["result"] or {}).get("metrics") or {}
        return 0 if m.get("recentlyLifting") else 1 if m.get("shelf") else 2

    lf = [r for r in prelim if ((r["result"] or {}).get("metrics") or {}).get("under50") is True]
    lf = sorted(lf, key=lambda r: (lf_rank(r), -((r["result"] or {}).get("score") or 0)))[:DEEP_OHLC_CAP]
    ld = [r for r in leaders if (r["leaders"] or {}).get("action") in ("SETUP", "WATCH")
          or (r["leaders"] or {}).get("status") == "WAIT"]
    ld = sorted(ld, key=lambda r: -((r["leaders"] or {}).get("score") or 0))[:DEEP_OHLC_CAP]
    want = {r["ticker"] for r in lf} | {r["ticker"] for r in ld} | {"SPY", "QQQ"}
    return want


def hydrate_quote(existing, result, series=None):
    """hydrateQuotesFromLocationFirst() for one ticker: the fields the paper pass reads (price, atr, ema21/50,
    locationFirstAt) — price falls back to the close series' price, atr to 2% of price."""
    existing = dict(existing or {})
    m = (result or {}).get("metrics") or {}
    price = m.get("price") if gt(number(m.get("price")), 0) else \
        (number((series or {}).get("price")) if gt(number((series or {}).get("price")), 0) else number(existing.get("price")))
    shelf = number(((m.get("shelf") or {}).get("price")))
    atr = number(m.get("atr14"))
    out = dict(existing)
    out["price"] = price if price > 0 else existing.get("price")
    out["atr"] = atr if atr > 0 else _first(existing.get("atr"), (price * 0.02 if price > 0 else 1))
    out["ema21"] = _first(m.get("ema21"), existing.get("ema21"))
    out["ema50"] = _first(m.get("ema50"), existing.get("ema50"))
    out["support"] = shelf if shelf > 0 else _first(existing.get("support"), price * 0.98 if price > 0 else 0)
    return out
