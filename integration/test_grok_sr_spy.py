"""grok_sr_spy blockers (GROK-SR-SPY-SPEC-2026-10-28, FROZEN).

Provenance wording per install law: X post by @thiccteddy, algo by
Grok, installed by owner order 2026-10-28. Edge UNPROVEN; no backtest
is claimed by these tests - they pin the frozen spec's mechanics.

Golden expectations are computed independently in this file from
hand-set fixture constants (band edges from the spec's clustering
rules worked by hand; stop/target/qty from the spec's math and the
install's stated sizing choice), never via the sleeve's helpers -
except where a test's very subject is a helper (build_zones), in
which case the expected bands are the hand-worked values below.

Hand-worked zone fixture (prior session, 60 flat bars c=100 v=1000,
one pivot high 102.0 at idx 20, one pivot low 98.0 at idx 40):
  * pivot items: 98.0 and 102.0, one touch each;
  * volume-at-price: a single 0.10 bin at close 100 (node price
    100.05) holding 100% of volume, at/above the 90th percentile;
  * all gaps > 0.40, so three singleton clusters, each expanded
    symmetrically to the 0.40 minimum width:
    [97.80, 98.20], [99.85, 100.25], [101.80, 102.20].
"""
from __future__ import annotations

import importlib
import json
import math
import os
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
PRIOR_DAY = 27
SESSION = "2026-10-28"
EQUITY = 10000.0

BAND_SUP = (97.80, 98.20)
BAND_NODE = (99.85, 100.25)
BAND_RES = (101.80, 102.20)

# Fade short at resistance, signal close 101.90 (hand math):
FADE_ENTRY = 101.90
FADE_STOP = 102.20 + 0.10                    # band top + 0.10
FADE_R = FADE_STOP - FADE_ENTRY              # 0.40
FADE_TARGET = FADE_ENTRY - 2 * FADE_R        # 2R (101.10) closer than node edge (dist 1.65)
FADE_QTY = int(math.floor(min(0.0025 * EQUITY / FADE_R,
                              0.25 * EQUITY / FADE_ENTRY)))   # 24

# Breakout long through resistance, signal close 102.50 (hand math):
BO_ENTRY = 102.50
BO_STOP = 101.80 - 0.10                      # band bottom - 0.10
BO_R = BO_ENTRY - BO_STOP                    # 0.80
BO_TARGET = BO_ENTRY + 2 * BO_R              # 104.10; no band above entry
BO_QTY = int(math.floor(min(0.0025 * EQUITY / BO_R,
                            0.25 * EQUITY / BO_ENTRY)))       # 24


def _bar(day, i, o, h, l, c, v):
    t = datetime(2026, 10, day, 9, 30, tzinfo=ET).timestamp() + i * 60
    return {"t": t, "o": float(o), "h": float(h), "l": float(l),
            "c": float(c), "v": float(v)}


def prior_bars():
    bars = [_bar(PRIOR_DAY, i, 100, 100.2, 99.8, 100, 1000) for i in range(60)]
    bars[20] = _bar(PRIOR_DAY, 20, 100, 102.0, 99.8, 100, 1000)   # pivot high
    bars[40] = _bar(PRIOR_DAY, 40, 100, 100.2, 98.0, 100, 1000)   # pivot low
    return bars


def _flat_today(n=24):
    return [_bar(28, i, 100.5, 100.6, 100.4, 100.5, 1000) for i in range(n)]


def fade_today():
    bars = _flat_today()
    # Rejection at resistance: wick 102.6-101.9=0.7 >= 0.5*(102.6-101.4)=0.6,
    # close back inside the band, volume 2000 > 1.5 * trailing avg 1000.
    bars.append(_bar(28, 24, 101.0, 102.6, 101.4, 101.9, 2000))
    return bars


def breakout_today():
    bars = _flat_today()
    # Decisive close 102.50 > 102.20+0.10; body 1.0 >= 0.6*1.2 range;
    # volume 2000 > prior 1000 and >= 1.2 * trailing avg 1000.
    bars.append(_bar(28, 24, 101.5, 102.6, 101.4, 102.5, 2000))
    return bars


def drive(today, prior=None, equity=EQUITY, state=None, position=None):
    """Feed bars one at a time (adapter-style state round-trip).
    Returns (decisions, final_state); decisions = [(today_idx, intent)]."""
    from core.sleeve import Context
    from sleeves.grok_sr_spy import GrokSrSpySleeve
    sleeve = GrokSrSpySleeve()
    prior = prior_bars() if prior is None else prior
    state = dict(state or {})
    pos = dict(position or {})
    decisions = []
    for end in range(1, len(today) + 1):
        latest = today[end - 1]
        ctx = Context(now=latest["t"] + 60, session=SESSION, equity=equity,
                      extra={"grok_state": state})
        intents = sleeve.signal({"SPY": prior + today[:end]}, pos, ctx) or []
        state = sleeve.grok_state
        for it in intents:
            decisions.append((end - 1, it))
            if it.kind == "enter":
                pos = {"SPY": it.qty if it.side == "buy" else -it.qty}
            else:
                cur = pos.get("SPY", 0.0)
                new = cur + it.qty if cur < 0 else cur - it.qty
                pos = {"SPY": new} if new != 0 else {}
    return decisions, state


class TestGoldenZones(unittest.TestCase):
    def test_zone_clustering_hand_worked(self):
        from sleeves.grok_sr_spy import build_zones
        bands = build_zones(prior_bars())
        self.assertEqual([(b["low"], b["high"]) for b in bands],
                         [BAND_SUP, BAND_NODE, BAND_RES])
        self.assertEqual([b["touches"] for b in bands], [1, 0, 1])
        for b in bands:
            self.assertAlmostEqual(b["score"], 1.0, places=9)

    def test_zone_split_at_largest_gap(self):
        from sleeves.grok_sr_spy import build_zones
        bars = [_bar(26, i, 90, 90.2, 89.8, 90, 1000) for i in range(120)]
        # Pivot highs 100.00 / 100.30 / 100.68 / 100.98: chain gaps
        # 0.30 / 0.38 / 0.30 (all <= 0.40, so one cluster), width 0.98
        # > 0.80, largest internal gap 0.38 -> split into two pairs,
        # each widened from 0.30 to the 0.40 minimum symmetrically.
        for j, px in enumerate((100.0, 100.3, 100.68, 100.98)):
            idx = 20 + j * 25
            bars[idx] = _bar(26, idx, 90, px, 89.8, 90, 1000)
        bands = build_zones(bars)
        pairs = [(b["low"], b["high"]) for b in bands]
        self.assertIn((99.95, 100.35), pairs)
        self.assertIn((100.63, 101.03), pairs)
        wide = [p for p in pairs if p[1] - p[0] > 0.80]
        self.assertEqual(wide, [])


class TestGoldenFade(unittest.TestCase):
    def test_fade_short_entry_math_to_the_cent(self):
        decisions, state = drive(fade_today())
        entries = [(i, it) for i, it in decisions if it.kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        idx, it = entries[0]
        self.assertEqual(idx, 24)
        self.assertEqual(it.symbol, "SPY")
        self.assertEqual(it.side, "sell")
        self.assertEqual(it.position_intent, "sell_to_open")
        self.assertAlmostEqual(it.price_hint, FADE_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, FADE_STOP, places=6)
        self.assertAlmostEqual(it.target, FADE_TARGET, places=6)
        self.assertEqual(it.qty, FADE_QTY)
        rules = {r.kind: r.value for r in it.exit_rules}
        self.assertAlmostEqual(rules["stop"], FADE_STOP, places=6)
        self.assertAlmostEqual(rules["target"], FADE_TARGET, places=6)
        plan = state["plan"]
        self.assertEqual(plan["setup"], "fade")
        self.assertEqual(plan["direction"], -1)
        self.assertAlmostEqual(plan["band_high"], BAND_RES[1], places=6)

    def test_fade_needs_volume_confirmation(self):
        today = fade_today()
        today[-1] = _bar(28, 24, 101.0, 102.6, 101.4, 101.9, 1400)  # <= 1.5x avg
        decisions, _ = drive(today)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestGoldenBreakout(unittest.TestCase):
    def test_breakout_long_entry_math_to_the_cent(self):
        decisions, state = drive(breakout_today())
        entries = [(i, it) for i, it in decisions if it.kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        idx, it = entries[0]
        self.assertEqual(idx, 24)
        self.assertEqual(it.side, "buy")
        self.assertEqual(it.position_intent, "buy_to_open")
        self.assertAlmostEqual(it.price_hint, BO_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, BO_STOP, places=6)
        self.assertAlmostEqual(it.target, BO_TARGET, places=6)
        self.assertEqual(it.qty, BO_QTY)
        self.assertEqual(state["plan"]["setup"], "breakout")

    def test_breakout_needs_expanding_volume(self):
        today = breakout_today()
        today[-1] = _bar(28, 24, 101.5, 102.6, 101.4, 102.5, 900)  # < prior bar vol
        decisions, _ = drive(today)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestReclaimInvalidation(unittest.TestCase):
    def _after_entry(self, extra_bars):
        today = fade_today() + extra_bars
        return drive(today)

    def test_reclaim_within_3_bars_exits(self):
        extra = [
            _bar(28, 25, 101.6, 101.8, 101.3, 101.5, 1000),   # fill bar, holds
            _bar(28, 26, 102.0, 102.7, 101.9, 102.5, 1000),   # close back above band top
        ]
        decisions, state = self._after_entry(extra)
        exits = [(i, it) for i, it in decisions if it.kind == "exit"]
        self.assertEqual(len(exits), 1, decisions)
        idx, it = exits[0]
        self.assertEqual(idx, 26)  # entry idx 24; fill bar 25; reclaim bar 26 (<= 3 after fill)
        self.assertEqual(it.qty, FADE_QTY)
        self.assertEqual(it.side, "buy")
        self.assertIn("reclaim", it.reason)
        self.assertIsNone(state["plan"])
        self.assertIn("101.80-102.20", state["dead_bands"])

    def test_reclaim_on_bar_4_does_not_exit(self):
        extra = [
            _bar(28, 25, 101.6, 101.8, 101.3, 101.5, 1000),
            _bar(28, 26, 101.6, 101.8, 101.3, 101.5, 1000),
            _bar(28, 27, 101.6, 101.8, 101.3, 101.5, 1000),
            _bar(28, 28, 102.0, 102.7, 101.9, 102.5, 1000),   # 4th bar after fill bar: lapsed
        ]
        decisions, state = self._after_entry(extra)
        self.assertEqual([d for d in decisions if d[1].kind == "exit"], [])
        self.assertIsNotNone(state["plan"])

    def test_hard_flat_1300(self):
        from core.sleeve import Context
        from sleeves.grok_sr_spy import GrokSrSpySleeve
        _, state = drive(fade_today())
        sleeve = GrokSrSpySleeve()
        bar = _bar(28, 210, 101.6, 101.8, 101.3, 101.5, 1000)  # 13:00 ET
        ctx = Context(now=bar["t"] + 60, session=SESSION, equity=EQUITY,
                      extra={"grok_state": state})
        out = sleeve.signal({"SPY": prior_bars() + [bar]}, {"SPY": -FADE_QTY}, ctx)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertIn("13:00", out[0].reason)


class TestCaps(unittest.TestCase):
    def test_max_entries_3_per_session(self):
        state = {"day": SESSION, "entries_today": 3, "plan": None,
                 "dead_bands": []}
        decisions, _ = drive(fade_today(), state=state)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])

    def test_no_entries_after_1130(self):
        today = fade_today()
        # Re-time the whole session so the signal bar starts at 11:30.
        shifted = []
        base = datetime(2026, 10, 28, 11, 6, tzinfo=ET).timestamp()
        for i, b in enumerate(today):
            shifted.append(dict(b, t=base + i * 60))
        decisions, _ = drive(shifted)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestCausality(unittest.TestCase):
    def test_zones_identical_with_or_without_today(self):
        from sleeves.grok_sr_spy import zones_for
        prior = prior_bars()
        wild_today = [_bar(28, i, 500, 900.0, 1.0, 500, 999999) for i in range(30)]
        self.assertEqual(zones_for(prior, SESSION),
                         zones_for(prior + wild_today, SESSION))

    def test_future_bars_never_change_entry(self):
        base, _ = drive(fade_today())
        base_entries = [(i, it.qty, round(it.stop, 6), round(it.target, 6))
                        for i, it in base if it.kind == "enter"]
        mutated = fade_today() + [
            _bar(28, 25, 50, 900.0, 1.0, 50, 999999),
            _bar(28, 26, 50, 900.0, 1.0, 50, 999999)]
        alt, _ = drive(mutated)
        alt_entries = [(i, it.qty, round(it.stop, 6), round(it.target, 6))
                       for i, it in alt if it.kind == "enter"]
        self.assertEqual(base_entries, alt_entries)

    def test_truncation_never_changes_earlier_decisions(self):
        today = fade_today() + [
            _bar(28, 25, 101.6, 101.8, 101.3, 101.5, 1000),
            _bar(28, 26, 102.0, 102.7, 101.9, 102.5, 1000)]
        full, _ = drive(today)
        full_map = {i: (it.kind, it.qty) for i, it in full}
        for cut in (10, 20, 24, 25):
            part, _ = drive(today[:cut])
            for i, it in part:
                self.assertEqual((it.kind, it.qty), full_map[i])


class TestAdapterDrive(unittest.TestCase):
    def test_adapter_drive_matches_core(self):
        mod = importlib.import_module("adapters3.grok_sr_spy")
        from datetime import timezone as _tz
        bars = prior_bars() + fade_today()
        iso_bars = [dict(b, t=datetime.fromtimestamp(b["t"], _tz.utc).isoformat())
                    for b in bars]
        view = {"now": datetime.fromtimestamp(bars[-1]["t"] + 60, tz=ET).isoformat(),
                "bars": {"SPY|1Min": iso_bars}, "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
            self.assertTrue(os.path.exists(
                os.path.join(td, "grok_state.json")))
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["qty"], FADE_QTY)
        self.assertAlmostEqual(entries[0]["stop_price"], FADE_STOP, places=6)
        self.assertAlmostEqual(entries[0]["target"], FADE_TARGET, places=6)


class TestInstallWiring(unittest.TestCase):
    def test_config_row_and_roster_delta(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 315)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        grok = [r for r in rows if r["id"] == "grok_sr_spy"]
        self.assertEqual(len(grok), 1)
        row = grok[0]
        self.assertEqual(row["module"], "adapters3.grok_sr_spy")
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
        mod = importlib.import_module("adapters3.grok_sr_spy")
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        row = [r for r in cfg["sleeves"] if r["id"] == "grok_sr_spy"][0]
        self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]))
        from desk3.producers_g4 import BarsProjection, _BARS_TF_KEYS
        self.assertIn("bars:SPY:1Min", _BARS_TF_KEYS)
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "state"))
            from datetime import timezone
            now = datetime(2026, 10, 28, 15, 0, tzinfo=timezone.utc)
            doc = {"fetched_at": now.isoformat(),
                   "bars": {"SPY|1Min": [{"t": "x"}] * 100}}
            json.dump(doc, open(os.path.join(td, "state", "warm_bars.json"), "w"))
            proj = BarsProjection(td, ["bars:SPY:1Min"], mode="keys")
            out = proj({"now": now})
        self.assertIn("bars:SPY:1Min", out)
        self.assertEqual(out["bars:SPY:1Min"]["bar_counts"], {"SPY": 100})

    def test_warm_window_serves_10_prior_sessions(self):
        from desk3.warm import INTRADAY_FETCHES
        self.assertIn(("SPY", "1Min", 18), INTRADAY_FETCHES)
        self.assertNotIn(("SPY", "1Min", 10), INTRADAY_FETCHES)


if __name__ == "__main__":
    unittest.main()
