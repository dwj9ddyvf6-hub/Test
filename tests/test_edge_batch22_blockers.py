"""Edge batch 22 blockers (ENH-Q07EXEC / ENH-Q07WLOW, 20261024).

lazarus_q07 (11 sleeves): entries were filtered, sized and stopped on
the signal-time fire price (up to 5 sessions stale) while the market
order fills at the current price — measured qty 100 @ stale $10 vs
$20 current = 2x the $1,000 slot, stop $8.50 = 57% below the fill.
Fail-first: stale-price tests fail on the pre-change engine.
q07_engine (s_q07w_g52_ml_ins2_wlow): wlow failed OPEN — a fire with
no wiki evidence defaulted to 0 views and passed as 'low attention'.
"""
import unittest

from desk3.lazarus_q07 import evaluate_sleeve, SPECS
from desk3.q07_engine import evaluate_q07

LAZ_IDS = ["s_q07w_c78_ml_mom6_tierA_wlow", "s_q07w_c78_ml_tierA_wcov",
           "s_q07w_c78_ml_tierA_wlow", "s_q07w_c78_sm_deep70_ins2_vix20",
           "s_q07w_c78_sm_deep70_wcov", "s_q07w_c78_sm_ins2_mom6_vix20",
           "s_q07w_c78_sm_tierA_wcov", "s_q07w_g52_ml_ats_z1_mom6_wlow",
           "s_q07w_g52_ml_tierA_wcov", "s_q07w_g52_sm_deep70_ins2_vix20",
           "s_q07w_g52_sm_deep70_wcov"]
CTX = {"session": "2026-10-23", "now": "2026-10-23"}
TAGS = {"tier": "A", "wiki_cov": True, "wiki_low": True,
        "insider_buys": 3, "vix": 25.0, "mom6_pct": 5.0, "ats_z": 1.5}


def laz_view(sid, fire_price, cur, extra=None, deep_tag=True):
    spec = SPECS[sid]
    tags = dict(TAGS)
    if deep_tag:
        tags["deep70"] = True
    fire = {"symbol": "TEST", "family": spec["family"], "band": spec["band"],
            "signal_date": "2026-10-23", "price": fire_price, "tags": tags}
    bars = {"QQQ": [{"c": 101.0}, {"c": 100.0}],
            "TEST": [{"c": cur}] * 30}
    v = {"bars": bars, "positions": [], "fires": [fire]}
    if extra:
        v["extra"] = extra
    return v


class TestExecPrice(unittest.TestCase):
    def test_sizing_and_stop_use_current_price(self):
        o = evaluate_sleeve("s_q07w_c78_ml_tierA_wcov",
                            laz_view("s_q07w_c78_ml_tierA_wcov", 10.0, 20.0), CTX)
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["qty"], 50)          # $1,000 / $20 current
        self.assertEqual(o[0]["stop_price"], 17.0)  # 15% below fill, not stale

    def test_switch_off_restores_stale_exactly(self):
        off = {"q07_enh": {"s_q07w_c78_ml_tierA_wcov": {"exec_price": False}}}
        o = evaluate_sleeve("s_q07w_c78_ml_tierA_wcov",
                            laz_view("s_q07w_c78_ml_tierA_wcov", 10.0, 20.0, off), CTX)
        self.assertEqual(o[0]["qty"], 100)
        self.assertEqual(o[0]["stop_price"], 8.5)

    def test_deep70_rechecked_at_current_price(self):
        # No deep70 tag: computed from price. Stale $7 passes, current $20 fails.
        on = evaluate_sleeve("s_q07w_c78_sm_deep70_wcov",
                             laz_view("s_q07w_c78_sm_deep70_wcov", 7.0, 20.0,
                                      deep_tag=False), CTX)
        self.assertEqual(on, [])
        off = {"q07_enh": {"s_q07w_c78_sm_deep70_wcov": {"exec_price": False}}}
        old = evaluate_sleeve("s_q07w_c78_sm_deep70_wcov",
                              laz_view("s_q07w_c78_sm_deep70_wcov", 7.0, 20.0,
                                       off, deep_tag=False), CTX)
        self.assertEqual(len(old), 1)

    def test_all_laz_sleeves_enter_fresh_and_journal(self):
        for sid in LAZ_IDS:
            j = {"records": []}
            o = evaluate_sleeve(sid, laz_view(sid, 10.0, 10.0,
                                              {"q07_exp_journal": j}), CTX)
            self.assertEqual(len(o), 1, sid)
            self.assertEqual(o[0]["qty"], 100, sid)
            self.assertEqual(len(j["records"]), 1, sid)
            self.assertTrue(j["records"][0]["treatment_enter"], sid)

    def test_exit_untouched(self):
        v = laz_view("s_q07w_c78_ml_tierA_wcov", 10.0, 8.0)
        v["positions"] = [{"symbol": "TEST", "qty": 10, "avg_price": 10.0}]
        v["fires"] = []
        o = evaluate_sleeve("s_q07w_c78_ml_tierA_wcov", v, CTX)
        self.assertTrue(any(i["kind"] == "exit" for i in o))


SPEC52 = {"id": "s_q07w_g52_ml_ins2_wlow", "family": "green",
          "horizon_wk": 52, "band": "ml", "filters": ("ins2", "wlow")}
BARS52 = {"QQQ|1day": [{"t": "2026-10-22", "c": 101.0},
                       {"t": "2026-10-23", "c": 100.0}],
          "TEST|1day": [{"t": "2026-10-23", "c": 50.0}]}


def eng_view(fire, extra=None):
    e = {"sleeve_fires": [fire]}
    if extra:
        e.update(extra)
    return {"extra": e, "bars": BARS52, "positions": [],
            "now": "2026-10-23T14:00:00+00:00"}


FIRE52 = {"sleeve": "s_q07w_g52_ml_ins2_wlow", "symbol": "TEST",
          "signal_date": "2026-10-23", "insider_buys": 3}


class TestWlowEvidence(unittest.TestCase):
    def test_no_wiki_evidence_fails_closed(self):
        self.assertEqual(evaluate_q07(SPEC52, eng_view(dict(FIRE52)), {}), [])

    def test_switch_off_restores_fail_open(self):
        off = {"q07_enh": {"s_q07w_g52_ml_ins2_wlow": {"wlow_evidence": False}}}
        o = evaluate_q07(SPEC52, eng_view(dict(FIRE52), off), {})
        self.assertEqual(len(o), 1)

    def test_low_evidence_still_enters_and_journals(self):
        j = {"records": []}
        f = dict(FIRE52, wiki_views_30d=120)
        o = evaluate_q07(SPEC52, eng_view(f, {"q07_exp_journal": j}), {})
        self.assertEqual(len(o), 1)
        self.assertEqual(len(j["records"]), 1)
        self.assertTrue(j["records"][0]["treatment_enter"])

    def test_high_views_refused_both_rules(self):
        f = dict(FIRE52, wiki_views_30d=50000)
        self.assertEqual(evaluate_q07(SPEC52, eng_view(f), {}), [])


if __name__ == "__main__":
    unittest.main()
