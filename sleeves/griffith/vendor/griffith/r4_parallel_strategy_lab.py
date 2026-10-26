"""Frozen, brokerless strategy candidates for Griffith's parallel R4 laboratory.

The module deliberately contains no broker, allocator, risk, or live-strategy
imports.  It converts synchronized completed daily evidence into shadow signals.
Data-blocked candidates remain registered with explicit dependency states.
"""
from __future__ import annotations

from copy import deepcopy
from statistics import median
from typing import Any

from strategy_system import valid_bars
from validation_factory import digest


AUTHORITY = "OFFLINE_SHADOW_NO_PROMOTION_NO_RISK_NO_BROKER"
VERSION = "r4-parallel-strategy-lab/1.0.0"
ETF_BASKET = frozenset({
    "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLI", "XLY",
    "XLP", "XLV", "XLU", "XLB", "XLRE", "TLT", "IEF", "GLD",
})

# Every rule is preregistered before outcomes are inspected.  Separate versions
# are charged as separate trials; overlays are never silently optimized.
SPECS: dict[str, dict[str, Any]] = {
    "XSMOM_12_1_MONTHLY_1_0_0": {"family":"CROSS_SECTIONAL_MOMENTUM","lookback":252,"skip":21,"rebalance":"MONTH_END","liquidity":"TOP_HALF_MEDIAN_DOLLAR_VOLUME_60D","selection":"TOP_DECILE_EQUAL_WEIGHT","horizonSessions":21,"state":"IMPLEMENTED_SHADOW"},
    "XSMOM_6_1_MONTHLY_1_0_0": {"family":"CROSS_SECTIONAL_MOMENTUM","lookback":126,"skip":21,"rebalance":"MONTH_END","liquidity":"TOP_HALF_MEDIAN_DOLLAR_VOLUME_60D","selection":"TOP_DECILE_EQUAL_WEIGHT","horizonSessions":21,"state":"IMPLEMENTED_SHADOW"},
    "HIGH52_MONTHLY_1_0_0": {"family":"52_WEEK_HIGH_RELATIVE_STRENGTH","lookback":252,"rebalance":"MONTH_END","liquidity":"TOP_HALF_MEDIAN_DOLLAR_VOLUME_60D","selection":"TOP_DECILE_EQUAL_WEIGHT","horizonSessions":21,"state":"IMPLEMENTED_SHADOW"},
    "ETF_TSMOM_12M_1_0_0": {"family":"ETF_TIME_SERIES_MOMENTUM","universe":sorted(ETF_BASKET),"lookback":252,"rule":"LONG_IF_252_SESSION_RETURN_POSITIVE_ELSE_CASH","rebalance":"MONTH_END","horizonSessions":21,"state":"IMPLEMENTED_SHADOW"},
    "ETF_SMA10_MONTHLY_1_0_0": {"family":"ETF_TREND","universe":sorted(ETF_BASKET),"lookbackMonths":10,"rule":"LONG_IF_MONTH_END_CLOSE_ABOVE_10_MONTH_SMA_ELSE_CASH","rebalance":"MONTH_END","horizonSessions":21,"state":"IMPLEMENTED_SHADOW"},
    "PEAD_SUE_20D_1_0_0": {"family":"PEAD","rule":"TOP_DECILE_STANDARDIZED_UNEXPECTED_EARNINGS","minimumPriorQuarters":8,"horizonSessions":20,"state":"BLOCKED_POINT_IN_TIME_CONSENSUS_ACTUAL_HISTORY"},
    "ORB20_RVOL_1_0_0": {"family":"OPENING_RANGE_BREAKOUT","timeframe":"5Min","range":"09:30_09:50_ET","relativeVolume":"FIRST_20M_GE_2X_20_SESSION_SAME_WINDOW_MEDIAN","exit":"FLAT_15:55_ET","state":"BLOCKED_INTRADAY_POINT_IN_TIME_FIXTURE_AND_COST_MODEL"},
    "REGIME_ABLATION_1_0_0": {"family":"ABSTENTION_ABLATION","arms":["BASE","SPY_ABOVE_SMA200","PANIC_ABSTAIN"],"state":"REGISTERED_PAIRED_SHADOW_REQUIRES_BASE_CANDIDATE_OUTCOMES"},
    "TENSOR_HTF_ABLATION_1_0_0": {"family":"TENSOR_ABLATION","arms":["NO_TENSOR","DAILY_ONLY","WEEKLY_ONLY","DAILY_PLUS_WEEKLY"],"lowerTimeframes":"EXCLUDED","state":"REGISTERED_PAIRED_SHADOW_REQUIRES_TIMESTAMPED_TENSOR_PACKETS"},
}


def frozen_specs() -> dict[str, dict[str, Any]]:
    return deepcopy(SPECS)


def _bars_at_or_before(raw: list[dict[str, Any]], cutoff: str) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for bar in valid_bars(raw):
        stamp = str(bar["t"])
        if stamp > cutoff:
            continue
        prior = unique.get(stamp)
        if prior is not None and prior != bar:
            raise ValueError(f"conflicting duplicate completed bar: {stamp}")
        unique[stamp] = bar
    return [unique[key] for key in sorted(unique)]


def _month_ends(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ends: dict[str, dict[str, Any]] = {}
    for bar in bars:
        ends[str(bar["t"])[:7]] = bar
    return [ends[key] for key in sorted(ends)]


def _feature(version_id: str, symbol: str, bars: list[dict[str, Any]]) -> dict[str, Any]:
    spec = SPECS[version_id]
    if version_id.startswith("XSMOM"):
        lookback, skip = int(spec["lookback"]), int(spec["skip"])
        if len(bars) < lookback + 1:
            return {"status":"UNAVAILABLE","reason":"INSUFFICIENT_COMPLETED_DAILY_BARS"}
        closes = [float(bar["c"]) for bar in bars]
        score = closes[-1-skip] / closes[-1-lookback] - 1
    elif version_id == "HIGH52_MONTHLY_1_0_0":
        if len(bars) < 252:
            return {"status":"UNAVAILABLE","reason":"INSUFFICIENT_COMPLETED_DAILY_BARS"}
        score = float(bars[-1]["c"]) / max(float(bar["h"]) for bar in bars[-252:])
    else:
        raise ValueError("not a cross-sectional candidate")
    if len(bars) < 60 or any(float(bar.get("v") or 0) <= 0 for bar in bars[-60:]):
        return {"status":"UNAVAILABLE","reason":"VALID_60D_VOLUME_REQUIRED"}
    liquidity = median(float(bar["c"]) * float(bar["v"]) for bar in bars[-60:])
    return {"status":"FEATURED","score":score,"medianDollarVolume60":liquidity,"asOf":str(bars[-1]["t"])}


def evaluate_cross_section(version_id: str, panel: dict[str, list[dict[str, Any]]], cutoff: str) -> dict[str, Any]:
    """Rank a synchronized point-in-time panel; incomplete peers never borrow future data."""
    if version_id not in {"XSMOM_12_1_MONTHLY_1_0_0","XSMOM_6_1_MONTHLY_1_0_0","HIGH52_MONTHLY_1_0_0"}:
        raise ValueError("candidate is not cross-sectional")
    features = []
    for symbol in sorted(panel):
        bars = _bars_at_or_before(panel[symbol], cutoff)
        item = _feature(version_id, symbol, bars)
        if item.get("status") == "FEATURED" and str(item["asOf"])[:10] == cutoff[:10]:
            features.append({"symbol":symbol,**item})
    if len(features) < 10:
        return {"versionId":version_id,"status":"UNAVAILABLE","reason":"INCOMPLETE_CROSS_SECTION","eligible":len(features),"asOf":cutoff,"authority":AUTHORITY}
    liquidity_cut = median(item["medianDollarVolume60"] for item in features)
    liquid = [item for item in features if item["medianDollarVolume60"] >= liquidity_cut]
    ranked = sorted(liquid, key=lambda item:(-item["score"], item["symbol"]))
    selected_count = max(1, (len(ranked) + 9) // 10)
    selected = [item["symbol"] for item in ranked[:selected_count]]
    evidence = {"versionId":version_id,"asOf":cutoff,"eligible":len(features),"liquid":len(ranked),"selected":selected,"scores":{item["symbol"]:item["score"] for item in ranked},"authority":AUTHORITY}
    return {**evidence,"status":"SETUP","evidenceHash":digest(evidence)}


def evaluate_etf_candidate(version_id: str, symbol: str, raw_bars: list[dict[str, Any]], cutoff: str) -> dict[str, Any]:
    if version_id not in {"ETF_TSMOM_12M_1_0_0","ETF_SMA10_MONTHLY_1_0_0"}:
        raise ValueError("candidate is not an ETF trend candidate")
    if symbol not in ETF_BASKET:
        return {"versionId":version_id,"symbol":symbol,"status":"INELIGIBLE","reason":"OUTSIDE_FROZEN_ETF_BASKET","authority":AUTHORITY}
    bars = _bars_at_or_before(raw_bars, cutoff)
    if not bars or str(bars[-1]["t"])[:10] != cutoff[:10]:
        return {"versionId":version_id,"symbol":symbol,"status":"UNAVAILABLE","reason":"CUTOFF_BAR_REQUIRED","authority":AUTHORITY}
    if version_id == "ETF_TSMOM_12M_1_0_0":
        if len(bars) < 253:
            return {"versionId":version_id,"symbol":symbol,"status":"UNAVAILABLE","reason":"INSUFFICIENT_COMPLETED_DAILY_BARS","authority":AUTHORITY}
        metric = float(bars[-1]["c"]) / float(bars[-253]["c"]) - 1
        passed = metric > 0
        metrics = {"return252":metric}
    else:
        months = _month_ends(bars)
        if len(months) < 10:
            return {"versionId":version_id,"symbol":symbol,"status":"UNAVAILABLE","reason":"INSUFFICIENT_COMPLETED_MONTH_ENDS","authority":AUTHORITY}
        closes = [float(bar["c"]) for bar in months[-10:]]
        sma10 = sum(closes) / 10
        passed = closes[-1] > sma10
        metrics = {"monthEndClose":closes[-1],"sma10Month":sma10}
    evidence = {"versionId":version_id,"symbol":symbol,"asOf":cutoff,"metrics":metrics,"authority":AUTHORITY}
    return {**evidence,"status":"SETUP" if passed else "WAIT","evidenceHash":digest(evidence)}


def dependency_status() -> dict[str, Any]:
    candidates = {version:{"family":spec["family"],"state":spec["state"],"specHash":digest({"versionId":version,**spec,"authority":AUTHORITY})} for version,spec in SPECS.items()}
    return {"version":VERSION,"authority":AUTHORITY,"candidates":candidates,"implemented":sum(item["state"]=="IMPLEMENTED_SHADOW" for item in SPECS.values()),"registered":len(SPECS),"automaticPromotion":False,"strategyAuthority":False,"riskAuthority":False,"brokerAuthority":False}
