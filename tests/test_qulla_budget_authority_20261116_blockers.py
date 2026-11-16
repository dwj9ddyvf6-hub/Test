"""Blockers QULLA-BUDGET-AUTHORITY-20261116 (Mon 2026-11-16 total
audit, row 1): qullamaggie_paper's BUDGET_USD = 100,000 carried no
stated authority, against a $10,000 standard slice.

Provenance (four routes, run in order 2026-11-16):
(1) git: femto-lean d5829b9 (Wave D, 2026-10-15, Decision #119)
    introduced the constant extracted from aurelia_qulla_live.py;
    muse-desk-v3 f2e35ca (PORT batch 5, 2026-10-24) carried it
    byte-identical. No commit note fixes another value.
(2) source material: femto-lean ports/qullamaggie_paper.md records
    aurelia_common.BUDGETS["qullamaggie_paper"] = $100,000 — the
    carrier's own virtual-book budget config. The Qullamaggie author
    material (superthesis v3 + qualla_desk/config.json in
    dwj9ddyvf6-hub/quant-research-critical; adopted 2026-10-28
    playbook) fixes NO absolute budget — sizing is fractions of
    equity only.
(3) internet: canonical sizing summaries agree — percentages only.
(4) no derivation claimed; route (2) fixes the figure.

Cure: the authority is annotated at the source (sleeve docstring,
citing every source above) and pinned here. The figure and the
accept gate are unchanged; the gate is NOT the $10,000 slice, and
the behavioral pin below proves it (a $10,001 proposal is accepted
against the book budget; cumulative sent notional past $100,000 is
blocked_budget).

Fail direction: on the pre-cure tree the authority-annotation tests
fail (the annotation does not exist); the value/gate pins pass both
ways by design (they pin the ported figure the hunt confirmed).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sleeves import qullamaggie_paper as qp  # noqa: E402


def _prop(symbol="NVDA", qty=10, entry=100.0, stop=95.0):
    return {"symbol": symbol, "side": 1, "setup": "breakout",
            "quantity": qty, "entry": entry, "stop": stop}


class TestBudgetAuthority(unittest.TestCase):
    def test_figure_is_the_ported_carrier_budget(self):
        self.assertEqual(qp.BUDGET_USD, 100_000.0)

    def test_authority_annotated_at_the_source(self):
        doc = qp.__doc__ or ""
        self.assertIn("QULLA-BUDGET-AUTHORITY-20261116", doc)
        self.assertIn('aurelia_common.BUDGETS["qullamaggie_paper"]', doc)
        self.assertIn("d5829b9", doc)
        self.assertIn("f2e35ca", doc)
        # The annotation must state what the figure is NOT, on its face.
        self.assertIn("NOT a Qullamaggie sizing rule", doc)
        self.assertIn("NOT this", doc)

    def test_gate_is_the_book_budget_not_the_slice(self):
        # A single proposal above the $10,000 slice is accepted
        # against the $100,000 book budget (authority distinction,
        # proven behaviorally).
        ok, why, _ = qp.accept(_prop(qty=101, entry=100.0), "2026-11-16",
                               set(), 0.0)
        self.assertTrue(ok, why)
        # Cumulative sent notional past $100,000 is blocked_budget.
        ok, why, _ = qp.accept(_prop(qty=500, entry=100.0), "2026-11-16",
                               set(), 60_000.0)
        self.assertFalse(ok)
        self.assertEqual(why, "blocked_budget")


if __name__ == "__main__":
    unittest.main()
