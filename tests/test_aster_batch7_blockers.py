"""Aster batch 7 blockers (ASTER-B7): R19 ENJUSDT — absorption_base
(volume1pct), absorption_negative_funding x2, absorption_nonnegative_
funding x2, breakout_base x2, negative_funding_squeeze fixed16 x2 +
fixed96 fullcash. Oracle = archive r19_crypto.py + absorption/signals.py
+ crypto_rules.json (read from the staged archive): absorption shock/
confirm with >=300 bars; breakout close > prior-20 highest high;
funding <0 / >=0 filters (funding-off controls ignore funding); fixed
16h/96h deadline exits survive missing inputs; sizing fullcash =
cash/(price*1.001), volume1pct caps at 1% of preceding 4h volume.
Fail-first: adapters absent pre-build => import errors."""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
P = "aster_r19_enjusdt_"
IDS = [P+"absorption_base_fixed16_volume1pct",
       P+"absorption_negative_funding_fixed16_fullcash",
       P+"absorption_negative_funding_fixed16_volume1pct",
       P+"absorption_nonnegative_funding_fixed16_fullcash",
       P+"absorption_nonnegative_funding_fixed16_volume1pct",
       P+"breakout_base_fixed16_fullcash",
       P+"breakout_base_fixed16_volume1pct",
       P+"negative_funding_squeeze_fixed16_fullcash",
       P+"negative_funding_squeeze_fixed16_volume1pct",
       P+"negative_funding_squeeze_fixed96_fullcash"]
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def bars(n=25, breakout=True, vol=100000.0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        c = 1.10 if (breakout and i == n - 1) else 1.0
        out.append({"t": t.isoformat(), "o": 1.0, "h": 1.05, "l": 0.95, "c": c, "v": vol})
    return out


def abs_bars():
    out = []
    for i in range(302):
        t = NOW - timedelta(hours=4 * (302 - i)); o = c = 2.0; h = 2.02; l = 1.98; v = 1000.0
        if i == 300: o, c, h, l, v = 2.0, 1.90, 2.0, 1.88, 5000.0
        if i == 301: o, c = 1.90, 1.96
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return out


def drive(sid, brs=None, funding=-0.01, positions=None, cash=10000.0):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(),
            "bars": {"ENJUSDT|4Hour": brs if brs is not None else bars()},
            "funding": {"ENJUSDT": funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": cash},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": tempfile.mkdtemp()})


def pos(hours=20, qty=5000.0, **kw):
    d = {"symbol": "ENJUSDT", "qty": qty, "avg_price": 1.0,
         "opened_at": (NOW - timedelta(hours=hours)).isoformat(), "breakout_level": 1.05}
    d.update(kw); return [d]


class TestEntries(unittest.TestCase):
    def test_absorption_base_volume_cap(self):
        out = drive(IDS[0], brs=abs_bars(), funding=None)
        self.assertEqual(len(out), 1); self.assertEqual(out[0].kind, "enter")
        self.assertAlmostEqual(out[0].qty, 50.0)  # 1% of preceding (shock) bar volume 5000

    def test_absorption_base_ignores_funding(self):
        self.assertEqual(len(drive(IDS[0], brs=abs_bars(), funding=0.5)), 1)

    def test_abs_neg_entry_fullcash(self):
        out = drive(IDS[1], brs=abs_bars())
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0].qty, 10000 / (1.96 * 1.001), places=4)

    def test_abs_nonneg_entry(self):
        self.assertEqual(len(drive(IDS[3], brs=abs_bars(), funding=0.0)), 1)
        self.assertEqual(len(drive(IDS[4], brs=abs_bars(), funding=0.002)), 1)

    def test_breakout_entry_fullcash(self):
        out = drive(IDS[5], funding=None)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0].qty, 10000 / (1.10 * 1.001), places=4)

    def test_breakout_volume_cap(self):
        out = drive(IDS[6], funding=None)
        self.assertAlmostEqual(out[0].qty, 1000.0)

    def test_nfs_entries(self):
        self.assertEqual(len(drive(IDS[7])), 1)
        out = drive(IDS[8]); self.assertAlmostEqual(out[0].qty, 1000.0)
        self.assertEqual(len(drive(IDS[9])), 1)


class TestRefusals(unittest.TestCase):
    def test_no_breakout_refuses(self):
        self.assertEqual(drive(IDS[5], brs=bars(breakout=False), funding=None), [])
        self.assertEqual(drive(IDS[7], brs=bars(breakout=False)), [])

    def test_funding_sign_refuses(self):
        self.assertEqual(drive(IDS[1], brs=abs_bars(), funding=0.001), [])
        self.assertEqual(drive(IDS[3], brs=abs_bars(), funding=-0.001), [])
        self.assertEqual(drive(IDS[7], funding=0.0), [])

    def test_missing_funding_refuses_filtered_only(self):
        self.assertEqual(drive(IDS[1], brs=abs_bars(), funding=None), [])
        self.assertEqual(drive(IDS[7], funding=None), [])
        self.assertEqual(len(drive(IDS[5], funding=None)), 1)  # control unaffected

    def test_absorption_short_history_refuses(self):
        self.assertEqual(drive(IDS[1], brs=abs_bars()[:200]), [])
        self.assertEqual(drive(IDS[0], brs=abs_bars()[:200], funding=None), [])

    def test_no_shock_refuses(self):
        flat = bars(n=302, breakout=False, vol=1000.0)
        self.assertEqual(drive(IDS[1], brs=flat), [])

    def test_short_breakout_history_refuses(self):
        self.assertEqual(drive(IDS[7], brs=bars(n=20)), [])

    def test_occupied_refuses(self):
        self.assertEqual(drive(IDS[7], positions=pos(hours=1)), [])


class TestExits(unittest.TestCase):
    def test_fixed16_exit_and_not_yet(self):
        out = drive(IDS[7], positions=pos(hours=17))
        self.assertEqual([o.kind for o in out], ["exit"])
        self.assertEqual(drive(IDS[7], positions=pos(hours=8)), [])
        self.assertEqual(len(drive(IDS[0], brs=abs_bars(), funding=None,
                                   positions=pos(hours=17))), 1)

    def test_fixed96_exit(self):
        self.assertEqual(len(drive(IDS[9], positions=pos(hours=97))), 1)
        self.assertEqual(drive(IDS[9], positions=pos(hours=20)), [])

    def test_deadline_survives_missing_inputs(self):
        out = drive(IDS[8], brs=[], funding=None, positions=pos(hours=100))
        self.assertEqual(len(out), 1); self.assertEqual(out[0].kind, "exit")


class TestRegistryAndE2E(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch7 import config_rows
        rows = {r["id"]: r for r in config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have)
            self.assertEqual(have[sid]["inputs"], rows[sid]["inputs"])
            self.assertEqual(importlib.import_module(f"adapters3.{sid}").INPUTS,
                             tuple(rows[sid]["inputs"]))
            self.assertEqual(have[sid]["slice"]["capital_usd"], 10000.0)

    def test_funding_inputs_declared_only_where_filtered(self):
        from desk3.aster_batch7 import inputs_for
        self.assertNotIn("funding", inputs_for(IDS[0]))
        self.assertNotIn("funding", inputs_for(IDS[5]))
        self.assertIn("funding", inputs_for(IDS[1]))
        self.assertIn("funding", inputs_for(IDS[9]))

    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        # volume1pct arm: qty is a whole 1000.0 — the v3 dispatcher
        # validator treats only USD/-USD forms as fractional, so the
        # source-faithful fractional fullcash qty is dispatch-blocked
        # upstream (FIDELITY-LEDGER ASTER-B7 platform note).
        sid = IDS[8]; out = drive(sid); self.assertEqual(len(out), 1)
        tmp = tempfile.mkdtemp(); broker = FakeBroker(prices={"ENJUSDT": 1.10})
        disp = Dispatcher(tmp, broker, slices={sid: {"capital_usd": 10000.0, "cash_usd": 10000.0}})

        def as_dict(i, n):
            return {"intent_id": f"{sid}-e2e-{n}", "kind": "entry" if i.kind == "enter" else "exit",
                    "symbol": i.symbol, "side": i.side, "qty": i.qty, "order_type": "market",
                    "price_hint": i.price_hint}
        r = disp.process_intent(as_dict(out[0], 1), sid); self.assertEqual(r["status"], "filled")
        held = disp.slice_for(sid)["positions"]; self.assertIn("ENJ/USD", held)  # BLOCKED-EXIT-20261029: broker dialect at the door
        ex = drive(sid, positions=pos(hours=100, qty=held["ENJ/USD"]["qty"]))
        r2 = disp.process_intent(as_dict(ex[0], 2), sid); self.assertEqual(r2["status"], "filled")
        self.assertEqual(disp.slice_for(sid)["positions"], {})


if __name__ == "__main__":
    unittest.main()
