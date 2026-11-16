"""coffin_rebuilt blockers (2026-11-09).

Provenance: CAND-ROT-04 "The Coffin Rebuilt", formulated from the
Biotech2k rotation family, frozen 2026-11-09 and reproduced by the
independent quantjourney-bt oracle with an identical trade path
(research_notes/biotech2k-rotation-tests-20261109/: SWEEP-REPORT.md,
CROSSCHECK-REPORT.md, qj/CROSSCHECK-FREEZE.md). Installed as a desk
paper sleeve by owner ruling 2026-11-09 (the desk exists to test
individual sleeves). On the pre-install tree these tests fail: the
sleeve modules do not exist and the roster has 337 rows with no
coffin_rebuilt row.

These tests pin the frozen mechanics in the desk's streaming form:
the lowage-only entry gate (rank-from-worst <= 2 on both the
126-session return and the distance below the 126-session high,
low_age >= 20), the daily invalidation exit, the month-end-only
trail15 exit (an intra-month breach that recovers by month-end
never exits — frozen gap G1), the 18-month cap, no double entry,
the streaming month-end definition (a session is a month-end only
when the next session is in a different month), and the
fill-adoption rule that an unconfirmed exit is re-emitted once
per session under the same decision.

Fixtures are hand-worked: business-day sessions from Mon
2026-01-05, every symbol flat at 100 except the driven sector.
XLE decline path (plans A/C/D/E): close falls linearly 100 -> 64
over sessions 0..110, then rises 0.05/session. Session indices:
2026-06-30 is idx 126 (the first month-end with a full 126
window), 2026-07-31 is idx 149, 2026-08-03 is idx 150.
  * At 2026-06-30 the trailing-126 minimum low sits at idx 110,
    so low_age = 126 - 110 = 16 < 20: the gate BLOCKS the entry
    even though XLE is rank-from-worst 1 on both metrics.
  * At 2026-07-31 low_age = 149 - 110 = 39 >= 20, rW =
    65.95/92.47 - 1 < 0 (rank 1), distW rank 1: ENTRY. July's
    minimum XLE low is the 2026-07-01 low, 64.35. Qty =
    floor(10000 / 65.95) = 151. The intent is emitted at the
    2026-08-03 evaluation (the next session), the desk's
    next_bar fill convention.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")

SECTORS = ("XLK", "XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI",
           "XLB", "XLRE", "XLU")
SYMBOLS = SECTORS + ("SPY",)


def business_sessions(start, end):
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


SESSIONS = business_sessions(date(2026, 1, 5), date(2028, 2, 29))
IDX = {d: i for i, d in enumerate(SESSIONS)}


_OTHERS = {sym: k for k, sym in enumerate(
    [s for s in SECTORS if s != "XLE"], start=1)}


def plan_a(sym, i, d):
    """XLE: the decline-and-base path. Every other sector: a mild
    DISTINCT decline (1.5k percent to idx 110, k = its position in
    the sector list) then a slight rise, so every rank is strict.
    Perfectly flat sectors would tie at rW = distW = 0 and the
    frozen tie-break (stable sort in sector order) would make the
    first flat sector a rank-2 candidate whose constant lows give
    it a passing low_age — a degenerate fixture, not a sleeve
    defect: the frozen engine on the same fixture enters XLK at
    the June month-end by the same rules."""
    if sym == "SPY":
        return 100.0
    if sym != "XLE":
        k = _OTHERS[sym]
        if i <= 110:
            return 100.0 - 1.5 * k * i / 110.0
        return (100.0 - 1.5 * k) + (i - 110) * 0.01 * k
    if i <= 110:
        return 100.0 - 36.0 * i / 110.0
    return 64.0 + min(4.0, (i - 110) * 0.05)


def make_rows(plan):
    rows = {}
    for sym in SYMBOLS:
        sym_rows = []
        for i, d in enumerate(SESSIONS):
            c = plan(sym, i, d)
            ts = datetime(d.year, d.month, d.day, 9, 30,
                          tzinfo=ET).timestamp()
            sym_rows.append({"t": ts, "o": c, "h": c + 0.5,
                             "l": c - 0.5, "c": c, "v": 1000.0})
        rows[sym] = sym_rows
    return rows


class Drive:
    """Day-by-day driver mirroring the desk: bars served are the
    completed sessions before the evaluation session; emitted
    intents fill during the evaluation session (qty applied after
    the call) unless apply_fills is False."""

    def __init__(self, rows, equity=10000.0):
        self.rows = rows
        self.equity = equity
        self.qty = {}
        self.state = {}
        self.log = []          # (session_iso, intent)
        self.apply_fills = True

    def call(self, session_date):
        from core.sleeve import Context
        from sleeves.coffin_rebuilt import CoffinRebuiltSleeve
        idx = IDX[session_date]
        bars = {sym: self.rows[sym][:idx] for sym in SYMBOLS}
        ctx = Context(
            now=datetime(session_date.year, session_date.month,
                         session_date.day, 10, 0,
                         tzinfo=ET).timestamp(),
            session=session_date.isoformat(), equity=self.equity,
            extra={"coffin_state": self.state})
        sleeve = CoffinRebuiltSleeve()
        intents = sleeve.signal(bars, dict(self.qty), ctx) or []
        self.state = sleeve.coffin_state
        self.last_ev = sleeve.last_evaluation
        for it in intents:
            self.log.append((session_date.isoformat(), it))
            if self.apply_fills:
                if it.kind == "enter":
                    self.qty[it.symbol] = float(it.qty)
                elif it.kind == "exit":
                    self.qty.pop(it.symbol, None)
        return intents

    def run(self, first_idx, last_idx):
        for i in range(first_idx, last_idx + 1):
            self.call(SESSIONS[i])

    def enters(self):
        return [(s, it) for s, it in self.log if it.kind == "enter"]

    def exits(self):
        return [(s, it) for s, it in self.log if it.kind == "exit"]


def drive_to_entry(plan):
    """Run from a cold start (idx 10) through the entry fill and
    its adoption (idx 151, 2026-08-04)."""
    dv = Drive(make_rows(plan))
    dv.run(10, 151)
    return dv


class TestEntryGate(unittest.TestCase):
    def test_gate_blocks_june_then_entry_fires_july(self):
        dv = drive_to_entry(plan_a)
        enters = dv.enters()
        self.assertEqual(len(enters), 1)
        sess, it = enters[0]
        self.assertEqual(sess, "2026-08-03")
        self.assertEqual(it.symbol, "XLE")
        self.assertEqual(it.signal_date, "2026-07-31")
        self.assertEqual(it.qty, 151)
        self.assertEqual(it.side, "buy")
        self.assertEqual(it.position_intent, "buy_to_open")
        # adopted on the fill session's close processing
        st = dv.state
        self.assertEqual(st["mode"], "holding")
        self.assertEqual(st["held"], "XLE")
        self.assertEqual(st["entry_month_low"], 64.35)
        self.assertEqual(st["entry_fill_session"], "2026-08-03")
        self.assertEqual(st["peak_close"], 66.0)

    def test_no_double_entry_and_quiet_hold(self):
        dv = drive_to_entry(plan_a)
        dv.run(152, IDX[date(2026, 10, 30)])
        self.assertEqual(len(dv.enters()), 1)
        self.assertEqual(len(dv.exits()), 0)
        self.assertEqual(dv.state["mode"], "holding")

    def test_rank_block_distw_third(self):
        def plan_b(sym, i, d):
            if sym in ("XLK", "XLF"):
                return 200.0 if 60 <= i <= 80 else 100.0
            return plan_a(sym, i, d)
        dv = Drive(make_rows(plan_b))
        # Through the Sep 1 call (Aug 31 processed): XLE is distW
        # rank 3 at both the July and August month-ends and stays
        # flat. (The drive stops there on purpose: by Sep 30 the
        # trailing window's start sits inside the spike, which
        # poisons XLK's rW as well and makes XLK a genuine
        # frozen-rule entry — correct behavior, a different test.)
        dv.run(10, IDX[date(2026, 9, 1)])
        self.assertEqual(dv.enters(), [])


class TestExits(unittest.TestCase):
    def test_invalidation_daily(self):
        drop = IDX[date(2026, 9, 10)]

        def plan_c(sym, i, d):
            if sym == "XLE" and i >= drop:
                return 60.0
            return plan_a(sym, i, d)
        dv = drive_to_entry(plan_c)
        dv.run(152, IDX[date(2026, 9, 14)])
        exits = dv.exits()
        self.assertEqual(len(exits), 1)
        sess, it = exits[0]
        self.assertEqual(sess, "2026-09-11")
        self.assertEqual(it.signal_date, "2026-09-10")
        self.assertIn("invalidation", it.reason)
        self.assertEqual(it.qty, 151.0)
        dv.run(IDX[date(2026, 9, 15)], IDX[date(2026, 9, 16)])
        self.assertEqual(dv.state["mode"], "flat")
        self.assertEqual(len(dv.exits()), 1)

    def test_trail15_month_end_only_g1(self):
        oct15 = IDX[date(2026, 10, 15)]
        fill = IDX[date(2026, 8, 3)]

        def plan_d(sym, i, d):
            if sym != "XLE":
                return plan_a(sym, i, d)
            if i <= IDX[date(2026, 7, 31)]:
                return plan_a(sym, i, d)
            if i <= oct15:
                return 66.0 + 24.0 * (i - fill) / (oct15 - fill)
            if d <= date(2026, 11, 12):
                return 90.0
            if d <= date(2026, 11, 17):
                return 74.0        # intra-month breach of 0.85*90
            if d <= date(2026, 11, 30):
                return 85.0        # recovered by month-end: no exit
            return 74.0            # December: breach holds to month-end
        dv = drive_to_entry(plan_d)
        dv.run(152, IDX[date(2026, 12, 31)])
        self.assertEqual(dv.exits(), [])
        nxt = SESSIONS[IDX[date(2026, 12, 31)] + 1]
        dv.call(nxt)
        exits = dv.exits()
        self.assertEqual(len(exits), 1)
        sess, it = exits[0]
        self.assertEqual(sess, nxt.isoformat())
        self.assertEqual(it.signal_date, "2026-12-31")
        self.assertIn("trail15", it.reason)

    def test_cap_18_months(self):
        def plan_e(sym, i, d):
            if sym == "XLE" and i > IDX[date(2026, 7, 31)]:
                return 67.0
            return plan_a(sym, i, d)
        dv = drive_to_entry(plan_e)
        # monthly calls on the 3rd: each processes the sessions
        # since the last call, month-ends included
        probe = date(2026, 9, 3)
        exit_seen = None
        while probe <= date(2028, 2, 3):
            if probe in IDX:
                dv.call(probe)
                if dv.exits():
                    exit_seen = probe
                    break
            probe = date(probe.year + (1 if probe.month == 12 else 0),
                         1 if probe.month == 12 else probe.month + 1, 3)
        self.assertIsNotNone(exit_seen)
        sess, it = dv.exits()[0]
        self.assertIn("18_months", it.reason)
        # the cap fires at the Jan-2028 month-end: 18 months after
        # the Jul-2026 entry-signal month, not at Dec-2027 (17)
        self.assertEqual(it.signal_date[:7], "2028-01")
        self.assertEqual(len(dv.exits()), 1)


class TestFillAdoption(unittest.TestCase):
    def test_unconfirmed_exit_reemitted_once_per_session(self):
        drop = IDX[date(2026, 9, 10)]

        def plan_c(sym, i, d):
            if sym == "XLE" and i >= drop:
                return 60.0
            return plan_a(sym, i, d)
        dv = drive_to_entry(plan_c)
        dv.apply_fills = False          # fills stop landing NOW,
        dv.run(152, IDX[date(2026, 9, 11)])   # before the exit emits
        self.assertEqual(len(dv.exits()), 1)
        dv.call(date(2026, 9, 14))
        # The Sep 14 call processes the Sep 11 fill session: the
        # fill check finds the position still present and names it
        # (exit_unconfirmed_reemit), and because the emitted fill
        # session has completed with the position still held, the
        # exit re-emits once, sized to the remaining position.
        exits = dv.exits()
        self.assertEqual(len(exits), 2)
        self.assertIn("re-emitted", exits[1][1].reason)
        self.assertIn("exit_unconfirmed_reemit",
                      " ".join(dv.state["defects"]))
        again = dv.call(date(2026, 9, 14))    # same session: no dup
        self.assertEqual([i for i in again if i.kind == "exit"], [])
        dv.qty.pop("XLE", None)               # now the fill lands
        dv.call(date(2026, 9, 15))
        self.assertEqual(dv.state["mode"], "flat")
        self.assertEqual(len(dv.exits()), 2)


class TestStreamingMonthEnd(unittest.TestCase):
    def test_forming_bar_never_reaches_a_decision(self):
        from sleeves.coffin_rebuilt import clean_daily_bars
        rows = []
        base = date(2026, 11, 2)
        for k in range(5):
            d = base + timedelta(days=k)
            ts = datetime(d.year, d.month, d.day, 9, 30,
                          tzinfo=ET).timestamp()
            rows.append({"t": ts, "o": 10.0, "h": 10.5, "l": 9.5,
                         "c": 10.0, "v": 1.0})
        cleaned = clean_daily_bars(rows, "2026-11-05")
        self.assertEqual([b["date"] for b in cleaned],
                         ["2026-11-02", "2026-11-03", "2026-11-04"])

    def test_latest_session_is_not_a_month_end_mid_month(self):
        from sleeves.coffin_rebuilt import month_end_set
        cal = ["2026-11-02", "2026-11-03", "2026-11-04"]
        self.assertEqual(month_end_set(cal, "2026-11-05"), set())
        cal2 = ["2026-10-29", "2026-10-30", "2026-11-02"]
        self.assertEqual(month_end_set(cal2, "2026-11-03"),
                         {"2026-10-30"})


class TestLiveChainSmoke(unittest.TestCase):
    def test_adapters3_evaluate_flat_market(self):
        """The full live chain (snapshot view -> SnapshotSleeveContext
        -> v2 adapter -> strategy) loads and evaluates without error
        on a flat market: no intents, and the sleeve's state file is
        written beside its journal with the machine flat."""
        import tempfile
        entry = importlib.import_module("adapters3.coffin_rebuilt")
        sessions = business_sessions(date(2026, 1, 5), date(2026, 11, 6))
        bars = {}
        for sym in SYMBOLS:
            bars["%s|1Day" % sym] = [
                {"t": d.isoformat(), "o": 100.0, "h": 100.5,
                 "l": 99.5, "c": 100.0, "v": 1000.0} for d in sessions]
        view = {"now": "2026-11-09T10:00:00-05:00", "bars": bars,
                "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}, "extra": {}}
        with tempfile.TemporaryDirectory() as td:
            out = entry.evaluate(view, {"state_dir": td})
            self.assertEqual(out, [])
            spath = os.path.join(td, "coffin_state.json")
            self.assertTrue(os.path.exists(spath))
            saved = json.load(open(spath))
            self.assertEqual(saved["coffin_state"]["mode"], "flat")
            self.assertEqual(saved["coffin_state"]["last_processed"],
                             "2026-11-06")


class TestRosterAndShape(unittest.TestCase):
    def test_roster_row(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        rows = [r for r in cfg["sleeves"] if r["id"] == "coffin_rebuilt"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["module"], "adapters3.coffin_rebuilt")
        self.assertEqual(row["slice"]["capital_usd"], 10000.0)
        self.assertEqual(row["inputs"], ["bars", "positions"])
        self.assertFalse(row["parked"])
        self.assertFalse(row["flat_by_close"])

    def test_module_shapes(self):
        strat = importlib.import_module("sleeves.coffin_rebuilt")
        self.assertEqual(strat.CONFIG.sleeve_id, "coffin_rebuilt")
        entry = importlib.import_module("adapters3.coffin_rebuilt")
        self.assertEqual(entry.SLEEVE_ID, "coffin_rebuilt")
        self.assertEqual(entry.INPUTS, ["bars", "positions"])
        self.assertTrue(callable(entry.evaluate))
        adapter = importlib.import_module("adapters.coffin_rebuilt")
        self.assertTrue(callable(adapter.evaluate))


if __name__ == "__main__":
    unittest.main()
