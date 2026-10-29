"""Trullas variant family blockers (TRULLAS-VARIANTS-SPEC-2026-10-29).

Per variant trullas_v01..v10: config row shape + INPUTS equality, and
the one-joint difference on a fixed fixture (decisions differ from the
primary's exactly where the joint dictates, and match where the joint
is inert). Plus: primary identity post-refactor on the golden fixture
(entry/stop/TP1/TP2/qty from the primary blockers, recomputed here),
and no variant may act on an unconfirmed pivot.

Fixtures are hand-built bar series; expected geometry for the golden
fixture is computed independently from its known swing constants
(A = 103.8, B = 111.0), never via the sleeve's own helpers.
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
SESSION = "2026-10-23"
EQUITY = 10000.0

A_LOW, B_HIGH = 103.8, 111.0
RANGE_AB = B_HIGH - A_LOW
EXP_ENTRY = B_HIGH - 0.236 * RANGE_AB - 0.01
EXP_STOP = B_HIGH + 0.01
EXP_TP1 = B_HIGH - 0.382 * RANGE_AB
EXP_TP2 = B_HIGH - 0.618 * RANGE_AB
EXP_TP2_V04 = B_HIGH - 0.667 * RANGE_AB
EXP_QTY = int(math.floor(min(
    3 * 0.0025 * EQUITY / (EXP_STOP - EXP_ENTRY),
    0.25 * EQUITY / EXP_ENTRY)))

VARIANT_IDS = [f"trullas_v{i:02d}" for i in range(1, 11)]


def _bar(i, o, h, l, c, v):
    t = datetime(2026, 10, 23, 9, 30, tzinfo=ET).timestamp() + i * 60
    return {"t": t, "o": float(o), "h": float(h), "l": float(l),
            "c": float(c), "v": float(v)}


def golden_bars(wiggle=False):
    """The primary blockers' golden series (bearish triple divergence,
    pivot 1 at index 39, pivot 2 at index 74). `wiggle` dips every
    third close of the second rise by 0.9, pulling RSI at pivot 2 to
    ~67.5 (out of the >70 extreme zone) while the RSI divergence and
    the pivot geometry stay intact."""
    bars = []
    for i in range(30):
        bars.append(_bar(len(bars), 100, 100.2, 99.8, 100, 1000))
    for j in range(10):
        c = 101 + j
        bars.append(_bar(len(bars), c - 1, c + 0.2, c - 1.2, c, 2000))
    bars[-1] = _bar(len(bars) - 1, 109, 110.0, 108.8, 110, 5000)
    for j in range(10):
        c = 109.4 - 0.6 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    for j in range(25):
        c = 104.28 + 0.28 * j
        if wiggle and j % 3 == 2:
            c -= 0.9
        bars.append(_bar(len(bars), round(c - 0.28, 2), round(c + 0.15, 2),
                         round(c - 0.43, 2), round(c, 2), 1200))
    bars[-1] = _bar(len(bars) - 1, 110.7, 111.0, 110.5, 110.9, 2000)
    for j in range(10):
        c = 110.3 - 0.5 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    return bars


def hidden_bars():
    """Lower second high (109.8 < 110.0) with a HIGHER MACD reading:
    a hidden (continuation) divergence. Primary: no setup at all."""
    bars = []
    for i in range(30):
        bars.append(_bar(len(bars), 100, 100.2, 99.8, 100, 1000))
    for j in range(5):
        c = 100.0 + 10.0 * (j + 1) / 5
        bars.append(_bar(len(bars), round(c - 0.3, 2), round(c + 0.2, 2),
                         round(c - 0.5, 2), round(c, 2), 2000))
    bars[-1] = _bar(len(bars) - 1, 109, 110.0, 108.8, 110, 5000)
    for j in range(3):
        c = 110.0 - 2.5 * (j + 1) / 3
        bars.append(_bar(len(bars), round(c + 0.4, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    for j in range(8):
        c = 107.5 + 2.3 * (j + 1) / 8
        bars.append(_bar(len(bars), round(c - 0.3, 2), round(c + 0.15, 2),
                         round(c - 0.4, 2), round(c, 2), 1200))
    bars[-1] = _bar(len(bars) - 1, 109.5, 109.8, 109.3, 109.7, 2000)
    for j in range(10):
        c = 109.3 - 0.5 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    return bars


def fallo_bars():
    """Higher second high (110.5 > 110.0) with MACD NOT diverging
    (higher at the second high), but the MACD line never crosses up
    through its signal line in the 5 bars after the second extreme
    and the extreme stays intact: a fallo de MACD. Primary: no setup."""
    bars = []
    for i in range(30):
        bars.append(_bar(len(bars), 110, 110.2, 109.8, 110, 1000))
    for j in range(10):
        c = 110.0 - 15.0 * (j + 1) / 10
        bars.append(_bar(len(bars), round(c + 0.3, 2), round(c + 0.3, 2),
                         round(c - 0.3, 2), round(c, 2), 1500))
    for j in range(15):
        c = 95.0 + 15.0 * (j + 1) / 15
        bars.append(_bar(len(bars), round(c - 0.3, 2), round(c + 0.2, 2),
                         round(c - 0.5, 2), round(c, 2), 2000))
    bars[-1] = _bar(len(bars) - 1, 109, 110.0, 108.8, 110, 5000)
    for j in range(6):
        c = 110.0 - 2.5 * (j + 1) / 6
        bars.append(_bar(len(bars), round(c + 0.4, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    for j in range(15):
        c = 107.5 + 3.0 * (j + 1) / 15
        bars.append(_bar(len(bars), round(c - 0.3, 2), round(c + 0.15, 2),
                         round(c - 0.4, 2), round(c, 2), 1200))
    bars[-1] = _bar(len(bars) - 1, 110.2, 110.5, 110.0, 110.4, 2000)
    for j in range(10):
        c = 110.0 - 0.5 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    return bars


def sleeve_of(vid):
    mod = importlib.import_module(f"sleeves.{vid}")
    return mod.TrullasDivergenceSleeve()


def drive(vid, bars, equity=EQUITY):
    """Bar-by-bar drive of a variant (or the primary) sleeve class."""
    from core.sleeve import Context
    if vid == "trullas_divergence":
        from sleeves.trullas_divergence import TrullasDivergenceSleeve
        sleeve = TrullasDivergenceSleeve()
    else:
        sleeve = sleeve_of(vid)
    state, pos, decisions = {}, {}, []
    for end in range(1, len(bars) + 1):
        latest = bars[end - 1]
        ctx = Context(now=latest["t"] + 60, session=SESSION, equity=equity,
                      extra={"trullas_state": state})
        intents = sleeve.signal({"QQQ": bars[:end]}, pos, ctx) or []
        state = sleeve.trullas_state
        for it in intents:
            decisions.append((end - 1, it))
            if it.kind == "enter":
                cur = pos.get("QQQ", 0.0)
                pos = {"QQQ": cur + (-it.qty if it.side == "sell" else it.qty)}
            else:
                cur = pos.get("QQQ", 0.0)
                new = cur + it.qty if cur < 0 else cur - it.qty
                pos = {"QQQ": new} if new != 0 else {}
    return decisions, state


def setups_of(vid, bars):
    from sleeves.trullas_divergence import PRIMARY_PARAMS, detect_setups
    if vid == "trullas_divergence":
        return detect_setups(bars, PRIMARY_PARAMS)
    return detect_setups(bars, sleeve_of(vid).PARAMS)


def entries(decisions):
    return [(i, it) for i, it in decisions if it.kind == "enter"]


class TestPrimaryIdentityPostRefactor(unittest.TestCase):
    def test_primary_golden_unchanged(self):
        decisions, _ = drive("trullas_divergence", golden_bars())
        ents = entries(decisions)
        self.assertEqual(len(ents), 1, decisions)
        idx, it = ents[0]
        self.assertEqual(idx, 79)
        self.assertAlmostEqual(it.price_hint, EXP_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, EXP_STOP, places=6)
        self.assertAlmostEqual(it.target, EXP_TP2, places=6)
        self.assertEqual(it.qty, EXP_QTY)
        _, state = drive("trullas_divergence", golden_bars()[:idx + 1])
        self.assertAlmostEqual(state["plan"]["tp1"], EXP_TP1, places=6)
        self.assertAlmostEqual(state["plan"]["tp2"], EXP_TP2, places=6)


class TestNoUnconfirmedPivot(unittest.TestCase):
    def test_no_variant_acts_before_confirmation(self):
        # Pivot 2 sits at index 74; with only bars[:75] no variant
        # (even k=3, confirming at 77) may hold a pending setup or enter.
        bars = golden_bars()
        for vid in ["trullas_divergence"] + VARIANT_IDS:
            decisions, state = drive(vid, bars[:75])
            self.assertEqual(entries(decisions), [], vid)
            self.assertIsNone(state.get("pending"), vid)


class TestVariantJoints(unittest.TestCase):
    def test_v01_adapter_requests_5min_and_matches_primary_math(self):
        src = open(os.path.join(ROOT, "adapters", "trullas_v01.py")).read()
        self.assertIn('bars_old(ctx, "QQQ", "5Min", 4000)', src)
        # Strategy math identical: the golden series fed as bars
        # produces the primary's exact entry through the v01 adapter.
        mod = importlib.import_module("adapters3.trullas_v01")
        bars = golden_bars()[:83]
        from datetime import timezone as _tz
        iso = [dict(b, t=datetime.fromtimestamp(b["t"], _tz.utc).isoformat())
               for b in bars]
        view = {"now": datetime.fromtimestamp(bars[-1]["t"] + 60, ET).isoformat(),
                "bars": {"QQQ|5Min": iso}, "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        ents = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(ents), 1, out)
        self.assertEqual(ents[0]["qty"], EXP_QTY)
        self.assertAlmostEqual(ents[0]["stop_price"], EXP_STOP, places=6)
        self.assertAlmostEqual(ents[0]["target"], EXP_TP2, places=6)

    def test_v02_pivot_k3_confirms_earlier(self):
        bars = golden_bars()
        prim = setups_of("trullas_divergence", bars)
        var = setups_of("trullas_v02", bars)
        pair_p = [s for s in prim if s["second_index"] == 74]
        pair_v = [s for s in var if s["second_index"] == 74]
        self.assertEqual(len(pair_p), 1)
        self.assertEqual(len(pair_v), 1)
        self.assertEqual(pair_p[0]["confirm_index"], 79)
        self.assertEqual(pair_v[0]["confirm_index"], 77)  # 74 + k(3)
        self.assertAlmostEqual(pair_v[0]["entry_trigger"],
                               pair_p[0]["entry_trigger"], places=6)
        ents = entries(drive("trullas_v02", bars)[0])
        self.assertEqual(len(ents), 1)
        self.assertLess(ents[0][0], 79)  # enters before the primary can

    def test_v03_pivot_k8_confirms_later(self):
        bars = golden_bars()
        var = setups_of("trullas_v03", bars)
        pair_v = [s for s in var if s["second_index"] == 74]
        self.assertEqual(len(pair_v), 1)
        self.assertEqual(pair_v[0]["confirm_index"], 82)  # 74 + k(8)
        ents = entries(drive("trullas_v03", bars)[0])
        self.assertEqual(len(ents), 1)
        self.assertGreaterEqual(ents[0][0], 82)

    def test_v04_tp2_at_667(self):
        decisions, _ = drive("trullas_v04", golden_bars())
        ents = entries(decisions)
        self.assertEqual(len(ents), 1)
        _, it = ents[0]
        self.assertAlmostEqual(it.price_hint, EXP_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, EXP_STOP, places=6)
        self.assertAlmostEqual(it.target, EXP_TP2_V04, places=6)
        self.assertNotAlmostEqual(it.target, EXP_TP2, places=4)

    def test_v05_hidden_divergence_admitted(self):
        bars = hidden_bars()
        self.assertEqual(setups_of("trullas_divergence", bars), [])
        var = setups_of("trullas_v05", bars)
        self.assertEqual(len(var), 1)
        self.assertEqual(var[0]["direction"], -1)  # highs pair -> short
        self.assertLess(var[0]["second_price"], var[0]["first_price"])
        self.assertGreater(var[0]["macd_second"], var[0]["macd_first"])
        # ...and the regular golden setup still fires identically (union).
        g = setups_of("trullas_v05", golden_bars())
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0]["divergence_count"], 3)

    def test_v06_rsi_zone_only_count(self):
        bars = golden_bars(wiggle=True)
        prim = setups_of("trullas_divergence", bars)
        var = setups_of("trullas_v06", bars)
        self.assertEqual(len(prim), 1)
        self.assertEqual(len(var), 1)
        self.assertLess(var[0]["rsi_second"], 70.0)
        self.assertEqual(prim[0]["divergence_count"], 3)
        self.assertEqual(var[0]["divergence_count"], 2)  # RSI not counted
        # On the plain golden fixture RSI IS leaving the zone (>70), so
        # the joint is inert and the count matches the primary's.
        g = setups_of("trullas_v06", golden_bars())
        self.assertEqual(g[0]["divergence_count"], 3)

    def test_v07_fallo_admitted(self):
        bars = fallo_bars()
        self.assertEqual(setups_of("trullas_divergence", bars), [])
        var = setups_of("trullas_v07", bars)
        self.assertEqual(len(var), 1)
        self.assertEqual(var[0]["direction"], -1)
        self.assertGreater(var[0]["second_price"], var[0]["first_price"])
        self.assertGreaterEqual(var[0]["macd_second"], var[0]["macd_first"])
        g = setups_of("trullas_v07", golden_bars())
        self.assertEqual(len(g), 1)  # regular path unchanged (union)

    def test_v08_pyramid_add(self):
        from core.sleeve import Context
        plan = {"direction": -1, "entry": EXP_ENTRY, "stop": EXP_STOP,
                "stop_orig": EXP_STOP, "tp1": EXP_TP1, "tp2": EXP_TP2,
                "tp1_done": False, "qty_initial": 22, "added": False,
                "session": SESSION}
        state = {"day": SESSION, "entries_today": 1, "realized_pnl": 0.0,
                 "pending": None, "plan": dict(plan), "traded_pairs": []}
        # Bar falls to entry - 0.6R (favourable) but not to TP1.
        mid = EXP_ENTRY - 0.6 * (EXP_STOP - EXP_ENTRY)
        bar = _bar(0, EXP_ENTRY - 0.2, EXP_ENTRY + 0.1, mid, mid, 1000)
        sleeve = sleeve_of("trullas_v08")
        ctx = Context(now=bar["t"] + 60, session=SESSION, equity=EQUITY,
                      extra={"trullas_state": state})
        out = sleeve.signal({"QQQ": [bar]}, {"QQQ": -22}, ctx) or []
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "enter")  # the add is an entry intent
        exp_add = int(math.floor(min(
            0.0025 * EQUITY / (EXP_STOP - EXP_ENTRY),
            0.25 * EQUITY / EXP_ENTRY)))
        self.assertEqual(out[0].qty, exp_add)
        new_plan = sleeve.trullas_state["plan"]
        self.assertTrue(new_plan["added"])
        self.assertAlmostEqual(new_plan["stop"], EXP_ENTRY, places=6)
        # The primary on the identical bar adds nothing.
        from sleeves.trullas_divergence import TrullasDivergenceSleeve
        prim = TrullasDivergenceSleeve()
        state2 = {"day": SESSION, "entries_today": 1, "realized_pnl": 0.0,
                  "pending": None, "plan": dict(plan), "traded_pairs": []}
        ctx2 = Context(now=bar["t"] + 60, session=SESSION, equity=EQUITY,
                       extra={"trullas_state": state2})
        out2 = prim.signal({"QQQ": [bar]}, {"QQQ": -22}, ctx2) or []
        self.assertEqual(out2, [])

    def test_v09_volume_window_count(self):
        bars = golden_bars()
        for j in (72, 73, 75, 76):
            bars[j]["v"] = 9000.0  # neighbours of pivot 2, not the bar itself
        prim = setups_of("trullas_divergence", bars)
        var = setups_of("trullas_v09", bars)
        self.assertEqual(prim[0]["divergence_count"], 3)  # single bar: 2000 < 5000
        self.assertEqual(var[0]["divergence_count"], 2)   # windowed: no vol div
        # Windowed readings are stored on the setup.
        self.assertGreater(var[0]["vol_second"], var[0]["vol_first"])
        g = setups_of("trullas_v09", golden_bars())
        self.assertEqual(g[0]["divergence_count"], 3)  # inert on plain golden

    def test_v10_all_three_required(self):
        bars = golden_bars()
        bars[74]["v"] = 9999.0  # volume divergence removed -> count 2
        prim = setups_of("trullas_divergence", bars)
        self.assertEqual(len(prim), 1)
        self.assertEqual(prim[0]["divergence_count"], 2)
        self.assertEqual(setups_of("trullas_v10", bars), [])
        self.assertEqual(entries(drive("trullas_v10", bars)[0]), [])
        self.assertEqual(len(entries(drive("trullas_divergence", bars)[0])), 1)
        # Full triple divergence still fires at exactly 3 units' geometry.
        g = entries(drive("trullas_v10", golden_bars())[0])
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0][1].qty, EXP_QTY)


class TestVariantWiring(unittest.TestCase):
    def test_config_rows_and_inputs_equality(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        self.assertEqual(len(cfg["sleeves"]), 328)
        for vid in VARIANT_IDS:
            rows = [r for r in cfg["sleeves"] if r["id"] == vid]
            self.assertEqual(len(rows), 1, vid)
            row = rows[0]
            self.assertFalse(row["parked"], vid)
            self.assertEqual(row["module"], f"adapters3.{vid}", vid)
            self.assertEqual(row["slice"]["capital_usd"], 10000.0, vid)
            self.assertEqual(row["slice"]["cash_usd"], 10000.0, vid)
            self.assertEqual(row["cadence_s"], 60, vid)
            self.assertEqual(row["session"], "rth", vid)
            self.assertFalse(row["flat_by_close"], vid)
            self.assertIsNone(row["flatten_time_et"], vid)
            mod = importlib.import_module(f"adapters3.{vid}")
            self.assertEqual(list(mod.INPUTS), list(row["inputs"]), vid)
            strat = importlib.import_module(f"sleeves.{vid}")
            self.assertEqual(strat.CONFIG.sleeve_id, vid)
            self.assertFalse(strat.CONFIG.parked, vid)

    def test_each_variant_differs_in_exactly_one_param_field(self):
        from dataclasses import fields
        from sleeves.trullas_divergence import PRIMARY_PARAMS
        expected = {
            "trullas_v01": set(),  # adapter-side timeframe joint only
            "trullas_v02": {"pivot_k"}, "trullas_v03": {"pivot_k"},
            "trullas_v04": {"tp2_level"}, "trullas_v05": {"include_hidden"},
            "trullas_v06": {"rsi_zone_only"}, "trullas_v07": {"fallo_admitted"},
            "trullas_v08": {"pyramid"}, "trullas_v09": {"vol_window"},
            "trullas_v10": {"require_all_three"},
        }
        for vid, want in expected.items():
            p = sleeve_of(vid).PARAMS
            diff = {f.name for f in fields(p)
                    if getattr(p, f.name) != getattr(PRIMARY_PARAMS, f.name)}
            self.assertEqual(diff, want, vid)

    def test_producer_key_5min(self):
        from desk3.producers_g4 import _BARS_TF_KEYS
        self.assertIn("bars:QQQ:5Min", _BARS_TF_KEYS)
        self.assertIn("bars:QQQ:1Min", _BARS_TF_KEYS)


if __name__ == "__main__":
    unittest.main()
