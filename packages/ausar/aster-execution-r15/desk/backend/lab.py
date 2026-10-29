"""Append-only peer communication, research evidence and operational incidents.

This module never selects securities, originates orders or installs strategies.
Pre-registrations are immutable; results and operator decisions are separate.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from .store import DeskError, identifier, now
from .strategy_contract import installed_strategies


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Message(Strict):
    sender: str = Field(default="operator", min_length=1, max_length=80)
    recipient: str = Field(default="all", min_length=1, max_length=80)
    topic: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=30000)
    source: str = Field(default="operator", max_length=500)
    confidence: Literal["high", "medium", "low", "unassessed"] = "unassessed"


class Cursor(Strict):
    reader: str = Field(min_length=1, max_length=80)
    through_id: int = Field(ge=0)


class Study(Strict):
    title: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1, max_length=10000)
    method: str = Field(min_length=1, max_length=10000)
    dataset: str = Field(min_length=1, max_length=4000)
    primary_metric: str = Field(min_length=1, max_length=2000)
    null_controls: str = Field(min_length=1, max_length=4000)
    acceptance_criteria: str = Field(min_length=1, max_length=4000)
    target_sample: int = Field(ge=1, le=1000000000)
    source_pins: list[str] = Field(default_factory=list, max_length=100)


class StudyUpdate(Strict):
    status: Literal["running", "completed", "rejected", "archived"]
    results: str = Field(default="", max_length=30000)
    sample_count: int = Field(default=0, ge=0, le=1000000000)
    limitations: str = Field(default="", max_length=10000)


class Artifact(Strict):
    study_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=200000)
    source: str = Field(default="operator", max_length=1000)
    source_pin: str = Field(default="", max_length=1000)


class Incident(Strict):
    title: str = Field(min_length=1, max_length=200)
    severity: Literal["info", "warning", "critical"] = "warning"
    evidence: str = Field(min_length=1, max_length=30000)
    book_id: str | None = None


class Proposal(Strict):
    title: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=10000)
    evidence: str = Field(min_length=1, max_length=30000)
    study_id: str | None = None
    book_id: str | None = None
    policy_patch: dict = Field(default_factory=dict)
    rollback_drawdown_pct: float | None = Field(default=None, gt=0, le=100)


class Decision(Strict):
    decision: Literal["approved", "rejected", "accepted", "rollback"]
    reason: str = Field(min_length=1, max_length=10000)


class Lab:
    def __init__(self, store):
        self.store = store
        self.trading = None
        self.research = None
        with store.connect() as con:
            con.executescript("""
              CREATE TABLE IF NOT EXISTS lab_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,sender TEXT NOT NULL,recipient TEXT NOT NULL,topic TEXT NOT NULL,body TEXT NOT NULL,source TEXT NOT NULL,confidence TEXT NOT NULL,created_at TEXT NOT NULL,dedupe_key TEXT UNIQUE);
              CREATE TABLE IF NOT EXISTS lab_cursors(reader TEXT PRIMARY KEY,through_id INTEGER NOT NULL,updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS lab_alerts(id TEXT PRIMARY KEY,dedupe_key TEXT UNIQUE NOT NULL,severity TEXT NOT NULL,message TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,acknowledged_at TEXT,resolved_at TEXT);
              CREATE TABLE IF NOT EXISTS lab_studies(id TEXT PRIMARY KEY,registration TEXT NOT NULL,registration_hash TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS lab_study_results(id TEXT PRIMARY KEY,study_id TEXT NOT NULL REFERENCES lab_studies(id),status TEXT NOT NULL,results TEXT NOT NULL,sample_count INTEGER NOT NULL,limitations TEXT NOT NULL,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS lab_artifacts(id TEXT PRIMARY KEY,study_id TEXT REFERENCES lab_studies(id),name TEXT NOT NULL,content TEXT NOT NULL,sha256 TEXT NOT NULL,source TEXT NOT NULL,source_pin TEXT NOT NULL,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS lab_incidents(id TEXT PRIMARY KEY,title TEXT NOT NULL,severity TEXT NOT NULL,evidence TEXT NOT NULL,book_id TEXT,status TEXT NOT NULL,created_at TEXT NOT NULL,resolved_at TEXT);
              CREATE TABLE IF NOT EXISTS lab_proposals(id TEXT PRIMARY KEY,proposal TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,before_policy TEXT,applied_policy_hash TEXT);
              CREATE TABLE IF NOT EXISTS lab_decisions(id TEXT PRIMARY KEY,proposal_id TEXT NOT NULL REFERENCES lab_proposals(id),decision TEXT NOT NULL,reason TEXT NOT NULL,actor TEXT NOT NULL,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS lab_state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS lab_message_created ON lab_messages(created_at);
            """)
            columns = {r[1] for r in con.execute("PRAGMA table_info(lab_proposals)")}
            for column in ("rollback_actor", "rollback_reason", "stage_token"):
                if column not in columns:
                    con.execute("ALTER TABLE lab_proposals ADD COLUMN " + column + " TEXT")
            if "stage_until" not in columns:
                con.execute("ALTER TABLE lab_proposals ADD COLUMN stage_until REAL NOT NULL DEFAULT 0")

    def bind(self, trading, research=None):
        self.trading = trading
        self.research = research

    @staticmethod
    def _json(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    @staticmethod
    def _hash(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _message(self, con, payload, dedupe_key=None):
        if dedupe_key:
            found = con.execute("SELECT * FROM lab_messages WHERE dedupe_key=?", (dedupe_key,)).fetchone()
            if found:
                return dict(found)
        ts = now()
        rid = con.execute("INSERT INTO lab_messages(sender,recipient,topic,body,source,confidence,created_at,dedupe_key) VALUES(?,?,?,?,?,?,?,?)", (payload["sender"], payload["recipient"], payload["topic"], payload["body"], payload.get("source", "local desk"), payload.get("confidence", "unassessed"), ts, dedupe_key)).lastrowid
        self.store.event(con, "peer_message", payload["sender"], payload["topic"], {"message_id": rid, "recipient": payload["recipient"]})
        return dict(con.execute("SELECT * FROM lab_messages WHERE id=?", (rid,)).fetchone())

    def message(self, payload):
        with self.store.transaction() as con:
            return self._message(con, payload)

    def cursor(self, reader, through_id):
        with self.store.transaction() as con:
            maximum = con.execute("SELECT COALESCE(MAX(id),0) FROM lab_messages").fetchone()[0]
            if through_id > maximum:
                raise DeskError("Reader cursor cannot skip messages that do not exist", 422)
            old = con.execute("SELECT through_id FROM lab_cursors WHERE reader=?", (reader,)).fetchone()
            if old and through_id < old[0]:
                raise DeskError("Reader cursor cannot move backwards", 409)
            con.execute("INSERT INTO lab_cursors VALUES(?,?,?) ON CONFLICT(reader) DO UPDATE SET through_id=excluded.through_id,updated_at=excluded.updated_at", (reader, through_id, now()))
            return dict(con.execute("SELECT * FROM lab_cursors WHERE reader=?", (reader,)).fetchone())

    def alert(self, key, severity, message, payload=None):
        if severity not in {"info", "warning", "critical"}:
            raise DeskError("Invalid alert severity", 422)
        data = self._json(payload or {})
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM lab_alerts WHERE dedupe_key=?", (key,)).fetchone()
            if row and row["message"] == message and row["payload"] == data and row["severity"] == severity and row["status"] != "resolved":
                return dict(row)
            ts = now()
            if row:
                levels = {"info": 0, "warning": 1, "critical": 2}
                reopened = row["status"] == "resolved" or levels[severity] > levels[row["severity"]]
                con.execute("UPDATE lab_alerts SET severity=?,message=?,payload=?,status=?,acknowledged_at=?,updated_at=?,resolved_at=NULL WHERE id=?", (severity, message, data, "open" if reopened else row["status"], None if reopened else row["acknowledged_at"], ts, row["id"]))
                rid = row["id"]
            else:
                rid = identifier()
                con.execute("INSERT INTO lab_alerts VALUES(?,?,?,?,?,'open',?,?,NULL,NULL)", (rid, key, severity, message, data, ts, ts))
            self.store.event(con, "operational_alert", "risk_officer", message, {"alert_id": rid, "key": key, "severity": severity, **(payload or {})})
            return dict(con.execute("SELECT * FROM lab_alerts WHERE id=?", (rid,)).fetchone())

    def resolve_key(self, key):
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM lab_alerts WHERE dedupe_key=? AND status!='resolved'", (key,)).fetchone()
            if row:
                con.execute("UPDATE lab_alerts SET status='resolved',resolved_at=?,updated_at=? WHERE id=?", (now(), now(), row["id"]))
                self.store.event(con, "alert_resolved", "coordinator", "Operational condition recovered", {"alert_id": row["id"], "key": key})

    def update_alert(self, rid, action):
        with self.store.transaction() as con:
            if not con.execute("SELECT 1 FROM lab_alerts WHERE id=?", (rid,)).fetchone():
                raise DeskError("Alert not found", 404)
            if action == "ack":
                con.execute("UPDATE lab_alerts SET status=CASE WHEN status='resolved' THEN status ELSE 'acknowledged' END,acknowledged_at=?,updated_at=? WHERE id=?", (now(), now(), rid))
            else:
                con.execute("UPDATE lab_alerts SET status='resolved',resolved_at=?,updated_at=? WHERE id=?", (now(), now(), rid))
            self.store.event(con, "alert_" + action, "operator", "Operator updated alert", {"alert_id": rid})
            return dict(con.execute("SELECT * FROM lab_alerts WHERE id=?", (rid,)).fetchone())

    def register(self, payload):
        encoded = self._json(payload)
        rid, ts = identifier(), now()
        with self.store.transaction() as con:
            con.execute("INSERT INTO lab_studies VALUES(?,?,?,'registered',?,?)", (rid, encoded, self._hash(encoded), ts, ts))
            self.store.event(con, "research_registered", "operator", payload["title"], {"study_id": rid, "registration_hash": self._hash(encoded)})
        return self.study(rid)

    def study(self, rid):
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM lab_studies WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Study not found", 404)
            result = dict(row)
            result["registration"] = json.loads(result["registration"])
            result["results"] = [dict(r) for r in con.execute("SELECT * FROM lab_study_results WHERE study_id=? ORDER BY created_at", (rid,))]
            return result

    def study_update(self, rid, payload):
        transitions = {"registered": {"running", "rejected", "archived"}, "running": {"completed", "rejected", "archived"}, "completed": {"archived"}, "rejected": {"archived"}, "archived": set()}
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM lab_studies WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Study not found", 404)
            status = payload["status"]
            if status not in transitions[row["status"]]:
                raise DeskError("Study transition is not allowed; registration and prior results are immutable")
            if status in {"completed", "rejected"} and not payload.get("results", "").strip():
                raise DeskError("A completed or rejected study requires recorded results", 422)
            con.execute("INSERT INTO lab_study_results VALUES(?,?,?,?,?,?,?)", (identifier(), rid, status, payload.get("results", ""), payload.get("sample_count", 0), payload.get("limitations", ""), now()))
            con.execute("UPDATE lab_studies SET status=?,updated_at=? WHERE id=?", (status, now(), rid))
            self.store.event(con, "research_stage", "operator", "Research stage: " + status, {"study_id": rid, "status": status})
        return self.study(rid)

    def artifact(self, payload):
        rid, ts = identifier(), now()
        with self.store.transaction() as con:
            if payload.get("study_id") and not con.execute("SELECT 1 FROM lab_studies WHERE id=?", (payload["study_id"],)).fetchone():
                raise DeskError("Study not found", 404)
            sha = self._hash(payload["content"])
            con.execute("INSERT INTO lab_artifacts VALUES(?,?,?,?,?,?,?,?)", (rid, payload.get("study_id"), payload["name"], payload["content"], sha, payload.get("source", "operator"), payload.get("source_pin", ""), ts))
            self.store.event(con, "research_artifact", "archivist", payload["name"], {"artifact_id": rid, "sha256": sha, "study_id": payload.get("study_id")})
        return {"id": rid, "sha256": sha, **payload, "created_at": ts}

    def incident(self, payload):
        rid, ts = identifier(), now()
        with self.store.transaction() as con:
            con.execute("INSERT INTO lab_incidents VALUES(?,?,?,?,?,'open',?,NULL)", (rid, payload["title"], payload["severity"], payload["evidence"], payload.get("book_id"), ts))
            self.store.event(con, "incident_recorded", "operator", payload["title"], {"incident_id": rid, "book_id": payload.get("book_id")})
        return {"id": rid, **payload, "status": "open", "created_at": ts}

    def proposal(self, payload):
        # Strategy activation is not a possible proposal operation.
        allowed = {"gross_exposure_cap", "symbol_exposure_cap", "drawdown_alert_percent", "drawdown_brake_percent", "slippage_bps", "fees_per_order", "max_fill_quantity"}
        if set(payload.get("policy_patch", {})) - allowed:
            raise DeskError("Proposals may change documented operational risk/execution parameters only", 422)
        if payload.get("policy_patch") and not payload.get("book_id"):
            raise DeskError("A policy proposal requires a book identity", 422)
        if payload.get("rollback_drawdown_pct") and not payload.get("policy_patch"):
            raise DeskError("Rollback guard requires an explicit policy proposal", 422)
        rid, ts = identifier(), now()
        with self.store.transaction() as con:
            if payload.get("study_id") and not con.execute("SELECT 1 FROM lab_studies WHERE id=?", (payload["study_id"],)).fetchone():
                raise DeskError("Study not found", 404)
            con.execute("INSERT INTO lab_proposals(id,proposal,status,created_at,updated_at,before_policy,applied_policy_hash) VALUES(?,?, 'pending',?,?,NULL,NULL)", (rid, self._json(payload), ts, ts))
            self.store.event(con, "proposal_recorded", "operator", payload["title"], {"proposal_id": rid})
        return {"id": rid, "proposal": payload, "status": "pending", "created_at": ts}

    def decision(self, rid, decision, reason):
        if decision == "rollback":
            return self.rollback(rid, reason, actor="operator")
        with self.store.transaction() as con:
            row = con.execute("SELECT * FROM lab_proposals WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Proposal not found", 404)
            transitions = {"pending": {"approved", "rejected"}, "approved": {"accepted"}, "observing": {"accepted"}}
            if decision not in transitions.get(row["status"], set()):
                raise DeskError("Proposal decision does not match its current stage")
            con.execute("INSERT INTO lab_decisions VALUES(?,?,?,?,?,?)", (identifier(), rid, decision, reason, "operator", now()))
            # Approval is a concrete signed decision; application is a separate explicit action.
            con.execute("UPDATE lab_proposals SET status=?,updated_at=? WHERE id=?", (decision, now(), rid))
            self.store.event(con, "proposal_decision", "operator", reason, {"proposal_id": rid, "decision": decision})
        return self.proposal_get(rid)

    def apply(self, rid):
        if not self.trading:
            raise DeskError("Trading engine is unavailable", 503)
        proposal = self.proposal_get(rid)
        if proposal["status"] == "observing":
            return proposal
        if proposal["status"] != "approved":
            raise DeskError("Only an operator-approved proposal can be applied")
        payload = proposal["proposal"]
        if not payload.get("policy_patch"):
            raise DeskError("This is a research proposal; it has no executable policy change", 422)
        book = next((b for b in self.trading.snapshot()["books"] if b["id"] == payload["book_id"]), None)
        if not book:
            raise DeskError("Proposal book not found", 404)
        before = {"policy": book["policy"], "policy_hash": book["policy_hash"], "policy_version": book["policy_version"]}
        token = identifier()
        with self.store.transaction() as con:
            # The durable record precedes the policy change. If the worker dies,
            # the exact versioned policy actor identifies the committed effect.
            changed = con.execute("UPDATE lab_proposals SET status='applying',before_policy=?,stage_until=?,stage_token=?,updated_at=? WHERE id=? AND status='approved'", (self._json(before), time.time() + 120, token, now(), rid)).rowcount
            if not changed:
                raise DeskError("Proposal has already changed stage")
        try:
            self.trading.set_book(payload["book_id"], {"policy": payload["policy_patch"]}, expected_hash=before["policy_hash"], actor="proposal:" + rid + ":" + token, transaction_guard=self._policy_guard(rid, "applying", token))
        except Exception:
            self._settle_apply(rid, payload["book_id"], token, retry_if_absent=True)
            raise
        self._settle_apply(rid, payload["book_id"], token)
        return self.proposal_get(rid)

    def _settle_apply(self, rid, book_id, token, retry_if_absent=False):
        """Bind observation to this exact committed write, never its later read view."""
        with self.store.transaction() as con:
            history = con.execute("SELECT hash FROM p_policy_history WHERE book_id=? AND actor=? ORDER BY version DESC LIMIT 1", (book_id, self._policy_actor("proposal:", rid, token))).fetchone()
            if not history and not retry_if_absent:
                raise DeskError("Proposal policy commit could not be verified; recovery will inspect the durable history", 503)
            changed = con.execute("UPDATE lab_proposals SET status=?,applied_policy_hash=?,stage_until=0,updated_at=? WHERE id=? AND status='applying' AND stage_token=?", ("observing" if history else "approved", history[0] if history else None, now(), rid, token)).rowcount
            if changed and history:
                self.store.event(con, "proposal_applied", "operator", "Approved operational policy entered observation", {"proposal_id": rid, "book_id": book_id, "policy_hash": history[0]})

    @staticmethod
    def _policy_actor(prefix, rid, token):
        return prefix + rid + (":" + token if token else "")

    @staticmethod
    def _policy_guard(rid, status, token):
        def guard(con):
            row = con.execute("SELECT status,stage_token FROM lab_proposals WHERE id=?", (rid,)).fetchone()
            if not row or row["status"] != status or row["stage_token"] != token:
                raise DeskError("Policy proposal authority changed; stale work cannot change policy")
        return guard

    def rollback(self, rid, reason, actor="operator"):
        if not self.trading:
            raise DeskError("Trading engine is unavailable", 503)
        proposal = self.proposal_get(rid)
        if proposal["status"] == "rolled_back":
            return proposal
        if proposal["status"] == "rolling_back":
            return self._resume_rollback(proposal)
        if proposal["status"] not in {"approved", "observing"}:
            raise DeskError("Proposal is not awaiting decision or observation")
        payload = proposal["proposal"]
        if proposal["status"] == "observing":
            with self.store.transaction() as con:
                changed = con.execute("UPDATE lab_proposals SET status='rolling_back',rollback_actor=?,rollback_reason=?,stage_token=?,updated_at=? WHERE id=? AND status='observing'", (actor, reason, identifier(), now(), rid)).rowcount
                if not changed:
                    raise DeskError("Proposal has already changed stage")
            return self._resume_rollback(self.proposal_get(rid))
        return self._finish_rollback(proposal, reason, actor)

    def _finish_rollback(self, proposal, reason, actor):
        rid, payload = proposal["id"], proposal["proposal"]
        with self.store.transaction() as con:
            changed = con.execute("UPDATE lab_proposals SET status='rolled_back',updated_at=? WHERE id=? AND status=? AND stage_token IS ?", (now(), rid, proposal["status"], proposal["stage_token"])).rowcount
            if not changed:
                current = con.execute("SELECT status FROM lab_proposals WHERE id=?", (rid,)).fetchone()
                if current and current[0] == "rolled_back":
                    return self.proposal_get(rid)
                raise DeskError("Proposal changed stage before rollback completion")
            con.execute("INSERT INTO lab_decisions VALUES(?,?,?,?,?,?)", (identifier(), rid, "rollback", reason, actor, now()))
            self.store.event(con, "proposal_rolled_back", actor, reason, {"proposal_id": rid, "book_id": payload.get("book_id")})
        return self.proposal_get(rid)

    def _resume_rollback(self, proposal):
        rid, payload = proposal["id"], proposal["proposal"]
        policy_actor = self._policy_actor("proposal_rollback:", rid, proposal["stage_token"])
        with self.store.connect() as con:
            restored = con.execute("SELECT 1 FROM p_policy_history WHERE book_id=? AND actor=?", (payload["book_id"], policy_actor)).fetchone()
        if not restored:
            patch = {key: proposal["before_policy"]["policy"][key] for key in payload["policy_patch"]}
            try:
                self.trading.set_book(payload["book_id"], {"policy": patch}, expected_hash=proposal["applied_policy_hash"], actor=policy_actor, transaction_guard=self._policy_guard(rid, "rolling_back", proposal["stage_token"]))
            except DeskError:
                with self.store.transaction() as con:
                    restored = con.execute("SELECT 1 FROM p_policy_history WHERE book_id=? AND actor=?", (payload["book_id"], policy_actor)).fetchone()
                    if not restored:
                        con.execute("UPDATE lab_proposals SET status='observing',updated_at=? WHERE id=? AND status='rolling_back' AND stage_token=?", (now(), rid, proposal["stage_token"]))
                if not restored:
                    raise
        # The exact committed actor proves restoration even if a later operator
        # update exists. Never replay restoration over that newer policy.
        return self._finish_rollback(proposal, proposal["rollback_reason"], proposal["rollback_actor"])

    def _observe_proposals(self, books):
        with self.store.connect() as con:
            rows = [dict(r) for r in con.execute("SELECT * FROM lab_proposals WHERE status IN ('applying','observing','rolling_back')")]
        for row in rows:
            payload = json.loads(row["proposal"])
            bid = payload.get("book_id")
            if row["status"] == "rolling_back":
                try:
                    self._resume_rollback(self.proposal_get(row["id"]))
                except DeskError:
                    self.alert("proposal-conflict:" + row["id"], "warning", "Interrupted policy rollback requires operator review; a newer policy was preserved", {"proposal_id": row["id"], "book_id": bid})
                continue
            if row["status"] == "applying":
                with self.store.transaction() as con:
                    history = con.execute("SELECT hash FROM p_policy_history WHERE book_id=? AND actor=? ORDER BY version DESC LIMIT 1", (bid, self._policy_actor("proposal:", row["id"], row["stage_token"]))).fetchone()
                    if not history and row["stage_until"] > time.time():
                        continue
                    con.execute("UPDATE lab_proposals SET status=?,applied_policy_hash=?,updated_at=? WHERE id=? AND status='applying' AND stage_token IS ?", ("observing" if history else "approved", history[0] if history else None, now(), row["id"], row["stage_token"]))
                continue
            guard = payload.get("rollback_drawdown_pct")
            book = next((b for b in books if b["id"] == bid), None)
            if guard is None or not book:
                continue
            account = book.get("account", {})
            if account.get("missing_marks") != 0 or account.get("stale_marks") != 0:
                self.alert("proposal-marks:" + row["id"], "warning", "Policy observation guard awaits complete fresh marks", {"proposal_id": row["id"], "book_id": bid})
                continue
            self.resolve_key("proposal-marks:" + row["id"])
            drawdown = account.get("drawdown_percent")
            if drawdown is None or drawdown < guard:
                continue
            try:
                self.rollback(row["id"], "Operator-approved observation guard reached: drawdown " + str(drawdown) + "%", actor="calibration_guard")
                self.alert("proposal-rollback:" + row["id"], "warning", "Approved operational policy automatically rolled back", {"proposal_id": row["id"], "book_id": bid})
            except DeskError:
                self.alert("proposal-conflict:" + row["id"], "warning", "Policy observation guard requires operator review; a newer policy was preserved", {"proposal_id": row["id"], "book_id": bid})

    def record_agent_review(self, con, task, result):
        """Journal completed coordinator work in the same task transaction."""
        self._message(con, {"sender": "research_coordinator", "recipient": "chief_of_staff", "topic": task["title"], "body": result[:30000], "source": "durable task:" + task["id"], "confidence": "unassessed"}, "task-review:" + task["id"])
        sha = self._hash(result)
        con.execute("INSERT OR IGNORE INTO lab_artifacts VALUES(?,NULL,?,?,?,?,?,?)", ("task-" + task["id"], task["title"], result, sha, "Completed operational/research task", "local-task:" + task["id"], now()))

    def proposal_get(self, rid):
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM lab_proposals WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Proposal not found", 404)
            result = dict(row)
            result["proposal"] = json.loads(result["proposal"])
            result["before_policy"] = json.loads(result["before_policy"]) if result["before_policy"] else None
            result["decisions"] = [dict(r) for r in con.execute("SELECT * FROM lab_decisions WHERE proposal_id=? ORDER BY created_at", (rid,))]
            return result

    def operate(self, trading_snapshot=None, runtime_status=None, clock=None):
        """Factual peer handoffs and tape-linked reviews; no investment judgments."""
        snapshot = trading_snapshot or {}
        books, fills, intents = snapshot.get("books", []), snapshot.get("fills", []), snapshot.get("intents", [])
        ts = now()
        hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        with self.store.transaction() as con:
            registry = installed_strategies(con=con)
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='p_fills'").fetchone():
                cursor = con.execute("SELECT value FROM lab_state WHERE key='fill_review_cursor'").fetchone()
                rows = con.execute("SELECT rowid AS receipt_sequence,* FROM p_fills WHERE rowid>? ORDER BY rowid LIMIT 200", (int(cursor[0]) if cursor else 0,)).fetchall()
                fills = [dict(r) for r in rows]
            for fill in fills:
                key = "fill-review:" + str(fill.get("id", self._hash(self._json(fill))))
                body = self._json({"execution_receipt": fill, "scope": "Execution review only. No strategy or trade recommendation.", "questions": ["Did the submitted instruction match the receipt?", "Was the recorded mark timely?", "Were fees, partials and ownership preserved?"]})
                self._message(con, {"sender": "journal_coach", "recipient": "chief_of_staff", "topic": "Tape-linked execution review", "body": body, "source": "durable paper fill ledger", "confidence": "high"}, key)
                if "receipt_sequence" in fill:
                    con.execute("INSERT OR REPLACE INTO lab_state VALUES('fill_review_cursor',?)", (str(fill["receipt_sequence"]),))
            if books:
                summary = [{"id": book.get("id"), "name": book.get("name"), "broker": book.get("broker"), "account": book.get("account", {}), "halted": book.get("policy", {}).get("halted", False), "policy_version": book.get("policy_version"), "policy_hash": book.get("policy_hash")} for book in books]
                self._message(con, {"sender": "chief_of_staff", "recipient": "all", "topic": "Hourly desk handoff", "body": self._json({"books": summary, "intent_count": len(intents), "strategy_count": len(registry), "installed_strategies": list(registry), "runtime": runtime_status or {}, "recorded_at": ts}), "source": "local desk observations", "confidence": "high"}, "hourly:" + hour)
        for intent in intents:
            status, rid = intent.get("status"), intent.get("id")
            if not rid:
                continue
            key = "intent-state:" + rid
            if status in {"expired", "rejected"}:
                self.alert(key, "warning", "Supplied paper intent did not reach a full fill: " + status, {"intent_id": rid, "book_id": intent.get("book_id"), "filled_quantity": intent.get("filled_quantity"), "requested_quantity": intent.get("quantity"), "reason": intent.get("error")})
            elif status == "blocked" or status == "submitting" and intent.get("error"):
                self.alert(key, "warning" if status == "blocked" else "critical", "Paper intent requires reconciliation or execution-condition recovery", {"intent_id": rid, "book_id": intent.get("book_id"), "status": status, "reason": intent.get("error")})
            elif status in {"filled", "cancelled", "open", "partially_filled"}:
                self.resolve_key(key)
        # Live alert keys are based on factual conditions, not P&L-driven selection.
        for book in books:
            bid = book.get("id", "unknown")
            halted = book.get("halted", (book.get("policy") or {}).get("halted", False))
            if halted:
                self.alert("book-halted:" + bid, "warning", "Paper book is halted: " + book.get("name", bid), {"book_id": bid, "reason": book.get("halt_reason")})
            else:
                self.resolve_key("book-halted:" + bid)
        if self.trading:
            self._observe_proposals(books)
        research = self.research.operate() if self.research else None
        return {"book_count": len(books), "fill_receipts_reviewed": len(fills), "research": research, "strategy_count": len(registry), "completed_at": ts}

    def snapshot(self):
        with self.store.connect() as con:
            con.execute("BEGIN")
            registry = installed_strategies(con=con)
            inbox = [dict(r) for r in con.execute("SELECT * FROM lab_messages ORDER BY id DESC LIMIT 200")]
            alerts = [dict(r) for r in con.execute("SELECT * FROM lab_alerts ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'acknowledged' THEN 1 ELSE 2 END,updated_at DESC LIMIT 200")]
            for row in alerts:
                row["payload"] = json.loads(row["payload"])
            studies = []
            for row in con.execute("SELECT * FROM lab_studies ORDER BY created_at DESC LIMIT 100"):
                item = dict(row)
                item["registration"] = json.loads(item["registration"])
                item["results"] = [dict(r) for r in con.execute("SELECT * FROM lab_study_results WHERE study_id=? ORDER BY created_at", (item["id"],))]
                studies.append(item)
            proposals = []
            for row in con.execute("SELECT * FROM lab_proposals ORDER BY created_at DESC LIMIT 100"):
                item = dict(row)
                item["proposal"] = json.loads(item["proposal"])
                item["before_policy"] = json.loads(item["before_policy"]) if item["before_policy"] else None
                item["decisions"] = [dict(r) for r in con.execute("SELECT * FROM lab_decisions WHERE proposal_id=? ORDER BY created_at", (item["id"],))]
                proposals.append(item)
            return {"inbox": inbox, "inbox_total": con.execute("SELECT COUNT(*) FROM lab_messages").fetchone()[0], "cursors": [dict(r) for r in con.execute("SELECT * FROM lab_cursors")], "alerts": alerts, "studies": studies, "proposals": proposals, "incidents": [dict(r) for r in con.execute("SELECT * FROM lab_incidents ORDER BY created_at DESC LIMIT 100")], "artifacts": [dict(r) for r in con.execute("SELECT id,study_id,name,sha256,source,source_pin,created_at FROM lab_artifacts ORDER BY created_at DESC LIMIT 100")], "agent_authority": {"chief_of_staff": ["factual briefs", "operational task handoffs"], "data_steward": ["collect configured data", "validate timestamps"], "accountant": ["ledger and broker reconciliation"], "risk_manager": ["alerts", "policy inspection"], "execution_clerk": ["execute supplied intents"], "journal_coach": ["tape-linked reviews", "preserve evidence"]}, "strategy_count": len(registry), "installed_strategies": list(registry)}

    def export(self):
        with self.store.connect() as con:
            return {name: [dict(r) for r in con.execute("SELECT * FROM " + name)] for name in ("lab_messages", "lab_cursors", "lab_alerts", "lab_studies", "lab_study_results", "lab_artifacts", "lab_incidents", "lab_proposals", "lab_decisions")}


def lab_router(lab):
    router = APIRouter(prefix="/api/lab")

    @router.get("")
    def snapshot():
        return lab.snapshot()

    @router.post("/inbox")
    def message(body: Message):
        return lab.message(body.model_dump())

    @router.post("/inbox/read")
    def cursor(body: Cursor):
        return lab.cursor(body.reader, body.through_id)

    @router.post("/alerts/{rid}/ack")
    def acknowledge(rid: str):
        return lab.update_alert(rid, "ack")

    @router.post("/alerts/{rid}/resolve")
    def resolve(rid: str):
        return lab.update_alert(rid, "resolve")

    @router.post("/studies")
    def register(body: Study):
        return lab.register(body.model_dump())

    @router.patch("/studies/{rid}")
    def study_update(rid: str, body: StudyUpdate):
        return lab.study_update(rid, body.model_dump())

    @router.post("/artifacts")
    def artifact(body: Artifact):
        return lab.artifact(body.model_dump())

    @router.get("/artifacts/{rid}")
    def read_artifact(rid: str):
        with lab.store.connect() as con:
            row = con.execute("SELECT * FROM lab_artifacts WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Artifact not found", 404)
            return dict(row)

    @router.post("/incidents")
    def incident(body: Incident):
        return lab.incident(body.model_dump())

    @router.post("/incidents/{rid}/resolve")
    def close_incident(rid: str):
        with lab.store.transaction() as con:
            if not con.execute("SELECT 1 FROM lab_incidents WHERE id=?", (rid,)).fetchone():
                raise DeskError("Incident not found", 404)
            con.execute("UPDATE lab_incidents SET status='resolved',resolved_at=? WHERE id=?", (now(), rid))
            lab.store.event(con, "incident_resolved", "operator", "Operator resolved incident", {"incident_id": rid})
            return dict(con.execute("SELECT * FROM lab_incidents WHERE id=?", (rid,)).fetchone())

    @router.post("/proposals")
    def proposal(body: Proposal):
        return lab.proposal(body.model_dump())

    @router.post("/proposals/{rid}/decision")
    def decide(rid: str, body: Decision):
        return lab.decision(rid, body.decision, body.reason)

    @router.post("/proposals/{rid}/apply")
    def apply(rid: str):
        return lab.apply(rid)

    return router
