"""HARDEN batch-1 blockers (2026-10-24):
- G4 producer bulkhead: one raising producer degrades ONLY its declared
  dependents (UNFED by name); other producers/sleeves still evaluate;
  the failure is named in the roll + health, never crashes the cycle.
- G5 runner roster freshness: run_live.ConfigWatcher detects a
  sleeves.json change so the live runner rebuilds at 311 instead of
  serving the stale 156 roster it was started with; build_desk roster
  always equals config/sleeves.json length.
- FIDELITY B13: Tensor C1 cool/hot split is source-exact
  (atr_ratio<=1)==cool (r19_tensor.passes), not cool<1/hot>=1.
- FIDELITY B10: LEADER1 eligibility requires the source's 252-session
  history (r19_etf._scores); a 127..251-bar symbol is never ranked.
- FIDELITY B6: structural-exit deadlines source-verified (fixed16 else
  96h for every other policy, r19_crypto exit_due_at) — regression pin.
"""
import json, os, sys, tempfile, textwrap, unittest
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def at(sec):
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=sec)


GOOD = '''
def evaluate(view, ctx):
    return [{"intent_id": ctx["cycle_id"] + "-e1", "kind": "entry",
             "symbol": "SPY", "side": "buy", "qty": 1,
             "limit_price": 100.0, "order_type": "limit"}]
'''


class TestProducerBulkhead(unittest.TestCase):
    def test_raising_producer_degrades_only_dependents(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        tmp = tempfile.mkdtemp()
        fixdir = os.path.join(tmp, "fix"); os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent(GOOD))
        desk = Desk(tmp, broker=FakeBroker(prices={"SPY": 100.0}),
                    sleeve_path=fixdir, timeout_s=10.0)
        def boom(ctx):
            raise RuntimeError("funding endpoint down")
        desk.add_producer("funding", boom, outputs=("funding",),
                          freshness_sla_s=3600)
        desk.add_producer("bars", lambda ctx: {"bars": {"SPY": [
            {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
            outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars",), cadence_s=60,
                        slice_usd=10000.0)
        desk.add_sleeve("dep1", "good", inputs=("bars", "funding"),
                        cadence_s=60, slice_usd=10000.0)
        roll = desk.run_cycle(now=at(30000))
        self.assertEqual(roll["status"], "ok")
        self.assertIn("funding", roll.get("producer_errors", {}))
        self.assertIn("RuntimeError", roll["producer_errors"]["funding"])
        self.assertEqual(roll["sleeves"]["fed1"]["status"], "ok")
        self.assertEqual(roll["sleeves"]["dep1"]["state"], "UNFED")
        self.assertIn("funding", roll["sleeves"]["dep1"]["missing"])
        self.assertEqual(roll["dispatched"], 1)
        health = json.load(open(os.path.join(tmp, "state", "health.json")))
        self.assertEqual(sorted(health["sleeves"]), ["dep1", "fed1"])
        self.assertIn("funding", health.get("producer_errors", {}))
        feed = json.load(open(os.path.join(tmp, "state", "terminal_feed.json")))
        self.assertEqual(feed["summary"]["strategies_total"], 2)


class TestRunnerRosterFreshness(unittest.TestCase):
    def test_config_watcher_detects_roster_change(self):
        from desk3.run_live import ConfigWatcher
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "config"))
        path = os.path.join(tmp, "config", "sleeves.json")
        with open(path, "w") as fh:
            json.dump({"sleeves": [{"id": "a"}]}, fh)
        w = ConfigWatcher(tmp)
        self.assertFalse(w.changed())
        with open(path, "w") as fh:
            json.dump({"sleeves": [{"id": "a"}, {"id": "b"}]}, fh)
        self.assertTrue(w.changed())
        w.mark_seen()
        self.assertFalse(w.changed())

    def test_build_desk_roster_equals_config(self):
        from desk3.run_live import build_desk
        desk, rows = build_desk(ROOT)
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        self.assertEqual(len(rows), len(cfg["sleeves"]))
        self.assertEqual(len(desk.sleeves), len(cfg["sleeves"]))
        # 328 since przm_zero + przm_fade_edges landed 2026-10-29 (PRZM recreation, parked); 326 was the trullas_v01..v10 variant family 2026-10-29.
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows), 400)


class TestFidelityB13AtrSplit(unittest.TestCase):
    def test_atr_ratio_exactly_one_is_cool_not_hot(self):
        sys.path.insert(0, ROOT)
        import importlib
        CTX = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}
        def fire(sid, ar):
            return {"sleeve_id": sid, "symbol": "AAA", "signal": "buy-cyan",
                    "date": "2026-10-23", "price": 4.0, "ret60": 40,
                    "vol20": 0.1, "adv_usd": 3000000, "atr_ratio": ar}
        def ev(sid, ar):
            v = {"now": CTX["now"], "tensor": {"fires": [fire(sid, ar)]},
                 "bars": {}, "positions": [], "extra": {}}
            return importlib.import_module(f"adapters3.{sid}").evaluate(v, dict(CTX))
        cool = "aster_tensor_c1_cash_cool_25"
        hot = "aster_tensor_c1_cash_hot_25"
        self.assertEqual(len(ev(cool, 1.0)), 1)   # source: atr<=1 is cool
        self.assertEqual(ev(hot, 1.0), [])        # source: hot is atr>1


class TestFidelityB10LeaderEligibility(unittest.TestCase):
    def test_symbol_under_252_sessions_is_never_ranked(self):
        import importlib
        CTX = {"session": "2026-10-01", "now": "2026-10-01T09:36:00",
               "slice": {"capital_usd": 10000.0}}
        def flat(px, n):
            return [{"t": f"d{i}", "o": px, "h": px, "l": px, "c": px,
                     "v": 1000} for i in range(n)]
        def rising(px, n):
            out = flat(100.0, n); out[-1] = dict(out[-1], c=px, o=px, h=px, l=px)
            return out
        basket = ["QQQ", "SPY", "SMH", "XLB", "XLC", "XLE", "XLF", "XLI",
                  "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
        m = {s: flat(100.0, 260) for s in basket}
        m["SMH"] = rising(150.0, 200)  # best return but only 200 sessions
        v = {"now": CTX["now"], "bars": m, "positions": [], "quotes": {},
             "extra": {}}
        # WEIGHT-LAG-ACTIVE-20261031 (desk3/aster_etf.py): evaluate()
        # acts on the PREVIOUS evaluation's pending targets held in
        # module state (_PENDING_TARGETS); the first evaluation after
        # activation computes targets and emits nothing. This test
        # previously made a single call, so standalone (no earlier
        # test file priming _PENDING_TARGETS for this sleeve) it got
        # [] and failed, while the full discover gate passed only
        # because an earlier file had primed the state. Hermetic
        # cure (same ev2 pattern as test_aster_batch10_blockers.py):
        # clear this sleeve's pending state, then drive two
        # evaluations and assert on the second.
        from desk3 import aster_etf
        aster_etf._PENDING_TARGETS.pop(
            "aster_etf_leader1_m150", None)
        mod = importlib.import_module(
            "adapters3.aster_etf_leader1_m150")
        first = mod.evaluate(v, dict(CTX))
        self.assertEqual(first, [])  # weight lag: first emits nothing
        o = mod.evaluate(v, dict(CTX))
        self.assertTrue(o)
        self.assertNotIn("SMH", [x["symbol"] for x in o])
        self.assertEqual(o[0]["symbol"], "QQQ")  # eligible tie -> alphabetical


class TestFidelityB6Deadlines(unittest.TestCase):
    def test_structural_policies_carry_96h_deadline(self):
        from desk3.aster_crypto import SPECS
        for sid, spec in SPECS.items():
            if spec["exit"] == "fixed16":
                self.assertEqual(spec["hold_h"], 16, sid)
            else:
                self.assertEqual(spec["hold_h"], 96, sid)


if __name__ == "__main__":
    unittest.main()
