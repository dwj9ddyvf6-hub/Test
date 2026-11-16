"""Blockers: Edge IMPROVE batch 11 (2026-10-24) — 12 Aster sleeves.

Four treatments, each behind a per-sleeve switch (default ON; OFF
restores the pre-change rule exactly), each with paired shadow
records (control = pre-change decision) in the served journal:

1. aster_rsi2_1d / aster_squeeze_1d (desk3/aster_batch1): trader
   features were computed over the still-forming daily bar. Treatment:
   features on completed bars only (ENH-B11-TRADER-COMPLETEDBAR).
2. aster_rec_vwap20_vert_{fixed,touch}_{a,b} (desk3/aster_b4): exits
   crossed the full spread at market with price_hint = cost basis,
   after entries got the batch-10 mid-limit cure. Treatment: exit as
   a limit at the package mid (ENH-B11-VWAP20VERT-EXITMID).
3. aster_tensor_{beta,c1}_cash_* (desk3/aster_batch13): batch 12
   repriced entries but cash mode accepted Tensor fires of ANY age.
   Treatment: refuse fires older than 1 session (ENH-B11-TENSOR-FIREAGE).
4. aster_squeeze_ada_fullcash (aster_sleeves/_common): the defining
   funding<0 input was read at the signal bar, 4h before entry.
   Treatment: revalidate funding at the entry bar (ENH-B11-...).

aster_rec_vwap20_long_touch_b carries the batch-10 mid-limit
treatment (desk3/aster_batch3, recovery family); batch 11 verifies
it binds for THIS sleeve (it was not in batch 10's test census).

Fail direction: every treatment assertion below (limit prices,
journal records, refusals) names artifacts that do not exist on the
pre-cure engines; the switch-OFF assertions pin the pre-change rule.
"""
import importlib
import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "tests", name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B3 = _load("test_aster_batch3_blockers")

from desk3 import aster_b4, aster_batch1 as b1, aster_batch13 as b13
from aster_sleeves import _common


def mkrows(closes, end_date, vols=1_000_000):
    dates, cur = [], end_date
    for _ in closes:
        dates.append(cur)
        cur -= timedelta(days=1)
    dates.reverse()
    return [{"t": d.isoformat(), "o": c, "h": c * 1.001, "l": c * 0.999,
             "c": c, "v": vols} for d, c in zip(dates, closes)]


TODAY = datetime(2026, 10, 26).date()
SLICE = {"capital_usd": 10000.0, "cash_usd": 10000.0}
CTX = {"session": "2026-10-26"}


class TestTraderCompletedBar(unittest.TestCase):
    def _rsi2_rows(self):
        base = [100.0 + i * 0.05 for i in range(258)]
        return mkrows(base + [base[-1] - 4.0, base[-1] - 8.0], TODAY)

    def test_rsi2_forming_bar_changes_decision(self):
        v = {"bars": {"SPY": self._rsi2_rows()}, "positions": [],
             "slice": SLICE, "now": "2026-10-26T15:00:00-04:00",
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        out = b1.evaluate("aster_rsi2_1d", v, dict(CTX))
        self.assertEqual([(o["kind"], o["symbol"]) for o in out],
                         [("entry", "SPY")])
        recs = v["extra"]["aster_enh_exp_journal"]["records"]
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["control_enter"])
        self.assertTrue(recs[0]["treatment_enter"])

    def test_rsi2_switch_off_restores_forming_bar_rule(self):
        v = {"bars": {"SPY": self._rsi2_rows()}, "positions": [],
             "slice": SLICE, "now": "2026-10-26T15:00:00-04:00",
             "extra": {"enh_aster_rsi2_1d": {"completed_bar": False}}}
        self.assertEqual(b1.evaluate("aster_rsi2_1d", v, dict(CTX)), [])

    def test_squeeze_forming_bar_hides_exit(self):
        decl = [200.0 - i * 0.3 for i in range(259)]
        rows = mkrows(decl + [260.0], TODAY)
        pos = [{"symbol": "SPY", "qty": 10, "avg_price": 190.0}]
        v = {"bars": {"SPY": rows}, "positions": pos, "slice": SLICE,
             "now": "2026-10-26T15:00:00-04:00",
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        out = b1.evaluate("aster_squeeze_1d", v, dict(CTX))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("close_below_ema20", out[0]["reason"])
        v_off = {"bars": {"SPY": rows}, "positions": pos, "slice": SLICE,
                 "now": "2026-10-26T15:00:00-04:00",
                 "extra": {"enh_aster_squeeze_1d": {"completed_bar": False}}}
        self.assertEqual(b1.evaluate("aster_squeeze_1d", v_off, dict(CTX)), [])


VERTS = ["aster_rec_vwap20_vert_fixed_a", "aster_rec_vwap20_vert_fixed_b",
         "aster_rec_vwap20_vert_touch_a", "aster_rec_vwap20_vert_touch_b"]


class TestVertExitMid(unittest.TestCase):
    def _view(self, sid, off=False):
        legs = [{"symbol": "SPY260C", "ratio": 1, "underlying": "SPY",
                 "expiry": "2026-11-13"},
                {"symbol": "SPY265C", "ratio": -1, "underlying": "SPY",
                 "expiry": "2026-11-13"}]
        v = {"options": [{"symbol": "SPY260C", "bid": 2.90, "ask": 3.00},
                         {"symbol": "SPY265C", "bid": 1.10, "ask": 1.20}],
             "positions": [{"symbol": "SPY260C", "qty": 2,
                            "avg_price": 1.50, "legs": legs,
                            "sessions_held": 5, "opened_at": "2026-10-19"}],
             "bars": {"SPY": [{"t": "2026-10-26", "c": 100.0}]},
             "now": "2026-10-26T15:00:00+00:00",
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        if off:
            v["extra"] = {f"enh_{sid}": {"exit_mid_limit": False}}
        return v

    def test_exit_limit_at_mid_all_four(self):
        for sid in VERTS:
            v = self._view(sid)
            out = aster_b4.evaluate(sid, v, dict(CTX))
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["order_type"], "limit", sid)
            self.assertEqual(out[0]["limit_price"], 1.80, sid)
            rec = out[0]["enhance_exp"]
            self.assertEqual(rec["control_price_ps"], 1.70, sid)
            self.assertAlmostEqual(rec["spread_saved_ps"], 0.10, sid)
            self.assertEqual(v["extra"]["aster_enh_exp_journal"]
                             ["records"], [rec], sid)

    def test_switch_off_restores_market_exit(self):
        for sid in VERTS:
            out = aster_b4.evaluate(sid, self._view(sid, off=True), dict(CTX))
            self.assertEqual(out[0]["order_type"], "market", sid)
            self.assertIsNone(out[0]["limit_price"], sid)
            self.assertNotIn("enhance_exp", out[0], sid)


TENSORS = ["aster_tensor_beta_cash_all_25", "aster_tensor_c1_cash_all_25",
           "aster_tensor_c1_cash_cool_25", "aster_tensor_c1_cash_hot_25"]


def _fire(sid, date_s):
    if sid.startswith("aster_tensor_beta"):
        return {"symbol": "BETA1", "signal": "beta_m2", "price": 50.0,
                "m2_qualified": True, "date": date_s}
    return {"symbol": "ACME", "signal": "buy_cyan", "price": 4.0,
            "ret60": 40.0, "vol20": 0.10, "adv_usd": 3_000_000,
            "atr_ratio": 2.0 if "hot" in sid else 0.5, "date": date_s}


class TestTensorFireAge(unittest.TestCase):
    def _view(self, sid, fire, off=False):
        v = {"tensor": {"fires": [fire]}, "bars": {}, "positions": [],
             "now": "2026-10-26T15:00:00+00:00",
             "extra": {"aster_enh_exp_journal": {"records": []}}}
        if off:
            v["extra"] = {f"{sid}_improve": {"fire_age": False}}
        return v

    def test_stale_fire_refused_all_four(self):
        for sid in TENSORS:
            v = self._view(sid, _fire(sid, "2026-10-19"))
            self.assertEqual(b13.evaluate(sid, v, dict(CTX)), [], sid)
            recs = v["extra"]["aster_enh_exp_journal"]["records"]
            self.assertEqual(len(recs), 1, sid)
            self.assertEqual(recs[0]["refusal"], "stale_fire_age", sid)
            self.assertEqual(recs[0]["age_days"], 7, sid)
            self.assertTrue(recs[0]["control_enter"], sid)

    def test_fresh_fire_enters_and_off_restores_any_age(self):
        for sid in TENSORS:
            out = b13.evaluate(sid, self._view(sid, _fire(sid, "2026-10-26")),
                               dict(CTX))
            self.assertEqual([o["kind"] for o in out], ["entry"], sid)
            out = b13.evaluate(sid, self._view(sid, _fire(sid, "2026-10-19"),
                                               off=True), dict(CTX))
            self.assertEqual([o["kind"] for o in out], ["entry"], sid)


class TestSqueezeAdaFundingRevalidation(unittest.TestCase):
    SID = "aster_squeeze_ada_fullcash"

    def _drive(self, entry_rate, off=False):
        t0 = datetime(2026, 10, 24, 0, 0, tzinfo=timezone.utc)
        bars = []
        for i in range(24):
            c = h = 0.50
            if i >= 22:
                c, h = 0.60, 0.61
            bars.append({"t": (t0 + timedelta(hours=4 * i)).isoformat(),
                         "o": c, "h": h, "l": 0.49, "c": c, "v": 1_000_000})
        entry_close = t0 + timedelta(hours=96)
        sig_close = entry_close - timedelta(hours=4)
        fund = [{"rate": -0.001,
                 "settled_at": (sig_close - timedelta(hours=1)).isoformat(),
                 "received_at": (sig_close - timedelta(minutes=30)).isoformat()},
                {"rate": entry_rate,
                 "settled_at": (entry_close - timedelta(hours=1)).isoformat(),
                 "received_at": (entry_close - timedelta(minutes=30)).isoformat()}]
        v = {"bars": {"ADAUSDT|4Hour": bars}, "positions": [],
             "funding": {"ADAUSDT": fund},
             "now": (entry_close + timedelta(seconds=120)).isoformat(),
             "slice": {"cash_usd": 10000.0}, "extra": {}}
        ctx = {}
        if off:
            ctx = {f"{self.SID}_enhance": {"funding_revalidation": False}}
        out = _common.evaluate_crypto(v, ctx, self.SID,
                                      "negative_funding_squeeze", "fullcash")
        return out, ctx

    def test_funding_normalized_refuses_entry(self):
        out, ctx = self._drive(0.002)
        self.assertEqual(out, [])
        rec = ctx["enhance_paired"][0]
        self.assertEqual(rec["treatment"], "refuse_funding_normalized")
        self.assertEqual(rec["funding_at_entry"], 0.002)

    def test_control_enters_on_flipped_funding(self):
        out, _ = self._drive(0.002, off=True)
        self.assertEqual([o["kind"] for o in out], ["entry"])

    def test_still_negative_funding_enters(self):
        out, ctx = self._drive(-0.003)
        self.assertEqual([o["kind"] for o in out], ["entry"])
        self.assertEqual(ctx["enhance_paired"][0]["treatment"], "enter")


class TestLongTouchBMidLimitVerified(unittest.TestCase):
    SID = "aster_rec_vwap20_long_touch_b"

    def _ev(self, view):
        return importlib.import_module(f"adapters3.{self.SID}").evaluate(
            view, {"sleeve_id": self.SID, "session": B3.SESSION,
                   "now": B3.ENTRY_NOW, "state_dir": "/tmp"})

    def test_entry_limit_at_mid_binds_for_touch_b(self):
        v = B3.entry_view_for(self.SID)
        v["extra"]["aster_enh_exp_journal"] = {"records": []}
        out = self._ev(v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["order_type"], "limit")
        rec = out[0]["enhance_exp"]
        self.assertEqual(rec["exp_id"], "ENH-ASTERB3-MIDLIMIT-20261024")
        self.assertGreater(rec["spread_saved"], 0)
        self.assertEqual(v["extra"]["aster_enh_exp_journal"]["records"],
                         [rec])

    def test_switch_off_restores_market(self):
        v = B3.entry_view_for(self.SID)
        v["extra"][f"enh_{self.SID}"] = {"mid_limit": False}
        out = self._ev(v)
        self.assertEqual(out[0]["order_type"], "market")
        self.assertNotIn("enhance_exp", out[0])


if __name__ == "__main__":
    unittest.main()
