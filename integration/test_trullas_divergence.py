"""Trullas divergence blockers (TRULLAS-SPEC-2026-10-25 v1.0, PRIMARY ARM).

Golden fixture: a hand-constructed QQQ 1-minute series with a known
bearish triple divergence. Expected entry/stop/TP1/TP2 are computed
independently in this file from the fixture's known swing constants
(A = 103.8, B = 111.0) — never via the sleeve's own helpers.

Fail direction: on the pre-install tree sleeves/trullas_divergence
does not exist (ImportError at collection). Removing the pivot
confirmation lag (confirm_index = pivot index) makes the causality
test fail — proven at install time, recorded in TRULLAS-SLEEVE-BUILD.md.
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

# Known fixture swing constants (hand-set in golden_bars below).
A_LOW = 103.8
B_HIGH = 111.0
RANGE_AB = B_HIGH - A_LOW
EXP_ENTRY = B_HIGH - 0.236 * RANGE_AB - 0.01
EXP_STOP = B_HIGH + 0.01
EXP_TP1 = B_HIGH - 0.382 * RANGE_AB
EXP_TP2 = B_HIGH - 0.618 * RANGE_AB
EXP_QTY = int(math.floor(min(
    3 * 0.0025 * EQUITY / (EXP_STOP - EXP_ENTRY),
    0.25 * EQUITY / EXP_ENTRY)))


def _bar(i, o, h, l, c, v):
    t = datetime(2026, 10, 23, 9, 30, tzinfo=ET).timestamp() + i * 60
    return {"t": t, "o": float(o), "h": float(h), "l": float(l),
            "c": float(c), "v": float(v)}


def golden_bars():
    """30 flat / sharp rise to 110 (pivot 1, vol 5000) / dip to 103.8 /
    slow rise to 111 (pivot 2, vol 2000) / decline through the trigger."""
    bars = []
    for i in range(30):
        bars.append(_bar(len(bars), 100, 100.2, 99.8, 100, 1000))
    for j in range(10):
        c = 101 + j
        bars.append(_bar(len(bars), c - 1, c + 0.2, c - 1.2, c, 2000))
    bars[-1] = _bar(len(bars) - 1, 109, 110.0, 108.8, 110, 5000)  # pivot 1
    for j in range(10):
        c = 109.4 - 0.6 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    # lowest low of the decline segment is 103.8 == A_LOW (bar above, j=9)
    for j in range(25):
        c = 104.28 + 0.28 * j
        bars.append(_bar(len(bars), round(c - 0.28, 2), round(c + 0.15, 2),
                         round(c - 0.43, 2), round(c, 2), 1200))
    bars[-1] = _bar(len(bars) - 1, 110.7, 111.0, 110.5, 110.9, 2000)  # pivot 2
    for j in range(10):
        c = 110.3 - 0.5 * j
        bars.append(_bar(len(bars), round(c + 0.5, 2), round(c + 0.3, 2),
                         round(c - 0.2, 2), round(c, 2), 1500))
    return bars


def drive(bars, equity=EQUITY, state=None, position=None):
    """Feed bars one at a time (adapter-style state round-trip).
    Returns (decisions, final_state) where decisions = [(bar_idx, intent)]."""
    from core.sleeve import Context
    from sleeves.trullas_divergence import TrullasDivergenceSleeve
    sleeve = TrullasDivergenceSleeve()
    state = dict(state or {})
    pos = dict(position or {})
    decisions = []
    for end in range(1, len(bars) + 1):
        latest = bars[end - 1]
        ctx = Context(now=latest["t"] + 60, session=SESSION, equity=equity,
                      extra={"trullas_state": state})
        intents = sleeve.signal({"QQQ": bars[:end]}, pos, ctx) or []
        state = sleeve.trullas_state
        for it in intents:
            decisions.append((end - 1, it))
            if it.kind == "enter":
                pos = {"QQQ": -it.qty if it.side == "sell" else it.qty}
            else:
                cur = pos.get("QQQ", 0.0)
                new = cur + it.qty if cur < 0 else cur - it.qty
                pos = {"QQQ": new} if new != 0 else {}
    return decisions, state


class TestGoldenFixture(unittest.TestCase):
    def test_golden_bearish_divergence_entry(self):
        decisions, _ = drive(golden_bars())
        entries = [(i, it) for i, it in decisions if it.kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        idx, it = entries[0]
        self.assertEqual(it.symbol, "QQQ")
        self.assertEqual(it.side, "sell")
        self.assertEqual(it.position_intent, "sell_to_open")
        self.assertAlmostEqual(it.price_hint, EXP_ENTRY, places=6)
        self.assertAlmostEqual(it.stop, EXP_STOP, places=6)
        self.assertAlmostEqual(it.target, EXP_TP2, places=6)
        self.assertEqual(it.qty, EXP_QTY)
        rules = {r.kind: r.value for r in it.exit_rules}
        self.assertAlmostEqual(rules["stop"], EXP_STOP, places=6)
        self.assertAlmostEqual(rules["target"], EXP_TP2, places=6)
        # TP1 is carried in the persisted plan (half-exit level).
        _, state = drive(golden_bars()[:idx + 1])
        self.assertAlmostEqual(state["plan"]["tp1"], EXP_TP1, places=6)
        self.assertAlmostEqual(state["plan"]["tp2"], EXP_TP2, places=6)

    def test_adapter_drive_matches(self):
        mod = importlib.import_module("adapters3.trullas_divergence")
        bars = golden_bars()[:83]  # through the trigger bar (index 82)
        # Live snapshot shape: bar timestamps are ISO strings.
        from datetime import timezone as _tz
        iso_bars = [dict(b, t=datetime.fromtimestamp(b["t"], _tz.utc).isoformat())
                    for b in bars]
        view = {"now": datetime.fromtimestamp(bars[-1]["t"] + 60, tz=ET).isoformat(),
                "bars": {"QQQ|1Min": iso_bars}, "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["qty"], EXP_QTY)
        self.assertAlmostEqual(entries[0]["stop_price"], EXP_STOP, places=6)
        self.assertAlmostEqual(entries[0]["target"], EXP_TP2, places=6)


class TestCausality(unittest.TestCase):
    def test_pivot_never_usable_before_confirmation(self):
        # Pivot 2 is bar index 74 in the fixture; it confirms at 79.
        # Before bar 79 exists: no pending setup and no entry, ever.
        bars = golden_bars()
        for end in (75, 76, 77, 78, 79):
            decisions, state = drive(bars[:end])
            self.assertIsNone(state.get("pending"),
                              f"pending usable at bar {end - 1} (pre-confirmation)")
            self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])
        # At confirmation the setup becomes actionable (and the
        # confirmation bar itself already crosses the trigger here).
        decisions, _ = drive(bars[:80])
        self.assertEqual(len([d for d in decisions if d[1].kind == "enter"]), 1)

    def test_truncation_never_changes_earlier_decisions(self):
        bars = golden_bars()
        full, _ = drive(bars)
        full_map = {i: (it.kind, it.qty, round(it.price_hint or 0, 6))
                    for i, it in full}
        for cut in (50, 70, 79, 80, 82, 84):
            part, _ = drive(bars[:cut])
            part_map = {i: (it.kind, it.qty, round(it.price_hint or 0, 6))
                        for i, it in part}
            for i, sig in part_map.items():
                self.assertEqual(sig, full_map[i],
                                 f"decision at bar {i} changed under truncation {cut}")


def _state_with(plan=None, pending=None, **kw):
    s = {"day": SESSION, "entries_today": 0, "realized_pnl": 0.0,
         "pending": pending, "plan": plan, "traded_pairs": []}
    s.update(kw)
    return s


def _one_bar_signal(state, position, bar, now=None):
    from core.sleeve import Context
    from sleeves.trullas_divergence import TrullasDivergenceSleeve
    sleeve = TrullasDivergenceSleeve()
    ctx = Context(now=now if now is not None else bar["t"] + 60,
                  session=SESSION, equity=EQUITY,
                  extra={"trullas_state": state})
    out = sleeve.signal({"QQQ": [bar]}, position, ctx) or []
    return out, sleeve


class TestTradeManagement(unittest.TestCase):
    PLAN = {"direction": -1, "entry": EXP_ENTRY, "stop": EXP_STOP,
            "tp1": EXP_TP1, "tp2": EXP_TP2, "tp1_done": False,
            "qty_initial": 22, "session": SESSION}

    def test_pessimistic_ordering_stop_before_target(self):
        bar = _bar(0, 110, EXP_STOP + 0.5, EXP_TP1 - 0.5, 109.5, 1000)
        out, sleeve = _one_bar_signal(_state_with(plan=dict(self.PLAN)),
                                      {"QQQ": -22}, bar)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertEqual(out[0].qty, 22)  # full exit at the stop, not TP1 half
        self.assertIn("stop", out[0].reason)
        self.assertIsNone(sleeve.trullas_state["plan"])

    def test_tp1_half_then_breakeven_stop(self):
        bar = _bar(0, 110, 110.5, EXP_TP1 - 0.1, 109.0, 1000)
        out, sleeve = _one_bar_signal(_state_with(plan=dict(self.PLAN)),
                                      {"QQQ": -22}, bar)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].qty, 11)  # half
        plan = sleeve.trullas_state["plan"]
        self.assertTrue(plan["tp1_done"])
        self.assertAlmostEqual(plan["stop"], EXP_ENTRY, places=6)  # to entry
        bar2 = _bar(1, 109.2, EXP_ENTRY + 0.05, 109.0, 109.2, 1000)
        out2, sleeve2 = _one_bar_signal(sleeve.trullas_state, {"QQQ": -11}, bar2)
        self.assertEqual(len(out2), 1)
        self.assertEqual(out2[0].qty, 11)
        self.assertIn("stop", out2[0].reason)

    def test_flat_1200(self):
        bar = _bar(0, 110, 110.2, 109.8, 110, 1000)
        noon = datetime(2026, 10, 23, 12, 0, tzinfo=ET).timestamp()
        out, _ = _one_bar_signal(_state_with(plan=dict(self.PLAN)),
                                 {"QQQ": -22}, bar, now=noon)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].qty, 22)
        self.assertIn("12:00", out[0].reason)


class TestCapsAndExpiry(unittest.TestCase):
    PENDING = {"direction": -1, "first_index": 39, "second_index": 74,
               "confirm_index": 79, "session": SESSION,
               "swing_a": A_LOW, "swing_b": B_HIGH, "divergence_count": 3,
               "entry_trigger": EXP_ENTRY, "stop": EXP_STOP,
               "tp1": EXP_TP1, "tp2": EXP_TP2}

    def _feed(self, state, bars):
        from core.sleeve import Context
        from sleeves.trullas_divergence import TrullasDivergenceSleeve
        sleeve = TrullasDivergenceSleeve()
        out_all = []
        for i, bar in enumerate(bars):
            ctx = Context(now=bar["t"] + 60, session=SESSION, equity=EQUITY,
                          extra={"trullas_state": state})
            # signal() re-detects setups from bars; give it the golden
            # prefix so detection agrees, then the probe bars.
            out_all += sleeve.signal({"QQQ": bars}, {}, ctx) or []
            state = sleeve.trullas_state
            break
        return out_all, sleeve

    def test_max_entries_cap(self):
        _, state = drive(golden_bars())
        self.assertEqual(state["entries_today"], 1)
        capped = dict(state, entries_today=5, plan=None,
                      pending=dict(self.PENDING), traded_pairs=[])
        bars = golden_bars()
        trigger = _bar(200, 109.5, 110.0, 109.0, 109.4, 1000)
        trig_t = datetime(2026, 10, 23, 10, 52, tzinfo=ET).timestamp()
        trigger["t"] = trig_t
        series = bars[:83] + [trigger]
        decisions, _ = drive(series, state=capped)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])

    def test_daily_loss_stop(self):
        capped = _state_with(pending=dict(self.PENDING), realized_pnl=-80.0)
        bars = golden_bars()
        trigger = _bar(200, 109.5, 110.0, 109.0, 109.4, 1000)
        trigger["t"] = datetime(2026, 10, 23, 10, 52, tzinfo=ET).timestamp()
        series = bars[:83] + [trigger]
        decisions, _ = drive(series, state=capped)
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])

    def test_entry_expiry_30_bars(self):
        # Through pivot 2 (index 74), then flat bars that confirm it
        # (index 79) without ever crossing the entry trigger.
        bars = golden_bars()[:75]
        t0 = bars[-1]["t"]
        flat = []
        for j in range(36):
            b = _bar(0, 110.5, 110.7, 110.2, 110.5, 1000)
            b["t"] = t0 + (j + 1) * 60
            flat.append(b)
        _, state = drive(bars + flat[:5])
        self.assertIsNotNone(state.get("pending"))  # confirmed, armed
        _, state = drive(bars + flat)
        self.assertIsNone(state.get("pending"))  # expired after 30 bars
        # A trigger-shaped bar after expiry must not enter.
        trig = _bar(0, 109.5, 110.0, 109.0, 109.4, 1000)
        trig["t"] = t0 + 37 * 60
        decisions, _ = drive(bars + flat + [trig])
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])


class TestInstallWiring(unittest.TestCase):
    def test_config_row(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = [r for r in cfg["sleeves"] if r["id"] == "trullas_divergence"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertFalse(row["parked"])
        self.assertEqual(row["slice"]["capital_usd"], 10000.0)
        self.assertEqual(row["session"], "rth")
        self.assertEqual(row["cadence_s"], 60)
        for key in ("bars", "bars_1min", "bars:QQQ:1Min", "positions",
                    "quotes", "session_fills"):
            self.assertIn(key, row["inputs"])

    def test_inputs_declared_and_producer_key(self):
        mod = importlib.import_module("adapters3.trullas_divergence")
        self.assertEqual(tuple(mod.INPUTS), tuple(
            json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
            ["sleeves"][[r["id"] for r in json.load(open(
                os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]]
            .index("trullas_divergence")]["inputs"]))
        from desk3.producers_g4 import BarsProjection, _BARS_TF_KEYS
        self.assertIn("bars:QQQ:1Min", _BARS_TF_KEYS)
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "state"))
            from datetime import timezone
            now = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)
            doc = {"fetched_at": now.isoformat(),
                   "bars": {"QQQ|1Min": [{"t": "x"}] * 100}}
            json.dump(doc, open(os.path.join(td, "state", "warm_bars.json"), "w"))
            proj = BarsProjection(td, ["bars:QQQ:1Min"], mode="keys")
            out = proj({"now": now})
        self.assertIn("bars:QQQ:1Min", out)
        self.assertEqual(out["bars:QQQ:1Min"]["bar_counts"], {"QQQ": 100})


if __name__ == "__main__":
    unittest.main()
