"""Blockers: POS-SHAPE-20261026 — snapshot positions shape cure.

Root cause: build_desk wired the dispatch-mode account producer as
{'positions': broker.get_positions()}, but PaperDoor.get_positions()
returns the RECONCILE shape {SYM: float(qty)} while the snapshot
contract every fixture serves and every bridge/adapter consumes is a
LIST of records {symbol, qty, avg_price, ...}. Evaluate-only served
{} (an empty dict iterates like an empty list), so the defect was
invisible until the 2026-10-26 09:25 ET dispatch flip put the real
85-position book into the snapshot as a dict: sleeves crashed on its
string keys (178 sleeves with eval errors: AttributeError 'str'
object has no attribute 'get', TypeError string indices, ValueError
dictionary update sequence) and zero real orders were placed.

Cure: PaperDoor.get_positions_snapshot() / FakeBroker parity method
serve the canonical list; the dispatch producer serves it; the
evaluate-only producer serves [] — one list contract in both modes.
get_positions() (reconcile dict) is untouched.

Fail direction (proven by temporary revert of the run_live wiring
back to get_positions()/{}): test_a, test_c and test_d fail with the
original error classes; restored wiring passes.
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker, PaperDoor  # noqa: E402
from desk3.run_live import build_desk  # noqa: E402

ENV = {"ALPACA_KEY_ID": "k", "ALPACA_SECRET_KEY": "s"}
NOW = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc).isoformat()

TWO_ROWS = [
    {"symbol": "AAPL", "qty": "10", "avg_entry_price": "227.50"},
    {"symbol": "TSLA", "qty": "-3", "avg_entry_price": None},
]
DUMMY85 = [{"symbol": f"S{i:02d}", "qty": str(i + 1),
            "avg_entry_price": "100.00"} for i in range(85)]


def stubbed_door(rows):
    door = PaperDoor(env=dict(ENV))
    door._get = lambda path: [dict(r) for r in rows]
    return door


def dispatch_desk_with(rows):
    desk, _ = build_desk(ROOT, dispatch=True, env=dict(ENV))
    desk.broker._get = lambda path: [dict(r) for r in rows]
    return desk


class TestProducerShape(unittest.TestCase):
    def test_a_dispatch_producer_serves_canonical_list(self):
        desk = dispatch_desk_with(TWO_ROWS)
        out = desk.producers["account"]({"now": NOW, "root": ROOT})
        pos = out["positions"]
        self.assertIsInstance(pos, list)
        self.assertEqual(pos, [
            {"symbol": "AAPL", "qty": 10.0, "avg_price": 227.50},
            {"symbol": "TSLA", "qty": -3.0, "avg_price": 0.0},
        ])

    def test_a2_snapshot_method_maps_avg_entry_price(self):
        door = stubbed_door(TWO_ROWS)
        self.assertEqual(door.get_positions_snapshot(), [
            {"symbol": "AAPL", "qty": 10.0, "avg_price": 227.50},
            {"symbol": "TSLA", "qty": -3.0, "avg_price": 0.0},
        ])
        # Reconcile shape preserved, untouched by the cure.
        self.assertEqual(door.get_positions(),
                         {"AAPL": 10.0, "TSLA": -3.0})

    def test_a3_fakebroker_parity(self):
        fb = FakeBroker(prices={"AAPL": 227.50})
        fb.positions = {"AAPL": 10.0, "TSLA": -3.0}
        snap = fb.get_positions_snapshot()
        self.assertIsInstance(snap, list)
        self.assertEqual({p["symbol"]: p for p in snap}, {
            "AAPL": {"symbol": "AAPL", "qty": 10.0, "avg_price": 227.50},
            "TSLA": {"symbol": "TSLA", "qty": -3.0, "avg_price": 0.0},
        })
        self.assertEqual(fb.get_positions(), {"AAPL": 10.0, "TSLA": -3.0})

    def test_d_evaluate_only_producer_serves_list(self):
        desk, _ = build_desk(ROOT, dispatch=False)
        out = desk.producers["account"]({"now": NOW, "root": ROOT})
        self.assertIsInstance(out["positions"], list)
        self.assertEqual(out["positions"], [])


class TestBridgeDrive(unittest.TestCase):
    def test_b_state_build_over_populated_list_incl_short(self):
        from adapters import _bridge

        class Ctx:
            positions = [
                {"symbol": "AAPL", "qty": 10.0, "avg_price": 227.50},
                {"symbol": "TSLA", "qty": -3.0, "avg_price": 250.25},
            ]
            params = {}
            slice = {"cash_usd": 10000.0, "capital_usd": 10000.0}

        ctx = Ctx()
        st = _bridge.state_common(ctx)
        self.assertEqual(set(st), {"AAPL", "TSLA"})
        self.assertEqual(st["AAPL"]["position"]["qty"], 10.0)
        self.assertEqual(st["AAPL"]["position"]["entry_px"], 227.50)
        self.assertEqual(st["TSLA"]["position"]["qty"], -3.0)
        self.assertEqual(st["TSLA"]["position"]["entry_px"], 250.25)
        st5 = _bridge.state_batch5(ctx)
        self.assertEqual(st5["TSLA"]["position"]["qty"], -3.0)
        self.assertEqual(st5["TSLA"]["position"]["avg_price"], 250.25)
        old = _bridge.state_old(ctx)
        self.assertEqual(old["AAPL"]["position"]["qty"], 10.0)
        self.assertEqual(old["AAPL"]["position"]["entry_px"], 227.50)
        self.assertEqual(_bridge.held_map(ctx),
                         {"AAPL": 10.0, "TSLA": -3.0})


class TestHistoricalErrorClassesCured(unittest.TestCase):
    """(c) The three sleeves that produced the three historical error
    classes evaluate WITHOUT error against a snapshot whose positions
    came from the cured dispatch producer populated with 85 dummy
    positions (the size of the real legacy book at the flip)."""

    SLEEVES = [
        ("t_cci_corr", "adapters3.t_cci_corr"),            # AttributeError
        ("aster_abs_enj_4h", "adapters3.aster_abs_enj_4h"),  # AttributeError
        ("bb_rsi_divergence", "adapters3.bb_rsi_divergence"),  # TypeError
        ("s_mn_faber", "adapters.s_mn_faber"),             # ValueError
    ]

    def test_c_sleeves_evaluate_clean_on_cured_producer_output(self):
        import importlib
        desk = dispatch_desk_with(DUMMY85)
        out = desk.producers["account"]({"now": NOW, "root": ROOT})
        positions = out["positions"]
        # Evaluate FIRST: on the pre-cure dict shape the sleeves
        # themselves raise the original error classes here, which is
        # the fail direction this blocker exists to pin.
        for sid, modname in self.SLEEVES:
            view = {"now": NOW, "now_iso": NOW, "bars": {},
                    "positions": positions,
                    "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                    "params": {}, "quotes": {}, "session_fills": [],
                    "vix": {}}
            ctx = {"sleeve_id": sid,
                   "state_dir": tempfile.mkdtemp(),
                   "cycle_id": "pos-shape-blocker"}
            mod = importlib.import_module(modname)
            result = mod.evaluate(view, ctx)  # must not raise
            self.assertIsInstance(result, list, sid)
        self.assertIsInstance(positions, list)
        self.assertEqual(len(positions), 85)


if __name__ == "__main__":
    unittest.main()
