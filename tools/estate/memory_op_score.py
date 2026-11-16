#!/usr/bin/env python3
"""Operation-level scorer for memory synthesis changes (A-3, adoption
2026-11-03; HaluMem-style, source MemTensor/HaluMem).

The standard: a synthesis change is graded per operation, never as one blob.
Each operation is {op: add|update|delete, target, before, after, evidence}
where evidence is the source text the change claims to rest on. Scoring is
deterministic and lexical:
  add    FAIL if it carries no evidence; FAIL if less than half its content
         tokens are grounded in its evidence (an ungrounded addition);
         WARN if it drops no links but evidence is thin (grounding < 0.8).
  update FAIL if linked ids present in `before` vanish from `after` with no
         mention in evidence (a link-breaking rewrite); FAIL if ungrounded
         the same way an add is; otherwise PASS.
  delete FAIL if it names no successor / tombstone reference in evidence;
         PASS when the evidence names where the fact went.
Overall verdict is the worst per-operation verdict. An operation with no
evidence is UNMEASURED, never silently PASS (entry 62: unmeasured is never
reported as OK); UNMEASURED counts as FAIL for the overall grade.
CLI: memory_op_score.py ops.json  |  memory_op_score.py selftest
"""
import json, re, sys

TOK = re.compile(r"[a-z0-9]+")
LINKS = re.compile(r"\[\[([^\]]+)\]\]|links?:\s*\[([^\]]*)\]", re.I)

def _tokens(text):
    return set(TOK.findall((text or "").lower()))

def _links(text):
    out = set()
    for m in LINKS.finditer(text or ""):
        for g in m.groups():
            if g:
                out.update(x.strip() for x in g.split(",") if x.strip())
    return out

def _grounding(after, evidence):
    a, e = _tokens(after), _tokens(evidence)
    if not a:
        return 1.0
    return len(a & e) / len(a)

def score_operation(op):
    kind = op.get("op"); before = op.get("before") or ""; after = op.get("after") or ""
    evidence = op.get("evidence") or ""
    if kind not in ("add", "update", "delete"):
        return {"target": op.get("target"), "op": kind, "verdict": "FAIL", "reason": f"unknown op {kind!r}"}
    if not evidence.strip():
        return {"target": op.get("target"), "op": kind, "verdict": "UNMEASURED",
                "reason": "no evidence supplied; an unmeasured operation is not a pass"}
    if kind == "delete":
        if re.search(r"successor|tombstone|moved to|replaced by|retired into", evidence, re.I):
            return {"target": op.get("target"), "op": kind, "verdict": "PASS", "reason": "deletion names its successor/tombstone in evidence"}
        return {"target": op.get("target"), "op": kind, "verdict": "FAIL", "reason": "deletion names no successor or tombstone in evidence"}
    g = _grounding(after, evidence)
    if g < 0.5:
        return {"target": op.get("target"), "op": kind, "verdict": "FAIL", "reason": f"content grounding {g:.2f} < 0.50 against its evidence"}
    if kind == "update":
        lost = _links(before) - _links(after) - _tokens(evidence)
        lost = {x for x in lost if x not in evidence}
        if lost:
            return {"target": op.get("target"), "op": kind, "verdict": "FAIL", "reason": f"update drops linked ids unexplained in evidence: {sorted(lost)}"}
    if g < 0.8:
        return {"target": op.get("target"), "op": kind, "verdict": "WARN", "reason": f"grounding {g:.2f} is thin (0.50-0.80)"}
    return {"target": op.get("target"), "op": kind, "verdict": "PASS", "reason": f"grounding {g:.2f}"}

def score_operations(ops):
    rows = [score_operation(o) for o in ops]
    order = {"PASS": 0, "WARN": 1, "UNMEASURED": 2, "FAIL": 2}
    overall = max((r["verdict"] for r in rows), key=lambda v: order[v], default="PASS")
    if overall == "UNMEASURED":
        overall = "FAIL"
    return {"operations": rows, "overall": overall,
            "counts": {v: sum(1 for r in rows if r["verdict"] == v) for v in ("PASS", "WARN", "FAIL", "UNMEASURED")}}

def selftest():
    ev = "the desk gate runs 1755 tests and the fee walk uses the generic endpoint"
    good = {"op": "add", "target": "fee-walk", "after": "the fee walk uses the generic endpoint", "evidence": ev}
    bad = {"op": "add", "target": "invented", "after": "the broker raised margin to ninety percent yesterday", "evidence": ev}
    noev = {"op": "add", "target": "noev", "after": "anything at all"}
    linkbreak = {"op": "update", "target": "u", "before": "fact links: [fee-walk, cash-halt]", "after": "fact links: [fee-walk] the fee walk uses the generic endpoint", "evidence": ev}
    delok = {"op": "delete", "target": "old", "evidence": "retired into the dated note 2026-11-03; tombstone kept"}
    delbad = {"op": "delete", "target": "old2", "evidence": "cleanup pass"}
    r = score_operations([good, bad, noev, linkbreak, delok, delbad])
    by = {x["target"]: x["verdict"] for x in r["operations"]}
    assert by == {"fee-walk": "PASS", "invented": "FAIL", "noev": "UNMEASURED", "u": "FAIL", "old": "PASS", "old2": "FAIL"}, by
    assert r["overall"] == "FAIL"
    r2 = score_operations([good, delok])
    assert r2["overall"] == "PASS", r2
    print("SELFTEST PASS memory_op_score: grounded add passes, ungrounded add fails, evidenceless op is UNMEASURED, link-breaking update fails, successor-named delete passes, bare delete fails")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) > 1:
        data = json.load(open(sys.argv[1], encoding="utf-8"))
        ops = data["operations"] if isinstance(data, dict) else data
        out = score_operations(ops)
        print(json.dumps(out, indent=1))
        raise SystemExit(0 if out["overall"] in ("PASS", "WARN") else 1)
    print(__doc__)
