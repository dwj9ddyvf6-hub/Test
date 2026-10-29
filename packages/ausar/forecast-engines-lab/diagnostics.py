"""Research-only tools for forecast dependency and disagreement audits."""

from __future__ import annotations

from collections import Counter, defaultdict
from math import isfinite, log
from statistics import median
from typing import Sequence

from .contracts import Forecast, parse_timestamp
from .label_context import label_context_binding_is_valid


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        return False


def _lineage_tokens(forecast: Forecast) -> dict[str, set[str]]:
    tokens: dict[str, set[str]] = {
        "exact_hash": set(),
        "source_id": set(),
        "declared_group": set(),
        "transform_id": set(),
        "transform_hash": set(),
    }
    for feature in forecast.feature_manifest:
        if feature.value is None:
            continue
        if feature.source_hash:
            tokens["exact_hash"].add(feature.source_hash.lower().removeprefix("sha256:"))
        if feature.source_id:
            tokens["source_id"].add(feature.source_id.strip().casefold())
        if feature.independence_group:
            tokens["declared_group"].add(feature.independence_group.strip().casefold())
        if feature.transform_id:
            tokens["transform_id"].add(feature.transform_id.strip().casefold())
        if feature.transform_hash:
            tokens["transform_hash"].add(feature.transform_hash.strip().lower().removeprefix("sha256:"))
    return tokens


def _score_orientation_category(direction: str) -> str:
    if direction in {"POSITIVE_SCORE", "UP", "ELEVATED_RISK"}:
        return "positive_score"
    if direction in {"NEGATIVE_SCORE", "DOWN", "LOWER_RISK"}:
        return "negative_score"
    if direction in {"ZERO_SCORE", "NEUTRAL", "INDETERMINATE"}:
        return "neutral_score"
    return "unknown"


def _cluster_score_orientation(rows: Sequence[Forecast]) -> str:
    votes = Counter(_score_orientation_category(row.direction) for row in rows)
    informative = {key: count for key, count in votes.items() if key != "unknown"}
    if not informative:
        return "unknown"
    highest = max(informative.values())
    winners = [key for key, count in informative.items() if count == highest]
    return winners[0] if len(winners) == 1 else "mixed"


def forecast_collision_map(forecasts: Sequence[Forecast]) -> dict[str, object]:
    """Partition comparable forecasts and expose evidence overlap and conflict.

    Forecasts with different targets, units, horizons, symbols, or cutoffs are
    never averaged together. Overlap clusters are conservative dependency
    warnings, not estimates of statistical correlation or independence.
    """
    forecast_ids = [forecast.forecast_id for forecast in forecasts]
    if any(not isinstance(forecast_id, str) or not forecast_id.strip() for forecast_id in forecast_ids):
        raise ValueError("forecast_id values must be non-empty strings")
    if len(forecast_ids) != len(set(forecast_ids)):
        raise ValueError("forecast_id values must be unique across the input")
    panels: dict[tuple[object, ...], list[Forecast]] = defaultdict(list)
    for forecast in forecasts:
        if forecast.decision_eligible is not False:
            raise ValueError("research collision map refuses decision-eligible records")
        if not isinstance(forecast.status, str) or forecast.status not in {"forecast", "abstain"}:
            raise ValueError(f"forecast {forecast.forecast_id} has an unknown status")
        if forecast.status == "forecast":
            if not _finite_number(forecast.forecast_value) or not _finite_number(forecast.model_score):
                raise ValueError(f"forecast {forecast.forecast_id} has an invalid emitted score")
        elif (forecast.forecast_value is not None or forecast.model_score is not None
              or forecast.direction != "ABSTAIN"):
            raise ValueError(f"abstention {forecast.forecast_id} carries a score or direction")
        for field_name in (
            "engine_id", "symbol", "target", "target_unit", "horizon",
            "forecast_unit", "direction_semantics", "direction",
        ):
            value = getattr(forecast, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"forecast {forecast.forecast_id} has an invalid {field_name}")
        if forecast.label_context is not None and not label_context_binding_is_valid(
            forecast.label_context, forecast.label_context_fingerprint
        ):
            raise ValueError(f"forecast {forecast.forecast_id} has an invalid label-context fingerprint")
        if forecast.label_context is None and forecast.label_context_fingerprint is not None:
            raise ValueError(f"forecast {forecast.forecast_id} has a label-context hash without its context")
        for field_name in (
            "target_contract_fingerprint", "target_window_id",
            "target_window_start_at", "target_window_end_at",
        ):
            value = getattr(forecast, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"forecast {forecast.forecast_id} has an invalid {field_name}")
        as_of = parse_timestamp(forecast.as_of).isoformat()
        window_fields = (
            forecast.target_window_id,
            forecast.target_window_start_at,
            forecast.target_window_end_at,
        )
        if any(value is not None for value in window_fields):
            if any(value is None for value in window_fields):
                raise ValueError(f"forecast {forecast.forecast_id} has an incomplete target window")
            try:
                window_start_time = parse_timestamp(forecast.target_window_start_at)
                window_end_time = parse_timestamp(forecast.target_window_end_at)
            except (OverflowError, TypeError, ValueError) as exc:
                raise ValueError(f"forecast {forecast.forecast_id} has an invalid target window") from exc
            if window_end_time <= window_start_time:
                raise ValueError(f"forecast {forecast.forecast_id} has a non-positive target window")
            window_start = window_start_time.isoformat()
            window_end = window_end_time.isoformat()
        else:
            window_start = None
            window_end = None
        key = (
            forecast.symbol.strip().upper(),
            as_of,
            forecast.target,
            forecast.target_unit,
            forecast.horizon,
            forecast.forecast_unit,
            forecast.direction_semantics,
            forecast.target_contract_fingerprint,
            forecast.target_window_id,
            window_start,
            window_end,
            forecast.label_context_fingerprint,
        )
        panels[key].append(forecast)

    panel_results: list[dict[str, object]] = []
    def panel_sort_key(item: tuple[tuple[object, ...], list[Forecast]]) -> tuple[tuple[bool, str], ...]:
        return tuple(
            (value is not None, "" if value is None else str(value))
            for value in item[0]
        )

    for key, rows in sorted(panels.items(), key=panel_sort_key):
        usable = [
            row for row in rows
            if row.status == "forecast"
            and _finite_number(row.forecast_value)
        ]
        counts_by_engine = Counter(row.engine_id for row in rows)
        duplicate_engine_ids = sorted(engine_id for engine_id, count in counts_by_engine.items() if count > 1)
        tokens_by_id = {row.forecast_id: _lineage_tokens(row) for row in usable}
        parent = {row.forecast_id: row.forecast_id for row in usable}

        def find(item: str) -> str:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(left: str, right: str) -> None:
            root_left, root_right = find(left), find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        overlap_edges: list[dict[str, object]] = []
        for i, left in enumerate(usable):
            left_tokens = tokens_by_id[left.forecast_id]
            for right in usable[i + 1:]:
                right_tokens = tokens_by_id[right.forecast_id]
                shared = {
                    kind: left_tokens[kind] & right_tokens[kind]
                    for kind in left_tokens
                }
                kinds = [kind for kind, values in shared.items() if values]
                if kinds:
                    dependency_kinds = [
                        kind for kind in kinds
                        if kind in {"exact_hash", "source_id", "declared_group"}
                    ]
                    if dependency_kinds:
                        union(left.forecast_id, right.forecast_id)
                    overlap_edges.append({
                        "left_engine_id": left.engine_id,
                        "right_engine_id": right.engine_id,
                        "overlap_kinds": kinds,
                        "dependency_overlap_kinds": dependency_kinds,
                        "shared_exact_hash_count": len(shared["exact_hash"]),
                        "shared_transform_id_count": len(shared["transform_id"]),
                        "shared_transform_hash_count": len(shared["transform_hash"]),
                    })

        component_map: dict[str, list[Forecast]] = defaultdict(list)
        for row in usable:
            component_map[find(row.forecast_id)].append(row)
        components = list(component_map.values())
        cluster_values = [
            float(median(row.forecast_value for row in component))
            for component in components
        ]
        magnitude_units_match = key[5] == key[3]
        if duplicate_engine_ids:
            descriptive_median = None
        elif magnitude_units_match and len(cluster_values) >= 2:
            descriptive_median = float(median(cluster_values))
        else:
            descriptive_median = None

        cluster_score_orientations = [
            _cluster_score_orientation(component) for component in components
        ]
        orientation_counts = Counter(cluster_score_orientations)
        score_orientation_available = any(
            category != "unknown" for category in cluster_score_orientations
        )
        non_neutral = sum(
            count for category, count in orientation_counts.items()
            if category in {"positive_score", "negative_score"}
        )
        if not duplicate_engine_ids and len(components) >= 2 and non_neutral:
            entropy = -sum(
                (orientation_counts[category] / non_neutral)
                * log(orientation_counts[category] / non_neutral)
                for category in ("positive_score", "negative_score")
                if orientation_counts[category]
            ) / log(2)
            disagreement_entropy = min(1.0, entropy)
        else:
            disagreement_entropy = None

        unknown_lineage = sorted(
            row.engine_id for row in usable
            if not any(tokens_by_id[row.forecast_id].values())
        )
        panel_results.append({
            "symbol": key[0],
            "as_of": key[1],
            "target": key[2],
            "target_unit": key[3],
            "horizon": key[4],
            "forecast_unit": key[5],
            "direction_semantics": key[6],
            "target_contract_fingerprint": key[7],
            "target_window_id": key[8],
            "target_window_start_at": key[9],
            "target_window_end_at": key[10],
            "label_context_fingerprint": key[11],
            "record_count": len(rows),
            "usable_forecast_count": len(usable),
            "abstention_count": sum(row.status == "abstain" for row in rows),
            "duplicate_engine_ids": duplicate_engine_ids,
            "potential_dependency_cluster_count": len(components),
            "potential_dependency_clusters": [
                sorted(row.engine_id for row in component)
                for component in components
            ],
            "cluster_score_orientation_categories": cluster_score_orientations,
            "overlap_edges": overlap_edges,
            "unknown_lineage_engine_ids": unknown_lineage,
            "magnitude_units_match_target": magnitude_units_match,
            "descriptive_cluster_median": descriptive_median,
            "score_orientation_available": score_orientation_available,
            "cross_cluster_score_orientation_entropy": disagreement_entropy,
            "aggregation_status": (
                "suppressed_duplicate_engine_records"
                if duplicate_engine_ids
                else "descriptive_same_unit_only"
                if descriptive_median is not None
                else "risk_rank_only_units_differ"
                if not magnitude_units_match and key[6] == "uncalibrated_risk_rank_only"
                else "score_orientation_only_units_differ"
                if not magnitude_units_match and score_orientation_available
                else "no_score_orientation_units_differ"
                if not magnitude_units_match
                else "not_comparable_or_only_one_dependency_cluster"
            ),
        })

    return {
        "schema_version": "1.3",
        "status": "research_diagnostic",
        "decision_eligible": False,
        "panel_count": len(panel_results),
        "panels": panel_results,
        "interpretation": (
            "Panels preserve exact target, unit, symbol, cutoff, and horizon. "
            "An overlap edge means that caller-provided hashes, source IDs, or "
            "independence-group labels overlap; it is not a measured correlation. "
            "Different labels do not prove independent information. The cluster "
            "median is emitted only when forecast units equal target units and is "
            "still descriptive, not calibrated or an ensemble forecast. Direction "
            "categories summarize uncalibrated score orientation within matching "
            "direction semantics; they are not realized-direction accuracy."
        ),
    }
