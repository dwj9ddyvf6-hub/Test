#!/usr/bin/env python3
"""Evidence capsules for consequential actions. Discipline 7, built
2026-11-03 (shape adopted from the ECC evidence layer; patterns adopted,
tool not installed).

Every recorded action declares an effect class:
  SE0 read-only evaluation
  SE1 reversible local writes
  SE2 process or filesystem mutation
  SE3 append-only remote publication: NEVER replayed
  SE4 economic or secret-handling effects: NEVER replayed, and refused
      in record mode unless a trusted caller explicitly allows it
Capsules are append-only and hash-chained: each capsule carries the
sha256 of its predecessor, so verification fails at the exact tampered
entry with a stable code (HASH_MISMATCH, CHAIN_BREAK, SEQ_GAP,
BAD_CLASS). Replay fails closed: replay_plan returns only SE0-SE2
capsules and names the refused ones; receipts are verifiable offline by
a party that does not trust the producer. A capsule is a record, not
containment: it proves what was declared, never that the action was
safe.

First live consumer: tools_gate records every gate run as an SE1
capsule (actor tools_gate, action gate_run) in
~/workspace/tools/state/evidence_capsules.jsonl.

CLI: evidence_capsules.py verify [path] | selftest
"""
import hashlib, json, os, sys, tempfile

CLASSES = ("SE0", "SE1", "SE2", "SE3", "SE4")
REPLAYABLE = ("SE0", "SE1", "SE2")
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "state", "evidence_capsules.jsonl")

def _hash(capsule_without_hash):
    canon = json.dumps(capsule_without_hash, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()

def _read(path):
    rows = []
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows

def record(path, actor, action, effect_class, target, detail=None, ts=None,
           allow_se4=False):
    if effect_class not in CLASSES:
        raise ValueError(f"effect_class must be one of {CLASSES}, got {effect_class!r}")
    if effect_class == "SE4" and not allow_se4:
        raise ValueError("SE4 (economic or secret-handling) is forbidden in record "
                         "mode unless a trusted caller allows it")
    rows = _read(path)
    prev = rows[-1]["hash"] if rows else "GENESIS"
    cap = {"seq": len(rows) + 1, "ts": ts, "actor": actor, "action": action,
           "effect_class": effect_class, "target": target,
           "detail": detail or {}, "prev": prev}
    cap["hash"] = _hash(cap)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cap) + "\n")
    return cap

def verify(path):
    rows = _read(path)
    prev = "GENESIS"
    for i, cap in enumerate(rows, 1):
        if cap.get("effect_class") not in CLASSES:
            return {"ok": False, "entries": len(rows),
                    "error": {"seq": i, "code": "BAD_CLASS"}}
        if cap.get("seq") != i:
            return {"ok": False, "entries": len(rows),
                    "error": {"seq": i, "code": "SEQ_GAP"}}
        if cap.get("prev") != prev:
            return {"ok": False, "entries": len(rows),
                    "error": {"seq": i, "code": "CHAIN_BREAK"}}
        body = {k: v for k, v in cap.items() if k != "hash"}
        if _hash(body) != cap.get("hash"):
            return {"ok": False, "entries": len(rows),
                    "error": {"seq": i, "code": "HASH_MISMATCH"}}
        prev = cap["hash"]
    return {"ok": True, "entries": len(rows), "error": None}

def replay_plan(path):
    v = verify(path)
    if not v["ok"]:
        raise ValueError(f"replay fails closed: chain does not verify ({v['error']})")
    rows = _read(path)
    return {"replayable": [c for c in rows if c["effect_class"] in REPLAYABLE],
            "refused": [{"seq": c["seq"], "effect_class": c["effect_class"],
                         "reason": "SE3 and above are refused in replay"}
                        for c in rows if c["effect_class"] not in REPLAYABLE]}

def selftest():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "capsules.jsonl")
        record(p, "tester", "read a file", "SE0", "x.md", ts=1)
        record(p, "tester", "write a receipt", "SE1", "receipt.json", ts=2)
        record(p, "tester", "publish a page", "SE3", "public page", ts=3)
        v = verify(p)
        assert v == {"ok": True, "entries": 3, "error": None}, v
        plan = replay_plan(p)
        assert [c["seq"] for c in plan["replayable"]] == [1, 2], plan
        assert [r["seq"] for r in plan["refused"]] == [3], plan
        try:
            record(p, "tester", "move money", "SE4", "account")
            raise SystemExit("SE4 must be refused in record mode")
        except ValueError:
            pass
        record(p, "trusted", "move money", "SE4", "account", ts=4, allow_se4=True)
        rows = _read(p)
        rows[1]["detail"] = {"tampered": True}
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        v2 = verify(p)
        assert v2["ok"] is False and v2["error"] == {"seq": 2, "code": "HASH_MISMATCH"}, v2
        try:
            replay_plan(p); raise SystemExit("replay must fail closed on a broken chain")
        except ValueError:
            pass
        print("SELFTEST PASS evidence_capsules: hash chain verifies, tamper fails at the exact entry (seq 2, HASH_MISMATCH), SE3 refused in replay, SE4 refused in record mode without a trusted caller, replay fails closed on a broken chain")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print(json.dumps(verify(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH), indent=1))
    else:
        print(__doc__)
