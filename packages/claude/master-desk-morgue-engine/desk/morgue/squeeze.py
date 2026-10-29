"""S5 Squeeze pane (ported from Silicon, with two None-handling fixes in the scoring) (Tapeboard Squeeze Score v6, PUBLISHED in full).

Formula verbatim: gate SI >=15% of float (readings >120% of float are
data errors -> missing, never ranked); score = 100 * (0.6 * percentile
of 20-session volatility [RMS of returns excluding the largest move]
+ 0.2 * percentile of 5-session float rotation + 0.2 * percentile of
last-session relative volume capped at 50x). Percentiles are
average-tie within the gated set; ties on score break by higher SI%.
SI% itself carries ZERO weight in the score. A100 universe filters as
published. Borrow fee has no free route -> explicit no-data field.
The pane is a display, never a Board input.
"""
from __future__ import annotations

import math
import statistics

FORMULA_VERSION = "squeeze_v6"
VENDOR_CALIBRATION = {
    "label": "vendor out-of-sample calibration (the vendor's figures)",
    "top10_plus20_in_5_sessions": 0.166, "top10_minus20_in_5_sessions": 0.120,
    "base_plus20": 0.045, "base_minus20": 0.023,
    "top10_median_5d_return": -0.018}


def rms_ex_largest(returns: list[float]) -> float | None:
    """RMS of returns after removing the single largest-|move| return."""
    if len(returns) < 2:
        return None
    idx = max(range(len(returns)), key=lambda i: abs(returns[i]))
    rest = [r for i, r in enumerate(returns) if i != idx]
    return math.sqrt(statistics.fmean([r * r for r in rest]))


def _pct(values: dict[str, float], key: str) -> float:
    """Average-tie percentile as a 0-1 fraction (board convention)."""
    v = values[key]
    below = sum(1 for x in values.values() if x < v)
    equal = sum(1 for x in values.values() if x == v)
    return (below + 0.5 * equal) / len(values)


def _returns(closes: list[float], n: int = 20) -> list[float]:
    seg = closes[-(n + 1):]
    return [seg[i] / seg[i - 1] - 1.0 for i in range(1, len(seg))
            if seg[i - 1]]


def gate_reason(rec: dict) -> str | None:
    """None = admitted to the gated set; else the named exclusion."""
    si = rec.get("si_pct_float")  # percent units, e.g. 18.5 means 18.5%
    if si is None:
        return "si_missing"
    if si > 120.0:
        return "si_data_error_over_120pct"
    if rec.get("settlement_age_days") is None or \
            rec["settlement_age_days"] > 40:
        return "si_stale_over_40d"
    if si < 15.0:
        return "si_below_15pct_gate"
    if rec.get("close") is None or rec["close"] < 1.0:
        return "close_below_1"
    if rec.get("adv20") is None or rec["adv20"] < 100_000:
        return "adv20_below_100k"
    if rec.get("median_dollar_vol") is None or \
            rec["median_dollar_vol"] < 500_000:
        return "median_dollar_vol_below_500k"
    mcap = rec.get("market_cap")
    if mcap is None and rec.get("shares_outstanding") and rec.get("close"):
        mcap = rec["shares_outstanding"] * rec["close"]
    if mcap is None or mcap < 25_000_000:
        return "market_cap_below_25m"
    if len(rec.get("closes") or []) < 21:
        return "insufficient_sessions"
    return None


def build_pane(records: list[dict], as_of: str) -> dict:
    gated, excluded = [], {}
    for rec in records:
        reason = gate_reason(rec)
        if reason:
            excluded[rec["symbol"]] = reason
        else:
            gated.append(rec)
    if not gated:
        return {"state": "no_data", "as_of": as_of,
                "formula_version": FORMULA_VERSION, "rows": [],
                "excluded": excluded,
                "reason": "no names pass the published gate + A100 "
                          "universe filters on owned data",
                "vendor_calibration": VENDOR_CALIBRATION}
    vol = {r["symbol"]: rms_ex_largest(_returns(r["closes"]))
           for r in gated}
    rot = {r["symbol"]: (sum(r["volumes"][-5:]) / r["float_shares"]
                         if r.get("float_shares") else 0.0)       # no float basis: no rotation (was None: a TypeError)
           for r in gated}
    rel = {r["symbol"]: min((r["volumes"][-1] / r["adv20"]) if r.get("adv20") else 0.0, 50.0)
           for r in gated}
    rows = []
    for r in gated:
        sym = r["symbol"]
        score = 100.0 * (0.6 * _pct(vol, sym) + 0.2 * _pct(rot, sym)
                         + 0.2 * _pct(rel, sym))
        closes = r["closes"]
        rows.append({
            "symbol": sym, "score": round(score, 2),
            "si_pct_float": r["si_pct_float"],
            # zero-weight vendor-displayed fields (weight 0, declared)
            "si_change_pct": r.get("si_change_pct"),
            "days_to_cover": (r["si_shares"] / r["adv20"]
                              if r.get("si_shares") and r.get("adv20")
                              else None),
            "short_volume_ratio": r.get("short_volume_ratio"),
            "momentum_5d": (closes[-1] / closes[-6] - 1.0
                            if len(closes) >= 6 else None),
            "borrow_fee": None, "borrow_fee_state": "no_data_no_free_route",
            "already_ran": bool(len(closes) >= 6
                                and closes[-1] / closes[-6] - 1.0 >= 0.30),
            "volatility_rms_ex_largest": vol[sym],
            "float_rotation_5d": rot[sym],
            "relative_volume_capped": rel[sym]})
    rows.sort(key=lambda x: (-x["score"], -x["si_pct_float"]))
    return {"state": "graded", "as_of": as_of,
            "formula_version": FORMULA_VERSION, "rows": rows,
            "excluded": excluded, "gated_n": len(rows),
            "vendor_calibration": VENDOR_CALIBRATION,
            "note": "dated/frozen pane (A101): history is never re-scored "
                    "when a formula version changes"}
