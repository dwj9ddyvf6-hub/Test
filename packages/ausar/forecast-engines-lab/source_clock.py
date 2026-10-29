"""Point-in-time empirical hazard for a source observation being refreshed."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import re
from typing import Sequence

from .contracts import parse_timestamp


_AGE_RATIO_UPPER_BOUNDS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
_SHA256 = re.compile(r"(?:sha256:)?[a-fA-F0-9]{64}\Z")
_DATETIME_RESOLUTION_SECONDS = 1e-6


def _finite_numeric(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class RefreshObservation:
    """One historical cutoff with a time-verifiable source-refresh label."""

    observation_id: str
    source_id: str
    source_family: str
    age_seconds_at_cutoff: float
    horizon_seconds: float
    refreshed_within_horizon: bool
    observation_cutoff_at: datetime | str
    first_refresh_at: datetime | str | None
    label_available_at: datetime | str
    source_hash: str
    rights_approved: bool


def _age_ratio_band(age_seconds: float, horizon_seconds: float) -> str:
    ratio = age_seconds / horizon_seconds
    for upper in _AGE_RATIO_UPPER_BOUNDS:
        if ratio <= upper:
            return f"<= {upper:g}x horizon"
    return "> 8x horizon"


def _wilson_interval(successes: int, sample_count: int, z: float = 1.96) -> tuple[float, float]:
    if sample_count <= 0:
        return 0.0, 1.0
    proportion = successes / sample_count
    denominator = 1.0 + z * z / sample_count
    center = (proportion + z * z / (2.0 * sample_count)) / denominator
    radius = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / sample_count
            + z * z / (4.0 * sample_count * sample_count)
        )
        / denominator
    )
    return max(0.0, center - radius), min(1.0, center + radius)


def estimate_source_refresh(
    *,
    source_id: str,
    source_family: str,
    age_seconds: float,
    horizon_seconds: float,
    as_of: datetime | str,
    history: Sequence[RefreshObservation],
    min_samples: int = 30,
) -> dict[str, object]:
    """Estimate whether comparable source data usually refreshes before horizon.

    A row is eligible only when its observation cutoff and label are available
    by as_of, and its label timing agrees with the declared horizon. Positive
    labels require a recorded first refresh inside the horizon; negative labels
    require proof that the complete horizon elapsed without one. The response
    is an empirical source-freshness diagnostic, never a calibrated market
    forecast or a substitute for the feature's own timestamp gate.
    """
    cutoff = parse_timestamp(as_of)
    if cutoff > datetime.now(timezone.utc):
        raise ValueError("as_of cannot be in the future")
    if (not isinstance(source_id, str) or not source_id.strip()
            or not isinstance(source_family, str) or not source_family.strip()):
        raise ValueError("source_id and source_family are required")
    if not _finite_numeric(age_seconds) or age_seconds < 0:
        raise ValueError("age_seconds must be finite and non-negative")
    if not _finite_numeric(horizon_seconds) or horizon_seconds <= 0:
        raise ValueError("horizon_seconds must be finite and positive")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 2:
        raise ValueError("min_samples must be at least 2")

    seen_ids: set[str] = set()
    eligible: list[RefreshObservation] = []
    rights_rejected = 0
    not_yet_matured = 0
    for row in history:
        if not isinstance(row, RefreshObservation):
            raise ValueError("history rows must be RefreshObservation records")
        if not isinstance(row.observation_id, str) or not row.observation_id.strip():
            raise ValueError("historical observation_id is required")
        normalized_observation_id = row.observation_id.strip()
        if (not isinstance(row.source_id, str) or not row.source_id.strip()
                or not isinstance(row.source_family, str) or not row.source_family.strip()):
            raise ValueError(f"source_id and source_family are required for {row.observation_id}")
        if normalized_observation_id in seen_ids:
            raise ValueError(f"duplicate historical observation_id: {normalized_observation_id}")
        seen_ids.add(normalized_observation_id)
        if not isinstance(row.rights_approved, bool):
            raise ValueError("rights_approved must be an explicit boolean")
        if not isinstance(row.source_hash, str) or not _SHA256.fullmatch(row.source_hash.strip()):
            raise ValueError(f"invalid source_hash for {row.observation_id}")
        if not isinstance(row.refreshed_within_horizon, bool):
            raise ValueError("refreshed_within_horizon must be a boolean label")
        if (
            not _finite_numeric(row.age_seconds_at_cutoff)
            or row.age_seconds_at_cutoff < 0
            or not _finite_numeric(row.horizon_seconds)
            or row.horizon_seconds < _DATETIME_RESOLUTION_SECONDS
        ):
            raise ValueError(f"invalid age/horizon for {row.observation_id}")
        try:
            observation_cutoff = parse_timestamp(row.observation_cutoff_at)
            horizon_end = observation_cutoff + timedelta(seconds=float(row.horizon_seconds))
            label_available_at = parse_timestamp(row.label_available_at)
            first_refresh_at = (
                parse_timestamp(row.first_refresh_at)
                if row.first_refresh_at is not None else None
            )
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid timestamp or horizon for {row.observation_id}") from exc
        if label_available_at < observation_cutoff:
            raise ValueError(f"label became available before its cutoff for {row.observation_id}")
        if first_refresh_at is not None:
            if first_refresh_at <= observation_cutoff:
                raise ValueError(f"invalid first-refresh timing for {row.observation_id}")
        if row.refreshed_within_horizon:
            if (
                first_refresh_at is None
                or first_refresh_at > horizon_end
                or label_available_at < first_refresh_at
            ):
                raise ValueError(f"positive refresh label is outside its horizon for {row.observation_id}")
        elif (
            (first_refresh_at is not None and first_refresh_at <= horizon_end)
            or label_available_at < horizon_end
        ):
            raise ValueError(f"negative refresh label is not horizon-complete for {row.observation_id}")
        if observation_cutoff > cutoff or label_available_at > cutoff:
            not_yet_matured += 1
            continue
        if not row.rights_approved:
            rights_rejected += 1
            continue
        eligible.append(row)

    current_band = _age_ratio_band(age_seconds, horizon_seconds)
    same_band = [
        row for row in eligible
        if _age_ratio_band(row.age_seconds_at_cutoff, row.horizon_seconds) == current_band
    ]
    exact_source = [row for row in same_band if row.source_id.strip().casefold() == source_id.strip().casefold()]
    if len(exact_source) >= min_samples:
        sample = exact_source
        pool_level = "source_id"
    else:
        family_pool = [
            row for row in same_band
            if row.source_family.strip().casefold() == source_family.strip().casefold()
        ]
        if len(family_pool) >= min_samples:
            sample = family_pool
            pool_level = "source_family"
        else:
            sample = family_pool if len(family_pool) >= len(exact_source) else exact_source
            pool_level = "insufficient_history"

    successes = sum(row.refreshed_within_horizon for row in sample)
    sample_count = len(sample)
    def first_refresh_known_at_cutoff(row: RefreshObservation) -> str | None:
        if row.first_refresh_at is None:
            return None
        first_refresh = parse_timestamp(row.first_refresh_at)
        return first_refresh.isoformat() if first_refresh <= cutoff else None

    sample_manifest = [
        {
            "observation_id": row.observation_id.strip(),
            "source_id": row.source_id.strip().casefold(),
            "source_family": row.source_family.strip().casefold(),
            "age_seconds_at_cutoff": float(row.age_seconds_at_cutoff),
            "horizon_seconds": float(row.horizon_seconds),
            "refreshed_within_horizon": row.refreshed_within_horizon,
            "observation_cutoff_at": parse_timestamp(row.observation_cutoff_at).isoformat(),
            "first_refresh_at": first_refresh_known_at_cutoff(row),
            "label_available_at": parse_timestamp(row.label_available_at).isoformat(),
            "source_hash": row.source_hash.strip().lower().removeprefix("sha256:"),
            "rights_approved": row.rights_approved,
        }
        for row in sorted(sample, key=lambda item: item.observation_id.strip())
    ]
    canonical_manifest = json.dumps(
        sample_manifest, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    fingerprint = hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest()
    estimate = (successes + 1.0) / (sample_count + 2.0) if sample_count >= min_samples else None
    lower, upper = _wilson_interval(successes, sample_count)
    return {
        "schema_version": "1.1",
        "status": "empirical_estimate" if estimate is not None else "insufficient_history",
        "estimate_kind": "smoothed_refresh_frequency_not_calibrated",
        "decision_eligible": False,
        "source_id": source_id.strip(),
        "source_family": source_family.strip(),
        "age_seconds": age_seconds,
        "horizon_seconds": horizon_seconds,
        "age_ratio_band": current_band,
        "pool_level": pool_level,
        "sample_count": sample_count,
        "refresh_count": successes,
        "smoothing_prior_alpha_beta": [1.0, 1.0],
        "estimated_refresh_probability": estimate,
        "wilson_95_interval": [lower, upper] if sample_count else None,
        "rights_rejected_count": rights_rejected,
        "label_not_yet_matured_count": not_yet_matured,
        "history_source_hash_fingerprint": fingerprint if sample_count else None,
        "as_of": cutoff.isoformat(),
        "interpretation": (
            "This estimates how often comparable observations were refreshed before "
            "the specified horizon. It does not estimate price direction, forecast "
            "error, or market alpha. Insufficient history returns no probability."
        ),
    }


def refresh_observation_from_dict(raw: dict[str, object]) -> RefreshObservation:
    """Construct a typed history row from a decoded JSON object."""
    allowed = {field for field in RefreshObservation.__dataclass_fields__}
    extras = set(raw) - allowed
    missing = allowed - set(raw)
    if extras or missing:
        raise ValueError(f"invalid refresh row fields: missing={sorted(missing)}, extra={sorted(extras)}")
    return RefreshObservation(**raw)  # type: ignore[arg-type]


def refresh_observation_to_dict(row: RefreshObservation) -> dict[str, object]:
    """Serialize one refresh history row with timestamps in ISO form."""
    result = asdict(row)
    for name in ("observation_cutoff_at", "first_refresh_at", "label_available_at"):
        value = getattr(row, name)
        if isinstance(value, datetime):
            result[name] = value.isoformat()
    return result
