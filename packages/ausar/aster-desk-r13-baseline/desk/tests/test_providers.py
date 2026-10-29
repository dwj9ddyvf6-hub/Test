import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from backend.providers import AlpacaPaper, PAPER_URL, ProviderError, Providers, _csv_request, _request, exchange_calendar
from backend.store import DeskError, Store


UTC = timezone.utc


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "desk.sqlite")
        self.env = patch.dict(os.environ, {"ASTER_MARKET_DATA": "yahoo"}, clear=True)
        self.env.start()
        self.timestamp = int((datetime.now(UTC) - timedelta(seconds=30)).timestamp())
        self.calls = []

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def chart(self, *args):
        self.calls.append(args)
        return {"chart": {"result": [{"meta": {"regularMarketTime": self.timestamp, "regularMarketPrice": 123.45}, "timestamp": [self.timestamp - 86400], "indicators": {"quote": [{"open": [120], "high": [125], "low": [119], "close": [124], "volume": [1000]}], "adjclose": [{"adjclose": [123]}]}}], "error": None}}

    def test_quote_timestamp_is_provider_timestamp_and_connectivity_requires_read(self):
        provider = Providers(self.store, self.chart)
        self.assertFalse(provider.status()["market_data"]["connected"])
        result = provider.refresh(["AAPL"])
        self.assertEqual(result["refreshed"], 1)
        self.assertEqual(result["quotes"][0]["as_of"], datetime.fromtimestamp(self.timestamp, UTC).isoformat())
        self.assertIn("may be delayed", result["quotes"][0]["source"])
        self.assertTrue(provider.status()["market_data"]["connected"])
        self.assertIsNone(provider.broker)
        provider.refresh(["AAPL"])
        history = provider.observations("AAPL")
        self.assertEqual(len(history["quotes"]), 1)
        self.assertTrue(history["quotes"][0]["accepted"])
        self.assertEqual(history["quotes"][0]["provider_asof"], datetime.fromtimestamp(self.timestamp, UTC).isoformat())
        self.assertEqual(provider.observations("AAPL", datetime.now(UTC) - timedelta(minutes=1))["quotes"], [])

    def test_failed_or_old_read_preserves_saved_truth(self):
        provider = Providers(self.store, self.chart)
        provider.refresh(["AAPL"])
        self.timestamp -= 600
        result = provider.refresh(["AAPL"])
        self.assertEqual(result["refreshed"], 0)
        self.assertEqual(len(result["errors"]), 1)
        with self.store.connect() as con:
            self.assertEqual(float(con.execute("SELECT price FROM quotes").fetchone()[0]), 123.45)
        self.assertFalse(provider.status()["market_data"]["connected"])

    def test_bars_are_persisted_cached_and_do_not_create_quotes(self):
        provider = Providers(self.store, self.chart)
        bars = provider.bars("AAPL")
        self.assertEqual(bars["bars"][0]["adjusted_close"], 123)
        self.assertFalse(bars["cached"])
        self.assertTrue(Providers(self.store, self.chart).bars("AAPL")["cached"])
        self.assertEqual(len(self.calls), 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0], 0)
            con.execute("UPDATE a_bar_cache SET fetched_at=?", ((datetime.now(UTC) - timedelta(minutes=2)).isoformat(),))
        def fail(*args):
            raise ProviderError("Failed")
        stale = Providers(self.store, fail).bars("AAPL")
        self.assertTrue(stale["stale_cache"])
        self.assertEqual(stale["bars"], bars["bars"])

    def test_bar_revision_hash_retains_changed_history_and_dedupes_same_payload(self):
        provider = Providers(self.store, self.chart)
        original = provider.bars("AAPL")
        with self.store.transaction() as con:
            con.execute("DELETE FROM a_bar_cache")
        same = provider.bars("AAPL")
        self.assertEqual(same["revision_id"], original["revision_id"])
        self.assertEqual(same["observed_at"], original["observed_at"])
        def revised(*args):
            result = self.chart(*args)
            result["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"][0] = 122
            return result
        provider._transport = revised
        with self.store.transaction() as con:
            con.execute("DELETE FROM a_bar_cache")
        changed = provider.bars("AAPL")
        self.assertNotEqual(changed["revision_id"], original["revision_id"])
        revisions = provider.observations("AAPL")["bar_revisions"]
        self.assertEqual(len(revisions), 2)
        self.assertEqual({r["data"]["bars"][0]["adjusted_close"] for r in revisions}, {122, 123})
        self.assertTrue(all("adjusted_close" in r["adjustment"] for r in revisions))

    def test_manual_never_fabricates_history(self):
        with patch.dict(os.environ, {"ASTER_MARKET_DATA": "manual"}):
            provider = Providers(self.store, self.chart)
        self.assertEqual(provider.refresh(["AAPL"])["refreshed"], 0)
        with self.assertRaises(ProviderError):
            provider.bars("AAPL")
        self.assertFalse(self.calls)

    def test_yahoo_missing_candles_keep_exact_raw_omission_evidence(self):
        first = self.timestamp - 86400
        opening = self.timestamp - 90
        def transport(*args):
            return {"chart": {"result": [{"meta": {"dataGranularity": "1h",
                "regularMarketTime": self.timestamp}, "timestamp": [first, opening, self.timestamp],
                "indicators": {"quote": [{"open": [120, None, 123],
                    "high": [125, None, 123], "low": [119, None, 123],
                    "close": [124, None, 123], "volume": [1000, None, 0]}]}}]}}
        provider = Providers(self.store, transport)
        result = provider.bars("AAT", "5d", "60m")
        self.assertEqual(result["omitted_rows"], 1)
        self.assertEqual(result["completeness"]["status"], "bounded_partial")
        self.assertEqual(result["source_row_count"], 3)
        missing = {"row_index": 1, "timestamp": datetime.fromtimestamp(opening, UTC).isoformat(),
                   "open": None, "high": None, "low": None, "close": None, "volume": None}
        self.assertEqual(result["omitted_bar_rows"], [missing])
        self.assertEqual(provider.bars("AAT", "5d", "60m")["omitted_bar_rows"], [missing])
        with self.store.connect() as con:
            raw = json.loads(con.execute("SELECT data FROM a_bar_revisions WHERE id=?",
                                        (result["revision_id"],)).fetchone()[0])
        self.assertEqual(raw["omitted_bar_rows"], [missing])
        self.assertEqual(raw["bars"][-1]["volume"], 0)
        self.assertEqual(raw["bars"][0]["close"], 124)

    def test_yahoo_inconsistent_candle_is_retained_without_repaired_prices(self):
        day = int(datetime(2026, 10, 9, 13, 30, tzinfo=UTC).timestamp())
        def transport(*args):
            return {"chart": {"result": [{"meta": {"dataGranularity": "1d",
                "regularMarketTime": self.timestamp}, "timestamp": [day-86400, day],
                "indicators": {"quote": [{"open": [169.35, 169.35],
                    "high": [169.69, 168.665], "low": [164.34, 167.33],
                    "close": [168.96, 168.25], "volume": [271400, 13426]}]}}]}}
        provider = Providers(self.store, transport)
        result = provider.bars("ABG", "5d", "1d")
        self.assertEqual(result["omitted_rows"], 1)
        self.assertEqual(result["completeness"]["status"], "bounded_partial")
        self.assertEqual(result["source_row_count"], 2)
        self.assertEqual(len(result["bars"]), 1)
        original = {"row_index": 1, "timestamp": datetime.fromtimestamp(day, UTC).isoformat(),
                    "open": 169.35, "high": 168.665, "low": 167.33,
                    "close": 168.25, "volume": 13426}
        self.assertEqual(result["omitted_bar_rows"], [original])
        with self.store.connect() as con:
            saved = json.loads(con.execute("SELECT data FROM a_bar_revisions WHERE id=?",
                                          (result["revision_id"],)).fetchone()[0])
        self.assertEqual(saved["omitted_bar_rows"], [original])
        self.assertEqual(saved["bars"][0]["open"], 169.35)

    def test_weekly_named_range_requests_complete_new_york_week_boundary(self):
        provider = Providers(self.store, self.chart)
        result = provider.bars("MARA", "1mo", "1wk")
        query = parse_qs(urlparse(self.calls[-1][1]).query)
        self.assertNotIn("range", query)
        self.assertEqual(query["interval"], ["1wk"])
        start = datetime.fromtimestamp(int(query["period1"][0]), UTC).astimezone(ZoneInfo("America/New_York"))
        end = datetime.fromtimestamp(int(query["period2"][0]), UTC)
        nominal = end.astimezone(ZoneInfo("America/New_York")).date() - timedelta(days=31)
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(start.time().replace(tzinfo=None), datetime.min.time())
        self.assertLessEqual(start.date(), nominal)
        self.assertLess((nominal-start.date()).days, 7)
        self.assertEqual(result["request_window"]["start"], start.astimezone(UTC).isoformat())
        with self.store.connect() as con:
            saved = json.loads(con.execute("SELECT data FROM a_bar_revisions WHERE id=?",
                                          (result["revision_id"],)).fetchone()[0])
        self.assertEqual(saved["request_window"], result["request_window"])
        self.assertEqual(result["bars"][0]["close"], 124)

    def test_weekly_supplemental_aggregate_keeps_vendor_marker_and_raw_prices(self):
        def chart(*args):
            response = self.chart(*args)
            data = response["chart"]["result"][0]
            data["meta"]["dataGranularity"] = "1wk"
            data["timestamp"] = [self.timestamp - 7 * 86400, self.timestamp]
            data["indicators"]["quote"] = [{"open": [120, 121], "high": [125, 127],
                "low": [119, 120], "close": [124, 126], "volume": [1000, 750]}]
            return response
        provider = Providers(self.store, chart)
        result = provider.bars("AAPL", "1mo", "1wk")
        self.assertEqual(result["vendor_regular_market_timestamp"], datetime.fromtimestamp(self.timestamp, UTC).isoformat())
        self.assertEqual(len(result["bars"]), 2)
        self.assertEqual(result["bars"][-1]["volume"], 750)
        self.assertEqual(result["bars"][-1]["high"], 127)
        revision = provider.observations("AAPL")["bar_revisions"][0]["data"]
        self.assertEqual(revision["vendor_regular_market_timestamp"], result["vendor_regular_market_timestamp"])
        self.assertEqual(revision["bars"], result["bars"])

    def test_broker_only_hardcoded_paper_url_preserves_legs_and_no_blind_retry(self):
        calls = []
        def transport(method, url, payload, headers):
            calls.append((method, url, payload, headers))
            if url.endswith("/account"):
                return {"status": "ACTIVE", "account_number": "PA123", "cash": "1000", "trading_blocked": False}
            if method == "POST":
                return {"id": "broker-id", "client_order_id": payload["client_order_id"], "status": "new", "filled_qty": "0", "legs": [{"id": "stop-id", "status": "held"}]}
            return []
        broker = AlpacaPaper("test-key", "test-secret", transport=transport)
        result = broker.submit({"client_id": "aster_owned_1", "symbol": "AAPL", "side": "buy", "quantity": "2", "take_profit": "150", "stop_loss": {"stop_price": "110"}})
        self.assertEqual(result["legs"][0]["id"], "stop-id")
        self.assertEqual(calls[-1][2]["order_class"], "bracket")
        self.assertEqual(calls[-1][2]["qty"], "2")
        self.assertTrue(all(url.startswith(PAPER_URL) for _, url, _, _ in calls))
        broker.orders()
        self.assertIn("nested=true", calls[-1][1])
        self.assertIn("status=all", calls[-1][1])
        def ambiguous(*args):
            raise ProviderError("Ambiguous submission")
        broker._transport = ambiguous
        with self.assertRaises(ProviderError):
            broker.submit({"client_id": "aster_owned_2", "symbol": "AAPL", "side": "buy", "quantity": 1})

    def test_not_found_is_distinct_from_unavailable_and_keys_not_exported(self):
        def absent(*args):
            raise ProviderError("Not found", 404)
        broker = AlpacaPaper("test-key", "test-secret", transport=absent)
        self.assertIsNone(broker.get_order("aster_owned"))
        def unavailable(*args):
            raise ProviderError("Unavailable", 503)
        broker._transport = unavailable
        with self.assertRaises(ProviderError):
            broker.get_order("aster_owned")
        with patch.dict(os.environ, {"ASTER_ALPACA_KEY": "private-key", "ASTER_ALPACA_SECRET": "private-secret"}):
            provider = Providers(self.store, unavailable)
        public = json.dumps(provider.status())
        self.assertNotIn("private-key", public)
        self.assertNotIn("private-secret", public)
        self.assertFalse(provider.status()["broker"]["connected"])

    def test_broker_telemetry_never_deadlocks_existing_sqlite_writer(self):
        provider = Providers(self.store, self.chart)
        with self.store.transaction() as con:
            provider._record("broker", True, None)
            self.assertTrue(provider.status()["broker"]["last_success_at"])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_provider_state").fetchone()[0], 0)
        provider.status()
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_provider_state").fetchone()[0], 1)

    def test_named_accounts_are_isolated_configured_connections_without_secrets(self):
        calls = []
        def accounts(method, url, payload, headers):
            calls.append(headers["APCA-API-KEY-ID"])
            return {"status": "ACTIVE", "account_number": "PA-" + headers["APCA-API-KEY-ID"], "cash": "0"}
        env = {"ASTER_ALPACA_ACCOUNTS": "research,forward", "ASTER_ALPACA_KEY": "default-key", "ASTER_ALPACA_SECRET": "default-secret", "ASTER_ALPACA_RESEARCH_KEY": "research-key", "ASTER_ALPACA_RESEARCH_SECRET": "research-secret", "ASTER_ALPACA_FORWARD_KEY": "forward-key", "ASTER_ALPACA_FORWARD_SECRET": "forward-secret"}
        with patch.dict(os.environ, env):
            provider = Providers(self.store, accounts)
        self.assertIs(provider.broker, provider.broker_for("default"))
        self.assertIsNone(provider.broker_for("unconfigured"))
        self.assertFalse(provider.status()["broker"]["accounts"][1]["connected"])
        provider.broker_for("research").account()
        provider.broker_for("forward").account()
        self.assertEqual(calls, ["research-key", "forward-key"])
        status = provider.status()
        self.assertEqual(status["broker"]["connection_ids"], ["default", "research", "forward"])
        self.assertFalse(status["broker"]["accounts"][0]["connected"])
        self.assertTrue(status["broker"]["accounts"][1]["connected"])
        public = json.dumps(status)
        self.assertTrue(all(value not in public for value in env.values() if "secret" in value or "key" in value))
        with patch.dict(os.environ, {"ASTER_ALPACA_ACCOUNTS": "research,../../secret"}):
            with self.assertRaises(DeskError):
                Providers(self.store, accounts)

    def test_nyse_dst_holidays_and_early_close(self):
        before = exchange_calendar(datetime(2025, 3, 7, 15, 0, tzinfo=UTC))
        after = exchange_calendar(datetime(2025, 3, 10, 15, 0, tzinfo=UTC))
        self.assertEqual(before["open_at"], "2025-03-07T14:30:00+00:00")
        self.assertEqual(after["open_at"], "2025-03-10T13:30:00+00:00")
        self.assertFalse(exchange_calendar(datetime(2025, 7, 4, 15, tzinfo=UTC))["is_session"])
        early = exchange_calendar(datetime(2025, 7, 3, 16, tzinfo=UTC))
        self.assertTrue(early["early_close"])
        self.assertEqual(early["close_at"], "2025-07-03T17:00:00+00:00")
        self.assertFalse(exchange_calendar(datetime(2025, 7, 3, 17, tzinfo=UTC))["is_open"])
        self.assertFalse(exchange_calendar(datetime(2025, 1, 9, 16, tzinfo=UTC))["is_session"])

    def test_stooq_daily_failover_has_real_source_identity_and_never_becomes_quote(self):
        csv_calls = []
        date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        def failed_primary(*args):
            raise ProviderError("Fixture Yahoo unavailable")
        def csv_data(url):
            csv_calls.append(url)
            return "Date,Open,High,Low,Close,Volume\n" + date + ",10,11,9,10.5,1000\n"
        provider = Providers(self.store, failed_primary, csv_data)
        result = provider.bars("AAPL", "1mo", "1d")
        self.assertEqual(result["provider"], "stooq")
        self.assertEqual(result["fallback_from"], "yahoo")
        self.assertIn("adjustment policy unspecified", result["adjustment"])
        self.assertNotIn("adjusted_close", result["bars"][0])
        self.assertEqual(len(csv_calls), 1)
        self.assertIn("s=aapl.us", csv_calls[0])
        self.assertEqual(provider.refresh(["AAPL"])["refreshed"], 0)
        self.assertEqual(len(csv_calls), 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0], 0)
        manifest = provider.bar_manifest(result["revision_id"])
        self.assertEqual(manifest["finality"], "provisional_vendor_observation")
        self.assertIn("not a trade", manifest["timestamp_semantics"])
        status = provider.status()
        self.assertFalse(status["market_data"]["connected"])
        self.assertTrue(next(a for a in status["historical_data"]["adapters"] if a["provider"] == "stooq")["connected"])

    def test_intraday_requests_cannot_fall_back_to_daily_data_or_claim_availability(self):
        csv_calls = []
        def unavailable(*args):
            raise ProviderError("Fixture unavailable")
        provider = Providers(self.store, unavailable, lambda url: csv_calls.append(url) or "No data")
        with self.assertRaises(ProviderError):
            provider.bars("AAPL", "1d", "1m")
        self.assertFalse(csv_calls)
        with self.assertRaises(ProviderError):
            provider.bars("AAPL", "1mo", "1d")
        self.assertEqual(len(csv_calls), 1)
        self.assertTrue(all(not a["connected"] for a in provider.status()["historical_data"]["adapters"]))

    def test_full_vendor_response_pages_are_bound_to_immutable_revision(self):
        count = 2501
        start = self.timestamp - count * 60
        price = [9.0]
        def many_bars(*args):
            return {"chart": {"result": [{"timestamp": [start + i * 60 for i in range(count)], "indicators": {"quote": [{"open": [9] * count, "high": [10] * count, "low": [8] * count, "close": [price[0]] * count, "volume": [100] * count}]}}]}}
        provider = Providers(self.store, many_bars)
        original = provider.bars("AAPL", "5d", "1m")
        self.assertEqual(len(original["bars"]), count)
        self.assertFalse(original["truncated"])
        manifest = provider.bar_manifest(original["revision_id"])
        self.assertEqual(manifest["bar_count"], count)
        self.assertEqual(manifest["completeness"]["status"], "complete_vendor_response")
        first = provider.bar_page(original["revision_id"], limit=1000)
        second = provider.bar_page(original["revision_id"], first["next_cursor"], 1000)
        last = provider.bar_page(original["revision_id"], second["next_cursor"], 1000)
        self.assertEqual(first["bars"] + second["bars"] + last["bars"], original["bars"])
        self.assertIsNone(last["next_cursor"])
        price[0] = 9.5
        with self.store.transaction() as con:
            con.execute("DELETE FROM a_bar_cache")
        revised = provider.bars("AAPL", "5d", "1m")
        self.assertNotEqual(revised["revision_id"], original["revision_id"])
        self.assertEqual(provider.bar_page(original["revision_id"], limit=1)["bars"][0]["close"], 9.0)
        with self.assertRaises(DeskError):
            provider.bar_page(revised["revision_id"], first["next_cursor"])
        with self.assertRaises(DeskError):
            provider.bar_page(original["revision_id"], limit=1001)

    def test_alpaca_bounded_vendor_continuation_creates_new_complete_revision(self):
        calls = []
        start = datetime.now(UTC) - timedelta(days=5)
        def pages(method, url, payload, headers):
            calls.append(url)
            token = parse_qs(urlparse(url).query).get("page_token", ["p0"])[0]
            index = int(token[1:])
            return {"bars": [{"t": (start + timedelta(days=index)).isoformat(), "o": 10, "h": 11, "l": 9, "c": 10, "v": 100}], "next_page_token": "p" + str(index + 1) if index < 3 else None}
        with patch.dict(os.environ, {"ASTER_MARKET_DATA": "alpaca", "ASTER_ALPACA_KEY": "fixture-key", "ASTER_ALPACA_SECRET": "fixture-secret"}):
            provider = Providers(self.store, pages)
        initial = provider.bars("AAPL", "1mo", "1d")
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(initial["bars"]), 3)
        manifest = provider.bar_manifest(initial["revision_id"])
        self.assertEqual(manifest["completeness"]["status"], "bounded_partial")
        self.assertTrue(manifest["vendor_continuation_available"])
        completed = provider.continue_bars(initial["revision_id"])
        self.assertTrue(completed["continued"])
        self.assertEqual(completed["manifest"]["bar_count"], 4)
        self.assertEqual(completed["manifest"]["completeness"]["status"], "complete_vendor_response")
        self.assertEqual(provider.bar_manifest(initial["revision_id"])["bar_count"], 3)
        self.assertFalse(provider.continue_bars(completed["manifest"]["revision_id"])["continued"])

    def test_manifest_detects_tampered_revision_content(self):
        provider = Providers(self.store, self.chart)
        revision = provider.bars("AAPL")["revision_id"]
        with self.store.transaction() as con:
            content = json.loads(con.execute("SELECT data FROM a_bar_revisions WHERE id=?", (revision,)).fetchone()[0])
            content["bars"][0]["close"] = 500
            con.execute("UPDATE a_bar_revisions SET data=? WHERE id=?", (json.dumps(content), revision))
        with self.assertRaisesRegex(DeskError, "integrity"):
            provider.bar_manifest(revision)

    def test_historical_registry_can_fail_over_to_explicit_fixture_adapter(self):
        def unavailable(*args):
            raise ProviderError("Fixture primary unavailable")
        provider = Providers(self.store, unavailable)
        def fixture(sym, range, interval):
            return {"provider": "fixture_daily", "source": "Explicit in-process historical fixture", "adjustment": "Fixture raw", "bars": [{"timestamp": datetime.fromtimestamp(self.timestamp - 86400, UTC).isoformat(), "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100}], "truncated": False}
        provider.register_historical_adapter("fixture_daily", fixture, {"1d"})
        provider.bar_fallbacks = ["fixture_daily"]
        result = provider.bars("AAPL")
        self.assertEqual(result["provider"], "fixture_daily")
        adapter = next(a for a in provider.status()["historical_data"]["adapters"] if a["provider"] == "fixture_daily")
        self.assertTrue(adapter["historical_only"])
        self.assertTrue(adapter["connected"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0], 0)

    def test_nonfinite_bar_volume_preserves_prior_valid_revision(self):
        provider = Providers(self.store, self.chart)
        original = provider.bars("AAPL")
        def bad_volume(*args):
            response = self.chart(*args)
            response["chart"]["result"][0]["indicators"]["quote"][0]["volume"][0] = float("nan")
            return response
        provider._transport = bad_volume
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_cache SET fetched_at=?", ((datetime.now(UTC) - timedelta(minutes=2)).isoformat(),))
        retained = provider.bars("AAPL")
        self.assertTrue(retained["stale_cache"])
        self.assertEqual(retained["revision_id"], original["revision_id"])
        self.assertEqual(provider.bar_manifest(original["revision_id"])["bar_count"], 1)

    def test_max_history_uses_explicit_bounds_and_records_vendor_granularity(self):
        def daily(*args):
            result = self.chart(*args)
            result["chart"]["result"][0]["meta"]["dataGranularity"] = "1d"
            return result
        provider = Providers(self.store, daily)
        result = provider.bars("AAPL", "max", "1d")
        params = parse_qs(urlparse(self.calls[0][1]).query)
        self.assertEqual(params["interval"], ["1d"])
        self.assertEqual(params["period1"], ["-2208988800"])
        self.assertNotIn("range", params)
        self.assertEqual(provider.bar_manifest(result["revision_id"])["vendor_interval"], "1d")

    def test_monthly_vendor_response_cannot_masquerade_as_daily_bars(self):
        def coarse(*args):
            result = self.chart(*args)
            result["chart"]["result"][0]["meta"]["dataGranularity"] = "1mo"
            return result
        provider = Providers(self.store, coarse)
        with self.assertRaises(ProviderError):
            provider.bars("AAPL", "max", "1d")
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_bar_revisions").fetchone()[0], 0)

    def test_open_order_census_cannot_be_hidden_by_recent_closed_history(self):
        calls = []
        def census(method, url, payload, headers):
            status = parse_qs(urlparse(url).query)["status"][0]
            calls.append(status)
            return [{"id": "old-open", "status": "new"}] if status == "open" else [{"id": "recent-closed", "status": "filled"}]
        broker = AlpacaPaper("fixture", "fixture", transport=census)
        self.assertEqual({row["id"] for row in broker.orders()}, {"old-open", "recent-closed"})
        self.assertEqual(calls, ["open", "all"])

    def test_saturated_open_order_census_is_not_claimed_complete(self):
        broker = AlpacaPaper("fixture", "fixture", transport=lambda *args: [{"id": str(i)} for i in range(500)])
        with self.assertRaises(ProviderError):
            broker.orders()

    def test_malformed_quote_is_contained_and_other_symbols_continue(self):
        def malformed(method, url, *args):
            if "/BAD?" in url:
                return []
            if "/HUGE?" in url:
                return {"chart": {"result": [{"meta": {"regularMarketTime": 10 ** 100, "regularMarketPrice": 10}}]}}
            return self.chart(method, url, *args)
        provider = Providers(self.store, malformed)
        result = provider.refresh(["BAD", "HUGE", "GOOD"])
        self.assertEqual(result["refreshed"], 1)
        self.assertEqual({row["symbol"] for row in result["errors"]}, {"BAD", "HUGE"})

    def test_cached_bar_corruption_is_recovered_from_immutable_revision(self):
        provider = Providers(self.store, self.chart)
        original = provider.bars("AAPL")
        with self.store.transaction() as con:
            cached = json.loads(con.execute("SELECT data FROM a_bar_cache").fetchone()[0])
            cached["bars"][0]["close"] = 999
            con.execute("UPDATE a_bar_cache SET data=?", (json.dumps(cached),))
        retained = provider.bars("AAPL")
        self.assertEqual(retained["bars"], original["bars"])
        self.assertEqual(retained["revision_id"], original["revision_id"])

    def test_invalid_ohlc_preserves_last_valid_revision(self):
        provider = Providers(self.store, self.chart)
        original = provider.bars("AAPL")
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_cache SET fetched_at=?", ((datetime.now(UTC) - timedelta(minutes=2)).isoformat(),))
        def invalid(*args):
            result = self.chart(*args)
            result["chart"]["result"][0]["indicators"]["quote"][0]["high"][0] = 100
            return result
        provider._transport = invalid
        retained = provider.bars("AAPL")
        self.assertTrue(retained["stale_cache"])
        self.assertEqual(retained["revision_id"], original["revision_id"])

    def test_vendor_timestamps_are_normalized_before_sort_and_deduplication(self):
        provider = Providers(self.store, self.chart)
        content = {"provider": "fixture", "source": "Fixture", "adjustment": "raw", "bars": [
            {"timestamp": "2025-01-02T15:00:00+02:00", "open": 10, "high": 11, "low": 9, "close": 10},
            {"timestamp": "2025-01-02T14:00:00+00:00", "open": 10, "high": 11, "low": 9, "close": 10}]}
        result = provider._save_bars("AAPL", "1mo", "1d", content)
        self.assertEqual([b["timestamp"] for b in result["bars"]], ["2025-01-02T13:00:00+00:00", "2025-01-02T14:00:00+00:00"])
        content["bars"][1]["timestamp"] = "2025-01-02T13:00:00+00:00"
        with self.assertRaises(ProviderError):
            provider._save_bars("AAPL", "1mo", "1d", content)

    def test_malformed_revision_is_unavailable_and_cache_cannot_use_it(self):
        provider = Providers(self.store, self.chart)
        revision = provider.bars("AAPL")["revision_id"]
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_revisions SET data='not json' WHERE id=?", (revision,))
        with self.assertRaises(DeskError) as caught:
            provider.bar_manifest(revision)
        self.assertEqual(caught.exception.status, 503)
        with self.assertRaises(DeskError):
            provider.observations("AAPL")
        # A fresh identical provider read cannot claim the broken archive has
        # been repaired, or silently replace its immutable evidence.
        with self.assertRaises(ProviderError):
            provider.bars("AAPL")
        provider._transport = lambda *args: (_ for _ in ()).throw(ProviderError("Fixture unavailable"))
        with self.assertRaises(ProviderError):
            provider.bars("AAPL")

    def test_adapter_bound_is_partial_even_when_adapter_fails_to_flag_it(self):
        provider = Providers(self.store, self.chart)
        provider.MAX_BARS = 2
        content = {"provider": "fixture", "source": "Fixture", "adjustment": "raw", "bars": [
            {"timestamp": f"2025-01-0{i}T14:00:00+00:00", "open": 10, "high": 11, "low": 9, "close": 10}
            for i in (2, 3, 4)], "truncated": False}
        result = provider._save_bars("AAPL", "1mo", "1d", content)
        self.assertTrue(result["truncated"])
        self.assertEqual(provider.bar_manifest(result["revision_id"])["completeness"]["status"], "bounded_partial")

    def test_adapter_interval_generator_is_retained(self):
        provider = Providers(self.store, self.chart)
        provider.register_historical_adapter("fixture", lambda *args: {}, (i for i in ["1d"]))
        self.assertEqual(provider.historical_adapters["fixture"]["intervals"], {"1d"})

    def test_adapter_cannot_mislabel_another_provider_as_its_own_source(self):
        provider = Providers(self.store, self.chart)
        provider.register_historical_adapter("fixture", lambda *args: {"provider": "yahoo", "bars": []}, {"1d"})
        provider.kind = "fixture"
        with self.assertRaises(ProviderError):
            provider.bars("AAPL")

    def test_revision_receipt_metadata_must_match_hashed_content(self):
        provider = Providers(self.store, self.chart)
        revision = provider.bars("AAPL")["revision_id"]
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_revisions SET provider_asof='2020-01-01T00:00:00+00:00' WHERE id=?", (revision,))
        with self.assertRaises(DeskError) as caught:
            provider.bar_manifest(revision)
        self.assertEqual(caught.exception.status, 503)

    def test_failed_continuation_marks_history_unavailable_and_preserves_revision(self):
        at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        def page(*args):
            return {"bars": [{"t": at, "o": 10, "h": 11, "l": 9, "c": 10, "v": 100}], "next_page_token": "next"}
        with patch.dict(os.environ, {"ASTER_MARKET_DATA": "alpaca", "ASTER_ALPACA_KEY": "fixture", "ASTER_ALPACA_SECRET": "fixture"}):
            provider = Providers(self.store, page)
        provider.MAX_VENDOR_PAGES = 1
        original = provider.bars("AAPL")
        provider._transport = lambda *args: {"bars": None}
        provider.broker._transport = provider._transport
        with self.assertRaises(ProviderError):
            provider.continue_bars(original["revision_id"])
        self.assertEqual(provider.bar_manifest(original["revision_id"])["bar_count"], 1)
        self.assertFalse(next(a for a in provider.status()["historical_data"]["adapters"] if a["provider"] == "alpaca")["connected"])

    def test_empty_historical_response_cannot_overwrite_valid_history(self):
        provider = Providers(self.store, self.chart)
        original = provider.bars("AAPL")
        with self.store.transaction() as con:
            con.execute("UPDATE a_bar_cache SET fetched_at=?", ((datetime.now(UTC) - timedelta(minutes=2)).isoformat(),))
        provider._transport = lambda *args: {"chart": {"result": [{"timestamp": [], "indicators": {"quote": [{}]}}]}}
        retained = provider.bars("AAPL")
        self.assertTrue(retained["stale_cache"])
        self.assertEqual(retained["revision_id"], original["revision_id"])

    def test_transport_total_deadline_limits_and_paper_redirect_policy(self):
        with patch("backend.providers.bounded_http", return_value=(200, b'{"ok": true}')) as bounded:
            self.assertEqual(_request("POST", PAPER_URL + "/v2/orders", {"symbol": "AAPL"}), {"ok": True})
            self.assertEqual(bounded.call_args.kwargs, {"timeout_seconds": 8, "maximum_bytes": 8_000_000, "follow_redirects": False})
            _request("GET", "https://query1.finance.yahoo.com/chart")
            self.assertTrue(bounded.call_args.kwargs["follow_redirects"])
            _request("GET", "https://data.alpaca.markets/v2/stocks/AAPL/trades/latest")
            self.assertFalse(bounded.call_args.kwargs["follow_redirects"])
        with patch("backend.providers.bounded_http", return_value=(404, b'private broker response')):
            with self.assertRaises(ProviderError) as caught:
                _request("GET", PAPER_URL + "/v2/orders:by_client_order_id")
            self.assertEqual(caught.exception.status, 404)
            self.assertNotIn("private", str(caught.exception))
        with patch("backend.providers.bounded_http", side_effect=TimeoutError("private details")):
            with self.assertRaises(ProviderError) as caught:
                _request("GET", PAPER_URL)
            self.assertNotIn("private", str(caught.exception))

    def test_csv_transport_uses_deadline_and_size_bound_and_redacts_errors(self):
        with patch("backend.providers.bounded_http", return_value=(200, b'\xef\xbb\xbfDate,Close\n2025-01-01,10\n')) as bounded:
            self.assertTrue(_csv_request("https://stooq.com/q/d/l/").startswith("Date,"))
            self.assertEqual(bounded.call_args.kwargs, {"timeout_seconds": 8, "maximum_bytes": 8_000_000, "follow_redirects": True})
        with patch("backend.providers.bounded_http", side_effect=ValueError("oversized private body")):
            with self.assertRaises(ProviderError) as caught:
                _csv_request("https://stooq.com/q/d/l/")
            self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
