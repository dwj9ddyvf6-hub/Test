"""Blockers for WARM-DAILY-PARTIAL-BAR-20261102.

The desk gate's one failure (named 2026-11-02, R3 build):
test_investandbefree_dmac_blockers.TestInstallWiring
.test_live_warm_product_covers_daily_need read 0 bars for SPY|1Day
in the live warm product. Root cause: during the trading session
Alpaca's 1Day payload ends with today's IN-PROGRESS bar, so every
equity series ends on the current session instead of the latest
completed one, validate_daily_payload returned history_ends_*, and
_fetch dropped every equity symbol. The intraday warm product
therefore carried no equity |1Day series at all.

Cure (desk3/warm.py): before validation, trailing bars dated after
the latest completed session are trimmed (they are by definition
not completed bars; adapters' closed_bars would drop them anyway).
A series that is stale even after trimming still drops.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import unittest
from unittest import mock
from desk3 import warm


def _bar(day, close=100.0):
    return {"t": f"{day}T04:00:00Z", "o": close, "h": close,
            "l": close, "c": close, "v": 1000}


def _series(end_day, extra=()):
    days = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29"]
    if end_day != "2026-10-29":
        days.append(end_day)
    return [_bar(d) for d in days] + [_bar(d) for d in extra]


def _fetch_with(payload):
    drops = []
    def fake_fetch_json(url, headers=None, timeout=None):
        return {"bars": payload, "next_page_token": None}
    with mock.patch("desk3.netfetch.fetch_json", fake_fetch_json):
        out = warm._fetch(["SPY"], "1Day", "2025-06-01T00:00:00Z", {},
                          expected_last="2026-10-30",
                          session_drops=drops)
    return out, drops


class TestPartialBarTrim(unittest.TestCase):
    def test_partial_current_session_bar_does_not_drop_symbol(self):
        # Series ends on the completed session (Fri 2026-10-30) plus
        # today's in-progress bar (Mon 2026-11-02): symbol is kept,
        # and the in-progress bar is NOT in the returned series.
        out, drops = _fetch_with({"SPY": _series("2026-10-30",
                                                 extra=("2026-11-02",))})
        self.assertIn("SPY", out)
        self.assertEqual(out["SPY"][-1]["t"], "2026-10-30T04:00:00Z")
        self.assertEqual(drops, [])

    def test_stale_series_still_drops(self):
        # Ends Thu 2026-10-29 with nothing after: still stale, drops.
        out, drops = _fetch_with({"SPY": _series("2026-10-29")})
        self.assertNotIn("SPY", out)
        self.assertEqual(len(drops), 1)

    def test_exact_completed_series_unchanged(self):
        out, drops = _fetch_with({"SPY": _series("2026-10-30")})
        self.assertIn("SPY", out)
        self.assertEqual(len(out["SPY"]), 5)
        self.assertEqual(drops, [])


if __name__ == "__main__":
    unittest.main()
