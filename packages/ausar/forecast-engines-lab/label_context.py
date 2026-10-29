"""Canonical instance-level conventions for constructing forecast outcomes."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping


LABEL_CONTEXT_SCHEMA = "forecast-label-context-v1"
LABEL_CONTEXT_FIELDS = (
    "series_id",
    "measurement_basis_id",
    "calendar_id",
    "reference_series_id",
    "vintage_policy_id",
    "corporate_action_policy_id",
)
_NOT_APPLICABLE = {"none", "not_applicable"}
_UNKNOWN = {"", "unknown", "tbd", "todo", "na", "n/a", "null"}
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@=-]{0,191}$")


def normalize_label_context(raw: Mapping[str, Any]) -> dict[str, str]:
    """Validate a complete, explicit measurement context without interpreting IDs.

    Identifiers are intentionally caller-defined so vendor, venue, calendar and
    corporate-action policies can be represented without hard-coding providers.
    Use the literal ``not_applicable`` only when a dimension truly does not
    apply; empty, unknown and placeholder values are rejected.
    """
    if not isinstance(raw, Mapping):
        raise ValueError("label_context must be an object of stable identifiers")
    supplied = set(raw)
    expected = set(LABEL_CONTEXT_FIELDS)
    if supplied != expected:
        raise ValueError(
            "label_context fields must match the registered schema exactly; "
            f"missing={sorted(expected - supplied)}, extra={sorted(supplied - expected)}"
        )
    normalized: dict[str, str] = {}
    for field in LABEL_CONTEXT_FIELDS:
        value = raw[field]
        if not isinstance(value, str):
            raise ValueError(f"label_context.{field} must be a string identifier")
        value = value.strip()
        if value.casefold() in _UNKNOWN or not _TOKEN.fullmatch(value):
            raise ValueError(f"label_context.{field} must be a stable, non-placeholder identifier")
        if value.casefold() in _NOT_APPLICABLE:
            value = value.casefold()
        normalized[field] = value
    for field in ("series_id", "measurement_basis_id", "calendar_id", "vintage_policy_id"):
        if normalized[field] in _NOT_APPLICABLE:
            raise ValueError(f"label_context.{field} cannot be not_applicable")
    return normalized


def label_context_fingerprint(raw: Mapping[str, Any]) -> str:
    """Hash normalized instance conventions using stable canonical JSON."""
    normalized = normalize_label_context(raw)
    canonical = json.dumps(
        {"schema": LABEL_CONTEXT_SCHEMA, **normalized},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def label_context_binding_is_valid(raw: Mapping[str, Any] | None, fingerprint: str | None) -> bool:
    """Check that a serialized context and its digest agree exactly."""
    if not isinstance(raw, Mapping) or not isinstance(fingerprint, str):
        return False
    try:
        return label_context_fingerprint(raw) == fingerprint
    except (TypeError, ValueError):
        return False
