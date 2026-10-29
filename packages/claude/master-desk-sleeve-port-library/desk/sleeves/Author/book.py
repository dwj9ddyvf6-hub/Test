"""The Author scanner book — line-by-line ports of Author-desk @652db7af src/lib/workdesk/{doctrine,select,curl,
location-law,bottom-screen,sector-map,sector-tape,fund-overlay,buy-desk,after-hours,roster}.ts, fund-io.ts's SEC fact
reads, copy.ts buyCall / callRank, and the book assembly of scripts/desk-autopilot.mjs (orderBook,
filterBookForCurl, keepNearBuy). Bars are dicts {t (epoch ms), o, h, l, c, v}; None stands for null / undefined;
`now` is epoch ms (the source's Date.now()). Parity: tools/parity/Author_book.py."""
import math
import re
from datetime import date, datetime, timedelta, timezone
from functools import cmp_to_key

from ..jsport import INF, js_round, js_str, lsum, to_fixed, truthy
from ..v8math import log as vlog
from . import levels as L
from . import paper as P
from . import tensor as T


def _jmin(xs):
    xs = list(xs)
    return min(xs) if xs else INF


def _jmax(xs):
    xs = list(xs)
    return max(xs) if xs else -INF


def _fin(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _round_px(n):
    if n >= 100:
        return js_round(n * 100) / 100
    if n >= 1:
        return js_round(n * 100) / 100
    return js_round(n * 1000) / 1000


def _iso(ms):
    d = datetime.fromtimestamp(math.floor(ms) / 1000.0, tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (int(math.floor(ms)) % 1000)


def _parse_iso_ms(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return int(round(d.timestamp() * 1000))


def _unique(xs):
    out = []
    for x in xs:
        if x and x not in out:
            out.append(x)
    return out


# == doctrine.ts =======================================================================================================
DOCTRINE = {"name": "QuantMaster5000", "minRR": 1.5, "bookCeiling": 20, "typicalYield": 18, "lateR": 0.45,
            "zoneAtr": 1, "triggerAtr": 0.75, "gapAtr": 1, "daySigma": 3, "maxWidthAtr": 1.25, "below200": 0.12,
            "offLowPct": 0.12, "offLowBars": 15}

EVENT_FROM_LANE = [
    (re.compile(r"SWEEP|FAILED_BEAR|FAILED_BREAK|FAILED_AUCTION"), "SWEEP"),
    (re.compile(r"ABSORPTION"), "ABSORPTION"),
    (re.compile(r"DIVERGENCE|REVERSAL_RESOLUTION|REGULAR_REVERSAL|HIDDEN_CONTINUATION"), "DIVERGENCE"),
    (re.compile(r"DEPARTURE"), "DEPARTURE"),
    (re.compile(r"DEFENSE|BOUNCE|DEMAND_DEFENSE"), "BOUNCE"),
    (re.compile(r"RECLAIM|POC_VALUE|EMA55_RECLAIM|CONFLUENCE_RECLAIM"), "RECLAIM"),
    (re.compile(r"RETEST|PULLBACK|PATH_RETEST|EXPANSION_PULLBACK|FAST_CLOUD"), "RETEST"),
    (re.compile(r"BREAK|ACCEPTANCE|CLEARANCE|DIRECT_ACCEPT|CLOUD_REGIME_EXPANSION"), "BREAKOUT"),
    (re.compile(r"TRANSITION|REGIME|BULL_FLIP|FEAR_RECOVERY"), "REGIME"),
]
BLOCK_MISSING = re.compile(r"^(twoFamilies|fullTraversal|reclaim)$")


def event_class_of(ep):
    blob = f"{ep['lane']} {ep['event']} {ep['nativePhase']}".upper()
    for rx, klass in EVENT_FROM_LANE:
        if rx.search(blob):
            return klass
    return "ROTATION"


def is_reverb_overlap(e):
    return e["scannerId"] == "lattice" and "CONFLUENCE" in e["lane"]


def is_rail_class(klass):
    return klass in ("RETEST", "BOUNCE", "SWEEP", "DIVERGENCE", "ABSORPTION", "RECLAIM")


def blocking_missing(ep):
    for m in ep["missing"]:
        if BLOCK_MISSING.search(m):
            return m
    if is_reverb_overlap(ep) and "SINGLE_FAMILY" in ep["nativePhase"]:
        return "twoFamilies"
    return None


def lead_score(e):
    klass = event_class_of(e)
    overlap = is_reverb_overlap(e)
    score = 0
    if e["phase"] == "ACTIVE":
        score += 0
    elif e["phase"] == "READY":
        score += 18
    else:
        score += 40
    if klass == "SWEEP":
        score += 0
    elif klass == "BOUNCE":
        score += 1
    elif klass == "DIVERGENCE":
        score += 2
    elif klass == "ABSORPTION":
        score += 3
    elif klass == "RETEST":
        score += 4
    elif klass == "RECLAIM" and not overlap:
        score += 5
    elif klass == "DEPARTURE":
        score += 6
    elif overlap:
        score += 24
    else:
        score += 10
    if e["grade"] == "S":
        score += 0
    elif e["grade"] == "A":
        score += 3
    else:
        score += 8
    if not e["antiChase"]:
        score += 5
    if e["missing"]:
        score += 4
    trig = e["geometry"].get("trigger")
    trig = trig if trig is not None else e["close"]
    if trig > 0 and e["close"] > 0:
        gap = abs(e["close"] - trig) / e["close"]
        if gap > 0.06:
            score += 15
        if gap > 0.12:
            score += 20
    return score


def pick_primary(live):
    return min(live, key=lead_score)


def hard_contradiction(ep):
    blob = " ".join(ep["conflicts"]).lower()
    if re.search(r"invalidat|lost zone|failed boundary|failed auction", blob):
        return "hard contradiction — invalidation or boundary failed"
    return None


def developing_phase(phase):
    return phase in ("FORMING", "DISCOVERED")


def dead_phase(phase):
    return phase in ("FAILED", "EXPIRED")


def exhausted_native(ep):
    return bool(re.search(r"DEPLET|EXHAUST|EXPIRED|DEAD_ZONE|COLLAPS", f"{ep['nativePhase']} {ep['lane']} {ep['event']}"))


def approaching_only(ep):
    return "APPROACH" in f"{ep['nativePhase']} {ep['lane']} {ep['event']}"


def in_demand_band(ep):
    g = ep["geometry"]
    buy = g.get("trigger")
    if buy is None:
        buy = g.get("zoneHigh")
    if buy is None:
        buy = ep["close"]
    stop = g.get("invalidation")
    if stop is None:
        stop = g.get("zoneLow")
    if buy is None or buy <= 0:
        return False
    if stop is None or stop >= buy:
        return abs(ep["close"] - buy) / buy <= 0.04
    risk = buy - stop
    if risk <= 0:
        return False
    ext = (ep["close"] - buy) / risk
    return -0.35 <= ext <= 0.4


def _ema_last(closes, n):
    if len(closes) < n:
        return None
    k = 2 / (n + 1)
    acc = lsum(closes[:n], 0) / n
    for i in range(n, len(closes)):
        acc = closes[i] * k + acc * (1 - k)
    return acc


def structural_floor(bars, close):
    if not bars or len(bars) < 20 or close <= 0:
        return False
    closes = [b["c"] for b in bars]
    e200 = _ema_last(closes, 200) if len(bars) >= 200 else None
    on200 = e200 is not None and e200 > 0 and e200 * 0.97 <= close <= e200 * 1.05
    e21 = _ema_last(closes, 21)
    damaged = e21 is not None and e21 > 0 and close < e21 * 0.96
    lo20 = _jmin(b["l"] for b in bars[-20:])
    lo60 = _jmin(b["l"] for b in bars[-60:]) if len(bars) >= 60 else lo20
    at_floor = (lo20 > 0 and close <= lo20 * 1.04) or (lo60 > 0 and close <= lo60 * 1.04)
    return on200 or (at_floor and damaged)


def is_first_defense(ep, bars=None):
    if ep["scannerId"] not in ("vector", "meridian"):
        return False
    if approaching_only(ep):
        return False
    if dead_phase(ep["phase"]):
        return False
    klass = event_class_of(ep)
    if not is_rail_class(klass) and klass != "REGIME":
        return False
    return in_demand_band(ep) and structural_floor(bars, ep["close"])


def _pretty(lane):
    return lane.replace("_", " ").lower()


def location_why(ep):
    g = ep["geometry"]
    if g.get("zoneLow") is not None and g.get("zoneHigh") is not None:
        band = f"{js_str(_round_px(g['zoneLow']))}–{js_str(_round_px(g['zoneHigh']))}"
    elif g.get("trigger") is not None:
        band = f"trigger {js_str(_round_px(g['trigger']))}"
    else:
        band = "unlocated"
    sid = ep["scannerId"]
    if sid == "vector":
        return f"Structural demand {band}. {ep['publicName']} {_pretty(ep['lane'])}."
    if sid == "ravel":
        return f"EMA ribbon / EMA55 {band}. Cascade topology."
    if sid == "breakline":
        return f"Accepted boundary {band}. Threshold auction."
    if sid == "ripster":
        return f"Cloud interaction {band}. Fissure clocks."
    if sid == "panic":
        return f"Weekly value / POC {band}. Dread regime."
    if sid == "lattice":
        return f"Independent confluence {band}. Reverb path."
    if sid == "apex":
        return f"Structural extreme {band}. Zenith residual."
    if sid == "strata":
        return f"Demand origin {band}. Strata absorption."
    if sid == "meridian":
        return f"Regime location {band}. Meridian recovery."
    return f"Located {band}. {ep['publicName']}."


def invalidate_line(stop):
    return f"Daily close below {js_str(_round_px(stop))} voids the plan."


def supporting_of(live, primary):
    return _unique([e["publicName"] for e in live if e["scannerId"] != primary["scannerId"] and e["phase"] == "ACTIVE"
                    and not e["missing"] and not blocking_missing(e)])


def disagreement_of(row):
    return _unique([f"{e['publicName']} {'failed' if e['phase'] == 'FAILED' else e['conflicts'][0]}"
                    for e in row["episodes"] if e["phase"] == "FAILED" or e["conflicts"]])


def _atr14_doc(bars):
    if len(bars) < 15:
        return None
    s = 0.0
    for i in range(len(bars) - 14, len(bars)):
        prev, b = bars[i - 1], bars[i]
        s += max(b["h"] - b["l"], abs(b["h"] - prev["c"]), abs(b["l"] - prev["c"]))
    return s / 14


def _day_move_sigma(bars):
    if len(bars) < 12:
        return None
    rets = []
    for i in range(len(bars) - 21, len(bars) - 1):
        if i < 1:
            continue
        a, b = bars[i - 1]["c"], bars[i]["c"]
        if a > 0 and b > 0:
            rets.append(vlog(b / a))
    if len(rets) < 8:
        return None
    srt = sorted(rets)
    mid = srt[len(srt) // 2]
    mad = sorted(abs(r - mid) for r in rets)[len(rets) // 2]
    sigma = 1.4826 * mad
    if sigma <= 0:
        return None
    last, prev = bars[-1], bars[-2]
    if prev["c"] <= 0:
        return None
    return abs(vlog(last["c"] / prev["c"])) / sigma


def chase_tape(episode, plan, bars=None):
    risk = plan["buy"] - plan["stop"]
    extension_r = (episode["close"] - plan["buy"]) / risk if risk > 0 else 0
    if not bars or len(bars) < 16:
        return {"extensionR": extension_r, "zoneAtr": None, "triggerAtr": None, "gapAtr": None, "daySigma": None}
    atr = _atr14_doc(bars)
    last, prev = bars[-1], bars[-2]
    g = episode["geometry"]
    zone_high = g.get("zoneHigh") if g.get("zoneHigh") is not None else plan["buy"]
    trigger = g.get("trigger") if g.get("trigger") is not None else plan["buy"]
    return {"extensionR": extension_r,
            "zoneAtr": max(0, last["c"] - zone_high) / atr if atr else None,
            "triggerAtr": max(0, last["c"] - trigger) / atr if atr else None,
            "gapAtr": max(0, last["o"] - prev["c"]) / atr if (atr and prev) else None,
            "daySigma": _day_move_sigma(bars)}


def ran_off_low(bars, last):
    if not bars or len(bars) < 8 or not (last is not None and last > 0):
        return None
    win = bars[-DOCTRINE["offLowBars"]:]
    lows = [b["l"] for b in win if _fin(b["l"]) and b["l"] > 0]
    if not lows:
        return None
    lo = min(lows)
    pct = (last - lo) / lo
    if pct > DOCTRINE["offLowPct"]:
        return f"already {js_str(js_round(pct * 100))}% off the {DOCTRINE['offLowBars']}-session low — aftermath, not origin"
    return None


def chase_reject(tape):
    if tape["zoneAtr"] is not None and tape["zoneAtr"] > DOCTRINE["zoneAtr"]:
        return "late — more than 1 ATR past the zone"
    if tape["triggerAtr"] is not None and tape["triggerAtr"] > DOCTRINE["triggerAtr"]:
        return "late — more than 0.75 ATR past the trigger"
    if tape["gapAtr"] is not None and tape["gapAtr"] > DOCTRINE["gapAtr"]:
        return "gapped more than 1 ATR — entry quality is poor"
    if tape["daySigma"] is not None and tape["daySigma"] > DOCTRINE["daySigma"] and tape["extensionR"] > 0.1:
        return "unusually large daily move — chase risk"
    return None


def rail_state(bars, close):
    if not bars or len(bars) < 21:
        return {"ema21": None, "ema50": None, "ema200": None, "vs21": None, "vs50": None, "vs200": None,
                "sitting": False, "leftRail": False}
    closes = [b["c"] for b in bars]
    ema21 = _ema_last(closes, 21)
    ema50 = _ema_last(closes, 50) if len(bars) >= 50 else None
    ema200 = _ema_last(closes, 200) if len(bars) >= 200 else None
    vs21 = (close - ema21) / ema21 if (ema21 and ema21 > 0) else None
    vs50 = (close - ema50) / ema50 if (ema50 and ema50 > 0) else None
    vs200 = (close - ema200) / ema200 if (ema200 and ema200 > 0) else None
    on50 = vs50 is not None and -0.02 <= vs50 <= 0.03
    on200 = vs200 is not None and -0.02 <= vs200 <= 0.03
    left = vs50 is not None and vs50 > 0.04 and (vs200 is None or vs200 > 0.03)
    return {"ema21": ema21, "ema50": ema50, "ema200": ema200, "vs21": vs21, "vs50": vs50, "vs200": vs200,
            "sitting": on50 or on200, "leftRail": left}


def doctrine_headline(event_class, kt):
    rr = f"{to_fixed(kt['rr'], 1)}R"
    in_band = kt["close"] <= kt["buy"] + 0.25 * (kt["buy"] - kt["stop"])
    if event_class == "SWEEP":
        return f"Failed breakdown reclaimed. {rr} from the origin."
    if event_class == "BOUNCE":
        return f"Demand is defending the mark. Work the buy band. {rr}." if in_band \
            else f"Demand defended. {rr} if the zone still holds."
    if event_class == "RECLAIM":
        return "Holding the backtest of the reclaim. Close enough to work a limit."
    if event_class == "DIVERGENCE":
        return f"Weakness failed at structure. {rr} on the resolution."
    if event_class == "ABSORPTION":
        return f"Sellers spent. Price did not. {rr} from the origin."
    if event_class == "RETEST":
        return "Holding the 50-day or 200-day after the breakout. That is the add." if kt["tier"] == "S" \
            else "Controlled retest. Levels are live at the mark."
    if event_class == "BREAKOUT":
        return f"Accepted outside the boundary. Wait for a dip into the buy band. {rr}." if in_band \
            else f"Accepted outside the boundary. {rr} plan, full attention."
    if event_class == "DEPARTURE":
        return f"First controlled test of the departure. {rr}."
    if event_class == "REGIME":
        return f"Regime flipped and held. {rr} on the first clean location."
    if event_class == "ROTATION":
        return f"Control changed hands on the completed bar. {rr}."
    return None


# == curl.ts ===========================================================================================================
CURL_GATE = {"maxOffLow60": 0.06, "rsiTroughMax": 35, "rsiNowMax": 50}


def _last_finite(arr, back=0):
    seen = 0
    for v in reversed(arr):
        if v is None or not math.isfinite(v):
            continue
        if seen == back:
            return v
        seen += 1
    return None


def _trough(arr, n):
    mn = None
    count = 0
    for v in reversed(arr):
        if count >= n:
            break
        if v is None or not math.isfinite(v):
            continue
        count += 1
        if mn is None or v < mn:
            mn = v
    return mn


def read_curl(bars=None):
    empty = {"rsi": None, "rsiPrev": None, "rsiTrough": None, "rsiCurl": False, "macdHist": None,
             "macdHistPrev": None, "macdCurl": False, "bullDiv": False, "offLow60": None, "atBottom": False,
             "extended": False, "ok": False, "why": "need completed dailies for the curl read"}
    if not bars or len(bars) < 40:
        return empty
    closes = [b["c"] for b in bars]
    r = T.rsi(closes, 14)
    m = T.macd(closes)
    close = _last_finite(closes)
    rsi_now = _last_finite(r)
    rsi_prev = _last_finite(r, 1)
    rsi_two = _last_finite(r, 2)
    rsi_trough = _trough(r, 10)
    hist_now = _last_finite(m["hist"])
    hist_prev = _last_finite(m["hist"], 1)
    hist_two = _last_finite(m["hist"], 2)
    lows = [b["l"] for b in bars[-60:] if _fin(b["l"])]
    low60 = min(lows) if lows else None
    off_low60 = (close - low60) / low60 if (close is not None and low60 and low60 > 0) else None
    at_bottom = off_low60 is not None and off_low60 < CURL_GATE["maxOffLow60"]
    rsi_curl = (rsi_now is not None and rsi_prev is not None and rsi_two is not None and rsi_now > rsi_prev and
                rsi_prev > rsi_two and rsi_trough is not None and rsi_trough <= CURL_GATE["rsiTroughMax"] and
                rsi_now < CURL_GATE["rsiNowMax"])
    extended = rsi_now is not None and rsi_now >= CURL_GATE["rsiNowMax"]
    macd_curl = (hist_now is not None and hist_prev is not None and hist_two is not None and hist_now > hist_prev and
                 hist_prev > hist_two)
    bull_div = False
    if len(closes) >= 24 and len(m["hist"]) >= 24:
        a, b = closes[-12:], closes[-24:-12]
        ha, hb = m["hist"][-12:], m["hist"][-24:-12]
        min_a = _jmin(x for x in a if x is not None)
        min_b = _jmin(x for x in b if x is not None)
        hmin_a = _jmin(x for x in ha if x is not None)
        hmin_b = _jmin(x for x in hb if x is not None)
        if all(math.isfinite(x) for x in (min_a, min_b, hmin_a, hmin_b)):
            bull_div = min_a < min_b and hmin_a > hmin_b
    why = "curl ready"
    if not at_bottom:
        why = "not at a 60-day bottom"
    elif extended:
        why = "RSI already extended — wait for the backtest"
    elif not rsi_curl:
        why = "RSI is not curling up from a depressed trough"
    elif not macd_curl:
        why = "MACD is not curling"
    ok = at_bottom and not extended and rsi_curl and macd_curl
    return {"rsi": rsi_now, "rsiPrev": rsi_prev, "rsiTrough": rsi_trough, "rsiCurl": rsi_curl, "macdHist": hist_now,
            "macdHistPrev": hist_prev, "macdCurl": macd_curl, "bullDiv": bull_div, "offLow60": off_low60,
            "atBottom": at_bottom, "extended": extended, "ok": ok, "why": why}


def _pick_line(seed, opts):
    h = 0
    for ch in seed:
        for unit in _utf16(ch):
            h = (h * 33 + unit) % 4294967296
    return opts[h % len(opts)]


def _utf16(ch):
    o = ord(ch)
    if o < 0x10000:
        return (o,)
    o -= 0x10000
    return (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF))


def _js_or_empty(v):
    return "" if v is None else js_str(v)


def curl_note(read, seed=""):
    if not read["ok"]:
        if read["rsi"] is not None:
            return f"RSI 14 at {to_fixed(read['rsi'], 0)}"
        return ""
    bits = []
    key = f"{seed}:{_js_or_empty(read['rsi'])}:{_js_or_empty(read['rsiTrough'])}"
    if read["rsi"] is not None and read["rsiTrough"] is not None:
        n = to_fixed(read["rsi"], 0)
        t = to_fixed(max(0, read["rsiTrough"]), 0)
        bits.append(_pick_line(key + "r", [f"RSI 14 at {n} after a {t} trough", f"RSI 14 {n}, up from {t}",
                                           f"RSI 14 lifting {t} → {n}", f"RSI 14 {n} after it stopped falling at {t}"]))
    if read["bullDiv"]:
        bits.append(_pick_line(key + "d", ["price made a newer low, RSI 14 did not", "bullish RSI divergence",
                                           "RSI 14 refused the new price low"]))
    elif read["macdCurl"]:
        bits.append(_pick_line(key + "m", ["MACD histogram turning up", "MACD 12/26/9 histogram flipped up",
                                           "MACD histogram no longer making new lows"]))
    if read["offLow60"] is not None:
        pct = to_fixed(read["offLow60"] * 100, 0)
        bits.append(_pick_line(key + "o", [f"{pct}% off the 60-day low", f"{pct}% above the 60-day low",
                                           f"still {pct}% from the 60-day low"]))
    return " · ".join(bits)


def keep_after_curl(setup, bars=None):
    if not bars or len(bars) < 40:
        return {"keep": True, "read": None, "why": "no dailies — last book stands"}
    read = read_curl(bars)
    if read["ok"]:
        return {"keep": True, "read": read, "why": "curl ready"}
    if read["extended"] and not setup.get("atSupport"):
        return {"keep": False, "read": read, "why": read["why"]}
    if setup.get("atSupport"):
        return {"keep": True, "read": read, "why": "strength at support"}
    if setup.get("curlOk"):
        return {"keep": True, "read": read, "why": "already cleared curl"}
    return {"keep": True, "read": read, "why": read["why"]}


# == location-law.ts (liveBuyWhy) ======================================================================================
def live_buy_why(bars, last, buy=None):
    if not (last is not None and last > 0):
        return "no last"
    if buy is not None and buy > last * 1.002:
        return "buy is above last · next lower shelf"
    return None


# == select.ts =========================================================================================================
EMA_ON_PCT = 0.02


def _sel_last_finite(arr):
    for v in reversed(arr):
        if v is not None and math.isfinite(v):
            return v
    return None


def _near(last, px, pct=EMA_ON_PCT):
    return last > 0 and px > 0 and abs(last - px) / last <= pct


def marked_levels(bars, last):
    if not bars or not (last > 0):
        return []
    closes = [b["c"] for b in bars]
    win15 = bars[-DOCTRINE["offLowBars"]:]
    lo15 = _jmin(b["l"] for b in win15 if b["l"] > 0)
    win60 = bars[-60:]
    hi = _jmax(b["h"] for b in win60)
    lo = _jmin(b["l"] for b in win60 if b["l"] > 0)
    span = hi - lo
    out = []
    if lo15 > 0:
        out.append({"name": "15-session low", "px": lo15, "kind": "origin"})
    if span > 0:
        for r, name in ((0.382, "38.2% retrace"), (0.5, "50% retrace"), (0.618, "61.8% retrace"),
                        (0.786, "78.6% retrace"), (0.887, "88.7% retrace"), (1.0, "100% retrace"),
                        (1.272, "127.2% extension")):
            out.append({"name": name, "px": hi - r * span, "kind": "fib"})
    e9 = _sel_last_finite(T.ema(closes, 9))
    e21 = _sel_last_finite(T.ema(closes, 21))
    e50 = _sel_last_finite(T.ema(closes, 50))
    e200 = _sel_last_finite(T.ema(closes, 200)) if len(bars) >= 200 else None
    if e9 is not None:
        out.append({"name": "9-day EMA", "px": e9, "kind": "ema"})
    if e21 is not None:
        out.append({"name": "21-day EMA", "px": e21, "kind": "ema"})
    if e50 is not None:
        out.append({"name": "50-day EMA", "px": e50, "kind": "ema"})
    if e200 is not None:
        out.append({"name": "200-day EMA", "px": e200, "kind": "ema"})
    for px in _prior_support(bars):
        out.append({"name": "prior support", "px": px, "kind": "origin"})
    return out


def _prior_support(bars):
    win = bars[-120:]
    pivots = []
    for i in range(2, len(win) - 2):
        l = win[i]["l"]
        if l < win[i - 1]["l"] and l < win[i - 2]["l"] and l < win[i + 1]["l"] and l < win[i + 2]["l"]:
            pivots.append(l)
    clusters = []
    for p in pivots:
        near_hits = [q for q in pivots if abs(q - p) / p <= 0.015]
        if len(near_hits) >= 2:
            avg = lsum(near_hits, 0) / len(near_hits)
            if not any(abs(c - avg) / avg <= 0.015 for c in clusters):
                clusters.append(avg)
    return clusters


def _is_backtest(bars, level, last):
    if not (level > 0) or len(bars) < 20:
        return False
    if not _near(last, level, EMA_ON_PCT):
        return False
    return any(b["h"] > level * 1.03 for b in bars[-25:-3])


def _weekly_ok(bars):
    w = P.weekly_bars(bars)
    if len(w) < 20:
        return False
    closes = [b["c"] for b in w]
    r = T.rsi(closes, 14)
    now = _sel_last_finite(r)
    prev = _sel_last_finite(r[:-1])
    m = T.macd(closes)
    hist = _sel_last_finite(m["hist"])
    hist_prev = _sel_last_finite(m["hist"][:-1])
    oversold = now is not None and now <= 40
    rising = now is not None and prev is not None and now > prev and now <= 45
    macd_up = hist is not None and hist_prev is not None and hist > hist_prev
    return (oversold or rising) and (macd_up or oversold)


def _volume_dryup(bars):
    if len(bars) < 30:
        return False
    last5 = bars[-5:]
    prior = bars[-25:-5]
    a = lsum((b["v"] for b in last5), 0) / len(last5)
    b = lsum((x["v"] for x in prior), 0) / len(prior)
    if not (b > 0):
        return False
    net_down = last5[-1]["c"] <= last5[0]["o"] * 1.01
    return a / b <= 0.75 and net_down


def _ma_flip(bars, last, levels):
    for rail in (l for l in levels if l["name"] in ("50-day EMA", "200-day EMA")):
        if not _near(last, rail["px"]):
            continue
        prior = bars[-18:-2]
        below = len([b for b in prior if b["c"] < rail["px"]])
        if below >= 5 and last >= rail["px"] * 0.995:
            return True
    return False


def _is_stacked(sitting):
    for i in range(len(sitting)):
        for j in range(i + 1, len(sitting)):
            a, b = sitting[i], sitting[j]
            if a["kind"] == b["kind"]:
                continue
            mid = (a["px"] + b["px"]) / 2
            if mid > 0 and abs(a["px"] - b["px"]) / mid <= 0.025:
                return True
    return False


def _level_held(bars, level):
    win = bars[-6:]
    if not win:
        return False
    tested = any(b["l"] <= level["px"] * 1.01 for b in win)
    return tested and win[-1]["c"] >= level["px"] * 0.99


def _find(levels, name):
    return next((l for l in levels if l["name"] == name), None)


def _failed_shallow(bars, last, levels):
    e50 = _find(levels, "50-day EMA")
    shallow = _find(levels, "61.8% retrace") or _find(levels, "38.2% retrace")
    if not e50 or not shallow or not (last > 0):
        return False
    tagged = any(shallow["px"] * 0.995 <= b["h"] <= shallow["px"] * 1.04 for b in bars[-8:])
    return tagged and last < e50["px"] * 0.98


def _immediate_vol(bars, last, levels):
    if len(bars) < 3:
        return False
    a, b = bars[-1], bars[-2]
    day = abs(a["c"] - a["o"]) / a["o"] if a["o"] > 0 else 0
    gap = (a["o"] - b["c"]) / b["c"] if b["c"] > 0 else 0
    e50 = _find(levels, "50-day EMA")
    above = e50 is not None and last > e50["px"] * 1.01
    return above and (day >= 0.08 or gap >= 0.05)


def _blank_read(verdict, why):
    return {"verdict": verdict, "why": why, "buy": None, "level": None, "confluence": 0, "onLevel": False,
            "curl": False, "volume": False, "origin": False, "backtest": False, "aftermath": False, "stacked": False,
            "held": False, "weeklyOk": False, "dryup": False, "maFlip": False, "washout": False, "coil": False,
            "size": "starter"}


def read_select(bars, last, now):
    if not bars or len(bars) < 20 or not (last is not None and last > 0):
        return _blank_read("WAIT", "need a daily tape to mark a level")
    bounce = ran_off_low(bars, last)
    levels = marked_levels(bars, last)
    sitting = sorted((lv for lv in levels if _near(last, lv["px"], 0.05 if lv["kind"] == "origin" else EMA_ON_PCT)),
                     key=lambda lv: abs(last - lv["px"]))
    level = sitting[0] if sitting else None
    on_level = level is not None
    origin = bool(level and (level["kind"] == "origin" or any(l["kind"] == "origin" for l in sitting)))
    flip = _ma_flip(bars, last, levels)
    backtest = (_is_backtest(bars, level["px"], last) if level else False) or flip
    aftermath = bool(bounce) and not backtest
    stacked = _is_stacked(sitting)
    held = (level["kind"] == "origin" or _level_held(bars, level)) if level else False
    week = _weekly_ok(bars)
    dryup = _volume_dryup(bars)
    curl = read_curl(bars)
    wash = L.read_washout(bars, last, now)
    coil = L.read_coil(bars, last, now)
    vols = T.relative_volume(bars, 20)
    vol_now = _sel_last_finite(vols)
    volume = vol_now is not None and vol_now >= 1.3
    curl_ok = curl["ok"] or ((curl["rsiCurl"] or curl["bullDiv"]) and curl["macdCurl"]) or week
    confluence = 0
    if on_level:
        confluence += 1
    if curl_ok:
        confluence += 1
    if volume:
        confluence += 1
    if origin or backtest:
        confluence += 1
    if stacked:
        confluence += 1
    if held and on_level:
        confluence += 1
    if week:
        confluence += 1
    if dryup:
        confluence += 1
    if wash["ok"]:
        confluence += 2
    pack = {"buy": last if wash["ok"] else (level["px"] if level else None), "level": level,
            "confluence": confluence, "onLevel": on_level or wash["ok"], "curl": curl_ok, "volume": volume,
            "origin": origin, "backtest": backtest, "aftermath": aftermath, "stacked": stacked, "held": held,
            "weeklyOk": week, "dryup": dryup, "maFlip": flip, "washout": wash["ok"], "coil": coil["ok"],
            "size": "heavy" if coil["ok"] else "starter"}
    if _immediate_vol(bars, last, levels):
        return dict(pack, verdict="WAIT", why="immediate volatility — wait for the level, not the gap")
    if coil["ok"]:
        return dict(pack, verdict="BUY", why=coil["why"], size="heavy")
    if wash["ok"]:
        heavy = bool(wash["onFib"] and wash["onFib"]["r"] >= 0.786)
        return dict(pack, verdict="BUY", why=wash["why"], size="heavy" if heavy else "starter")
    loc_why = live_buy_why(bars, last) if len(bars) >= 50 else None
    if loc_why:
        return dict(pack, verdict="LATE" if re.search(r"already back above|spent|too far off|Chase", loc_why, re.I)
                    else "WAIT", why=loc_why, buy=pack["buy"])
    if aftermath:
        return dict(pack, verdict="LATE", why=bounce or "already ran off the low — aftermath, not origin")
    if _failed_shallow(bars, last, levels) and not (level and re.search(r"78\.6|88\.7", level["name"])):
        f786 = _find(levels, "78.6% retrace")
        return dict(pack, verdict="WAIT", why="first Fib failed — Echo waits for 0.786",
                    buy=f786["px"] if (f786 and f786["px"] is not None) else pack["buy"])
    if curl["extended"] and not on_level:
        return dict(pack, verdict="LATE", why="RSI already extended — wait for the backtest", buy=None, level=None)
    if not on_level:
        return dict(pack, verdict="WAIT", why="no marked level — Echo does not buy mid-air")
    if not held and not origin:
        return dict(pack, verdict="WAIT", why=f"need {level['name']} to hold")
    if not curl_ok and not origin and not backtest and not stacked:
        return dict(pack, verdict="WAIT", why="level is marked, confirmation is not")
    if confluence < 2:
        return dict(pack, verdict="WAIT", why="need two of: level, curl, volume, origin/backtest, stack")
    if stacked:
        label = f"stacked {level['name']} at {to_fixed(level['px'], 2)}"
    elif backtest:
        label = f"backtest of {level['name']} at {to_fixed(level['px'], 2)}"
    else:
        label = f"origin at {level['name']} {to_fixed(level['px'], 2)}"
    heavy = stacked or flip or bool(re.search(r"78\.6|88\.7|200-day", level["name"]))
    return dict(pack, verdict="BUY", why=label, size="heavy" if heavy else "starter")


# == sector-map.ts =====================================================================================================
SECTOR_ETFS = ("XLK", "SMH", "SOXX", "XLE", "XOP", "XLF", "IYF", "XBI", "IBB", "GDX", "COPX", "USO", "SLV", "GLD",
               "XLY", "XHB")
SECTOR_MAP = {
    "NVDA": "SMH", "AVGO": "SMH", "TSM": "SMH", "ASML": "SMH", "AMAT": "SMH", "LRCX": "SMH", "KLAC": "SMH",
    "QCOM": "SMH", "TXN": "SMH", "ADI": "SMH", "NXPI": "SMH", "MCHP": "SMH", "ON": "SMH", "MPWR": "SMH",
    "MRVL": "SMH", "MU": "SMH", "INTC": "SMH", "AMD": "SMH", "ARM": "SMH", "SMCI": "SMH",
    "DELL": "XLK", "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLK", "AMZN": "XLK", "META": "XLK", "CRM": "XLK",
    "NOW": "XLK", "ORCL": "XLK", "ADBE": "XLK", "PANW": "XLK", "CRWD": "XLK", "DDOG": "XLK", "NET": "XLK",
    "SNOW": "XLK", "MDB": "XLK", "TEAM": "XLK", "INTU": "XLK", "ACN": "XLK", "APP": "XLK", "SHOP": "XLK",
    "SQ": "XLK", "PYPL": "XLK", "COIN": "XLK", "HOOD": "XLK",
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "EOG": "XLE", "SLB": "XLE", "HAL": "XLE", "OXY": "XLE",
    "FANG": "XLE", "DVN": "XLE", "MPC": "XLE", "VLO": "XLE", "CTRA": "XLE", "LNG": "XLE", "KMI": "XLE",
    "WMB": "XLE", "ET": "XLE",
    "LLY": "IBB", "UNH": "IBB", "JNJ": "IBB", "ABBV": "IBB", "MRK": "IBB", "PFE": "IBB", "AMGN": "IBB",
    "GILD": "IBB", "REGN": "IBB", "ISRG": "IBB", "ZTS": "IBB",
    "NKE": "XLY", "HD": "XLY", "LOW": "XLY", "SBUX": "XLY", "TGT": "XLY", "F": "XLY", "GM": "XLY",
    "AA": "COPX", "CENX": "COPX",
    "NEM": "GDX", "GOLD": "GDX", "AEM": "GDX", "WPM": "GDX", "KGC": "GDX", "PAAS": "GDX", "AU": "GDX",
    "FCX": "COPX", "SCCO": "COPX", "TECK": "COPX", "RIO": "COPX", "BHP": "COPX", "VALE": "COPX", "ALB": "COPX",
    "SQM": "COPX", "MP": "COPX",
    "MOS": "XLE", "CF": "XLE", "NTR": "XLE", "ADM": "XLE", "BG": "XLE", "CTVA": "XLE", "DE": "XLE",
    "NEE": "XLE", "SO": "XLE", "DUK": "XLE", "D": "XLE", "AEP": "XLE", "EXC": "XLE",
    "AMT": "XLK", "EQIX": "XLK", "DLR": "XLK", "PLD": "XLK", "CCI": "XLK",
    "O": "XLF", "SPG": "XLF", "WELL": "XLF",
    "BA": "XLK", "RTX": "XLK", "LMT": "XLK", "NOC": "XLK", "GD": "XLK", "HII": "XLK", "LHX": "XLK",
    "TSLA": "XLK", "RIVN": "XLK", "LCID": "XLK", "NIO": "XLK", "XPEV": "XLK", "LI": "XLK",
    "IREN": "XLK", "WULF": "XLK", "HIVE": "XLK", "SEDG": "XLK", "RUN": "XLK", "FLNC": "XLK",
    "PPC": "XLE", "TSN": "XLE",
    "ATEN": "XLK", "VPG": "XLK", "GRAB": "XLK", "ROK": "XLK",
}


def sector_etf_of(symbol):
    s = str(symbol or "").upper()
    if s in SECTOR_ETFS:
        return None
    return SECTOR_MAP.get(s)


# == sector-tape.ts ====================================================================================================
REGIME_EXTRA = ("XLY", "XLP", "XHB", "XLU")
DISPLAY = {"SMH": "Semis", "SOXX": "Semis", "XLK": "Tech", "XLE": "Energy", "XOP": "E&P", "COPX": "Copper",
           "GDX": "Miners", "XLF": "Financials", "IYF": "Financials", "XBI": "Biotech", "IBB": "Biotech", "USO": "Oil",
           "XHB": "Housing", "XLY": "Discretionary", "XLP": "Staples", "XLU": "Utilities"}
CYCLICAL = {"SMH", "SOXX", "XLE", "XOP", "COPX", "USO", "XBI", "XHB", "GDX", "XLY"}
RANK = ("SMH", "XLK", "XLE", "XOP", "COPX", "GDX", "XLY", "XLF", "XBI", "IBB", "USO", "XHB")


def _num_or0(v):
    """Number(v || 0) for a bar close."""
    try:
        x = float(v) if v else 0.0
    except (TypeError, ValueError):
        return float("nan")
    return x


def _ret(bars, days):
    if not bars or len(bars) <= days:
        return None
    a = _num_or0(bars[-1]["c"])
    b = _num_or0(bars[-1 - days]["c"])
    if not (a > 0) or not (b > 0):
        return None
    return (a - b) / b


def _rs(a, b, days):
    x, y = _ret(a, days), _ret(b, days)
    if x is None or y is None:
        return None
    return x - y


def _range_low(bars, n):
    lows = [b["l"] for b in bars[-n:] if b["l"] > 0]          # slice(-0) is the whole array in both languages
    return min(lows) if lows else 0


def _range_high(bars, n):
    highs = [b["h"] for b in bars[-n:] if b["h"] > 0]
    return max(highs) if highs else 0


def label_sleeve(etf, spy):
    if not etf or len(etf) < 60 or not spy or len(spy) < 60:
        return "trough"
    long = _rs(etf, spy, min(126, len(etf) - 2))
    short = _rs(etf, spy, 20)
    last = _num_or0(etf[-1]["c"])
    closes = [b["c"] for b in etf]
    e50 = L.last_ema(closes, 50)
    e50prev = L.last_ema(closes[:-8], 50)
    falling50 = e50 is not None and e50prev is not None and e50 < e50prev
    lo20 = _range_low(etf, 20)
    lo_prev = _range_low(etf[:-5], 25)
    new_low = lo20 > 0 and lo_prev > 0 and lo20 <= lo_prev * 1.002 and (short is None or short < -0.015)
    if new_low and falling50:
        return "waterfall"
    if short is not None and short < -0.03 and falling50:
        return "waterfall"
    if long is not None and long > 0.04 and short is not None and short > 0 and e50 is not None and last > e50:
        return "trend"
    if long is not None and long < -0.04 and short is not None and short > 0.005:
        return "turn"
    if short is not None and short > 0.012 and not falling50 and (long is None or long < 0.02):
        return "turn"
    return "trough"


def _uniq_names(etfs):
    seen, out = set(), []
    for e in etfs:
        n = DISPLAY.get(e) or e
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def sector_line(tape):
    if tape["line"]:
        return tape["line"]
    turn = _uniq_names(tape["turning"])
    trough = _uniq_names(tape["trough"])
    bits = []
    if turn:
        bits.append(f"{', '.join(turn)} turning")
    if trough:
        bits.append(f"{', '.join(trough)} trough")
    if tape["xlyXlp"] is not None and tape["xlyXlp"] < -0.015:
        bits.append("Discretionary still risk-off")
    if tape["riskOff"] and not turn:
        bits.append("Risk-off. Quality only")
    if not turn:
        bits.append("No sleeve has turned. Wait only")
    else:
        bits.append(f"Hunting {' and '.join(turn)} only")
    return ". ".join(bits) + "."


def read_sector_tape(bars_by, now):
    get = bars_by.get
    spy = get("SPY")
    last = _num_or0(spy[-1]["c"]) if spy else 0
    e200 = L.last_ema([b["c"] for b in spy], min(200, len(spy) - 1)) if (spy and len(spy) >= 80) else None
    spy_under200 = e200 is not None and last > 0 and last < e200
    lo20 = _range_low(spy, 20) if spy else 0
    lo_prev = _range_low(spy[:-20], 20) if spy else 0
    spy_new_low20 = lo20 > 0 and lo_prev > 0 and lo20 < lo_prev
    a, b = _ret(get("XLY"), 20), _ret(get("XLP"), 20)
    xly_xlp = None if (a is None or b is None) else a - b
    iwm_spy = _rs(get("IWM"), spy, 20)
    risk_off = bool((spy_under200 and spy_new_low20) or
                    (xly_xlp is not None and xly_xlp < -0.02 and iwm_spy is not None and iwm_spy < -0.02))
    sleeves = []
    want = list(RANK) + [e for e in REGIME_EXTRA if e not in RANK]
    for etf in want:
        bars = get(etf)
        if not bars or len(bars) < 60:
            continue
        sleeves.append({"etf": etf, "name": DISPLAY.get(etf) or etf, "label": label_sleeve(bars, spy),
                        "rsLong": _rs(bars, spy, min(126, len(bars) - 2)), "rsShort": _rs(bars, spy, 20)})
    tape = {"at": _iso(now), "riskOff": risk_off, "spyUnder200": spy_under200, "spyNewLow20": spy_new_low20,
            "xlyXlp": xly_xlp, "iwmSpy": iwm_spy, "sleeves": sleeves,
            "turning": [s["etf"] for s in sleeves if s["label"] == "turn"],
            "trough": [s["etf"] for s in sleeves if s["label"] == "trough"], "line": ""}
    tape["line"] = sector_line(tape)
    return tape


def name_policy(symbol, tape):
    if not tape or not tape["sleeves"]:
        return "buy"
    etf = sector_etf_of(symbol)
    label = next((s["label"] for s in tape["sleeves"] if s["etf"] == etf), None) if etf else None
    if label == "waterfall":
        return "omit"
    if label == "trend":
        return "trend"
    if label == "trough":
        return "wait"
    if label == "turn":
        if tape["riskOff"] and etf and etf in CYCLICAL:
            return "wait"
        return "buy"
    if not etf:
        return "omit"
    return "wait"


# == fund-overlay.ts / fund-io.ts ======================================================================================
FUND_TTL_MS = 18 * 60 * 60 * 1000


def _fund_pick_line(symbol, lines):
    if not lines:
        return ""
    return _pick_line(symbol, lines)


def empty_fund(symbol, why="skip", now=None):
    return {"symbol": str(symbol or "").upper(), "status": "unknown", "sources": {"yahoo": why, "sec": "skip"},
            "quality": 0, "flow": 0, "bad": False, "line": "", "lines": [], "at": _iso(now or 0)}


def merge_sec(ev, sec):
    if not sec:
        return dict(ev, sources=dict(ev["sources"], sec="skip"))
    lines = list(ev["lines"])
    quality, flow, bad = ev["quality"], ev["flow"], ev["bad"]
    saw = ev["status"] != "unknown" or ev["quality"] or ev["flow"]
    if sec.get("shares") is not None and sec.get("sharesYearAgo") is not None and sec["sharesYearAgo"] > 0:
        dil = (sec["shares"] - sec["sharesYearAgo"]) / sec["sharesYearAgo"]
        if dil > 0.18:
            bad = True
            lines.append(f"Share count is up {js_str(js_round(dil * 100))}% this year. Half size.")
    if sec.get("cash") is not None and sec.get("debt") is not None and sec["cash"] > 0 and sec["debt"] > sec["cash"] * 8:
        if sec.get("netIncome") is not None and sec["netIncome"] < 0:
            bad = True
    if sec.get("cash") is not None and sec["cash"] > 0 and not bad and ev["quality"] == 0:
        quality = 1
        saw = True
        lines.append("Filings still show cash on the balance sheet.")
    if (sec.get("form4Buys90d") or 0) >= 2 and (sec.get("form4Buys90d") or 0) > (sec.get("form4Sells90d") or 0):
        flow = 1
        saw = True
        lines.append("Multiple open-market insider buys in the last 90 days.")
    status = "bad" if bad else ("ok" if (saw or quality or flow) else "unknown")
    line = _fund_pick_line(ev["symbol"], lines) or ev["line"]
    return dict(ev, status=status, quality=0 if bad else quality, flow=flow, bad=bad, line=line, lines=lines,
                sources=dict(ev["sources"], sec="ok"))


def apply_fund_overlay(hit, ev):
    if not ev or ev.get("status") == "unknown":
        return hit
    quality = hit["quality"]
    if ev.get("quality") == 1:
        quality = min(3, quality + 1)
    total = hit["total"] - hit["quality"] + quality
    size = "Half size" if (ev.get("bad") or hit["size"] == "Half size") else hit["size"]
    return dict(hit, quality=quality, total=total, size=size)


def _ymd_ms(s):
    try:
        d = date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None
    return (d - date(1970, 1, 1)).days * 86_400_000


def _sorted_by_end_desc(rows):
    return sorted(rows, key=cmp_to_key(lambda a, b: _locale_cmp(str(b.get("end")), str(a.get("end")))))


def _locale_cmp(a, b):
    return (a > b) - (a < b)


def last_fact(facts):
    units = (facts or {}).get("units") or {}
    rows = units.get("USD") or units.get("shares") or units.get("pure") or []
    if not rows:
        return None
    n = rows and _sorted_by_end_desc(rows)[0].get("val")
    try:
        n = float(n)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def year_ago_fact(facts):
    units = (facts or {}).get("units") or {}
    rows = units.get("shares") or units.get("USD") or []
    if len(rows) < 2:
        return None
    srt = _sorted_by_end_desc(rows)
    latest = _ymd_ms(srt[0].get("end") or "")
    if latest is None:
        return None
    old = next((r for r in srt if (_ymd_ms(r.get("end") or "") is not None and
                                   latest - _ymd_ms(r.get("end") or "") > 300 * 86_400_000)), None)
    try:
        n = float(old.get("val")) if old else float("nan")
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def sec_facts(companyfacts):
    """fund-io.ts secFacts on a parsed companyfacts document. The source reads `facts.us_gaap`; SEC's documents key the
    taxonomy `us-gaap`, so on a real document this returns None, exactly as the source's read did (the SEC lane of
    the overlay never landed: every name's evidence stays "unknown")."""
    g = ((companyfacts or {}).get("facts") or {}).get("us_gaap")
    if not g:
        return None

    def first(*vals):
        for v in vals:
            if v is not None:
                return v
        return None
    return {"cash": last_fact(g.get("CashAndCashEquivalentsAtCarryingValue")),
            "debt": first(last_fact(g.get("LongTermDebt")), last_fact(g.get("LongTermDebtNoncurrent"))),
            "shares": first(last_fact(g.get("CommonStockSharesOutstanding")),
                            last_fact(g.get("WeightedAverageNumberOfSharesOutstandingBasic"))),
            "sharesYearAgo": first(year_ago_fact(g.get("CommonStockSharesOutstanding")),
                                   year_ago_fact(g.get("WeightedAverageNumberOfSharesOutstandingBasic"))),
            "netIncome": last_fact(g.get("NetIncomeLoss")), "form4Buys90d": 0, "form4Sells90d": 0}


def fund_evidence(symbol, companyfacts, now):
    """loadFundEvidence as it runs when Yahoo's quoteSummary refuses (the unknown path): emptyFund "fail", then the SEC
    companyfacts merge."""
    s = str(symbol or "").upper()
    ev = dict(empty_fund(s, "fail", now), sources={"yahoo": "fail", "sec": "skip"})
    sec = sec_facts(companyfacts) if companyfacts else None
    if sec:
        ev = dict(merge_sec(ev, sec), at=_iso(now))
    else:
        ev = dict(ev, sources=dict(ev["sources"], sec="fail"))
    ev["at"] = _iso(now)
    return ev


# == bottom-screen.ts ==================================================================================================
BOTTOM_BUY = 8
BOTTOM_WATCH = 6
BOTTOM_SKIP = {"SPY", "QQQ", "DIA", "VOO", "IWM", "XLK", "XLF", "XLE", "XOP", "XBI", "XLB", "IYF", "IBB", "GLD", "SLV",
               "GDX", "GDXJ", "SIL", "SILJ", "USO", "IBIT", "EWY", "SMH", "SOXX", "COPX", "PALL", "GRID", "QTUM", "URA",
               "URNM", "PICK", "BTC-USD", "ETH-USD", "ETHV", "XLY", "XLP", "XHB", "XLU"}


def _bpx(n):
    if not (n > 0) or not math.isfinite(n):
        return n
    return _round_px(n)


def _dollar_vol20(bars):
    win = bars[-20:]
    if len(win) < 10:
        return 0
    s = 0.0
    for b in win:
        c = b["c"] if (b["c"] and b["c"] == b["c"]) else 0
        v = b["v"] if (b["v"] and b["v"] == b["v"]) else 0
        s += c * v
    return s / len(win)


def _bempty(why, last=0):
    return {"tag": "LEAVE", "live": False, "total": 0, "quality": 0, "cheap": 0, "sector": 0, "structure": 0,
            "volume": 0, "impulse": 0, "lead": why, "why": why, "buy": last, "stop": last, "target": last,
            "size": "Half size", "book": "quality"}


def _climax_and_quiet(bars):
    vol = T.relative_volume(bars, 50)
    climax_i, climax_vol = -1, 0
    for i in range(max(0, len(bars) - 40), len(bars) - 3):
        b, rv = bars[i], vol[i]
        if rv is not None and rv >= 2 and b["c"] < b["o"] and rv >= climax_vol:
            climax_vol = rv
            climax_i = i
    if climax_i < 0:
        return {"climax": False, "quiet": False, "i": -1}
    low = bars[climax_i]["l"]
    quiet = False
    for i in range(climax_i + 1, len(bars)):
        rv = vol[i]
        near = low > 0 and bars[i]["l"] <= low * 1.02
        if near and rv is not None and rv < 1.2:
            quiet = True
    return {"climax": True, "quiet": quiet, "i": climax_i}


def _spring(bars):
    if len(bars) < 40:
        return False
    body = bars[-40:-5]
    recent = bars[-8:]
    base_low = _jmin(b["l"] for b in body if b["l"] > 0)
    if not (base_low > 0):
        return False
    under = any(b["l"] < base_low * 0.995 for b in recent)
    back = _num_or0(bars[-1]["c"]) >= base_low
    return under and back


def _base_contract(bars):
    if len(bars) < 60:
        return False
    late = bars[-25:]
    prior = bars[-60:-25]
    late_span = _range_high(late, 25) - _range_low(late, 25)
    prior_span = _range_high(prior, 35) - _range_low(prior, 35)
    last = _num_or0(bars[-1]["c"])
    if not (prior_span > 0) or not (last > 0):
        return False
    return late_span / prior_span <= 0.55 and late_span / last <= 0.18


def _ema_slope_up(closes, length, look=8):
    e = L.last_ema(closes, length)
    if e is None:
        return False
    prev = L.last_ema(closes[:-look], length)
    if prev is None:
        return False
    return e > prev


def score_bottom(bars, last, ctx=None):
    ctx = ctx or {}
    if not bars or len(bars) < 60 or not (last is not None and last > 0):
        return _bempty("Need more daily history.", last)
    closes = [b["c"] for b in bars]
    e21 = L.last_ema(closes, 21)
    e50 = L.last_ema(closes, 50)
    e200 = L.last_ema(closes, min(200, math.floor(len(bars) * 0.9)))
    r60 = _ret(bars, 60)
    high252 = _range_high(bars, min(252, len(bars)))
    dd = (high252 - last) / high252 if high252 > 0 else None
    vs200 = (last - e200) / e200 if (e200 is not None and e200 > 0) else None
    vs50 = (last - e50) / e50 if (e50 is not None and e50 > 0) else None
    adv = _dollar_vol20(bars)
    last20 = _ret(bars, 20)
    if last < 8:
        return _bempty("Too thin to trade.", last)
    if adv > 0 and adv < 15_000_000:
        return _bempty("Not enough volume to trade.", last)
    if r60 is not None and r60 < -0.7:
        return _bempty("A collapse, not a base.", last)
    quality = 0
    if e200 is not None and last > e200 * 0.45:
        quality += 1
    if not (r60 is not None and r60 < -0.45):
        quality += 1
    if adv >= 25_000_000:
        quality += 1
    if quality == 0:
        return dict(_bempty("Not a going concern on this tape.", last), quality=0)
    cheap = 0
    if dd is not None and 0.18 <= dd <= 0.55:
        cheap += 2
    elif dd is not None and 0.12 <= dd <= 0.7:
        cheap += 1
    if vs200 is not None and -0.28 < vs200 < -0.03:
        cheap += 1
    if last20 is not None and last20 < -0.18:
        cheap = max(0, cheap - 1)
    impulse = 0
    if e21 is not None and e21 * 0.98 <= last <= e21 * 1.03 and vs50 is not None and vs50 < 0:
        impulse += 1
    if _ema_slope_up(closes, 21, 5) and vs50 is not None and vs50 < 0.02:
        impulse += 1
    cq = _climax_and_quiet(bars)
    sprang = _spring(bars)
    coiled = _base_contract(bars)
    lo25 = _range_low(bars, 25)
    stop = lo25 if (lo25 > 0 and lo25 < last * 0.995) else last * 0.965
    if last - stop < last * 0.02:
        stop = last * 0.97
    if last - stop > last * 0.08:
        stop = last * 0.96
    return _bfinish({"quality": min(3, quality), "cheap": min(3, cheap), "sector": 0,
                     "structure": min(2, (1 if coiled else 0) + (1 if sprang else 0)), "volume": 1 if cq["climax"] else 0,
                     "impulse": min(2, impulse), "last": last, "stop": stop, "e50": e50, "e200": e200,
                     "sprang": sprang, "coiled": coiled, "climax": cq["climax"], "quiet": cq["quiet"], "vs50": vs50,
                     "vs200": vs200, "dd": dd, "regimeHalf": bool(ctx.get("spyUnder200") and ctx.get("spyNewLow20"))})


def _bfinish(i):
    total = i["quality"] + i["cheap"] + i["sector"] + i["structure"] + i["volume"] + i["impulse"]
    turn = i["structure"] + i["volume"] + i["impulse"]
    buy = _bpx(i["last"])
    stop = _bpx(i["stop"] if (i.get("stop") and i["stop"] < i["last"]) else i["last"] * 0.965)
    if not (stop < buy):
        stop = _bpx(buy * 0.97)
    target = i["e50"] if (i["e50"] is not None and i["e50"] > buy * 1.04) else buy * 1.08
    if i["e200"] is not None and i["e200"] > target:
        target = i["e200"]
    if (target - buy) / buy < 0.06:
        target = buy * 1.08
    target = _bpx(target)
    tag = "LEAVE"
    if total >= BOTTOM_BUY and turn >= 2 and i["cheap"] >= 1 and i["quality"] >= 2:
        tag = "BUY"
    elif total >= BOTTOM_WATCH and i["quality"] >= 1:
        tag = "WAIT"
    elif i["vs50"] is not None and i["vs50"] > 0.02 and i["vs200"] is not None and i["vs200"] > 0:
        tag = "LEAVE"
    elif total >= 4:
        tag = "WAIT"
    if i["regimeHalf"] and tag == "BUY" and total < 9:
        tag = "WAIT"
    if tag == "LEAVE":
        lead = "Already through the longer average. Not a buy at this price."
    elif tag == "WAIT":
        lead = (f"Last {js_str(_bpx(i['last']))}. The range has not held yet." if not turn
                else f"Last {js_str(_bpx(i['last']))}. Wait for the range low to hold.")
    elif i["coiled"] and i["sprang"]:
        lead = "Undercut the range low and closed back in. Still under the longer average."
    elif i["climax"] and i["quiet"]:
        lead = "Heavy selling already printed. The retest is quieter. Still cheap."
    elif i["coiled"]:
        lead = "Range is tightening under the longer average."
    else:
        lead = "Sitting under the longer average after a long drop. The tape is turning."
    why = (f"q{i['quality']} c{i['cheap']} s{i['sector']} st{i['structure']} v{i['volume']} i{i['impulse']} = "
           f"{total}")
    book = "value" if (i["dd"] is not None and i["dd"] > 0.35) else ("cyclical" if i["sector"] >= 1 else "quality")
    return {"tag": tag, "live": tag == "BUY", "total": total, "quality": i["quality"], "cheap": i["cheap"],
            "sector": i["sector"], "structure": i["structure"], "volume": i["volume"], "impulse": i["impulse"],
            "lead": lead, "why": why, "buy": buy, "stop": stop, "target": target,
            "size": "Half size" if (i["regimeHalf"] or total < 10) else "Full size", "book": book}


def score_bottom_named(symbol, bars, last, ctx=None):
    ctx = ctx or {}
    s = str(symbol or "").upper()
    if s in BOTTOM_SKIP:
        return _bempty("Index or product. Not a single-name buy.", last)
    base = score_bottom(bars, last, ctx)
    if not bars or (base["quality"] == 0 and base["tag"] == "LEAVE"):
        return base
    sector = 0
    etf = sector_etf_of(s)
    spy = ctx.get("spy")
    sleeve = (ctx.get("sectors") or {}).get(etf) if etf else None
    if spy and len(spy) >= 80 and sleeve and len(sleeve) >= 80 and len(bars) >= 80:
        stock_long, spy_long = _ret(bars, 126), _ret(spy, 126)
        stock_short, spy_short = _ret(bars, 20), _ret(spy, 20)
        sleeve_long, sleeve_short = _ret(sleeve, 126), _ret(sleeve, 20)
        if stock_long is not None and spy_long is not None and stock_long - spy_long < -0.08:
            if sleeve_long is not None and spy_long is not None and sleeve_long - spy_long < -0.04:
                sector += 1
        if stock_short is not None and spy_short is not None and stock_short - spy_short > 0.01:
            if sleeve_short is not None and spy_short is not None and sleeve_short - spy_short > 0:
                sector += 1
    tape = ctx.get("tape")
    policy = name_policy(s, tape)
    if policy == "omit":
        return _bempty("Sleeve is still making relative lows.", last)
    if policy == "trend":
        return _bempty("The sleeve is already in trend. Not a bottom.", last)
    if tape and any(x["etf"] == (sector_etf_of(s) or "") and x["label"] == "turn" for x in tape["sleeves"]):
        sector = max(sector, 2)
    closes = [b["c"] for b in bars]
    e50 = L.last_ema(closes, 50)
    e200 = L.last_ema(closes, min(200, math.floor(len(bars) * 0.9)))
    cq = _climax_and_quiet(bars)
    h = _range_high(bars, min(252, len(bars)))
    hit = _bfinish({"quality": base["quality"], "cheap": base["cheap"], "sector": min(2, sector),
                    "structure": base["structure"], "volume": base["volume"], "impulse": base["impulse"], "last": last,
                    "stop": base["stop"], "e50": e50, "e200": e200,
                    "sprang": bool(re.search(r"Undercut|range low", base["lead"])) or _spring(bars),
                    "coiled": _base_contract(bars), "climax": cq["climax"], "quiet": cq["quiet"],
                    "vs50": (last - e50) / e50 if (e50 and e50 > 0) else None,
                    "vs200": (last - e200) / e200 if (e200 and e200 > 0) else None,
                    "dd": (h - last) / h if h > 0 else None,
                    "regimeHalf": bool(ctx.get("spyUnder200") and ctx.get("spyNewLow20")) or
                    bool(tape and tape.get("riskOff"))})
    funded = apply_fund_overlay(hit, (ctx.get("funds") or {}).get(s))
    if policy == "wait" and funded["tag"] == "BUY":
        return dict(funded, tag="WAIT", live=False, lead=f"Last {js_str(funded['buy'])}. Wait for the sector to turn.")
    return funded


# == buy-desk.ts =======================================================================================================
BUY_BOOK_LIMIT = DOCTRINE["bookCeiling"]
LATE_R_THRESHOLD = DOCTRINE["lateR"]
BROAD_PRODUCT = {"SPY", "QQQ", "DIA", "VOO", "IWM", "XLK", "XLF", "XLE", "XOP", "XBI", "XLB", "IYF", "IBB", "GLD",
                 "SLV", "GDX", "GDXJ", "SIL", "SILJ", "USO", "IBIT", "EWY", "SMH", "SOXX", "COPX", "PALL", "GRID",
                 "QTUM"}
KIND_FROM_LANE = [
    (re.compile(r"DEFENSE|DEMAND_DEFENSE"), "DEFENSE"),
    (re.compile(r"RECLAIM|POC_VALUE|FAILED_BEAR"), "RECLAIM"),
    (re.compile(r"RETEST|PULLBACK|PATH_RETEST|DEPARTURE"), "RETEST"),
    (re.compile(r"BREAK|ACCEPTANCE|EXPANSION|CLEARANCE|DIRECT_ACCEPT"), "BREAKOUT"),
    (re.compile(r"ABSORPTION|ORIGIN"), "PULLBACK"),
    (re.compile(r"TRANSITION|REGIME"), "ACCEPTANCE"),
]


def kind_of(ep):
    blob = f"{ep['lane']} {ep['event']} {ep['nativePhase']}".upper()
    for rx, kind in KIND_FROM_LANE:
        if rx.search(blob):
            return kind
    return "RETEST"


def _first_finite(*xs):
    for x in xs:
        if _fin(x) and x > 0:
            return x
    return None


def build_plan(ep, rail=None):
    g = ep.get("geometry") or {}
    close = float(ep["close"])
    buy = _first_finite(g.get("trigger"), g.get("zoneHigh"), close)
    if buy is None or not (buy > 0):
        buy = close if close > 0 else 1
    if rail and rail.get("sitting") and close >= buy:
        buy = close
    stop = _first_finite(g.get("invalidation"), g.get("zoneLow"))
    if stop is None or not (stop < buy):
        stop = _round_px(buy * 0.975)
    target = _first_finite(g.get("target"))
    risk = buy - stop
    if target is None or not (target > buy):
        target = _round_px(buy + 3 * max(risk, buy * 0.01))
    rr = (target - buy) / risk if risk > 0 else 2
    return {"buy": _round_px(buy), "stop": _round_px(stop), "target": _round_px(target), "rr": js_round(rr * 10) / 10}


def late_reason(ep, plan, bars=None):
    risk = plan["buy"] - plan["stop"]
    if risk <= 0:
        return None
    if (ep["close"] - plan["buy"]) / risk > LATE_R_THRESHOLD:
        return "late entry — already ran past the buy"
    return None


def _rr_label(rr):
    return f"{to_fixed(rr, 1)}R"


def headline_for(setup):
    if setup.get("eventClass"):
        return doctrine_headline(setup["eventClass"], {"tier": setup["tier"], "close": setup["close"],
                                                       "buy": setup["plan"]["buy"], "stop": setup["plan"]["stop"],
                                                       "rr": setup["plan"]["rr"]})
    rr = _rr_label(setup["plan"]["rr"])
    in_band = setup["close"] <= setup["plan"]["buy"] + 0.25 * (setup["plan"]["buy"] - setup["plan"]["stop"])
    k = setup["kind"]
    if k == "BREAKOUT":
        return (f"Tensor event buy on the latest completed bar. Wait for a dip into the buy band. {rr} plan, full "
                f"attention.") if in_band else f"Tensor event buy on the latest completed bar. {rr} plan, full attention."
    if k == "RETEST":
        return "Holding the 50-day or 200-day after the breakout. That is the add." if setup["tier"] == "S" \
            else "Rail retest with the higher-timeframe ribbon still constructive. Levels are live at the mark."
    if k == "RECLAIM":
        return "Holding the backtest of the breakout. Close enough to work a limit."
    if k == "DEFENSE":
        return "Demand still lives at the mark. Sized up only inside the zone."
    if k == "PULLBACK":
        return f"Controlled pullback into the ribbon. {rr} if it works."
    if k == "ACCEPTANCE":
        return f"Acceptance beat rejection on the completed bar. {rr} plan."
    return None


def _decorate(setup):
    setup["headline"] = headline_for(setup)
    return setup


def setup_from_bottom(symbol, bars, hit, now):
    last = _num_or0(bars[-1]["c"]) if bars else 0
    if not last:
        last = hit["buy"]
    t = L.admit_ticker(symbol, bars, last, now)
    buy = t["buy"] if t["buy"] is not None else hit["buy"]
    stop = t["stop"] if t["stop"] is not None else hit["stop"]
    target = t["target"] if t["target"] is not None else hit["target"]
    risk = max(buy - stop, buy * 0.02)
    rr = js_round(((target - buy) / risk) * 10) / 10
    return _decorate({
        "id": f"bottom-{symbol}", "symbol": symbol,
        "tier": "A" if t["size"] == "Half size" else ("S" if hit["size"] == "Full size" else "A"),
        "kind": "RETEST", "plan": {"buy": _round_px(buy), "stop": _round_px(stop), "target": _round_px(target), "rr": rr},
        "close": _round_px(last), "size": t["size"] if t["live"] else hit["size"], "headline": "",
        "scanners": ["Bottom"], "lanes": [hit["book"]], "antiChase": True,
        "completedBarAt": (bars[-1]["t"] if bars else None) or now, "note": t["why"], "eventClass": "RETEST",
        "primaryScanner": "Bottom", "supporting": [], "disagreement": [], "locationWhy": t["why"],
        "invalidateIf": invalidate_line(stop), "extensionR": 0, "lifecycle": "READY" if t["live"] else "PREVIEW",
        "curlOk": t["macdUp"] is not False, "coilOk": hit["structure"] >= 2, "atSupport": t["onShelf"]})


def bottom_ctx_from(bars_by, funds, now):
    spy = bars_by.get("SPY") if bars_by is not None else None
    sectors = {}
    if bars_by is not None:
        for etf in SECTOR_ETFS:
            b = bars_by.get(etf)
            if b:
                sectors[etf] = b
    spy_under200 = False
    spy_new_low20 = False
    if spy and len(spy) >= 80:
        last = _num_or0(spy[-1]["c"])
        e200 = L.last_ema([b["c"] for b in spy], min(200, len(spy) - 1))
        spy_under200 = e200 is not None and last < e200
        lo20 = _jmin(b["l"] for b in spy[-20:])
        lo_prev = _jmin(b["l"] for b in spy[-40:-20])
        spy_new_low20 = lo20 < lo_prev
    tape = read_sector_tape(bars_by, now) if bars_by is not None else None
    return {"spy": spy, "sectors": sectors, "spyUnder200": spy_under200, "spyNewLow20": spy_new_low20, "tape": tape,
            "funds": funds}


def merge_bottom_book(buys, rejected, bars_by, funds, now, ctx=None):
    if bars_by is None:
        return {"buys": buys, "rejected": rejected}
    ctx = ctx or bottom_ctx_from(bars_by, funds, now)
    have = {b["symbol"] for b in buys}
    extra = []
    for symbol, bars in bars_by.items():
        if symbol in have or symbol in BROAD_PRODUCT:
            continue
        last = _num_or0(bars[-1]["c"]) if bars else 0
        hit = score_bottom_named(symbol, bars, last, ctx)
        if hit["tag"] != "BUY":
            continue
        t = L.admit_ticker(symbol, bars, last, now)
        if t["tag"] != "BUY" or not t["live"]:
            continue
        extra.append(setup_from_bottom(symbol, bars, hit, now))
        have.add(symbol)
    extra = sorted(extra, key=cmp_to_key(lambda a, b: _num_sign(b["plan"]["rr"] - a["plan"]["rr"]) or
                                         _locale_cmp(a["symbol"], b["symbol"])))
    return {"buys": buys + extra, "rejected": rejected}


def _num_sign(x):
    if x != x:
        return 0
    return (x > 0) - (x < 0)


def _hold(row, status, reason, ep=None):
    out = {"symbol": row["symbol"], "reason": reason, "close": ep["close"] if ep is not None else row["close"],
           "status": status}
    if ep is not None:
        out["scanner"] = ep["publicName"]
        out["eventClass"] = event_class_of(ep)
    return {"kind": "hold", "row": out}


def _unique_episodes(eps):
    seen, out = set(), []
    for e in eps:
        key = f"{e['scannerId']}:{e['lane']}:{e['event']}"
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def classify_row(row, bars, now):
    if row["coverage"] == "quarantined":
        return _hold(row, "QUARANTINED", row.get("reason") if row.get("reason") is not None else "quarantined")
    if row["coverage"] != "usable":
        return _hold(row, "UNAVAILABLE", row.get("reason") if row.get("reason") is not None else "unavailable")
    if not row["episodes"]:
        return _hold(row, "WAIT", "no native event")
    graded = [e for e in row["episodes"] if e["grade"] in ("S", "A")]
    defense = [e for e in row["episodes"] if is_first_defense(e, bars)]
    live = _unique_episodes(graded + defense)
    if not live:
        best = row["episodes"][0]
        if developing_phase(best["phase"]):
            return _hold(row, "DEVELOPING", "transition not complete", best)
        if dead_phase(best["phase"]):
            return _hold(row, "AVOID", "event failed or expired", best)
        return _hold(row, "WAIT", "no S/A native event", best)
    primary = pick_primary(live)
    first = is_first_defense(primary, bars)
    floor = structural_floor(bars, primary["close"])
    contradiction = hard_contradiction(primary)
    if contradiction:
        return _hold(row, "AVOID", contradiction, primary)
    if developing_phase(primary["phase"]) and not first:
        return _hold(row, "DEVELOPING", "location is real, confirmation has not completed", primary)
    if dead_phase(primary["phase"]) or (exhausted_native(primary) and not floor):
        return _hold(row, "AVOID", "native event is depleting or expired", primary)
    klass = event_class_of(primary)
    rail = rail_state(bars, primary["close"])
    plan = build_plan(primary, rail)
    at_support = (rail["sitting"] and klass in ("RETEST", "BOUNCE")) or first
    stacked = False
    sel_buy = None
    sel_size = "starter"
    if bars and len(bars) >= 20:
        sel = read_select(bars, primary["close"], now)
        if sel["verdict"] == "LATE":
            return _hold(row, "LATE", sel["why"], primary)
        if sel["verdict"] == "WAIT":
            return _hold(row, "WAIT", sel["why"], primary)
        if not sel["washout"] and not sel["coil"]:
            curl_early = read_curl(bars) if len(bars) >= 40 else None
            bottom = score_bottom_named(row["symbol"], bars, primary["close"])
            if bottom["tag"] == "BUY":
                at_support = True
                sel_buy = bottom["buy"]
                sel_size = "heavy" if bottom["size"] == "Full size" else "starter"
                plan = {"buy": _round_px(bottom["buy"]), "stop": _round_px(bottom["stop"]),
                        "target": _round_px(bottom["target"]),
                        "rr": js_round(((bottom["target"] - bottom["buy"]) /
                                        max(bottom["buy"] - bottom["stop"], bottom["buy"] * 0.02)) * 10) / 10}
            elif not (curl_early and curl_early["ok"]):
                wash = L.read_washout(bars, primary["close"], now)
                return _hold(row, "WAIT", wash["why"] or "not a washout under the 50-day", primary)
        at_support = sel["onLevel"] or at_support
        stacked = sel["stacked"] is True
        if sel_buy is None:
            sel_buy = sel["buy"]
            sel_size = sel["size"]
        if sel_buy is not None and sel_buy > 0:
            buy = _round_px(sel_buy)
            stop = plan["stop"]
            if not (stop < buy):
                stop = _round_px(buy * 0.975)
            risk = buy - stop
            rr = (plan["target"] - buy) / risk if risk > 0 else plan["rr"]
            plan = dict(plan, buy=buy, stop=stop, rr=js_round(rr * 10) / 10)
    else:
        blocked = blocking_missing(primary)
        if blocked:
            return _hold(row, "WAIT", f"native proof missing — {blocked}", primary)
        late = late_reason(primary, plan, bars)
        if late:
            return _hold(row, "LATE", late, primary)
        chase = chase_tape(primary, plan, bars)
        chase_why = chase_reject(chase)
        if chase_why:
            return _hold(row, "LATE", chase_why, primary)
        bounce = ran_off_low(bars, primary["close"])
        if bounce:
            return _hold(row, "LATE", bounce, primary)
        curl = read_curl(bars) if (bars and len(bars) >= 40) else None
        if curl and curl["extended"] and not at_support:
            return _hold(row, "LATE", curl["why"], primary)
        if not primary["antiChase"] and not at_support:
            return _hold(row, "WAIT", "anti-chase not cleared", primary)
    curl = read_curl(bars) if (bars and len(bars) >= 40) else None
    coil = L.read_coil(bars, primary["close"], now) if (bars and len(bars) >= 60) else None
    chase = chase_tape(primary, plan, bars)
    proven = [e for e in live if e["phase"] == "ACTIVE" and not e["missing"]]
    scanners = _unique([e["publicName"] for e in (proven or [primary])])
    lanes = _unique([e["lane"] for e in (proven or [primary])])
    heavy = sel_size == "heavy" or stacked or (coil is not None and coil["ok"] is True)
    tier = "S" if ((coil and coil["ok"]) or (heavy and primary["phase"] == "ACTIVE")) else "A"
    loc_tail = coil["why"] if (coil and coil["ok"]) else (curl_note(curl) if (curl and curl["ok"]) else "")
    setup = _decorate({
        "id": f"{row['symbol']}-{primary['scannerId']}-{js_str(primary['completedBarAt'])}", "symbol": row["symbol"],
        "tier": tier, "kind": kind_of(primary), "plan": plan, "close": _round_px(primary["close"]),
        "size": "Full size" if heavy else "Half size", "headline": "", "scanners": scanners, "lanes": lanes,
        "antiChase": primary["antiChase"], "completedBarAt": primary["completedBarAt"], "note": primary["note"],
        "eventClass": klass, "primaryScanner": primary["publicName"], "supporting": supporting_of(live, primary),
        "disagreement": disagreement_of(row),
        "locationWhy": " ".join(x for x in (location_why(primary), loc_tail) if x),
        "invalidateIf": invalidate_line(plan["stop"]), "extensionR": js_round(chase["extensionR"] * 100) / 100,
        "lifecycle": f"{primary['phase']} · {primary['nativePhase']}",
        "curlOk": (curl is not None and curl["ok"] is True) or (coil is not None and coil["ok"] is True),
        "curlNote": curl_note(curl) if curl else None, "coilOk": coil is not None and coil["ok"] is True,
        "atSupport": at_support})
    return {"kind": "buy", "setup": setup}


def _rail_quality(s):
    if s["eventClass"] in ("DIVERGENCE", "SWEEP", "ABSORPTION") and "ACTIVE" in s["lifecycle"]:
        return 0
    if s["eventClass"] == "RETEST":
        return 1
    if s["eventClass"] == "BOUNCE" and "FORMING" in s["lifecycle"]:
        return 1
    if s["primaryScanner"] in ("Zenith", "Reverb"):
        return 2
    if s["eventClass"] == "BOUNCE" and "READY" in s["lifecycle"]:
        return 5
    return 3


def _rank_setups(a, b):
    if a["tier"] != b["tier"]:
        return -1 if a["tier"] == "S" else 1
    if bool(a.get("curlOk")) != bool(b.get("curlOk")):
        return -1 if a.get("curlOk") else 1
    ra, rb = _rail_quality(a), _rail_quality(b)
    if ra != rb:
        return ra - rb

    def fav(s):
        return 0 if s == "Zenith" else 1 if s == "Reverb" else 2
    if fav(a["primaryScanner"]) != fav(b["primaryScanner"]):
        return fav(a["primaryScanner"]) - fav(b["primaryScanner"])
    aa = 0 if "ACTIVE" in a["lifecycle"] else 1
    ab = 0 if "ACTIVE" in b["lifecycle"] else 1
    if aa != ab:
        return aa - ab
    if a["antiChase"] != b["antiChase"]:
        return -1 if a["antiChase"] else 1
    if len(a["supporting"]) != len(b["supporting"]):
        return len(b["supporting"]) - len(a["supporting"])
    ea = 1 if a["symbol"] in BROAD_PRODUCT else 0
    eb = 1 if b["symbol"] in BROAD_PRODUCT else 0
    if ea != eb:
        return ea - eb
    pocket = abs(a["extensionR"]) - abs(b["extensionR"])
    if abs(pocket) > 0.02:
        return pocket
    if b["plan"]["rr"] != a["plan"]["rr"]:
        return b["plan"]["rr"] - a["plan"]["rr"]
    return _locale_cmp(a["symbol"], b["symbol"])


def _cmp_sign(f):
    return lambda a, b: _num_sign(f(a, b))


def distill_buys(rows, bars_by, funds, now):
    """distillBuys(rows, barsBySymbol, funds) with the source's clock `now` (epoch ms)."""
    rejected = []
    candidates = []
    ctx = bottom_ctx_from(bars_by, funds, now)
    for row in rows:
        pol = name_policy(row["symbol"], ctx["tape"])
        if pol in ("omit", "trend"):
            rejected.append({"symbol": row["symbol"], "reason": "sleeve is still making relative lows" if pol == "omit"
                             else "sleeve is already in trend", "close": row["close"], "status": "WAIT"})
            continue
        hit = classify_row(row, (bars_by or {}).get(row["symbol"]), now)
        if hit["kind"] == "buy":
            if pol == "wait":
                s = hit["setup"]
                rejected.append({"symbol": row["symbol"], "reason": "sleeve has not turned", "close": s["close"],
                                 "status": "WAIT", "scanner": s["primaryScanner"], "eventClass": s["eventClass"]})
                continue
            candidates.append(hit["setup"])
        else:
            rejected.append(hit["row"])
    candidates = sorted(candidates, key=cmp_to_key(_cmp_sign(_rank_setups)))
    merged = merge_bottom_book(candidates, rejected, bars_by, funds, now, ctx)
    admitted = []
    for b in merged["buys"]:
        bars = (bars_by or {}).get(b["symbol"])
        last = b["close"] or (bars[-1]["c"] if bars else 0) or 0
        t = L.admit_ticker(b["symbol"], bars, last, now)
        if t["tag"] != "BUY" or not t["live"] or t["buy"] is None or t["stop"] is None or t["target"] is None:
            rejected.append({"symbol": b["symbol"], "reason": t["why"], "close": last,
                             "status": "LATE" if t["tag"] == "LEAVE" else "WAIT", "scanner": b["primaryScanner"],
                             "eventClass": b["eventClass"]})
            continue
        risk = max(t["buy"] - t["stop"], t["buy"] * 0.01)
        admitted.append(dict(b, close=last, plan={"buy": t["buy"], "stop": t["stop"], "target": t["target"],
                                                  "rr": js_round(((t["target"] - t["buy"]) / risk) * 10) / 10},
                             locationWhy=t["why"], antiChase=True, atSupport=True, curlOk=t["macdUp"] is not False))
    buys = admitted[:BUY_BOOK_LIMIT]
    for c in admitted[BUY_BOOK_LIMIT:]:
        rejected.append({"symbol": c["symbol"], "reason": "outside today's book ceiling", "close": c["close"],
                         "status": "CUT", "scanner": c["primaryScanner"], "eventClass": c["eventClass"]})
    return {"buys": buys, "rejected": rejected, "scanned": len(rows),
            "usable": len([r for r in rows if r["coverage"] == "usable"])}


def distill_bottom(bars_by, funds, now):
    """the bottom screen's own book: mergeBottomBook's names (scoreBottomNamed BUY + admitTicker BUY live ->
    setupFromBottom, ranked by R then symbol) through distillBuys' admission pass and book ceiling — the bottom lane as
    distillBuys routes it, without the Prism candidates in front of it."""
    merged = merge_bottom_book([], [], bars_by, funds, now)
    admitted, rejected = [], []
    for b in merged["buys"]:
        bars = (bars_by or {}).get(b["symbol"])
        last = b["close"] or (bars[-1]["c"] if bars else 0) or 0
        t = L.admit_ticker(b["symbol"], bars, last, now)
        if t["tag"] != "BUY" or not t["live"] or t["buy"] is None or t["stop"] is None or t["target"] is None:
            rejected.append({"symbol": b["symbol"], "reason": t["why"], "close": last,
                             "status": "LATE" if t["tag"] == "LEAVE" else "WAIT", "scanner": b["primaryScanner"],
                             "eventClass": b["eventClass"]})
            continue
        risk = max(t["buy"] - t["stop"], t["buy"] * 0.01)
        admitted.append(dict(b, close=last, plan={"buy": t["buy"], "stop": t["stop"], "target": t["target"],
                                                  "rr": js_round(((t["target"] - t["buy"]) / risk) * 10) / 10},
                             locationWhy=t["why"], antiChase=True, atSupport=True, curlOk=t["macdUp"] is not False))
    for c in admitted[BUY_BOOK_LIMIT:]:
        rejected.append({"symbol": c["symbol"], "reason": "outside today's book ceiling", "close": c["close"],
                         "status": "CUT", "scanner": c["primaryScanner"], "eventClass": c["eventClass"]})
    return {"buys": admitted[:BUY_BOOK_LIMIT], "rejected": rejected}


# == desk-book.ts setupFromRoster / bookFromRoster =====================================================================
def setup_from_roster(m, now):
    buy, stop, target = _num0(m.get("buy")), _num0(m.get("stop")), _num0(m.get("target"))
    rr = _num0(m.get("rr")) or 0
    booked = _parse_iso_ms(m.get("lastBookedAt"))
    return {"id": f"roster-{m['symbol']}", "symbol": m["symbol"], "tier": "S" if m.get("call") == "BUY" else "A",
            "kind": "RETEST", "plan": {"buy": buy, "stop": stop, "target": target, "rr": rr},
            "close": _num0(m.get("lastClose")) or buy, "size": "Full size" if m.get("call") == "BUY" else "Half size",
            "headline": "Held from the last booked card.", "scanners": [m.get("scanner") or "Desk"], "lanes": [],
            "antiChase": True, "completedBarAt": booked or now, "note": "Overnight book.", "eventClass": "RETEST",
            "primaryScanner": m.get("scanner") or "Desk", "supporting": [], "disagreement": [], "locationWhy": "",
            "invalidateIf": "", "extensionR": 0, "lifecycle": "READY"}


def book_from_roster(roster, now):
    return [setup_from_roster(m, now) for m in ((roster or {}).get("members") or [])
            if m.get("status") == "LIVE" and m.get("buy", 0) > m.get("stop", 0) and m.get("target", 0) > m.get("buy", 0)]


# == copy.ts buyCall / callRank; desk-autopilot.mjs book assembly ======================================================
PAPER_CALL = {"SPY", "QQQ", "DIA", "VOO", "IWM", "XLK", "XLF", "XLE", "XOP", "XBI", "XLB", "IYF", "IBB", "GLD", "SLV",
              "GDX", "GDXJ", "SIL", "SILJ", "USO", "IBIT", "EWY", "SMH", "SOXX", "COPX", "PALL", "GRID", "QTUM"}


def buy_call(s):
    if s["symbol"] in PAPER_CALL:
        return "PAPER"
    if s.get("coilOk") or s.get("tier") == "S":
        return "BUY"
    if not s.get("atSupport") and not s.get("antiChase"):
        return "HALF"
    if s.get("size") == "Full size":
        return "BUY"
    if s.get("eventClass") == "BOUNCE" and "FORMING" in str(s.get("lifecycle")):
        return "HALF"
    if s.get("eventClass") == "DIVERGENCE" and "ACTIVE" in str(s.get("lifecycle")):
        return "BUY"
    if s.get("eventClass") == "RETEST" and s.get("atSupport"):
        return "BUY"
    return "HALF"


def call_rank(call):
    return 0 if call == "BUY" else 1 if call == "HALF" else 2


def order_book(buys):
    return sorted(buys, key=lambda s: call_rank(buy_call(s)))


def filter_book_for_curl(book, bars_by):
    kept = []
    for setup in book:
        gate = keep_after_curl(setup, (bars_by or {}).get(setup["symbol"]))
        if not gate["keep"]:
            continue
        if gate["read"] and gate["read"]["ok"]:
            kept.append(dict(setup, curlOk=True, curlNote=curl_note(gate["read"])))
        else:
            kept.append(setup)
    return kept


def keep_near_buy(setups):
    out = []
    for s in setups:
        ah = s.get("afterHours") or {}
        last = ah.get("last") if ah.get("last") is not None else s.get("close")
        plan = s.get("plan") or {}
        buy, stop, tgt = _num_or0(plan.get("buy")), _num_or0(plan.get("stop")), _num_or0(plan.get("target"))
        if last is not None and stop > 0 and last <= stop:
            continue
        if last is not None and tgt > 0 and last >= tgt * 0.99:
            continue
        if last is not None and buy > 0 and last > buy * 1.03:
            continue
        out.append(s)
    return out


# == after-hours.ts ====================================================================================================
THROUGH_PCT = 0.03
STOP_MIN_PCT = 0.025
STOP_MAX_PCT = 0.035
DAY_MS = 86_400_000


def already_through(last, buy):
    return last > 0 and buy > 0 and (last - buy) / buy > THROUGH_PCT


def last_friday_ymd(now):
    t = now
    for _ in range(8):
        e = T.et_parts(t)
        if e["dow"] == 5:
            return e["ymd"]
        t -= DAY_MS
    return T.et_parts(now)["ymd"]


def last_regular_ymd(now):
    p = T.et_parts(now)
    hm = p["hour"] * 60 + p["minute"]
    t = now
    if p["dow"] in (0, 6) or hm < 16 * 60:
        t = now - 20 * 60 * 60 * 1000
    for _ in range(8):
        e = T.et_parts(t)
        if 1 <= e["dow"] <= 5:
            return e["ymd"]
        t -= DAY_MS
    return p["ymd"]


def today_ymd(now):
    return T.et_parts(now)["ymd"]


def session_tape(bars, now):
    session_ymd = last_regular_ymd(now)
    today = today_ymd(now)
    empty = {"sessionYmd": session_ymd, "regularClose": None, "ahLast": None, "preLast": None, "last": None,
             "high": None, "low": None, "at": None, "nAh": 0, "nPre": 0}
    if not bars:
        return empty
    regular_close = None
    post, pre = [], []
    today_reg = None
    for b in bars:
        if not _fin(b["c"]):
            continue
        e = T.et_parts(b["t"])
        hm = e["hour"] * 60 + e["minute"]
        if e["ymd"] == session_ymd:
            if 9 * 60 + 30 <= hm < 16 * 60:
                regular_close = b["c"]
            if 16 * 60 <= hm < 20 * 60 + 1:
                post.append(b)
        if e["ymd"] == today and 1 <= e["dow"] <= 5:
            if 4 * 60 <= hm < 9 * 60 + 30:
                pre.append(b)
            if 9 * 60 + 30 <= hm < 16 * 60:
                today_reg = b
    ah_last = post[-1] if post else None
    pre_last = pre[-1] if pre else None
    tail = today_reg or pre_last or ah_last
    range_bars = post + pre + ([today_reg] if today_reg else [])
    highs = [b["h"] for b in range_bars if _fin(b["h"])]
    lows = [b["l"] for b in range_bars if _fin(b["l"])]
    return {"sessionYmd": session_ymd, "regularClose": regular_close,
            "ahLast": ah_last["c"] if ah_last else None, "preLast": pre_last["c"] if pre_last else None,
            "last": tail["c"] if tail else None,
            "high": max(highs) if highs else (tail["h"] if tail else None),
            "low": min(lows) if lows else (tail["l"] if tail else None),
            "at": tail["t"] if tail else None, "nAh": len(post), "nPre": len(pre)}


def _ah_px(n):
    if n >= 100:
        return js_str(js_round(n * 100) / 100)
    if n >= 1:
        return to_fixed(js_round(n * 100) / 100, 2)
    return js_str(js_round(n * 1000) / 1000)


def _session_word(ymd, now):
    today = today_ymd(now)
    if ymd == last_friday_ymd(now) and today != ymd:
        return "Friday"
    if ymd == today:
        return "today"
    return "yesterday"


def tape_note(tape, now):
    bits = []
    day = _session_word(tape["sessionYmd"], now)
    if tape["regularClose"] is not None and tape["ahLast"] is not None:
        if abs(tape["ahLast"] - tape["regularClose"]) / tape["regularClose"] < 0.005:
            bits.append(f"{day} after-hours held {_ah_px(tape['ahLast'])}")
        else:
            d = "up" if tape["ahLast"] > tape["regularClose"] else "down"
            bits.append(f"{day} regular {_ah_px(tape['regularClose'])}, after-hours {d} to {_ah_px(tape['ahLast'])}")
    elif tape["ahLast"] is not None:
        bits.append(f"{day} after-hours {_ah_px(tape['ahLast'])}")
    if tape["preLast"] is not None:
        bits.append(f"premarket {_ah_px(tape['preLast'])}")
    return ", ".join(bits)


def _decide(setup, last, regular, note, stamp):
    nxt = dict(setup, afterHours=stamp if stamp is not None else setup.get("afterHours"))
    if last is None:
        return {"keep": True, "why": "no session tape after the regular close", "setup": nxt}
    buy = _num_or0((setup.get("plan") or {}).get("buy"))
    base = regular if regular is not None else _num_or0(setup.get("close"))
    thru = already_through(last, buy)
    pop = (last - base) / base if base > 0 else 0
    if thru:
        return {"keep": False, "why": f"{note or 'session tape'} already through the {_ah_px(buy)} buy", "setup": nxt}
    if pop >= 0.05 and buy > 0 and last >= buy * 0.97:
        return {"keep": False, "why": f"session tape ran {to_fixed(pop * 100, 1)}% into the buy", "setup": nxt}
    if setup.get("antiChase") and pop >= 0.03:
        nxt["antiChase"] = False
    return {"keep": True, "why": note or "session tape inside the plan", "setup": nxt}


def apply_session_tape(setup, tape, now, daily=None):
    note = tape_note(tape, now)
    stamp = ({"last": tape["last"], "regularClose": tape["regularClose"], "high": tape["high"], "note": note}
             if tape["last"] is not None else setup.get("afterHours"))
    first = _decide(setup, tape["last"], tape["regularClose"], note, stamp)
    if not first["keep"]:
        return first
    return rebase_plan(first["setup"], tape, now, daily)


def _atr14_ah(bars):
    if not bars or len(bars) < 16:
        return None
    acc, n = 0.0, 0
    for i in range(max(1, len(bars) - 15), len(bars)):
        prev = bars[i - 1]["c"]
        tr = max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - prev), abs(bars[i]["l"] - prev))
        if math.isfinite(tr):
            acc += tr
            n += 1
    return acc / n if n else None


def _swing_low(bars, n=12):
    if not bars:
        return None
    lows = [b["l"] for b in bars[-n:] if _fin(b["l"])]
    return min(lows) if lows else None


def aggressive_target(bars, buy, risk):
    if not (buy > 0) or not (risk > 0):
        return None
    floor = buy + 2.5 * risk
    three = buy + 3 * risk
    cap = buy + 5 * risk
    if not bars:
        return three
    win = bars[-90:]
    highs = [b["h"] for b in win if _fin(b["h"]) and b["h"] > buy]
    if not highs:
        return three
    peaks = []
    for i in range(2, len(win) - 2):
        h = win[i]["h"]
        if h >= win[i - 1]["h"] and h >= win[i - 2]["h"] and h >= win[i + 1]["h"] and h >= win[i + 2]["h"] and h > buy:
            peaks.append(h)
    hi = max(highs)
    pool = peaks + [hi]
    in_cap = [h for h in pool if h <= cap * 1.01]
    strong = [h for h in in_cap if h >= floor]
    if strong:
        return min(max(strong), cap)
    if in_cap:
        return min(max(in_cap), cap)
    if hi >= floor:
        return cap
    if hi > buy:
        return min(hi, cap)
    return min(three, hi * 1.02)


def live_stop(buy, daily=None):
    if not (buy > 0):
        return 0
    atr = _atr14_ah(daily)
    floor = _swing_low(daily, 12)
    min_room = buy * (1 - STOP_MIN_PCT)
    max_room = buy * (1 - STOP_MAX_PCT)
    if floor is not None and floor < buy:
        under = floor - 0.35 * atr if atr is not None else floor * 0.994
    else:
        under = min_room
    stop = under
    if stop > min_room:
        stop = min_room
    if stop < max_room:
        stop = max_room
    if not (stop < buy):
        stop = min_room
    return stop


def rebase_plan(setup, tape, now, daily=None):
    ah = setup.get("afterHours") or {}
    last = tape["last"]
    if last is None:
        last = ah.get("last") if ah.get("last") is not None else setup.get("close")
    prev = setup["plan"]
    buy, stop, target = _num_or0(prev["buy"]), _num_or0(prev["stop"]), _num_or0(prev["target"])
    note = ah.get("note") or tape_note(tape, now)
    if not (last is not None and last > 0) or not (buy > 0):
        return {"keep": True, "why": note, "setup": setup}
    if last <= stop:
        return {"keep": False, "why": f"last print {_ah_px(last)} already through the {_ah_px(stop)} stop",
                "setup": setup}
    bounce = ran_off_low(daily, last)
    if bounce:
        return {"keep": False, "why": bounce, "setup": setup}
    if target > buy and last >= target * 0.99:
        return {"keep": False, "why": f"last print {_ah_px(last)} already at the {_ah_px(target)} target",
                "setup": setup}
    if last < buy * 0.97:
        buy = last
    if not (stop < buy) or not (stop < last) or last - stop < buy * STOP_MIN_PCT * 0.8:
        stop = live_stop(min(buy, last), daily)
    if not (stop < buy) or not (stop < last):
        stop = min(buy, last) * 0.985
    risk = buy - stop
    if not (risk > 0):
        return {"keep": False, "why": "cannot form a stop under the last print", "setup": setup}
    far = P.wave3_target(daily, buy, risk)
    if not truthy(far):
        far = aggressive_target(daily, buy, risk)
    hi90 = _jmax(b["h"] for b in daily[-90:] if _fin(b["h"])) if daily else None
    if far is not None:
        target = far
    elif not (target > buy) or (target - buy) / risk < 2.5:
        target = buy + 3 * risk
    if (target - buy) / risk > 5.05:
        target = buy + 5 * risk
    if hi90 is not None and target > hi90 * 1.02:
        target = hi90
    rr = js_round(((target - buy) / risk) * 10) / 10
    if not (target > buy) or not (buy > stop):
        return {"keep": False, "why": "plan is not a buy after the last print", "setup": setup}
    return {"keep": True, "why": note or "rebasing plan to last print",
            "setup": dict(setup, close=last, plan={"buy": float(_ah_px(buy)), "stop": float(_ah_px(stop)),
                                                   "target": float(_ah_px(target)), "rr": rr})}


def live_accurate_plan(setup, last, now, daily=None):
    ah = setup.get("afterHours") or {}
    px_last = _num_or0(last or ah.get("last") or setup.get("close") or setup["plan"]["buy"])
    if not (px_last > 0):
        return setup
    t = L.admit_ticker(setup["symbol"], daily, px_last, now)
    if t["tag"] != "BUY" or not t["live"] or t["buy"] is None or t["stop"] is None or t["target"] is None:
        return dict(setup, close=px_last, afterHours=dict(ah, last=px_last, note=t["why"]), atSupport=False,
                    locationWhy=t["why"])
    risk = max(t["buy"] - t["stop"], t["buy"] * 0.01)
    rr = js_round(((t["target"] - t["buy"]) / risk) * 10) / 10
    return dict(setup, close=px_last, afterHours=dict(ah, last=px_last),
                plan=dict(setup["plan"], buy=t["buy"], stop=t["stop"], target=t["target"], rr=rr), atSupport=True,
                locationWhy=t["why"], antiChase=True)


# == roster.ts =========================================================================================================
ROSTER_CAP = 24
ROSTER_TTL_DAYS = 5


def empty_roster(date_et):
    return {"dateEt": date_et, "members": [], "addedToday": [], "kept": [], "droppedToday": []}


def live_symbols(state):
    return [m["symbol"] for m in state["members"] if m["status"] == "LIVE"]


def date_et_of(iso):
    ms = _parse_iso_ms(iso)
    if ms is None:
        return str(iso)[:10]
    return T.et_parts(ms)["ymd"]


def trading_days_between(from_iso, to_iso):
    a, b = date_et_of(from_iso), date_et_of(to_iso)
    if b <= a:
        return 0
    da, db = date.fromisoformat(a), date.fromisoformat(b)
    n = 0
    d = da + timedelta(days=1)
    while d <= db:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def normalize_member(m, now):
    at = _iso(now)
    close = _num0(m.get("lastClose") if m.get("lastClose") is not None else m.get("buy"))
    entry_high = _num0(m.get("entryHigh")) if m.get("entryHigh") is not None else max(close, _num0(m.get("buy")))
    added = m.get("addedAt") if m.get("addedAt") is not None else at
    return {"symbol": m["symbol"], "addedAt": added,
            "lastBookedAt": m.get("lastBookedAt") if m.get("lastBookedAt") is not None else added,
            "buy": _num0(m.get("buy")), "stop": _num0(m.get("stop")), "target": _num0(m.get("target")),
            "rr": _num0(m.get("rr")), "call": m.get("call") if m.get("call") is not None else "BUY",
            "scanner": m.get("scanner") if m.get("scanner") is not None else "", "lastClose": close,
            "lastMarkedAt": m.get("lastMarkedAt") if m.get("lastMarkedAt") is not None else added,
            "lastTensorBuyAt": m.get("lastTensorBuyAt"), "held": bool(m.get("held")),
            "status": "DROPPED" if m.get("status") == "DROPPED" else "LIVE", "dropReason": m.get("dropReason"),
            "entryHigh": entry_high,
            "lastHigh": _num0(m.get("lastHigh")) if m.get("lastHigh") is not None else entry_high,
            "sessionMarks": list(m.get("sessionMarks")) if isinstance(m.get("sessionMarks"), list) else [],
            "demoted": bool(m.get("demoted")), "weakFlags": _num0(m.get("weakFlags") or 0),
            "clusterTight": bool(m.get("clusterTight"))}


def _num0(v):
    """Number(v ?? 0) for roster fields (undefined -> 0)."""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def evict_reason(m, quote, now, booked_today, median_ret=None):
    row = normalize_member(m, now)
    px = quote if quote is not None else row["lastClose"]
    now_iso = _iso(now)
    if row["held"]:
        if px > 0 and row["stop"] > 0 and px <= row["stop"]:
            return "STOP"
        if px > 0 and row["target"] > 0 and px >= row["target"]:
            return "TARGET"
        return None
    if px > 0 and row["stop"] > 0 and px <= row["stop"]:
        return "STOP" if quote is not None else "STRUCTURE_BREAK"
    if px > 0 and row["target"] > 0 and px >= row["target"]:
        return "TARGET"
    reaffirm = row["lastTensorBuyAt"] or row["lastBookedAt"] or row["addedAt"]
    since_reaffirm = trading_days_between(reaffirm, now_iso)
    days_on = trading_days_between(row["addedAt"], now_iso)
    sessions = max(days_on, len(row["sessionMarks"]))
    progress_days = 2 if row["clusterTight"] else 3
    risk = row["buy"] - row["stop"]
    no_higher_high = px > 0 and row["lastHigh"] <= row["entryHigh"] * 1.001
    against = risk > 0 and px > 0 and row["buy"] - px >= 1.5 * risk
    if not booked_today:
        if since_reaffirm >= ROSTER_TTL_DAYS and days_on >= ROSTER_TTL_DAYS:
            return "TTL"
        if sessions >= progress_days and no_higher_high and (against or px <= row["buy"]):
            code = "CLUSTER_CUT" if row["clusterTight"] else "NO_PROGRESS"
            return code if row["demoted"] else "DEMOTE"
        if median_ret is not None and len(row["sessionMarks"]) >= 3:
            first = row["entryHigh"] or row["buy"]
            ret = (px - first) / first if (first > 0 and px > 0) else 0
            if ret < median_ret:
                return "REL_WEAK"
    return None


def _roster_rank(m, booked_today, now):
    s = 0
    if m["held"]:
        s += 80
    if booked_today:
        s += 40
    if m["call"] == "BUY":
        s += 12
    elif m["call"] == "HALF":
        s += 6
    if m["lastTensorBuyAt"]:
        s += 8
    if m["demoted"]:
        s -= 8
    added = _parse_iso_ms(m["addedAt"])
    age = (now - added) / 86400000 if added is not None else float("nan")
    s += max(0, 6 - age) if age == age else float("nan")
    return s


def _stamp_session(prev, date_et):
    if not date_et:
        return prev
    if date_et in prev:
        return prev
    return (list(prev) + [date_et])[-8:]


def curate_roster(prev, book, quotes, date_et, now, protect=()):
    at = _iso(now)
    booked = {b["symbol"]: b for b in book}
    by_sym = {}
    for m in prev["members"]:
        by_sym[m["symbol"]] = normalize_member(m, now)
    added_today = list(prev["addedToday"]) if date_et == prev["dateEt"] else []
    dropped_today = list(prev["droppedToday"]) if date_et == prev["dateEt"] else []
    for b in book:
        existing = by_sym.get(b["symbol"])
        px = quotes.get(b["symbol"]) if b["symbol"] in quotes else b["close"]
        if existing is None or existing["status"] == "DROPPED":
            if b["symbol"] not in added_today:
                added_today.append(b["symbol"])
            by_sym[b["symbol"]] = normalize_member({
                "symbol": b["symbol"], "addedAt": existing["addedAt"] if existing else at, "lastBookedAt": at,
                "buy": b["buy"], "stop": b["stop"], "target": b["target"], "rr": b["rr"], "call": b["call"],
                "scanner": b["scanner"], "lastClose": px, "lastMarkedAt": at,
                "lastTensorBuyAt": existing["lastTensorBuyAt"] if existing else None,
                "held": bool((existing and existing["held"]) or b.get("held")), "status": "LIVE", "dropReason": None,
                "entryHigh": max(px, b["buy"], existing["entryHigh"] if existing else 0),
                "lastHigh": max(px, existing["lastHigh"] if existing else 0, b["buy"]),
                "sessionMarks": _stamp_session(existing["sessionMarks"] if existing else [], date_et),
                "demoted": False, "weakFlags": existing["weakFlags"] if existing else 0,
                "clusterTight": existing["clusterTight"] if existing else False}, now)
            continue
        existing.update(lastBookedAt=at, buy=b["buy"], stop=b["stop"], target=b["target"], rr=b["rr"], call=b["call"],
                        scanner=b["scanner"], lastClose=px, lastMarkedAt=at, lastHigh=max(existing["lastHigh"], px),
                        sessionMarks=_stamp_session(existing["sessionMarks"], date_et), status="LIVE",
                        dropReason=None, demoted=False)
        if existing["held"] or b.get("held"):
            existing["held"] = True
    live_for_median = [m for m in by_sym.values() if m["status"] == "LIVE"]
    rets = []
    for m in live_for_median:
        px = quotes.get(m["symbol"]) if m["symbol"] in quotes else m["lastClose"]
        base = m["entryHigh"] or m["buy"]
        if base > 0 and px > 0:
            rets.append((px - base) / base)
    rets.sort()
    median_ret = rets[len(rets) // 2] if len(rets) >= 3 else None
    stopped = []
    for m in by_sym.values():
        if m["status"] != "LIVE":
            continue
        q = quotes[m["symbol"]] if m["symbol"] in quotes else None
        if q is not None:
            m["lastClose"] = q
            m["lastMarkedAt"] = at
            m["lastHigh"] = max(m["lastHigh"], q)
            m["sessionMarks"] = _stamp_session(m["sessionMarks"], date_et)
        why = evict_reason(m, q, now, m["symbol"] in booked, median_ret)
        if why == "DEMOTE":
            m["demoted"] = True
            continue
        if why == "REL_WEAK":
            m["weakFlags"] += 1
            if m["weakFlags"] < 2:
                continue
        elif not why:
            m["weakFlags"] = 0
        if why:
            m["status"] = "DROPPED"
            m["dropReason"] = why
            dropped_today.append({"symbol": m["symbol"], "reason": why, "at": at})
            if why == "STOP":
                stopped.append(m["symbol"])
    if stopped:
        hit = {c for c in (P.cluster_of(s) for s in stopped) if c}
        for m in by_sym.values():
            if m["status"] != "LIVE":
                continue
            c = P.cluster_of(m["symbol"])
            if c and c in hit and m["symbol"] not in stopped:
                m["clusterTight"] = True
    live = [m for m in by_sym.values() if m["status"] == "LIVE"]
    if len(live) > ROSTER_CAP:
        live = sorted(live, key=cmp_to_key(lambda a, b: _num_sign(_roster_rank(b, b["symbol"] in booked, now) -
                                                                  _roster_rank(a, a["symbol"] in booked, now))))
        for extra in live[ROSTER_CAP:]:
            if extra["held"]:
                continue
            extra["status"] = "DROPPED"
            extra["dropReason"] = "ROSTER_FULL"
            dropped_today.append({"symbol": extra["symbol"], "reason": "ROSTER_FULL", "at": at})
    kept = [m["symbol"] for m in by_sym.values() if m["status"] == "LIVE" and m["symbol"] not in added_today]
    return {"dateEt": date_et, "members": list(by_sym.values()), "addedToday": added_today, "kept": kept,
            "droppedToday": dropped_today[-40:]}


def stamp_tensor_buy(state, symbol, at_iso, now):
    return dict(state, members=[dict(normalize_member(m, now), lastTensorBuyAt=at_iso, demoted=False)
                                if (m["symbol"] == symbol and m["status"] == "LIVE") else normalize_member(m, now)
                                for m in state["members"]])


def stamp_tensor_sell(state, symbol, at_iso, now):
    members = [normalize_member(m, now) for m in state["members"]]
    for i, m in enumerate(members):
        if m["symbol"] == symbol and m["status"] == "LIVE" and m["lastTensorBuyAt"]:
            members[i] = dict(m, lastTensorBuyAt=None, lastMarkedAt=at_iso)
            break
    return dict(state, members=members)
