"""Edge batch 25 blockers (ENH25): rules freshest-first slot allocation,
Q07 stale symbol-bar entry gate, wcov entry and exit traces (the two
wcov lanes were parked at batch time; PARKED-ROSTER-Q07-20261116
unparked them in SPECS to match the config roster), Saty family
verify-only fail-closed traces.

Fail-first: ENH25 tests fail on the pre-cure engines (producer-order
allocation entered the stale fire; stale-bar fixtures entered at the
ancient close). Verify-only traces pin designed behavior.
"""
import importlib
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = "2026-10-23T15:00:00Z"
RULES = ("s_rules_1d", "s_rules_1w")
Q07_SPECS = {
    "s_q07w_s78_sm_cheap5_ins2_vix20": dict(
        id="s_q07w_s78_sm_cheap5_ins2_vix20", family="swing", horizon_wk=78,
        band="sm", filters=("cheap5", "ins2", "vix20")),
    "s_q07w_s78_sm_deep70_ins2": dict(
        id="s_q07w_s78_sm_deep70_ins2", family="swing", horizon_wk=78,
        band="sm", filters=("deep70", "ins2")),
}
WCOV = ("s_q07w_s78_sm_cheap5_wcov", "s_q07w_s78_sm_deep70_wcov")
SATY = ("saty_day", "saty_gpt_v02", "saty_gpt_v03", "saty_magnum",
        "saty_sol", "saty_sol_0dte")


def _rules_view(sid, held_n, old_ts, enh25=None):
    from desk3 import lazarus  # noqa: F401  (import guard)
    pos = [{"symbol": f"H{i}", "qty": 10, "avg_price": 10.0,
            "opened_at": "2026-10-23T14:00:00Z"} for i in range(held_n)]
    fires = [
        {"sleeve_id": sid, "symbol": "OLD", "fired_at": old_ts,
         "price": 10.0, "qqq_red": True},
        {"sleeve_id": sid, "symbol": "NEW", "fired_at": "2026-10-23T14:30:00Z",
         "price": 10.0, "qqq_red": True},
    ]
    extra = {"enh25_journal": []}
    if enh25 is not None:
        extra[f"{sid}_enh25"] = enh25
    return {"now": NOW, "positions": pos, "lazarus_fires": fires,
            "extra": extra, "bars": {}}


def _rules_eval(sid, view):
    from desk3 import lazarus
    return lazarus.evaluate(sid, view,
                            {"now": NOW, "state_dir": tempfile.mkdtemp()})


class TestRulesFreshFirst(unittest.TestCase):
    def test_1w_last_slot_goes_to_fresh_fire(self):
        v = _rules_view("s_rules_1w", 5, "2026-10-16T14:00:00Z")
        out = _rules_eval("s_rules_1w", v)
        entries = [o for o in out if o["kind"] == "entry"]
        self.assertEqual([e["symbol"] for e in entries], ["NEW"])
        recs = [r for r in v["extra"]["enh25_journal"]
                if r["exp_id"] == "ENH25-RULES-FRESH-20261024"]
        self.assertTrue(recs and recs[0]["control_first"] == "OLD"
                        and recs[0]["treatment_first"] == "NEW")

    def test_1w_off_restores_producer_order(self):
        v = _rules_view("s_rules_1w", 5, "2026-10-16T14:00:00Z",
                        {"fresh_first": False})
        out = _rules_eval("s_rules_1w", v)
        entries = [o for o in out if o["kind"] == "entry"]
        self.assertEqual([e["symbol"] for e in entries], ["OLD"])

    def test_1d_order_fresh_first_on_producer_order_off(self):
        v = _rules_view("s_rules_1d", 0, "2026-10-21T16:00:00Z")
        out = _rules_eval("s_rules_1d", v)
        self.assertEqual([o["symbol"] for o in out], ["NEW", "OLD"])
        v = _rules_view("s_rules_1d", 0, "2026-10-21T16:00:00Z",
                        {"fresh_first": False})
        out = _rules_eval("s_rules_1d", v)
        self.assertEqual([o["symbol"] for o in out], ["OLD", "NEW"])


def _weekdays(start, end):
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _bars(days, close, high=None):
    return [{"t": f"{d.isoformat()}T04:00:00Z", "o": close,
             "h": high or close, "l": close, "c": close, "v": 1000}
            for d in days]


QQQ_DAYS = _weekdays(date(2026, 9, 1), date(2026, 10, 23))
QQQ = [{"t": f"{d.isoformat()}T04:00:00Z", "o": 100.0, "h": 100.0,
        "l": 99.0, "c": 99.0 if d == date(2026, 10, 23) else 100.0,
        "v": 1000} for d in QQQ_DAYS]
STALE_DAYS = _weekdays(date(2026, 8, 3), date(2026, 9, 25))
FRESH_DAYS = _weekdays(date(2026, 8, 3), date(2026, 10, 23))


def _q07_view(sid, days, close, high, enh=None):
    extra = {"sleeve_fires": [{"sleeve": sid, "symbol": "XYZ",
                               "signal_date": "2026-10-23", "cap_band": "sm",
                               "insider_buys": 3}],
             "vix": 25.0, "q07_exp_journal": {"records": []}}
    if enh is not None:
        extra["q07_enh"] = {sid: enh}
    return {"now": NOW,
            "bars": {"QQQ|1day": QQQ, "XYZ|1day": _bars(days, close, high)},
            "positions": [], "extra": extra}


class TestQ07StaleBars(unittest.TestCase):
    def _run(self, sid, days, enh=None):
        from desk3.q07_engine import evaluate_q07
        close, high = (4.0, 4.0) if "cheap5" in sid else (6.0, 10.0)
        v = _q07_view(sid, days, close, high, enh)
        return evaluate_q07(Q07_SPECS[sid], v, {}), v

    def test_stale_bars_refused_on(self):
        for sid in Q07_SPECS:
            out, v = self._run(sid, STALE_DAYS)
            self.assertEqual([o for o in out if o.kind == "enter"], [], sid)
            recs = [r for r in v["extra"]["q07_exp_journal"]["records"]
                    if r["exp_id"] == "ENH25-Q07-STALEBARS-20261024"]
            self.assertTrue(recs and recs[0]["treatment_enter"] is False, sid)

    def test_stale_bars_off_restores_prechange_entry(self):
        for sid in Q07_SPECS:
            out, _ = self._run(sid, STALE_DAYS, {"fresh_bars": False})
            self.assertEqual(len([o for o in out if o.kind == "enter"]), 1, sid)

    def test_fresh_bars_enter_unchanged(self):
        for sid in Q07_SPECS:
            out, _ = self._run(sid, FRESH_DAYS)
            self.assertEqual(len([o for o in out if o.kind == "enter"]), 1, sid)


class TestWcovParkedTraces(unittest.TestCase):
    def test_parked_no_entries_stop_exit_fires(self):
        # PARKED-ROSTER-Q07-20261116 (was: parked, no entries): both
        # WCOV lanes are unparked in SPECS to match the config roster
        # (unparked 2026-11-14), so a qualifying fire now ENTERS;
        # the stop-exit trace below is unchanged.
        from desk3.lazarus_q07 import evaluate_sleeve
        for sid in WCOV:
            tags = {"wiki_cov": True}
            if "deep70" in sid:
                tags["deep70"] = True
            fire = {"symbol": "ABC", "family": "swing", "band": "small",
                    "signal_date": "2026-10-23", "price": 4.0,
                    "tags": tags}
            v = {"fires": [fire],
                 "bars": {"ABC": [{"c": 4.0}] * 3,
                          "QQQ": [{"c": 100.0}, {"c": 99.0}]},
                 "positions": []}
            out = evaluate_sleeve(sid, v, {"session": "2026-10-23",
                                           "now": "2026-10-23"})
            self.assertEqual(
                len([i for i in out if i["kind"] == "entry"]), 1, sid)
            v2 = {"fires": [], "bars": {"ABC": [{"c": 8.0}]},
                  "positions": [{"symbol": "ABC", "qty": 10,
                                 "avg_price": 10.0, "opened_at": "2026-10-01"}]}
            out = evaluate_sleeve(sid, v2, {"session": "2026-10-23",
                                            "now": "2026-10-23"})
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["kind"], "exit", sid)
            self.assertIn("stop_15pct", out[0]["reason"], sid)


class TestSatyVerifyOnlyTraces(unittest.TestCase):
    def test_saty_family_fails_closed_on_empty_view(self):
        for sid in SATY:
            if sid == "saty_day":
                mod = importlib.import_module("desk_sleeves.saty_day")
                out = mod.evaluate(
                    {"now": NOW, "bars": {}, "positions": [], "extra": {}},
                    {"sleeve_id": sid, "state_dir": tempfile.mkdtemp(),
                     "cycle_id": "fix", "snapshot_hash": "fix"})
            else:
                mod = importlib.import_module(f"adapters3.{sid}")
                out = mod.evaluate(
                    {"now": NOW,
                     "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}},
                    {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()})
            self.assertEqual(out, [], sid)


if __name__ == "__main__":
    unittest.main()
