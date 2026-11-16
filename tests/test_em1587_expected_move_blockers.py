"""EXPECTED-MOVE-FILING-20261030 blockers (desk side).

Root cause (RESEARCH-R2 defect 3): em_1587 declared the bare
input "extra", which no live producer emits, so the sleeve was
UNFED forever; and the v3 port discarded the sleeve's
last_evaluation stamp, so no evaluation ever filed its
expected-move map into the permanent ledger the Expected Move
Map page reads. The filing lane went dark at the desk migration
(last filed session 2026-10-23).

Cure pinned here:
- em_1587's declared inputs (config row, port_batch2 INPUTS and
  adapters3 INPUTS, all three equal) are the real producer
  outputs it depends on: bars, positions, options, vix,
  bars:VIX:1Day. "extra" is declared nowhere for this sleeve.
- adapters3.em_1587 translates the snapshot's literal VIX rows
  into the v2 adapter's extra["vix_series"] channel.
- adapters3.em_1587 files each distinct (session, map) into the
  permanent ledger at evaluation time, stamped filed_at_time,
  and never duplicates a filing.

On the pre-cure tree: the config row declared "extra" (test 1
fails), adapters3 had no INPUTS, no VIX translation and no
filing bridge (tests 2 and 3 fail: no ledger row is written).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

ET = ZoneInfo("America/New_York")
EXPECTED_INPUTS = ["bars", "positions", "options", "vix",
                   "bars:VIX:1Day"]


def _producer_outputs():
    from desk3.run_live import build_desk
    desk, _rows = build_desk(ROOT, dispatch=False, env={})
    outs = set()
    for spec in desk.registry.producers.values():
        outs.update(spec["outputs"])
    return outs


def _5m(day, hh, mm, n, px):
    t = datetime.combine(day, time(hh, mm), tzinfo=ET)
    out = []
    for _ in range(n):
        out.append({"t": t.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"), "o": px, "h": px, "l": px,
            "c": px, "v": 10000.0})
        t += timedelta(minutes=5)
    return out


def _daily(day, px):
    return [{"t": f"{day.isoformat()}T04:00:00Z", "o": px, "h": px,
             "l": px, "c": px, "v": 0.0}]


class TestEm1587FeedContract(unittest.TestCase):
    def test_inputs_agree_and_are_produced(self):
        cfg = json.load(open(os.path.join(ROOT, "config",
                                          "sleeves.json")))
        row = [r for r in cfg["sleeves"] if r["id"] == "em_1587"][0]
        self.assertEqual(row["inputs"], EXPECTED_INPUTS)
        self.assertNotIn("extra", row["inputs"])
        from desk3.port_batch2 import INPUTS
        self.assertEqual(list(INPUTS["em_1587"]), EXPECTED_INPUTS)
        mod = importlib.import_module("adapters3.em_1587")
        self.assertEqual(list(mod.INPUTS), EXPECTED_INPUTS)
        outs = _producer_outputs()
        for key in EXPECTED_INPUTS:
            self.assertIn(key, outs, f"em_1587 declares unproduced {key}")


class TestEm1587FilingBridge(unittest.TestCase):
    def _drive(self, mod, tmp):
        bars = {
            "SPY|5Min": _5m(date(2026, 10, 20), 9, 30, 78, 700.0)
            + _5m(date(2026, 10, 21), 9, 30, 7, 700.0),
            "QQQ|5Min": _5m(date(2026, 10, 20), 9, 30, 78, 600.0)
            + _5m(date(2026, 10, 21), 9, 30, 7, 600.0),
        }
        view = {
            "now": "2026-10-21T10:05:00-04:00",
            "bars": bars,
            "bars:VIX:1Day": (_daily(date(2026, 10, 19), 15.0)
                              + _daily(date(2026, 10, 20), 14.0)),
            "positions": [],
            "options": {},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {},
        }
        ctx = {"state_dir": tmp, "cycle_id": "cycle-test-1",
               "sleeve_id": "em_1587", "snapshot_hash": "testhash"}
        return mod.evaluate(view, ctx)

    def test_evaluation_files_map_once_with_vix_translation(self):
        mod = importlib.import_module("adapters3.em_1587")
        with tempfile.TemporaryDirectory() as tmp:
            ledger = os.path.join(tmp, "ledger.jsonl")
            old = mod.FILING_LOG_PATH
            mod.FILING_LOG_PATH = ledger
            try:
                out = self._drive(mod, tmp)
                self.assertEqual(out, [])
                self.assertTrue(os.path.exists(ledger),
                                "evaluation filed no ledger row")
                rows = [json.loads(x) for x in open(ledger)]
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row["session"], "2026-10-21")
                self.assertEqual(row["filing"], "filed_at_time")
                self.assertEqual(row["source_desk"], "muse-desk-v3")
                stamp = row["evaluations"]["em_1587"]["sleeve_stamp"]
                self.assertEqual(stamp["session"], "2026-10-21")
                m = stamp["map"]
                # The map exists only if the VIX series reached
                # the sleeve: VIX close 14.0 on 2026-10-20, SPY
                # prior close 700.0.
                self.assertEqual(m["vix_close"], 14.0)
                self.assertEqual(m["anchor_close"], 700.0)
                self.assertEqual(m["em"], 6.2)
                # Second identical evaluation: no duplicate filing.
                self._drive(mod, tmp)
                rows = [json.loads(x) for x in open(ledger)]
                self.assertEqual(len(rows), 1)
            finally:
                mod.FILING_LOG_PATH = old

    def test_fixture_drive_without_snapshot_files_nothing(self):
        # Regression for the leak caught the night of the cure:
        # desk test harnesses drive evaluate() with a fixture
        # ctx (no snapshot_hash); those evaluations must never
        # reach the permanent log.
        mod = importlib.import_module("adapters3.em_1587")
        with tempfile.TemporaryDirectory() as tmp:
            ledger = os.path.join(tmp, "ledger.jsonl")
            old = mod.FILING_LOG_PATH
            mod.FILING_LOG_PATH = ledger
            try:
                bars = {
                    "SPY|5Min": _5m(date(2026, 10, 20), 9, 30, 78,
                                    700.0)
                    + _5m(date(2026, 10, 21), 9, 30, 7, 700.0),
                    "QQQ|5Min": _5m(date(2026, 10, 20), 9, 30, 78,
                                    600.0)
                    + _5m(date(2026, 10, 21), 9, 30, 7, 600.0),
                }
                view = {
                    "now": "2026-10-21T10:05:00-04:00",
                    "bars": bars,
                    "bars:VIX:1Day": (_daily(date(2026, 10, 19), 15.0)
                                      + _daily(date(2026, 10, 20),
                                               14.0)),
                    "positions": [], "options": {},
                    "slice": {"capital_usd": 10000.0,
                              "cash_usd": 10000.0},
                    "params": {},
                }
                ctx = {"state_dir": tmp, "cycle_id": "fixture",
                       "sleeve_id": "em_1587"}
                self.assertEqual(mod.evaluate(view, ctx), [])
                self.assertFalse(os.path.exists(ledger),
                                 "fixture drive filed into the log")
            finally:
                mod.FILING_LOG_PATH = old


if __name__ == "__main__":
    unittest.main()
