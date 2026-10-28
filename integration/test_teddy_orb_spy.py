"""teddy_orb_spy blockers (TEDDY-ORB-SPY-SPEC-2026-10-28, FROZEN).

Provenance wording per install law: X post by @ThiccTeddy, strategy
from his posted video, installed by owner order 2026-10-28. Edge
UNPROVEN; no backtest is claimed by these tests - they pin the frozen
spec's mechanics.

Golden expectations are computed independently in this file from
hand-set fixture constants (opening range, stop/target/qty from the
spec's math and the install's stated sizing choice), never via the
sleeve's entry logic - except where a test's very subject is a pure
helper (aggregate_5min / opening_range), in which case the expected
values are the hand-worked values below.

Hand-worked fixture (session 2026-10-28, six opening-range 5-min bars):
  highs 101 / 102 / 101.5 / 100.8 / 100.5 / 101.2  -> OR high 102.0
  lows   99 / 100 / 99.5 / 98.5 / 98.8 / 99.2      -> OR low 98.5
  volumes 1000 / 1200 / 800 / 1000 / 1100 / 900    -> mean 1000,
  breakout threshold 1.5x mean = 1500. OR height = 3.5.

Long sequence: breakout close 102.8 on volume 2000 (qualifies);
pullback closes 102.4 (v1200) then 102.2 (v1000), pullback high
103.0; trigger close 103.2 on volume 1500 (> last pullback 1000).
  entry 103.2; stop = 102.0 - 0.10 = 101.90; risk 1.30;
  measured move = 102.0 + 3.5 = 105.5; 2R = 103.2 + 2.6 = 105.8;
  target = min = 105.5;
  qty = floor(min(0.0025*10000/1.30, 0.25*10000/103.2)) = 19.

Short sequence: breakout close 97.8 on volume 2000; pullback closes
98.0 (v1200) then 98.1 (v1000), pullback low 97.4; trigger close
97.2 on volume 1500.
  entry 97.2; stop = 98.5 + 0.10 = 98.60; risk 1.40;
  measured move = 98.5 - 3.5 = 95.0; 2R = 97.2 - 2.8 = 94.4;
  target = max = 95.0;
  qty = floor(min(0.0025*10000/1.40, 0.25*10000/97.2)) = 17.

Fixtures are fed as 1-minute bars (five per 5-minute bar, volume
split evenly), so the tests also pin the core's deterministic
1-minute -> 5-minute aggregation (the desk serves no native
bars:SPY:5Min key; route (b) of the install scout).
"""
from __future__ import annotations

import importlib
import json
import math
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
SESSION = "2026-10-28"
EQUITY = 10000.0

OR_HIGH = 102.0
OR_LOW = 98.5
OR_MEAN_VOL = 1000.0

LONG_ENTRY = 103.2
LONG_STOP = 101.90
LONG_R = LONG_ENTRY - LONG_STOP             # 1.30
LONG_TARGET = 105.5                          # measured move < 2R (105.8)
LONG_QTY = int(math.floor(min(0.0025 * EQUITY / LONG_R,
                              0.25 * EQUITY / LONG_ENTRY)))   # 19

SHORT_ENTRY = 97.2
SHORT_STOP = 98.60
SHORT_R = SHORT_STOP - SHORT_ENTRY           # 1.40
SHORT_TARGET = 95.0                          # measured move > 2R (94.4)
SHORT_QTY = int(math.floor(min(0.0025 * EQUITY / SHORT_R,
                               0.25 * EQUITY / SHORT_ENTRY)))  # 17

# (o, h, l, c, v) per 5-minute bar, index = bars since 09:30 ET.
OR5 = [
    (100.0, 101.0, 99.0, 100.5, 1000),
    (100.5, 102.0, 100.0, 101.0, 1200),
    (101.0, 101.5, 99.5, 100.0, 800),
    (100.0, 100.8, 98.5, 99.0, 1000),
    (99.0, 100.5, 98.8, 100.2, 1100),
    (100.2, 101.2, 99.2, 100.8, 900),
]
LONG_BREAKOUT = (101.0, 103.0, 100.8, 102.8, 2000)
LONG_PULLBACK = [
    (102.8, 103.0, 102.2, 102.4, 1200),
    (102.4, 102.6, 102.0, 102.2, 1000),
]
LONG_TRIGGER = (102.2, 103.4, 102.1, 103.2, 1500)

SHORT_BREAKOUT = (99.0, 99.1, 97.6, 97.8, 2000)
SHORT_PULLBACK = [
    (97.8, 98.2, 97.4, 98.0, 1200),
    (98.0, 98.3, 97.7, 98.1, 1000),
]
SHORT_TRIGGER = (98.1, 98.2, 97.0, 97.2, 1500)


def _mk1(idx5, o, h, l, c, v):
    """Expand one 5-minute bar into its five 1-minute constituents:
    minute 0 carries the open and the full range, minutes 1-3 sit at
    the open, minute 4 carries the close. Aggregation must rebuild
    exactly (o, h, l, c, v). Requires v divisible by 5."""
    assert v % 5 == 0
    base = datetime(2026, 10, 28, 9, 30, tzinfo=ET).timestamp() + idx5 * 300
    out = []
    specs = [(o, h, l, o), (o, o, o, o), (o, o, o, o), (o, o, o, o),
             (o, max(o, c), min(o, c), c)]
    for k, (mo, mh, ml, mc) in enumerate(specs):
        out.append({"t": base + k * 60, "o": float(mo), "h": float(mh),
                    "l": float(ml), "c": float(mc), "v": float(v // 5)})
    return out


def to_1min(bars5_with_idx):
    out = []
    for idx, spec in bars5_with_idx:
        out.extend(_mk1(idx, *spec))
    return out


def long_sequence():
    specs = list(OR5) + [LONG_BREAKOUT] + LONG_PULLBACK + [LONG_TRIGGER]
    return [(i, s) for i, s in enumerate(specs)]


def short_sequence():
    specs = list(OR5) + [SHORT_BREAKOUT] + SHORT_PULLBACK + [SHORT_TRIGGER]
    return [(i, s) for i, s in enumerate(specs)]


def drive(seq, state=None, position=None, equity=EQUITY):
    """Feed the 5-minute sequence one completed bar at a time
    (adapter-style teddy_state round-trip). Returns (decisions,
    final_state); decisions = [(idx5, intent)]."""
    from core.sleeve import Context
    from sleeves.teddy_orb_spy import TeddyOrbSpySleeve
    sleeve = TeddyOrbSpySleeve()
    state = dict(state or {})
    pos = dict(position or {})
    decisions = []
    for end in range(1, len(seq) + 1):
        part = seq[:end]
        bars1 = to_1min(part)
        idx, spec = part[-1]
        now = datetime(2026, 10, 28, 9, 30, tzinfo=ET).timestamp() \
            + idx * 300 + 300
        ctx = Context(now=now, session=SESSION, equity=equity,
                      extra={"teddy_state": state})
        intents = sleeve.signal({"SPY": bars1}, pos, ctx) or []
        state = sleeve.teddy_state
        for it in intents:
            decisions.append((idx, it))
            if it.kind == "enter":
                pos = {"SPY": it.qty if it.side == "buy" else -it.qty}
            else:
                cur = pos.get("SPY", 0.0)
                new = cur + it.qty if cur < 0 else cur - it.qty
                pos = {"SPY": new} if new != 0 else {}
    return decisions, state


class TestAggregationAndRange(unittest.TestCase):
    def test_aggregation_rebuilds_5min_bars_exactly(self):
        from sleeves.teddy_orb_spy import aggregate_5min
        bars5 = aggregate_5min(to_1min(long_sequence()))
        expect = list(OR5) + [LONG_BREAKOUT] + LONG_PULLBACK + [LONG_TRIGGER]
        self.assertEqual(len(bars5), len(expect))
        for got, (o, h, l, c, v) in zip(bars5, expect):
            self.assertAlmostEqual(got["o"], o, places=6)
            self.assertAlmostEqual(got["h"], h, places=6)
            self.assertAlmostEqual(got["l"], l, places=6)
            self.assertAlmostEqual(got["c"], c, places=6)
            self.assertAlmostEqual(got["v"], v, places=6)

    def test_incomplete_bucket_is_dropped(self):
        from sleeves.teddy_orb_spy import aggregate_5min
        bars1 = to_1min([(i, s) for i, s in enumerate(OR5)])
        bars1 += _mk1(6, *LONG_BREAKOUT)[:3]   # only 3 of 5 minutes
        self.assertEqual(len(aggregate_5min(bars1)), 6)

    def test_opening_range_construction_hand_worked(self):
        from sleeves.teddy_orb_spy import aggregate_5min, opening_range
        bars5 = aggregate_5min(to_1min(long_sequence()))
        orr = opening_range(bars5)
        self.assertAlmostEqual(orr[0], OR_HIGH, places=6)
        self.assertAlmostEqual(orr[1], OR_LOW, places=6)
        self.assertAlmostEqual(orr[2], OR_MEAN_VOL, places=6)

    def test_range_never_moves_after_1000(self):
        from sleeves.teddy_orb_spy import aggregate_5min, opening_range
        wild = [(10, (500.0, 900.0, 1.0, 500.0, 999995)),
                (11, (500.0, 900.0, 1.0, 500.0, 999995))]
        bars5 = aggregate_5min(to_1min(long_sequence() + wild))
        orr = opening_range(bars5)
        self.assertAlmostEqual(orr[0], OR_HIGH, places=6)
        self.assertAlmostEqual(orr[1], OR_LOW, places=6)
        self.assertAlmostEqual(orr[2], OR_MEAN_VOL, places=6)


class TestBreakoutQualification(unittest.TestCase):
    def test_high_volume_breakout_qualifies_but_does_not_enter(self):
        from core.sleeve import Context
        from sleeves.teddy_orb_spy import TeddyOrbSpySleeve
        seq = [(i, s) for i, s in enumerate(list(OR5) + [LONG_BREAKOUT])]
        sleeve = TeddyOrbSpySleeve()
        now = datetime(2026, 10, 28, 9, 30, tzinfo=ET).timestamp() + 6 * 300 + 300
        ctx = Context(now=now, session=SESSION, equity=EQUITY,
                      extra={"teddy_state": {}})
        out = sleeve.signal({"SPY": to_1min(seq)}, {}, ctx)
        self.assertEqual(out, [])
        self.assertEqual(sleeve.last_evaluation["state"], "setup_pending")
        self.assertAlmostEqual(sleeve.last_evaluation["or_high"], OR_HIGH)

    def test_low_volume_break_must_not_qualify(self):
        low = (101.0, 103.0, 100.8, 102.8, 1400)   # 1400 < 1.5 * 1000
        specs = list(OR5) + [low] + LONG_PULLBACK + [LONG_TRIGGER]
        seq = [(i, s) for i, s in enumerate(specs)]
        decisions, _ = drive(seq)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestGoldenEntries(unittest.TestCase):
    def test_long_pullback_continuation_entry_to_the_cent(self):
        decisions, state = drive(long_sequence())
        entries = [(i, it) for i, it in decisions if it.kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        idx, it = entries[0]
        self.assertEqual(idx, 9)
        self.assertEqual(it.symbol, "SPY")
        self.assertEqual(it.side, "buy")
        self.assertEqual(it.position_intent, "buy_to_open")
        self.assertAlmostEqual(it.price_hint, LONG_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, LONG_STOP, places=6)
        self.assertAlmostEqual(it.target, LONG_TARGET, places=6)
        self.assertEqual(it.qty, LONG_QTY)
        rules = {r.kind: r.value for r in it.exit_rules}
        self.assertAlmostEqual(rules["stop"], LONG_STOP, places=6)
        self.assertAlmostEqual(rules["target"], LONG_TARGET, places=6)
        plan = state["plan"]
        self.assertEqual(plan["direction"], 1)
        self.assertAlmostEqual(plan["or_high"], OR_HIGH, places=6)

    def test_short_pullback_continuation_entry_to_the_cent(self):
        decisions, state = drive(short_sequence())
        entries = [(i, it) for i, it in decisions if it.kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        idx, it = entries[0]
        self.assertEqual(idx, 9)
        self.assertEqual(it.side, "sell")
        self.assertEqual(it.position_intent, "sell_to_open")
        self.assertAlmostEqual(it.price_hint, SHORT_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, SHORT_STOP, places=6)
        self.assertAlmostEqual(it.target, SHORT_TARGET, places=6)
        self.assertEqual(it.qty, SHORT_QTY)
        self.assertEqual(state["plan"]["direction"], -1)


class TestInvalidation(unittest.TestCase):
    def test_pullback_close_back_inside_invalidates_before_entry(self):
        inside = (102.4, 102.6, 101.2, 101.5, 1000)   # close inside OR
        strong = (102.0, 103.4, 101.9, 103.2, 3000)   # would-be trigger
        specs = list(OR5) + [LONG_BREAKOUT, inside, strong]
        seq = [(i, s) for i, s in enumerate(specs)]
        decisions, _ = drive(seq)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])

    def test_post_entry_close_inside_exits(self):
        inside = (103.0, 103.2, 101.5, 101.8, 1300)   # close back inside
        seq = long_sequence() + [(10, inside)]
        decisions, state = drive(seq)
        entries = [d for d in decisions if d[1].kind == "enter"]
        exits = [(i, it) for i, it in decisions if it.kind == "exit"]
        self.assertEqual(len(entries), 1, decisions)
        self.assertEqual(len(exits), 1, decisions)
        idx, it = exits[0]
        self.assertEqual(idx, 10)
        self.assertEqual(it.qty, LONG_QTY)
        self.assertEqual(it.side, "sell")
        self.assertIn("inside", it.reason)
        self.assertIsNone(state["plan"])
        self.assertIn(1, state["dead_directions"])

    def test_higher_volume_pullback_must_not_produce_entry(self):
        hot = (102.8, 103.0, 102.2, 102.4, 2500)   # pullback vol >= breakout 2000
        specs = list(OR5) + [LONG_BREAKOUT, hot,
                             LONG_PULLBACK[1], LONG_TRIGGER]
        seq = [(i, s) for i, s in enumerate(specs)]
        decisions, _ = drive(seq)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestFlatAndCutoff(unittest.TestCase):
    def test_hard_flat_1400(self):
        from core.sleeve import Context
        from sleeves.teddy_orb_spy import TeddyOrbSpySleeve
        _, state = drive(long_sequence())
        sleeve = TeddyOrbSpySleeve()
        flat_idx = 53   # 13:55 ET
        seq = long_sequence() + [(flat_idx, (103.0, 103.2, 102.9, 103.0, 1000))]
        now = datetime(2026, 10, 28, 14, 0, tzinfo=ET).timestamp()
        ctx = Context(now=now, session=SESSION, equity=EQUITY,
                      extra={"teddy_state": state})
        out = sleeve.signal({"SPY": to_1min(seq)}, {"SPY": LONG_QTY}, ctx)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertIn("14:00", out[0].reason)

    def test_no_entry_at_1230_cutoff(self):
        filler = (100.5, 101.0, 100.0, 100.5, 900)   # inside the range
        specs = list(OR5) + [filler] * 23 + [LONG_BREAKOUT]
        pullback = []
        prev_c = 102.8
        for k in range(6):
            c = round(prev_c - 0.1 * (k + 1) + 0.1, 4) if k == 0 else round(102.8 - 0.1 * k, 4)
            c = round(102.7 - 0.1 * k, 4)
            pullback.append((prev_c, max(prev_c, c) + 0.2, min(prev_c, c) - 0.2, c, 1000))
            prev_c = c
        specs += pullback + [(102.1, 103.5, 102.0, 103.3, 1500)]  # trigger at 12:30
        seq = [(i, s) for i, s in enumerate(specs)]
        self.assertEqual(len(seq), 6 + 23 + 1 + 6 + 1)
        decisions, _ = drive(seq)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestCausality(unittest.TestCase):
    def test_future_bars_never_change_entry(self):
        base, _ = drive(long_sequence())
        base_entries = [(i, it.qty, round(it.stop, 6), round(it.target, 6))
                        for i, it in base if it.kind == "enter"]
        mutated = long_sequence() + [
            (10, (50.0, 900.0, 1.0, 50.0, 999995)),
            (11, (50.0, 900.0, 1.0, 50.0, 999995))]
        alt, _ = drive(mutated)
        # The wild bar at idx 10 closes inside the range, so an exit
        # may follow; the ENTRY itself must be bit-identical.
        alt_entries = [(i, it.qty, round(it.stop, 6), round(it.target, 6))
                       for i, it in alt if it.kind == "enter"]
        self.assertEqual(base_entries, alt_entries)

    def test_truncation_never_changes_earlier_decisions(self):
        inside = (103.0, 103.2, 101.5, 101.8, 1300)
        seq = long_sequence() + [(10, inside)]
        full, _ = drive(seq)
        full_map = {i: (it.kind, it.qty) for i, it in full}
        for cut in (6, 8, 9, 10):
            part, _ = drive(seq[:cut])
            for i, it in part:
                self.assertEqual((it.kind, it.qty), full_map[i])


class TestAdapterDrive(unittest.TestCase):
    def test_adapter_drive_matches_core(self):
        mod = importlib.import_module("adapters3.teddy_orb_spy")
        bars1 = to_1min(long_sequence())
        iso_bars = [dict(b, t=datetime.fromtimestamp(b["t"], timezone.utc).isoformat())
                    for b in bars1]
        view = {"now": datetime.fromtimestamp(bars1[-1]["t"] + 60, tz=ET).isoformat(),
                "bars": {"SPY|1Min": iso_bars}, "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
            self.assertTrue(os.path.exists(
                os.path.join(td, "teddy_state.json")))
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["qty"], LONG_QTY)
        self.assertAlmostEqual(entries[0]["stop_price"], LONG_STOP, places=6)
        self.assertAlmostEqual(entries[0]["target"], LONG_TARGET, places=6)
        self.assertTrue(entries[0]["intent_id"].startswith("teddy_orb_spy-"))


class TestInstallWiring(unittest.TestCase):
    def test_config_row_and_roster_delta(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 316)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        teddy = [r for r in rows if r["id"] == "teddy_orb_spy"]
        self.assertEqual(len(teddy), 1)
        row = teddy[0]
        self.assertEqual(row["module"], "adapters3.teddy_orb_spy")
        self.assertFalse(row["parked"])
        self.assertEqual(row["slice"]["capital_usd"], 10000.0)
        self.assertEqual(row["session"], "rth")
        self.assertEqual(row["cadence_s"], 60)
        self.assertFalse(row["flat_by_close"])
        self.assertIsNone(row["flatten_time_et"])
        for key in ("bars", "bars_1min", "bars:SPY:1Min", "positions",
                    "quotes", "session_fills"):
            self.assertIn(key, row["inputs"])

    def test_inputs_declared_and_producer_key(self):
        mod = importlib.import_module("adapters3.teddy_orb_spy")
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        row = [r for r in cfg["sleeves"] if r["id"] == "teddy_orb_spy"][0]
        self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]))
        from desk3.producers_g4 import _BARS_TF_KEYS
        self.assertIn("bars:SPY:1Min", _BARS_TF_KEYS)


if __name__ == "__main__":
    unittest.main()
