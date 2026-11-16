#!/usr/bin/env python3
"""Grounding record (adoption item A-25, source: bytedance/UI-TARS).

For GUI / browser work, grounding is recorded SEPARATELY from task success:
whether the action landed on the intended target is its own field and never
inferred from whether the task completed. A record is valid only when both
fields are present and independent: task_success in {pass, fail, partial},
grounding in {hit, miss, not_applicable} with a named intended target when
grounding is hit or miss.
"""
import json, sys

def validate(rec):
    errors = []
    if "task_success" not in rec:
        errors.append("missing task_success")
    elif rec["task_success"] not in ("pass", "fail", "partial"):
        errors.append(f"bad task_success {rec['task_success']!r}")
    if "grounding" not in rec:
        errors.append("missing grounding (must be recorded separately from task_success)")
    elif rec["grounding"] not in ("hit", "miss", "not_applicable"):
        errors.append(f"bad grounding {rec['grounding']!r}")
    if rec.get("grounding") in ("hit", "miss") and not rec.get("intended_target"):
        errors.append("grounding hit/miss requires intended_target")
    if "action" not in rec:
        errors.append("missing action")
    return errors

def make_record(action, intended_target, grounding, task_success):
    rec = {"action": action, "intended_target": intended_target,
           "grounding": grounding, "task_success": task_success}
    errs = validate(rec)
    if errs:
        raise ValueError("; ".join(errs))
    return rec

if __name__ == "__main__":
    # Self-check: a successful task with a grounding miss is a valid,
    # distinct record; a record missing grounding is rejected.
    ok = make_record("click submit", "Submit button", "miss", "pass")
    assert ok["grounding"] == "miss" and ok["task_success"] == "pass"
    bad = validate({"action": "click", "task_success": "pass"})
    assert bad, "record without grounding must fail validation"
    print("grounding_record self-check OK:", json.dumps(ok))
