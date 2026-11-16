#!/usr/bin/env python3
"""Gate/scheduled runner for memory_reconcile (WIRED round-5 row b).
Builds the derived index (relpath -> sha256 prefix) from the reconcile state
file, runs memory_reconcile.reconcile over the tooling memory store, heals
the index for candidates that are not escalated, persists state, and writes
a dated proof artifact (JSON receipt) to the receipts dir given on the CLI
(default: ~/workspace/tools/state/reconcile_receipts/). Invoked live by
tools_gate.py on every gate run and by the cron lane
round5-memory-reconcile-daily. Exit 1 only if an item is ESCALATE-named.
"""
import hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory_reconcile
from memory_write import STORE

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "state", "memory_reconcile_state.json")
INDEX_FILE = os.path.join(HERE, "state", "memory_index.json")
DEFAULT_RECEIPTS = os.path.join(HERE, "state", "reconcile_receipts")

def _h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def run(receipts_dir=None, now=None):
    now = time.time() if now is None else now
    receipts_dir = receipts_dir or DEFAULT_RECEIPTS
    os.makedirs(receipts_dir, exist_ok=True)
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    index = json.load(open(INDEX_FILE)) if os.path.isfile(INDEX_FILE) else {}
    state = json.load(open(STATE_FILE)) if os.path.isfile(STATE_FILE) else {}
    result = memory_reconcile.reconcile(STORE, index, state)
    escalated = set(result["escalate_named"])
    healed = []
    for rel in result["heal_candidates"]:
        if rel in escalated or rel.endswith(":orphan"):
            continue
        p = os.path.join(STORE, rel)
        if os.path.isfile(p):
            index[rel] = _h(p); healed.append(rel)
            result["state"].pop(rel, None)
    for rel in list(index):
        if rel + ":orphan" in result["heal_candidates"]:
            index.pop(rel, None); healed.append(rel + ":orphan")
    json.dump(index, open(INDEX_FILE, "w"), indent=1, sort_keys=True)
    json.dump(result["state"], open(STATE_FILE, "w"), indent=1, sort_keys=True)
    stamp = time.strftime("%Y-%m-%dT%H%M%S", time.localtime(now))
    receipt = {"run_at": stamp, "store": STORE, "heal_candidates": result["heal_candidates"],
               "healed": healed, "escalate_named": result["escalate_named"]}
    rp = os.path.join(receipts_dir, f"reconcile-{stamp}.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1)
    receipt["receipt_path"] = rp
    return receipt

if __name__ == "__main__":
    r = run(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(r))
    raise SystemExit(1 if r["escalate_named"] else 0)
