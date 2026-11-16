"""EXIT-REASON-FIELDS-20261115 regression blockers.

Defect (proven 2026-11-15 by the Vein 3 dig, pass2/VEIN3-DIG.md
structural find S1): zero of 1,526 dispatcher exit fills carried a
strategy reason (stop, target, horizon, signal flip, manual)
anywhere, in fills, per-sleeve journals, or broker orders. Sleeves
state their exit triggers only as prose ("{sid}_stop15",
"time_exit_40s", "aster_deadline_fixed16 held=16.0h"), so the WHY
of every fleet exit was ungradable, the same defect class as the
intent-log fields cured the same morning (INTENT-LOG-FIELDS-
20261115, desk commit 87a3956).

Cure: one classifier at the record funnels. desk3/dispatcher.py
classify_exit_reason maps an exit intent's own fields and reason
prose into the closed enum {stop, target, horizon, signal_flip,
manual, pooled_close, unknown_with_cause}, carrying the triggering
values the path knows; exit_reason_fields stamps exit_reason plus
exit_detail on (1) the cycle journal intent record (desk3/cycle.py,
at emission), (2) dispatcher intent_rejected rows for exits, and
(3) dispatcher fill rows for exit fills. Sweep-imported exit fills
(desk3/reconcile.py) carry no intent prose to classify, so they
stamp unknown_with_cause with the cause named. A path that cannot
classify stamps unknown_with_cause with its cause; omitting the
keys is the defect. Entry records carry neither key.

Fail direction: on the pre-cure writers the exit_reason key does
not exist on any of these rows, so every assertion below on it
fails. Proven on preserved pre-cure copies of desk3/dispatcher.py,
desk3/cycle.py and desk3/reconcile.py in /tmp (see
BUGLOG_2026-11-15.md, EXIT-REASON-FIELDS-20261115).
"""
import json
import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.cycle import Desk  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402
from desk3.journal import read_lines  # noqa: E402
from desk3.reconcile import sweep_unjournaled_fills  # noqa: E402

PRICE = 100.0
SLICES = {"sA": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


def _disp(tmp):
    broker = FakeBroker(prices={"QQQ": PRICE})
    return Dispatcher(tmp, broker, slices=dict(SLICES),
                      price_lookup=lambda s: PRICE)


class TestClassifyExitReason(unittest.TestCase):
    def _cls(self, reason, **kw):
        # Imported per call so that on the pre-cure tree the
        # record-shape tests below still run and fail on the
        # missing exit_reason key itself, instead of the whole
        # module dying on this import.
        from desk3.dispatcher import classify_exit_reason
        intent = {"kind": "exit", "reason": reason}
        intent.update(kw)
        return classify_exit_reason(intent, "sA")

    def test_lazarus_prose_classes(self):
        self.assertEqual(self._cls("sA_stop15")[0], "stop")
        self.assertEqual(self._cls("sA_target")[0], "target")
        self.assertEqual(self._cls("sA_target20")[0], "target")
        r, d = self._cls("sA_partial30_trail")
        self.assertEqual(r, "target")
        self.assertTrue(d["partial"])
        r, d = self._cls("sA_time_exit_40s")
        self.assertEqual(r, "horizon")
        self.assertEqual(d["horizon_sessions"], 40.0)

    def test_aster_prose_classes_and_values(self):
        r, d = self._cls("sA exit: aster_deadline_fixed16 held=16.0h")
        self.assertEqual(r, "horizon")
        self.assertEqual(d["held"], 16.0)
        self.assertEqual(d["held_unit"], "hours")
        r, d = self._cls(
            "sA exit: observed_quote_initial_2atr_stop "
            "stop=101.50 last=99.00")
        self.assertEqual(r, "stop")
        self.assertEqual(d["stop_price"], 101.5)
        self.assertAlmostEqual(d["stop_distance_frac"],
                               2.5 / 99.0)
        r, d = self._cls(
            "sA exit: official_PM_expiry_settle expiry=2026-11-20")
        self.assertEqual(r, "horizon")
        self.assertEqual(d["expiry"], "2026-11-20")
        r, d = self._cls("sA exit: time_1w age_sessions=7")
        self.assertEqual(r, "horizon")
        self.assertEqual(d["held"], 7.0)
        self.assertEqual(d["held_unit"], "sessions")

    def test_signal_flip_and_origin_classes(self):
        r, d = self._cls("sA exit: ma_cross_down flip")
        self.assertEqual(r, "signal_flip")
        self.assertEqual(d["signal"], "sA")
        self.assertEqual(self._cls("manual close by operator")[0],
                         "manual")
        self.assertEqual(self._cls("pooled lot closure")[0],
                         "pooled_close")

    def test_unknown_forms_carry_named_causes(self):
        r, d = self._cls("sA exit: donchian_exit_long")
        self.assertEqual(r, "unknown_with_cause")
        self.assertEqual(d["cause"], "unclassified_sleeve_reason")
        self.assertEqual(d["reason_text"],
                         "sA exit: donchian_exit_long")
        r, d = self._cls("")
        self.assertEqual(r, "unknown_with_cause")
        self.assertEqual(d["cause"], "no_reason_on_exit_intent")


class TestDispatcherExitRecords(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_rejected_exit_row_carries_reason(self):
        d = _disp(self.tmp)
        intent = {"intent_id": "erf1", "kind": "exit",
                  "symbol": "QQQ", "side": "sell", "qty": 0,
                  "order_type": "market",
                  "position_intent": "sell_to_close",
                  "reason": "sA_target"}
        r = d.process_intent(intent, "sA")
        self.assertEqual(r["status"], "rejected")
        rows = [x for x in read_lines(d.djournal)
                if x.get("event") == "intent_rejected"
                and x.get("intent_id") == "erf1"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["exit_reason"], "target")
        self.assertEqual(rows[0]["exit_detail"]["reason_text"],
                         "sA_target")

    def test_rejected_entry_row_carries_no_exit_keys(self):
        d = _disp(self.tmp)
        intent = {"intent_id": "erf2", "kind": "entry",
                  "symbol": "QQQ", "side": "sell", "qty": 0,
                  "order_type": "limit", "limit_price": 55.5,
                  "position_intent": "sell_to_open"}
        r = d.process_intent(intent, "sA")
        self.assertEqual(r["status"], "rejected")
        rows = [x for x in read_lines(d.djournal)
                if x.get("event") == "intent_rejected"
                and x.get("intent_id") == "erf2"]
        self.assertEqual(len(rows), 1)
        self.assertNotIn("exit_reason", rows[0])
        self.assertNotIn("exit_detail", rows[0])


class TestCycleExitRecords(unittest.TestCase):
    def _desk(self, tmp, intent):
        mod = os.path.join(tmp, "erf_sleeve.py")
        with open(mod, "w") as fh:
            fh.write(textwrap.dedent("""
                INTENT = %r
                def evaluate(view, ctx):
                    return [dict(INTENT)]
            """) % (intent,))
        broker = FakeBroker(prices={"TEST": PRICE})
        desk = Desk(tmp, broker=broker, sleeve_path=tmp)
        desk.add_producer("warm", lambda c: {"bars": {}}, ["bars"],
                          10 ** 9)
        desk.add_sleeve("erf", "erf_sleeve", ["bars"], 300, 1000.0)
        return desk

    def _journal_intent_rows(self, tmp, sid="erf"):
        path = os.path.join(tmp, "state", sid, "journal.jsonl")
        return [json.loads(l) for l in open(path)
                if json.loads(l).get("event") == "intent"]

    def test_filled_exit_stamps_journal_and_fill_rows(self):
        tmp = tempfile.mkdtemp()
        intent = {"intent_id": "erf-exit", "kind": "exit",
                  "symbol": "TEST", "side": "sell", "qty": 2,
                  "order_type": "market", "time_in_force": "day",
                  "position_intent": "sell_to_close",
                  "price_hint": PRICE, "reason": "erf_stop15"}
        desk = self._desk(tmp, intent)
        desk.run_cycle()
        rows = self._journal_intent_rows(tmp)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["result"], "filled")
        self.assertEqual(rows[0]["exit_reason"], "stop")
        self.assertEqual(rows[0]["exit_detail"]["reason_text"],
                         "erf_stop15")
        drows = [json.loads(l) for l in open(
            os.path.join(tmp, "state", "dispatcher.jsonl"))]
        fills = [r for r in drows if r.get("event") == "fill"
                 and r.get("intent_id") == "erf-exit"]
        self.assertEqual(len(fills), 1, drows)
        self.assertEqual(fills[0]["exit_reason"], "stop")
        self.assertEqual(fills[0]["exit_detail"]["reason_text"],
                         "erf_stop15")

    def test_filled_entry_stamps_no_exit_keys(self):
        tmp = tempfile.mkdtemp()
        intent = {"intent_id": "erf-entry", "kind": "entry",
                  "symbol": "TEST", "side": "buy", "qty": 3,
                  "order_type": "market", "time_in_force": "day",
                  "price_hint": PRICE}
        desk = self._desk(tmp, intent)
        desk.run_cycle()
        rows = self._journal_intent_rows(tmp)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["result"], "filled")
        self.assertNotIn("exit_reason", rows[0])
        drows = [json.loads(l) for l in open(
            os.path.join(tmp, "state", "dispatcher.jsonl"))]
        fills = [r for r in drows if r.get("event") == "fill"
                 and r.get("intent_id") == "erf-entry"]
        self.assertEqual(len(fills), 1, drows)
        self.assertNotIn("exit_reason", fills[0])


class _StubBroker:
    """Legacy-path broker double: no list_orders, so the sweep
    reads each submitted coid back individually."""

    def __init__(self, order):
        self._order = order

    def get_order_by_client_id(self, coid):
        return dict(self._order)

    def get_positions(self):
        return {}


class TestSweepImportedExitFill(unittest.TestCase):
    def test_imported_exit_fill_stamps_unknown_with_cause(self):
        tmp = tempfile.mkdtemp()
        sub = {"event": "order_submitted", "intent_id": "erf-sweep",
               "sleeve": "sA", "client_order_id": "erf-coid",
               "symbol": "TEST"}
        with open(os.path.join(tmp, "dispatcher.jsonl"), "w") as fh:
            fh.write(json.dumps(sub) + "\n")
        order = {"status": "filled", "filled_qty": 2,
                 "filled_avg_price": PRICE, "side": "sell",
                 "position_intent": "sell_to_close",
                 "symbol": "TEST", "id": "broker-1",
                 "filled_at": "2026-11-14T15:00:00+00:00"}
        res = sweep_unjournaled_fills(tmp, _StubBroker(order))
        self.assertEqual(res["imported_rows"], 1, res)
        rows = [json.loads(l) for l in open(
            os.path.join(tmp, "dispatcher.jsonl"))]
        fills = [r for r in rows if r.get("event") == "fill"]
        self.assertEqual(len(fills), 1, rows)
        self.assertEqual(fills[0]["exit_reason"],
                         "unknown_with_cause")
        self.assertEqual(
            fills[0]["exit_detail"]["cause"],
            "sweep_imported_fill_no_intent_record")


if __name__ == "__main__":
    unittest.main()
