"""PRZM-ZERO-RISKSHAPE-20261116 regression blockers (owner ruling
2026-11-16 12:46 ET, "Make it work" — the unblocker the BUGLOG's
BLOCKED disposition named at (a)).

The cure landed for sleeves/przm_zero.py, two parts:

Part 1 — session stop at the sourced family standard:
DAILY_LOSS_FRACTION = 0.01 of slice equity, sourced from
sleeves/saty_magnum.py SESSION_STOP_PCT = 0.01 and
sleeves/saty_sol_0dte.py DAILY_LOSS_FRACTION = 0.01 (the same
pair saty_day cites for its DAILY_STOP_FRACTION). Session P&L is
the realized P&L accumulated in przm_state across the session's
closed calls (each closed call records its exit price and
realized P&L, priced at its exit intent's price_hint, with qty
recorded at entry) plus the open call marked at the current
spot. At session P&L <= -DAILY_LOSS_FRACTION * slice equity, no
NEW entries are taken for the rest of the session; exits
(drop/flip and the 15:45 force-close) continue normally. Slice
equity is ctx.equity — the serving adapter
(adapters/przm_zero.py) builds this sleeve's Context with
equity = the config slice's capital_usd ($10,000), the same
source saty_day reads. The halt is journaled on the evaluation
stamp as daily_stop_halt / daily_stop_fraction / daily_stop_usd
plus session_pnl, saty_day's field names.

Part 2 — trade-level bounds, journaled, from the structures
przm_zero actually trades: long SPY shares are defined-risk, so
each long call record journals max_loss_usd = qty * entry px.
Short SPY shares are undefined-risk; the estate search recorded
in BUGLOG_2026-11-16.md (przm_fade_edges INVALID_FRAC bound to a
gamma edge przm_zero never computes; saty_day / saty_sol_0dte
anchor/ATR ladder; shen_fade option-premium bracket; em_1587 box
1R; milkman_0dte book stop only; grok_sr_spy S/R band;
teddy_orb_spy opening range; trullas_divergence pivot;
raschke_pf3 ATR anchor; bta_onebar_qqq QQQ STOP_PCT translated
from that system's NQ dollar stop; red_day_reversal long-only
multi-day) found NO genuinely transferable same-structure
bound, so no level was invented: short call records journal
risk_bound = "session_stop_only" — the named remaining gap.

FALSIFIER (registered in BUGLOG_2026-11-16.md under
PRZM-ZERO-RISKSHAPE-20261116): this shape is re-derived from
przm_zero's own recorded calls once they exist — first read at
the 2026-11-16 night inspection if today's first fed session
produced calls, otherwise at its first 20 recorded calls; any
contradiction reopens the item.

Proven here: (a) the session stop halts new entries at the
fraction on a fixture drive (realized losses accumulated across
closed calls past 1% of the slice, then a fresh entry signal
emits no entry intent and the stamp carries
daily_stop_halt/fraction/usd), while an exit intent for an open
position is still emitted after the halt; (b) no emitted Intent
in any fixture carries a stop or target field (the family
standard preserved); (c) long entries journal
max_loss_usd = qty * entry px; (d) the short-side outcome:
risk_bound = "session_stop_only" journaling, with the session
stop as its only bound (open short marked through the stop
stamps the halt, and its exit still fires).
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
SESSION = "2026-10-29"


def _bars(spot, hh, mm):
    """Flat 1-minute SPY bars 09:30 -> hh:mm ET on the session day
    at a constant spot."""
    t0 = datetime(2026, 10, 29, 9, 30, tzinfo=ET).timestamp()
    end = datetime(2026, 10, 29, hh, mm, tzinfo=ET).timestamp()
    n = int((end - t0) // 60) + 1
    return [{"t": t0 + i * 60, "o": spot, "h": spot, "l": spot,
             "c": spot, "v": 1000} for i in range(n)]


def _prints(bars, legs):
    """legs: [(bull, size)] prints on the last bar. delta 0.5,
    price 3.0, plain calls — spec weight 1.0 each."""
    t_ms = int(bars[-1]["t"] * 1000)
    return [{"t": t_ms, "bull": b, "delta": 0.5, "price": 3.0,
             "size": s, "is_call": True} for b, s in legs]


def _drive(state, spot, hh, mm, legs, slice_state=None, equity=10000.0):
    from core.sleeve import Context
    from sleeves.przm_zero import PrzmZeroSleeve
    bars = _bars(spot, hh, mm)
    now = datetime(2026, 10, 29, hh, mm, tzinfo=ET).timestamp()
    extra = {"przm_prints": _prints(bars, legs),
             "przm_state": state}
    ctx = Context(now=now, session=SESSION, equity=equity, extra=extra)
    sl = PrzmZeroSleeve()
    out = sl.signal({"SPY": bars}, slice_state or {}, ctx)
    return out, sl


def _fresh_state():
    return {"day": SESSION, "direction": 0, "since_ms": None,
            "calls": [], "open_call": None}


STRONG_LONG = [(1, 100)]
STRONG_SHORT = [(-1, 100)]
# net/abs = (100-90)/(100+90) -> score ~5: a drop signal past the
# minimum hold, far from the flip threshold.
FADED = [(1, 100), (-1, 90)]
FADED_SHORT = [(-1, 100), (1, 90)]


class TestSessionStopSource(unittest.TestCase):
    def test_fraction_matches_both_sibling_sources(self):
        from sleeves import przm_zero, saty_magnum, saty_sol_0dte
        self.assertEqual(przm_zero.DAILY_LOSS_FRACTION, 0.01)
        self.assertEqual(przm_zero.DAILY_LOSS_FRACTION,
                         saty_magnum.SESSION_STOP_PCT)
        self.assertEqual(przm_zero.DAILY_LOSS_FRACTION,
                         saty_sol_0dte.DAILY_LOSS_FRACTION)


class TestSessionStopHalt(unittest.TestCase):
    def test_realized_losses_across_calls_halt_new_entries(self):
        # Call 1: long at 100 (qty 10), dropped at 92.5 -> -75.00.
        out, sl = _drive(_fresh_state(), 100.0, 10, 0, STRONG_LONG)
        self.assertEqual([i.kind for i in out], ["enter"])
        st = sl.przm_state
        out, sl = _drive(st, 92.5, 10, 11, FADED,
                         slice_state={"SPY": 10})
        self.assertEqual([i.kind for i in out], ["exit"])
        st = sl.przm_state
        closed = [c for c in st["calls"] if "realized_pnl" in c]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["realized_pnl"], -75.0)
        self.assertEqual(closed[0]["exit_px"], 92.5)
        # -75 > -100: a fresh entry is still allowed.
        out, sl = _drive(st, 92.5, 10, 12, STRONG_LONG)
        self.assertEqual([i.kind for i in out], ["enter"])
        st = sl.przm_state
        # Call 2: long at 92.5 (qty 10), dropped at 85 -> -75.00.
        out, sl = _drive(st, 85.0, 10, 23, FADED,
                         slice_state={"SPY": 10})
        self.assertEqual([i.kind for i in out], ["exit"])
        st = sl.przm_state
        closed = [c for c in st["calls"] if "realized_pnl" in c]
        self.assertEqual(len(closed), 2)
        self.assertEqual(sum(c["realized_pnl"] for c in closed), -150.0)
        # Session P&L -150 <= -1% of the $10,000 slice: a fresh
        # entry signal emits NO entry intent, and the stamp
        # carries the halt in saty_day's field names.
        out, sl = _drive(st, 85.0, 10, 24, STRONG_LONG)
        self.assertEqual(out, [])
        stamp = sl.last_evaluation
        self.assertEqual(stamp["daily_stop_halt"], True)
        self.assertEqual(stamp["daily_stop_fraction"], 0.01)
        self.assertEqual(stamp["daily_stop_usd"], 100.0)
        self.assertEqual(stamp["session_pnl"], -150.0)

    def test_exit_still_emitted_after_halt(self):
        # A session already past the stop (one closed call at
        # -150) with a position still open: the 15:45 force-close
        # exit is emitted normally after the halt.
        open_call = {"t_ms": 1, "px": 100.0, "direction": 1,
                     "qty": 10, "max_loss_usd": 1000.0}
        st = {"day": SESSION, "direction": 1, "since_ms": 1,
              "calls": [{"t_ms": 0, "px": 110.0, "direction": 1,
                         "qty": 10, "exit_px": 95.0,
                         "realized_pnl": -150.0}, open_call],
              "open_call": open_call}
        out, sl = _drive(st, 100.0, 15, 45, STRONG_LONG,
                         slice_state={"SPY": 10})
        self.assertEqual([i.kind for i in out], ["exit"])
        self.assertEqual(sl.last_evaluation["daily_stop_halt"], True)


class TestFamilyStandardPreserved(unittest.TestCase):
    def test_no_intent_carries_stop_or_target(self):
        seen = []
        out, sl = _drive(_fresh_state(), 100.0, 10, 0, STRONG_LONG)
        seen += out
        out, sl = _drive(sl.przm_state, 92.5, 10, 11, FADED,
                         slice_state={"SPY": 10})
        seen += out
        out, sl = _drive(_fresh_state(), 100.0, 10, 0, STRONG_SHORT)
        seen += out
        out, sl = _drive(sl.przm_state, 120.0, 10, 11, FADED_SHORT,
                         slice_state={"SPY": -10})
        seen += out
        self.assertEqual(len(seen), 4)
        for it in seen:
            self.assertIsNone(it.stop)
            self.assertIsNone(it.target)


class TestTradeLevelBounds(unittest.TestCase):
    def test_long_entry_journals_structure_max_loss(self):
        out, sl = _drive(_fresh_state(), 100.0, 10, 0, STRONG_LONG)
        self.assertEqual(out[0].position_intent, "buy_to_open")
        call = sl.przm_state["calls"][-1]
        self.assertEqual(call["qty"], 10)
        self.assertEqual(call["max_loss_usd"], 10 * 100.0)
        self.assertNotIn("risk_bound", call)

    def test_short_entry_journals_session_stop_only(self):
        out, sl = _drive(_fresh_state(), 100.0, 10, 0, STRONG_SHORT)
        self.assertEqual(out[0].position_intent, "sell_to_open")
        call = sl.przm_state["calls"][-1]
        self.assertEqual(call["risk_bound"], "session_stop_only")
        self.assertNotIn("max_loss_usd", call)
        st = sl.przm_state
        # The open short marked at 120 is -200 of session P&L:
        # the session stop — its only bound — stamps the halt.
        out, sl = _drive(st, 120.0, 10, 5, STRONG_SHORT,
                         slice_state={"SPY": -10})
        self.assertEqual(out, [])
        self.assertEqual(sl.last_evaluation["session_pnl"], -200.0)
        self.assertEqual(sl.last_evaluation["daily_stop_halt"], True)
        # And its exit still fires after the halt (drop past the
        # minimum hold), recording the realized loss.
        out, sl = _drive(sl.przm_state, 120.0, 10, 11, FADED_SHORT,
                         slice_state={"SPY": -10})
        self.assertEqual([i.kind for i in out], ["exit"])
        closed = [c for c in sl.przm_state["calls"]
                  if "realized_pnl" in c]
        self.assertEqual(closed[-1]["realized_pnl"], -200.0)


if __name__ == "__main__":
    unittest.main()
