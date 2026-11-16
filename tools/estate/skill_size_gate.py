#!/usr/bin/env python3
"""Compaction-cut size gate. Round-5 item 26 (Superpowers skill-size tests).
A SKILL.md at or over 20,000 bytes loses its tail silently after compaction.
Oversized skills must split body plus references. Gate-wired checker.
"""
import os, sys, tempfile
LIMIT=20000
def check(path):
    n=os.path.getsize(path); return {"path":path,"bytes":n,"ok":n<LIMIT}
def check_tree(roots):
    bad=[]
    for root in roots:
        for dirpath,_,files in os.walk(root):
            for fn in files:
                if fn=="SKILL.md":
                    r=check(os.path.join(dirpath,fn))
                    if not r["ok"]: bad.append(r)
    return bad
def selftest():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,"SKILL.md"); open(p,"w").write("x"*100)
        assert check(p)["ok"]
        open(p,"w").write("x"*20000); assert not check(p)["ok"], "at-limit must fail"
        print("SELFTEST PASS skill_size_gate: 100B passes, 20000B fails at the compaction-cut limit")
    return 0
if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="selftest": raise SystemExit(selftest())
    bad=check_tree(sys.argv[1:] or ["/home/hatch/workspace/custom-skills"])
    for b in bad: print(f"OVERSIZED {b['bytes']} {b['path']}")
    print(f"checked roots={sys.argv[1:]} oversized={len(bad)}")
    raise SystemExit(1 if bad else 0)
