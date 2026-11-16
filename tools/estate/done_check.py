#!/usr/bin/env python3
"""Done-check gate design spec. Round-5 item 36 (ECC delivery-gate +
done-gate + context-guard stop gate). Blocks only on machine-verifiable
facts; heuristics warn only. Block-once fingerprint = sha256(hook, session,
text). Config errors fail closed; gate crashes fail open and log.
Interruptions budgeted; exhaustion degrades to named UNVERIFIED. Completion
requires unique-candidate cover: every obligation matched by exactly one
evidence record.
"""
import hashlib, json, sys, tempfile, os
def fingerprint(hook, session, text): return hashlib.sha256(f"{hook}\0{session}\0{text}".encode()).hexdigest()
def cover(obligations, evidence):
    """evidence: list of {id, covers}. Return (ok, uncovered, ambiguous)."""
    uncovered=[]; ambiguous=[]
    for ob in obligations:
        cands=[e for e in evidence if ob in e.get("covers",[])]
        if not cands: uncovered.append(ob)
        elif len(cands)>1: ambiguous.append(ob)
    return (not uncovered and not ambiguous), uncovered, ambiguous
class Gate:
    def __init__(self, budget=3): self.budget=budget; self.blocks=0; self.seen=set()
    def evaluate(self, obligations, evidence, config_ok=True):
        if not config_ok: return {"verdict":"BLOCKED","reason":"config error: fail closed"}
        fp=fingerprint("done","s",json.dumps(obligations,sort_keys=True))
        ok,unc,amb=cover(obligations,evidence)
        if ok: return {"verdict":"GREEN","reason":"unique-candidate cover complete"}
        if fp in self.seen: return {"verdict":"UNVERIFIED","reason":"block-once: already blocked on this fingerprint"}
        self.seen.add(fp); self.blocks+=1
        if self.blocks>self.budget: return {"verdict":"UNVERIFIED","reason":"interruption budget exhausted"}
        return {"verdict":"BLOCKED","reason":f"uncovered={unc} ambiguous={amb}","next_step":"supply evidence records"}
def selftest():
    g=Gate()
    ev=[{"id":"e1","covers":["tests pass"]},{"id":"e2","covers":["read back"]}]
    assert g.evaluate(["tests pass","read back"],ev)["verdict"]=="GREEN"
    g2=Gate(); r=g2.evaluate(["tests pass"],[])
    assert r["verdict"]=="BLOCKED" and "next_step" in r
    assert g2.evaluate(["tests pass"],[])["verdict"]=="UNVERIFIED", "block-once fingerprint"
    assert Gate().evaluate(["x"],[],config_ok=False)["verdict"]=="BLOCKED"
    ok,unc,amb=cover(["a"],[{"id":"1","covers":["a"]},{"id":"2","covers":["a"]}])
    assert not ok and amb==["a"], "ambiguous cover must not pass"
    print("SELFTEST PASS done_check: unique cover GREEN, uncovered BLOCKED with next step, repeat is UNVERIFIED (block-once), config error fail-closed, ambiguous cover rejected")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
