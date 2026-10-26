"""R10 native schema and physical decision gates; no native-data substitution.

Synthetic schema acceptance establishes required fields, not source authenticity,
native adapter implementation, or permission to trade. All are separate gates.
"""
from datetime import datetime
import math
import numpy as np

VERSION = "r10-bolt-clock-anchor-physical-gates-v1"

def _real(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def _t(s):
    if not isinstance(s, str):
        raise ValueError("clock must be an ISO string")
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("aware clock")
    return t

def native_gate(row, cutoff):
    try:
        now = _t(cutoff)
        snapshot = _t(row["snapshot"])
        ts, recv, ready, heartbeat = [_t(row[k]) for k in ("event_time", "first_received", "ready", "heartbeat")]
        if not ts <= recv <= ready <= snapshot <= now or heartbeat > snapshot:
            return "NO_TRADE_CLOCK"
        if (snapshot-heartbeat).total_seconds() > 1 or (snapshot-ts).total_seconds() > 60:
            return "NO_TRADE_STALE"
        if row.get("feed") != "CME_NATIVE" or row.get("exercise") != "EUROPEAN" or row.get("underlier_type") != "FIXED_QUARTERLY_FUTURES":
            return "NO_TRADE_NATIVE_CONTRACT"
        if row.get("deliverable_before") != row.get("deliverable_after") or not row.get("deliverable_before"):
            return "NO_TRADE_UNDERLIER_ROLL"
        if not (_t(row["calendar_received"]) <= _t(row["snapshot"]) <= now and _t(row["rule_received"]) <= _t(row["snapshot"])):
            return "NO_TRADE_CALENDAR_RULE_VINTAGE"
        if not (_t(row["snapshot"]) < _t(row["expiry_before"]) < _t(row["event"]) < _t(row["expiry_after"]) < _t(row["underlying_expiry"])):
            return "NO_TRADE_BRACKET"
        if row.get("fixing_rule") != "VERIFIED_RULE_VERSION" or row.get("delivery_adapter") != "INDEPENDENTLY_VERIFIED":
            return "NO_TRADE_NATIVE_PAYOFF_ADAPTER"
        for k in ("bid", "ask", "bid_size", "ask_size", "midpoint_floor_tick"):
            if isinstance(row[k], bool) or not math.isfinite(row[k]) or row[k] <= 0:
                return "NO_TRADE_QUOTE_DOMAIN"
        if row["bid"] >= row["ask"]:
            return "NO_TRADE_LOCKED_CROSSED"
        mid = (row["bid"]+row["ask"])/2
        if (row["ask"]-row["bid"])/max(mid,row["midpoint_floor_tick"]) > .20:
            return "NO_TRADE_SPREAD"
        if row.get("distinct_strikes",0) < 9 or row.get("both_sides_covered") is not True or row.get("complete_chain") is not True:
            return "NO_TRADE_CHAIN_COVERAGE"
        if row.get("quote_condition") != "ELIGIBLE_NATIVE_BOOK":
            return "NO_TRADE_QUOTE_CONDITION"
        if row.get("native_authenticity_verified") is not True or row.get("continuous_tail_certified") is not True:
            return "NO_TRADE_AUTHENTICITY_OR_TAIL"
        return "INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED"
    except (KeyError, ValueError, TypeError):
        return "NO_TRADE_MALFORMED"

def crossing_at_anchor(x, y, anchor, theta):
    vals = (anchor,theta)
    if any(isinstance(v,bool) or not math.isfinite(v) or v <= 0 for v in vals):
        raise ValueError("positive finite anchor/threshold")
    x,y = np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if x.ndim != 1 or y.ndim != 1 or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("finite states")
    return ((x[:,None] <= anchor)&(y[None,:] >= anchor*(1+theta))).astype(float) - ((x[:,None] >= anchor)&(y[None,:] <= anchor*(1-theta))).astype(float)

def physical_admission(scenario_net_portfolio_increments, paired_increment_lcb,
                       training_origins, calibration_origins, development_origins,
                       native_gate_status, margin=.005):
    """All supplied conservative NET scenarios must clear portfolio-unit margin.

    These values must already contain exact funded costs once. A Q crossing
    score cannot supply them. No cost is deducted a second time. This helper
    cannot authenticate that supplied physical forecasts are calibrated.
    """
    if not _real(margin) or margin < .005:
        return "NO_TRADE_MARGIN_DOMAIN"
    try:
        vals = list(scenario_net_portfolio_increments)
    except TypeError:
        return "NO_TRADE_PHYSICAL_FORECAST"
    if native_gate_status != "INPUT_SCHEMA_VALID_PHYSICAL_MODEL_STILL_REQUIRED":
        return "NO_TRADE_NATIVE_INPUTS"
    if any(type(v) is not int or v < 0 for v in (training_origins,calibration_origins,development_origins)):
        return "NO_TRADE_SUPPORT_DOMAIN"
    if min(training_origins/80,calibration_origins/40,development_origins/24) < 1:
        return "NO_TRADE_INSUFFICIENT_PHYSICAL_SUPPORT"
    if not vals or any(not _real(v) for v in vals) or not _real(paired_increment_lcb):
        return "NO_TRADE_PHYSICAL_FORECAST"
    if min(vals) <= margin or paired_increment_lcb <= 0:
        return "NO_TRADE_NET_EDGE_OR_CONTROL"
    return "RESEARCH_ADMISSION_ONLY_NO_EXECUTION_AUTHORIZATION"
