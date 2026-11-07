"""Regression blockers for GRADING-STREAM-20261106.

The defect: the live grading runner (forecast.run_grading) held
the whole parsed ledger in its process for the run's whole
length. Ledger.rows() parses the entire JSONL file (500 MB,
253,163 rows on 2026-11-06) into dicts: measured 1,832.9 MB
peak RSS and 28.9 s for one load. The runner verified through
rows(), graded through rows() (append_grade additionally
scanned rows() on every grade, which is also why the classic
grading of one 6,000-row prefix took 54.9 s against the
streaming form's 1.3 s), and ran the report aggregations over
rows() in the same process, beside the full price panel, for
44-plus minutes. On 2026-11-06 the refresh's forecast-grading
step died at exit -9 (SIGKILL) about 44 minutes in, the third
straight failed refresh night (2026-11-04 runner kills,
2026-11-05 SIGTERM during the same lane), with other lanes on
the host: the largest resident process is the one the kernel
takes. The proofgate lane died of the same disease and its
streaming cure (PROOFGATE-APPEND-STREAM-20261105) is the
pattern this cure follows.

The cure: Ledger.iter_rows() streams rows without retaining
them; Ledger.grading_stream_state() makes one chain-verifying
streaming pass collecting only the tail hash, the graded-id
set, the void map, the grade count and the handful of context
rows grade_forecast scans for (28 rows in the 253,163-row
ledger); Ledger.append_grade(stream_state=...) runs its
refusal checks against those sets and appends through
_append_streaming; grading.run_grading_streaming walks the
ledger with the same predicates and accounting as
run_grading; forecast.run_grading routes its proof-gate pass
through the same state; and the report aggregations run in a
child process (forecast.run_grading_reports) that loads the
rows once and exits, so the one remaining full parse is
isolated and its memory is freed with the child.

What is test-proven here:
- the streaming grading path never calls Ledger.rows(): with
  rows() rigged to raise, a full streaming grading pass over a
  live-ledger prefix completes and the chain still verifies.
  The same rig makes the classic run_grading raise at once,
  which is the fail direction: the rig bites the old mechanism.
- appended bytes are identical: on twin prefixes of the live
  ledger, the streaming driver appends byte-identical grade
  rows to the classic driver's, with equal skipped lists; on a
  forged proof-gate fixture (one resolvable, one waiting, one
  off-panel record), the streaming proof-gate route appends
  byte-identical rows with equal counts.
- the streaming grade append refuses exactly as the classic
  one does: a second grade and a voided forecast are refused
  with the classic messages.
- grading_stream_state refuses a broken chain.
- the reports child loads the rows exactly once.
"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))
# proof_gate imports its siblings bare (from grading import ...),
# so the forecast directory itself must be importable too.
sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup/forecast"))

from forecast import grading, ledger as ledger_mod, proof_gate
from forecast import registry as registry_mod
from forecast import run_grading_reports

LIVE_LEDGER = os.path.expanduser(
    "~/workspace/terminal-lineup/forecast/ledger.jsonl")
PREFIX_ROWS = 3000


def _prefix(tmp_path, rows=PREFIX_ROWS, name="prefix.jsonl"):
    dst = tmp_path / name
    with open(LIVE_LEDGER) as fh, open(dst, "w") as out:
        for i, line in enumerate(fh):
            if i >= rows:
                break
            out.write(line)
    return str(dst)


def _forge(path, rows):
    prev = ""
    with open(path, "w") as fh:
        for row in rows:
            row = {k: v for k, v in row.items()
                   if k not in ("row_hash", "prev_hash", "row_id")}
            row["prev_hash"] = prev
            body = {k: v for k, v in row.items()
                    if k not in ("row_hash", "prev_hash", "row_id")}
            row["row_hash"] = hashlib.sha256(
                (prev + ledger_mod._canonical(body)).encode()
            ).hexdigest()
            row["row_id"] = row["row_hash"][:16]
            fh.write(ledger_mod._canonical(row) + "\n")
            prev = row["row_hash"]


@pytest.fixture(scope="module")
def reg():
    return registry_mod.load()


@pytest.fixture(scope="module")
def prices():
    return grading.PriceSource()


def test_streaming_grading_never_loads_the_ledger(tmp_path, reg,
                                                   prices, monkeypatch):
    path = _prefix(tmp_path, rows=6000)
    led = ledger_mod.Ledger(path, registry=reg)

    def _rigged(self):
        raise AssertionError("Ledger.rows() called on the "
                             "streaming grading path")

    monkeypatch.setattr(ledger_mod.Ledger, "rows", _rigged)
    # The rig bites the classic mechanism at once (fail
    # direction): the classic driver cannot take a step
    # without the whole parsed ledger.
    with pytest.raises(AssertionError):
        grading.run_grading(led, prices, reg, skipped=[])
    state = led.grading_stream_state()
    skipped = []
    new_grades = grading.run_grading_streaming(
        led, prices, reg, state, skipped=skipped)
    assert len(new_grades) > 0
    assert state["grade_count"] > 0
    monkeypatch.undo()
    assert led.verify_chain_streaming()


def test_streaming_matches_classic_appended_bytes(tmp_path, reg,
                                                  prices):
    pa = _prefix(tmp_path, name="twinA.jsonl")
    pb = _prefix(tmp_path, name="twinB.jsonl")
    led_a = ledger_mod.Ledger(pa, registry=reg)
    assert led_a.verify_chain()
    skipped_a = []
    new_a = grading.run_grading(led_a, prices, reg, skipped=skipped_a)
    led_b = ledger_mod.Ledger(pb, registry=reg)
    state = led_b.grading_stream_state()
    skipped_b = []
    new_b = grading.run_grading_streaming(
        led_b, prices, reg, state, skipped=skipped_b)
    assert len(new_a) == len(new_b) > 0
    assert skipped_a == skipped_b
    with open(pa) as fh:
        lines_a = fh.readlines()
    with open(pb) as fh:
        lines_b = fh.readlines()
    assert lines_a == lines_b


def test_proof_gate_streaming_matches_classic(tmp_path, reg, prices):
    # A real proof-gate record from the live ledger, its horizon
    # moved into the deep past so the frozen forward window has
    # fully traded; one waiting record; one off-panel record.
    candidate = waiting = nopanel = None
    with open(LIVE_LEDGER) as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("type") != "forecast":
                continue
            if (row.get("outcome") or {}).get("kind") != \
                    "provisional_proof_forward_check":
                continue
            sym = (row.get("outcome") or {}).get("symbol") \
                or row.get("subject")
            cal = prices.calendars.get(sym)
            if cal and candidate is None:
                candidate = row
            elif cal and waiting is None:
                waiting = row
            if not cal and nopanel is None:
                nopanel = row
            if candidate is not None and waiting is not None \
                    and nopanel is not None:
                break
    import copy
    mut = copy.deepcopy(candidate)
    sym = (mut.get("outcome") or {}).get("symbol") or mut.get("subject")
    cal = prices.calendars[sym]
    mut["horizon_open"] = cal[5]
    mut["issued_ts"] = cal[5]
    rows = [{"type": "genesis", "note": "blocker fixture"},
            mut, waiting, nopanel]

    def run(path, streaming):
        led = ledger_mod.Ledger(path, registry=reg)
        st = led.grading_stream_state() if streaming else None
        gids = None
        if not streaming:
            assert led.verify_chain()
            gids = {r.get("forecast_row_id") for r in led.rows()
                    if r.get("type") == "grade"}
        counts = [0, 0, 0]
        for row in (led.iter_rows() if streaming else led.rows()):
            if row.get("type") != "forecast":
                continue
            if (row.get("outcome") or {}).get("kind") != \
                    "provisional_proof_forward_check":
                continue
            gset = st["graded_ids"] if streaming else gids
            if row["row_id"] in gset:
                continue
            s2 = (row.get("outcome") or {}).get("symbol") \
                or row.get("subject")
            cal2 = prices.calendars.get(s2)
            if not cal2 or row["horizon_open"] not in cal2:
                counts[2] += 1
                continue
            closes = [prices.close(s2, d) for d in cal2]
            realised = proof_gate.forward_return(
                closes, cal2.index(row["horizon_open"]),
                reg.proof_gate_rule(row["engine_id"]))
            if realised is None:
                counts[1] += 1
                continue
            if streaming:
                proof_gate.grade_forward_record(
                    led, row, realised, stream_state=st)
            else:
                proof_gate.grade_forward_record(led, row, realised)
            counts[0] += 1
        with open(path) as fh:
            return counts, fh.readlines()

    pa = str(tmp_path / "pgA.jsonl")
    pb = str(tmp_path / "pgB.jsonl")
    _forge(pa, rows)
    _forge(pb, rows)
    counts_a, lines_a = run(pa, streaming=False)
    counts_b, lines_b = run(pb, streaming=True)
    assert counts_a == counts_b == [1, 1, 1]
    assert lines_a == lines_b


def test_streaming_grade_append_refusals(tmp_path, reg):
    fc1 = {"type": "forecast", "engine_id": "engine_19",
           "subject": "AAA", "horizon_close": "2026-01-01",
           "outcome": {"kind": "synthetic"}}
    fc2 = {"type": "forecast", "engine_id": "engine_19",
           "subject": "BBB", "horizon_close": "2026-01-01",
           "outcome": {"kind": "synthetic"}}
    path = str(tmp_path / "tiny.jsonl")
    _forge(path, [{"type": "genesis", "note": "tiny"}, fc1, fc2])
    # Learn the forged row ids, then add a correction voiding fc2.
    ids = {}
    led = ledger_mod.Ledger(path, registry=reg)
    for row in led.iter_rows():
        if row.get("type") == "forecast":
            ids[row["subject"]] = row["row_id"]
    corr = {"type": "correction", "corrects_row_id": ids["BBB"],
            "note": "void", "payload": {}}
    with open(path) as fh:
        existing = [json.loads(line) for line in fh]
    _forge(path, existing + [corr])
    led = ledger_mod.Ledger(path, registry=reg)
    state = led.grading_stream_state()
    rows_by_subject = {}
    for row in led.iter_rows():
        if row.get("type") == "forecast":
            rows_by_subject[row["subject"]] = row
    grade = {"rule_id": "abs_error", "scores": {"x": 1.0}}
    appended = led.append_grade(
        forecast_row=rows_by_subject["AAA"], grade=grade,
        stream_state=state)
    assert appended["forecast_row_id"] == ids["AAA"]
    with pytest.raises(ledger_mod.LedgerError, match="already graded"):
        led.append_grade(forecast_row=rows_by_subject["AAA"],
                         grade=grade, stream_state=state)
    with pytest.raises(ledger_mod.LedgerError, match="voided by"):
        led.append_grade(forecast_row=rows_by_subject["BBB"],
                         grade=grade, stream_state=state)
    assert led.verify_chain_streaming()


def test_grading_stream_state_refuses_broken_chain(tmp_path, reg):
    path = _prefix(tmp_path, rows=50)
    with open(path) as fh:
        lines = fh.readlines()
    lines[10] = lines[10].replace('"forecast"', '"forecasx"', 1) \
        if '"forecast"' in lines[10] else \
        lines[10][:-3] + 'x"}\n'
    with open(path, "w") as fh:
        fh.writelines(lines)
    led = ledger_mod.Ledger(path, registry=reg)
    with pytest.raises(ledger_mod.LedgerError):
        led.grading_stream_state()


def test_reports_child_loads_rows_exactly_once(tmp_path, reg,
                                               monkeypatch, capsys):
    path = _prefix(tmp_path, rows=6000)
    monkeypatch.setattr(run_grading_reports, "LEDGER_PATH", path)
    calls = []
    original = ledger_mod.Ledger.rows

    def counting(self):
        calls.append(1)
        return original(self)

    monkeypatch.setattr(ledger_mod.Ledger, "rows", counting)
    assert run_grading_reports.main() == 0
    assert len(calls) == 1
    out = capsys.readouterr().out
    assert "overlap engine_" in out
    assert "family engine_" in out or "har control" in out
