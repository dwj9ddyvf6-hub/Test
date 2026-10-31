"""Regression blockers for DEEP-PASS 3.2 item 3: label definition
freezing (target context and transform fingerprints) and registry
edge cards.

Fail direction: on the pre-fix machinery these tests fail because
ledger.py has no label context helpers, append_forecast accepts no
label identity, append_grade repeats no frozen identity,
recompute_figures pools every grade into one mean, and registry.json
carries no edge_card fields at all."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

REG = R.load()
CLOCKS = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
LINEAGE = {"source_artifacts": [{"path": "fixture.json", "sha256": "ab" * 32}],
           "clocks": CLOCKS}
CONTEXT_A = {
    "series": "SPY daily close",
    "measurement_basis": "close-to-close, split adjusted bars",
    "calendar": "NYSE sessions",
    "reference_series": "SPY",
    "data_vintage_policy": "point in time as first available",
    "corporate_action_policy": "split adjusted, dividends excluded"}
CONTEXT_B = dict(CONTEXT_A, measurement_basis="open-to-close, unadjusted")
TRANSFORM_SPEC = {"operation": "close_at_date", "version": 1}


def make_ledger(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    return led


def label_kwargs(context=CONTEXT_A):
    return {"label_context": context,
            "label_transform_id": "close_at_date_v1",
            "label_transform_hash": L.label_transform_hash_for(
                "close_at_date_v1", TRANSFORM_SPEC)}


def forecast_kwargs(**over):
    kw = dict(engine_id="engine_01", issued_ts="2026-10-20T13:00:00Z",
              subject="SPY", quantity="close_band_5s",
              value={"lower": 100.0, "upper": 110.0,
                     "stated_coverage": 0.68},
              horizon_open="2026-10-21", horizon_close="2026-10-27",
              lineage=LINEAGE, families=["distributional_volatility"],
              outcome={"symbol": "SPY", "kind": "close",
                       "at_date": "2026-10-27"})
    kw.update(over)
    return kw


class FakePrices:
    path = "fixture-prices"

    def __init__(self):
        self.bars = {"SPY": {"2026-10-21": (100.0, 101.0, 99.0, 100.5),
                             "2026-10-27": (104.0, 106.0, 103.0, 105.0)}}
        self.calendars = {"SPY": sorted(self.bars["SPY"])}

    def has_session(self, s, d):
        return d in self.bars.get(s, {})

    def bar(self, s, d):
        return self.bars[s][d]

    def close(self, s, d):
        return self.bars[s][d][3]

    def window(self, s, a, b):
        return [(d, self.bars[s][d]) for d in self.calendars[s]
                if a <= d <= b]


# ---- label context fingerprint -------------------------------------

def test_context_fingerprint_is_six_field_and_stable():
    fp_a = L.label_context_fingerprint(CONTEXT_A)
    assert fp_a == L.label_context_fingerprint(dict(CONTEXT_A))
    assert len(fp_a) == 64
    assert fp_a != L.label_context_fingerprint(CONTEXT_B)
    assert set(L.LABEL_CONTEXT_FIELDS) == set(CONTEXT_A)


def test_incomplete_or_extra_context_refused():
    with pytest.raises(L.LedgerError):
        L.normalize_label_context({k: v for k, v in CONTEXT_A.items()
                                   if k != "calendar"})
    with pytest.raises(L.LedgerError):
        L.normalize_label_context(dict(CONTEXT_A, extra="nope"))
    with pytest.raises(L.LedgerError):
        L.normalize_label_context(dict(CONTEXT_A, calendar="  "))


# ---- forecast rows gain the frozen identity -------------------------

def test_forecast_row_carries_frozen_identity(tmp_path):
    led = make_ledger(tmp_path)
    row, created = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    assert created is True
    assert row["label_context"] == CONTEXT_A
    assert row["label_context_fingerprint"] == \
        L.label_context_fingerprint(CONTEXT_A)
    assert row["label_transform_id"] == "close_at_date_v1"
    assert row["label_transform_hash"] == label_kwargs()[
        "label_transform_hash"]
    assert led.verify_chain() is True


def test_partial_label_identity_refused_at_append(tmp_path):
    led = make_ledger(tmp_path)
    with pytest.raises(L.LedgerError):
        led.append_forecast(**forecast_kwargs(
            label_context=CONTEXT_A))
    with pytest.raises(L.LedgerError):
        led.append_forecast(**forecast_kwargs(
            label_transform_id="close_at_date_v1",
            label_transform_hash="zz" * 32))
    with pytest.raises(L.LedgerError):
        led.append_forecast(**forecast_kwargs(
            label_context=CONTEXT_A, label_transform_id="x",
            label_transform_hash="not-a-hash"))


def test_same_value_under_different_context_is_not_a_duplicate(tmp_path):
    led = make_ledger(tmp_path)
    _r1, c1 = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    _r2, c2 = led.append_forecast(
        **forecast_kwargs(**label_kwargs(context=CONTEXT_B)))
    assert c1 is True and c2 is True
    _r3, c3 = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    assert c3 is False


def test_legacy_row_without_identity_still_appends(tmp_path):
    led = make_ledger(tmp_path)
    row, created = led.append_forecast(**forecast_kwargs())
    assert created is True
    assert "label_context_fingerprint" not in row


# ---- outcome appends must repeat the frozen identity ----------------

def test_grade_without_repeated_identity_refused(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    with pytest.raises(L.LedgerError):
        led.append_grade(forecast_row=row, grade={"scores": {}})


def test_grade_with_mismatched_identity_refused(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    ident = L.frozen_label_identity(row)
    bad = dict(ident, label_context_fingerprint="0" * 64)
    with pytest.raises(L.LedgerError):
        led.append_grade(forecast_row=row, grade={"scores": {}},
                         **bad)


def test_grade_repeating_identity_appends_and_stores_it(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(**label_kwargs()))
    grade = led.append_grade(forecast_row=row, grade={"scores": {}},
                             **L.frozen_label_identity(row))
    for field, val in L.frozen_label_identity(row).items():
        assert grade[field] == val


def test_identity_supplied_for_unfrozen_forecast_refused(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs())
    with pytest.raises(L.LedgerError):
        led.append_grade(forecast_row=row, grade={"scores": {}},
                         **label_kwargs_identity())


def label_kwargs_identity():
    kw = label_kwargs()
    return {"label_context_fingerprint":
            L.label_context_fingerprint(kw["label_context"]),
            "label_transform_id": kw["label_transform_id"],
            "label_transform_hash": kw["label_transform_hash"]}


def test_grading_runner_repeats_frozen_identity(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs(
        quantity="close_distribution_5s",
        value={"quantiles": {"0.1": 100.0, "0.5": 105.0, "0.9": 110.0}},
        **label_kwargs()))
    grade = G.grade_forecast(led, row, FakePrices(), REG)
    assert grade["label_context_fingerprint"] == \
        L.label_context_fingerprint(CONTEXT_A)
    assert grade["label_transform_id"] == "close_at_date_v1"


# ---- grading never pools across fingerprints ------------------------

def test_recompute_figures_groups_by_fingerprint(tmp_path):
    led = make_ledger(tmp_path)
    rows = []
    for ctx, pinball in ((CONTEXT_A, 0.0), (CONTEXT_B, 10.0)):
        row, _ = led.append_forecast(**forecast_kwargs(
            subject=f"S{len(rows)}", **label_kwargs(context=ctx)))
        rows.append(row)
        led.append_grade(forecast_row=row, grade={
            "scores": {"pinball@0.5": pinball}},
            **L.frozen_label_identity(row))
    figs = L.recompute_figures(led.rows())
    eng = figs["engine_01"]
    assert eng["forecasts"] == 2 and eng["graded"] == 2
    # pooled mean would be 5.0; pooling across fingerprints is refused
    assert eng["mean_scores"] == {}
    groups = eng["by_label_fingerprint"]
    assert groups[L.label_context_fingerprint(CONTEXT_A)][
        "mean_scores"]["pinball@0.5"] == 0.0
    assert groups[L.label_context_fingerprint(CONTEXT_B)][
        "mean_scores"]["pinball@0.5"] == 10.0


def test_recompute_single_group_keeps_top_level_mean(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs())
    led.append_grade(forecast_row=row,
                     grade={"scores": {"pinball@0.5": 2.0}})
    figs = L.recompute_figures(led.rows())
    assert figs["engine_01"]["mean_scores"]["pinball@0.5"] == 2.0
    assert "unfrozen_legacy" in figs["engine_01"]["by_label_fingerprint"]


# ---- registry edge cards ---------------------------------------------

def test_every_engine_carries_a_complete_edge_card():
    for eng in REG.data["engines"]:
        card = eng.get("edge_card") or {}
        for field in R.EDGE_CARD_FIELDS:
            assert isinstance(card.get(field), str) and card[field].strip(), \
                f"{eng['id']} edge card missing {field}"
        # language strengthening sits alongside the fields already carried
        assert eng["proving_threshold"] and eng["grading_rule_id"]


def test_registry_validation_refuses_missing_edge_card(tmp_path):
    data = json.loads(json.dumps(REG.data))
    del data["engines"][0]["edge_card"]["payer"]
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(data))
    with pytest.raises(R.RegistryError):
        R.Registry(str(path))
