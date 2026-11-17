"""Regression blocker for GRADING-REPORTS-STREAM-20261116.

The defect: forecast.run_grading_reports loaded the whole
ledger with Ledger.rows() (435,910 rows / 837 MB on 2026-11-16;
the parsed form is multiple GB) and was OOM-killed (exit 137
standalone, zero report lines printed) before its first report
line, on two consecutive refresh runs. In the live runner that
surfaced only as forecast-grading exit 1: run_grading relays
the child's failure to stderr, which refresh_engines discards
for spine steps. Session 2026-11-16 could not settle.

The cure: run_grading_reports.compact_rows makes one streaming
pass (Ledger.iter_rows) retaining only the fields the four
report aggregations read (full rows only for the HAR engines
engine_01/engine_07); the aggregation functions are then
called unchanged on the compact rows.

Fail direction: on the pre-cure module there is no
compact_rows and main() calls led.rows(); both tests below
fail there (AttributeError / source assertion). Proven by
running this file against the pre-cure copy on 2026-11-16.
"""
import copy
import os
import pickle
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

from forecast import grading, run_grading_reports


BULK = "x" * 20000


def _forecast(row_id, engine_id, quantity, value, **kw):
    row = {"type": "forecast", "row_id": row_id,
           "engine_id": engine_id, "quantity": quantity,
           "subject": kw.get("subject", "SPY"),
           "horizon_open": kw.get("horizon_open", "2026-10-05"),
           "horizon_close": kw.get("horizon_close", "2026-11-02"),
           "absence_state": None,
           "outcome": {"kind": "binary_event", "symbol": "SPY"},
           "value": value, "bulk_payload": BULK}
    return row


def _grade(forecast_row_id, scores, binary=1.0):
    return {"type": "grade", "forecast_row_id": forecast_row_id,
            "grade": {"binary_outcome": binary, "scores": scores},
            "bulk_payload": BULK}


def _fixture_rows():
    rows = [
        # engine_30 declared baseline (on-row probability)
        _forecast("f30a", "engine_30", "vix_spike",
                  {"p": 0.4, "p_control_vix_only": 0.3}),
        _grade("f30a", {"brier": 0.36}, binary=1.0),
        _forecast("f30b", "engine_30", "vix_spike",
                  {"p": 0.2, "p_control_vix_only": 0.25}),
        _grade("f30b", {"brier": 0.04}, binary=0.0),
        # engine_17 benchmark pair (main + Benchmark: quantity)
        _forecast("f17m", "engine_17", "dispersion",
                  {"estimate": 1.0}, subject="QQQ"),
        _grade("f17m", {"abs_error": 0.5}, binary=None),
        _forecast("f17b", "engine_17", "Benchmark: dispersion",
                  {"estimate": 1.0}, subject="QQQ"),
        _grade("f17b", {"abs_error": 0.9}, binary=None),
        # coverage_hit cell with a stated 0.1/0.9 band
        _forecast("f05a", "engine_05", "range",
                  {"quantiles": {"0.1": 1.0, "0.5": 2.0, "0.9": 3.0}}),
        _grade("f05a", {"coverage_hit": 1.0}, binary=None),
        _forecast("f05b", "engine_05", "range",
                  {"quantiles": {"0.1": 1.0, "0.5": 2.0, "0.9": 3.0}}),
        _grade("f05b", {"coverage_hit": 0.0}, binary=None),
        # a 20-session window row for the overlap report
        _forecast("f09a", "engine_09", "drift", {"p": 0.5},
                  horizon_open="2026-10-05",
                  horizon_close="2026-10-30"),
        # a row type no aggregation reads
        {"type": "correction", "row_id": "c1",
         "corrects_row_id": "nobody", "bulk_payload": BULK},
    ]
    return rows


class _FakeLedger:
    def __init__(self, rows):
        self._rows = rows

    def iter_rows(self):
        for r in self._rows:
            yield copy.deepcopy(r)

    def rows(self):
        raise AssertionError(
            "reports phase must stream (iter_rows), never rows()")


class _NoSessionPrices:
    def has_session(self, sym, date):
        return False


def test_compact_rows_stream_and_match_full_reports():
    full = _fixture_rows()
    compact = run_grading_reports.compact_rows(_FakeLedger(full))
    # Equivalence: every aggregation the reports phase prints
    # is identical on compact rows and on the full rows.
    assert grading.record_horizon_overlap(compact) == \
        grading.record_horizon_overlap(copy.deepcopy(full))
    assert grading.paired_baseline_report(compact) == \
        grading.paired_baseline_report(copy.deepcopy(full))
    assert grading.engine_cell_family(compact) == \
        grading.engine_cell_family(copy.deepcopy(full))
    assert grading.har_control_report(
        compact, _NoSessionPrices()) == grading.har_control_report(
            copy.deepcopy(full), _NoSessionPrices())
    # The bulky field no aggregation reads is not retained,
    # and the retained form is a small fraction of the full
    # form's size on this bulk-carrying fixture.
    assert all("bulk_payload" not in r for r in compact)
    assert len(pickle.dumps(compact)) < \
        len(pickle.dumps(full)) // 10


def test_reports_module_never_calls_rows():
    src = open(run_grading_reports.__file__, encoding="utf-8").read()
    assert "rows = led.rows()" not in src
    assert "rows = compact_rows(led)" in src


def test_recount_retention_is_compact_and_regenerate_streams():
    """Second kill point, same night: the attestation recount
    (refresh_attestations.regenerate, called in-process by the
    grading runner and as the attestation-refresh spine step)
    OOM-killed at exit -9 because recompute_figures retained
    every full forecast/grade row and regenerate held
    led.rows() beside it. On the pre-cure tree both source
    assertions below fail."""
    from forecast import ledger as ledger_mod
    from forecast import refresh_attestations
    led_src = open(ledger_mod.__file__, encoding="utf-8").read()
    assert "Compact retention (GRADING-REPORTS-STREAM-20261116)" \
        in led_src
    att_src = open(refresh_attestations.__file__,
                   encoding="utf-8").read()
    assert "rows = led.rows()" not in att_src
    assert "led.iter_rows()" in att_src


def test_recompute_figures_values_unchanged():
    """The compaction inside recompute_figures must not move
    any figure: frozen-identity grouping, void exclusion,
    scored-zero counting and mean scores on a fixture that
    exercises each."""
    from forecast import ledger as ledger_mod
    rows = [
        {"type": "forecast", "row_id": "a1", "engine_id": "e1",
         "label_context_fingerprint": "fp1",
         "label_transform_id": "t1", "label_transform_hash": "h1"},
        {"type": "forecast", "row_id": "a2", "engine_id": "e1",
         "scored_zero": {"drivers": {"event_passed": 1.0}}},
        {"type": "forecast", "row_id": "a3", "engine_id": "e1"},
        {"type": "correction", "row_id": "c1",
         "corrects_row_id": "a3"},
        {"type": "grade", "row_id": "g1", "engine_id": "e1",
         "forecast_row_id": "a1",
         "grade": {"scores": {"brier": 0.25, "note": "text"}}},
        {"type": "grade", "row_id": "g2", "engine_id": "e1",
         "forecast_row_id": "a2",
         "grade": {"scores": {"brier": 0.75}}},
        {"type": "grade", "row_id": "g3", "engine_id": "e1",
         "forecast_row_id": "a3",
         "grade": {"scores": {"brier": 0.5}}},
    ]
    figs = ledger_mod.recompute_figures(iter(rows))
    e1 = figs["e1"]
    assert e1["forecasts"] == 3
    assert e1["forecasts_voided"] == 1
    assert e1["forecasts_valid"] == 2
    assert e1["scored_zero"] == 1
    assert e1["graded"] == 2
    assert e1["grades_on_voided"] == 1
    assert e1["graded_raw"] == 3
    # Two fingerprint groups (fp1 and unfrozen): no pooled mean.
    assert e1["mean_scores"] == {}
    by_group = e1["by_label_fingerprint"]
    assert by_group["fp1"]["mean_scores"] == {"brier": 0.25}
    assert by_group[ledger_mod.UNFROZEN_GROUP]["mean_scores"] == \
        {"brier": 0.75}
