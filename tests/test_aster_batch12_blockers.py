"""Aster batch 12 blockers (ASTER-B12): breakout_base LINKUSDT volume1pct
+ 9x negative_funding_squeeze LINKUSDT. Source-verified against the staged
archive r19_crypto.py + crypto_rules.json: entry = completed 4h close >
highest high of prior 20 bars (NFS additionally latest observed funding < 0;
breakout_base is the funding-OFF control); entry sizing fullcash = slice
cash net 10bp fee, volume1pct = min(fullcash, 1% of preceding 4h volume);
exits fixed16/fixed96 deadlines, lost_breakout / normalization /
normalization_failure structural exits executable 4h after the trigger bar
closes, 96h deadline backstop on structural arms (source: exit_due =
entry_due + 96 for every non-fixed16 policy); owned deadlines survive
missing bars/funding. Fail-first: adapters absent pre-build => errors.
Also blocks ASTER-B12-2: fractional qty on bare USDT spot pairs must pass
intent validation (dispatcher E2E), whole-qty rule for equities unchanged.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
P = "aster_r19_linkusdt_"
IDS = [P + "breakout_base_fixed16_volume1pct",
 P + "negative_funding_squeeze_fixed16_fullcash",
 P + "negative_funding_squeeze_fixed16_volume1pct",
 P + "negative_funding_squeeze_fixed96_fullcash",
 P + "negative_funding_squeeze_fixed96_volume1pct",
 P + "negative_funding_squeeze_lost_breakout_fullcash",
 P + "negative_funding_squeeze_lost_breakout_volume1pct",
 P + "negative_funding_squeeze_normalization_failure_fullcash",
 P + "negative_funding_squeeze_normalization_failure_volume1pct",
 P + "negative_funding_squeeze_normalization_fullcash"]
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)
SYM = "LINKUSDT"

def bars(n=25, breakout=True, vol=100000.0, last_close=None, shift_h=0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=shift_h) - timedelta(hours=4 * (n - i))
        c = 22.0 if (breakout and i == n - 1) else 20.0
        out.append({"t": t.isoformat(), "o": 20.0, "h": 20.5, "l": 19.5, "c": c, "v": vol})
    if last_close is not None:
        out[-1]["c"] = last_close
    return out

def drive(sid, brs=None, funding=-0.01, positions=None, cash=10000.0):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(), "bars": {f"{SYM}|4Hour": brs if brs is not None else bars()},
            "funding": {SYM: funding} if funding is not None else {},
            "positions": positions or [], "slice": {"capital_usd": 10000.0, "cash_usd": cash},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": tempfile.mkdtemp()})

def pos(hours=20, qty=400.0, **kw):
    d = {"symbol": SYM, "qty": qty, "avg_price": 20.0,
         "opened_at": (NOW - timedelta(hours=hours)).isoformat(), "breakout_level": 20.5}
    d.update(kw); return [d]

class TestEntries(unittest.TestCase):
    def test_breakout_entry_volume_cap(self):
        out = drive(IDS[0], brs=bars(vol=10000.0), funding=None)  # funding OFF control: no funding needed
        self.assertEqual(len(out), 1); self.assertEqual(out[0].kind, "enter")
        self.assertAlmostEqual(out[0].qty, 100.0)  # 1% of 10k preceding-bar volume binds
    def test_breakout_entry_ignores_positive_funding(self):
        self.assertEqual(len(drive(IDS[0], funding=0.005)), 1)
    def test_nfs_entry_fullcash(self):
        out = drive(IDS[1]); self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0].qty, 10000 * 0.999 / 22.0, places=4)
    def test_nfs_entry_volume_cap(self):
        out = drive(IDS[2], brs=bars(vol=10000.0)); self.assertEqual(len(out), 1); self.assertAlmostEqual(out[0].qty, 100.0)  # 1% of 10k preceding-bar volume binds under fullcash 454.09
    def test_all_nfs_arms_enter(self):
        for sid in IDS[1:]:
            self.assertEqual(len(drive(sid)), 1, sid)

class TestRefusals(unittest.TestCase):
    def test_no_breakout_refuses(self):
        self.assertEqual(drive(IDS[1], brs=bars(breakout=False)), [])
        self.assertEqual(drive(IDS[0], brs=bars(breakout=False), funding=None), [])
    def test_positive_funding_refuses_nfs(self): self.assertEqual(drive(IDS[1], funding=0.001), [])
    def test_zero_funding_refuses_nfs(self):
        # AMENDED 2026-11-12 (GATE-CURE-CRYPTO-20261112,
        # STRICTNESS-CENSUS proposal 9): the LINK nfs funding leg
        # relaxes < 0 -> < 0.00005, so funding 0.0 now ENTERS and
        # the refusal boundary sits at 0.00005. Pre-amendment pin
        # preserved in ~/workspace/.gatecure-20261112/pre/tests/.
        # AMENDED again 2026-11-12 (READINESS-ROUND2-20261112,
        # CADENCE-SWEEPS S4): the boundary moves to 0.00015.
        self.assertEqual(len(drive(IDS[1], funding=0.0)), 1)
        self.assertEqual(drive(IDS[1], funding=0.00015), [])
        self.assertEqual(drive(IDS[1], funding=0.001), [])
    def test_missing_funding_refuses_nfs(self): self.assertEqual(drive(IDS[1], funding=None), [])
    def test_short_history_refuses(self): self.assertEqual(drive(IDS[1], brs=bars(n=20)), [])
    def test_occupied_refuses(self): self.assertEqual(drive(IDS[1], positions=pos(hours=1)), [])

class TestExits(unittest.TestCase):
    def test_fixed16_exit(self):
        self.assertEqual([o.kind for o in drive(IDS[2], positions=pos(hours=17))], ["exit"])
        self.assertEqual(drive(IDS[2], positions=pos(hours=8)), [])
    def test_fixed96_exit(self):
        self.assertEqual(len(drive(IDS[3], positions=pos(hours=97))), 1)
        self.assertEqual(drive(IDS[3], positions=pos(hours=20)), [])
    def test_lost_breakout_exit_after_delay(self):
        b = bars(breakout=False, last_close=19.0, shift_h=8)
        self.assertEqual(len(drive(IDS[5], brs=b, positions=pos(hours=20))), 1)
    def test_lost_breakout_no_exit_before_delay(self):
        b = bars(breakout=False, last_close=19.0)  # trigger bar closes at NOW; +4h not met
        self.assertEqual(drive(IDS[5], brs=b, positions=pos(hours=20)), [])
    def test_lost_breakout_holds_above_level(self):
        b = bars(breakout=False, last_close=21.0, shift_h=8)
        self.assertEqual(drive(IDS[5], brs=b, positions=pos(hours=20)), [])
    def test_normalization_exit(self):
        b = bars(breakout=False, shift_h=8)
        self.assertEqual(len(drive(IDS[9], brs=b, funding=0.0, positions=pos(hours=20))), 1)
        self.assertEqual(drive(IDS[9], brs=b, funding=-0.01, positions=pos(hours=20)), [])
    def test_normalization_no_exit_before_delay(self):
        self.assertEqual(drive(IDS[9], funding=0.0, positions=pos(hours=20)), [])
    def test_norm_failure_exit(self):
        b = bars(breakout=False, last_close=18.0, shift_h=8)
        b[-1]["l"] = 18.0
        self.assertEqual(len(drive(IDS[7], brs=b, funding=0.002, positions=pos(hours=20))), 1)
    def test_norm_failure_needs_price_failure(self):
        b = bars(breakout=False, last_close=20.0, shift_h=8)
        self.assertEqual(drive(IDS[7], brs=b, funding=0.002, positions=pos(hours=20)), [])
    def test_norm_failure_needs_funding_reset(self):
        b = bars(breakout=False, last_close=18.0, shift_h=8)
        self.assertEqual(drive(IDS[7], brs=b, funding=-0.002, positions=pos(hours=20)), [])
    def test_structural_deadline_backstop_96h(self):
        self.assertEqual(len(drive(IDS[5], brs=[], funding=None, positions=pos(hours=100))), 1)
        self.assertEqual(len(drive(IDS[9], brs=[], funding=None, positions=pos(hours=97))), 1)

class TestFractionalUsdtValidation(unittest.TestCase):
    def test_fractional_linkusdt_qty_valid(self):
        from desk3.models import validate_intent
        self.assertTrue(validate_intent({"intent_id": "x", "kind": "entry", "symbol": "LINKUSDT",
                                         "side": "buy", "qty": 454.09}))
    def test_fractional_equity_qty_admitted_ws4(self):
        # WS4-FRACTIONAL-20261114 (owner ruling 2026-11-14, "It
        # needs to buy stuff of any price"): the pre-cure shape
        # rule rejected fractional quantities for every non-crypto
        # symbol; that rejection WAS the defect class's door-level
        # reinforcement and is cured in desk3/models.py. Fractional
        # equity quantities are admitted; the two named exceptions
        # still refuse: options contracts (whole by the
        # instrument) and equity fractional limit orders (the
        # fractional door is market-only).
        from desk3.models import validate_intent, IntentError
        self.assertTrue(validate_intent(
            {"intent_id": "x", "kind": "entry", "symbol": "SPY",
             "side": "buy", "qty": 1.5}))
        with self.assertRaises(IntentError) as cm:
            validate_intent({"intent_id": "x", "kind": "entry",
                             "symbol": "SPY261120C00750000",
                             "side": "buy", "qty": 1.5})
        self.assertEqual(str(cm.exception), "qty_not_whole")
        with self.assertRaises(IntentError) as cm:
            validate_intent({"intent_id": "x", "kind": "entry",
                             "symbol": "SPY", "side": "buy", "qty": 1.5,
                             "order_type": "limit", "limit_price": 100.0})
        self.assertEqual(str(cm.exception), "fractional_qty_limit_order")

class TestRegistryAndE2E(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch12 import config_rows
        rows = {r["id"]: r for r in config_rows()}; self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have); self.assertEqual(have[sid]["inputs"], rows[sid]["inputs"])
            self.assertEqual(have[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(importlib.import_module(f"adapters3.{sid}").INPUTS, tuple(rows[sid]["inputs"]))
        # breakout_base is the funding-OFF control: it must not declare funding
        self.assertNotIn("funding", rows[IDS[0]]["inputs"])
        for sid in IDS[1:]:
            self.assertIn("funding", rows[sid]["inputs"])
    def _e2e(self, sid, price):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        out = drive(sid); self.assertEqual(len(out), 1)
        tmp = tempfile.mkdtemp(); broker = FakeBroker(prices={SYM: price})
        disp = Dispatcher(tmp, broker, slices={sid: {"capital_usd": 11000.0, "cash_usd": 11000.0}},
                          price_lookup=lambda s: price)
        def as_dict(i, n):
            return {"intent_id": f"{sid}-e2e-{n}", "kind": "entry" if i.kind == "enter" else "exit",
                    "symbol": i.symbol, "side": i.side, "qty": i.qty, "order_type": "market"}
        r = disp.process_intent(as_dict(out[0], 1), sid); self.assertEqual(r["status"], "filled")
        held = disp.slice_for(sid)["positions"]; self.assertIn("LINK/USD", held)  # BLOCKED-EXIT-20261029: broker dialect at the door
        return disp, held
    def test_e2e_roundtrip_nfs_fixed16(self):
        sid = IDS[1]; disp, held = self._e2e(sid, 22.0)
        ex = drive(sid, positions=pos(hours=17, qty=held["LINK/USD"]["qty"]))
        r2 = disp.process_intent({"intent_id": f"{sid}-e2e-2", "kind": "exit", "symbol": SYM,
                                   "side": "sell", "qty": ex[0].qty, "order_type": "market"}, sid)
        self.assertEqual(r2["status"], "filled"); self.assertEqual(disp.slice_for(sid)["positions"], {})
    def test_e2e_roundtrip_breakout_volume(self):
        sid = IDS[0]; disp, held = self._e2e(sid, 22.0)
        ex = drive(sid, funding=None, positions=pos(hours=17, qty=held["LINK/USD"]["qty"]))
        r2 = disp.process_intent({"intent_id": f"{sid}-e2e-2", "kind": "exit", "symbol": SYM,
                                   "side": "sell", "qty": ex[0].qty, "order_type": "market"}, sid)
        self.assertEqual(r2["status"], "filled"); self.assertEqual(disp.slice_for(sid)["positions"], {})

if __name__ == "__main__":
    unittest.main()
