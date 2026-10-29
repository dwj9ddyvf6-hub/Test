"""Actual HTTP boundary and lifespan-worker checks on isolated databases."""
import tempfile
import time
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app


class HTTPTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name) / "http.sqlite", start_worker=False)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_contract_initial_snapshot_and_errors(self):
        snapshot = self.client.get("/api/desk")
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual(snapshot.json()["desk"]["name"], "Aster Desk")
        self.assertEqual(self.client.get("/api/strategies").json(), [])
        for path, payload in (
            ("/api/account/funding", {"amount": 0, "client_id": "bad"}),
            ("/api/tasks", {"kind": "strategy"}),
            ("/api/quotes", {"symbol": "AAPL", "price": 10, "as_of": "2026-01-01T00:00:00", "source": "Manual"}),
            ("/api/orders", {"symbol": "AAPL", "quantity": 1, "side": "buy", "client_id": "missing-quote"}),
        ):
            response = self.client.post(path, json=payload)
            self.assertIn(response.status_code, (409, 422))
            self.assertIn("detail", response.json())
        self.assertEqual(self.client.get("/api/nonexistent").status_code, 404)
        self.assertEqual(self.client.post("/api/orders/not-found/approve", json={}).status_code, 404)

    def test_nonfinite_json_returns_validation_detail_without_internal_failure(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            response = self.client.post("/api/account/funding", content='{"amount":' + token + ',"client_id":"invalid"}', headers={"Content-Type": "application/json"})
            self.assertEqual(response.status_code, 422)
            self.assertIn("detail", response.json())
        self.assertEqual(self.client.get("/api/desk").json()["account"]["cash"], 0)

    def test_operator_paper_roundtrip_and_export(self):
        funding = {"amount": 100, "client_id": "http-fund"}
        first = self.client.post("/api/account/funding", json=funding)
        self.assertEqual(first.json(), self.client.post("/api/account/funding", json=funding).json())
        self.assertEqual(self.client.post("/api/watchlist", json={"symbol": "aapl"}).json()["symbol"], "AAPL")
        quote = {"symbol": "AAPL", "price": 10, "as_of": datetime.now(timezone.utc).isoformat(), "source": "Manually observed test quote"}
        self.assertEqual(self.client.post("/api/quotes", json=quote).status_code, 200)
        order = self.client.post("/api/orders", json={"symbol": "AAPL", "side": "buy", "quantity": 2, "type": "market", "client_id": "http-order"}).json()
        self.assertEqual(order["status"], "pending_review")
        self.assertEqual(self.client.get("/api/desk").json()["fills"], [])
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/approve", json={}).json()["status"], "filled")
        s = self.client.get("/api/desk").json()
        self.assertEqual(s["account"]["cash"], 80)
        self.assertEqual(s["positions"][0]["quantity"], 2)
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/cancel", json={}).status_code, 409)
        exported = self.client.get("/api/export")
        self.assertIn("attachment", exported.headers["content-disposition"])
        self.assertEqual(len(exported.json()["tables"]["fills"]), 1)
        self.assertEqual(exported.json()["strategy_count"], 0)

    def test_settings_runtime_and_queue_controls(self):
        response = self.client.patch("/api/settings", json={"quote_max_age_seconds": 120, "heartbeat_seconds": 3, "cycle_interval_seconds": 10})
        self.assertEqual(response.json()["quote_max_age_seconds"], 120)
        self.assertEqual(self.client.patch("/api/settings", json={"cycle_interval_seconds": 0}).status_code, 422)
        cycle = self.client.post("/api/runtime/cycle", json={}).json()
        self.assertEqual(self.client.post("/api/runtime/cycle", json={}).json()["id"], cycle["id"])
        self.assertEqual(self.client.post(f"/api/tasks/{cycle['id']}/cancel", json={}).json()["status"], "cancelled")
        self.assertTrue(self.client.post("/api/runtime", json={"running": True}).json()["running"])
        self.assertFalse(self.client.post("/api/runtime", json={"running": False}).json()["running"])
        health = self.client.get("/api/health").json()
        self.assertFalse(health["worker"]["alive"])
        self.assertEqual(health["database"]["status"], "ok")
        self.assertEqual(health["reasoning"]["reachability"], "not checked")

    def test_real_background_worker_runs_manual_queue_when_recurring_paused(self):
        application = create_app(Path(self.temp.name) / "threaded.sqlite")
        with TestClient(application) as client:
            task = client.post("/api/tasks", json={"kind": "research_note", "instructions": "Verbatim operator evidence", "symbol": "aapl"}).json()
            deadline = time.monotonic() + 5
            result = None
            while time.monotonic() < deadline:
                snapshot = client.get("/api/desk").json()
                result = next(t for t in snapshot["tasks"] if t["id"] == task["id"])
                if result["status"] in {"completed", "failed"}:
                    break
                time.sleep(0.05)
            self.assertEqual(result["status"], "completed")
            self.assertIn("Verbatim operator evidence", result["result"])
            self.assertFalse(snapshot["desk"]["runtime"]["running"])
            self.assertTrue(client.get("/api/health").json()["worker"]["alive"])
            self.assertEqual(snapshot["orders"], [])
        self.assertFalse(application.state.worker.thread.is_alive())

    def test_joined_autonomous_contract_keeps_manual_book_separate(self):
        snapshot = self.client.get("/api/autonomy").json()
        self.assertTrue({"trading", "runtime", "lab", "research", "reports", "notifications"}.issubset(snapshot))
        self.assertEqual(snapshot["trading"]["books"][0]["account"]["cash"], 0)
        self.assertEqual(snapshot["trading"]["strategy_count"], 0)
        funding = self.client.post("/api/books/main/funding", json={"amount": 100, "client_id": "auto-fund"})
        self.assertEqual(funding.status_code, 200)
        self.assertEqual(self.client.get("/api/desk").json()["account"]["cash"], 0)
        quote = {"symbol": "AAPL", "price": 10, "as_of": datetime.now(timezone.utc).isoformat(), "source": "Manual test"}
        self.client.post("/api/quotes", json=quote)
        order = self.client.post("/api/intents", json={"book_id": "main", "symbol": "AAPL", "side": "buy", "quantity": 2, "order_type": "market", "time_in_force": "gtc", "client_id": "auto-intent"}).json()
        self.assertEqual(order["status"], "queued")
        self.assertEqual(self.client.post(f"/api/intents/{order['id']}/cancel", json={}).json()["status"], "cancelled")
        exported = self.client.get("/api/export").json()
        self.assertEqual(len(exported["autonomous_tables"]["p_intents"]), 1)
        self.assertNotIn("n_subscriptions", exported["autonomous_tables"])
        self.assertEqual(self.client.get("/api/health?deep=true").json()["journal_integrity"]["status"], "ok")

    def test_portfolio_policy_operator_route_is_versioned_and_exported(self):
        initial = self.client.get("/api/autonomy").json()["trading"]["global_policy"]
        updated = self.client.patch("/api/portfolio-policy", json={"gross_exposure_cap": 100, "symbol_exposure_cap": 50, "expected_hash": initial["hash"]})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["version"], initial["version"] + 1)
        stale = self.client.patch("/api/portfolio-policy", json={"gross_exposure_cap": 80, "expected_hash": initial["hash"]})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(self.client.patch("/api/portfolio-policy", json={"strategy": "invalid"}).status_code, 422)
        snapshot = self.client.get("/api/autonomy").json()["trading"]
        self.assertEqual(snapshot["global_policy"]["gross_exposure_cap"], 100)
        self.assertEqual(snapshot["global_exposure"]["scope"], "autonomous_books_only")
        self.assertEqual(snapshot["global_exposure"]["gross_exposure"], 0)
        exported = self.client.get("/api/export").json()
        self.assertEqual(len(exported["autonomous_tables"]["p_portfolio_policy_history"]), 2)

    def test_book_policy_route_fences_stale_operator_forms(self):
        initial = self.client.get("/api/autonomy").json()["trading"]["books"][0]
        first = self.client.patch("/api/books/main", json={"policy": {"halted": True}, "expected_hash": initial["policy_hash"]})
        self.assertEqual(first.status_code, 200)
        stale = self.client.patch("/api/books/main", json={"policy": {"halted": False}, "expected_hash": initial["policy_hash"]})
        self.assertEqual(stale.status_code, 409)
        self.assertTrue(self.client.get("/api/autonomy").json()["trading"]["books"][0]["policy"]["halted"])
        for payload in ({"policy": {}, "expected_hash": 12}, {"policy": {}, "ignored": True}):
            self.assertEqual(self.client.patch("/api/books/main", json=payload).status_code, 422)
        # Existing flat policy clients still work.
        self.assertEqual(self.client.patch("/api/books/main", json={"halted": False, "expected_hash": first.json()["policy_hash"]}).status_code, 200)

    def test_broker_snapshot_and_export_withhold_unverified_realized_accounting(self):
        from tests.test_trading import FakeBroker, FakeProviders
        book = self.client.post("/api/books", json={"name": "Isolated paper broker", "broker": "alpaca"}).json()
        broker = FakeBroker()
        broker.cash = "990"
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        observed_at = datetime.now(timezone.utc).isoformat()
        broker.remote_orders = [{"id": "http-coverage-order", "client_order_id": "aster_http_coverage", "symbol": "AAPL", "side": "buy", "qty": "1", "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": "1", "filled_avg_price": "10", "submitted_at": observed_at, "filled_at": observed_at}]
        quote = {"symbol": "AAPL", "price": 12, "as_of": datetime.now(timezone.utc).isoformat(), "source": "Isolated broker accounting quote"}
        self.assertEqual(self.client.post("/api/quotes", json=quote).status_code, 200)
        self.app.state.trading.reconcile(FakeProviders(broker))
        snapshot = self.client.get("/api/autonomy").json()["trading"]
        account = next(item["account"] for item in snapshot["books"] if item["id"] == book["id"])
        position = next(item for item in snapshot["positions"] if item["book_id"] == book["id"])
        self.assertEqual(account["cash"], 990)
        self.assertIsNone(account["realized_pnl"])
        self.assertEqual(account["realized_pnl_coverage"]["status"], "withheld")
        self.assertEqual(position["average_cost"], 10)
        self.assertEqual(position["cost_basis_coverage"]["status"], "known")
        self.assertEqual(position["unrealized_pnl"], 2)
        self.assertIsNone(position["realized_pnl"])
        self.assertIsNone(snapshot["fills"][0]["realized_pnl"])
        self.assertIsNone(snapshot["fills"][0]["realized_cents"])
        self.assertEqual(snapshot["fills"][0]["realized_pnl_coverage"]["status"], "withheld")
        self.assertEqual(snapshot["broker_accounting_coverage"]["status"], "withheld")
        exported = self.client.get("/api/export").json()
        self.assertIn("Internal reconstruction estimates", exported["accounting_coverage"]["raw_realized_cents"]["broker_books"])
        self.assertEqual(exported["accounting_coverage"]["broker"]["status"], "withheld")
        self.assertIn("cost_basis_coverage", exported["accounting_coverage"]["raw_position_basis"])
        self.assertEqual(exported["autonomous_tables"]["p_fills"][0]["realized_cents"], 0)
        self.assertIsNone(exported["trading"]["fills"][0]["realized_pnl"])

    def test_export_replaces_initial_manual_read_with_coherent_raw_evidence(self):
        original_export = self.app.state.store.export
        def interleaved_export(reasoning):
            old = original_export(reasoning)
            # Simulate an authorized write after the initial metadata lookup.
            self.app.state.store.fund(Decimal("50"), "export-interleaving-manual")
            self.app.state.trading.fund_book("main", Decimal("75"), "export-interleaving-autonomous")
            return old
        with patch.object(self.app.state.store, "export", side_effect=interleaved_export):
            exported = self.client.get("/api/export").json()
        self.assertEqual(exported["tables"]["account"][0]["cash_cents"], 5000)
        self.assertEqual(exported["autonomous_tables"]["p_books"][0]["cash_cents"], 7500)
        types = [event["event_type"] for event in exported["tables"]["events"]]
        self.assertIn("paper_funding", types)
        self.assertIn("independent_book_funding", types)
        self.assertIn("One SQLite read transaction", exported["consistency"]["raw_tables"])

    def test_lifespan_cleans_up_worker_when_supervisor_start_fails(self):
        application = create_app(Path(self.temp.name) / "failed-start.sqlite")
        with patch.object(application.state.worker, "start"), patch.object(application.state.worker, "stop") as worker_stop, patch.object(application.state.autonomy, "start", side_effect=RuntimeError("fixture start failure")), patch.object(application.state.autonomy, "stop") as autonomy_stop:
            with self.assertRaisesRegex(RuntimeError, "fixture start failure"):
                with TestClient(application):
                    pass
            autonomy_stop.assert_called_once()
            worker_stop.assert_called_once()

    def test_lifespan_cleans_up_worker_when_supervisor_stop_fails(self):
        application = create_app(Path(self.temp.name) / "failed-stop.sqlite")
        with patch.object(application.state.worker, "start"), patch.object(application.state.worker, "stop") as worker_stop, patch.object(application.state.autonomy, "start"), patch.object(application.state.autonomy, "stop", side_effect=RuntimeError("fixture stop failure")):
            with self.assertRaisesRegex(RuntimeError, "fixture stop failure"):
                with TestClient(application):
                    pass
            worker_stop.assert_called_once()

    def test_immutable_market_revision_routes_page_saved_evidence_without_fetching(self):
        provider = self.app.state.autonomy.providers
        result = provider._save_bars("AAPL", "1mo", "1d", {"provider": "fixture", "source": "Isolated historical fixture", "adjustment": "raw fixture", "bars": [{"timestamp": f"2026-01-0{day}T00:00:00+00:00", "open": 10, "high": 12, "low": 9, "close": 11, "volume": 100} for day in (1, 2, 3)]})
        revision = result["revision_id"]
        manifest = self.client.get(f"/api/market/revisions/{revision}/manifest").json()
        self.assertTrue(manifest["immutable"])
        self.assertEqual(manifest["bar_count"], 3)
        self.assertEqual(manifest["provider"], "fixture")
        first = self.client.get(f"/api/market/revisions/{revision}/bars", params={"limit": 2}).json()
        second = self.client.get(f"/api/market/revisions/{revision}/bars", params={"cursor": first["next_cursor"], "limit": 2}).json()
        self.assertEqual(len(first["bars"]) + len(second["bars"]), 3)
        self.assertEqual(second["offset"], 2)
        self.assertIsNone(second["next_cursor"])
        self.assertFalse(self.client.post(f"/api/market/revisions/{revision}/continue").json()["continued"])
        self.assertEqual(self.client.get(f"/api/market/revisions/{'0' * 64}/manifest").status_code, 404)
        self.assertEqual(self.client.get(f"/api/market/revisions/{revision}/bars", params={"limit": 1001}).status_code, 422)

    def test_failed_market_provider_returns_visible_redacted_service_error(self):
        from backend.providers import ProviderError
        with patch.object(self.app.state.autonomy.providers, "bars", side_effect=ProviderError("Historical data unavailable; no fabricated bars")):
            response = self.client.get("/api/market/bars/AAPL")
        self.assertEqual(response.status_code, 503)
        self.assertIn("no fabricated bars", response.json()["detail"])

    def test_real_supervisor_executes_authorized_intent_without_manual_cycle(self):
        from tests.test_trading import FakeProviders
        with patch.dict("os.environ", {"ASTER_MARKET_DATA": "manual"}):
            application = create_app(Path(self.temp.name) / "autonomous.sqlite")
        application.state.autonomy.providers.calendar = FakeProviders().calendar
        application.state.research.operate = lambda: {"collected": 0, "errors": [], "scope": "In-process fixture; external research disabled"}
        application.state.trading.fund_book("main", 100, "boot-capital")
        application.state.store.ingest_quote("AAPL", Decimal("10"), datetime.now(timezone.utc), "Manual test observation")
        intent = application.state.trading.submit_intent({"book_id": "main", "symbol": "AAPL", "side": "buy", "quantity": 2, "order_type": "market", "time_in_force": "gtc", "client_id": "boot-intent"})
        with TestClient(application) as client:
            deadline = time.monotonic() + 5
            status = None
            while time.monotonic() < deadline:
                snapshot = client.get("/api/autonomy").json()
                status = next(i for i in snapshot["trading"]["intents"] if i["id"] == intent["id"])["status"]
                if status == "filled":
                    break
                time.sleep(0.05)
            self.assertEqual(status, "filled")
            self.assertEqual(snapshot["trading"]["positions"][0]["quantity"], 2)
            self.assertEqual(snapshot["trading"]["strategy_count"], 0)
            self.assertEqual(client.get("/api/desk").json()["orders"], [])


if __name__ == "__main__":
    unittest.main()
