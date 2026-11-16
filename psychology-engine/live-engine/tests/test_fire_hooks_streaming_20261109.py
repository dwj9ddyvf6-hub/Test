#!/usr/bin/env python3
"""Regression blocker for HOOKS-LEDGER-STREAM-20261109.

Failure of record: the 2026-11-09 psychology daily run
compiled and published its state (23:26:25Z) and was then
OOM-killed (exit 137) inside fire_hooks. The stage called
Ledger.rows() on the estate forecast ledger (622 MB,
about 296k rows) for its before count; the append changed
the file, so the after count re-parsed the entire ledger
into a second parsed copy while the first was still cached,
and verify_chain plus the backdated scan materialised more.
Two parsed copies of that ledger do not fit this cell
alongside the rest of the run (a single parse peaks above
2 GB, measured 2026-11-09), so the hooks stage died before
hooks-day-one.json was written and no F1 forecast fired.

Cure pinned here: fire_hooks never materialises the ledger.
Counts, the F1 dedupe scan and the backdated scan stream
through Ledger.iter_rows(); the append goes through the
ledger's own streaming append state (chain verified
streaming, tail hash carried, no parsed copy held); chain
validity is verify_chain_streaming(). This test forbids
rows() outright: a Ledger whose rows() raises must still
see the stage complete with the same outputs.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

import pipeline  # noqa: E402
import forecast.ledger as ledger_mod  # noqa: E402

CLOCKS = {c: "2026-11-01T00:00:00+00:00" for c in
          ("event_time", "publication_time", "first_available_time",
           "ingestion_time", "decision_as_of")}
LINEAGE = {"clocks": CLOCKS, "source_artifacts": [
    {"path": "fixture", "sha256": "0" * 64}]}

AAII = [{"date": "2026-10-29", "spread": "1.0"},
        {"date": "2026-11-05", "spread": "2.5"}]


def _read_series(name):
    if name == "aaii_weekly.csv":
        return [dict(r) for r in AAII]
    return []


def test_fire_hooks_completes_without_materialising_the_ledger(
        tmp_path, monkeypatch):
    led_path = str(tmp_path / "ledger.jsonl")
    RealLedger = ledger_mod.Ledger
    real = RealLedger(led_path)
    real.append_genesis("hooks streaming test")
    real.append_forecast(
        engine_id="psychology_engine_f1",
        issued_ts="2026-11-01T00:00:00+00:00",
        subject="AAII bull minus bear spread, next weekly print",
        quantity="three-bucket probability distribution",
        value={"buckets": {"widens_bullish": 0.3,
                           "within_plus_minus_2": 0.4,
                           "narrows_or_falls": 0.3}},
        horizon_open="2026-11-06", horizon_close="2026-11-06",
        lineage=LINEAGE, families=["filings_positioning"],
        outcome={"kind": "survey_print", "series": "aaii_spread_bucket",
                 "resolver": "psychology grading_hooks (survey prints)"})
    real.append_forecast(
        engine_id="some_other_engine",
        issued_ts="2026-11-09T00:00:00+00:00",
        subject="fixture", quantity="fixture",
        value={"x": 1},
        horizon_open="2026-11-20", horizon_close="2026-11-20",
        lineage=LINEAGE, families=["filings_positioning"],
        outcome={"kind": "survey_print", "series": "fixture",
                 "resolver": "fixture"})

    class NoRowsLedger(ledger_mod.Ledger):
        def rows(self):
            raise AssertionError(
                "fire_hooks must not materialise the ledger")

    monkeypatch.setattr(ledger_mod, "Ledger",
                        lambda path: NoRowsLedger(led_path))
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    (series_dir / "aaii_weekly.csv").write_text("date,spread\n")
    monkeypatch.setattr(pipeline, "SERIES", str(series_dir))
    monkeypatch.setattr(pipeline, "OUT", str(tmp_path))
    monkeypatch.setattr(pipeline, "read_series", _read_series)

    fired = pipeline.fire_hooks({})
    assert "error" not in fired, fired
    assert fired["F1"]["created"] is True, fired
    assert fired["ledger_rows_before"] == 3, fired
    assert fired["ledger_rows_after"] == 4, fired
    assert fired["chain_valid"] is True, fired
    assert fired["backdated_psychology_rows"] == 1, fired

    written = json.loads((tmp_path / "hooks-day-one.json").read_text())
    assert written["ledger_rows_after"] == 4
    check = RealLedger(led_path)
    assert len(check.rows()) == 4
    assert check.verify_chain() is True
