#!/usr/bin/env python3
"""Near-miss ledger. Round-5 discipline 17 (ink-planner near_misses.py).
Diagnostics-only records of matched-but-not-admitted proposals. Bounded:
MAX_LAWS 4096, MAX_REPORTED 512, MAX_SAMPLES 4, MAX_TEXT 400. A record does
NOT establish the class can never apply; an absent record establishes
nothing; the ledger never feeds ranking, selection, or rejection counts.
"""
import json, sys, tempfile, os, re
MAX_LAWS=4096; MAX_REPORTED=512; MAX_SAMPLES=4; MAX_TEXT=400
GATES={"threshold","scope","authority","freshness","cost","other"}
def skeleton(text):
    t=re.sub(r"\b\d+(\.\d+)?\b","<n>",str(text)); t=re.sub(r"['\"][^'\"]*['\"]","<s>",t)
    return t[:MAX_TEXT]
class NearMissLedger:
    def __init__(self, path): self.path=path; self.rows=[]
        # load
    def load(self):
        if os.path.exists(self.path):
            self.rows=[json.loads(l) for l in open(self.path,encoding="utf-8") if l.strip()][:MAX_LAWS]
        return self
    def record(self, law_id, gate, premise):
        assert gate in GATES, f"gate must be coarse class {GATES}"
        if len(self.rows)>=MAX_LAWS: return False
        self.rows.append({"law":str(law_id)[:MAX_TEXT],"gate":gate,"skeleton":skeleton(premise)})
        with open(self.path,"a",encoding="utf-8") as f: f.write(json.dumps(self.rows[-1])+"\n")
        return True
    def report(self):
        out=self.rows[:MAX_REPORTED]
        by={}
        for r in out: by[r["gate"]]=by.get(r["gate"],0)+1
        samples={}
        for r in out: samples.setdefault(r["law"],[])
        for r in out:
            if len(samples[r["law"]])<MAX_SAMPLES: samples[r["law"]].append(r["skeleton"])
        return {"count":len(out),"by_gate":by,"samples":samples,
                "non_authority":"diagnostics only: no ranking, selection, or rejection inference"}
def selftest():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,"nm.jsonl"); led=NearMissLedger(p).load()
        assert led.record("gate-a","threshold","score 0.42 below 0.7 for 'secret value'")
        assert led.rows[0]["skeleton"]=="score <n> below <n> for <s>", led.rows[0]
        rep=led.report(); assert rep["count"]==1 and rep["by_gate"]=={"threshold":1}
        try: led.record("x","bogus","y"); raise SystemExit("gate class not enforced")
        except AssertionError: pass
        print("SELFTEST PASS near_misses: skeleton erases params, coarse gate enforced, bounded report, non-authority stated")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
