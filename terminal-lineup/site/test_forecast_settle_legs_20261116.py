"""Regression blockers for FORECAST-SETTLE-LEGS-20261116.

Failure of record (session 2026-11-16, settle run finished
2026-11-17T01:14:23Z and rescue retry 01:28:13Z, identical):
- capitulation-clock (refresh_capitulationclock.py) exited -9:
  after grading its own rows it built fc_by_id, a dict of EVERY
  forecast row on the ledger (all engines, full parsed rows,
  ~158k of them engine_19's alone) to read back one field
  (quantity) for its own engine's grades — the full-ledger
  retention disease on a 6 GB box.
- in-regime-oracle (refresh_inregimeoracle.py) exited 1:
  KeyError 'trailing_hit_rate' at its Monday grading loop. The
  loop walked every engine_19 forecast on the ledger; 158,440
  of the 158,443 are Aperture proof-gate rows (outcome kind
  provisional_proof_forward_check) whose outcome carries no
  trailing_hit_rate. Only the 3 rows of kind
  next_window_hit_rate_exceeds_trailing are this page's weekly
  windows and carry the field.

Cures pinned here:
- the capitulation tail retains only {row_id: quantity} for
  its own engine's forecasts (fc_qty_by_id);
- the in-regime grading scan collects only forecasts whose
  outcome kind is next_window_hit_rate_exceeds_trailing.

Set LEG_MODULE_DIR to a directory holding pre-cure copies of
the refreshers to watch the source assertions fail.
"""
import importlib.util
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))


def _src(name):
    with open(os.path.join(MODULE_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _load_inregime():
    path = os.path.join(MODULE_DIR, "refresh_inregimeoracle.py")
    spec = importlib.util.spec_from_file_location(
        "refresh_inregimeoracle", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------- capitulation-clock ----------------

def test_capitulation_no_all_engine_forecast_retention():
    src = _src("refresh_capitulationclock.py")
    assert "fc_by_id" not in src
    assert '{r["row_id"]: r for r in led.iter_rows()' not in src


def test_capitulation_retains_only_own_engine_quantities():
    src = _src("refresh_capitulationclock.py")
    assert "fc_qty_by_id" in src
    assert 'r.get("quantity", "?")' in src
    # the retained map is built from own-engine forecasts only
    i = src.index("fc_qty_by_id = ")
    window = src[i:i + 400]
    assert 'r.get("engine_id") == ENGINE_ID' in window


# ---------------- in-regime-oracle ----------------

def test_inregime_grading_scan_filters_by_outcome_kind():
    src = _src("refresh_inregimeoracle.py")
    i = src.index("engine_forecasts = ")
    window = src[i:i + 500]
    assert '"next_window_hit_rate_exceeds_trailing"' in window


def test_inregime_proof_gate_rows_carry_no_trailing_hit_rate():
    # The defect shape, on fixtures: an unfiltered matured
    # proof-gate row raises the exact KeyError of record, and
    # the cured scan (kind filter) leaves only the window row,
    # which grades through the module's own grade_window.
    mod = _load_inregime()
    proof_row = {
        "type": "forecast", "engine_id": "engine_19",
        "row_id": "proof1", "horizon_open": "2026-10-05",
        "horizon_close": "2026-10-30",
        "outcome": {"kind": "provisional_proof_forward_check",
                    "population": "board_gate"}}
    window_row = {
        "type": "forecast", "engine_id": "engine_19",
        "row_id": "win1", "horizon_open": "2026-10-05",
        "horizon_close": "2026-10-30",
        "value": {"p": 0.5, "p_rival": 0.5},
        "outcome": {"kind": "next_window_hit_rate_exceeds_trailing",
                    "population": "board_gate",
                    "trailing_hit_rate": 0.4}}
    with pytest.raises(KeyError):
        proof_row["outcome"]["trailing_hit_rate"]
    kept = [r for r in (proof_row, window_row)
            if (r.get("outcome") or {}).get("kind")
            == "next_window_hit_rate_exceeds_trailing"]
    assert kept == [window_row]
    g = mod.grade_window([], kept[0]["outcome"]["trailing_hit_rate"])
    assert g["outcome"] == 0.0  # no-call window grades, never crashes


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
