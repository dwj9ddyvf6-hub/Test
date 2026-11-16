"""CR-5 blockers (2026-11-14): raschke_rre warmup persistence.

Founding evidence: after 13 live sessions the sleeve's stamps sat at
core_features 0/27 and baseline_count 0/20 (FIRING-LINE-RESIDUE.md
CR-5). Mechanism proven on the live warm cache: the bar door serves
SPY 5Min extended hours (04:00-19:55, 192 bars/day), while the
strategy's frozen prior-session reference reads complete only when
the prior day's first bar is the 09:30 session open and its last bar
ends at the session close -- so the reference never read complete,
current-session feeding (gated on a complete reference) never ran,
and the warmup accumulator stayed at zero across every runner
restart. The cure shapes the door's bars to the sleeve's RTH session
in the adapter (desk_sleeves/raschke_rre.py) and loads the persisted
rre_journal at evaluate start there.

Fail direction: on the pre-cure tree the drive below stamps
blocked_warmup (prior_reference) with core_features 0/27 and
bars_fed 0; proven on a worktree at pre-cure HEAD.
"""
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")


def _day_bars(day, base=600.0, drift=0.05):
    """One full extended-hours day (04:00-19:55 ET, 5Min), shaped
    exactly like the live warm door's SPY 5Min series."""
    out, t, i = [], datetime(2026, 10, day, 4, 0, tzinfo=ET), 0
    end = datetime(2026, 10, day, 20, 0, tzinfo=ET)
    while t < end:
        c = base + drift * i
        out.append({"t": t.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
            "o": c, "h": c + 0.3, "l": c - 0.3, "c": c, "v": 10000})
        t += timedelta(minutes=5)
        i += 1
    return out


def _last_stamp(state_dir):
    stamp = None
    with open(os.path.join(state_dir, "journal.jsonl")) as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("event") == "last_evaluation":
                stamp = rec["stamp"]
    return stamp


class TestCr5WarmupPersistence(unittest.TestCase):
    def _drive(self):
        mod = importlib.import_module("desk_sleeves.raschke_rre")
        importlib.reload(mod)
        sd = tempfile.mkdtemp()
        bars = {"SPY|5Min": _day_bars(20) + _day_bars(21) + _day_bars(22)}
        ctx = {"cycle_id": "cr5-1", "sleeve_id": "raschke_rre",
               "state_dir": sd, "snapshot_hash": "cr5"}
        view = {"now": "2026-10-22T15:00:00-04:00", "bars": bars,
                "positions": [], "extra": {}}
        mod.evaluate(view, ctx)
        s1 = _last_stamp(sd)
        # simulated runner restart: fresh module state, same journal
        importlib.reload(mod)
        view2 = {"now": "2026-10-22T15:30:00-04:00", "bars": bars,
                 "positions": [], "extra": {}}
        mod.evaluate(view2, ctx)
        s2 = _last_stamp(sd)
        return s1, s2

    def test_prior_reference_completes_on_extended_hours_door(self):
        s1, _ = self._drive()
        self.assertTrue(s1["warmup"]["prior_reference"], s1["decision"])
        self.assertNotEqual(s1["state"], "blocked_warmup", s1["decision"])

    def test_core_features_accumulate_past_gate(self):
        s1, _ = self._drive()
        self.assertGreaterEqual(s1["warmup"]["core_features"], 27,
                                s1["decision"])

    def test_counters_survive_simulated_restart(self):
        s1, s2 = self._drive()
        c1 = s1["rre_journal"]["pass_counters"]["bars_fed"]
        c2 = s2["rre_journal"]["pass_counters"]["bars_fed"]
        self.assertGreater(c1, 0)
        self.assertGreater(c2, c1,
                           "accumulator reset on simulated restart")
        self.assertGreaterEqual(s2["warmup"]["core_features"],
                                s1["warmup"]["core_features"])

    def test_only_rth_bars_are_fed(self):
        # 2 prior RTH days (78 bars each, fed for the router build on
        # the first pass of a session only when their own reference
        # chain exists) + the current session's RTH bars up to 15:30
        # (72). Extended-hours bars must never reach the accumulator:
        # bars_fed stays far below the 192/day door count.
        _, s2 = self._drive()
        fed = s2["rre_journal"]["pass_counters"]["bars_fed"]
        self.assertLessEqual(fed, 78 + 72)


if __name__ == "__main__":
    unittest.main()
