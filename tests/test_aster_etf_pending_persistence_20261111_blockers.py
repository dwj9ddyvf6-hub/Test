"""ASTER-ETF PENDING-TARGET PERSISTENCE blockers (CR-1, 2026-11-11).

Diagnosis (DIAGNOSIS.md S1 / CR-1): eight flat-allocation sleeves of
the aster_etf family sat flat for 14 sessions with zero orders. The
weight-lag mechanism (WEIGHT-LAG-ACTIVE-20261031, by design) acts on
the PREVIOUS evaluation's pending targets, but the pending targets
lived only in process memory (_PENDING_TARGETS): the single 09:35 ET
in-window evaluation stored them and emitted nothing, and any runner
restart before the next evaluation restarted the lag from zero. For
BUY_HOLD sleeves it was worse: the same-session catch-up path was
MONTHLY-only, so a flat BUY_HOLD sleeve's second evaluation at 09:40
was gated out entirely.

Cure pinned here: pending targets persist to the sleeve's state
directory (weight_lag_pending.json) and are reloaded after a restart,
and the same-session catch-up treatment extends to flat BUY_HOLD
initial allocations. No target, weight, sizing or policy changes.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ET = ZoneInfo("America/New_York")


def _view(now):
    return {"now": now,
            "bars": {"QLD|1Day": [{"c": 100.0}]},
            "positions": []}


def _ctx(state_dir):
    return {"state_dir": state_dir,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"account_value": 10000.0}}


def _simulate_restart(sleeve_id):
    """A runner restart, scoped to this sleeve: the process memory
    (the module's pending dict) is gone; only the state directory
    survives. Scoped deliberately — a full module reload would wipe
    every other suite's primed lag state in a shared gate process."""
    import desk3.aster_etf as ae
    ae._PENDING_TARGETS.pop(sleeve_id, None)
    return ae


class TestPendingPersistence(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_buy_hold_allocation_survives_restart_into_catchup(self):
        import desk3.aster_etf as ae
        ae._PENDING_TARGETS.pop("aster_etf_qld_buy_hold", None)
        sd = os.path.join(self._root(), "aster_etf_qld_buy_hold")
        t1 = datetime(2026, 11, 11, 9, 35, tzinfo=ET)
        out1 = ae.evaluate("aster_etf_qld_buy_hold", _view(t1), _ctx(sd))
        self.assertEqual(out1, [])  # weight lag: first eval emits none
        self.assertTrue(os.path.exists(
            os.path.join(sd, "weight_lag_pending.json")),
            "pending targets were not persisted")
        ae = _simulate_restart("aster_etf_qld_buy_hold")
        t2 = datetime(2026, 11, 11, 9, 40, tzinfo=ET)
        out2 = ae.evaluate("aster_etf_qld_buy_hold", _view(t2), _ctx(sd))
        self.assertEqual(len(out2), 1,
                         "allocation did not survive the restart")
        self.assertEqual(out2[0]["symbol"], "QLD")
        self.assertEqual(out2[0]["side"], "buy")
        self.assertEqual(out2[0]["qty"], 100)

    def test_monthly_allocation_survives_restart_inside_window(self):
        import desk3.aster_etf as ae
        ae._PENDING_TARGETS.pop("aster_etf_qld_monthly", None)
        sd = os.path.join(self._root(), "aster_etf_qld_monthly")
        t1 = datetime(2026, 11, 11, 9, 35, tzinfo=ET)
        self.assertEqual(
            ae.evaluate("aster_etf_qld_monthly", _view(t1), _ctx(sd)), [])
        ae = _simulate_restart("aster_etf_qld_monthly")
        t2 = datetime(2026, 11, 11, 9, 36, tzinfo=ET)
        out = ae.evaluate("aster_etf_qld_monthly", _view(t2), _ctx(sd))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "QLD")
        self.assertEqual(out[0]["qty"], 100)


if __name__ == "__main__":
    unittest.main()
