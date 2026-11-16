#!/usr/bin/env python3
"""Judge calibration set, built the labelling-pipeline way (A-24).

If a model judge is ever added beside the formula gate, its calibration
comes from a small human-labelled local set passed through a consistency
filter, never from the rubric prompt alone. This module is that pipeline:
  load_set(path) -> entries {id, input, human_label, provenance, rationale}
  consistency_filter(entries) -> (kept, dropped with reasons): duplicate
    inputs with disagreeing labels, labels outside the allowed set,
    missing provenance, and missing rationale are dropped, never repaired.
  agreement(entries, judge_fn) -> agreement rate of a candidate judge
    against the kept human labels.
The shipped judge_calibration_set.json is a SEED set: every entry's
provenance says seed-example and it must be replaced with genuinely
human-labelled entries before any judge is calibrated on it.

Usage: judge_calibration.py selftest | check [set.json] | filter [set.json]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SET = os.path.join(HERE, "judge_calibration_set.json")
ALLOWED_LABELS = {"fire", "silent", "slow"}

def consistency_filter(entries):
    kept, dropped, by_input = [], [], {}
    for e in entries:
        reasons = []
        if e.get("human_label") not in ALLOWED_LABELS:
            reasons.append(f"label {e.get('human_label')!r} not in allowed set")
        if not e.get("provenance"):
            reasons.append("missing provenance")
        if not e.get("rationale"):
            reasons.append("missing rationale")
        key = (e.get("input") or "").strip().lower()
        if key in by_input and by_input[key] != e.get("human_label"):
            reasons.append("duplicate input with disagreeing human label")
        by_input.setdefault(key, e.get("human_label"))
        (dropped if reasons else kept).append({**e, "drop_reasons": reasons} if reasons else e)
    return kept, dropped

def agreement(entries, judge_fn):
    kept, _d = consistency_filter(entries)
    if not kept:
        return {"n": 0, "agreement": None}
    agree = sum(1 for e in kept if judge_fn(e["input"]) == e["human_label"])
    return {"n": len(kept), "agreement": agree / len(kept)}

def selftest():
    entries = [
        {"id": "1", "input": "visit tomorrow at 9", "human_label": "fire",
         "provenance": "human:owner 2026-11-03", "rationale": "deadline near"},
        {"id": "2", "input": "routine digest", "human_label": "silent",
         "provenance": "human:owner 2026-11-03", "rationale": "no need"},
        {"id": "3", "input": "visit tomorrow at 9", "human_label": "silent",
         "provenance": "human:owner 2026-11-03", "rationale": "conflicting duplicate"},
        {"id": "4", "input": "mystery", "human_label": "maybe",
         "provenance": "human:owner 2026-11-03", "rationale": "bad label"},
        {"id": "5", "input": "no provenance row", "human_label": "fire",
         "provenance": "", "rationale": "x"},
    ]
    kept, dropped = consistency_filter(entries)
    assert len(kept) == 2 and len(dropped) == 3, (kept, dropped)
    a = agreement(entries, lambda s: "fire" if "visit" in s else "silent")
    assert a["n"] == 2 and a["agreement"] == 1.0, a
    seed = json.load(open(DEFAULT_SET))
    sk, sd = consistency_filter(seed["entries"])
    assert sk and not sd, f"seed set must pass its own filter: dropped={sd}"
    assert all("seed" in e["provenance"] for e in sk), "seed provenance must be honest"
    print(f"SELFTEST PASS judge_calibration: filter kept 2 dropped 3 with reasons, agreement computed on kept only, seed set ({len(sk)} entries) passes filter with seed provenance named")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] in ("check", "filter"):
        path = args[1] if len(args) > 1 else DEFAULT_SET
        data = json.load(open(path))
        kept, dropped = consistency_filter(data["entries"])
        print(json.dumps({"kept": len(kept), "dropped": dropped}, indent=1))
        raise SystemExit(1 if dropped else 0)
    print(__doc__)
    raise SystemExit(2)
