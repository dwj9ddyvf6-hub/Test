"""A4-7 GAUGE-WIRING blockers (NO-PARTIALS DRIVE 2026-11-11):
pipeline.compute_gauges (which writes G1-G9, including G7
attention/narrative) had zero callers repo-wide: the daily lane
(run_daily.py) called live_all() then compile_state(), and
compile_state only READS the gauge CSVs. The gauges therefore
froze at their last manual regeneration (2026-10-31; G7
hand-regenerated 2026-11-10 under AUDIT4-G7-GAUGE-REGEN).

Cure: run_daily calls compute_gauges() between live_all() and
compile_state(). This blocker holds the wiring by source
assertion (the lane's full daily run is a live-data operation,
not a unit fixture).

Fail direction on the pre-cure tree: run_daily.py contains no
compute_gauges call.
"""
import os, re, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


class TestGaugeWiring(unittest.TestCase):

    def test_run_daily_calls_compute_gauges_between_collect_and_compile(self):
        src = open(os.path.join(ROOT, "run_daily.py")).read()
        live = src.index("live_all()")
        compute = src.index("compute_gauges()")
        compile_ = src.index("compile_state()")
        self.assertLess(live, compute)
        self.assertLess(compute, compile_)

    def test_compute_gauges_still_defines_all_nine_gauges(self):
        src = open(os.path.join(ROOT, "pipeline.py")).read()
        body = src[src.index("def compute_gauges():"):
                   src.index("def compile_state")]
        for g in ("g1_stated_sentiment", "g2_slow_climate",
                  "g3_positioning", "g4_fragility",
                  "g5_protection_cost", "g6_breadth_volatility",
                  "g7_attention_narrative", "g8_belief_markets",
                  "g9_crypto_mood"):
            self.assertIn(g, body)


if __name__ == "__main__":
    unittest.main()
