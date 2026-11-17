"""Regression blocker for SUITE-RED-CURE-20261117.

The defect: refresh_attestations.regenerate() accepts
registry_path / ledger_path overrides (used by fixture tests
such as test_attestation_stamp_20261108, which regenerates a
two-row fixture registry against a two-row fixture ledger),
but its closing write_checkpoint call used the checkpoint
writer's default path, the LIVE forecast/ledger-checkpoint.json.
Every fixture regeneration therefore overwrote the live ledger
anchor with the fixture's stats. Proven on 2026-11-17: the
live checkpoint read ledger_rows 2 / head 807b8bb4 (the stamp
fixture's BBB row hash, a hash that appears nowhere in the
live ledger), checked 2026-11-17T14:13:46Z, during the morning
suite run that had executed the stamp test minutes earlier,
while the live ledger held 480,188 rows with head 7e34f627.
test_health_r1_cures_20261031's checkpoint test failed on it.

The cure: regenerate() derives the checkpoint path from the
ledger it actually recounted (the directory of ledger_path),
so a fixture regeneration anchors its own fixture directory
and never touches the live file. For the default ledger the
derived path is exactly the live checkpoint path, so the
production anchor is unchanged.

Fail direction: on the pre-cure module the live-bytes assertion
below fails (the fixture regeneration rewrites the live
checkpoint to 2 rows / the fixture head). This test snapshots
the live checkpoint first and restores it in a finally block
when it changed, so even a failing run leaves no pollution
behind, unlike the defect it blocks.
"""
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
ROOT = os.path.dirname(FORECAST)
sys.path.insert(0, ROOT)

LIVE_CHECKPOINT = os.path.join(FORECAST, "ledger-checkpoint.json")


def _load_refresh_attestations():
    spec = importlib.util.spec_from_file_location(
        "refresh_attestations_isolation_test",
        os.path.join(FORECAST, "refresh_attestations.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture_registry():
    return {
        "schema": "forecast-family-registry/v1",
        "families": [{"id": "price", "name": "price",
                      "description": "fixture family"}],
        "grading_rules": [{"id": "coverage",
                           "scorer": "coverage",
                           "description": "fixture rule"}],
        "engines": [{
            "id": "engine_01", "name": "Fixture Engine",
            "number": 1, "state": "proving",
            "grading_rule_id": "coverage",
            "forecast_form": "distribution",
            "horizons": "1 session",
            "inputs": [{"name": "bars", "family": "price"}],
            "kill_criterion": "fixture",
            "proving_threshold": "1 live forecast",
            "edge_card": {
                "payer": "fixture", "bad_state": "fixture",
                "holdability_and_co_losses": "fixture",
                "execution_net": "fixture",
                "price_aware_baseline": "fixture"},
            "calibration_attestation": {}}]}


def test_fixture_regeneration_never_touches_live_checkpoint():
    ra = _load_refresh_attestations()
    led = __import__("importlib").import_module("forecast.ledger")
    with open(LIVE_CHECKPOINT, "rb") as fh:
        live_before = fh.read()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = os.path.join(tmp, "registry.json")
            ledger_path = os.path.join(tmp, "ledger.jsonl")
            with open(reg_path, "w", encoding="utf-8") as fh:
                json.dump(_fixture_registry(), fh)
            ledger = led.Ledger(ledger_path)
            clocks = {c: "2026-11-08T13:00:00Z"
                      for c in led.CLOCK_FIELDS}
            lineage = {"source_artifacts": [{"path": "f.json",
                                             "sha256": "ab" * 32}],
                       "clocks": clocks}
            common = dict(engine_id="engine_01",
                          issued_ts="2026-11-08T13:00:00Z",
                          quantity="touch_probability",
                          horizon_open="2026-11-09",
                          horizon_close="2026-11-10",
                          lineage=lineage, families=["price"])
            for sym, level in (("AAA", 105.5), ("BBB", 55.0)):
                ledger.append_forecast(
                    subject=sym, value={"p": 0.5},
                    outcome={"symbol": sym, "kind": "touch",
                             "level": level,
                             "window_open": "2026-11-09",
                             "window_close": "2026-11-10",
                             "at_date": "2026-11-10"}, **common)
            with open(ledger_path, encoding="utf-8") as fh:
                fixture_head = [json.loads(line) for line in fh
                                ][-1]["row_hash"]
            changed = ra.regenerate(recorded_on="2026-11-17",
                                    registry_path=reg_path,
                                    ledger_path=ledger_path)
            assert changed == ["engine_01"], changed
            # The fixture's own anchor is written beside the
            # fixture ledger, with the fixture's stats.
            fixture_ckpt = json.load(open(
                os.path.join(tmp, "ledger-checkpoint.json"),
                encoding="utf-8"))
            assert fixture_ckpt["ledger_rows"] == 2
            assert fixture_ckpt["ledger_head"] == fixture_head
            # The live anchor is byte-identical.
            with open(LIVE_CHECKPOINT, "rb") as fh:
                assert fh.read() == live_before, (
                    "fixture regeneration rewrote the live "
                    "ledger-checkpoint.json")
    finally:
        with open(LIVE_CHECKPOINT, "rb") as fh:
            if fh.read() != live_before:
                with open(LIVE_CHECKPOINT, "wb") as fh:
                    fh.write(live_before)
