#!/usr/bin/env python3
"""Content-bound approvals. Round-5 discipline 18 (codex-context-guard
cg_authority.py + bounded-loops trust_store.py). An approval binds a stated
action once to resolved target identity fields + sha256 of content; any
post-trust edit invalidates; 30-day default expiry; revocable; generation
counter voids pre-compaction bindings. Five-way ladder:
authorized_unique / requires_selection / authorization_invalid / drifted /
out_of_scope. Publish implies nothing toward unpublish (no implications
beyond the exact action recorded).
"""
import hashlib, json, sys, tempfile, os, time
def content_hash(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
class ApprovalStore:
    def __init__(self, path, generation=0):
        self.path=path; self.generation=generation; self.rows=[]
        if os.path.exists(path):
            self.rows=[json.loads(l) for l in open(path,encoding="utf-8") if l.strip()]
    def _save(self):
        with open(self.path,"w",encoding="utf-8") as f:
            for r in self.rows: f.write(json.dumps(r)+"\n")
    def record(self, action, target: dict, content: bytes, ttl_days=30, now=None):
        now=time.time() if now is None else now
        rec={"action":action,"target":target,"hash":content_hash(content),
             "generation":self.generation,"expires":now+ttl_days*86400,"revoked":False,"used":False}
        self.rows.append(rec); self._save(); return rec
    def revoke(self, action, target):
        for r in self.rows:
            if r["action"]==action and r["target"]==target: r["revoked"]=True
        self._save()
    def check(self, action, candidates: list, content: bytes, now=None) -> str:
        now=time.time() if now is None else now
        matches=[r for r in self.rows if r["action"]==action and r["target"] in candidates]
        if not matches: return "out_of_scope"
        valid=[r for r in matches if not r["revoked"] and not r["used"] and r["expires"]>now and r["generation"]==self.generation]
        if not valid: return "authorization_invalid"
        if len(candidates)>1 and len({json.dumps(c,sort_keys=True) for c in candidates})>1 and len(valid)>1: return "requires_selection"
        r=valid[0]
        if r["hash"]!=content_hash(content): return "drifted"
        if r["target"] not in candidates: return "out_of_scope"
        return "authorized_unique"
    def consume(self, action, target):
        for r in self.rows:
            if r["action"]==action and r["target"]==target and not r["used"]: r["used"]=True
        self._save()
def selftest():
    with tempfile.TemporaryDirectory() as td:
        s=ApprovalStore(os.path.join(td,"a.jsonl"), generation=1)
        tgt={"repo":"example/repo","path":"docs/x.md"}
        s.record("publish", tgt, b"v1 content", now=1000.0)
        assert s.check("publish",[tgt],b"v1 content",now=2000.0)=="authorized_unique"
        assert s.check("publish",[tgt],b"v2 edited",now=2000.0)=="drifted", "post-trust edit must invalidate"
        assert s.check("unpublish",[tgt],b"v1 content",now=2000.0)=="out_of_scope", "publish must not imply unpublish"
        assert s.check("publish",[tgt],b"v1 content",now=1000.0+31*86400)=="authorization_invalid", "expiry"
        s2=ApprovalStore(os.path.join(td,"a.jsonl"), generation=2)
        assert s2.check("publish",[tgt],b"v1 content",now=2000.0)=="authorization_invalid", "generation void"
        s.consume("publish",tgt); assert s.check("publish",[tgt],b"v1 content",now=2000.0)=="authorization_invalid", "one-shot"
        print("SELFTEST PASS approvals: authorized_unique, drifted on edit, out_of_scope on unpublish, expired invalid, generation void, one-shot consume")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
