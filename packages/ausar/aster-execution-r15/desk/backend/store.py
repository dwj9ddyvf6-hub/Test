"""Durable desk state. All ledger mutations run under SQLite BEGIN IMMEDIATE.

Cash and cost basis are integer cents. Quantities/prices use exact Decimal text;
only the public JSON boundary uses floating point numbers. Pending intentions
reserve existing cash/shares but can never create a fill without approval.
"""
import json
import base64
import hashlib
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .strategy_contract import installed_strategies


UTC = timezone.utc
AGENTS = [
    ("coordinator", "Coordinator", "Composes factual briefs and durable handoffs", ["Operational brief", "Task coordination"]),
    ("data_steward", "Data steward", "Audits manually supplied quotes and their provenance", ["Quote freshness", "Coverage audit"]),
    ("accountant", "Accountant", "Reconciles funding, fills and the paper book", ["Ledger reconciliation", "Balance snapshots"]),
    ("risk_officer", "Risk officer", "Reports actual reservations, marks and exposure", ["Reservation audit", "Exposure reporting"]),
    ("execution_clerk", "Execution clerk", "Reports manual approvals and autonomous operator-authorized order lifecycle", ["Legacy manual approval handoff", "Autonomous intent execution receipts"]),
    ("archivist", "Archivist", "Preserves supplied notes and workflow outcomes", ["Evidence preservation", "Completion journal"]),
]
WORKFLOWS = {
    "operational_cycle": ["data_steward", "accountant", "risk_officer", "execution_clerk", "coordinator", "archivist"],
    "desk_brief": ["data_steward", "accountant", "risk_officer", "execution_clerk", "coordinator", "archivist"],
    "data_audit": ["data_steward", "coordinator", "archivist"],
    "reconcile": ["accountant", "risk_officer", "archivist"],
    "research_note": ["coordinator", "archivist"],
}
DEFAULTS = {"quote_max_age_seconds": 300, "heartbeat_seconds": 2, "cycle_interval_seconds": 60}


class DeskError(Exception):
    def __init__(self, detail: str, status: int = 409):
        self.detail, self.status = detail, status
        super().__init__(detail)


def now() -> str:
    return datetime.now(UTC).isoformat()


def identifier() -> str:
    return uuid.uuid4().hex


def symbol(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{0,9}(?:[.-][A-Z0-9]{1,4})?", value) or len(value) > 15:
        raise DeskError("Enter a valid equity symbol, such as AAPL or BRK.B", 422)
    return value


def cents(value: Decimal) -> int:
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def checked_cents(value: int, name="Ledger value") -> int:
    """SQLite promotes overflowing arithmetic to REAL; reject it before writing."""
    if not isinstance(value, int) or not -(2 ** 63) <= value <= 2 ** 63 - 1:
        raise DeskError(name + " exceeds the exact integer-cents ledger range", 422)
    return value


def number(value) -> float:
    return float(Decimal(str(value)))


def rowdict(row):
    return dict(row) if row is not None else None


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY CHECK(id=1),cash_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL);
                INSERT OR IGNORE INTO account VALUES(1,0,0);
                CREATE TABLE IF NOT EXISTS fundings(id TEXT PRIMARY KEY,client_id TEXT NOT NULL UNIQUE,amount_cents INTEGER NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS watchlist(symbol TEXT PRIMARY KEY,added_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS quotes(symbol TEXT PRIMARY KEY,price TEXT NOT NULL,as_of TEXT NOT NULL,source TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS a_quote_history(id TEXT PRIMARY KEY,symbol TEXT NOT NULL,provider TEXT NOT NULL,provider_asof TEXT NOT NULL,observed_at TEXT NOT NULL,price TEXT NOT NULL,source TEXT NOT NULL,content_sha256 TEXT NOT NULL UNIQUE,accepted INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,client_id TEXT NOT NULL UNIQUE,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,type TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,filled_at TEXT,fill_price TEXT,reason TEXT,reserve_cents INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS fills(id TEXT PRIMARY KEY,order_id TEXT NOT NULL UNIQUE REFERENCES orders(id),symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,notional_cents INTEGER NOT NULL,basis_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL,timestamp TEXT NOT NULL,source TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS positions(symbol TEXT PRIMARY KEY,quantity TEXT NOT NULL,cost_cents INTEGER NOT NULL,realized_cents INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,actor TEXT NOT NULL,timestamp TEXT NOT NULL,message TEXT NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,task_step_id TEXT UNIQUE,timestamp TEXT NOT NULL,equity_cents INTEGER NOT NULL,cash_cents INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,instructions TEXT,symbol TEXT,status TEXT NOT NULL,created_at TEXT NOT NULL,started_at TEXT,completed_at TEXT,result TEXT,error TEXT,attempts INTEGER NOT NULL DEFAULT 0,lease_owner TEXT,lease_until REAL,cancel_requested INTEGER NOT NULL DEFAULT 0);
                CREATE UNIQUE INDEX IF NOT EXISTS active_cycle ON tasks(kind) WHERE kind='operational_cycle' AND status IN ('queued','running');
                CREATE TABLE IF NOT EXISTS steps(id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id),sequence INTEGER NOT NULL,agent_id TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL,result TEXT,started_at TEXT,completed_at TEXT,UNIQUE(task_id,sequence));
                CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY,last_run_at TEXT,last_result TEXT,last_error TEXT);
                CREATE TABLE IF NOT EXISTS worker_lock(id INTEGER PRIMARY KEY CHECK(id=1),owner TEXT,expires REAL);
                INSERT OR IGNORE INTO worker_lock(id,owner,expires) VALUES(1,NULL,0);
                CREATE INDEX IF NOT EXISTS task_status_created ON tasks(status,created_at);
                CREATE INDEX IF NOT EXISTS steps_task_sequence ON steps(task_id,sequence);
            """)
            for key, value in {**DEFAULTS, "runtime_running": False, "last_cycle_at": None, "heartbeat_at": None}.items():
                con.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (key, json.dumps(value)))
            for agent in AGENTS:
                con.execute("INSERT OR IGNORE INTO agents(id) VALUES(?)", (agent[0],))
            event_columns = {r[1] for r in con.execute("PRAGMA table_info(events)")}
            migrated_chain = "event_hash" not in event_columns
            for column in ("prev_hash", "event_hash"):
                if column not in event_columns:
                    con.execute(f"ALTER TABLE events ADD COLUMN {column} TEXT")
            if migrated_chain:
                previous = "0" * 64
                for row in con.execute("SELECT * FROM events ORDER BY id").fetchall():
                    digest = self._event_digest(row, previous)
                    con.execute("UPDATE events SET prev_hash=?,event_hash=? WHERE id=?", (previous, digest, row["id"]))
                    previous = digest
        self.verify_ledger()

    def connect(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=15000")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    @contextmanager
    def transaction(self):
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def settings(con):
        return {r["key"]: json.loads(r["value"]) for r in con.execute("SELECT * FROM settings")}

    @staticmethod
    def setting(con, key, value):
        con.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value)))

    @staticmethod
    def event(con, kind, actor, message, payload=None):
        previous_row = con.execute("SELECT event_hash FROM events ORDER BY id DESC LIMIT 1").fetchone()
        previous = previous_row[0] if previous_row else "0" * 64
        cursor = con.execute("INSERT INTO events(event_type,actor,timestamp,message,payload,prev_hash) VALUES(?,?,?,?,?,?)", (kind, actor, now(), message, json.dumps(payload or {}), previous))
        row = con.execute("SELECT * FROM events WHERE id=?", (cursor.lastrowid,)).fetchone()
        con.execute("UPDATE events SET event_hash=? WHERE id=?", (Store._event_digest(row, previous), row["id"]))

    @staticmethod
    def _event_digest(row, previous):
        canonical = {"id": row["id"], "event_type": row["event_type"], "actor": row["actor"], "timestamp": row["timestamp"], "message": row["message"], "payload": json.loads(row["payload"]), "prev_hash": previous}
        return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

    def verify_ledger(self):
        previous, count, error_row = "0" * 64, 0, None
        # Scan and checkpoint/status publication share one writer transaction.
        # Otherwise a slower verification can overwrite a newer checkpoint or
        # failure status after another worker has already inspected later rows.
        with self.transaction() as con:
            prior_status = self.settings(con).get("journal_integrity", {})
            checkpoint_id = prior_status.get("checkpoint_event_id")
            checkpoint_hash = prior_status.get("checkpoint_hash")
            checkpoint_seen = checkpoint_id is None
            latest_id = None
            for row in con.execute("SELECT * FROM events ORDER BY id"):
                count += 1
                latest_id = row["id"]
                try:
                    computed = self._event_digest(row, previous)
                    if row["prev_hash"] != previous or row["event_hash"] != computed:
                        error_row = row["id"]
                        break
                    previous = row["event_hash"]
                    if row["id"] == checkpoint_id:
                        checkpoint_seen = True
                        if previous != checkpoint_hash:
                            error_row = row["id"]
                            break
                except (TypeError, ValueError):
                    error_row = row["id"]
                    break
            if error_row is None and not checkpoint_seen:
                error_row = checkpoint_id
            if error_row is None:
                checkpoint_id, checkpoint_hash = latest_id, previous
            result = {"status": "ok" if error_row is None else "failed", "checked_at": now(), "verified_events": count if error_row is None else max(count - 1, 0), "last_verified_hash": previous, "error_row": error_row, "checkpoint_event_id": checkpoint_id, "checkpoint_hash": checkpoint_hash}
            self.setting(con, "journal_integrity", result)
        return result

    def ledger_status(self):
        with self.connect() as con:
            status = self.settings(con).get("journal_integrity", {"status": "not_checked"})
            latest = con.execute("SELECT id,event_hash FROM events ORDER BY id DESC LIMIT 1").fetchone()
            return {**status, "latest_event_id": latest["id"] if latest else None, "latest_event_hash": latest["event_hash"] if latest else "0" * 64, "cached": True}

    def quote(self, con, sym, settings=None):
        row = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
        if not row:
            return None
        data = dict(row)
        age = (datetime.now(UTC) - datetime.fromisoformat(row["as_of"])).total_seconds()
        data["fresh"] = -5 <= age <= (settings or self.settings(con))["quote_max_age_seconds"]
        data["price"] = number(row["price"])
        return data

    def fresh_quote(self, con, sym):
        quote = self.quote(con, sym)
        if not quote or not quote["fresh"]:
            raise DeskError("A fresh manually supplied quote is required before creating or approving a paper order")
        if any(word in quote["source"].lower() for word in ("historical", "daily bar", "daily close")):
            raise DeskError("Historical daily bars cannot authorize intraday fills")
        return con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()

    @staticmethod
    def reserved_cash(con, exclude=None):
        return con.execute("SELECT COALESCE(SUM(reserve_cents),0) FROM orders WHERE status='pending_review' AND id != ?", (exclude or "",)).fetchone()[0]

    @staticmethod
    def reserved_shares(con, sym, exclude=None):
        return sum((Decimal(r[0]) for r in con.execute("SELECT quantity FROM orders WHERE status='pending_review' AND side='sell' AND symbol=? AND id != ?", (sym, exclude or ""))), Decimal(0))

    def fund(self, amount: Decimal, client_id: str):
        if not amount.is_finite():
            raise DeskError("Funding must be a positive whole-cent amount", 422)
        amount_cents = cents(amount)
        if amount_cents <= 0 or Decimal(amount_cents) / 100 != amount:
            raise DeskError("Funding must be a positive whole-cent amount", 422)
        with self.transaction() as con:
            existing = con.execute("SELECT * FROM fundings WHERE client_id=?", (client_id,)).fetchone()
            if existing:
                if existing["amount_cents"] != amount_cents:
                    raise DeskError("client_id has already been used with different funding")
                return {"id": existing["id"], "client_id": client_id, "amount": amount_cents / 100, "created_at": existing["created_at"]}
            rid, ts = identifier(), now()
            cash = checked_cents(con.execute("SELECT cash_cents FROM account WHERE id=1").fetchone()[0] + amount_cents, "Funded cash")
            checked_cents(sum(row[0] for row in con.execute("SELECT amount_cents FROM fundings")) + amount_cents, "Total contributed capital")
            con.execute("INSERT INTO fundings VALUES(?,?,?,?)", (rid, client_id, amount_cents, ts))
            con.execute("UPDATE account SET cash_cents=? WHERE id=1", (cash,))
            self.event(con, "paper_funding", "operator", f"Operator added ${amount_cents / 100:,.2f} in paper cash", {"funding_id": rid, "amount": amount_cents / 100})
            self.balance_snapshot(con)
            return {"id": rid, "client_id": client_id, "amount": amount_cents / 100, "created_at": ts}

    def add_watch(self, sym):
        sym = symbol(sym)
        with self.transaction() as con:
            existing = con.execute("SELECT * FROM watchlist WHERE symbol=?", (sym,)).fetchone()
            if not existing:
                con.execute("INSERT INTO watchlist VALUES(?,?)", (sym, now()))
                self.event(con, "watch_added", "operator", f"Added {sym} to the watchlist", {"symbol": sym})
            result = dict(con.execute("SELECT * FROM watchlist WHERE symbol=?", (sym,)).fetchone())
            result["quote"] = self.quote(con, sym)
            return result

    def remove_watch(self, sym):
        sym = symbol(sym)
        with self.transaction() as con:
            deleted = con.execute("DELETE FROM watchlist WHERE symbol=?", (sym,)).rowcount
            if deleted:
                self.event(con, "watch_removed", "operator", f"Removed {sym} from the watchlist", {"symbol": sym})
            return {"symbol": sym, "removed": bool(deleted)}

    def ingest_quote(self, sym, price: Decimal, as_of: datetime, source: str, provider="manual"):
        sym = symbol(sym)
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise DeskError("Quote timestamp must include a timezone", 422)
        as_of = as_of.astimezone(UTC)
        if (as_of - datetime.now(UTC)).total_seconds() > 5:
            raise DeskError("Quote timestamp cannot be in the future", 422)
        if not price.is_finite() or price <= 0 or not source.strip():
            raise DeskError("Quote needs a positive finite price and explicit source", 422)
        timestamp = as_of.isoformat()
        receipt = {"symbol": sym, "provider": provider, "provider_asof": timestamp, "price": str(price), "source": source}
        digest = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.transaction() as con:
            current = con.execute("SELECT * FROM quotes WHERE symbol=?", (sym,)).fetchone()
            if current:
                old = datetime.fromisoformat(current["as_of"])
                if as_of < old:
                    raise DeskError("An older quote cannot replace a newer quote")
                if as_of == old:
                    if Decimal(current["price"]) != price or current["source"] != source:
                        raise DeskError("This quote timestamp already has different price or provenance")
                    con.execute("INSERT OR IGNORE INTO a_quote_history VALUES(?,?,?,?,?,?,?,?,1)", (identifier(), sym, provider, timestamp, now(), str(price), source, digest))
                    return self.quote(con, sym)
            con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", (sym, str(price), timestamp, source))
            con.execute("INSERT OR IGNORE INTO a_quote_history VALUES(?,?,?,?,?,?,?,?,1)", (identifier(), sym, provider, timestamp, now(), str(price), source, digest))
            con.execute("INSERT OR IGNORE INTO watchlist VALUES(?,?)", (sym, now()))
            self.event(con, "manual_quote", "operator", f"Recorded a manual quote for {sym}", {"symbol": sym, "price": number(price), "as_of": timestamp, "source": source})
            return self.quote(con, sym)

    @staticmethod
    def order_public(row):
        return {k: number(row[k]) if k in {"quantity", "fill_price"} and row[k] is not None else row[k] for k in ("id", "client_id", "symbol", "side", "quantity", "type", "status", "created_at", "filled_at", "fill_price", "reason")}

    def create_order(self, sym, side, quantity: Decimal, client_id, order_type="market"):
        sym = symbol(sym)
        if side not in {"buy", "sell"} or order_type != "market" or not quantity.is_finite() or quantity <= 0:
            raise DeskError("A valid positive paper market order is required", 422)
        with self.transaction() as con:
            existing = con.execute("SELECT * FROM orders WHERE client_id=?", (client_id,)).fetchone()
            if existing:
                if (existing["symbol"], existing["side"], Decimal(existing["quantity"]), existing["type"]) != (sym, side, quantity, order_type):
                    raise DeskError("client_id has already been used with a different order")
                return self.order_public(existing)
            quote = self.fresh_quote(con, sym)
            notional = checked_cents(cents(quantity * Decimal(quote["price"])), "Order notional")
            if notional < 1:
                raise DeskError("Paper order notional must be at least one cent", 422)
            if side == "buy":
                cash = con.execute("SELECT cash_cents FROM account WHERE id=1").fetchone()[0]
                if cash - self.reserved_cash(con) < notional:
                    raise DeskError("Insufficient unreserved paper cash")
            else:
                position = con.execute("SELECT quantity FROM positions WHERE symbol=?", (sym,)).fetchone()
                if (Decimal(position[0]) if position else Decimal(0)) - self.reserved_shares(con, sym) < quantity:
                    raise DeskError("Insufficient unreserved paper shares; short selling is unavailable")
            rid = identifier()
            con.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (rid, client_id, sym, side, str(quantity), order_type, "pending_review", now(), None, None, None, notional if side == "buy" else 0))
            self.event(con, "order_intent", "operator", f"Operator submitted {side} {quantity} {sym} for paper approval", {"order_id": rid, "reserved_cash": notional / 100 if side == "buy" else 0})
            return self.order_public(con.execute("SELECT * FROM orders WHERE id=?", (rid,)).fetchone())

    def approve_order(self, rid):
        with self.transaction() as con:
            order = con.execute("SELECT * FROM orders WHERE id=?", (rid,)).fetchone()
            if not order:
                raise DeskError("Paper order not found", 404)
            if order["status"] == "filled":
                return self.order_public(order)
            if order["status"] != "pending_review":
                raise DeskError("Only a pending paper order can be approved")
            quote = self.fresh_quote(con, order["symbol"])
            qty, price = Decimal(order["quantity"]), Decimal(quote["price"])
            notional = checked_cents(cents(qty * price), "Fill notional")
            if notional < 1:
                raise DeskError("Paper order notional must be at least one cent", 422)
            account = con.execute("SELECT * FROM account WHERE id=1").fetchone()
            pos = con.execute("SELECT * FROM positions WHERE symbol=?", (order["symbol"],)).fetchone()
            old_qty, old_cost, old_realized = (Decimal(pos["quantity"]), pos["cost_cents"], pos["realized_cents"]) if pos else (Decimal(0), 0, 0)
            basis, realized = 0, 0
            if order["side"] == "buy":
                if account["cash_cents"] - self.reserved_cash(con, rid) < notional:
                    raise DeskError("Quote changed: insufficient unreserved cash to approve this order")
                new_qty, new_cost, cash_delta = old_qty + qty, old_cost + notional, -notional
            else:
                if old_qty - self.reserved_shares(con, order["symbol"], rid) < qty:
                    raise DeskError("Insufficient unreserved shares to approve this order")
                basis = old_cost if qty == old_qty else int((Decimal(old_cost) * qty / old_qty).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                realized = notional - basis
                new_qty, new_cost, cash_delta = old_qty - qty, old_cost - basis, notional
            ts, fid = now(), identifier()
            cash = checked_cents(account["cash_cents"] + cash_delta, "Resulting cash")
            realized_total = checked_cents(account["realized_cents"] + realized, "Realized P&L")
            checked_cents(new_cost, "Position cost basis")
            checked_cents(old_realized + realized, "Position realized P&L")
            # Validate the valuation receipt before mutating the ledger.
            marked = sum((cents(Decimal(row["quantity"]) * Decimal(row["price"])) for row in con.execute("SELECT p.quantity,q.price FROM positions p JOIN quotes q ON q.symbol=p.symbol WHERE p.symbol!=?", (order["symbol"],))), cents(new_qty * price))
            checked_cents(cash + marked, "Resulting equity")
            con.execute("UPDATE account SET cash_cents=?,realized_cents=? WHERE id=1", (cash, realized_total))
            con.execute("INSERT OR REPLACE INTO positions VALUES(?,?,?,?)", (order["symbol"], str(new_qty), new_cost, old_realized + realized))
            con.execute("INSERT INTO fills VALUES(?,?,?,?,?,?,?,?,?,?,?)", (fid, rid, order["symbol"], order["side"], str(qty), str(price), notional, basis, realized, ts, quote["source"]))
            con.execute("UPDATE orders SET status='filled',filled_at=?,fill_price=?,reserve_cents=0 WHERE id=?", (ts, str(price), rid))
            self.event(con, "paper_fill", "operator", f"Operator approved paper {order['side']} {qty} {order['symbol']} at ${price}", {"order_id": rid, "fill_id": fid, "quote_as_of": quote["as_of"], "source": quote["source"], "notional": notional / 100, "realized_pnl": realized / 100})
            self.balance_snapshot(con)
            return self.order_public(con.execute("SELECT * FROM orders WHERE id=?", (rid,)).fetchone())

    def cancel_order(self, rid):
        with self.transaction() as con:
            row = con.execute("SELECT * FROM orders WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Paper order not found", 404)
            if row["status"] == "filled":
                raise DeskError("A filled paper order cannot be cancelled")
            if row["status"] == "pending_review":
                con.execute("UPDATE orders SET status='cancelled',reserve_cents=0,reason='Cancelled by operator' WHERE id=?", (rid,))
                self.event(con, "order_cancelled", "operator", "Operator cancelled a pending paper intention", {"order_id": rid})
            return self.order_public(con.execute("SELECT * FROM orders WHERE id=?", (rid,)).fetchone())

    def account_public(self, con, settings=None):
        settings = settings or self.settings(con)
        a = con.execute("SELECT * FROM account WHERE id=1").fetchone()
        positions, mv, pnl, missing = [], 0, 0, 0
        for pos in con.execute("SELECT * FROM positions WHERE CAST(quantity AS REAL)>0 ORDER BY symbol"):
            qty = Decimal(pos["quantity"])
            quote = self.quote(con, pos["symbol"], settings)
            # Missing marks are visibly omitted from market value and P&L; no fabricated mark.
            raw_quote = con.execute("SELECT price FROM quotes WHERE symbol=?", (pos["symbol"],)).fetchone()
            value = cents(qty * Decimal(raw_quote[0])) if raw_quote else 0
            unrealized = value - pos["cost_cents"] if quote else 0
            mv += value
            pnl += unrealized
            missing += int(quote is None)
            positions.append({"symbol": pos["symbol"], "quantity": number(qty), "average_cost": number(Decimal(pos["cost_cents"]) / 100 / qty), "mark_price": quote["price"] if quote else None, "market_value": value / 100, "unrealized_pnl": unrealized / 100, "realized_pnl": pos["realized_cents"] / 100, "quote_fresh": bool(quote and quote["fresh"])})
        reserved = self.reserved_cash(con)
        return {"currency": "USD", "cash": a["cash_cents"] / 100, "equity": (a["cash_cents"] + mv) / 100, "market_value": mv / 100, "reserved_cash": reserved / 100, "available_cash": (a["cash_cents"] - reserved) / 100, "realized_pnl": a["realized_cents"] / 100, "unrealized_pnl": pnl / 100, "missing_marks": missing}, positions

    def balance_snapshot(self, con, step_id=None):
        cash_cents = con.execute("SELECT cash_cents FROM account WHERE id=1").fetchone()[0]
        marked_cents = sum((cents(Decimal(row["quantity"]) * Decimal(row["price"])) for row in con.execute("SELECT p.quantity,q.price FROM positions p JOIN quotes q ON q.symbol=p.symbol WHERE CAST(p.quantity AS REAL)>0")), 0)
        con.execute("INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?)", (identifier(), step_id, now(), checked_cents(cash_cents + marked_cents, "Recorded equity"), cash_cents))

    def _enqueue(self, con, kind, title=None, instructions=None, sym=None, actor="operator"):
        if kind not in WORKFLOWS:
            raise DeskError("Unsupported operational task", 422)
        if kind == "operational_cycle":
            existing = con.execute("SELECT * FROM tasks WHERE kind=? AND status IN ('queued','running')", (kind,)).fetchone()
            if existing:
                return self.task_public(con, existing)
        if con.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('queued','running')").fetchone()[0] >= 100:
            raise DeskError("Work queue is full; finish or cancel queued work", 429)
        rid = identifier()
        title = title or {"operational_cycle": "Desk operating cycle", "desk_brief": "Operational desk brief", "data_audit": "Manual data audit", "reconcile": "Paper book reconciliation", "research_note": "Preserve a research note"}[kind]
        con.execute("INSERT INTO tasks(id,kind,title,instructions,symbol,status,created_at) VALUES(?,?,?,?,?,'queued',?)", (rid, kind, title, instructions, sym, now()))
        names = {a[0]: a[1] for a in AGENTS}
        for index, agent in enumerate(WORKFLOWS[kind]):
            con.execute("INSERT INTO steps(id,task_id,sequence,agent_id,title,status) VALUES(?,?,?,?,?,'queued')", (identifier(), rid, index, agent, names[agent] + " handoff"))
        self.event(con, "task_queued", actor, f"Queued {title}", {"task_id": rid, "kind": kind})
        return self.task_public(con, con.execute("SELECT * FROM tasks WHERE id=?", (rid,)).fetchone())

    def enqueue(self, kind, title=None, instructions=None, sym=None):
        if sym:
            sym = symbol(sym)
        with self.transaction() as con:
            return self._enqueue(con, kind, title, instructions, sym)

    @staticmethod
    def task_public(con, row):
        data = {k: row[k] for k in ("id", "kind", "title", "status", "created_at", "started_at", "completed_at", "result", "error")}
        data["steps"] = [{k: r[k] for k in ("id", "agent_id", "title", "status", "result")} for r in con.execute("SELECT * FROM steps WHERE task_id=? ORDER BY sequence", (row["id"],))]
        return data

    def cancel_task(self, rid):
        with self.transaction() as con:
            row = con.execute("SELECT * FROM tasks WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Task not found", 404)
            if row["status"] in {"queued", "running"}:
                # The running step may finish. The worker observes the fence before any next step.
                con.execute("UPDATE tasks SET cancel_requested=1 WHERE id=?", (rid,))
                if row["status"] == "queued":
                    con.execute("UPDATE tasks SET status='cancelled',completed_at=? WHERE id=?", (now(), rid))
                    con.execute("UPDATE steps SET status='cancelled' WHERE task_id=? AND status='queued'", (rid,))
                self.event(con, "task_cancel_requested", "operator", "Operator requested task cancellation", {"task_id": rid})
            return self.task_public(con, con.execute("SELECT * FROM tasks WHERE id=?", (rid,)).fetchone())

    def runtime(self, running):
        with self.transaction() as con:
            self.setting(con, "runtime_running", running)
            self.event(con, "runtime_changed", "operator", "Recurring desk cycles started" if running else "Recurring desk cycles paused", {"running": running})
            return {"running": running}

    def update_settings(self, changes):
        bounds = {"quote_max_age_seconds": (1, 86400), "heartbeat_seconds": (1, 60), "cycle_interval_seconds": (5, 86400)}
        with self.transaction() as con:
            for key, value in changes.items():
                if value is None:
                    continue
                if key not in bounds or not isinstance(value, int) or not bounds[key][0] <= value <= bounds[key][1]:
                    raise DeskError("Invalid desk setting", 422)
                self.setting(con, key, value)
            self.event(con, "settings_updated", "operator", "Updated operating settings", {k: v for k, v in changes.items() if v is not None})
            settings = self.settings(con)
            return {key: settings[key] for key in DEFAULTS}

    def snapshot(self, reasoning):
        with self.connect() as con:
            # A read transaction keeps cash, reservations, fills and tasks mutually consistent.
            con.execute("BEGIN")
            s = self.settings(con)
            strategies = installed_strategies(con=con)
            account, positions = self.account_public(con, s)
            agents = []
            for aid, name, role, capabilities in AGENTS:
                a = con.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
                working = con.execute("SELECT 1 FROM steps st JOIN tasks t ON t.id=st.task_id JOIN worker_lock wl ON wl.id=1 AND wl.owner=t.lease_owner WHERE st.agent_id=? AND st.status='running' AND t.status='running' AND t.lease_until>? AND wl.expires>?", (aid, time.time(), time.time())).fetchone()
                agents.append({"id": aid, "name": name, "role": role, "capabilities": capabilities, "status": "working" if working else "error" if a["last_error"] else "idle", "last_run_at": a["last_run_at"], "last_result": a["last_result"]})
            result = {
                "desk": {"name": "Aster Desk", "mode": "paper", "strategy_count": len(strategies), "runtime": {"running": s["runtime_running"], "last_cycle_at": s["last_cycle_at"], "heartbeat_at": s["heartbeat_at"]}, "reasoning": reasoning},
                "account": account, "positions": positions,
                "orders": [self.order_public(r) for r in con.execute("SELECT * FROM orders ORDER BY created_at DESC")],
                "fills": [{"id": r["id"], "order_id": r["order_id"], "symbol": r["symbol"], "side": r["side"], "quantity": number(r["quantity"]), "price": number(r["price"]), "notional": r["notional_cents"] / 100, "timestamp": r["timestamp"], "source": r["source"]} for r in con.execute("SELECT * FROM fills ORDER BY timestamp DESC")],
                "agents": agents,
                "tasks": [self.task_public(con, r) for r in con.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 200")],
                "watchlist": [{"symbol": r["symbol"], "added_at": r["added_at"], "quote": self.quote(con, r["symbol"], s)} for r in con.execute("SELECT * FROM watchlist ORDER BY symbol")],
                "events": [{**dict(r), "payload": json.loads(r["payload"])} for r in con.execute("SELECT * FROM events ORDER BY id DESC LIMIT 300")],
                "equity_history": [{"timestamp": r["timestamp"], "equity": r["equity_cents"] / 100, "cash": r["cash_cents"] / 100} for r in con.execute("SELECT * FROM (SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT 1000) ORDER BY timestamp")],
                "settings": {k: s[k] for k in DEFAULTS},
                "connections": {"market_data": {"kind": "manual", "status": "Manual quotes only; no external feed"}, "broker": {"kind": "paper", "status": "Local paper ledger; no live broker"}, "reasoning": reasoning},
                "strategy_slots": list(strategies),
            }
            return result

    def export(self, reasoning):
        with self.connect() as con:
            con.execute("BEGIN")
            tables = ("settings", "account", "fundings", "watchlist", "quotes", "orders", "fills", "positions", "events", "snapshots", "tasks", "steps", "agents")
            strategy_tables = tuple(row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name GLOB 'a_tensor_*' OR name GLOB 'a_strategy_*' OR name GLOB 'a_trader_*') ORDER BY name"))
            # Only desk-owned SQL data, never environment/provider secrets.
            def encoded_row(row):
                return {key: {"encoding": "base64", "data": base64.b64encode(bytes(value)).decode("ascii"), "bytes": len(bytes(value))}
                        if isinstance(value, (bytes, bytearray, memoryview)) else value for key, value in dict(row).items()}
            return {"desk": "Aster Desk", "format_version": 1, "exported_at": now(), "mode": "paper", "strategy_count": len(installed_strategies(con=con)), "reasoning": reasoning,
                    "binary_encoding": {"scope": "SQLite BLOB columns retain exact bytes in base64 envelopes", "envelope": {"encoding": "base64", "data": "ASCII base64 of original bytes", "bytes": "Original byte count"}},
                    "tables": {t: [encoded_row(r) for r in con.execute('SELECT * FROM "' + t.replace('"', '""') + '"')] for t in tables + strategy_tables}}
