"""READINESS-D2-20261112 blockers (ENTER-EXIT-CENSUS class D2).

Defect: the 52-week deadline exit — the ONLY exit for 19 Tensor
sleeves in aster_batch13 and aster_batch14 — computed position age
from sessions_held / age_sessions / held_sessions / weeks_held /
age_weeks. Real desk position rows carry none of those fields;
they carry opened_at (the dispatcher's fill stamp). Age therefore
read 0 forever and the deadline could never fire: a position in
these sleeves could be held past its 52 weeks indefinitely.

Cure: when no explicit counter is present, age in sessions is
derived from opened_at against the sleeve's own daily bars — the
count of distinct bar dates after the opened date (the house
pattern, cf. aster_batch1._held_bars and the ENH-B5 link deadline
in batch13 itself). Explicit counters keep precedence; the 260
session threshold is unchanged.

Fail direction: proven on a worktree at the pre-cure HEAD — a
position opened 300 bar-sessions ago produces NO exit intent in
either module.
"""
import os
import sys
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _bars(start, n, close=4.0):
    out, d, added = [], start, 0
    while added < n:
        if d.weekday() < 5:
            out.append({"t": d.isoformat(), "o": close, "h": close,
                        "l": close, "c": close, "v": 1000})
            added += 1
        d += timedelta(days=1)
    return out


def _view(pos, bars):
    return {"now": "2026-03-02T15:00:00",
            "positions": [pos],
            "bars": {"AAA|1Day": bars},
            "tensor": {}, "extra": {}}


OLD_POS = {"symbol": "AAA", "qty": 5, "avg_price": 4.0,
           "opened_at": "2025-01-06T15:00:00Z"}
YOUNG_POS = {"symbol": "AAA", "qty": 5, "avg_price": 4.0,
             "opened_at": "2026-02-16T15:00:00Z"}


class TestWeek52DeadlineFires(unittest.TestCase):
    def test_batch14_old_position_exits(self):
        from desk3 import aster_batch14
        bars = _bars(date(2025, 1, 7), 300)
        out = aster_batch14.evaluate(
            "aster_tensor_g4_cash_all_10", _view(OLD_POS, bars), {})
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertIn("week52_deadline", exits[0]["reason"])

    def test_batch14_young_position_holds(self):
        from desk3 import aster_batch14
        bars = _bars(date(2026, 2, 17), 10)
        out = aster_batch14.evaluate(
            "aster_tensor_g4_cash_all_10", _view(YOUNG_POS, bars), {})
        self.assertEqual([i for i in out if i["kind"] == "exit"], [])

    def test_batch13_old_position_exits(self):
        from desk3 import aster_batch13
        bars = _bars(date(2025, 1, 7), 300)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25", _view(OLD_POS, bars), {})
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertIn("week52_deadline", exits[0]["reason"])

    def test_batch13_young_position_holds(self):
        from desk3 import aster_batch13
        bars = _bars(date(2026, 2, 17), 10)
        out = aster_batch13.evaluate(
            "aster_tensor_c1_cash_all_25", _view(YOUNG_POS, bars), {})
        self.assertEqual([i for i in out if i["kind"] == "exit"], [])

    def test_explicit_counter_still_governs(self):
        from desk3 import aster_batch14
        pos = dict(YOUNG_POS, sessions_held=300)
        bars = _bars(date(2026, 2, 17), 10)
        out = aster_batch14.evaluate(
            "aster_tensor_g4_cash_all_10", _view(pos, bars), {})
        self.assertEqual(
            len([i for i in out if i["kind"] == "exit"]), 1, out)


if __name__ == "__main__":
    unittest.main()
