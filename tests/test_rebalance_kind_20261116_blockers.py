"""REBALANCE-KIND-20261116 blockers: a partial reduction decided by a
monthly aster ETF sleeve is a partial exit in the door's vocabulary.

Defect: desk3/aster_etf.py (base path) and desk3/aster_batch8.py
(_etf) emitted kind="rebalance" for a partial reduction (target > 0
but below held). desk3/models.py validate_intent admits only
entry/exit and raises bad_kind; the dispatcher journal carries 5
live intent_rejected/bad_kind rows dated 2026-11-13
(aster_etf_core25_m150 / aster_etf_core25_c098), so decided
reductions silently never executed. Cure: the kind is "exit"
(position_intent sell_to_close, qty = held - target, unchanged);
the partial case stays named rebalance in the reason prose, the
form the CONV21-INVERT-20261116 inverted branch already used.

Fail direction: on the pre-cure tree both drives below emit
kind="rebalance" and validate_intent raises bad_kind.
"""
import importlib
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ET = ZoneInfo("America/New_York")


def _fb(px, n=130, start=None):
    return [{"t": f"2026-01-{(i % 28) + 1:02d}", "o": px, "h": px,
             "l": px, "c": (start if (start is not None and i == n - 127)
                           else px), "v": 1000} for i in range(n)]


def _basket(leader="XLK"):
    syms = ["QQQ", "SPY", "SMH", "XLB", "XLC", "XLE", "XLF", "XLI",
            "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
    m = {s: _fb(100.0) for s in syms}
    if leader:
        m[leader] = _fb(120.0, start=100.0)
    return m


class TestBatch8PartialReduction(unittest.TestCase):
    def test_partial_reduction_is_an_exit_the_door_admits(self):
        from desk3.models import validate_intent
        mod = importlib.import_module("adapters3.aster_etf_core25_m150")
        ctx = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
               "slice": {"capital_usd": 10000.0}}
        # QQQ target for CORE25 m150 on this basket is 112 (the
        # family blocker's own entry case); hold 150 from September
        # so the October rebalance decides a 38-share reduction.
        positions = [{"symbol": "QQQ", "qty": 150, "avg_price": 100.0,
                      "opened_at": "2026-09-15T14:00:00Z"}]
        view = {"now": "2026-10-01T09:36:00", "bars": _basket(),
                "positions": positions, "quotes": {}, "extra": {}}
        out = mod.evaluate(view, dict(ctx))
        sells = [o for o in out if o["symbol"] == "QQQ"
                 and o["side"] == "sell"]
        self.assertEqual(len(sells), 1)
        o = sells[0]
        self.assertEqual(o["kind"], "exit")
        self.assertEqual(o["qty"], 38)
        self.assertEqual(o["position_intent"], "sell_to_close")
        self.assertIn("rebalance", o["reason"])
        for intent in out:
            validate_intent(intent)  # the door admits every emission


class TestAsterEtfPartialReduction(unittest.TestCase):
    def setUp(self):
        import desk3.aster_etf as ae
        self.ae = ae
        ae._PENDING_TARGETS.pop("aster_etf_qld_monthly", None)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.sd = tmp

    def _ctx(self):
        return {"state_dir": self.sd,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "extra": {"account_value": 10000.0}}

    def test_partial_reduction_is_an_exit_the_door_admits(self):
        from desk3.models import validate_intent
        sid = "aster_etf_qld_monthly"
        bars = {"QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out1 = self.ae.evaluate(
            sid, {"now": t1, "bars": bars, "positions": []}, self._ctx())
        self.assertEqual(out1, [], "weight lag: first eval emits none")
        # Staged target is 100 (gross 1.0 x $10,000 / $100); hold 140
        # so the diff decides a 40-share partial reduction.
        positions = [{"symbol": "QLD", "qty": 140, "avg_price": 100.0}]
        out = self.ae.evaluate(
            sid, {"now": t2, "bars": bars, "positions": positions},
            self._ctx())
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual(o["kind"], "exit")
        self.assertEqual(o["side"], "sell")
        self.assertEqual(o["qty"], 40)
        self.assertEqual(o["position_intent"], "sell_to_close")
        self.assertIn("rebalance", o["reason"])
        validate_intent(o)  # the door admits it


class TestNoRebalanceKindAnywhere(unittest.TestCase):
    def test_emission_sources_carry_no_rebalance_kind(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        for rel in ("desk3/aster_etf.py", "desk3/aster_batch8.py"):
            src = open(os.path.join(root, rel)).read()
            self.assertNotIn('kind="exit" if tgt==0 else "rebalance"',
                             src)


if __name__ == "__main__":
    unittest.main()
