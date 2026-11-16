#!/usr/bin/env python3
"""Deterministic content-hash IDs and JSONL dedup. Round-4 discipline 14.
ID = truncated SHA-256 (32 hex chars) of canonical JSON of the parts list,
mirroring src/core/ids.ts in deepseek-ai/dsh-superagent-prototype @6337fc8.
"""
import hashlib, json, sys, tempfile, os

def deterministic_id(parts) -> str:
    canon = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:32]

def record_id(record: dict) -> str:
    if "id" in record and isinstance(record["id"], str) and record["id"]:
        return record["id"]
    return deterministic_id(record)

def check_stream(path: str):
    """Return (total, unique, duplicates list of (line_no, id))."""
    seen, dups, total = {}, [], 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            rec = json.loads(line)
            rid = record_id(rec)
            if rid in seen:
                dups.append((i, rid, seen[rid]))
            else:
                seen[rid] = i
    return total, len(seen), dups

def comment_event_id(source_id, updated_at) -> str:
    """A-19 edited-comment rule: the deterministic event ID for a
    comment-driven lane includes the source's updated_at, so an edit
    (a new updated_at) is a new event by design, and a redelivery of
    the same version (same updated_at) is the same event, deduped."""
    return deterministic_id(["comment", source_id, updated_at])

def eval_score_id(run, assertion, occurrence) -> str:
    """Round-5 item 35: eval results keyed by deterministic ID of (run, assertion, occurrence), UUIDv5 shape."""
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_URL, deterministic_id([run, assertion, occurrence])))

def selftest() -> int:
    assert deterministic_id(["a", 1]) == deterministic_id(["a", 1]), "not deterministic"
    assert deterministic_id(["a", 1]) != deterministic_id(["a", 2]), "collision on differing input"
    rows = [
        {"kind": "delivery", "key": "gallery:item-1", "body": "hello"},
        {"kind": "delivery", "key": "gallery:item-2", "body": "world"},
        {"kind": "delivery", "key": "gallery:item-1", "body": "hello"},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tf:
        for r in rows:
            tf.write(json.dumps(r) + "\n")
        path = tf.name
    try:
        total, uniq, dups = check_stream(path)
        assert total == 3 and uniq == 2 and len(dups) == 1, f"unexpected: {total} {uniq} {dups}"
        assert dups[0][0] == 3, "duplicate line number wrong"
        print(f"SELFTEST PASS dedup_ids: total=3 unique=2 duplicates=1 dup_line=3 dup_id={dups[0][1]}")
        assert comment_event_id("c-1", "2026-11-03T10:00:00Z") == comment_event_id("c-1", "2026-11-03T10:00:00Z"), "redelivery must dedupe"
        assert comment_event_id("c-1", "2026-11-03T10:00:00Z") != comment_event_id("c-1", "2026-11-03T11:00:00Z"), "an edit must be a new event"
        print("SELFTEST PASS comment_event_id A-19: same updated_at dedupes, edited updated_at is a new event")
        assert eval_score_id("r1","a1",0) == eval_score_id("r1","a1",0) and eval_score_id("r1","a1",0) != eval_score_id("r1","a1",1)
        print("SELFTEST PASS eval_score_id: stable per (run,assertion,occurrence), distinct per occurrence")
        print(f"SELFTEST PASS deterministic_id stable: {deterministic_id(['a', 1])}")
        return 0
    finally:
        os.unlink(path)

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    elif len(sys.argv) >= 3 and sys.argv[1] == "id":
        print(deterministic_id(sys.argv[2:]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "check":
        total, uniq, dups = check_stream(sys.argv[2])
        print(f"total={total} unique={uniq} duplicates={len(dups)}")
        for ln, rid, first in dups:
            print(f"DUPLICATE line={ln} id={rid} first_seen_line={first}")
        raise SystemExit(1 if dups else 0)
    else:
        print(__doc__); print("usage: dedup_ids.py selftest | id <part...> | check <file.jsonl>")
        raise SystemExit(2)
