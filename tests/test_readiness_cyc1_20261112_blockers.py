"""READINESS-CYC1-20261112 blockers (DEFECT-HUNT CYC-1, Critical).

Defect: any exception inside the cycle's reconcile block replaced
the report with an empty one and cleared self._reconcile_report, so
the dispatcher was built with no halted sleeves and no cash halt and
new entries dispatched as if reconcile had passed; the roll's
top-level status stayed "ok"; and neither health.json nor
terminal.json carried the reconcile status, so the failure existed
only in the unpersisted in-memory roll.

Cure: on reconcile exception the cycle fails CLOSED for entries (a
desk-wide cash halt for that cycle; exits still pass), the prior
cycle's sleeve halts are kept, and the reconcile status rides
health.json and terminal.json.

Fail direction: proven on a worktree at the pre-cure HEAD — the
failing-broker cycle dispatches the entry (submit_count 1), the
report carries no cash halt, and the surfaces carry no reconcile
key.
"""
import json
import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.cycle import Desk
from desk3.broker import FakeBroker


class RaisingBroker(FakeBroker):
    def get_positions(self):
        raise RuntimeError("positions read down")


def _desk(tmp, broker):
    mod = os.path.join(tmp, "buyer_sleeve.py")
    with open(mod, "w") as fh:
        fh.write(textwrap.dedent("""
            def evaluate(view, ctx):
                return [{"intent_id": "buyer-1", "kind": "entry",
                         "symbol": "TEST", "side": "buy", "qty": 1,
                         "order_type": "market",
                         "time_in_force": "day", "price_hint": 10.0}]
        """))
    desk = Desk(tmp, broker=broker, sleeve_path=tmp)
    desk.add_producer("warm", lambda c: {"bars": {}}, ["bars"], 10 ** 9)
    desk.add_sleeve("buyer", "buyer_sleeve", ["bars"], 300, 10000.0)
    desk.reconcile_enabled = True
    return desk


class TestReconcileFailureFailsClosed(unittest.TestCase):
    def test_reconcile_exception_halts_entries_and_surfaces(self):
        tmp = tempfile.mkdtemp()
        broker = RaisingBroker(prices={"TEST": 10.0})
        desk = _desk(tmp, broker)
        roll = desk.run_cycle()
        # No entry reached the broker this cycle.
        self.assertEqual(broker.submit_count, 0)
        # The roll names the failure as a halt, not as a pass.
        rec = roll.get("reconcile") or {}
        self.assertTrue(str(rec.get("status", "")).startswith("error:"),
                        rec)
        self.assertTrue(rec.get("cash_halt"), rec)
        # Both persisted surfaces carry the reconcile status.
        for name in ("health.json", "terminal.json"):
            payload = json.load(open(os.path.join(tmp, "state", name)))
            self.assertIn("reconcile", payload, name)
            self.assertTrue(
                str(payload["reconcile"].get("status", "")).startswith(
                    "error:"), (name, payload["reconcile"]))
            self.assertTrue(payload["reconcile"]["cash_halt"],
                            (name, payload["reconcile"]))

    def test_prior_cycle_halts_are_kept(self):
        tmp = tempfile.mkdtemp()
        broker = RaisingBroker(prices={"TEST": 10.0})
        desk = _desk(tmp, broker)
        desk._reconcile_report = {
            "status": "DISCREPANCY", "discrepancies": [],
            "halted_sleeves": ["buyer"], "cash_halt": False}
        roll = desk.run_cycle()
        rec = roll.get("reconcile") or {}
        self.assertIn("buyer", rec.get("halted_sleeves") or [], rec)
        self.assertTrue(rec.get("cash_halt"), rec)
        self.assertEqual(broker.submit_count, 0)

    def test_healthy_reconcile_still_dispatches(self):
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"TEST": 10.0})
        desk = _desk(tmp, broker)
        roll = desk.run_cycle()
        self.assertEqual(broker.submit_count, 1)
        for name in ("health.json", "terminal.json"):
            payload = json.load(open(os.path.join(tmp, "state", name)))
            self.assertIn("reconcile", payload, name)
            self.assertFalse(payload["reconcile"]["cash_halt"],
                             (name, payload["reconcile"]))


if __name__ == "__main__":
    unittest.main()
