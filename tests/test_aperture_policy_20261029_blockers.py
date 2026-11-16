"""APERTURE-POLICY-20261029 blockers (desk side): DEEP-PASS 3.2
item 1. The desk candidate and card path qualifies candidates
through desk3/aperture_policy.py: ordinal deterministic stages,
fail closed shadow default, explicit authority, out of hours
degradation, structure bounded target, per name exclusion
reasons ledgered, and trigger freshness from trigger age
against registry TTLs. Desk.run_cycle surfaces the result in
roll["aperture_policy"] when a producer supplies candidates.

Fail direction: desk3/aperture_policy.py does not exist on the
pre-cure tree, so these fail pre-cure at import.
"""
import os, sys, tempfile, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 28, 14, 0, 0, tzinfo=timezone.utc)


def _good(**over):
    cand = {"symbol": "AAA", "price": 100.0, "support": 99.0,
            "atr": 2.0, "resistance": 110.0, "daily_bar_count": 120,
            "intraday_bar_count": 10,
            "median_dollar_volume": 20_000_000, "session": "regular",
            "trigger": {"family": "structural_hold",
                        "state": "CONFIRMED", "fired_bar": 10}}
    cand.update(over)
    return cand


class AperturePolicyTests(unittest.TestCase):
    def test_shadow_default_and_authority(self):
        from desk3.aperture_policy import classify_candidate
        out = classify_candidate(_good(), current_bar=11)
        self.assertTrue(out["shadow_only"])
        self.assertFalse(out["execution_eligible"])
        out2 = classify_candidate(
            _good(shadow_only=False, authority="ORDER_AUTHORIZED"),
            current_bar=11)
        self.assertTrue(out2["execution_eligible"])

    def test_ttl_freshness_not_window_flag(self):
        from desk3.aperture_policy import trigger_freshness
        trig = {"family": "structural_hold", "state": "CONFIRMED",
                "fired_bar": 1, "in_window": True}
        self.assertEqual(
            trigger_freshness(trig, current_bar=50)["state"],
            "expired")

    def test_exclusions_ledgered_in_batch(self):
        from desk3.aperture_policy import classify_candidates
        out = classify_candidates(
            [_good(), _good(symbol="BBB", daily_bar_count=2)],
            current_bar=11)
        self.assertEqual(out["counts"]["total"], 2)
        self.assertEqual(len(out["exclusions"]), 1)
        self.assertEqual(out["exclusions"][0]["symbol"], "BBB")

    def test_cycle_roll_carries_policy_result(self):
        from desk3.cycle import Desk
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            desk = Desk(td)
            desk.add_producer(
                "cands",
                lambda ctx: {"candidates": [
                    _good(), _good(symbol="BBB", daily_bar_count=2)]},
                ["candidates"], 60)
            roll = desk.run_cycle(now=NOW)
            desk.close()
        self.assertIn("aperture_policy", roll)
        self.assertEqual(roll["aperture_policy"]["counts"]["total"], 2)
        self.assertEqual(
            len(roll["aperture_policy"]["exclusions"]), 1)


if __name__ == "__main__":
    unittest.main()
