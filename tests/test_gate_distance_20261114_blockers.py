"""GATE-DISTANCE-20261114 blockers (H-TRIAGE-1 desk landing).

Fail-first: on the pre-patch tree desk3.gate_distance does not
exist and cycle.py carries no recorder seam, so every test here
fails; on the patched tree all pass.
"""
import glob
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3 import gate_distance  # noqa: E402

DESK = os.path.join(os.path.dirname(__file__), "..")


def _retained_view():
    snaps = sorted(glob.glob(os.path.join(
        DESK, "state", "snapshots", "*.json")))
    with open(snaps[-1]) as fh:
        s = json.load(fh)
    return s["asof"], s["data"]


class TestGateDistanceFixtureDrive(unittest.TestCase):
    def test_each_probed_family_emits_populated_record(self):
        asof, view = _retained_view()
        by_probe = {}
        for sleeve in gate_distance.PROBED_SLEEVES:
            for r in gate_distance.record(asof, sleeve, view):
                by_probe.setdefault(r["probe"], []).append(r)
        for family in ("sma200", "funding", "absorption",
                       "breakout", "rsi2"):
            rows = by_probe.get(family) or []
            self.assertTrue(rows, f"no records for family {family}")
            populated = [r for r in rows
                         if r["measured"] is not None
                         and r["threshold"] is not None
                         and r["distance"] is not None]
            self.assertTrue(
                populated,
                f"family {family} emitted no populated record")
            for r in populated:
                for k in ("asof", "sleeve", "symbol", "gate", "unit"):
                    self.assertIn(k, r)

    def test_missing_series_is_named_never_fabricated(self):
        asof, view = _retained_view()
        view = dict(view)
        bars = dict(view.get("bars") or {})
        bars.pop("QQQ|1Day", None)
        view["bars"] = bars
        recs = gate_distance.record(
            asof, "aster_rec_rsi2_long_touch_a", view)
        self.assertEqual(len(recs), 1)
        self.assertIsNone(recs[0]["measured"])
        self.assertIsNone(recs[0]["distance"])
        self.assertTrue(recs[0]["note"],
                        "missing-series reason must be named")


class TestGateDistanceFailOpen(unittest.TestCase):
    def test_raising_probe_leaves_results_identical_and_counts(self):
        asof, view = _retained_view()

        def boom(out, asof_, sleeve, view_):
            raise RuntimeError("injected recorder failure")

        probes = dict(gate_distance._PROBES)
        target = "aster_native_eth_sma200"
        probes[target] = boom
        results = {target: {"status": "ok", "intents": []},
                   "aster_breakout_ada_fullcash":
                       {"status": "ok", "intents": []}}
        before = json.dumps(results, sort_keys=True)
        with tempfile.TemporaryDirectory() as td:
            n, errors = gate_distance.record_cycle(
                td, asof, list(results.keys()), view, probes=probes)
        self.assertEqual(json.dumps(results, sort_keys=True), before,
                         "recorder failure altered the result set")
        self.assertEqual(errors, 1)
        self.assertGreaterEqual(n, 1,
                                "healthy probes must still record")

    def test_cycle_seam_is_fail_open_and_counts_on_roll(self):
        # Source assertion (the full Cycle harness is impractical
        # here): the seam must call the recorder inside a guard
        # and count failures on the roll, never raise them.
        src = open(os.path.join(DESK, "desk3", "cycle.py")).read()
        self.assertIn("gate_distance", src)
        self.assertIn('roll["gate_distance_errors"]', src)
        seam = src[src.index("gate_distance") - 200:
                   src.index("gate_distance") + 800]
        self.assertIn("except Exception", seam)


if __name__ == "__main__":
    unittest.main()
