"""M7 evidence-only validation registry and qualification factory."""
from __future__ import annotations
import hashlib,json,os,sqlite3,uuid
from contextlib import closing
from datetime import datetime,timezone,timedelta
from pathlib import Path
from typing import Any

VERSIONS={
 "PX_1_3_0_EXACT":("PARALLAX","BASELINE_SHADOW"),"PX_1_3_0_CHALLENGER":("PARALLAX","CHALLENGER_SHADOW"),
 "LR_1_0_0_EXACT":("LEADERS_REST","BASELINE_SHADOW"),"LR_1_1_0_CORRECTED":("LEADERS_REST","CHALLENGER_SHADOW"),
 "LF_2_0_0_EXACT":("foliotend-location-first-swing","BASELINE_SHADOW"),"LF_2_1_0_CORRECTED":("foliotend-location-first-swing","CHALLENGER_SHADOW"),
}
def now()->str:return datetime.now(timezone.utc).isoformat()
def canonical(value:Any)->str:return json.dumps(value,sort_keys=True,separators=(",",":"),default=str)
def digest(value:Any)->str:return hashlib.sha256(canonical(value).encode()).hexdigest()
def parse(value:Any)->datetime|None:
    try:return datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone(timezone.utc)
    except (TypeError,ValueError):return None

class ValidationFactory:
    VERSION="m7-validation/1.0.0";AUTHORITY="SHADOW_EVIDENCE_NO_AUTO_PROMOTION"
    def __init__(self,path:Path,root:Path|None=None)->None:
        self.path,self.root=path,root or Path(__file__).resolve().parent
        with closing(sqlite3.connect(path,timeout=10)) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS m7_registry_events(event_id TEXT PRIMARY KEY,version_id TEXT NOT NULL,strategy_id TEXT NOT NULL,state TEXT NOT NULL,code_hash TEXT NOT NULL,config_hash TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS m7_experiment_records(experiment_id TEXT PRIMARY KEY,observed_at TEXT NOT NULL,status TEXT NOT NULL,passed INTEGER NOT NULL,total INTEGER NOT NULL,evidence_hash TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS m7_registry_version ON m7_registry_events(version_id,created_at);
            CREATE TRIGGER IF NOT EXISTS m7_registry_no_update BEFORE UPDATE ON m7_registry_events BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS m7_registry_no_delete BEFORE DELETE ON m7_registry_events BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS m7_experiments_no_update BEFORE UPDATE ON m7_experiment_records BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS m7_experiments_no_delete BEFORE DELETE ON m7_experiment_records BEGIN SELECT RAISE(ABORT,'append-only');END;
            """);db.commit()
        self.seed_registry()
    def code_hash(self)->str:return hashlib.sha256((self.root/"strategy_system.py").read_bytes()).hexdigest()
    def config_hash(self)->str:return hashlib.sha256((self.root/"config.json").read_bytes()).hexdigest()
    def seed_registry(self)->None:
        code,config,stamp=self.code_hash(),self.config_hash(),now()
        with closing(sqlite3.connect(self.path,timeout=10)) as db:
            for version,(strategy,state) in VERSIONS.items():
                event_id=f"registry:{version}:foundation"
                payload={"versionId":version,"strategyId":strategy,"state":state,"frozen":True,"authority":self.AUTHORITY}
                db.execute("INSERT OR IGNORE INTO m7_registry_events VALUES(?,?,?,?,?,?,?,?,?)",(event_id,version,strategy,state,code,config,"M7_FOUNDATION_REGISTRATION",stamp,canonical(payload)))
            db.commit()
    @staticmethod
    def criterion(name:str,passed:bool,observed:Any,required:Any,scope:str="GLOBAL")->dict[str,Any]:return {"name":name,"passed":bool(passed),"observed":observed,"required":required,"scope":scope}
    def registry(self)->list[dict[str,Any]]:
        with closing(sqlite3.connect(self.path,timeout=10)) as db:
            db.row_factory=sqlite3.Row;rows=db.execute("SELECT * FROM m7_registry_events ORDER BY version_id,created_at").fetchall()
        latest={str(row["version_id"]):dict(row) for row in rows}
        return [{"versionId":key,"strategyId":row["strategy_id"],"state":row["state"],"codeHash":row["code_hash"],"configHash":row["config_hash"],"frozen":True,"createdAt":row["created_at"]} for key,row in sorted(latest.items())]
    def _version_evidence(self,db:sqlite3.Connection,version:str)->dict[str,Any]:
        decisions=int(db.execute("SELECT COUNT(*) FROM strategy_decisions WHERE scanner_version=?",(version,)).fetchone()[0]);sessions=int(db.execute("SELECT COUNT(DISTINCT substr(as_of,1,10)) FROM strategy_decisions WHERE scanner_version=? AND as_of LIKE '%T%'",(version,)).fetchone()[0]);contexts=int(db.execute("SELECT COUNT(*) FROM strategy_decisions d JOIN strategy_decision_contexts c ON c.decision_id=d.decision_id WHERE d.scanner_version=?",(version,)).fetchone()[0]);outcomes=int(db.execute("SELECT COUNT(*) FROM decision_outcomes o JOIN strategy_decisions d ON d.decision_id=o.decision_id WHERE d.scanner_version=?",(version,)).fetchone()[0])
        rows=db.execute("SELECT d.as_of,c.completed_bar_cutoff FROM strategy_decisions d LEFT JOIN strategy_decision_contexts c ON c.decision_id=d.decision_id WHERE d.scanner_version=?",(version,)).fetchall();invalid=0;future=0
        for as_of,cutoff in rows:
            if cutoff is None:continue
            a,c=parse(as_of),parse(cutoff)
            if a is None or c is None:invalid+=1
            elif c>a:future+=1
        collisions=int(db.execute("SELECT COUNT(*) FROM (SELECT evidence_hash,COUNT(DISTINCT payload) n FROM strategy_decisions WHERE scanner_version=? GROUP BY evidence_hash HAVING n>1)",(version,)).fetchone()[0])
        return {"decisions":decisions,"sessions":sessions,"contexts":contexts,"contextCoverage":round(contexts/decisions,4) if decisions else 0,"outcomes":outcomes,"invalidTimestamps":invalid,"futureCutoffs":future,"evidenceCollisions":collisions}
    def evaluate(self,m6:dict[str,Any],reference:dict[str,Any],reality:dict[str,Any],studies:dict[str,Any]|None=None,robustness:dict[str,Any]|None=None)->dict[str,Any]:
        with closing(sqlite3.connect(self.path,timeout=10)) as db:
            registry=self.registry();per_version={version:self._version_evidence(db,version) for version in VERSIONS};replay_rows=db.execute("SELECT status,mismatch_count,details FROM replay_runs").fetchall();compatible=[]
            for replay_status,replay_mismatches,replay_details in replay_rows:
                try: drift=bool(json.loads(replay_details).get("codeDrift"))
                except (TypeError,ValueError,json.JSONDecodeError): drift=True
                if not drift:compatible.append((replay_status,replay_mismatches))
            replay_pass=sum(status=="PASS" and mismatches==0 for status,mismatches in compatible);replay_fail=sum(status=="FAIL" or mismatches>0 for status,mismatches in compatible)
        criteria=[]
        for version,evidence in per_version.items():
            criteria.extend([self.criterion("decision_sample",evidence["decisions"]>=100,evidence["decisions"],">=100",version),self.criterion("session_sample",evidence["sessions"]>=5,evidence["sessions"],">=5",version),self.criterion("context_coverage",evidence["contextCoverage"]==1,evidence["contextCoverage"],"1.0",version),self.criterion("timestamp_integrity",evidence["invalidTimestamps"]==0 and evidence["futureCutoffs"]==0,{"invalid":evidence["invalidTimestamps"],"future":evidence["futureCutoffs"]},"0 violations",version),self.criterion("evidence_hash_integrity",evidence["evidenceCollisions"]==0,evidence["evidenceCollisions"],"0",version),self.criterion("completed_outcomes",evidence["outcomes"]>=20,evidence["outcomes"],">=20",version)])
        sources=reference.get("sources") or {};studies=studies or {};robustness=robustness or {};version_studies=studies.get("versions") or {};walk_pass=all((((version_studies.get(version) or {}).get("walkForward") or {}).get("passed") is True) for version in VERSIONS);holdout_pass=all((((version_studies.get(version) or {}).get("holdout") or {}).get("passed") is True) for version in VERSIONS);robust={item.get("name"):item for item in robustness.get("criteria",[])};baseline_pass=bool((robust.get("spy_benchmark") or {}).get("passed"));regime_pass=bool((robust.get("regime_stability") or {}).get("passed"));neighborhood_pass=bool((robust.get("version_neighborhood") or {}).get("passed"))
        criteria.extend([self.criterion("frozen_registry",len(registry)==len(VERSIONS) and all(item["frozen"] for item in registry),len(registry),len(VERSIONS)),self.criterion("clean_replays",replay_pass>=5 and replay_fail==0,{"pass":replay_pass,"fail":replay_fail},">=5 pass, 0 fail"),self.criterion("m6_eligible",m6.get("status")=="ELIGIBLE_FOR_REVIEW",m6.get("status"),"ELIGIBLE_FOR_REVIEW"),self.criterion("brokerage_cost_model",reality.get("status")=="READY",reality.get("status"),"READY"),self.criterion("corporate_action_reference",(sources.get("corporate-actions") or {}).get("state")=="READY",(sources.get("corporate-actions") or {}).get("state"),"READY"),self.criterion("purged_walk_forward",walk_pass,studies.get("status") or "PENDING","ALL_6_PASS"),self.criterion("untouched_holdout",holdout_pass,{"sealed":studies.get("sealedHoldouts",0),"status":studies.get("status")},"ALL_6_PASS"),self.criterion("spy_benchmark",baseline_pass,(robust.get("spy_benchmark") or {}).get("observed",robustness.get("status") or "PENDING"),"6"),self.criterion("regime_stability",regime_pass,(robust.get("regime_stability") or {}).get("observed",robustness.get("status") or "PENDING"),"6"),self.criterion("version_neighborhood",neighborhood_pass,(robust.get("version_neighborhood") or {}).get("observed",robustness.get("status") or "PENDING"),"3")])
        passed=sum(item["passed"] for item in criteria);status="ELIGIBLE_FOR_HUMAN_REVIEW" if passed==len(criteria) else "REGRESSION" if replay_fail else "SHADOW_BUILDING";stamp=now()
        result={"version":self.VERSION,"authority":self.AUTHORITY,"status":status,"passed":passed,"total":len(criteria),"observedAt":stamp,"registry":registry,"perVersion":per_version,"criteria":criteria,"studiesEvidenceHash":studies.get("evidenceHash"),"robustnessEvidenceHash":robustness.get("evidenceHash"),"automaticPromotion":False,"brokerAuthority":False,"nextGate":"COMPLETED_OUTCOMES" if studies.get("status") in {None,"PENDING","INSUFFICIENT_EVIDENCE"} else "HUMAN_REVIEW"}
        evidence_hash=digest(result);experiment_id=f"m7:{evidence_hash[:24]}";result["experimentId"]=experiment_id;result["evidenceHash"]=evidence_hash
        with closing(sqlite3.connect(self.path,timeout=10)) as db:db.execute("INSERT OR IGNORE INTO m7_experiment_records VALUES(?,?,?,?,?,?,?)",(experiment_id,stamp,status,passed,len(criteria),evidence_hash,canonical(result)));db.commit()
        return result
    def evaluate_if_due(self,m6:dict[str,Any],reference:dict[str,Any],reality:dict[str,Any],studies:dict[str,Any]|None=None,robustness:dict[str,Any]|None=None,hours:float=24)->dict[str,Any]|None:
        with closing(sqlite3.connect(self.path,timeout=10)) as db:row=db.execute("SELECT observed_at FROM m7_experiment_records ORDER BY observed_at DESC LIMIT 1").fetchone()
        if row and datetime.now(timezone.utc)-(parse(row[0]) or datetime.min.replace(tzinfo=timezone.utc))<timedelta(hours=hours):return None
        return self.evaluate(m6,reference,reality,studies,robustness)
    def health(self)->dict[str,Any]:
        with closing(sqlite3.connect(self.path,timeout=10)) as db:
            row=db.execute("SELECT experiment_id,observed_at,status,passed,total,evidence_hash,payload FROM m7_experiment_records ORDER BY observed_at DESC LIMIT 1").fetchone();count=int(db.execute("SELECT COUNT(*) FROM m7_experiment_records").fetchone()[0])
        if not row:return {"version":self.VERSION,"authority":self.AUTHORITY,"status":"PENDING","experiments":0,"registry":self.registry(),"automaticPromotion":False}
        payload=json.loads(row[6]);return {"version":self.VERSION,"authority":self.AUTHORITY,"status":row[2],"experiments":count,"passed":row[3],"total":row[4],"observedAt":row[1],"experimentId":row[0],"evidenceHash":row[5],"registry":payload.get("registry",[]),"nextGate":payload.get("nextGate"),"automaticPromotion":False}
    def write_report(self,result:dict[str,Any],report_root:Path|None=None)->tuple[Path,Path]:
        root=report_root or Path(os.environ.get("LOCALAPPDATA",str(self.path.parent)))/"AlpacaPaperDesk"/"reports";root.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ");machine=root/f"m7-validation-{stamp}.json";report=root/f"m7-validation-{stamp}.md";machine.write_text(json.dumps(result,indent=2),encoding="utf-8")
        lines=["# M7 Shadow Validation Report","",f"- Status: **{result['status']}** ({result['passed']}/{result['total']})",f"- Experiment: `{result['experimentId']}`",f"- Evidence: `{result['evidenceHash']}`",f"- Authority: `{result['authority']}`","- Automatic promotion: **NO**","","| Scope | Criterion | Pass | Observed | Required |","|---|---|---:|---|---|"]
        for item in result["criteria"]:lines.append(f"| {item['scope']} | {item['name']} | {'YES' if item['passed'] else 'NO'} | `{canonical(item['observed'])}` | `{item['required']}` |")
        report.write_text("\n".join(lines)+"\n",encoding="utf-8");return report,machine
