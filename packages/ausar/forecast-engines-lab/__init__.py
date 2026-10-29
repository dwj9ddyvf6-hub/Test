"""Point-in-time, research-only forecast engine lab.

This package emits forecasts and abstentions. It has no broker, OMS, or order API.
"""

from .abstention_audit import abstention_coverage_audit
from .catalog import ENGINES, get_engine
from .contracts import FeatureObservation, Forecast, ForecastRequest
from .diagnostics import forecast_collision_map
from .edge_cards import EDGE_CARDS, EdgeCard, get_edge_card
from .engine import ForecastEngine
from .horizon_overlap import horizon_overlap_audit
from .label_context import (
    LABEL_CONTEXT_FIELDS,
    LABEL_CONTEXT_SCHEMA,
    label_context_binding_is_valid,
    label_context_fingerprint,
    normalize_label_context,
)
from .source_clock import RefreshObservation, estimate_source_refresh
from .target_contract import (
    target_contract_fingerprint,
    target_contract_payload,
    target_label_contract,
)
from .target_provenance import target_contract_inventory, target_provenance_audit

__all__ = [
    "ENGINES",
    "EDGE_CARDS",
    "EdgeCard",
    "abstention_coverage_audit",
    "FeatureObservation",
    "Forecast",
    "ForecastEngine",
    "ForecastRequest",
    "RefreshObservation",
    "estimate_source_refresh",
    "forecast_collision_map",
    "get_edge_card",
    "get_engine",
    "horizon_overlap_audit",
    "LABEL_CONTEXT_FIELDS",
    "LABEL_CONTEXT_SCHEMA",
    "label_context_binding_is_valid",
    "label_context_fingerprint",
    "normalize_label_context",
    "target_contract_fingerprint",
    "target_contract_inventory",
    "target_contract_payload",
    "target_label_contract",
    "target_provenance_audit",
]
