"""przm_zero + przm_fade_edges blockers (PRZM-RECREATION-SPEC-2026-10-29, FROZEN).

Recreation of PRZM ZERO from the public record only (Flight Manual
V201 + public client fallback). Every golden below is hand-worked
from the spec's frozen numbers in this file, never via the sleeves'
helpers except where the helper itself is the subject. No backtest
is claimed; these tests pin mechanics: the driver equalizer, the
hysteresis (a held call does not flip on a small change, a call
drops only on a real fade), the chasing discount (about half), the
contrarian premium, sign-only 30-minute grading counting BOTH
outcomes, Fade Edges standing aside in a run and fading in a pin,
and the two honest WAITING states.
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
SESSION = "2026-10-29"
EQUITY = 10000.0


def _bar(day, i, o, h, l, c, v=1000):
    t = datetime(2026, 10, day, 9, 30, tzinfo=ET).timestamp() + i * 60
    return {"t": t, "o": float(o), "h": float(h), "l": float(l),
            "c": float(c), "v": float(v)}


def _ctx(now_ts, extra, equity=EQUITY):
    from core.sleeve import Context
    return Context(now=now_ts, session=SESSION, equity=equity, extra=extra)


# ---------------------------------------------------------------- drivers
class TestDriverEqualizer(unittest.TestCase):
    def test_equalizer_hand_worked(self):
        from sleeves.przm_zero import compute_drivers
        # Buckets (net, abs): +100,+100,+100,-100 over 400 abs.
        buckets = [(0, 100.0, 100.0), (300, 100.0, 100.0),
                   (600, 100.0, 100.0), (900, -100.0, 100.0)]
        drv = compute_drivers(buckets, spot=101.0, c30=100.0, v1=0.001)
        # SES = 200/400 = 0.5; all windows see all buckets (now_t None)
        self.assertEqual(drv["SES"], 50)
        self.assertEqual(drv["30M"], 50)
        self.assertEqual(drv["10M"], 50)
        # F = 0.5; STDY: 3 of last 4 buckets agree with F>0 -> 75
        self.assertEqual(drv["STDY"], 75)
        # PX = tanh((0.01)/(0.001*sqrt(30))/1.5)
        px = math.tanh(0.01 / (0.001 * math.sqrt(30.0)) / 1.5)
        self.assertEqual(drv["PX"], round(px * 100))
        # x = 0.5*(0.7+0.3*0.75) * (1+0.15*|PX|)  (price agrees)
        x = 0.5 * (0.7 + 0.3 * 0.75) * (1 + 0.15 * px)
        self.assertEqual(drv["score"], round(max(-1.0, min(1.0, x)) * 100))

    def test_chasing_counts_about_half_contrarian_counts_more(self):
        from sleeves.przm_zero import print_weight, signed_value
        p = {"bull": 1, "delta": 0.5, "price": 2.0, "size": 10,
             "is_call": True}
        plain = print_weight(p, m5=0.0)
        chasing = print_weight(p, m5=1.0)      # agrees with sharp move
        contra = print_weight(p, m5=-1.0)      # leans against it
        self.assertEqual(plain, 1.0)
        self.assertEqual(chasing, 0.55)        # manual: "about half"
        self.assertTrue(0.5 < chasing / plain < 0.6)
        self.assertEqual(contra, 1.25)         # manual: "counts more"
        ratio = signed_value(p, 100.0, m5=1.0) / signed_value(p, 100.0, m5=0.0)
        self.assertAlmostEqual(ratio, 0.55, places=9)

    def test_noise_filter_weights(self):
        from sleeves.przm_zero import print_weight
        base = {"bull": 1, "delta": 0.5, "price": 2.0, "size": 10,
                "is_call": True}
        self.assertEqual(print_weight({**base, "mid": True}), 0.0)
        self.assertEqual(print_weight({**base, "bull": 0}), 0.0)
        self.assertEqual(print_weight({**base, "delta": 0.05}), 0.15)
        self.assertEqual(print_weight({**base, "delta": 0.9}), 0.5)
        ins = {"bull": -1, "delta": 0.2, "price": 1.0, "size": 5,
               "is_call": False, "bought_at_ask": True, "otm_frac": 0.8}
        self.assertEqual(print_weight(ins), 0.2)
        self.assertEqual(print_weight({**base, "sweep": True}), 1.35)
        self.assertEqual(print_weight({**base, "opening": True}), 1.25)
        self.assertEqual(print_weight({**base, "closing": True}), 0.7)


# ------------------------------------------------------------- hysteresis
class TestHysteresis(unittest.TestCase):
    def test_held_call_does_not_flip_on_small_driver_change(self):
        from sleeves.przm_zero import CallMachine
        m = CallMachine()
        d, changed = m.update(30, 0)
        self.assertEqual((d, changed), (1, True))       # entry at >=25
        d, changed = m.update(-20, 60_000)              # small opposing move
        self.assertEqual((d, changed), (1, False))      # held, no flip (<35)
        d, changed = m.update(-34, 120_000)
        self.assertEqual((d, changed), (1, False))      # still under flip bar
        d, changed = m.update(-40, 180_000)             # real opposing read
        self.assertEqual((d, changed), (-1, True))      # flips at >=35

    def test_call_dropped_only_on_real_fade(self):
        from sleeves.przm_zero import CallMachine
        m = CallMachine()
        m.update(30, 0)                                  # long at t=0
        d, changed = m.update(5, 599_999)                # faded but <10 min
        self.assertEqual((d, changed), (1, False))       # minimum hold holds
        d, changed = m.update(5, 600_000)                # real fade + 10 min
        self.assertEqual((d, changed), (0, True))        # dropped
        m2 = CallMachine()
        m2.update(30, 0)
        d, changed = m2.update(20, 900_000)              # score*dir=20, not <8
        self.assertEqual((d, changed), (1, False))       # no drop without fade

    def test_entry_needs_clear_read(self):
        from sleeves.przm_zero import CallMachine
        m = CallMachine()
        self.assertEqual(m.update(24, 0), (0, False))
        self.assertEqual(m.update(-24, 0), (0, False))
        self.assertEqual(m.update(-25, 0), (-1, True))


# ---------------------------------------------------------------- grading
class TestGrading30Min(unittest.TestCase):
    def test_grading_counts_both_outcomes(self):
        from sleeves.przm_zero import grade_call, grade_ledger
        self.assertEqual(grade_call(100.0, 100.5, 1), "RIGHT")
        self.assertEqual(grade_call(100.0, 99.5, 1), "WRONG")
        self.assertEqual(grade_call(100.0, 99.5, -1), "RIGHT")
        self.assertEqual(grade_call(100.0, 100.5, -1), "WRONG")
        self.assertEqual(grade_call(100.0, 100.0, 1), "WRONG")  # zero = wrong
        calls = [{"t_ms": 0, "px": 100.0, "direction": 1},
                 {"t_ms": 0, "px": 100.0, "direction": -1},
                 {"t_ms": 10**12, "px": 100.0, "direction": 1}]
        prices = {1_800_000: 101.0}
        out = grade_ledger(calls, lambda t: prices.get(t))
        self.assertEqual(out["right"], 1)     # the long
        self.assertEqual(out["wrong"], 1)     # the short, counted not hidden
        self.assertEqual(out["pending"], 1)
        self.assertEqual(out["right_rate"], 0.5)


# ------------------------------------------------------------- zero sleeve
class TestZeroSleeveStates(unittest.TestCase):
    def test_waiting_no_print_tape(self):
        from sleeves.przm_zero import PrzmZeroSleeve
        bars = [_bar(29, i, 100, 100.2, 99.8, 100) for i in range(40)]
        s = PrzmZeroSleeve()
        out = s.signal({"SPY": bars}, {}, _ctx(bars[-1]["t"] + 60, {}))
        self.assertEqual(out, [])
        self.assertEqual(s.last_evaluation["state"], "WAITING_NO_PRINT_TAPE")

    def test_live_prints_make_long_call(self):
        from sleeves.przm_zero import PrzmZeroSleeve
        bars = [_bar(29, i, 100, 100.2, 99.8, 100) for i in range(40)]
        t_ms = int((bars[39]["t"]) * 1000)
        prints = [{"t": t_ms, "bull": 1, "delta": 0.5, "price": 3.0,
                   "size": 100, "is_call": True}]
        s = PrzmZeroSleeve()
        out = s.signal({"SPY": bars}, {},
                       _ctx(bars[-1]["t"] + 60, {"przm_prints": prints}))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "enter")
        self.assertEqual(out[0].side, "buy")
        self.assertEqual(out[0].qty, 10)  # $1,000 notional / $100
        self.assertEqual(s.last_evaluation["score"], 100)


# ------------------------------------------------------------ fade edges
CHAIN = [
    {"strike": 99.0, "right": "put", "gamma": 0.10, "open_interest": 100},
    {"strike": 100.0, "right": "call", "gamma": 0.10, "open_interest": 300},
    {"strike": 101.0, "right": "call", "gamma": 0.10, "open_interest": 50},
]
# Hand math (spot 100): GEX 99P=-100k, 100C=+300k, 101C=+50k.
# Magnet = 100 (largest |net|). Cumulative: -100k at 99, +200k at 100
# -> sign change at strike 100 -> flip = 100.


class TestGammaLevels(unittest.TestCase):
    def test_gamma_hand_worked(self):
        from sleeves.przm_fade_edges import gamma_levels, regime_for
        lv = gamma_levels(CHAIN, 100.0)
        self.assertEqual(lv["magnet"], 100.0)
        self.assertEqual(lv["flip"], 100.0)
        self.assertEqual(regime_for(100.5, lv), "pin")   # spot > flip
        self.assertEqual(regime_for(99.5, lv), "run")

    def test_delta_only_chain_is_waiting(self):
        from sleeves.przm_fade_edges import gamma_levels
        rows = [{"strike": 100.0, "right": "call", "delta": 0.5}]
        self.assertIsNone(gamma_levels(rows, 100.0))
        self.assertIsNone(gamma_levels([], 100.0))


def _fade_bars(spot=100.98, hi=101.0, lo=99.0):
    bars = [_bar(29, i, 100, 100.4, 99.6, 100) for i in range(31)]
    bars[10] = _bar(29, 10, 100, hi, 99.6, 100)      # session high prints
    bars[20] = _bar(29, 20, 100, 100.4, lo, 100)     # session low prints
    bars[-1] = _bar(29, 30, spot, hi, 99.6, spot)    # latest at the high edge
    return bars


class TestFadeEdgesSleeve(unittest.TestCase):
    def test_fades_in_pin(self):
        from sleeves.przm_fade_edges import PrzmFadeEdgesSleeve
        bars = _fade_bars()
        s = PrzmFadeEdgesSleeve()
        out = s.signal({"SPY": bars}, {},
                       _ctx(bars[-1]["t"] + 60, {"przm_chain": CHAIN}))
        self.assertEqual(len(out), 1, s.last_evaluation)
        it = out[0]
        self.assertEqual(it.kind, "enter")
        self.assertEqual(it.side, "sell")                    # fade the high
        self.assertEqual(it.qty, 19)                         # $2,000 / 100.98
        self.assertAlmostEqual(it.target, 100.0, places=6)   # the magnet
        self.assertAlmostEqual(it.stop, round(101.0 * 1.0015, 4), places=6)
        self.assertEqual(s.last_evaluation["state"], "fade_entry")

    def test_stands_aside_in_run(self):
        from sleeves.przm_fade_edges import PrzmFadeEdgesSleeve
        # Spot 99.5 <= flip 100 -> run: no fade even at an edge.
        bars = _fade_bars(spot=99.02, hi=100.4, lo=99.0)
        bars[-1] = _bar(29, 30, 99.02, 99.4, 99.0, 99.02)
        s = PrzmFadeEdgesSleeve()
        out = s.signal({"SPY": bars}, {},
                       _ctx(bars[-1]["t"] + 60, {"przm_chain": CHAIN}))
        self.assertEqual(out, [])
        self.assertEqual(s.last_evaluation["state"], "stand_aside_run")

    def test_waiting_no_gamma_levels(self):
        from sleeves.przm_fade_edges import PrzmFadeEdgesSleeve
        bars = _fade_bars()
        rows = [{"strike": 100.0, "right": "call", "delta": 0.5}]
        s = PrzmFadeEdgesSleeve()
        out = s.signal({"SPY": bars}, {},
                       _ctx(bars[-1]["t"] + 60, {"przm_chain": rows}))
        self.assertEqual(out, [])
        self.assertEqual(s.last_evaluation["state"], "WAITING_NO_GAMMA_LEVELS")

    def test_regime_flip_exits_open_fade(self):
        from sleeves.przm_fade_edges import PrzmFadeEdgesSleeve
        bars = _fade_bars()
        s = PrzmFadeEdgesSleeve()
        s.signal({"SPY": bars}, {}, _ctx(bars[-1]["t"] + 60, {"przm_chain": CHAIN}))
        state = s.przm_fade_state
        # Next bar: spot falls to 99.5 (<= flip) while the fade is open.
        later = bars + [_bar(29, 31, 99.6, 99.7, 99.4, 99.5)]
        out = s.signal({"SPY": later}, {"SPY": -19},
                       _ctx(later[-1]["t"] + 60,
                            {"przm_chain": CHAIN, "przm_fade_state": state}))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertIn("run", out[0].reason)


# ----------------------------------------------------------------- wiring
class TestInstallWiring(unittest.TestCase):
    def test_config_rows_parked_with_named_reasons(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 328)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for sid, needle in (("przm_zero", "NO_PRINT_TAPE"),
                            ("przm_fade_edges", "NO_GAMMA_LEVELS")):
            row = [r for r in rows if r["id"] == sid]
            self.assertEqual(len(row), 1, sid)
            row = row[0]
            self.assertEqual(row["module"], f"adapters3.{sid}")
            self.assertTrue(row["parked"], sid)
            self.assertIn(needle, row["params"]["parked_reason"])
            self.assertEqual(row["slice"]["capital_usd"], 10000.0)
            self.assertEqual(row["session"], "rth")
            self.assertEqual(row["cadence_s"], 60)
            mod = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]))

    def test_adapter_drives_waiting_states(self):
        from datetime import timezone as _tz
        for sid, adapter_mod in (("przm_zero", "adapters3.przm_zero"),
                                 ("przm_fade_edges", "adapters3.przm_fade_edges")):
            mod = importlib.import_module(adapter_mod)
            bars = [_bar(29, i, 100, 100.2, 99.8, 100) for i in range(40)]
            iso = [dict(b, t=datetime.fromtimestamp(b["t"], _tz.utc).isoformat())
                   for b in bars]
            view = {"now": datetime.fromtimestamp(bars[-1]["t"] + 60, tz=ET).isoformat(),
                    "bars": {"SPY|1Min": iso}, "positions": [],
                    "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                    "params": {}}
            with tempfile.TemporaryDirectory() as td:
                out = mod.evaluate(view, {"state_dir": td})
                self.assertEqual(out, [], sid)  # parked sleeves trade nothing
                state_file = "przm_state.json" if sid == "przm_zero" \
                    else "przm_fade_state.json"
                self.assertTrue(os.path.exists(os.path.join(td, state_file)), sid)


if __name__ == "__main__":
    unittest.main()
