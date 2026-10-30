"""Blockers for t_cci_corr (installed 2026-10-25, the owner's order;
GrokBot inbox note 2026-10-25 19:40 ET; reference in
quant-research-backup research/cci_correction/).

Pins: the reference signal math (CCI(27) correction + both
triggers), the regime gates, the adopted install sizing (five
$200 slots, whole shares, >$200 skipped), ranking by deepest dip,
the pending-entry lifecycle, and the exit rules (target, trailing
stop ratchet, SMA200, 20-bar time exit).
"""
import json
import os
import sys
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sleeve import Context  # noqa: E402
from sleeves import t_cci_corr as strat  # noqa: E402


def rows_from_closes(closes, vol=1_000_000, start=date(2025, 1, 6)):
    out = []
    d = start
    prev = closes[0]
    for c in closes:
        o = prev
        out.append({"t": d.isoformat(), "o": o,
                    "h": max(o, c) * 1.004, "l": min(o, c) * 0.996,
                    "c": c, "v": vol})
        prev = c
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
    return out


def next_day(iso):
    d = date.fromisoformat(iso) + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


UP = [50 + 0.2 * i for i in range(250)]
DIP = [99.0, 97.5, 95.5, 93.0, 90.5, 89.0, 88.5]
TRIG_A_TAIL = [90.0, 92.5, 92.0]   # CCI crosses back above -100
TRIG_B_TAIL = [90.0, 92.5]         # close > prior high, CCI rising < 0


def spy_rows(n=260):
    return rows_from_closes([400 + 0.2 * i for i in range(n)])


def vix_rows(level=19.0):
    return rows_from_closes([level] * 260)


def signal(bars, slice_state=None, state=None, session=None, vix=None):
    """One strategy evaluation. bars maps sym -> rows (incl. SPY).
    Returns (intents, sleeve) so tests can chain state."""
    last = max(str(r["t"])[:10] for rows in bars.values() for r in rows)
    session = session or next_day(last)
    ctx = Context(now=1_700_000_000.0, session=session, equity=1000.0,
                  extra={"cci_state": state or {},
                         "vix_rows": vix if vix is not None else vix_rows()})
    sleeve = strat.TcciCorrSleeve()
    intents = sleeve.signal(bars, slice_state or {}, ctx)
    return intents, sleeve


def fixture(tail, sym="TEST"):
    rows = rows_from_closes(UP + DIP + tail)
    return {sym: rows, "SPY": spy_rows(len(rows))}, rows


class TestSignalMath(unittest.TestCase):
    def test_cci_of_linear_rise_is_theoretical(self):
        cci = strat._cci_series(rows_from_closes(UP))
        self.assertAlmostEqual(cci[-1], 128.6, delta=1.5)

    def test_atr_seeds_with_first_true_range(self):
        rows = rows_from_closes([100.0, 101.0, 102.0])
        atr = strat._atr_series(rows)
        self.assertAlmostEqual(atr[0], rows[0]["h"] - rows[0]["l"])

    def test_trigger_a_cross_back_enters(self):
        bars, rows = fixture(TRIG_A_TAIL)
        intents, _ = signal(bars)
        self.assertEqual(len(intents), 1)
        it = intents[0]
        self.assertEqual(it.kind, "enter")
        self.assertEqual(it.symbol, "TEST")
        self.assertEqual(it.qty, 2.0)  # $200 slot // $92 close
        self.assertEqual(it.signal_date, rows[-1]["t"])
        atr = strat._atr_series(rows)[-1]
        self.assertAlmostEqual(it.stop, 92.0 - 2 * atr, places=6)
        self.assertAlmostEqual(it.target, 92.0 + 3 * (2 * atr), places=6)
        kinds = {r.kind for r in it.exit_rules}
        self.assertEqual(kinds, {"stop", "target", "time_bars"})

    def test_trigger_b_prior_high_enters(self):
        bars, _ = fixture(TRIG_B_TAIL)
        intents, _ = signal(bars)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].symbol, "TEST")

    def test_no_dip_no_signal(self):
        bars = {"TEST": rows_from_closes(UP + [100.2, 100.4]),
                "SPY": spy_rows()}
        intents, _ = signal(bars)
        self.assertEqual(intents, [])


class TestRegimeAndSizingGates(unittest.TestCase):
    def test_vix_at_30_blocks(self):
        bars, _ = fixture(TRIG_A_TAIL)
        intents, _ = signal(bars, vix=vix_rows(30.0))
        self.assertEqual(intents, [])

    def test_spy_below_sma200_blocks(self):
        bars, _ = fixture(TRIG_A_TAIL)
        bars["SPY"] = rows_from_closes([600 - 0.5 * i for i in range(260)])
        intents, _ = signal(bars)
        self.assertEqual(intents, [])

    def test_price_over_200_skipped(self):
        rows = rows_from_closes([3 * c for c in UP + DIP + TRIG_A_TAIL])
        bars = {"TEST": rows, "SPY": spy_rows()}
        intents, _ = signal(bars)
        self.assertEqual(intents, [])

    def test_slots_cap_five_and_rank_deepest_first(self):
        # Seven candidates on the same dip, recoveries tuned so the
        # signal-bar CCI spreads -98 (S0) to -157 (S6). The five
        # slots must take the five deepest readings, deepest first.
        tails = {"S0": [90.5, 94.0], "S1": [89.5, 94.0],
                 "S2": [90.0, 93.2], "S3": [90.5, 92.5],
                 "S4": [90.5, 91.8], "S5": [89.5, 91.2],
                 "S6": [89.0, 90.6]}
        bars = {"SPY": spy_rows(259)}
        for sym, tail in tails.items():
            bars[sym] = rows_from_closes(UP + DIP + tail)
        intents, _ = signal(bars)
        self.assertEqual([it.symbol for it in intents],
                         ["S6", "S5", "S4", "S3", "S2"])
        ccis = []
        for it in intents:
            s = strat._signal_for(strat._completed(bars[it.symbol],
                                                   "2999-01-01"))
            ccis.append(s["cci"])
        self.assertEqual(ccis, sorted(ccis))


class TestLifecycle(unittest.TestCase):
    def test_pending_no_dup_reemit_then_conversion(self):
        bars, rows = fixture(TRIG_A_TAIL)
        day1 = next_day(rows[-1]["t"])
        intents, sleeve = signal(bars, session=day1)
        self.assertEqual(len(intents), 1)
        state = sleeve.cci_state
        # same session again: no duplicate emission
        intents2, sleeve = signal(bars, state=state, session=day1)
        self.assertEqual(intents2, [])
        # next session, still unfilled: re-emit exactly once
        day2 = next_day(day1)
        intents3, sleeve = signal(bars, state=sleeve.cci_state,
                                  session=day2)
        self.assertEqual(len(intents3), 1)
        # filled: conversion to a managed position, no new entry
        intents4, sleeve = signal(bars, slice_state={"TEST": 2},
                                  state=sleeve.cci_state, session=day2)
        self.assertEqual(intents4, [])
        self.assertIn("TEST", sleeve.cci_state["positions"])
        self.assertEqual(sleeve.cci_state["pending"], {})

    def test_time_exit_after_20_bars(self):
        bars, rows = fixture(TRIG_A_TAIL)
        day1 = next_day(rows[-1]["t"])
        _, sleeve = signal(bars, session=day1)
        state = sleeve.cci_state
        pos_bars = {"TEST": rows, "SPY": spy_rows()}
        session = day1
        exit_seen = None
        for k in range(20):
            last = pos_bars["TEST"][-1]["t"]
            session = next_day(last)
            pos_bars["TEST"] = pos_bars["TEST"] + rows_from_closes(
                [92.0], start=date.fromisoformat(session))
            intents, sleeve = signal(pos_bars, slice_state={"TEST": 2},
                                     state=state, session=next_day(session))
            state = sleeve.cci_state
            if intents:
                exit_seen = (k + 1, intents[0])
                break
        self.assertIsNotNone(exit_seen)
        self.assertEqual(exit_seen[0], 20)
        self.assertEqual(exit_seen[1].kind, "exit")
        self.assertIn("time_exit_20_bars", exit_seen[1].reason)

    def test_target_exit(self):
        bars, rows = fixture(TRIG_A_TAIL)
        day1 = next_day(rows[-1]["t"])
        _, sleeve = signal(bars, session=day1)
        state = sleeve.cci_state
        session = next_day(rows[-1]["t"])
        pos_bars = {"TEST": rows + rows_from_closes(
            [104.0], start=date.fromisoformat(session)), "SPY": spy_rows()}
        intents, _ = signal(pos_bars, slice_state={"TEST": 2},
                            state=state, session=next_day(session))
        self.assertEqual(len(intents), 1)
        self.assertIn("target_on_close", intents[0].reason)

    def test_trail_ratchet_then_stop_exit(self):
        bars, rows = fixture(TRIG_A_TAIL)
        state = {"positions": {"TEST": {
            "entry_ref": 92.0, "signal_date": rows[-1]["t"],
            "stop": 80.0, "target": 130.0, "hi_close": 92.0,
            "bars_held": 1, "last_bar": rows[-1]["t"],
            "exiting": False}}, "pending": {}, "last_scan": None}
        d1 = next_day(rows[-1]["t"])
        up = rows + rows_from_closes([100.0], start=date.fromisoformat(d1))
        intents, sleeve = signal({"TEST": up, "SPY": spy_rows()},
                                 slice_state={"TEST": 2}, state=state,
                                 session=next_day(d1))
        self.assertEqual(intents, [])
        new_stop = sleeve.cci_state["positions"]["TEST"]["stop"]
        self.assertGreater(new_stop, 90.0)  # trailed up from 80
        d2 = next_day(d1)
        down = up + rows_from_closes([90.0], start=date.fromisoformat(d2))
        intents, _ = signal({"TEST": down, "SPY": spy_rows()},
                            slice_state={"TEST": 2},
                            state=sleeve.cci_state, session=next_day(d2))
        self.assertEqual(len(intents), 1)
        self.assertIn("stop_on_close", intents[0].reason)

    def test_sma200_exit(self):
        bars, rows = fixture(TRIG_A_TAIL)
        # hi_close seeded at the falling level so the trailing stop
        # cannot pre-empt the SMA200 rule this test isolates.
        state = {"positions": {"TEST": {
            "entry_ref": 92.0, "signal_date": rows[-1]["t"],
            "stop": 10.0, "target": 400.0, "hi_close": 70.0,
            "bars_held": 1, "last_bar": rows[-1]["t"],
            "exiting": False}}, "pending": {}, "last_scan": None}
        d1 = next_day(rows[-1]["t"])
        down = rows + rows_from_closes(
            [70.0], start=date.fromisoformat(d1))
        intents, _ = signal({"TEST": down, "SPY": spy_rows()},
                            slice_state={"TEST": 2}, state=state,
                            session=next_day(d1))
        self.assertEqual(len(intents), 1)
        self.assertIn("close_below_sma200", intents[0].reason)


class TestInstallShape(unittest.TestCase):
    def test_config_row_and_inputs(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = [r for r in cfg["sleeves"] if r["id"] == "t_cci_corr"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["module"], "adapters3.t_cci_corr")
        self.assertEqual(row["slice"]["capital_usd"], 1000.0)
        self.assertFalse(row["parked"])
        import adapters3.t_cci_corr as mod
        self.assertEqual(row["inputs"], mod.INPUTS)

    def test_adapter_end_to_end(self):
        import tempfile
        from adapters3.t_cci_corr import evaluate
        bars, rows = fixture(TRIG_A_TAIL)
        view = {"now": "2026-01-05T14:35:00+00:00",
                "bars": {"TEST|1Day": bars["TEST"],
                         "SPY|1Day": bars["SPY"]},
                "bars:VIX:1Day": vix_rows(),
                "positions": [],
                "slice": {"capital_usd": 1000.0, "cash_usd": 1000.0},
                "params": {}}
        tmp = tempfile.mkdtemp()
        intents = evaluate(view, {"state_dir": tmp,
                                  "now": view["now"]})
        self.assertEqual(len(intents), 1)
        d = intents[0]
        self.assertEqual(d["kind"], "entry")
        self.assertEqual(d["symbol"], "TEST")
        self.assertEqual(d["qty"], 2.0)
        self.assertIsNotNone(d["stop_price"])
        self.assertGreater(d["target"], 92.0)
        self.assertTrue(os.path.exists(
            os.path.join(tmp, "cci_state.json")))


if __name__ == "__main__":
    unittest.main()
