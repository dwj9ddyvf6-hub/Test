"""Regression blockers: GOING-LIVE-BASKETS-20261115 (2026-11-15).

Defect class: the Conversion Program's overnight family
(CONV-01, 02, 03, 04, 163) stood SHADOW-ARMED only, and the
owner ruled Sun 2026-11-15 22:35 ET that no shadow sleeves are
allowed: they have to be live. Two stacked feed facts would
have kept the live form from ever firing honestly:

- Seven basket names (SOXX, TSM, AMAT, FLNC, EOSE, CEG, XLE)
  were in no warm list, so the live snapshot carried no bars
  for them: energy8 could resolve only 4 of its 8 names, below
  its registered 6-name floor, on every night.
- No overnight basket engine existed on the desk at all: no
  sleeve entered a basket at the close and exited it at the
  next open.

Cure (this landing): desk3/overnight_baskets.py (one engine,
five live sleeves, own_book_view so each basket exits exactly
its own book), warm desk_symbols serving the seven missing
names, and config/overnight_baskets_20261115.json registering
each basket's falsifier and kill rule byte-identical to its
Conversion Register row, the riding components (CONV-05, 06,
119) and the blocked rows (CONV-104, CONV-86) with their exact
missing sources named.

Fail direction: on the pre-change tree at commit a0a481f the
engine module, its adapters, the registry file and the warm
names do not exist, so the import and membership tests error
or fail; the floor, drop, exit and sizing tests have no
engine to run against.
"""
import json
import os
import unittest

from desk3 import overnight_baskets as ob
from desk3.warm import desk_symbols

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.expanduser(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/"
    "pass2/CONVERSION-REGISTER-2026-11-15.jsonl")

# 2026-11-16 is a Monday; 15:55 ET is 20:55 UTC (EST).
ENTRY_NOW = "2026-11-16T20:55:00Z"
EXIT_NOW = "2026-11-17T14:35:00Z"  # Tue 09:35 ET
TODAY = "2026-11-16"


def _bar(day, close, open_=None):
    return {"t": f"{day}T05:00:00Z", "o": open_ or close,
            "h": close, "l": close, "c": close, "v": 1000.0}


def _view(names, now=ENTRY_NOW, positions=None, stale=()):
    bars = {}
    for i, sym in enumerate(names):
        day = "2026-11-13" if sym in stale else TODAY
        bars[f"{sym}|1Day"] = [_bar(day, 100.0 + i)]
    return {"now": now, "bars": bars,
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestBasketMembershipAndFloors(unittest.TestCase):
    def test_focus29_is_focus30_minus_sive(self):
        self.assertEqual(len(ob.FOCUS29), 29)
        self.assertNotIn("SIVE", ob.FOCUS29)
        self.assertEqual(set(ob.FOCUS29), {
            "SMH", "SOXX", "NVDA", "AVGO", "AMD", "MRVL", "ARM",
            "TSM", "AMAT", "MU", "SNDK", "WDC", "AAOI", "COHR",
            "LITE", "CRDO", "ALAB", "AXTI", "CRWV", "PLTR",
            "RKLB", "FLNC", "EOSE", "FCEL", "BE", "OKLO", "VST",
            "CEG", "XLE"})

    def test_registered_baskets_and_floors(self):
        self.assertEqual(ob.SPECS["overnight_focus29"]["min_names"], 10)
        self.assertEqual(ob.SPECS["overnight_energy8"]["min_names"], 6)
        self.assertEqual(list(ob.SPECS["overnight_energy8"]["names"]),
                         ["FLNC", "EOSE", "FCEL", "BE", "OKLO", "VST",
                          "CEG", "XLE"])
        self.assertEqual(ob.SPECS["overnight_basket8"]["min_names"], 6)
        self.assertEqual(ob.SPECS["overnight_semis12"]["min_names"], 9)

    def test_exclusion_variant_drops_only_rklb(self):
        names = ob.SPECS["overnight_focus29_ex_rklb"]["names"]
        self.assertEqual(len(names), 28)
        self.assertNotIn("RKLB", names)
        self.assertEqual(set(ob.FOCUS29) - set(names), {"RKLB"})

    def test_below_floor_stays_flat(self):
        # energy8 with only 5 of 8 resolving: below its 6 floor.
        view = _view(ob.ENERGY8[:5])
        self.assertEqual(ob.evaluate("overnight_energy8", view), [])

    def test_at_floor_enters(self):
        view = _view(ob.ENERGY8[:6])
        intents = ob.evaluate("overnight_energy8", view)
        self.assertEqual(len(intents), 6)
        self.assertTrue(all(i.kind == "enter" for i in intents))


class TestDropOnMissingBars(unittest.TestCase):
    def test_missing_name_dropped_never_stale(self):
        # SOXX carries only a stale Friday bar: it must drop,
        # and semis12 falls to 11 present, still above floor 9,
        # entering exactly the 11 fresh names.
        view = _view(ob.SEMIS12, stale=("SOXX",))
        intents = ob.evaluate("overnight_semis12", view)
        syms = [i.symbol for i in intents]
        self.assertEqual(len(intents), 11)
        self.assertNotIn("SOXX", syms)

    def test_absent_name_dropped(self):
        names = [s for s in ob.BASKET8 if s != "AXTI"]
        view = _view(names)
        intents = ob.evaluate("overnight_basket8", view)
        self.assertEqual(len(intents), 7)
        self.assertNotIn("AXTI", [i.symbol for i in intents])

    def test_no_bars_no_entry(self):
        view = {"now": ENTRY_NOW, "bars": {}, "positions": []}
        self.assertEqual(ob.evaluate("overnight_focus29", view), [])


class TestEqualWeightSliceMath(unittest.TestCase):
    def test_equal_weight_over_present_names(self):
        view = _view(ob.BASKET8)
        intents = ob.evaluate("overnight_basket8", view)
        self.assertEqual(len(intents), 8)
        notionals = [i.qty * i.price_hint for i in intents]
        for n in notionals:
            self.assertAlmostEqual(n, 10000.0 / 8, delta=0.02)
        self.assertAlmostEqual(sum(notionals), 10000.0, delta=0.05)

    def test_equal_weight_recomputed_over_survivors(self):
        # One name missing: the slice splits over 7, not 8.
        view = _view([s for s in ob.BASKET8 if s != "MU"])
        intents = ob.evaluate("overnight_basket8", view)
        for i in intents:
            self.assertAlmostEqual(i.qty * i.price_hint,
                                   10000.0 / 7, delta=0.02)


class TestFlatAfterOpenExit(unittest.TestCase):
    def test_exit_window_exits_every_held_name_at_held_qty(self):
        positions = [{"symbol": s, "qty": 12.5}
                     for s in ob.BASKET8[:3]]
        view = _view(ob.BASKET8, now=EXIT_NOW, positions=positions)
        # Exit morning bars: a 1Day bar dated the exit day.
        for sym in ob.BASKET8[:3]:
            view["bars"][f"{sym}|1Day"] = [
                _bar("2026-11-17", 101.0, open_=100.5)]
        intents = ob.evaluate("overnight_basket8", view)
        self.assertEqual(len(intents), 3)
        for i in intents:
            self.assertEqual(i.kind, "exit")
            self.assertEqual(i.side, "sell")
            self.assertEqual(i.position_intent, "sell_to_close")
            self.assertEqual(i.qty, 12.5)
            self.assertEqual(i.price_hint, 100.5)

    def test_no_exit_outside_morning_window(self):
        positions = [{"symbol": "SMH", "qty": 10.0}]
        view = _view(ob.BASKET8, now="2026-11-17T17:00:00Z",
                     positions=positions)
        self.assertEqual(ob.evaluate("overnight_basket8", view), [])

    def test_held_position_blocks_new_entries(self):
        positions = [{"symbol": "SMH", "qty": 10.0}]
        view = _view(ob.BASKET8, positions=positions)
        self.assertEqual(ob.evaluate("overnight_basket8", view), [])

    def test_no_entry_outside_closing_window(self):
        view = _view(ob.BASKET8, now="2026-11-16T18:00:00Z")
        self.assertEqual(ob.evaluate("overnight_basket8", view), [])

    def test_other_sleeves_names_are_not_exited(self):
        # A held name outside this basket is not this sleeve's
        # position to exit (own_book_view serves only its own
        # book live; the engine also filters by basket membership).
        positions = [{"symbol": "SPY", "qty": 5.0}]
        view = _view(ob.BASKET8, now=EXIT_NOW, positions=positions)
        self.assertEqual(ob.evaluate("overnight_basket8", view), [])


class TestWarmServesBasketNames(unittest.TestCase):
    def test_seven_missing_names_now_served(self):
        syms = desk_symbols(ROOT)
        for sym in ("SOXX", "TSM", "AMAT", "FLNC", "EOSE", "CEG",
                    "XLE"):
            self.assertIn(sym, syms)
        self.assertNotIn("SIVE", syms)


class TestRegistryByteIdentical(unittest.TestCase):
    def setUp(self):
        self.doc = json.load(open(os.path.join(
            ROOT, "config", "overnight_baskets_20261115.json")))
        self.reg = {}
        with open(REGISTER) as fh:
            for line in fh:
                if line.strip():
                    d = json.loads(line)
                    self.reg[d["id"]] = d

    def test_baskets_registered_live_with_register_text(self):
        by_conv = {b["conv"]: b for b in self.doc["baskets"]}
        self.assertEqual(set(by_conv), {"CONV-01", "CONV-02",
                                        "CONV-03", "CONV-04",
                                        "CONV-163"})
        for conv, b in by_conv.items():
            self.assertEqual(b["falsifier"],
                             self.reg[conv]["falsifier"])
            self.assertEqual(b["kill_rule"],
                             self.reg[conv]["kill_rule"])
            self.assertIn(b["id"], ob.SPECS)

    def test_components_ride_with_register_text(self):
        by_conv = {c["conv"]: c
                   for c in self.doc["components_riding_conv_01"]}
        self.assertEqual(set(by_conv),
                         {"CONV-05", "CONV-06", "CONV-119"})
        for conv, c in by_conv.items():
            self.assertEqual(c["falsifier"],
                             self.reg[conv]["falsifier"])
            self.assertEqual(c["kill_rule"],
                             self.reg[conv]["kill_rule"])

    def test_blocked_rows_named_with_register_text(self):
        by_conv = {b["conv"]: b for b in self.doc["blocked"]}
        self.assertEqual(set(by_conv), {"CONV-104", "CONV-86"})
        for conv, b in by_conv.items():
            self.assertEqual(b["falsifier"],
                             self.reg[conv]["falsifier"])
            self.assertEqual(b["kill_rule"],
                             self.reg[conv]["kill_rule"])
            self.assertTrue(b["blocked"].startswith("BLOCKED"))


class TestRosterRows(unittest.TestCase):
    def test_config_rows_shape(self):
        rows = ob.config_rows()
        self.assertEqual(len(rows), 5)
        for r in rows:
            self.assertEqual(r["slice"]["capital_usd"], 10000.0)
            self.assertFalse(r["parked"])
            self.assertTrue(r["own_book_view"])
            self.assertEqual(r["inputs"], ["bars", "positions"])
            self.assertTrue(os.path.exists(os.path.join(
                ROOT, "adapters3", f"{r['id']}.py")))


if __name__ == "__main__":
    unittest.main()
