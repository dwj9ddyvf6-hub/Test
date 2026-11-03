#!/usr/bin/env python3
"""Shared calibration attestation block for the engine pages
(RC-22 cure, 2026-10-30).

One shared mechanism, in the pattern of proof_gate_block.py: every
engine refresher attaches this block to its page data immediately
before its provenance stamp. The block is read from the registry's
per engine calibration_attestation record, which is populated from
the engine's own graded record in the forecast ledger (see
forecast/grading.py attestation_record), and the page's probability
rendering decision is routed through grading.render_probability /
probability_render_decision: a number may be rendered as a
probability only when a calibrated out of sample attestation is on
record. No engine currently carries one, so every page renders its
numbers as uncalibrated scores and says why, in the block.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "forecast") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "forecast"))

try:
    from forecast import grading as _grading
    from forecast import registry as _registry
except Exception:  # refresh stays runnable standalone
    _grading = None
    _registry = None


def attestation_block(engine_id):
    """The block for one engine, or None when the registry cannot
    be read (the refresher then publishes without it rather than
    inventing one)."""
    if _grading is None or _registry is None:
        return None
    try:
        reg = _registry.load()
        entry = reg.engines[engine_id]
    except Exception:
        return None
    decision = _grading.probability_render_decision(entry)
    return {
        "engine_id": engine_id,
        "attestation": entry.get("calibration_attestation"),
        # Named zero state (terminal audit cure, 2026-10-31): an
        # engine that has never ledgered a forecast carries its
        # reason and trigger on every page, not as a settled
        # proving state. Present only while the count is zero.
        "zero_forecast_state": entry.get("zero_forecast_state"),
        "probability_rendering": {
            "render_as_probability": decision["render_as_probability"],
            "rendered_as": "probability"
            if decision["render_as_probability"]
            else "uncalibrated_score",
            "reason": decision["reason"],
        },
    }


def render_probability(engine_id, p):
    """Route one probability shaped number through the gate for a
    page: returns grading.render_probability's labelled dict."""
    if _grading is None or _registry is None:
        return {"value": float(p), "rendered_as": "uncalibrated_score",
                "reason": "attestation machinery unavailable; "
                          "published as an uncalibrated score"}
    reg = _registry.load()
    return _grading.render_probability(reg.engines[engine_id], p)


def attach(data, engine_id):
    """Return ``data`` with the shared attestation block attached.
    Only adds the calibration_attestation key; nothing else in the
    page changes."""
    block = attestation_block(engine_id)
    if block is None:
        return data
    out = dict(data)
    out["calibration_attestation"] = block
    return out
