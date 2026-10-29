"""Typed contracts for point-in-time forecast inputs and immutable outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Mapping
from uuid import uuid4


def parse_timestamp(value: datetime | str) -> datetime:
    """Return an aware UTC datetime; naive timestamps are rejected."""
    if isinstance(value, str):
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        value = datetime.fromisoformat(normalized)
    elif not isinstance(value, datetime):
        raise ValueError("timestamps must be ISO strings or datetime values")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FeatureObservation:
    value: float
    unit: str
    observed_at: datetime | str
    available_at: datetime | str
    ingested_at: datetime | str
    source_id: str
    source_hash: str
    independence_group: str
    rights_approved: bool
    quality: float
    evidence_kind: str = "observed"
    transform_id: str | None = None
    transform_hash: str | None = None

    def normalized(self) -> "FeatureObservation":
        if not isinstance(self.rights_approved, bool):
            raise ValueError("rights_approved must be an explicit boolean attestation")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("value must be a numeric observation, not a boolean or coercible string")
        if isinstance(self.quality, bool) or not isinstance(self.quality, (int, float)):
            raise ValueError("quality must be a numeric score, not a boolean or coercible string")
        if not isinstance(self.unit, str):
            raise ValueError("unit must be a string identifier")
        if not isinstance(self.source_id, str) or not isinstance(self.independence_group, str):
            raise ValueError("source_id and independence_group must be strings")
        if not isinstance(self.source_hash, str):
            raise ValueError("source_hash must be a SHA-256 string")
        if not isinstance(self.evidence_kind, str):
            raise ValueError("evidence_kind must be a string")
        if self.transform_id is not None and not isinstance(self.transform_id, str):
            raise ValueError("transform_id must be a string")
        if self.transform_hash is not None and not isinstance(self.transform_hash, str):
            raise ValueError("transform_hash must be a string")
        source_hash = self.source_hash.strip()
        if not re.fullmatch(r"(?:sha256:)?[a-fA-F0-9]{64}", source_hash):
            raise ValueError("source_hash must be a SHA-256 hex digest")
        transform_id = (self.transform_id or "").strip() or None
        transform_hash = (self.transform_hash or "").strip() or None
        if bool(transform_id) != bool(transform_hash):
            raise ValueError("transform_id and transform_hash must be supplied together")
        if transform_hash and not re.fullmatch(r"(?:sha256:)?[a-fA-F0-9]{64}", transform_hash):
            raise ValueError("transform_hash must be a SHA-256 hex digest")
        return FeatureObservation(
            value=float(self.value),
            unit=self.unit,
            observed_at=parse_timestamp(self.observed_at),
            available_at=parse_timestamp(self.available_at),
            ingested_at=parse_timestamp(self.ingested_at),
            source_id=self.source_id.strip(),
            source_hash=source_hash,
            independence_group=self.independence_group.strip(),
            rights_approved=self.rights_approved,
            quality=float(self.quality),
            evidence_kind=self.evidence_kind,
            transform_id=transform_id,
            transform_hash=transform_hash,
        )


@dataclass(frozen=True)
class ForecastRequest:
    engine_id: str
    symbol: str
    as_of: datetime | str
    features: Mapping[str, FeatureObservation]
    target_window_id: str | None = None
    target_window_start_at: datetime | str | None = None
    target_window_end_at: datetime | str | None = None
    label_transform_id: str | None = None
    label_transform_hash: str | None = None
    label_context: Mapping[str, str] | None = None


@dataclass(frozen=True)
class FeatureUse:
    name: str
    value: float | None
    unit: str | None
    source_id: str | None
    source_hash: str | None
    evidence_kind: str | None
    independence_group: str | None
    age_seconds: float | None
    quality: float | None
    available_age_seconds: float | None = None
    publication_lag_seconds: float | None = None
    transform_id: str | None = None
    transform_hash: str | None = None


@dataclass(frozen=True)
class Forecast:
    schema_version: str
    forecast_id: str
    engine_id: str
    engine_version: str
    maturity: str
    symbol: str
    issued_at: str
    as_of: str
    horizon: str
    target: str
    target_unit: str
    status: str
    forecast_value: float | None
    forecast_unit: str
    model_score: float | None
    direction: str
    input_quality_score: float | None
    independent_source_groups: int
    calibrated_probability: float | None
    decision_eligible: bool
    abstain_reasons: tuple[str, ...] = field(default_factory=tuple)
    drivers: Mapping[str, float] = field(default_factory=dict)
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    kill_conditions: tuple[str, ...] = field(default_factory=tuple)
    feature_manifest: tuple[FeatureUse, ...] = field(default_factory=tuple)
    declared_source_group_concentration: float | None = None
    effective_declared_source_groups: float | None = None
    model_fingerprint: str | None = None
    target_contract_fingerprint: str | None = None
    target_label_status: str | None = None
    target_window_id: str | None = None
    target_window_start_at: str | None = None
    target_window_end_at: str | None = None
    label_transform_id: str | None = None
    label_transform_hash: str | None = None
    label_context: Mapping[str, str] | None = None
    label_context_fingerprint: str | None = None
    direction_semantics: str = "legacy_direction_label"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["abstain_reasons"] = list(self.abstain_reasons)
        result["assumptions"] = list(self.assumptions)
        result["kill_conditions"] = list(self.kill_conditions)
        result["feature_manifest"] = [asdict(item) for item in self.feature_manifest]
        return result


def new_forecast_id() -> str:
    return str(uuid4())
