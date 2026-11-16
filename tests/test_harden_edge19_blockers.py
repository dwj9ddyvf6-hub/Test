"""EDGE-19 blockers (Harden+Enhance Edge pass batch 19).

ENH19 decision changes (default ON; OFF restores pre-change exactly):
- desk3/lazarus.py x6 (s_1wc_micro, s_1wc_ml, s_1wg_small, s_1wlab,
  s_1wsw, s_1wsw_stress): fresh-price entry-bound revalidation --
  refuse entry when the execution (fresh) price is already >= the
  fire's target_price, or breaches the spec max_price that was
  pre-change checked only on the stale fire print.
- desk3/lazarus_midna.py s_mn_d_green_band: band gate + sizing off
  the fresh bar close, not the up-to-10-day-old fire print.
- laz_sleeves s_cl_qm_small (8 slots) + s_mn_hourly (12 slots):
  slot-count cure -- pre-change the break test used the fixed held
  count and emitted one entry per qualifying symbol, over the book.
- laz_sleeves s_cl_vmr_qqq + s_mn_hedge and sleeves/s_mn_faber:
  stale-bar entry gate -- refuse entries sized off a decision bar
  >4 calendar days before the session; exits untouched.

Fail direction: on the pre-ENH19 tree the *_on refusal/cap cases
emit (no such code), so these tests fail there.
"""
import importlib, os, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
NOW = "2026-10-23T14:00:00+00:00"


def bars(sym, closes, tf="1Day", start="2026-10-20"):
    return {f"{sym}|{tf}": [{"t": start, "o": c, "h": c, "l": c, "c": c}
                            for c in closes]}


class TestLazarusBoundGuard(unittest.TestCase):
    def _view(self, sid, fire, bmap, extra=None):
        ex = {"enh19_journal": []}
        ex.update(extra or {})
        return {"now": NOW, "positions": [], "lazarus_fires": [fire],
                "bars": bmap, "extra": ex}

    def test_target_passed_refused_on(self):
        mod = importlib.import_module("adapters3.laz_s_1wc_micro")
        fire = {"sleeve_id": "s_1wc_micro", "symbol": "AAA",
                "fired_at": "2026-10-22T14:00:00+00:00", "price": 10.0,
                "target_price": 11.0, "family": "cyan",
                "signal_tier": "A", "cap_tier": "micro"}
        v = self._view("s_1wc_micro", fire, bars("AAA", [12.0, 12.5]))
        self.assertEqual(mod.evaluate(v, {}), [])
        self.assertEqual(v["extra"]["enh19_journal"][0]["enhanced"],
                         "refuse_bound")

    def test_target_passed_enters_off(self):
        mod = importlib.import_module("adapters3.laz_s_1wc_micro")
        fire = {"sleeve_id": "s_1wc_micro", "symbol": "AAA",
                "fired_at": "2026-10-22T14:00:00+00:00", "price": 10.0,
                "target_price": 11.0, "family": "cyan",
                "signal_tier": "A", "cap_tier": "micro"}
        v = self._view("s_1wc_micro", fire, bars("AAA", [12.0, 12.5]),
                       {"s_1wc_micro_enh19": {"bound_guard": False}})
        out = mod.evaluate(v, {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)
        self.assertEqual(out[0]["qty"], 80)  # sized off fresh 12.50

    def test_below_target_still_enters_on(self):
        mod = importlib.import_module("adapters3.laz_s_1wlab")
        fire = {"sleeve_id": "s_1wlab", "symbol": "BBB",
                "fired_at": "2026-10-22T14:00:00+00:00", "price": 10.0,
                "target_price": 20.0, "family": "cyan"}
        v = self._view("s_1wlab", fire, bars("BBB", [11.0, 12.0]))
        out = mod.evaluate(v, {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)

    def test_max_price_rechecked_on_fresh(self):
        mod = importlib.import_module("adapters3.s_1wsw_stress")
        fire = {"sleeve_id": "s_1wsw_stress", "symbol": "CCC",
                "fired_at": "2026-10-22T14:00:00+00:00", "price": 4.0,
                "family": "swing", "tags": {"deep": True, "vix": 25.0}}
        v = self._view("s_1wsw_stress", fire, bars("CCC", [5.5, 6.0]))
        self.assertEqual(mod.evaluate(v, {}), [])
        v2 = self._view("s_1wsw_stress", fire, bars("CCC", [5.5, 6.0]),
                        {"s_1wsw_stress_enh19": {"bound_guard": False}})
        self.assertEqual(
            len([i for i in mod.evaluate(v2, {}) if i["kind"] == "entry"]), 1)


class TestGreenBandReprice(unittest.TestCase):
    def _view(self, close, extra=None):
        ex = dict(extra or {})
        return {"now": NOW, "positions": [],
                "midna_fires": [{"sleeve_id": "s_mn_d_green_band",
                                 "family": "green", "timeframe": "1D",
                                 "date": "2026-10-23", "price": 15.0,
                                 "symbol": "AAA"}],
                "bars": bars("AAA", [close]), "extra": ex}

    def test_out_of_band_fresh_refused_on(self):
        mod = importlib.import_module("adapters3.s_mn_d_green_band")
        self.assertEqual(mod.evaluate(self._view(25.0), {}), [])

    def test_out_of_band_fresh_enters_off_on_fire_price(self):
        mod = importlib.import_module("adapters3.s_mn_d_green_band")
        v = self._view(25.0, {"s_mn_d_green_band_enh19":
                              {"fresh_price": False}})
        out = mod.evaluate(v, {})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 66)  # 1000 // fire 15.0

    def test_in_band_repriced_on(self):
        mod = importlib.import_module("adapters3.s_mn_d_green_band")
        out = mod.evaluate(self._view(18.0), {})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 55)  # 1000 // fresh 18.0
        self.assertIn("enhance_exp", out[0])


def _qm_view(extra=None):
    bmap = {"QQQ|1Day": [{"t": "2026-10-22", "o": 100, "h": 100, "l": 100, "c": 100},
                         {"t": "2026-10-23", "o": 99, "h": 99, "l": 99, "c": 99}]}
    alt = {}
    for i in range(1, 11):
        sym = f"S{i:02d}"
        rows = [{"t": "2026-10-01", "o": 10, "h": 10.5, "l": 10, "c": 10}
                for _ in range(24)]
        rows.append({"t": "2026-10-23", "o": 11, "h": 11.2, "l": 11, "c": 11})
        bmap[f"{sym}|1Day"] = rows
        alt[sym] = {"mcap_band": "small"}
    v = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
         "bars": bmap, "alt_data": alt}
    if extra:
        v["extra"] = extra
    return v


class TestSlotCountCure(unittest.TestCase):
    def test_qm_capped_on(self):
        mod = importlib.import_module("laz_sleeves.s_cl_qm_small")
        out = mod.evaluate(_qm_view(), {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 8)

    def test_qm_overflow_off(self):
        mod = importlib.import_module("laz_sleeves.s_cl_qm_small")
        v = _qm_view({"s_cl_qm_small_enh19": {"slot_guard": False},
                      "enh19_journal": []})
        out = mod.evaluate(v, {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 10)

    def test_hourly_capped_on(self):
        mod = importlib.import_module("laz_sleeves.s_mn_hourly")
        sig, bmap = {}, {}
        for i in range(1, 16):
            sym = f"S{i:02d}"
            sig[sym] = {"signal": True}
            bmap[f"{sym}|1Hour"] = [{"t": "2026-10-23T14:00:00+00:00",
                                     "o": 10, "h": 10, "l": 10, "c": 10}]
        v = {"now": "2026-10-23T15:00:00+00:00", "positions": [],
             "midna_signals": sig, "bars": bmap}
        out = mod.evaluate(v, {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 12)

    def test_hourly_overflow_off(self):
        mod = importlib.import_module("laz_sleeves.s_mn_hourly")
        sig, bmap = {}, {}
        for i in range(1, 16):
            sym = f"S{i:02d}"
            sig[sym] = {"signal": True}
            bmap[f"{sym}|1Hour"] = [{"t": "2026-10-23T14:00:00+00:00",
                                     "o": 10, "h": 10, "l": 10, "c": 10}]
        v = {"now": "2026-10-23T15:00:00+00:00", "positions": [],
             "midna_signals": sig, "bars": bmap,
             "extra": {"s_mn_hourly_enh19": {"slot_guard": False}}}
        out = mod.evaluate(v, {})
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 15)


def _daily(sym, last_t, close=50.0):
    return {f"{sym}|1Day": [{"t": "2026-10-20", "o": close, "h": close,
                             "l": close, "c": close},
                            {"t": last_t, "o": close, "h": close,
                             "l": close, "c": close}]}


class TestStaleBarGate(unittest.TestCase):
    def test_vmr_stale_refused_on_fresh_enters(self):
        mod = importlib.import_module("laz_sleeves.s_cl_vmr_qqq")
        v = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
             "bars": _daily("QQQ", "2026-10-12"), "vix": 20.0,
             "extra": {"enh19_journal": []}}
        self.assertEqual(mod.evaluate(v, {}), [])
        self.assertEqual(v["extra"]["enh19_journal"][0]["enhanced"],
                         "refuse_stale_bar")
        v2 = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
              "bars": _daily("QQQ", "2026-10-23"), "vix": 20.0}
        self.assertEqual(len(mod.evaluate(v2, {})), 1)

    def test_vmr_stale_enters_off(self):
        mod = importlib.import_module("laz_sleeves.s_cl_vmr_qqq")
        v = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
             "bars": _daily("QQQ", "2026-10-12"), "vix": 20.0,
             "extra": {"s_cl_vmr_qqq_enh19": {"stale_gate": False}}}
        self.assertEqual(len(mod.evaluate(v, {})), 1)

    def test_hedge_stale_refused_on_fresh_enters(self):
        mod = importlib.import_module("laz_sleeves.s_mn_hedge")
        v = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
             "bars": _daily("TZA", "2026-10-12", 20.0), "hedge_signal": True,
             "extra": {"enh19_journal": []}}
        self.assertEqual(mod.evaluate(v, {}), [])
        v2 = {"now": "2026-10-23T14:00:00+00:00", "positions": [],
              "bars": _daily("TZA", "2026-10-23", 20.0), "hedge_signal": True}
        self.assertEqual(len(mod.evaluate(v2, {})), 1)

    def test_faber_stale_refused_on_fresh_enters_off_enters(self):
        mod = importlib.import_module("adapters.s_mn_faber")
        def mk(last_t):
            rows = [{"t": "2026-01-05", "o": 100, "h": 100, "l": 100, "c": 100}
                    for _ in range(209)]
            rows.append({"t": last_t, "o": 110, "h": 110, "l": 110, "c": 110})
            return {"bars": {"SPY": rows}, "positions": []}
        ctx = {"session": "2026-10-23", "now": NOW, "extra": {}}
        self.assertEqual(mod.evaluate(mk("2026-10-01"), dict(ctx)), [])
        out = mod.evaluate(mk("2026-10-23"), dict(ctx))
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)
        ctx_off = {"session": "2026-10-23", "now": NOW,
                    "extra": {"s_mn_faber_enh19": {"stale_gate": False}}}
        out = mod.evaluate(mk("2026-10-01"), ctx_off)
        self.assertEqual(len([i for i in out if i["kind"] == "entry"]), 1)


if __name__ == "__main__":
    unittest.main()
