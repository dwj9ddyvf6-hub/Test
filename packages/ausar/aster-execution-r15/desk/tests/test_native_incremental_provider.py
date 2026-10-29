import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend.providers import ProviderError, Providers
from backend.store import DeskError, Store
from backend.tensor_runtime import canonical_native_bars, latest_native_clock

UTC = timezone.utc
CLOCK = datetime(2026, 10, 9, 19, 40, tzinfo=UTC)
ANCHOR = datetime(2026, 10, 8, 19, 30, tzinfo=UTC)


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return CLOCK.astimezone(tz) if tz else CLOCK.replace(tzinfo=None)


class IncrementalNativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"ASTER_MARKET_DATA": "yahoo", "ASTER_BAR_FALLBACK": "none"})
        self.env.start()
        self.time = patch("backend.providers.datetime", FrozenDateTime)
        self.time.start()
        self.store = Store(Path(self.temp.name) / "isolated.sqlite")
        self.calls = []
        self.missing = None
        self.price = 101
        self.fail = False
        self.provider = Providers(self.store, self.fetch)

    def tearDown(self):
        self.time.stop()
        self.env.stop()
        self.temp.cleanup()

    def fetch(self, method, url, *args):
        self.calls.append(url)
        if self.fail:
            raise ProviderError("fixture unavailable")
        stamps = [ANCHOR, *[datetime(2026, 10, 9, h, 30, tzinfo=UTC) for h in range(13, 20)]]
        prices = [None if s == self.missing else self.price for s in stamps]
        quote = {"open": prices, "high": [None if p is None else p+1 for p in prices],
                 "low": [None if p is None else p-1 for p in prices], "close": prices,
                 "volume": [1000 for s in stamps]}
        return {"chart": {"result": [{"meta": {"dataGranularity": "60m"},
            "timestamp": [int(s.timestamp()) for s in stamps], "indicators": {"quote": [quote]}}]}}

    def test_exact_overlap_window_cache_identity_and_no_quote_side_effect(self):
        first = self.provider.native_bars_since("AAPL", ANCHOR)
        query = parse_qs(urlparse(self.calls[0]).query)
        self.assertEqual(query["period1"], [str(int(ANCHOR.timestamp()))])
        self.assertEqual(query["period2"], [str(int(CLOCK.timestamp()))])
        self.assertNotIn("range", query)
        self.assertEqual(first["request_window"]["start"], ANCHOR.isoformat())
        second = self.provider.native_bars_since("AAPL", ANCHOR)
        self.assertTrue(second["cached"])
        self.assertEqual(first["revision_id"], second["revision_id"])
        self.assertEqual(first["observed_at"], second["observed_at"])
        self.assertEqual(len(self.calls), 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0], 0)
        rows = canonical_native_bars(first, "1h", CLOCK, expected_symbol="AAPL")
        self.assertEqual(rows[0].executable_at_ms, int(ANCHOR.timestamp()*1000))
        self.assertEqual(rows[-1].completed_at_ms, int(datetime(2026,10,9,19,30,tzinfo=UTC).timestamp()*1000))

    def test_completed_missing_row_remains_blocked(self):
        self.missing = datetime(2026,10,9,17,30,tzinfo=UTC)
        revision = self.provider.native_bars_since("AAPL", ANCHOR)
        self.assertEqual(revision["omitted_bar_rows"][0]["timestamp"], self.missing.isoformat())
        with self.assertRaisesRegex(DeskError, "already completed"):
            canonical_native_bars(revision, "1h", CLOCK, expected_symbol="AAPL")

    def test_only_proven_current_forming_omission_can_be_quarantined(self):
        self.missing = datetime(2026,10,9,19,30,tzinfo=UTC)
        revision = self.provider.native_bars_since("AAPL", ANCHOR)
        diagnostics = []
        rows = canonical_native_bars(revision, "1h", CLOCK, expected_symbol="AAPL", diagnostics=diagnostics)
        self.assertEqual(len(rows), 7)
        self.assertEqual(diagnostics[0]["reason"], "quarantined_proved_unfinished_vendor_omission")
        self.assertFalse(diagnostics[0]["native_bar_admitted"])

    def test_failed_refresh_never_returns_stale_native_revision(self):
        self.provider.native_bars_since("AAPL", ANCHOR)
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_cache SET fetched_at=?", ((CLOCK-timedelta(minutes=2)).isoformat(),))
        self.fail = True
        with self.assertRaisesRegex(ProviderError, "no stale"):
            self.provider.native_bars_since("AAPL", ANCHOR)

    def test_changed_payload_gets_new_revision_and_preserves_prior(self):
        first = self.provider.native_bars_since("AAPL", ANCHOR)
        with self.store.transaction() as con:
            con.execute("DELETE FROM a_bar_cache")
        self.price = 102
        second = self.provider.native_bars_since("AAPL", ANCHOR)
        self.assertNotEqual(first["revision_id"], second["revision_id"])
        self.assertEqual(self.provider._revision(first["revision_id"])[1]["bars"][0]["close"], 101)

    def test_invalid_anchor_or_foreign_source_is_rejected_before_transport(self):
        for stamp in (CLOCK+timedelta(seconds=1), CLOCK-timedelta(days=733), CLOCK.replace(tzinfo=None), None, True):
            with self.assertRaises(DeskError):
                self.provider.native_bars_since("AAPL", stamp)
        self.provider.kind = "alpaca"
        with self.assertRaises(DeskError):
            self.provider.native_bars_since("AAPL", ANCHOR)
        self.assertEqual(self.calls, [])

    def test_coherent_foreign_source_or_wrong_anchor_cache_never_authorizes(self):
        for change in ('provider', 'window'):
            with self.subTest(change=change):
                first = self.provider.native_bars_since('AAPL', ANCHOR)
                content = self.provider._revision(first['revision_id'])[1]
                if change == 'provider':
                    content['provider'] = 'alpaca'
                else:
                    content['request_window'] = {**content['request_window'], 'start':(ANCHOR-timedelta(hours=1)).isoformat()}
                self.provider._save_bars('AAPL', first['range'], '60m', content)
                calls = len(self.calls)
                repaired = self.provider.native_bars_since('AAPL', ANCHOR)
                self.assertEqual(len(self.calls), calls+1)
                self.assertEqual(repaired['provider'], 'yahoo')
                self.assertEqual(repaired['request_window']['start'], ANCHOR.isoformat())
                self.assertFalse(repaired['cached'])

    def test_last_short_and_half_day_bar_anchor_is_not_one_hour_before_close(self):
        normal = latest_native_clock("1h", datetime(2026,10,8,20,tzinfo=UTC))
        half = latest_native_clock("1h", datetime(2025,11,28,18,tzinfo=UTC))
        self.assertEqual(normal["executable_at_ms"], int(ANCHOR.timestamp()*1000))
        self.assertEqual(half["executable_at_ms"], int(datetime(2025,11,28,17,30,tzinfo=UTC).timestamp()*1000))


if __name__ == "__main__":
    unittest.main()
