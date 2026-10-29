"""Author daily-level screens — line-by-line ports of Author-desk @652db7af src/lib/workdesk/{tape-levels,
admit-ticker,washout}.ts: the Fib swing / next lower shelf, the admit-ticker v1.1 next-support plan, the washout and
PPC-coil reads. Bars are dicts {t (epoch ms), o, h, l, c, v}; None stands for null / undefined. `now` (epoch ms) is
the clock tape-levels' completedDailyBars reads (Date.now() in the source). Parity: tools/parity/Author_levels.py."""
import math

from ..jsport import INF, js_round, js_str, to_fixed
from . import tensor as T


def _jmin(xs):
    xs = list(xs)
    return min(xs) if xs else INF


def _jmax(xs):
    xs = list(xs)
    return max(xs) if xs else -INF


# -- tape-levels.ts ----------------------------------------------------------------------------------------------------
FIB_SWING_BARS = 60
FIB_RATIOS = (0.382, 0.5, 0.618, 0.786)
FIB_NEAR_PCT = 0.015
EMA_ON_PCT = 0.02
BUY_ON_PCT = 0.01


def last_completed(bars, now):
    done = T.completed_daily_bars(bars, now)
    if len(done) >= 20:
        return done
    return [b for b in bars if all(isinstance(b.get(k), (int, float)) and math.isfinite(b[k]) for k in ("h", "l", "c"))]


def _num0(v):
    """Number(v) || 0."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0.0
    return x if (x == x and x != 0) else 0.0


def fib_swing(bars, now):
    win = last_completed(bars, now)[-FIB_SWING_BARS:]
    if not win:
        return {"high": 0, "low": 0}
    hi_i = 0
    for i in range(1, len(win)):
        if win[i]["h"] >= win[hi_i]["h"]:
            hi_i = i
    lo_i = hi_i
    for i in range(hi_i, len(win)):
        if win[i]["l"] < win[lo_i]["l"]:
            lo_i = i
    return {"high": _num0(win[hi_i]["h"]), "low": _num0(win[lo_i]["l"])}


def fib_levels(bars, now):
    sw = fib_swing(bars, now)
    span = sw["high"] - sw["low"]
    if not (span > 0):
        return []
    return [{"r": r, "px": sw["high"] - r * span} for r in FIB_RATIOS]


def last_ema(closes, period):
    s = T.ema(closes, period)
    for v in reversed(s):
        if v is not None and math.isfinite(v):
            return v
    return None


def fib_name(r):
    return f"{to_fixed(r * 100, 1)} Fibonacci"


def next_lower_shelf(bars, last, now):
    if not (last is not None and last > 0) or not bars:
        return None
    cap = last * 1.015
    closes = [b["c"] for b in bars]
    e21 = last_ema(closes, 21)
    lows = [b["l"] for b in bars[-12:] if b["l"] > 0]
    low12 = min(lows) if lows else None
    rows = []
    for f in fib_levels(bars, now):
        if f["px"] > 0 and f["px"] <= cap:
            rows.append({"px": f["px"], "name": fib_name(f["r"])})
    if e21 and e21 <= cap:
        rows.append({"px": e21, "name": "21-day EMA"})
    if low12 and low12 <= cap:
        rows.append({"px": low12, "name": "12-day"})
    if not rows:
        return None
    rows.sort(key=lambda r: -r["px"])
    return rows[0]


def on_next_lower_shelf(last, shelf):
    if not shelf or not (last is not None and last > 0):
        return False
    return abs(last - shelf["px"]) / last <= BUY_ON_PCT


# -- admit-ticker.ts ---------------------------------------------------------------------------------------------------
ON_PCT = 0.01
MIN_GAIN = 0.06
MAX_GAIN = 0.18
BLOCK_THROUGH = 0.008


def _px(n):
    if n >= 100:
        return js_round(n * 100) / 100
    if n >= 1:
        return js_round(n * 100) / 100
    return js_round(n * 1000) / 1000


def _admit_stop(buy, bars):
    if not (buy > 0):
        return 0
    lows = [b["l"] for b in (bars or [])[-12:] if b["l"] > 0]
    low12 = min(lows) if lows else None
    min_room = buy * (1 - 0.025)
    max_room = buy * (1 - 0.035)
    stop = low12 * 0.994 if (low12 is not None and low12 < buy) else min_room
    if stop > min_room:
        stop = min_room
    if stop < max_room:
        stop = max_room
    if not (stop < buy):
        stop = min_room
    return _px(stop)


def _admit_target(buy, stop, e50, e21, e200, last):
    risk = max(buy - stop, buy * 0.01)
    floor = buy * (1 + MIN_GAIN)
    cap_r = buy + 5 * risk
    cap_pct = buy * (1 + MAX_GAIN)
    cap = min(cap_r, cap_pct)
    target = buy + 5 * risk

    def ok(n):
        return n is not None and n > last and n >= buy * 1.06 and n <= cap and (e200 is None or abs(n - e200) / n > 0.02)
    if ok(e21) and e21 > target * 0.9:
        target = e21
    if ok(e50) and e50 > target * 0.9:
        target = e50
    if target < floor:
        target = min(floor, cap)
    if target > cap:
        target = cap
    if last > buy and target <= last * 1.01:
        target = min(max(last * (1 + MIN_GAIN), buy + 3 * risk), cap_pct)
    if e200 and abs(target - e200) / target < 0.02:
        alt = min(cap, last * 1.08 if last > buy else buy + 4 * risk)
        target = (e200 * 1.04 if alt > e200 else e200 * 0.96) if abs(alt - e200) / alt < 0.02 else alt
    if not (target > buy):
        target = min(floor, cap)
    if not (target > last):
        target = last * (1 + MIN_GAIN)
    r = max(buy - stop, buy * 0.01)
    if (target - buy) / r > 5:
        target = buy + 5 * r
    if not (target > buy):
        target = buy + 3 * r
    return _px(target)


def admit_ticker(symbol, bars, last, now):
    s = str(symbol or "").upper()
    empty = {"symbol": s, "tag": "WAIT", "live": False, "last": last, "buy": None, "stop": None, "target": None,
             "waitPx": None, "waitName": None, "on21": False, "onFib": False, "onShelf": False, "under50": True,
             "through50pct": None, "e21": None, "e50": None, "e200": None, "rsi": None, "macdUp": None, "shelf": None,
             "why": "no last", "size": "Wait"}
    if not (last is not None and last > 0) or not bars:
        return empty
    closes = [b["c"] for b in bars]
    e21 = last_ema(closes, 21)
    e50 = last_ema(closes, 50)
    e200 = last_ema(closes, min(200, max(20, len(bars) - 1)))
    rr = T.rsi(closes, 14)
    r = rr[-1] if rr else None
    rsi_n = r if (r is not None and math.isfinite(r)) else None
    hist = T.macd(closes)["hist"]
    h = hist[-1] if hist else None
    h1 = hist[-4] if len(hist) >= 4 else None
    if h1 is None:
        h1 = hist[-2] if len(hist) >= 2 else None
    macd_up = (h > h1) if (h is not None and h1 is not None) else None
    through50 = (last - e50) / e50 if (e50 and e50 > 0) else None
    under50 = through50 is None or through50 < BLOCK_THROUGH
    on21 = bool(e21 and abs(last - e21) / last <= ON_PCT and last >= e21 * (1 - ON_PCT))
    shelf = next_lower_shelf(bars, last, now)
    on_shelf = on_next_lower_shelf(last, shelf)
    on_fib = bool(shelf and "fibonacci" in shelf["name"].lower() and on_shelf)
    buy = _px(shelf["px"]) if (shelf and shelf["px"] < last * 0.998) else _px(last * 0.985)
    if not (buy < last):
        buy = _px(last * 0.985)
    stop = _admit_stop(buy, bars)
    target = _admit_target(buy, stop, _px(e50) if e50 is not None else None, _px(e21) if e21 is not None else None,
                           _px(e200) if e200 is not None else None, last)
    out = dict(empty)
    out.update({"symbol": s, "last": _px(last), "e21": _px(e21) if e21 is not None else None,
                "e50": _px(e50) if e50 is not None else None, "e200": _px(e200) if e200 is not None else None,
                "rsi": rsi_n, "macdUp": macd_up, "shelf": shelf, "on21": on21, "onFib": on_fib, "onShelf": on_shelf,
                "under50": under50, "through50pct": through50, "waitPx": buy,
                "waitName": (shelf["name"] if shelf else None) or "next support", "tag": "BUY", "live": True,
                "buy": buy, "stop": stop, "target": target,
                "why": (f"next support is the {shelf['name']} at {js_str(_px(shelf['px']))}" if shelf
                        else f"buy the tape at {js_str(_px(last))}"), "size": "Half size"})
    return out


# -- washout.ts --------------------------------------------------------------------------------------------------------
WASHOUT_GATE = {"rsiNowMax": 50, "maxOff12": 0.06, "minOffHigh60": 0.08, "fibNear": 0.025, "shelfOff12": 0.04,
                "ema21Near": 0.02, "rvolMax": 2.2}
COIL_GATE = {"under50Max": 0.03, "ema21Near": 0.02, "rsiMin": 40, "rsiMax": 52, "maxRange60": 0.25, "rvolMax": 1.1,
             "fibNear": 0.025}


def _last_finite(arr, back=0):
    seen = 0
    for v in reversed(arr):
        if v is None or not math.isfinite(v):
            continue
        if seen == back:
            return v
        seen += 1
    return None


def read_washout(bars, last, now):
    empty = {"ok": False, "why": "need dailies for the washout read", "under50": False, "rsi": None,
             "macdHist": None, "macdUp": False, "off12": None, "offHigh60": None, "onFib": None, "onShelf": False,
             "on21": False, "dry": False}
    if not bars or len(bars) < 50 or not (last is not None and last > 0):
        return empty
    closes = [b["c"] for b in bars]
    e50 = last_ema(closes, 50)
    e21 = last_ema(closes, 21)
    r = T.rsi(closes, 14)
    m = T.macd(closes)
    rsi_now = _last_finite(r)
    hist = _last_finite(m["hist"])
    hist_prev = _last_finite(m["hist"], 1)
    low12 = _jmin(b["l"] for b in bars[-12:] if b["l"] > 0)
    high60 = _jmax(b["h"] for b in bars[-60:] if b["h"] > 0)
    off12 = (last - low12) / low12 if low12 > 0 else None
    off_high60 = (high60 - last) / high60 if high60 > 0 else None
    under50 = e50 is not None and last < e50
    macd_up = hist is not None and hist_prev is not None and hist > hist_prev
    macd_repair = hist is not None and (hist < 0 or (macd_up and hist < 0.15))
    on_fib = None
    for f in fib_levels(bars, now):
        if f["r"] not in (0.5, 0.618, 0.786):
            continue
        if abs(last - f["px"]) / last <= WASHOUT_GATE["fibNear"]:
            on_fib = f
            break
    on_shelf = off12 is not None and off12 <= WASHOUT_GATE["shelfOff12"]
    on21 = e21 is not None and abs(last - e21) / last <= WASHOUT_GATE["ema21Near"]
    vol_r = _last_finite(T.relative_volume(bars, 20))
    dry = vol_r is not None and vol_r < 1
    climax = vol_r is not None and vol_r >= WASHOUT_GATE["rvolMax"]
    ok = False
    why = "washout under the 50-day"
    if not under50:
        why = "already back above the 50-day"
    elif rsi_now is None or rsi_now >= WASHOUT_GATE["rsiNowMax"]:
        why = "RSI 14 is not washed out"
    elif not macd_repair:
        why = "MACD is not still repairing"
    elif off_high60 is not None and off_high60 < WASHOUT_GATE["minOffHigh60"]:
        why = "not a 60-day washout"
    elif off12 is not None and off12 > WASHOUT_GATE["maxOff12"] and not on21:
        why = "too far off the 12-day shelf"
    elif not on_fib and not on_shelf and not on21:
        why = "not on a Fib of the drop or the shelf"
    elif climax:
        why = "volume already climaxed"
    else:
        ok = True
        if on_fib:
            why = f"washout under the 50-day on the {to_fixed(on_fib['r'] * 100, 1)} Fib"
        elif on_shelf:
            why = "washout under the 50-day on the 12-day shelf"
        else:
            why = "washout under the 50-day sitting on the 21-day"
    return {"ok": ok, "why": why, "under50": under50, "rsi": rsi_now, "macdHist": hist, "macdUp": macd_up,
            "off12": off12, "offHigh60": off_high60, "onFib": on_fib, "onShelf": on_shelf, "on21": on21, "dry": dry}


def read_coil(bars, last, now):
    empty = {"ok": False, "why": "need dailies for the coil read", "vs50": None, "vs21": None, "range60": None,
             "flushed786": False}
    if not bars or len(bars) < 60 or not (last is not None and last > 0):
        return empty
    wash = read_washout(bars, last, now)
    closes = [b["c"] for b in bars]
    e50 = last_ema(closes, 50)
    e21 = last_ema(closes, 21)
    vs50 = (e50 - last) / e50 if e50 else None
    vs21 = (last - e21) / e21 if e21 else None
    win60 = bars[-60:]
    high60 = _jmax(b["h"] for b in win60 if b["h"] > 0)
    low60 = _jmin(b["l"] for b in win60 if b["l"] > 0)
    range60 = (high60 - low60) / low60 if low60 > 0 else None
    vol_r = _last_finite(T.relative_volume(bars, 20))
    fibs = fib_levels(bars, now)
    fib618 = next((f for f in fibs if f["r"] == 0.618), None)
    fib50 = next((f for f in fibs if f["r"] == 0.5), None)
    fib786 = next((f for f in fibs if f["r"] == 0.786), None)
    on618 = (fib618 is not None and abs(last - fib618["px"]) / last <= COIL_GATE["fibNear"]) or \
            (fib50 is not None and abs(last - fib50["px"]) / last <= COIL_GATE["fibNear"])
    flushed786 = bool(fib786 and any(b["l"] <= fib786["px"] * 1.015 and b["c"] >= fib786["px"] * 0.98
                                     for b in bars[-6:]))
    rsi_ok = wash["rsi"] is not None and COIL_GATE["rsiMin"] <= wash["rsi"] <= COIL_GATE["rsiMax"]
    on21 = vs21 is not None and abs(vs21) <= COIL_GATE["ema21Near"]
    tight50 = vs50 is not None and 0 <= vs50 <= COIL_GATE["under50Max"]
    dry = vol_r is not None and vol_r <= COIL_GATE["rvolMax"]
    tight_range = range60 is not None and range60 <= COIL_GATE["maxRange60"]
    ok = False
    why = "PPC coil under the 50-day"
    if not wash["under50"]:
        why = "already back above the 50-day"
    elif not tight50:
        why = "too far under the 50-day — wreck, not coil"
    elif not on21:
        why = "not sitting on the 21-day"
    elif not rsi_ok:
        why = "RSI is not the 40–52 coil band"
    elif not wash["macdUp"] or wash["macdHist"] is None or wash["macdHist"] >= 0:
        why = "MACD hist is not lifting into zero"
    elif not tight_range:
        why = "60-day range is a wreck, not a coil"
    elif not dry:
        why = "volume already expanding"
    elif not on618:
        why = "not on the 50/61.8 of the coil"
    elif not flushed786:
        why = "no 78.6 shakeout that held"
    else:
        ok = True
    return {"ok": ok, "why": why, "vs50": vs50, "vs21": vs21, "range60": range60, "flushed786": flushed786}


def washout_buy(bars, last, now):
    coil = read_coil(bars, last, now)
    if coil["ok"]:
        return {"buy": last, "why": coil["why"], "coil": True}
    w = read_washout(bars, last, now)
    if not w["ok"]:
        return None
    return {"buy": w["onFib"]["px"] if w["onFib"] else last, "why": w["why"], "coil": False}
