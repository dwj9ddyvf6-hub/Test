"""CR6-V03 blockers (2026-11-14): saty_gpt_v03 producer half.

Pre-cure, every RTH evaluation since 2026-10-26 died in the
strategy's book rebuild ("observation rejected (C-1/C-10)"):
the shared snapshot serves extended-hours intraday bars and
clock-aligned 1Hour bars, while the strategy's FeatureBook
accepts only regular-session bars and its 1H frame is
session-aligned by design (bridge breaks at every overnight
seam for clock bars; warmup 1000 unreachable). The cure shapes
this sleeve's view at its v3 entrypoint (adapters3) and widens
the desk's SPY 5Min warm window 60 -> 300 days so the
session-aligned resample carries the pinned warmup depth.

These tests fail on the pre-cure tree (no shaping: the drive
stamps blocked_data) and pass on the cured tree. unittest
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


def _trading_days(end, n):
    from core.data import is_trading_day
    out = []
    d = end
    while len(out) < n:
        if is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace(
        "+00:00", "Z")


def _synthetic_view(now_iso):
    days = _trading_days(date(2026, 11, 13), 25)
    daily, five, one_h = [], [], []
    px = 750.0
    for d in days:
        daily.append({"t": _iso(datetime.combine(d, dtime(0, 0), ET)),
                      "o": px, "h": px + 3, "l": px - 3, "c": px + 1,
                      "v": 1000000})
        # extended-hours poison rows (premarket + post-close)
        five.append({"t": _iso(datetime.combine(d, dtime(4, 0), ET)),
                     "o": px, "h": px, "l": px, "c": px, "v": 10})
        five.append({"t": _iso(datetime.combine(d, dtime(16, 5), ET)),
                     "o": px, "h": px, "l": px, "c": px, "v": 10})
        t = datetime.combine(d, dtime(9, 30), ET)
        while t.time() < dtime(16, 0):
            five.append({"t": _iso(t), "o": px, "h": px + 0.5,
                         "l": px - 0.5, "c": px + 0.1, "v": 100})
            t += timedelta(minutes=5)
        # clock-aligned 1Hour poison (starts on the clock hour)
        t = datetime.combine(d, dtime(8, 0), ET)
        while t.time() < dtime(20, 0):
            one_h.append({"t": _iso(t), "o": px, "h": px + 1,
                          "l": px - 1, "c": px, "v": 500})
            t += timedelta(hours=1)
        px += 0.5
    return {"now": now_iso,
            "bars": {"SPY|1Day": daily, "SPY|5Min": five,
                     "SPY|1Hour": one_h},
            "positions": [], "slice": {"capital_usd": 10000.0,
                                       "cash_usd": 10000.0},
            "params": {}, "extra": {}}


def _stamp(tmp):
    stamp = None
    with open(os.path.join(tmp, "journal.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("event") == "last_evaluation":
                stamp = r["stamp"]
    return stamp


class TestCR6V03(unittest.TestCase):

    def test_shaping_contract(self):
        from adapters3.saty_gpt_v03 import _rth_shaped_view, _bar_start
        view = _synthetic_view("2026-11-13T15:09:56+00:00")
        shaped = _rth_shaped_view(view)
        self.assertIsNot(shaped, view)
        # the shared snapshot object is never mutated
        self.assertNotEqual(len(view["bars"]["SPY|5Min"]),
                            len(shaped["bars"]["SPY|5Min"]))
        for row in shaped["bars"]["SPY|5Min"]:
            start = _bar_start(row).astimezone(ET)
            self.assertTrue(dtime(9, 30) <= start.time()
                            <= dtime(15, 55))
        # 1H rebuilt session-aligned: 6 complete buckets per
        # session, anchored at 09:30 ET
        h1 = shaped["bars"]["SPY|1Hour"]
        self.assertEqual(len(h1), 25 * 6)
        for row in h1:
            start = _bar_start(row).astimezone(ET)
            self.assertEqual(start.minute, 30)
            self.assertTrue(9 <= start.hour <= 14)
        # daily untouched
        self.assertEqual(shaped["bars"]["SPY|1Day"],
                         view["bars"]["SPY|1Day"])

    def test_evaluation_passes_reference_and_book(self):
        import importlib
        mod = importlib.import_module("adapters3.saty_gpt_v03")
        view = _synthetic_view("2026-11-13T15:09:56+00:00")
        with tempfile.TemporaryDirectory() as tmp:
            ctx = {"state_dir": tmp,
                   "now": "2026-11-13T15:09:56+00:00",
                   "cycle_id": "test-cr6-v03"}
            self.assertEqual(mod.evaluate(view, ctx), [])
            stamp = _stamp(tmp)
        self.assertIsNotNone(stamp)
        # pre-cure this stamp is blocked_data / observation rejected
        self.assertNotEqual(stamp["state"], "blocked_data")
        self.assertNotIn("observation rejected",
                         str(stamp["decision"]))
        self.assertIsNotNone(stamp["reference"])
        self.assertGreater(stamp["frames"]["1H"]["count"], 0)

    def test_warm_window_carries_warmup_depth(self):
        from desk3.warm import INTRADAY_FETCHES
        self.assertIn(("SPY", "5Min", 300), INTRADAY_FETCHES)


if __name__ == "__main__":
    unittest.main()
