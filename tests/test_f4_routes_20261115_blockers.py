"""FIX-F4-20261115 regression blockers.

Cures covered:
1. desk3/aster_batch7.py — the ENH freshness gate (_signal_age_s)
   hardcoded the native 4H bar duration, so on any other served
   timeframe (the 1H ENJ tape) every signal read -3h old and the
   gate refused every entry. Duration is now derived from the
   served bars' own spacing; native 4H behavior is bit-identical.
2. desk3/aster_batch8.py — the entry_freshness lag hardcoded
   bt + 4h; same cure (derived spacing, 4h fallback).
3. desk3/tensor_warm.py — _apply_native_pass built its analysis
   universe from the producer memo only; a bundle fire whose symbol
   was outside the memo got no analysis record and its feature
   cells stayed empty. Universe is now memo UNION fire symbols.
4. config/f4_variations_20261115.json — the variation registry:
   every Q07 _vargd variation's filters are exactly the alt-drop of
   its parent's CURRENT catalog filters (parents untouched), every
   variation carries replay counts and a falsifier.

Fail direction: proven on preserved pre-cure copies in
research_notes/alpha-hunt-chaos-20261115/pass2/f4_work/precure/
(see BUGLOG_2026-11-15.md FIX-F4 entry): tests 1, 2, 4 and 5 fail
on the pre-cure modules; test 3 passes both ways (preserved path).
"""
import importlib
import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3 import aster_batch7, aster_batch8  # noqa: E402


def _bars(start, spacing_h, n, breakout=True):
    """n bars, spacing_h apart; closes flat then a breakout close."""
    out = []
    t0 = start
    for i in range(n):
        t = t0 + timedelta(hours=spacing_h * i)
        c = 10.0 + (3.0 if (breakout and i == n - 1) else 0.0)
        out.append({"t": t.isoformat(), "o": 10.0, "h": 10.5,
                    "l": 9.5, "c": c, "v": 100000.0})
    return out


class Batch7Freshness(unittest.TestCase):
    SID = "aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash"

    def _view(self, bars, bar_h):
        last_open = datetime.fromisoformat(bars[-1]["t"])
        now = last_open + timedelta(hours=bar_h, seconds=60)
        return {"bars": {"ENJUSDT|4Hour": bars},
                "funding": {"ENJUSDT": -0.001}, "positions": [],
                "now": now, "slice": {"cash_usd": 10000.0}}

    def test_signal_age_uses_served_spacing_1h(self):
        bars = _bars(datetime(2026, 11, 1, tzinfo=timezone.utc), 1, 25)
        now = datetime.fromisoformat(bars[-1]["t"]) + timedelta(hours=1, seconds=300)
        self.assertEqual(aster_batch7._signal_age_s(bars, now), 300.0)

    def test_entry_fires_on_1h_tape(self):
        bars = _bars(datetime(2026, 11, 1, tzinfo=timezone.utc), 1, 25)
        out = aster_batch7.evaluate(self.SID, self._view(bars, 1), {})
        self.assertTrue(any(getattr(o, "kind", None) in ("enter", "entry")
                            for o in out), f"no entry on 1H tape: {out}")

    def test_entry_still_fires_on_native_4h_tape(self):
        bars = _bars(datetime(2026, 11, 1, tzinfo=timezone.utc), 4, 25)
        out = aster_batch7.evaluate(self.SID, self._view(bars, 4), {})
        self.assertTrue(any(getattr(o, "kind", None) in ("enter", "entry")
                            for o in out), f"no entry on 4H tape: {out}")


class Batch8Freshness(unittest.TestCase):
    SID = "aster_enj_nfs_lost_full"

    def test_entry_fires_on_1d_spaced_tape(self):
        # Fresh on its own tape (60s past the 24h bar close); the
        # pre-cure hardcoded +4h close read it 20h stale and refused.
        bars = _bars(datetime(2026, 10, 1, tzinfo=timezone.utc), 24, 25)
        last_open = datetime.fromisoformat(bars[-1]["t"])
        now = last_open + timedelta(hours=24, seconds=60)
        view = {"bars": {"ENJUSDT|4Hour": bars},
                "funding": {"ENJUSDT": -0.001}, "positions": [],
                "now": now, "slice": {"cash_usd": 10000.0}}
        out = aster_batch8.evaluate(self.SID, view, {})
        self.assertTrue(any(o.get("kind") == "entry" for o in out),
                        f"no entry on 1D-spaced tape: {out}")


class TensorWarmUniverse(unittest.TestCase):
    def test_fire_symbols_are_in_analysis_universe(self):
        import tempfile
        from desk3 import tensor_native, tensor_warm
        captured = {}

        def fake_products(root, universe, daily_map, now):
            captured["universe"] = list(universe)
            return {"analysis": {}, "census": {}, "panels": {}, "skips": {}}

        orig = tensor_native.build_native_products
        tensor_native.build_native_products = fake_products
        try:
            with tempfile.TemporaryDirectory() as td:
                os.makedirs(os.path.join(td, "state"))
                with open(os.path.join(td, "state",
                                       "tensor_signals_memo.json"), "w") as fh:
                    json.dump({"rows": {"AAA": {}}}, fh)
                payload = {"generated_at": datetime.now(timezone.utc).isoformat(),
                           "fires": [{"symbol": "BBB"}], "sleeves": {}}
                tensor_warm._apply_native_pass(td, payload, lambda syms: {})
        finally:
            tensor_native.build_native_products = orig
        self.assertIn("BBB", captured.get("universe", []))
        self.assertIn("AAA", captured.get("universe", []))


class VariationRegistry(unittest.TestCase):
    def test_registry_parents_untouched_and_counts_present(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        reg = json.load(open(os.path.join(
            root, "config", "f4_variations_20261115.json")))
        # VEIN2-VARIATIONS-20261115: the registry grew by the 3
        # _varsg entries (the two MISPRICED funding sign-gate
        # forms); the count pin moves 16 -> 19 with them. The
        # parents-untouched assertions below are unchanged.
        self.assertEqual(len(reg["variations"]), 19)
        from desk3.lazarus_q07 import SPECS

        def parent_filters(pid):
            if pid in SPECS:
                return list(SPECS[pid]["filters"])
            m = importlib.import_module(f"adapters3.{pid}")
            return list(m.SPEC["filters"])

        bar_computable = {"deep70", "cheap5", "mom6"}
        for v in reg["variations"]:
            self.assertTrue(v["falsifier"], v["id"])
            if v["id"].endswith("_vargd"):
                # parent untouched: registry's recorded parent filters
                # equal the parent's CURRENT catalog filters
                self.assertEqual(v["parent_filters"],
                                 parent_filters(v["parent"]), v["id"])
                self.assertEqual(v["variation_filters"],
                                 [f for f in v["parent_filters"]
                                  if f in bar_computable], v["id"])
                self.assertGreater(
                    v["replay"]["variation_entries_revealed"], 0, v["id"])
                self.assertEqual(v["replay"]["parent_entries"], 0, v["id"])


if __name__ == "__main__":
    unittest.main()
