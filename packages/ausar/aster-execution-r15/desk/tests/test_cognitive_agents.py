import tempfile
import unittest
import json
import hashlib
import threading
import time
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.lab import Lab
from backend.providers import Providers
from backend.research import Research
from backend.reasoning import Reasoning
from backend.store import Store
from backend.trading import TradingDesk
from backend.worker import Worker
from tests.test_backend import LocalReasoning, CountingReasoning, ScriptedReasoning, model_call, model_reply


class CognitiveAgentTests(unittest.TestCase):
    def test_manual_accountant_reconstructs_append_order_across_clock_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            store.fund(Decimal("100"), "fixture-funding")
            clock = datetime.now(timezone.utc)
            store.ingest_quote("AAPL", Decimal("10"), clock, "Synthetic test observation")
            buy = store.create_order("AAPL", "buy", Decimal("1"), "fixture-buy")
            with patch("backend.store.now", return_value=clock.isoformat()):
                store.approve_order(buy["id"])
            sell = store.create_order("AAPL", "sell", Decimal("1"), "fixture-sell")
            with patch("backend.store.now", return_value=(clock - timedelta(seconds=1)).isoformat()):
                store.approve_order(sell["id"])
            with store.connect() as con:
                fills = con.execute("SELECT side,timestamp FROM fills ORDER BY rowid").fetchall()
                self.assertEqual([r["side"] for r in fills], ["buy", "sell"])
                self.assertGreater(fills[0]["timestamp"], fills[1]["timestamp"])
            task = store.enqueue("reconcile")
            worker = Worker(store, LocalReasoning())
            for _ in range(6):
                worker.run_once()
            state = store.snapshot({})
            result = next(t for t in state["tasks"] if t["id"] == task["id"])
            self.assertEqual(result["status"], "completed")
            self.assertIsNone(result["error"])
            self.assertEqual(state["account"]["cash"], 100)
            self.assertEqual(state["account"]["realized_pnl"], 0)
            self.assertEqual(state["positions"], [])
            worker.stop()

    def test_model_http_deadline_cancels_a_continuously_dribbling_response(self):
        closed = []
        class DribblingResponse(httpx.AsyncByteStream):
            async def __aiter__(self):
                for _ in range(1000):
                    await asyncio.sleep(0.005)
                    yield b" "
            async def aclose(self):
                closed.append(True)
        transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=DribblingResponse()))
        client = httpx.AsyncClient(transport=transport)
        provider = Reasoning()
        provider.base_url, provider.model, provider.key = "https://fixture.invalid/v1", "fixture", ""
        provider.REQUEST_TIMEOUT_SECONDS = 0.04
        started = time.monotonic()
        with patch("backend.reasoning.httpx.AsyncClient", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "could not produce an annotation"):
                provider.annotate("Facts")
        self.assertLess(time.monotonic() - started, 1)
        self.assertTrue(closed)
        self.assertTrue(client.is_closed)
        self.assertIsNotNone(provider.last_error)

    def test_model_http_client_preserves_completion_payload_and_usage_receipt(self):
        requests = []
        def completion(request):
            requests.append(request)
            return httpx.Response(200, json=model_reply("Fixture source review"))
        client = httpx.AsyncClient(transport=httpx.MockTransport(completion))
        provider = Reasoning()
        provider.base_url, provider.model, provider.key = "https://fixture.invalid/v1", "fixture", "fixture-key"
        receipts = []
        with patch("backend.reasoning.httpx.AsyncClient", return_value=client) as factory:
            annotation = provider.annotate("Facts", record_receipt=receipts.append)
        self.assertIn("Fixture source review", annotation)
        self.assertEqual(str(requests[0].url), "https://fixture.invalid/v1/chat/completions")
        self.assertEqual(requests[0].headers["Authorization"], "Bearer fixture-key")
        self.assertEqual(json.loads(requests[0].content)["model"], "fixture")
        self.assertEqual(json.loads(requests[0].content)["temperature"], 0.2)
        self.assertEqual(json.loads(requests[0].content)["max_tokens"], 1000)
        self.assertEqual(json.loads(requests[0].content)["tool_choice"], "auto")
        self.assertEqual(receipts[0]["usage"]["total_tokens"], 15)
        self.assertTrue(factory.call_args.kwargs["trust_env"])
        self.assertFalse(factory.call_args.kwargs["follow_redirects"])

    def test_model_shared_transport_keeps_deadline_limit_and_sanitizes_non_success(self):
        provider = Reasoning()
        provider.base_url, provider.model, provider.key = "https://fixture.invalid/v1", "fixture", "fixture-key"
        with patch("backend.reasoning.bounded_http", return_value=(429, b"Private provider body")) as request:
            with self.assertRaisesRegex(RuntimeError, "could not produce an annotation") as failed:
                provider.annotate("Facts")
        self.assertEqual(request.call_args.args, ("POST", "https://fixture.invalid/v1/chat/completions"))
        self.assertEqual(request.call_args.kwargs["timeout_seconds"], 15)
        self.assertEqual(request.call_args.kwargs["maximum_bytes"], 512000)
        self.assertFalse(request.call_args.kwargs["follow_redirects"])
        self.assertEqual(request.call_args.kwargs["headers"]["Authorization"], "Bearer fixture-key")
        self.assertTrue(json.loads(request.call_args.kwargs["body"])["tools"])
        self.assertNotIn("Private", str(failed.exception))
        self.assertIsNotNone(provider.last_error)

    def test_same_worker_instance_cannot_execute_one_step_concurrently(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            entered, release = threading.Event(), threading.Event()
            class BlockingReasoning(CountingReasoning):
                def annotate(self, context, **kwargs):
                    self.calls.append(context)
                    entered.set()
                    if not release.wait(timeout=5):
                        raise RuntimeError("Fixture barrier timed out")
                    return "Fixture evidence review"
            provider = BlockingReasoning()
            worker = Worker(store, provider)
            store.enqueue("research_note", instructions="Evidence only")
            with ThreadPoolExecutor(max_workers=1) as pool:
                first = pool.submit(worker.run_once)
                try:
                    self.assertTrue(entered.wait(timeout=5))
                    self.assertFalse(worker.run_once())
                finally:
                    release.set()
                self.assertTrue(first.result(timeout=5))
            self.assertEqual(len(provider.calls), 1)
            handoffs = [e for e in store.snapshot({})["events"] if e["event_type"] == "agent_handoff"]
            self.assertEqual(len(handoffs), 1)
            self.assertEqual(handoffs[0]["actor"], "coordinator")
            worker.stop()

    def test_model_evidence_boundaries_renew_only_valid_leases(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            clock = [time.time()]
            started = clock[0]
            class SlowReasoning(ScriptedReasoning):
                def _completion(self, messages, tool_definitions):
                    clock[0] += 20 if not self.requests else 15
                    return super()._completion(messages, tool_definitions)
            class SlowEvidenceWorker(Worker):
                def _read_model_tool(self, tid, name):
                    result = super()._read_model_tool(tid, name)
                    clock[0] += 26
                    return result
            provider = SlowReasoning([model_reply(calls=[model_call("get_task_evidence")]), model_reply("Fixture review completed with bounded source inspections")])
            worker = SlowEvidenceWorker(store, provider)
            task = store.enqueue("research_note", instructions="Evidence only")
            with patch("backend.worker.time.time", side_effect=lambda: clock[0]):
                self.assertTrue(worker.run_once())
                self.assertGreater(clock[0] - started, Worker.LEASE_SECONDS)
                with store.connect() as con:
                    row = con.execute("SELECT * FROM tasks WHERE id=?", (task["id"],)).fetchone()
                    self.assertEqual(row["attempts"], 1)
                    self.assertGreater(row["lease_until"], clock[0])
                    self.assertEqual(con.execute("SELECT status FROM steps WHERE task_id=? AND sequence=0", (task["id"],)).fetchone()[0], "completed")
                self.assertTrue(worker.run_once())
            self.assertEqual(store.snapshot({})["tasks"][0]["status"], "completed")
            worker.stop()

    def test_expired_or_cancelled_model_work_cannot_extend_its_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            worker = Worker(store, CountingReasoning())
            task = store.enqueue("research_note", instructions="Evidence only")
            worker.run_once()
            for expired, cancelled in ((True, False), (False, True)):
                with store.transaction() as con:
                    until = 0 if expired else time.time() + 45
                    con.execute("UPDATE tasks SET lease_until=?,cancel_requested=? WHERE id=?", (until, int(cancelled), task["id"]))
                    con.execute("UPDATE worker_lock SET expires=? WHERE id=1", (until,))
                with self.assertRaises(RuntimeError):
                    worker._read_model_tool(task["id"], "get_task_evidence")
                with store.connect() as con:
                    self.assertEqual(con.execute("SELECT lease_until FROM tasks WHERE id=?", (task["id"],)).fetchone()[0], until)
                    self.assertEqual(con.execute("SELECT expires FROM worker_lock WHERE id=1").fetchone()[0], until)
            worker.stop()

    def test_shutdown_does_not_release_an_inflight_tick_or_let_it_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            entered, release = threading.Event(), threading.Event()
            class BlockingReasoning(CountingReasoning):
                def annotate(self, context, **kwargs):
                    entered.set()
                    if not release.wait(timeout=5):
                        raise RuntimeError("Fixture barrier timed out")
                    return "Fixture evidence review"
            worker = Worker(store, BlockingReasoning())
            task = store.enqueue("research_note", instructions="Evidence only")
            worker.start()
            try:
                self.assertTrue(entered.wait(timeout=5))
                original_thread = worker.thread
                with patch.object(original_thread, "join", return_value=None):
                    worker.stop()
                with store.connect() as con:
                    self.assertEqual(con.execute("SELECT owner FROM worker_lock WHERE id=1").fetchone()[0], worker.owner)
                    self.assertEqual(con.execute("SELECT lease_owner FROM tasks WHERE id=?", (task["id"],)).fetchone()[0], worker.owner)
                self.assertFalse(Worker(store, CountingReasoning()).run_once())
                worker.start()
                self.assertIs(worker.thread, original_thread)
                self.assertTrue(worker.stop_event.is_set())
                self.assertFalse(worker.run_once())
            finally:
                release.set()
                worker.thread.join(timeout=5)
            self.assertFalse(worker.thread.is_alive())
            worker.stop()
            with store.connect() as con:
                self.assertIsNone(con.execute("SELECT owner FROM worker_lock WHERE id=1").fetchone()[0])
                self.assertEqual(con.execute("SELECT lease_until FROM tasks WHERE id=?", (task["id"],)).fetchone()[0], 0)

    def test_oversized_tool_evidence_preserves_valid_bounded_json_and_hash_receipt(self):
        evidence = {"source": "fixture", "text": "\u03b1" * 50000}
        provider = ScriptedReasoning([model_reply(calls=[model_call("get_task_evidence")]), model_reply("The evidence preview is bounded; full evidence requires inspection.")])
        receipts = []
        provider.annotate("Facts", tools=lambda name: evidence, record_receipt=receipts.append)
        tool_content = next(message["content"] for message in provider.requests[1]["messages"] if message["role"] == "tool")
        decoded = json.loads(tool_content)
        self.assertTrue(decoded["result_omitted"])
        raw = json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        self.assertEqual(decoded["result_bytes"], len(raw))
        self.assertEqual(decoded["result_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertLess(len(tool_content.encode()), 40000)
        self.assertEqual(next(r["result"] for r in receipts if r["kind"] == "tool_call"), decoded)

    def test_malformed_provider_shapes_fail_with_recorded_bounded_health(self):
        malformed = [[], {"choices": []}, {"choices": [{"message": None}]}, {"choices": [{"message": {"content": "ignored"}}], "usage": ["invalid"]}, {"choices": [{"message": {"tool_calls": "bad"}}]}, {"choices": [{"message": {"tool_calls": ["bad"]}}]}]
        for reply in malformed:
            with self.subTest(reply=reply):
                provider = ScriptedReasoning([reply])
                calls = []
                with self.assertRaisesRegex(RuntimeError, "could not produce an annotation"):
                    provider.annotate("Facts", tools=lambda name: calls.append(name))
                self.assertTrue(provider.last_error)
                self.assertIsNone(provider.last_success_at)
                self.assertEqual(calls, [])

    def test_independent_cognitive_roles_inspect_actual_books_and_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "desk.sqlite")
            trading, lab = TradingDesk(store), Lab(store)
            providers = Providers(store)
            research = Research(store, transport=lambda url, headers: b'<rss><channel><item><title>Source report</title><link>https://example.org/report</link><pubDate>Wed, 07 Oct 2026 20:00:00 GMT</pubDate></item></channel></rss>')
            research.sec_user_agent = ""
            research.collect(["AAPL"], force=True)
            trading.fund_book("main", Decimal("100"), "initial")
            lab.bind(trading, research)
            provider = ScriptedReasoning([
                model_reply(calls=[model_call("get_autonomous_books", "risk")]),
                model_reply("Risk review: no positions; no funded strategy."),
                model_reply(calls=[model_call("get_research_evidence", "research")]),
                model_reply("Source review: one collected headline; no conclusion of edge."),
                model_reply(calls=[model_call("get_task_evidence", "journal")]),
                model_reply("Journal review: preserve claims separately from facts."),
            ])
            provider.multi_agent = True
            worker = Worker(store, provider)
            worker.trading, worker.lab, worker.research, worker.providers = trading, lab, research, providers
            task = store.enqueue("desk_brief", "Independent research review")
            for _ in range(12):
                worker.run_once()
                result = next(t for t in store.snapshot({})["tasks"] if t["id"] == task["id"])
                if result["status"] == "completed":
                    break
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(provider.requests), 6)
            self.assertIn("risk_officer", provider.requests[0]["messages"][0]["content"])
            self.assertIn("coordinator", provider.requests[2]["messages"][0]["content"])
            self.assertIn("archivist", provider.requests[4]["messages"][0]["content"])
            receipts = [e for e in store.snapshot({})["events"] if e["event_type"] == "model_tool_receipt"]
            self.assertEqual({e["actor"] for e in receipts}, {"risk_officer", "coordinator", "archivist"})
            self.assertEqual(trading.snapshot()["intents"], [])
            self.assertEqual(trading.snapshot()["books"][0]["account"]["cash"], 100)
            self.assertEqual(len(lab.snapshot()["artifacts"]), 1)
            self.assertEqual(lab.snapshot()["inbox_total"], 1)
            self.assertEqual(lab.snapshot()["strategy_count"], 0)
            worker.stop()


if __name__ == "__main__":
    unittest.main()
