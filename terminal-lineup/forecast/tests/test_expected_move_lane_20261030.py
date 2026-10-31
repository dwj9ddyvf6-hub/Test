"""EXPECTED-MOVE-FILING-20261030 blockers (terminal side).

Root cause (RESEARCH-R2 defect 3): refresh_expected_move.py read
only the femto-lean ledger, frozen 2026-10-24 when its desk was
superseded; the v3 successor sleeve was UNFED and filed nothing;
and the refresher itself was not in the scheduled tools chain.
The page stayed honest but stale at session 2026-10-23, with
five sessions (2026-10-26 to 2026-10-30) missing.

Cure pinned here:
- refresh_tools.py runs refresh_expected_move.py in its
  producers group (the scheduled path the sibling lanes use).
- The refresh computes an expected-versus-filed session diff on
  every run and publishes it as data["filing_lane"], naming
  missing sessions in the coverage note automatically.
- A map rebuilt later from primary records enters only as a
  ledger row stamped filing="reconstructed" with its true
  computation time, and is published labelled reconstructed,
  never as filed at the time.
- The live data file holds a map for every expected session
  through the latest completed session (2026-10-30).

Fixture tests drive the real refresh build() against a temp
ledger and temp price records. On the pre-cure refresh they
fail: there was no filing_lane block, no reconstructed
provenance, and the coverage note was static text.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))
sys.path.insert(0, SITE)
sys.path.insert(0, os.path.expanduser("~/workspace/femto-lean"))

from core import em_1587 as em  # noqa: E402  the construction

SPEC = importlib.util.spec_from_file_location(
    "refresh_expected_move", os.path.join(SITE, "refresh_expected_move.py"))
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)


def _vix_doc(pairs):
    ts, closes = [], []
    for day, close in pairs:
        dt = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        ts.append(int(dt.timestamp()))
        closes.append(close)
    return {"chart": {"result": [{
        "timestamp": ts,
        "indicators": {"quote": [{"close": closes}]}}]}}


def _stamp(session, anchor_spy, anchor_qqq, vix_close):
    plan = em.build_map(anchor_spy, vix_close)
    return {
        "sleeve": "em_1587", "session": session,
        "map": {
            "anchor_close": plan["anchor_close"],
            "vix_close": plan["vix_close"],
            "pct": round(plan["pct"], 4),
            "em": plan["em"],
            "lines": plan["lines"],
            "regime": plan["regime"],
            "session_1r": plan["session_1r"],
            "funded_at_flat": round(plan["funded_at_flat"], 2),
            "weekly_em": plan["weekly_em"],
            "em_qqq": em.expected_move(anchor_qqq, vix_close),
            "oi": "unavailable",
        },
    }


def _row(session, epoch, stamp, filing=None):
    row = {"kind": "tick", "session": session, "now": epoch,
           "evaluations": {"em_1587": {
               "bars_served": {"SPY": 705, "QQQ": 705},
               "sleeve_stamp": stamp}}}
    if filing:
        row["filing"] = filing
    return row


EPOCH_1022 = datetime(2026, 10, 22, 14, 53,
                      tzinfo=timezone.utc).timestamp()
EPOCH_1023 = datetime(2026, 10, 23, 9, 8,
                      tzinfo=timezone.utc).timestamp()
EPOCH_RECON = datetime(2026, 10, 31, 2, 0,
                       tzinfo=timezone.utc).timestamp()


class FixtureLane(unittest.TestCase):
    """Sessions: 2026-10-22 filed at the time; the next weekday
    session depends on the variant. Price records cover priors
    2026-10-21 (for the 22nd) and 2026-10-22 (for the 23rd)."""

    def _build(self, rows):
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        ledger = os.path.join(root, "ledger.jsonl")
        with open(ledger, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        bars = {
            "SPY_daily": [{"t": "2026-10-21", "c": 760.0},
                          {"t": "2026-10-22", "c": 762.2}],
            "QQQ_daily": [{"t": "2026-10-21", "c": 725.2},
                          {"t": "2026-10-22", "c": 730.0}],
        }
        bars_p = os.path.join(root, "bars.json")
        json.dump(bars, open(bars_p, "w"))
        vix_p = os.path.join(root, "vix.json")
        json.dump(_vix_doc([("2026-10-21", 16.68),
                            ("2026-10-22", 19.03)]), open(vix_p, "w"))
        cache = {
            "SPY": [["2026-10-21", 0, 0, 0, 760.0, 0],
                    ["2026-10-22", 0, 0, 0, 762.2, 0]],
            "QQQ": [["2026-10-21", 0, 0, 0, 725.2, 0],
                    ["2026-10-22", 0, 0, 0, 730.0, 0]],
        }
        cache_p = os.path.join(root, "cache.json")
        json.dump(cache, open(cache_p, "w"))
        out_p = os.path.join(root, "expected-move", "data.json")
        saved = (REF.LOG_PATH, REF.BARS_PATH, REF.VIX_PATH,
                 REF.CACHE_PATH, REF.OUT_PATH)
        REF.LOG_PATH, REF.BARS_PATH, REF.VIX_PATH = ledger, bars_p, vix_p
        REF.CACHE_PATH, REF.OUT_PATH = cache_p, out_p
        try:
            rc = REF.build()
        finally:
            (REF.LOG_PATH, REF.BARS_PATH, REF.VIX_PATH,
             REF.CACHE_PATH, REF.OUT_PATH) = saved
        self.assertEqual(rc, 0)
        data = json.load(open(out_p))
        tmp.cleanup()
        return data

    def _filed_row(self):
        return _row("2026-10-22", EPOCH_1022,
                    _stamp("2026-10-22", 760.0, 725.2, 16.68))


class TestMissingSessionIsNamed(FixtureLane):
    def test_gap_named_in_lane_block_and_note(self):
        data = self._build([self._filed_row()])
        lane = data["filing_lane"]
        self.assertEqual(lane["filed_sessions"], ["2026-10-22"])
        self.assertEqual(lane["latest_completed_session"],
                         "2026-10-23")
        self.assertEqual(lane["missing_sessions"], ["2026-10-23"])
        self.assertEqual(lane["reconstructed_sessions"], [])
        self.assertIn("October 23, 2026", data["coverage_note"])
        self.assertIn("stay gaps", data["coverage_note"])
        self.assertEqual(data["session"], "2026-10-22")


class TestReconstructedSessionLabelled(FixtureLane):
    def test_reconstruction_published_with_label(self):
        recon = _row("2026-10-23", EPOCH_RECON,
                     _stamp("2026-10-23", 762.2, 730.0, 19.03),
                     filing="reconstructed")
        data = self._build([self._filed_row(), recon])
        lane = data["filing_lane"]
        self.assertEqual(lane["missing_sessions"], [])
        self.assertEqual(lane["reconstructed_sessions"],
                         ["2026-10-23"])
        self.assertEqual(data["session"], "2026-10-23")
        spy = [n for n in data["names"] if n["symbol"] == "SPY"][0]
        self.assertTrue(spy["reconstructed"])
        self.assertEqual(spy["receipt"]["filing"], "reconstructed")
        self.assertEqual(spy["receipt"]["computed_at_utc"],
                         "2026-10-31T02:00:00+00:00")
        self.assertIn("reconstructed", data["coverage_note"])
        self.assertIn("not filed at the time",
                      spy["receipt"]["source"])


class TestScheduledChainWiring(unittest.TestCase):
    def test_refresher_in_tools_chain(self):
        src = open(os.path.join(SITE, "refresh_tools.py")).read()
        self.assertIn('"refresh_expected_move.py"', src)


class TestLiveDataCurrent(unittest.TestCase):
    def test_live_lane_complete_through_latest_session(self):
        data = json.load(open(os.path.join(
            SITE, "expected-move", "data.json")))
        self.assertEqual(data["session"], "2026-10-30")
        lane = data["filing_lane"]
        self.assertEqual(lane["missing_sessions"], [])
        self.assertEqual(lane["latest_completed_session"],
                         "2026-10-30")
        self.assertEqual(
            lane["reconstructed_sessions"],
            ["2026-10-26", "2026-10-27", "2026-10-28",
             "2026-10-29", "2026-10-30"])
        spy = [n for n in data["names"] if n["symbol"] == "SPY"][0]
        self.assertEqual(spy["receipt"]["session"], "2026-10-30")
        self.assertTrue(spy["reconstructed"])


if __name__ == "__main__":
    unittest.main()
