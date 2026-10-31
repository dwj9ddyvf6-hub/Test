"""Bars payload integrity gate for grading.PriceSource (DEEP-PASS
3.1 item 2, adopted as is from the new-head Trade Brain hardening,
Section 2.3 point 10).

The daily history payload behind grading is validated as a whole
at load: more than 1000 bars for one symbol, a non finite or non
positive OHLC value, or a duplicate or non increasing date each
refuse the payload as daily_history_invalid_or_incomplete, instead
of the old per row dict load that silently overwrote duplicate
dates and accepted any values. Where a caller supplies the
expected latest completed session per symbol (derived from the
trading calendar, never a tolerance window), a history that does
not end on that session refuses as well; symbols the caller does
not name are not session checked, so a delisted name's shorter
history stays loadable.

Fail direction: on the pre-cure tree PriceSource loads every
payload below without complaint, so the refusal tests fail; the
clean load tests pass both ways as contract pins.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402


def _rows(days, close=100.0):
    return [[d, close, close + 1.0, close - 1.0, close, 1000]
            for d in days]


def _write(payload):
    fh = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False)
    json.dump(payload, fh)
    fh.close()
    return fh.name


class PriceSourceGateTests(unittest.TestCase):
    def test_clean_payload_loads(self):
        path = _write({"SPY": _rows(["2026-10-26", "2026-10-27"])})
        prices = G.PriceSource(path)
        self.assertEqual(prices.close("SPY", "2026-10-27"), 100.0)

    def test_duplicate_date_refused(self):
        path = _write({"SPY": _rows(["2026-10-27", "2026-10-27"])})
        with self.assertRaises(G.BarsIntegrityError) as cm:
            G.PriceSource(path)
        self.assertIn("daily_history_invalid_or_incomplete",
                      str(cm.exception))

    def test_non_increasing_dates_refused(self):
        path = _write({"SPY": _rows(["2026-10-27", "2026-10-26"])})
        with self.assertRaises(G.BarsIntegrityError):
            G.PriceSource(path)

    def test_non_positive_ohlc_refused(self):
        rows = _rows(["2026-10-27"])
        rows[0][4] = 0.0
        path = _write({"SPY": rows})
        with self.assertRaises(G.BarsIntegrityError):
            G.PriceSource(path)

    def test_non_finite_ohlc_refused(self):
        rows = _rows(["2026-10-27"])
        rows[0][2] = float("inf")
        path = _write({"SPY": rows})
        with self.assertRaises(G.BarsIntegrityError):
            G.PriceSource(path)

    def test_more_than_1000_bars_refused(self):
        days = [f"20{20 + i // 360:02d}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                for i in range(1001)]
        # strictly increasing unique dates across ~3 years
        import datetime as _dt
        base = _dt.date(2020, 1, 1)
        days = [(base + _dt.timedelta(days=i)).isoformat()
                for i in range(1001)]
        path = _write({"SPY": _rows(days)})
        with self.assertRaises(G.BarsIntegrityError):
            G.PriceSource(path)

    def test_expected_session_match_and_mismatch(self):
        path = _write({"SPY": _rows(["2026-10-26", "2026-10-27"]),
                       "OLD": _rows(["2026-10-20"])})
        prices = G.PriceSource(
            path, expected_sessions={"SPY": "2026-10-27"})
        self.assertEqual(prices.close("SPY", "2026-10-27"), 100.0)
        with self.assertRaises(G.BarsIntegrityError):
            G.PriceSource(path, expected_sessions={"SPY": "2026-10-28"})


if __name__ == "__main__":
    unittest.main()
