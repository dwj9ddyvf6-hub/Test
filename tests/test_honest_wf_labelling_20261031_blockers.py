"""Blockers HONEST-WF-LABELLING-20261031: honest walk-forward labelling.

Audit (research_notes/quants-mechanisms-steal-20261031/AUDIT.md item 3):
the desk has no walk-forward engine at all, yet
desk3/forecast/__init__.py declared split names wf_1..wf_20 that
nothing produces: a walk-forward label with no engine behind it, no
slice-vs-refit distinction, no in-sample banner obligation, and no
documented honest-refit limits.

Quants.md form (extraction/WALKFORWARD-ENGINE.md): the default mode
slice_diagnostics is one full-sample run sliced by calendar and is
named as in-sample everywhere the number appears (per-fold warning,
per-run warning, summary banner "IN-SAMPLE SLICE DIAGNOSTICS (not
out-of-sample)", deflated Sharpe withheld in that mode); the honest
per_fold_refit mode is documented with its limits (refit is one
continuous IS+OOS run; purge is a scoring/fitting exclusion, not a
data exclusion; no post-test embargo exists).

What lands (risk BACKTEST; advisory forecast package only, no live
path imports it): no refit engine is fabricated. The wf_* names are
labelled diagnostic-only at the contract layer in
desk3/forecast/__init__.py: mode, in-sample flag, banner and limits
are stated once, every wf_* Score carries them (including in its
dumped JSON), a wf_* label that omits the banner is refused, and
deflation-style claims are withheld for slice diagnostics. Non-wf
splits keep their existing honest meaning (preservation).

These tests fail on the pre-change tree (no WF labelling anywhere)
and pass on the landed tree.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BANNER = "IN-SAMPLE SLICE DIAGNOSTICS (not out-of-sample)"


def _score(split, **kw):
    from desk3.forecast import Score
    base = dict(forecaster="f", target="t", cell="all", split=split,
                n_obs=400, n_dates=40)
    base.update(kw)
    return Score(**base)


class TestWfContractConstants(unittest.TestCase):
    def test_wf_splits_are_exactly_the_declared_names(self):
        from desk3.forecast import SPLITS, WF_SPLITS
        self.assertEqual(WF_SPLITS, tuple(f"wf_{k}" for k in range(1, 21)))
        for name in WF_SPLITS:
            self.assertIn(name, SPLITS)

    def test_only_mode_is_slice_diagnostics_and_refit_is_not_implemented(self):
        from desk3 import forecast as F
        self.assertEqual(F.WF_MODE, "slice_diagnostics")
        self.assertEqual(F.WF_BANNER, BANNER)
        self.assertEqual(F.WF_REFIT_MODE, "per_fold_refit")
        self.assertIs(F.WF_REFIT_IMPLEMENTED, False)

    def test_refit_limits_are_documented_with_the_three_limits(self):
        from desk3.forecast import WF_REFIT_LIMITS
        text = " ".join(WF_REFIT_LIMITS).lower()
        self.assertIn("not implemented", text)
        self.assertIn("one continuous", text)          # IS+OOS in one run
        self.assertIn("scoring/fitting exclusion", text)
        self.assertIn("not a data exclusion", text)
        self.assertIn("no post-test embargo", text)

    def test_split_helpers_distinguish_slice_from_refit_and_holdout(self):
        from desk3.forecast import (split_is_in_sample, split_label,
                                    split_mode)
        self.assertEqual(split_mode("wf_3"), "slice_diagnostics")
        self.assertTrue(split_is_in_sample("wf_3"))
        self.assertIn(BANNER, split_label("wf_3"))
        # preservation: existing splits keep their meaning
        self.assertEqual(split_mode("disc"), "discovery")
        self.assertTrue(split_is_in_sample("disc"))
        self.assertNotIn(BANNER, split_label("disc"))
        self.assertEqual(split_mode("hold"), "holdout")
        self.assertFalse(split_is_in_sample("hold"))
        self.assertFalse(split_is_in_sample("forward"))

    def test_deflation_withheld_for_slice_diagnostics_only(self):
        from desk3.forecast import deflation_allowed
        for name in ("wf_1", "wf_20"):
            self.assertIs(deflation_allowed(name), False, name)
        self.assertIs(deflation_allowed("hold"), True)
        self.assertIs(deflation_allowed("disc"), True)


class TestWfScoreLabelling(unittest.TestCase):
    def test_wf_score_carries_mode_banner_and_in_sample_flag(self):
        sc = _score("wf_7")
        self.assertEqual(sc.evaluation_mode, "slice_diagnostics")
        self.assertIs(sc.is_in_sample, True)
        self.assertEqual(sc.banner, BANNER)
        self.assertIn(BANNER, sc.evaluation_label)
        self.assertIn("wf_7", sc.evaluation_label)

    def test_wf_banner_survives_serialization(self):
        from desk3.forecast import dumps
        out = dumps(_score("wf_1"))
        self.assertIn(BANNER, out)
        self.assertIn("slice_diagnostics", out)

    def test_wf_label_omitting_the_banner_is_refused(self):
        from desk3.forecast import ContractError
        with self.assertRaises(ContractError):
            _score("wf_2", evaluation_label="wf_2 out-of-sample result")

    def test_non_wf_scores_are_not_bannered_as_slice_diagnostics(self):
        sc = _score("hold")
        self.assertEqual(sc.evaluation_mode, "holdout")
        self.assertIs(sc.is_in_sample, False)
        self.assertIsNone(sc.banner)
        self.assertNotIn(BANNER, sc.evaluation_label)

    def test_scorer_produced_wf_score_is_labelled(self):
        import numpy as np
        from desk3.forecast.score import score as run_score
        dates = np.array([f"2024-01-{d:02d}" for d in range(1, 29)] +
                         [f"2024-02-{d:02d}" for d in range(1, 13)])
        sc = run_score("f", "t", "all", "wf_5", dates,
                       np.linspace(-0.1, 0.1, 40), np.full(40, 20))
        self.assertIn(BANNER, sc.evaluation_label)
        self.assertIs(sc.is_in_sample, True)


if __name__ == "__main__":
    unittest.main()
