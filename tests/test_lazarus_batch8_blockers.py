"""Blockers: Lazarus batch 8 (s_mn_* Midna ports) — LAZ8-1.

Sources: lazarus_sleeves_1024.csv rows + SLEEVE-CATALOG-CONSOLIDATED
§4.2 rule table. Every sleeve fixture-drives through its v3 adapter:
entry fires, each designed exit fires, refusals refuse (no data, no
fresh fire/forecast, no options vehicle, spread inside the band,
mid-hold no-churn). Fail direction: on the pre-batch tree none of the
adapters/sleeves exist (imports error).
"""
import json, os, sys, unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EPOCH = date(1970, 1, 1)
START = date(2025, 1, 1)


def bars(closes, start=START, vol=10000):
    out = []
    for i, c in enumerate(closes):
        d = start + timedelta(days=i)
        out.append({"t": float((d - EPOCH).days * 86400), "o": c,
                    "h": c * 1.001, "l": c * 0.999, "c": c, "v": vol})
    return out


def dstr(bar):
    return date.fromtimestamp(bar["t"] + 4 * 3600).isoformat() if False else \
        (EPOCH + timedelta(days=int(bar["t"] // 86400))).isoformat()


def ctx(sid, session="2025-04-10", **kw):
    c = {"sleeve_id": sid, "session": session,
         "now": session + "T15:00:00", "equity": 10000.0}
    c.update(kw)
    return c


def ev(sid, view, c=None):
    import importlib
    return importlib.import_module(f"adapters.{sid}").evaluate(view, c or ctx(sid))


def pos(sym, qty, entry_idx, series_start=START, px=50.0):
    d = series_start + timedelta(days=entry_idx)
    return [{"symbol": sym, "qty": qty, "avg_price": px,
             "opened_at": d.isoformat() + "T15:00:00"}]


class TestMacd(unittest.TestCase):
    def _series(self):
        from sleeves.s_mn_macd import macd_hist
        cl = [100 - 0.3 * i for i in range(45)] + [86.5 + 1.2 * i for i in range(1, 30)]
        h = macd_hist(cl)
        idx = next(i for i in range(35, len(h)) if h[i - 1] <= 0 < h[i])
        return cl[:idx + 1]

    def test_entry_cross_up(self):
        out = ev("s_mn_macd", {"bars": {"AAA": bars(self._series())}, "positions": []})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "AAA")
        self.assertIn("macd_cross_up", out[0]["reason"])

    def test_exit_cross_down_and_refusals(self):
        from sleeves.s_mn_macd import macd_hist
        cl = [50 + 0.4 * i for i in range(45)] + [68 - 1.0 * i for i in range(1, 30)]
        h = macd_hist(cl)
        idx = next(i for i in range(35, len(h)) if h[i - 1] >= 0 > h[i])
        series = bars(cl[:idx + 1])
        p = pos("AAA", 5, 0)
        out = ev("s_mn_macd", {"bars": {"AAA": series}, "positions": p})
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertEqual(ev("s_mn_macd", {"bars": {}, "positions": []}), [])
        flat = bars([100.0] * 60)
        self.assertEqual(ev("s_mn_macd", {"bars": {"AAA": flat}, "positions": []}), [])


class TestVwap(unittest.TestCase):
    def test_entry_and_exit(self):
        up = bars([100.0] * 25 + [110.0])
        out = ev("s_mn_vwap", {"bars": {"AAA": up}, "positions": []})
        self.assertEqual(len(out), 1)
        self.assertIn("cross_above_vwap", out[0]["reason"])
        dn = bars([100.0] * 25 + [90.0])
        out = ev("s_mn_vwap", {"bars": {"AAA": dn}, "positions": pos("AAA", 9, 0)})
        self.assertEqual([o["kind"] for o in out], ["exit"])

    def test_refusal_flat(self):
        self.assertEqual(ev("s_mn_vwap", {"bars": {"AAA": bars([100.0] * 40)},
                                          "positions": []}), [])


class TestFaber(unittest.TestCase):
    UP = [50 + 0.2 * i for i in range(250)]
    DN = [100 - 0.2 * i for i in range(250)]

    def test_entry_above_average_only(self):
        out = ev("s_mn_faber", {"bars": {"SPY": bars(self.UP), "EFA": bars(self.DN)},
                                "positions": []})
        self.assertEqual([o["symbol"] for o in out], ["SPY"])

    def test_exit_below_average(self):
        out = ev("s_mn_faber", {"bars": {"SPY": bars(self.DN)},
                                "positions": pos("SPY", 6, 0)})
        self.assertEqual([o["kind"] for o in out], ["exit"])


class TestReversal(unittest.TestCase):
    def _mk(self, r):
        return bars([100.0] * 10 + [100 * (1 + r)] * 12)

    def test_entry_worst_three(self):
        view = {"bars": {"AAA": self._mk(-0.2), "BBB": self._mk(-0.1),
                         "CCC": self._mk(0.05), "DDD": self._mk(-0.3)},
                "positions": []}
        out = ev("s_mn_reversal", view)
        self.assertEqual([o["symbol"] for o in out], ["DDD", "AAA", "BBB"])

    def test_exit_rotation_and_midhold_refusal(self):
        series = self._mk(-0.2)
        old = pos("AAA", 12, 0)  # entered at series start, 21+ sessions ago
        out = ev("s_mn_reversal", {"bars": {"AAA": series, "EEE": self._mk(-0.4)},
                                   "positions": old})
        self.assertIn("exit", [o["kind"] for o in out])
        young = pos("AAA", 12, 15)
        out = ev("s_mn_reversal", {"bars": {"AAA": series}, "positions": young})
        self.assertEqual(out, [])


class TestPairs(unittest.TestCase):
    BASE = [50 + 0.05 * i for i in range(70)]

    def test_entry_two_legs_and_refusal_inside_band(self):
        ko = self.BASE[:60] + [x * 1.12 for x in self.BASE[60:]]
        out = ev("s_mn_pairs", {"bars": {"KO": bars(ko), "PEP": bars(self.BASE)},
                                "positions": []})
        self.assertEqual(len(out), 2)
        sides = {o["symbol"]: o["position_intent"] for o in out}
        self.assertEqual(sides, {"PEP": "buy_to_open", "KO": "sell_to_open"})
        same = {"bars": {"KO": bars(self.BASE), "PEP": bars(self.BASE)}, "positions": []}
        self.assertEqual(ev("s_mn_pairs", same), [])

    def test_exit_on_reversion(self):
        view = {"bars": {"KO": bars(self.BASE), "PEP": bars(self.BASE)},
                "positions": pos("KO", -8, 0) + pos("PEP", 9, 0)}
        out = ev("s_mn_pairs", view)
        self.assertEqual(sorted(o["kind"] for o in out), ["exit", "exit"])
        pi = {o["symbol"]: o["position_intent"] for o in out}
        self.assertEqual(pi["KO"], "buy_to_close")


class TestMoonshot(unittest.TestCase):
    SERIES = bars([20.0] * 400)

    def _view(self, fires, positions=None):
        return {"bars": {"XYZ": self.SERIES}, "positions": positions or [],
                "fires": fires}

    def test_entry_on_fresh_fire(self):
        f = [{"sleeve_id": "s_mn_moonshot", "symbol": "XYZ", "date": "2025-04-09"}]
        out = ev("s_mn_moonshot", self._view(f))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 50)

    def test_refusals_no_stale_wrong_sleeve(self):
        self.assertEqual(ev("s_mn_moonshot", self._view([])), [])
        stale = [{"sleeve_id": "s_mn_moonshot", "symbol": "XYZ", "date": "2025-01-01"}]
        self.assertEqual(ev("s_mn_moonshot", self._view(stale)), [])
        other = [{"sleeve_id": "s_mn_kronos", "symbol": "XYZ", "date": "2025-04-09"}]
        self.assertEqual(ev("s_mn_moonshot", self._view(other)), [])

    def test_exit_78_weeks(self):
        old = pos("XYZ", 50, 0, px=20.0)
        out = ev("s_mn_moonshot", self._view([], old))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        young = pos("XYZ", 50, 395, px=20.0)
        self.assertEqual(ev("s_mn_moonshot", self._view([], young)), [])


class TestKronos(unittest.TestCase):
    SERIES = bars([25.0] * 60)

    def _fires(self, names, d="2025-04-09"):
        return [{"sleeve_id": "s_mn_kronos", "symbol": s, "date": d,
                 "rank": i + 1} for i, s in enumerate(names)]

    def _view(self, fires, positions=None):
        barsmap = {s: self.SERIES for s in ("AAA", "BBB", "CCC", "DDD", "EEE")}
        return {"bars": barsmap, "positions": positions or [], "fires": fires}

    def test_entry_top4(self):
        out = ev("s_mn_kronos", self._view(self._fires(["AAA", "BBB", "CCC", "DDD", "EEE"])))
        self.assertEqual(sorted(o["symbol"] for o in out), ["AAA", "BBB", "CCC", "DDD"])
        self.assertTrue(all(o["qty"] == 20 for o in out))

    def test_refusal_no_forecast(self):
        self.assertEqual(ev("s_mn_kronos", self._view([])), [])

    def test_exit_after_min_hold_and_hold_before(self):
        old = pos("EEE", 20, 0, px=25.0)
        out = ev("s_mn_kronos", self._view(self._fires(["AAA", "BBB", "CCC", "DDD"]), old))
        self.assertIn("exit", [o["kind"] for o in out])
        young = pos("EEE", 20, 58, px=25.0)
        out = ev("s_mn_kronos", self._view(self._fires(["AAA", "BBB", "CCC", "DDD"]), young))
        self.assertNotIn("EEE", [o["symbol"] for o in out if o["kind"] == "exit"])


def _chain(sym, strike, exp="2025-05-20", typ="call"):
    root = sym
    cp = "C" if typ == "call" else "P"
    occ = f"{root}250520{cp}{int(strike * 1000):08d}"
    return occ, {"symbol": occ, "strike": strike, "expiration": exp, "type": typ}


class TestOptTurtle(unittest.TestCase):
    def test_entry_breakout_call_and_no_vehicle_refusal(self):
        cl = [50.0] * 60 + [60.0]
        occ, contract = _chain("AAA", 60)
        view = {"bars": {"AAA": bars(cl)}, "positions": [],
                "options": {"chains": {"AAA": [contract]},
                            "quotes": {occ: {"bid": 1.9, "ask": 2.0}}}}
        out = ev("s_mn_opt_turtle", view)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], occ)
        self.assertEqual(out[0]["qty"], 5)
        view["options"] = {"chains": {"AAA": []}, "quotes": {}}
        self.assertEqual(ev("s_mn_opt_turtle", view), [])

    def test_exit_10day_low(self):
        cl = [60.0] * 30 + [50.0]
        occ, _ = _chain("AAA", 60)
        view = {"bars": {"AAA": bars(cl)}, "positions": pos(occ, 5, 0, px=2.0),
                "options": {"chains": {}, "quotes": {}}}
        out = ev("s_mn_opt_turtle", view)
        self.assertEqual([o["kind"] for o in out], ["exit"])


class TestOptReversal(unittest.TestCase):
    def test_entry_worst_name_call_and_rotation_exit(self):
        def mk(r):
            return bars([100.0] * 10 + [100 * (1 + r)] * 12)
        occ, contract = _chain("AAA", 80)
        view = {"bars": {"AAA": mk(-0.2), "BBB": mk(0.05)}, "positions": [],
                "options": {"chains": {"AAA": [contract]},
                            "quotes": {occ: {"bid": 1.9, "ask": 2.0}}}}
        out = ev("s_mn_opt_reversal", view)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], occ)
        held = pos(occ, 5, 0, px=2.0)
        view2 = {"bars": {"AAA": mk(-0.2)}, "positions": held,
                 "options": {"chains": {}, "quotes": {}}}
        out = ev("s_mn_opt_reversal", view2)
        self.assertEqual([o["kind"] for o in out], ["exit"])


class TestOptPairs(unittest.TestCase):
    BASE = [50 + 0.05 * i for i in range(70)]

    def test_entry_and_exit(self):
        ko = self.BASE[:60] + [x * 1.12 for x in self.BASE[60:]]
        pep_px, ko_px = self.BASE[-1], ko[-1]
        occ_c, call = _chain("PEP", pep_px, typ="call")
        occ_p, put = _chain("KO", ko_px, typ="put")
        view = {"bars": {"KO": bars(ko), "PEP": bars(self.BASE)}, "positions": [],
                "options": {"chains": {"PEP": [call], "KO": [put]},
                            "quotes": {occ_c: {"bid": 1.9, "ask": 2.0},
                                       occ_p: {"bid": 1.9, "ask": 2.0}}}}
        out = ev("s_mn_opt_pairs", view)
        self.assertEqual(len(out), 2)
        self.assertEqual({o["symbol"] for o in out}, {occ_c, occ_p})
        held = pos(occ_c, 2, 0, px=2.0) + pos(occ_p, 2, 0, px=2.0)
        view2 = {"bars": {"KO": bars(self.BASE), "PEP": bars(self.BASE)},
                 "positions": held, "options": {"chains": {}, "quotes": {}}}
        out = ev("s_mn_opt_pairs", view2)
        self.assertEqual(sorted(o["kind"] for o in out), ["exit", "exit"])


IDS = ["s_mn_moonshot", "s_mn_kronos", "s_mn_macd", "s_mn_vwap", "s_mn_faber",
       "s_mn_reversal", "s_mn_pairs", "s_mn_opt_turtle", "s_mn_opt_reversal",
       "s_mn_opt_pairs"]


class TestRegistryRows(unittest.TestCase):
    def test_config_rows_and_inputs_match(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = {s["id"]: s for s in cfg["sleeves"]}
        import importlib
        for sid in IDS:
            self.assertIn(sid, rows)
            r = rows[sid]
            self.assertEqual(r["module"], f"adapters.{sid}")
            self.assertFalse(r["parked"])
            mod = importlib.import_module(f"adapters.{sid}")
            self.assertEqual(tuple(r["inputs"]), mod.INPUTS)
            self.assertTrue(mod.PRODUCERS)


if __name__ == "__main__":
    unittest.main()
