#!/usr/bin/env python3
"""Prompt dependency pinning lint. Round-5 item 35 (langfuse). Shared prompt
fragments are referenced by name plus pinned hash, never copy-pasted; a
reference whose pinned hash no longer matches is flagged. Reference syntax:
{{fragment:name@sha256hexprefix}} resolved against a fragments directory.
Eval results record fixture-set hash; eval IDs use dedup_ids (see done_check).
"""
import hashlib, os, re, sys, tempfile
REF=re.compile(r"\{\{fragment:([A-Za-z0-9_-]+)@([0-9a-f]{8,64})\}\}")
def frag_hash(path): return hashlib.sha256(open(path,'rb').read()).hexdigest()
def lint(text, frag_dir):
    errs=[]
    for name,pin in REF.findall(text):
        p=os.path.join(frag_dir,name)
        if not os.path.isfile(p): errs.append(f"fragment missing: {name}"); continue
        if not frag_hash(p).startswith(pin): errs.append(f"fragment hash drift: {name}")
    return errs
def selftest():
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td,"intro"),"w").write("hello fragment")
        h=frag_hash(os.path.join(td,"intro"))[:16]
        assert lint(f"use {{{{fragment:intro@{h}}}}}",td)==[]
        assert lint("use {{fragment:intro@deadbeefdeadbeef}}",td), "drift must flag"
        assert lint("use {{fragment:ghost@deadbeef}}",td), "missing must flag"
        print("SELFTEST PASS fragment_lint: matching pin passes, drifted pin and missing fragment flagged")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
