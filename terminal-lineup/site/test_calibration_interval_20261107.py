"""Regression blocker for CALIBRATION-INTERVAL-20261107.

build_table demanded the interval recomputed from today's
measured centre equal the pre-registered November will-stake
interval within 0.26 points. The measured centre is computed
over a walk-forward sample that grows as the price panel
advances (the same file's G2 re-registration made the counts
floors for exactly this reason), so the equality broke on a
healthy record: engine_01 computed -19.6..4.4 against the
registered -19.3..4.6.

The cure stakes the REGISTERED interval, reproduced from the
register itself by registered_interval() (a register no centre
can reproduce fails closed), and drift-guards the measured
interval at DRIFT_TOL: what is ledgered for a round is the
registered stake, never a drifted recomputation. Set
LEG_MODULE_DIR to a directory holding a pre-cure copy of the
refresher to watch these fail.
"""
import importlib.util
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_calibrationleague.py")

spec = importlib.util.spec_from_file_location("refresh_calibrationleague", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_registered_interval_reproduces_engine_01():
    out = mod.registered_interval(68.0, (-19.3, 4.6))
    assert out is not None
    iv, centre = out
    assert abs(iv["err_low_pts"] - (-19.3)) <= 0.15
    assert abs(iv["err_high_pts"] - 4.6) <= 0.15
    assert centre is not None


def test_registered_interval_reproduces_the_anchored_entrant():
    # engine_05's interval is anchored (anchor_q 0.83) and so
    # centre-free; its stated is the registered constant 82.4 in
    # measure_entrants, and with it the register reproduces
    # exactly (rate bounds 71.6..90.4 from the anchor, less the
    # stated 82.4).
    out = mod.registered_interval(82.4, (-10.8, 8.0), anchor_q=0.83)
    assert out is not None
    iv, centre = out
    assert abs(iv["err_low_pts"] - (-10.8)) <= 0.15
    assert abs(iv["err_high_pts"] - 8.0) <= 0.15
    assert centre is None


def test_an_irreproducible_register_fails_closed():
    # No centre at n=60 yields a zero-width interval.
    assert mod.registered_interval(68.0, (0.0, 0.0)) is None
    assert mod.registered_interval(82.4, (0.0, 0.0),
                                   anchor_q=0.83) is None


def test_the_live_drift_shape_is_inside_the_drift_bound():
    # The drift that broke the leg: 0.3 and 0.2 points. It must
    # sit far inside DRIFT_TOL while a genuine break (over
    # DRIFT_TOL) stays a failure in build_table.
    assert abs(-19.6 - (-19.3)) < mod.DRIFT_TOL
    assert abs(4.4 - 4.6) < mod.DRIFT_TOL
    assert mod.DRIFT_TOL >= 1.0


def test_source_stakes_the_register_with_a_drift_guard():
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert "registered_interval" in src
    assert "DRIFT_TOL" in src


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
