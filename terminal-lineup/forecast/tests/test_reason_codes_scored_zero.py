"""Regression blockers for DEEP-PASS 3.1 items 6 and 7.

Item 6: per feature abstention reason codes in Ausar's fixed
vocabulary (research/forecast_engines/engine.py, branch
codex/forecast-engines-2026-10-29, read in code for this item),
landed in forecast/ledger.py abstention rows alongside the existing
absence states, and counted by grading.abstention_coverage_audit.

Item 7: the scored zero convention for passed events (FE26 in
Ausar's scorers.py: a passed event returns a scored zero with
drivers event_passed=1.0 and time_weight=0.0, not an abstention and
not silence), landed in forecast/ledger.py and wired into Engine 27
(Pin or Escape) for expiries that pass unrecorded.

Fail direction: pre-fix, ledger.py has no abstain_reasons or
scored_zero parameter, no vocabulary constants, and the audit has
no refused_by_reason counts, so these tests fail on the old code.
"""
import importlib.util
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

REG = R.load()
BASE = "2026-10-20"
AT = "2026-10-27"


def _load_pin():
    path = os.path.join(os.path.dirname(__file__), "..", "..",
                        "site", "refresh_pinorescape.py")
    spec = importlib.util.spec_from_file_location("pin27", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ledger(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("reason codes test")
    return led


def _common(tmp_path):
    art = tmp_path / "f.json"
    art.write_text("{}", encoding="utf-8")
    clocks = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
    lineage = {"source_artifacts": [{"path": str(art),
                                     "sha256": L.file_sha256(str(art))}],
               "clocks": clocks}
    return dict(engine_id="engine_02", issued_ts="2026-10-20T13:00:00Z",
                quantity="touch_probability", horizon_open=BASE,
                horizon_close=AT, lineage=lineage, families=["price"],
                outcome={"symbol": "SPY", "kind": "touch", "level": 105.5,
                         "window_open": BASE, "window_close": AT,
                         "at_date": AT})


# ---- the vocabulary, taken whole -------------------------------------

def test_vocabulary_is_ausars_fixed_set():
    assert set(L.PER_FEATURE_REASON_CAUSES) == {
        "missing", "invalid_observation", "non_finite", "unit_mismatch",
        "value_out_of_range", "future_or_late_data",
        "timestamp_order_invalid", "stale", "missing_provenance",
        "data_rights_not_approved", "unknown_evidence_kind",
        "missing_transform_provenance", "invalid_quality",
        "quality_below_floor"}
    assert set(L.GLOBAL_ABSTAIN_REASONS) == {
        "invalid_as_of", "invalid_symbol", "invalid_feature_collection",
        "invalid_target_window_id", "incomplete_target_window_binding",
        "target_contract_not_labelable", "target_window_id_not_allowed",
        "invalid_target_window_end", "target_window_start_before_as_of",
        "target_window_end_not_after_start", "invalid_label_transform_id",
        "invalid_label_transform_hash",
        "incomplete_label_transform_binding",
        "label_transform_for_nonlabelable_target", "invalid_label_context",
        "missing_label_context", "label_context_for_nonlabelable_target",
        "as_of_in_future", "score_computation_failed"}


def test_normalize_sorts_and_deduplicates():
    out = L.normalize_abstain_reasons(
        ["stale:ret_21d_z", "missing:ret_21d_z", "stale:ret_21d_z",
         "invalid_as_of"])
    assert out == ["invalid_as_of", "missing:ret_21d_z", "stale:ret_21d_z"]


@pytest.mark.parametrize("bad", [
    "stale",                      # per feature cause without its feature
    "stale:",                     # empty feature
    "not_a_cause:ret_21d_z",      # cause outside the vocabulary
    "made_up_reason",             # global outside the vocabulary
    "missing_provenance",         # per feature cause used as a global
    "",
])
def test_normalize_refuses_outside_vocabulary(bad):
    with pytest.raises(L.LedgerError):
        L.normalize_abstain_reasons([bad])


def test_feature_reason_builder_validates():
    assert L.feature_reason("stale", "ret_21d_z") == "stale:ret_21d_z"
    with pytest.raises(L.LedgerError):
        L.feature_reason("nope", "ret_21d_z")
    with pytest.raises(L.LedgerError):
        L.feature_reason("stale", "")


# ---- ledger rows ------------------------------------------------------

def test_abstention_row_stores_sorted_reason_codes(tmp_path):
    led = _ledger(tmp_path)
    row, was = led.append_forecast(
        subject="SPY", value={"p": None},
        absence_state="no_data",
        abstain_reasons=["stale:chain_snapshot",
                         "missing:chain_snapshot",
                         "stale:chain_snapshot"],
        **_common(tmp_path))
    assert was and row["abstain_reasons"] == [
        "missing:chain_snapshot", "stale:chain_snapshot"]
    assert led.verify_chain()


def test_abstention_without_reasons_stores_empty_list(tmp_path):
    # Legacy callers stay legal; the gap is stored as an empty list so
    # the audit can count reasonless refusals instead of hiding them.
    led = _ledger(tmp_path)
    row, _was = led.append_forecast(
        subject="SPY", value={"p": None}, absence_state="no_data",
        **_common(tmp_path))
    assert row["abstain_reasons"] == []


def test_taken_row_with_abstain_reasons_is_refused(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(L.LedgerError):
        led.append_forecast(subject="SPY", value={"p": 0.5},
                            abstain_reasons=["stale:x"],
                            **_common(tmp_path))
    assert len(led.rows()) == 1  # genesis only; nothing was written


def test_unknown_reason_at_append_is_refused_and_writes_nothing(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(L.LedgerError):
        led.append_forecast(subject="SPY", value={"p": None},
                            absence_state="no_data",
                            abstain_reasons=["engine_felt_like_it:x"],
                            **_common(tmp_path))
    assert len(led.rows()) == 1 and led.verify_chain()


def test_present_row_shape_unchanged_without_new_fields(tmp_path):
    led = _ledger(tmp_path)
    row, _was = led.append_forecast(subject="SPY", value={"p": 0.5},
                                    **_common(tmp_path))
    assert "abstain_reasons" not in row and "scored_zero" not in row


# ---- scored zero ------------------------------------------------------

def _zero_kwargs(tmp_path):
    kw = _common(tmp_path)
    kw["engine_id"] = "engine_27"
    return kw


def test_scored_zero_row_is_taken_and_counted(tmp_path):
    led = _ledger(tmp_path)
    row, was = led.append_forecast(
        subject="2026-10-23 SPY pin morning: event_passed",
        value={"estimate": 0.0, "event_passed": 1.0, "time_weight": 0.0},
        scored_zero={"drivers": {"event_passed": 1.0, "time_weight": 0.0}},
        **_zero_kwargs(tmp_path))
    assert was and row["absence_state"] == "present"
    assert L.is_scored_zero(row)
    figs = L.recompute_figures(led.rows())
    assert figs["engine_27"]["forecasts"] == 1
    assert figs["engine_27"]["scored_zero"] == 1
    assert figs["engine_02" if "engine_02" in figs else "engine_27"]


def test_scored_zero_requires_event_passed_driver(tmp_path):
    led = _ledger(tmp_path)
    for bad in ({"drivers": {"time_weight": 0.0}},
                {"drivers": {"event_passed": 0.0}},
                {"drivers": {}},
                {}):
        with pytest.raises(L.LedgerError):
            led.append_forecast(subject="SPY", value={"estimate": 0.0},
                                scored_zero=bad, **_zero_kwargs(tmp_path))
    assert len(led.rows()) == 1


def test_scored_zero_cannot_be_an_abstention(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(L.LedgerError):
        led.append_forecast(
            subject="SPY", value={"estimate": 0.0}, absence_state="no_data",
            abstain_reasons=["missing:pin"],
            scored_zero={"drivers": {"event_passed": 1.0}},
            **_zero_kwargs(tmp_path))


def test_engine27_passed_expiry_ledgers_scored_zero(tmp_path):
    pin = _load_pin()
    led = _ledger(tmp_path)
    art = tmp_path / "snapshot.json"
    art.write_text("{}", encoding="utf-8")
    n = pin.ledger_passed_expiry(led, "2026-10-23", "SPY", BASE,
                                 [str(art)])
    assert n == 1
    # A second call for the same passed expiry counts once (dedupe).
    n2 = pin.ledger_passed_expiry(led, "2026-10-23", "SPY", BASE,
                                  [str(art)])
    assert n2 == 0
    (row,) = [r for r in led.rows() if r.get("type") == "forecast"]
    assert row["engine_id"] == "engine_27"
    assert L.is_scored_zero(row)
    assert row["value"]["event_passed"] == 1.0
    assert row["scored_zero"]["drivers"]["event_passed"] == 1.0


# ---- audit counts the vocabulary -------------------------------------

class _Prices:
    path = "fixture"

    def __init__(self):
        self.bars = {"SPY": {BASE: (100.0, 100.0, 100.0, 100.0),
                             AT: (101.0, 101.0, 101.0, 101.0)}}
        self.calendars = {"SPY": [BASE, AT]}

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        return self.bars[s][d]

    def close(self, s, d):
        return self.bars[s][d][3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


def _audit_row(absence, reasons_marker, subject):
    r = {"type": "forecast", "engine_id": "engine_02",
         "subject": subject, "absence_state": absence,
         "horizon_open": BASE, "horizon_close": AT, "value": {"p": 0.5},
         "outcome": {"symbol": "SPY", "kind": "touch", "level": 105.5,
                     "window_open": BASE, "window_close": AT,
                     "at_date": AT}}
    if reasons_marker is not None:
        r["abstain_reasons"] = reasons_marker
    return r


def test_audit_counts_refused_by_reason():
    rows = [
        _audit_row("no_data", ["stale:bars", "missing:bars"], "A"),
        _audit_row("no_data", ["stale:bars"], "B"),
        _audit_row("no_data", [], "C"),          # reasonless refusal
        _audit_row("no_data", None, "D"),        # legacy row, no field
        _audit_row("present", None, "E"),
    ]
    # A scored zero row is taken, never refused.
    zero = _audit_row("present", None, "F")
    zero["scored_zero"] = {"drivers": {"event_passed": 1.0}}
    rows.append(zero)
    audit = G.abstention_coverage_audit(rows, _Prices())
    eng = audit["engines"]["engine_02"]
    assert eng["taken"] == 2 and eng["refused"] == 4
    assert eng["refused_by_reason"] == {"missing:bars": 1, "stale:bars": 2}
    assert eng["refused_without_reasons"] == 2
    assert audit["totals"]["refused_by_reason"] == {
        "missing:bars": 1, "stale:bars": 2}
    assert audit["totals"]["refused_without_reasons"] == 2
