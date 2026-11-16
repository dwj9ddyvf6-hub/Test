"""Edge batch 24 blockers (Q07 stale-bar entry gates, 20261024).

Binding leak (all three Q07 engines): entries were filtered, sized and
stopped off the symbol's last bar close with NO check of that bar's age
against the decision session. A halted/delisted name whose feed died
weeks earlier still entered at the ancient close; the market fill at
the real price breaks the $1,000 slot and the designed 15% stop.
- engine A desk3/q07_engine.py: cured by ENH25-Q07-STALEBARS
  (switch extra.q07_enh[sid].fresh_bars, >5 QQQ sessions stale);
  batch 24 supplies the per-sleeve A/B proof for its 4 lanes.
- engine B desk3/lazarus_q07.py: VERIFY-ONLY x4 — all four lanes are
  parked=True in SPECS and evaluate_sleeve enforces it in-function
  (exits only), so no entry leak can bind (batch-23 precedent for the
  parked swing lanes). Evidence below: a fully qualifying fire emits
  no entry; the 15% stop exit and the horizon exit both fire.
- engine C laz_sleeves/_common.q07_evaluate: ENH24-LAZB7-Q07STALE —
  switch extra.<sid>_enh24.stale_gate, _bar_stale >4 days.
Exits are never gated in any engine. Fail-first: the stale-entry
assertions fail on the pre-change engines.
"""
import importlib
import os
import sys
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.q07_engine import evaluate_q07                       # engine A
from desk3.lazarus_q07 import evaluate_sleeve as laz_evaluate   # engine B

SESS = date(2026, 10, 23)  # Friday


def _weekdays(end, n):
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


# ------------------------------------------------------------ engine A
A_IDS = ["s_q07w_s52_sm_cheap5_deep70_ins2",
         "s_q07w_s52_sm_cheap5_ins2_vix20",
         "s_q07w_s78_mi_cheap5_ins2_mom6",
         "s_q07w_s78_ml_deep70_ins2_vix20"]


def _a_spec(sid):
    return importlib.import_module(f"adapters3.{sid}").SPEC


def _a_view(sid, closes, highs=None, stale=True, extra=None):
    days = _weekdays(SESS, 15)
    qqq = [{"t": d.isoformat(), "c": 200.0 - i} for i, d in enumerate(days)]
    sym_end = date(2026, 10, 9) if stale else SESS
    sym_days = _weekdays(sym_end, len(closes))
    bars = [{"t": d.isoformat(), "c": c,
             "h": (highs[i] if highs else c)} for i, (d, c)
            in enumerate(zip(sym_days, closes))]
    spec = _a_spec(sid)
    fire = {"sleeve": sid, "symbol": "TEST", "signal_date": SESS.isoformat(),
            "cap_band": spec["band"], "insider_buys": 2}
    e = {"sleeve_fires": [fire], "vix": 25.0,
         "q07_exp_journal": {"records": []}}
    if extra:
        e.update(extra)
    return spec, {"extra": e, "bars": {"QQQ|1day": qqq, "TEST|1day": bars},
                  "positions": [], "now": "2026-10-23T14:00:00+00:00"}, e


A_FIXTURES = {  # sid -> (closes, highs)
    "s_q07w_s52_sm_cheap5_deep70_ins2": ([4.0] * 25, [10.0] * 25),
    "s_q07w_s52_sm_cheap5_ins2_vix20": ([4.0] * 5, None),
    "s_q07w_s78_mi_cheap5_ins2_mom6": ([3.0] * 4 + [4.0] * 126, None),
    "s_q07w_s78_ml_deep70_ins2_vix20": ([10.0] * 25, [20.0] * 25),
}


class TestEngineAStaleBars(unittest.TestCase):
    def test_stale_refused_on_fresh_enters_off_restores(self):
        for sid in A_IDS:
            closes, highs = A_FIXTURES[sid]
            spec, v, e = _a_view(sid, closes, highs, stale=True)
            self.assertEqual(evaluate_q07(spec, v, {}), [], sid)
            recs = [r for r in e["q07_exp_journal"]["records"]
                    if r["exp_id"] == "ENH25-Q07-STALEBARS-20261024"
                    and r["sleeve"] == sid]
            self.assertEqual(len(recs), 1, sid)
            self.assertFalse(recs[0]["treatment_enter"], sid)
            self.assertTrue(recs[0]["control_enter"], sid)
            off = {"q07_enh": {sid: {"fresh_bars": False}}}
            spec, v2, _ = _a_view(sid, closes, highs, stale=True, extra=off)
            out = evaluate_q07(spec, v2, {})
            self.assertEqual(len([i for i in out if i.kind == "enter"]), 1, sid)
            spec, v3, _ = _a_view(sid, closes, highs, stale=False)
            out = evaluate_q07(spec, v3, {})
            self.assertEqual(len([i for i in out if i.kind == "enter"]), 1, sid)


# ------------------------------------------------------------ engine B
B_IDS = ["s_q07w_s52_sm_cheap5_wcov", "s_q07w_s52_sm_deep70_wcov",
         "s_q07w_s78_ml_deep70_mom6_wlow", "s_q07w_s78_ml_deep70_wcov"]
B_CTX = {"session": "2026-10-23", "now": "2026-10-23"}
B_TAGS = {
    "s_q07w_s52_sm_cheap5_wcov": ({"wiki_cov": True}, "small", 4.0),
    "s_q07w_s52_sm_deep70_wcov": ({"wiki_cov": True, "deep70": True},
                                  "small", 10.0),
    "s_q07w_s78_ml_deep70_mom6_wlow": ({"wiki_low": True, "deep70": True,
                                        "mom6_pct": 5.0}, "midlarge", 10.0),
    "s_q07w_s78_ml_deep70_wcov": ({"wiki_cov": True, "deep70": True},
                                  "midlarge", 10.0),
}
def _b_view(sid, last_day, extra=None):
    tags, band, px = B_TAGS[sid]
    days = _weekdays(last_day, 30)
    bars = [{"date": d.isoformat(), "c": px} for d in days]
    fire = {"symbol": "TEST", "family": "swing", "band": band,
            "signal_date": "2026-10-23", "price": px, "tags": dict(tags)}
    v = {"bars": {"QQQ": [{"date": "2026-10-22", "c": 101.0},
                          {"date": "2026-10-23", "c": 100.0}],
                  "TEST": bars},
         "positions": [], "fires": [fire],
         "extra": {"q07_exp_journal": {"records": []}}}
    if extra:
        v["extra"].update(extra)
    return v


class TestEngineBParkedVerifyOnly(unittest.TestCase):
    def test_parked_qualifying_fire_emits_no_entry(self):
        from desk3.lazarus_q07 import SPECS
        # FIX-F1-Q07-20261115: the two ML lanes in B_IDS were
        # unparked in SPECS to match the roster
        # (UNPARK-REGISTRY-20261114) and now ENTER on a qualifying
        # fire. PARKED-ROSTER-Q07-20261116: the two SM lanes in
        # B_IDS were likewise in the config roster all along,
        # unparked on 2026-11-14 (the earlier SPECS-only claim was
        # false), and are now unparked in SPECS in the same cure
        # shape, so all four B_IDS lanes ENTER on a qualifying fire.
        _unparked_f1 = {"s_q07w_s78_ml_deep70_mom6_wlow",
                        "s_q07w_s78_ml_deep70_wcov",
                        "s_q07w_s52_sm_cheap5_wcov",
                        "s_q07w_s52_sm_deep70_wcov"}
        for sid in B_IDS:
            self.assertEqual(SPECS[sid]["parked"],
                             sid not in _unparked_f1, sid)
            o = laz_evaluate(sid, _b_view(sid, SESS), B_CTX)
            if sid in _unparked_f1:
                self.assertEqual(
                    len([i for i in o if i["kind"] == "entry"]), 1, sid)
            else:
                self.assertEqual(
                    [i for i in o if i["kind"] == "entry"], [], sid)

    def test_stop_exit_fires_even_on_stale_bars(self):
        sid = "s_q07w_s52_sm_cheap5_wcov"
        v = _b_view(sid, date(2026, 10, 9))
        v["fires"] = []
        v["positions"] = [{"symbol": "TEST", "qty": 10, "avg_price": 10.0}]
        for row in v["bars"]["TEST"]:
            row["c"] = 8.0  # below the 15% stop
        o = laz_evaluate(sid, v, B_CTX)
        self.assertTrue(any(i["kind"] == "exit" for i in o))

    def test_horizon_exit_fires(self):
        for sid in B_IDS:
            v = _b_view(sid, SESS)
            v["fires"] = []
            _, _, px = B_TAGS[sid]
            v["positions"] = [{"symbol": "TEST", "qty": 10,
                               "avg_price": px, "opened_at": "2025-01-02"}]
            o = laz_evaluate(sid, v, B_CTX)
            self.assertTrue(any(i["kind"] == "exit" and "horizon" in i["reason"]
                                for i in o), sid)


# ------------------------------------------------------------ engine C
C_IDS = ["s_q07w_s52_ml_ins2_mom6_wlow", "s_q07w_s78_mi_ats_z1_cheap5",
         "s_q07w_s78_mi_ats_z1_mom6", "s_q07w_s78_ml_deep70_glow_ins2"]
EXP24_C = "ENH24-LAZB7-Q07STALE-20261024"


def _c_bars(closes, end):
    days = _weekdays(end, len(closes))
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": c, "h": c * 1.001,
             "l": c * 0.999, "c": c, "v": 10000.0}
            for d, c in zip(days, closes)]


C_FIXTURES = {  # sid -> (closes, alt tags)
    "s_q07w_s52_ml_ins2_mom6_wlow": (
        [40.0] * 65 + [50.0] * 65,
        {"insider_buys": 3, "wiki": "low", "mcap_band": "midlarge"}),
    "s_q07w_s78_mi_ats_z1_cheap5": (
        [4.0] * 10, {"ats_z": 1.5, "mcap_band": "micro"}),
    "s_q07w_s78_mi_ats_z1_mom6": (
        [40.0] * 65 + [50.0] * 65, {"ats_z": 1.5, "mcap_band": "micro"}),
    "s_q07w_s78_ml_deep70_glow_ins2": (
        [100.0] * 130 + [25.0],
        {"insider_buys": 3, "gamma_low": True, "mcap_band": "midlarge"}),
}


def _c_view(sid, end, extra=None):
    closes, alt = C_FIXTURES[sid]
    v = {"now": "2026-10-23T15:30:00-04:00",
         "bars": {"ACME|1Day": _c_bars(closes, end),
                  "QQQ|1Day": _c_bars([500.0, 499.0], SESS)},
         "positions": [],
         "tensor_fires": {"ACME": {"family": "swing", "date": "2026-10-22"}},
         "alt_data": {"ACME": dict(alt)}, "vix": 25.0,
         "extra": {"enh24_journal": []}}
    if extra:
        v["extra"].update(extra)
    return v


def _c_eval(sid, view):
    mod = importlib.import_module(f"laz_sleeves.{sid}")
    return mod.evaluate(view, {"sleeve_id": sid, "state_dir": "/tmp"})


class TestEngineCStaleBar(unittest.TestCase):
    def test_stale_refused_on_fresh_enters_off_restores(self):
        for sid in C_IDS:
            v = _c_view(sid, date(2026, 10, 8))  # last bar 15d before session
            self.assertEqual(_c_eval(sid, v), [], sid)
            recs = [r for r in v["extra"]["enh24_journal"]
                    if r["exp_id"] == EXP24_C and r["sleeve"] == sid]
            self.assertEqual(len(recs), 1, sid)
            self.assertEqual(recs[0]["age_days"], 15, sid)
            off = {f"{sid}_enh24": {"stale_gate": False}}
            o = _c_eval(sid, _c_view(sid, date(2026, 10, 8), off))
            self.assertEqual(len([i for i in o if i["kind"] == "entry"]), 1, sid)
            o = _c_eval(sid, _c_view(sid, SESS))
            self.assertEqual(len([i for i in o if i["kind"] == "entry"]), 1, sid)

    def test_exit_never_gated(self):
        sid = "s_q07w_s78_ml_deep70_glow_ins2"
        v = _c_view(sid, date(2026, 10, 8))
        v["positions"] = [{"symbol": "ACME", "qty": 40, "avg_price": 30.0,
                           "opened_at": "2026-10-05", "sleeve_id": sid}]
        o = _c_eval(sid, v)  # last close 25 <= 0.85*30 stop, on stale bars
        self.assertTrue(any(i["kind"] == "exit" for i in o))


if __name__ == "__main__":
    unittest.main()
