"""Measure what forecast attempts exclude when the engine abstains."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from math import fsum, isfinite
import re
from typing import Any, Mapping, Sequence

from .contracts import parse_timestamp
from .label_context import label_context_binding_is_valid


def _group_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"forecast grouping field {field} must be a non-empty string")
    return value.strip()


def _optional_group_text(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"forecast grouping field {field} must be non-empty text when supplied")
    return value


def _stable_mean(values: Sequence[float]) -> float:
    """Average finite values without overflowing on a representable mean."""
    if not values:
        raise ValueError("cannot average an empty sequence")
    scale = max(abs(value) for value in values)
    if scale == 0:
        return 0.0
    normalized_mean = fsum(value / scale for value in values) / len(values)
    return scale * max(-1.0, min(1.0, normalized_mean))


def abstention_coverage_audit(
    records: Sequence[Mapping[str, Any]],
    *,
    evaluation_as_of: str,
    tail_thresholds: Mapping[str, float],
) -> dict[str, Any]:
    """Compare labeled outcomes for emitted forecasts and abstained attempts.

    ``records`` should come from ``ForecastLedger.coverage_records`` so all
    labels are cutoff-filtered and the event hash chain has been verified.
    Tail thresholds are caller-supplied in each target's own unit.
    """
    cutoff = parse_timestamp(evaluation_as_of)
    if cutoff > datetime.now(timezone.utc):
        raise ValueError("evaluation cutoff cannot be in the future")
    thresholds: dict[str, float] = {}
    for unit, value in tail_thresholds.items():
        if (not isinstance(unit, str) or not unit.strip()
                or isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError("tail thresholds require a target unit and positive finite value")
        try:
            threshold = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("tail thresholds require a target unit and positive finite value") from exc
        if not isfinite(threshold) or threshold <= 0.0:
            raise ValueError("tail thresholds require a target unit and positive finite value")
        normalized_unit = unit.strip()
        if normalized_unit in thresholds:
            raise ValueError("tail thresholds contain duplicate target units after normalization")
        thresholds[normalized_unit] = threshold

    groups: dict[tuple[str | None, ...], list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    bad_outcome_count = 0
    ambiguous_outcome_count = 0
    missing_outcome_count = 0
    for record in records:
        forecast_id = record.get("forecast_id")
        if not isinstance(forecast_id, str) or not forecast_id.strip():
            raise ValueError("every forecast attempt requires a forecast_id")
        if forecast_id in seen_ids:
            raise ValueError(f"duplicate forecast_id in coverage records: {forecast_id}")
        seen_ids.add(forecast_id)
        status = record.get("status")
        if not isinstance(status, str) or status not in {"forecast", "abstain"}:
            raise ValueError(f"unknown forecast status for {forecast_id}: {status!r}")
        group_key = (
            _group_text(record, "engine_id"),
            _optional_group_text(record, "model_fingerprint"),
            _optional_group_text(record, "target_contract_fingerprint"),
            _group_text(record, "target"),
            _group_text(record, "target_unit"),
            _group_text(record, "horizon"),
            _optional_group_text(record, "target_window_id"),
            _optional_group_text(record, "label_transform_hash"),
            _optional_group_text(record, "label_context_fingerprint"),
        )
        outcomes = record.get("outcomes", [])
        if not isinstance(outcomes, list):
            raise ValueError(f"outcomes for {forecast_id} must be a list")
        raw_reasons = record.get("abstain_reasons", ())
        if raw_reasons is None:
            raw_reasons = ()
        if (not isinstance(raw_reasons, (list, tuple))
                or any(not isinstance(reason, str) or not reason.strip() for reason in raw_reasons)):
            raise ValueError(f"abstain_reasons for {forecast_id} must be a list of non-empty strings")
        parsed_outcome: dict[str, Any] | None = None
        if len(outcomes) > 1:
            ambiguous_outcome_count += 1
        elif not outcomes:
            missing_outcome_count += 1
        elif not isinstance(outcomes[0], Mapping):
            bad_outcome_count += 1
        else:
            outcome = outcomes[0]
            expected_role = "forecast_skill" if status == "forecast" else "abstention_audit"
            try:
                observed_at = parse_timestamp(outcome["observed_at"])
                available_at = parse_timestamp(outcome["available_at"])
                ingested_at = parse_timestamp(outcome["ingested_at"])
                forecast_as_of = parse_timestamp(record["as_of"])
                realized_raw = outcome["realized_value"]
                if isinstance(realized_raw, bool) or not isinstance(realized_raw, (int, float)):
                    raise ValueError("realized outcome must be numeric")
                realized = float(realized_raw)
            except (TypeError, ValueError, OverflowError, KeyError):
                valid = False
            else:
                source_hash = str(outcome.get("source_hash") or "").removeprefix("sha256:")
                target_contract = record.get("target_contract_fingerprint")
                transform_hash = str(outcome.get("label_transform_hash") or "").removeprefix("sha256:")
                transform_id = outcome.get("label_transform_id")
                contract_bound = (re.fullmatch(r"sha256:[a-fA-F0-9]{64}", target_contract) is not None) and (
                    outcome.get("target_contract_fingerprint") == target_contract
                    and outcome.get("target_contract_binding") == "bound_attested"
                    and isinstance(transform_id, str) and bool(transform_id.strip())
                    and re.fullmatch(r"[a-fA-F0-9]{64}", transform_hash) is not None
                    and transform_id == record.get("label_transform_id")
                    and "sha256:" + transform_hash.lower() == record.get("label_transform_hash")
                    and outcome.get("label_context_fingerprint") == record.get("label_context_fingerprint")
                    and isinstance(record.get("label_context_fingerprint"), str)
                    and re.fullmatch(r"sha256:[a-fA-F0-9]{64}", record["label_context_fingerprint"]) is not None
                    and label_context_binding_is_valid(
                        record.get("label_context"), record.get("label_context_fingerprint")
                    )
                ) if target_contract is not None else (
                    outcome.get("target_contract_fingerprint") is None
                    and outcome.get("target_contract_binding", "legacy_unbound") == "legacy_unbound"
                )
                if target_contract is None and (
                    record.get("label_transform_id") is not None
                    or record.get("label_transform_hash") is not None
                ):
                    frozen_transform_id = record.get("label_transform_id")
                    frozen_transform_hash = str(record.get("label_transform_hash") or "").removeprefix("sha256:")
                    outcome_transform_hash = str(outcome.get("label_transform_hash") or "").removeprefix("sha256:")
                    contract_bound = contract_bound and (
                        isinstance(frozen_transform_id, str)
                        and bool(frozen_transform_id.strip())
                        and re.fullmatch(r"[a-fA-F0-9]{64}", frozen_transform_hash) is not None
                        and outcome.get("label_transform_id") == frozen_transform_id.strip()
                        and outcome_transform_hash.lower() == frozen_transform_hash.lower()
                    )
                if target_contract is not None:
                    try:
                        frozen_start = parse_timestamp(record["target_window_start_at"])
                        outcome_start = parse_timestamp(outcome["target_window_start_at"])
                        frozen_end = parse_timestamp(record["target_window_end_at"])
                        outcome_end = parse_timestamp(outcome["target_window_end_at"])
                        window_bound = (
                            record.get("target_label_status") == "labelable"
                            and bool(record.get("target_window_id"))
                            and outcome.get("target_window_id") == record.get("target_window_id")
                            and forecast_as_of <= frozen_start < frozen_end
                            and frozen_start == outcome_start
                            and frozen_end == outcome_end == observed_at
                        )
                    except (KeyError, TypeError, ValueError):
                        window_bound = False
                else:
                    window_fields = (
                        record.get("target_window_id"), record.get("target_window_start_at"),
                        record.get("target_window_end_at"), outcome.get("target_window_id"),
                        outcome.get("target_window_start_at"), outcome.get("target_window_end_at"),
                    )
                    if all(value is None for value in window_fields):
                        window_bound = True
                    else:
                        try:
                            legacy_start = parse_timestamp(record["target_window_start_at"])
                            legacy_end = parse_timestamp(record["target_window_end_at"])
                            window_bound = (
                                bool(record.get("target_window_id"))
                                and record.get("target_window_id") == outcome.get("target_window_id")
                                and forecast_as_of <= legacy_start < legacy_end
                                and legacy_start == parse_timestamp(outcome["target_window_start_at"])
                                and legacy_end == parse_timestamp(outcome["target_window_end_at"]) == observed_at
                            )
                        except (KeyError, TypeError, ValueError):
                            window_bound = False
                valid = (
                    outcome.get("evaluation_role") == expected_role
                    and outcome.get("rights_approved") is True
                    and outcome.get("horizon_complete") is True
                    and outcome.get("realized_unit") == group_key[4]
                    and isinstance(outcome.get("source_id"), str)
                    and bool(outcome["source_id"].strip())
                    and re.fullmatch(r"[a-fA-F0-9]{64}", source_hash) is not None
                    and contract_bound
                    and window_bound
                    and forecast_as_of < observed_at <= available_at <= ingested_at <= cutoff
                    and isfinite(realized)
                )
            if valid:
                parsed_outcome = {
                    "value": realized,
                    "available_at": available_at,
                    "ingested_at": ingested_at,
                    "label_transform_hash": transform_hash or None,
                }
            else:
                bad_outcome_count += 1
        groups[group_key].append({
            "forecast_id": forecast_id,
            "status": status,
            "outcome": parsed_outcome,
            "abstain_reasons": tuple(raw_reasons),
        })

    reports: list[dict[str, Any]] = []
    sort_key = lambda item: tuple((value is not None, value or "") for value in item[0])
    for key, rows in sorted(groups.items(), key=sort_key):
        engine_id, fingerprint, target_contract, target, target_unit, horizon, window_id, transform_fingerprint, context_fingerprint = key
        attempts_answered = [row for row in rows if row["status"] == "forecast"]
        attempts_abstained = [row for row in rows if row["status"] == "abstain"]
        labeled_answered = [row["outcome"]["value"] for row in attempts_answered if row["outcome"] is not None]
        labeled_abstained = [row["outcome"]["value"] for row in attempts_abstained if row["outcome"] is not None]
        total_attempts = len(rows)
        total_labeled = len(labeled_answered) + len(labeled_abstained)
        threshold = thresholds.get(target_unit)

        def outcome_summary(values: list[float]) -> dict[str, Any]:
            count = len(values)
            result: dict[str, Any] = {
                "labeled_count": count,
                "mean_realized": _stable_mean(values) if count else None,
                "mean_absolute_realized": (
                    _stable_mean([abs(value) for value in values]) if count else None
                ),
            }
            if threshold is not None:
                tail_count = sum(abs(value) >= threshold for value in values)
                result.update({
                    "tail_threshold": threshold,
                    "tail_count": tail_count,
                    "tail_rate": tail_count / len(values) if values else None,
                })
            return result

        answered_summary = outcome_summary(labeled_answered)
        abstained_summary = outcome_summary(labeled_abstained)
        if threshold is not None and labeled_answered and labeled_abstained:
            tail_rate_delta = abstained_summary["tail_rate"] - answered_summary["tail_rate"]
        else:
            tail_rate_delta = None

        reason_rows: dict[str, list[float]] = defaultdict(list)
        for row in attempts_abstained:
            if row["outcome"] is None:
                continue
            reasons = row["abstain_reasons"] or ("unclassified_abstention",)
            for reason in reasons:
                reason_rows[str(reason)].append(row["outcome"]["value"])
        reason_profiles = []
        for reason, values in sorted(reason_rows.items()):
            item = {"reason": reason, **outcome_summary(values)}
            reason_profiles.append(item)

        transform_versions = sorted({
            row["outcome"]["label_transform_hash"]
            for row in rows
            if row["outcome"] is not None and row["outcome"]["label_transform_hash"]
        })

        reports.append({
            "engine_id": engine_id,
            "model_fingerprint": fingerprint if fingerprint is not None else "legacy-unfingerprinted",
            "target_contract_fingerprint": target_contract,
            "target_window_id": window_id,
            "label_transform_hash": transform_fingerprint,
            "label_context_fingerprint": context_fingerprint,
            "target": target,
            "target_unit": target_unit,
            "horizon": horizon,
            "attempt_count": total_attempts,
            "forecast_attempt_count": len(attempts_answered),
            "abstention_attempt_count": len(attempts_abstained),
            "attempt_coverage": len(attempts_answered) / total_attempts if total_attempts else None,
            "labeled_attempt_count": total_labeled,
            "label_coverage": total_labeled / total_attempts if total_attempts else None,
            "selective_coverage_on_labeled_attempts": (
                len(labeled_answered) / total_labeled if total_labeled else None
            ),
            "forecasted_outcomes": answered_summary,
            "abstained_outcomes": abstained_summary,
            "abstention_minus_forecast_tail_rate": tail_rate_delta,
            "abstention_reason_outcomes": reason_profiles,
            "label_transform_hashes": transform_versions,
            "multiple_label_transform_versions": len(transform_versions) > 1,
        })

    return {
        "schema_version": "1.1",
        "status": "research_diagnostic",
        "decision_eligible": False,
        "evaluation_as_of": cutoff.isoformat(),
        "attempt_count": len(seen_ids),
        "engine_model_group_count": len(reports),
        "missing_outcome_count": missing_outcome_count,
        "ambiguous_outcome_count": ambiguous_outcome_count,
        "invalid_or_mismatched_outcome_count": bad_outcome_count,
        "groups": reports,
        "interpretation": (
            "Positive abstention-minus-forecast tail rate means labeled abstentions contained "
            "more threshold-sized absolute outcomes in this sample. It does not establish that "
            "the forecast predicted those outcomes or that abstention improved returns. Counts "
            "are descriptive; outcomes are not probability forecasts and no p-values are emitted."
        ),
    }
