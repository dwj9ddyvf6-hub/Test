"""Author paper desk rules — line-by-line ports of Author-desk @652db7af src/lib/workdesk/{paper-rules,tensor-edge,
exit,cluster,timing}.ts (+ weeklyBars of select.ts, isConfirmedBuyCode of tensor/doctrine.ts). Parity under Node 22:
tools/parity/Author_paper.py. Inputs are keyword arguments named as the TypeScript input objects' fields; None stands
for undefined / null."""
import math
import re

from ..jsport import js_round
from . import tensor as T

INF = float("inf")

# -- paper-rules.ts ----------------------------------------------------------------------------------------------------
PAPER_LAW = {"maxImpulseOpen": 4, "maxSwingOpen": 6, "maxOpen": 10, "maxNewBuysPerDay": 16, "maxSameStory": 2,
             "firstBuyMinute": 4 * 60, "fullSizeMinute": 9 * 60 + 35, "lastBuyMinute": 15 * 60 + 45, "pocketR": 0.25,
             "takeProfit": 0.05, "popStop": 0.02, "sellGraceMs": 70_000, "impulseNotional": 0.015,
             "impulseObserveUntil": 20, "goldNotional": 0.04, "goldPremarketNotional": 0.02, "swingRisk": 0.015,
             "swingNotionalCap": 0.08, "crumbNotional": 75}


def _n0(x):
    """Number(x || 0)."""
    if x is None or x is False or x == 0 or (isinstance(x, float) and x != x):
        return 0.0
    return float(x)


def _gt0(x):
    return x is not None and x > 0


def is_premarket(hour, minute):
    return hour * 60 + minute < PAPER_LAW["fullSizeMinute"]


def paper_shares(equity, buy, sleeve, stop=None, premarket=None):
    if not _gt0(equity) or not _gt0(buy):
        return 0
    if sleeve == "impulse":
        return math.floor((equity * PAPER_LAW["impulseNotional"]) / buy)
    if sleeve == "gold":
        pct = PAPER_LAW["goldPremarketNotional"] if premarket else PAPER_LAW["goldNotional"]
        return max(1, math.floor((equity * pct) / buy))
    stop = _n0(stop)
    risk = buy - stop if (stop > 0 and stop < buy) else buy * PAPER_LAW["popStop"]
    if not risk > 0:
        return 0
    by_risk = (equity * PAPER_LAW["swingRisk"]) / risk
    by_cap = (equity * PAPER_LAW["swingNotionalCap"]) / buy
    return math.floor(min(by_risk, by_cap))


def book_may_enter(price, buy, stop, target, antiChase=None, atSupport=None, curlOk=None, coilOk=None, context=None):
    price, buy, stop, target = _n0(price), _n0(buy), _n0(stop), _n0(target)
    if not (buy > 0) or not (stop > 0) or not (target > buy) or stop >= buy:
        return {"ok": False, "reason": "plan is not a buy"}
    if not (price > 0):
        return {"ok": False, "reason": "no mark"}
    if price <= stop:
        return {"ok": False, "reason": "through the stop"}
    if price >= target:
        return {"ok": False, "reason": "already at the target"}
    if antiChase is False:
        return {"ok": False, "reason": "chase — scan said no"}
    if curlOk is False and coilOk is not True:
        return {"ok": False, "reason": "no curl"}
    if atSupport is False:
        return {"ok": False, "reason": "not on the shelf"}
    if price > buy * 1.03:
        return {"ok": False, "reason": "late — more than 3% through the buy"}
    if price < buy * 0.97:
        return {"ok": False, "reason": "too far under the buy — wait for the level"}
    if context == "adverse" and atSupport is not True:
        return {"ok": False, "reason": "adverse tape and not on support"}
    return {"ok": True, "reason": "reasonable book entry"}


def exit_math(price, entry, stop, impulse=None, openedAt=None, now=None, atr=None, mfe=None, bars=None,
              alreadyTrimmed=None, alreadyAdded=None, hour=None, minute=None, target=None, clock=None):
    price, entry, stop = _n0(price), _n0(entry), _n0(stop)
    if not (price > 0) or not (entry > 0):
        return {"action": "hold", "reason": "no fill to mark against"}
    if stop > 0 and price <= stop:
        return {"action": "sell", "reason": "card stop"}
    if not impulse:
        tgt = _n0(target)
        if tgt > entry and price >= tgt and price > entry:
            return {"action": "sell", "reason": "card target · in profit"}
    if impulse and openedAt is not None:
        imp = impulse_exit(price=price, entry=entry, openedAt=openedAt, now=now if now is not None else clock,
                           atr=atr, mfe=mfe)
        if imp["action"] == "sell":
            return imp
    if impulse:
        tgt = paper_target(entry)
        if tgt > 0 and price >= tgt:
            return {"action": "sell", "reason": "5% target"}
        return {"action": "hold", "reason": "impulse still on"}
    swing = read_exit(bars=bars, last=price, buy=entry, stop=stop, alreadyTrimmed=alreadyTrimmed,
                      alreadyAdded=alreadyAdded, openedAt=openedAt, now=now)
    if swing["action"] == "SELL":
        return {"action": "sell", "reason": swing["why"]}
    if swing["action"] == "TRIM":
        return {"action": "trim", "reason": swing["why"], "trimPct": swing["trimPct"]}
    if swing["action"] == "ADD":
        return {"action": "add", "reason": swing["why"]}
    return {"action": "hold", "reason": swing["why"]}


def paper_stop(entry, card_stop):
    if not _gt0(entry):
        return 0
    pop = entry * (1 - PAPER_LAW["popStop"])
    card = _n0(card_stop)
    if card > 0 and card < entry:
        return max(card, pop)
    return pop


def paper_target(entry):
    if not _gt0(entry):
        return 0
    raw = entry * (1 + PAPER_LAW["takeProfit"])
    if raw >= 1:
        return js_round(raw * 100) / 100
    return js_round(raw * 10000) / 10000


def in_pocket(price, buy, stop):
    risk = buy - stop
    if not (risk > 0) or not _gt0(price):
        return False
    return price <= buy + PAPER_LAW["pocketR"] * risk


def same_story_count(symbol, open_symbols):
    story = cluster_of(symbol)
    if not story:
        return 0
    return len([s for s in open_symbols if cluster_of(s) == story])


def paper_eligible(member):
    if not member:
        return False
    if member.get("status") and member.get("status") != "LIVE":
        return False
    if member.get("demoted"):
        return False
    if member.get("call") != "BUY":
        return False
    buy = float(member.get("buy") if member.get("buy") is not None else 0)
    stop = float(member.get("stop") if member.get("stop") is not None else 0)
    target = float(member.get("target") if member.get("target") is not None else 0)
    return buy > stop and target > buy


def impulse_armed(closed_swing):
    return _n0(closed_swing) >= PAPER_LAW["impulseObserveUntil"]


def judge_paper(side, code, price, buy, stop, target, hour, minute, openCount, buysToday, lastBuyAt, barAt,
                hasPosition, symbol=None, entry=None, barUp=None, sameDay=None, clusterOpen=None, eligible=None,
                folioFlatten=None, tensorFlatten=None, goldTicket=None, echoTicket=None, echoAdd=None,
                bookTicket=None, weekend=None, alreadyTrimmed=None, alreadyAdded=None, bars=None, episodeKind=None,
                chaseKind=None, impulse=None, openedAt=None, now=None, atr=None, mfe=None, impulseOpen=None,
                swingOpen=None, closedSwing=None, antiChase=None, atSupport=None, curlOk=None, coilOk=None,
                context=None, observe_lock=True):
    """judgePaper. observe_lock=False drops the impulse lane's 20-closed-swing-ticket lock (a staging gate the desk
    doctrine removes; see desk/sleeves/families/Author.py) — the only change, and only when asked."""
    hm = hour * 60 + minute
    premarket = hm < PAPER_LAW["fullSizeMinute"]
    impulse_open = impulseOpen if impulseOpen is not None else openCount
    swing_open = swingOpen if swingOpen is not None else openCount
    L = PAPER_LAW
    if side == "buy":
        if goldTicket:
            if swing_open >= L["maxSwingOpen"]:
                return {"action": "hold", "reason": "six swings already open"}
            if openCount >= L["maxOpen"]:
                return {"action": "hold", "reason": "book is full"}
            return {"action": "buy", "reason": "Gold diamond · half size before 9:35" if premarket
                    else "Gold diamond · buy no matter what"}
        if echoTicket:
            if premarket:
                return {"action": "hold", "reason": "premarket — observe only"}
            if weekend:
                return {"action": "hold", "reason": "weekend — no Echo paper"}
            if hm > L["lastBuyMinute"]:
                return {"action": "hold", "reason": "no new buys after 15:45"}
            if hasPosition and not echoAdd:
                return {"action": "hold", "reason": "already in"}
            if not echoAdd and swing_open >= L["maxSwingOpen"]:
                return {"action": "hold", "reason": "six swings already open"}
            if not echoAdd and openCount >= L["maxOpen"]:
                return {"action": "hold", "reason": "book is full"}
            if not echoAdd and buysToday >= L["maxNewBuysPerDay"]:
                return {"action": "hold", "reason": "daily entry cap"}
            return {"action": "buy", "reason": "Echo add · paper" if echoAdd else "Echo buy · paper"}
        if bookTicket:
            if premarket:
                return {"action": "hold", "reason": "premarket — observe only"}
            if weekend:
                return {"action": "hold", "reason": "weekend — no book paper"}
            if hm > L["lastBuyMinute"]:
                return {"action": "hold", "reason": "no new buys after 15:45"}
            if hasPosition:
                return {"action": "hold", "reason": "already in"}
            if sameDay:
                return {"action": "hold", "reason": "no same-day revenge"}
            if swing_open >= L["maxSwingOpen"]:
                return {"action": "hold", "reason": "six swings already open"}
            if openCount >= L["maxOpen"]:
                return {"action": "hold", "reason": "book is full"}
            if buysToday >= L["maxNewBuysPerDay"]:
                return {"action": "hold", "reason": "daily entry cap"}
            if (clusterOpen if clusterOpen is not None else 0) >= L["maxSameStory"]:
                return {"action": "hold", "reason": "two of that story already open"}
            e = book_may_enter(price=price, buy=buy, stop=stop, target=target, antiChase=antiChase,
                               atSupport=atSupport, curlOk=curlOk, coilOk=coilOk, context=context)
            if not e["ok"]:
                return {"action": "hold", "reason": e["reason"]}
            return {"action": "buy", "reason": "Book buy · reasonable entry"}
        if observe_lock and not impulse_armed(closedSwing):
            return {"action": "hold", "reason": f"green observe-only — {_jsn(_n0(closedSwing))}/"
                                                f"{L['impulseObserveUntil']} closed swing tickets"}
        if not is_buy_code(code):
            return {"action": "hold", "reason": "not a Tensor buy"}
        if premarket:
            return {"action": "hold", "reason": "premarket — observe only"}
        if eligible is False and not goldTicket:
            return {"action": "hold", "reason": "not a full-size name"}
        if hm > L["lastBuyMinute"]:
            return {"action": "hold", "reason": "no new buys after 15:45"}
        if hasPosition:
            return {"action": "hold", "reason": "already in"}
        if sameDay:
            return {"action": "hold", "reason": "no same-day revenge"}
        if openCount >= L["maxOpen"]:
            return {"action": "hold", "reason": "book is full"}
        if impulse_open >= L["maxImpulseOpen"]:
            return {"action": "hold", "reason": "four impulses already open"}
        if (clusterOpen if clusterOpen is not None else 0) >= L["maxSameStory"]:
            return {"action": "hold", "reason": "two of that story already open"}
        if buysToday >= L["maxNewBuysPerDay"]:
            return {"action": "hold", "reason": "daily entry cap"}
        if not (buy > 0) or not (stop > 0) or not (target > buy) or stop >= buy:
            if not goldTicket:
                return {"action": "hold", "reason": "plan is not a buy"}
        if barUp is False and not goldTicket:
            return {"action": "hold", "reason": "buy bar already failed — missed the pop"}
        if price > 0 and price <= stop:
            return {"action": "hold", "reason": "through the stop"}
        if not goldTicket and not green_may_enter(episodeKind, chaseKind):
            if episodeKind == "REPEATED":
                return {"action": "hold", "reason": "repeated green — same episode"}
            if episodeKind == "REINFORCED":
                return {"action": "hold", "reason": "reinforced green — already in the episode"}
            if episodeKind == "STALE":
                return {"action": "hold", "reason": "stale green — entry window closed"}
            if chaseKind == "WAIT":
                return {"action": "hold", "reason": "wait — above the zone, under the chase line"}
            if chaseKind == "AVOID":
                return {"action": "hold", "reason": "avoid — chase line already broken"}
        if not goldTicket and not in_pocket(price, buy, stop):
            return {"action": "hold", "reason": "late — Tensor printed after the pocket"}
        tgt = paper_target(price if price > 0 else buy)
        if not (tgt > price) or tgt <= stop:
            return {"action": "hold", "reason": "5% target does not clear the stop"}
        return {"action": "buy", "reason": "Gold diamond · paper" if goldTicket else
                "Tensor buy · fresh 5m impulse" if impulse else "Tensor buy · 5% target"}

    if not hasPosition:
        return {"action": "hold", "reason": "no paper position"}
    if folioFlatten or tensorFlatten:
        if bookTicket or echoTicket:
            return {"action": "hold", "reason": "swing rides to the card — Tensor sell ignored"}
        e = entry if (entry and entry > 0) else buy
        if e > 0 and price > e:
            return {"action": "sell", "reason": "Tensor sell · in profit"}
        return {"action": "hold", "reason": "Tensor sell ignored — not in profit"}
    if lastBuyAt is not None and barAt - lastBuyAt < L["sellGraceMs"]:
        return {"action": "hold", "reason": "one bar after entry"}
    return exit_math(price=price, entry=entry if (entry and entry > 0) else buy, stop=stop, impulse=impulse,
                     openedAt=openedAt, now=now if now is not None else barAt, atr=atr, mfe=mfe, bars=bars,
                     alreadyTrimmed=alreadyTrimmed, alreadyAdded=alreadyAdded, hour=hour, minute=minute)


def _jsn(x):
    from ..jsport import js_str
    return js_str(x)


# -- tensor-edge.ts ----------------------------------------------------------------------------------------------------
EDGE_LAW = {"chaseAtr": 0.75, "chasePct": 0.05, "waitAtr": 0.5, "avoidAtr": 1.5, "episodeBars": 6, "barMs": 5 * 60_000,
            "impulseHorizonBars": 6, "t1Atr": 0.75, "t1Floor": 0.015, "noProgressAtr": 0.25, "giveback": 0.6,
            "shrinkN": 200}


def episode_ttl(bar_at, interval="5m"):
    return bar_at + EDGE_LAW["episodeBars"] * EDGE_LAW["barMs"]


def classify_episode(last, nxt):
    """last: {symbol, interval, side, barAt, eventKey, expiresAt} | None; nxt: same without expiresAt, opt. now."""
    now = nxt.get("now") if nxt.get("now") is not None else nxt["barAt"]
    if not last:
        return "FRESH"
    if now > last["expiresAt"] and nxt["barAt"] > last["expiresAt"]:
        return "FRESH"
    if nxt["side"] != last["side"]:
        return "REVERSAL"
    if nxt["eventKey"] == last["eventKey"] or nxt["barAt"] == last["barAt"]:
        return "REPEATED"
    if nxt["barAt"] > last["barAt"] and nxt["barAt"] <= last["expiresAt"]:
        return "REINFORCED"
    if now - nxt["barAt"] > EDGE_LAW["episodeBars"] * EDGE_LAW["barMs"]:
        return "STALE"
    return "FRESH"


def atr14(bars):
    if not bars or len(bars) < 16:
        return None
    acc = 0.0
    n = 0
    for i in range(max(1, len(bars) - 15), len(bars)):
        prev = bars[i - 1]["c"]
        tr = max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - prev), abs(bars[i]["l"] - prev))
        if math.isfinite(tr):
            acc += tr
            n += 1
    return acc / n if n else None


def chase_line(signal, atr):
    if not _gt0(signal):
        return 0
    span = EDGE_LAW["chaseAtr"] * atr if atr > 0 else signal * EDGE_LAW["chasePct"]
    return signal + min(span, signal * EDGE_LAW["chasePct"])


def chase_verdict(price, signal, atr):
    width = atr if (atr and atr > 0) else signal * 0.02
    line = chase_line(signal, width)
    ext = (price - signal) / width if width > 0 else 0
    if not _gt0(price) or not _gt0(signal):
        return {"kind": "OK", "extensionAtr": 0, "line": line}
    if ext <= EDGE_LAW["waitAtr"]:
        return {"kind": "OK", "extensionAtr": ext, "line": line}
    if price <= line and ext < EDGE_LAW["avoidAtr"]:
        return {"kind": "WAIT", "extensionAtr": ext, "line": line}
    return {"kind": "AVOID", "extensionAtr": ext, "line": line}


def impulse_target(entry, atr):
    if not _gt0(entry):
        return 0
    width = atr if (atr and atr > 0) else entry * 0.02
    raw = entry + max(EDGE_LAW["t1Atr"] * width, EDGE_LAW["t1Floor"] * entry)
    return js_round(raw * 100) / 100 if raw >= 1 else js_round(raw * 10000) / 10000


def impulse_exit(price, entry, openedAt, now, atr=None, mfe=None):
    if not _gt0(price) or not _gt0(entry):
        return {"action": "hold", "reason": "no fill to mark against"}
    t1 = impulse_target(entry, atr if atr is not None else None)
    if t1 > 0 and price >= t1:
        return {"action": "sell", "reason": "impulse T1"}
    horizon = EDGE_LAW["impulseHorizonBars"] * EDGE_LAW["barMs"]
    age = now - openedAt
    width = atr if (atr and atr > 0) else entry * 0.02
    if age >= horizon and price < entry + EDGE_LAW["noProgressAtr"] * width:
        return {"action": "sell", "reason": "impulse no progress"}
    peak = mfe if (mfe is not None and mfe > entry) else price
    if peak >= t1 and t1 > entry:
        kept = (price - entry) / (peak - entry)
        if kept <= 1 - EDGE_LAW["giveback"]:
            return {"action": "sell", "reason": "impulse gave back"}
    return {"action": "hold", "reason": "impulse still on"}


def green_may_enter(kind, chase):
    if kind in ("REPEATED", "REINFORCED", "STALE"):
        return False
    if chase in ("AVOID", "WAIT"):
        return False
    return True


# -- timing.ts / doctrine.ts -------------------------------------------------------------------------------------------
TIMING_WATCH_CAP = 36


def is_buy_code(code):
    return bool(re.search(r"GREEN_BUY", code)) and not re.search(r"CYAN|HOLD|DEFENSE|WAIT|DCB", code)


def is_sell_code(code):
    return bool(re.search(r"RED_SELL|MAGENTA_SELL|^SELL$|VECTOR_SELL", code))


def cap_watch(symbols):
    out = []
    for s in symbols:
        t = s.strip().upper()
        if not t or t in out:
            continue
        out.append(t)
        if len(out) >= TIMING_WATCH_CAP:
            break
    return out


# -- cluster.ts --------------------------------------------------------------------------------------------------------
CLUSTERS = {
    "semis": ["TSM", "NVTS", "SMH", "ASX", "AMD", "NVDA", "AVGO", "MU", "AMAT", "LRCX", "KLAC", "ASML", "ARM", "INTC",
              "QCOM"],
    "software": ["AFRM", "PLTR", "CRM", "NOW", "SNOW", "DDOG", "NET", "CRWD", "PANW", "FTNT"],
    "ev": ["RIVN", "XPEV", "TSLA", "NIO", "LI", "LCID"],
    "space": ["ASTS", "RKLB", "RDW", "LUNR", "SATL", "SKYQ"],
    "ag": ["ADM", "MOS", "AGCO", "DE", "CTVA", "NTR"],
    "energy": ["DVN", "XLE", "XOP", "COP", "OXY", "CVX", "XOM"],
    "biotech": ["XBI", "LLY", "AMGN", "VRTX", "REGN"],
    "mega": ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLF"],
}


def cluster_of(symbol):
    t = symbol.strip().upper()
    for name, members in CLUSTERS.items():
        if t in members:
            return name
    return None


# -- select.ts weeklyBars ----------------------------------------------------------------------------------------------
def _utc_day_ms(t):
    """Date.UTC(y, m, d) of the UTC calendar date of epoch-ms t, and Date.UTC(y, 0, 1)."""
    days = math.floor(t / 86_400_000)
    import datetime as _dt
    d = _dt.date(1970, 1, 1) + _dt.timedelta(days=days)
    jan1 = _dt.date(d.year, 1, 1)
    return days * 86_400_000, (jan1 - _dt.date(1970, 1, 1)).days * 86_400_000, d.year


def weekly_bars(bars):
    weeks = []
    cur = None
    key = ""
    for b in bars:
        day, jan1, year = _utc_day_ms(b["t"])
        k = f"{year}-w{math.floor((day - jan1) / 604800000)}"
        if k != key:
            if cur:
                weeks.append(cur)
            key = k
            cur = {"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
        elif cur:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            cur["v"] += b["v"]
    if cur:
        weeks.append(cur)
    return weeks


# -- exit.ts -----------------------------------------------------------------------------------------------------------
EMA_ON_PCT = 0.02


def _last_finite(arr):
    for v in reversed(arr):
        if v is not None and math.isfinite(v):
            return v
    return None


def _weekly_rsi_now(bars):
    w = weekly_bars(bars)
    if len(w) < 16:
        return None
    return _last_finite(T.rsi(T.series(w, "c"), 14))


def _daily_bear_div(bars):
    if len(bars) < 30:
        return False
    win = bars[-30:]
    r = T.rsi(T.series(win, "c"), 14)
    hi1 = hi2 = -1
    for i in range(2, len(win) - 2):
        if win[i]["h"] >= win[i - 1]["h"] and win[i]["h"] >= win[i + 1]["h"]:
            hi1 = hi2
            hi2 = i
    if hi1 < 0 or hi2 < 0:
        return False
    p1, p2 = win[hi1]["h"], win[hi2]["h"]
    r1, r2 = r[hi1], r[hi2]
    return p2 > p1 and r1 is not None and r2 is not None and r2 < r1


def _swing_range(bars):
    win = bars[-90:]
    if len(win) < 10:
        return None
    hi, lo = -INF, INF
    for b in win:
        if b["h"] > hi:
            hi = b["h"]
        if b["l"] < lo:
            lo = b["l"]
    if not (hi > lo) or not (lo > 0):
        return None
    return {"hi": hi, "lo": lo, "span": hi - lo}


def overhead_fib(bars, buy):
    r = _swing_range(bars)
    if not r or not _gt0(buy):
        return None
    marks = [r["lo"] + f * r["span"] for f in (0.382, 0.5, 0.618)]
    above = sorted(px for px in marks if px > buy * 1.01)
    return above[0] if above else None


def wave3_target(bars, buy, risk):
    if not _gt0(buy) or not _gt0(risk):
        return buy + 3 * risk
    if not bars:
        return buy + 3 * risk
    r = _swing_range(bars)
    if not r:
        return buy + 3 * risk
    ext = buy + 1.618 * r["span"]
    cap = buy + 5 * risk
    if ext > buy * 1.08:
        return min(ext, max(cap, buy * 1.35))
    return buy + 3 * risk


def _rejected_at(bars, level):
    b = bars[-1] if bars else None
    if not b or not _gt0(level):
        return False
    tagged = b["h"] >= level * (1 - EMA_ON_PCT) and b["h"] <= level * 1.04
    failed = b["c"] < level and b["c"] < b["o"]
    return tagged and failed


def _broke_then_rejected(bars, level, last):
    if not _gt0(level) or len(bars) < 8:
        return False
    prior = bars[-12:-1]
    broke = any(b["c"] < level * 0.99 for b in prior)
    retest = last >= level * 0.985 and last <= level * 1.02
    b = bars[-1] if bars else None
    reject = bool(b and b["c"] < level and b["c"] <= b["o"])
    return broke and retest and reject


def _ema_now(bars, n):
    return _last_finite(T.ema(T.series(bars, "c"), n))


def failed618(bars, last):
    if len(bars) < 20 or not _gt0(last):
        return False
    r = _swing_range(bars)
    e50 = _ema_now(bars, 50)
    if not r or e50 is None:
        return False
    fib = r["lo"] + 0.618 * r["span"]
    recent = bars[-8:]
    tagged = any(b["h"] >= fib * 0.995 and b["h"] <= fib * 1.04 for b in recent)
    return tagged and last < e50 * 0.98


def rail_flip(bars, last):
    if len(bars) < 25 or not _gt0(last):
        return None
    closes = T.series(bars, "c")
    for n in (50, 200):
        rail = _last_finite(T.ema(closes, n))
        if rail is None:
            continue
        if abs(last - rail) / last > EMA_ON_PCT:
            continue
        prior = bars[-18:-2]
        below = len([b for b in prior if b["c"] < rail])
        if below >= 5 and last >= rail * 0.995:
            return f"{n}-day"
    return None


def read_exit(last, buy, stop, bars=None, alreadyTrimmed=None, alreadyAdded=None, openedAt=None, now=None):
    last, buy, stop = _n0(last), _n0(buy), _n0(stop)
    bars = bars if (bars and len(bars) >= 8) else []
    overhead = overhead_fib(bars, buy) if bars else None
    wave3 = wave3_target(bars, buy, buy - stop) if (bars and buy > 0 and stop > 0 and buy > stop) else None
    run_pct = (last - buy) / buy if (buy > 0 and last > 0) else 0
    held_days = (now - openedAt) / 86_400_000 if (openedAt and now and now > openedAt) else None

    def blank(action, why, trim=0):
        return {"action": action, "why": why, "trimPct": trim, "stop": stop if stop > 0 else None,
                "overhead": overhead, "wave3": wave3, "runPct": run_pct}

    if not (last > 0) or not (buy > 0):
        return blank("HOLD", "no mark")
    if stop > 0 and last <= stop:
        return blank("SELL", "lower low under the Fib")
    if bars and _broke_then_rejected(bars, buy, last):
        return blank("SELL", "Fib broke, retested, rejected")
    rejected_overhead = overhead is not None and _rejected_at(bars, overhead)
    if rejected_overhead and run_pct >= 0.35:
        return blank("SELL", "Wave B Fib rejected after a large run")
    wrsi = _weekly_rsi_now(bars) if bars else None
    stretched = wrsi is not None and wrsi >= 68 and _daily_bear_div(bars) and run_pct >= 0.8
    banked_week = held_days is not None and held_days <= 8 and run_pct >= 0.5
    if not alreadyTrimmed and (stretched or banked_week):
        return blank("TRIM", "weekly RSI extreme and daily divergence — trim half" if stretched
                     else "50% in a week — bank half", 0.5)
    if rejected_overhead and not alreadyTrimmed:
        return blank("TRIM", "rejection at the first overhead Fib", 0.2)
    if bars and failed618(bars, last) and last < buy:
        return blank("HOLD", "0.618 failed and closed under the 50-day — no add")
    if not alreadyAdded and bars:
        flip = rail_flip(bars, last)
        if flip:
            return blank("ADD", f"{flip} flipped to support")
    return blank("HOLD", "no rejection — hold the rest")


def swing_stop(entry, card_stop):
    if not _gt0(entry):
        return 0
    card = _n0(card_stop)
    if card > 0 and card < entry:
        return card
    return js_round(entry * 0.98 * 100) / 100


def swing_target(entry, card_target):
    if not _gt0(entry):
        return 0
    card = _n0(card_target)
    if card > entry:
        return card
    return js_round(entry * 1.35 * 100) / 100
