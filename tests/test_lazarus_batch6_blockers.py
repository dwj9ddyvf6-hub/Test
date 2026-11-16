"""Lazarus batch-6 blockers (LAZ-B6): the ten Q07 alt-data confluence
lanes. No v2 oracle exists (authored for v3); the oracle is the catalog
section 4.1 family rule itself, driven as fixtures: entry fires only
when family/band/filters pass, QQQ is down, and the signal is <=5
sessions old; refusals refuse (stale signal, QQQ up, each filter,
wrong band, occupied slot); exits fire on the 15% stop and at the
52/78-week horizon; entries carry stop + time exit-rule DATA.

Fail direction: on the pre-build tree adapters3.<lane> does not exist,
so every drive errors.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IDS = ["s_q07w_g52_sm_ins2_wcov", "s_q07w_g78_mi_cheap5_deep70_ins2",
       "s_q07w_g52_ml_ins2_wlow", "s_q07w_s78_sm_cheap5_ins2_vix20",
       "s_q07w_s52_sm_cheap5_ins2_vix20", "s_q07w_s78_mi_cheap5_ins2_mom6",
       "s_q07w_s78_ml_deep70_ins2_vix20", "s_q07w_s52_ml_deep70_ins2_vix20",
       "s_q07w_s78_sm_deep70_ins2", "s_q07w_s52_sm_cheap5_deep70_ins2"]
TODAY = date(2026, 10, 23)  # Friday


def bars(sym_closes, days=300, start_high=None):
    out, d = [], TODAY - timedelta(days=days)
    for i, c in enumerate(sym_closes):
        out.append({"t": (d + timedelta(days=i)).isoformat(),
                    "o": c, "h": max(c, start_high or c), "l": c,
                    "c": c, "v": 1000})
    return out


def series(n, last, first=None, high=None):
    first = last if first is None else first
    closes = [first + (last - first) * i / max(n - 1, 1) for i in range(n)]
    return bars(closes, days=n, start_high=high)


def qqq(down=True):
    closes = [500.0] * 298 + [500.0, 495.0 if down else 505.0]
    return {"QQQ|1day": bars(closes)}


def drive(sid, fire=None, sym_bars=None, down=True, vix=25.0,
          positions=None, extra_over=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    b = qqq(down)
    if sym_bars:
        b.update(sym_bars)
    extra = {"sleeve_fires": [fire] if fire else [], "vix": vix}
    if extra_over:
        extra.update(extra_over)
    view = {"now": "2026-10-23T15:00:00-04:00", "bars": b,
            "positions": positions or [],
            "slice": {"capital_usd": 1000.0, "cash_usd": 1000.0},
            "params": {}, "extra": extra, "session_fills": []}
    ctx = {"state_dir": tempfile.mkdtemp(prefix="laz6-"),
           "sleeve_id": sid, "cycle_id": "fixture"}
    return mod.evaluate(view, ctx)


def fire(sid, sym="ABC", band="sm", ins=3, wiki=5000, sig_days=2,
         mcap=1_000_000_000):
    return {"sleeve": sid, "symbol": sym, "cap_band": band,
            "insider_buys": ins, "wiki_views_30d": wiki,
            "signal_date": (TODAY - timedelta(days=sig_days)).isoformat(),
            "mcap_usd": mcap}


class TestEntries(unittest.TestCase):
    def test_wcov_entry(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid), {"ABC|1day": series(300, 20.0)})
        self.assertEqual(len(out), 1)
        i = out[0]
        self.assertEqual((i.kind, i.symbol, i.qty), ("enter", "ABC", 50))
        self.assertEqual(i.stop, 17.0)
        self.assertEqual([r.kind for r in i.exit_rules], ["stop", "time_bars"])
        self.assertEqual(i.exit_rules[1].value, 260.0)

    def test_cheap5_deep70_ins2_entry(self):
        sid = "s_q07w_s52_sm_cheap5_deep70_ins2"
        sb = {"ABC|1day": series(300, 3.0, high=10.0)}
        out = drive(sid, fire(sid), sb)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].qty, 333)

    def test_mom6_entry(self):
        sid = "s_q07w_s78_mi_cheap5_ins2_mom6"
        sb = {"ABC|1day": series(300, 4.0, first=2.0)}
        out = drive(sid, fire(sid, band="mi", mcap=100_000_000), sb)
        self.assertEqual(len(out), 1)

    def test_ins2_wlow_entry_low_wiki(self):
        sid = "s_q07w_g52_ml_ins2_wlow"
        f = fire(sid, band="ml", wiki=100, mcap=5_000_000_000)
        out = drive(sid, f, {"ABC|1day": series(300, 40.0)})
        self.assertEqual(len(out), 1)

    def test_vix20_entry_when_vix_high(self):
        sid = "s_q07w_s78_sm_cheap5_ins2_vix20"
        out = drive(sid, fire(sid), {"ABC|1day": series(300, 4.0)},
                    vix=22.0)
        self.assertEqual(len(out), 1)


class TestRefusals(unittest.TestCase):
    def test_qqq_up_refuses(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid), {"ABC|1day": series(300, 20.0)},
                    down=False)
        self.assertEqual(out, [])

    def test_stale_signal_refuses(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid, sig_days=20),
                    {"ABC|1day": series(300, 20.0)})
        self.assertEqual(out, [])

    def test_ins2_filter_refuses(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid, ins=1),
                    {"ABC|1day": series(300, 20.0)})
        self.assertEqual(out, [])

    def test_wcov_filter_refuses(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid, wiki=0),
                    {"ABC|1day": series(300, 20.0)})
        self.assertEqual(out, [])

    def test_wlow_filter_refuses_high_wiki(self):
        sid = "s_q07w_g52_ml_ins2_wlow"
        f = fire(sid, band="ml", wiki=9000, mcap=5_000_000_000)
        self.assertEqual(drive(sid, f, {"ABC|1day": series(300, 40.0)}), [])

    def test_cheap5_refuses_at_6(self):
        sid = "s_q07w_s78_sm_cheap5_ins2_vix20"
        out = drive(sid, fire(sid), {"ABC|1day": series(300, 6.0)})
        self.assertEqual(out, [])

    def test_deep70_refuses_shallow(self):
        sid = "s_q07w_s78_sm_deep70_ins2"
        sb = {"ABC|1day": series(300, 9.0, high=10.0)}
        self.assertEqual(drive(sid, fire(sid), sb), [])

    def test_vix20_refuses_low_vix(self):
        sid = "s_q07w_s52_ml_deep70_ins2_vix20"
        f = fire(sid, band="ml", mcap=5_000_000_000)
        sb = {"ABC|1day": series(300, 20.0, high=40.0)}
        self.assertEqual(drive(sid, f, sb, vix=15.0), [])

    def test_mom6_refuses_downtrend(self):
        sid = "s_q07w_s78_mi_cheap5_ins2_mom6"
        sb = {"ABC|1day": series(300, 4.0, first=4.9)}
        f = fire(sid, band="mi", mcap=100_000_000)
        self.assertEqual(drive(sid, f, sb), [])

    def test_wrong_band_refuses(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        f = fire(sid, band="ml", mcap=5_000_000_000)
        self.assertEqual(drive(sid, f, {"ABC|1day": series(300, 20.0)}), [])

    def test_no_fire_refuses(self):
        sid = "s_q07w_g78_mi_cheap5_deep70_ins2"
        self.assertEqual(drive(sid, None, {}), [])


class TestExits(unittest.TestCase):
    def _pos(self, avg=20.0, opened="2026-10-20", qty=50):
        return [{"symbol": "ABC", "qty": qty, "avg_price": avg,
                 "opened_at": opened}]

    def test_stop_exit(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, None, {"ABC|1day": series(300, 16.0)},
                    positions=self._pos())
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0].kind, out[0].reason),
                         ("exit", "q07_stop15"))

    def test_horizon_exit_52(self):
        sid = "s_q07w_s52_sm_cheap5_deep70_ins2"
        out = drive(sid, None, {"ABC|1day": series(300, 3.0)},
                    positions=self._pos(avg=3.0, opened="2025-10-01"))
        self.assertEqual([o.reason for o in out], ["q07_horizon_exit"])

    def test_no_horizon_exit_at_52_for_78_lane(self):
        sid = "s_q07w_s78_sm_deep70_ins2"
        out = drive(sid, None, {"ABC|1day": series(300, 20.0)},
                    positions=self._pos(opened="2025-10-01"))
        self.assertEqual(out, [])

    def test_occupied_slot_blocks_entry(self):
        sid = "s_q07w_g52_sm_ins2_wcov"
        out = drive(sid, fire(sid, sym="XYZ"),
                    {"ABC|1day": series(300, 20.0),
                     "XYZ|1day": series(300, 10.0)},
                    positions=self._pos())
        self.assertEqual(out, [])


class TestRegistryRows(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.lazarus_batch6 import config_rows, PRODUCERS
        rows = {r["id"]: r for r in config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have)
            self.assertEqual(have[sid]["inputs"], rows[sid]["inputs"])
            mod = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(mod.INPUTS, rows[sid]["inputs"])
        self.assertIn("sleeve_fires", PRODUCERS["sleeve_feed"][0])

    def test_specs_are_distinct(self):
        specs = set()
        for sid in IDS:
            mod = importlib.import_module(f"adapters3.{sid}")
            s = mod.SPEC
            specs.add((s["family"], s["horizon_wk"], s["band"],
                       tuple(s["filters"])))
        self.assertEqual(len(specs), len(IDS))


if __name__ == "__main__":
    unittest.main()
