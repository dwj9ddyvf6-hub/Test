#!/usr/bin/env python3
"""Regression blocker: HONESTPOP-CAP-PROBE-20261114.

The honest-pop self-test probed the IV correction only on rows[0],
the deepest in-the-money strike. On the 2026-11-13 price panel that
row's IV chance is 0.9903, above the correction's stated 99 percent
holding cap, so its corrected value (0.99) could not lift and the
refresh refused its own output from 2026-11-10 on, although the
correction lifts every uncapped row by the full 13.5 points.

These tests pin: (1) the correction's exact arithmetic including the
cap region, (2) the preserved pre-cure probe really does refuse on
the current synthetic surface (fail direction), (3) the cured
self-test passes end to end on the current panel.
"""
import importlib.util
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hp = _load("refresh_honestpop_cured",
           os.path.join(HERE, "refresh_honestpop.py"))


def test_correction_exact_arithmetic():
    for p in (0.01, 0.10, 0.3644, 0.5988, 0.8017, 0.8549, 0.855,
              0.9257, 0.9903, 0.999):
        want = min(max(p + 0.135, 0.01), 0.99)
        got = hp.corrected_iv_pop(p)
        assert abs(got - want) < 1e-12, (p, got, want)
    # strict lift on every uncapped input
    for p in (0.01, 0.30, 0.60, 0.8549):
        assert hp.corrected_iv_pop(p) > p


def _synthetic_surface(mod):
    with open(mod.PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    closes = [float(r[4]) for r in panel["SPY"]]
    spot = closes[-1]
    strikes_iv = {}
    k = 600.0
    while k <= 920.0:
        strikes_iv[k] = 0.16 + 0.00012 * max(0.0, spot - k)
        k += 5.0
    return mod.compute_surface("SPY", spot, closes, date(2026, 10, 30),
                               date(2026, 10, 23), strikes_iv)


def test_precure_probe_refuses_on_current_surface():
    """Fail direction: the old rows[0]-only probe refuses today's
    surface because rows[0] sits above the cap, while every uncapped
    row lifts by the full correction."""
    surf = _synthetic_surface(hp)
    first = surf["rows"][0]["benchmark_p"]
    assert not (first < hp.corrected_iv_pop(first) <= 0.99), (
        "pre-cure probe would not refuse; the bug no longer "
        "reproduces and this blocker's premise must be re-checked")
    uncapped = [r for r in surf["rows"] if r["benchmark_p"] < 0.855]
    assert uncapped, "no uncapped row to prove the lift on"
    for r in uncapped:
        assert abs(hp.corrected_iv_pop(r["benchmark_p"])
                   - (r["benchmark_p"] + 0.135)) < 1e-9


def test_cured_self_test_passes():
    with open(hp.PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    result = hp.oracle_self_test(panel)
    assert result["state"] == "passed"
    assert result["synthetic_strikes"] >= 10


if __name__ == "__main__":
    test_correction_exact_arithmetic()
    print("pass test_correction_exact_arithmetic")
    test_precure_probe_refuses_on_current_surface()
    print("pass test_precure_probe_refuses_on_current_surface")
    test_cured_self_test_passes()
    print("pass test_cured_self_test_passes")
