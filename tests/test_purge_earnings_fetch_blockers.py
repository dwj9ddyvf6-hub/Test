"""PURGE-2 regression blockers: earnings producers' day-fetch shape.

Pre-cure, EarningsProducer (forward scan, up to ~72 weekday fetches)
and EarningsEventsProducer (90-day history, ~64 weekday fetches) each
walked the SAME Nasdaq calendar endpoint strictly sequentially inside
one desk cycle — measured 234.2 s + 179.5 s of a 434.8 s producer
stage on the 2026-10-24 cold-cache cycle (95% of the cycle wall).
Cure: day fetches run through a bounded parallel map; every output
(payload, evidence counts, reports, days_failed) is byte-identical
to the sequential walk — only the wall changes. The concurrency
assertions FAIL pre-cure (max in flight == 1); the identity
assertions must pass on BOTH sides (preservation guard).
"""
import os, sys, threading, time, unittest
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desk3.producers3 import (EarningsEventsProducer,
                              build_earnings_payload)


class _InFlight:
    def __init__(self, delay=0.05):
        self.delay = delay
        self.lock = threading.Lock()
        self.cur = 0
        self.max = 0

    def __enter__(self):
        with self.lock:
            self.cur += 1
            self.max = max(self.max, self.cur)
        time.sleep(self.delay)
        return self

    def __exit__(self, *a):
        with self.lock:
            self.cur -= 1


class TestForwardScanParallel(unittest.TestCase):
    def test_identity_and_concurrency(self):
        tracker = _InFlight()
        session = date(2026, 10, 26)  # a Monday

        def fetch_day(iso):
            with tracker:
                if iso == "2026-10-27":
                    return {"AAA": "pre"}
                if iso == "2026-10-28":
                    return {"BBB": "after", "AAA": "after"}
                return {}

        payload = build_earnings_payload(["AAA", "BBB"], session, fetch_day)
        # identity: earliest date per symbol + evidence over consumed days
        self.assertEqual(payload["earnings"],
                         {"AAA": "2026-10-27", "BBB": "2026-10-28"})
        self.assertEqual(payload["earnings_time"],
                         {"AAA": "pre", "BBB": "after"})
        ev = payload["evidence"]
        self.assertEqual(ev["days_failed"], 0)
        self.assertEqual(ev["symbols_found"], 2)
        self.assertTrue(payload["fresh"])
        # the cure: fetches overlapped
        self.assertGreaterEqual(tracker.max, 2)


class TestHistoryParallel(unittest.TestCase):
    def test_identity_and_concurrency(self):
        tracker = _InFlight()
        good = {"2026-10-20": {"AAA": 0.05}, "2026-10-21": {"BBB": -0.02}}

        def transport(url):
            iso = url.rsplit("date=", 1)[-1]
            with tracker:
                if iso in good:
                    rows = [{"symbol": s,
                             "surprise": f"{v * 100:.1f}"}
                            for s, v in good[iso].items()]
                    return {"data": {"rows": rows},
                            "status": {"rCode": 200}}
                if iso == "2026-10-22":
                    raise RuntimeError("source down")
                return {"data": None, "status": {"rCode": 200}}

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            prod = EarningsEventsProducer(tmp, transport=transport,
                                          history_days=10)
            now = datetime(2026, 10, 26, tzinfo=timezone.utc)
            hist = prod._history(now, date(2026, 10, 26))
        self.assertIsNotNone(hist)
        self.assertEqual(hist["reports"],
                         {k: v for k, v in good.items()})
        self.assertEqual(hist["days_failed"], 1)  # only 2026-10-22
        self.assertGreaterEqual(tracker.max, 2)


if __name__ == "__main__":
    unittest.main()
