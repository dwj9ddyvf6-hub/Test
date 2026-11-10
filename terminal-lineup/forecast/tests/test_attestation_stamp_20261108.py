"""Blockers for the attestation position-stamp cure
(ATTESTATION-STAMP-20261108).

Failure class: on 2026-11-08 verify_terminal.sh reported four
problems (registry engine_17 forecasts_recorded 72 vs recounted
76, registry engine_20 graded_forecasts 2 vs 4, and the same two
figures on the calibration-league and family-fracture pages).
The attestations were regenerated on 2026-11-07 at ledger
position 280,313 rows and the ledger then grew to 296,138 rows
through supervised runs that never completed the engines
runner, so the check asked a dated snapshot to equal today's
recount with nothing on the record saying which ledger the
snapshot counts. The cure stamps every attestation with
ledger_rows_at_write and the verifier ties figures strictly
only when the stamp equals the current row count; a
regeneration stamps and refreshes the figures together.

Fail direction: pre-cure, attestation_record carries no stamp
(check 1), regeneration passes no position (check 2, by source),
and the verifier's ties take no total_rows argument and fail on
stale snapshots exactly as they did on 2026-11-08 (checks 3-5).
Run standalone: python3 test_attestation_stamp_20261108.py
(exit 0 = pass)."""
import importlib
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FORECAST = os.path.dirname(HERE)
ROOT = os.path.dirname(FORECAST)
sys.path.insert(0, ROOT)

from forecast import grading  # noqa: E402
from forecast import verify_grade_rows as V  # noqa: E402


def _load_refresh_attestations():
    spec = importlib.util.spec_from_file_location(
        "refresh_attestations_stamp_test",
        os.path.join(FORECAST, "refresh_attestations.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_stamp_written_only_when_position_passed():
    figures = {"forecasts": 10, "forecasts_valid": 10,
               "graded": 4, "mean_scores": {}}
    eng = {"id": "engine_99"}
    plain = grading.attestation_record(eng, figures, "2026-11-08")
    assert "ledger_rows_at_write" not in plain
    stamped = grading.attestation_record(
        eng, figures, "2026-11-08", ledger_rows=296138)
    assert stamped["ledger_rows_at_write"] == 296138
    # Figures are the stamped ones either way.
    assert stamped["forecasts_recorded"] == 10
    assert stamped["graded_forecasts"] == 4


def test_regenerate_stamps_the_full_ledger_position():
    src = open(os.path.join(FORECAST, "refresh_attestations.py"),
               encoding="utf-8").read()
    assert "ledger_rows=len(rows)" in src
    # Behavioural: regenerate a one-engine fixture registry
    # against a fixture ledger; the stamp must equal the
    # ledger's full row count and the figures must recount from
    # that same ledger. (A live-registry equality check would
    # rot the moment the ledger grows again, which is the very
    # class this cure exists for.)
    ra = _load_refresh_attestations()
    led = importlib.import_module("forecast.ledger")
    with tempfile.TemporaryDirectory() as tmp:
        reg_path = os.path.join(tmp, "registry.json")
        ledger_path = os.path.join(tmp, "ledger.jsonl")
        # Minimal registry that still validates: regenerate ends
        # by loading the registry, whose validator needs the
        # families, grading rules and a complete engine entry.
        fixture_registry = {
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
        with open(reg_path, "w", encoding="utf-8") as fh:
            json.dump(fixture_registry, fh)
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
                         "level": level, "window_open": "2026-11-09",
                         "window_close": "2026-11-10",
                         "at_date": "2026-11-10"}, **common)
        changed = ra.regenerate(recorded_on="2026-11-08",
                                registry_path=reg_path,
                                ledger_path=ledger_path)
        assert changed == ["engine_01"], changed
        reg = json.load(open(reg_path, encoding="utf-8"))
        att = reg["engines"][0]["calibration_attestation"]
        assert att["ledger_rows_at_write"] == 2, att
        assert att["forecasts_recorded"] == 2, att


def _fixtures(tmp):
    site = os.path.join(tmp, "site")
    page_dir = os.path.join(site, "page-x")
    os.makedirs(page_dir)
    att = {"forecasts_recorded": 99, "graded_forecasts": 88,
           "ledger_rows_at_write": 500}
    with open(os.path.join(page_dir, "data.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"calibration_attestation": {
            "engine_id": "engine_01", "attestation": dict(att)}},
            fh)
    reg_path = os.path.join(tmp, "registry.json")
    with open(reg_path, "w", encoding="utf-8") as fh:
        json.dump({"engines": [{"id": "engine_01",
                                "calibration_attestation":
                                dict(att)}]}, fh)
    per = {"engine_01": {"forecasts_valid": 10, "grades_valid": 5,
                         "forecasts_valid_own": 10,
                         "grades_valid_own": 5}}
    return site, reg_path, per


def test_current_position_wrong_figures_still_fail():
    with tempfile.TemporaryDirectory() as tmp:
        site, reg_path, per = _fixtures(tmp)
        mm, _ = V.cross_tie(site, per, total_rows=500)
        assert any("forecasts_recorded" in m for m in mm), mm
        rm = V.registry_mismatches(reg_path, per, total_rows=500)
        assert any("forecasts_recorded" in m for m in rm), rm


def test_older_position_snapshot_is_not_judged_by_todays_recount():
    with tempfile.TemporaryDirectory() as tmp:
        site, reg_path, per = _fixtures(tmp)
        mm, _ = V.cross_tie(site, per, total_rows=600)
        assert mm == [], mm
        rm = V.registry_mismatches(reg_path, per, total_rows=600)
        assert rm == [], rm


def test_unstamped_attestation_keeps_the_strict_tie():
    with tempfile.TemporaryDirectory() as tmp:
        site, reg_path, per = _fixtures(tmp)
        page = os.path.join(site, "page-x", "data.json")
        data = json.load(open(page, encoding="utf-8"))
        del data["calibration_attestation"]["attestation"][
            "ledger_rows_at_write"]
        with open(page, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        mm, _ = V.cross_tie(site, per, total_rows=600)
        assert any("forecasts_recorded" in m for m in mm), mm


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    fails = []
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            fails.append(f"{t.__name__}: {exc!r}")
        except Exception as exc:  # noqa: BLE001
            fails.append(f"{t.__name__}: ERROR {exc!r}")
    for f in fails:
        print("FAIL: " + f)
    print("attestation stamp tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
