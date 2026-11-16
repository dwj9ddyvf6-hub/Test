"""CONV21-INVERT-20261116 blockers: the QLD monthly inversion's
inverted evaluator (Conversion Register CONV-21).

Pre-cure state (GOING-LIVE-2026-11-15, CONV-21 BLOCKED): desk3/
aster_etf.py SPECS carried only policy, freq, gross and long weights;
no direction or side parameter existed and the emission diff could
only sell what a long book held, so the inverted form (negative
targets, sell-to-open entries, buy-to-cover covers, DH2 borrow priced
in-path) was inexpressible. Cure pinned here: two direction=-1 SPECS
mirroring the base sleeves' policy/freq/gross/weights, a sign-aware
diff for inverted specs only, a borrow record on every inverted
sell_to_open intent at the DH2 snapshot fees, the register's
falsifier and kill rule carried byte-identical in the engine and in
the both-sides FWD_GRADE arm (config/conversion_shadow_20261115.json)
that grades the base sleeves' next 10 forward fires.

Door proof pinned here too: the emitted sell_to_open / buy_to_close
intents pass desk3.models.validate_intent (the dispatcher's own
validator) — equity sell_to_open is an entry on this desk, facing the
slice buying-power gate like any entry.
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
INV1 = "aster_etf_qld_monthly_inv"
INV2 = "aster_etf_qqq_qld_monthly_inv"
BASE1 = "aster_etf_qld_monthly"

FALSIFIER = ("The inversion dies if forward fwd5 excess of the long "
             "(base) side is not negative over the next 10 forward "
             "fires; symmetrically, the inverted form promotes only "
             "if its own forward fwd5 excess is positive over the "
             "same fires.")
KILL_RULE = ("Base-side forward fwd5 excess not negative over those "
             "fires kills the inversion.")


def _view(now, bars, positions):
    return {"now": now, "bars": bars, "positions": positions}


def _ctx(state_dir):
    return {"state_dir": state_dir,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"account_value": 10000.0}}


class TestConv21Inverted(unittest.TestCase):
    def setUp(self):
        import desk3.aster_etf as ae
        self.ae = ae
        for sid in (INV1, INV2, BASE1):
            ae._PENDING_TARGETS.pop(sid, None)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.sd = tmp

    def _two_evals(self, sid, view1, view2):
        out1 = self.ae.evaluate(sid, view1, _ctx(self.sd))
        self.assertEqual(out1, [], "weight lag: first eval emits none")
        return self.ae.evaluate(sid, view2, _ctx(self.sd))

    def test_specs_mirror_base_with_direction(self):
        ae = self.ae
        for inv, base in ((INV1, "aster_etf_qld_monthly"),
                          (INV2, "aster_etf_qqq_qld_monthly")):
            s, b = ae.SPECS[inv], ae.SPECS[base]
            self.assertEqual(s["direction"], -1)
            for k in ("policy", "freq", "gross", "weights"):
                self.assertEqual(s[k], b[k], (inv, k))
            self.assertNotIn("direction", b,
                             "base spec gained a direction key")

    def test_falsifier_byte_identical(self):
        self.assertEqual(self.ae.CONV21_FALSIFIER, FALSIFIER)
        self.assertEqual(self.ae.CONV21_KILL_RULE, KILL_RULE)

    def test_open_short_qld_sell_to_open_with_borrow(self):
        bars = {"QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(INV1, _view(t1, bars, []),
                              _view(t2, bars, []))
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual(o["symbol"], "QLD")
        self.assertEqual(o["side"], "sell")
        self.assertEqual(o["qty"], 100)
        self.assertEqual(o["kind"], "entry")
        self.assertEqual(o["position_intent"], "sell_to_open")
        self.assertIn("borrow", o)
        self.assertEqual(o["borrow"]["fee_rate_pct_per_year"], 0.7690)
        self.assertEqual(o["borrow"]["source"],
                         "DH2-BORROW-SERIES-2026-11-15")
        self.assertAlmostEqual(o["borrow"]["borrow_cost_per_day_usd"],
                               round(100 * 100.0 * 0.00769 / 365.0, 4))
        from desk3.models import validate_intent
        validate_intent(o)  # the door admits the inverted entry

    def test_open_short_qqq_qld_pair(self):
        bars = {"QQQ|1Day": [{"c": 200.0}], "QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(INV2, _view(t1, bars, []),
                              _view(t2, bars, []))
        by = {o["symbol"]: o for o in out}
        self.assertEqual(set(by), {"QQQ", "QLD"})
        self.assertEqual(by["QLD"]["qty"], 50)
        self.assertEqual(by["QQQ"]["qty"], 25)
        for o in out:
            self.assertEqual(o["position_intent"], "sell_to_open")
        self.assertEqual(by["QQQ"]["borrow"]["fee_rate_pct_per_year"],
                         0.26)
        self.assertAlmostEqual(
            by["QQQ"]["borrow"]["borrow_cost_per_day_usd"],
            round(25 * 200.0 * 0.0026 / 365.0, 4))

    def test_cover_is_buy_to_close(self):
        bars = {"QLD|1Day": [{"c": 200.0}]}
        pos = [{"symbol": "QLD", "qty": -100,
                "entry_date": "2026-11-10", "avg_price": 100.0}]
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(INV1, _view(t1, bars, pos),
                              _view(t2, bars, pos))
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual(o["side"], "buy")
        self.assertEqual(o["qty"], 50)  # target -50 vs held -100
        # Door vocabulary is entry/exit only (bad_kind): a partial
        # cover is kind exit, named rebalance in its reason prose.
        self.assertEqual(o["kind"], "exit")
        self.assertIn("rebalance", o["reason"])
        self.assertEqual(o["position_intent"], "buy_to_close")
        self.assertNotIn("borrow", o)
        from desk3.models import validate_intent
        validate_intent(o)

    def test_flip_long_to_short_splits_close_and_open(self):
        bars = {"QLD|1Day": [{"c": 100.0}]}
        pos = [{"symbol": "QLD", "qty": 30,
                "entry_date": "2026-11-10", "avg_price": 90.0}]
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(INV1, _view(t1, bars, pos),
                              _view(t2, bars, pos))
        self.assertEqual(len(out), 2)
        close_o, open_o = out
        self.assertEqual(close_o["position_intent"], "sell_to_close")
        self.assertEqual(close_o["qty"], 30)
        self.assertEqual(close_o["kind"], "exit")
        self.assertEqual(open_o["position_intent"], "sell_to_open")
        # +30 long to -100 short is a 130 sell: 30 close + 100 open.
        self.assertEqual(open_o["qty"], 100)
        self.assertIn("borrow", open_o)

    def test_base_sleeve_unchanged_long_form(self):
        bars = {"QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(BASE1, _view(t1, bars, []),
                              _view(t2, bars, []))
        self.assertEqual(len(out), 1)
        o = out[0]
        self.assertEqual(o["side"], "buy")
        self.assertEqual(o["qty"], 100)
        self.assertEqual(o["position_intent"], "buy_to_open")
        self.assertNotIn("borrow", o)

    def test_adapters_delegate(self):
        import adapters3.aster_etf_qld_monthly_inv as a1
        import adapters3.aster_etf_qqq_qld_monthly_inv as a2
        self.assertEqual(a1.SLEEVE_ID, INV1)
        self.assertEqual(a2.SLEEVE_ID, INV2)
        bars = {"QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        self.assertEqual(a1.evaluate(_view(t1, bars, []),
                                     _ctx(self.sd)), [])

    def test_inverted_entry_submits_through_dispatcher(self):
        # End-to-end door proof on the final tree: the inverted
        # evaluator's sell_to_open intent is submitted by the
        # Dispatcher to the broker double, not rejected at any gate
        # (validate_intent, preflight, slice buying-power).
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        bars = {"QLD|1Day": [{"c": 100.0}]}
        t1 = datetime(2026, 12, 1, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 12, 1, 9, 40, tzinfo=ET)
        out = self._two_evals(INV1, _view(t1, bars, []),
                              _view(t2, bars, []))
        self.assertEqual(len(out), 1)
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        broker = FakeBroker(prices={"QLD": 100.0})
        disp = Dispatcher(root, broker, slices={
            INV1: {"capital_usd": 10000.0, "cash_usd": 10000.0}})
        res = disp.process_intent(dict(out[0]), INV1)
        self.assertEqual(res.get("status"), "filled", res)
        self.assertEqual(broker.submit_count, 1)
        order = list(broker.orders.values())[0]
        self.assertEqual(order["position_intent"], "sell_to_open")
        self.assertEqual(order["side"], "sell")
        self.assertEqual(order["qty"], 100)

    def test_grader_arm_registered_byte_identical(self):
        p = os.path.join(os.path.dirname(__file__), "..", "config",
                         "conversion_shadow_20261115.json")
        cfg = json.load(open(p))
        arms = [a for a in cfg["arms"] if a.get("conv") == "CONV-21"]
        self.assertEqual(len(arms), 1)
        arm = arms[0]
        self.assertEqual(arm["kind"], "FWD_GRADE")
        self.assertTrue(arm["both_sides"])
        self.assertEqual(arm["parents"],
                         ["aster_etf_qld_monthly",
                          "aster_etf_qqq_qld_monthly"])
        self.assertEqual(arm["grade_n"], 10)
        self.assertEqual(arm["decisive_horizons"], [5])
        self.assertEqual(arm["falsifier"], FALSIFIER)
        self.assertEqual(arm["kill_rule"], KILL_RULE)


if __name__ == "__main__":
    unittest.main()
