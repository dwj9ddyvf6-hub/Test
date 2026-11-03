#!/usr/bin/env python3
"""Adapted FE forms for Engines 10 and 12 (DEEP-PASS 3.2 items
6 and 7, 2026-10-29).

Forms adopted, coefficients NOT imported as tuned parameters
(the source author states his coefficients are starter
transforms; the 3.4 item 9 ruling keeps numbers out). What lands
here is each formula's shape, our registered constants stated in
this module, and strict input discipline: a missing input is a
named not_recorded state, never a zero; an out of range input is
refused, never silently floored or clipped except where the form
itself clips (the FE17 dispersion term).

FE17 (Engine 12 centre): centre = (0.60 * implied + 0.40 *
historical) * (1 + 0.08 * clip(dispersion_z, -2, 2)) *
timing_quality. The dispersion input is the forecast error
dispersion on record, adopted as the registered input under
its own true name by the registry amendment of 2026-10-30;
it is not cross analyst estimate dispersion. Adaptation
against the code read: a negative
implied or historical move is refused, not floored to zero
inside the scorer as his code does. The returned estimate is
the forecast itself; his model_score (dispersion adjustment
minus 1) is returned separately as dispersion_adjustment and
must never be used as the forecast magnitude or ranked across
engines.

FE18 (Engine 12 sub forecast): score = (0.50 * surprise_z +
0.30 * observed_post_event_drift_z + 0.20 * sector_residual_z)
* (0.5 + 0.5 * revision_breadth), clipped to [-8, 8] under the
FE signed score convention. It is a persistence form: it
consumes already observed drift, so a sub forecast may only be
issued after the drift window it consumes has closed (the
ledger helper in refresh_earningsdistribution.py enforces
this; see ledger_fe18_sub_forecast there).

FE23 (Engine 10): discretionary flow discounted by a single
non 10b5-1 confidence multiplier, recency, and an illiquidity
damper 1 / (1 + max(0, illiquidity_z)); liquid issuers get no
boost. The adaptation is the classifier: Form 4 footnote plan
status classification (plan status is footnote text, not a
structured field), with its precision tracked against a
labelled set and a registered kill floor: below the floor the
classifier is retired and plan adjustment stops.

FE12 (DEEP-PASS 3.2 item 10): a session quality guard, not an
engine. Only the one sided form is adopted: every input enters
as max(0, value), so an improvement in any reading can never
raise the flag and a deterioration can never be hidden by an
improvement elsewhere. His intercept (minus 1.00) and his
logit weights are NOT imported, and his sigmoid is not used:
the source read showed the sigmoid saturates past a logit of
about 3, so a guard with graded responses needs a graded
scale. Ours: deterioration is the equal weighted mean of the
one sided parts over the inputs actually supplied (equal
weights are this adoption's registered choice, stated here),
the band widen factor is 1 + 0.25 * deterioration, and the
guard trips at a deterioration of 1.0. A missing input is
named, never zero filled: with some inputs supplied the state
is partial and the mean is over those supplied, with the count
disclosed; with none supplied the state is not_recorded and
the guard changes nothing.

FE20 (DEEP-PASS 3.2 item 11): the panel reliability form as
the standard discount for panel derived inputs: reliability =
panel_stability * coverage / (1 + abs(panel_drift_z)), bounded
above by 1, quartered at a drift z of 3. A panel derived input
is discounted by multiplying it by the reliability. Stability
and coverage must lie in [0, 1]; any missing input names a
not_recorded state and no discount is applied, because a
reliability with a missing leg is not a number this lineup
will invent.
"""

import re

FE17_IMPLIED_WEIGHT = 0.60
FE17_HISTORICAL_WEIGHT = 0.40
FE17_DISPERSION_COEF = 0.08
FE17_DISPERSION_CLIP = 2.0

FE18_WEIGHTS = (0.50, 0.30, 0.20)
FE18_SCORE_CLIP = 8.0

# Our registered floor for the footnote classifier (a ruling of
# this adoption, stated here before any labelled set exists):
# measured precision below this on a labelled set of at least
# 20 footnotes retires the classifier.
PLAN_CLASSIFIER_PRECISION_FLOOR = 0.90
PLAN_CLASSIFIER_MIN_LABELLED = 20

_PLAN_PATTERNS = [
    r"10b5\s*-\s*1",
    r"rule\s+10b5",
    r"trading\s+plan\s+(adopted|entered|established)",
    r"pursuant\s+to\s+a\s+(written\s+)?plan",
]
_PLAN_RE = [re.compile(p, re.IGNORECASE) for p in _PLAN_PATTERNS]


def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def fe17_centre(implied_move_pct, historical_event_move_pct,
                forecast_error_dispersion_z, timing_quality):
    """FE17 blend as a point estimate of the absolute earnings
    move, in percent. The dispersion input is forecast error
    dispersion: the standard deviation of the name's own prior
    forecast errors, z scored across reporting names, adopted
    as this centre's registered dispersion input by the
    registry amendment of 2026-10-30 under its own true name.
    It is not cross analyst estimate dispersion. Returns a
    state dict; missing inputs are named, never substituted."""
    missing = []
    if implied_move_pct is None:
        missing.append("implied_move")
    if historical_event_move_pct is None:
        missing.append("historical_event_move")
    if forecast_error_dispersion_z is None:
        missing.append("forecast_error_dispersion_z")
    if timing_quality is None:
        missing.append("timing_quality")
    if missing:
        return {"state": "not_recorded", "centre_pct": None,
                "missing": missing}
    if implied_move_pct < 0 or historical_event_move_pct < 0:
        raise ValueError(
            "FE17 move inputs must be non negative; a negative "
            "input is refused, not floored to zero")
    if not (0.0 < timing_quality <= 1.0):
        raise ValueError("timing_quality must lie in (0, 1]")
    dispersion_adj = FE17_DISPERSION_COEF * _clip(
        forecast_error_dispersion_z, -FE17_DISPERSION_CLIP,
        FE17_DISPERSION_CLIP)
    centre = (FE17_IMPLIED_WEIGHT * implied_move_pct
              + FE17_HISTORICAL_WEIGHT
              * historical_event_move_pct) \
        * (1.0 + dispersion_adj) * timing_quality
    return {"state": "recorded", "centre_pct": round(centre, 4),
            "missing": [],
            "dispersion_input": "forecast_error_dispersion",
            "dispersion_z": round(forecast_error_dispersion_z, 4),
            "dispersion_adjustment": round(dispersion_adj, 4),
            "model_score_normalised": round(centre, 4)}


def fe18_score(standardized_surprise_z,
               observed_post_event_drift_z, sector_residual_z,
               revision_breadth):
    """FE18 signed drift score after controls. Missing inputs
    are named, never substituted."""
    missing = []
    if standardized_surprise_z is None:
        missing.append("standardized_surprise_z")
    if observed_post_event_drift_z is None:
        missing.append("observed_post_event_drift")
    if sector_residual_z is None:
        missing.append("sector_residual_z")
    if revision_breadth is None:
        missing.append("revision_breadth")
    if missing:
        return {"state": "not_recorded", "score": None,
                "missing": missing}
    if not (0.0 <= revision_breadth <= 1.0):
        raise ValueError("revision_breadth must lie in [0, 1]")
    raw = (FE18_WEIGHTS[0] * standardized_surprise_z
           + FE18_WEIGHTS[1] * observed_post_event_drift_z
           + FE18_WEIGHTS[2] * sector_residual_z) \
        * (0.5 + 0.5 * revision_breadth)
    return {"state": "recorded",
            "score": round(_clip(raw, -FE18_SCORE_CLIP,
                                 FE18_SCORE_CLIP), 4),
            "missing": []}


def classify_plan_status(footnote_text):
    """Classify one Form 4 footnote's plan status.
    Returns plan_10b5_1 when plan language matches,
    discretionary when footnote text exists with no plan
    language, unknown when there is no footnote text to read.
    Confidence is the classifier's stated certainty in its own
    label shape: a direct plan match is high, an absence based
    discretionary call is lower, unknown carries none."""
    if not footnote_text or not str(footnote_text).strip():
        return {"label": "unknown", "confidence": None,
                "matched": None}
    for pat, rx in zip(_PLAN_PATTERNS, _PLAN_RE):
        if rx.search(footnote_text):
            return {"label": "plan_10b5_1", "confidence": 0.95,
                    "matched": pat}
    return {"label": "discretionary", "confidence": 0.70,
            "matched": None}


def classifier_precision(labelled):
    """labelled: [(footnote_text, expected_label)]. Precision
    over the plan_10b5_1 calls (the calls the adjustment acts
    on): of the footnotes the classifier calls plan, the share
    that truly are plan. None when nothing was called plan."""
    calls = correct = 0
    for text, expected in labelled:
        got = classify_plan_status(text)["label"]
        if got == "plan_10b5_1":
            calls += 1
            if expected == "plan_10b5_1":
                correct += 1
    return {"labelled": len(labelled), "plan_calls": calls,
            "plan_correct": correct,
            "precision": (round(correct / calls, 4)
                          if calls else None)}


def classifier_kill_state(precision_report):
    """The kill floor, applied exactly as registered: precision
    is judged only on at least PLAN_CLASSIFIER_MIN_LABELLED
    labelled footnotes; below the floor the classifier is
    retired; with too little labelled evidence the state is
    unmeasured, never passed."""
    if precision_report["labelled"] < PLAN_CLASSIFIER_MIN_LABELLED:
        return "unmeasured"
    p = precision_report["precision"]
    if p is None:
        return "unmeasured"
    return "retired" if p < PLAN_CLASSIFIER_PRECISION_FLOOR \
        else "standing"


def fe23_adjusted_flow(discretionary_net_flow_z,
                       non_10b5_1_confidence, recency,
                       illiquidity_z):
    """FE23 adjusted insider flow: the discretionary flow
    discounted by the single non plan confidence multiplier and
    recency, damped on positive illiquidity only."""
    missing = []
    if discretionary_net_flow_z is None:
        missing.append("discretionary_net_flow_z")
    if non_10b5_1_confidence is None:
        missing.append("non_10b5_1_confidence")
    if recency is None:
        missing.append("recency")
    if illiquidity_z is None:
        missing.append("illiquidity_z")
    if missing:
        return {"state": "not_recorded", "score": None,
                "missing": missing}
    for name, v in (("non_10b5_1_confidence",
                     non_10b5_1_confidence),
                    ("recency", recency)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} must lie in [0, 1]")
    damper = 1.0 / (1.0 + max(0.0, illiquidity_z))
    score = discretionary_net_flow_z * non_10b5_1_confidence \
        * recency * damper
    return {"state": "recorded", "score": round(score, 4),
            "missing": [], "illiquidity_damper": round(damper, 4)}


# ---- FE12 session quality guard (3.2 item 10) -----------------

FE12_INPUTS = ("spread_z", "depth_drop_z", "volume_concentration",
               "realised_vol_z")
GUARD_WIDEN_COEF = 0.25
GUARD_TRIP_DETERIORATION = 1.0


def fe12_session_quality_guard(spread_z=None, depth_drop_z=None,
                               volume_concentration=None,
                               realised_vol_z=None):
    """One sided liquidity deterioration flag. Each supplied
    input contributes max(0, value); deterioration is the mean
    of those parts over the inputs supplied. Returns a state
    dict: recorded (all four supplied), partial (some), or
    not_recorded (none, with every input named missing)."""
    supplied = {"spread_z": spread_z, "depth_drop_z": depth_drop_z,
                "volume_concentration": volume_concentration,
                "realised_vol_z": realised_vol_z}
    if volume_concentration is not None \
            and not (0.0 <= volume_concentration <= 1.0):
        raise ValueError("volume_concentration must lie in [0, 1]")
    present = {k: v for k, v in supplied.items() if v is not None}
    missing = [k for k in FE12_INPUTS if k not in present]
    if not present:
        return {"state": "not_recorded", "deterioration": None,
                "missing": missing, "inputs_used": [],
                "band_widen_factor": 1.0, "tripped": False}
    parts = {k: max(0.0, float(v)) for k, v in present.items()}
    deterioration = sum(parts.values()) / len(parts)
    return {"state": "recorded" if not missing else "partial",
            "deterioration": round(deterioration, 4),
            "missing": missing,
            "inputs_used": sorted(parts),
            "one_sided_parts": {k: round(v, 4)
                                for k, v in sorted(parts.items())},
            "band_widen_factor": round(
                1.0 + GUARD_WIDEN_COEF * deterioration, 4),
            "tripped": deterioration >= GUARD_TRIP_DETERIORATION}


def fe12_widen_band(lower, upper, guard):
    """Widen a band around its midpoint by the guard's widen
    factor. A not_recorded guard returns the band unchanged;
    the guard can only widen, never narrow."""
    if not guard or guard.get("deterioration") is None:
        return (lower, upper)
    factor = float(guard["band_widen_factor"])
    mid = (float(lower) + float(upper)) / 2.0
    half = (float(upper) - float(lower)) / 2.0 * factor
    return (round(mid - half, 4), round(mid + half, 4))


def fe12_abstention_threshold(base_threshold, guard):
    """Raise an abstention threshold by the guard: a consumer
    that abstains below a confidence threshold abstains more
    readily in a deteriorated session. A not_recorded guard
    leaves the threshold unchanged."""
    if not guard or guard.get("deterioration") is None:
        return {"threshold": base_threshold, "raised": False,
                "tripped": False}
    raised = float(base_threshold) * float(guard["band_widen_factor"])
    return {"threshold": round(raised, 4),
            "raised": raised > float(base_threshold),
            "tripped": bool(guard.get("tripped"))}


# ---- FE20 panel reliability discount (3.2 item 11) ------------

def fe20_panel_reliability(panel_stability, coverage, panel_drift_z):
    """reliability = stability * coverage / (1 + abs(drift_z)).
    Missing inputs are named, never substituted."""
    missing = []
    if panel_stability is None:
        missing.append("panel_stability")
    if coverage is None:
        missing.append("coverage")
    if panel_drift_z is None:
        missing.append("panel_drift_z")
    if missing:
        return {"state": "not_recorded", "reliability": None,
                "missing": missing}
    for name, v in (("panel_stability", panel_stability),
                    ("coverage", coverage)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} must lie in [0, 1]")
    reliability = panel_stability * coverage \
        / (1.0 + abs(float(panel_drift_z)))
    return {"state": "recorded",
            "reliability": round(reliability, 4), "missing": []}


def fe20_discounted(value, reliability_report):
    """A panel derived input discounted by its panel's
    reliability. An unrecorded reliability discounts nothing
    and says so."""
    if not reliability_report \
            or reliability_report.get("reliability") is None:
        return {"state": "not_recorded", "value": None,
                "missing": (reliability_report or {}).get(
                    "missing", ["panel_reliability"])}
    return {"state": "recorded",
            "value": round(float(value)
                           * reliability_report["reliability"], 4),
            "reliability": reliability_report["reliability"]}


def fe20_composition_stability(current_ids, prior_ids):
    """Panel composition stability between two recorded panels:
    the Jaccard overlap of the member sets (members in both,
    over members in either). Either panel empty or absent is a
    not_recorded state, never a zero."""
    if not current_ids or not prior_ids:
        return {"state": "not_recorded", "stability": None,
                "missing": ["panel_composition_history"]}
    cur, pri = set(current_ids), set(prior_ids)
    union = cur | pri
    if not union:
        return {"state": "not_recorded", "stability": None,
                "missing": ["panel_composition_history"]}
    return {"state": "recorded",
            "stability": round(len(cur & pri) / len(union), 4),
            "members_current": len(cur), "members_prior": len(pri),
            "members_both": len(cur & pri)}
