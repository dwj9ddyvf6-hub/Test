#!/usr/bin/env python3
"""Small, private, durable HTTP job service for research calculations only."""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager

from engine_adapters import run_job


BUILD_ID = os.environ.get("SHIPYARD_BUILD_ID", "educational-component-unpinned")
ADAPTER_CONTRACT = "SHIPYARD_PYTHON_ADAPTER_V2"
DB_PATH = Path(os.environ.get("SHIPYARD_DB", "./data/jobs.sqlite3"))
TOKEN = os.environ.get("SHIPYARD_SERVICE_TOKEN", "")
MAX_BODY = 4 * 1024 * 1024
MAX_RESULT_BYTES = 512 * 1024
MAX_QUEUE = 64
MAX_RETAINED_RECEIPTS = 256
RECEIPT_TTL_SECONDS = 30 * 24 * 60 * 60
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def reject_constant(value: str):
    raise ValueError("non-finite JSON number")


def pairs_no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


@contextmanager
def connect_db(path: Path = DB_PATH):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


class JobStore:
    def __init__(self, path: Path):
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
        self.path = path
        with connect_db(path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                request_hash TEXT NOT NULL,
                engine TEXT NOT NULL,
                build_id TEXT,
                symbol TEXT,
                request_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('queued','running','complete','failed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                error_code TEXT
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS jobs_status_created ON jobs(status, created_at)")
            conn.execute("BEGIN IMMEDIATE")
            # Migrate receipts without inventing provenance for historical jobs.
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
            if "build_id" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN build_id TEXT")
                for row in conn.execute("SELECT id,result_json FROM jobs WHERE result_json IS NOT NULL").fetchall():
                    try:
                        historical_build = json.loads(row["result_json"]).get("build_id")
                    except (ValueError, TypeError, AttributeError):
                        continue
                    if isinstance(historical_build, str) and historical_build:
                        conn.execute("UPDATE jobs SET build_id=? WHERE id=?", (historical_build, row["id"]))
            if "symbol" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN symbol TEXT")
                for row in conn.execute("SELECT id,request_json FROM jobs").fetchall():
                    try:
                        symbol = json.loads(row["request_json"]).get("payload", {}).get("symbol")
                    except (ValueError, TypeError, AttributeError):
                        continue
                    if isinstance(symbol, str) and symbol in ("SPY", "QQQ"):
                        conn.execute("UPDATE jobs SET symbol=? WHERE id=?", (symbol, row["id"]))
            # Never replay queued work under a different or unknown source build.
            conn.execute("""UPDATE jobs SET status='failed',request_json='{}',
                         error_code=CASE WHEN build_id IS NULL THEN 'RESEARCH_BUILD_UNKNOWN' ELSE 'RESEARCH_BUILD_CHANGED' END,
                         updated_at=? WHERE status IN ('queued','running') AND (build_id IS NULL OR build_id != ?)""",
                         (now_iso(), BUILD_ID))
            # A crash can occur after the deterministic research calculation but before commit.
            # Re-running an immutable request is safe; its idempotency key remains unchanged.
            conn.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (now_iso(),))
            conn.execute("COMMIT")
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError("research database integrity check failed")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def submit(self, idem: str, engine: str, request: dict) -> tuple[dict, bool]:
        symbol = request.get("payload", {}).get("symbol")
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with connect_db(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM jobs WHERE idempotency_key=?", (idem,)).fetchone()
            if existing:
                if existing["request_hash"] != digest:
                    conn.execute("ROLLBACK")
                    raise Conflict("idempotency key reused with different request")
                conn.execute("COMMIT")
                return self._record(existing), False
            self._prune(conn)
            queued = conn.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]
            if queued >= MAX_QUEUE:
                conn.execute("ROLLBACK")
                raise Busy("research queue is full")
            job_id = uuid.uuid4().hex
            stamp = now_iso()
            conn.execute("""INSERT INTO jobs
                (id,idempotency_key,request_hash,engine,build_id,symbol,request_json,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,'queued',?,?)""",
                (job_id, idem, digest, engine, BUILD_ID, symbol, encoded, stamp, stamp))
            conn.execute("COMMIT")
            return {"id": job_id, "engine": engine, "symbol": symbol, "status": "queued", "created_at": stamp,
                    "updated_at": stamp, "build_id": BUILD_ID, "attempts": 0,
                    "schema": "SHIPYARD_PYTHON_JOB_V1", "adapter_contract": ADAPTER_CONTRACT}, True

    @staticmethod
    def _record(row: sqlite3.Row) -> dict:
        record = {"id": row["id"], "engine": row["engine"], "symbol": row["symbol"], "status": row["status"],
                  "created_at": row["created_at"], "updated_at": row["updated_at"],
                  "attempts": row["attempts"], "build_id": row["build_id"],
                  "schema": "SHIPYARD_PYTHON_JOB_V1", "adapter_contract": ADAPTER_CONTRACT}
        if row["result_json"]:
            record["result"] = json.loads(row["result_json"])
        if row["error_code"]:
            record["error_code"] = row["error_code"]
        return record

    @staticmethod
    def _prune(conn):
        cutoff = datetime.fromtimestamp(time.time() - RECEIPT_TTL_SECONDS, UTC).isoformat()
        conn.execute("DELETE FROM jobs WHERE status IN ('complete','failed') AND updated_at < ?", (cutoff,))
        conn.execute("""DELETE FROM jobs WHERE id IN (
            SELECT id FROM jobs WHERE status IN ('complete','failed')
            ORDER BY updated_at DESC,id DESC LIMIT -1 OFFSET ?)""", (MAX_RETAINED_RECEIPTS,))

    def get(self, job_id: str) -> dict | None:
        with connect_db(self.path) as conn:
            self._prune(conn)
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return self._record(row) if row else None

    def counts(self) -> dict[str, int]:
        with connect_db(self.path) as conn:
            self._prune(conn)
            rows = conn.execute("SELECT status,COUNT(*) AS n FROM jobs GROUP BY status").fetchall()
        counts = {row["status"]: row["n"] for row in rows}
        return {key: counts.get(key, 0) for key in ("queued", "running", "complete", "failed")}

    def claim(self) -> dict | None:
        with connect_db(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._prune(conn)
            row = conn.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
            if not row:
                conn.execute("COMMIT")
                return None
            stamp = now_iso()
            conn.execute("UPDATE jobs SET status='running',attempts=attempts+1,updated_at=? WHERE id=? AND status='queued'",
                         (stamp, row["id"]))
            claimed = conn.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
            conn.execute("COMMIT")
        return {"id": claimed["id"], "engine": claimed["engine"],
                "request": json.loads(claimed["request_json"]), "attempts": claimed["attempts"]}

    def finish(self, job_id: str, result: dict):
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
            result = {"status": "blocked", "blockers": ["RESULT_EXCEEDS_LIMIT"], "signals": [], "intents": [],
                      "job_id": job_id, "build_id": result.get("build_id"), "completed_at": result.get("completed_at")}
            encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        with connect_db(self.path) as conn:
            conn.execute("UPDATE jobs SET status='complete',request_json='{}',result_json=?,error_code=NULL,updated_at=? WHERE id=?",
                         (encoded, now_iso(), job_id))
            self._prune(conn)

    def fail(self, job_id: str, code: str):
        with connect_db(self.path) as conn:
            conn.execute("UPDATE jobs SET status='failed',request_json='{}',error_code=?,updated_at=? WHERE id=?",
                         (code[:80], now_iso(), job_id))
            self._prune(conn)


class Conflict(Exception):
    pass


class Busy(Exception):
    pass


def worker_loop(store: JobStore, stop: threading.Event):
    while not stop.is_set():
        try:
            job = store.claim()
        except sqlite3.Error:
            # A temporary lock/storage fault must not silently kill the worker.
            stop.wait(1)
            continue
        if job is None:
            stop.wait(0.5)
            continue
        failed = False
        try:
            request = job["request"]
            result = run_job(job["engine"], request.get("payload"))
            result["job_id"] = job["id"]
            result["completed_at"] = now_iso()
            result["build_id"] = BUILD_ID
            json.dumps(result, allow_nan=False)
        except Exception:
            # Error details stay out of the API and logs; inputs may include market data.
            failed = True
        # Retain this immutable calculation while retrying persistence. Do not
        # strand a running row or recompute a clock-sensitive job after a DB lock.
        while not stop.is_set():
            try:
                if failed:
                    store.fail(job["id"], "RESEARCH_CALCULATION_FAILED")
                else:
                    store.finish(job["id"], result)
                break
            except sqlite3.Error:
                stop.wait(1)
            except Exception:
                failed = True
                stop.wait(1)


class Handler(BaseHTTPRequestHandler):
    server_version = "ShipyardResearch/1"
    sys_version = ""

    def log_message(self, fmt, *args):
        # Do not log request bodies, auth headers, or query strings.
        print(f"{now_iso()} {self.command} {self.path.split('?')[0]} {args[1] if len(args)>1 else ''}", flush=True)

    def _send(self, status: int, value: dict):
        data = json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        scheme, _, candidate = header.partition(" ")
        return scheme.lower() == "bearer" and bool(candidate) and secrets.compare_digest(candidate, TOKEN)

    def do_GET(self):
        if self.path == "/healthz":
            if hasattr(self.server, "worker") and not self.server.worker.is_alive():
                self._send(503, {"status": "unavailable", "error": "worker_unavailable"})
                return
            self._send(200, {"status": "ok", "build_id": BUILD_ID})
            return
        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return
        if self.path == "/v1/status":
            if hasattr(self.server, "worker") and not self.server.worker.is_alive():
                self._send(503, {"status": "unavailable", "error": "worker_unavailable"})
                return
            self._send(200, {"schema": "SHIPYARD_PYTHON_SERVICE_STATUS_V1", "status": "ok",
                             "build_id": BUILD_ID, "adapter_contract": ADAPTER_CONTRACT,
                             "queue": self.server.store.counts(),
                             "engines": {"saty": "0.3.0", "rre": "0.2.0"}})
            return
        prefix = "/v1/jobs/"
        if not self.path.startswith(prefix):
            self._send(404, {"error": "not_found"})
            return
        job_id = self.path[len(prefix):]
        if not re.fullmatch(r"[a-f0-9]{32}", job_id):
            self._send(400, {"error": "invalid_job_id"})
            return
        record = self.server.store.get(job_id)
        if not record:
            self._send(404, {"error": "not_found"})
            return
        self._send(200, record)

    def do_POST(self):
        if self.path != "/v1/jobs":
            self._send(404, {"error": "not_found"})
            return
        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return
        if self.headers.get("Transfer-Encoding"):
            self._send(411, {"error": "content_length_required"})
            return
        raw_length = self.headers.get("Content-Length", "")
        length = int(raw_length) if re.fullmatch(r"[0-9]{1,8}", raw_length) else -1
        if length < 1 or length > MAX_BODY:
            self._send(413 if length > MAX_BODY else 411, {"error": "invalid_content_length"})
            return
        if self.headers.get_content_type() != "application/json":
            self._send(415, {"error": "application_json_required"})
            return
        idem = self.headers.get("Idempotency-Key", "")
        if not IDEMPOTENCY_RE.fullmatch(idem):
            self._send(400, {"error": "valid_idempotency_key_required"})
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("short body")
            request = json.loads(raw, object_pairs_hook=pairs_no_duplicates, parse_constant=reject_constant)
            if not isinstance(request, dict) or set(request) != {"engine", "payload"}:
                raise ValueError("request requires engine and payload")
            engine = request["engine"]
            if engine not in ("saty", "rre") or not isinstance(request["payload"], dict):
                raise ValueError("invalid engine request")
            if "symbol" in request["payload"] and request["payload"]["symbol"] not in ("SPY", "QQQ"):
                raise ValueError("invalid symbol")
            # JSON exponent overflow (1e309) is not parse_constant; reject it too.
            json.dumps(request, allow_nan=False)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
            self._send(400, {"error": "invalid_json_or_schema"})
            return
        try:
            record, created = self.server.store.submit(idem, engine, request)
        except Conflict:
            self._send(409, {"error": "idempotency_conflict"})
            return
        except Busy:
            self._send(503, {"error": "queue_full"})
            return
        self._send(202 if created else 200, record)


class BoundedHTTPServer(HTTPServer):
    request_queue_size = 16

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(20)
        return request, address


def main():
    if len(TOKEN) < 40:
        raise SystemExit("SHIPYARD_SERVICE_TOKEN must contain at least 40 characters")
    store = JobStore(DB_PATH)
    stop = threading.Event()
    worker = threading.Thread(target=worker_loop, args=(store, stop), name="research-worker", daemon=True)
    worker.start()
    server = BoundedHTTPServer(("127.0.0.1", int(os.environ.get("SHIPYARD_PORT", "8765"))), Handler)
    server.store = store
    server.worker = worker
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        stop.set()
        worker.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    main()
