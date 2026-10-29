"""investandbefree_dmac blockers (INVESTANDBEFREE-DMAC-SPEC-2026-10-29, FROZEN).

Edge UNPROVEN; no backtest is claimed by these tests — they pin the
frozen spec's mechanics. Golden expectations are computed
independently in this file: the MACD expectations come from the tiny
independent implementation below (written separately from the
sleeve's code) plus hand-embedded values for the crafted series, and
the sizing/partial/strike expectations are hand arithmetic stated
in each test. The sleeve's own functions are never used to generate
an expectation.

Crafted MACD series (35 closes):
  [10,11,12,11,12,13,14,13,14,15,16,15,16,17,18,17,18,19,20,19,
   20,21,22,21,22,23,24,23,24,25,26,25,26,27,28]
Independent hand calculation (seed = mean of first `period` values;
exponential alpha 2/(p+1), Wilder alpha 1/p; signal smoothed the
same way as its MACD, seeded on the first 9 MACD values):
  MACD-E last line 3.552095, signal 3.506225
  MACD-W last line 3.008849, signal 2.305244
The two smoothings genuinely diverge on this series (line gap
0.543), which is the point of the fixture.
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

CRAFTED = [10, 11, 12, 11, 12, 13, 14, 13, 14, 15, 16, 15, 16, 17, 18,
           17, 18, 19, 20, 19, 20, 21, 22, 21, 22, 23, 24, 23, 24, 25,
           26, 25, 26, 27, 28]
GOLD_E_LINE, GOLD_E_SIG = 3.552095, 3.506225
GOLD_W_LINE, GOLD_W_SIG = 3.008849, 2.305244


def ind_smooth(values, period, wilder):
    """Independent smoothing (test-only, written from the definition)."""
    alpha = 1.0 / period if wilder else 2.0 / (period + 1)
    out = [None] * len(values)
    if len(values) < period:
        return out
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = prev + alpha * (values[i] - prev)
        out[i] = prev
    return out


def ind_macd(closes, wilder):
    fast = ind_smooth(closes, 12, wilder)
    slow = ind_smooth(closes, 26, wilder)
    mac = [None if f is None or s is None else f - s
           for f, s in zip(fast, slow)]
    defined = [v for v in mac if v is not None]
    sig_def = ind_smooth(defined, 9, wilder)
    sig = [None] * len(closes)
    j = 0
    for i, v in enumerate(mac):
        if v is not None:
            sig[i] = sig_def[j]
            j += 1
    return mac, sig


def bull_closes(n=60):
    return [50 + 0.05 * i * i for i in range(n)]


def bear_closes(n=60):
    return [300 - 0.05 * i * i for i in range(n)]


def crossover_closes():
    """Bull run, 3 bars of -5 (MACD-E pushed under its signal), then
    +30 on the last bar: MACD-E crosses up on the last closed bar."""
    c = bull_closes()
    last = c[-1]
    for _ in range(3):
        last -= 5
        c.append(last)
    c.append(last + 30)
    return c


def curl_closes():
    """Bull run, 2 bars of -5 (a pullback in the MACD line), then
    +15: the line curls back up without a signal-line cross."""
    c = bull_closes()
    last = c[-1]
    for _ in range(2):
        last -= 5
        c.append(last)
    c.append(last + 15)
    return c


def _bars(closes, day0=1):
    # Timestamps END at 2026-10-28 00:00 ET, the last CLOSED daily
    # bar relative to _ctx (2026-10-29 12:00 ET, mid-session). The
    # frozen spec is closed-bars-only, so fixtures must not hand
    # the sleeve bars whose period has not ended at "now" (an
    # earlier version of this helper dated bars into November,
    # past the fixture now, which the closed-bars cure in
    # sleeves/investandbefree_dmac.closed_bars would rightly drop).
    end = datetime(2026, 10, 29, 0, 0, tzinfo=ET).timestamp()
    out = []
    n = len(closes)
    for i, c in enumerate(closes):
        t = end - (n - i) * 86400
        out.append({"t": t, "o": float(c), "h": float(c), "l": float(c),
                    "c": float(c), "v": 1000.0})
    return out


def _ctx(extra, equity=EQUITY):
    from core.sleeve import Context
    return Context(now=datetime(2026, 10, 29, 12, 0, tzinfo=ET).timestamp(),
                   session=SESSION, equity=equity, extra=extra)


OCC_CALL = "SPY261128C00239000"   # SPY 2026-11-28 call 239
OCC_PUT = "SPY261128P00239000"


def chain_quotes(spot_ask=5.0, spot_bid=4.9):
    chain = [
        {"symbol": "SPY261110C00239000", "strike": 239.0,
         "expiry": "2026-11-10", "right": "call"},          # 12 DTE: too soon
        {"symbol": OCC_CALL, "strike": 239.0,
         "expiry": "2026-11-28", "right": "call"},          # exactly 30 DTE
        {"symbol": "SPY261128C00245000", "strike": 245.0,
         "expiry": "2026-11-28", "right": "call"},
        {"symbol": "SPY261219C00239000", "strike": 239.0,
         "expiry": "2026-12-19", "right": "call"},          # later expiry
        {"symbol": OCC_PUT, "strike": 239.0,
         "expiry": "2026-11-28", "right": "put"},
    ]
    quotes = {c["symbol"]: {"bid": spot_bid, "ask": spot_ask} for c in chain}
    return chain, quotes


def drive_entry(closes, weekly=None, chain=None, quotes=None):
    from sleeves.investandbefree_dmac import InvestAndBeFreeDmacSleeve
    chain, quotes = (chain, quotes) if chain is not None else chain_quotes()
    sleeve = InvestAndBeFreeDmacSleeve()
    extra = {"bars_weekly": {"SPY": _bars(weekly if weekly is not None
                                          else bull_closes())},
             "bars_1h": {}, "chains": {"SPY": chain}, "quotes": quotes,
             "sleeve_state": {}, "dmac_state": {}}
    return sleeve.signal({"SPY": _bars(closes)}, {}, _ctx(extra)), sleeve


class TestMacdGolden(unittest.TestCase):
    def test_wilder_vs_exponential_diverge_on_crafted_series(self):
        from sleeves.investandbefree_dmac import macd_series
        e_line, e_sig = macd_series(CRAFTED, wilder=False)
        w_line, w_sig = macd_series(CRAFTED, wilder=True)
        self.assertAlmostEqual(e_line[-1], GOLD_E_LINE, places=5)
        self.assertAlmostEqual(e_sig[-1], GOLD_E_SIG, places=5)
        self.assertAlmostEqual(w_line[-1], GOLD_W_LINE, places=5)
        self.assertAlmostEqual(w_sig[-1], GOLD_W_SIG, places=5)
        self.assertGreater(abs(e_line[-1] - w_line[-1]), 0.5)
        # Independent implementation agrees with the embedded goldens.
        ie_line, ie_sig = ind_macd(CRAFTED, False)
        iw_line, iw_sig = ind_macd(CRAFTED, True)
        self.assertAlmostEqual(ie_line[-1], GOLD_E_LINE, places=5)
        self.assertAlmostEqual(iw_line[-1], GOLD_W_LINE, places=5)
        self.assertAlmostEqual(ie_sig[-1], GOLD_E_SIG, places=5)
        self.assertAlmostEqual(iw_sig[-1], GOLD_W_SIG, places=5)

    def test_components_separately_unit_testable(self):
        from sleeves.investandbefree_dmac import ema_exponential, ema_wilder
        vals = [float(i) for i in range(1, 31)]
        e = ema_exponential(vals, 12)
        w = ema_wilder(vals, 12)
        ie = ind_smooth(vals, 12, False)
        iw = ind_smooth(vals, 12, True)
        for got, exp in ((e, ie), (w, iw)):
            for a, b in zip(got, exp):
                if b is None:
                    self.assertIsNone(a)
                else:
                    self.assertAlmostEqual(a, b, places=9)
        self.assertNotAlmostEqual(e[-1], w[-1], places=3)


class TestAlignmentDominance(unittest.TestCase):
    def test_alignment_bull_bear_none(self):
        from sleeves.investandbefree_dmac import alignment_of
        self.assertEqual(alignment_of(bull_closes()), 1)
        self.assertEqual(alignment_of(bear_closes()), -1)
        self.assertIsNone(alignment_of([100.0] * 60))  # lines == signals
        self.assertIsNone(alignment_of(bull_closes(20)))  # too short

    def test_dominance_slowest_aligned_wins(self):
        from sleeves.investandbefree_dmac import evaluate_timeframes
        f = evaluate_timeframes(bull_closes(), bear_closes(), [])
        self.assertEqual(f["weekly"], -1)
        self.assertEqual(f["daily"], 1)
        self.assertEqual(f["dominant_tf"], "weekly")
        self.assertEqual(f["dominant_dir"], -1)
        f2 = evaluate_timeframes(bull_closes(), [100.0] * 60, [])
        self.assertIsNone(f2["weekly"])
        self.assertEqual(f2["dominant_tf"], "daily")
        self.assertEqual(f2["dominant_dir"], 1)

    def test_no_trade_on_disagreement(self):
        intents, _ = drive_entry(crossover_closes(), weekly=bear_closes())
        self.assertEqual(intents, [])


class TestTriggers(unittest.TestCase):
    def test_crossover_trigger(self):
        from sleeves.investandbefree_dmac import find_trigger
        closes = crossover_closes()
        # Independent check: MACD-E diff prev <= 0 < last.
        mac, sig = ind_macd(closes, False)
        self.assertLessEqual(mac[-2] - sig[-2], 0)
        self.assertGreater(mac[-1] - sig[-1], 0)
        self.assertEqual(find_trigger(closes, 1), "crossover")
        intents, _ = drive_entry(closes)
        self.assertEqual(len(intents), 1)
        self.assertIn("trigger=crossover", intents[0].reason)

    def test_curl_trigger(self):
        from sleeves.investandbefree_dmac import find_trigger
        closes = curl_closes()
        mac_e, sig_e = ind_macd(closes, False)
        # Not a crossover on the last bar:
        self.assertGreater(mac_e[-2] - sig_e[-2], 0)
        self.assertEqual(find_trigger(closes, 1), "curl")
        intents, _ = drive_entry(closes)
        self.assertEqual(len(intents), 1)
        self.assertIn("trigger=curl", intents[0].reason)

    def test_no_trigger_no_trade(self):
        intents, _ = drive_entry(bull_closes())
        # A plain bull run may curl/cross only if the fixture says so;
        # the last bar of the smooth run has rising MACD steps with no
        # pullback step and no cross, so no entry is due.
        self.assertEqual(intents, [])


class TestContractSelection(unittest.TestCase):
    def test_atm_and_min_30dte(self):
        from sleeves.investandbefree_dmac import select_contract
        chain, quotes = chain_quotes()
        sel = select_contract(chain, quotes, 239.05, SESSION, 1)
        self.assertEqual(sel["occ"], OCC_CALL)
        self.assertEqual(sel["expiry"], "2026-11-28")  # 30 DTE, nearest >= 30
        self.assertEqual(sel["strike"], 239.0)         # nearest to 239.05
        put = select_contract(chain, quotes, 239.05, SESSION, -1)
        self.assertEqual(put["occ"], OCC_PUT)

    def test_spread_gate_rejects_wide_quote(self):
        from sleeves.investandbefree_dmac import select_contract
        chain, quotes = chain_quotes(spot_ask=5.0, spot_bid=4.0)
        # (5.0-4.0)/4.5 = 0.222 > 0.10 for every quoted contract.
        self.assertIsNone(select_contract(chain, quotes, 239.05, SESSION, 1))
        intents, _ = drive_entry(crossover_closes(), chain=chain, quotes=quotes)
        self.assertEqual(intents, [])


class TestSizing(unittest.TestCase):
    def test_budget_floor_and_cap(self):
        from sleeves.investandbefree_dmac import qty_for_position
        # floor(2000/500) = 4; cap floor(2500/500) = 5 -> 4.
        self.assertEqual(qty_for_position(5.0, 10000.0), 4)
        # Budget binds: floor(2000/200) = 10 < cap floor(2500/200) = 12.
        self.assertEqual(qty_for_position(2.0, 10000.0), 10)
        # Cap binds: slice 4000 -> cap 1000; floor(1000/200) = 5 < 10.
        self.assertEqual(qty_for_position(2.0, 4000.0), 5)

    def test_single_contract_over_cap_skips(self):
        from sleeves.investandbefree_dmac import qty_for_position
        # One contract = 500 premium > 25% of a 1000 slice (250).
        self.assertEqual(qty_for_position(5.0, 1000.0), 0)
        self.assertEqual(qty_for_position(30.0, 10000.0), 0)


class TestExits(unittest.TestCase):
    def _drive_pos(self, pos, quotes, closes=None, weekly=None):
        from sleeves.investandbefree_dmac import InvestAndBeFreeDmacSleeve
        sleeve = InvestAndBeFreeDmacSleeve()
        extra = {"bars_weekly": {"SPY": _bars(weekly if weekly is not None
                                              else bull_closes())},
                 "bars_1h": {}, "chains": {}, "quotes": quotes,
                 "sleeve_state": {"SPY": {"position": pos}},
                 "dmac_state": {"SPY": dict(pos)}}
        return sleeve.signal({"SPY": _bars(closes or bull_closes())}, {},
                             _ctx(extra)), sleeve

    def _pos(self, **kw):
        pos = {"occ": OCC_CALL, "qty": 4, "entry_premium": 5.0,
               "expiry": "2026-11-28", "direction": 1, "partial_done": False}
        pos.update(kw)
        return pos

    def test_partial_qty_math(self):
        from sleeves.investandbefree_dmac import partial_qty
        # ceil(4*5/10) = 2 sold, 2 runners remain.
        self.assertEqual(partial_qty(4, 5.0, 10.0), 2)
        # ceil(3*5/10) = 2 sold, exactly 1 runner remains.
        self.assertEqual(partial_qty(3, 5.0, 10.0), 2)
        # ceil(5*4/12) = 2.
        self.assertEqual(partial_qty(5, 4.0, 12.0), 2)
        # Below +100% no partial is due.
        self.assertEqual(partial_qty(4, 5.0, 9.99), 0)
        # qty 1: the partial is a full exit.
        self.assertEqual(partial_qty(1, 5.0, 10.0), 1)

    def test_partial_fires_once_and_qty1_full_exit(self):
        quotes = {OCC_CALL: {"bid": 9.9, "ask": 10.1}}  # mid 10.0 = +100%
        intents, sleeve = self._drive_pos(self._pos(), quotes)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].kind, "exit")
        self.assertEqual(intents[0].qty, 2)
        self.assertIn("partial_100pct", intents[0].reason)
        self.assertTrue(sleeve.dmac_state["SPY"]["partial_done"])
        # Once done, the same quote produces no second partial.
        intents2, _ = self._drive_pos(self._pos(qty=2, partial_done=True),
                                      quotes)
        self.assertEqual(intents2, [])
        # qty 1 at +100%: full exit.
        intents3, _ = self._drive_pos(self._pos(qty=1), quotes)
        self.assertEqual(len(intents3), 1)
        self.assertEqual(intents3[0].qty, 1)
        self.assertIn("partial_full_exit_qty1", intents3[0].reason)

    def test_premium_stop_exit(self):
        quotes = {OCC_CALL: {"bid": 2.4, "ask": 2.6}}  # mid 2.5 = 50% of 5.0
        intents, _ = self._drive_pos(self._pos(), quotes)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 4)
        self.assertIn("premium_stop_50pct", intents[0].reason)
        above = {OCC_CALL: {"bid": 2.51, "ask": 2.71}}  # mid 2.61 > 2.5
        intents2, _ = self._drive_pos(self._pos(), above)
        self.assertEqual(intents2, [])

    def test_runner_5dte_exit(self):
        quotes = {OCC_CALL: {"bid": 5.9, "ask": 6.1}}
        pos = self._pos(qty=2, partial_done=True, expiry="2026-11-03")  # 5 DTE
        intents, _ = self._drive_pos(pos, quotes)
        self.assertEqual(len(intents), 1)
        self.assertIn("runner_5dte", intents[0].reason)
        pos6 = self._pos(qty=2, partial_done=True, expiry="2026-11-04")  # 6 DTE
        intents2, _ = self._drive_pos(pos6, quotes)
        self.assertEqual(intents2, [])

    def test_dominant_break_exit(self):
        quotes = {OCC_CALL: {"bid": 5.9, "ask": 6.1}}
        intents, _ = self._drive_pos(self._pos(), quotes,
                                     closes=bear_closes(),
                                     weekly=bear_closes())
        self.assertEqual(len(intents), 1)
        self.assertIn("dominant_alignment_break", intents[0].reason)


class TestFourHourAggregation(unittest.TestCase):
    def test_buckets_complete_only_and_anchored(self):
        from sleeves.investandbefree_dmac import aggregate_4h
        bars = []
        for day in (27, 28):
            for h in range(7):  # 09:30 + h hours, RTH hourly starts
                t = datetime(2026, 10, day, 9, 30, tzinfo=ET).timestamp() + h * 3600
                bars.append({"t": t, "o": 100 + h, "h": 101 + h,
                             "l": 99 + h, "c": 100.5 + h, "v": 10.0})
        agg = aggregate_4h(bars)
        # 7 bars/day -> one complete 4-bar bucket per day; the 3-bar
        # remainder is never emitted.
        self.assertEqual(len(agg), 2)
        self.assertEqual(agg[0]["o"], 100.0)
        self.assertEqual(agg[0]["h"], 104.0)
        self.assertEqual(agg[0]["l"], 99.0)
        self.assertEqual(agg[0]["c"], 103.5)
        self.assertEqual(agg[0]["v"], 40.0)


class TestAdapterDrive(unittest.TestCase):
    def test_adapter_drive_entry_and_state_roundtrip(self):
        mod = importlib.import_module("adapters3.investandbefree_dmac")
        from datetime import timezone as _tz

        def iso_bars(closes):
            return [{"t": datetime.fromtimestamp(b["t"], _tz.utc).isoformat(),
                     "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                     "v": b["v"]} for b in _bars(closes)]

        chain, quotes = chain_quotes()
        view = {"now": datetime(2026, 10, 29, 12, 0, tzinfo=ET).isoformat(),
                "bars": {"SPY|1Day": iso_bars(crossover_closes()),
                         "SPY|1Week": iso_bars(bull_closes()),
                         "QQQ|1Day": iso_bars(bull_closes()),
                         "QQQ|1Week": iso_bars(bull_closes())},
                "options": {"SPY": {"chains": {"SPY": chain},
                                    "quotes": quotes}},
                "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
            self.assertTrue(os.path.exists(
                os.path.join(td, "dmac_state.json")))
            saved = json.load(open(os.path.join(td, "dmac_state.json")))
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(entries[0]["qty"], 4)  # floor(2000/(5.0*100))
        self.assertEqual(entries[0]["position_intent"], "buy_to_open")
        self.assertEqual(entries[0]["limit_price"], 5.0)
        self.assertEqual(saved["dmac_state"]["SPY"]["occ"], OCC_CALL)
        self.assertFalse(saved["dmac_state"]["SPY"]["partial_done"])


class TestClosedBarsOnly(unittest.TestCase):
    """Regression blocker for the 2026-10-29 verifier finding: the
    live path served forming bars (today's daily, the current
    week, the in-progress hour) and signal() consumed bars[-1]
    unconditionally. Mid-session now = 2026-10-29 12:00 ET."""

    NOW = datetime(2026, 10, 29, 12, 0, tzinfo=ET).timestamp()

    def test_closed_bars_period_ends_all_timeframes(self):
        from sleeves.investandbefree_dmac import closed_bars
        # 1Day: yesterday's bar kept, today's (forming) dropped.
        daily = [{"t": datetime(2026, 10, 28, tzinfo=ET).timestamp(), "c": 1.0},
                 {"t": datetime(2026, 10, 29, tzinfo=ET).timestamp(), "c": 2.0}]
        kept = closed_bars(daily, "1Day", self.NOW)
        self.assertEqual([b["c"] for b in kept], [1.0])
        # 1Week: the week of Mon 2026-10-19 ended Mon 2026-10-26
        # 00:00 ET (kept); the current week (Mon 2026-10-26) has
        # not ended (dropped).
        weekly = [{"t": datetime(2026, 10, 19, tzinfo=ET).timestamp(), "c": 1.0},
                  {"t": datetime(2026, 10, 26, tzinfo=ET).timestamp(), "c": 2.0}]
        kept = closed_bars(weekly, "1Week", self.NOW)
        self.assertEqual([b["c"] for b in kept], [1.0])
        # 1Hour: the 11:00 ET bar ends exactly at now (kept); the
        # 12:00 ET bar is in progress (dropped).
        hourly = [{"t": datetime(2026, 10, 29, 11, 0, tzinfo=ET).timestamp(), "c": 1.0},
                  {"t": datetime(2026, 10, 29, 12, 0, tzinfo=ET).timestamp(), "c": 2.0}]
        kept = closed_bars(hourly, "1Hour", self.NOW)
        self.assertEqual([b["c"] for b in kept], [1.0])
        # No readable timestamp: cannot be proven closed, dropped.
        self.assertEqual(closed_bars([{"c": 1.0}], "1Day", self.NOW), [])

    def test_forming_daily_and_weekly_bars_do_not_change_entry(self):
        from sleeves.investandbefree_dmac import InvestAndBeFreeDmacSleeve
        chain, quotes = chain_quotes()
        base_daily = _bars(crossover_closes())
        base_weekly = _bars(bull_closes())
        forming_daily = {"t": datetime(2026, 10, 29, tzinfo=ET).timestamp(),
                         "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 1.0}
        forming_weekly = {"t": datetime(2026, 10, 26, tzinfo=ET).timestamp(),
                          "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 1.0}

        def drive(daily, weekly):
            sleeve = InvestAndBeFreeDmacSleeve()
            extra = {"bars_weekly": {"SPY": weekly}, "bars_1h": {},
                     "chains": {"SPY": chain}, "quotes": quotes,
                     "sleeve_state": {}, "dmac_state": {}}
            return sleeve.signal({"SPY": daily}, {}, _ctx(extra))

        clean = drive(base_daily, base_weekly)
        self.assertEqual(len(clean), 1)
        dirty = drive(base_daily + [forming_daily],
                      base_weekly + [forming_weekly])
        # The crash-priced forming bars would destroy the daily
        # alignment and the trigger if consumed; closed-bars-only
        # means the mid-session decision is identical.
        self.assertEqual(len(dirty), 1)
        self.assertEqual(dirty[0].reason, clean[0].reason)
        self.assertEqual(dirty[0].qty, clean[0].qty)

    def test_adapter_mid_session_forming_bars_ignored(self):
        mod = importlib.import_module("adapters3.investandbefree_dmac")
        from datetime import timezone as _tz

        def iso_bars(bars):
            return [{"t": datetime.fromtimestamp(b["t"], _tz.utc).isoformat(),
                     "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                     "v": b["v"]} for b in bars]

        chain, quotes = chain_quotes()
        spy_daily = _bars(crossover_closes()) + [
            {"t": datetime(2026, 10, 29, tzinfo=ET).timestamp(),
             "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 1.0}]
        spy_weekly = _bars(bull_closes()) + [
            {"t": datetime(2026, 10, 26, tzinfo=ET).timestamp(),
             "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 1.0}]
        view = {"now": datetime(2026, 10, 29, 12, 0, tzinfo=ET).isoformat(),
                "bars": {"SPY|1Day": iso_bars(spy_daily),
                         "SPY|1Week": iso_bars(spy_weekly),
                         "QQQ|1Day": iso_bars(_bars(bull_closes())),
                         "QQQ|1Week": iso_bars(_bars(bull_closes()))},
                "options": {"SPY": {"chains": {"SPY": chain},
                                    "quotes": quotes}},
                "positions": [],
                "slice": {"capital_usd": EQUITY, "cash_usd": EQUITY},
                "params": {}}
        with tempfile.TemporaryDirectory() as td:
            out = mod.evaluate(view, {"state_dir": td})
        entries = [d for d in out if d["kind"] == "entry"]
        self.assertEqual(len(entries), 1, out)
        self.assertEqual(entries[0]["symbol"], OCC_CALL)
        self.assertEqual(entries[0]["qty"], 4)


class TestAlignmentLossExits(unittest.TestCase):
    """Regression blocker for the verifier's secondary finding: a
    complete loss of alignment on every timeframe (dominant_dir
    None, daily None) produced no exit, although exit rule (2)
    treats loss of alignment as a break."""

    def _drive_pos(self, pos, quotes, closes):
        from sleeves.investandbefree_dmac import InvestAndBeFreeDmacSleeve
        sleeve = InvestAndBeFreeDmacSleeve()
        extra = {"bars_weekly": {"SPY": _bars(closes)},
                 "bars_1h": {}, "chains": {}, "quotes": quotes,
                 "sleeve_state": {"SPY": {"position": pos}},
                 "dmac_state": {"SPY": dict(pos)}}
        return sleeve.signal({"SPY": _bars(closes)}, {}, _ctx(extra))

    def _pos(self, **kw):
        pos = {"occ": OCC_CALL, "qty": 4, "entry_premium": 5.0,
               "expiry": "2026-11-28", "direction": 1, "partial_done": False}
        pos.update(kw)
        return pos

    def test_total_alignment_loss_exits_open_position(self):
        # Flat closes: both MACDs equal their signals on every
        # timeframe, so weekly/daily/4H alignment is None and
        # dominant_dir is None. Mid 6.0: no premium stop, no
        # partial (+100% needs >= 10.0). Only the alignment-loss
        # break can fire, and it must.
        quotes = {OCC_CALL: {"bid": 5.9, "ask": 6.1}}
        intents = self._drive_pos(self._pos(), quotes, [100.0] * 60)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 4)
        self.assertIn("dominant_alignment_break", intents[0].reason)

    def test_total_alignment_loss_exits_runner(self):
        quotes = {OCC_CALL: {"bid": 5.9, "ask": 6.1}}
        pos = self._pos(qty=2, partial_done=True)
        intents = self._drive_pos(pos, quotes, [100.0] * 60)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].qty, 2)
        self.assertIn("daily_alignment_break_runner", intents[0].reason)


class TestInstallWiring(unittest.TestCase):
    def test_config_row_and_roster_delta(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = cfg["sleeves"]
        self.assertEqual(len(rows), 329)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        mine = [r for r in rows if r["id"] == "investandbefree_dmac"]
        self.assertEqual(len(mine), 1)
        row = mine[0]
        self.assertEqual(row["module"], "adapters3.investandbefree_dmac")
        self.assertFalse(row["parked"])
        self.assertEqual(row["cadence_s"], 3600)
        self.assertEqual(row["session"], "rth")
        self.assertFalse(row["flat_by_close"])
        self.assertEqual(row["slice"]["capital_usd"], 10000.0)
        self.assertEqual(row["slice"]["cash_usd"], 10000.0)

    def test_inputs_declared_and_producer_keys(self):
        mod = importlib.import_module("adapters3.investandbefree_dmac")
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        row = [r for r in cfg["sleeves"]
               if r["id"] == "investandbefree_dmac"][0]
        self.assertEqual(tuple(mod.INPUTS), tuple(row["inputs"]))
        from desk3.producers_g4 import _BARS_TF_KEYS
        for key in mod.INPUTS:
            if key.startswith("bars:"):
                self.assertIn(key, _BARS_TF_KEYS)

    def test_warm_windows_widened_for_feeding(self):
        from desk3.warm import EXTRA_TF_FETCHES, INTRADAY_FETCHES
        self.assertIn(("1Week", 1000), EXTRA_TF_FETCHES)
        self.assertIn(("SPY", "1Hour", 200), INTRADAY_FETCHES)
        self.assertIn(("QQQ", "1Hour", 200), INTRADAY_FETCHES)

    def test_live_warm_product_covers_daily_need(self):
        # The desk's own warm product on disk at build time: SPY/QQQ
        # daily rows must cover the 300-bar warmup the spec names.
        path = os.path.join(ROOT, "state", "warm_bars.json")
        if not os.path.exists(path):
            self.skipTest("warm product absent on this tree")
        doc = json.load(open(path))
        bars = doc.get("bars") or {}
        for sym in ("SPY", "QQQ"):
            self.assertGreaterEqual(len(bars.get(sym + "|1Day") or []), 300)


if __name__ == "__main__":
    unittest.main()
