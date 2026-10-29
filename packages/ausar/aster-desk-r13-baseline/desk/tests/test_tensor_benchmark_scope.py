"""Strategy NAV must be compared against the same dividend-return scope."""
import tempfile
import hashlib
import json
import unittest
from pathlib import Path

from backend.analytics import Analytics
from backend.providers import Providers
from backend.store import Store
from backend.tensor_runtime import TensorRuntimeManager
from backend.trading import TradingDesk
from tests import test_analytics as archive_fixtures


class TensorBenchmarkScopeTests(unittest.TestCase):
    def test_action_affected_raw_fill_statistics_are_withheld(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "action-scope.sqlite")
            trading = TradingDesk(store)
            definition = json.dumps({"kind": "split", "numerator": 2, "denominator": 1})
            with store.transaction() as con:
                con.execute("INSERT INTO a_strategy_actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
                    "action-scope-fixture", "main", "AMD", "split", "2026-10-06T13:30:00+00:00", definition,
                    hashlib.sha256(definition.encode()).hexdigest(), "Synthetic scope fixture", "2026-10-06T14:00:00+00:00", "applied", "{}", "2026-10-06T14:00:00+00:00"))
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertIsNone(report["closed_roundtrips"])
            self.assertIsNone(report["closed_trade_net_pnl"])
            self.assertEqual(report["trade_accounting_coverage"]["status"], "withheld")
            self.assertIsNone(report["metrics"]["net_expectancy"]["value"])
            self.assertIn("action-normalized", report["metrics"]["net_expectancy"]["reason"])

    def test_strategy_owned_nav_requires_adjusted_benchmarks(self):
        fixtures = archive_fixtures.AnalyticsTests("test_funding_is_not_a_trading_return")
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "scope.sqlite")
            trading = TradingDesk(store)
            manager = TensorRuntimeManager(store, trading, Providers(store))
            manager.install({"id": "benchmark-scope-fixture", "sleeve": "H1STATE", "book_id": "main", "symbols": ["AMD"]})
            with store.transaction() as con:
                con.execute("INSERT INTO p_equity VALUES('first','main','2026-10-05T20:01:00+00:00',10000,10000,0,0,0)")
                con.execute("INSERT INTO p_equity VALUES('last','main','2026-10-06T20:01:00+00:00',11000,11000,0,0,0)")
                for sym in ("QQQ", "SPY"):
                    fixtures._archive(con, sym, ["2026-10-05", "2026-10-06"], [100, 105], adjusted=False)
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertIsNone(report["return_percent"])
            self.assertEqual(report["benchmarks"], [])
            self.assertIn("requires adjusted", report["coverage"])
            with store.transaction() as con:
                for sym in ("QQQ", "SPY"):
                    fixtures._archive(con, sym, ["2026-10-05", "2026-10-06"], [100, 105], adjusted=True)
            report = Analytics(store, trading).snapshot()["books"][0]
            self.assertAlmostEqual(report["return_percent"], 10)
            self.assertEqual(len(report["benchmarks"]), 2)
            self.assertTrue(all(b["scope"] == "Vendor adjusted-close return" for b in report["benchmarks"]))


if __name__ == "__main__":
    unittest.main()
