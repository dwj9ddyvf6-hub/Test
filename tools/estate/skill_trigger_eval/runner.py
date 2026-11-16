#!/usr/bin/env python3
"""Skill trigger eval, phase 1: eval-set format + runner. Round-5 item 27
(anthropics skill-creator). Eval set JSON: {skill, cases:[{query, expect:
trigger|no-trigger, split: train|test}]}. Runner scores a matcher callable
in tests; in production the matcher is the host trigger decision recorded
per run (3 runs per query, threshold 0.5, winner selected on TEST score).
Improver loop (phase 2) is an open row in IMPLEMENT.md.
"""
import json, sys, tempfile, os
def split_cases(cases):
    return [c for c in cases if c.get("split")=="train"], [c for c in cases if c.get("split")=="test"]
def score(cases, matcher, runs=3, threshold=0.5):
    tp=fp=fn=tn=0
    for c in cases:
        hits=sum(1 for _ in range(runs) if matcher(c["query"]))/runs
        fired=hits>=threshold
        if fired and c["expect"]=="trigger": tp+=1
        elif fired: fp+=1
        elif c["expect"]=="trigger": fn+=1
        else: tn+=1
    total=tp+fp+fn+tn
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,"accuracy":(tp+tn)/total if total else 0.0,"runs_per_query":runs,"threshold":threshold}
def benchmark_line(before, after):
    return f"benchmark delta: accuracy {before['accuracy']:.3f} -> {after['accuracy']:.3f}"
def selftest():
    cases=[{"query":"book a flight","expect":"trigger","split":"test"},
           {"query":"what is the weather","expect":"no-trigger","split":"test"},
           {"query":"fly me to Boston","expect":"trigger","split":"train"}]
    tr,te=split_cases(cases); assert len(tr)==1 and len(te)==2
    good=lambda q: ("flight" in q or "fly" in q)
    s=score(te,good); assert s["accuracy"]==1.0, s
    bad=lambda q: True; assert score(te,bad)["accuracy"]==0.5
    print("SELFTEST PASS skill_trigger_eval: stratified split, 3-run 0.5-threshold scoring, perfect matcher 1.0, always-fire matcher 0.5 on test split")
    print(benchmark_line(score(te,bad),s))
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
