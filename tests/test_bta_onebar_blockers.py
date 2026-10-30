"""bta_onebar family blockers (2026-10-30).

Provenance: X post by Breakout Trading Academy (verified account,
handle truncated as @onl... in the source screenshot), installed by
owner order 2026-10-30. Edge UNPROVEN; no backtest is claimed by
these tests: they pin the translated rule mechanics.

Hand worked fixtures. Prior 50 bars are flat: high 620, low 610,
so the Donchian channel is 620 / 610.
  Long trigger bar (open 618, high 626, low 612, close 624):
    buy stop fills at the channel high 620.00 (open is below it).
    stop = 620 x (1 - 0.0020) = 618.76. qty = floor(10000/620) = 16.
  Short trigger bar (open 612, high 618, low 608, close 611):
    sell stop fills at the channel low 610.00.
    stop = 610 x (1 + 0.0020) = 611.22. qty = floor(10000/610) = 16.
  Gap long bar (open 630): fill at the open 630.00, not the level.
    stop = 630 x 0.998 = 628.74. qty = floor(10000/630) = 15.
  Stop translation: stop_price(1, 625) = 623.75 and
    stop_price(-1, 625) = 626.25 (50 NQ points at the 25,000
    reference level = 0.20 percent; see ANALYSIS.md).
Stems covered for the ratchet: bta_onebar_qqq, bta_onebar_basket,
bta_onebar_rth (sleeves, adapters and adapters3 modules all carry
those stems).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
EQUITY = 10000.0

FLAT = (615.0, 620.0, 610.0, 615.0, 1000)
LONG_TRIG = (618.0, 626.0, 612.0, 624.0, 1000)
SHORT_TRIG = (612.0, 618.0, 608.0, 611.0, 1000)
T0 = datetime(2026, 10, 26, 9, 30, tzinfo=ET).timestamp()


def bar(t, spec):
    o, h, l, c, v = spec
    return {"t": float(t), "o": o, "h": h, "l": l, "c": c, "v": v}


def prior50(t0=T0):
    return [bar(t0 + i * 1800, FLAT) for i in range(50)]


def seq(specs, t0=T0):
    """50 flat prior bars plus the given specs, sequential 30 min."""
    out = prior50(t0)
    base = t0 + 50 * 1800
    out += [bar(base + i * 1800, s) for i, s in enumerate(specs)]
    return out


def drive(bars_list, sleeve_cls, state=None, pos=None, sym="QQQ"):
    from core.sleeve import Context
    sleeve = sleeve_cls()
    state = dict(state or {})
    pos = dict(pos or {})
    decisions = []
    for end in range(1, len(bars_list) + 1):
        part = bars_list[:end]
        latest = part[-1]
        now = latest["t"] + 1800
        session = datetime.fromtimestamp(latest["t"], tz=ET).date().isoformat()
        ctx = Context(now=now, session=session, equity=EQUITY,
                      extra={"onebar_state": state})
        intents = sleeve.signal({sym: part}, pos, ctx) or []
        state = sleeve.onebar_state
        for it in intents:
            decisions.append((latest["t"], it))
            if it.kind == "enter":
                pos = {sym: it.qty if it.side == "buy" else -it.qty}
            else:
                cur = pos.get(sym, 0.0)
                new = cur + it.qty if cur < 0 else cur - it.qty
                pos = {sym: new} if new != 0 else {}
    return decisions, state, sleeve


def qqq_drive(bars_list, **kw):
    from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve
    return drive(bars_list, BtaOnebarQqqSleeve, **kw)


class TestChannelAndStopMath(unittest.TestCase):
    def test_channel_hand_worked(self):
        from sleeves.bta_onebar_qqq import channel
        bars = prior50()
        bars[10] = bar(bars[10]["t"], (615.0, 621.5, 610.0, 615.0, 1000))
        bars[20] = bar(bars[20]["t"], (615.0, 620.0, 609.25, 615.0, 1000))
        self.assertEqual(channel(bars), (621.5, 609.25))

    def test_channel_requires_50_bars(self):
        from sleeves.bta_onebar_qqq import channel
        self.assertIsNone(channel(prior50()[:49]))

    def test_channel_uses_only_last_50(self):
        from sleeves.bta_onebar_qqq import channel
        old = bar(T0 - 1800, (615.0, 999.0, 1.0, 615.0, 1000))
        self.assertEqual(channel([old] + prior50()), (620.0, 610.0))

    def test_stop_translation_arithmetic(self):
        from sleeves.bta_onebar_qqq import STOP_PCT, stop_price
        self.assertEqual(STOP_PCT, 0.0020)
        self.assertAlmostEqual(stop_price(1, 625.0), 623.75, places=6)
        self.assertAlmostEqual(stop_price(-1, 625.0), 626.25, places=6)


class TestGoldenEntriesAndExit(unittest.TestCase):
    def test_long_entry_and_next_bar_open_exit(self):
        exit_bar = (623.0, 624.0, 620.0, 622.0, 1000)
        decisions, state, _ = qqq_drive(seq([LONG_TRIG, exit_bar]))
        entries = [d for d in decisions if d[1].kind == "enter"]
        exits = [d for d in decisions if d[1].kind == "exit"]
        self.assertEqual(len(entries), 1, decisions)
        self.assertEqual(len(exits), 1, decisions)
        it = entries[0][1]
        self.assertEqual(it.symbol, "QQQ")
        self.assertEqual(it.side, "buy")
        self.assertEqual(it.position_intent, "buy_to_open")
        self.assertAlmostEqual(it.price_hint, 620.0, places=6)
        self.assertAlmostEqual(it.stop, 618.76, places=6)
        self.assertEqual(it.qty, 16)
        rules = {r.kind: r.value for r in it.exit_rules}
        self.assertAlmostEqual(rules["stop"], 618.76, places=6)
        ex = exits[0][1]
        self.assertAlmostEqual(ex.price_hint, 623.0, places=6)
        self.assertEqual(ex.qty, 16)
        self.assertEqual(ex.position_intent, "sell_to_close")

    def test_short_entry_and_exit(self):
        exit_bar = (609.0, 612.0, 607.0, 610.0, 1000)
        decisions, _, _ = qqq_drive(seq([SHORT_TRIG, exit_bar]))
        entries = [d for d in decisions if d[1].kind == "enter"]
        exits = [d for d in decisions if d[1].kind == "exit"]
        self.assertEqual(len(entries), 1, decisions)
        self.assertEqual(len(exits), 1, decisions)
        it = entries[0][1]
        self.assertEqual(it.side, "sell")
        self.assertEqual(it.position_intent, "sell_to_open")
        self.assertAlmostEqual(it.price_hint, 610.0, places=6)
        self.assertAlmostEqual(it.stop, 611.22, places=6)
        self.assertEqual(it.qty, 16)
        self.assertEqual(exits[0][1].position_intent, "buy_to_close")
        self.assertAlmostEqual(exits[0][1].price_hint, 609.0, places=6)

    def test_gap_open_fills_at_open(self):
        gap = (630.0, 632.0, 628.0, 631.0, 1000)
        decisions, _, _ = qqq_drive(seq([gap]))
        entries = [d for d in decisions if d[1].kind == "enter"]
        self.assertEqual(len(entries), 1, decisions)
        self.assertAlmostEqual(entries[0][1].price_hint, 630.0, places=6)
        self.assertAlmostEqual(entries[0][1].stop, 628.74, places=6)
        self.assertEqual(entries[0][1].qty, 15)

    def test_no_breakout_no_entry(self):
        inside = (615.0, 619.9, 610.1, 615.0, 1000)
        decisions, _, _ = qqq_drive(seq([inside, inside]))
        self.assertEqual(decisions, [])

    def test_both_extremes_same_bar_no_entry(self):
        both = (615.0, 626.0, 605.0, 615.0, 1000)
        decisions, _, _ = qqq_drive(seq([both]))
        self.assertEqual([d for d in decisions if d[1].kind == "enter"], [])

    def test_forming_bar_never_triggers(self):
        from core.sleeve import Context
        from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve
        bars = seq([LONG_TRIG])
        sleeve = BtaOnebarQqqSleeve()
        latest = bars[-1]
        ctx = Context(now=latest["t"] + 900,
                      session=datetime.fromtimestamp(latest["t"], tz=ET).date().isoformat(),
                      equity=EQUITY, extra={"onebar_state": {}})
        self.assertEqual(sleeve.signal({"QQQ": bars}, {}, ctx), [])


class TestCapsAndReentry(unittest.TestCase):
    def _day_bars(self):
        day = datetime(2026, 10, 28, 10, 0, tzinfo=ET).timestamp()
        specs = [
            LONG_TRIG,                                # entry 1 at 620
            (623.0, 624.0, 620.0, 622.0, 1000),       # exit 1
            (620.0, 630.0, 618.0, 628.0, 1000),       # entry 2 at 626
            (628.0, 629.0, 625.0, 627.0, 1000),       # exit 2
            (627.0, 635.0, 626.0, 633.0, 1000),       # would-be entry 3
        ]
        return prior50() + [bar(day + i * 1800, s) for i, s in enumerate(specs)]

    def test_max_two_entries_per_day(self):
        decisions, state, _ = qqq_drive(self._day_bars())
        entries = [d for d in decisions if d[1].kind == "enter"]
        self.assertEqual(len(entries), 2, decisions)
        self.assertAlmostEqual(entries[1][1].price_hint, 626.0, places=6)
        self.assertEqual(state["entries"]["QQQ"]["count"], 2)

    def test_no_reentry_in_same_bar_after_exit(self):
        from core.sleeve import Context
        from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve
        exit_trig = (623.0, 630.0, 620.0, 629.0, 1000)
        bars = seq([LONG_TRIG, exit_trig])
        decisions, state, _ = qqq_drive(bars)
        exits = [d for d in decisions if d[1].kind == "exit"]
        self.assertEqual(len(exits), 1, decisions)
        sleeve = BtaOnebarQqqSleeve()
        latest = bars[-1]
        ctx = Context(now=latest["t"] + 1800,
                      session=datetime.fromtimestamp(latest["t"], tz=ET).date().isoformat(),
                      equity=EQUITY, extra={"onebar_state": state})
        out = sleeve.signal({"QQQ": bars}, {}, ctx)
        self.assertEqual([i for i in out if i.kind == "enter"], [])


class TestCausality(unittest.TestCase):
    def test_future_bars_never_change_entry(self):
        base, _, _ = qqq_drive(seq([LONG_TRIG]))
        wild = (50.0, 900.0, 1.0, 50.0, 999995)
        alt_bars = seq([LONG_TRIG]) + [bar(T0 + 51 * 1800, wild)]
        alt, _, _ = qqq_drive(alt_bars)
        pick = lambda ds: [(round(i.price_hint, 6), i.qty, round(i.stop, 6))
                           for _, i in ds if i.kind == "enter"]
        self.assertEqual(pick(base), pick(alt))

    def test_truncation_never_changes_earlier_decisions(self):
        exit_bar = (623.0, 624.0, 620.0, 622.0, 1000)
        bars = seq([LONG_TRIG, exit_bar])
        full, _, _ = qqq_drive(bars)
        full_map = {t: (i.kind, i.qty) for t, i in full}
        for cut in range(50, len(bars)):
            part, _, _ = qqq_drive(bars[:cut + 1] if cut < len(bars) else bars)
            for t, i in part:
                self.assertEqual((i.kind, i.qty), full_map[t])


def rth_bars(specs_with_times):
    """specs_with_times: list of (datetime_et, spec)."""
    return [bar(dt.timestamp(), s) for dt, s in specs_with_times]


def rth_prior50():
    days = [datetime(2026, 10, 21, tzinfo=ET), datetime(2026, 10, 22, tzinfo=ET),
            datetime(2026, 10, 23, tzinfo=ET), datetime(2026, 10, 26, tzinfo=ET),
            datetime(2026, 10, 27, tzinfo=ET)]
    out = []
    for d in days:
        for k in range(13):
            if len(out) >= 50:
                return out
            t = d.replace(hour=9, minute=30) + timedelta(minutes=30 * k)
            out.append((t, FLAT))
    return out


class TestRthVariant(unittest.TestCase):
    def test_rth_entry_and_exit_and_premarket_ignored(self):
        from sleeves.bta_onebar_rth import BtaOnebarRthSleeve
        items = rth_prior50()
        pre = (datetime(2026, 10, 28, 8, 0, tzinfo=ET), (900.0, 999.0, 900.0, 950.0, 1000))
        trig = (datetime(2026, 10, 28, 10, 0, tzinfo=ET), LONG_TRIG)
        exitb = (datetime(2026, 10, 28, 10, 30, tzinfo=ET), (623.0, 624.0, 620.0, 622.0, 1000))
        bars = rth_bars(items + [pre, trig, exitb])
        decisions, _, sleeve = drive(bars, BtaOnebarRthSleeve)
        entries = [d for d in decisions if d[1].kind == "enter"]
        exits = [d for d in decisions if d[1].kind == "exit"]
        self.assertEqual(len(entries), 1, decisions)
        self.assertAlmostEqual(entries[0][1].price_hint, 620.0, places=6)
        self.assertEqual(len(exits), 1, decisions)

    def test_rth_flat_1555_exits_even_on_entry_bar(self):
        from core.sleeve import Context
        from sleeves.bta_onebar_rth import BtaOnebarRthSleeve
        items = rth_prior50()
        trig = (datetime(2026, 10, 28, 14, 30, tzinfo=ET), LONG_TRIG)
        bars = rth_bars(items + [trig])
        decisions, state, _ = drive(bars, BtaOnebarRthSleeve)
        self.assertEqual(len([d for d in decisions if d[1].kind == "enter"]), 1)
        sleeve = BtaOnebarRthSleeve()
        now = datetime(2026, 10, 28, 15, 55, tzinfo=ET).timestamp()
        ctx = Context(now=now, session="2026-10-28", equity=EQUITY,
                      extra={"onebar_state": state})
        out = sleeve.signal({"QQQ": bars}, {"QQQ": 16}, ctx)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertIn("15:55", out[0].reason)

    def test_base_sleeve_does_not_flat_at_1555(self):
        from core.sleeve import Context
        from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve
        bars = seq([LONG_TRIG])
        decisions, state, _ = qqq_drive(bars)
        self.assertEqual(len([d for d in decisions if d[1].kind == "enter"]), 1)
        sleeve = BtaOnebarQqqSleeve()
        latest = bars[-1]
        ctx = Context(now=latest["t"] + 1800, session="2026-10-27",
                      equity=EQUITY, extra={"onebar_state": state})
        out = sleeve.signal({"QQQ": bars}, {"QQQ": 16}, ctx)
        self.assertEqual(out, [])


class TestBasket(unittest.TestCase):
    def test_basket_independent_per_symbol(self):
        from sleeves.bta_onebar_basket import BtaOnebarBasketSleeve
        from core.sleeve import Context
        bars = {
            "SPY": seq([LONG_TRIG]),
            "QQQ": seq([(615.0, 619.0, 611.0, 615.0, 1000)]),
            "MDY": seq([(615.0, 619.0, 611.0, 615.0, 1000)]),
            "DIA": seq([SHORT_TRIG]),
        }
        sleeve = BtaOnebarBasketSleeve()
        latest_t = bars["SPY"][-1]["t"]
        ctx = Context(now=latest_t + 1800, session="2026-10-27",
                      equity=EQUITY, extra={"onebar_state": {}})
        out = sleeve.signal(bars, {}, ctx)
        entries = {i.symbol: i for i in out if i.kind == "enter"}
        self.assertEqual(set(entries), {"SPY", "DIA"}, out)
        self.assertEqual(entries["SPY"].side, "buy")
        self.assertEqual(entries["DIA"].side, "sell")
        self.assertAlmostEqual(entries["DIA"].price_hint, 610.0, places=6)
        plans = sleeve.onebar_state["plans"]
        self.assertEqual(set(plans), {"SPY", "DIA"})
        self.assertEqual(sleeve.onebar_state["entries"]["SPY"]["count"], 1)
        self.assertEqual(sleeve.onebar_state["entries"]["DIA"]["count"], 1)


class TestAdapterDrive(unittest.TestCase):
    def _view(self, bars_list, sym="QQQ"):
        iso = [dict(b, t=datetime.fromtimestamp(b["t"], timezone.utc).isoformat())
               for b in bars_list]
        return {"now": datetime.fromtimestamp(bars_list[-1]["t"] + 1800, tz=ET).isoformat(),
                "bars": {f"{sym}|30Min": iso}, "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}

    def test_adapter_drive_qqq_matches_core(self):
        mod = importlib.import_module("adapters3.bta_onebar_qqq")
        bars = seq([LONG_TRIG])
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(self._view(bars), {"state_dir": td})
            self.assertTrue(os.path.exists(os.path.join(td, "onebar_state.json")))
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["qty"], 16)
        self.assertAlmostEqual(entries[0]["stop_price"], 618.76, places=6)
        self.assertTrue(entries[0]["intent_id"].startswith("bta_onebar_qqq-"))

    def test_adapter_drive_basket(self):
        mod = importlib.import_module("adapters3.bta_onebar_basket")
        view = self._view(seq([LONG_TRIG]), sym="SPY")
        view["bars"]["DIA|30Min"] = view["bars"].pop("SPY|30Min")
        view["bars"]["SPY|30Min"] = [dict(b) for b in view["bars"]["DIA|30Min"]]
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual({d["symbol"] for d in entries}, {"SPY", "DIA"}, out)


class TestInstallWiring(unittest.TestCase):
    IDS = ("bta_onebar_qqq", "bta_onebar_basket", "bta_onebar_rth")

    def test_config_rows_and_roster(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 336)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for sid in self.IDS:
            match = [r for r in rows if r["id"] == sid]
            self.assertEqual(len(match), 1, sid)
            row = match[0]
            self.assertEqual(row["module"], f"adapters3.{sid}")
            self.assertFalse(row["parked"])
            self.assertEqual(row["slice"]["capital_usd"], 10000.0)
            self.assertEqual(row["slice"]["cash_usd"], 10000.0)
            self.assertEqual(row["cadence_s"], 60)

    def test_inputs_match_and_producer_keys_registered(self):
        from desk3.producers_g4 import _BARS_TF_KEYS
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        for sid in self.IDS:
            mod = importlib.import_module(f"adapters3.{sid}")
            row = [r for r in cfg["sleeves"] if r["id"] == sid][0]
            self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]), sid)
            for key in row["inputs"]:
                if key.startswith("bars:"):
                    self.assertIn(key, _BARS_TF_KEYS)

    def test_producer_serves_30min_keys_from_warm_map(self):
        from desk3.producers_g4 import BarsProjection
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "state"))
            now = datetime(2026, 10, 28, 15, 0, tzinfo=timezone.utc)
            doc = {"fetched_at": now.isoformat(),
                   "bars": {f"{s}|30Min": [{"t": "x"}] * 60
                            for s in ("QQQ", "SPY", "MDY", "DIA")}}
            json.dump(doc, open(os.path.join(td, "state", "warm_bars.json"), "w"))
            keys = [f"bars:{s}:30Min" for s in ("QQQ", "SPY", "MDY", "DIA")]
            proj = BarsProjection(td, keys, mode="keys")
            out = proj({"now": now})
        for key in keys:
            self.assertIn(key, out)
            self.assertEqual(out[key]["bar_counts"][key.split(":")[1]], 60)

    def test_warm_fetches_carry_30min(self):
        from desk3.warm import INTRADAY_FETCHES
        for sym in ("QQQ", "SPY", "MDY", "DIA"):
            self.assertTrue(any(s == sym and tf == "30Min"
                                for s, tf, _d in INTRADAY_FETCHES), sym)


if __name__ == "__main__":
    unittest.main()
