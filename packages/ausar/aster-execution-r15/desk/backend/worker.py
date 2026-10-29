"""Single fenced operational worker, with durable steps and restart recovery."""
import json
import threading
import time
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from .store import DeskError, Store, identifier, now
from .strategy_contract import installed_strategies


class Worker:
    LEASE_SECONDS = 45
    MAX_ATTEMPTS = 3

    def __init__(self, store: Store, reasoning):
        self.store, self.reasoning = store, reasoning
        self.owner = identifier()
        self.stop_event = threading.Event()
        self.tick_lock = threading.Lock()
        self.thread = None
        self.last_error = None
        self.last_tick = None
        self.trading = self.lab = self.research = self.providers = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name="aster-operational-worker", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=20)
        # A slow in-flight annotation retains its valid lease until its tick
        # ends. It cannot be re-entered or compete with a replacement worker.
        if not self.tick_lock.acquire(blocking=False):
            return
        try:
            self._release_lease()
        finally:
            self.tick_lock.release()

    def _release_lease(self):
        # Release only our own lock. Another process's live ownership is untouched.
        with self.store.transaction() as con:
            con.execute("UPDATE worker_lock SET owner=NULL,expires=0 WHERE owner=?", (self.owner,))
            con.execute("UPDATE tasks SET lease_until=0 WHERE lease_owner=? AND status='running'", (self.owner,))

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                self.run_once()
                self.last_error = None
            except Exception:
                # A database fault is visible in health; no fabricated successful heartbeat.
                self.last_error = "Operational worker encountered a storage or runtime error"
            self.stop_event.wait(0.25)

    def _own_lock(self, con, clock):
        row = con.execute("SELECT * FROM worker_lock WHERE id=1").fetchone()
        if row["owner"] not in {None, self.owner} and row["expires"] > clock:
            return False
        con.execute("UPDATE worker_lock SET owner=?,expires=? WHERE id=1", (self.owner, clock + self.LEASE_SECONDS))
        return True

    def _fenced(self, con, tid):
        clock = time.time()
        lock = con.execute("SELECT * FROM worker_lock WHERE id=1").fetchone()
        task = con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return bool(lock["owner"] == self.owner and lock["expires"] > clock and task and task["lease_owner"] == self.owner and task["lease_until"] > clock and task["status"] == "running")

    def run_once(self):
        if self.stop_event.is_set() or not self.tick_lock.acquire(blocking=False):
            return False
        try:
            return self._run_once()
        finally:
            try:
                if self.stop_event.is_set():
                    self._release_lease()
            finally:
                self.tick_lock.release()

    def _run_once(self):
        clock = time.time()
        with self.store.transaction() as con:
            if not self._own_lock(con, clock):
                return False
            self.last_tick = now()
            settings = self.store.settings(con)
            heartbeat = settings["heartbeat_at"]
            if not heartbeat or clock - datetime.fromisoformat(heartbeat).timestamp() >= settings["heartbeat_seconds"]:
                self.store.setting(con, "heartbeat_at", self.last_tick)
            # A crashed process cannot strand a task or duplicate an already committed step.
            for task in con.execute("SELECT * FROM tasks WHERE status='running' AND (lease_until IS NULL OR lease_until<=?)", (clock,)).fetchall():
                if task["cancel_requested"]:
                    self._cancel(con, task["id"])
                elif task["attempts"] >= self.MAX_ATTEMPTS:
                    con.execute("UPDATE tasks SET status='failed',completed_at=?,error='Restart recovery attempt limit reached',lease_owner=NULL,lease_until=NULL WHERE id=?", (now(), task["id"]))
                    con.execute("UPDATE steps SET status='failed' WHERE task_id=? AND status='running'", (task["id"],))
                    self.store.event(con, "task_failed", "worker", "Restart recovery attempt limit reached", {"task_id": task["id"]})
                else:
                    con.execute("UPDATE tasks SET status='queued',lease_owner=NULL,lease_until=NULL WHERE id=?", (task["id"],))
                    con.execute("UPDATE steps SET status='queued',started_at=NULL WHERE task_id=? AND status='running'", (task["id"],))
                    self.store.event(con, "task_recovered", "worker", "Recovered unfinished task after an expired worker lease", {"task_id": task["id"], "previous_attempts": task["attempts"]})
            for cancelled in con.execute("SELECT id FROM tasks WHERE status='queued' AND cancel_requested=1").fetchall():
                self._cancel(con, cancelled["id"])
            if settings["runtime_running"] and clock >= settings.get("next_cycle_due", 0):
                try:
                    self.store._enqueue(con, "operational_cycle", actor="scheduler")
                except DeskError as exc:
                    if exc.status != 429:
                        raise
                    self.store.event(con, "scheduled_cycle_deferred", "scheduler", "Work queue is full; existing operator work takes precedence")
                self.store.setting(con, "next_cycle_due", clock + settings["cycle_interval_seconds"])
            row = con.execute("SELECT * FROM tasks WHERE status='running' AND lease_owner=? ORDER BY created_at LIMIT 1", (self.owner,)).fetchone()
            if not row:
                row = con.execute("SELECT * FROM tasks WHERE status='queued' AND cancel_requested=0 ORDER BY created_at LIMIT 1").fetchone()
                if not row:
                    return False
                con.execute("UPDATE tasks SET status='running',started_at=COALESCE(started_at,?),attempts=attempts+1,lease_owner=?,lease_until=? WHERE id=?", (now(), self.owner, clock + self.LEASE_SECONDS, row["id"]))
                self.store.event(con, "task_started", "worker", f"Started {row['title']}", {"task_id": row["id"], "attempt": row["attempts"] + 1})
            else:
                con.execute("UPDATE tasks SET lease_until=? WHERE id=?", (clock + self.LEASE_SECONDS, row["id"]))
            tid = row["id"]
            task = dict(con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone())
            if task["cancel_requested"]:
                self._cancel(con, tid)
                return True
            step = con.execute("SELECT * FROM steps WHERE task_id=? AND status IN ('queued','running') ORDER BY sequence LIMIT 1", (tid,)).fetchone()
            if not step:
                self._finish(con, task)
                return True
            step = dict(step)
            con.execute("UPDATE steps SET status='running',started_at=COALESCE(started_at,?) WHERE id=?", (now(), step["id"]))
            handoffs = [dict(r) for r in con.execute("SELECT agent_id,result FROM steps WHERE task_id=? AND status='completed' ORDER BY sequence", (tid,))]
        try:
            # Reasoning is a side-effect-free external annotation, solely for explicitly
            # queued desk_brief/research_note. Scheduled/manual cycles are always local.
            annotation = None
            cognitive = step["agent_id"] == "coordinator" or getattr(self.reasoning, "multi_agent", False) and step["agent_id"] in {"risk_officer", "archivist"}
            if cognitive and task["kind"] in {"desk_brief", "research_note"} and self.reasoning.configured:
                context = {"title": task["title"], "kind": task["kind"], "symbol": task["symbol"], "operator_supplied_text": task["instructions"], "prior_operational_handoffs": handoffs}
                registry = installed_strategies(store=self.store)
                context.update(installed_strategies=list(registry), strategy_count=len(registry))
                extra = {"role": step["agent_id"]} if getattr(self.reasoning, "multi_agent", False) else {}
                annotation = self.reasoning.annotate(json.dumps(context), tools=lambda name: self._read_model_tool(tid, name), record_receipt=lambda receipt: self._model_receipt(tid, step["id"], receipt), **extra)
            with self.store.transaction() as con:
                if not self._fenced(con, tid):
                    return False
                result = self._operate(con, task, step, handoffs, annotation)
                con.execute("UPDATE steps SET status='completed',result=?,completed_at=? WHERE id=?", (result, now(), step["id"]))
                con.execute("UPDATE agents SET last_run_at=?,last_result=?,last_error=NULL WHERE id=?", (now(), result, step["agent_id"]))
                self.store.event(con, "agent_handoff", step["agent_id"], f"Completed {step['title']}", {"task_id": tid, "step_id": step["id"], "result": result})
                if con.execute("SELECT cancel_requested FROM tasks WHERE id=?", (tid,)).fetchone()[0]:
                    self._cancel(con, tid)
                elif not con.execute("SELECT 1 FROM steps WHERE task_id=? AND status='queued'", (tid,)).fetchone():
                    self._finish(con, task)
                return True
        except Exception as exc:
            detail = str(exc)[:1000] if isinstance(exc, RuntimeError) else "Operational step failed; no ledger effects were committed"
            with self.store.transaction() as con:
                if not self._fenced(con, tid):
                    return False
                if con.execute("SELECT cancel_requested FROM tasks WHERE id=?", (tid,)).fetchone()[0]:
                    self._cancel(con, tid)
                    return True
                attempt = con.execute("SELECT attempts FROM tasks WHERE id=?", (tid,)).fetchone()[0]
                con.execute("UPDATE agents SET last_run_at=?,last_error=?,last_result=? WHERE id=?", (now(), detail, detail, step["agent_id"]))
                self.store.event(con, "step_failed", step["agent_id"], detail, {"task_id": tid, "step_id": step["id"], "attempt": attempt})
                if attempt < self.MAX_ATTEMPTS:
                    con.execute("UPDATE tasks SET status='queued',error=?,lease_owner=NULL,lease_until=NULL WHERE id=?", (detail, tid))
                    con.execute("UPDATE steps SET status='queued',result=?,started_at=NULL WHERE id=?", (detail, step["id"]))
                else:
                    con.execute("UPDATE tasks SET status='failed',error=?,completed_at=?,lease_owner=NULL,lease_until=NULL WHERE id=?", (detail, now(), tid))
                    con.execute("UPDATE steps SET status='failed',result=?,completed_at=? WHERE id=?", (detail, now(), step["id"]))
            return True

    def _cancel(self, con, tid):
        con.execute("UPDATE tasks SET status='cancelled',completed_at=?,lease_owner=NULL,lease_until=NULL WHERE id=?", (now(), tid))
        con.execute("UPDATE steps SET status='cancelled' WHERE task_id=? AND status IN ('queued','running')", (tid,))
        self.store.event(con, "task_cancelled", "worker", "Task cancelled; completed handoffs preserved", {"task_id": tid})

    def _model_receipt(self, tid, sid, receipt):
        with self.store.transaction() as con:
            self._renew_model_lease(con, tid)
            payload = {"task_id": tid, "step_id": sid, **receipt}
            if receipt["kind"] == "tool_call":
                kind = "model_tool_receipt"
                message = f"Read-only model inspection {receipt['name']}: {receipt['status']}"
            else:
                kind = "model_provider_round"
                message = f"Model reasoning round {receipt['round']} recorded"
            agent = con.execute("SELECT agent_id FROM steps WHERE id=?", (sid,)).fetchone()[0]
            self.store.event(con, kind, agent, message, payload)

    def _renew_model_lease(self, con, tid):
        # Check ownership/expiry and cancellation before extending either
        # fence. Expired or superseded work can never reclaim authority here.
        if not self._fenced(con, tid):
            raise RuntimeError("Model task lost its worker lease")
        if con.execute("SELECT cancel_requested FROM tasks WHERE id=?", (tid,)).fetchone()[0]:
            raise RuntimeError("Operator cancelled the model task")
        until = time.time() + self.LEASE_SECONDS
        con.execute("UPDATE worker_lock SET expires=? WHERE id=1 AND owner=?", (until, self.owner))
        con.execute("UPDATE tasks SET lease_until=? WHERE id=? AND lease_owner=? AND status='running'", (until, tid, self.owner))

    def _read_model_tool(self, tid, name):
        with self.store.transaction() as con:
            self._renew_model_lease(con, tid)
        with self.store.connect() as con:
            con.execute("BEGIN")
            if not self._fenced(con, tid):
                raise RuntimeError("Model task lost its worker lease")
            task = con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
            if task["cancel_requested"]:
                raise RuntimeError("Operator cancelled the model task")
            if name == "get_account_snapshot":
                account, positions = self.store.account_public(con)
                registry = installed_strategies(con=con)
                return {"mode": "paper", "account": account, "positions": positions[:100], "total_open_positions": len(positions), "strategy_count": len(registry), "installed_strategies": list(registry)}
            if name == "audit_quote_quality":
                symbols = [r[0] for r in con.execute("SELECT symbol FROM watchlist ORDER BY symbol")]
                all_quotes = [{"symbol": sym, "quote": self.store.quote(con, sym)} for sym in symbols]
                return {"source_kind": "Each quote carries its actual manual/provider provenance; freshness is assessed from source time", "quote_max_age_seconds": self.store.settings(con)["quote_max_age_seconds"], "total_watched": len(symbols), "missing": sum(q["quote"] is None for q in all_quotes), "stale": sum(bool(q["quote"] and not q["quote"]["fresh"]) for q in all_quotes), "quotes": all_quotes[:100]}
            if name == "get_pending_intents":
                rows = list(con.execute("SELECT * FROM orders WHERE status='pending_review' ORDER BY created_at"))
                return {"operator_approval_required": True, "total_pending": len(rows), "intents": [self.store.order_public(r) for r in rows[:100]]}
            if name == "get_task_evidence":
                steps = [dict(r) for r in con.execute("SELECT agent_id,status,result FROM steps WHERE task_id=? ORDER BY sequence", (tid,))]
                events = []
                for row in con.execute("SELECT * FROM events ORDER BY id DESC LIMIT 300"):
                    payload = json.loads(row["payload"])
                    if payload.get("task_id") == tid:
                        events.append({"id": row["id"], "timestamp": row["timestamp"], "actor": row["actor"], "event_type": row["event_type"], "message": row["message"]})
                return {"task_id": tid, "title": task["title"], "symbol": task["symbol"], "operator_supplied_text": task["instructions"], "handoffs": steps, "recent_receipts": events[:30]}
            if name == "get_autonomous_books":
                if not self.trading:
                    return {"configured": False}
                state = self.trading.snapshot()
                registry = installed_strategies(con=con)
                return {"books": state["books"], "positions": state["positions"][:100], "intents": state["intents"][:50], "fills": state["fills"][:30], "strategy_count": len(registry), "installed_strategies": list(registry)}
            if name == "get_research_evidence":
                research = self.research.snapshot() if self.research else {"configured": False}
                research["receipts"] = research.get("receipts", [])[:25]
                lab = self.lab.snapshot() if self.lab else {}
                return {"observations": research, "studies": lab.get("studies", [])[:10], "proposals": lab.get("proposals", [])[:10], "scope": "Evidence only; no strategy or execution authority"}
            if name == "get_peer_inbox":
                state = self.lab.snapshot() if self.lab else {}
                return {"messages": state.get("inbox", [])[:25], "alerts": [a for a in state.get("alerts", []) if a["status"] != "resolved"][:25]}
            if name == "get_market_context":
                if not self.providers:
                    return {"configured": False}
                cached = []
                for row in con.execute("SELECT symbol,range,interval,provider,fetched_at,data FROM a_bar_cache ORDER BY fetched_at DESC LIMIT 8"):
                    item = dict(row)
                    data = json.loads(item.pop("data"))
                    if isinstance(data, dict) and "bars" in data:
                        data = {**data, "bars": data["bars"][-15:], "total_cached_bars": len(data["bars"])}
                    item["data"] = data[-15:] if isinstance(data, list) else data
                    cached.append(item)
                return {"provider": self.providers.status(), "calendar": self.providers.calendar(), "cached_bars": cached, "scope": "Calendar, bar provenance and source readiness; prices are never inferred"}
            raise RuntimeError("Unregistered read-only inspection was denied")

    def _finish(self, con, task):
        results = list(con.execute("SELECT agent_id,result FROM steps WHERE task_id=? ORDER BY sequence", (task["id"],)))
        result = "\n\n".join(f"{r['agent_id']}: {r['result']}" for r in results)
        con.execute("UPDATE tasks SET status='completed',completed_at=?,result=?,error=NULL,lease_owner=NULL,lease_until=NULL WHERE id=?", (now(), result, task["id"]))
        if task["kind"] == "operational_cycle":
            self.store.setting(con, "last_cycle_at", now())
        self.store.event(con, "task_completed", "archivist", f"Completed {task['title']}", {"task_id": task["id"], "handoff_count": len(results)})

        if self.lab and task["kind"] in {"desk_brief", "research_note"}:
            self.lab.record_agent_review(con, task, result)

    def _operate(self, con, task, step, handoffs, annotation):
        agent = step["agent_id"]
        registry = installed_strategies(con=con)
        account, positions = self.store.account_public(con)
        auto = self.trading.snapshot() if self.trading else None
        books = auto["books"] if auto else []
        book_summary = "; ".join(f"{b['name']}: cash ${b['account']['cash']:,.2f}, equity ${b['account']['equity']:,.2f}, reconciliation {b.get('reconciliation_health', {}).get('status', 'not checked')}" for b in books)
        if agent == "data_steward":
            watches = list(con.execute("SELECT symbol FROM watchlist ORDER BY symbol"))
            fresh, stale, missing = [], [], []
            for row in watches:
                quote = self.store.quote(con, row[0])
                (missing if not quote else fresh if quote["fresh"] else stale).append(row[0])
            sources = sorted({q[0] for q in con.execute("SELECT DISTINCT source FROM quotes")})
            return f"Data audit: {len(watches)} watched symbols; {len(fresh)} fresh, {len(stale)} stale, {len(missing)} missing quotes. Recorded sources: {', '.join(sources) or 'none'}. Stale: {', '.join(stale) or 'none'}. Missing: {', '.join(missing) or 'none'}. This inspection fetched no external data."
        if agent == "accountant":
            funded = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM fundings").fetchone()[0]
            cash, realized = funded, 0
            rebuilt = {}
            # Wall-clock changes cannot reorder already committed ledger effects.
            for fill in con.execute("SELECT * FROM fills ORDER BY rowid"):
                sym, qty = fill["symbol"], Decimal(fill["quantity"])
                current = rebuilt.setdefault(sym, [Decimal(0), 0, 0])
                if fill["side"] == "buy":
                    cash -= fill["notional_cents"]
                    current[0] += qty
                    current[1] += fill["notional_cents"]
                else:
                    if qty > current[0]:
                        raise RuntimeError("Reconciliation failed: fill exceeds reconstructed holdings")
                    basis = current[1] if qty == current[0] else int((Decimal(current[1]) * qty / current[0]).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                    gain = fill["notional_cents"] - basis
                    if basis != fill["basis_cents"] or gain != fill["realized_cents"]:
                        raise RuntimeError("Reconciliation failed: recorded sale cost basis differs from average-cost ledger")
                    current[0] -= qty
                    current[1] -= basis
                    current[2] += gain
                    cash += fill["notional_cents"]
                    realized += gain
            stored = con.execute("SELECT * FROM account WHERE id=1").fetchone()
            if stored["cash_cents"] != cash or stored["realized_cents"] != realized:
                raise RuntimeError("Reconciliation failed: funding/fills do not match account balances")
            actual_positions = {r["symbol"]: [Decimal(r["quantity"]), r["cost_cents"], r["realized_cents"]] for r in con.execute("SELECT * FROM positions")}
            if actual_positions != rebuilt:
                raise RuntimeError("Reconciliation failed: reconstructed positions differ from paper book")
            self.store.balance_snapshot(con, step["id"])
            return f"Reconciliation passed (separate manual ledger): funding ${funded / 100:,.2f}; cash ${cash / 100:,.2f}; realized P&L ${realized / 100:,.2f}; {len(positions)} open positions. Funding and fill ledger independently reconstructed, including average-cost sale basis. A balance snapshot was recorded." + ("\nIndependent autonomous books (last observed reconciliation): " + book_summary if books else "")
        if agent == "risk_officer":
            stale = [p["symbol"] for p in positions if not p["quote_fresh"]]
            sells = [(r["symbol"], r["quantity"]) for r in con.execute("SELECT symbol,quantity FROM orders WHERE status='pending_review' AND side='sell'")]
            text = f"Manual-ledger exposure: marked value ${account['market_value']:,.2f}; reserved paper cash ${account['reserved_cash']:,.2f}; available cash ${account['available_cash']:,.2f}; {account['missing_marks']} missing marks. Stale or missing position marks: {', '.join(stale) or 'none'}. Pending sell reservations: {json.dumps(sells)}."
            for book in books:
                a, p = book["account"], book["policy"]
                text += f"\n{book['name']}: gross ${a['gross_exposure']:,.2f}; reserved ${a['reserved_cash']:,.2f}; missing/stale marks {a['missing_marks']}/{a['stale_marks']}; drawdown {a['drawdown_percent']:.2f}%; halted {p['halted']}; policy version {book['policy_version']}."
            return text + " No trade recommendations or policy changes." + ("\n\nIndependent risk model review:\n" + annotation if annotation else "")
        if agent == "execution_clerk":
            pending = list(con.execute("SELECT id,symbol,side,quantity FROM orders WHERE status='pending_review' ORDER BY created_at"))
            details = "; ".join(f"{r['side']} {r['quantity']} {r['symbol']} ({r['id'][:8]})" for r in pending)
            text = f"{len(pending)} separate manual-ledger intentions await operator approval or cancellation. {details or 'No manual action is waiting.'}"
            if auto:
                active = [i for i in auto["intents"] if i["status"] not in {"filled", "cancelled", "expired", "rejected"}]
                text += f"\n{len(active)} independently authorized autonomous intents; {len(auto['fills'])} recorded execution receipts. Pending states: " + "; ".join(f"{i['symbol']} {i['status']}: {i.get('error') or 'awaiting order/session condition'}" for i in active[:20])
            return text + " This review did not originate or mutate any order."
        if agent == "coordinator":
            if task["kind"] == "research_note":
                text = f"Supplied note preserved verbatim. Symbol: {task['symbol'] or 'not specified'}.\n\n{task['instructions'] or '(No source text supplied.)'}\n\nThe note itself is evidence supplied to this task; independent source receipts are inspected separately."
            else:
                text = f"Operational brief: {len(handoffs)} completed handoffs; separate manual-ledger cash ${account['cash']:,.2f}, {len(positions)} manual positions. Independent autonomous books: {book_summary or 'not bound to this worker'}. {len(registry)} installed deterministic paper strategies; this review has no order authority."
                if task["instructions"]:
                    text += "\n\nOperator-supplied instructions: " + task["instructions"]
                text += "\n\n" + "\n".join(f"{h['agent_id']}: {h['result']}" for h in handoffs)
            if annotation:
                text += "\n\nOptional model annotation (read-only operational tools; no trade execution authority):\n" + annotation
            return text
        if agent == "archivist":
            return f"Preserved {len(handoffs)} completed handoffs, task title, operator text, source symbol and UTC receipts in the durable desk journal. Task {task['id']}." + ("\n\nIndependent Journal & Coach model review:\n" + annotation if annotation else "")
        raise RuntimeError("Unknown operational agent")

    def health(self):
        clock = time.time()
        with self.store.connect() as con:
            lock = con.execute("SELECT * FROM worker_lock WHERE id=1").fetchone()
            result = con.execute("PRAGMA quick_check").fetchone()[0]
            registry = installed_strategies(con=con)
        own_active = lock["owner"] == self.owner and lock["expires"] > clock
        return {"worker": {"alive": bool(self.thread and self.thread.is_alive()), "owns_lease": own_active, "lease_active": bool(lock["owner"] and lock["expires"] > clock), "last_tick_at": self.last_tick, "error": self.last_error}, "database": {"status": "ok" if result == "ok" else "error", "journal_mode": "wal"}, "reasoning": {**self.reasoning.status(), "reachability": "not checked", "last_success_at": self.reasoning.last_success_at, "last_error": self.reasoning.last_error}, "market_data": "manual; no external feed", "broker": "paper ledger; no live broker", "strategy_count": len(registry), "installed_strategies": list(registry)}
