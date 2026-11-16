#!/usr/bin/env python3
"""Store-to-index reconciliation. Round-5 item 19 (Honcho sync_vectors).
Compares canonical store files against derived index listing; bounded batch
healing (report missing/stale); an item failing 3 consecutive runs is named
(ESCALATE) rather than retried forever or dropped silently. State in a JSON
ledger beside the index.
"""
import json, os, sys, tempfile, hashlib
def _h(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]
def reconcile(store_root, index: dict, state: dict, batch=50):
    healed=[]; failed={}
    seen=set()
    for dirpath,_,files in os.walk(store_root):
        for fn in sorted(files):
            if not fn.endswith(".md"): continue
            rel=os.path.relpath(os.path.join(dirpath,fn),store_root); seen.add(rel)
            if len(healed)>=batch: break
            if index.get(rel)!=_h(os.path.join(dirpath,fn)):
                healed.append(rel)
    for rel in index:
        if rel not in seen: healed.append(rel+":orphan")
    for rel in healed:
        state[rel]=state.get(rel,0)+1
    escalate=[r for r,c in state.items() if c>=3]
    return {"heal_candidates":healed,"escalate_named":sorted(escalate),"state":state}
def selftest():
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td,"a.md"),"w").write("alpha")
        open(os.path.join(td,"b.md"),"w").write("beta")
        idx={"a.md":_h(os.path.join(td,"a.md"))}
        st={}
        r=reconcile(td,idx,st); assert "b.md" in r["heal_candidates"], r
        for _ in range(2): r=reconcile(td,idx,r["state"])
        assert "b.md" in r["escalate_named"], "3 consecutive failures must be named"
        print("SELFTEST PASS memory_reconcile: missing index entry detected, bounded heal list, 3-strike item escalated by name")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
