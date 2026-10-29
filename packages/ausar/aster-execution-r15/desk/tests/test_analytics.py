import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
from pathlib import Path

from backend.analytics import Analytics, completed_episodes, flow_adjusted_return, trade_metrics
from backend.providers import Providers, exchange_calendar
from backend.store import Store
from backend.trading import TradingDesk


class AnalyticsTests(unittest.TestCase):
    def test_funding_is_not_a_trading_return(self):
        data = [
            {"timestamp": "2026-10-05T20:00:00Z", "equity_cents": 10000, "missing_marks": 0, "stale_marks": 0},
            {"timestamp": "2026-10-06T15:00:00Z", "equity_cents": 11000, "missing_marks": 0, "stale_marks": 0},
            {"timestamp": "2026-10-06T15:00:02Z", "equity_cents": 21000, "missing_marks": 0, "stale_marks": 0},
            {"timestamp": "2026-10-06T20:00:00Z", "equity_cents": 23100, "missing_marks": 0, "stale_marks": 0},
        ]
        flows = [{"timestamp": "2026-10-06T15:00:01Z", "amount_cents": 10000}]
        self.assertAlmostEqual(flow_adjusted_return(data, flows), 21)
        data[2]["stale_marks"] = 1
        self.assertIsNone(flow_adjusted_return(data, flows))

    def test_only_completed_roundtrip_counts_as_a_win(self):
        def fill(rid, side, qty, pnl=0, fee=0):
            return {"id": rid, "book_id": "main", "symbol": "AAPL", "side": side, "quantity": qty, "realized_cents": pnl, "fee_cents": fee, "timestamp": "2026-10-06T15:00:00Z", "observed_at": "2026-10-06T15:00:00Z"}
        fills = [fill("1", "buy", 10, fee=100), fill("2", "sell", 5, pnl=500, fee=50)]
        self.assertEqual(completed_episodes(fills), [])
        fills.append(fill("3", "sell", 5, pnl=-300, fee=50))
        data = completed_episodes(fills)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["gross_pnl"], 2)
        self.assertEqual(data[0]["net_pnl"], 0)

    def test_flip_closes_old_episode_and_keeps_new_position_open(self):
        base = {"book_id": "main", "symbol": "AAPL", "fee_cents": 0, "timestamp": "2026-10-06T15:00:00Z", "observed_at": "2026-10-06T15:00:00Z"}
        fills = [{**base, "id": "1", "side": "sell", "quantity": 5, "realized_cents": 0}, {**base, "id": "2", "side": "buy", "quantity": 8, "realized_cents": 500}]
        episodes = completed_episodes(fills)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["direction"], "short")
        self.assertEqual(episodes[0]["net_pnl"], 5)

    def test_benchmarks_use_same_clean_eod_period_and_withhold_stale_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            with store.transaction() as con:
                con.execute("INSERT INTO p_equity(id,book_id,timestamp,cash_cents,equity_cents,market_value_cents,missing_marks,stale_marks) VALUES('first','main','2026-10-05T20:01:00+00:00',10000,10000,0,0,0)")
                con.execute("INSERT INTO p_equity(id,book_id,timestamp,cash_cents,equity_cents,market_value_cents,missing_marks,stale_marks) VALUES('last','main','2026-10-06T20:01:00+00:00',11000,11000,0,0,0)")
                for sym in ("QQQ", "SPY"):
                    self._archive(con, sym, ["2026-10-05", "2026-10-06"], [100, 105])
            result = Analytics(store, trading).snapshot()["books"][0]
            self.assertAlmostEqual(result["return_percent"], 10)
            self.assertEqual(len(result["benchmarks"]), 2)
            self.assertAlmostEqual(result["benchmarks"][0]["excess_return_points"], 5)
            self.assertEqual(result["benchmarks"][0]["baseline_date"], "2026-10-05")
            with store.transaction() as con:
                con.execute("UPDATE p_equity SET stale_marks=1 WHERE id='last'")
            self.assertIsNone(Analytics(store, trading).snapshot()["books"][0]["return_percent"])

    def test_net_trade_statistics_include_fees_flats_and_exact_cents(self):
        def fill(rid, side, qty, realized=0, fee=0):
            return {"id": rid, "book_id": "main", "symbol": "AAPL", "side": side,
                    "quantity": qty, "realized_cents": realized, "fee_cents": fee,
                    "timestamp": "2026-10-06T15:00:00Z", "observed_at": "2026-10-06T15:00:00Z"}
        # Net completed episodes: +8, -4, 0. An open +100 realized partial
        # is not a completed sample and cannot inflate expectancy.
        fills = [fill("1", "buy", 1, fee=100), fill("2", "sell", 1, 1000, 100),
                 fill("3", "buy", 1, fee=50), fill("4", "sell", 1, -300, 50),
                 fill("5", "buy", 1, fee=50), fill("6", "sell", 1, 100, 50),
                 fill("7", "buy", 2), fill("8", "sell", 1, 10000)]
        metrics = trade_metrics(completed_episodes(fills))
        self.assertAlmostEqual(metrics["net_expectancy"]["value"], 4 / 3)
        self.assertEqual(metrics["net_expectancy"]["samples"], 3)
        self.assertEqual(metrics["profit_factor"]["value"], 2)
        self.assertEqual(metrics["average_net_win"]["value"], 8)
        self.assertEqual(metrics["average_net_loss"]["value"], -4)
        only_wins = trade_metrics([{"net_pnl_cents": 100}])
        self.assertIsNone(only_wins["profit_factor"]["value"])
        self.assertIn("undefined", only_wins["profit_factor"]["reason"])
        self.assertIsNone(trade_metrics([])["net_expectancy"]["value"])
        self.assertIsNone(trade_metrics([{"net_pnl_cents": 100}], complete=False)["net_expectancy"]["value"])
        json.dumps(metrics, allow_nan=False)

    def test_flip_fee_allocation_preserves_total_cents(self):
        base = {"book_id": "main", "symbol": "AAPL", "timestamp": "2026-10-06T15:00:00Z", "observed_at": "2026-10-06T15:00:00Z"}
        fills = [{**base, "id": "1", "side": "sell", "quantity": 1, "realized_cents": 0, "fee_cents": 0},
                 {**base, "id": "2", "side": "buy", "quantity": 2, "realized_cents": 1000, "fee_cents": 1},
                 {**base, "id": "3", "side": "sell", "quantity": 1, "realized_cents": 500, "fee_cents": 0}]
        episodes = completed_episodes(fills)
        self.assertEqual(sum(e["net_pnl_cents"] for e in episodes), 1499)
        self.assertAlmostEqual(sum(e["fees"] for e in episodes), 0.01)

    def test_timezone_normalization_and_unbracketed_funding_withheld(self):
        rows = [{"timestamp": "2026-10-06T10:00:00-04:00", "equity_cents": 10000, "missing_marks": 0, "stale_marks": 0},
                {"timestamp": "2026-10-06T14:00:02Z", "equity_cents": 20000, "missing_marks": 0, "stale_marks": 0}]
        flows = [{"timestamp": "2026-10-06T14:00:01+00:00", "amount_cents": 10000}]
        self.assertEqual(flow_adjusted_return(rows, flows), 0)
        rows[-1]["timestamp"] = "2026-10-06T20:00:00Z"
        self.assertIsNone(flow_adjusted_return(rows, flows))
        rows[0]["stale_marks"] = 1
        self.assertIsNone(flow_adjusted_return(rows, []))

    def _revision(self, con, symbol, interval, bars, adjustment="raw OHLC", range="1d", observed="2026-10-06T15:00:00Z"):
        normalized = []
        for bar in bars:
            price = bar.get("close", bar.get("low"))
            normalized.append({"open": price, "high": price, "low": price, "close": price,
                               "volume": 0, **bar})
        payload = {"symbol": symbol, "range": range, "interval": interval, "provider": "fixture",
                   "source": "isolated synthetic fixture", "adjustment": adjustment,
                   "truncated": False, "bars": normalized}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        asof = normalized[-1]["timestamp"] if normalized else None
        con.execute("INSERT OR IGNORE INTO a_bar_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (digest, symbol, range, interval, "fixture", asof, observed, observed,
                     payload["source"], adjustment, digest, json.dumps(payload)))
        return {**payload, "revision_id": digest, "content_sha256": digest, "observed_at": observed,
                "provider_asof": asof, "fetched_at": observed, "cached": False, "stale_cache": False}

    def _archive(self, con, symbol, dates, prices, adjusted=True, range="1y", fetched="2026-10-08T01:00:00Z"):
        bars = []
        for day, price in zip(dates, prices):
            bar = {"timestamp": day + "T00:00:00+00:00", "close": float(price)}
            if adjusted:
                bar["adjusted_close"] = float(price)
            bars.append(bar)
        payload = self._revision(con, symbol, "1d", bars, range=range, observed=fetched)
        con.execute("INSERT OR REPLACE INTO a_bar_cache VALUES(?,?,?,?,?,?)", (symbol, range, "1d", "fixture", fetched, json.dumps(payload)))
        return payload["revision_id"]

    def _sessions(self, count):
        date, result = datetime(2026, 9, 1, 12, tzinfo=timezone.utc), []
        while len(result) < count:
            calendar = exchange_calendar(date)
            if calendar["is_session"]:
                result.append(calendar["session_date"])
            date += timedelta(days=1)
        return result

    def _valuation(self, con, rid, day, equity, stamp=None):
        stamp = stamp or day + "T20:01:00+00:00"
        con.execute("INSERT INTO p_equity(id,book_id,timestamp,cash_cents,equity_cents,market_value_cents,missing_marks,stale_marks) VALUES(?,'main',?,?,?,0,0,0)", (rid, stamp, equity, equity))

    def test_replicated_daily_exposure_beta_and_zero_variance_denominators(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = self._sessions(21)
            book, spy, qqq = Decimal(100000000), Decimal(100), Decimal(100)
            equities, spy_prices, qqq_prices = [int(book)], [spy], [qqq]
            for i in range(20):
                change = [Decimal("-0.02"), Decimal("0.01"), Decimal("0.03"), Decimal("0")][i % 4]
                book *= 1 + 2 * change
                spy *= 1 + change
                equities.append(int(book.quantize(Decimal(1))))
                spy_prices.append(spy)
                qqq_prices.append(qqq)  # Constant benchmark: undefined beta.
            with store.transaction() as con:
                for i, (day, equity) in enumerate(zip(days, equities)):
                    self._valuation(con, str(i), day, equity)
                self._archive(con, "SPY", days, spy_prices)
                self._archive(con, "QQQ", days, qqq_prices)
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertTrue(report["daily_return_coverage"]["contiguous_sessions"])
            self.assertEqual(report["metrics"]["sharpe_ratio"]["samples"], 20)
            self.assertIsNotNone(report["metrics"]["sharpe_ratio"]["value"])
            self.assertAlmostEqual(report["metrics"]["beta_spy"]["value"], 2, places=5)
            self.assertIsNone(report["metrics"]["beta_qqq"]["value"])
            self.assertIn("variance", report["metrics"]["beta_qqq"]["reason"])
            self.assertEqual(report["risk_assumptions"]["risk_free_annual_rate"], 0)
            self.assertFalse(report["profitability_claim"])
            json.dumps(report, allow_nan=False)
            with store.transaction() as con:
                con.execute("UPDATE p_equity SET cash_cents=100000000,equity_cents=100000000")
            metrics = Analytics(store, trading).snapshot()["books"][0]["metrics"]
            self.assertEqual(metrics["annualized_volatility_percent"]["value"], 0)
            self.assertIsNone(metrics["sharpe_ratio"]["value"])
            self.assertIn("variance", metrics["sharpe_ratio"]["reason"])

    def test_session_gap_is_not_annualized_as_a_daily_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = self._sessions(23)
            with store.transaction() as con:
                for i, day in enumerate(days):
                    if i != 10:
                        self._valuation(con, str(i), day, 10000 + i * 100)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100 + i for i in range(len(days))])
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertIsNotNone(report["return_percent"])  # Honest whole-period observation return.
            self.assertFalse(report["daily_return_coverage"]["contiguous_sessions"])
            for key in ("daily_volatility_percent", "annualized_volatility_percent", "sharpe_ratio", "beta_spy"):
                self.assertIsNone(report["metrics"][key]["value"])
                self.assertIn("Missing exchange sessions", report["metrics"][key]["reason"])

    def test_finite_vendor_prices_cannot_overflow_benchmark_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = ["2026-10-05", "2026-10-06"]
            with store.transaction() as con:
                for i, day in enumerate(days):
                    self._valuation(con, str(i), day, 10000 + i * 1000)
                # Individually finite prices can still produce an infinite ratio.
                self._archive(con, "SPY", days, [1e-308, 1e308])
                self._archive(con, "QQQ", days, [100, 105])
            response = Analytics(store, trading).snapshot()
            report = response["books"][0]
            self.assertIsNone(report["return_percent"])
            self.assertIn("Nonfinite benchmark", report["coverage"])
            self.assertIsNone(report["metrics"]["beta_spy"]["value"])
            json.dumps(response, allow_nan=False)

    def test_cashflow_adjusted_drawdown_retains_ruin_and_excludes_deposit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = ["2026-10-05", "2026-10-06", "2026-10-07"]
            with store.transaction() as con:
                self._valuation(con, "baseline", days[0], 10000)
                self._valuation(con, "gain", days[1], 11000, "2026-10-06T15:00:00Z")
                self._valuation(con, "deposit", days[1], 21000, "2026-10-06T15:00:02Z")
                con.execute("INSERT INTO p_fundings VALUES('f','main','fixture',10000,'2026-10-06T15:00:01Z')")
                self._valuation(con, "drawdown", days[1], 18900)
                self._valuation(con, "zero-before-close", days[2], 0, "2026-10-07T15:00:00Z")
                self._valuation(con, "zero-again", days[2], 0, "2026-10-07T16:00:00Z")
                self._valuation(con, "ruin", days[2], 0)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100, 101, 102])
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertEqual(report["return_percent"], -100)
            self.assertEqual(report["metrics"]["max_drawdown_percent"]["value"], 100)
            with store.transaction() as con:
                con.execute("DELETE FROM p_equity WHERE id IN ('ruin','zero-before-close','zero-again')")
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertAlmostEqual(report["return_percent"], -1)
            self.assertAlmostEqual(report["metrics"]["max_drawdown_percent"]["value"], 10)

    def test_unitized_nav_records_negative_equity_without_hiding_drawdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = ["2026-10-05", "2026-10-06", "2026-10-07"]
            with store.transaction() as con:
                self._valuation(con, "baseline", days[0], 10000)
                self._valuation(con, "zero", days[1], 0)
                self._valuation(con, "negative", days[2], -1000, "2026-10-07T16:00:00Z")
                self._valuation(con, "recovery", days[2], 5000)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100, 101, 102])
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertEqual(report["return_percent"], -50)
            self.assertEqual(report["metrics"]["max_drawdown_percent"]["value"], 110)
            self.assertIsNone(report["metrics"]["sharpe_ratio"]["value"])
            self.assertIn("Nonpositive", report["metrics"]["sharpe_ratio"]["reason"])

    def test_overnight_valuation_does_not_become_exchange_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = ["2026-10-05", "2026-10-06"]
            with store.transaction() as con:
                self._valuation(con, "baseline", days[0], 10000)
                self._valuation(con, "overnight", days[1], 50000, "2026-10-06T23:00:00Z")
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100, 105])
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertIsNone(report["return_percent"])
            self.assertIsNone(report["metrics"]["sharpe_ratio"]["value"])

    def test_excursion_requires_exact_complete_raw_intraday_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            analytics = Analytics(store, trading)
            fills = {"a": {"id": "a", "quantity": "1", "price": "100", "timestamp": "2026-10-06T14:00:00Z"},
                     "b": {"id": "b", "quantity": "1", "price": "101", "timestamp": "2026-10-06T14:02:00Z"}}
            episode = {"symbol": "AAPL", "direction": "long", "opened_at": fills["a"]["timestamp"], "closed_at": fills["b"]["timestamp"], "fill_ids": ["a", "b"]}
            bars = [{"timestamp": "2026-10-06T14:00:00Z", "low": 98, "high": 102},
                    {"timestamp": "2026-10-06T14:01:00Z", "low": 99, "high": 103}]
            def revision(con, interval, body):
                con.execute("DELETE FROM a_bar_revisions WHERE symbol='AAPL'")
                self._revision(con, "AAPL", interval, body)
            with store.transaction() as con:
                # Daily high999 must never count as the intraday holding maximum.
                revision(con, "1d", [{"timestamp": "2026-10-06T13:30:00Z", "low": 1, "high": 999}])
                self.assertEqual(analytics._excursion(con, episode, fills)["status"], "withheld")
                revision(con, "1m", bars)
                result = analytics._excursion(con, episode, fills)
                self.assertEqual(result["mfe_percent"], 3)
                self.assertEqual(result["mae_percent"], 2)
                self.assertEqual(result["finality"], "provisional_vendor_observation")
                self.assertIn("not certified", result["scope"])
                episode["direction"] = "short"
                self.assertEqual(analytics._excursion(con, episode, fills)["mfe_percent"], 2)
                self.assertEqual(analytics._excursion(con, episode, fills)["mae_percent"], 3)
                episode["opened_at"] = "2026-10-06T14:00:30Z"
                self.assertEqual(analytics._excursion(con, episode, fills)["status"], "withheld")
                episode["opened_at"] = fills["a"]["timestamp"]
                revision(con, "1m", bars[:1])
                self.assertEqual(analytics._excursion(con, episode, fills)["status"], "withheld")
                revision(con, "1m", bars)
                fills["b"]["timestamp"] = None
                self.assertEqual(analytics._excursion(con, episode, fills)["status"], "withheld")

    def test_excursion_rejects_ambiguous_raw_basis_and_finite_price_ratio_overflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            analytics = Analytics(store, trading)
            fills = {"a": {"quantity": "1", "price": ".01", "timestamp": "2026-10-06T14:00:00Z"},
                     "b": {"quantity": "1", "price": ".02", "timestamp": "2026-10-06T14:01:00Z"}}
            episode = {"symbol": "AAPL", "direction": "long", "opened_at": fills["a"]["timestamp"],
                       "closed_at": fills["b"]["timestamp"], "fill_ids": ["a", "b"]}
            bars = {"bars": [{"timestamp": fills["a"]["timestamp"], "low": ".01", "high": ".02"}], "truncated": False}
            with store.transaction() as con:
                self._revision(con, "AAPL", "1m", bars["bars"], adjustment="split-adjusted OHLC; raw basis unavailable")
                result = analytics._excursion(con, episode, fills)
                self.assertEqual(result["status"], "withheld")
                self.assertIsNone(result["mfe_percent"])
                self.assertIsNone(result["mae_percent"])
                con.execute("DELETE FROM a_bar_revisions WHERE symbol='AAPL'")
                self._revision(con, "AAPL", "1m", bars["bars"])
                self.assertEqual(analytics._excursion(con, episode, fills)["status"], "available")
                # Finite positive raw OHLC does not guarantee a finite excursion.
                bars["bars"][0]["high"] = 1e308
                con.execute("DELETE FROM a_bar_revisions WHERE symbol='AAPL'")
                self._revision(con, "AAPL", "1m", bars["bars"])
                result = analytics._excursion(con, episode, fills)
                self.assertEqual(result["status"], "withheld")
                self.assertIsNone(result["mfe_percent"])
                self.assertIsNone(result["mae_percent"])
                self.assertIn("Nonfinite", result["reason"])
                json.dumps(result, allow_nan=False)

    def test_empty_and_broker_reports_withhold_unverified_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading = TradingDesk(store)
            trading.create_book({"name": "Paper provider", "kind": "forward", "broker": "alpaca"})
            report = Analytics(store, trading).snapshot()
            self.assertEqual(report["strategy_count"], 0)
            self.assertEqual(report["completed_trades"], [])
            for book in report["books"]:
                self.assertTrue(all(m["value"] is None and m["reason"] for m in book["metrics"].values()))
                if book["book_name"] == "Paper provider":
                    self.assertIsNone(book["closed_trade_net_pnl"])
                    self.assertIsNone(book["win_rate_percent"])
            json.dumps(report, allow_nan=False)

    def test_shorter_chart_refresh_does_not_shrink_aligned_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = self._sessions(21)
            with store.transaction() as con:
                for i, day in enumerate(days):
                    self._valuation(con, str(i), day, 10000 + i * 100)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100 + i for i in range(21)])
                    # This is a newer, valid short chart revision, not a new
                    # performance baseline selected by the operator.
                    self._archive(con, sym, days[-2:], [119, 120], range="5d", fetched="2026-10-08T02:00:00Z")
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertEqual(report["matched_sessions"], 21)
            self.assertAlmostEqual(report["return_percent"], 20)
            self.assertEqual(report["metrics"]["sharpe_ratio"]["samples"], 20)
            self.assertTrue(all(b["baseline_date"] == days[0] for b in report["benchmarks"]))

    def test_revision_pair_maximizes_common_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = self._sessions(6)
            with store.transaction() as con:
                for i, day in enumerate(days):
                    self._valuation(con, str(i), day, 10000 + i * 100)
                self._archive(con, "SPY", days[:4], [100, 101, 102, 103])
                self._archive(con, "SPY", days[3:], [103, 104, 105], range="5d")
                self._archive(con, "QQQ", days[2:], [102, 103, 104, 105])
                self._archive(con, "QQQ", days[:3], [100, 101, 102], range="5d")
            report = Analytics(store, trading).snapshot()["books"][0]
            # Independently taking each largest cache would produce only two
            # common days. Whole-revision pair selection retains three.
            self.assertEqual(report["matched_sessions"], 3)
            self.assertEqual(len(report["benchmarks"]), 2)

    def test_max_history_before_calendar_start_preserves_desk_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            days = ["2026-10-05", "2026-10-06"]
            with store.transaction() as con:
                for i, day in enumerate(days):
                    self._valuation(con, str(i), day, 10000 + i * 1000)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, ["1999-03-10", *days], [50, 100, 105], range="max")
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertEqual(report["matched_sessions"], 2)
            self.assertAlmostEqual(report["return_percent"], 10)
            self.assertTrue(all(b["baseline_date"] == days[0] for b in report["benchmarks"]))

    def test_corrupted_daily_cache_and_revision_are_withheld(self):
        for corruption in ("cache", "revision", "metadata", "malformed_json", "nonobject_json"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                store = Store(Path(tmp) / "desk.sqlite")
                trading, providers = TradingDesk(store), Providers(store)
                days = ["2026-10-05", "2026-10-06"]
                with store.transaction() as con:
                    for i, day in enumerate(days):
                        self._valuation(con, str(i), day, 10000 + i * 1000)
                    for sym in ("SPY", "QQQ"):
                        rid = self._archive(con, sym, days, [100, 105])
                    if corruption == "metadata":
                        con.execute("UPDATE a_bar_revisions SET adjustment='split-adjusted' WHERE id=?", (rid,))
                    elif corruption == "malformed_json":
                        con.execute("UPDATE a_bar_cache SET data='broken JSON' WHERE symbol='QQQ'")
                    elif corruption == "nonobject_json":
                        con.execute("UPDATE a_bar_cache SET data='[]' WHERE symbol='QQQ'")
                    else:
                        table = "a_bar_cache" if corruption == "cache" else "a_bar_revisions"
                        row = con.execute("SELECT data FROM " + table + " WHERE symbol='QQQ'").fetchone()
                        payload = json.loads(row["data"])
                        payload["bars"][-1]["close"] = 999
                        con.execute("UPDATE " + table + " SET data=? WHERE symbol='QQQ'", (json.dumps(payload),))
                response = Analytics(store, trading).snapshot()
                report = response["books"][0]
                self.assertIsNone(report["return_percent"])
                self.assertIn("integrity", report["coverage"])
                json.dumps(response, allow_nan=False)

    def test_excursion_rejects_corruption_and_hash_bound_incoherent_ohlc(self):
        for corruption in ("data", "metadata", "incoherent_ohlc", "invalid_timestamp", "invalid_receipt_time"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                store = Store(Path(tmp) / "desk.sqlite")
                trading, providers = TradingDesk(store), Providers(store)
                fills = {"a": {"quantity": "1", "price": "100", "timestamp": "2026-10-06T14:00:00Z"},
                         "b": {"quantity": "1", "price": "101", "timestamp": "2026-10-06T14:01:00Z"}}
                episode = {"symbol": "AAPL", "direction": "long", "opened_at": fills["a"]["timestamp"],
                           "closed_at": fills["b"]["timestamp"], "fill_ids": ["a", "b"]}
                bars = [{"timestamp": fills["a"]["timestamp"], "open": 100, "close": 101, "low": 98, "high": 102}]
                with store.transaction() as con:
                    if corruption == "incoherent_ohlc":
                        bars[0]["low"] = 102  # Valid digest, invalid OHLC range.
                    elif corruption == "invalid_timestamp":
                        bars[0]["timestamp"] = None
                    payload = self._revision(con, "AAPL", "1m", bars)
                    if corruption == "data":
                        bars[0]["high"] = 999
                        con.execute("UPDATE a_bar_revisions SET data=?", (json.dumps({**payload, "bars": bars}),))
                    elif corruption == "metadata":
                        con.execute("UPDATE a_bar_revisions SET source='different provenance'")
                    elif corruption == "invalid_receipt_time":
                        con.execute("UPDATE a_bar_revisions SET observed_at='invalid'")
                    result = Analytics(store, trading)._excursion(con, episode, fills)
                    self.assertEqual(result["status"], "withheld")
                    self.assertIsNone(result["mfe_percent"])
                    json.dumps(result, allow_nan=False)

    def test_ambiguous_funding_timestamps_and_redeemed_units_are_withheld(self):
        rows = [{"timestamp": "2026-10-06T14:00:00Z", "equity_cents": 10000, "missing_marks": 0, "stale_marks": 0},
                {"timestamp": "2026-10-06T14:00:02Z", "equity_cents": 20000, "missing_marks": 0, "stale_marks": 0}]
        for stamp in (rows[0]["timestamp"], rows[1]["timestamp"]):
            self.assertIsNone(flow_adjusted_return(rows, [{"timestamp": stamp, "amount_cents": 10000}]))
        rows[-1]["equity_cents"] = 0
        self.assertIsNone(flow_adjusted_return(rows, [{"timestamp": "2026-10-06T14:00:01Z", "amount_cents": -10000}]))

    def test_broker_flattening_sequences_do_not_expose_verified_net_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading = TradingDesk(store)
            book = trading.create_book({"name": "Unverified broker fixture", "kind": "forward", "broker": "alpaca"})
            Providers(store)
            with store.transaction() as con:
                for i, (side, realized) in enumerate((("buy", 0), ("sell", 5000))):
                    stamp = f"2026-10-06T14:0{i}:00Z"
                    con.execute("INSERT INTO p_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                ("f" + str(i), "i" + str(i), book["id"], "AAPL", side, "1", "100", 10000,
                                 0, realized, "synthetic" + str(i), stamp, stamp, "isolated synthetic broker delta",
                                 None, None, 1))
                self._revision(con, "AAPL", "1m", [{"timestamp": "2026-10-06T14:00:00Z", "open": 100,
                    "close": 100, "low": 99, "high": 102}])
            result = Analytics(store, trading).snapshot()
            report = next(b for b in result["books"] if b["book_id"] == book["id"])
            self.assertIsNone(report["closed_roundtrips"])
            self.assertEqual(report["recorded_flattening_sequences"], 1)
            self.assertIsNone(report["metrics"]["net_expectancy"]["value"])
            episode = result["completed_trades"][0]
            self.assertEqual(episode["accounting_status"], "unverified_broker_basis_and_fees")
            for key in ("gross_pnl", "fees", "net_pnl", "net_pnl_cents"):
                self.assertIsNone(episode[key])
            self.assertEqual(episode["excursion"]["status"], "withheld")
            self.assertIn("Broker opening inventory", episode["excursion"]["reason"])
            json.dumps(result, allow_nan=False)

    def test_clock_rollback_preserves_causal_episodes_and_withholds_time_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, providers = TradingDesk(store), Providers(store)
            with store.transaction() as con:
                for i, (side, quantity, realized, fee) in enumerate((("buy", "1", 0, 1),
                        ("sell", "2", 500, 3), ("buy", "1", 200, 2))):
                    stamp = (datetime(2026, 10, 6, 15, tzinfo=timezone.utc) - timedelta(minutes=i)).isoformat()
                    con.execute("INSERT INTO p_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                ("f" + str(i), "i" + str(i), "main", "AAPL", side, quantity, "100", 10000,
                                 fee, realized, "synthetic" + str(i), stamp, stamp, "isolated clock-rollback fixture", None, None, 1))
                days = ["2026-10-05", "2026-10-06"]
                for i, day in enumerate(days):
                    self._valuation(con, str(i), day, 10000 + i * 1000)
                for sym in ("SPY", "QQQ"):
                    self._archive(con, sym, days, [100, 105])
            result = Analytics(store, trading).snapshot()
            report = result["books"][0]
            self.assertEqual(report["closed_roundtrips"], 2)
            self.assertEqual([e["direction"] for e in result["completed_trades"]], ["long", "short"])
            self.assertAlmostEqual(report["closed_trade_net_pnl"], 6.94)
            self.assertFalse(report["clock_coverage"]["fill_timestamps_monotonic"])
            self.assertIsNone(report["return_percent"])
            self.assertIn("moved backwards", report["coverage"])
            for episode in result["completed_trades"]:
                self.assertIsNone(episode["duration_seconds"])
                self.assertEqual(episode["excursion"]["status"], "withheld")
            json.dumps(result, allow_nan=False)

    def test_equity_and_funding_append_clock_rollback_is_not_hidden_by_sorting(self):
        for ledger in ("equity", "funding"):
            with self.subTest(ledger=ledger), tempfile.TemporaryDirectory() as tmp:
                store = Store(Path(tmp) / "desk.sqlite")
                trading, providers = TradingDesk(store), Providers(store)
                days = ["2026-10-05", "2026-10-06"]
                with store.transaction() as con:
                    self._valuation(con, "baseline", days[0], 10000)
                    self._valuation(con, "close", days[1], 11000)
                    if ledger == "equity":
                        self._valuation(con, "backward-clock", days[1], 12000, stamp="2026-10-06T15:00:00Z")
                    else:
                        con.execute("INSERT INTO p_fundings VALUES('later','main','later',500,'2026-10-06T15:00:01Z')")
                        con.execute("INSERT INTO p_fundings VALUES('earlier','main','earlier',1000,'2026-10-06T14:00:01Z')")
                    for sym in ("SPY", "QQQ"):
                        self._archive(con, sym, days, [100, 105])
                report = Analytics(store, trading).snapshot()["books"][0]
                self.assertFalse(report["clock_coverage"][ledger + "_timestamps_monotonic"])
                self.assertIsNone(report["return_percent"])
                self.assertIn("moved backwards", report["coverage"])


if __name__ == "__main__":
    unittest.main()
