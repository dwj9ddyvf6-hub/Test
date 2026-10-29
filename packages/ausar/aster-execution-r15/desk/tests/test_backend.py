import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from backend.models import Funding, Order, Quote, Settings, Task
from backend.reasoning import Reasoning, TOOL_DESCRIPTIONS
from backend.store import DeskError, Store, WORKFLOWS
from backend.worker import Worker


class LocalReasoning:
    configured = False
    last_success_at = None
    last_error = None

    def status(self):
        return {"provider": "local", "configured": False, "model": None}


class CountingReasoning(LocalReasoning):
    configured = True

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def annotate(self, context, **kwargs):
        self.calls.append(context)
        if self.fail:
            raise RuntimeError("Configured reasoning provider could not produce an annotation")
        return "Supplied context summarized."


class ScriptedReasoning(Reasoning):
    """An in-process provider fixture: it cannot make network requests."""
    def __init__(self, replies):
        self.base_url, self.model, self.key = "http://unused.invalid/v1", "fixture-model", ""
        self.last_error = self.last_success_at = None
        self.replies = list(replies)
        self.requests = []

    def _completion(self, messages, tool_definitions):
        self.requests.append({"messages": json.loads(json.dumps(messages)), "tools": tool_definitions})
        if not self.replies:
            raise ValueError("Fixture has no more responses")
        return self.replies.pop(0)


def model_reply(text=None, calls=None):
    return {"choices": [{"message": {"role": "assistant", "content": text, "tool_calls": calls or []}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}


def model_call(name, rid="call-1", arguments="{}"):
    return {"id": rid, "type": "function", "function": {"name": name, "arguments": arguments}}


class DeskTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "desk.sqlite"
        self.store = Store(self.path)
        self.reasoning = LocalReasoning()

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return self.store.snapshot(self.reasoning.status())

    def quote(self, price="10", sym="AAPL", age=0):
        return self.store.ingest_quote(sym, Decimal(price), datetime.now(timezone.utc) - timedelta(seconds=age), "Operator test observation")

    def fund(self, amount="1000", key="fund"):
        return self.store.fund(Decimal(amount), key)

    def buy(self, qty="10", key="buy", price="10"):
        self.quote(price)
        order = self.store.create_order("AAPL", "buy", Decimal(qty), key)
        self.store.approve_order(order["id"])
        return order

    def run_task(self, worker, limit=30):
        for _ in range(limit):
            worker.run_once()
            if not any(t["status"] in {"queued", "running"} for t in self.snapshot()["tasks"]):
                break
        return self.snapshot()["tasks"][0]

    def test_empty_initial_state_is_truthful(self):
        s = self.snapshot()
        self.assertEqual(s["account"]["cash"], 0)
        self.assertEqual(s["account"]["equity"], 0)
        self.assertFalse(s["desk"]["runtime"]["running"])
        self.assertFalse(s["desk"]["reasoning"]["configured"])
        self.assertEqual(len(s["agents"]), 6)
        for key in ("positions", "orders", "fills", "watchlist", "tasks", "events", "equity_history", "strategy_slots"):
            self.assertEqual(s[key], [])

    def test_funding_idempotency_and_payload_mismatch(self):
        first = self.fund("10.01")
        second = self.fund("10.01")
        self.assertEqual(first, second)
        self.assertEqual(self.snapshot()["account"]["cash"], 10.01)
        with self.assertRaisesRegex(DeskError, "different funding"):
            self.fund("10.02")
        self.assertEqual(len(self.snapshot()["events"]), 1)

    def test_quote_chronology_and_future_are_atomic(self):
        original = self.quote()
        with self.assertRaisesRegex(DeskError, "older"):
            self.quote("20", age=30)
        with self.assertRaisesRegex(DeskError, "future"):
            self.quote("20", age=-20)
        ts = datetime.fromisoformat(original["as_of"])
        with self.assertRaisesRegex(DeskError, "different price"):
            self.store.ingest_quote("AAPL", Decimal(20), ts, original["source"])
        self.assertEqual(self.store.ingest_quote("AAPL", Decimal(10), ts, original["source"]), original)
        self.assertEqual(self.snapshot()["watchlist"][0]["quote"]["price"], 10)
        self.assertEqual(len(self.snapshot()["events"]), 1)

    def test_timezone_and_nonfinite_rejected(self):
        with self.assertRaises(DeskError):
            self.store.ingest_quote("AAPL", Decimal(10), datetime.now(), "Source")
        for value in ("NaN", "Infinity", "-1", "0"):
            with self.assertRaises(Exception):
                Quote(symbol="AAPL", price=value, as_of=datetime.now(timezone.utc), source="Source")
        with self.assertRaises(Exception):
            Funding(amount="0.001", client_id="tiny")
        with self.assertRaises(Exception):
            Order(symbol="AAPL", side="buy", quantity="0.0000001", client_id="tiny")

    def test_watchlist_does_not_invent_price_and_symbols_normalized(self):
        watch = self.store.add_watch(" brk.b ")
        self.assertEqual(watch["symbol"], "BRK.B")
        self.assertIsNone(watch["quote"])
        self.assertEqual(self.store.add_watch("BRK.B"), watch)
        with self.assertRaises(DeskError):
            self.store.add_watch("AAPL OR 1=1")
        self.store.remove_watch("BRK.B")
        self.assertEqual(self.snapshot()["watchlist"], [])

    def test_pending_order_reserves_but_does_not_fill(self):
        self.fund()
        self.quote()
        order = self.store.create_order("AAPL", "buy", Decimal(30), "intent")
        s = self.snapshot()
        self.assertEqual(order["status"], "pending_review")
        self.assertEqual(s["account"]["cash"], 1000)
        self.assertEqual(s["account"]["reserved_cash"], 300)
        self.assertEqual(s["account"]["available_cash"], 700)
        self.assertEqual(s["positions"], [])
        self.assertEqual(s["fills"], [])

    def test_order_and_approval_idempotency(self):
        self.fund()
        self.quote()
        first = self.store.create_order("aapl", "buy", Decimal(10), "intent")
        self.assertEqual(self.store.create_order("AAPL", "buy", Decimal("10.0"), "intent"), first)
        with self.assertRaisesRegex(DeskError, "different order"):
            self.store.create_order("AAPL", "buy", Decimal(11), "intent")
        filled = self.store.approve_order(first["id"])
        self.assertEqual(self.store.approve_order(first["id"]), filled)
        self.assertEqual(len(self.snapshot()["fills"]), 1)
        self.assertEqual(self.snapshot()["account"]["cash"], 900)

    def test_concurrent_cash_reservations_cannot_overcommit(self):
        self.fund("100")
        self.quote()
        gate = threading.Barrier(8)

        def attempt(index):
            gate.wait()
            try:
                return self.store.create_order("AAPL", "buy", Decimal(6), f"intent-{index}")
            except DeskError:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(self.snapshot()["account"]["reserved_cash"], 60)
        self.assertEqual(self.snapshot()["account"]["available_cash"], 40)

    def test_concurrent_idempotent_approval_fills_once(self):
        self.fund()
        self.quote()
        order = self.store.create_order("AAPL", "buy", Decimal(10), "intent")
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.store.approve_order(order["id"]), range(6)))
        self.assertTrue(all(r["status"] == "filled" for r in results))
        self.assertEqual(len(self.snapshot()["fills"]), 1)
        self.assertEqual(self.snapshot()["account"]["cash"], 900)

    def test_stale_quote_blocks_intent_and_approval_without_effects(self):
        self.fund()
        self.quote(age=400)
        with self.assertRaisesRegex(DeskError, "fresh"):
            self.store.create_order("AAPL", "buy", Decimal(10), "intent")
        self.quote()
        order = self.store.create_order("AAPL", "buy", Decimal(10), "intent")
        self.store.update_settings({"quote_max_age_seconds": 1})
        with self.store.transaction() as con:
            con.execute("UPDATE quotes SET as_of=?", ((datetime.now(timezone.utc) - timedelta(seconds=2)).isoformat(),))
        with self.assertRaisesRegex(DeskError, "fresh"):
            self.store.approve_order(order["id"])
        s = self.snapshot()
        self.assertEqual(s["account"]["cash"], 1000)
        self.assertEqual(s["account"]["reserved_cash"], 100)
        self.assertEqual(s["fills"], [])
        self.assertEqual(s["orders"][0]["status"], "pending_review")

    def test_price_change_rechecks_other_reservations_atomically(self):
        self.fund("100")
        self.quote()
        first = self.store.create_order("AAPL", "buy", Decimal(5), "first")
        second = self.store.create_order("AAPL", "buy", Decimal(5), "second")
        self.quote("11")
        with self.assertRaisesRegex(DeskError, "insufficient"):
            self.store.approve_order(first["id"])
        self.assertEqual(self.snapshot()["account"]["cash"], 100)
        self.store.cancel_order(second["id"])
        self.store.approve_order(first["id"])
        self.assertEqual(self.snapshot()["account"]["cash"], 45)

    def test_cancel_releases_cash_and_preserves_intent_history(self):
        self.fund()
        self.quote()
        order = self.store.create_order("AAPL", "buy", Decimal(10), "intent")
        cancelled = self.store.cancel_order(order["id"])
        self.assertEqual(self.store.cancel_order(order["id"]), cancelled)
        self.assertEqual(self.snapshot()["account"]["reserved_cash"], 0)
        self.assertEqual(cancelled["status"], "cancelled")
        with self.assertRaises(DeskError):
            self.store.approve_order(order["id"])

    def test_sell_reservations_prevent_share_oversubscription(self):
        self.fund()
        self.buy("10")
        first = self.store.create_order("AAPL", "sell", Decimal(6), "first")
        with self.assertRaisesRegex(DeskError, "unreserved paper shares"):
            self.store.create_order("AAPL", "sell", Decimal(5), "second")
        self.store.cancel_order(first["id"])
        self.store.create_order("AAPL", "sell", Decimal(10), "all")
        with self.assertRaises(DeskError):
            self.store.create_order("AAPL", "sell", Decimal("0.1"), "extra")

    def test_average_cost_partial_and_final_liquidation_realized_pnl(self):
        self.fund()
        self.buy("10", "buy-1", "10")
        self.buy("10", "buy-2", "20")
        self.assertEqual(self.snapshot()["positions"][0]["average_cost"], 15)
        self.quote("25")
        order = self.store.create_order("AAPL", "sell", Decimal(5), "sell-1")
        self.store.approve_order(order["id"])
        s = self.snapshot()
        self.assertEqual(s["positions"][0]["quantity"], 15)
        self.assertEqual(s["positions"][0]["average_cost"], 15)
        self.assertEqual(s["account"]["realized_pnl"], 50)
        self.assertEqual(s["account"]["unrealized_pnl"], 150)
        self.quote("12")
        final = self.store.create_order("AAPL", "sell", Decimal(15), "sell-2")
        self.store.approve_order(final["id"])
        s = self.snapshot()
        self.assertEqual(s["positions"], [])
        self.assertEqual(s["account"]["cash"], 1005)
        self.assertEqual(s["account"]["realized_pnl"], 5)
        self.assertEqual(s["account"]["unrealized_pnl"], 0)
        task = self.store.enqueue("reconcile")
        result = self.run_task(Worker(self.store, self.reasoning))
        self.assertEqual(result["id"], task["id"])
        self.assertEqual(result["status"], "completed")

    def test_fractional_shares_cent_basis_rounding_remains_reconcilable(self):
        self.fund("10")
        self.buy("3", "buy", "0.333333")
        for index in range(3):
            self.quote("0.5")
            order = self.store.create_order("AAPL", "sell", Decimal(1), f"sell-{index}")
            self.store.approve_order(order["id"])
        self.assertEqual(self.snapshot()["account"]["cash"], 10.5)
        self.assertEqual(self.snapshot()["account"]["realized_pnl"], 0.5)
        self.store.enqueue("reconcile")
        self.assertEqual(self.run_task(Worker(self.store, self.reasoning))["status"], "completed")

    def test_paused_runtime_executes_queued_work_with_durable_handoffs(self):
        self.store.add_watch("AAPL")
        task = self.store.enqueue("operational_cycle")
        result = self.run_task(Worker(self.store, self.reasoning))
        self.assertEqual(result["id"], task["id"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual([s["agent_id"] for s in result["steps"]], WORKFLOWS["operational_cycle"])
        self.assertTrue(all(s["status"] == "completed" and s["result"] for s in result["steps"]))
        self.assertIn("1 missing quotes", result["steps"][0]["result"])
        self.assertIn("reconciliation passed", result["steps"][1]["result"].lower())
        state = Store(self.path).snapshot(self.reasoning.status())
        self.assertEqual(state["tasks"][0]["result"], result["result"])
        self.assertEqual(state["account"]["cash"], 0)
        self.assertEqual(state["orders"], [])
        self.assertEqual(state["strategy_slots"], [])

    def test_cycle_never_fills_pending_human_intent(self):
        self.fund()
        self.quote()
        intent = self.store.create_order("AAPL", "buy", Decimal(10), "intent")
        self.store.enqueue("operational_cycle")
        result = self.run_task(Worker(self.store, self.reasoning))
        self.assertIn("operator approval", result["steps"][3]["result"])
        self.assertEqual(self.snapshot()["orders"][0]["id"], intent["id"])
        self.assertEqual(self.snapshot()["orders"][0]["status"], "pending_review")
        self.assertEqual(self.snapshot()["fills"], [])

    def test_equivalent_cycles_are_idempotent_while_active(self):
        task = self.store.enqueue("operational_cycle")
        self.assertEqual(self.store.enqueue("operational_cycle")["id"], task["id"])
        worker = Worker(self.store, self.reasoning)
        worker.run_once()
        self.assertEqual(self.store.enqueue("operational_cycle")["id"], task["id"])
        self.run_task(worker)
        self.assertNotEqual(self.store.enqueue("operational_cycle")["id"], task["id"])

    def test_single_worker_fencing_and_restart_resumes_completed_steps(self):
        task = self.store.enqueue("operational_cycle")
        first = Worker(self.store, self.reasoning)
        first.run_once()
        second = Worker(Store(self.path), self.reasoning)
        self.assertFalse(second.run_once())
        first.stop()
        result = self.run_task(second)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["steps"]), 6)
        events = [e for e in self.snapshot()["events"] if e["event_type"] == "agent_handoff"]
        self.assertEqual(len(events), 6)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT attempts FROM tasks WHERE id=?", (task["id"],)).fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM snapshots WHERE task_step_id IS NOT NULL").fetchone()[0], 1)

    def test_crashed_running_step_is_recovered_without_duplicate_snapshot(self):
        task = self.store.enqueue("reconcile")
        with self.store.transaction() as con:
            con.execute("UPDATE tasks SET status='running',attempts=1,lease_owner='dead',lease_until=0 WHERE id=?", (task["id"],))
            con.execute("UPDATE steps SET status='running' WHERE task_id=? AND sequence=0", (task["id"],))
        result = self.run_task(Worker(Store(self.path), self.reasoning))
        self.assertEqual(result["status"], "completed")
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0], 1)
        self.assertIn("task_recovered", [e["event_type"] for e in self.snapshot()["events"]])

    def test_cancel_queued_and_running_work_prevents_future_steps(self):
        queued = self.store.enqueue("research_note", instructions="Original supplied note")
        self.assertEqual(self.store.cancel_task(queued["id"])["status"], "cancelled")
        task = self.store.enqueue("operational_cycle")
        worker = Worker(self.store, self.reasoning)
        worker.run_once()
        self.store.cancel_task(task["id"])
        worker.run_once()
        result = next(t for t in self.snapshot()["tasks"] if t["id"] == task["id"])
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["steps"][0]["status"], "completed")
        self.assertTrue(all(s["status"] == "cancelled" for s in result["steps"][1:]))

    def test_recovery_attempt_limit_visible_and_bounded(self):
        task = self.store.enqueue("reconcile")
        with self.store.transaction() as con:
            con.execute("UPDATE tasks SET status='running',attempts=3,lease_owner='dead',lease_until=0 WHERE id=?", (task["id"],))
        worker = Worker(self.store, self.reasoning)
        worker.run_once()
        result = self.snapshot()["tasks"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("attempt limit", result["error"])

    def test_expired_task_cannot_claim_agent_is_working(self):
        task = self.store.enqueue("data_audit")
        with self.store.transaction() as con:
            con.execute("UPDATE tasks SET status='running',lease_owner='dead',lease_until=0 WHERE id=?", (task["id"],))
            con.execute("UPDATE steps SET status='running' WHERE task_id=? AND sequence=0", (task["id"],))
        steward = next(a for a in self.snapshot()["agents"] if a["id"] == "data_steward")
        self.assertEqual(steward["status"], "idle")

    def test_model_only_explicit_brief_or_note_and_verbatim_note_preserved(self):
        provider = CountingReasoning()
        worker = Worker(self.store, provider)
        self.store.enqueue("operational_cycle")
        self.run_task(worker)
        self.assertEqual(provider.calls, [])
        note = "Source: my own memo\nAAPL is a supplied symbol, not a finding."
        self.store.enqueue("research_note", instructions=note, sym="aapl")
        result = self.run_task(worker)
        self.assertEqual(len(provider.calls), 1)
        self.assertIn(note, result["result"])
        self.assertIn("Optional model annotation", result["result"])
        self.assertEqual(json.loads(provider.calls[0])["symbol"], "AAPL")
        self.assertEqual(self.snapshot()["orders"], [])

    def test_model_selects_read_only_tools_and_journals_actual_receipts(self):
        self.store.add_watch("AAPL")
        provider = ScriptedReasoning([
            model_reply(calls=[model_call("get_account_snapshot"), model_call("audit_quote_quality", "call-2")]),
            model_reply("Cash is zero and the manually watched name lacks a quote."),
        ])
        self.store.enqueue("research_note", instructions="Inspect actual operations")
        result = self.run_task(Worker(self.store, provider))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(provider.requests), 2)
        tool_messages = [m for m in provider.requests[1]["messages"] if m["role"] == "tool"]
        self.assertEqual(json.loads(tool_messages[0]["content"])["account"]["cash"], 0)
        self.assertEqual(json.loads(tool_messages[1]["content"])["missing"], 1)
        self.assertEqual({t["function"]["name"] for t in provider.requests[0]["tools"]}, set(TOOL_DESCRIPTIONS))
        events = self.snapshot()["events"]
        receipts = [e for e in events if e["event_type"] == "model_tool_receipt"]
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(e["payload"]["status"] == "completed" for e in receipts))
        self.assertEqual(len([e for e in events if e["event_type"] == "model_provider_round"]), 2)
        self.assertIn("audit_quote_quality", result["result"])
        self.assertEqual(self.snapshot()["orders"], [])
        self.assertEqual(self.snapshot()["account"]["cash"], 0)

    def test_model_mutation_and_nonempty_arguments_are_denied_visibly(self):
        provider = ScriptedReasoning([
            model_reply(calls=[model_call("approve_order"), model_call("get_account_snapshot", "call-2", '{"fund":1000}')]),
            model_reply("The requested mutation tools were denied."),
        ])
        self.store.enqueue("research_note", instructions="Source text")
        result = self.run_task(Worker(self.store, provider))
        self.assertEqual(result["status"], "completed")
        receipts = [e for e in self.snapshot()["events"] if e["event_type"] == "model_tool_receipt"]
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(e["payload"]["status"] == "denied" for e in receipts))
        self.assertIn("Denied calls: approve_order, get_account_snapshot", result["result"])
        self.assertEqual(self.snapshot()["account"]["cash"], 0)
        self.assertEqual(self.snapshot()["orders"], [])

    def test_model_round_and_inspection_budgets_are_enforced(self):
        provider = ScriptedReasoning([
            model_reply(calls=[model_call("get_account_snapshot")]),
            model_reply(calls=[model_call("get_account_snapshot", "again")]),
        ])
        receipts = []
        with self.assertRaises(RuntimeError):
            provider.annotate("Facts", tools=lambda name: {"cash": 0}, record_receipt=receipts.append)
        self.assertEqual(len(provider.requests), 2)
        self.assertEqual(receipts[-1]["status"], "denied")
        too_many = ScriptedReasoning([model_reply(calls=[model_call("get_account_snapshot", f"c-{i}") for i in range(7)])])
        inspections = []
        with self.assertRaises(RuntimeError):
            too_many.annotate("Facts", tools=lambda name: inspections.append(name))
        self.assertEqual(inspections, [])

    def test_cycle_never_calls_configured_model_tool_provider(self):
        provider = ScriptedReasoning([])
        self.store.enqueue("operational_cycle")
        result = self.run_task(Worker(self.store, provider))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(provider.requests, [])

    def test_provider_failure_has_bounded_visible_attempts(self):
        provider = CountingReasoning(fail=True)
        self.store.enqueue("research_note", instructions="Source text")
        result = self.run_task(Worker(self.store, provider))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(provider.calls), 3)
        self.assertIn("could not produce", result["error"])
        self.assertEqual(self.snapshot()["orders"], [])

    def test_cancel_during_provider_failure_cannot_strand_retry(self):
        store = self.store
        task = store.enqueue("research_note", instructions="Evidence")

        class CancellingProvider(CountingReasoning):
            def annotate(self, context, **kwargs):
                store.cancel_task(task["id"])
                raise RuntimeError("Provider failed after operator cancellation")

        worker = Worker(store, CancellingProvider())
        worker.run_once()
        worker.run_once()
        result = self.snapshot()["tasks"][0]
        self.assertEqual(result["status"], "cancelled")
        self.assertTrue(all(step["status"] == "cancelled" for step in result["steps"]))

    def test_full_queue_does_not_block_worker_when_scheduler_enabled(self):
        for index in range(100):
            self.store.enqueue("research_note", title=f"Note {index}")
        self.store.runtime(True)
        worker = Worker(self.store, self.reasoning)
        self.assertTrue(worker.run_once())
        self.assertEqual(sum(t["status"] == "running" for t in self.snapshot()["tasks"]), 1)
        self.assertIn("scheduled_cycle_deferred", [e["event_type"] for e in self.snapshot()["events"]])

    def test_accountant_detects_corruption_instead_of_claiming_success(self):
        self.fund()
        with self.store.transaction() as con:
            con.execute("UPDATE account SET cash_cents=cash_cents+1")
        self.store.enqueue("reconcile")
        result = self.run_task(Worker(self.store, self.reasoning))
        self.assertEqual(result["status"], "failed")
        self.assertIn("do not match", result["error"])
        self.assertEqual(len(self.snapshot()["equity_history"]), 1)

    def test_recurring_cycles_require_explicit_control_and_pause(self):
        worker = Worker(self.store, self.reasoning)
        worker.run_once()
        self.assertEqual(self.snapshot()["tasks"], [])
        self.store.runtime(True)
        worker.run_once()
        self.assertEqual(len(self.snapshot()["tasks"]), 1)
        self.store.runtime(False)
        self.run_task(worker)
        for _ in range(3):
            worker.run_once()
        self.assertEqual(len(self.snapshot()["tasks"]), 1)
        self.assertFalse(self.snapshot()["desk"]["runtime"]["running"])

    def test_input_bounds_and_export_preserves_all_desk_state(self):
        for payload in ({"kind": "strategy"}, {"kind": "desk_brief", "instructions": "x" * 12001}):
            with self.assertRaises(Exception):
                Task(**payload)
        with self.assertRaises(Exception):
            Settings(heartbeat_seconds=0)
        self.fund()
        self.store.enqueue("research_note", instructions="Evidence text")
        exported = self.store.export(self.reasoning.status())
        self.assertEqual(exported["tables"]["tasks"][0]["instructions"], "Evidence text")
        self.assertEqual(len(exported["tables"]["fundings"]), 1)
        self.assertNotIn("ASTER_LLM_API_KEY", json.dumps(exported))

    def test_ordered_journal_hashes_and_tamper_detection_persist_on_restart(self):
        self.fund()
        self.quote()
        result = self.store.verify_ledger()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["verified_events"], 2)
        with self.store.transaction() as con:
            rows = list(con.execute("SELECT * FROM events ORDER BY id"))
            self.assertEqual(rows[1]["prev_hash"], rows[0]["event_hash"])
            con.execute("UPDATE events SET message='Altered message' WHERE id=?", (rows[0]["id"],))
        failed = Store(self.path).ledger_status()
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error_row"], rows[0]["id"])

    def test_verified_journal_truncation_is_detected(self):
        self.fund()
        self.quote()
        verified = self.store.verify_ledger()
        with self.store.transaction() as con:
            con.execute("DELETE FROM events WHERE id=?", (verified["checkpoint_event_id"],))
        self.assertEqual(self.store.verify_ledger()["status"], "failed")


    def test_manual_ledger_rejects_historical_quote_for_creation_and_approval(self):
        self.fund()
        self.quote()
        order = self.store.create_order("AAPL", "buy", Decimal(1), "manual")
        self.store.ingest_quote("AAPL", Decimal(10), datetime.now(timezone.utc), "Historical daily close fixture")
        with self.assertRaisesRegex(DeskError, "Historical daily bars"):
            self.store.create_order("AAPL", "buy", Decimal(1), "other")
        with self.assertRaisesRegex(DeskError, "Historical daily bars"):
            self.store.approve_order(order["id"])
        self.assertEqual(self.snapshot()["fills"], [])
        self.assertEqual(self.snapshot()["account"]["cash"], 1000)

    def test_manual_extreme_notional_is_a_validation_error_without_write(self):
        self.fund()
        self.quote("1000000000")
        with self.assertRaisesRegex(DeskError, "integer-cents ledger range") as ctx:
            self.store.create_order("AAPL", "buy", Decimal("1000000000"), "extreme")
        self.assertEqual(ctx.exception.status, 422)
        self.assertEqual(self.snapshot()["orders"], [])

    def test_funding_cannot_promote_cash_to_sqlite_real(self):
        maximum = 2 ** 63 - 1
        with self.store.transaction() as con:
            con.execute("UPDATE account SET cash_cents=? WHERE id=1", (maximum,))
        with self.assertRaisesRegex(DeskError, "integer-cents ledger range"):
            self.fund("0.01")
        with self.store.connect() as con:
            self.assertEqual(tuple(con.execute("SELECT cash_cents,typeof(cash_cents) FROM account").fetchone()), (maximum, "integer"))
            self.assertEqual(con.execute("SELECT COUNT(*) FROM fundings").fetchone()[0], 0)

    def test_journal_scan_and_checkpoint_publication_exclude_stale_concurrent_results(self):
        self.fund()
        self.store.verify_ledger()
        scanning, release, later_finished = threading.Event(), threading.Event(), threading.Event()
        errors = []
        original_digest = Store._event_digest
        def gated_digest(row, previous):
            if threading.current_thread().name == "older-verification" and not scanning.is_set():
                scanning.set()
                if not release.wait(5):
                    raise RuntimeError("Verification fixture timed out")
            return original_digest(row, previous)
        def earlier():
            try:
                self.store.verify_ledger()
            except BaseException as exc:
                errors.append(exc)
        def later():
            try:
                self.store.fund(Decimal(1), "later-funding")
                advanced = self.store.verify_ledger()
                with self.store.transaction() as con:
                    con.execute("UPDATE events SET message='Changed after later checkpoint' WHERE id=?", (advanced["checkpoint_event_id"],))
                self.store.verify_ledger()
            except BaseException as exc:
                errors.append(exc)
            finally:
                later_finished.set()
        with patch.object(Store, "_event_digest", side_effect=gated_digest):
            old = threading.Thread(target=earlier, name="older-verification")
            newer = threading.Thread(target=later, name="newer-verification")
            old.start()
            try:
                self.assertTrue(scanning.wait(2))
                newer.start()
                # The scan holds BEGIN IMMEDIATE, so an event append and newer
                # verification cannot interleave with its checkpoint write.
                self.assertFalse(later_finished.wait(0.15))
            finally:
                release.set()
                old.join(5)
                if newer.ident is not None:
                    newer.join(5)
        self.assertFalse(errors)
        self.assertFalse(old.is_alive())
        self.assertFalse(newer.is_alive())
        status = self.store.ledger_status()
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["checkpoint_event_id"], 2)
        self.assertEqual(status["error_row"], 2)


if __name__ == "__main__":
    unittest.main()
