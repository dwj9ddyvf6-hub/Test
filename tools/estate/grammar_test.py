#!/usr/bin/env python3
"""Offline grammar testing with a mock model (A-30).

For the machine-consumed outputs that recur (workflow result envelopes,
snapshot JSON, ledger rows), the checked-in schema in
grammar_schemas.json carries positive and negative example strings, and
this runner checks them offline with no model call: every positive
example must validate, every negative example must fail. A malformed
output shape is therefore a deterministic test failure, not a runtime
surprise downstream.

Schema shape per entry: {required: {field: type-name}, optional: {...}}.
Type names: str, number, bool, list, dict, any.

Usage: grammar_test.py selftest | check [schemas.json]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMAS = os.path.join(HERE, "grammar_schemas.json")

_TYPES = {"str": str, "bool": bool, "list": list, "dict": dict, "any": object}

def _type_ok(value, tname):
    if tname == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[tname])

def validate(instance, schema):
    if not isinstance(instance, dict):
        return ["top level must be an object"]
    errs = []
    for field, tname in schema.get("required", {}).items():
        if field not in instance:
            errs.append(f"missing required field: {field}")
        elif not _type_ok(instance[field], tname):
            errs.append(f"field {field}: expected {tname}")
    for field, tname in schema.get("optional", {}).items():
        if field in instance and not _type_ok(instance[field], tname):
            errs.append(f"field {field}: expected {tname}")
    return errs

def run_schemas(doc):
    failures = []
    for name, spec in doc["schemas"].items():
        for i, ex in enumerate(spec["positive_examples"]):
            try:
                inst = json.loads(ex)
            except json.JSONDecodeError as e:
                failures.append(f"{name} positive[{i}]: unparseable example: {e}")
                continue
            errs = validate(inst, spec["schema"])
            if errs:
                failures.append(f"{name} positive[{i}] must pass but failed: {errs}")
        for i, ex in enumerate(spec["negative_examples"]):
            try:
                inst = json.loads(ex)
            except json.JSONDecodeError:
                continue  # unparseable is a correct failure for JSON grammars
            errs = validate(inst, spec["schema"])
            if not errs:
                failures.append(f"{name} negative[{i}] must fail but passed")
    return failures

def selftest():
    doc = json.load(open(DEFAULT_SCHEMAS))
    failures = run_schemas(doc)
    assert not failures, failures
    names = sorted(doc["schemas"])
    assert names == ["ledger_row", "snapshot_json", "workflow_envelope"], names
    bad = {"schemas": {"x": {"schema": {"required": {"a": "str"}},
                             "positive_examples": ['{"a": 1}'], "negative_examples": []}}}
    assert run_schemas(bad), "a wrong-polarity example must be caught"
    print(f"SELFTEST PASS grammar_test: {names} schemas, all positive examples pass and all negative examples fail, offline with no model call")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "check":
        path = args[1] if len(args) > 1 else DEFAULT_SCHEMAS
        failures = run_schemas(json.load(open(path)))
        for f in failures:
            print(f"FAIL: {f}")
        print("OK" if not failures else f"{len(failures)} failure(s)")
        raise SystemExit(1 if failures else 0)
    print(__doc__)
    raise SystemExit(2)
