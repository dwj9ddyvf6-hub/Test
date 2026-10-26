"""The legacy desk-native completed-bar support scanner — line-by-line port of autopilot-desk @48e8f90f:

  src/lib/scanner/desk-core.mjs    blob 1b5f9041  scoreDeskQuote / buildDeskScan / deskScanToBundle (lines 42-240)
  src/lib/scanner/features.mjs     blob 843833d1  loc52Of / sessionReturn / sessionFromQuote / rsiOf / macdHistogram
  src/lib/market/quote-core.mjs    blob 7b2bac12  quoteFromCompletedBars (+ atr / rsi / macd / swing / vwap helpers)
  src/lib/desk/screen-core.mjs     blob 4a94dc93  the two-pass screen: screenScore / pickDeep / quoteFromSparkMeta

Inputs are the sources' plain objects. JSON null and a missing key differ in JavaScript (Number(null) = 0,
Number(undefined) = NaN); the port reads fields through _g(), which returns UNDEF for a missing key and None for
null, and jnum() applies Number() to either exactly. Parity: tools/parity/sable_desk_scanner.py."""
import math
import re

from ..jsport import INF, js_round, lsum, to_fixed
from .location_first import fill_cap, is_buy_side_candidate, radar_cap

DESK_SCANNER = "desk"
DEEP_CAP = 36
DEEP_VANES = ("SPY", "QQQ", "IWM")
MEGA = {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "LLY", "UNH", "JPM", "V", "MA"}


class _Undef:
    def __repr__(self):
        return "undefined"


UNDEF = _Undef()


def _g(obj, key):
    if not isinstance(obj, dict) or key not in obj:
        return UNDEF
    return obj[key]


def jnumber(v):
    """Number(v) for JSON-shaped values: undefined -> NaN, null -> 0."""
    if v is UNDEF:
        return float("nan")
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    return float("nan")


def jnum(v, fallback=None):
    n = jnumber(v)
    return n if math.isfinite(n) else fallback


def nullish(v):
    return v is UNDEF or v is None


def jstr(v):
    if v is UNDEF:
        return "undefined"
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    from ..jsport import js_str
    return js_str(v) if isinstance(v, (int, float)) else str(v)


# -- features.mjs ------------------------------------------------------------------------------------------------
def loc52_of(price, low, high):
    p, lo, hi = jnumber(price), jnumber(low), jnumber(high)
    if not p > 0 or not hi > lo or not lo > 0:
        return None
    return ((p - lo) / (hi - lo)) * 100


def session_return(price, prev_close):
    p, prev = jnumber(price), jnumber(prev_close)
    if not p > 0 or not prev > 0:
        return None
    return (p - prev) / prev


def session_from_quote(quote):
    price = jnumber(_g(quote, "price"))
    day_prev = jnumber(_g(quote, "dayPrevClose"))
    spark = _g(quote, "screen") is True or _g(quote, "source") == "live-read-quote"
    if math.isfinite(day_prev) and day_prev > 0:
        prev = day_prev
    elif spark:
        prev = jnumber(_g(quote, "prevClose"))
    else:
        prev = None                                       # JS null: Number(null) = 0 in sessionReturn
    day_ret = session_return(price, prev)
    ok_prev = prev is not None and math.isfinite(prev) and prev > 0
    return {"dayPrevClose": prev if ok_prev else None, "dayRet": day_ret,
            "sessionRed": day_ret is not None and day_ret <= -0.015,
            "sessionGreen": day_ret is not None and day_ret >= 0.015}


def ema_series_f(values, period):
    """features.mjs emaSeries: seeded with the first value."""
    if not isinstance(values, list) or not values or not period > 0:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for i in range(1, len(values)):
        out.append(values[i] * k + out[i - 1] * (1 - k))
    return out


def rsi_of(values, period=14):
    if not isinstance(values, list) or len(values) <= period:
        return None
    gain = loss = 0
    for i in range(1, period + 1):
        diff = values[i] - values[i - 1]
        if diff >= 0:
            gain += diff
        else:
            loss -= diff
    gain /= period
    loss /= period
    for i in range(period + 1, len(values)):
        diff = values[i] - values[i - 1]
        gain = (gain * (period - 1) + max(diff, 0)) / period
        loss = (loss * (period - 1) + max(-diff, 0)) / period
    if loss == 0:
        return 100
    return 100 - 100 / (1 + gain / loss)


def macd_series(values):
    if not isinstance(values, list) or len(values) < 28:
        return []
    e12, e26 = ema_series_f(values, 12), ema_series_f(values, 26)
    macd = [v - e26[i] for i, v in enumerate(e12)]
    sig = ema_series_f(macd[25:], 9)
    return [macd[i + 25] - sig[i] for i in range(len(sig))]


def macd_histogram(values):
    s = macd_series(values)
    return s[-1] if s else None


# -- quote-core.mjs ----------------------------------------------------------------------------------------------------
def atr_from_bars(bars, period=14):
    if not isinstance(bars, list) or len(bars) < 2:
        return None
    sl = bars[-max(period + 1, 2):]
    ranges = []
    for i in range(1, len(sl)):
        high, low, prev = jnum(_g(sl[i], "high")), jnum(_g(sl[i], "low")), jnum(_g(sl[i - 1], "close"))
        if high is None or low is None or prev is None:
            continue
        ranges.append(max(high - low, abs(high - prev), abs(low - prev)))
    if not ranges:
        return None
    return lsum(ranges) / len(ranges)


def rsi_from_bars(bars, period=14):
    if not isinstance(bars, list) or len(bars) < period + 1:
        return None
    closes = [c for c in (jnum(_g(b, "close")) for b in bars) if c is not None]
    if len(closes) < period + 1:
        return None
    gain = loss = 0
    for i in range(len(closes) - period, len(closes)):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gain += d
        else:
            loss -= d
    if loss == 0:
        return 100
    return 100 - 100 / (1 + gain / loss)


def macd_hist_from_bars(bars):
    closes = [c for c in (jnum(_g(b, "close")) for b in (bars if isinstance(bars, list) else [])) if c is not None]
    if len(closes) < 26:
        return None

    def ema(period):
        k = 2 / (period + 1)
        v = closes[0]
        for i in range(1, len(closes)):
            v = closes[i] * k + v * (1 - k)
        return v

    return ema(12) - ema(26)


def swing_low(bars, lookback=36):
    low = None
    for b in (bars if isinstance(bars, list) else [])[-lookback:]:
        v = jnum(_g(b, "low"))
        if v is None:
            continue
        low = v if low is None else min(low, v)
    return low


def swing_high(bars, lookback=36):
    high = None
    for b in (bars if isinstance(bars, list) else [])[-lookback:]:
        v = jnum(_g(b, "high"))
        if v is None:
            continue
        high = v if high is None else max(high, v)
    return high


def vwap_from_bars(bars, lookback=48):
    sl = (bars if isinstance(bars, list) else [])[-lookback:]
    notional = volume = 0
    for b in sl:
        close = jnum(_g(b, "close"))
        vol = jnum(_g(b, "volume"))
        vol = 0 if vol is None else vol
        if close is None or vol <= 0:
            continue
        notional += close * vol
        volume += vol
    if volume > 0:
        return notional / volume
    return jnum(_g(sl[-1], "close")) if sl else None


def quote_from_completed_bars(meta, bars, source="live-read"):
    if not meta or not isinstance(bars, list) or not bars:
        return None
    last = bars[-1]
    prev = bars[-2] if len(bars) >= 2 else last
    close = jnum(_g(last, "close"))
    prev_close = jnum(_g(prev, "close"))
    if close is None or close <= 0:
        return None
    window = bars[-48:]
    high, low = swing_high(window), swing_low(window)
    atr = atr_from_bars(bars)
    support, resistance = swing_low(bars, 64), swing_high(bars, 64)
    volume = jnum(_g(last, "volume"))
    s = 0
    for b in window:
        v = jnum(_g(b, "volume"))
        s += v if v is not None else 0
    avg_volume = s / max(1, len(window))
    rsi = rsi_from_bars(bars)
    macd = macd_hist_from_bars(bars)
    completed_at = jnumber(_g(last, "time"))
    if atr is None or support is None or resistance is None or volume is None:
        return None
    op = jnum(_g(window[0], "open")) if window else None
    vw = vwap_from_bars(window)
    return {"ticker": _g(meta, "ticker"), "kind": _g(meta, "kind"), "price": close,
            "prevClose": prev_close if prev_close is not None else close, "open": op if op is not None else close,
            "high": high if high is not None else close, "low": low if low is not None else close, "volume": volume,
            "avgVolume": avg_volume, "support": support, "resistance": resistance,
            "vwap": vw if vw is not None else close, "rsi": rsi, "macdHist": macd, "atr": atr,
            "extensionAtr": (close - support) / max(atr, 0.01),
            "completedBarAt": completed_at * 1000 if math.isfinite(completed_at) else None, "source": source}


# -- screen-core.mjs ------------------------------------------------------------------------------------------------------
def screen_score(row):
    price = jnumber(_g(row, "price"))
    if not math.isfinite(price) or price <= 0:
        return 0
    low52, high52 = jnumber(_g(row, "low52")), jnumber(_g(row, "high52"))
    lo = _g(row, "low")
    day_low = jnumber(_g(row, "dayLow") if nullish(lo) else lo)
    prev = jnumber(_g(row, "prevClose"))
    near52 = (price - low52) / price if math.isfinite(low52) else 1
    near_day = (price - day_low) / price if math.isfinite(day_low) else 1
    loc52 = (price - low52) / (high52 - low52) if (math.isfinite(high52) and math.isfinite(low52) and high52 > low52) \
        else 0.5
    score = 0
    if near52 <= 0.08:
        score += 40
    elif near52 <= 0.15:
        score += 24
    elif loc52 <= 0.25:
        score += 16
    if near_day <= 0.01:
        score += 20
    elif near_day <= 0.02:
        score += 10
    if math.isfinite(prev) and price < prev:
        score += 8
    if loc52 >= 0.88:
        score -= 30
    return score


def pick_deep(rows, positions=(), pins=(), vanes=DEEP_VANES, cap=DEEP_CAP):
    must = [str(t or "").upper() for t in list(positions) + list(pins) + list(vanes)]
    must = [t for t in must if t]
    ranked = sorted(rows or [], key=lambda r: -screen_score(r))
    out, seen = [], set()
    for t in must:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    for r in ranked:
        if len(out) >= cap:
            break
        t = str(_g(r, "ticker") if not nullish(_g(r, "ticker")) else "").upper()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def spark_tape_from_closes(closes=None, times=None):
    series = [v for v in (jnumber(x) for x in (closes if isinstance(closes, list) else [])) if math.isfinite(v) and v > 0]
    stamps = [v for v in (jnumber(x) for x in (times if isinstance(times, list) else [])) if math.isfinite(v) and v > 0]
    if not series:
        return None
    last_time = stamps[-1] if stamps else None
    return {"price": series[-1], "sparkBars": len(series),
            "lastSparkBarAt": last_time * 1000 if (last_time is not None and last_time > 0) else None,
            "rsi": rsi_of(series, 14), "macdHist": macd_histogram(series)}


def quote_from_spark_meta(meta, ticker, seed=None):
    sym = str(ticker or (_g(meta, "symbol") if not nullish(_g(meta, "symbol")) else "") or "").upper()
    tape = spark_tape_from_closes(_g(meta, "sparkCloses") if not nullish(_g(meta, "sparkCloses")) else None,
                                  _g(meta, "sparkTimes") if not nullish(_g(meta, "sparkTimes")) else None)
    price = jnumber(tape["price"] if tape and tape.get("price") is not None else _g(meta, "regularMarketPrice"))
    if not sym or not math.isfinite(price) or price <= 0:
        return None

    pv = _g(meta, "previousClose")
    pv = pv if (not nullish(pv) and pv != 0 and pv != "") else _g(meta, "chartPreviousClose")
    prev = jnumber(pv)
    prev = prev if (math.isfinite(prev) and prev != 0) else price
    dh = jnumber(_g(meta, "regularMarketDayHigh"))
    day_high = dh if (math.isfinite(dh) and dh != 0) else price
    dl = jnumber(_g(meta, "regularMarketDayLow"))
    day_low = dl if (math.isfinite(dl) and dl != 0) else price
    low52, high52 = jnumber(_g(meta, "fiftyTwoWeekLow")), jnumber(_g(meta, "fiftyTwoWeekHigh"))
    atr = max(day_high - day_low, price * 0.012, 0.01)
    support = day_low if (math.isfinite(day_low) and day_low > 0) else (low52 if math.isfinite(low52) else price)
    resistance = high52 if math.isfinite(high52) else day_high
    it = _g(meta, "instrumentType")
    if str("" if nullish(it) or it == "" else it).upper() == "ETF":
        kind = "etf"
    else:
        sk = _g(seed, "kind") if seed is not None else UNDEF
        kind = "stock" if nullish(sk) else sk
    vol = jnumber(_g(meta, "regularMarketVolume"))
    av = _g(seed, "avgVolume") if seed is not None else UNDEF
    rsi = jnumber(tape["rsi"]) if tape else float("nan")          # Number(null) = 0: a too-short spark reads 0
    mh = jnumber(tape["macdHist"]) if tape else float("nan")
    return {"ticker": sym, "kind": kind, "price": price, "prevClose": prev, "dayPrevClose": prev, "open": prev,
            "high": day_high, "low": day_low, "volume": vol if (math.isfinite(vol) and vol != 0) else 0,
            "avgVolume": av if (not nullish(av) and av != 0) else 0, "support": support, "resistance": resistance,
            "vwap": price, "rsi": rsi if math.isfinite(rsi) else None, "macdHist": mh if math.isfinite(mh) else None,
            "atr": atr, "extensionAtr": (price - support) / max(atr, 0.01), "source": "live-read-quote",
            "screen": True, "low52": low52 if math.isfinite(low52) else None,
            "high52": high52 if math.isfinite(high52) else None,
            "sparkBars": tape["sparkBars"] if tape else 0,
            "lastSparkBarAt": tape["lastSparkBarAt"] if tape else None}


# -- desk-core.mjs ---------------------------------------------------------------------------------------------------------
_TICKER = re.compile(r"^[A-Z][A-Z0-9.^=-]{0,23}$")


def _vol_word(r):
    return "confirming" if r > 1.15 else "quiet" if r < 0.7 else "confirming"


def score_desk_quote(quote, tensor=None, mandate=None):
    t = _g(quote, "ticker")
    ticker = ("" if nullish(t) else jstr(t)).strip().upper()
    if not _TICKER.match(ticker):
        return None
    price = jnum(_g(quote, "price"))
    if price is None or price <= 0:
        return None
    support = jnum(_g(quote, "support"))
    vwap = jnum(_g(quote, "vwap"))
    atr = max(jnum(_g(quote, "atr"), 0), price * 0.008, 0.01)
    e = jnum(_g(quote, "extensionAtr"))
    ext = e if e is not None else ((price - support) / atr if support is not None else 1)
    vs_vwap = (price - vwap) / atr if vwap is not None else 0
    rsi = 50 if nullish(_g(quote, "rsi")) else jnum(_g(quote, "rsi"), 50)
    macd = 0 if nullish(_g(quote, "macdHist")) else jnum(_g(quote, "macdHist"), 0)
    vol = jnum(_g(quote, "volume"))
    vol = vol if (vol is not None and vol != 0) else 0
    avg = jnum(_g(quote, "avgVolume"))
    avg = avg if (avg is not None and avg != 0) else 0
    vol_ratio = vol / avg if avg > 0 else 1
    lost = support is not None and price < support * 0.995
    near_local = support is not None and price >= support * 0.995 and ext <= 1.6 and rsi <= 72
    loc52 = loc52_of(price, _g(quote, "low52"), _g(quote, "high52"))
    near52 = loc52 is not None and loc52 <= 30
    at_demand = (near_local or near52) and not lost
    upper_range = loc52 is not None and loc52 >= 75 and not near52
    roof = loc52 is not None and loc52 >= 88
    chase_upper = ext > 1.85 and (loc52 is None or loc52 >= 55)
    stretched_local = ext > 1.6 and rsi > 68 and (loc52 is None or loc52 >= 55)
    compressed = ext < 0.55
    deteriorating = rsi < 38 or macd < -0.15
    improving = macd > 0.08 and 48 < rsi < 72
    paper_sell = _g(tensor, "paperSell") is True if tensor is not None else False
    ts = _g(tensor, "state") if tensor is not None else UNDEF
    tensor_state = None if nullish(ts) else ts
    screen_only = _g(quote, "source") == "live-read-quote" or _g(quote, "screen") is True
    session = session_from_quote(quote)
    earnings_soon = _g(quote, "earningsImminent") is True
    k = _g(quote, "kind")
    kind = "etf" if ("" if nullish(k) else jstr(k)).lower() == "etf" else "stock"
    etf_only = (_g(mandate, "assetClass") == "etfs" or _g(mandate, "allowStocks") is False) if mandate else False
    structurally_lost = lost and not near52
    if paper_sell or roof or structurally_lost or chase_upper or stretched_local:
        if paper_sell:
            reason = "Tensor printed a completed-bar SELL. Scanner will not invert that into a setup."
        elif roof:
            reason = f"Pressed at {to_fixed(loc52, 0)}% of the 52-week range. Not a support residual."
        elif chase_upper or (ext > 1.85 and not near52):
            reason = f"Extended {to_fixed(ext, 2)} ATR from swing support. Chase blocked."
        elif structurally_lost:
            reason = "Price is below support. Not a setup."
        elif stretched_local:
            reason = f"Stretched {to_fixed(ext, 2)} ATR with RSI {to_fixed(rsi, 0)}. Chase blocked."
        else:
            reason = "Momentum is deteriorating away from support."
        return {"ticker": ticker, "kind": kind, "loc52": loc52, "source": DESK_SCANNER, "tier": None,
                "action": "PRESSURE", "score": js_round(18 + (12 if paper_sell else 0) + min(20, ext * 4)),
                "support": "lost" if structurally_lost else "untested",
                "location": "extended" if (chase_upper or stretched_local or roof) else "favorable",
                "momentum": "deteriorating" if (deteriorating or paper_sell) else "neutral",
                "volume": _vol_word(vol_ratio), "antiChase": "blocked", "freshness": "fresh", "reason": reason,
                "tensorState": tensor_state, "paperBuy": False, "paperSell": bool(paper_sell)}
    if deteriorating and not at_demand and ext > 1.2:
        return {"ticker": ticker, "kind": kind, "loc52": loc52, "source": DESK_SCANNER, "tier": None,
                "action": "PRESSURE", "score": js_round(18 + min(20, ext * 4)), "support": "untested",
                "location": "favorable", "momentum": "deteriorating", "volume": _vol_word(vol_ratio),
                "antiChase": "blocked", "freshness": "fresh", "reason": "Momentum is deteriorating away from support.",
                "tensorState": tensor_state, "paperBuy": False, "paperSell": False}
    tier = action = None
    score = 0
    reason = ""
    floor = None
    if at_demand:
        if screen_only:
            tier, action = "A", "WATCH"
            score = 64 + (4 if improving else 0) + (8 if near52 else 0)
            reason = ("Spark 5m closes on the catalog. Waiting on completed OHLC 5m for SETUP."
                      if jnumber(_g(quote, "sparkBars")) > 0 else
                      "Near 52-week or session location on the quote screen. Waiting on a completed 5m bar.")
        elif earnings_soon:
            tier, action = "A", "WATCH"
            score = 58 + (6 if improving else 0) + (2 if compressed else 0)
            floor = "earnings"
            reason = "Earnings inside 48h. Watch the level; do not fill the event."
        elif kind == "etf" and not etf_only:
            tier, action = "A", "WATCH"
            score = 60 + (4 if improving else 0)
            floor = "etf"
            reason = "ETF is context. Stock book first."
        elif deteriorating:
            tier, action = "A", "WATCH"
            score = 62 + (8 if near52 else 0) + (2 if compressed else 0)
            reason = (f"At {to_fixed(loc52, 0)}% of the 52-week range with the tape still dumping. Watch the hold."
                      if near52 else "Holding support but the 5m tape is still dumping.")
        elif upper_range and not near_local:
            tier, action = "A", "WATCH"
            score = 56
            reason = f"Upper-range residual at {to_fixed(loc52, 0)}% of the 52-week. Not a stock support sit."
        elif session["sessionGreen"] and not near_local and ext > 1.6:
            tier, action = "A", "WATCH"
            score = 61 + (6 if near52 else 0)
            reason = "Session already lifted it off the low. Let it sit."
        else:
            tier, action = "S", "SETUP"
            score = 78 + (8 if improving else 0) + (4 if compressed else 0) + (3 if vol_ratio > 1.15 else 0) + \
                (8 if near52 else 0)
            if near52:
                reason = f"Stock at {to_fixed(loc52, 0)}% of the 52-week range. Swing support."
            elif session["sessionRed"]:
                dr = session["dayRet"] if session["dayRet"] is not None else 0
                reason = f"Holding completed-bar support after a {to_fixed(dr * 100, 1)}% session."
            else:
                reason = "Holding completed-bar support with room left in the range."
    elif not lost and ext < 1.35 and 42 <= rsi <= 68 and not deteriorating and vs_vwap < 1.4:
        tier, action = "A", "WATCH"
        score = 62 + (7 if improving else 0) + (3 if vol_ratio > 1.1 else 0)
        reason = "Favorable location on the last completed bar. Not a Tensor BUY."
        if kind == "etf" and not etf_only:
            floor = "etf"
            reason = "ETF is context. Stock book first."
    elif not lost and ((40 <= rsi <= 72 and ext < 1.7) or near52):
        tier, action = "B", "WATCH"
        score = 48 + (5 if improving else 0) + (8 if near52 else 0)
        reason = "Near 52-week lows. Not confirmed." if near52 else "Inside the range. Worth watching, not a confirmation."
    else:
        return None
    if tensor is not None and _g(tensor, "paperBuy") not in (UNDEF, None, False, 0, ""):
        reason = f"{reason} Tensor already printed a completed-bar BUY on this name."
        score += 6
    elif tensor_state == "VECTOR_BUY":
        reason = f"{reason} Tensor is VECTOR_BUY without an immediate buy marker."
    elif tensor_state == "REVERSAL_WINDOW":
        score += 3
        reason = f"{reason} Tensor is in a reversal window — still not a fill."
    if kind == "etf" and not etf_only:
        score = min(score, 66)
    return {"ticker": ticker, "kind": kind, "loc52": loc52, "source": DESK_SCANNER, "tier": tier, "action": action,
            "score": js_round(min(99, score)), "support": "holding" if at_demand else "untested",
            "location": "compressed" if compressed else "favorable",
            "momentum": "improving" if improving else "deteriorating" if deteriorating else "neutral",
            "volume": _vol_word(vol_ratio), "antiChase": "clear", "freshness": "fresh", "floor": floor,
            "reason": reason, "tensorState": tensor_state, "paperBuy": False, "paperSell": False}


def build_desk_scan(quotes, reads=(), mandate=None, completed_bar_at=None):
    by_ticker = {jstr(_g(r, "ticker") if not nullish(_g(r, "ticker")) else "").upper(): r for r in reads or []}
    cap, hands = radar_cap(mandate), fill_cap(mandate)
    setups, pressure, usable = [], [], 0
    for q in (quotes or {}).values():
        cba = _g(q, "completedBarAt")
        src = _g(q, "source")
        if (nullish(cba) or cba in (0, False, "")) and src not in ("live-read", "demo", "live-read-quote"):
            continue
        usable += 1
        t = _g(q, "ticker")
        row = score_desk_quote(q, by_ticker.get(("" if nullish(t) else jstr(t)).upper()), mandate)
        if not row:
            continue
        (pressure if row["action"] == "PRESSURE" else setups).append(row)
    radar = _g(mandate, "discoveryPreference") == "under_the_radar" if mandate else False
    order = {"SETUP": 0, "WATCH": 1}

    def key(r):
        s = (r.get("score") or 0) - (18 if (radar and r["ticker"] in MEGA) else 0)
        return (order.get(r["action"], 9), 1 if r["kind"] == "etf" else 0, -s, r["ticker"])

    from .location_first import _JsStr
    setups = sorted(setups, key=lambda r: key(r)[:3] + (_JsStr(r["ticker"]),))
    pressure = sorted(pressure, key=lambda r: (-(r.get("score") or 0), _JsStr(r["ticker"])))
    cands = [dict(r, rank=i + 1) for i, r in enumerate(setups[:cap])]
    return {"source": DESK_SCANNER, "status": "unavailable" if usable == 0 else "ready",
            "completedBarAt": completed_bar_at, "candidates": cands, "pressure": pressure[:12],
            "rejected": max(0, len(setups) - len(cands)), "scanned": usable, "fillCap": hands, "radarCap": cap,
            "hands": [{"ticker": r["ticker"], "action": r["action"], "tier": r["tier"], "score": r["score"], "rank": i + 1}
                      for i, r in enumerate([r for r in setups if is_buy_side_candidate(r)][:hands])],
            "missing": ["No completed-bar quotes. Desk scanner will not invent names."] if usable == 0 else []}


def desk_scan_to_bundle(scan):
    ready = (scan or {}).get("status") == "ready"
    return {"status": "ready" if ready else ((scan or {}).get("status") or "unavailable"),
            "candidates": (scan or {}).get("candidates") or [], "pressure": (scan or {}).get("pressure") or [],
            "missing": (scan or {}).get("missing") or [], "scanned": int((scan or {}).get("scanned") or 0),
            "fillCap": (scan or {}).get("fillCap"), "radarCap": (scan or {}).get("radarCap"),
            "hands": (scan or {}).get("hands") or [], "origin": DESK_SCANNER}
