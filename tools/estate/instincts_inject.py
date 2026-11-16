#!/usr/bin/env python3
"""Instincts injection mechanism (T-68, adoption 2026-11-03).

Until now instincts_checklist.md was reference-only: no live mechanism read
it. This module is that mechanism. It executes the checklist mechanically
over instinct notes stored in the ONE memory of record (the tooling memory
store, files under instincts/ with frontmatter type: instinct) and builds
the session-start injection block:

  admission   confidence >= 0.7 and success_rate >= MIN_SUCCESS_RATE;
              contradicted units are excluded (frozen, never strengthened);
              retrieval alone never changes any unit (this module writes
              nothing to the store).
  dedupe      near-duplicates (trigger token Jaccard >= 0.80) merge to the
              highest-confidence unit; merged names are reported.
  caps        per-type cap MAX_PER_TYPE; injection cap 6 units; each summary
              at most 220 chars; total block built through context_inject at
              8,000 chars with omissions named inside the block (A-10).
  ranking     score = confidence + 0.25 if project-scoped + 0.20 if the
              unit's domain matches the caller's stack tag. Boosts are fixed
              constants here, never configurable, and never lower the floor.

An instinct is a prior, not proof. Wired into tools_gate.py: every gate run
executes build_injection over the live store and records the summary in its
receipt, so the checklist runs in a live memory lane, not only on paper.
The platform's own session-start injection is runtime-managed and untouched;
this is the mechanism for the local memory lane's session/task start.
"""
import os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import context_inject

MIN_CONFIDENCE = 0.7
MIN_SUCCESS_RATE = 0.6   # the store's floor (checklist: at/above the store's MIN_SUCCESS_RATE)
MAX_PER_TYPE = 3
MAX_INJECT = 6
SUMMARY_CHARS = 220
BUDGET_CHARS = 8000
PROJECT_BOOST = 0.25
STACK_BOOST = 0.20
NEAR_DUP_JACCARD = 0.80

TOK = re.compile(r"[a-z0-9]+")

def _fm(text):
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip().lower()] = v.strip()
    return fm

def load_instincts(store):
    out = []
    root = os.path.join(store, "instincts")
    if not os.path.isdir(root):
        return out
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".md"):
            continue
        text = open(os.path.join(root, fn), encoding="utf-8").read()
        fm = _fm(text)
        if fm.get("type") != "instinct":
            continue
        body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text
        out.append({"name": fn[:-3], "confidence": float(fm.get("confidence", 0)),
                    "success_rate": float(fm.get("success_rate", 0)),
                    "type_tag": fm.get("domain", "general"), "scope": fm.get("scope", "project"),
                    "contradicted": fm.get("contradicted", "false").lower() == "true",
                    "trigger": body.strip().splitlines()[0] if body.strip() else fn,
                    "summary": fm.get("summary", body.strip().replace("\n", " "))})
    return out

def build_injection(store, stack=None):
    units = load_instincts(store)
    rejected, admitted = [], []
    for u in units:
        if u["contradicted"]:
            rejected.append((u["name"], "contradicted: frozen, excluded"))
        elif u["confidence"] < MIN_CONFIDENCE:
            rejected.append((u["name"], f"confidence {u['confidence']} < {MIN_CONFIDENCE}"))
        elif u["success_rate"] < MIN_SUCCESS_RATE:
            rejected.append((u["name"], f"success_rate {u['success_rate']} < {MIN_SUCCESS_RATE}"))
        else:
            admitted.append(u)
    # near-duplicate merge on trigger tokens, highest confidence wins
    merged = []
    kept = []
    for u in sorted(admitted, key=lambda x: -x["confidence"]):
        toks = set(TOK.findall(u["trigger"].lower()))
        dup = None
        for k in kept:
            kt = set(TOK.findall(k["trigger"].lower()))
            if toks and kt and len(toks & kt) / len(toks | kt) >= NEAR_DUP_JACCARD:
                dup = k; break
        if dup:
            merged.append(u["name"])
        else:
            kept.append(u)
    # per-type cap, then ranking with the fixed boosts
    by_type, capped = {}, []
    for u in kept:
        by_type.setdefault(u["type_tag"], []).append(u)
    pool = []
    for tag, group in by_type.items():
        group.sort(key=lambda x: -x["confidence"])
        pool.extend(group[:MAX_PER_TYPE])
        capped.extend(x["name"] for x in group[MAX_PER_TYPE:])
    for u in pool:
        u["rank"] = u["confidence"] + (PROJECT_BOOST if u["scope"] == "project" else 0) \
            + (STACK_BOOST if stack and u["type_tag"] == stack else 0)
    pool.sort(key=lambda x: -x["rank"])
    chosen = pool[:MAX_INJECT]
    items = [(u["name"], u["summary"][:SUMMARY_CHARS]) for u in chosen]
    block = context_inject.build_injection(items, BUDGET_CHARS)
    return {"text": block["text"], "injected": [u["name"] for u in chosen],
            "rejected": rejected, "merged": merged, "type_capped": capped,
            "rank_capped": [u["name"] for u in pool[MAX_INJECT:]],
            "omitted_named_in_block": block["omitted"], "total_units": len(units)}

def selftest():
    with tempfile.TemporaryDirectory() as td:
        root = os.path.join(td, "instincts"); os.makedirs(root)
        def w(name, fm, body):
            lines = "\n".join(f"{k}: {v}" for k, v in fm.items())
            open(os.path.join(root, name), "w").write(f"---\ntype: instinct\n{lines}\n---\n{body}\n")
        base = {"confidence": 0.85, "success_rate": 0.9, "domain": "memory", "scope": "project", "summary": "do the thing carefully"}
        w("strong.md", base, "when writing memory always run the store check first")
        w("strongdup.md", {**base, "confidence": 0.75}, "when writing memory always run the store check first please")
        w("weak.md", {**base, "confidence": 0.5}, "some weak trigger")
        w("frozen.md", {**base, "contradicted": "true"}, "a contradicted trigger")
        w("lowrate.md", {**base, "success_rate": 0.2}, "another trigger entirely")
        r = build_injection(td, stack="memory")
        assert r["injected"] == ["strong"], r
        assert any(n == "weak" for n, _ in r["rejected"]) and any(n == "frozen" for n, _ in r["rejected"]) and any(n == "lowrate" for n, _ in r["rejected"]), r["rejected"]
        assert r["merged"] == ["strongdup"], r
        assert "INJECTION OMISSIONS" in r["text"]
        r2 = build_injection(os.path.join(td, "nonexistent-store"))
        assert r2["injected"] == [] and r2["total_units"] == 0, r2
        print("SELFTEST PASS instincts_inject: admission floor, success-rate gate, contradicted freeze, near-duplicate merge, empty store honest; checklist executed mechanically")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    import json
    store = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_store")
    print(json.dumps(build_injection(store, sys.argv[2] if len(sys.argv) > 2 else None), indent=1))
