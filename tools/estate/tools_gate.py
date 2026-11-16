#!/usr/bin/env python3
"""Tools completion gate (WIRED round-5 rows b, c, d). This is a live gate:
it runs on demand and from the cron lane round5-memory-reconcile-daily, and
its exit code is the verdict. On every run it:
  1. runs memory_store_check.check_store over the tooling memory store,
  2. runs memory_reconcile via memory_reconcile_run (dated receipt),
  3. evaluates done_check over the run's obligations with the evidence
     records produced by steps 1-2 plus caller-supplied evidence: GREEN
     only on a unique-candidate cover, BLOCKED on any uncovered obligation,
  4. consumes exactly one pending handoff (handoff.py) when --handoff
     id/token/waiter are supplied: the consumer side of the transaction.
  5. validates the rationale store (why_record.py, discipline 11) when one
     exists: a clean store with entries earns the "why store valid"
     evidence record; invalid entries are named in the receipt and earn
     nothing. Never affects the verdict beyond that evidence pattern.
  6. records non-verdict summaries in the receipt: the memory corpus
     audit (memory_edges.py: facts, pending derived-fact reviews, junk
     rate, junk skeletons recorded to the near-miss ledger), a skill
     library sweep (skill_lint + skill_size_gate over custom-skills),
     and a freshness count over the two named registers
     (freshness_lint.py). Summaries observe; they never block.
  7. records the run itself as an evidence capsule
     (evidence_capsules.py, SE1) in state/evidence_capsules.jsonl.
Receipt JSON is written to state/gate_receipts/ and printed. Exit 0 = GREEN,
1 = BLOCKED, 2 = UNVERIFIED/config error.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import done_check, evidence_capsules, freshness_lint, handoff, instincts_inject
import memory_edges, memory_reconcile_run, memory_store_check, skill_lint
import skill_size_gate, why_record
from memory_write import STORE

HERE = os.path.dirname(os.path.abspath(__file__))
RECEIPTS = os.path.join(HERE, "state", "gate_receipts")
STATE = os.path.join(HERE, "state")
CUSTOM_SKILLS = os.path.expanduser("~/workspace/custom-skills")
FRESHNESS_TARGETS = [(os.path.expanduser("~/workspace/midna-book/memory/STATE.md"), "state"),
                     (os.path.expanduser("~/workspace/midna-book/CONTEXT-SNAPSHOT.md"), "snapshot")]

def run_gate(obligations, extra_evidence, handoff_args=None, now=None):
    now = time.time() if now is None else now
    run_id = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    evidence = list(extra_evidence)
    errors, total = memory_store_check.check_store(STORE)
    if not errors:
        evidence.append({"id": f"memcheck-{run_id}", "covers": ["memory store check passes"]})
    rec = memory_reconcile_run.run()
    if not rec["escalate_named"]:
        evidence.append({"id": f"reconcile-{run_id}", "covers": ["memory reconcile clean"]})
    # T-68: the instincts checklist executes in this live lane on every run;
    # the summary is recorded in the receipt. It never affects the verdict.
    instincts_summary = instincts_inject.build_injection(STORE)
    handoff_summary = None
    if handoff_args:
        handoff_summary = handoff.deliver(handoff_args["id"], handoff_args["token"], handoff_args["waiter"])
        evidence.append({"id": f"handoff-{run_id}", "covers": ["handoff consumed"]})
    # Discipline 11: the rationale store is checked in this gate. A clean
    # store with entries earns evidence; invalid entries are named, and a
    # caller who listed "why store valid" as an obligation gets BLOCKED.
    why_summary = None
    if os.path.isfile(why_record.DEFAULT_PATH):
        rep = why_record.validate_store(why_record.DEFAULT_PATH)
        why_summary = {"entries": rep["entries"], "active": rep["active"],
                       "pending_confirmation": rep["pending_confirmation"],
                       "errors": rep["errors"]}
        if rep["entries"] and not rep["errors"]:
            evidence.append({"id": f"why-{run_id}", "covers": ["why store valid"]})
    # Non-verdict summaries (observe only): corpus audit + near-miss sink,
    # skill library sweep, freshness counts over the named registers.
    try:
        corpus_summary = memory_edges.corpus_summary(
            STORE, near_miss_path=os.path.join(STATE, "near_miss_memory.jsonl"))
    except Exception as e:
        corpus_summary = {"error": f"{type(e).__name__}: {e}"}
    try:
        lint_errors, oversized, checked = {}, [], 0
        if os.path.isdir(CUSTOM_SKILLS):
            for name in sorted(os.listdir(CUSTOM_SKILLS)):
                p = os.path.join(CUSTOM_SKILLS, name, "SKILL.md")
                if not os.path.isfile(p):
                    continue
                checked += 1
                errs = skill_lint.lint_text(open(p, encoding="utf-8").read())
                if errs:
                    lint_errors[name] = errs
                if not skill_size_gate.check(p)["ok"]:
                    oversized.append(name)
        skill_sweep = {"checked": checked, "lint_errors": lint_errors, "oversized": oversized}
    except Exception as e:
        skill_sweep = {"error": f"{type(e).__name__}: {e}"}
    try:
        pairs = [(p, k) for p, k in FRESHNESS_TARGETS if os.path.isfile(p)]
        found = freshness_lint.lint(pairs) if pairs else {}
        freshness_summary = {k: len(found.get(k, [])) for k in ("FRESH-1", "FRESH-2", "FRESH-3", "due")}
    except Exception as e:
        freshness_summary = {"error": f"{type(e).__name__}: {e}"}
    gate = done_check.Gate()
    verdict = gate.evaluate(obligations, evidence)
    receipt = {"run_id": run_id, "verdict": verdict["verdict"], "reason": verdict["reason"],
               "obligations": obligations, "evidence_ids": [e["id"] for e in evidence],
               "memory_store_errors": errors, "memory_total_chars": total,
               "reconcile_receipt": rec["receipt_path"], "handoff_summary": handoff_summary,
               "instincts": {k: instincts_summary[k] for k in ("injected", "rejected", "merged", "type_capped", "total_units")},
               "why": why_summary, "memory_corpus": corpus_summary,
               "skill_sweep": skill_sweep, "freshness": freshness_summary}
    os.makedirs(RECEIPTS, exist_ok=True)
    rp = os.path.join(RECEIPTS, f"gate-{run_id}.json")
    try:
        cap = evidence_capsules.record(evidence_capsules.DEFAULT_PATH, actor="tools_gate",
                                       action="gate_run", effect_class="SE1", target=rp,
                                       detail={"run_id": run_id, "verdict": verdict["verdict"]},
                                       ts=now)
        receipt["capsule"] = {"seq": cap["seq"], "hash": cap["hash"][:16]}
    except Exception as e:
        receipt["capsule_error"] = f"{type(e).__name__}: {e}"
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1)
    receipt["receipt_path"] = rp
    return receipt

if __name__ == "__main__":
    # CLI: tools_gate.py '<obligations json>' '<evidence json>' [--handoff id token waiter]
    obs = json.loads(sys.argv[1]) if len(sys.argv) > 1 else ["memory store check passes", "memory reconcile clean"]
    ev = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    hargs = None
    if "--handoff" in sys.argv:
        i = sys.argv.index("--handoff")
        hargs = {"id": sys.argv[i + 1], "token": sys.argv[i + 2], "waiter": sys.argv[i + 3]}
    r = run_gate(obs, ev, hargs)
    print(json.dumps(r, indent=1))
    raise SystemExit(0 if r["verdict"] == "GREEN" else (1 if r["verdict"] == "BLOCKED" else 2))
