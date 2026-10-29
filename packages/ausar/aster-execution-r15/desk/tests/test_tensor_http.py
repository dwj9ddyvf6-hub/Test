"""Four installed sleeves across the real HTTP and fenced supervisor boundaries."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from fastapi.testclient import TestClient
from backend.app import create_app


class TensorHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name) / "tensor-http.sqlite", start_worker=False)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def install(self, sleeve="H1STATE"):
        book = self.client.post("/api/books", json={"name": "Fixture " + sleeve, "kind": "forward", "broker": "local"}).json()
        self.assertEqual(self.client.post(f"/api/books/{book['id']}/funding", json={"amount": 100000, "client_id": "fixture-opening"}).status_code, 200)
        payload = {"id": "fixture-" + sleeve, "sleeve": sleeve, "book_id": book["id"], "symbols": ["AMD"], "enabled": True}
        response = self.client.post("/api/strategies/install", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return payload, response.json()

    def test_four_independent_books_registry_pause_and_fast_queue(self):
        installs = [self.install(s)[1] for s in ("H1STATE", "WSTATE", "D20PV", "D20TENSOR")]
        self.assertEqual(len({v["book_id"] for v in installs}), 4)
        self.assertEqual(len(self.client.get("/api/strategies").json()), 4)
        snapshot = self.client.get("/api/autonomy").json()
        self.assertEqual(snapshot["strategies"]["strategy_count"], 4)
        self.assertEqual(snapshot["trading"]["strategy_count"], 4)
        self.assertEqual(self.client.get("/api/desk").json()["desk"]["strategy_count"], 4)
        for v in installs:
            paused = self.client.patch(f"/api/strategies/{v['id']}", json={"enabled": False})
            self.assertEqual(paused.status_code, 200)
            self.assertFalse(paused.json()["enabled"])
            self.assertEqual(self.client.patch(f"/api/strategies/{v['id']}", json={"enabled": "false"}).status_code, 422)
        with patch.object(self.app.state.strategies, "run_once", side_effect=AssertionError("HTTP trigger must not run slow computation")):
            response = self.client.post("/api/strategies/run")
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["queued"])
        with self.app.state.store.connect() as con:
            schedule = dict(con.execute("SELECT * FROM a_schedules WHERE id='tensor-strategies'").fetchone())
            self.assertEqual(schedule["kind"], "strategies")
            self.assertEqual(schedule["interval_seconds"], 1)
            self.assertEqual(schedule["next_due"], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fundings").fetchone()[0], 4)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fills").fetchone()[0], 0)

    def test_immutable_install_identity_and_operator_ownership_boundary(self):
        payload, installed = self.install()
        self.assertEqual(self.client.post("/api/strategies/install", json=payload).json()["id"], installed["id"])
        self.assertEqual(self.client.post("/api/strategies/install", json={**payload, "symbols": ["AAPL"]}).status_code, 409)
        operator = self.client.post("/api/intents", json={"book_id": installed["book_id"], "symbol": "AMD", "side": "buy", "quantity": 1, "client_id": "operator-injection", "source": "strategy"})
        self.assertIn(operator.status_code, (409, 422))
        self.assertEqual(self.client.patch(f"/api/strategies/{installed['id']}", json={"enabled": False, "hold_native_bars": 1}).status_code, 422)

    def test_binary_native_state_exports_with_exact_lossless_encoding(self):
        self.install()
        native = zlib.compress(b'["causal historical bar fixture"]')
        with self.app.state.store.transaction() as con:
            con.execute("INSERT INTO a_tensor_coverage VALUES(?,?,?,?,?,?,?,?)", ("1h", "AMD", "fixture-revision", "2026-10-09T10:00:00+00:00", native, "ready", None, "2026-10-09T10:00:00+00:00"))
        direct = self.app.state.store.export({"configured": False})
        json.dumps(direct)
        response = self.client.get("/api/export")
        self.assertEqual(response.status_code, 200, response.text[:300])
        exported = response.json()
        column = exported["autonomous_tables"]["a_tensor_coverage"][0]["bars"]
        self.assertEqual(column["encoding"], "base64")
        self.assertEqual(column["bytes"], len(native))
        self.assertEqual(base64.b64decode(column["data"], validate=True), native)
        self.assertNotIn("a_tensor_coverage", exported["tables"])
        self.assertEqual(exported["strategy_count"], 1)

    def test_strategy_job_calls_manager_under_same_database_fence(self):
        self.install()
        runtime = self.app.state.autonomy
        calls = []
        def manager_run(clock=None, transaction_guard=None, providers=None):
            self.assertIsNone(clock)
            self.assertTrue(callable(transaction_guard))
            self.assertTrue(callable(providers.execution_fence))
            with self.app.state.store.transaction() as con:
                transaction_guard(con)
            calls.append("fenced")
            return {"entries": 0, "exits": 0, "errors": []}
        with patch.object(self.app.state.strategies, "run_once", side_effect=manager_run), patch.object(runtime.providers, "refresh", return_value={"errors": []}), patch.object(runtime.providers, "capture_quotes", return_value=None), patch.object(runtime.providers, "bars", return_value={"symbol": "QQQ", "bars": [], "errors": []}):
            self.assertTrue(runtime.run_once(force=True))
        self.assertEqual(calls, ["fenced"])
        with self.app.state.store.connect() as con:
            job = con.execute("SELECT status,result FROM a_jobs WHERE schedule_id='tensor-strategies' ORDER BY due_at DESC LIMIT 1").fetchone()
        self.assertEqual(job["status"], "succeeded")
        self.assertIn("strategies", json.loads(job["result"]))


if __name__ == "__main__":
    unittest.main()
