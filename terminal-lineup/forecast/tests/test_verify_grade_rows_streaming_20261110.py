"""Blocker for VERIFY-STREAM-RECOUNT-20261110.

verify_grade_rows.recount used to materialize every parsed ledger
row (rows.append(row) plus a full by-id dict of row bodies), a ~3 GB
parsed peak at ~349k rows that was OOM-killed inside the 2026-11-10
refresh_tools verify step. The cure streams the ledger in two
passes. These tests pin: (1) the materializing constructs are gone
and the two-pass streaming ones are present (source assertions, so
the test fails on the pre-cure file); (2) the recount's figures on a
synthetic chain-valid ledger (forecasts, a voiding correction, a
valid grade, an orphan, a double grade, a grade on a voided
forecast, mean scores) match hand-computed values exactly.
"""
import hashlib
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(HERE, "..", "verify_grade_rows.py")


def _load():
    spec = importlib.util.spec_from_file_location(
        "verify_grade_rows", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_recount_streams_instead_of_materializing():
    src = open(MODULE_PATH, encoding="utf-8").read()
    assert "rows.append(row)" not in src
    assert 'by_id = {r["row_id"]: r for r in rows}' not in src
    assert "VERIFY-STREAM-RECOUNT-20261110" in src
    # two open() passes over the ledger inside recount
    body = src[src.index("def recount"):src.index("def _attestation")]
    assert body.count('open(ledger_path, "r", encoding="utf-8")') == 2


def test_recount_figures_on_synthetic_ledger():
    mod = _load()

    def make_row(prev, body):
        stripped = {k: v for k, v in body.items()
                    if k not in ("row_hash", "prev_hash", "row_id")}
        h = hashlib.sha256(
            (prev + mod.canonical(stripped)).encode()).hexdigest()
        return h, {**body, "prev_hash": prev, "row_hash": h}

    bodies = [
        {"row_id": "f1", "type": "forecast", "engine_id": "e1",
         "outcome": {"kind": "x"}},
        {"row_id": "f2", "type": "forecast", "engine_id": "e1",
         "outcome": {"kind": "x"}},
        {"row_id": "c1", "type": "correction",
         "corrects_row_id": "f1"},
        {"row_id": "g1", "type": "grade", "engine_id": "e1",
         "forecast_row_id": "f2", "grade": {"scores": {"s": 1.0}}},
        {"row_id": "g2", "type": "grade", "engine_id": "e1",
         "forecast_row_id": "nope", "grade": {"scores": {}}},
        {"row_id": "g3", "type": "grade", "engine_id": "e1",
         "forecast_row_id": "f2", "grade": {"scores": {"s": 3.0}}},
        {"row_id": "g4", "type": "grade", "engine_id": "e1",
         "forecast_row_id": "f1", "grade": {"scores": {}}},
    ]
    rows, prev = [], ""
    for b in bodies:
        h, r = make_row(prev, b)
        rows.append(r)
        prev = h
    with tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False) as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        path = fh.name
    try:
        res = mod.recount(path)
    finally:
        os.unlink(path)
    assert res["rows"] == 7
    assert res["first_break"] is None
    assert res["head"] == prev
    e = res["per_engine"]["e1"]
    assert (e["forecasts_raw"], e["forecasts_voided"],
            e["forecasts_valid"]) == (2, 1, 1)
    assert (e["grades_raw"], e["grades_on_voided"],
            e["grades_valid"], e["orphan_grades"],
            e["double_grades"]) == (4, 1, 2, 1, 1)
    assert e["mean_scores_valid"] == {"s": 2.0}


if __name__ == "__main__":
    test_recount_streams_instead_of_materializing()
    test_recount_figures_on_synthetic_ledger()
    print("test_verify_grade_rows_streaming_20261110: all passed")
