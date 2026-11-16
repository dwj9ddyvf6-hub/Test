#!/usr/bin/env python3
"""Gate mutation harness. Round-5 item 14 (done-gate tests/mutate.py).
Each local gate carries named mutants that neuter its core check; the
harness applies each mutant to a scratch copy and requires the gate's own
selftest to go RED (mutant killed). 0 survived required. Seeded fuzz mode
prints cases= and seed= (frontier/rill form).
"""
import random, shutil, subprocess, sys, tempfile, os
# Mutants: (gate file, description, old, new)
MUTANTS=[
 ("dedup_ids.py","dedup always unique","if rid in seen:","if False and rid in seen:"),
 ("sendcheck.py","caps never block","if words > CAPS_WORDS[surface]:","if False and words > CAPS_WORDS[surface]:"),
 ("proactive_gate.py","tau always zero","return c_fa/denom","return 0.0"),
]
TOOLS="/home/hatch/workspace/tools"
def run_mutant(fn,desc,old,new):
    with tempfile.TemporaryDirectory() as td:
        src=open(os.path.join(TOOLS,fn),encoding="utf-8").read()
        assert old in src, f"mutant anchor missing in {fn}"
        p=os.path.join(td,fn); open(p,"w",encoding="utf-8").write(src.replace(old,new,1))
        r=subprocess.run([sys.executable,p,"selftest"],capture_output=True,text=True)
        return r.returncode!=0  # killed if selftest fails
def seeded_fuzz(seed=20261102, cases=200):
    rnd=random.Random(seed); import importlib.util
    spec=importlib.util.spec_from_file_location("dd",os.path.join(TOOLS,"dedup_ids.py")); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for i in range(cases):
        parts=[rnd.choice(["a","b",1,2,None]) for _ in range(rnd.randint(1,4))]
        assert m.deterministic_id(parts)==m.deterministic_id(list(parts))
    print(f"SEEDED FUZZ PASS cases={cases} seed={seed}")
def selftest():
    killed=0
    for fn,desc,old,new in MUTANTS:
        k=run_mutant(fn,desc,old,new); print(f"mutant {fn}: {desc}: {'KILLED' if k else 'SURVIVED'}")
        killed+=k
    assert killed==len(MUTANTS), f"{len(MUTANTS)-killed} mutants survived"
    seeded_fuzz()
    print(f"SELFTEST PASS mutation_harness: {killed}/{len(MUTANTS)} mutants killed, 0 survived")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
