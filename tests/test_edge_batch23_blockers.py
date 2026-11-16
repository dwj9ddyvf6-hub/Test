"""Edge batch 23 blockers (ENH-Q07FRESH / ENH-Q07SLOT, 20261024).

lazarus_q07 + q07_engine 1-slot lanes: the slot went to whichever
eligible fire the producer listed FIRST — a 5-session-old fire crowded
out a same-day fire (edge decayed, window expiring). Treatment:
freshest-signal-first allocation, switch fresh_first default ON, OFF =
list order exactly; paired q07_exp_journal records.
laz_sleeves q07 (s52_ml_ins2_mom6_vix20, 2 slots): the slot break test
used the FIXED held count, so with 0 held it never fired and EVERY
passing fire entered (3 entries vs a 2-slot book). Treatment counts
emitted entries (ENH19 mirror), switch slot_guard default ON.
Parked lazarus_q07 swing lanes (s52_ml_deep70_wlow / _vix20_wlow):
entries refused by spec — VERIFY-ONLY; exits proven here.
Fail-first: fresh-first and slot-guard tests fail on pre-change engines.
"""
import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.lazarus_q07 import evaluate_sleeve
from desk3.q07_engine import evaluate_q07

CTX = {"session": "2026-10-23", "now": "2026-10-23T15:00:00"}
QDATES = ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]


def qbars():
    return [{"c": c, "date": d} for c, d in zip([505.0, 504.0, 503.0, 502.0, 495.0], QDATES)]


def laz_fire(sym, date):
    return {"symbol": sym, "family": "green", "band": "small",
            "signal_date": date, "price": 20.0,
            "tags": {"tier": "A", "wiki_cov": True}}


SID_LAZ = "s_q07w_g78_sm_tierA_wcov"


def laz_view(extra=None):
    v = {"bars": {"QQQ": qbars()}, "positions": [],
         "fires": [laz_fire("OLD", "2026-10-16"), laz_fire("NEW", "2026-10-23")]}
    if extra:
        v["extra"] = extra
    return v


class TestFreshFirstLazarus(unittest.TestCase):
    def test_on_takes_freshest(self):
        o = evaluate_sleeve(SID_LAZ, laz_view(), CTX)
        self.assertEqual([i["symbol"] for i in o if i["kind"] == "entry"], ["NEW"])

    def test_off_restores_list_order(self):
        off = {"q07_enh": {SID_LAZ: {"fresh_first": False}}}
        o = evaluate_sleeve(SID_LAZ, laz_view(off), CTX)
        self.assertEqual([i["symbol"] for i in o if i["kind"] == "entry"], ["OLD"])

    def test_journal_paired_record(self):
        j = {"records": []}
        evaluate_sleeve(SID_LAZ, laz_view({"q07_exp_journal": j}), CTX)
        recs = [r for r in j["records"] if r["exp_id"] == "ENH-Q07FRESH-20261024"]
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["control_first"], "OLD")
        self.assertEqual(recs[0]["treatment_first"], "NEW")
        self.assertEqual(recs[0]["treatment_age"], 0)


SPEC52 = {"id": "s_q07w_g52_sm_ins2_wcov", "family": "green",
          "horizon_wk": 52, "band": "sm", "filters": ("ins2", "wcov")}
QB = {"QQQ|1day": [{"t": d, "c": c} for d, c in
                    zip(QDATES, [505.0, 504.0, 503.0, 502.0, 495.0])],
      "OLD|1day": [{"t": "2026-10-23", "c": 20.0}],
      "NEW|1day": [{"t": "2026-10-23", "c": 20.0}]}


def eng_fire(sym, date):
    return {"sleeve": SPEC52["id"], "symbol": sym, "signal_date": date,
            "insider_buys": 3, "wiki_views_30d": 500}


def eng_view(extra=None):
    e = {"sleeve_fires": [eng_fire("OLD", "2026-10-16"), eng_fire("NEW", "2026-10-23")]}
    if extra:
        e.update(extra)
    return {"extra": e, "bars": QB, "positions": [],
            "now": "2026-10-23T14:00:00+00:00"}


class TestFreshFirstEngine(unittest.TestCase):
    def test_on_takes_freshest(self):
        o = evaluate_q07(SPEC52, eng_view(), {})
        self.assertEqual([i.symbol for i in o if i.kind == "enter"], ["NEW"])

    def test_off_restores_list_order(self):
        off = {"q07_enh": {SPEC52["id"]: {"fresh_first": False}}}
        o = evaluate_q07(SPEC52, eng_view(off), {})
        self.assertEqual([i.symbol for i in o if i.kind == "enter"], ["OLD"])

    def test_journal_paired_record(self):
        j = {"records": []}
        evaluate_q07(SPEC52, eng_view({"q07_exp_journal": j}), {})
        recs = [r for r in j["records"] if r["exp_id"] == "ENH-Q07FRESH-20261024"]
        self.assertEqual(len(recs), 1)
        self.assertEqual((recs[0]["control_first"], recs[0]["treatment_first"]),
                         ("OLD", "NEW"))


SID_LAZB7 = "s_q07w_s52_ml_ins2_mom6_vix20"


def laz7_view(extra=None):
    bars = {"QQQ|1Day": [{"t": "2026-10-22", "c": 101.0},
                         {"t": "2026-10-23", "c": 100.0}]}
    fires, alt = {}, {}
    for sym in ("AAA", "BBB", "CCC"):
        bars[f"{sym}|1Day"] = [{"t": "2026-10-23", "c": 5.0 + 5.0 * k / 129}
                               for k in range(130)]
        fires[sym] = {"family": "swing", "date": "2026-10-22"}
        alt[sym] = {"insider_buys": 3, "mcap_band": "midlarge"}
    v = {"now": "2026-10-23T15:00:00", "bars": bars, "positions": [],
         "tensor_fires": fires, "alt_data": alt, "vix": 25.0}
    if extra:
        v["extra"] = extra
    return v


class TestSlotGuardLazB7(unittest.TestCase):
    def ev(self, extra=None):
        from laz_sleeves.s_q07w_s52_ml_ins2_mom6_vix20 import evaluate
        return evaluate(laz7_view(extra), {})

    def test_on_caps_at_two_slots(self):
        o = self.ev()
        self.assertEqual(len([i for i in o if i["kind"] == "entry"]), 2)

    def test_off_restores_unbounded(self):
        off = {f"{SID_LAZB7}_enh23": {"slot_guard": False}}
        o = self.ev(off)
        self.assertEqual(len([i for i in o if i["kind"] == "entry"]), 3)

    def test_journal_records(self):
        j = []
        self.ev({"enh23_journal": j})
        self.assertTrue(any(r["exp_id"] == "ENH-Q07SLOT-20261024" for r in j))


class TestParkedVerifyOnly(unittest.TestCase):
    # FIX-F1-Q07-20261115: these two lanes were unparked in
    # desk3/lazarus_q07.py SPECS to match the roster
    # (UNPARK-REGISTRY-20261114); the class name is kept from the
    # original verify-only pass, but the entry expectation is now
    # the cured one — a qualifying fire ENTERS and the stop exit is
    # still managed. The fail-closed proof lives in
    # test_q07_failclosed_f1_20261115_blockers.py.
    def test_unparked_lanes_enter_and_manage_stop_exit(self):
        for sid in ("s_q07w_s52_ml_deep70_wlow",
                    "s_q07w_s52_ml_deep70_vix20_wlow"):
            v = {"bars": {"QQQ": qbars(),
                          "TEST": [{"c": 16.0, "date": "2026-10-23"}]},
                 "positions": [{"symbol": "TEST", "qty": 10, "avg_price": 20.0}],
                 "fires": [{"symbol": "NEW", "family": "swing",
                            "band": "midlarge", "signal_date": "2026-10-23",
                            "price": 10.0, "tags": {"deep70": True,
                                                    "wiki_low": True, "vix": 25.0}}]}
            o = evaluate_sleeve(sid, v, CTX)
            self.assertTrue(any(i["kind"] == "exit" for i in o), sid)
            # entry leg on an empty book (the held TEST position
            # occupies the single slot above): NEW needs bars for
            # the exec-price revalidation.
            v2 = {"bars": {"QQQ": qbars(),
                           "NEW": [{"c": 10.0, "date": "2026-10-23"}]},
                  "positions": [],
                  "fires": [dict(v["fires"][0])]}
            o2 = evaluate_sleeve(sid, v2, CTX)
            self.assertTrue(any(i["kind"] == "entry" for i in o2), sid)


if __name__ == "__main__":
    unittest.main()
