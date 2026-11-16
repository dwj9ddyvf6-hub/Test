"""Blockers: Lazarus batch 4 — Q07 Green/Swing weekly lanes (LAZ4-1).

Family rule (catalog §4.1): Tensor 1W signal of named family (Green /
Swing) in named cap band, named alt-data filters, buy only on a
QQQ-down day within 5 sessions of the signal, exit on 15% stop or at
the horizon (52/78 weeks). 1 slot @ $1,000 standard; exceptions:
s_q07w_s78_sm_cheap5_wcov $1,194, s_q07w_s78_sm_deep70_wcov 2 slots
$2,265. Swing lanes were CSV-off => parked at batch time; the
config roster unparked them on 2026-11-14 and
PARKED-ROSTER-Q07-20261116 aligned the engine SPECS to
parked=False (entries live, exits still managed).
Fail direction: pre-build, adapters3.<id> modules do not exist.
"""
import json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IDS = ["s_q07w_g52_sm_deep70_wcov", "s_q07w_g78_sm_tierA_wcov",
       "s_q07w_g78_sm_deep70_wcov", "s_q07w_g52_ml_tierA_wcov",
       "s_q07w_g78_ml_tierA_wcov", "s_q07w_g52_ml_ats_z1_mom6_wlow",
       "s_q07w_s52_sm_cheap5_wcov", "s_q07w_s52_sm_deep70_wcov",
       "s_q07w_s78_sm_cheap5_wcov", "s_q07w_s78_sm_deep70_wcov"]
GREEN = {"s_q07w_g52_sm_deep70_wcov": ("green", "small", 52),
         "s_q07w_g78_sm_tierA_wcov": ("green", "small", 78),
         "s_q07w_g78_sm_deep70_wcov": ("green", "small", 78),
         "s_q07w_g52_ml_tierA_wcov": ("green", "midlarge", 52),
         "s_q07w_g78_ml_tierA_wcov": ("green", "midlarge", 78),
         "s_q07w_g52_ml_ats_z1_mom6_wlow": ("green", "midlarge", 52)}


def bars(closes, sym_dates=None):
    return [{"t": 1759000000.0 + k * 86400, "o": c, "h": c, "l": c, "c": c, "v": 1000,
             "date": d} for k, (c, d) in enumerate(zip(closes, sym_dates or
             ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"][:len(closes)]))]


def qqq_down():
    return bars([500.0, 495.0])


def fire(sym="ACME", family="green", band="small", date="2026-10-22", price=20.0, **tags):
    f = {"symbol": sym, "family": family, "band": band, "signal_date": date,
         "price": price, "tags": tags}
    return f


def view(fires=(), positions=(), qqq=None, extra_bars=None):
    b = {"QQQ": qqq if qqq is not None else qqq_down()}
    if extra_bars:
        b.update(extra_bars)
    return {"fires": list(fires), "bars": b, "positions": list(positions)}


def ctx(sid, session="2026-10-23", **kw):
    c = {"sleeve_id": sid, "session": session, "now": session + "T15:00:00",
         "equity": 10000.0, "state_dir": "/tmp"}
    c.update(kw)
    return c


def ev(sid, v, c=None):
    import importlib
    mod = importlib.import_module(f"adapters3.{sid}")
    return mod.evaluate(v, c or ctx(sid))


class TestEntries(unittest.TestCase):
    def test_deep70_wcov_entry(self):
        out = ev("s_q07w_g52_sm_deep70_wcov",
                 view([fire(deep70=True, wiki_cov=True)]))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry"); self.assertEqual(out[0]["side"], "buy")
        self.assertEqual(out[0]["symbol"], "ACME")
        self.assertEqual(out[0]["qty"], 50)  # $1,000 slot / $20
        self.assertAlmostEqual(out[0]["stop_price"], 17.0)  # 15% stop

    def test_tierA_wcov_entry_78(self):
        out = ev("s_q07w_g78_sm_tierA_wcov",
                 view([fire(band="small", tier="A", wiki_cov=True)]))
        self.assertEqual(len(out), 1)

    def test_ml_tierA_entry(self):
        out = ev("s_q07w_g52_ml_tierA_wcov",
                 view([fire(band="midlarge", tier_a=True, wiki_views=1200)]))
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["qty"], 50)

    def test_ats_mom6_wlow_entry(self):
        out = ev("s_q07w_g52_ml_ats_z1_mom6_wlow",
                 view([fire(band="midlarge", ats_z=1.4, mom6_pct=0.22, wiki_low=True)]))
        self.assertEqual(len(out), 1)

    def test_cheap5_swing_parked_refuses_entry_but_green_would(self):
        # PARKED-ROSTER-Q07-20261116 (was: parked refuses): the
        # roster unparked this lane on 2026-11-14 and SPECS now
        # matches it, so the same-shaped fire ENTERS.
        out = ev("s_q07w_s52_sm_cheap5_wcov",
                 view([fire(family="swing", price=4.0, wiki_cov=True)]))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")

    def test_swing_deep70_parked_refuses(self):
        # PARKED-ROSTER-Q07-20261116: unparked in SPECS to match
        # the roster, as above; a qualifying fire ENTERS.
        out = ev("s_q07w_s78_sm_deep70_wcov",
                 view([fire(family="swing", deep70=True, wiki_cov=True)]))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")


class TestRefusals(unittest.TestCase):
    def test_no_fires_refuses(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov", view()), [])

    def test_wrong_family_refuses(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(family="cyan", deep70=True, wiki_cov=True)])), [])

    def test_wrong_band_refuses(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(band="midlarge", deep70=True, wiki_cov=True)])), [])

    def test_missing_filter_tag_fails_closed(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(wiki_cov=True)])), [])  # no deep70 evidence
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(deep70=True)])), [])  # no wiki coverage

    def test_filter_false_refuses(self):
        self.assertEqual(ev("s_q07w_g78_sm_tierA_wcov",
                            view([fire(tier="B", wiki_cov=True)])), [])
        self.assertEqual(ev("s_q07w_g52_ml_ats_z1_mom6_wlow",
                            view([fire(band="midlarge", ats_z=0.4, mom6_pct=0.2,
                                       wiki_low=True)])), [])  # ats_z < 1
        self.assertEqual(ev("s_q07w_g52_ml_ats_z1_mom6_wlow",
                            view([fire(band="midlarge", ats_z=1.4, mom6_pct=-0.05,
                                       wiki_low=True)])), [])  # mom6 negative

    def test_qqq_up_day_refuses(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(deep70=True, wiki_cov=True)],
                                 qqq=bars([495.0, 500.0]))), [])

    def test_stale_signal_refuses(self):
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(date="2026-09-01", deep70=True, wiki_cov=True)])), [])

    def test_already_held_refuses_duplicate(self):
        pos = [{"symbol": "ACME", "qty": 10, "avg_price": 20.0, "opened_at": "2026-10-22"}]
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov",
                            view([fire(deep70=True, wiki_cov=True)], pos)), [])

    def test_cheap5_price_gate(self):
        # cheap5 reading is price-based; use the engine directly:
        # price >= $5 fails the cheap5 filter.
        from desk3.lazarus_q07 import passes_filters, SPECS
        self.assertFalse(passes_filters(SPECS["s_q07w_s52_sm_cheap5_wcov"],
                                        fire(family="swing", price=6.0, wiki_cov=True), {}))
        self.assertTrue(passes_filters(SPECS["s_q07w_s52_sm_cheap5_wcov"],
                                       fire(family="swing", price=4.0, wiki_cov=True), {}))


class TestExits(unittest.TestCase):
    def test_stop_exit_15pct(self):
        pos = [{"symbol": "ACME", "qty": 50, "avg_price": 20.0, "opened_at": "2026-10-22"}]
        v = view(positions=pos, extra_bars={"ACME": bars([16.9])})
        out = ev("s_q07w_g52_sm_deep70_wcov", v)
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["side"], "sell"); self.assertEqual(out[0]["qty"], 50)
        self.assertIn("stop_15pct", out[0]["reason"])

    def test_time_exit_52w(self):
        pos = [{"symbol": "ACME", "qty": 50, "avg_price": 20.0, "opened_at": "2025-10-20"}]
        v = view(positions=pos, extra_bars={"ACME": bars([21.0])})
        out = ev("s_q07w_g52_sm_deep70_wcov", v, ctx("s_q07w_g52_sm_deep70_wcov"))
        self.assertEqual(len(out), 1); self.assertIn("horizon_52w", out[0]["reason"])

    def test_time_exit_78w_not_52w(self):
        pos = [{"symbol": "ACME", "qty": 50, "avg_price": 20.0, "opened_at": "2025-10-20"}]
        v = view(positions=pos, extra_bars={"ACME": bars([21.0])})
        self.assertEqual(ev("s_q07w_g78_sm_deep70_wcov", v,
                            ctx("s_q07w_g78_sm_deep70_wcov")), [])  # 52w < 78w horizon

    def test_unparked_swing_still_exits_on_stop(self):
        pos = [{"symbol": "ACME", "qty": 100, "avg_price": 4.0, "opened_at": "2026-10-22"}]
        v = view(positions=pos, extra_bars={"ACME": bars([3.3])})
        out = ev("s_q07w_s52_sm_cheap5_wcov", v, ctx("s_q07w_s52_sm_cheap5_wcov"))
        self.assertEqual(len(out), 1); self.assertIn("stop_15pct", out[0]["reason"])

    def test_held_no_exit_due(self):
        pos = [{"symbol": "ACME", "qty": 50, "avg_price": 20.0, "opened_at": "2026-10-22"}]
        v = view(positions=pos, extra_bars={"ACME": bars([20.5])})
        self.assertEqual(ev("s_q07w_g52_sm_deep70_wcov", v), [])


class TestRegistryConfig(unittest.TestCase):
    def test_all_ids_distinct_specs(self):
        from desk3.lazarus_q07 import SPECS
        # Shared engine: later Q07 batches (5/6) add their own SPECS to
        # desk3.lazarus_q07 — batch 4's lanes must all be present with
        # distinct specs (subset, not equality; LAZ-B5 note).
        for sid in IDS:
            self.assertIn(sid, SPECS)
        self.assertEqual(len({(SPECS[s]["family"], SPECS[s]["band"], SPECS[s]["horizon_w"],
                               tuple(SPECS[s]["filters"])) for s in IDS}), 10)

    def test_config_rows(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {s["id"]: s for s in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, rows)
            r = rows[sid]
            self.assertEqual(r["module"], f"adapters3.{sid}")
            self.assertEqual(tuple(r["inputs"]), ("fires", "bars", "positions"))
        self.assertFalse(rows["s_q07w_g52_sm_deep70_wcov"]["parked"])
        # UNPARK-REGISTRY-20261114 (owner's all-sleeves-firing
        # order): unparked, was parked with no reason recorded.
        self.assertFalse(rows["s_q07w_s52_sm_cheap5_wcov"]["parked"])
        self.assertEqual(rows["s_q07w_s78_sm_cheap5_wcov"]["slice"]["capital_usd"], 1194.0)
        self.assertEqual(rows["s_q07w_s78_sm_deep70_wcov"]["slice"]["capital_usd"], 2265.0)

    def test_adapter_inputs_match_config(self):
        import importlib
        for sid in IDS:
            m = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(m.INPUTS, ("fires", "bars", "positions"))
            self.assertEqual(m.SLEEVE_ID, sid)


if __name__ == "__main__":
    unittest.main()
