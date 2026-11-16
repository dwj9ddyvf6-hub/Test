"""CR6-SHEN blockers (2026-11-14): shen_fade producer half.

Pre-cure, the plan for session D was attempted at ~19:00 ET on
D-1: the bridge derives the v2 session from the UTC date of the
cycle instant, the strategy's plan gate is time-of-day only
(first tick >= 09:29:30), D had no bars yet, _build_plan
returned BLOCKED_DATA, and the persisted latch held the sleeve
at plan_blocked for the whole session — every session since
landing. The cure is the entrypoint session guard in
adapters3/shen_fade.py: an evaluation whose ET calendar date
precedes its session date does not delegate and files nothing.

The sequence test below reproduces the latch on the pre-cure
tree (evening drive files BLOCKED_DATA into the shared state
dir; the plan-tick drive then serves it back, plan_blocked)
and proves the cure on the cured tree (nothing filed in the
evening; the plan FILES at the true 09:29:30 tick). unittest
TestCase form, per the desk gate's discovery.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ET = ZoneInfo("America/New_York")


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _view(now_iso):
    # Thu 2026-11-12 full RTH + Fri 2026-11-13 premarket and
    # morning, 1Min bars, gentle range so PDH/PDL/PM levels exist
    bars = []
    px = 752.0
    t = datetime.combine(date(2026, 11, 12), dtime(9, 30), ET)
    while t.time() < dtime(16, 0):
        bars.append({"t": _iso(t), "o": px, "h": px + 0.4,
                     "l": px - 0.4, "c": px + 0.05, "v": 1000})
        px += 0.02
        t += timedelta(minutes=1)
    t = datetime.combine(date(2026, 11, 13), dtime(4, 0), ET)
    while t.time() < dtime(11, 0):
        bars.append({"t": _iso(t), "o": px, "h": px + 0.3,
                     "l": px - 0.3, "c": px, "v": 800})
        t += timedelta(minutes=1)
    return {"now": now_iso, "bars": {"SPY|1Min": bars},
            "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}}


def _filings(tmp):
    out = []
    jp = os.path.join(tmp, "journal.jsonl")
    if os.path.exists(jp):
        with open(jp) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("event") == "shen_state":
                    out.append(r["journal"])
    return out


def _stamp(tmp):
    stamp = None
    jp = os.path.join(tmp, "journal.jsonl")
    if os.path.exists(jp):
        with open(jp) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("event") == "last_evaluation":
                    stamp = r["stamp"]
    return stamp


class TestCR6Shen(unittest.TestCase):

    def test_evening_latch_cannot_set_and_plan_files_on_the_day(self):
        import importlib
        mod = importlib.import_module("adapters3.shen_fade")
        with tempfile.TemporaryDirectory() as tmp:
            # A: Thu 19:11 ET carrying session Fri (rollover window)
            out = mod.evaluate(
                _view("2026-11-13T00:11:34+00:00"),
                {"state_dir": tmp,
                 "now": "2026-11-13T00:11:34+00:00",
                 "cycle_id": "test-cr6-shen-a"})
            self.assertEqual(out, [])
            # pre-cure: a BLOCKED_DATA plan is filed here
            self.assertEqual(_filings(tmp), [])
            # B: Fri 09:29:35 ET, the true plan tick, same state dir
            out = mod.evaluate(
                _view("2026-11-13T14:29:35+00:00"),
                {"state_dir": tmp,
                 "now": "2026-11-13T14:29:35+00:00",
                 "cycle_id": "test-cr6-shen-b"})
            self.assertEqual(out, [])
            filings = _filings(tmp)
            self.assertTrue(filings,
                            "no shen_state filed at the plan tick")
            plan = filings[-1].get("plan") or {}
            # pre-cure: plan is the evening BLOCKED_DATA, plan_blocked
            self.assertEqual(plan.get("status"), "FILED")
            self.assertTrue(plan.get("levels"),
                            "filed plan carries levels")
            stamp = _stamp(tmp)
            self.assertIsNotNone(stamp)
            self.assertNotEqual(stamp.get("state"), "plan_blocked")

    def test_session_guard_predicate(self):
        from adapters3.shen_fade import _session_not_begun
        # evening before (ET date < UTC session date): guard
        self.assertTrue(
            _session_not_begun({"now": "2026-11-13T00:11:34+00:00"}, {}))
        self.assertTrue(
            _session_not_begun({"now": "2026-11-13T04:30:00+00:00"}, {}))
        # the session's own ET day: no guard, even before the open
        self.assertFalse(
            _session_not_begun({"now": "2026-11-13T05:00:00+00:00"}, {}))
        self.assertFalse(
            _session_not_begun({"now": "2026-11-13T14:29:35+00:00"}, {}))
        self.assertFalse(
            _session_not_begun({"now": "2026-11-13T21:00:00+00:00"}, {}))


if __name__ == "__main__":
    unittest.main()
