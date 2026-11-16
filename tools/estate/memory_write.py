#!/usr/bin/env python3
"""The memory write path for our own tooling (WIRED round-5 row b, discipline 5).

Every write our tooling makes into its memory store
(~/workspace/tools/memory_store/) goes through write_note(), which:
  1. enforces the read-only list (memory_store_check.assert_writable),
  2. stages the write in a temp copy of the store,
  3. runs memory_store_check.check_store on the staged store,
  4. commits only if the check passes; otherwise raises and writes nothing.
Fail-closed: a store that fails the check after staging blocks the write.
Each attempt (commit or block) is logged to state/memory_write_log.jsonl.
The platform's own MEMORY.md is runtime-managed and on the read-only list;
this path governs the store our tooling itself owns and writes.
"""
import json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory_store_check

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "memory_store")
LOG = os.path.join(HERE, "state", "memory_write_log.jsonl")

def _log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def write_note(rel_name, text, now=None, schema_version=None):
    """Write one note. A-2 fence: a caller presenting a schema_version other
    than memory_store_check.SCHEMA_VERSION is refused before staging; a store
    declaring a mismatched version is refused by check_store on the staged
    copy. Omitting schema_version means the caller writes at the current
    version."""
    now = time.time() if now is None else now
    rec = {"ts": now, "target": rel_name}
    if schema_version is not None and schema_version != memory_store_check.SCHEMA_VERSION:
        rec.update(result="blocked", reason=f"schema version mismatch: caller presented {schema_version!r}, fence requires {memory_store_check.SCHEMA_VERSION}")
        _log(rec)
        raise ValueError(rec["reason"])
    try:
        memory_store_check.assert_writable(rel_name)
    except PermissionError as e:
        rec.update(result="blocked", reason=str(e)); _log(rec); raise
    os.makedirs(STORE, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        staged = os.path.join(td, "store")
        if os.path.isdir(STORE):
            shutil.copytree(STORE, staged)
        else:
            os.makedirs(staged)
        dest = os.path.join(staged, rel_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        errors, total = memory_store_check.check_store(staged)
        if errors:
            rec.update(result="blocked", reason=f"memory_store_check: {errors}")
            _log(rec)
            raise ValueError(f"write blocked by memory_store_check: {errors}")
        real_dest = os.path.join(STORE, rel_name)
        os.makedirs(os.path.dirname(real_dest), exist_ok=True)
        with open(real_dest, "w", encoding="utf-8") as f:
            f.write(text)
    rec.update(result="committed", total_chars=total)
    _log(rec)
    return rec

if __name__ == "__main__":
    print(__doc__)
