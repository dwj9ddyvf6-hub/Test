"""GAMMA-WINDOW-20261116 regression blockers (Lane E, desk full
audit 2026-11-16).

Defect, two halves:
(a) aster_open_gamma_a/b can never evaluate inside their
    09:35-09:45 ET entry window: the live path consumes no
    per-sleeve cadence (the desk cycle is 691-1671s + 60s, phase
    unanchored) while the strategy's break-freshness gate
    (desk3/aster_batch1.py, 5s) assumes a seconds-cadence
    in-window consumer.
(b) The opening-events assembler built its first-5-minute state
    only from warm 1Min slices, and warm served 1Min only for
    SPY/QQQ (plus the Focus 29 names), so for UNIVERSE15 carriers
    such as XLE/XLF/XLU the drop was necessarily empty; the drop
    carried no coverage field to distinguish "no break" from
    "never assembled", and there was no end-of-loop rewrite.

Cure: warm serves 1Min for the full UNIVERSE15; the assembler
records coverage (candidates / assembled / missing_1min) on
every write and always rewrites the drop at end-of-loop;
OpeningEventsProducer names a candidates>0 / assembled=0 drop
as a producer error instead of silently serving an empty list;
and the pair gets a detached in-window scan loop
(desk3/opening_gamma_scan.py, roster WINDOW_SIDS, launched by
OpeningGammaWarmer in the QullaScanWarmer shape) polling at
<=5s through the window.

Fail direction: pre-cure there is no desk3.opening_gamma_scan,
no OpeningGammaWarmer, no coverage in the assembler, and warm
serves no 1Min for XLF/XLU/IWM/... so every test below fails.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ET = ZoneInfo("America/New_York")
PROG = os.path.expanduser(
    "~/workspace/research_notes/sleeve-activation-calibration-20261111")
SESSION = "2026-11-16"          # a Monday
PREV = "2026-11-13"             # the prior Friday


def _boe():
    spec = importlib.util.spec_from_file_location(
        "boe_gamma", os.path.join(PROG, "build_opening_events.py"))
    boe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boe)
    return boe


def _r5doc(events):
    return {"session": PREV,
            "generated_at": "2026-11-13T21:23:00+00:00",
            "events": {s: {"is_event": True, "last2h": 0.01,
                           "p80": 0.005} for s in events}}


def _bar_et(hh, mm, o, h, l, c):
    dt = datetime(2026, 11, 16, hh, mm, tzinfo=ET)
    return {"t": dt.astimezone(timezone.utc).isoformat(),
            "o": o, "h": h, "l": l, "c": c, "v": 1000}


def _first5_bars(break_low=None):
    """09:30-09:34 ET bars: negative first-5 return, low 99.0;
    optionally one in-window bar breaking below that low."""
    bars = [_bar_et(9, 30, 100.0, 100.2, 99.6, 99.8),
            _bar_et(9, 31, 99.8, 99.9, 99.4, 99.5),
            _bar_et(9, 32, 99.5, 99.6, 99.2, 99.3),
            _bar_et(9, 33, 99.3, 99.4, 99.1, 99.2),
            _bar_et(9, 34, 99.2, 99.3, 99.0, 99.1)]
    if break_low is not None:
        bars.append(_bar_et(9, 37, 99.0, 99.0, break_low, 98.6))
    return bars


class TestWarmUniverse15OneMin(unittest.TestCase):
    def test_warm_serves_1min_for_full_universe15(self):
        from desk3.aster_batch1 import UNIVERSE15
        from desk3.warm import INTRADAY_FETCHES
        have = {s for s, tf, _d in INTRADAY_FETCHES if tf == "1Min"}
        for sym in UNIVERSE15:
            self.assertIn(sym, have, sym)


class TestAssemblerCoverage(unittest.TestCase):
    def test_assemble_state_names_assembled_and_missing(self):
        boe = _boe()
        state, cov = boe.assemble_state(
            {"XLE": {"is_event": True}, "XLF": {"is_event": True}},
            {"XLE|1Min": _first5_bars()}, SESSION)
        self.assertIn("XLE", state)
        self.assertEqual(cov["candidates"], ["XLE", "XLF"])
        self.assertEqual(cov["assembled"], ["XLE"])
        self.assertEqual(cov["missing_1min"], ["XLF"])
        self.assertTrue(cov["assembled_at"])

    def test_replay_xle_break_produces_event_and_coverage(self):
        boe = _boe()
        td = tempfile.mkdtemp()
        boe.REPLAY_DROP = os.path.join(td, "replay.json")
        rows = boe.replay(SESSION, r5doc=_r5doc(["XLE"]),
                          bars={"XLE|1Min": _first5_bars(98.5)})
        self.assertEqual([r["symbol"] for r in rows], ["XLE"])
        doc = json.load(open(boe.REPLAY_DROP))
        self.assertEqual(doc["coverage"]["candidates"], ["XLE"])
        self.assertEqual(doc["coverage"]["assembled"], ["XLE"])
        self.assertEqual(doc["coverage"]["missing_1min"], [])

    def test_replay_no_break_is_assembled_but_empty(self):
        boe = _boe()
        td = tempfile.mkdtemp()
        boe.REPLAY_DROP = os.path.join(td, "replay.json")
        rows = boe.replay(SESSION, r5doc=_r5doc(["XLE"]),
                          bars={"XLE|1Min": _first5_bars()})
        self.assertEqual(rows, [])
        doc = json.load(open(boe.REPLAY_DROP))
        # proven true-empty: assembled, not missing
        self.assertEqual(doc["coverage"]["assembled"], ["XLE"])
        self.assertEqual(doc["coverage"]["missing_1min"], [])
        self.assertEqual(doc["events"], [])

    def test_replay_missing_1min_is_named_not_silent_empty(self):
        boe = _boe()
        td = tempfile.mkdtemp()
        boe.REPLAY_DROP = os.path.join(td, "replay.json")
        rows = boe.replay(SESSION, r5doc=_r5doc(["XLF"]), bars={})
        self.assertEqual(rows, [])
        doc = json.load(open(boe.REPLAY_DROP))
        self.assertEqual(doc["coverage"]["assembled"], [])
        self.assertEqual(doc["coverage"]["missing_1min"], ["XLF"])

    def test_live_loop_final_rewrite_carries_event_and_coverage(self):
        boe = _boe()
        td = tempfile.mkdtemp()
        os.makedirs(os.path.join(td, "ingest"))
        r5p = os.path.join(td, "ingest", "r5.json")
        warmp = os.path.join(td, "warm.json")
        dropp = os.path.join(td, "ingest", "opening.json")
        with open(r5p, "w") as fh:
            json.dump(_r5doc(["XLE"]), fh)
        with open(warmp, "w") as fh:
            json.dump({"bars": {"XLE|1Min": _first5_bars()}}, fh)
        boe.R5_DROP, boe.WARM, boe.LIVE_DROP = r5p, warmp, dropp
        clock = {"now": datetime(2026, 11, 16, 9, 35, tzinfo=ET)}
        seen = {}

        def fetch(syms):
            # record the drop as the loop first wrote it (initial)
            if "initial" not in seen:
                seen["initial"] = json.load(open(dropp))
            clock["now"] = datetime(2026, 11, 16, 9, 46, tzinfo=ET)
            return {"trades": {"XLE": {
                "p": 98.5,
                "t": datetime(2026, 11, 16, 9, 37,
                              tzinfo=ET).astimezone(
                                  timezone.utc).isoformat()}}}

        boe.live(now_fn=lambda: clock["now"], fetch_trades=fetch,
                 sleep_fn=lambda s: None)
        final = json.load(open(dropp))
        self.assertEqual(seen["initial"]["events"], [])
        self.assertEqual([r["symbol"] for r in final["events"]],
                         ["XLE"])
        self.assertEqual(final["coverage"]["assembled"], ["XLE"])
        self.assertEqual(final["coverage"]["phase"], "final")


class TestProducerCoverageGap(unittest.TestCase):
    def _root(self, doc):
        td = tempfile.mkdtemp()
        os.makedirs(os.path.join(td, "state", "ingest"))
        with open(os.path.join(td, "state", "ingest",
                               "opening_events.json"), "w") as fh:
            json.dump(doc, fh)
        return td

    def test_candidates_with_zero_assembled_is_named_error(self):
        from desk3.producers3 import OpeningEventsProducer
        now = datetime(2026, 11, 16, 14, 40, tzinfo=timezone.utc)
        doc = {"generated_at": now.isoformat(), "session": SESSION,
               "events": [],
               "coverage": {"candidates": ["XLF"],
                            "assembled": [],
                            "missing_1min": ["XLF"],
                            "assembled_at": now.isoformat()}}
        prod = OpeningEventsProducer(self._root(doc))
        self.assertEqual(prod({"now": now}), {})
        self.assertIn("XLF", prod.last_error or "")


# ------------------------------------------------------------- scan loop
def _gamma_row(boe):
    open_dt = datetime(2026, 11, 16, 9, 30, tzinfo=ET)
    sig = datetime(2026, 11, 13, 16, 25, tzinfo=ET)
    return boe.make_row(
        "XLE", SESSION, PREV, {"last2h": 0.01, "p80": 0.005},
        99.0, -0.009, 98.5,
        open_dt + timedelta(minutes=7),
        open_dt + timedelta(minutes=7, seconds=1),
        open_dt + timedelta(minutes=5, seconds=30),
        open_dt, sig, sig + timedelta(seconds=5))


def _gamma_view(now, rows):
    return {"now": now.isoformat(),
            "calendar": {"session": SESSION, "previous_session": PREV,
                         "open": datetime(2026, 11, 16, 9, 30,
                                          tzinfo=ET).isoformat(),
                         "verified": True},
            "opening_events": rows,
            "options": [
                {"symbol": "XLE261117P00098500", "underlying": "XLE",
                 "right": "put", "expiry": "2026-11-17",
                 "strike": 98.5, "delta": -0.55, "bid": 0.8,
                 "ask": 0.9, "bid_size": 50, "ask_size": 50},
                {"symbol": "XLE261125P00098500", "underlying": "XLE",
                 "right": "put", "expiry": "2026-11-25",
                 "strike": 98.5, "delta": -0.55, "bid": 0.3,
                 "ask": 0.4, "bid_size": 50, "ask_size": 50}],
            "quotes": {"XLE": {"bid": 98.4, "ask": 98.5}},
            "positions": [], "slice": {"capital_usd": 10000.0},
            "market_open": True}


class _Clock:
    def __init__(self, start):
        self.now = start

    def __call__(self):
        return self.now

    def sleep(self, s):
        self.now += timedelta(seconds=s)


class TestWindowScan(unittest.TestCase):
    def test_roster_is_exactly_the_pair(self):
        from desk3.opening_gamma_scan import WINDOW_SIDS
        self.assertEqual(set(WINDOW_SIDS),
                         {"aster_open_gamma_a", "aster_open_gamma_b"})

    def test_scan_evaluates_and_dispatches_inside_window(self):
        from desk3.opening_gamma_scan import run_window_scan
        boe = _boe()
        row = _gamma_row(boe)
        clock = _Clock(datetime(2026, 11, 16, 9, 36, 55, tzinfo=ET))
        break_rx = datetime(2026, 11, 16, 9, 37, 1, tzinfo=ET)
        dispatched = []

        def dispatch(intent, sid):
            dispatched.append((sid, intent, clock.now))
            return {"status": "submitted",
                    "intent_id": intent.get("intent_id")}

        td = tempfile.mkdtemp()
        journal = os.path.join(td, "gamma_window.jsonl")
        summary = run_window_scan(
            td, now_fn=clock, sleep_fn=clock.sleep,
            events_fn=lambda now: [row] if now >= break_rx else [],
            view_fn=_gamma_view, dispatch_fn=dispatch,
            journal_path=journal, poll_s=2.0)
        sids = {sid for sid, _i, _t in dispatched}
        self.assertEqual(sids, {"aster_open_gamma_a",
                                "aster_open_gamma_b"})
        bm = datetime(2026, 11, 16, 9, 37, tzinfo=ET)
        for _sid, _intent, at in dispatched:
            self.assertLessEqual((at - bm).total_seconds(), 5.0)
            self.assertTrue((9, 35) <= (at.hour, at.minute) < (9, 45))
        self.assertGreaterEqual(summary["evaluations"], 2)
        rows = [json.loads(l) for l in open(journal)]
        evals = [r for r in rows if r.get("event") == "gamma_window_eval"
                 and r.get("intents")]
        self.assertEqual({r["sleeve"] for r in evals},
                         {"aster_open_gamma_a", "aster_open_gamma_b"})

    def test_scan_abstention_is_journaled_with_reason(self):
        from desk3.opening_gamma_scan import run_window_scan
        boe = _boe()
        row = _gamma_row(boe)
        clock = _Clock(datetime(2026, 11, 16, 9, 36, 59, tzinfo=ET))
        td = tempfile.mkdtemp()
        journal = os.path.join(td, "gamma_window.jsonl")

        def bare_view(now, rows):
            v = _gamma_view(now, rows)
            v["options"] = []  # event seen, no chain: no intent
            return v

        run_window_scan(
            td, now_fn=clock, sleep_fn=clock.sleep,
            events_fn=lambda now: [row], view_fn=bare_view,
            dispatch_fn=lambda i, s: {"status": "submitted"},
            journal_path=journal, poll_s=2.0)
        rows = [json.loads(l) for l in open(journal)]
        abst = [r for r in rows
                if r.get("event") == "gamma_window_abstain"]
        self.assertTrue(abst)
        self.assertTrue(all(r.get("reason") for r in abst))

    def test_switch_off_restores_no_scan(self):
        from desk3.opening_gamma_scan import run_window_scan
        clock = _Clock(datetime(2026, 11, 16, 9, 37, tzinfo=ET))
        called = []
        summary = run_window_scan(
            tempfile.mkdtemp(), now_fn=clock, sleep_fn=clock.sleep,
            events_fn=lambda now: called.append(now) or [],
            view_fn=_gamma_view,
            dispatch_fn=lambda i, s: {"status": "submitted"},
            enabled=False)
        self.assertEqual(called, [])
        self.assertEqual(summary["evaluations"], 0)


class TestOpeningGammaWarmer(unittest.TestCase):
    def test_launches_once_in_pre_window_band_only(self):
        from desk3.producers_g4 import OpeningGammaWarmer
        td = tempfile.mkdtemp()
        launches = []
        w = OpeningGammaWarmer(
            td, launcher=lambda root: launches.append(root) or 4321)
        at = lambda hh, mm: {"now": datetime(2026, 11, 16, hh, mm,
                                             tzinfo=ET)}
        self.assertEqual(w(at(9, 32)), {})
        self.assertEqual(len(launches), 1)
        self.assertEqual(w(at(9, 33)), {})   # marker bounds relaunch
        self.assertEqual(len(launches), 1)
        w2 = OpeningGammaWarmer(tempfile.mkdtemp(),
                                launcher=lambda root:
                                launches.append(root) or 4321)
        self.assertEqual(w2(at(9, 50)), {})  # window already closed
        self.assertEqual(len(launches), 1)

    def test_switch_off_launches_nothing(self):
        from desk3.producers_g4 import OpeningGammaWarmer
        launches = []
        w = OpeningGammaWarmer(
            tempfile.mkdtemp(),
            launcher=lambda root: launches.append(root) or 4321)
        w({"now": datetime(2026, 11, 16, 9, 32, tzinfo=ET),
           "gamma_window_scan": False})
        self.assertEqual(launches, [])


if __name__ == "__main__":
    unittest.main()
