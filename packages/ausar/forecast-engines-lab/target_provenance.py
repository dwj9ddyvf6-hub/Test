"""Inventory target definitions and audit label-transform provenance."""

from __future__ import annotations

from datetime import datetime, timezone
import re
import math
from typing import Any, Mapping, Sequence

from .catalog import ENGINES
from .contracts import parse_timestamp
from .label_context import label_context_binding_is_valid
from .target_contract import (
    target_contract_fingerprint,
    target_contract_payload,
    target_label_contract,
)


def target_contract_inventory() -> list[dict[str, Any]]:
    """Return the 30 frozen target definitions with independent semantic hashes."""
    return [
        {
            **target_contract_payload(spec.engine_id),
            "target_contract_fingerprint": target_contract_fingerprint(spec.engine_id),
        }
        for spec in ENGINES
    ]


def target_provenance_audit(
    records: Sequence[Mapping[str, Any]],
    *,
    evaluation_as_of: str,
) -> dict[str, Any]:
    """Report contract binding and label-transform versions without scoring labels."""
    cutoff = parse_timestamp(evaluation_as_of)
    if cutoff > datetime.now(timezone.utc):
        raise ValueError("evaluation cutoff cannot be in the future")

    groups: dict[tuple[str | None, ...], dict[str, Any]] = {}
    seen_ids: set[str] = set()
    invalid_record_count = 0
    for record in records:
        forecast_id = record.get("forecast_id")
        if not isinstance(forecast_id, str) or not forecast_id.strip():
            raise ValueError("every forecast attempt requires a forecast_id")
        if forecast_id in seen_ids:
            raise ValueError(f"duplicate forecast_id in target provenance input: {forecast_id}")
        seen_ids.add(forecast_id)
        engine_id = record.get("engine_id")
        target = record.get("target")
        target_unit = record.get("target_unit")
        horizon = record.get("horizon")
        raw_identity = (engine_id, target, target_unit, horizon)
        status = record.get("status")
        target_label_status = record.get("target_label_status")
        raw_window_id = record.get("target_window_id")
        raw_context_fingerprint = record.get("label_context_fingerprint")
        if raw_window_id is not None and (
            not isinstance(raw_window_id, str) or not raw_window_id.strip()
        ):
            raise ValueError(f"target window ID for {forecast_id} must be non-empty text when supplied")
        if raw_context_fingerprint is not None and (
            not isinstance(raw_context_fingerprint, str) or not raw_context_fingerprint.strip()
        ):
            raise ValueError(f"label context fingerprint for {forecast_id} must be non-empty text when supplied")
        window_id = raw_window_id if isinstance(raw_window_id, str) else None
        context_fingerprint = (
            raw_context_fingerprint
            if isinstance(raw_context_fingerprint, str) else None
        )
        frozen_contract = record.get("target_contract_fingerprint")
        if frozen_contract is not None and not isinstance(frozen_contract, str):
            raise ValueError(f"target contract fingerprint for {forecast_id} must be a string")
        contract_hash_valid = (
            frozen_contract is None
            or re.fullmatch(r"sha256:[a-fA-F0-9]{64}", frozen_contract) is not None
        )
        contract_is_current = False
        if (
            not all(isinstance(value, str) and value.strip()
                    for value in (engine_id, target, target_unit, horizon))
            or not isinstance(status, str)
            or status not in {"forecast", "abstain"}
        ):
            raise ValueError(f"forecast {forecast_id} is missing target identity fields")
        engine_id = engine_id.strip()
        target = target.strip()
        target_unit = target_unit.strip()
        horizon = horizon.strip()
        key = (engine_id, frozen_contract, target, target_unit, horizon, window_id, context_fingerprint)
        group = groups.setdefault(key, {
            "engine_id": engine_id,
            "target_contract_fingerprint": frozen_contract,
            "target": target,
            "target_unit": target_unit,
            "horizon": horizon,
            "target_window_id": window_id,
            "label_context_fingerprint": context_fingerprint,
            "attempt_count": 0,
            "bound_attempt_count": 0,
            "legacy_unbound_attempt_count": 0,
            "window_bound_attempt_count": 0,
            "label_transform_bound_attempt_count": 0,
            "label_context_bound_attempt_count": 0,
            "scenario_only_attempt_count": 0,
            "current_contract_match": None,
            "labeled_outcome_count": 0,
            "missing_outcome_count": 0,
            "label_transform_versions": {},
        })
        group["attempt_count"] += 1
        if frozen_contract is None:
            group["legacy_unbound_attempt_count"] += 1
        else:
            if not contract_hash_valid:
                invalid_record_count += 1
            else:
                group["bound_attempt_count"] += 1
            try:
                current = target_contract_fingerprint(engine_id)
            except KeyError:
                current = None
            group["current_contract_match"] = frozen_contract == current if current else False
            contract_is_current = bool(current and frozen_contract == current)
            try:
                label_contract = target_label_contract(engine_id)
            except KeyError:
                label_contract = {"allowed_window_ids": []}
            current_identity_valid = True
            if contract_hash_valid:
                if target_label_status not in {"labelable", "scenario_only"}:
                    invalid_record_count += 1
                elif contract_is_current:
                    current_contract = target_contract_payload(engine_id)
                    current_identity_valid = not (
                        raw_identity != (
                            current_contract["engine_id"],
                            current_contract["target"],
                            current_contract["target_unit"],
                            current_contract["horizon"],
                        )
                        or target_label_status != label_contract["status"]
                    )
                    if not current_identity_valid:
                        invalid_record_count += 1
                if (
                    target_label_status == "scenario_only"
                    and current_identity_valid
                ):
                    group["scenario_only_attempt_count"] += 1
                if target_label_status == "scenario_only" and any(
                    record.get(field) is not None
                    for field in (
                        "target_window_id", "target_window_start_at", "target_window_end_at",
                        "label_transform_id", "label_transform_hash", "label_context",
                        "label_context_fingerprint",
                    )
                ):
                    invalid_record_count += 1
            if (
                contract_hash_valid
                and target_label_status == "labelable"
                and (window_id in label_contract["allowed_window_ids"] if contract_is_current
                     else window_id is not None)
                and record.get("target_window_start_at")
                and record.get("target_window_end_at")
            ):
                try:
                    start = parse_timestamp(record["target_window_start_at"])
                    end = parse_timestamp(record["target_window_end_at"])
                    cutoff_at = parse_timestamp(record["as_of"])
                    if cutoff_at <= start < end:
                        group["window_bound_attempt_count"] += 1
                except (KeyError, TypeError, ValueError):
                    pass
            expected_transform_id = record.get("label_transform_id")
            expected_transform_hash = record.get("label_transform_hash")
            if (
                contract_hash_valid
                and target_label_status == "labelable"
                and isinstance(expected_transform_id, str) and expected_transform_id.strip()
                and isinstance(expected_transform_hash, str)
                and re.fullmatch(r"sha256:[a-fA-F0-9]{64}", expected_transform_hash)
            ):
                group["label_transform_bound_attempt_count"] += 1
            if (
                contract_hash_valid
                and target_label_status == "labelable"
                and label_context_binding_is_valid(
                    record.get("label_context"), context_fingerprint
                )
            ):
                group["label_context_bound_attempt_count"] += 1
            elif (
                contract_hash_valid
                and target_label_status == "labelable"
                and context_fingerprint is not None
            ):
                invalid_record_count += 1

        outcomes = record.get("outcomes", [])
        if not isinstance(outcomes, list) or len(outcomes) > 1:
            invalid_record_count += 1
            continue
        if not outcomes:
            group["missing_outcome_count"] += 1
            continue
        outcome = outcomes[0]
        if not isinstance(outcome, Mapping):
            invalid_record_count += 1
            continue
        realized_raw = outcome.get("realized_value")
        if isinstance(realized_raw, bool) or not isinstance(realized_raw, (int, float)):
            invalid_record_count += 1
            continue
        try:
            realized_value = float(realized_raw)
            forecast_as_of = parse_timestamp(record["as_of"])
            observed_at = parse_timestamp(outcome["observed_at"])
            available_at = parse_timestamp(outcome["available_at"])
            ingested_at = parse_timestamp(outcome["ingested_at"])
        except (KeyError, TypeError, ValueError, OverflowError):
            invalid_record_count += 1
            continue
        source_hash = outcome.get("source_hash")
        source_digest = (
            source_hash.removeprefix("sha256:")
            if isinstance(source_hash, str) else ""
        )
        expected_role = "forecast_skill" if status == "forecast" else "abstention_audit"
        if (
            not math.isfinite(realized_value)
            or outcome.get("realized_unit") != target_unit
            or outcome.get("rights_approved") is not True
            or outcome.get("horizon_complete") is not True
            or outcome.get("evaluation_role") != expected_role
            or not isinstance(outcome.get("source_id"), str)
            or not outcome["source_id"].strip()
            or re.fullmatch(r"[a-fA-F0-9]{64}", source_digest) is None
            or not forecast_as_of < observed_at <= available_at <= ingested_at <= cutoff
        ):
            invalid_record_count += 1
            continue
        if outcome.get("target_contract_fingerprint") != record.get("target_contract_fingerprint"):
            invalid_record_count += 1
            continue
        transform_id = outcome.get("label_transform_id")
        transform_hash = outcome.get("label_transform_hash")
        if frozen_contract is None:
            if outcome.get("target_contract_binding") != "legacy_unbound":
                invalid_record_count += 1
                continue
            frozen_transform_id = record.get("label_transform_id")
            frozen_transform_raw = record.get("label_transform_hash")
            if frozen_transform_id is not None or frozen_transform_raw is not None:
                frozen_transform_hash = (
                    frozen_transform_raw.removeprefix("sha256:")
                    if isinstance(frozen_transform_raw, str) else ""
                )
                outcome_transform_hash = (
                    transform_hash.removeprefix("sha256:")
                    if isinstance(transform_hash, str) else ""
                )
                if (
                    not isinstance(frozen_transform_id, str)
                    or not frozen_transform_id.strip()
                    or re.fullmatch(r"[a-fA-F0-9]{64}", frozen_transform_hash) is None
                    or transform_id != frozen_transform_id.strip()
                    or outcome_transform_hash.lower() != frozen_transform_hash.lower()
                ):
                    invalid_record_count += 1
                    continue
        else:
            if not contract_hash_valid:
                continue
            if record.get("target_label_status") != "labelable":
                invalid_record_count += 1
                continue
            if outcome.get("target_contract_binding") != "bound_attested":
                invalid_record_count += 1
                continue
            if not isinstance(transform_id, str) or not transform_id.strip():
                invalid_record_count += 1
                continue
            if not isinstance(transform_hash, str) or not re.fullmatch(
                r"(?:sha256:)?[a-fA-F0-9]{64}", transform_hash
            ):
                invalid_record_count += 1
                continue
            try:
                window_start = parse_timestamp(record["target_window_start_at"])
                window_end = parse_timestamp(record["target_window_end_at"])
                outcome_start = parse_timestamp(outcome["target_window_start_at"])
                outcome_end = parse_timestamp(outcome["target_window_end_at"])
            except (KeyError, TypeError, ValueError):
                invalid_record_count += 1
                continue
            try:
                allowed_windows = (
                    target_label_contract(engine_id)["allowed_window_ids"]
                    if contract_is_current else None
                )
            except KeyError:
                allowed_windows = None
            if (
                not record.get("target_window_id")
                or (allowed_windows is not None
                    and record.get("target_window_id") not in allowed_windows)
                or not forecast_as_of <= window_start < window_end
                or outcome_start != window_start
                or outcome_end != window_end
                or observed_at != window_end
                or transform_id != record.get("label_transform_id")
                or "sha256:" + transform_hash.removeprefix("sha256:").lower()
                != record.get("label_transform_hash")
                or outcome.get("target_window_id") != record.get("target_window_id")
                or outcome.get("label_context_fingerprint") != record.get("label_context_fingerprint")
                or not label_context_binding_is_valid(
                    record.get("label_context"), record.get("label_context_fingerprint")
                )
            ):
                invalid_record_count += 1
                continue
        if frozen_contract is None:
            window_fields = (
                record.get("target_window_id"), record.get("target_window_start_at"),
                record.get("target_window_end_at"), outcome.get("target_window_id"),
                outcome.get("target_window_start_at"), outcome.get("target_window_end_at"),
            )
            if any(value is not None for value in window_fields):
                try:
                    start = parse_timestamp(record["target_window_start_at"])
                    end = parse_timestamp(record["target_window_end_at"])
                    outcome_start = parse_timestamp(outcome["target_window_start_at"])
                    outcome_end = parse_timestamp(outcome["target_window_end_at"])
                except (KeyError, TypeError, ValueError):
                    invalid_record_count += 1
                    continue
                if (
                    not record.get("target_window_id")
                    or record.get("target_window_id") != outcome.get("target_window_id")
                    or not forecast_as_of <= start < end
                    or outcome_start != start
                    or outcome_end != end
                    or observed_at != end
                ):
                    invalid_record_count += 1
                    continue
        group["labeled_outcome_count"] += 1
        if transform_hash:
            normalized_hash = str(transform_hash).removeprefix("sha256:").lower()
            versions = group["label_transform_versions"]
            version = versions.setdefault(normalized_hash, {"label_transform_id": transform_id, "outcome_count": 0})
            version["outcome_count"] += 1

    reports: list[dict[str, Any]] = []
    sort_key = lambda item: tuple((value is not None, value or "") for value in item[0])
    for _, group in sorted(groups.items(), key=sort_key):
        versions = group.pop("label_transform_versions")
        group["label_transform_versions"] = [
            {"label_transform_hash": digest, **version}
            for digest, version in sorted(versions.items())
        ]
        group["multiple_label_transform_versions"] = len(versions) > 1
        group["pooling_requires_transform_review"] = len(versions) > 1
        reports.append(group)

    return {
        "schema_version": "2.0",
        "status": "research_diagnostic",
        "decision_eligible": False,
        "evaluation_as_of": cutoff.isoformat(),
        "registered_target_contract_count": len(ENGINES),
        "target_contract_inventory": target_contract_inventory(),
        "observed_contract_group_count": len(reports),
        "attempt_count": len(seen_ids),
        "unwindowed_bound_attempt_count": sum(
            max(
                0,
                group["bound_attempt_count"]
                - group["scenario_only_attempt_count"]
                - group["window_bound_attempt_count"],
            )
            for group in reports
        ),
        "bound_without_frozen_label_transform_count": sum(
            max(
                0,
                group["bound_attempt_count"]
                - group["scenario_only_attempt_count"]
                - group["label_transform_bound_attempt_count"],
            )
            for group in reports
        ),
        "bound_without_frozen_label_context_count": sum(
            max(
                0,
                group["bound_attempt_count"]
                - group["scenario_only_attempt_count"]
                - group["label_context_bound_attempt_count"],
            )
            for group in reports
        ),
        "scenario_only_attempt_count": sum(group["scenario_only_attempt_count"] for group in reports),
        "invalid_record_count": invalid_record_count,
        "groups": reports,
        "interpretation": (
            "Target-contract hashes pin target semantics. Label-context fingerprints pin the "
            "series, measurement basis, calendar, reference series, data-vintage policy, and "
            "corporate-action policy for a forecast instance. Label-transform hashes identify "
            "caller-attested code versions; none proves the source data are correct or that code "
            "produced the supplied value. Legacy records remain explicitly unbound. Keep "
            "different context and transform versions separate unless equivalence is established."
        ),
    }
