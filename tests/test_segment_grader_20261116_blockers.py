"""SEGMENT-CONSTRUCTION-20261116 blockers (piece 3): CONV-80's
stage-1 SEGMENT_GRADE arm kind in desk3/conversion_shadow.py.

Pins:
- The arm is registered exactly as its Conversion Register row
  specifies (parents 1w/1wa/s_1wlab/s_rules_1w, segments
  OPEN_DRIVE/MIDDAY/CLOSE_HOUR/OVERNIGHT, grade at 20 forward
  sessions, falsifier and kill rule byte-identical to the
  register file).
- Held sessions derive FIFO from entry/exit fills (entry
  session through the session before the exit; same-session
  round trip counts its entry session).
- Segment pricing comes from the 1Min cache through the shared
  engine: a held session with a known midday move grades that
  move; the state is ACCRUING below 20 forward sessions,
  GRADED_POSITIVE at 20 when the MIDDAY mean is negative (the
  registered claim), GRADED_NEGATIVE when it is not.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
REGISTER = os.path.expanduser(
    "~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/"
    "CONVERSION-REGISTER-2026-11-15.jsonl")


def day_rows(date_iso, drive=0.10, mid=-0.10, close=0.0, base_px=100.0):
    y, mo, d = (int(x) for x in date_iso.split("-"))
    start = datetime.combine(datetime(y, mo, d).date(),
                             time(9, 30), ET).astimezone(
                                 timezone.utc)
    rows = []
    price = base_px
    for i in range(390):
        m = 570 + i
        o = price
        if m == 629:
            c = base_px * (1 + drive)
        elif m == 899:
            c = base_px * (1 + drive) * (1 + mid)
        elif m == 959:
            c = base_px * (1 + drive) * (1 + mid) * (1 + close)
        else:
            c = o
        rows.append({"t": (start + timedelta(minutes=i)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"), "o": o, "h": max(o, c),
            "l": min(o, c), "c": c, "v": 1000})
        if m == 629:
            price = base_px * (1 + drive)
        if m == 899:
            price = base_px * (1 + drive) * (1 + mid)
    return rows


def make_root(dates, mid=-0.10):
    root = tempfile.mkdtemp()
    bdir = os.path.join(root, "cache", "bars", "NVDA")
    os.makedirs(bdir)
    with open(os.path.join(bdir, "1Min.jsonl"), "w") as fh:
        for d in dates:
            for r in day_rows(d, mid=mid):
                fh.write(json.dumps(r) + "\n")
    with open(os.path.join(bdir, "1Day.jsonl"), "w") as fh:
        for d in dates:
            fh.write(json.dumps({"t": d + "T14:30:00Z", "o": 100,
                                 "h": 101, "l": 99, "c": 100,
                                 "v": 1000}) + "\n")
    return root


def entry(date, qty=10.0):
    return {"sleeve": "1w", "symbol": "NVDA", "price": 100.0,
            "qty": qty, "ts": date + "T15:00:00Z",
            "intent_id": f"e-{date}", "date_et": date,
            "date_utc": date, "dir": 1}


class ArmRegistrationTest(unittest.TestCase):
    def test_arm_registered_byte_identical(self):
        cfg = json.load(open(os.path.join(
            ROOT, "config", "conversion_shadow_20261115.json")))
        arms = [a for a in cfg["arms"] if a["conv"] == "CONV-80"]
        self.assertEqual(1, len(arms))
        arm = arms[0]
        self.assertEqual("SEGMENT_GRADE", arm["kind"])
        self.assertEqual(["1w", "1wa", "s_1wlab", "s_rules_1w"],
                         arm["parents"])
        self.assertEqual(20, arm["grade_n"])
        self.assertEqual(["OPEN_DRIVE", "MIDDAY", "CLOSE_HOUR",
                          "OVERNIGHT"], arm["segments"])
        reg = {}
        with open(REGISTER) as fh:
            for line in fh:
                r = json.loads(line)
                if r["id"] == "CONV-80":
                    reg = r
        self.assertEqual(reg["falsifier"], arm["falsifier"])
        self.assertEqual(reg["kill_rule"], arm["kill_rule"])


class HeldSessionsTest(unittest.TestCase):
    def test_fifo_held_window(self):
        from desk3.conversion_shadow import SeriesBook, held_sessions
        dates = ["2026-11-09", "2026-11-10", "2026-11-11",
                 "2026-11-12", "2026-11-13"]
        root = make_root(dates)
        book = SeriesBook(root)
        exits = [{"sleeve": "1w", "symbol": "NVDA", "price": 101.0,
                  "qty": 10.0, "ts": "2026-11-12T15:00:00Z",
                  "intent_id": "x-1", "date_et": "2026-11-12",
                  "date_utc": "2026-11-12"}]
        held = held_sessions([entry("2026-11-10")], exits, book)
        self.assertEqual(["2026-11-10", "2026-11-11"],
                         [d for _e, d in held])


class GradeSegmentTest(unittest.TestCase):
    def _grade(self, dates, mid):
        from desk3.conversion_shadow import (MinuteBook, SeriesBook,
                                             grade_segment)
        root = make_root(dates, mid=mid)
        book = SeriesBook(root)
        arm = {"parents": ["1w"], "grade_n": 20}
        return grade_segment(book, book.bench(), arm,
                             [entry(dates[0])], [], MinuteBook(root))

    def test_accruing_below_20_sessions_with_priced_segments(self):
        dates = ["2026-11-09", "2026-11-10", "2026-11-11",
                 "2026-11-12", "2026-11-13"]
        res = self._grade(dates, mid=-0.10)
        self.assertEqual("ACCRUING", res["state"])
        self.assertEqual(5, res["forward_sessions"])
        self.assertEqual(5, res["held_sessions_priced"])
        self.assertAlmostEqual(
            -1000.0, res["segments"]["MIDDAY"]["mean_bp"], places=0)
        self.assertAlmostEqual(
            1000.0, res["segments"]["OPEN_DRIVE"]["mean_bp"],
            places=0)

    def test_graded_positive_at_20_sessions_negative_midday(self):
        base = datetime(2026, 9, 1)
        dates = [(base + timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(28)
                 if (base + timedelta(days=i)).weekday() < 5][:20]
        res = self._grade(dates, mid=-0.10)
        self.assertEqual(20, res["forward_sessions"])
        self.assertEqual("GRADED_POSITIVE", res["state"])

    def test_graded_negative_at_20_sessions_positive_midday(self):
        base = datetime(2026, 9, 1)
        dates = [(base + timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(28)
                 if (base + timedelta(days=i)).weekday() < 5][:20]
        res = self._grade(dates, mid=0.10)
        self.assertEqual("GRADED_NEGATIVE", res["state"])


if __name__ == "__main__":
    unittest.main()
