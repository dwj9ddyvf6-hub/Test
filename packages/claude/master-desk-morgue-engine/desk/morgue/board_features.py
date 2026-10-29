"""Per-name features + submetric scorers for the Board (ported from Silicon's research/morgue-engine, 2026-10-27).

Every scorer implements the vendor's published "measures" text (from
the shipped confluence8 config) with a simple OURS 0-100 transform.
None means the leaf is not available for this name/session and the
vendor's coverage mechanics absorb it.
"""
from __future__ import annotations

import math
import statistics

from . import board


def _last(s: list[float]) -> float | None:
    return s[-1] if s and not math.isnan(s[-1]) else None


def _slope(vals: list[float], n: int) -> float | None:
    """Least-squares slope per session over the last n values."""
    if len(vals) < n:
        return None
    ys = vals[-n:]
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def features(bars: list[dict]) -> dict | None:
    """Raw features from completed daily bars (ascending)."""
    if len(bars) < 60:
        return None
    c = [b["c"] for b in bars]
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    v = [b["v"] for b in bars]
    f: dict = {"close": c[-1], "prev_close": c[-2], "bars": bars}
    for n, key in ((9, "ema9"), (20, "ema20"), (50, "ema50"),
                   (200, "ema200")):
        f[key] = _last(board.ema_series(c, n))
        f[key + "_series"] = board.ema_series(c, n)
    atr = board.atr_series(h, l, c)
    f["atr"] = _last(atr)
    f["atr_pct"] = (f["atr"] / c[-1] * 100.0) if f["atr"] else None
    f["adv"] = statistics.mean(v[-20:])
    f["dollar_adv"] = statistics.mean(
        [cc * vv for cc, vv in zip(c[-20:], v[-20:])])
    f["blend"] = board.blend_ret(c)
    f["r5"] = board.ret(c, 5)
    f["r20"] = board.ret(c, 20)
    f["r60"] = board.ret(c, 60)
    f["mom12_1"] = ((c[-22] / c[-253] - 1.0) * 100.0
                    if len(c) > 253 and c[-253] else None)
    wk = board.weekly_bars(bars)
    f["weekly"] = wk
    f["stage"] = board.weinstein_stage([w["c"] for w in wk])
    f["relvol"] = v[-1] / f["adv"] if f["adv"] else None
    # support / resistance from fractal swings + range extremes
    sh, sl = board.swing_levels(h, l)
    f["swing_highs"], f["swing_lows"] = sh, sl
    below = [p for _, p in sl if p < c[-1]]
    if f["ema50"] and f["ema50"] < c[-1]:
        below.append(f["ema50"])
    f["support"] = max(below) if below else None
    above = [p for _, p in sh if p > c[-1]]
    f["resistance"] = min(above) if above else None
    f["high20"] = max(h[-20:])
    f["pos52"] = ((c[-1] - min(l[-252:])) /
                  (max(h[-252:]) - min(l[-252:]))
                  if max(h[-252:]) > min(l[-252:]) else None)
    f["pos26"] = ((c[-1] - min(l[-126:])) /
                  (max(h[-126:]) - min(l[-126:]))
                  if max(h[-126:]) > min(l[-126:]) else None)
    return f


def _ratio_series(f: dict, bench: list[float]) -> list[float] | None:
    bars = f["bars"]
    if len(bench) != len(bars):
        n = min(len(bench), len(bars))
        if n < 61:
            return None
        return [b["c"] / bb for b, bb in zip(bars[-n:], bench[-n:])]
    return [b["c"] / bb for b, bb in zip(bars, bench)]


def score_name(f: dict, ctx: dict) -> dict[str, dict[str, float | None]]:
    """ctx: {spy_c, qqq_c, sector_etf_c, sector (name), peer_blends,
    sector_blends_rank, industry_pct, market (leaves), tape_pos}."""
    c = [b["c"] for b in f["bars"]]
    h = [b["h"] for b in f["bars"]]
    l = [b["l"] for b in f["bars"]]
    v = [b["v"] for b in f["bars"]]
    atr = f["atr"] or 0.0
    L: dict[str, dict[str, float | None]] = {k: {} for k in board.CONFIG}
    spy = ctx["spy_c"]
    # ---------- Relative strength ----------
    rs = L["relativeStrength"]
    if f["blend"] is not None and ctx.get("spy_blend") is not None:
        rs["rsMarket"] = board.lin(f["blend"] - ctx["spy_blend"], -15, 15)
        rs["rsGrowth"] = board.lin(f["blend"] - ctx["qqq_blend"], -15, 15) \
            if ctx.get("qqq_blend") is not None else None
    else:
        rs["rsMarket"] = rs["rsGrowth"] = None
    if f["blend"] is not None and ctx.get("sector_blend") is not None:
        rs["rsSector"] = board.lin(f["blend"] - ctx["sector_blend"],
                                    -15, 15)
    else:
        rs["rsSector"] = None
    rs["peerRank"] = ctx.get("peer_rank")
    ratio = _ratio_series(f, spy)
    if ratio and len(ratio) > 61:
        rr = board.ret(ratio, 20)
        score = board.lin(rr, -8, 8) if rr is not None else None
        if score is not None and ratio[-1] >= max(ratio[-60:]) * 0.999:
            score = min(100.0, score + 15)
        rs["rsLine"] = score
    else:
        rs["rsLine"] = None
    if len(c) > 21 and len(spy) == len(c):
        diffs = [(c[i] / c[i - 1] - 1) - (spy[i] / spy[i - 1] - 1)
                 for i in range(len(c) - 20, len(c)) if spy[i] < spy[i - 1]]
        rs["downsideResilience"] = (board.lin(
            statistics.mean(diffs) * 100, -2, 2) if diffs else None)
    else:
        rs["downsideResilience"] = None
    rs["longMomentum"] = (board.lin(f["mom12_1"], -20, 40)
                          if f["mom12_1"] is not None else None)
    # ---------- Price action ----------
    pa = L["priceAction"]
    sh, sl = f["swing_highs"], f["swing_lows"]
    slope = _slope(c, 20)
    struct = None
    if len(sh) >= 2 and len(sl) >= 2 and slope is not None and atr:
        pts = (1 if sh[-1][1] > sh[-2][1] else 0) + \
              (1 if sl[-1][1] > sl[-2][1] else 0)
        struct = pts / 2 * 60 + board.lin(slope / atr, -0.05, 0.05) * 0.4
    pa["trendStructure"] = struct
    if atr:
        range_atr = (max(h[-60:]) - min(l[-60:])) / atr
        pos = (c[-1] - min(l[-60:])) / (max(h[-60:]) - min(l[-60:])) \
            if max(h[-60:]) > min(l[-60:]) else 0.5
        pa["baseQuality"] = (100 - board.lin(range_atr, 4, 14)) * 0.6 \
            + pos * 100 * 0.4
        tr = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
              for i in range(1, len(c))]
        tr_ratio = (statistics.mean(tr[-10:]) / statistics.mean(tr[-20:])
                    if statistics.mean(tr[-20:]) else None)
        rng_ratio = ((max(h[-10:]) - min(l[-10:])) /
                     (max(h[-20:]) - min(l[-20:]))
                     if max(h[-20:]) > min(l[-20:]) else None)
        if tr_ratio and rng_ratio:
            pa["volContraction"] = 100 - board.lin(
                (tr_ratio + rng_ratio) / 2, 0.55, 1.1)
        else:
            pa["volContraction"] = None
    else:
        pa["baseQuality"] = pa["volContraction"] = None
    if f["ema20"]:
        if c[-1] >= f["high20"] * 0.999:
            pa["pullbackQuality"] = 75.0
        else:
            adv = f["high20"] - min(l[-60:])
            give = (f["high20"] - c[-1]) / adv if adv > 0 else None
            if give is not None:
                s = 100 - board.lin(give, 0.15, 0.7)
                if c[-1] > f["ema20"]:
                    s = min(100.0, s + 15)
                pa["pullbackQuality"] = s
            else:
                pa["pullbackQuality"] = None
    else:
        pa["pullbackQuality"] = None
    pa["technicalRespect"] = _technical_respect(f)
    stage_score = {1: 60.0, 2: 95.0, 3: 35.0, 4: 5.0}
    pa["stageDevelopment"] = stage_score.get(f["stage"])
    if f["ema20"] and atr:
        atrs = (c[-1] - f["ema20"]) / atr
        streak = 0
        for i in range(len(c) - 1, 0, -1):
            if c[i] > c[i - 1]:
                streak += 1
            else:
                break
        off = statistics.mean(
            [(h[i] - c[i]) / (h[i] - l[i]) if h[i] > l[i] else 0
             for i in range(len(c) - 5, len(c))])
        s = 100 - board.lin(atrs, 0, 4)
        if streak >= 5:
            s -= 15
        s -= 20 * off
        pa["extension"] = max(0.0, min(100.0, s))
    else:
        pa["extension"] = None
    # ---------- Volume participation ----------
    vp = L["volumeParticipation"]
    if f["relvol"]:
        ratio = f["relvol"] * (0.85 if c[-1] < c[-2] else 1.0)
        vp["relVolume"] = board.lin(ratio, 0.4, 2.2)
    else:
        vp["relVolume"] = None
    dv5 = statistics.median([cc * vv for cc, vv in zip(c[-5:], v[-5:])])
    dv20 = statistics.median([cc * vv for cc, vv in zip(c[-20:], v[-20:])])
    vp["dollarVolTrend"] = board.lin((dv5 / dv20 - 1) * 100, -30, 30) \
        if dv20 else None
    obv = [0.0]
    for i in range(1, len(c)):
        obv.append(obv[-1] + (v[i] if c[i] > c[i - 1]
                              else -v[i] if c[i] < c[i - 1] else 0))
    obv_norm = ((obv[-1] - obv[-21]) / sum(v[-20:])
                if sum(v[-20:]) else None)
    clv = [((2 * cc - hh - ll) / (hh - ll) if hh > ll else 0)
           for cc, hh, ll in zip(c[-20:], h[-20:], l[-20:])]
    mf = (sum(a * b for a, b in zip(clv, v[-20:])) / sum(v[-20:])
          if sum(v[-20:]) else None)
    vp["accDist"] = (board.lin(obv_norm, -0.5, 0.5) * 0.6
                     + board.lin(mf, -0.3, 0.3) * 0.4) \
        if obv_norm is not None and mf is not None else None
    up = [v[i] for i in range(len(c) - 20, len(c)) if c[i] > c[i - 1]]
    dn = [v[i] for i in range(len(c) - 20, len(c)) if c[i] < c[i - 1]]
    vp["volPriceAgreement"] = (board.lin(
        statistics.mean(up) / statistics.mean(dn), 0.6, 1.8)
        if up and dn else None)
    vp["pullbackVolume"] = _pullback_volume(f)
    med60 = statistics.median(v[-60:])
    share = sum(1 for x in v[-20:] if x > med60) / 20
    breadth = share * 100
    if sum(v[-20:]) and max(v[-20:]) / sum(v[-20:]) > 0.4:
        breadth *= 0.8
    vp["participationBreadth"] = breadth
    rng5 = max(h[-5:]) - min(l[-5:])
    rng20 = max(h[-20:]) - min(l[-20:])
    if rng20:
        vp["expansionReadiness"] = (
            (100 - board.lin(rng5 / rng20, 0.25, 0.9)) * 0.6
            + board.lin(statistics.mean(v[-5:]) /
                        statistics.mean(v[-20:]), 0.7, 1.5) * 0.4)
    else:
        vp["expansionReadiness"] = None
    # ---------- Trend alignment ----------
    ta = L["trendAlignment"]
    emas = [f["ema9"], f["ema20"], f["ema50"], f["ema200"]]
    have = [e for e in emas if e]
    ta["emaPosition"] = (sum(1 for e in have if c[-1] > e) / len(have)
                         * 100) if have else None
    if atr:
        parts = []
        for key in ("ema9", "ema20", "ema50", "ema200"):
            s = f[key + "_series"]
            if len(s) > 6 and not math.isnan(s[-6]):
                parts.append(board.lin((s[-1] - s[-6]) / atr, -0.08, 0.08))
        ta["emaSlope"] = statistics.mean(parts) if parts else None
    else:
        ta["emaSlope"] = None
    daily = _trend_sign(c[-1], f["ema50"], f["ema50_series"], atr)
    wk = f["weekly"]
    wk_c = [w["c"] for w in wk]
    if len(wk_c) >= 35:
        ma30 = statistics.mean(wk_c[-30:])
        ma30p = statistics.mean(wk_c[-35:-5])
        weekly = 1 if (wk_c[-1] > ma30 and ma30 > ma30p) else \
            -1 if (wk_c[-1] < ma30 and ma30 < ma30p) else 0
    else:
        weekly = None
    if daily is not None and weekly is not None:
        ta["dailyWeeklyAgreement"] = {2: 100.0, 1: 65.0, 0: 40.0,
                                      -1: 20.0, -2: 0.0}[daily + weekly]
    else:
        ta["dailyWeeklyAgreement"] = None
    stg = f["stage"]
    if stg is None:
        ta["stageAlignment"] = None
    else:
        base = {2: 80.0, 1: 50.0, 3: 30.0, 4: 5.0}[stg]
        if stg == 2 and f["ema50"] and c[-1] > f["ema50"]:
            base = 95.0
        if stg == 1 and f["ema50"] and c[-1] > f["ema50"]:
            base = 65.0
        ta["stageAlignment"] = base
    ta["htfLevelPosition"] = (statistics.mean(
        [p for p in (f["pos26"], f["pos52"]) if p is not None]) * 100
        if (f["pos26"] is not None or f["pos52"] is not None) else None)
    ta["weeklyAccExhaustion"] = _weekly_acc(wk)
    # ---------- Support / resistance ----------
    sr = L["supportResistance"]
    sup, res = f["support"], f["resistance"]
    if sup and atr:
        sr["supportProximity"] = 100 - board.lin((c[-1] - sup) / atr,
                                                 0.3, 4.0)
    else:
        sr["supportProximity"] = None
    if res and atr:
        sr["roomToResistance"] = board.lin((res - c[-1]) / atr, 0.5, 6.0)
    elif res is None:
        sr["roomToResistance"] = 85.0  # open sky above (OURS convention)
    else:
        sr["roomToResistance"] = None
    sr["levelSignificance"] = _level_significance(f)
    sr["srConversion"] = _sr_conversion(f)
    if sup and res and c[-1] > sup:
        sr["tradeGeometry"] = board.lin(
            (res - c[-1]) / (c[-1] - sup), 0.5, 3.0)
    else:
        sr["tradeGeometry"] = None
    if f["ema20"] and atr and f["r5"] is not None:
        pen = board.lin((c[-1] - f["ema20"]) / atr, 0, 4) * 0.6 \
            + board.lin(f["r5"], 0, 15) * 0.4
        sr["chasePenalty"] = 100 - pen
    else:
        sr["chasePenalty"] = None
    # ---------- Sector leadership ----------
    sec = L["sectorLeadership"]
    sec["sectorStrength"] = ctx.get("sector_strength_pct")
    sec["industryStrength"] = ctx.get("industry_strength_pct")
    sec["capitalRotation"] = ctx.get("sector_rotation_score")
    if ctx.get("sector_peer_rank") is not None:
        sec["stockLeadership"] = ctx["sector_peer_rank"] * 0.7 + \
            (rs["downsideResilience"] or 50.0) * 0.3
    else:
        sec["stockLeadership"] = None
    sec["peerConfirmation"] = ctx.get("sector_peer_confirmation")
    sec["themeSympathy"] = None  # vendor: not measured yet
    sec["crowding"] = ctx.get("sector_crowding_score")
    # ---------- Institutional positioning ----------
    inst = L["institutionalPositioning"]
    # Slice 5 (I4): leaves arrive via a per-name ctx bundle built once
    # per run from the EDGAR/FINRA caches (inst_edgar / inst_13f /
    # inst_short). No bundle in ctx -> preserved v1 behaviour (all
    # None). dealerPositioning + darkPool stay None (named out of
    # scope: no free route / outside the named leaf set).
    bundle = ctx.get("inst_leaves") or {}
    for k in ("instOwnership", "instActivity", "insiderActivity",
              "dealerPositioning", "darkPool", "shortPositioning"):
        inst[k] = bundle.get(k)
    inst["optionsPositioning"] = ctx.get("tape_positioning")
    # ---------- Market context (same for all names) ----------
    L["marketContext"] = dict(ctx["market"])
    return L


def _trend_sign(close: float, ema: float | None, series: list[float],
                atr: float | None) -> int | None:
    if not ema or len(series) < 6 or math.isnan(series[-6]):
        return None
    slope = series[-1] - series[-6]
    if close > ema and slope > 0:
        return 1
    if close < ema and slope < 0:
        return -1
    return 0


def _technical_respect(f: dict) -> float | None:
    bars = f["bars"]
    c = [b["c"] for b in bars]
    tests = respected = 0
    for key in ("ema20_series", "ema50_series"):
        s = f[key]
        if len(s) != len(c):
            continue
        for i in range(max(60, len(c) - 120), len(c)):
            if math.isnan(s[i]) or not f["atr"]:
                continue
            if abs(bars[i]["l"] - s[i]) <= 0.25 * f["atr"] \
                    and c[i] > s[i]:
                tests += 1
                respected += 1
            elif bars[i]["l"] < s[i] - 0.25 * f["atr"] \
                    and c[i] < s[i]:
                tests += 1
    if tests < 2:
        return None
    return respected / tests * 100


def _pullback_volume(f: dict) -> float | None:
    bars = f["bars"]
    h = [b["h"] for b in bars]
    v = [b["v"] for b in bars]
    idx = h.index(f["high20"], len(h) - 20)
    since = len(h) - 1 - idx
    if since == 0:
        return 60.0
    if since >= 15 or idx < 20:
        return None
    pull = statistics.mean(v[idx:])
    adv = statistics.mean(v[idx - 20:idx])
    if not adv:
        return None
    return 100 - board.lin(pull / adv, 0.5, 1.3)


def _weekly_acc(wk: list[dict]) -> float | None:
    if len(wk) < 26:
        return None
    seg = wk[-26:]
    up = [w["v"] for i, w in enumerate(seg)
          if i and w["c"] > seg[i - 1]["c"]]
    dn = [w["v"] for i, w in enumerate(seg)
          if i and w["c"] < seg[i - 1]["c"]]
    if not up or not dn:
        return None
    s = board.lin(statistics.mean(up) / statistics.mean(dn), 0.6, 1.8)
    streak = 0
    for i in range(len(seg) - 1, 0, -1):
        if seg[i]["c"] > seg[i - 1]["c"]:
            streak += 1
        else:
            break
    if streak >= 6:
        s -= 15
    return max(0.0, s)


def _level_significance(f: dict) -> float | None:
    sup, atr = f["support"], f["atr"]
    if not sup or not atr:
        return None
    bars = f["bars"]
    touches = 0
    last_touch = None
    for i, b in enumerate(bars[-252:]):
        if abs(b["l"] - sup) <= 0.3 * atr:
            touches += 1
            last_touch = i
    if touches == 0:
        return 10.0
    s = board.lin(touches, 0, 6)
    if last_touch is not None and len(bars[-252:]) - last_touch <= 20:
        s = min(100.0, s + 10)
    return s


def _sr_conversion(f: dict) -> float | None:
    bars = f["bars"]
    c = [b["c"] for b in bars]
    sh = f["swing_highs"]
    cands = [(i, p) for i, p in sh if len(c) - 25 <= i < len(c) - 1
             and p < c[-1]]
    if not cands:
        return None
    i, p = cands[-1]
    held = all(cc >= p * 0.995 for cc in c[i + 1:])
    return 85.0 if held else 50.0


# ---- triggers + Saty ladder ----------------------------------------------
def detect_triggers(f: dict) -> list[dict]:
    bars = f["bars"]
    c = [b["c"] for b in bars]
    h = [b["h"] for b in bars]
    out = []
    expanding = (f["relvol"] or 0) >= 1.2
    if c[-1] > h[-2] and c[-2] <= h[-2]:
        out.append({"trigger": "prior-day-high break",
                    "level": h[-2], "validated": expanding})
    prior20 = max(h[-21:-1])
    if c[-1] > prior20 and c[-2] <= prior20:
        out.append({"trigger": "resistance break (20-session)",
                    "level": prior20, "validated": expanding})
    e20 = f["ema20_series"]
    if len(e20) == len(c) and not math.isnan(e20[-2]):
        if c[-2] < e20[-2] and c[-1] > e20[-1]:
            out.append({"trigger": "support reclaim (20 EMA)",
                        "level": e20[-1], "validated": expanding})
    if f["resistance"] is None and f["atr"]:
        for i, p in f["swing_highs"]:
            if len(c) - 5 <= i < len(c) - 1 and p < c[-1]:
                if abs(bars[-1]["l"] - p) <= 0.5 * f["atr"]:
                    out.append({"trigger": "holding retest",
                                "level": p, "validated": expanding})
                break
    return out


FIBS = (0.236, 0.382, 0.5, 0.618, 0.786, 1.0)


def saty_ladder(f: dict) -> dict | None:
    """Saty ATR Levels, Day mode: anchor = prior completed close,
    unit = ATR(14) Wilder; trigger fraction 0.236."""
    if not f["atr"]:
        return None
    anchor = f["prev_close"]
    unit = f["atr"]
    return {
        "anchor": round(anchor, 2), "atr": round(unit, 2),
        "up": {str(x): round(anchor + unit * x, 2) for x in FIBS},
        "down": {str(x): round(anchor - unit * x, 2) for x in FIBS},
        "trigger_up": round(anchor + unit * 0.236, 2),
        "trigger_down": round(anchor - unit * 0.236, 2),
    }


def ribbon_state(f: dict) -> str | None:
    c = [b["c"] for b in f["bars"]]
    e8 = board.ema_series(c, 8)
    e21 = board.ema_series(c, 21)
    e34 = board.ema_series(c, 34)
    e13 = board.ema_series(c, 13)
    e48 = board.ema_series(c, 48)
    if not e34 or not e48:
        return None
    bull = c[-1] >= e8[-1] >= e21[-1] >= e34[-1]
    bear = c[-1] <= e8[-1] <= e21[-1] <= e34[-1]
    conv = "conviction-up" if e13[-1] >= e48[-1] else "conviction-down"
    return ("bullish" if bull else "bearish" if bear else "mixed") \
        + " / " + conv
