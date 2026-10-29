from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from research.forecast_engines.boundary_map import forecast_boundary_map
from research.forecast_engines.abstention_audit import abstention_coverage_audit
from research.forecast_engines.catalog import ENGINES
from research.forecast_engines.cli import _read_json
from research.forecast_engines.contracts import FeatureObservation, ForecastRequest
from research.forecast_engines.diagnostics import forecast_collision_map
from research.forecast_engines.engine import ForecastEngine
from research.forecast_engines.evaluation import (
    calibration_bins,
    directional_hit_rate,
    paired_loss_delta,
    probability_metrics,
    qlike,
    risk_ranking_auc,
)
from research.forecast_engines.horizon_overlap import horizon_overlap_audit
from research.forecast_engines.label_context import label_context_fingerprint
from research.forecast_engines.ledger import ForecastLedger
from research.forecast_engines.scorers import f_gap
from research.forecast_engines.source_clock import (
    RefreshObservation,
    estimate_source_refresh,
)
from research.forecast_engines.target_provenance import target_provenance_audit
from research.forecast_engines.target_contract import target_contract_fingerprint


def _feature_values(spec):
    result = {}
    for requirement in spec.inputs:
        if requirement.unit == "ratio":
            result[requirement.name] = 0.5
        elif requirement.unit == "signed_ratio":
            result[requirement.name] = 0.0
        elif requirement.unit == "beta":
            result[requirement.name] = 1.0
        elif requirement.unit == "days":
            result[requirement.name] = 3.0
        elif requirement.unit == "log_variance":
            result[requirement.name] = -10.0
        elif requirement.unit in {"return", "absolute_return"}:
            result[requirement.name] = 0.02
        else:
            result[requirement.name] = 0.0
    return result


def _valid_request(engine_id="FE01"):
    spec = next(item for item in ENGINES if item.engine_id == engine_id)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    published = now - timedelta(seconds=1)
    features = {
        name: FeatureObservation(
            value=value,
            unit=next(item.unit for item in spec.inputs if item.name == name),
            observed_at=published,
            available_at=published,
            ingested_at=published,
            source_id=f"test:{name}",
            source_hash="a" * 64,
            independence_group=f"test:{name}",
            rights_approved=True,
            quality=1.0,
        )
        for name, value in _feature_values(spec).items()
    }
    return ForecastRequest(spec.engine_id, "TEST", now, features)


class ForecastIntegrityTests(unittest.TestCase):
    def test_all_30_engines_emit_finite_strict_json_forecasts(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            for spec in ENGINES:
                with self.subTest(engine=spec.engine_id):
                    forecast = ForecastEngine().forecast(_valid_request(spec.engine_id))
                    self.assertEqual(forecast.status, "forecast")
                    json.dumps(forecast.to_dict(), allow_nan=False)
                    ledger.append_forecast(forecast)
            self.assertTrue(ledger.verify()["valid"])
            self.assertEqual(ledger.verify()["checked"], len(ENGINES))
            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(len(view["records"]), len(ENGINES))

    def test_wrong_feature_object_abstains_without_crashing(self):
        request = _valid_request()
        features = dict(request.features)
        features["ret_21d_z"] = 1  # type: ignore[assignment]
        forecast = ForecastEngine().forecast(replace(request, features=features))
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("invalid_observation:ret_21d_z", forecast.abstain_reasons)

    def test_boolean_observation_is_not_coerced_to_numeric_one(self):
        request = _valid_request()
        features = dict(request.features)
        features["ret_21d_z"] = replace(features["ret_21d_z"], value=True)  # type: ignore[arg-type]
        forecast = ForecastEngine().forecast(replace(request, features=features))
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("invalid_observation:ret_21d_z", forecast.abstain_reasons)

    def test_non_finite_observations_abstain_and_remain_strict_json(self):
        request = _valid_request()
        for field, bad_value in (
            ("value", float("nan")),
            ("quality", float("inf")),
            ("quality", 10 ** 10000),
        ):
            with self.subTest(field=field):
                features = dict(request.features)
                features["ret_21d_z"] = replace(features["ret_21d_z"], **{field: bad_value})
                forecast = ForecastEngine().forecast(replace(request, features=features))
                self.assertEqual(forecast.status, "abstain")
                json.dumps(forecast.to_dict(), allow_nan=False)

    def test_non_finite_scorer_output_becomes_safe_abstention(self):
        request = _valid_request("FE09")
        features = dict(request.features)
        for name in ("jump_intensity_z", "overnight_gap_z", "left_tail_asymmetry_z"):
            features[name] = replace(features[name], value=1.7e308)
        forecast = ForecastEngine().forecast(replace(request, features=features))
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("score_computation_failed", forecast.abstain_reasons)
        json.dumps(forecast.to_dict(), allow_nan=False)

    def test_gap_acceptance_changes_continuation_to_fade(self):
        common = {"gap_z": 2.0, "fair_gap_z": 0.0, "premarket_liquidity": 1.0}
        accepted = f_gap({**common, "open_acceptance": 1.0})
        rejected = f_gap({**common, "open_acceptance": 0.0})
        undecided = f_gap({**common, "open_acceptance": 0.5})
        self.assertGreater(accepted.value, 0.0)
        self.assertLess(rejected.value, 0.0)
        self.assertEqual(undecided.value, 0.0)

    def test_ledger_rejects_target_metadata_that_disagrees_with_registered_contract(self):
        forecast = ForecastEngine().forecast(_valid_request())
        self.assertEqual(forecast.status, "forecast")
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            with self.assertRaisesRegex(ValueError, "target metadata"):
                ledger.append_forecast(replace(forecast, target_unit="unrelated_unit"))

    def test_ledger_rejects_mismatched_model_fingerprint_and_version(self):
        forecast = ForecastEngine().forecast(_valid_request())
        bad_records = (
            replace(forecast, model_fingerprint="sha256:" + "b" * 64),
            replace(forecast, engine_version="spoofed-version"),
            replace(forecast, model_fingerprint=None),
        )
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            for bad_record in bad_records:
                with self.subTest(
                    model_fingerprint=bad_record.model_fingerprint,
                    engine_version=bad_record.engine_version,
                ):
                    with self.assertRaisesRegex(ValueError, "model fingerprint|engine version"):
                        ledger.append_forecast(bad_record)

            legacy_record = replace(
                forecast,
                model_fingerprint=None,
                target_contract_fingerprint=None,
                target_label_status=None,
            )
            ledger.append_forecast(legacy_record)

            corrupt_payload = forecast.to_dict()
            corrupt_payload["forecast_id"] = "malformed-model-identity"
            corrupt_payload["model_fingerprint"] = "not-a-digest"
            ledger._append("forecast", "malformed-model-identity", corrupt_payload)

            missing_identity_payload = forecast.to_dict()
            missing_identity_payload["forecast_id"] = "missing-bound-model-identity"
            missing_identity_payload["model_fingerprint"] = None
            ledger._append(
                "forecast", "missing-bound-model-identity", missing_identity_payload,
            )
            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(view["invalid_forecast_count"], 2)

    def test_ledger_requires_explicit_false_decision_eligibility(self):
        forecast = ForecastEngine().forecast(_valid_request())
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            for value in (None, 0, True):
                with self.subTest(decision_eligible=value):
                    with self.assertRaisesRegex(ValueError, "decision-eligible"):
                        ledger.append_forecast(replace(forecast, decision_eligible=value))  # type: ignore[arg-type]

    def test_ledger_rejects_uncalibrated_probability_claims(self):
        forecast = ForecastEngine().forecast(_valid_request())
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            with self.assertRaisesRegex(ValueError, "calibrated-probability"):
                ledger.append_forecast(replace(forecast, calibrated_probability=0.9))

    def test_future_as_of_request_is_recordable_as_an_abstention(self):
        request = replace(
            _valid_request(),
            as_of=datetime.now(timezone.utc) + timedelta(days=1),
        )
        forecast = ForecastEngine().forecast(request)
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("as_of_in_future", forecast.abstain_reasons)
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            ledger.append_forecast(forecast)
            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(view["invalid_forecast_count"], 0)
            self.assertEqual(view["records"][0]["status"], "abstain")

    def test_collision_map_rejects_emitted_forecast_without_score(self):
        forecast = ForecastEngine().forecast(_valid_request())
        with self.assertRaisesRegex(ValueError, "invalid emitted score"):
            forecast_collision_map([replace(forecast, forecast_value=None)])

    def test_collision_map_keeps_missing_contract_distinct_from_literal_fallback_text(self):
        forecast = ForecastEngine().forecast(_valid_request())
        missing = replace(
            forecast,
            forecast_id="missing-contract",
            target_contract_fingerprint=None,
            feature_manifest=(),
        )
        literal = replace(
            forecast,
            forecast_id="literal-fallback-contract",
            target_contract_fingerprint="unbound-target-contract",
            feature_manifest=(),
        )
        report = forecast_collision_map([missing, literal])
        self.assertEqual(report["panel_count"], 2)
        self.assertEqual(
            {panel["target_contract_fingerprint"] for panel in report["panels"]},
            {None, "unbound-target-contract"},
        )

    def test_collision_map_rejects_non_string_direction_without_crashing(self):
        forecast = ForecastEngine().forecast(_valid_request())
        with self.assertRaisesRegex(ValueError, "invalid direction"):
            forecast_collision_map([replace(forecast, direction=[])])  # type: ignore[arg-type]

    def test_cli_json_reader_rejects_duplicate_keys_and_nonstandard_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for contents, message in (
                ('{"features": {}, "features": {}}', "duplicate JSON object key"),
                ('{"value": NaN}', "non-standard JSON numeric constant"),
                ('{"value": Infinity}', "non-standard JSON numeric constant"),
            ):
                with self.subTest(contents=contents):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        _read_json(path)

    def test_collision_entropy_is_suppressed_for_duplicate_engine_records(self):
        forecast = ForecastEngine().forecast(_valid_request())
        shared = {
            "target": forecast.target,
            "target_unit": forecast.target_unit,
            "horizon": forecast.horizon,
            "forecast_unit": forecast.forecast_unit,
            "direction_semantics": forecast.direction_semantics,
            "feature_manifest": (),
        }
        rows = [
            replace(forecast, forecast_id="dup-positive-1", engine_id="FE01",
                    direction="POSITIVE_SCORE", **shared),
            replace(forecast, forecast_id="dup-positive-2", engine_id="FE01",
                    direction="POSITIVE_SCORE", **shared),
            replace(forecast, forecast_id="independent-negative", engine_id="FE02",
                    direction="NEGATIVE_SCORE", **shared),
        ]
        panel = forecast_collision_map(rows)["panels"][0]
        self.assertEqual(panel["duplicate_engine_ids"], ["FE01"])
        self.assertIsNone(panel["cross_cluster_score_orientation_entropy"])
        self.assertEqual(panel["aggregation_status"], "suppressed_duplicate_engine_records")

    def test_outcome_rights_flag_requires_explicit_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            now = datetime.now(timezone.utc)
            with self.assertRaisesRegex(ValueError, "explicit boolean"):
                ledger.append_outcome(
                    "missing-forecast", 0.0, "unit", now, now, now,
                    "test-source", "a" * 64, "false", True,
                )
            with self.assertRaisesRegex(ValueError, "not boolean or coercible string"):
                ledger.append_outcome(
                    "missing-forecast", "0.0", "unit", now, now, now,
                    "test-source", "a" * 64, True, True,
                )

    def test_numeric_diagnostics_reject_boolean_measurements(self):
        with self.assertRaisesRegex(ValueError, "actual labels"):
            probability_metrics([True], [0.5], calibrated=True)  # type: ignore[list-item]
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            qlike([True], [1.0])  # type: ignore[list-item]
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            directional_hit_rate([True], [1.0])  # type: ignore[list-item]

    def test_qlike_preserves_small_near_equal_variance_loss(self):
        actual = 1.0 + 1e-10
        loss = qlike([actual], [1.0])
        self.assertGreater(loss, 0.0)
        self.assertAlmostEqual(loss / 5e-21, 1.0, delta=2e-6)

    def test_paired_loss_mean_handles_maximum_finite_values(self):
        largest = float("1.7976931348623157e308")
        report = paired_loss_delta([largest] * 3, [0.0] * 3)
        self.assertEqual(report["mean_candidate_minus_baseline"], largest)

    def test_risk_ranking_auc_counts_ties_as_half_credit(self):
        self.assertEqual(risk_ranking_auc([1, 0, 1, 0], [1.0, 1.0, 1.0, 1.0]), 0.5)
        self.assertEqual(risk_ranking_auc([1, 1, 0, 0], [3.0, 4.0, 1.0, 2.0]), 1.0)
        self.assertEqual(risk_ranking_auc([1, 1, 0, 0], [1.0, 2.0, 3.0, 4.0]), 0.0)
        self.assertIsNone(risk_ranking_auc([1, 1], [0.1, 0.2]))

    def test_calibration_bins_storage_scales_with_populated_bins(self):
        rows = calibration_bins(
            [0, 1], [0.25, 0.75], bins=100_000_000, calibrated=True
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual([row["n"] for row in rows], [1.0, 1.0])
        boundary_rows = calibration_bins([0, 1], [0.7, 1.0], bins=10, calibrated=True)
        self.assertEqual([row["bin_low"] for row in boundary_rows], [0.7, 0.9])
        with self.assertRaisesRegex(ValueError, r"between 2 and 2\^53 bins"):
            calibration_bins([0], [0.5], bins=2**53 + 1, calibrated=True)

    def test_probability_metrics_require_literal_true_calibration_attestation(self):
        for attestation in (False, 1, "false", None):
            with self.subTest(attestation=attestation):
                with self.assertRaisesRegex(ValueError, "calibrated"):
                    probability_metrics([0, 1], [0.1, 0.9], calibrated=attestation)  # type: ignore[arg-type]
                with self.assertRaisesRegex(ValueError, "calibrated"):
                    calibration_bins([0, 1], [0.1, 0.9], calibrated=attestation)  # type: ignore[arg-type]

    def test_abstention_summary_means_stay_finite_for_large_valid_values(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(minutes=2)
        observed = as_of + timedelta(seconds=1)
        available = observed + timedelta(seconds=1)

        def record(forecast_id):
            outcome = {
                "forecast_id": forecast_id,
                "realized_value": 1e308,
                "realized_unit": "unit",
                "observed_at": observed.isoformat(),
                "available_at": available.isoformat(),
                "ingested_at": available.isoformat(),
                "source_id": "source",
                "source_hash": "b" * 64,
                "rights_approved": True,
                "horizon_complete": True,
                "evaluation_role": "forecast_skill",
                "target_contract_fingerprint": None,
                "target_contract_binding": "legacy_unbound",
                "target_window_id": None,
                "target_window_start_at": None,
                "target_window_end_at": None,
                "label_transform_id": None,
                "label_transform_hash": None,
                "label_context_fingerprint": None,
            }
            return {
                "forecast_id": forecast_id,
                "engine_id": "FE01",
                "model_fingerprint": None,
                "target_contract_fingerprint": None,
                "target": "target",
                "target_unit": "unit",
                "horizon": "1d",
                "status": "forecast",
                "as_of": as_of.isoformat(),
                "outcomes": [outcome],
            }

        report = abstention_coverage_audit(
            [record("first"), record("second"), record("third")],
            evaluation_as_of=now,
            tail_thresholds={},
        )
        summary = report["groups"][0]["forecasted_outcomes"]
        self.assertEqual(summary["mean_realized"], 1e308)
        self.assertEqual(summary["mean_absolute_realized"], 1e308)
        json.dumps(report, allow_nan=False)

    def test_abstention_audit_rejects_zero_length_legacy_target_windows(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(hours=3)
        endpoint = as_of + timedelta(hours=1)
        endpoint_text = endpoint.isoformat()
        row = {
            "forecast_id": "zero-window",
            "engine_id": "FE01",
            "model_fingerprint": None,
            "target_contract_fingerprint": None,
            "target": "target",
            "target_unit": "unit",
            "horizon": "1d",
            "target_window_id": "window",
            "target_window_start_at": endpoint_text,
            "target_window_end_at": endpoint_text,
            "status": "forecast",
            "as_of": as_of.isoformat(),
            "outcomes": [{
                "realized_value": 0.01,
                "realized_unit": "unit",
                "observed_at": endpoint_text,
                "available_at": endpoint_text,
                "ingested_at": endpoint_text,
                "source_id": "source",
                "source_hash": "c" * 64,
                "rights_approved": True,
                "horizon_complete": True,
                "evaluation_role": "forecast_skill",
                "target_contract_fingerprint": None,
                "target_contract_binding": "legacy_unbound",
                "target_window_id": "window",
                "target_window_start_at": endpoint_text,
                "target_window_end_at": endpoint_text,
            }],
        }
        report = abstention_coverage_audit(
            [row], evaluation_as_of=now, tail_thresholds={}
        )
        self.assertEqual(report["invalid_or_mismatched_outcome_count"], 1)

    def test_tail_threshold_units_are_normalized_and_duplicates_rejected(self):
        now = datetime.now(timezone.utc)
        row = {
            "forecast_id": "threshold-normalization",
            "engine_id": "FE01",
            "model_fingerprint": None,
            "target_contract_fingerprint": None,
            "target": "target",
            "target_unit": "unit",
            "horizon": "1d",
            "status": "forecast",
            "as_of": (now - timedelta(minutes=1)).isoformat(),
            "outcomes": [],
        }
        report = abstention_coverage_audit(
            [row], evaluation_as_of=now, tail_thresholds={" unit ": 1.0}
        )
        self.assertEqual(
            report["groups"][0]["forecasted_outcomes"]["tail_threshold"], 1.0
        )
        with self.assertRaisesRegex(ValueError, "duplicate target units"):
            abstention_coverage_audit(
                [], evaluation_as_of=now,
                tail_thresholds={"unit": 1.0, " unit ": 2.0},
            )

    def test_audit_reports_reject_malformed_status_and_group_identity(self):
        now = datetime.now(timezone.utc)
        invalid_status = {
            "forecast_id": "bad-status",
            "engine_id": "FE01",
            "target": "target",
            "target_unit": "unit",
            "horizon": "1d",
            "status": [],
            "outcomes": [],
        }
        with self.assertRaisesRegex(ValueError, "forecast status"):
            abstention_coverage_audit(
                [invalid_status], evaluation_as_of=now, tail_thresholds={}
            )
        with self.assertRaisesRegex(ValueError, "forecast status"):
            horizon_overlap_audit(
                [dict(invalid_status, symbol="SPY")], evaluation_as_of=now
            )
        with self.assertRaisesRegex(ValueError, "target identity"):
            target_provenance_audit([invalid_status], evaluation_as_of=now)

        invalid_group = dict(invalid_status, forecast_id="bad-group", status="abstain", engine_id=None)
        with self.assertRaisesRegex(ValueError, "grouping field engine_id"):
            abstention_coverage_audit(
                [invalid_group], evaluation_as_of=now, tail_thresholds={}
            )
        with self.assertRaisesRegex(ValueError, "grouping field engine_id"):
            horizon_overlap_audit(
                [dict(invalid_group, symbol="SPY")], evaluation_as_of=now
            )

    def test_horizon_overlap_normalizes_equivalent_timezone_cutoffs(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        utc_cutoff = now - timedelta(days=2)
        utc_text = utc_cutoff.isoformat().replace("+00:00", "Z")
        eastern_text = utc_cutoff.astimezone(timezone(timedelta(hours=-4))).isoformat()

        def record(forecast_id, symbol, as_of):
            observed = datetime.fromisoformat(as_of.replace("Z", "+00:00")) + timedelta(hours=1)
            observed_text = observed.isoformat()
            return {
                "forecast_id": forecast_id,
                "engine_id": "FE01",
                "model_fingerprint": None,
                "target_contract_fingerprint": None,
                "target": "return",
                "target_unit": "return",
                "horizon": "1d",
                "target_window_id": None,
                "label_transform_hash": None,
                "label_context_fingerprint": None,
                "status": "forecast",
                "symbol": symbol,
                "as_of": as_of,
                "outcomes": [{
                    "observed_at": observed_text,
                    "available_at": observed_text,
                    "ingested_at": observed_text,
                    "realized_value": 0.01,
                    "realized_unit": "return",
                    "source_id": "source",
                    "source_hash": "a" * 64,
                    "rights_approved": True,
                    "horizon_complete": True,
                    "evaluation_role": "forecast_skill",
                    "target_contract_fingerprint": None,
                    "target_contract_binding": "legacy_unbound",
                }],
            }

        report = horizon_overlap_audit(
            [record("utc", "AAA", utc_text), record("eastern", "BBB", eastern_text)],
            evaluation_as_of=now,
        )
        group = report["groups"][0]
        self.assertEqual(group["unique_labeled_cutoff_count"], 1)
        self.assertEqual(group["same_cutoff_cross_symbol_pair_count"], 1)

    def test_audit_reports_do_not_accept_non_string_source_ids(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(minutes=2)
        observed = as_of + timedelta(seconds=1)
        observed_text = observed.isoformat()
        outcome = {
            "observed_at": observed_text,
            "available_at": observed_text,
            "ingested_at": observed_text,
            "realized_value": 0.01,
            "realized_unit": "unit",
            "source_id": 123,
            "source_hash": "b" * 64,
            "rights_approved": True,
            "horizon_complete": True,
            "evaluation_role": "forecast_skill",
            "target_contract_fingerprint": None,
            "target_contract_binding": "legacy_unbound",
        }
        row = {
            "forecast_id": "bad-source-id",
            "engine_id": "FE01",
            "model_fingerprint": None,
            "target_contract_fingerprint": None,
            "target": "target",
            "target_unit": "unit",
            "horizon": "1d",
            "status": "forecast",
            "as_of": as_of.isoformat(),
            "outcomes": [outcome],
        }
        coverage = abstention_coverage_audit(
            [row], evaluation_as_of=now, tail_thresholds={}
        )
        overlap = horizon_overlap_audit(
            [dict(row, symbol="SPY")], evaluation_as_of=now
        )
        self.assertEqual(coverage["invalid_or_mismatched_outcome_count"], 1)
        self.assertEqual(overlap["invalid_label_count"], 1)

    def test_source_refresh_rejects_boolean_age(self):
        with self.assertRaisesRegex(ValueError, "age_seconds"):
            estimate_source_refresh(
                source_id="source",
                source_family="family",
                age_seconds=True,  # type: ignore[arg-type]
                horizon_seconds=60.0,
                as_of=datetime.now(timezone.utc),
                history=[],
            )

    def test_source_refresh_rejects_negative_label_before_horizon_matures(self):
        now = datetime.now(timezone.utc)
        row = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=600.0,
            refreshed_within_horizon=False,
            observation_cutoff_at=now - timedelta(seconds=300),
            first_refresh_at=None,
            label_available_at=now,
            source_hash="a" * 64,
            rights_approved=True,
        )
        with self.assertRaisesRegex(ValueError, "not horizon-complete"):
            estimate_source_refresh(
                source_id="source",
                source_family="family",
                age_seconds=120.0,
                horizon_seconds=600.0,
                as_of=now,
                history=[row],
            )

    def test_source_refresh_accepts_negative_label_maturing_before_later_refresh(self):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=10)
        row = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=60.0,
            refreshed_within_horizon=False,
            observation_cutoff_at=cutoff,
            first_refresh_at=cutoff + timedelta(seconds=120),
            label_available_at=cutoff + timedelta(seconds=60),
            source_hash="a" * 64,
            rights_approved=True,
        )
        report = estimate_source_refresh(
            source_id="source",
            source_family="family",
            age_seconds=120.0,
            horizon_seconds=60.0,
            as_of=now,
            history=[row],
            min_samples=2,
        )
        self.assertEqual(report["sample_count"], 1)
        self.assertEqual(report["label_not_yet_matured_count"], 0)

    def test_source_refresh_rejects_duplicate_trimmed_observation_ids(self):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=10)
        row = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=60.0,
            refreshed_within_horizon=False,
            observation_cutoff_at=cutoff,
            first_refresh_at=None,
            label_available_at=cutoff + timedelta(seconds=60),
            source_hash="a" * 64,
            rights_approved=True,
        )
        with self.assertRaisesRegex(ValueError, "duplicate historical observation_id"):
            estimate_source_refresh(
                source_id="source",
                source_family="family",
                age_seconds=120.0,
                horizon_seconds=60.0,
                as_of=now,
                history=[row, replace(row, observation_id=" row-1 ")],
                min_samples=2,
            )

    def test_source_refresh_rejects_horizons_below_timestamp_resolution(self):
        now = datetime.now(timezone.utc)
        row = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=0.0,
            horizon_seconds=1e-9,
            refreshed_within_horizon=False,
            observation_cutoff_at=now - timedelta(seconds=1),
            first_refresh_at=None,
            label_available_at=now,
            source_hash="a" * 64,
            rights_approved=True,
        )
        with self.assertRaisesRegex(ValueError, "invalid age/horizon"):
            estimate_source_refresh(
                source_id="source",
                source_family="family",
                age_seconds=0.0,
                horizon_seconds=1.0,
                as_of=now,
                history=[row],
            )

    def test_source_refresh_excludes_future_cutoffs_and_labels(self):
        now = datetime.now(timezone.utc)
        row = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=600.0,
            refreshed_within_horizon=False,
            observation_cutoff_at=now - timedelta(seconds=300),
            first_refresh_at=None,
            label_available_at=now + timedelta(seconds=301),
            source_hash="a" * 64,
            rights_approved=True,
        )
        report = estimate_source_refresh(
            source_id="source",
            source_family="family",
            age_seconds=120.0,
            horizon_seconds=600.0,
            as_of=now,
            history=[row],
        )
        self.assertEqual(report["sample_count"], 0)
        self.assertEqual(report["label_not_yet_matured_count"], 1)

    def test_source_refresh_history_fingerprint_binds_outcome_and_timing(self):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=1200)
        refreshed = RefreshObservation(
            observation_id="row-1",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=600.0,
            refreshed_within_horizon=True,
            observation_cutoff_at=cutoff,
            first_refresh_at=cutoff + timedelta(seconds=300),
            label_available_at=cutoff + timedelta(seconds=400),
            source_hash="a" * 64,
            rights_approved=True,
        )
        not_refreshed_in_window = replace(
            refreshed,
            refreshed_within_horizon=False,
            first_refresh_at=cutoff + timedelta(seconds=700),
            label_available_at=cutoff + timedelta(seconds=800),
        )
        common = dict(
            source_id="source",
            source_family="family",
            age_seconds=120.0,
            horizon_seconds=600.0,
            as_of=now,
            min_samples=2,
        )
        first = estimate_source_refresh(**common, history=[refreshed])
        second = estimate_source_refresh(**common, history=[not_refreshed_in_window])
        self.assertNotEqual(
            first["history_source_hash_fingerprint"],
            second["history_source_hash_fingerprint"],
        )

    def test_source_refresh_fingerprint_excludes_refreshes_after_evaluation_cutoff(self):
        now = datetime.now(timezone.utc)
        evaluation_cutoff = now - timedelta(minutes=5)
        observation_cutoff = now - timedelta(hours=1)
        matured_negative = RefreshObservation(
            observation_id="negative-row",
            source_id="source",
            source_family="family",
            age_seconds_at_cutoff=120.0,
            horizon_seconds=60.0,
            refreshed_within_horizon=False,
            observation_cutoff_at=observation_cutoff,
            first_refresh_at=None,
            label_available_at=observation_cutoff + timedelta(seconds=60),
            source_hash="c" * 64,
            rights_approved=True,
        )
        future_refresh = replace(
            matured_negative,
            first_refresh_at=evaluation_cutoff + timedelta(days=1),
        )
        common = dict(
            source_id="source",
            source_family="family",
            age_seconds=120.0,
            horizon_seconds=60.0,
            as_of=evaluation_cutoff,
            min_samples=2,
        )
        without_future_event = estimate_source_refresh(
            **common, history=[matured_negative]
        )
        with_future_event_in_retrospective_row = estimate_source_refresh(
            **common, history=[future_refresh]
        )
        self.assertEqual(
            without_future_event["history_source_hash_fingerprint"],
            with_future_event_in_retrospective_row["history_source_hash_fingerprint"],
        )

    def test_invalid_as_of_becomes_explicit_forecast_abstention(self):
        forecast = ForecastEngine().forecast(
            replace(_valid_request(), as_of=123)  # type: ignore[arg-type]
        )
        self.assertEqual(forecast.status, "abstain")
        self.assertIn("invalid_as_of", forecast.abstain_reasons)

    def test_ledger_verify_reports_malformed_json_as_integrity_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecast = ForecastEngine().forecast(_valid_request())
            ledger.append_forecast(forecast)
            db = sqlite3.connect(ledger.path)
            try:
                db.execute("DROP TRIGGER ledger_no_update")
                db.execute(
                    "UPDATE ledger_events SET payload_json=? WHERE event_id=?",
                    ("not-json", forecast.forecast_id),
                )
                db.commit()
            finally:
                db.close()
            integrity = ledger.verify()
            self.assertEqual(integrity["valid"], False)
            self.assertEqual(integrity["failed_seq"], 1)
            with self.assertRaisesRegex(ValueError, "hash chain is invalid at sequence 1"):
                ledger.coverage_records(datetime.now(timezone.utc))

    def test_ledger_refuses_to_append_after_hash_chain_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecast = ForecastEngine().forecast(_valid_request())
            ledger.append_forecast(forecast)
            db = sqlite3.connect(ledger.path)
            try:
                db.execute("DROP TRIGGER ledger_no_update")
                db.execute(
                    "UPDATE ledger_events SET payload_json=? WHERE event_id=?",
                    ("{}", forecast.forecast_id),
                )
                db.commit()
            finally:
                db.close()

            with self.assertRaisesRegex(ValueError, "cannot append.*invalid hash chain"):
                ledger.append_forecast(replace(forecast, forecast_id="after-tamper"))
            db = sqlite3.connect(ledger.path)
            try:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0], 1
                )
            finally:
                db.close()

    def test_boundary_map_rejects_stress_ranges_outside_input_domain(self):
        with self.assertRaisesRegex(ValueError, "registered input domain"):
            forecast_boundary_map(
                _valid_request(),
                {"trend_efficiency": {"low": 0.1, "high": 1.2, "unit": "ratio"}},
            )
        with self.assertRaisesRegex(ValueError, "range endpoints must be numeric"):
            forecast_boundary_map(
                _valid_request(),
                {"trend_efficiency": {"low": False, "high": 0.9, "unit": "ratio"}},
            )
        with self.assertRaisesRegex(ValueError, "low/high must be finite"):
            forecast_boundary_map(
                _valid_request(),
                {"ret_21d_z": {"low": -(10**10000), "high": 10**10000, "unit": "z"}},
            )

    def test_boundary_map_does_not_call_risk_rank_constant_direction_stable(self):
        report = forecast_boundary_map(
            _valid_request("FE09"),
            {"event_density": {"low": 0.1, "high": 0.9, "unit": "ratio"}},
        )
        self.assertEqual(
            report["stability"],
            "direction_not_applicable_for_non_directional_score",
        )

    def test_boundary_map_reports_abstention_for_non_string_symbol(self):
        request = replace(_valid_request(), symbol=None)  # type: ignore[arg-type]
        report = forecast_boundary_map(
            request,
            {"ret_21d_z": {"low": -1.0, "high": 1.0, "unit": "z"}},
        )
        self.assertEqual(report["status"], "unavailable_baseline_abstained")
        self.assertEqual(report["symbol"], "")

    def test_collision_map_separates_different_frozen_windows(self):
        forecast = ForecastEngine().forecast(_valid_request())
        start = datetime.fromisoformat(forecast.as_of)
        first = replace(
            forecast,
            forecast_id="first-window",
            target_window_id="5-session",
            target_window_start_at=start.isoformat(),
            target_window_end_at=(start + timedelta(days=5)).isoformat(),
        )
        second = replace(
            forecast,
            forecast_id="second-window",
            target_window_id="10-session",
            target_window_start_at=start.isoformat(),
            target_window_end_at=(start + timedelta(days=10)).isoformat(),
        )
        report = forecast_collision_map([first, second])
        self.assertEqual(report["panel_count"], 2)

    def test_collision_map_normalizes_equivalent_window_timestamps(self):
        forecast = ForecastEngine().forecast(_valid_request())
        start = datetime(2030, 1, 2, 14, 30, tzinfo=timezone.utc)
        end = start + timedelta(days=5)
        first = replace(
            forecast,
            forecast_id="utc-window",
            target_window_id="5-session",
            target_window_start_at=start.isoformat(),
            target_window_end_at=end.isoformat(),
        )
        offset = timezone(timedelta(hours=-5))
        second = replace(
            forecast,
            forecast_id="offset-window",
            target_window_id="5-session",
            target_window_start_at=start.astimezone(offset).isoformat(),
            target_window_end_at=end.astimezone(offset).isoformat(),
        )
        report = forecast_collision_map([first, second])
        self.assertEqual(report["panel_count"], 1)
        self.assertEqual(
            report["panels"][0]["target_window_start_at"], start.isoformat()
        )

    def test_collision_map_rejects_partial_and_nonpositive_windows(self):
        forecast = ForecastEngine().forecast(_valid_request())
        with self.assertRaisesRegex(ValueError, "incomplete target window"):
            forecast_collision_map([
                replace(forecast, target_window_id="5-session")
            ])
        start = datetime(2030, 1, 2, 14, 30, tzinfo=timezone.utc).isoformat()
        with self.assertRaisesRegex(ValueError, "non-positive target window"):
            forecast_collision_map([
                replace(
                    forecast,
                    target_window_id="5-session",
                    target_window_start_at=start,
                    target_window_end_at=start,
                )
            ])

    def test_target_provenance_invalid_contract_cannot_create_negative_subtotals(self):
        now = datetime.now(timezone.utc)
        record = {
            "forecast_id": "invalid-contract-provenance",
            "engine_id": "FE01",
            "target": "next_5_session_return",
            "target_unit": "return",
            "horizon": "5-session",
            "status": "forecast",
            "as_of": (now - timedelta(days=2)).isoformat(),
            "target_contract_fingerprint": "not-a-contract-hash",
            "target_window_id": "5-session",
            "target_window_start_at": (now - timedelta(days=1)).isoformat(),
            "target_window_end_at": (now + timedelta(days=4)).isoformat(),
            "label_transform_id": "label-v1",
            "label_transform_hash": "sha256:" + "a" * 64,
            "outcomes": [],
        }
        report = target_provenance_audit(
            [record], evaluation_as_of=now.isoformat()
        )
        group = report["groups"][0]
        self.assertEqual(report["invalid_record_count"], 1)
        self.assertEqual(group["bound_attempt_count"], 0)
        self.assertEqual(group["window_bound_attempt_count"], 0)
        self.assertEqual(group["label_transform_bound_attempt_count"], 0)
        self.assertEqual(report["unwindowed_bound_attempt_count"], 0)
        self.assertEqual(report["bound_without_frozen_label_transform_count"], 0)

    def test_target_provenance_missing_values_do_not_alias_display_sentinels(self):
        now = datetime.now(timezone.utc)
        base = {
            "engine_id": "FE01",
            "target": "next_5_session_return",
            "target_unit": "return",
            "horizon": "5-session",
            "status": "forecast",
            "as_of": (now - timedelta(days=2)).isoformat(),
            "outcomes": [],
        }
        legacy = dict(base, forecast_id="real-legacy-row")
        malformed = dict(
            base,
            forecast_id="malformed-sentinel-contract",
            target_contract_fingerprint="legacy-unbound",
        )
        report = target_provenance_audit(
            [legacy, malformed], evaluation_as_of=now.isoformat()
        )

        self.assertEqual(report["observed_contract_group_count"], 2)
        self.assertEqual(report["invalid_record_count"], 1)
        self.assertEqual(
            sum(group["legacy_unbound_attempt_count"] for group in report["groups"]), 1
        )
        self.assertEqual(
            {group["target_contract_fingerprint"] for group in report["groups"]},
            {None, "legacy-unbound"},
        )

    def test_scenario_only_contracts_are_excluded_from_missing_label_binding_totals(self):
        now = datetime.now(timezone.utc)
        spec = next(engine for engine in ENGINES if engine.engine_id == "FE15")
        record = {
            "forecast_id": "scenario-only-attempt",
            "engine_id": "FE15",
            "target_contract_fingerprint": target_contract_fingerprint("FE15"),
            "target": spec.target,
            "target_unit": spec.target_unit,
            "horizon": spec.horizon,
            "target_label_status": "scenario_only",
            "status": "forecast",
            "as_of": now.isoformat(),
            "outcomes": [],
        }
        report = target_provenance_audit(
            [record], evaluation_as_of=now.isoformat()
        )

        self.assertEqual(report["scenario_only_attempt_count"], 1)
        self.assertEqual(report["unwindowed_bound_attempt_count"], 0)
        self.assertEqual(report["bound_without_frozen_label_transform_count"], 0)
        self.assertEqual(report["bound_without_frozen_label_context_count"], 0)

    def test_target_provenance_checks_current_contract_identity_and_status(self):
        now = datetime.now(timezone.utc)
        spec = next(engine for engine in ENGINES if engine.engine_id == "FE01")
        base = {
            "engine_id": spec.engine_id,
            "target_contract_fingerprint": target_contract_fingerprint(spec.engine_id),
            "target_unit": spec.target_unit,
            "horizon": spec.horizon,
            "status": "forecast",
            "target_label_status": "labelable",
            "as_of": now.isoformat(),
            "outcomes": [],
        }
        wrong_target = dict(
            base, forecast_id="wrong-current-target", target=spec.target + "-wrong"
        )
        wrong_label_status = dict(
            base, forecast_id="wrong-current-label-status", target=spec.target,
            target_label_status="scenario_only",
        )
        report = target_provenance_audit(
            [wrong_target, wrong_label_status], evaluation_as_of=now.isoformat()
        )

        self.assertEqual(report["invalid_record_count"], 2)
        self.assertEqual(report["observed_contract_group_count"], 2)

    def test_target_provenance_keeps_literal_unbound_window_distinct(self):
        now = datetime.now(timezone.utc)
        spec = next(engine for engine in ENGINES if engine.engine_id == "FE01")
        base = {
            "engine_id": "FE01",
            "target_contract_fingerprint": target_contract_fingerprint("FE01"),
            "target": spec.target,
            "target_unit": spec.target_unit,
            "horizon": spec.horizon,
            "status": "forecast",
            "target_label_status": "labelable",
            "as_of": (now - timedelta(days=2)).isoformat(),
            "outcomes": [],
        }
        missing = dict(base, forecast_id="missing-window")
        literal = dict(base, forecast_id="literal-window", target_window_id="unbound-window")
        report = target_provenance_audit(
            [missing, literal], evaluation_as_of=now.isoformat()
        )

        self.assertEqual(report["observed_contract_group_count"], 2)
        self.assertEqual(
            {group["target_window_id"] for group in report["groups"]},
            {None, "unbound-window"},
        )

    def test_coverage_and_overlap_reports_do_not_merge_missing_window_with_literal(self):
        now = datetime.now(timezone.utc)
        base = {
            "engine_id": "FE01",
            "model_fingerprint": None,
            "target_contract_fingerprint": None,
            "target": "next_5_session_return",
            "target_unit": "return",
            "horizon": "5-session",
            "status": "forecast",
            "as_of": (now - timedelta(minutes=1)).isoformat(),
            "symbol": "SPY",
            "outcomes": [],
        }
        missing = dict(base, forecast_id="missing-window-report")
        literal = dict(
            base,
            forecast_id="literal-window-report",
            target_window_id="unbound-window",
        )
        coverage = abstention_coverage_audit(
            [missing, literal], evaluation_as_of=now.isoformat(), tail_thresholds={}
        )
        overlap = horizon_overlap_audit(
            [missing, literal], evaluation_as_of=now.isoformat()
        )

        self.assertEqual(len(coverage["groups"]), 2)
        self.assertEqual(len(overlap["groups"]), 2)
        self.assertEqual(
            {group["target_window_id"] for group in coverage["groups"]},
            {None, "unbound-window"},
        )
        self.assertEqual(
            {group["target_window_id"] for group in overlap["groups"]},
            {None, "unbound-window"},
        )

    def test_target_provenance_does_not_trim_invalid_frozen_bindings_into_valid_ones(self):
        now = datetime.now(timezone.utc)
        spec = next(engine for engine in ENGINES if engine.engine_id == "FE01")
        context = {
            "series_id": "SPY",
            "measurement_basis_id": "close_to_close",
            "calendar_id": "XNYS",
            "reference_series_id": "SPY",
            "vintage_policy_id": "as_published",
            "corporate_action_policy_id": "split_adjusted",
        }
        context_hash = label_context_fingerprint(context)
        record = {
            "forecast_id": "padded-binding",
            "engine_id": "FE01",
            "target_contract_fingerprint": target_contract_fingerprint("FE01"),
            "target": spec.target,
            "target_unit": spec.target_unit,
            "horizon": spec.horizon,
            "status": "forecast",
            "as_of": (now - timedelta(days=2)).isoformat(),
            "target_label_status": "labelable",
            "target_window_id": " 5-session ",
            "target_window_start_at": (now - timedelta(days=1)).isoformat(),
            "target_window_end_at": (now + timedelta(days=4)).isoformat(),
            "label_transform_id": "transform-v1",
            "label_transform_hash": "sha256:" + "d" * 64,
            "label_context": context,
            "label_context_fingerprint": " " + context_hash,
            "outcomes": [],
        }
        report = target_provenance_audit(
            [record], evaluation_as_of=now.isoformat()
        )
        group = report["groups"][0]

        self.assertEqual(group["target_window_id"], " 5-session ")
        self.assertEqual(group["window_bound_attempt_count"], 0)
        self.assertEqual(group["label_context_bound_attempt_count"], 0)
        self.assertEqual(report["unwindowed_bound_attempt_count"], 1)
        self.assertEqual(report["invalid_record_count"], 1)

    def test_label_audits_reject_non_hash_target_contracts(self):
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=2)
        end = now - timedelta(hours=1)
        context = {
            "series_id": "SPY",
            "measurement_basis_id": "close_to_close",
            "calendar_id": "XNYS",
            "reference_series_id": "SPY",
            "vintage_policy_id": "as_published",
            "corporate_action_policy_id": "split_adjusted",
        }
        context_hash = label_context_fingerprint(context)
        record = {
            "forecast_id": "malformed-contract-label",
            "engine_id": "FE01",
            "model_fingerprint": "a" * 64,
            "target_contract_fingerprint": "legacy-unbound-target",
            "target": "next_5_session_return",
            "target_unit": "return",
            "horizon": "5-session",
            "status": "forecast",
            "as_of": (start - timedelta(minutes=1)).isoformat(),
            "target_label_status": "labelable",
            "target_window_id": "5-session",
            "target_window_start_at": start.isoformat(),
            "target_window_end_at": end.isoformat(),
            "label_transform_id": "transform-v1",
            "label_transform_hash": "sha256:" + "b" * 64,
            "label_context": context,
            "label_context_fingerprint": context_hash,
            "symbol": "SPY",
            "outcomes": [{
                "realized_value": 0.01,
                "realized_unit": "return",
                "observed_at": end.isoformat(),
                "available_at": (end + timedelta(minutes=1)).isoformat(),
                "ingested_at": (end + timedelta(minutes=2)).isoformat(),
                "source_id": "test-source",
                "source_hash": "c" * 64,
                "rights_approved": True,
                "horizon_complete": True,
                "evaluation_role": "forecast_skill",
                "target_contract_fingerprint": "legacy-unbound-target",
                "target_contract_binding": "bound_attested",
                "target_window_id": "5-session",
                "target_window_start_at": start.isoformat(),
                "target_window_end_at": end.isoformat(),
                "label_transform_id": "transform-v1",
                "label_transform_hash": "b" * 64,
                "label_context_fingerprint": context_hash,
            }],
        }

        coverage = abstention_coverage_audit(
            [record], evaluation_as_of=now.isoformat(), tail_thresholds={}
        )
        overlap = horizon_overlap_audit([record], evaluation_as_of=now.isoformat())
        self.assertEqual(coverage["invalid_or_mismatched_outcome_count"], 1)
        self.assertEqual(overlap["invalid_label_count"], 1)
        self.assertEqual(overlap["groups"][0]["labeled_interval_count"], 0)

    def test_ledger_cutoff_excludes_forecasts_not_yet_written(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecast = ForecastEngine().forecast(_valid_request())
            now = datetime.now(timezone.utc)
            forecast = replace(
                forecast,
                as_of=(now - timedelta(minutes=2)).isoformat(),
                issued_at=(now - timedelta(minutes=1)).isoformat(),
            )
            cutoff = now - timedelta(seconds=30)
            ledger.append_forecast(forecast)
            view = ledger.coverage_records(cutoff)
            self.assertEqual(view["records"], [])
            self.assertEqual(view["not_yet_recorded_forecast_count"], 1)

    def test_ledger_cutoff_excludes_outcomes_not_yet_written(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecast = ForecastEngine().forecast(_valid_request())
            forecast = replace(
                forecast,
                target_contract_fingerprint=None,
                target_label_status=None,
                as_of=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            )
            ledger.append_forecast(forecast)
            cutoff = datetime.now(timezone.utc)
            observed = cutoff - timedelta(seconds=3)
            outcome = {
                "forecast_id": forecast.forecast_id,
                "realized_value": 0.01,
                "realized_unit": forecast.target_unit,
                "observed_at": observed.isoformat(),
                "available_at": (observed + timedelta(seconds=1)).isoformat(),
                "ingested_at": (observed + timedelta(seconds=2)).isoformat(),
                "source_id": "test-source",
                "source_hash": "a" * 64,
                "rights_approved": True,
                "horizon_complete": True,
                "evaluation_role": "forecast_skill",
                "target_contract_fingerprint": None,
                "target_contract_binding": "legacy_unbound",
                "target_window_id": None,
                "target_window_start_at": None,
                "target_window_end_at": None,
                "label_transform_id": None,
                "label_transform_hash": None,
                "label_context_fingerprint": None,
            }
            time.sleep(0.02)
            ledger._append(
                "outcome", f"outcome:{forecast.forecast_id}:late-write", outcome,
                unique_outcome_forecast_id=forecast.forecast_id,
            )
            view = ledger.coverage_records(cutoff)
            self.assertEqual(view["records"][0]["outcomes"], [])
            self.assertEqual(view["not_yet_recorded_outcome_count"], 1)

    def test_legacy_outcomes_cannot_add_windows_or_change_frozen_transforms(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(hours=4)
        base = ForecastEngine().forecast(_valid_request())
        frozen = replace(
            base,
            as_of=as_of.isoformat(),
            target_contract_fingerprint=None,
            target_label_status=None,
            target_window_id=None,
            target_window_start_at=None,
            target_window_end_at=None,
            label_transform_id="transform-v1",
            label_transform_hash="a" * 64,
            label_context=None,
            label_context_fingerprint=None,
        )
        observed = now - timedelta(minutes=1)
        available = observed + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            ledger.append_forecast(frozen)
            common = (
                frozen.forecast_id, 0.01, frozen.target_unit, observed, available,
                available + timedelta(seconds=1), "source", "b" * 64, True, True,
            )
            with self.assertRaisesRegex(ValueError, "cannot add a target window"):
                ledger.append_outcome(
                    *common,
                    target_window_id="invented-later",
                    target_window_start_at=observed - timedelta(minutes=5),
                    target_window_end_at=observed,
                    label_transform_id="transform-v1",
                    label_transform_hash="a" * 64,
                )
            with self.assertRaisesRegex(ValueError, "does not match the transform frozen"):
                ledger.append_outcome(
                    *common,
                    label_transform_id="transform-v2",
                    label_transform_hash="c" * 64,
                )
            ledger.append_outcome(
                *common,
                label_transform_id="transform-v1",
                label_transform_hash="a" * 64,
            )

            frozen_start = as_of + timedelta(hours=1)
            frozen_end = now - timedelta(minutes=2)
            window_forecast = replace(
                frozen,
                forecast_id="legacy-frozen-window",
                target_window_id="legacy-fixed-window",
                target_window_start_at=frozen_start.isoformat(),
                target_window_end_at=frozen_end.isoformat(),
            )
            ledger.append_forecast(window_forecast)
            window_available = frozen_end + timedelta(seconds=1)
            ledger.append_outcome(
                window_forecast.forecast_id,
                0.02,
                window_forecast.target_unit,
                frozen_end,
                window_available,
                window_available + timedelta(seconds=1),
                "source",
                "e" * 64,
                True,
                True,
                target_window_id="legacy-fixed-window",
                target_window_start_at=frozen_start,
                target_window_end_at=frozen_end,
                label_transform_id="transform-v1",
                label_transform_hash="a" * 64,
            )
            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(view["invalid_outcome_count"], 0)
            records = {row["forecast_id"]: row for row in view["records"]}
            self.assertEqual(len(records[frozen.forecast_id]["outcomes"]), 1)
            self.assertEqual(len(records[window_forecast.forecast_id]["outcomes"]), 1)

    def test_coverage_readback_rejects_legacy_window_and_transform_mismatches(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(hours=4)
        base = ForecastEngine().forecast(_valid_request())
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecasts = {}
            for forecast_id in ("bad-legacy-window", "bad-legacy-transform"):
                forecast = replace(
                    base,
                    forecast_id=forecast_id,
                    as_of=as_of.isoformat(),
                    target_contract_fingerprint=None,
                    target_label_status=None,
                    target_window_id=None,
                    target_window_start_at=None,
                    target_window_end_at=None,
                    label_transform_id="transform-v1",
                    label_transform_hash="a" * 64,
                    label_context=None,
                    label_context_fingerprint=None,
                )
                ledger.append_forecast(forecast)
                forecasts[forecast_id] = forecast

            observed = now - timedelta(minutes=2)
            available = observed + timedelta(seconds=1)
            base_payload = {
                "realized_value": 0.01,
                "realized_unit": base.target_unit,
                "observed_at": observed.isoformat(),
                "available_at": available.isoformat(),
                "ingested_at": available.isoformat(),
                "source_id": "source",
                "source_hash": "d" * 64,
                "rights_approved": True,
                "horizon_complete": True,
                "evaluation_role": "forecast_skill",
                "target_contract_fingerprint": None,
                "target_contract_binding": "legacy_unbound",
                "target_window_id": None,
                "target_window_start_at": None,
                "target_window_end_at": None,
                "label_transform_id": "transform-v1",
                "label_transform_hash": "a" * 64,
                "label_context_fingerprint": None,
            }
            for forecast_id, changes in (
                ("bad-legacy-window", {
                    "target_window_id": "invented-later",
                    "target_window_start_at": (observed - timedelta(minutes=5)).isoformat(),
                    "target_window_end_at": observed.isoformat(),
                }),
                ("bad-legacy-transform", {
                    "label_transform_id": "transform-v2",
                    "label_transform_hash": "c" * 64,
                }),
            ):
                payload = {
                    **base_payload,
                    "forecast_id": forecast_id,
                    **changes,
                }
                ledger._append(
                    "outcome",
                    f"outcome:{forecast_id}:malformed-binding",
                    payload,
                    unique_outcome_forecast_id=forecast_id,
                )

            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(view["invalid_outcome_count"], 2)
            self.assertEqual(view["invalid_target_window_outcome_count"], 1)
            self.assertEqual(view["invalid_label_transform_outcome_count"], 1)
            self.assertTrue(all(not row["outcomes"] for row in view["records"]))

            for forecast_id in forecasts:
                row = next(item for item in view["records"] if item["forecast_id"] == forecast_id)
                direct = dict(row, outcomes=[{
                    **base_payload,
                    "forecast_id": forecast_id,
                    **({
                        "target_window_id": "invented-later",
                        "target_window_start_at": (observed - timedelta(minutes=5)).isoformat(),
                        "target_window_end_at": observed.isoformat(),
                    } if forecast_id == "bad-legacy-window" else {
                        "label_transform_id": "transform-v2",
                        "label_transform_hash": "c" * 64,
                    }),
                }])
                provenance = target_provenance_audit(
                    [direct], evaluation_as_of=datetime.now(timezone.utc)
                )
                coverage = abstention_coverage_audit(
                    [direct], evaluation_as_of=datetime.now(timezone.utc), tail_thresholds={}
                )
                overlap = horizon_overlap_audit(
                    [direct], evaluation_as_of=datetime.now(timezone.utc)
                )
                self.assertEqual(provenance["invalid_record_count"], 1)
                self.assertEqual(coverage["invalid_or_mismatched_outcome_count"], 1)
                self.assertEqual(overlap["invalid_label_count"], 1)

    def test_ledger_and_target_provenance_reject_malformed_legacy_label(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            forecast = ForecastEngine().forecast(_valid_request())
            forecast = replace(
                forecast,
                target_contract_fingerprint=None,
                target_label_status=None,
                as_of=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            )
            ledger.append_forecast(forecast)
            observed = datetime.now(timezone.utc) - timedelta(seconds=3)
            malformed = {
                "forecast_id": forecast.forecast_id,
                "realized_value": "0.01",
                "realized_unit": "wrong-unit",
                "observed_at": observed.isoformat(),
                "available_at": (observed + timedelta(seconds=1)).isoformat(),
                "ingested_at": (observed + timedelta(seconds=2)).isoformat(),
                "source_id": "",
                "source_hash": "invalid",
                "rights_approved": False,
                "horizon_complete": False,
                "evaluation_role": "wrong-role",
                "target_contract_fingerprint": None,
                "target_contract_binding": "legacy_unbound",
                "target_window_id": None,
                "target_window_start_at": None,
                "target_window_end_at": None,
                "label_transform_id": None,
                "label_transform_hash": None,
                "label_context_fingerprint": None,
            }
            ledger._append(
                "outcome", f"outcome:{forecast.forecast_id}:malformed", malformed,
                unique_outcome_forecast_id=forecast.forecast_id,
            )
            view = ledger.coverage_records(datetime.now(timezone.utc))
            self.assertEqual(view["records"][0]["outcomes"], [])
            self.assertEqual(view["invalid_outcome_count"], 1)
            direct_record = dict(view["records"][0], outcomes=[malformed])
            provenance = target_provenance_audit(
                [direct_record], evaluation_as_of=datetime.now(timezone.utc).isoformat()
            )
            self.assertEqual(provenance["groups"][0]["labeled_outcome_count"], 0)
            self.assertEqual(provenance["invalid_record_count"], 1)
            valid_legacy = dict(
                malformed,
                realized_value=0.01,
                realized_unit=forecast.target_unit,
                source_id="test-source",
                source_hash="a" * 64,
                rights_approved=True,
                horizon_complete=True,
                evaluation_role="forecast_skill",
            )
            valid_provenance = target_provenance_audit(
                [dict(view["records"][0], outcomes=[valid_legacy])],
                evaluation_as_of=datetime.now(timezone.utc).isoformat(),
            )
            self.assertEqual(valid_provenance["groups"][0]["labeled_outcome_count"], 1)
            self.assertEqual(valid_provenance["invalid_record_count"], 0)

    def test_bound_label_round_trips_through_ledger_and_provenance_audit(self):
        now = datetime.now(timezone.utc)
        as_of = now - timedelta(minutes=1)
        source_at = as_of - timedelta(seconds=5)
        request = _valid_request("FE13")
        features = {
            name: replace(
                item,
                observed_at=source_at,
                available_at=source_at,
                ingested_at=source_at,
            )
            for name, item in request.features.items()
        }
        context = {
            "series_id": "TEST:SPY",
            "measurement_basis_id": "midquote-return",
            "calendar_id": "XNYS",
            "reference_series_id": "SPY",
            "vintage_policy_id": "first-published",
            "corporate_action_policy_id": "split-adjusted",
        }
        window_start = as_of + timedelta(seconds=1)
        window_end = window_start + timedelta(seconds=10)
        request = replace(
            request,
            as_of=as_of,
            features=features,
            target_window_id="10-second",
            target_window_start_at=window_start,
            target_window_end_at=window_end,
            label_transform_id="test-label-transform-v1",
            label_transform_hash="b" * 64,
            label_context=context,
        )
        forecast = ForecastEngine().forecast(request)
        self.assertEqual(forecast.status, "forecast")
        with tempfile.TemporaryDirectory() as directory:
            ledger = ForecastLedger(Path(directory) / "forecasts.sqlite")
            ledger.append_forecast(forecast)
            available = window_end + timedelta(seconds=1)
            ledger.append_outcome(
                forecast.forecast_id,
                0.001,
                forecast.target_unit,
                window_end,
                available,
                available + timedelta(seconds=1),
                "test-label-source",
                "c" * 64,
                True,
                True,
                target_contract_fingerprint=forecast.target_contract_fingerprint,
                target_window_id=forecast.target_window_id,
                target_window_start_at=forecast.target_window_start_at,
                target_window_end_at=forecast.target_window_end_at,
                label_transform_id=forecast.label_transform_id,
                label_transform_hash=forecast.label_transform_hash,
                label_context_fingerprint=forecast.label_context_fingerprint,
            )
            cutoff = datetime.now(timezone.utc)
            view = ledger.coverage_records(cutoff)
            self.assertEqual(view["invalid_outcome_count"], 0)
            self.assertEqual(len(view["records"][0]["outcomes"]), 1)
            provenance = target_provenance_audit(view["records"], evaluation_as_of=cutoff.isoformat())
            self.assertEqual(provenance["groups"][0]["labeled_outcome_count"], 1)
            self.assertEqual(provenance["invalid_record_count"], 0)
            historical_hash = "sha256:" + "f" * 64
            historical = dict(view["records"][0])
            historical["target_contract_fingerprint"] = historical_hash
            historical["outcomes"] = [
                dict(view["records"][0]["outcomes"][0], target_contract_fingerprint=historical_hash)
            ]
            historical_provenance = target_provenance_audit(
                [historical], evaluation_as_of=cutoff.isoformat()
            )
            self.assertFalse(historical_provenance["groups"][0]["current_contract_match"])
            self.assertEqual(historical_provenance["groups"][0]["labeled_outcome_count"], 1)


if __name__ == "__main__":
    unittest.main()
