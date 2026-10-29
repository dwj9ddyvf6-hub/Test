import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.research import Research
from backend.store import DeskError, Store


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "desk.sqlite"
        self.store = Store(self.path)
        self.research = Research(self.store)
        self.engine = self.research.workflows
        self.calls = []
        self.research.search = lambda query: self.calls.append(query) or {"configured": True, "results": [{"path": "market/research.py", "blob_sha": "pinned"}]}

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self):
        return self.engine.register("Pinned research inventory", [{"id": "source", "tool": "catalogue_search", "params": {"query": "bars"}}, {"id": "review", "tool": "evidence_summary", "needs": ["source"]}])

    def test_dependency_runs_once_with_durable_receipts_and_no_financial_effects(self):
        plan = self.plan()
        run = self.engine.enqueue(plan["id"])
        self.assertEqual(run["run_id"], self.engine.enqueue(plan["id"])["run_id"])
        first = self.engine.operate()
        self.assertEqual(first["node_id"], "source")
        second = Research(Store(self.path))
        second.workflows.operate()
        snapshot = second.workflows.snapshot()
        self.assertEqual(snapshot["runs"][0]["status"], "completed")
        result = snapshot["runs"][0]["nodes"][1]["result"]
        self.assertEqual(result["dependencies"]["source"]["results"][0]["blob_sha"], "pinned")
        self.assertEqual(self.calls, ["bars"])
        self.assertFalse(second.workflows.operate()["processed"])
        self.assertEqual(second.workflows.get(plan["id"])["plan_hash"], plan["plan_hash"])
        self.assertEqual(len(second.export()["research_node_receipts"]), 2)
        self.assertEqual(self.store.snapshot({})["orders"], [])

    def test_failed_source_blocks_dependent_and_retry_preserves_failure_receipt(self):
        plan = self.plan()
        run = self.engine.enqueue(plan["id"])
        self.research.search = lambda query: {"configured": False, "results": []}
        self.assertEqual(self.engine.operate()["status"], "failed")
        snapshot = self.engine.snapshot()["runs"][0]
        self.assertEqual([n["status"] for n in snapshot["nodes"]], ["failed", "blocked"])
        self.assertFalse(self.engine.operate()["processed"])
        self.engine.retry(run["run_id"])
        self.research.search = lambda query: {"configured": True, "results": []}
        self.engine.operate()
        self.engine.operate()
        receipts = self.research.export()["research_node_receipts"]
        self.assertEqual([r["status"] for r in receipts], ["failed", "completed", "completed"])
        self.assertEqual([r["attempt"] for r in receipts], [1, 2, 1])

    def test_retry_cannot_overlap_a_newer_active_run_of_the_same_workflow(self):
        plan = self.plan()
        failed = self.engine.enqueue(plan["id"])
        self.research.search = lambda query: {"configured": False, "results": []}
        self.engine.operate()
        current = self.engine.enqueue(plan["id"])
        with self.assertRaises(DeskError) as error:
            self.engine.retry(failed["run_id"])
        self.assertEqual(error.exception.status, 409)
        runs = self.engine.snapshot()["runs"]
        self.assertEqual(sum(r["status"] in {"queued", "running"} for r in runs), 1)
        self.assertEqual(next(r["status"] for r in runs if r["id"] == failed["run_id"]), "failed")
        self.engine.cancel(current["run_id"])
        self.engine.retry(failed["run_id"])
        self.assertEqual(sum(r["status"] in {"queued", "running"} for r in self.engine.snapshot()["runs"]), 1)

    def test_deduplicated_enqueue_reports_the_actual_running_status(self):
        plan = self.plan()
        queued = self.engine.enqueue(plan["id"])
        self.engine.operate()
        existing = self.engine.enqueue(plan["id"])
        self.assertEqual(existing["run_id"], queued["run_id"])
        self.assertEqual(existing["status"], "running")

    def test_wrong_parameter_types_are_validation_errors_without_saved_plans(self):
        app = create_app(self.path, start_worker=False)
        invalid = [("bar_history", {"symbol": 123}), ("bar_history", {"symbol": "QQQ", "range": ["max"]}), ("bar_history", {"symbol": "QQQ", "interval": {}}), ("source_collection", {"symbols": [{"symbol": "QQQ"}]})]
        with TestClient(app, raise_server_exceptions=False) as client:
            for tool, params in invalid:
                with self.subTest(tool=tool, params=params):
                    response = client.post("/api/research/workflows", json={"title": "Invalid types", "nodes": [{"id": "source", "tool": tool, "params": params}]})
                    self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(client.get("/api/research/workflows").json()["workflows"], [])

    def test_active_lease_fences_duplicate_then_expired_read_recovers(self):
        plan = self.plan()
        run = self.engine.enqueue(plan["id"])
        original = self.research.search
        def concurrent(query):
            self.assertFalse(Research(Store(self.path)).workflows.operate()["processed"])
            return original(query)
        self.research.search = concurrent
        self.engine.operate()
        with self.store.transaction() as con:
            con.execute("UPDATE research_nodes SET status='running',lease_until=0,lease_token='interrupted' WHERE run_id=? AND node_id='review'", (run["run_id"],))
        self.engine.operate()
        self.assertEqual(self.engine.snapshot()["runs"][0]["status"], "completed")
        self.assertEqual(self.calls, ["bars"])

    def test_rejects_financial_tools_and_forward_or_cyclic_dependencies(self):
        for nodes in ([{"id": "bad", "tool": "submit_order"}], [{"id": "a", "tool": "evidence_summary", "needs": ["b"]}, {"id": "b", "tool": "evidence_summary", "needs": ["a"]}]):
            with self.assertRaises(DeskError):
                self.engine.register("Forbidden workflow", nodes)
        self.assertEqual(self.engine.snapshot()["workflows"], [])

    def test_stale_history_fails_and_cancel_fences_inflight_source_result(self):
        self.research.providers = type("StaleProvider", (), {"bars": lambda instance, *a, **kw: {"bars": [{"close": 100}], "stale_cache": True}})()
        plan = self.engine.register("Fresh bar check", [{"id": "bars", "tool": "bar_history", "params": {"symbol": "QQQ", "interval": "60m"}}])
        self.engine.enqueue(plan["id"])
        self.assertEqual(self.engine.operate()["status"], "failed")
        with self.assertRaises(DeskError):
            self.engine.register("Unsupported interval", [{"id": "bars", "tool": "bar_history", "params": {"symbol": "QQQ", "interval": "1h"}}])
        plan = self.plan()
        run = self.engine.enqueue(plan["id"])
        def cancel_during_read(query):
            self.engine.cancel(run["run_id"])
            return {"configured": True, "results": [{"blob_sha": "after-cancellation"}]}
        self.research.search = cancel_during_read
        result = self.engine.operate()
        self.assertIn("discarded", result)
        saved = next(r for r in self.engine.snapshot()["runs"] if r["id"] == run["run_id"])
        self.assertEqual(saved["status"], "cancelled")
        self.assertTrue(all(n["status"] == "cancelled" for n in saved["nodes"]))
        self.assertFalse(any(r["run_id"] == run["run_id"] for r in self.research.export()["research_node_receipts"]))

    def test_explicit_enabled_schedule_runs_without_operator_cycle(self):
        plan = self.plan()
        self.engine.configure(plan["id"], True)
        self.engine.operate()
        self.engine.operate()
        self.assertEqual(self.engine.snapshot()["runs"][0]["status"], "completed")
        self.assertEqual(len(self.engine.snapshot()["runs"]), 1)
        self.assertTrue(self.engine.get(plan["id"])["enabled"])

    def test_real_api_routes_validate_and_export_workflow_receipts(self):
        app = create_app(self.path, start_worker=False)
        with TestClient(app) as client:
            response = client.post("/api/research/workflows", json={"title": "Source manifest", "nodes": [{"id": "evidence", "tool": "evidence_summary"}]})
            self.assertEqual(response.status_code, 200, response.text)
            plan = response.json()
            run = client.post("/api/research/workflows/" + plan["id"] + "/run", json={}).json()
            app.state.research.workflows.operate()
            snapshot = client.get("/api/research/workflows").json()
            self.assertEqual(snapshot["runs"][0]["status"], "completed")
            result = client.get("/api/research/runs/" + run["run_id"] + "/nodes/evidence").json()
            self.assertEqual(result["result"]["strategy_count"], 0)
            self.assertEqual(client.get("/api/strategies").json(), [])
            exported = client.get("/api/export").json()
            self.assertEqual(len(exported["research"]["research_node_receipts"]), 1)
            self.assertEqual(exported["trading"]["intents"], [])


if __name__ == "__main__":
    unittest.main()
