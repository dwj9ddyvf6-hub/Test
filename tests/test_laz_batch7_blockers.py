"""Blockers LAZ-B7: Lazarus batch 7 (Q07 swing x5, ChartsLector x2,
Midna ports x3). Fixture drives prove entry, each designed exit, and
refusals through the v3 evaluate(view, ctx) interface; registry +
config rows asserted; Q07 lanes parked per source status (Disabled)."""
import importlib, json, os, sys, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IDS = ["s_q07w_s78_ml_deep70_glow_ins2", "s_q07w_s52_ml_ins2_mom6_vix20",
       "s_q07w_s52_ml_ins2_mom6_wlow", "s_q07w_s78_mi_ats_z1_cheap5",
       "s_q07w_s78_mi_ats_z1_mom6", "s_cl_qm_small", "s_cl_vmr_qqq",
       "s_mn_hourly", "s_mn_nostop", "s_mn_hedge"]
NOW = "2026-10-23T15:30:00-04:00"


def _b(t, c, v=10000.0, h=None, l=None):
    return {"t": t, "o": c, "h": h if h is not None else c * 1.001,
            "l": l if l is not None else c * 0.999, "c": c, "v": v}


def _daily(closes, end=date(2026, 10, 23)):
    days, d = [], end
    while len(days) < len(closes):
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    return [_b(f"{x.isoformat()}T04:00:00Z", float(c)) for x, c in zip(days, closes)]


def _hourly(n, price=50.0, end_day=date(2026, 10, 23)):
    out, d, made = [], end_day, 0
    days = []
    while made < (n // 7 + 2):
        if d.weekday() < 5:
            days.append(d); made += 1
        d -= timedelta(days=1)
    for day in sorted(days):
        for k in range(7):
            out.append(_b(f"{day.isoformat()}T{13 + k:02d}:30:00Z", price))
    return out[-n:]


def _qqq(down=True):
    return _daily([500.0, 499.0] if down else [499.0, 500.0])


def _view(**kw):
    v = {"now": NOW, "bars": {}, "positions": [], "slice":
         {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    v.update(kw)
    return v


def ev(sid, view):
    mod = importlib.import_module(f"laz_sleeves.{sid}")
    return mod.evaluate(view, {"sleeve_id": sid, "state_dir": "/tmp"})


def _q07_view(sid_filters, closes, fire_age_days=1, qqq_down=True, alt=None):
    fire_date = (date(2026, 10, 23) - timedelta(days=fire_age_days)).isoformat()
    v = _view(bars={"ACME|1Day": _daily(closes), "QQQ|1Day": _qqq(qqq_down)},
              tensor_fires={"ACME": {"family": "swing", "date": fire_date}},
              alt_data={"ACME": alt or {}})
    return v


class TestQ07(unittest.TestCase):
    def test_deep70_glow_ins2_entry_and_refusals(self):
        closes = [100.0] * 130 + [25.0]  # 75% below the 252d high zone
        alt = {"insider_buys": 3, "gamma_low": True, "mcap_band": "midlarge"}
        out = ev("s_q07w_s78_ml_deep70_glow_ins2", _q07_view(None, closes, alt=alt))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "ACME")
        # refusal: only 1 insider buy
        bad = dict(alt, insider_buys=1)
        self.assertEqual(ev("s_q07w_s78_ml_deep70_glow_ins2",
                            _q07_view(None, closes, alt=bad)), [])
        # refusal: QQQ up day (house rule)
        self.assertEqual(ev("s_q07w_s78_ml_deep70_glow_ins2",
                            _q07_view(None, closes, qqq_down=False, alt=alt)), [])
        # refusal: stale fire (>5 sessions window)
        self.assertEqual(ev("s_q07w_s78_ml_deep70_glow_ins2",
                            _q07_view(None, closes, fire_age_days=20, alt=alt)), [])
        # refusal: not deep (price near highs)
        self.assertEqual(ev("s_q07w_s78_ml_deep70_glow_ins2",
                            _q07_view(None, [100.0] * 131, alt=alt)), [])

    def test_deep70_stop_and_time_exits(self):
        closes = [100.0] * 130 + [25.0]
        alt = {"insider_buys": 3, "gamma_low": True, "mcap_band": "midlarge"}
        v = _q07_view(None, closes, alt=alt)
        v["positions"] = [{"symbol": "ACME", "qty": 40, "avg_price": 30.0,
                           "opened_at": "2026-10-20", "sleeve_id":
                           "s_q07w_s78_ml_deep70_glow_ins2"}]
        out = ev("s_q07w_s78_ml_deep70_glow_ins2", v)  # 25 <= 0.85*30 stop
        self.assertTrue(any(i["kind"] == "exit" for i in out))
        # time exit: opened 400 sessions ago, price above stop
        v2 = _q07_view(None, [100.0] * 500, alt=alt)
        v2["positions"] = [{"symbol": "ACME", "qty": 10, "avg_price": 90.0,
                            "opened_at": "2025-01-02", "sleeve_id":
                            "s_q07w_s78_ml_deep70_glow_ins2"}]
        out2 = ev("s_q07w_s78_ml_deep70_glow_ins2", v2)
        self.assertTrue(any(i["kind"] == "exit" and "time" in i["reason"]
                            for i in out2))

    def test_ins2_mom6_vix20(self):
        closes = [50.0 + i * 0.2 for i in range(140)]  # rising => mom6 > 0
        alt = {"insider_buys": 2, "mcap_band": "midlarge"}
        v = _q07_view(None, closes, alt=alt); v["vix"] = 25.0
        self.assertEqual(len(ev("s_q07w_s52_ml_ins2_mom6_vix20", v)), 1)
        v["vix"] = 15.0  # VIX gate refuses
        self.assertEqual(ev("s_q07w_s52_ml_ins2_mom6_vix20", v), [])

    def test_ins2_mom6_wlow(self):
        closes = [50.0 + i * 0.2 for i in range(140)]
        alt = {"insider_buys": 2, "mcap_band": "midlarge", "wiki": "low"}
        self.assertEqual(len(ev("s_q07w_s52_ml_ins2_mom6_wlow",
                                _q07_view(None, closes, alt=alt))), 1)
        alt2 = dict(alt, wiki="spike")
        self.assertEqual(ev("s_q07w_s52_ml_ins2_mom6_wlow",
                            _q07_view(None, closes, alt=alt2)), [])

    def test_ats_cheap5_and_mom6(self):
        alt = {"ats_z": 1.5, "mcap_band": "micro"}
        self.assertEqual(len(ev("s_q07w_s78_mi_ats_z1_cheap5",
                                _q07_view(None, [4.0] * 140, alt=alt))), 1)
        # cheap5 refuses at $6
        self.assertEqual(ev("s_q07w_s78_mi_ats_z1_cheap5",
                            _q07_view(None, [6.0] * 140, alt=alt)), [])
        closes = [10.0 + i * 0.1 for i in range(140)]
        self.assertEqual(len(ev("s_q07w_s78_mi_ats_z1_mom6",
                                _q07_view(None, closes, alt=alt))), 1)
        alt3 = dict(alt, ats_z=0.4)  # no dark-pool spike
        self.assertEqual(ev("s_q07w_s78_mi_ats_z1_mom6",
                            _q07_view(None, closes, alt=alt3)), [])


class TestCL(unittest.TestCase):
    def test_qm_small_breakout_entry_and_time_exit(self):
        closes = [10.0] * 25 + [12.0]  # breakout over prior 20d high, >= $5
        v = _view(bars={"SMCO|1Day": _daily(closes), "QQQ|1Day": _qqq(True)},
                  alt_data={"SMCO": {"mcap_band": "small"}})
        out = ev("s_cl_qm_small", v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "SMCO")
        # refusal: QQQ up day
        v2 = _view(bars={"SMCO|1Day": _daily(closes), "QQQ|1Day": _qqq(False)},
                   alt_data={"SMCO": {"mcap_band": "small"}})
        self.assertEqual(ev("s_cl_qm_small", v2), [])
        # time exit at 90 sessions, NO stop (price crash does not exit early)
        v3 = _view(bars={"SMCO|1Day": _daily([12.0] * 95), "QQQ|1Day": _qqq()})
        v3["positions"] = [{"symbol": "SMCO", "qty": 80, "avg_price": 12.0,
                            "opened_at": "2026-06-01", "sleeve_id": "s_cl_qm_small"}]
        out3 = ev("s_cl_qm_small", v3)
        self.assertTrue(any(i["kind"] == "exit" for i in out3))

    def test_vmr_qqq(self):
        v = _view(bars={"QQQ|1Day": _qqq()}, vix=30.0)
        out = ev("s_cl_vmr_qqq", v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "QQQ")
        v["vix"] = 40.0  # mood ring above 35 refuses
        self.assertEqual(ev("s_cl_vmr_qqq", v), [])
        v2 = _view(bars={"QQQ|1Day": _daily([500.0] * 10)}, vix=30.0)
        v2["positions"] = [{"symbol": "QQQ", "qty": 2, "avg_price": 480.0,
                            "opened_at": "2026-10-14", "sleeve_id": "s_cl_vmr_qqq"}]
        self.assertTrue(any(i["kind"] == "exit" for i in ev("s_cl_vmr_qqq", v2)))


class TestMidna(unittest.TestCase):
    def _mn_view(self, price=50.0, n=70):
        return _view(bars={"ACME|1Hour": _hourly(n, price)},
                     midna_signals={"ACME": {"signal": True}})

    def test_hourly_entry_stop_time(self):
        out = ev("s_mn_hourly", self._mn_view())
        self.assertEqual(len(out), 1)
        v = self._mn_view(); v["midna_signals"] = {}
        self.assertEqual(ev("s_mn_hourly", v), [])  # no signal, no entry
        # stop exit: entry 50, last close 40 (hourly bars all at 40)
        v2 = self._mn_view(price=40.0)
        v2["positions"] = [{"symbol": "ACME", "qty": 20, "avg_price": 50.0,
                            "opened_at": "2026-10-23T13:30:00Z",
                            "sleeve_id": "s_mn_hourly"}]
        self.assertTrue(any(i["kind"] == "exit" and "stop" in i["reason"]
                            for i in ev("s_mn_hourly", v2)))
        # time exit: opened 61+ bars ago at same price
        v3 = self._mn_view(price=50.0, n=70)
        v3["positions"] = [{"symbol": "ACME", "qty": 20, "avg_price": 50.0,
                            "opened_at": "2026-10-08T13:30:00Z",
                            "sleeve_id": "s_mn_hourly"}]
        self.assertTrue(any(i["kind"] == "exit" and "time" in i["reason"]
                            for i in ev("s_mn_hourly", v3)))

    def test_nostop_has_no_stop_but_time_exit(self):
        v = self._mn_view(price=40.0)  # -20%: nostop must NOT stop out
        v["positions"] = [{"symbol": "ACME", "qty": 20, "avg_price": 50.0,
                           "opened_at": "2026-10-23T13:30:00Z",
                           "sleeve_id": "s_mn_nostop"}]
        self.assertEqual(ev("s_mn_nostop", v), [])
        v2 = self._mn_view(price=40.0, n=70)
        v2["positions"] = [{"symbol": "ACME", "qty": 20, "avg_price": 50.0,
                            "opened_at": "2026-10-08T13:30:00Z",
                            "sleeve_id": "s_mn_nostop"}]
        self.assertTrue(any(i["kind"] == "exit" for i in ev("s_mn_nostop", v2)))

    def test_hedge(self):
        v = _view(bars={"TZA|1Day": _daily([20.0] * 30), "QQQ|1Day": _qqq()},
                  hedge_signal=True)
        out = ev("s_mn_hedge", v)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "TZA")
        self.assertEqual(out[0]["qty"], 15)  # 30% of $1,000 budget at $20
        v["hedge_signal"] = False
        self.assertEqual(ev("s_mn_hedge", v), [])
        v2 = _view(bars={"TZA|1Day": _daily([20.0] * 30), "QQQ|1Day": _qqq()},
                   hedge_signal=False)
        v2["positions"] = [{"symbol": "TZA", "qty": 15, "avg_price": 20.0,
                            "opened_at": "2026-10-22", "sleeve_id": "s_mn_hedge"}]
        self.assertTrue(any(i["kind"] == "exit" for i in ev("s_mn_hedge", v2)))


class TestRegistryConfig(unittest.TestCase):
    def test_registry_and_config_rows(self):
        from desk3 import laz_batch7
        rows = {r["id"]: r for r in laz_batch7.config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        for sid in IDS[:5]:
            self.assertTrue(rows[sid]["parked"], sid)  # Q07 source: Disabled
        for sid in IDS[5:]:
            self.assertFalse(rows[sid]["parked"], sid)
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have)
            self.assertEqual(have[sid]["module"], f"laz_sleeves.{sid}")
        led = open(os.path.join(ROOT, "FIDELITY-LEDGER.md")).read()
        for sid in IDS:
            self.assertIn(sid, led)


if __name__ == "__main__":
    unittest.main()
