"""Regression blockers for PROOFGATE-APPEND-STREAM-20261105.

The proof gate's full run appends one Engine 19 forward record
per scanned name (15,815 names at the 2026-11-04 issuance). The
append path it used (Ledger.append_forecast_declared ->
append_forecast -> _append) loaded and retained the WHOLE
parsed ledger on every append: rows() built the 242,931-row
parsed cache and the cache stayed resident for the run, so the
full run peaked at 1,847.5 MB resident (measured, run 4 of the
pending-proof-#0 completion, 2026-11-05) and grew with the
ledger. That resident set is the mechanism of the 2026-11-04
-9 kills whenever lanes overlapped the run. The scan half of
the same producer already streams (PROOFGATE-STREAM-20261104,
94.5 MB measured); the append half did not.

The cure: Ledger gains a streaming append form. One pass over
the file verifies the hash chain and collects only the tail
hash and the dedupe keys of the one (engine, issuance) batch
being appended; each append then consults that set and writes
through a streaming _append that never parses the ledger.
record_forward_records routes through it. Behaviour preserved:
same dedupe keys, same append order, same created/duplicates
accounting, same page output for identical inputs.

What is test-proven here (the accounting invariants):
- the streaming path never calls Ledger.rows() (the whole-
  ledger load): with rows() rigged to raise, a full
  record_forward_records run still completes with exact
  counts. On the pre-cure code this fails: the classic path
  calls rows() on the first append.
- dedupe: a republication of the same scan creates nothing
  and counts every name a duplicate; the file does not grow.
- order and bytes: a ledger written through the streaming
  path is byte-identical to the same issues written through
  the classic declared path.
- resume: a batch interrupted halfway and re-run from a
  fresh state creates exactly the remaining names and counts
  the first half as duplicates; no dedupe key repeats.
- the stream state is scoped: it collects only the keys of
  its own (engine, issuance) batch.

What is measurement-proven, not test-proven (stated plainly,
per the cure's BUGLOG): the resident-set bound itself. A unit
test cannot hold a 243k-row ledger's memory behaviour; the
bound is proven by the measured full run under the wrapper
(measure_run.py) recorded in BUGLOG
PROOFGATE-APPEND-STREAM-20261105.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
sys.path.insert(0, FORECAST)

import proof_gate as PG  # noqa: E402
from ledger import Ledger  # noqa: E402

ENGINE = "engine_19"
ISSUED = "2026-11-04"
H_OPEN = "2026-11-04"
H_CLOSE = "2026-11-18"
RULE = {"id": "test-rule",
        "forward_check": {"ledger_engine_id": ENGINE,
                          "horizon_sessions": 10}}
LINEAGE = {"clocks": {c: ISSUED for c in (
    "event_time", "publication_time", "first_available_time",
    "ingestion_time", "decision_as_of")},
    "source_artifacts": [{"path": "/tmp/panel.json",
                          "sha256": "0" * 64}]}


def _result():
    return {"proof_state": "OBSERVING",
            "display_state": "Observing",
            "rule_id": "test-rule", "episodes": 3, "hits": 1,
            "train": {"episodes": 2, "hit_rate": 0.5,
                      "median": 0.01},
            "holdout": {"episodes": 1, "hit_rate": 0.0,
                        "median": -0.02},
            "p_value": 0.5, "bh_q_value": 0.9,
            "bh_significant": False, "downgrade_reason": None}


def _results(symbols):
    return {s: _result() for s in symbols}


def _record(led, results):
    return PG.record_forward_records(
        led, results=results, issued_ts=ISSUED,
        horizon_open=H_OPEN, horizon_close=H_CLOSE,
        lineage=LINEAGE, rule=RULE)


def _forecast_rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                row = json.loads(line)
                if row.get("type") == "forecast":
                    out.append(row)
    return out


SYMBOLS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


def test_republication_creates_nothing_and_counts_duplicates(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    created, duplicates = _record(led, _results(SYMBOLS))
    assert (created, duplicates) == (len(SYMBOLS), 0)
    size = os.path.getsize(path)
    created, duplicates = _record(Ledger(path), _results(SYMBOLS))
    assert (created, duplicates) == (0, len(SYMBOLS))
    assert os.path.getsize(path) == size
    assert Ledger(path).verify_chain_streaming() is True


def test_append_order_is_sorted_subject_order(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    _record(Ledger(path), _results(list(reversed(SYMBOLS))))
    rows = _forecast_rows(path)
    assert [r["subject"] for r in rows] == SYMBOLS


def test_streaming_path_never_loads_whole_ledger(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    original = Ledger.rows

    def banned(self):
        raise AssertionError(
            "the append path loaded the whole ledger via rows()")

    Ledger.rows = banned
    try:
        created, duplicates = _record(led, _results(SYMBOLS))
    finally:
        Ledger.rows = original
    assert (created, duplicates) == (len(SYMBOLS), 0)
    assert Ledger(path).verify_chain_streaming() is True


def test_streaming_bytes_equal_classic_declared_bytes(tmp_path):
    # Streaming half, written by the lane's own entry point.
    path_b = str(tmp_path / "streamed.jsonl")
    _record(Ledger(path_b), _results(SYMBOLS))
    rows_b = _forecast_rows(path_b)
    # Classic half: the identical issues through the declared
    # path, with the value and outcome taken from the streamed
    # rows themselves so the inputs are identical by
    # construction and only the append mechanics differ.
    path_a = str(tmp_path / "classic.jsonl")
    led_a = Ledger(path_a)
    for row in rows_b:
        _r, made = led_a.append_forecast_declared(
            engine_id=row["engine_id"], issued_ts=row["issued_ts"],
            subject=row["subject"], quantity=row["quantity"],
            value=row["value"], horizon_open=row["horizon_open"],
            horizon_close=row["horizon_close"],
            lineage=row["lineage"], families=row["families"],
            outcome=row["outcome"])
        assert made is True
    with open(path_a, "rb") as fh:
        bytes_a = fh.read()
    with open(path_b, "rb") as fh:
        bytes_b = fh.read()
    assert bytes_a == bytes_b


def test_interrupted_batch_resumes_with_exact_accounting(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    first, rest = SYMBOLS[:3], SYMBOLS[3:]
    created, duplicates = _record(Ledger(path), _results(first))
    assert (created, duplicates) == (3, 0)
    # A fresh Ledger and fresh stream state, as after a kill.
    created, duplicates = _record(Ledger(path), _results(SYMBOLS))
    assert (created, duplicates) == (3, 3)
    rows = _forecast_rows(path)
    assert len(rows) == len(SYMBOLS)
    keys = [r["dedupe_key"] for r in rows]
    assert len(set(keys)) == len(keys)


def test_stream_state_scoped_to_engine_and_issuance(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    clocks = dict(LINEAGE)
    for engine_id, issued, h_close in (
            (ENGINE, ISSUED, H_CLOSE), (ENGINE, "2026-11-03", "2026-11-17"),
            ("engine_20", ISSUED, H_CLOSE)):
        led.append_forecast_declared(
            engine_id=engine_id, issued_ts=issued, subject="AAA",
            quantity=PG.FORWARD_QUANTITY,
            value={"proof_state": "OBSERVING"},
            horizon_open=H_OPEN, horizon_close=h_close,
            lineage=clocks, families=["price"],
            outcome={"kind": "provisional_proof_forward_check",
                     "symbol": "AAA", "horizon_sessions": 10})
    rows = _forecast_rows(path)
    assert len(rows) == 3
    state = Ledger(path).append_stream_state(
        engine_id=ENGINE, issued_ts=ISSUED)
    assert state["seen"] == {rows[0]["dedupe_key"]}
    assert state["tail_hash"] == rows[-1]["row_hash"]
