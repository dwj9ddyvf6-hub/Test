"""FEED80-OPENING-20261114 regression blockers.

Defect: aster_open_gamma_a/b consume opening_events rows with a
full causal clock chain, but no producer served the key: the R5
definition was believed lost with the relocated archive, and the
desk's quote feed was delayed SIP (SIP itself 403s on this tier).

Cure: the R5 rule was recovered from the estate (the research
script run_r5_overnight_gap_long.py on this box + the archive
sleeve spec in quant-research-backup) and is computed nightly by
build_r5_events.py; the morning assembler
(build_opening_events.py) emits rows from the desk's 1Min bars
and the IEX latest-trade route (probed SERVED 2026-11-14);
desk3.producers3.OpeningEventsProducer serves the drop with
strict chain validation.

Fail-first: pre-cure, OpeningEventsProducer did not exist
(ImportError) and no drop was served. The fixture row below is
built by the assembler's own make_row over recorded values, so
the contract pinned here is the assembler's real output shape.
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
NOW = datetime(2026, 11, 16, 14, 36, tzinfo=timezone.utc)

PROG = os.path.expanduser(
    "~/workspace/research_notes/sleeve-activation-calibration-20261111")


def _fixture_row():
    spec = importlib.util.spec_from_file_location(
        "boe", os.path.join(PROG, "build_opening_events.py"))
    boe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boe)
    open_dt = datetime(2026, 11, 16, 9, 30, tzinfo=ET)
    sig = datetime(2026, 11, 13, 16, 25, tzinfo=ET)
    return boe.make_row(
        "SPY", "2026-11-16", "2026-11-13",
        {"last2h": 0.004, "p80": 0.003}, 730.0, -0.0012, 729.5,
        open_dt + timedelta(minutes=7),
        open_dt + timedelta(minutes=7, seconds=1),
        open_dt + timedelta(minutes=5, seconds=30),
        open_dt, sig, sig + timedelta(seconds=5))


def _root(doc):
    td = tempfile.mkdtemp()
    os.makedirs(os.path.join(td, "state", "ingest"))
    if doc is not None:
        with open(os.path.join(td, "state", "ingest",
                               "opening_events.json"), "w") as fh:
            json.dump(doc, fh)
    return td


def _doc(rows):
    return {"generated_at": NOW.isoformat(),
            "source": "desk-opening-assembler-v1 (R5 pass + desk "
                      "1Min bars + IEX latest quotes)",
            "session": "2026-11-16", "events": rows}


class TestOpeningEventsProducer(unittest.TestCase):
    def test_serves_valid_row(self):
        from desk3.producers3 import OpeningEventsProducer
        out = OpeningEventsProducer(_root(_doc([_fixture_row()])))(
            {"now": NOW})
        rows = out.get("opening_events") or []
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "SPY")

    def test_broken_chain_rows_dropped(self):
        from desk3.producers3 import OpeningEventsProducer
        row = _fixture_row()
        bad1 = dict(row, causal_R5_prior_afternoon=False)
        bad2 = dict(row)
        del bad2["break_market_at"]
        bad3 = dict(row, first_5min_complete="yes")
        out = OpeningEventsProducer(
            _root(_doc([bad1, bad2, bad3])))({"now": NOW})
        self.assertEqual(out.get("opening_events"), [])

    def test_missing_drop_fails_closed(self):
        from desk3.producers3 import OpeningEventsProducer
        out = OpeningEventsProducer(_root(None))({"now": NOW})
        self.assertEqual(out, {})

    def test_registered_in_batch3(self):
        from desk3.producers3 import (BATCH3_PRODUCERS,
                                      OpeningEventsProducer)
        rows = {r[0]: r for r in BATCH3_PRODUCERS}
        self.assertIn("opening_events", rows)
        self.assertIs(rows["opening_events"][1], OpeningEventsProducer)


class TestR5Rule(unittest.TestCase):
    def test_r5_pass_rule_constants(self):
        spec = importlib.util.spec_from_file_location(
            "br5", os.path.join(PROG, "build_r5_events.py"))
        br5 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(br5)
        # recovered constants: run_r5_overnight_gap_long TRAIL /
        # MIN_OBS and the archive spec's top-quintile 0.80
        self.assertEqual((br5.TRAIL, br5.MIN_OBS, br5.PCT),
                         (252, 126, 0.80))

    def test_last2h_matches_recovered_definition(self):
        spec = importlib.util.spec_from_file_location(
            "br5b", os.path.join(PROG, "build_r5_events.py"))
        br5 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(br5)
        # 130 sessions of flat 30m bars; the last session's final
        # two hours rise 2% (13:30 bar close 100 -> 15:30 bar close
        # 102). Stamps are built in ET and converted to UTC so the
        # builder's ET keying is exercised honestly across DST.
        import datetime as _dt
        rows = []
        day = _dt.date(2026, 1, 5)
        made = 0
        while made < 130:
            if day.weekday() < 5:
                last = made == 129
                for hm, c in (("13:30", 100.0),
                              ("15:30", 102.0 if last else 100.0)):
                    et_dt = _dt.datetime.combine(
                        day, _dt.time.fromisoformat(hm)).replace(
                        tzinfo=ET)
                    rows.append({
                        "t": et_dt.astimezone(
                            _dt.timezone.utc).isoformat(),
                        "o": c, "h": c, "l": c, "c": c, "v": 1})
                made += 1
            day += _dt.timedelta(days=1)
        session, ev = br5.compute_symbol(rows)
        self.assertIsNotNone(ev)
        self.assertAlmostEqual(ev["last2h"], 0.02, places=6)
        self.assertTrue(ev["is_event"])  # 2% beats a flat p80 of 0
        self.assertGreaterEqual(ev["obs"], 126)


if __name__ == "__main__":
    unittest.main()
