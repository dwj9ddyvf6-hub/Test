"""Blockers: vix_hedge sizing ruling R3-VIXHEDGE-20261025 (audit OPEN #4,
EDGE-B26) — MIDNA RULING under the owner's 2026-10-25 delegation.

The defect: the config slice ($10,000) gave the sleeve a 1%-of-slice
hedge budget of $100, but ONE contract of its own designed vehicle at
its own recorded design premium costs $110 (ADOPTED_IMPORT
entry_premium $1.10 x 100 contract multiplier) — floor(100/110) = 0
contracts, so the sleeve could never enter at its design premium.

The ruling: slice = smallest size fitting ONE contract at the
sleeve's own design risk = $1.10 x 100 / 0.01 = $11,000. The sleeve
code already quantizes (floor to whole contracts, 0 = no intent);
its 1% budget is itself the hard debit cap (qty x ask x 100 <= 1%
of slice for every ask). No strategy code changed.

Fail direction: on the pre-ruling tree the config row and the
adapter DEFAULT_EQUITY are 10000.0 and every slice/equity assertion
below fails (proven by temporary revert when the ruling landed).
Gate-wired: run_regression_blockers.sh discovers test_*_blockers.py.
"""
import json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sleeves.vix_hedge import (ADOPTED_IMPORT, HEDGE_RISK_FRACTION,
                               size_contracts)

DESIGN_PREMIUM = float(ADOPTED_IMPORT["entry_premium"])   # 1.10
MULTIPLIER = 100                                          # options contract
ONE_CONTRACT_RISK = DESIGN_PREMIUM * MULTIPLIER           # $110 max loss (debit)
RULED_SLICE = round(ONE_CONTRACT_RISK / HEDGE_RISK_FRACTION, 2)  # $11,000
OLD_SLICE = 10000.0


def _row():
    cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
    rows = [s for s in cfg["sleeves"] if s["id"] == "vix_hedge"]
    assert len(rows) == 1
    return rows[0]


def _bars(px, n=5):
    return [{"t": 1760000000.0 + k * 86400, "o": px, "h": px, "l": px,
             "c": px, "v": 1000} for k in range(n)]


def _view(ask, bid):
    occ = "VXX270115C00024000"
    return {"bars": {"VXX": _bars(20.0), "VIX": _bars(15.0, 30)},
            "options": {"chains": {"VXX": [{"symbol": occ, "strike": 24,
                                            "expiration": "2027-01-15"}]},
                        "quotes": {occ: {"bid": bid, "ask": ask}}},
            "positions": []}


def _ctx(equity):
    return {"sleeve_id": "vix_hedge", "session": "2026-10-23",
            "now": "2026-10-23T15:00:00", "equity": equity,
            "state_dir": "/tmp"}


class TestVixHedgeSizingRuling(unittest.TestCase):
    def test_config_slice_is_the_ruled_smallest_fitting_size(self):
        r = _row()
        self.assertEqual(r["slice"]["capital_usd"], RULED_SLICE)
        self.assertEqual(r["slice"]["cash_usd"], RULED_SLICE)

    def test_adapter_default_equity_matches_config_slice(self):
        # One source of truth: the adapter's no-ctx fallback equity is
        # the config slice, never a second divergent number.
        from adapters.vix_hedge import DEFAULT_EQUITY
        self.assertEqual(DEFAULT_EQUITY, _row()["slice"]["capital_usd"])

    def test_one_contract_fits_at_design_premium_only_at_ruled_slice(self):
        self.assertEqual(size_contracts(RULED_SLICE, DESIGN_PREMIUM), 1)
        self.assertEqual(size_contracts(OLD_SLICE, DESIGN_PREMIUM), 0)

    def test_entry_intent_fires_at_design_premium_at_ruled_slice(self):
        from adapters.vix_hedge import evaluate
        out = evaluate(_view(ask=1.10, bid=1.05), _ctx(RULED_SLICE))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 1)
        # ... and did NOT fire at the old slice (the EDGE-B26 defect).
        self.assertEqual(evaluate(_view(ask=1.10, bid=1.05),
                                  _ctx(OLD_SLICE)), [])

    def test_quantization_and_hard_debit_cap_for_all_asks(self):
        # Whole contracts only, never below one contract in an intent,
        # and total debit never above the 1%-of-slice budget ($110) —
        # the budget is the hard cap, at every ask.
        budget = RULED_SLICE * HEDGE_RISK_FRACTION
        for ask in (0.01, 0.05, 0.10, 0.50, 0.95, 1.10, 2.30, 5.00):
            qty = size_contracts(RULED_SLICE, ask)
            self.assertIsInstance(qty, int)
            self.assertGreaterEqual(qty, 0)
            self.assertLessEqual(qty * ask * MULTIPLIER, budget + 1e-9)
        # Above the cap a single contract is REFUSED, never oversized:
        from adapters.vix_hedge import evaluate
        self.assertEqual(evaluate(_view(ask=2.30, bid=2.20),
                                  _ctx(RULED_SLICE)), [])


if __name__ == "__main__":
    unittest.main()
