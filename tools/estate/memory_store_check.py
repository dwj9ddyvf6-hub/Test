#!/usr/bin/env python3
"""Memory-store write-boundary validation. Round-5 item 17 (letta-code).
Checks: root index presence, per-file + total core char budgets, frontmatter
validity, read-only list for ruled files. Failing check blocks the write.
Unattended memory workers: fail-closed in narrowest scope (own subtree);
no scoping mechanism means read-only (stated in doctrine, enforced by caller).
"""
import json, os, sys, tempfile
PER_FILE_BUDGET=60000; TOTAL_BUDGET=400000
READ_ONLY={"MEMORY.md"}  # runtime-managed; edits go through memory tools
# A-2 (adoption 2026-11-03): schema-version fence for multi-agent memory
# writes. The store declares its version in schema_version.json at its root;
# a store whose declared version differs from SCHEMA_VERSION fails the check,
# and memory_write refuses any caller presenting a mismatched version.
SCHEMA_VERSION=1
SCHEMA_FILE="schema_version.json"
def check_store(root):
    errors=[]
    idx=os.path.join(root,"MEMORY.md")
    if not os.path.isfile(idx): errors.append("root index MEMORY.md missing")
    sf=os.path.join(root,SCHEMA_FILE)
    if os.path.isfile(sf):
        try:
            declared=json.load(open(sf,encoding="utf-8")).get("schema_version")
            if declared!=SCHEMA_VERSION:
                errors.append(f"schema version mismatch: store declares {declared!r}, fence requires {SCHEMA_VERSION}")
        except Exception as e: errors.append(f"{SCHEMA_FILE}: unreadable {e}")
    total=0
    for dirpath,_,files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"): continue
            p=os.path.join(dirpath,fn); rel=os.path.relpath(p,root)
            try: text=open(p,encoding="utf-8").read()
            except Exception as e: errors.append(f"{rel}: unreadable {e}"); continue
            total+=len(text)
            if len(text)>PER_FILE_BUDGET: errors.append(f"{rel}: {len(text)} chars > per-file budget {PER_FILE_BUDGET}")
            if text.startswith("---"):
                if "\n---" not in text[3:]: errors.append(f"{rel}: frontmatter not closed")
    if total>TOTAL_BUDGET: errors.append(f"total {total} > total budget {TOTAL_BUDGET}")
    return errors,total
def assert_writable(filename):
    if os.path.basename(filename) in READ_ONLY: raise PermissionError(f"{filename} is read-only by rule")
def selftest():
    with tempfile.TemporaryDirectory() as td:
        errs,_=check_store(td); assert errs, "missing index must fail"
        open(os.path.join(td,"MEMORY.md"),"w").write("# index\n")
        open(os.path.join(td,"note.md"),"w").write("---\ntitle: x\n---\nbody\n")
        errs,total=check_store(td); assert not errs,(errs,total)
        open(os.path.join(td,"bad.md"),"w").write("---\ntitle: unclosed\n")
        errs,_=check_store(td); assert any("frontmatter" in e for e in errs)
        os.remove(os.path.join(td,"bad.md"))
        json.dump({"schema_version":SCHEMA_VERSION+99},open(os.path.join(td,SCHEMA_FILE),"w"))
        errs,_=check_store(td); assert any("schema version mismatch" in e for e in errs), errs
        json.dump({"schema_version":SCHEMA_VERSION},open(os.path.join(td,SCHEMA_FILE),"w"))
        errs,_=check_store(td); assert not errs, errs
        try: assert_writable("MEMORY.md"); raise SystemExit("read-only not enforced")
        except PermissionError: pass
        print("SELFTEST PASS memory_store_check: missing index fails, valid store passes, unclosed frontmatter fails, read-only list enforced, schema-version fence rejects mismatched store and accepts matching store")
    return 0
if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="check":
        errs,total=check_store(sys.argv[2]); print(f"errors={errs} total_chars={total}"); raise SystemExit(1 if errs else 0)
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
