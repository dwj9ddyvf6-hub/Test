"""Durable read-only research DAGs. No shell, strategy or financial tools."""
import hashlib
import json
import time

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from .store import DeskError, identifier, now, symbol


class ResearchWorkflows:
    TOOLS = ("source_collection", "bar_history", "catalogue_search", "evidence_summary")

    def __init__(self, research):
        self.research, self.store = research, research.store
        with self.store.connect() as con:
            con.executescript("""
              CREATE TABLE IF NOT EXISTS research_workflows(id TEXT PRIMARY KEY,title TEXT NOT NULL,plan TEXT NOT NULL,plan_hash TEXT NOT NULL,enabled INTEGER NOT NULL,interval_seconds INTEGER NOT NULL,next_due REAL NOT NULL,created_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS research_runs(id TEXT PRIMARY KEY,workflow_id TEXT NOT NULL REFERENCES research_workflows(id),status TEXT NOT NULL,created_at TEXT NOT NULL,completed_at TEXT);
              CREATE TABLE IF NOT EXISTS research_nodes(run_id TEXT NOT NULL REFERENCES research_runs(id),node_id TEXT NOT NULL,status TEXT NOT NULL,attempt INTEGER NOT NULL,lease_until REAL NOT NULL,lease_token TEXT,result TEXT,error TEXT,PRIMARY KEY(run_id,node_id));
              CREATE TABLE IF NOT EXISTS research_node_receipts(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,node_id TEXT NOT NULL,attempt INTEGER NOT NULL,status TEXT NOT NULL,content TEXT NOT NULL,sha256 TEXT NOT NULL,created_at TEXT NOT NULL);
            """)

    @staticmethod
    def encode(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def register(self, title, nodes, interval_seconds=3600):
        if not title.strip() or len(title) > 200 or not 1 <= len(nodes) <= 12:
            raise DeskError("Research plans require a title and 1–12 bounded nodes", 422)
        if not 900 <= interval_seconds <= 604800:
            raise DeskError("Research cadence must be between 900 and 604800 seconds", 422)
        seen, validated = set(), []
        for node in nodes:
            nid, tool, params, needs = node["id"], node["tool"], dict(node.get("params", {})), node.get("needs", [])
            if not nid or len(nid) > 80 or nid in seen or any(dep not in seen for dep in needs):
                raise DeskError("Nodes need unique identities and dependencies earlier in the plan", 422)
            if tool not in self.TOOLS:
                raise DeskError("Unregistered research tool; financial and arbitrary execution tools are unavailable", 422)
            if tool == "source_collection":
                if set(params) != {"symbols"} or not isinstance(params["symbols"], list) or not 1 <= len(params["symbols"]) <= 2 or not all(isinstance(s, str) for s in params["symbols"]):
                    raise DeskError("Source collection accepts one or two symbols", 422)
                params["symbols"] = [symbol(s) for s in params["symbols"]]
            elif tool == "bar_history":
                if set(params) - {"symbol", "range", "interval"} or not isinstance(params.get("symbol"), str):
                    raise DeskError("Bar history requires symbol with optional range/interval", 422)
                params["symbol"] = symbol(params["symbol"])
                from .providers import BAR_INTERVALS, BAR_DAYS
                if not isinstance(params.get("range", "1mo"), str) or not isinstance(params.get("interval", "1d"), str) or params.get("range", "1mo") not in BAR_DAYS or params.get("interval", "1d") not in BAR_INTERVALS:
                    raise DeskError("Unsupported bounded bar range or interval", 422)
            elif tool == "catalogue_search":
                if set(params) != {"query"} or not isinstance(params["query"], str) or not 1 <= len(params["query"]) <= 500:
                    raise DeskError("Catalogue query must contain 1–500 characters", 422)
            elif params:
                raise DeskError("Evidence summary consumes only completed dependency receipts", 422)
            seen.add(nid)
            validated.append({"id": nid, "tool": tool, "params": params, "needs": list(dict.fromkeys(needs))})
        plan, rid = self.encode(validated), identifier()
        digest = hashlib.sha256(plan.encode()).hexdigest()
        with self.store.transaction() as con:
            con.execute("INSERT INTO research_workflows VALUES(?,?,?,?,0,?,?,?)", (rid, title, plan, digest, interval_seconds, 0, now()))
            self.store.event(con, "research_workflow_registered", "operator", title, {"workflow_id": rid, "plan_hash": digest})
        return self.get(rid)

    def get(self, rid):
        with self.store.connect() as con:
            row = con.execute("SELECT * FROM research_workflows WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Research workflow not found", 404)
            return {**dict(row), "plan": json.loads(row["plan"]), "enabled": bool(row["enabled"])}

    def configure(self, rid, enabled):
        self.get(rid)
        with self.store.transaction() as con:
            con.execute("UPDATE research_workflows SET enabled=?,next_due=? WHERE id=?", (int(enabled), time.time(), rid))
            self.store.event(con, "research_workflow_configured", "operator", "Research scheduling changed", {"workflow_id": rid, "enabled": enabled})
        return self.get(rid)

    def _enqueue(self, con, workflow):
        active = con.execute("SELECT id FROM research_runs WHERE workflow_id=? AND status IN ('queued','running')", (workflow["id"],)).fetchone()
        if active:
            return active[0]
        rid = identifier()
        con.execute("INSERT INTO research_runs VALUES(?,?,'queued',?,NULL)", (rid, workflow["id"], now()))
        for node in json.loads(workflow["plan"]):
            con.execute("INSERT INTO research_nodes VALUES(?,?,'queued',0,0,NULL,NULL,NULL)", (rid, node["id"]))
        return rid

    def enqueue(self, rid):
        self.get(rid)
        with self.store.transaction() as con:
            workflow = con.execute("SELECT * FROM research_workflows WHERE id=?", (rid,)).fetchone()
            run_id = self._enqueue(con, workflow)
            status = con.execute("SELECT status FROM research_runs WHERE id=?", (run_id,)).fetchone()[0]
            self.store.event(con, "research_run_requested", "operator", "Read-only research workflow queued", {"workflow_id": rid, "run_id": run_id})
        return {"run_id": run_id, "workflow_id": rid, "status": status}

    def retry(self, rid):
        with self.store.transaction() as con:
            row = con.execute("SELECT status,workflow_id FROM research_runs WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Research run not found", 404)
            if row[0] != "failed":
                raise DeskError("Only failed research runs can be retried")
            if con.execute("SELECT 1 FROM research_runs WHERE workflow_id=? AND id!=? AND status IN ('queued','running')", (row["workflow_id"], rid)).fetchone():
                raise DeskError("Another run of this research workflow is active; finish or cancel it before retrying")
            con.execute("UPDATE research_nodes SET status='queued',lease_until=0,lease_token=NULL,error=NULL WHERE run_id=? AND status IN ('failed','blocked')", (rid,))
            con.execute("UPDATE research_runs SET status='queued',completed_at=NULL WHERE id=?", (rid,))
            self.store.event(con, "research_run_retry", "operator", "Read-only nodes retried; prior receipts retained", {"run_id": rid})
        return {"run_id": rid, "status": "queued"}

    def cancel(self, rid):
        with self.store.transaction() as con:
            row = con.execute("SELECT status FROM research_runs WHERE id=?", (rid,)).fetchone()
            if not row:
                raise DeskError("Research run not found", 404)
            if row[0] not in {"queued", "running", "cancelled"}:
                raise DeskError("Completed or failed research runs retain their status")
            con.execute("UPDATE research_nodes SET status='cancelled',lease_until=0,lease_token=NULL WHERE run_id=? AND status IN ('queued','running')", (rid,))
            con.execute("UPDATE research_runs SET status='cancelled',completed_at=? WHERE id=? AND status!='cancelled'", (now(), rid))
            self.store.event(con, "research_run_cancelled", "operator", "Read-only run cancelled; prior receipts retained", {"run_id": rid})
        return {"run_id": rid, "status": "cancelled"}

    def operate(self):
        """One bounded node per pass; persisted lease fences concurrent workers."""
        epoch, selected = time.time(), None
        with self.store.transaction() as con:
            for workflow in con.execute("SELECT * FROM research_workflows WHERE enabled=1 AND next_due<=? ORDER BY next_due LIMIT 4", (epoch,)).fetchall():
                self._enqueue(con, workflow)
                con.execute("UPDATE research_workflows SET next_due=? WHERE id=?", (epoch + workflow["interval_seconds"], workflow["id"]))
            con.execute("UPDATE research_nodes SET status='queued',lease_token=NULL WHERE status='running' AND lease_until<=?", (epoch,))
            runs = con.execute("SELECT r.*,w.plan,w.plan_hash FROM research_runs r JOIN research_workflows w ON w.id=r.workflow_id WHERE r.status IN ('queued','running') ORDER BY r.created_at LIMIT 100").fetchall()
            for run in runs:
                states = {r["node_id"]: dict(r) for r in con.execute("SELECT * FROM research_nodes WHERE run_id=?", (run["id"],))}
                # Serialize nodes within a run to preserve failure/retry lineage.
                if any(r["status"] == "running" for r in states.values()):
                    continue
                for node in json.loads(run["plan"]):
                    row = states[node["id"]]
                    if row["status"] != "queued" or not all(states[d]["status"] == "completed" for d in node["needs"]):
                        continue
                    token = identifier()
                    con.execute("UPDATE research_nodes SET status='running',attempt=attempt+1,lease_until=?,lease_token=? WHERE run_id=? AND node_id=?", (epoch + 120, token, run["id"], node["id"]))
                    con.execute("UPDATE research_runs SET status='running' WHERE id=?", (run["id"],))
                    selected = (dict(run), node, states, token, row["attempt"] + 1)
                    break
                if selected:
                    break
        if not selected:
            return {"processed": False}
        run, node, states, token, attempt = selected
        status, error = "completed", None
        try:
            params = node["params"]
            if node["tool"] == "source_collection":
                result = self.research.collect(params["symbols"], force=True)
                if any(r["errors"] for r in result["results"]):
                    raise RuntimeError("Source collection incomplete")
            elif node["tool"] == "bar_history":
                if not self.research.providers:
                    raise RuntimeError("Market provider unavailable")
                result = self.research.providers.bars(params["symbol"], range=params.get("range", "1mo"), interval=params.get("interval", "1d"))
                if not result.get("bars") or result.get("stale") or result.get("stale_cache"):
                    raise RuntimeError("Fresh requested bar history unavailable")
            elif node["tool"] == "catalogue_search":
                result = self.research.search(params["query"])
                if not result["configured"]:
                    raise RuntimeError("Repository catalogue unconfigured")
            else:
                result = {"scope": "Factual dependency evidence, not an investment conclusion", "plan_hash": run["plan_hash"], "dependencies": {d: json.loads(states[d]["result"]) for d in node["needs"]}, "strategy_count": 0}
            encoded = self.encode(result)
            if len(encoded.encode()) > 1_500_000:
                raise RuntimeError("Research result too large")
        except Exception:
            status, error = "failed", "Read-only research node failed; inspect configuration/source availability and retry"
            encoded = self.encode({"error": error, "tool": node["tool"]})
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        with self.store.transaction() as con:
            changed = con.execute("UPDATE research_nodes SET status=?,result=?,error=?,lease_until=0,lease_token=NULL WHERE run_id=? AND node_id=? AND lease_token=?", (status, encoded, error, run["id"], node["id"], token)).rowcount
            if not changed:
                return {"processed": True, "discarded": "Lease superseded; result not committed"}
            con.execute("INSERT INTO research_node_receipts VALUES(?,?,?,?,?,?,?,?)", (identifier(), run["id"], node["id"], attempt, status, encoded, digest, now()))
            if status == "failed":
                con.execute("UPDATE research_nodes SET status='blocked' WHERE run_id=? AND status='queued'", (run["id"],))
                con.execute("UPDATE research_runs SET status='failed',completed_at=? WHERE id=?", (now(), run["id"]))
            elif not con.execute("SELECT 1 FROM research_nodes WHERE run_id=? AND status!='completed'", (run["id"],)).fetchone():
                con.execute("UPDATE research_runs SET status='completed',completed_at=? WHERE id=?", (now(), run["id"]))
            self.store.event(con, "research_node_receipt", "research_coordinator", "Read-only node " + status, {"run_id": run["id"], "node_id": node["id"], "attempt": attempt, "sha256": digest, "plan_hash": run["plan_hash"]})
        return {"processed": True, "run_id": run["id"], "node_id": node["id"], "status": status}

    def snapshot(self):
        with self.store.connect() as con:
            workflows = [{**dict(r), "plan": json.loads(r["plan"]), "enabled": bool(r["enabled"])} for r in con.execute("SELECT * FROM research_workflows ORDER BY created_at DESC LIMIT 100")]
            runs = []
            for row in con.execute("SELECT * FROM research_runs ORDER BY created_at DESC LIMIT 100"):
                run = dict(row)
                run["nodes"] = []
                for item in con.execute("SELECT * FROM research_nodes WHERE run_id=? ORDER BY rowid", (row["id"],)):
                    result = item["result"]
                    run["nodes"].append({**dict(item), "lease_token": None, "result": json.loads(result) if result and len(result) <= 12000 else None, "result_bytes": len(result.encode()) if result else 0, "result_sha256": hashlib.sha256(result.encode()).hexdigest() if result else None, "result_omitted": bool(result and len(result) > 12000)})
                runs.append(run)
        return {"registered_tools": list(self.TOOLS), "workflows": workflows, "runs": runs, "authority": "Read-only source/data/catalogue operations; no shell or financial tools"}


def workflow_router(engine):
    router = APIRouter()

    class Strict(BaseModel):
        model_config = ConfigDict(extra="forbid")

    class Node(Strict):
        id: str = Field(min_length=1, max_length=80)
        tool: str
        params: dict = Field(default_factory=dict)
        needs: list[str] = Field(default_factory=list, max_length=12)

    class Plan(Strict):
        title: str = Field(min_length=1, max_length=200)
        nodes: list[Node] = Field(min_length=1, max_length=12)
        interval_seconds: int = Field(default=3600, ge=900, le=604800)

    class Enabled(Strict):
        enabled: bool

    @router.get("/workflows")
    def snapshot():
        return engine.snapshot()

    @router.post("/workflows")
    def register(body: Plan):
        return engine.register(body.title, [n.model_dump() for n in body.nodes], body.interval_seconds)

    @router.patch("/workflows/{rid}")
    def configure(rid: str, body: Enabled):
        return engine.configure(rid, body.enabled)

    @router.post("/workflows/{rid}/run")
    def run(rid: str):
        return engine.enqueue(rid)

    @router.post("/runs/{rid}/retry")
    def retry(rid: str):
        return engine.retry(rid)

    @router.post("/runs/{rid}/cancel")
    def cancel(rid: str):
        return engine.cancel(rid)

    @router.get("/runs/{rid}/nodes/{nid}")
    def node_result(rid: str, nid: str):
        with engine.store.connect() as con:
            row = con.execute("SELECT * FROM research_nodes WHERE run_id=? AND node_id=?", (rid, nid)).fetchone()
            if not row:
                raise DeskError("Research node not found", 404)
            return {**dict(row), "lease_token": None, "result": json.loads(row["result"]) if row["result"] else None}

    return router
