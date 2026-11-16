"""Edge batch 21 blockers — Q07 execution-price revalidation (x9, served by
the shared ENH-Q07EXEC-20261024 cure in desk3/lazarus_q07.py) + second-look
VERIFY-ONLY pins for the Midna pair (ENH19) and s_moonshot (ENH-LAZ +
ENH19 bound guard).

Fail direction: pre-cure Q07 engine priced filters/sizing/stop off the
fire print — ON and OFF arms were identical (qty 100 / stop 8.50 on the
$10-fire/$12.50-fresh fixture; cheap5 entered at qty 250). Removing the
ENH19 / bound-guard cures likewise collapses the Midna/Moonshot A/B diffs.
"""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.lazarus_q07 import evaluate_sleeve as qev
from desk3.lazarus_midna import evaluate as mev
from desk3.lazarus import evaluate as lev

SESSION = "2026-10-23"
QQQ = [{"date": "2026-10-22", "c": 101.0}, {"date": "2026-10-23", "c": 100.0}]
Q07 = {
    "s_q07w_c52_ml_mom6_tierA_wlow": ({"mom6_pct": 5.0, "tier": "A", "wiki_low": True}, 10.0, 12.50),
    "s_q07w_c52_ml_mom6_wspike2": ({"mom6_pct": 5.0, "wiki_spike2": True}, 10.0, 12.50),
    "s_q07w_c52_ml_tierA_wcov": ({"tier": "A", "wiki_cov": True}, 10.0, 12.50),
    "s_q07w_c52_ml_tierA_wlow": ({"tier": "A", "wiki_low": True}, 10.0, 12.50),
    "s_q07w_c52_sm_cheap5_ins2_mom6": ({"insider_buys": 3, "mom6_pct": 5.0}, 4.00, 6.00),
    "s_q07w_c52_sm_cheap5_wcov": ({"wiki_cov": True}, 4.00, 6.00),
    "s_q07w_c52_sm_deep70_wcov": ({"wiki_cov": True}, 10.0, 12.50),
    "s_q07w_c52_sm_tierA_wcov": ({"tier": "A", "wiki_cov": True}, 10.0, 12.50),
    "s_q07w_c78_ml_deep70_tierA_wlow": ({"tier": "A", "wiki_low": True}, 10.0, 12.50),
}
CHEAP5 = {"s_q07w_c52_sm_cheap5_ins2_mom6", "s_q07w_c52_sm_cheap5_wcov"}


def qview(sid, tags, fire_px, fresh, off=False):
    extra = {"q07_exp_journal": {"records": []}}
    if off:
        extra["q07_enh"] = {sid: {"exec_price": False}}
    return {"fires": [{"sleeve_id": sid, "symbol": "XYZ", "family": "cyan",
                       "band": "midlarge" if "_ml_" in sid else "small",
                       "signal_date": "2026-10-22", "price": fire_px, "tags": tags}],
            "bars": {"QQQ": list(QQQ), "XYZ": [{"c": 20.0}, {"c": 18.0}, {"c": fresh}]},
            "positions": [], "extra": extra}


def entries(out):
    return [i for i in out if i["kind"] == "entry"]


class TestQ07ExecPrice(unittest.TestCase):
    def test_on_sizes_and_stops_at_execution_price(self):
        for sid, (tags, fp, fr) in Q07.items():
            if sid in CHEAP5:
                continue
            ent = entries(qev(sid, qview(sid, tags, fp, fr), {"session": SESSION}))
            self.assertEqual(len(ent), 1, sid)
            self.assertEqual(ent[0]["qty"], 80, sid)          # 1000 // 12.50
            self.assertEqual(ent[0]["stop_price"], 10.625, sid)  # 15% off fill

    def test_off_restores_fire_price_rule_exactly(self):
        for sid, (tags, fp, fr) in Q07.items():
            ent = entries(qev(sid, qview(sid, tags, fp, fr, off=True), {"session": SESSION}))
            self.assertEqual(len(ent), 1, sid)
            self.assertEqual(ent[0]["qty"], int(1000 // fp), sid)
            self.assertEqual(ent[0]["stop_price"], round(fp * 0.85, 4), sid)

    def test_cheap5_refused_at_execution_price(self):
        for sid in CHEAP5:
            tags, fp, fr = Q07[sid]
            self.assertEqual(entries(qev(sid, qview(sid, tags, fp, fr),
                                         {"session": SESSION})), [], sid)

    def test_paired_shadow_records(self):
        for sid, (tags, fp, fr) in Q07.items():
            v = qview(sid, tags, fp, fr)
            qev(sid, v, {"session": SESSION})
            recs = [r for r in v["extra"]["q07_exp_journal"]["records"]
                    if r.get("exp_id") == "ENH-Q07EXEC-20261024"]
            self.assertGreaterEqual(len(recs), 1, sid)
            self.assertEqual(recs[0]["control_price"], fp, sid)
            self.assertEqual(recs[0]["treatment_price"], fr, sid)
            self.assertTrue(recs[0]["control_enter"], sid)
            self.assertEqual(recs[0]["treatment_enter"], sid not in CHEAP5, sid)


class TestMidnaVerifyOnly(unittest.TestCase):
    def _drive(self, sid, gate_extra, off):
        extra = dict(gate_extra)
        if off:
            extra[f"{sid}_improve"] = {"fresh_price": False}
        v = {"tensor": [{"sleeve_id": sid, "symbol": "XYZ",
                         "family": "cyan" if "cyan" in sid else "green",
                         "timeframe": "1W", "date": SESSION, "price": 10.0}],
             "bars": {"XYZ": [{"c": 12.50}], "SMH": [{"c": 100.0}] * 21},
             "positions": [], "extra": extra, "now": "2026-10-23T14:00:00+00:00"}
        return entries(mev(sid, v, {"session": SESSION}))

    def test_enh19_reprice_holds_for_batch21_pair(self):
        for sid, gx in (("s_mn_w_cyan_vix", {"vix_close": 18.0}),
                        ("s_mn_w_green_smh", {})):
            on = self._drive(sid, gx, off=False)
            off = self._drive(sid, gx, off=True)
            self.assertEqual((len(on), on[0]["qty"], on[0]["price_hint"]), (1, 80, 12.50), sid)
            self.assertEqual((len(off), off[0]["qty"], off[0]["price_hint"]), (1, 100, 10.0), sid)


class TestMoonshotVerifyOnly(unittest.TestCase):
    def _fire(self, **kw):
        f = {"sleeve_id": "s_moonshot", "symbol": "XYZ",
             "fired_at": "2026-10-22T14:00:00+00:00", "price": 10.0,
             "qqq_red": True, "tags": {"deep60": True}}
        f.update(kw)
        return f

    def test_reprice_and_bound_guard_hold(self):
        with tempfile.TemporaryDirectory() as td:
            v = {"lazarus_fires": [self._fire()], "bars": {"XYZ": [{"c": 9.0}, {"c": 12.50}]},
                 "positions": [], "now": "2026-10-23T14:00:00+00:00", "extra": {}}
            ent = entries(lev("s_moonshot", v, {"state_dir": os.path.join(td, "a")}))
            self.assertEqual((len(ent), ent[0]["qty"], ent[0]["stop_price"]), (1, 20, 10.625))
            v2 = {"lazarus_fires": [self._fire(target_price=11.0)],
                  "bars": {"XYZ": [{"c": 9.0}, {"c": 12.50}]}, "positions": [],
                  "now": "2026-10-23T14:00:00+00:00", "extra": {"enh19_journal": []}}
            self.assertEqual(entries(lev("s_moonshot", v2, {"state_dir": os.path.join(td, "b")})), [])
            self.assertEqual(v2["extra"]["enh19_journal"][0]["enhanced"], "refuse_bound")


if __name__ == "__main__":
    unittest.main()
