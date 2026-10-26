"""The historical Galath seven-vote Anna printer — line-by-line port of galath-desk @7683c7dd
src/lib/tensor/anna-replica.ts (buildAnnaReplica, the last version before Tensor 2.0 retired it at a7864c6f) with
its printer (anna-printer.ts), epochs (anna-epochs.ts) and the indicators it reads (tensor/indicators.ts, math.ts —
the same blobs as @652db7af). Bars are dicts {t (epoch ms), o, h, l, c, v}. Parity: tools/parity/galath_anna.py."""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import tensor as T

INF = float("inf")
MIN_REPLICA_BARS = 35
AUTHORITY_BARS = 200
_ET = ZoneInfo("America/New_York")


def _et_ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=_ET).timestamp() * 1000)


# anna-epochs.ts: Date.parse("2026-MM-DDT00:00:00-04:00")
EPOCHS = [(0, {"id": "E0", "squeezeLength": 14, "momentumLength": 9}),
          (int(datetime(2026, 4, 11, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E1", "squeezeLength": 14, "momentumLength": 9}),
          (int(datetime(2026, 4, 16, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E2", "squeezeLength": 14, "momentumLength": 9}),
          (int(datetime(2026, 4, 27, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E3", "squeezeLength": 14, "momentumLength": 9}),
          (int(datetime(2026, 5, 22, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E4", "squeezeLength": 14, "momentumLength": 9}),
          (int(datetime(2026, 6, 17, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E4b", "squeezeLength": 20, "momentumLength": 10}),
          (int(datetime(2026, 7, 26, 4, tzinfo=timezone.utc).timestamp() * 1000), {"id": "E5", "squeezeLength": 20, "momentumLength": 10})]


# the gospel backup (galath-desk-backup @3e93f984, 2026-08-13) anna-epochs.ts: E4 from 05-22 already on 20 / 10
EPOCHS_GOSPEL = EPOCHS[:4] + [(EPOCHS[4][0], {"id": "E4", "squeezeLength": 20, "momentumLength": 10}), EPOCHS[6]]


def epoch_at(t, variant=None):
    table = EPOCHS_GOSPEL if variant == "gospel" else EPOCHS
    cur = table[0][1]
    for frm, params in table:
        if t >= frm:
            cur = params
    return cur


# -- indicators.ts (the replica's) -------------------------------------------------------------------------------------
def stoch_rsi(closes, rsi_len=14, stoch_len=14, k_len=3, d_len=3):
    r = T.rsi(closes, rsi_len)
    raw = [None] * len(closes)
    for i in range(len(r)):
        if r[i] is None:
            continue
        hi = T.highest(r, stoch_len, i)
        lo = T.lowest(r, stoch_len, i)
        if hi is None or lo is None or hi == lo:
            if hi is not None and lo is not None:
                raw[i] = 50
            continue
        raw[i] = (r[i] - lo) / (hi - lo) * 100
    k = T.sma(raw, k_len)
    return {"k": k, "d": T.sma(k, d_len)}


def aroon(bars, length=14):
    up = [None] * len(bars)
    down = [None] * len(bars)
    for i in range(length, len(bars)):
        hi_i = lo_i = i
        for j in range(i - length, i + 1):
            if bars[j]["h"] >= bars[hi_i]["h"]:
                hi_i = j
            if bars[j]["l"] <= bars[lo_i]["l"]:
                lo_i = j
        up[i] = (100 * (length - (i - hi_i))) / length
        down[i] = (100 * (length - (i - lo_i))) / length
    return {"up": up, "down": down}


def adx(bars, length=14):
    plus_dm = [None] * len(bars)
    minus_dm = [None] * len(bars)
    tr = T.true_range(bars)
    for i in range(1, len(bars)):
        up = bars[i]["h"] - bars[i - 1]["h"]
        dn = bars[i - 1]["l"] - bars[i]["l"]
        plus_dm[i] = up if (up > dn and up > 0) else 0
        minus_dm[i] = dn if (dn > up and dn > 0) else 0
    sm_tr, sm_p, sm_m = T.wilder(tr, length), T.wilder(plus_dm, length), T.wilder(minus_dm, length)
    pdi = [None] * len(bars)
    mdi = [None] * len(bars)
    dx = [None] * len(bars)
    for i in range(len(bars)):
        if sm_tr[i] is None or sm_tr[i] == 0 or sm_p[i] is None or sm_m[i] is None:
            continue
        pdi[i] = (100 * sm_p[i]) / sm_tr[i]
        mdi[i] = (100 * sm_m[i]) / sm_tr[i]
        den = pdi[i] + mdi[i]
        dx[i] = 0 if den == 0 else (100 * abs(pdi[i] - mdi[i])) / den
    return {"plusDI": pdi, "minusDI": mdi, "adx": T.wilder(dx, length)}


def wave_trend(bars, ch=10, avg=21, smooth=4):
    hlc3 = [(b["h"] + b["l"] + b["c"]) / 3 for b in bars]
    esa = T.ema(hlc3, ch)
    dev = [None if esa[i] is None else abs(v - esa[i]) for i, v in enumerate(hlc3)]
    d = T.ema(dev, ch)
    ci = [None if (esa[i] is None or d[i] is None or d[i] == 0) else (v - esa[i]) / (0.015 * d[i])
          for i, v in enumerate(hlc3)]
    wt1 = T.ema(ci, avg)
    return {"wt1": wt1, "wt2": T.sma(wt1, smooth)}


def obv(bars):
    out = [None] * len(bars)
    acc = 0.0
    for i, b in enumerate(bars):
        if i == 0:
            acc = b["v"]
        elif b["c"] > bars[i - 1]["c"]:
            acc += b["v"]
        elif b["c"] < bars[i - 1]["c"]:
            acc -= b["v"]
        out[i] = acc
    return out


def squeeze(bars, length, mom_len):
    closes = T.series(bars, "c")
    mid = T.sma(closes, length)
    sd = T.stdev(closes, length)
    atr = T.wilder(T.true_range(bars), length)
    bb_u = [None if (m is None or sd[i] is None) else m + 2 * sd[i] for i, m in enumerate(mid)]
    bb_l = [None if (m is None or sd[i] is None) else m - 2 * sd[i] for i, m in enumerate(mid)]
    kc_u = [None if (m is None or atr[i] is None) else m + 2 * atr[i] for i, m in enumerate(mid)]
    kc_l = [None if (m is None or atr[i] is None) else m - 2 * atr[i] for i, m in enumerate(mid)]
    squeezed = [False if (bb_u[i] is None or kc_u[i] is None or bb_l[i] is None or kc_l[i] is None)
                else (bb_u[i] < kc_u[i] and bb_l[i] > kc_l[i]) for i in range(len(mid))]
    highs, lows = T.series(bars, "h"), T.series(bars, "l")
    src = []
    for i, c in enumerate(closes):
        hh = T.highest(highs, length, i)
        ll = T.lowest(lows, length, i)
        if hh is None or ll is None or mid[i] is None:
            src.append(None)
            continue
        src.append(c - ((hh + ll) / 2 + mid[i]) / 2)
    return {"bbUpper": bb_u, "bbMid": mid, "bbLower": bb_l, "kcUpper": kc_u, "kcLower": kc_l, "squeezed": squeezed,
            "mom": T.linreg_endpoint(src, mom_len)}


def ut_bot(bars, atr_len=10, sensitivity=1):
    atr = T.wilder(T.true_range(bars), atr_len)
    stop = [None] * len(bars)
    dr = [None] * len(bars)
    for i, b in enumerate(bars):
        if atr[i] is None:
            continue
        n_loss = sensitivity * atr[i]
        close = b["c"]
        if i == 0 or stop[i - 1] is None or dr[i - 1] is None:
            stop[i] = close - n_loss
            dr[i] = 1
            continue
        ps = stop[i - 1]
        pc = bars[i - 1]["c"]
        if close > ps and pc > ps:
            stop[i] = max(ps, close - n_loss)
            dr[i] = 1
        elif close < ps and pc < ps:
            stop[i] = min(ps, close + n_loss)
            dr[i] = -1
        elif close > ps:
            stop[i] = close - n_loss
            dr[i] = 1
        else:
            stop[i] = close + n_loss
            dr[i] = -1
    return {"stop": stop, "dir": dr}


def strat(bars):
    out = [None] * len(bars)
    for i in range(1, len(bars)):
        b, p = bars[i], bars[i - 1]
        inside = b["h"] < p["h"] and b["l"] > p["l"]
        outside = b["h"] > p["h"] and b["l"] < p["l"]
        up = b["h"] > p["h"] and b["l"] >= p["l"]
        down = b["l"] < p["l"] and b["h"] <= p["h"]
        out[i] = "1" if inside else "3" if outside else "2U" if up else "2D" if down else None
    return out


def session_vwap(bars):
    out = [None] * len(bars)
    day = ""
    pv = vol = 0.0
    for i, b in enumerate(bars):
        key = T.et_parts(b["t"])["ymd"]
        if key != day:
            day = key
            pv = vol = 0.0
        typical = (b["h"] + b["l"] + b["c"]) / 3
        pv += typical * b["v"]
        vol += b["v"]
        out[i] = pv / vol if vol > 0 else None
    return out


def slope(values, lookback, i):
    a = values[i] if 0 <= i < len(values) else None
    j = i - lookback
    b = values[j] if 0 <= j < len(values) else None
    if a is None or b is None:
        return None
    return a - b


# -- anna-printer.ts ---------------------------------------------------------------------------------------------------
OPTS = {"deepRel": 0.65, "minBull": 5, "invertLaunchpadSell": True, "warnUpgrade": False, "padSequence": True,
        "supportBounce": True, "reclaimAllowRed": True, "warnConfirm": True, "holdCyan": False, "holdLook": 22,
        "holdRel": 0.94, "holdLast": True, "holdLastBars": 2}


def _range_stats(rep, i, look):
    lo = max(0, i - look + 1)
    hi, lw, min_c = -INF, INF, INF
    for j in range(lo, i + 1):
        b = rep[j]["bar"]
        if b["h"] > hi:
            hi = b["h"]
        if b["l"] < lw:
            lw = b["l"]
        if b["c"] < min_c:
            min_c = b["c"]
    return hi, lw, min_c


def _last_flip(rep, i):
    for j in range(i - 1, -1, -1):
        m = rep[j]["marker"]
        if m in ("CYAN_BUY", "GREEN_BUY"):
            return "buy", i - j
        if m in ("RED_SELL", "MAGENTA_SELL"):
            return "sell", i - j
    return None


def _recent_buy_print(rep, i, look):
    for j in range(max(0, i - look), i):
        if rep[j]["marker"] in ("CYAN_BUY", "GREEN_BUY"):
            return True
    return False


def classify_location(rep, i, days_above, prev_above, bull=0, marker=None, o=OPTS):
    r = rep[i]
    prev = rep[i - 1] if i >= 1 else None
    hi, lw, _ = _range_stats(rep, i, 20)
    _, _, min_c15 = _range_stats(rep, i, 15)
    rng = hi - lw
    bar = r["bar"]
    pos20 = (bar["c"] - lw) / rng if rng > 0 else 0.5
    dd = (hi - min_c15) / hi if hi > 0 else 0
    above = r["ema200"] is not None and bar["c"] > r["ema200"]
    rel = bar["c"] / r["ema200"] if (r["ema200"] is not None and r["ema200"] > 0) else 1
    reclaim = above and not prev_above
    bb_span = r["bbUpper"] - r["bbLower"] if (r["bbUpper"] is not None and r["bbLower"] is not None) else 0
    bb_pct = (bar["c"] - r["bbLower"]) / bb_span if (bb_span > 0 and r["bbLower"] is not None) else None
    stoch = r["stochK"]
    washout = dd >= 0.18 and days_above <= 2 and pos20 <= 0.65
    deep_pad = not above and rel <= o["deepRel"]
    failed_euph = not above and pos20 >= 0.88 and (bb_pct if bb_pct is not None else 0) >= 1.2 and \
        (stoch if stoch is not None else 0) >= 88
    loc = "above" if above else "below"
    if reclaim:
        loc = "reclaim"
    elif deep_pad or washout:
        loc = "launchpad"
    elif failed_euph:
        loc = "failed_euphoria"
    elif days_above >= 8 and pos20 >= 0.88 and (bb_pct if bb_pct is not None else 0) >= 0.85 and \
            (stoch if stoch is not None else 0) >= 85:
        loc = "extended"
    elif r["ema200"] is not None and abs(bar["c"] - r["ema200"]) <= \
            (r["atr14"] if r["atr14"] is not None else bar["c"] * 0.01) * 0.6:
        loc = "fight"
    prior_hi = bar["h"]
    if i >= 1:
        prior_hi = -INF
        for j in range(max(0, i - 3), i):
            prior_hi = max(prior_hi, rep[j]["bar"]["h"])
    failed_break = bar["h"] < prior_hi
    extra_buy = reclaim and bb_pct is not None and 0.35 <= bb_pct <= 0.92 and \
        (o["reclaimAllowRed"] or bar["c"] >= bar["o"])
    ext_fail = loc == "extended" and failed_break
    extra_sell = failed_euph or ext_fail
    invert = o["invertLaunchpadSell"] and deep_pad and not failed_euph and bull >= o["minBull"] and \
        marker in ("RED_SELL", "MAGENTA_SELL")
    flip = _last_flip(rep, i)
    suppress = ((o["holdLast"] and flip is not None and flip[0] == "buy" and flip[1] <= o["holdLastBars"]) or
                (o["holdCyan"] and _recent_buy_print(rep, i, o["holdLook"]))) and not failed_euph and rel >= o["holdRel"]
    upgrade = o["warnUpgrade"] and marker == "GOLD_WARNING" and not failed_euph and bull >= 6 and 0.88 <= rel <= 1.02 \
        and bb_pct is not None and 0.35 <= bb_pct <= 1.05
    cooled = _recent_buy_print(rep, i, 8)
    sq_up = r["squeezeMom"] is not None and prev is not None and prev["squeezeMom"] is not None and \
        r["squeezeMom"] > prev["squeezeMom"]
    inside_band = bb_pct is not None and 0.2 <= bb_pct <= 1.05
    pad_seq = o["padSequence"] and not cooled and (deep_pad or washout) and not failed_euph and not above and \
        bull >= 6 and sq_up and inside_band and bar["c"] >= bar["o"]
    lo10 = INF
    for j in range(max(0, i - 9), i + 1):
        lo10 = min(lo10, rep[j]["bar"]["l"])
    near_support = r["atr14"] is not None and math.isfinite(lo10) and bar["l"] - lo10 <= 1.5 * r["atr14"]
    bounce = o["supportBounce"] and not cooled and not failed_euph and not ext_fail and bull >= 5 and \
        0.82 <= rel <= 1.04 and inside_band and bar["c"] >= bar["o"] and 0.35 <= pos20 <= 0.85 and near_support
    warn_confirm = o["warnConfirm"] and prev is not None and prev["marker"] == "GOLD_WARNING" and not failed_euph and \
        not ext_fail and bull >= 5 and 0.88 <= rel <= 1.05 and bb_pct is not None and 0.2 <= bb_pct <= 1.05
    return {"loc": loc, "extraBuy": extra_buy, "extraSell": extra_sell, "invertToBuy": invert,
            "suppressSell": suppress, "upgradeWarn": upgrade, "padSeqBuy": pad_seq, "bounceBuy": bounce,
            "warnConfirmBuy": warn_confirm, "washout": washout, "deepPad": deep_pad, "bbPct": bb_pct, "pos20": pos20,
            "daysAbove": days_above, "dd": dd, "rel": rel}


def apply_printer(marker, snap):
    if snap["suppressSell"] and marker in ("RED_SELL", "MAGENTA_SELL") and not snap["extraSell"]:
        return None
    return marker


# -- anna-replica.ts ---------------------------------------------------------------------------------------------------
def _vote(name, bull, available):
    if not available:
        return {"name": name, "value": 0, "available": False}
    if bull is None:
        return {"name": name, "value": 0, "available": True}
    return {"name": name, "value": 1 if bull else -1, "available": True}


def build_anna_replica(bars, variant=None):
    """variant "gospel": the gospel backup's anna-replica.ts (5eda32b5) — on a same-bar buy / sell clash the buy marker
    wins (assigned last) and the E4 epoch already reads the squeeze on 20 / 10."""
    if len(bars) < MIN_REPLICA_BARS:
        return []
    closes = T.series(bars, "c")
    ema8, ema13, ema21 = T.ema(closes, 8), T.ema(closes, 13), T.ema(closes, 21)
    ema34, ema48, ema200 = T.ema(closes, 34), T.ema(closes, 48), T.ema(closes, 200)
    ep = epoch_at(bars[-1]["t"], variant)
    sq = squeeze(bars, ep["squeezeLength"], ep["momentumLength"])
    st = stoch_rsi(closes)
    ar = aroon(bars, 14)
    di = adx(bars, 14)
    ob = obv(bars)
    wt = wave_trend(bars)
    md = T.macd(closes)
    rsi14 = T.rsi(closes, 14)
    atr14 = T.wilder(T.true_range(bars), 14)
    rvol = T.relative_volume(bars, 20)
    vwap = session_vwap(bars)
    strat_s = strat(bars)
    ut, ut2, ut3 = ut_bot(bars, 10, 1), ut_bot(bars, 10, 2), ut_bot(bars, 10, 3)
    rep = []
    for i, bar in enumerate(bars):
        votes = []
        k, d = st["k"][i], st["d"][i]
        k_slope = slope(st["k"], 1, i)
        stoch_bull = None
        if k is not None and d is not None:
            stoch_bull = (None if k_slope is None else k_slope > 0) if k == d else k > d
        votes.append(_vote("stoch", stoch_bull, k is not None and d is not None))
        au, ad = ar["up"][i], ar["down"][i]
        votes.append(_vote("aroon", None if (au is None or ad is None) else au > ad, au is not None and ad is not None))
        p, m = di["plusDI"][i], di["minusDI"][i]
        votes.append(_vote("di", None if (p is None or m is None) else p > m, p is not None and m is not None))
        obv_sl = slope(ob, 5, i)
        votes.append(_vote("obv", None if obv_sl is None else obv_sl > 0, obv_sl is not None))
        sq_slope = slope(sq["mom"], 1, i)
        sq_sign = None if sq["mom"][i] is None else sq["mom"][i] >= 0
        votes.append(_vote("squeeze", (sq_slope > 0) if sq_slope is not None else sq_sign, sq["mom"][i] is not None))
        e8, e21 = ema8[i], ema21[i]
        votes.append(_vote("ema", None if (e8 is None or e21 is None) else e8 > e21, e8 is not None and e21 is not None))
        w1, w2 = wt["wt1"][i], wt["wt2"][i]
        votes.append(_vote("wavetrend", None if (w1 is None or w2 is None) else w1 > w2,
                           w1 is not None and w2 is not None))
        avail = [v for v in votes if v["available"]]
        bull = len([v for v in avail if v["value"] == 1])
        bear = len([v for v in avail if v["value"] == -1])
        dirs = [ut["dir"][i], ut2["dir"][i], ut3["dir"][i]]
        rep.append({"bar": bar, "ema8": ema8[i], "ema13": ema13[i], "ema21": ema21[i], "ema34": ema34[i],
                    "ema48": ema48[i], "ema200": ema200[i], "bbUpper": sq["bbUpper"][i], "bbMid": sq["bbMid"][i],
                    "bbLower": sq["bbLower"][i], "kcUpper": sq["kcUpper"][i], "kcLower": sq["kcLower"][i],
                    "squeezed": sq["squeezed"][i], "squeezeMom": sq["mom"][i], "stochK": k, "stochD": d,
                    "aroonUp": au, "aroonDown": ad, "plusDI": p, "minusDI": m, "adx": di["adx"][i], "obv": ob[i],
                    "obvSlope": obv_sl, "wt1": w1, "wt2": w2, "macd": md["line"][i], "macdSignal": md["signal"][i],
                    "macdHist": md["hist"][i], "rsi14": rsi14[i], "atr14": atr14[i], "rvol": rvol[i], "vwap": vwap[i],
                    "strat": strat_s[i], "utStop": ut["stop"][i], "utDir": ut["dir"][i],
                    "sellDotTiers": len([x for x in dirs if x == -1]), "buyDotTiers": len([x for x in dirs if x == 1]),
                    "regime": None, "votes": votes, "bullShare": (bull / len(avail)) if avail else None,
                    "resultant": None if not avail else (100 * (bull - bear)) / 7,
                    "coherence": None if not avail else max(bull, bear) / len(avail),
                    "marker": None, "signal": None, "location": "below", "glyphs": []})
    prev_regime = None
    raw_prev = None
    for r in rep:
        raw = None
        if None not in (r["ema8"], r["ema13"], r["ema21"], r["ema34"], r["ema48"]):
            c = r["bar"]["c"]
            if r["ema8"] > r["ema21"] and r["ema21"] > r["ema34"] and r["ema13"] > r["ema48"] and c > r["ema21"]:
                raw = "bull"
            elif r["ema8"] < r["ema21"] and r["ema21"] < r["ema34"] and r["ema13"] < r["ema48"] and c < r["ema21"]:
                raw = "bear"
        if raw and raw == raw_prev:
            prev_regime = raw
        elif not prev_regime and r["ema21"] is not None:
            prev_regime = "bull" if r["bar"]["c"] > r["ema21"] else "bear"
        raw_prev = raw
        r["regime"] = prev_regime
    dcb_age = None
    days_above = 0
    prev_above = False
    for i in range(1, len(rep)):
        r, prev = rep[i], rep[i - 1]
        ut_up = prev["utDir"] == -1 and r["utDir"] == 1
        ut_dn = prev["utDir"] == 1 and r["utDir"] == -1
        have = None not in (prev["ema8"], prev["ema21"], r["ema8"], r["ema21"])
        cross_up = have and prev["ema8"] <= prev["ema21"] and r["ema8"] > r["ema21"]
        cross_dn = have and prev["ema8"] >= prev["ema21"] and r["ema8"] < r["ema21"]
        wt_up = None not in (prev["wt1"], prev["wt2"], r["wt1"], r["wt2"]) and prev["wt1"] <= prev["wt2"] and \
            r["wt1"] > r["wt2"]
        st_up = None not in (prev["stochK"], prev["stochD"], r["stochK"], r["stochD"]) and \
            prev["stochK"] <= prev["stochD"] and r["stochK"] > r["stochD"]
        avail = [v for v in r["votes"] if v["available"]]
        bull = len([v for v in avail if v["value"] == 1])
        bear = len([v for v in avail if v["value"] == -1])
        gate = len(avail) == 7 and bull >= 5 and bull - bear >= 4
        recent_buy = recent_sell = False
        for look in range(1, 7):
            a = rep[i - look] if i - look >= 0 else None
            b = rep[i - look - 1] if i - look - 1 >= 0 else None
            if not a or not b:
                continue
            if b["utDir"] == -1 and a["utDir"] == 1:
                recent_buy = True
            if b["utDir"] == 1 and a["utDir"] == -1:
                recent_sell = True
        sell_mark = buy_mark = None
        if ut_dn:
            sell_mark = "RED_SELL"
        if cross_dn and recent_sell:
            sell_mark = "MAGENTA_SELL"
        if ut_up and gate:
            buy_mark = "CYAN_BUY"
        if cross_up and recent_buy and gate:
            buy_mark = "GREEN_BUY"
        if variant == "gospel":
            marker = buy_mark if buy_mark is not None else sell_mark
        else:
            marker = sell_mark if sell_mark is not None else buy_mark
            if sell_mark and buy_mark:
                r["glyphs"].append("sameBarSellWins")
        if not marker and wt_up and (r["regime"] == "bear" or (r["ema13"] is not None and r["ema48"] is not None and
                                                               r["ema13"] < r["ema48"])):
            marker = "GOLD_WARNING"
        if not marker and st_up and (r["bullShare"] if r["bullShare"] is not None else 0) >= 0.57 and \
                (r["stochK"] if r["stochK"] is not None else 100) <= 40:
            marker = "B"
        w1 = (not marker) and r["bullShare"] is not None and 0.5 <= r["bullShare"] < 0.72 and \
            (r["stochK"] if r["stochK"] is not None else 100) <= 30
        if w1:
            if not (rep[i - 1]["marker"] == "W1"):
                marker = "W1"
        if not marker and r["regime"] == "bear" and (r["stochK"] if r["stochK"] is not None else 100) <= 15:
            hi20 = -INF
            for j in range(max(0, i - 20), i):
                hi20 = max(hi20, rep[j]["bar"]["h"])
            dd = (hi20 - r["bar"]["c"]) / hi20 if hi20 > 0 else 0
            bar = r["bar"]
            loc = 0.5 if bar["h"] == bar["l"] else (bar["c"] - bar["l"]) / (bar["h"] - bar["l"])
            rising = r["squeezeMom"] is not None and prev["squeezeMom"] is not None and \
                r["squeezeMom"] > prev["squeezeMom"]
            if dd >= 0.18 and loc >= 0.6 and rising and bar["c"] > bar["o"]:
                marker = "DCB"
                dcb_age = 0
        if dcb_age is not None:
            dcb_age += 1
            weak = r["bar"]["c"] < r["bar"]["o"] or (r["stochK"] if r["stochK"] is not None else 0) >= 75 or \
                marker in ("RED_SELL", "MAGENTA_SELL")
            if 1 <= dcb_age <= 4 and weak and marker != "DCB":
                r["glyphs"].append("bounceEnd")
                dcb_age = None
            elif dcb_age > 4:
                dcb_age = None
        above_now = r["ema200"] is not None and r["bar"]["c"] > r["ema200"]
        days_above = days_above + 1 if above_now else 0
        snap = classify_location(rep, i, days_above, prev_above, bull, marker)
        prev_above = above_now
        r["location"] = snap["loc"]
        marker = apply_printer(marker, snap)
        r["marker"] = marker
        prev_signal = rep[i - 1]["signal"]
        if marker in ("CYAN_BUY", "GREEN_BUY"):
            r["signal"] = "buy"
        elif marker in ("RED_SELL", "MAGENTA_SELL"):
            r["signal"] = "sell"
        elif prev_signal == "buy" and r["ema200"] is not None and r["bar"]["c"] < r["ema200"] and \
                prev["ema200"] is not None and prev["bar"]["c"] >= prev["ema200"]:
            r["signal"] = "sell"
        else:
            r["signal"] = prev_signal
        if marker in ("RED_SELL", "MAGENTA_SELL"):
            r["glyphs"].append("sell")
        if marker in ("CYAN_BUY", "GREEN_BUY"):
            r["glyphs"].append("buy")
        if marker == "GOLD_WARNING":
            r["glyphs"].append("warn")
        if marker == "DCB":
            r["glyphs"].append("dcb")
        if marker == "B":
            r["glyphs"].append("B")
        if marker == "W1":
            r["glyphs"].append("W1")
    return rep
