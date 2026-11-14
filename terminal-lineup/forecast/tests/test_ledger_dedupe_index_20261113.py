"""Regression blockers for LEDGER-DEDUPE-INDEX-20261113.

Failure class: the classic forecast append paths
(Ledger.append_forecast and Ledger.append_forecast_declared)
proved a republication by streaming the whole ledger and
parsing every row's JSON, once per append, twice over
(declared's legacy scan, then append_forecast's own). At the
2026-11-13 ledger (401,862 rows, 804 MB, about 9s per parse)
a bulk caller recording dozens of forecasts in one run paid
that parse per forecast: refresh_insiderdivergence.py's
appends landed 20 to 50 seconds apart in the ledger
provenance log (pid 11403, 2026-11-14T00:52Z onward) and the
leg never finished before the tools runner was terminated.

Cure pinned here: a dedupe offset index on Ledger. One raw
scan records each forecast row's stored dedupe key and byte
offset (append-only file: offsets never move); later calls
rescan only the appended suffix, and a dedupe lookup parses
only the candidate line, applying the exact checks the full
scan applied.

What is test-proven here:
- neither classic append path calls Ledger.iter_rows at all
  (rigged to raise): a new issue and its republication both
  resolve through the index. On the pre-cure code the first
  declared append raises from the rigged iter_rows.
- republication verdicts are the scan's own: the existing
  row is returned (same row_id), nothing is written, for the
  declared path, the plain path, and the legacy-unfrozen
  return a cured refresher relies on.
- the index stays honest across writers: a second Ledger
  instance sees rows another instance appended after its
  index was built (suffix refresh), so cross-process
  republications still dedupe.
- a bulk batch of declared appends on one instance creates
  each forecast once, counts every republication a
  duplicate, and leaves a verifying chain.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
sys.path.insert(0, FORECAST)

from ledger import Ledger  # noqa: E402

ISSUED = "2026-11-13"
LINEAGE = {"clocks": {c: ISSUED for c in (
    "event_time", "publication_time", "first_available_time",
    "ingestion_time", "decision_as_of")},
    "source_artifacts": [{"path": "/tmp/panel.json",
                          "sha256": "0" * 64}]}


def _args(subject, estimate=1.0):
    return dict(engine_id="engine_10", issued_ts=ISSUED,
                subject=subject, quantity="21-session gain",
                value={"estimate": estimate, "cell": "control"},
                horizon_open="2026-11-16",
                horizon_close="2026-12-15",
                lineage=LINEAGE, families=["price"],
                outcome={"kind": "excess_21s", "symbol": subject})


def _forecast_count(path):
    n = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if '"type":"forecast"' in line:
                n += 1
    return n


def test_classic_appends_never_stream_the_ledger(tmp_path,
                                                 monkeypatch):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)

    def _rigged(self):
        raise AssertionError(
            "classic append streamed the whole ledger")

    monkeypatch.setattr(Ledger, "iter_rows", _rigged)
    row, created = led.append_forecast_declared(**_args("AAA"))
    assert created is True
    again, created = led.append_forecast_declared(**_args("AAA"))
    assert created is False
    assert again["row_id"] == row["row_id"]
    plain, created = led.append_forecast(**_args("BBB"))
    assert created is True
    plain2, created = led.append_forecast(**_args("BBB"))
    assert created is False
    assert plain2["row_id"] == plain["row_id"]
    monkeypatch.undo()
    assert Ledger(path).verify_chain_streaming() is True
    assert _forecast_count(path) == 2


def test_index_sees_rows_appended_by_another_instance(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    writer = Ledger(path)
    reader = Ledger(path)
    row_a, created = writer.append_forecast_declared(**_args("AAA"))
    assert created is True
    # Build the reader's index now, then have the writer land
    # a second forecast behind it.
    got, created = reader.append_forecast_declared(**_args("AAA"))
    assert created is False and got["row_id"] == row_a["row_id"]
    row_b, created = writer.append_forecast_declared(**_args("BBB"))
    assert created is True
    got, created = reader.append_forecast_declared(**_args("BBB"))
    assert created is False and got["row_id"] == row_b["row_id"]
    assert _forecast_count(path) == 2


def test_bulk_declared_appends_create_once_each(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    subjects = [f"S{i:02d}" for i in range(40)]
    for s in subjects:
        _row, created = led.append_forecast_declared(**_args(s))
        assert created is True
    for s in subjects:
        _row, created = led.append_forecast_declared(**_args(s))
        assert created is False
    assert _forecast_count(path) == len(subjects)
    assert Ledger(path).verify_chain_streaming() is True
