"""SEGMENT-CONSTRUCTION-20261116 blockers (pieces 1-2): the
Focus 29 1Min warm/producer landing and the shared KG-4
intraday segment engine with the CONV-88 / CONV-108 live
sleeves.

Pins:
- warm serves 1Min for every Focus 29 name (list pinned against
  desk3.overnight_baskets.FOCUS29, the FEED80 mechanism) and the
  bars_timeframes producer declares every bars:<SYM>:1Min key;
  BarsProjection serves all 29 keys from a warm cache.
- Segment boundaries are exactly KG-4's (open drive
  09:30-10:30, midday 10:30-15:00, close hour 15:00-16:00 ET),
  priced at the segment joints; an incomplete session (< 380
  RTH bars) prices no segment.
- CONV-88 (ls9_midday_short) shorts only up-drive names for the
  midday segment and covers at the close hour; CONV-108
  (b3_midday_fade_var) shorts the full basket only when all 29
  names are present. Falsifiers in
  config/segment_sleeves_20261116.json are byte-identical to the
  Conversion Register rows.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
REGISTER = os.path.expanduser(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/"
    "CONVERSION-REGISTER-2026-11-15.jsonl")


def synth_rows(drive=0.10, mid=-0.10, close=0.0):
    rows = []
    base = datetime(2026, 11, 13, 14, 30, tzinfo=timezone.utc)
    price = 100.0
    for i in range(390):
        m = 570 + i
        o = price
        if m == 629:
            c = 100 * (1 + drive)
        elif m == 899:
            c = 100 * (1 + drive) * (1 + mid)
        elif m == 959:
            c = 100 * (1 + drive) * (1 + mid) * (1 + close)
        else:
            c = o
        rows.append({"t": (base + timedelta(minutes=i)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"), "o": o, "h": max(o, c),
            "l": min(o, c), "c": c, "v": 1000})
        if m == 629:
            price = 100 * (1 + drive)
        if m == 899:
            price = 100 * (1 + drive) * (1 + mid)
    return rows


class WarmLandingTest(unittest.TestCase):
    def test_warm_1min_list_pinned_to_focus29(self):
        from desk3 import warm
        from desk3.overnight_baskets import FOCUS29
        self.assertEqual(tuple(FOCUS29), warm.FOCUS29_1MIN_SYMBOLS)
        have = {(s, tf) for s, tf, _d in warm.INTRADAY_FETCHES}
        for s in FOCUS29:
            self.assertIn((s, "1Min"), have)

    def test_producer_declares_and_serves_all_29_keys(self):
        from desk3.overnight_baskets import FOCUS29
        from desk3.producers_g4 import BarsProjection, bars_tf_keys
        keys = bars_tf_keys()
        for s in FOCUS29:
            self.assertIn(f"bars:{s}:1Min", keys)
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, "state"))
        now = datetime.now(timezone.utc)
        bars = {f"{s}|1Min": synth_rows() for s in FOCUS29}
        with open(os.path.join(root, "state", "warm_bars.json"),
                  "w") as fh:
            json.dump({"fetched_at": now.isoformat(), "bars": bars},
                      fh)
        out = BarsProjection(root, keys, mode="keys")({"now": now})
        served = [s for s in FOCUS29 if f"bars:{s}:1Min" in out]
        self.assertEqual(29, len(served))


class SegmentEngineTest(unittest.TestCase):
    def test_boundaries_exact_on_known_session(self):
        from desk3 import intraday_segments as seg
        marks = seg.segment_marks(synth_rows(), "2026-11-13",
                                  prev_close=99.0)
        self.assertAlmostEqual(0.10, marks["OPEN_DRIVE"])
        self.assertAlmostEqual(-0.10, marks["MIDDAY"])
        self.assertAlmostEqual(0.0, marks["CLOSE_HOUR"])
        self.assertAlmostEqual(100 / 99 - 1, marks["OVERNIGHT"])

    def test_incomplete_session_prices_nothing(self):
        from desk3 import intraday_segments as seg
        self.assertIsNone(
            seg.segment_marks(synth_rows()[:100], "2026-11-13"))

    def test_segment_names_and_bounds_are_kg4(self):
        from desk3 import intraday_segments as seg
        self.assertEqual((("OPEN_DRIVE", 570, 630),
                          ("MIDDAY", 630, 900),
                          ("CLOSE_HOUR", 900, 960)),
                         seg.SEGMENT_BOUNDS_MIN)


class SleeveTest(unittest.TestCase):
    def _view(self, z, held=None, up=()):
        from desk3.overnight_baskets import FOCUS29
        bars = {f"{s}|1Min": synth_rows(
            drive=0.05 if s in up else -0.05) for s in FOCUS29}
        return {"now": z, "bars": bars, "positions": held or [],
                "slice": {"cash_usd": 10000.0}}

    def test_conv88_shorts_only_up_drive_names(self):
        from desk3 import intraday_segments as seg
        v = self._view("2026-11-13T15:35:00Z", up=("NVDA", "AMD"))
        out = seg.evaluate("ls9_midday_short", v)
        self.assertEqual({"NVDA", "AMD"}, {i.symbol for i in out})
        for i in out:
            self.assertEqual("sell_to_open", i.position_intent)

    def test_conv88_no_entry_before_drive_completes(self):
        from desk3 import intraday_segments as seg
        v = self._view("2026-11-13T15:15:00Z", up=("NVDA",))
        self.assertEqual([], seg.evaluate("ls9_midday_short", v))

    def test_conv108_shorts_full_basket_only_when_complete(self):
        from desk3 import intraday_segments as seg
        v = self._view("2026-11-13T15:35:00Z")
        out = seg.evaluate("b3_midday_fade_var", v)
        self.assertEqual(29, len(out))
        del v["bars"]["NVDA|1Min"]
        self.assertEqual([], seg.evaluate("b3_midday_fade_var", v))

    def test_covers_at_close_hour_at_held_qty(self):
        from desk3 import intraday_segments as seg
        held = [{"symbol": "NVDA", "qty": -10.0}]
        v = self._view("2026-11-13T20:05:00Z", held=held)
        out = seg.evaluate("ls9_midday_short", v)
        self.assertEqual(1, len(out))
        self.assertEqual("buy_to_close", out[0].position_intent)
        self.assertEqual(10.0, out[0].qty)

    def test_roster_and_falsifiers_byte_identical(self):
        from desk3 import intraday_segments as seg
        rows = seg.config_rows()
        cfg = json.load(open(os.path.join(ROOT, "config",
                                          "sleeves.json")))
        roster = {r["id"]: r for r in cfg["sleeves"]}
        for row in rows:
            self.assertIn(row["id"], roster)
            self.assertEqual(row, roster[row["id"]])
        reg = {}
        with open(REGISTER) as fh:
            for line in fh:
                r = json.loads(line)
                if r["id"] in ("CONV-88", "CONV-108"):
                    reg[r["id"]] = r
        doc = json.load(open(os.path.join(
            ROOT, "config", "segment_sleeves_20261116.json")))
        for s in doc["sleeves"]:
            self.assertEqual(reg[s["conv"]]["falsifier"],
                             s["falsifier"])
            self.assertEqual(reg[s["conv"]]["kill_rule"],
                             s["kill_rule"])


if __name__ == "__main__":
    unittest.main()
