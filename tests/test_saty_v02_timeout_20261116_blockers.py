"""SATY-V02-TIMEOUT-20261116 blockers: saty_gpt_v02 carries a
per-sleeve evaluation timeout override in desk3/run_live.py.

What broke: saty_gpt_v02's live evaluation cost is ~33s (the EFF-1
pool record, the desk's slowest; BUGLOG_2026-11-16.md
CENSUS-TAXONOMY-20261116 open remainder) against the evaluation
pool's 30.0s default budget, and the sleeve declared timeout_s
null, so it wedged intermittently (journal eval rows: wedged at
2026-11-16T11:27:01Z and 2026-11-16T11:44:05Z, ok unaided at
12:28Z; 12 wedged rows in its journal overall). Cause of the cost
growth: desk3/warm.py CR-6 (CR6-V03-WARMUP-20261114) widened the
shared SPY 5Min warm window 60 -> 300 days for saty_gpt_v03,
growing v02's input ~5x (39,946 SPY 5Min bars on the
2026-11-16T13:46Z live snapshot); the desk3/saty_v02_agg.py
aggregation cache is process-local and is defeated by snapshot
hash churn, so the cold path runs in the live pool.

Sizing derivation (measured 2026-11-16, this landing): the live
pool cost is ~33s; a timed fixture evaluation through a fresh
desk3.worker on the 2026-11-16T13:46Z live snapshot measured
6.46s / 6.56s cold and 4.26s / 4.50s on warm repeat in isolation
-- the ~5x gap to the live figure is pool CPU contention, and the
budget must hold the LIVE cost, whose wedge verdicts
(timeout>30.0s) are the system of record. The override is
120.0s: ~3.6x the 33s live cost, ~18x the isolated cold cost,
and 5x tighter than the D20 pair's 600.0s precedent in the same
build_desk call. saty_gpt_v03 was measured on the same snapshot
at 0.79s / 0.81s isolated and has zero wedged rows in 2,716
journal eval rows, so it is NOT given an override.

Fail direction: on the pre-cure tree build_desk serves
saty_gpt_v02 with timeout_s None, so the override tests fail;
the default-budget, D20-precedent and v03-left-alone tests pass
on both trees by design (they pin what this cure must not move).
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OVERRIDE_S = 120.0
LIVE_COST_S = 33.0


class TestSatyV02TimeoutOverride(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from desk3.run_live import build_desk
        cls.desk, cls.rows = build_desk(ROOT, dispatch=False, env={})

    def test_v02_carries_the_override(self):
        self.assertEqual(
            self.desk.sleeves["saty_gpt_v02"]["timeout_s"], OVERRIDE_S)

    def test_override_value_derivation(self):
        v = self.desk.sleeves["saty_gpt_v02"]["timeout_s"]
        self.assertIsNotNone(v)
        # strictly above the default budget it kept wedging against
        self.assertGreater(v, 30.0)
        # at least 3x the measured ~33s live cost (headroom for the
        # contention tail that produced the intermittent wedges)
        self.assertGreaterEqual(v, 3.0 * LIVE_COST_S)
        # bounded, and tighter than the D20 pair's 600.0s precedent
        self.assertLess(v, 600.0)

    def test_v03_left_alone_on_its_measurement(self):
        # measured 0.79s/0.81s isolated, zero wedged journal rows:
        # no override is landed for v03 by this cure
        self.assertIsNone(
            self.desk.sleeves["saty_gpt_v03"]["timeout_s"])

    def test_d20_precedent_unchanged(self):
        for sid in ("aster_tensor_d20_pv", "aster_tensor_d20_tensor"):
            self.assertEqual(self.desk.sleeves[sid]["timeout_s"], 600.0)

    def test_pool_default_and_other_sleeves_unchanged(self):
        self.assertEqual(self.desk.timeout_s, 30.0)
        self.assertIsNone(self.desk.sleeves["saty_sol"]["timeout_s"])


if __name__ == "__main__":
    unittest.main()
