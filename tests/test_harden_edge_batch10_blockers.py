"""Blockers: Edge IMPROVE batch 10 (2026-10-24) — mid-price limit
execution for 12 Aster sleeves (aster_b2 recovery RSI2 long x4,
aster_batch3 recovery RSI2 vertical x4 + VWAP20 long x3,
aster_batch15 overnight 25bp).

Binding leak: entries pay the full ask / exits take the full bid via
market orders on short-horizon edges. Treatment (default ON): limit
at the package mid of the already-fetched quotes; shadow control =
the ask/bid price the pre-change rule would have crossed, recorded
paired in intent["enhance_exp"] + extra["aster_enh_exp_journal"].
Switch OFF (extra["enh_<sid>"]={"mid_limit": False}) restores the
pre-change market order exactly.

Fail direction: pre-enhancement every intent below was
order_type="market", limit_price=None, with no "enhance_exp" — the
treatment assertions fail on the old engines.
"""
import importlib, importlib.util, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "tests", name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B2 = _load("test_aster_batch2_blockers")
B3 = _load("test_aster_batch3_blockers")
B15 = _load("test_aster_batch15_blockers")

B2_IDS = ["aster_rec_rsi2_long_fixed_a", "aster_rec_rsi2_long_fixed_b",
          "aster_rec_rsi2_long_touch_a", "aster_rec_rsi2_long_touch_b"]
B3_IDS = ["aster_rec_rsi2_vertical_fixed_a", "aster_rec_rsi2_vertical_fixed_b",
          "aster_rec_rsi2_vertical_touch_a", "aster_rec_rsi2_vertical_touch_b",
          "aster_rec_vwap20_long_fixed_a", "aster_rec_vwap20_long_fixed_b",
          "aster_rec_vwap20_long_touch_a"]
ON25 = "aster_r19_timing_overnight_25bp"


def ev3(sid, view):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, {"sleeve_id": sid, "session": B3.SESSION, "now": B3.ENTRY_NOW,
               "state_dir": "/tmp"})


class TestB2MidLimit(unittest.TestCase):
    def view(self, sid, off=False):
        v = {"bars": {"SPY": B2.bars(B2.rsi2_series())},
             "options": B2.chain(), "positions": [],
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        if off:
            v["extra"][f"enh_{sid}"] = {"mid_limit": False}
        return v

    def test_entry_limit_at_mid_all_four(self):
        for sid in B2_IDS:
            v = self.view(sid)
            out = B2.ev(sid, v)
            self.assertEqual(len(out), 1, sid)
            i = out[0]
            self.assertEqual(i["order_type"], "limit", sid)
            # chain ask 0.40 / bid 0.35 -> mid 0.375 (limit rounded 0.38)
            self.assertGreaterEqual(i["limit_price"], 0.35, sid)
            self.assertLess(i["limit_price"], 0.40, sid)
            rec = i["enhance_exp"]
            self.assertEqual(rec["control_price_ps"], 0.40, sid)
            self.assertAlmostEqual(rec["spread_saved_ps"], 0.025, sid)
            self.assertEqual(v["extra"]["aster_enh_exp_journal"]
                             ["records"], [rec], sid)

    def test_switch_off_restores_market_exactly(self):
        for sid in B2_IDS:
            out = B2.ev(sid, self.view(sid, off=True))
            self.assertEqual(out[0]["order_type"], "market", sid)
            self.assertIsNone(out[0]["limit_price"], sid)
            self.assertNotIn("enhance_exp", out[0], sid)

    def test_exit_limit_at_mid(self):
        v = {"bars": {"SPY": B2.bars([185.0] * 10)}, "options": B2.chain(),
             "positions": B2.opt_pos("x", held=5),
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        out = B2.ev("aster_rec_rsi2_long_fixed_a", v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertEqual(out[0]["order_type"], "limit")
        self.assertLess(out[0]["limit_price"], 0.40)
        self.assertAlmostEqual(
            out[0]["enhance_exp"]["control_price_ps"], 0.35)


class TestB3MidLimit(unittest.TestCase):
    def test_entry_limit_at_mid_all_seven(self):
        for sid in B3_IDS:
            v = B3.entry_view_for(sid)
            v["extra"]["aster_enh_exp_journal"] = {"records": []}
            out = ev3(sid, v)
            self.assertEqual(len(out), 1, sid)
            i = out[0]
            self.assertEqual(i["order_type"], "limit", sid)
            self.assertGreater(i["limit_price"], 0, sid)
            rec = i["enhance_exp"]
            # mid debit strictly inside the crossed ask package price
            self.assertLess(rec["treatment_limit_ps"] * 100,
                            rec["control_price"], sid)
            self.assertGreater(rec["spread_saved"], 0, sid)
            self.assertEqual(v["extra"]["aster_enh_exp_journal"]
                             ["records"], [rec], sid)

    def test_vertical_a_exact_mid(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        out = ev3(sid, B3.entry_view_for(sid))
        # long mid 2.95 - wing mid 1.15 = 1.80/share (control 1.90)
        self.assertEqual(out[0]["limit_price"], 1.80)
        self.assertAlmostEqual(out[0]["enhance_exp"]["control_price"], 190.0)

    def test_switch_off_restores_market_exactly(self):
        for sid in B3_IDS:
            v = B3.entry_view_for(sid)
            v["extra"][f"enh_{sid}"] = {"mid_limit": False}
            out = ev3(sid, v)
            self.assertEqual(out[0]["order_type"], "market", sid)
            self.assertIsNone(out[0]["limit_price"], sid)
            self.assertNotIn("enhance_exp", out[0], sid)

    def test_exit_limit_at_mid(self):
        sid = "aster_rec_rsi2_vertical_fixed_a"
        now = "2026-10-30T15:56:00-04:00"
        v = B3.exit_view(B3.held_position(), now, "2026-10-30")
        v["extra"]["aster_enh_exp_journal"] = {"records": []}
        out = ev3(sid, v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["order_type"], "limit")
        rec = out[0]["enhance_exp"]
        # control close 4.00-0.55=3.45/share; mid close 4.05-0.525=3.525
        self.assertAlmostEqual(rec["control_price"], 345.0)
        self.assertAlmostEqual(rec["treatment_limit_ps"], 3.525)
        self.assertGreater(out[0]["limit_price"], 3.45)


class TestOvernightMidLimit(unittest.TestCase):
    def test_entry_limit_at_mid(self):
        v = B15.overnight_fixture()
        v["extra"]["aster_enh_exp_journal"] = {"records": []}
        out = B15.drive(ON25, v)
        self.assertEqual(len(out), 1)
        i = out[0]
        self.assertEqual(i["order_type"], "limit")
        self.assertEqual(i["limit_price"], 100.95)  # bid 100.9 / ask 101.0
        rec = i["enhance_exp"]
        self.assertEqual(rec["control_price"], 101.0)
        self.assertAlmostEqual(rec["spread_saved"], 0.05)
        self.assertEqual(v["extra"]["aster_enh_exp_journal"]["records"],
                         [rec])

    def test_switch_off_restores_market_exactly(self):
        v = B15.overnight_fixture()
        v["extra"][f"enh_{ON25}"] = {"mid_limit": False}
        out = B15.drive(ON25, v)
        self.assertEqual(out[0]["order_type"], "market")
        self.assertIsNone(out[0]["limit_price"])
        self.assertNotIn("enhance_exp", out[0])


if __name__ == "__main__":
    unittest.main()
