"""Layer 3 / THE BOARD: Leadr confluence8 over the genome universe (ported from Silicon's research/morgue-engine).

VERBATIM from the vendor's shipped client config (confluence8, fw-c8-v2,
recovered in the Leadr teardown): the eight category weights, every
submetric name and weight, category states
(>=60 confirming, 45-60 neutral, <45 conflicting, no leaf at all = no-data),
the confirmation count (5), the conviction threshold (65) and the
data-confidence threshold (70), and the Qualify gate inputs.

OURS (labelled, never hidden): the per-submetric 0-100 transforms. The
vendor computes those server-side from the published "measures" text;
the transforms were never public, so each scorer below is a simple,
documented mapping from the published measure to 0-100. The vendor's
own not-measured leaves (themeSympathy) stay na. Leaves with no free
data route in v1 (13F ownership/activity, dark pool, short interest)
are na. DEC-02 (2026-10-27, UNI-04): the vendor's 60% coverage floor is DROPPED, because no data the desk
holds can fit it and a hand-picked cutoff made the institutional category unreachable for ordinary stocks (at most
4 of 7 leaves = 57%). A category now scores from the leaves it has, weighted by the designed leaf weights, and shows
covered/designed; the data-confidence figure still carries how much of the board is missing.

Institutional Positioning's optionsPositioning leaf is the SPEC's
pre-designed substitution: our own Tape aggregates (Slice 2) where
they exist (the index ETFs), na elsewhere in v1.
"""
from __future__ import annotations

import math

# ---- vendor config, verbatim (weights) --------------------------------
CONFIG = {
    "relativeStrength": (15, {"rsMarket": 20, "rsGrowth": 10, "rsSector": 15,
                              "peerRank": 15, "rsLine": 15,
                              "downsideResilience": 15, "longMomentum": 10}),
    "priceAction": (18, {"trendStructure": 20, "baseQuality": 20,
                         "volContraction": 15, "pullbackQuality": 15,
                         "technicalRespect": 10, "stageDevelopment": 10,
                         "extension": 10}),
    "volumeParticipation": (15, {"relVolume": 20, "dollarVolTrend": 10,
                                 "accDist": 20, "volPriceAgreement": 20,
                                 "pullbackVolume": 15,
                                 "participationBreadth": 10,
                                 "expansionReadiness": 5}),
    "trendAlignment": (12, {"emaPosition": 15, "emaSlope": 15,
                            "dailyWeeklyAgreement": 25, "stageAlignment": 15,
                            "htfLevelPosition": 15,
                            "weeklyAccExhaustion": 15}),
    "supportResistance": (12, {"supportProximity": 20, "roomToResistance": 20,
                               "levelSignificance": 20, "srConversion": 15,
                               "tradeGeometry": 20, "chasePenalty": 5}),
    "sectorLeadership": (10, {"sectorStrength": 15, "industryStrength": 15,
                              "capitalRotation": 20, "stockLeadership": 20,
                              "peerConfirmation": 10, "themeSympathy": 15,
                              "crowding": 5}),
    "institutionalPositioning": (8, {"instOwnership": 15, "instActivity": 10,
                                     "insiderActivity": 10,
                                     "optionsPositioning": 25,
                                     "dealerPositioning": 15, "darkPool": 15,
                                     "shortPositioning": 10}),
    "marketContext": (10, {"marketRegime": 20, "marketBreadth": 20,
                           "indexAccDist": 15, "breakoutFollowThrough": 15,
                           "riskAppetite": 10, "sectorRotation": 10,
                           "macroEventRisk": 5, "indexConfirmation": 5}),
}
COVERAGE_FLOOR = None     # vendor L = .6, dropped by DEC-02 (UNI-04): no fitted value exists, so no floor
CONFIRM_COUNT = 5         # vendor N = 5
CONVICTION_MIN = 65       # vendor _ = 65
DC_MIN = 70               # vendor b = 70
STATE_CONFIRM = 60        # vendor I = 60
STATE_NEUTRAL = 45        # vendor E = 45
DESIGNED_LEAVES = sum(len(s) for _, s in CONFIG.values())  # 55


def lin(x: float, lo: float, hi: float) -> float:
    """Linear map [lo, hi] -> [0, 100], clipped."""
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (x - lo) / (hi - lo) * 100.0))


def pct_rank(values: dict[str, float], key: str) -> float | None:
    """Percentile (0-100) of key within values; None if absent."""
    if key not in values or len(values) < 2:
        return None
    v = values[key]
    below = sum(1 for x in values.values() if x < v)
    equal = sum(1 for x in values.values() if x == v)
    return (below + 0.5 * equal) / len(values) * 100.0


# ---- bar feature helpers ------------------------------------------------
def ema_series(vals: list[float], n: int) -> list[float]:
    if len(vals) < n:
        return []
    seed = sum(vals[:n]) / n
    out = [math.nan] * (n - 1) + [seed]
    k = 2.0 / (n + 1)
    for v in vals[n:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def atr_series(h: list[float], l: list[float], c: list[float],
               n: int = 14) -> list[float]:
    """Wilder ATR with SMA seed (Saty SPEC / Pine ta.atr semantics)."""
    if len(c) <= n:
        return []
    trs = []
    for i in range(1, len(c)):
        trs.append(max(h[i] - l[i], abs(h[i] - c[i - 1]),
                       abs(l[i] - c[i - 1])))
    seed = sum(trs[:n]) / n
    out = [math.nan] * n + [seed]
    for tr in trs[n:]:
        out.append(out[-1] + (tr - out[-1]) / n)
    return out


def ret(vals: list[float], sessions: int) -> float | None:
    if len(vals) <= sessions or vals[-1 - sessions] == 0:
        return None
    return (vals[-1] / vals[-1 - sessions] - 1.0) * 100.0


def blend_ret(vals: list[float]) -> float | None:
    parts = [(ret(vals, 5), 0.25), (ret(vals, 20), 0.35),
             (ret(vals, 60), 0.40)]
    if any(p is None for p, _ in parts):
        return None
    return sum(p * w for p, w in parts)


def weekly_bars(bars: list[dict]) -> list[dict]:
    """Resample daily bars (ascending) into ISO-week bars."""
    out: dict[tuple, dict] = {}
    for b in bars:
        key = (b["d"].isocalendar()[0], b["d"].isocalendar()[1])
        w = out.get(key)
        if w is None:
            out[key] = {"o": b["o"], "h": b["h"], "l": b["l"],
                        "c": b["c"], "v": b["v"]}
        else:
            w["h"] = max(w["h"], b["h"])
            w["l"] = min(w["l"], b["l"])
            w["c"] = b["c"]
            w["v"] += b["v"]
    return [out[k] for k in sorted(out)]


def swing_levels(h: list[float], l: list[float], look: int = 2):
    """Fractal swing highs/lows: (index, price) lists."""
    sh, sl = [], []
    for i in range(look, len(h) - look):
        if all(h[i] >= h[i + k] for k in range(-look, look + 1) if k) and \
           all(h[i] > h[i + k] for k in (-look, look)):
            sh.append((i, h[i]))
        if all(l[i] <= l[i + k] for k in range(-look, look + 1) if k) and \
           all(l[i] < l[i + k] for k in (-look, look)):
            sl.append((i, l[i]))
    return sh, sl


def weinstein_stage(wcloses: list[float]) -> int | None:
    """Stage from price vs the 30-week MA and the MA's slope."""
    if len(wcloses) < 40:
        return None
    ma = sum(wcloses[-30:]) / 30
    ma_prev = sum(wcloses[-35:-5]) / 30
    rising = ma > ma_prev
    above = wcloses[-1] > ma
    if above and rising:
        return 2
    if above and not rising:
        return 3
    if not above and rising:
        return 1
    return 4


# ---- aggregation mechanics (vendor) -------------------------------------
def category_state(score: float | None, covered: int, designed: int) -> str:
    if score is None or designed == 0 or covered == 0:
        return "no-data"
    if score >= STATE_CONFIRM:
        return "confirming"
    if score >= STATE_NEUTRAL:
        return "neutral"
    return "conflicting"


def aggregate(leaf_scores: dict[str, dict[str, float | None]]) -> dict:
    """leaf_scores: {category: {leaf: score|None}} -> vendor aggregation."""
    cats, covered_total = {}, 0
    for cat, (weight, subs) in CONFIG.items():
        got = leaf_scores.get(cat, {})
        avail = {k: v for k, v in got.items() if v is not None}
        covered = len(avail)
        covered_total += covered
        score = None
        if avail:
            wsum = sum(subs[k] for k in avail)
            score = sum(avail[k] * subs[k] for k in avail) / wsum
        cats[cat] = {"weight": weight, "score": score,
                     "state": category_state(score, covered, len(subs)),
                     "covered": covered, "designed": len(subs),
                     "leaves": got}
    scored = {c: v for c, v in cats.items() if v["state"] != "no-data"}
    overall = None
    if scored:
        wsum = sum(v["weight"] for v in scored.values())
        overall = sum(v["score"] * v["weight"] for v in scored.values()) / wsum
    confirming = sum(1 for v in cats.values() if v["state"] == "confirming")
    dc = covered_total / DESIGNED_LEAVES * 100.0
    return {"categories": cats, "score": overall, "confirming": confirming,
            "dc": round(dc, 1), "covered_leaves": covered_total,
            "designed_leaves": DESIGNED_LEAVES}


def qualify(feat: dict) -> tuple[bool, list[str]]:
    """Vendor Qualify gate (SPEC): ADV, $ADV, ATR%, EMA position, stage."""
    fails = []
    if feat["adv"] <= 500_000:
        fails.append("adv<=500k")
    if feat["dollar_adv"] <= 5_000_000:
        fails.append("dollar-adv<=$5M")
    if feat["atr_pct"] < 2.0:
        fails.append("atr<2%")
    if feat["ema50"] is None or feat["close"] < feat["ema50"] * 0.98:
        fails.append("below-50ema")
    if feat["ema200"] is None or feat["close"] < feat["ema200"] * 0.98:
        fails.append("below-200ema")
    if feat["stage"] not in (1, 2):
        fails.append(f"stage-{feat['stage']}")
    return (not fails), fails


def vendor_gate(qualified: bool, agg: dict) -> tuple[bool, list[str]]:
    """The shipped qualification function T, verbatim thresholds."""
    fails = []
    if not qualified:
        fails.append("not-qualified")
    if agg["confirming"] < CONFIRM_COUNT:
        fails.append("count")
    if agg["score"] is None or round(agg["score"]) < CONVICTION_MIN:
        fails.append("conviction")
    if agg["dc"] < DC_MIN:
        fails.append("data-confidence")
    return (not fails), fails
