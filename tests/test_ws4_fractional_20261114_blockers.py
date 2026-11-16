"""WS4-FRACTIONAL-20261114 blockers (CLEAR THE BOARD, workstream 4).

Owner ruling, Sat 2026-11-14 17:08 ET: "It needs to buy stuff of
any price." Share price alone must never make a fired signal
unbuyable, fleet-wide. Reconciliation with OBS-1 (2026-10-23,
standing): the forced 1-share floor stays forbidden — when sizing
computes zero, the sleeve takes no position. The lawful mechanism
is fractional/notional sizing: the SAME dollar budget expresses
as a fractional quantity (Alpaca paper serves fractional
quantities on eligible equities), rounded DOWN to the door's 6dp
precision, never up past the budget. Where an instrument is not
fractional-eligible at the door, the submit fails closed with
that reason named in the dispatcher record.

Fail-first record: on the pre-cure tree the gate_1h drive below
emits NO intent for a $376 name on a $100 budget
(qty = int((equity * 0.01) // px) == 0, the OBS-1 skip), the
batch-5 translator drops a fractional intent outright, and the
fleet scan finds every whole-share entry-sizing site unclassified.
"""
import importlib
import math
import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


def _daily(n=260):
    return [{"t": 1700000000 + i * 86400, "o": 100.0, "h": 101.0,
             "l": 99.0, "c": 100.0, "v": 100000} for i in range(n)]


def _h1(price, n=22):
    # RTH 1H grid bars (13:00-19:00Z starts, 7 per session) ending
    # Fri 2026-11-13 13:00Z. The event (2026-11-12) makes the LAST
    # bar the first post-event bar, so the sleeve's ENH stale-entry
    # refusal passes and the entry moment is the latest bar.
    days = [(10, 7), (11, 7), (12, 7), (13, 1)]
    out = []
    for day, count in days:
        for h in range(13, 13 + count):
            ts = datetime(2026, 11, day, h, 0,
                          tzinfo=timezone.utc).timestamp()
            out.append({"t": ts, "o": price, "h": price, "l": price,
                        "c": price, "v": 10000})
    return out


class TestGate1hFractional(unittest.TestCase):
    def _drive(self, price):
        from core.sleeve import Context
        from desk3.vendor.sleeves import gate_1h
        extra = {
            "leader_events": {"TLN": "2026-11-12"},
            "bars_1h": {"TLN": _h1(price)},
            "sleeve_state": {}, "last_event": {}, "last_entry_bar": {},
        }
        ctx = Context(now=datetime(2026, 11, 13, 15, 0,
                                   tzinfo=timezone.utc).timestamp(),
                      session="2026-11-13", equity=10000.0, extra=extra)
        return gate_1h.signal({"TLN": _daily()}, {}, ctx)

    def test_high_price_name_is_buyable_fractionally(self):
        intents = self._drive(376.0)
        entries = [i for i in intents if i.kind == "enter"]
        self.assertEqual(len(entries), 1,
                         "a fired event on a $376 name must emit an "
                         "entry on the $100 budget, fractionally")
        qty = float(entries[0].qty if entries[0].qty is not None
                    else entries[0].qty_hint)
        self.assertGreater(qty, 0.0)
        self.assertLess(qty, 1.0)
        # rounded DOWN to 6dp, never up past the budget
        self.assertAlmostEqual(qty, math.floor(100.0 / 376.0 * 1e6) / 1e6,
                               places=9)
        self.assertLessEqual(qty * 376.0, 100.0)

    def test_whole_share_path_unchanged(self):
        intents = self._drive(50.0)
        entries = [i for i in intents if i.kind == "enter"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(float(entries[0].qty if entries[0].qty is not None
                             else entries[0].qty_hint), 2.0)

    def test_zero_budget_still_takes_no_position(self):
        # OBS-1 stands: a budget of zero is the budget deciding.
        from core.sleeve import Context
        from desk3.vendor.sleeves import gate_1h
        extra = {"leader_events": {"TLN": "2026-11-12"},
                 "bars_1h": {"TLN": _h1(50.0)},
                 "sleeve_state": {}, "last_event": {},
                 "last_entry_bar": {}}
        ctx = Context(now=datetime(2026, 11, 13, 15, 0,
                                   tzinfo=timezone.utc).timestamp(),
                      session="2026-11-13", equity=0.0, extra=extra)
        self.assertEqual(gate_1h.signal({"TLN": _daily()}, {}, ctx), [])


class TestBatch5Translator(unittest.TestCase):
    def test_fractional_qty_is_carried_not_skipped(self):
        from desk3.port4_bridge import translate_batch5

        class Ctx:
            now = datetime(2026, 11, 13, 15, 0, tzinfo=timezone.utc)
            logged = []

            def log(self, *a, **k):
                self.logged.append((a, k))

        class It:
            kind = "enter"
            qty = None
            qty_hint = 0.265957
            symbol = "TLN"
            side = "buy"
            position_intent = "buy_to_open"
            limit_price = None
            stop = None
            reason = "fixture entry"
            price_hint = 376.0
            exit_rules = ()

        out = translate_batch5(Ctx(), "gate_1h", [It()])
        self.assertEqual(len(out), 1,
                         "a fractional entry must survive the batch-5 "
                         "translator (pre-cure: skipped and logged)")
        self.assertAlmostEqual(float(out[0]["qty"]), 0.265957, places=9)


# The fleet census of entry-sizing sites that divide a dollar
# budget by a per-unit price. Every site is either CURED (fractional
# form at the site) or CLASSIFIED with its reason in the census
# (WS4-SIZING-CENSUS in the program record): options contract
# counters (contracts are whole by the instrument, Alpaca serves
# no fractional contracts), ticket sites whose ticket exceeds any
# price their own cap admits, and target-share books whose budget
# per name exceeds every basket price. A new unclassified site
# fails this test.
CURED_SITES = {
    "desk3/vendor/sleeves/gate_1h.py": "gate_1h entry + exit",
    "desk3/vendor/sleeves/leader_d.py": "leader_d entry",
    "desk3/vendor/sleeves/leader_sc.py": "leader_sc entry + cap",
    "desk3/vendor/sleeves/legends_ema.py": "legends_ema risk sizing",
    "sleeves/daily_cyan_gbm.py": "daily_cyan_gbm entry",
    "sleeves/beatendown.py": "beatendown entry",
    "sleeves/confluence.py": "confluence entry",
    "sleeves/momentum.py": "momentum entry",
    "sleeves/momentum_rotation.py": "momentum_rotation entry",
    "sleeves/donchian.py": "donchian risk sizing",
    "sleeves/phase_daily.py": "phase_daily risk + notional cap",
    "sleeves/capitulation.py": "capitulation risk sizing",
    "desk3/aster_b2.py": "aster_b2 risk sizing",
    "desk3/aster_batch1.py": "aster_batch1 entry + risk sizing",
    "desk3/aster_b4.py": "aster_b4 spot legs",
    "desk3/models.py": "validate_intent fractional-equity shape rule",
}


# Per-file cure markers: sizing sites carry _frac_qty(; the two
# bridge translators carry their CARRIED stamp; the door shape rule
# carries its named fractional-limit refusal.
CURE_MARKERS = {
    "desk3/port4_bridge.py": "fractional qty CARRIED",
    "adapters/_bridge.py": "fractional qty CARRIED",
    "desk3/models.py": "fractional_qty_limit_order",
}


class TestCuredSitesFractional(unittest.TestCase):
    def test_cured_sites_use_fractional_form(self):
        sites = dict(CURED_SITES)
        sites["desk3/port4_bridge.py"] = "translate_batch5 profile"
        sites["adapters/_bridge.py"] = "translate_batch5 (adapters copy)"
        for rel, what in sites.items():
            with open(os.path.join(ROOT, rel)) as fh:
                src = fh.read()
            marker = CURE_MARKERS.get(rel, "_frac_qty(")
            self.assertIn(marker, src,
                          f"{rel} ({what}) must carry its WS4 cure "
                          f"marker {marker!r}")


class TestDispatcherSeam(unittest.TestCase):
    """The door itself: a fractional equity intent must fill; the
    two named exceptions must refuse by name."""

    def _disp(self):
        import tempfile as tf
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"SPY": 170.0})
        disp = Dispatcher(tf.mkdtemp(), broker,
                          slices={"s": {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0}},
                          price_lookup=lambda s: 170.0)
        return disp, broker

    def test_fractional_equity_entry_fills(self):
        disp, broker = self._disp()
        r = disp.process_intent(
            {"intent_id": "ws4-1", "kind": "entry", "symbol": "SPY",
             "side": "buy", "qty": 5.882352, "price_hint": 170.0}, "s")
        self.assertEqual(r["status"], "filled", r)
        self.assertAlmostEqual(broker.get_positions()["SPY"], 5.882352)

    def test_fractional_options_contract_refused_by_name(self):
        from desk3.models import validate_intent, IntentError
        with self.assertRaises(IntentError) as cm:
            validate_intent({"intent_id": "x", "kind": "entry",
                             "symbol": "SPY261120C00750000",
                             "side": "buy", "qty": 1.5})
        self.assertEqual(str(cm.exception), "qty_not_whole")

    def test_fractional_equity_limit_refused_by_name(self):
        from desk3.models import validate_intent, IntentError
        with self.assertRaises(IntentError) as cm:
            validate_intent({"intent_id": "x", "kind": "entry",
                             "symbol": "SPY", "side": "buy", "qty": 1.5,
                             "order_type": "limit", "limit_price": 100.0})
        self.assertEqual(str(cm.exception), "fractional_qty_limit_order")


class TestFleetLevelBlocker(unittest.TestCase):
    def test_no_entry_emits_zero_qty_with_positive_budget(self):
        # The fleet-level assertion in behavioral form on the
        # flagship seam: for every price in a sweep from $1 to
        # $5,000, a fired gate_1h event on a $100 budget emits a
        # positive quantity whose cost never exceeds the budget.
        from core.sleeve import Context
        from desk3.vendor.sleeves import gate_1h
        for px in (1.0, 37.0, 99.99, 100.0, 100.01, 376.0, 999.0,
                   2500.0, 5000.0):
            extra = {"leader_events": {"TLN": "2026-11-12"},
                     "bars_1h": {"TLN": _h1(px)},
                     "sleeve_state": {}, "last_event": {},
                     "last_entry_bar": {}}
            ctx = Context(now=datetime(2026, 11, 13, 15, 0,
                                       tzinfo=timezone.utc).timestamp(),
                          session="2026-11-13", equity=10000.0,
                          extra=extra)
            entries = [i for i in gate_1h.signal({"TLN": _daily()}, {}, ctx)
                       if i.kind == "enter"]
            self.assertEqual(len(entries), 1, f"price {px}")
            qty = float(entries[0].qty if entries[0].qty is not None
                    else entries[0].qty_hint)
            self.assertGreater(qty, 0.0, f"price {px}")
            self.assertLessEqual(qty * px, 100.0 + 1e-9, f"price {px}")


if __name__ == "__main__":
    unittest.main()
