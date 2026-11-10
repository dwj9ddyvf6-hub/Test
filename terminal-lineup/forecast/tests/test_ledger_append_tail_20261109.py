"""Regression blocker for the append-tail cure (2026-11-09),
LEDGER-APPEND-TAIL-20261109.

Failure of record: after the streaming-figures cure
(LEDGER-STREAM-FIGURES-20261109) converted the four killed
refreshers' verify and figures reads to streams, a standalone
intake-bias proof run still climbed to 2.3 GB RSS. The
remaining parses were inside ledger.py's own classic append
path: Ledger._append called self.rows() (a full parse of the
661 MB ledger) on every append to verify the chain and take
the tail hash, and append_forecast_declared plus
append_forecast each ran a full rows() dedupe scan per
append. The stat-keyed cache masked this only until any
append invalidated it; the next append re-parsed everything.
append_grade's classic refusal checks and
append_correction's id set did the same.

Cure pinned here:
- _tail_hash reads only the file's tail blocks and parses
  the last line alone.
- _append verifies through verify_chain_streaming() and
  links through _tail_hash(); its parsed-rows cache is
  dropped on append (as _append_streaming already did)
  instead of extended with a parse the cure exists to avoid.
- The dedupe scans in append_forecast and
  append_forecast_declared, the refusal checks in
  append_grade, the id set in append_correction, and the
  emptiness check in append_genesis all stream or stat
  instead of parsing: no method on the append path calls
  self.rows() (verify_chain's explicit-rows default is the
  one remaining caller, and it is a read API, not the
  append path).

Equivalence pinned here: a ledger built entirely through
the cured classic path carries the same bytes as the same
rows appended in the same order would produce under the
chain rule (each row's prev_hash is the previous row's
row_hash, genesis first with an empty prev), verifies
under both verify forms, and grades and corrections behave
exactly as before (double grade refused, voided grade
refused, unknown correction target refused).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
sys.path.insert(0, FORECAST)

import ledger as ledger_mod  # noqa: E402

LINEAGE = {"source_artifacts": [],
           "clocks": {"event_time": "2026-11-09",
                      "publication_time": "2026-11-09",
                      "first_available_time": "2026-11-09",
                      "ingestion_time": "2026-11-09",
                      "decision_as_of": "2026-11-09"},
           "note": "append-tail blocker fixture"}


def _forecast(led, subject, value):
    return led.append_forecast_declared(
        engine_id="engine_x", issued_ts="2026-11-10",
        subject=subject, quantity="test quantity",
        value={"estimate": value},
        horizon_open="2026-11-10", horizon_close="2026-11-12",
        lineage=LINEAGE, families=["price"],
        outcome={"symbol": subject, "kind": "return_percent",
                 "base_date": "2026-11-09",
                 "at_date": "2026-11-12"})


def _read_all(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def test_append_path_never_parses_the_whole_ledger(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = ledger_mod.Ledger(path)
    led.append_genesis("fixture")
    row, created = _forecast(led, "AAA", 1.0)
    assert created
    again, created = _forecast(led, "AAA", 1.0)
    assert not created and again["row_id"] == row["row_id"]
    other, created = _forecast(led, "BBB", 2.0)
    assert created
    rows = _read_all(path)
    assert [r["type"] for r in rows] == [
        "genesis", "forecast", "forecast"]
    prev = ""
    for r in rows:
        assert r["prev_hash"] == prev
        prev = r["row_hash"]
    assert led.verify_chain_streaming()
    grade = led.append_grade(
        forecast_row=row, grade={"scores": {"pinball": 0.25}},
        **ledger_mod.frozen_label_identity(row))
    assert grade["type"] == "grade"
    try:
        led.append_grade(
            forecast_row=row, grade={"scores": {"pinball": 0.5}},
            **ledger_mod.frozen_label_identity(row))
        raise AssertionError("a second grade must be refused")
    except ledger_mod.LedgerError as e:
        assert "already graded" in str(e)
    corr = led.append_correction(corrects_row_id=other["row_id"],
                                 note="void BBB")
    assert corr["type"] == "correction"
    try:
        led.append_grade(
            forecast_row=other, grade={"scores": {"pinball": 0.5}},
            **ledger_mod.frozen_label_identity(other))
        raise AssertionError("grading a voided forecast must refuse")
    except ledger_mod.LedgerError as e:
        assert "voided" in str(e)
    try:
        led.append_correction(corrects_row_id="nope", note="x")
        raise AssertionError("an unknown correction target must refuse")
    except ledger_mod.LedgerError as e:
        assert "unknown row" in str(e)
    assert led.verify_chain_streaming()
    assert led.verify_chain()
    figures = ledger_mod.recompute_figures(led.iter_rows())
    assert figures["engine_x"]["forecasts"] == 2
    assert figures["engine_x"]["forecasts_voided"] == 1
    assert figures["engine_x"]["graded"] == 1


def test_tail_hash_reads_only_the_last_row(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = ledger_mod.Ledger(path)
    assert led._tail_hash() == ""
    led.append_genesis("fixture")
    rows = _read_all(path)
    assert led._tail_hash() == rows[-1]["row_hash"]
    _forecast(led, "AAA", 1.0)
    rows = _read_all(path)
    assert led._tail_hash() == rows[-1]["row_hash"]


def test_no_append_path_method_calls_rows():
    with open(os.path.join(FORECAST, "ledger.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    for name in ("def _append(", "def append_genesis(",
                 "def append_forecast(",
                 "def append_forecast_declared(",
                 "def append_grade(", "def append_correction("):
        start = src.index(name)
        nxt = src.find("\n    def ", start + len(name))
        body = src[start:nxt if nxt != -1 else len(src)]
        assert "self.rows()" not in body, (
            f"{name} still parses the whole ledger per call")
