"""PARKED-ROSTER-Q07-20261116 blockers (2026-11-16).

Defect: desk3/lazarus_q07.py SPECS carried parked=True for the four
swing-SM lanes below while the roster of record,
config/sleeves.json, carries parked=False for all four (unparked
2026-11-14 under the owner's all-sleeves-firing order; each config
row stamps unparked_on 2026-11-14 with that authority).
evaluate_sleeve returns right after exits at the parked check, so
the four lanes could never enter while state/health.json read them
FED ok. A FIX-F1-Q07-20261115 comment in the same file claimed the
four are not in the config roster at all; that is false against
config, which carries all four rows.

Precedent (the shape this cure mirrors): FIX-F1-Q07-20261115 cured
the same defect class for the four swing-ML lanes in this same
engine by correcting the SPECS parked values to parked=False so
they match the roster; it did not derive SPECS from config.

Fail direction: on the pre-cure tree the agreement test fails with
exactly the four named mismatches, the named-sleeves test fails,
and the entry test emits no entry; the exit guard passes on both
trees (parked lanes always managed exits).
"""
import json
import os
import sys
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FOUR = ("s_q07w_s52_sm_cheap5_wcov", "s_q07w_s52_sm_deep70_wcov",
        "s_q07w_s78_sm_cheap5_wcov", "s_q07w_s78_sm_deep70_wcov")

TODAY = date(2026, 10, 23)


def _config_parked():
    with open(os.path.join(ROOT, "config", "sleeves.json")) as fh:
        cfg = json.load(fh)
    return {row["id"]: row.get("parked") for row in cfg["sleeves"]}


class TestParkedRosterAgreement(unittest.TestCase):
    def test_every_served_sleeve_parked_agrees_with_config(self):
        from desk3.lazarus_q07 import SPECS
        config = _config_parked()
        mismatches = []
        for sid, spec in sorted(SPECS.items()):
            self.assertIn(sid, config, sid)
            if spec["parked"] != config[sid]:
                mismatches.append(
                    f"{sid}: SPECS parked={spec['parked']} "
                    f"config parked={config[sid]}")
        self.assertEqual(mismatches, [])

    def test_four_named_sleeves_unparked_in_config_and_specs(self):
        from desk3.lazarus_q07 import SPECS
        config = _config_parked()
        for sid in FOUR:
            self.assertIn(sid, config, sid)
            self.assertFalse(config[sid], sid)
            self.assertIn(sid, SPECS, sid)
            self.assertFalse(SPECS[sid]["parked"], sid)


class TestNamedLaneEntryAndExit(unittest.TestCase):
    def _view(self, positions):
        days = [TODAY - timedelta(days=i) for i in range(29, -1, -1)]
        bars = [{"date": d.isoformat(), "c": 4.0} for d in days]
        fire = {"symbol": "TEST", "family": "swing", "band": "small",
                "signal_date": "2026-10-23", "price": 4.0,
                "tags": {"wiki_cov": True}}
        return {"bars": {"QQQ": [{"date": "2026-10-22", "c": 101.0},
                                 {"date": "2026-10-23", "c": 100.0}],
                         "TEST": bars},
                "positions": positions, "fires": [fire],
                "extra": {"q07_exp_journal": {"records": []}}}

    def test_named_cheap5_lane_enters_on_qualifying_fire(self):
        from desk3.lazarus_q07 import evaluate_sleeve
        sid = "s_q07w_s52_sm_cheap5_wcov"
        out = evaluate_sleeve(sid, self._view([]),
                              {"session": "2026-10-23",
                               "now": "2026-10-23"})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_named_lane_exit_still_fires(self):
        from desk3.lazarus_q07 import evaluate_sleeve
        sid = "s_q07w_s52_sm_cheap5_wcov"
        positions = [{"symbol": "TEST", "qty": 10, "avg_price": 10.0,
                      "current_price": 4.0, "opened_at": "2026-10-01"}]
        out = evaluate_sleeve(sid, self._view(positions),
                              {"session": "2026-10-23",
                               "now": "2026-10-23"})
        self.assertEqual(len([i for i in out if i["kind"] == "exit"]), 1)


if __name__ == "__main__":
    unittest.main()
