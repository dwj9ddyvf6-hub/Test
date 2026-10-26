"""Midna's forward-lab scan (src/lib/equity/forward-scan.ts, forward.ts helpers and gbm.ts @ cursor/paper-desk-f184
68315288; blobs 005059c6 / 125bda69 / 09eab421), ported line for line: validBars, stockBag, barBag, laneHistory,
marketBag, htfBag, scanForward; turnOfMonth, weekIndex, htfFromWeeks, fomcWithin, opexWeek, priceBucket, hitsFor,
capHits, FORWARD_SPECS; binOf, binsFor, walkTree, scoreBins (the frozen v4 daily-cyan trees,
tensor_gbm_v4_1D_cyan_full.json blob cda5b9b1 = desk/vendor/old_desk_research/models/).

The engine layers (indicators / markers / extras / weekly) are the Midna engine itself, executed by
desk/feedlib/midna_forward_runner.mjs; this module reads the values that runner returns for each name.

JavaScript semantics kept: NaN for a missing value (put() keeps finite values only), Math.round, left-to-right sums,
toFixed (round half away from zero on the exact binary value) in the flags. Named divergence (numerics): CPython's
log / exp / pow are glibc's, V8's are fdlibm's; they differ in the last bit on a few percent of inputs, so a feature can
differ by an ulp — tools/parity/midna_forward.py counts those and requires every decision (bins, score, tests, hits)
to be identical."""
import json
import math
import os
from decimal import ROUND_HALF_UP, Decimal

from . import common as M

NAN = float("nan")
MARKET = ["SPY", "QQQ", "IWM", "SMH", "TLT", "GLD", "USO", "UUP", "HYG", "IEF", "BTC-USD"]
FORWARD_SLOTS = 6
FOMC_DECISIONS = ["2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28",
                  "2026-12-09"]
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                          "old_desk_research", "models", "tensor_gbm_v4_1D_cyan_full.json")


def fin(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def nn(x):
    """a runner value (null -> NaN)."""
    return NAN if x is None else x


def to_fixed(x, d):
    """Number.prototype.toFixed for finite x (the exact binary value rounded half away from zero)."""
    q = Decimal(1).scaleb(-d)
    return str(Decimal(0.0 if x == 0 else x).quantize(q, rounding=ROUND_HALF_UP))


# -- forward.ts helpers -------------------------------------------------------------------------------------------
def price_bucket(price):
    if not price > 0:
        return NAN
    if price < 2:
        return 0
    if price < 5:
        return 1
    if price < 10:
        return 2
    if price < 20:
        return 3
    if price < 50:
        return 4
    return 5


def turn_of_month(as_of, clock):
    month = as_of[:7]
    try:
        index = len(clock) - 1 - clock[::-1].index(as_of)
    except ValueError:
        index = -1
    before = 0
    if index >= 0:
        k = index - 1
        while k >= 0 and clock[k][:7] == month:
            before += 1
            k -= 1
    after = 0
    cursor = M.add_days(as_of, 1)
    while cursor[:7] == month:
        if M.is_trading_day(cursor):
            after += 1
        cursor = M.add_days(cursor, 1)
    return 1 if before < 3 or after < 2 else 0


def week_index(week_ends, as_of):
    use = -1
    for k, w in enumerate(week_ends):
        if w and w <= as_of:
            use = k
    return use


def _last_index(lst, x):
    for i in range(len(lst) - 1, -1, -1):
        if lst[i] == x:
            return i
    return -1


def htf_from_weeks(bar_days, week_ends, buy, cyan, as_of):
    week = week_index(week_ends, as_of)
    t = _last_index(bar_days, as_of)
    if week < 0 or t < 0:
        return None
    last_buy = last_cyan = -1
    start = max(0, week - 60)
    k = week
    while k >= start:
        if last_buy < 0 and buy[k]:
            last_buy = k
        if last_cyan < 0 and cyan[k]:
            last_cyan = k
        if last_buy >= 0 and last_cyan >= 0:
            break
        k -= 1

    def index_of(w):
        return _last_index(bar_days, week_ends[w] if 0 <= w < len(week_ends) else "")
    buy_at = index_of(last_buy) if last_buy >= 0 else -1
    cyan_at = index_of(last_cyan) if last_cyan >= 0 else -1
    return {"week": week, "htfsince": min(500, t - buy_at) if 0 <= buy_at <= t else 500,
            "htfcyan": 1 if (cyan_at >= 0 and cyan_at <= t and t - cyan_at <= 40) else 0}


def fomc_within(ymd, ahead):
    for d in FOMC_DECISIONS:
        gap = M.trading_gap(ymd, d)
        if 1 <= gap <= ahead:
            return True
    return False


def opex_week(ymd):
    from datetime import date
    d = date.fromisoformat(ymd)
    first = date(d.year, d.month, 1)
    first_dow_js = (first.weekday() + 1) % 7
    first_fri = 1 + ((5 - first_dow_js + 7) % 7)
    third_fri = first_fri + 14
    dom = d.day
    dow = (((d.weekday() + 1) % 7) + 6) % 7
    return dom - dow <= third_fri <= dom - dow + 4


# -- forward-scan.ts ----------------------------------------------------------------------------------------------
def valid_bars(clock, points):
    out = []
    if not points:
        return out
    for i in range(min(len(clock), len(points))):
        p = points[i]
        o = p.get("open")
        o = 0.0 if o is None else o                      # point.open ?? 0
        h = p.get("high")
        lo = p.get("low")
        lo = 0.0 if lo is None else lo                   # point.low ?? 0
        c = p.get("close")
        if not (o > 0 and h is not None and h > 0 and lo > 0 and c is not None and c > 0):
            continue
        if not (h >= max(o, c) and lo <= min(o, c)):
            continue
        adj = p["adj"] if (p.get("adj") or 0) > 0 else c
        out.append({"day": clock[i], "o": o, "h": h, "l": lo, "c": c, "adj": adj, "v": p.get("volume") or 0.0})
    return out


def _past(values, index, sessions):
    target = index - sessions
    k = target
    while k >= max(0, target - 3):
        if 0 <= k < len(values) and values[k] > 0:
            return values[k]
        k -= 1
    return NAN


def _ret(values, index, sessions):
    then = _past(values, index, sessions)
    v = values[index] if 0 <= index < len(values) else NAN
    return v / then - 1 if (then > 0 and v > 0) else NAN


def _mean(values):
    if not values:
        return NAN
    return M.js_sum(values) / len(values)


def _stdev(values):
    if len(values) < 2:
        return NAN
    avg = _mean(values)
    return math.sqrt(max(0.0, _mean([(v - avg) ** 2 for v in values])))


def dv20(bars, index):
    if index < 19:
        return NAN
    s, n = 0.0, 0
    for k in range(index - 19, index + 1):
        b = bars[k]
        if not b["c"] > 0 or not b["v"] > 0:
            continue
        s += b["c"] * b["v"]
        n += 1
    return s / n if n >= 15 else NAN


def _volume_ratio(bars, index):
    if index < 20:
        return NAN
    s, n = 0.0, 0
    for k in range(index - 20, index):
        if bars[k]["v"] > 0:
            s += bars[k]["v"]
            n += 1
    return bars[index]["v"] / (s / n) if (n >= 15 and s > 0) else NAN


def session_log_returns(bars, spy):
    own, mkt = [], []
    limit = math.log(8)
    for i in range(1, len(bars)):
        lp, rp = bars[i - 1]["adj"], bars[i]["adj"]
        left, right = spy[i - 1], spy[i]
        gap = M.sessions_after(bars[i - 1]["day"], bars[i]["day"])
        if not lp > 0 or not rp > 0 or gap > 5:
            own.append(NAN)
            mkt.append(NAN)
            continue
        r = math.log(rp / lp)
        if abs(r) > limit:
            own.append(NAN)
            mkt.append(NAN)
            continue
        own.append(r)
        mkt.append(math.log(right / left) if (left > 0 and right > 0) else NAN)
    return own, mkt


def _window(own, mkt, length):
    a = [x for x in own[-length:] if fin(x)] if length else []
    start = max(0, len(own) - length)
    pairs = [(own[i], mkt[i]) for i in range(start, len(own)) if fin(own[i]) and fin(mkt[i])]
    return a, pairs


def stock_bag(bars, spy_close):
    bag = {}

    def put(k, v):
        if fin(v):
            bag[k] = v
    i = len(bars) - 1
    raw = [b["c"] for b in bars]
    c = [b["adj"] for b in bars]
    dollar = dv20(bars, i)
    put("dv", math.log10(dollar) if dollar > 0 else NAN)
    put("px", raw[i])
    put("pxn", price_bucket(raw[i]))
    put("mom", _ret(c, i, 126))
    p21, p252 = _past(c, i, 21), _past(c, i, 252)
    put("mom121", p21 / p252 - 1 if (p21 > 0 and p252 > 0) else NAN)
    put("ret20", _ret(c, i, 20))
    put("ret5", _ret(c, i, 5))
    stock, market = _ret(c, i, 63), _ret(list(spy_close), i, 63)
    put("rs63", stock - market if (fin(stock) and fin(market)) else NAN)
    then = dv20(bars, i - 63)
    put("dvtrend", dollar / then - 1 if (dollar > 0 and then > 0) else NAN)
    peak, peak_at = -math.inf, -1
    frm = max(0, i - 251)
    for k in range(frm, i + 1):
        if c[k] >= peak:
            peak, peak_at = c[k], k
    if i - frm >= 200 and peak > 0:
        put("dd", c[i] / peak - 1)
        put("dsh", i - peak_at)
    sma, n50 = 0.0, 0
    for k in range(max(0, i - 49), i + 1):
        if c[k] > 0:
            sma += c[k]
            n50 += 1
    if n50 >= 45:
        put("ext50", c[i] / (sma / n50) - 1)
    spy = spy_close if len(spy_close) == len(bars) else [NAN] * len(bars)
    own, mkt = session_log_returns(bars, spy)
    short = _window(own, mkt, 63)
    span126 = _window(own, mkt, 126)
    year = _window(own, mkt, 252)
    month = _window(own, mkt, 21)
    if len(short[0]) >= 50:
        put("vol", _stdev(short[0]) * math.sqrt(252))
        rs = [p[0] for p in short[1]]
        mr = _mean(rs)
        m2 = _mean([r ** 2 for r in rs])
        m3 = _mean([r ** 3 for r in rs])
        variance = m2 - mr * mr
        if len(short[1]) >= 50 and variance > 0:
            put("skew", (m3 - 3 * mr * m2 + 2 * mr ** 3) / variance ** 1.5)
    if len(month[0]) >= 17 and len(span126[0]) >= 100:
        v21 = _stdev(month[0]) ** 2
        v126 = _stdev(span126[0]) ** 2
        if v126 > 0:
            put("volratio", math.sqrt(max(0.0, v21) / v126))
    if len(short[1]) >= 50:
        rs = [p[0] for p in short[1]]
        xs = [p[1] for p in short[1]]
        mr, mx = _mean(rs), _mean(xs)
        cov = _mean([r * xs[k] for k, r in enumerate(rs)]) - mr * mx
        vx = _stdev(xs) ** 2
        vr = _stdev(rs) ** 2
        if vx > 0 and vr > 0:
            put("corr", cov / math.sqrt(vr * vx))
            put("idio", math.sqrt(max(0.0, vr - (cov / vx) ** 2 * vx) * 252))
    if len(year[1]) >= 200:
        rs = [p[0] for p in year[1]]
        xs = [p[1] for p in year[1]]
        mr, mx = _mean(rs), _mean(xs)
        cov = _mean([r * xs[k] for k, r in enumerate(rs)]) - mr * mx
        vx = _stdev(xs) ** 2
        if vx > 1e-12:
            put("beta", cov / vx)
    max_ret = NAN
    for k in range(max(1, i - 20), i + 1):
        if not bars[k]["c"] > 0 or not bars[k - 1]["c"] > 0:
            continue
        simple = bars[k]["adj"] / bars[k - 1]["adj"] - 1
        if not fin(max_ret) or simple > max_ret:
            max_ret = simple
    put("maxret", max_ret)
    last_gap, last_sign = -1, 1
    for k in range(1, i + 1):
        ratio = _volume_ratio(bars, k)
        if not bars[k]["o"] > 0 or not bars[k - 1]["c"] > 0 or not ratio >= 2.5:
            continue
        gap = bars[k]["o"] / bars[k - 1]["c"] - 1
        if abs(gap) >= 0.04:
            last_gap = k
            last_sign = 2 if gap > 0 else 0
    if last_gap >= 0:
        put("evdays", min(252, i - last_gap))
        put("evsign", last_sign if i - last_gap <= 63 else 1)
    else:
        put("evsign", 1)
    return bag


def _recent(values, length):
    """recent(values, j, length) over the runner's last values (the last element is index j)."""
    for v in values[-length:]:
        if v:
            return 1
    return 0


def lane_history(s, index):
    last, last_sell, buys = 0, -1, 0
    for j in range(index):
        if s["primaryDir"][j] != 0:
            last = s["primaryDir"][j]
        if j >= index - 20 and (s["cyan"][j] or s["green"][j] or s["swingEvent"][j]):
            buys += 1
        if s["red"][j] or s["magenta"][j]:
            last_sell = j
    return {"prev": 0 if last == 0 else (1 if last == -1 else 2), "buys20": buys,
            "sinceSell": min(500, index - last_sell) if last_sell >= 0 else 500}


def bar_bag(s):
    """barBag(ind, mk, ex, j) at the series' last bar from the runner's values."""
    bag = {}

    def put(k, v):
        if fin(v):
            bag[k] = v
    j = s["n"] - 1
    atr = nn(s["atr14"])
    c, o, h, lo = nn(s["c"]), nn(s["o"]), nn(s["h"]), nn(s["l"])
    cprev = nn(s["cprev"])
    put("gap", o / cprev - 1 if (j > 0 and cprev > 0) else NAN)
    put("rangeatr", (h - lo) / atr if (fin(atr) and atr > 0) else NAN)
    put("closeloc", (c - lo) / (h - lo) if h > lo else NAN)
    ema21 = nn(s["ema21"])
    put("ext21", (c - ema21) / atr if (fin(atr) and atr > 0 and fin(ema21)) else NAN)
    bull = nn(s["bull"])
    put("bull", 0 if bull <= 4 else bull - 4)
    put("slow", nn(s["slowj"]) + 1)
    put("fast", nn(s["fast"]) + 1)
    ust = nn(s["utstop"])
    put("utdist", (c - ust) / atr if (fin(atr) and atr > 0 and fin(ust)) else NAN)
    put("stochk", nn(s["stochK"]))
    wt1, wt2 = nn(s["wt1"]), nn(s["wt2"])
    put("wt1", wt1)
    put("wtgap", wt1 - wt2 if (fin(wt1) and fin(wt2)) else NAN)
    put("adx", nn(s["adx"]))
    pd_, md = nn(s["plusDi"]), nn(s["minusDi"])
    put("di", pd_ - md if (fin(pd_) and fin(md)) else NAN)
    sq = nn(s["squeezeOn"])
    put("squeeze", sq if sq >= 0 else NAN)
    e200 = nn(s["ema200"])
    put("ema200", (1 if c > e200 else 0) if fin(e200) else NAN)
    put("erv", nn(s["rvol"]))
    hist = lane_history(s, j)
    put("prev", hist["prev"])
    for k, key in enumerate(["v_stoch", "v_aroon", "v_di", "v_obv", "v_squeeze", "v_pivot", "v_wave"]):
        put(key, 1 if s["votes"][k] == 1 else 0)
    put("nfire20", min(2, hist["buys20"]))
    put("sincesell", hist["sinceSell"])
    put("warning", nn(s["warning"]))
    put("weak", nn(s["weak"]))
    put("candle", nn(s["candle"]))
    put("dots", min(2, nn(s["dots"])))
    rb = nn(s["ribbon"])
    put("ribbon", NAN if rb == -2 else rb + 1)
    put("ribbonw", nn(s["ribbonWidth"]))
    put("ribbons", nn(s["ribbonSlope"]))
    mh = nn(s["macdHist"])
    put("macdpos", (1 if mh > 0 else 0) if fin(mh) else NAN)
    st = nn(s["strat"])
    put("strat", st if st >= 0 else NAN)
    oc = nn(s["ocState"])
    put("ocstate", NAN if oc == -2 else oc + 1)
    put("ocgreen", _recent(s["ocGreenDot"], 3))
    put("octri", _recent(s["ocBlueTriangle"], 3))
    put("ocblood", _recent(s["ocBlood"], 3))
    put("ocyellow", _recent(s["ocYellowX"], 3))
    put("mcdxp", nn(s["mcdxProfit"]))
    put("mcdxl", nn(s["mcdxLocked"]))
    ob = nn(s["obvDiv"])
    put("obvdiv", NAN if ob == -2 else ob + 1)
    put("dcb", _recent(s["dcbBuy"], 4))
    put("call", nn(s["activeCall"]) + 1)
    put("lifecycle", nn(s["lifecycle"]))
    age = nn(s["lastPrimaryAge"])
    put("primage", min(500, age) if age >= 0 else 500)
    put("footprint", nn(s["footprint"]))
    put("extwarn", nn(s["extWarn"]))
    put("lifestate", nn(s["lifeState"]))
    put("swingscore", max(0, nn(s["swingScore"]) - 5))
    put("phenotype", nn(s["phenotype"]))
    last_buy = last_cyan = run_start = -1
    last_run = NAN
    reg = s["regime"]
    for k in range(j):
        regime = reg[k]
        if regime == -1 and (k == 0 or reg[k - 1] != -1):
            run_start = k
        if regime == 1 and k > 0 and reg[k - 1] == -1 and run_start >= 0:
            last_run = k - run_start
        if s["cyan"][k] or s["green"][k] or s["swingEvent"][k]:
            last_buy = k
        if s["cyan"][k]:
            last_cyan = k
    put("cyanrecent", 1 if (last_cyan >= 0 and j - last_cyan <= 10) else 0)
    put("sincebuy", min(500, j - last_buy) if last_buy >= 0 else 500)
    put("bearrun", last_run)
    return bag


def prepare(clock, points, engine_out):
    """prepare(): valid bars (>= 60) + the runner's daily / weekly series; weekly days = the session of each week's
    last daily bar."""
    bars = valid_bars(clock, points)
    if len(bars) < 60 or engine_out is None:
        return None
    w = engine_out.get("w")
    weekly = None
    if w is not None:
        days = [bars[i]["day"] if 0 <= i < len(bars) else "" for i in engine_out["wlast"]]
        weekly = {"s": w, "days": days, "day": days[-1] if days else ""}
    return {"bars": bars, "d": engine_out["d"], "n": engine_out["n"], "weekly": weekly}


def _sma(values, index, length):
    if index < length - 1:
        return NAN
    s, n = 0.0, 0
    for k in range(index - length + 1, index + 1):
        if values[k] > 0:
            s += values[k]
            n += 1
    return s / n if n >= length * 0.9 else NAN


def market_bag(panel, names, as_of):
    bag = {}

    def put(k, v):
        if fin(v):
            bag[k] = v
    spy = names.get("SPY")
    clock = panel["clock"]
    i = clock.index(as_of) if as_of in clock else -1
    put("vix", panel["vixLast"] if (panel.get("vixLast") is not None and panel["vixLast"] > 0) else NAN)
    vix = panel.get("vixCloses") or []
    if len(vix) == len(clock) and i >= 19:
        sl = [v for v in vix[i - 19:i + 1] if v > 0]
        if len(sl) >= 15 and vix[i] > 0:
            put("vixrel", vix[i] / _mean(sl))
    v3 = names.get("^VIX3M")
    if v3 and panel.get("vixLast") and v3["bars"][-1]["day"] == as_of and v3["bars"][-1]["c"] > 0:
        put("vixts", panel["vixLast"] / v3["bars"][-1]["c"])

    def rel(sym, key):
        series, sp = names.get(sym), names.get("SPY")
        if not series or not sp or series["bars"][-1]["day"] != as_of or sp["bars"][-1]["day"] != as_of:
            return
        a = [b["adj"] for b in series["bars"]]
        m = [b["adj"] for b in sp["bars"]]
        stock, market = _ret(a, len(a) - 1, 63), _ret(m, len(m) - 1, 63)
        if fin(stock) and fin(market):
            absolute = key in ("tlt63", "gld63", "oil63", "btc63", "uup63")
            put(key, stock if absolute else stock - market)
    for sym, key in (("IWM", "iwmrel"), ("QQQ", "qqqrel"), ("SMH", "smhrel"), ("TLT", "tlt63"), ("GLD", "gld63"),
                     ("USO", "oil63"), ("UUP", "uup63"), ("BTC-USD", "btc63")):
        rel(sym, key)
    hyg, ief = names.get("HYG"), names.get("IEF")
    if hyg and ief and hyg["bars"][-1]["day"] == as_of and ief["bars"][-1]["day"] == as_of:
        a, b = [x["adj"] for x in hyg["bars"]], [x["adj"] for x in ief["bars"]]
        credit, treasury = _ret(a, len(a) - 1, 63), _ret(b, len(b) - 1, 63)
        if fin(credit) and fin(treasury):
            put("credit63", credit - treasury)
    if spy and spy["bars"][-1]["day"] == as_of:
        closes = [b["adj"] for b in spy["bars"]]
        last = len(closes) - 1
        put("spy20", _ret(closes, last, 20))
        put("spy63", _ret(closes, last, 63))
        avg = _sma(closes, last, 200)
        if fin(avg):
            put("spy200", 1 if closes[last] > avg else 0)
        put("spycons", spy["d"]["consensus"][spy["n"] - 1])
        if spy["weekly"]:
            use = week_index(spy["weekly"]["days"], as_of)
            if use >= 0:
                put("spywkut", 1 if spy["weekly"]["s"]["regime"][use] == 1 else 0)
    for sym, key in (("QQQ", "qqqwkut"), ("IWM", "iwmwkut"), ("SMH", "smhwkut")):
        series = names.get(sym)
        if not series or not series["weekly"]:
            continue
        use = week_index(series["weekly"]["days"], as_of)
        if use >= 0:
            put(key, 1 if series["weekly"]["s"]["regime"][use] == 1 else 0)

    stock_names = [(s, x) for s, x in names.items() if s not in MARKET and not s.startswith("^")]
    day_index = {s: {b["day"]: k for k, b in enumerate(x["bars"])} for s, x in stock_names}
    adjs = {s: [b["adj"] for b in x["bars"]] for s, x in stock_names}

    def breadth_at(day):
        up = count = 0
        for s, x in stock_names:
            index = day_index[s].get(day, -1)
            if index < 49:
                continue
            avg_ = _sma(adjs[s], index, 50)
            if not fin(avg_):
                continue
            count += 1
            if adjs[s][index] > avg_:
                up += 1
        return up / count if count >= 40 else NAN
    breadth = breadth_at(as_of)
    put("breadth", breadth)
    prior_day = clock[i - 10] if i - 10 >= 0 else None
    if prior_day and fin(breadth):
        prior = breadth_at(prior_day)
        if fin(prior):
            put("breadthchg", breadth - prior)
        if fin(prior):
            lo = breadth
            for k in range(i - 10, i + 1):
                value = breadth_at(clock[k])
                if fin(value):
                    lo = min(lo, value)
            put("thrust", 1 if (breadth > 0.615 and lo < 0.4) else 0)
    returns = []
    for k in range(max(1, i - 20), i + 1):
        day, prev = clock[k], clock[k - 1]
        sample = []
        for s, x in stock_names:
            bi, pi = day_index[s].get(day), day_index[s].get(prev)
            if bi is None or pi is None:
                continue
            bar, before = x["bars"][bi], x["bars"][pi]
            if not before["c"] > 0:
                continue
            r = bar["adj"] / before["adj"] - 1
            if abs(math.log(1 + r)) > math.log(8):
                continue
            sample.append(r)
        if len(sample) >= 40:
            returns.append(sample)
    if len(returns) >= 15:
        put("disp", _mean([_stdev(sm) for sm in returns]))
    from datetime import date
    d = date.fromisoformat(as_of)
    put("month", d.month - 1)
    put("dow", d.weekday())
    put("tom", turn_of_month(as_of, clock))
    put("prefomc", 1 if fomc_within(as_of, 5) else 0)
    put("postfomc", 1 if any(x <= as_of and M.sessions_after(x, as_of) <= 5 for x in FOMC_DECISIONS) else 0)
    put("opex", 1 if opex_week(as_of) else 0)
    return bag


def htf_bag(prep, as_of):
    bag = {}
    w = prep["weekly"]
    if not w:
        return bag
    s = w["s"]
    n = len(w["days"])
    clock = htf_from_weeks([b["day"] for b in prep["bars"]], w["days"],
                           [bool(s["cyan"][k] or s["green"][k] or s["swingEvent"][k]) for k in range(n)],
                           [s["cyan"][k] == 1 for k in range(n)], as_of)
    if not clock:
        return bag
    use = clock["week"]
    bag["htfcons"] = s["consensus"][use]
    bag["htfut"] = 1 if s["regime"][use] == 1 else 0
    bag["htfslow"] = 1 if s["slow"][use] == 1 else 0
    bag["htfsince"] = clock["htfsince"]
    bag["htfcyan"] = clock["htfcyan"]
    return bag


# -- gbm.ts ------------------------------------------------------------------------------------------------------
_MODEL = {}


def load_model(path=MODEL_PATH):
    if path not in _MODEL:
        raw = json.load(open(path))
        raw["index"] = {k: i for i, k in enumerate(raw["features"])}
        _MODEL[path] = raw
    return _MODEL[path]


def bin_of(model, key, value):
    i = model["index"].get(key)
    if i is None or not fin(value):
        return 0
    cuts = model["binCuts"][i]
    if cuts:
        k = 0
        while k < len(cuts) and value > cuts[k]:
            k += 1
        return k + 1
    return min(15, max(0, M.js_round(value) + 1))


def bins_for(model, values):
    bins = [0] * len(model["features"])
    for key, value in values.items():
        i = model["index"].get(key)
        if i is None:
            continue
        bins[i] = bin_of(model, key, value) % 256
    return bins


def walk_tree(node, bins):
    while True:
        if node.get("v") is not None:
            return node["v"]
        if node.get("f") is None or node.get("c") is None or not node.get("l") or not node.get("r"):
            return 0
        node = node["l"] if bins[node["f"]] <= node["c"] else node["r"]


def score_cyan(values, model=None):
    model = model or load_model()
    bins = bins_for(model, values)
    score = model["base"]
    for tree in model["trees"]:
        score += walk_tree(tree, bins)
    filled = sum(1 for k in model["features"] if fin(values.get(k)))
    return {"score": score, "cut": model["cut"], "filled": filled, "total": len(model["features"])}


# -- forward.ts specs -----------------------------------------------------------------------------------------------
def _f(bag, key):
    v = bag.get(key)
    return v if fin(v) else None


def _inside(v, lo, hi):
    return v is not None and lo <= v <= hi


def _t_gbm(row):
    if not row["dailyCyan"] or row["score"] is None:
        return None
    return f"score {to_fixed(row['score'], 5)}"


def _t_breadth(row):
    if not row["weeklyCyan"]:
        return None
    dv, slow, chg = _f(row["daily"], "dv"), _f(row["weekly"], "slow"), _f(row["daily"], "breadthchg")
    if dv is None or dv > 6.92 or slow != 2 or chg is None or chg < 0.037:
        return None
    return f"dv {to_fixed(dv, 2)} · breadth {to_fixed(chg, 3)}"


def _t_vix(row):
    if not row["weeklyCyan"]:
        return None
    dv, mom, vix = _f(row["daily"], "dv"), _f(row["daily"], "mom"), _f(row["daily"], "vix")
    if dv is None or dv > 7.36 or mom is None or mom < 0.441 or not _inside(vix, 13.71, 26.38):
        return None
    return f"dv {to_fixed(dv, 2)} · 126d {to_fixed(mom * 100, 0)}% · VIX {to_fixed(vix, 1)}"


def _t_green_band(row):
    if not row["dailyGreen"]:
        return None
    px, disp, ev = _f(row["daily"], "px"), _f(row["daily"], "disp"), _f(row["daily"], "evdays")
    if not _inside(px, 10, 20) or not _inside(disp, 0.021, 0.029) or not _inside(ev, 32, 252):
        return None
    return f"${to_fixed(px, 2)} · disp {to_fixed(disp, 3)} · gap age {to_fixed(ev, 0)}"


def _t_green_smh(row):
    if not row["weeklyGreen"]:
        return None
    skew, smh, pre = _f(row["daily"], "skew"), _f(row["daily"], "smhrel"), _f(row["daily"], "prefomc")
    if not _inside(skew, -0.68, 0.472) or not _inside(smh, -0.049, 0.097) or pre != 0:
        return None
    return f"skew {to_fixed(skew, 2)} · SMH−SPY {to_fixed(smh, 3)}"


def _t_adx(row):
    if not row["weeklyCyan"]:
        return None
    dv, mom, adx = _f(row["daily"], "dv"), _f(row["daily"], "mom"), _f(row["weekly"], "adx")
    if dv is None or dv > 7.35 or mom is None or mom < 0.445 or adx is None or adx < 25.8:
        return None
    return f"dv {to_fixed(dv, 2)} · 126d {to_fixed(mom * 100, 0)}% · ADX {to_fixed(adx, 1)}"


FORWARD_SPECS = [
    {"id": "gbm-1d-cyan", "label": "Daily cyan GBM", "ruleId": "V4-GBM-1D-CYAN-ALL", "holdSessions": 21, "test": _t_gbm},
    {"id": "w-cyan-breadth", "label": "Weekly cyan, quiet tape", "ruleId": "V4-1W-CYAN-RAW-H126-COV-7332415a",
     "holdSessions": 126, "test": _t_breadth},
    {"id": "w-cyan-vix", "label": "Weekly cyan, mid VIX", "ruleId": "V4-1W-CYAN-RAW-H252-COV-bcd9f74d",
     "holdSessions": 252, "test": _t_vix},
    {"id": "d-green-band", "label": "Daily green, $10–20", "ruleId": "V4-1D-GREEN-RAW-H21-ALL-879f9d43",
     "holdSessions": 21, "test": _t_green_band},
    {"id": "w-green-smh", "label": "Weekly green, calm SMH", "ruleId": "V4-1W-GREEN-TAIL-H126-ALL-fb459d4f",
     "holdSessions": 126, "test": _t_green_smh},
    {"id": "w-cyan-adx", "label": "Weekly cyan, high ADX", "ruleId": "V2-1W-CYAN-RAW-H126-f10092bc",
     "holdSessions": 126, "test": _t_adx},
]


def hits_for(row, cut):
    hits = []
    for spec in FORWARD_SPECS:
        if spec["id"] == "gbm-1d-cyan" and (cut is None or row["score"] is None or row["score"] < cut):
            continue
        detail = spec["test"](row)
        if not detail:
            continue
        hits.append({"accountId": spec["id"], "sym": row["sym"],
                     "score": row["score"] if spec["id"] == "gbm-1d-cyan" else None,
                     "flag": f"{spec['ruleId']}. {detail}"})
    return hits


def _hit_order(h):
    return (-(h["score"]) if h["score"] is not None else math.inf, h["sym"])


def cap_hits(hits):
    out = []
    for spec in FORWARD_SPECS:
        mine = sorted([h for h in hits if h["accountId"] == spec["id"]], key=_hit_order)
        out += mine[:FORWARD_SLOTS]
    return out


def scan_forward(panel, engine_out, model=None):
    """scanForward(panel) -> {hits, blocked, cyan, green, rows}; engine_out = the runner's output per symbol."""
    as_of = panel["asOf"]
    clock = panel["clock"]
    index = clock.index(as_of) if as_of in clock else -1
    if index < 80:
        return {"hits": [], "blocked": True, "cyan": 0, "green": 0, "why": "Not enough sessions."}
    sample = panel["series"].get(panel["universe"][0] if panel["universe"] else "SPY") or []
    probe = next((p for p in sample if p["close"] > 0), None)
    if not probe or not probe.get("open") or not probe.get("low"):
        return {"hits": [], "blocked": True, "cyan": 0, "green": 0, "why": "Open and low are missing."}
    names = {}
    for sym in list(panel["universe"]) + MARKET + ["^VIX3M"]:
        prep = prepare(clock, panel["series"].get(sym), (engine_out or {}).get(sym))
        if prep:
            names[sym] = prep
    spy = names.get("SPY")
    if not spy or spy["bars"][-1]["day"] != as_of:
        return {"hits": [], "blocked": True, "cyan": 0, "green": 0, "why": "SPY bars are short."}
    market = market_bag(panel, names, as_of)
    closed = M.week_just_closed(as_of)
    hits, rows = [], []
    cyan_d = green_d = 0
    cut = None
    spy_by_day = {}
    for b in spy["bars"]:
        spy_by_day.setdefault(b["day"], b["adj"])
    for sym in panel["universe"]:
        prep = names.get(sym)
        if not prep or prep["bars"][-1]["day"] != as_of:
            continue
        dollar = dv20(prep["bars"], len(prep["bars"]) - 1)
        price = prep["bars"][-1]["c"]
        if not price >= 5 or not dollar >= 1_000_000:
            continue
        spy_close = [spy_by_day.get(b["day"], NAN) for b in prep["bars"]]
        daily = dict(market)
        daily.update(stock_bag(prep["bars"], spy_close))
        daily.update(bar_bag(prep["d"]))
        daily.update(htf_bag(prep, as_of))
        j = prep["n"] - 1
        d_cyan = prep["d"]["cyan"][j] == 1
        d_green = prep["d"]["green"][j] == 1
        cyan_d += d_cyan
        green_d += d_green
        w_cyan = w_green = False
        weekly = {}
        if closed and prep["weekly"] and prep["weekly"]["day"] == as_of:
            ws = prep["weekly"]["s"]
            wj = ws["n"] - 1
            w_cyan = ws["cyan"][wj] == 1
            w_green = ws["green"][wj] == 1
            weekly = bar_bag(ws)
        score = None
        if d_cyan:
            sc = score_cyan(daily, model)
            score, cut = sc["score"], sc["cut"]
        row = {"sym": sym, "dailyCyan": d_cyan, "dailyGreen": d_green, "weeklyCyan": w_cyan, "weeklyGreen": w_green,
               "daily": daily, "weekly": weekly, "score": score}
        rows.append(row)
        hits += hits_for(row, cut)
    return {"hits": cap_hits(hits), "blocked": False, "cyan": cyan_d, "green": green_d, "rows": rows}


def runner_input(panel):
    """the runner's names: every prepared symbol's valid bars (forward-scan prepare order)."""
    out, seen = [], set()
    for sym in list(panel["universe"]) + MARKET + ["^VIX3M"]:
        if sym in seen:
            continue
        seen.add(sym)
        bars = valid_bars(panel["clock"], panel["series"].get(sym))
        if len(bars) < 60:
            continue
        out.append({"sym": sym, "day": [b["day"] for b in bars], "o": [b["o"] for b in bars], "h": [b["h"] for b in bars],
                    "l": [b["l"] for b in bars], "c": [b["c"] for b in bars], "v": [b["v"] for b in bars]})
    return out
