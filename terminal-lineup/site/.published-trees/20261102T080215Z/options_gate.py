#!/usr/bin/env python3
"""Options candidate gate: Greeks freshness and IV ceiling.

One source of truth for DEEP-PASS 3.1 item 3 (adopted as is from
Ausar's Tradier options leg, Section 2.7 of the deep pass):

- A ranked contract must carry a Greek timestamp no older than
  75 minutes where the provider supplies one. The 75 minutes
  matches ORATS' roughly hourly Greeks refresh. A Greek dated
  more than 5 seconds in the future is also refused: a future
  dated Greek is a broken clock, not a fresh one.
- Where the provider supplies no Greek timestamp, the contract
  is NOT silently trusted and NOT refused for that reason alone:
  it is labelled "undated", in the open, exactly as the deep
  pass directs. Every consumer of this gate must surface that
  label beside any candidate built from undated Greeks.
- IV ceiling: implied volatility at or above 5.0 (500 percent)
  rejects the candidate. An IV that is present but not a finite
  positive number also rejects. An absent IV stays absent: the
  candidate is admitted with iv_state "absent" and no IV based
  figure may be built from it.

This module is pure: callers pass timestamps in (epoch seconds
or ISO strings) and get a verdict dict back. Nothing here reads
a clock, a file or a network.
"""

import math
from datetime import datetime, timezone

GREEK_MAX_AGE_SECONDS = 75 * 60          # 4500, the 75 minute gate
GREEK_FUTURE_TOLERANCE_SECONDS = 5       # a Greek may lead by 5s
IV_CEILING = 5.0                         # 500 percent, at or above rejects

GREEK_STATES = ("fresh", "stale", "future", "undated")
IV_STATES = ("ok", "absent", "over_ceiling", "invalid")


def _to_epoch(ts):
    """Epoch seconds for an epoch number or an ISO timestamp
    string, or None when the value carries no usable time."""
    if ts is None or isinstance(ts, bool):
        return None
    if isinstance(ts, (int, float)):
        return float(ts) if math.isfinite(float(ts)) else None
    if isinstance(ts, str):
        text = ts.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    return None


def greek_freshness(greek_ts, now_ts):
    """Classify one Greek timestamp against a stated now.

    Returns "undated" when no usable Greek timestamp exists (the
    provider supplied none, or an unparseable one: either way the
    Greek cannot be dated and must be labelled, not trusted),
    "future" when it is dated more than the tolerance ahead of
    now, "stale" when it is older than the 75 minute gate, and
    "fresh" otherwise. A now that cannot be read makes every
    dated Greek "undated" too: freshness unprovable is labelled,
    never assumed.
    """
    g = _to_epoch(greek_ts)
    n = _to_epoch(now_ts)
    if g is None or n is None:
        return "undated"
    age = n - g
    if age < -GREEK_FUTURE_TOLERANCE_SECONDS:
        return "future"
    if age > GREEK_MAX_AGE_SECONDS:
        return "stale"
    return "fresh"


def iv_state(iv):
    """Classify one implied volatility reading (a decimal, so
    0.20 is 20 percent and the ceiling 5.0 is 500 percent)."""
    if iv is None:
        return "absent"
    if isinstance(iv, bool) or not isinstance(iv, (int, float)) \
            or not math.isfinite(float(iv)) or float(iv) <= 0:
        return "invalid"
    if float(iv) >= IV_CEILING:
        return "over_ceiling"
    return "ok"


def gate_candidate(candidate, now_ts):
    """Gate one candidate contract.

    candidate is a mapping that may carry "greek_ts" (or
    "greeks_ts") and "iv". Returns a verdict dict:
    {admitted, greek_state, iv_state, reasons}. Undated Greeks
    and an absent IV admit with their labels attached; stale or
    future Greeks, an over ceiling IV and an invalid IV refuse.
    """
    greek_ts = candidate.get("greek_ts", candidate.get("greeks_ts"))
    gstate = greek_freshness(greek_ts, now_ts)
    istate = iv_state(candidate.get("iv"))
    reasons = []
    if gstate == "stale":
        reasons.append("greeks_stale_over_75_minutes")
    elif gstate == "future":
        reasons.append("greeks_future_dated")
    if istate == "over_ceiling":
        reasons.append("iv_at_or_over_ceiling")
    elif istate == "invalid":
        reasons.append("iv_invalid")
    return {"admitted": not reasons, "greek_state": gstate,
            "iv_state": istate, "reasons": reasons}


def gate_summary(candidates, now_ts):
    """Gate a list of candidates and count the outcome, so a
    surface can publish the gate's effect instead of only its
    survivors. Counts always sum: total == admitted + refused,
    and the Greek and IV state counts each sum to total."""
    verdicts = [gate_candidate(c, now_ts) for c in candidates]
    out = {"total": len(verdicts),
           "admitted": sum(1 for v in verdicts if v["admitted"]),
           "refused": sum(1 for v in verdicts if not v["admitted"]),
           "greek_max_age_seconds": GREEK_MAX_AGE_SECONDS,
           "iv_ceiling": IV_CEILING,
           "greek_states": {s: 0 for s in GREEK_STATES},
           "iv_states": {s: 0 for s in IV_STATES}}
    for v in verdicts:
        out["greek_states"][v["greek_state"]] += 1
        out["iv_states"][v["iv_state"]] += 1
    return out
