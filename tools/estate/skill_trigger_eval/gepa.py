#!/usr/bin/env python3
"""GEPA reflective revision loop for skills with eval sets (MASTER-EXTRACTION A-28).
Source: stanfordnlp/dspy (GEPA, BootstrapFewShot, MIPROv2 proposer checklist).

Rules implemented here, mechanically where cheap:
1. A failed fixture must produce a score PLUS one paragraph of textual
   feedback naming the failure (feedback_for_failure). A bare score is rejected.
2. The revision step edits ONLY the skill text (apply_revision refuses any
   target that is not the skill's SKILL.md text).
3. Few-shot examples are harvested ONLY from outputs that passed the
   playbook's own metric, and the metric name and threshold are recorded
   beside the example (harvest_example). A failed output can never become
   an example.
4. After revision the eval set reruns, or the edit reverts (the runner's
   keep/revert rule from A-13 applies unchanged).
"""
import sys

def feedback_for_failure(case_id, score, feedback):
    if not isinstance(feedback, str) or len(feedback.strip()) < 20 or "\n\n" in feedback.strip():
        raise ValueError("feedback must be exactly one paragraph (>=20 chars) naming the failure")
    return {"case": case_id, "score": score, "feedback": feedback.strip()}

def apply_revision(skill_text, old, new, target="SKILL.md"):
    if target != "SKILL.md":
        raise ValueError(f"GEPA revision edits only the skill text; refused target {target!r}")
    if old not in skill_text:
        raise ValueError("revision anchor not found in skill text; no edit applied")
    return skill_text.replace(old, new, 1)

def harvest_example(output_passed_metric, metric_name, threshold, example):
    if not output_passed_metric:
        raise ValueError("few-shot examples are harvested only from outputs that passed the metric")
    if not metric_name or threshold is None:
        raise ValueError("metric name and threshold must be recorded beside the example")
    return {"example": example, "metric": metric_name, "threshold": threshold,
            "provenance": "passed the playbook's own metric"}

def selftest():
    f = feedback_for_failure("case-1", 0.0, "The description never mentions appointment texts, so the query about drafting one did not trigger the skill.")
    assert f["score"] == 0.0 and "did not trigger" in f["feedback"]
    try:
        feedback_for_failure("c", 0.0, "bad."); raise AssertionError("accepted short feedback")
    except ValueError: pass
    out = apply_revision("alpha beta", "beta", "gamma")
    assert out == "alpha gamma"
    try:
        apply_revision("x", "x", "y", target="runner.py"); raise AssertionError("edited non-skill target")
    except ValueError: pass
    ex = harvest_example(True, "test_accuracy", 0.5, "worked example")
    assert ex["metric"] == "test_accuracy" and ex["threshold"] == 0.5
    try:
        harvest_example(False, "test_accuracy", 0.5, "failed output"); raise AssertionError("harvested a failed output")
    except ValueError: pass
    print("SELFTEST PASS gepa: score+one-paragraph feedback enforced, revision confined to SKILL.md text, few-shot harvest only from metric-passing outputs with metric and threshold recorded")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
