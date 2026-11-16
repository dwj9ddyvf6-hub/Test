#!/usr/bin/env python3
"""Analyst pass for skill self-improvement (MASTER-EXTRACTION A-13).
Three-role split (source: Shubhamsaboo/awesome-llm-apps):
  Executor = phase1/phase2 runner (runs the skill's eval set, scores it).
  Analyst  = this module: given the Executor's failures, it MUST name exactly
             one mutation strategy per change from the four-value enum below.
  Mutator  = the edit itself: one surgical change to the skill text, kept if
             the holdout score improves, reverted if not.
A change record without a valid `mutation_strategy` is rejected here, so the
enum becomes change-log vocabulary, not decoration.
"""
import sys
STRATEGIES = ("add_example", "add_constraint", "restructure", "add_edge_case")

def analyst_pass(failures, strategy):
    """Return an analyst record or raise ValueError naming the defect."""
    if strategy not in STRATEGIES:
        raise ValueError(
            f"mutation_strategy must be one of {STRATEGIES}, got {strategy!r}")
    if not failures:
        raise ValueError("analyst pass requires at least one named failure; "
                         "a change with no failure is not an improvement change")
    return {"role": "analyst", "mutation_strategy": strategy,
            "failures_addressed": list(failures),
            "rule": "Mutator applies ONE surgical fix for this strategy; "
                    "keep only if the TEST (holdout) score improves, else revert."}

def validate_change_record(record):
    """A change record dict must carry a valid mutation_strategy."""
    return analyst_pass(record.get("failures", []), record.get("mutation_strategy"))

def selftest():
    r = analyst_pass(["query X did not trigger"], "add_example")
    assert r["mutation_strategy"] == "add_example"
    for bad in (None, "", "rewrite_everything", "ADD_EXAMPLE"):
        try:
            analyst_pass(["f"], bad); raise AssertionError(f"accepted {bad!r}")
        except ValueError:
            pass
    try:
        analyst_pass([], "restructure"); raise AssertionError("accepted empty failures")
    except ValueError:
        pass
    ok = validate_change_record({"failures": ["f"], "mutation_strategy": "add_constraint"})
    assert ok["role"] == "analyst"
    print("SELFTEST PASS analyst: four-value enum enforced (add_example, add_constraint, restructure, add_edge_case); invalid/missing strategy and empty failure list each rejected")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
