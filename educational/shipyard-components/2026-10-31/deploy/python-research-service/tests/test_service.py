import json
import os
from pathlib import Path
import tempfile
import sqlite3
from contextlib import contextmanager
from unittest.mock import patch
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

os.environ.setdefault("SHIPYARD_SERVICE_TOKEN", "test-token-" + "x" * 48)

from service import Handler, HTTPServer, JobStore, worker_loop, Conflict
import service
from engine_adapters import run_job, _coverage


@contextmanager
def closed_sqlite_connection(path):
    connection = sqlite3.connect(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "private" / "jobs.sqlite3"
        self.store = JobStore(self.db)
        self.stop = threading.Event()
        self.worker = threading.Thread(target=worker_loop, args=(self.store, self.stop), daemon=True)
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.server.store = self.store
        self.http = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.http.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.stop.set()
        self.server.shutdown()
        self.server.server_close()
        self.http.join(timeout=2)
        self.worker.join(timeout=2)
        self.tmp.cleanup()

    def request(self, path, *, token=None, body=None, idem=None):
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idem is not None:
            headers["Idempotency-Key"] = idem
        data = json.dumps(body).encode() if body is not None else None
        req = Request(self.base + path, data=data, headers=headers, method="POST" if data else "GET")
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_health_is_minimal_and_auth_rejects_missing_token(self):
        status, health = self.request("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        status, _ = self.request("/v1/jobs/nope")
        self.assertEqual(status, 401)
        status, _ = self.request("/v1/status")
        self.assertEqual(status, 401)
        status, info = self.request("/v1/status", token=os.environ["SHIPYARD_SERVICE_TOKEN"])
        self.assertEqual(status, 200)
        self.assertEqual(info["schema"], "SHIPYARD_PYTHON_SERVICE_STATUS_V1")
        self.assertEqual(info["adapter_contract"], "SHIPYARD_PYTHON_ADAPTER_V2")
        self.assertEqual(info["engines"], {"saty": "0.3.0", "rre": "0.2.0"})

    def test_idempotent_submission_and_durable_blocked_result(self):
        body = {"engine": "saty", "payload": {}}
        first_status, first = self.request("/v1/jobs", token=os.environ["SHIPYARD_SERVICE_TOKEN"],
                                            body=body, idem="saty-run-0001")
        second_status, second = self.request("/v1/jobs", token=os.environ["SHIPYARD_SERVICE_TOKEN"],
                                              body=body, idem="saty-run-0001")
        self.assertEqual(first_status, 202)
        self.assertEqual(second_status, 200)
        self.assertEqual(first["id"], second["id"])
        deadline = time.time() + 3
        record = None
        while time.time() < deadline:
            record = self.store.get(first["id"])
            if record and record["status"] == "complete":
                break
            time.sleep(.02)
        self.assertEqual(record["status"], "complete")
        self.assertEqual(record["result"]["status"], "blocked")

    def test_conflicting_idempotency_key_is_rejected(self):
        self.store.submit("same-key-0001", "saty", {"engine": "saty", "payload": {}})
        with self.assertRaises(Conflict):
            self.store.submit("same-key-0001", "rre", {"engine": "rre", "payload": {}})

    def test_running_job_is_requeued_after_restart(self):
        # The normal test worker must not race this direct claim/restart path.
        self.stop.set()
        self.worker.join(timeout=2)
        record, _ = self.store.submit("restart-key-0001", "saty", {"engine": "saty", "payload": {}})
        claimed = self.store.claim()
        self.assertEqual(claimed["id"], record["id"])
        recovered = JobStore(self.db).get(record["id"])
        self.assertEqual(recovered["status"], "queued")

    def test_missing_market_and_event_inputs_block_without_synthetic_fallback(self):
        result = run_job("rre", {})
        self.assertEqual(result["status"], "blocked")
        self.assertIn("DATA_COVERAGE_NOT_COMPLETE", result["blockers"])
        self.assertIn("EVENT_COVERAGE_UNKNOWN_OR_INCOMPLETE", result["blockers"])
        self.assertEqual(result["intents"], [])

    def test_partial_event_scope_is_returned_as_a_blocker(self):
        now = datetime.now(timezone.utc).isoformat()
        result = run_job("rre", {
            "source": {"provider": "alpaca", "feed": "iex", "adjustment": "raw", "venue": "IEX"},
            "coverage": {"status": "complete", "captured_at": now, "provider_received_at": now},
            "calendar": {"version": "official-test-calendar", "provider": "alpaca", "retrieved_at": now},
            "event_coverage": {"source": "scoped test calendar", "version": "v1", "captured_at": now,
                               "covered_from": now, "covered_until": now, "status": "partial",
                               "scope_complete": False, "exclusions": ["unscheduled news"]},
        })
        self.assertEqual(result["status"], "blocked")
        self.assertIn("EVENT_COVERAGE_UNKNOWN_OR_INCOMPLETE", result["blockers"])
        self.assertEqual(result["event_coverage"]["status"], "partial")
        self.assertEqual(result["event_coverage"]["exclusions"], ["unscheduled news"])
        self.assertEqual(result["intents"], [])

    def test_saty_missing_snapshot_blocks_without_calling_strategy(self):
        result = run_job("saty", {})
        self.assertEqual(result["status"], "blocked")
        self.assertIn("DATA_COVERAGE_NOT_COMPLETE", result["blockers"])
        self.assertEqual(result["signals"], [])

    def test_stale_receipts_are_explicitly_blocked(self):
        stale = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        result = run_job("rre", {
            "source": {"provider": "alpaca", "feed": "iex", "adjustment": "raw", "venue": "US"},
            "coverage": {"status": "complete", "captured_at": stale, "provider_received_at": stale},
            "calendar": {"version": "test", "provider": "test", "retrieved_at": stale},
        })
        self.assertEqual(result["status"], "blocked")
        self.assertIn("STALE_CAPTURE_TIME", result["blockers"])
        self.assertIn("STALE_PROVIDER_RECEIPT_TIME", result["blockers"])


class ProvenanceTests(unittest.TestCase):
    def test_original_build_and_symbol_survive_receipt_read_and_runtime_upgrade(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "db" / "jobs.sqlite3"
            store = JobStore(path)
            record, _ = store.submit("build-key-0001", "saty", {"engine":"saty", "payload":{"symbol":"SPY"}})
            store.claim()
            store.finish(record["id"], {"status":"blocked","blockers":["NO_INPUTS"],"build_id":service.BUILD_ID})
            original = service.BUILD_ID
            with patch.object(service,"BUILD_ID","new-test-build"):
                read = JobStore(path).get(record["id"])
                self.assertEqual(read["build_id"], original)
                self.assertEqual(read["symbol"], "SPY")
                self.assertEqual(read["result"]["build_id"], original)

    def test_pending_job_is_not_replayed_under_different_build(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "db" / "jobs.sqlite3"
            store = JobStore(path)
            record, _ = store.submit("build-key-0002", "rre", {"engine":"rre", "payload":{"symbol":"QQQ"}})
            store.claim()
            with patch.object(service,"BUILD_ID","new-test-build"):
                changed = JobStore(path)
                read = changed.get(record["id"])
                self.assertEqual(read["status"], "failed")
                self.assertEqual(read["error_code"], "RESEARCH_BUILD_CHANGED")
                self.assertIsNone(changed.claim())
                with closed_sqlite_connection(path) as db:
                    self.assertEqual(db.execute("SELECT request_json FROM jobs").fetchone()[0], "{}")

    def test_legacy_migration_recovers_only_recorded_build_and_pending_symbol(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "jobs.sqlite3"
            with closed_sqlite_connection(path) as db:
                db.execute("""CREATE TABLE jobs (id TEXT PRIMARY KEY,idempotency_key TEXT NOT NULL UNIQUE,
                    request_hash TEXT NOT NULL,engine TEXT NOT NULL,request_json TEXT NOT NULL,status TEXT NOT NULL,
                    created_at TEXT NOT NULL,updated_at TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT,error_code TEXT)""")
                stamp=datetime.now(timezone.utc).isoformat()
                for job_id,status,result,request in [
                    ("a"*32,"complete",json.dumps({"build_id":"historical-build"}),"{}"),
                    ("b"*32,"running",None,json.dumps({"engine":"saty","payload":{"symbol":"SPY"}})),
                    ("c"*32,"failed",None,"{}")]:
                    db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (job_id,"legacy-"+job_id,"hash","saty",request,status,stamp,stamp,0,result,None))
            store=JobStore(path)
            self.assertEqual(store.get("a"*32)["build_id"],"historical-build")
            pending=store.get("b"*32)
            self.assertEqual(pending["status"],"failed")
            self.assertEqual(pending["error_code"],"RESEARCH_BUILD_UNKNOWN")
            self.assertEqual(pending["symbol"],"SPY")
            self.assertIsNone(store.get("c"*32)["build_id"])
            self.assertIsNone(store.claim())
            self.assertEqual(JobStore(path).get("a"*32)["build_id"],"historical-build")

    def test_complete_label_cannot_override_explicit_incomplete_event_scope(self):
        now=datetime.now(timezone.utc).isoformat()
        _, blockers=_coverage({"source":{"provider":"alpaca","feed":"iex","adjustment":"raw","venue":"IEX"},
            "coverage":{"status":"complete","captured_at":now,"provider_received_at":now},
            "calendar":{"version":"test","provider":"test","retrieved_at":now},
            "event_coverage":{"status":"complete","scope_complete":False,"source":"test","version":"test",
                "captured_at":now,"covered_from":now,"covered_until":now,"events":[]}},require_events=True)
        self.assertIn("EVENT_COVERAGE_UNKNOWN_OR_INCOMPLETE",blockers)

    def test_result_limit_preserves_envelope_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            store=JobStore(Path(folder)/"db"/"jobs.sqlite3")
            record,_=store.submit("large-key-0001","saty",{"engine":"saty","payload":{"symbol":"SPY"}})
            stamp=datetime.now(timezone.utc).isoformat()
            store.finish(record["id"],{"status":"complete","data":"x"*(service.MAX_RESULT_BYTES+1),
                "job_id":record["id"],"build_id":service.BUILD_ID,"completed_at":stamp})
            result=store.get(record["id"])["result"]
            self.assertEqual(result["blockers"],["RESULT_EXCEEDS_LIMIT"])
            self.assertEqual(result["job_id"],record["id"])
            self.assertEqual(result["build_id"],service.BUILD_ID)
            self.assertEqual(result["completed_at"],stamp)

    def test_idle_receipts_expire_without_new_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"db"/"jobs.sqlite3"
            store=JobStore(path)
            record,_=store.submit("expire-key-0001","saty",{"engine":"saty","payload":{}})
            store.finish(record["id"],{"status":"blocked"})
            with closed_sqlite_connection(path) as db:
                db.execute("UPDATE jobs SET updated_at='2000-01-01T00:00:00+00:00'")
            self.assertIsNone(store.get(record["id"]))
            self.assertEqual(store.counts()["complete"],0)

    def test_finished_receipt_cap_is_enforced_without_another_submit(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(service,"MAX_RETAINED_RECEIPTS",2):
            store=JobStore(Path(folder)/"db"/"jobs.sqlite3")
            jobs=[store.submit("cap-key-000"+str(i),"saty",{"engine":"saty","payload":{}})[0] for i in range(4)]
            for record in jobs:store.finish(record["id"],{"status":"blocked"})
            self.assertEqual(store.counts()["complete"],2)

    def test_database_claim_and_finish_faults_retry_without_recalculation(self):
        class Stop:
            done=False
            def is_set(self):return self.done
            def wait(self,seconds):pass
        stop=Stop()
        class FaultStore:
            claims=0
            finishes=0
            def claim(self):
                self.claims+=1
                if self.claims==1:raise sqlite3.OperationalError("test lock")
                return {"id":"a"*32,"engine":"saty","request":{"payload":{}}}
            def finish(self,job_id,result):
                self.finishes+=1
                if self.finishes==1:raise sqlite3.OperationalError("test lock")
                stop.done=True
            def fail(self,*args):raise AssertionError("not a calculation failure")
        store=FaultStore()
        with patch.object(service,"run_job",return_value={"status":"blocked","blockers":[]}) as run:
            worker_loop(store,stop)
            self.assertEqual(run.call_count,1)
        self.assertEqual(store.claims,2)
        self.assertEqual(store.finishes,2)


if __name__ == "__main__":
    unittest.main()
