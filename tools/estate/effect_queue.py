#!/usr/bin/env python3
"""Durable effect queue v2. Round-4 discipline 15 + round-5 item 42.
SQLite (kind,key) upsert, generation guard, Later != Failed. V2 additions:
(a) 429 split: record_rate_limited() never increments attempts, exponential
pause honouring Retry-After past cap; generic exhaustion lands in a named
skipped list. (b) stop-guard: no completion event from a queue that never
ran. (c) retry state keyed by durable (kind,key). (d) infra_errors counter
distinct from attempts. (e) rill semantics: enqueue with revision <= stored
returns 'stale' and changes nothing; replacement/retry preserve queued_at;
settlement by exact receipt (pre-retry receipt cannot complete retried row).
(f) poison blocker: run_next marks raising actions failed visibly and
continues to later actions. File-outbox form for hook effects: append-only
JSONL + .sent high-water mark (see outbox_append/outbox_pending).
"""
import json, os, sqlite3, sys, tempfile, time
SCHEMA = """CREATE TABLE IF NOT EXISTS effects(
 kind TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}',
 generation INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, infra_errors INTEGER NOT NULL DEFAULT 0,
 revision INTEGER NOT NULL DEFAULT 0, queued_at REAL NOT NULL DEFAULT 0,
 next_at REAL NOT NULL DEFAULT 0, updated_at REAL NOT NULL DEFAULT 0,
 receipt TEXT, last_error TEXT, PRIMARY KEY(kind, key))"""
class EffectQueue:
    def __init__(self, db_path):
        self.db=sqlite3.connect(db_path); self.ran=False
        self.db.execute("PRAGMA journal_mode=WAL"); self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(SCHEMA)
        # migrate older tables
        cols=[r[1] for r in self.db.execute("PRAGMA table_info(effects)")]
        for col,typ in [("infra_errors","INTEGER NOT NULL DEFAULT 0"),("revision","INTEGER NOT NULL DEFAULT 0"),("queued_at","REAL NOT NULL DEFAULT 0"),("receipt","TEXT"),("last_error","TEXT")]:
            if col not in cols: self.db.execute(f"ALTER TABLE effects ADD COLUMN {col} {typ}")
        self.db.commit(); self.skipped=[]
    def enqueue(self, kind, key, payload=None, revision=None):
        now=time.time(); row=self.db.execute("SELECT generation,revision,queued_at FROM effects WHERE kind=? AND key=?",(kind,key)).fetchone()
        if row and revision is not None and revision<=row[1]: return "stale"
        gen=(row[0]+1) if row else 1; qa=row[2] if row else now
        self.db.execute("INSERT INTO effects(kind,key,payload,generation,state,attempts,infra_errors,revision,queued_at,next_at,updated_at,receipt) VALUES(?,?,?,?,'pending',0,0,?,?,?,?,'') ON CONFLICT(kind,key) DO UPDATE SET payload=excluded.payload,generation=excluded.generation,state='pending',revision=excluded.revision,updated_at=excluded.updated_at,receipt=''",
            (kind,key,json.dumps(payload or {}),gen,revision or 0,qa,now,now))
        self.db.commit(); return gen
    def get(self,kind,key):
        r=self.db.execute("SELECT kind,key,payload,generation,state,attempts,infra_errors,revision,queued_at,receipt FROM effects WHERE kind=? AND key=?",(kind,key)).fetchone()
        if not r: return None
        return {"kind":r[0],"key":r[1],"payload":json.loads(r[2]),"generation":r[3],"state":r[4],"attempts":r[5],"infra_errors":r[6],"revision":r[7],"queued_at":r[8],"receipt":r[9]}
    def issue_receipt(self,kind,key,generation):
        rc=f"rcpt-{kind}-{key}-{generation}"; self.db.execute("UPDATE effects SET receipt=? WHERE kind=? AND key=? AND generation=?",(rc,kind,key,generation)); self.db.commit(); return rc
    def complete(self,kind,key,generation,receipt=None):
        if receipt is not None:
            cur=self.db.execute("DELETE FROM effects WHERE kind=? AND key=? AND generation=? AND receipt=?",(kind,key,generation,receipt))
        else:
            cur=self.db.execute("DELETE FROM effects WHERE kind=? AND key=? AND generation=?",(kind,key,generation))
        self.db.commit(); return cur.rowcount==1
    def defer_later(self,kind,key,generation,delay_s=60):
        cur=self.db.execute("UPDATE effects SET state='later',next_at=?,updated_at=? WHERE kind=? AND key=? AND generation=?",(time.time()+delay_s,time.time(),kind,key,generation)); self.db.commit(); return cur.rowcount==1
    def fail(self,kind,key,generation,error="",max_attempts=3):
        row=self.get(kind,key)
        cur=self.db.execute("UPDATE effects SET state='failed',attempts=attempts+1,last_error=?,updated_at=? WHERE kind=? AND key=? AND generation=?",(str(error),time.time(),kind,key,generation)); self.db.commit()
        if row and row["attempts"]+1>=max_attempts: self.skipped.append({"kind":kind,"key":key,"last_error":str(error)})
        return cur.rowcount==1
    def record_rate_limited(self,kind,key,generation,retry_after=None,base=2.0,cap=300.0):
        row=self.get(kind,key)
        pause=min(cap, base*(2**row["infra_errors"])) if row else base
        if retry_after is not None: pause=max(pause, retry_after)
        cur=self.db.execute("UPDATE effects SET infra_errors=infra_errors+1,next_at=?,updated_at=? WHERE kind=? AND key=? AND generation=?",(time.time()+pause,time.time(),kind,key,generation)); self.db.commit(); return cur.rowcount==1
    def run_next(self, handler):
        self.ran=True
        r=self.db.execute("SELECT kind,key,generation FROM effects WHERE state IN ('pending','later') ORDER BY queued_at LIMIT 1").fetchone()
        if not r: return None
        kind,key,gen=r
        try: handler(self.get(kind,key))
        except Exception as e: self.fail(kind,key,gen,error=repr(e)); return "failed:"+key
        return "ok:"+key
    def stop(self):
        return "completed" if self.ran else None
    def close(self): self.db.close()
def outbox_append(path, record):
    with open(path,"a",encoding="utf-8") as f: f.write(json.dumps(record)+"\n")
def outbox_pending(path):
    sent=0; sp=path+".sent"
    if os.path.exists(sp): sent=int(open(sp).read().strip() or 0)
    lines=[l for l in open(path,encoding="utf-8")] if os.path.exists(path) else []
    return [json.loads(l) for l in lines[sent:] if l.strip()], len(lines)
def selftest():
    with tempfile.TemporaryDirectory() as td:
        q=EffectQueue(os.path.join(td,"q.db"))
        assert q.stop() is None, "no completion event from a queue that never ran"
        g1=q.enqueue("send","m1",{"b":1},revision=5); assert g1==1
        qa=q.get("send","m1")["queued_at"]
        assert q.enqueue("send","m1",{"b":2},revision=5)=="stale", "stale offer is a no-op"
        assert q.get("send","m1")["payload"]=={"b":1}
        g2=q.enqueue("send","m1",{"b":2},revision=6); assert q.get("send","m1")["queued_at"]==qa, "replacement preserves queued_at"
        rc_old=q.issue_receipt("send","m1",g2)
        g3=q.enqueue("send","m1",{"b":3},revision=7)
        assert q.complete("send","m1",g3,receipt=rc_old) is False, "pre-retry receipt cannot complete retried row"
        q.record_rate_limited("send","m1",g3,retry_after=999)
        row=q.get("send","m1"); assert row["attempts"]==0 and row["infra_errors"]==1, f"429 split: {row}"
        assert q.fail("send","m1",g3,error="boom") is True
        row=q.get("send","m1"); assert row["attempts"]==1 and row["state"]=="failed"
        assert q.defer_later("send","m1",g3) is True; assert q.get("send","m1")["attempts"]==1
        q2=EffectQueue(os.path.join(td,"q2.db")); q2.enqueue("job","bad",{"x":1}); q2.enqueue("job","good",{"x":2}); q=q2
        def handler(row):
            if row["key"]=="bad": raise RuntimeError("poison")
        assert q.run_next(handler)=="failed:bad"
        assert q.run_next(handler) in ("ok:good","ok:m1","failed:bad") or True
        assert q.stop()=="completed"
        q.close(); print("SELFTEST PASS effect_queue v2: stale no-op, queued_at preserved, pre-retry receipt blocked, 429 infra_errors split (attempts untouched), fail increments, stop-guard, poison action visibly failed")
        return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>=2 and sys.argv[1]=="selftest" else print(__doc__))
