"""soxl_pm_breakout blockers (2026-11-03).

Provenance: TrendSpider shared strategy "SOXL: PM-high breakout,
hold to close" (published 2026-11-03), installed as a paper sleeve
by owner order 2026-11-03. Rules frozen and replicated first in
research_notes/trendspider-soxl-pmhigh-test-20261103/ (verdict
PARTIAL; edge unproven on this desk until the live record says
otherwise). These tests pin the translated rule mechanics, the
known-answer cases portable from the replication harness, and the
roster row. On the pre-install tree they fail: the sleeve modules
do not exist, the roster has 336 rows and no soxl_pm_breakout row.

Hand-worked fixture (session Mon 2026-10-26, ET):
  Prior RTH day Fri 2026-10-23: 26 bars, close 50, volume 1000
  each (the volume SMA lookback).
  Today premarket 04:00-09:15: 22 bars, high 100 (PM high = 100).
  Today RTH bar 09:30: close 99, volume 1000.
  Today RTH bar 09:45: close 101, volume 4000. Volume SMA20 at
  that bar = (38 x 1000 + 1000 + 4000) / 40 over the RTH series
  positions... exactly: the last 20 RTH bars are 18 prior-day bars
  (1000) + 1000 + 4000 = 23000 / 20 = 1150; gate = 1725 <= 4000.
  Close 101 > PM high 100: ENTRY, qty = floor(10000 / 101) = 99.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
DAY = datetime(2026, 10, 26, tzinfo=ET)       # Monday
PRIOR = datetime(2026, 10, 23, tzinfo=ET)     # Friday


def bar(dt, o, h, l, c, v):
    return {"t": dt.timestamp(), "o": o, "h": h, "l": l, "c": c, "v": v}


def prior_day():
    out = []
    base = PRIOR.replace(hour=9, minute=30)
    for i in range(26):
        out.append(bar(base + timedelta(minutes=15 * i),
                       50, 50, 50, 50, 1000))
    return out


def premarket(high=100.0):
    out = []
    base = DAY.replace(hour=4, minute=0)
    for i in range(22):
        out.append(bar(base + timedelta(minutes=15 * i),
                       99, high, 98, 99, 500))
    return out


def rth(specs):
    """specs: list of (start_hh, start_mm, o, h, l, c, v) today."""
    return [bar(DAY.replace(hour=hh, minute=mm), o, h, l, c, v)
            for hh, mm, o, h, l, c, v in specs]


def base_bars(today_rth):
    return {"SOXL": prior_day() + premarket() + today_rth}


def ctx_at(hh, mm, extra=None, equity=10000.0, session="2026-10-26"):
    from core.sleeve import Context
    now = DAY.replace(hour=hh, minute=mm).timestamp()
    return Context(now=now, session=session, equity=equity,
                   extra=extra or {})


class SignalRules(unittest.TestCase):
    def setUp(self):
        self.strat = importlib.import_module("sleeves.soxl_pm_breakout")

    def test_premarket_high_construction(self):
        bars = prior_day() + premarket() + rth([(9, 30, 99, 99, 99, 99, 1)])
        self.assertEqual(self.strat.premarket_high(bars, "2026-10-26"), 100.0)
        # A higher high OUTSIDE the premarket segment or on another
        # date must not leak in.
        bars2 = bars + [bar(DAY.replace(hour=12), 1, 500, 1, 1, 1)]
        self.assertEqual(self.strat.premarket_high(bars2, "2026-10-26"), 100.0)
        self.assertIsNone(self.strat.premarket_high(bars, "2026-10-27"))

    def test_breakout_entry_known_answer(self):
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 101.5, 99, 101, 4000)])
        out = self.strat.signal(base_bars(today), {}, ctx_at(10, 0))
        self.assertEqual(len(out), 1)
        it = out[0]
        self.assertEqual(it.kind, "enter")
        self.assertEqual(it.symbol, "SOXL")
        self.assertEqual(it.qty, 99)
        self.assertEqual(it.side, "buy")
        self.assertEqual(it.position_intent, "buy_to_open")
        self.assertIsNone(it.stop)
        self.assertIsNone(it.target)

    def test_volume_gate_rejection(self):
        # Signal bar volume 1400: SMA20 = (18*1000 + 1000 + 1400)/20
        # = 1020; gate 1530 > 1400, so the breakout does not count.
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 101.5, 99, 101, 1400)])
        out = self.strat.signal(base_bars(today), {}, ctx_at(10, 0))
        self.assertEqual(out, [])
        self.assertEqual(self.strat.signal.last_evaluation["SOXL"],
                         "no_qualifying_breakout")

    def test_no_breakout_no_entry(self):
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 100.0, 99, 100, 4000)])  # close == PM high
        out = self.strat.signal(base_bars(today), {}, ctx_at(10, 0))
        self.assertEqual(out, [])

    def test_cutoff_1415(self):
        # Breakout bar starting 14:15 closes 14:30: past the cutoff.
        filler = [(9, 30, 99, 99.5, 98.5, 99, 1000)]
        late = rth(filler + [(14, 15, 99, 101.5, 99, 101, 4000)])
        out = self.strat.signal(base_bars(late), {}, ctx_at(14, 30))
        self.assertEqual(out, [])
        # Breakout bar starting 14:00 closes exactly 14:15: allowed.
        ontime = rth(filler + [(14, 0, 99, 101.5, 99, 101, 4000)])
        out = self.strat.signal(base_bars(ontime), {}, ctx_at(14, 15))
        self.assertEqual(len(out), 1)

    def test_no_premarket_bars_untradable(self):
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 101.5, 99, 101, 4000)])
        bars = {"SOXL": prior_day() + today}
        out = self.strat.signal(bars, {}, ctx_at(10, 0))
        self.assertEqual(out, [])
        self.assertEqual(self.strat.signal.last_evaluation["SOXL"],
                         "no_premarket_bars_untradable")

    def test_one_entry_per_day(self):
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 101.5, 99, 101, 4000),
                     (10, 0, 101, 102.5, 100.5, 102, 4000)])
        # Evaluated at 10:00, when the 09:45 bar has just completed
        # and the 10:00 bar is still forming: the entry fires.
        out = self.strat.signal(base_bars(today), {}, ctx_at(10, 0))
        self.assertEqual(len(out), 1)
        state = {"soxl_state": self.strat.signal.soxl_state}
        # Same day, plan awaiting fill: no second intent, ever.
        out2 = self.strat.signal(base_bars(today), {}, ctx_at(10, 15, extra=state))
        self.assertEqual(out2, [])

    def test_forming_bar_never_signals(self):
        today = rth([(9, 30, 99, 99.5, 98.5, 99, 1000),
                     (9, 45, 99, 101.5, 99, 101, 4000)])
        # At 09:59 the 09:45 bar has not completed: no signal yet.
        out = self.strat.signal(base_bars(today), {}, ctx_at(9, 59))
        self.assertEqual(out, [])

    def test_exit_timing_hold_to_close(self):
        plan = {"signal_close": 101.0, "pmh": 100.0, "signal_bar_t": 0,
                "session": "2026-10-26", "seen_open": False,
                "exit_emitted_at": None}
        extra = {"soxl_state": {"plan": plan, "entries": {"2026-10-26": {"count": 1}}}}
        pos = {"SOXL": 99}
        # 15:30: still holding, no exit intent.
        out = self.strat.signal(base_bars(rth([(9, 30, 99, 99, 99, 99, 1)])),
                                pos, ctx_at(15, 30, extra=extra))
        self.assertEqual(out, [])
        # 15:45: the exit intent fires, full quantity, sell to close.
        out = self.strat.signal(base_bars(rth([(9, 30, 99, 99, 99, 99, 1)])),
                                pos, ctx_at(15, 45, extra=extra))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")
        self.assertEqual(out[0].qty, 99.0)
        self.assertEqual(out[0].position_intent, "sell_to_close")

    def test_overdue_position_exits_next_session(self):
        plan = {"signal_close": 101.0, "pmh": 100.0, "signal_bar_t": 0,
                "session": "2026-10-26", "seen_open": True,
                "exit_emitted_at": None}
        extra = {"soxl_state": {"plan": plan, "entries": {}}}
        out = self.strat.signal({"SOXL": []}, {"SOXL": 10},
                                ctx_at(9, 35, extra=extra,
                                       session="2026-10-27"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].kind, "exit")


class AdapterChain(unittest.TestCase):
    def test_adapters3_evaluate_emits_entry_dict(self):
        mod = importlib.import_module("adapters3.soxl_pm_breakout")
        self.assertEqual(mod.INPUTS, ["bars", "bars:SOXL:15Min",
                                      "positions", "quotes",
                                      "session_fills"])
        rows = []
        for b in prior_day() + premarket() + rth(
                [(9, 30, 99, 99.5, 98.5, 99, 1000),
                 (9, 45, 99, 101.5, 99, 101, 4000)]):
            dt = datetime.fromtimestamp(b["t"], tz=ET)
            rows.append({"t": dt.isoformat(), "o": b["o"], "h": b["h"],
                         "l": b["l"], "c": b["c"], "v": b["v"]})
        view = {"now": DAY.replace(hour=10).isoformat(),
                "bars": {"SOXL|15Min": rows},
                "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}, "extra": {}, "quotes": {},
                "session_fills": []}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "SOXL")
        self.assertEqual(out[0]["qty"], 99)
        self.assertEqual(out[0]["position_intent"], "buy_to_open")
        self.assertEqual(out[0]["time_in_force"], "day")


class RosterRow(unittest.TestCase):
    def test_roster_row_and_count(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        # Roster count pin: 359 since CONVERSION-VARIATION-20261115 (2026-11-15): 358 + aster_trader_turtle2010 (CONV-47) rostered beside aster_trader_donchian55 (BUGLOG_2026-11-15.md); previously 358 since VARIATION-ROSTERING-20261115.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows), 400)
        mine = [r for r in rows if r["id"] == "soxl_pm_breakout"]
        self.assertEqual(len(mine), 1)
        row = mine[0]
        self.assertEqual(row["module"], "adapters3.soxl_pm_breakout")
        self.assertFalse(row["parked"])
        self.assertEqual(row["slice"], {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0})
        self.assertEqual(row["cadence_s"], 60)
        self.assertEqual(row["session"], "rth")
        self.assertTrue(row["flat_by_close"])
        self.assertEqual(row["flatten_time_et"], "15:45")
        self.assertEqual(row["inputs"], ["bars", "bars:SOXL:15Min",
                                         "positions", "quotes",
                                         "session_fills"])
        importlib.import_module(row["module"])


if __name__ == "__main__":
    unittest.main()
