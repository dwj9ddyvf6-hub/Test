"""Caller-bounded forecast boundary tomography; no scenario probabilities."""

from __future__ import annotations

from itertools import product
from math import isfinite
from typing import Mapping

from .catalog import get_engine
from .contracts import ForecastRequest
from .engine import ForecastEngine
from .scorers import score


_MAX_STRESS_DIMENSIONS = 8
_PATH_SAMPLES = 128


def forecast_boundary_map(
    request: ForecastRequest,
    stress_ranges: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Map where a deterministic forecast changes category inside supplied ranges.

    The caller supplies every range. This function never estimates a plausible
    range, assigns scenario likelihood, or emits a forecast/order.
    """
    spec = get_engine(request.engine_id)
    baseline = ForecastEngine().forecast(request)
    base_report: dict[str, object] = {
        "schema_version": "1.0",
        "status": "research_diagnostic",
        "decision_eligible": False,
        "engine_id": spec.engine_id,
        "symbol": baseline.symbol,
        "as_of": baseline.as_of,
        "horizon": baseline.horizon,
        "target": baseline.target,
        "target_unit": baseline.target_unit,
        "model_fingerprint": baseline.model_fingerprint,
        "baseline_status": baseline.status,
        "baseline_direction": baseline.direction,
        "baseline_value": baseline.forecast_value,
        "baseline_model_score": baseline.model_score,
    }
    if baseline.status != "forecast" or baseline.forecast_value is None:
        base_report.update({
            "status": "unavailable_baseline_abstained",
            "abstain_reasons": list(baseline.abstain_reasons),
            "interpretation": "No sensitivity surface is computed for an invalid baseline forecast.",
        })
        return base_report

    requirements = {item.name: item for item in spec.inputs}
    unknown = set(stress_ranges) - set(requirements)
    if unknown:
        raise ValueError(f"stress ranges include unknown engine inputs: {sorted(unknown)}")
    if not stress_ranges:
        raise ValueError("at least one caller-supplied stress range is required")
    if len(stress_ranges) > _MAX_STRESS_DIMENSIONS:
        raise ValueError(f"at most {_MAX_STRESS_DIMENSIONS} stress dimensions are allowed")

    values = {
        item.name: float(item.value)
        for item in baseline.feature_manifest
        if item.value is not None
    }
    parsed: dict[str, tuple[float, float]] = {}
    for name, raw in stress_ranges.items():
        if not isinstance(raw, Mapping):
            raise ValueError(f"{name}: range must be an object")
        if set(raw) != {"low", "high", "unit"}:
            raise ValueError(f"{name}: range requires exactly low, high, and unit")
        if raw["unit"] != requirements[name].unit:
            raise ValueError(f"{name}: range unit must be {requirements[name].unit!r}")
        if any(
            isinstance(raw[key], bool) or not isinstance(raw[key], (int, float))
            for key in ("low", "high")
        ):
            raise ValueError(f"{name}: range endpoints must be numeric, not booleans or strings")
        try:
            low = float(raw["low"])
            high = float(raw["high"])
        except (OverflowError, ValueError) as exc:
            raise ValueError(f"{name}: low/high must be finite and low < high") from exc
        value = values[name]
        if not isfinite(low) or not isfinite(high) or low >= high or not isfinite(high - low):
            raise ValueError(f"{name}: low/high must be finite and low < high")
        domain = requirements[name].value_range
        if domain is not None and (low < domain[0] or high > domain[1]):
            raise ValueError(
                f"{name}: stress range must stay within the registered input domain {domain}"
            )
        if not low <= value <= high:
            raise ValueError(f"{name}: baseline value must lie inside its supplied range")
        parsed[name] = (low, high)

    def evaluate(scenario: Mapping[str, float]) -> tuple[float, float, str]:
        signal = score(spec.formula, scenario)
        if not isfinite(signal.value) or not isfinite(signal.model_score):
            raise ValueError("scorer emitted a non-finite scenario value")
        direction = ForecastEngine._direction(spec, signal.value)
        return signal.value, signal.model_score, direction

    base_direction = baseline.direction
    one_feature: list[dict[str, object]] = []
    for name, (low, high) in parsed.items():
        current = values[name]
        endpoints: dict[str, dict[str, object]] = {}
        first_flip: dict[str, object] | None = None
        for side, endpoint in (("low", low), ("high", high)):
            scenario = dict(values)
            scenario[name] = endpoint
            endpoint_value, endpoint_score, endpoint_direction = evaluate(scenario)
            endpoints[side] = {
                "value": endpoint_value,
                "model_score": endpoint_score,
                "direction": endpoint_direction,
                "direction_changed": endpoint_direction != base_direction,
            }
            for step in range(1, _PATH_SAMPLES + 1):
                fraction = step / _PATH_SAMPLES
                candidate = current + (endpoint - current) * fraction
                probe = dict(values)
                probe[name] = candidate
                probe_value, probe_score, probe_direction = evaluate(probe)
                if probe_direction != base_direction:
                    candidate_result = {
                        "toward": side,
                        "feature_value": candidate,
                        "value": probe_value,
                        "model_score": probe_score,
                        "direction": probe_direction,
                        "path_fraction_from_baseline": fraction,
                        "fraction_of_supplied_range": abs(candidate - current) / (high - low),
                    }
                    if first_flip is None or candidate_result["fraction_of_supplied_range"] < first_flip["fraction_of_supplied_range"]:
                        first_flip = candidate_result
                    break
        one_feature.append({
            "feature": name,
            "unit": requirements[name].unit,
            "baseline_value": current,
            "supplied_range": {"low": low, "high": high},
            "sampling_points_per_direction": _PATH_SAMPLES,
            "endpoint_scenarios": endpoints,
            "endpoint_secant_score_per_unit": (
                (endpoints["high"]["model_score"] - endpoints["low"]["model_score"]) / (high - low)
            ),
            "first_sampled_one_feature_direction_flip": first_flip,
        })

    names = list(parsed)
    corner_rows: list[dict[str, object]] = []
    for bits in product((0, 1), repeat=len(names)):
        scenario = dict(values)
        settings: dict[str, float] = {}
        for name, bit in zip(names, bits):
            scenario[name] = parsed[name][bit]
            settings[name] = scenario[name]
        value, model_score, direction = evaluate(scenario)
        corner_rows.append({
            "settings": settings,
            "value": value,
            "model_score": model_score,
            "direction": direction,
        })

    pairwise_interactions: list[dict[str, object]] = []
    for left_index, left_name in enumerate(names):
        left_low, left_high = parsed[left_name]
        for right_name in names[left_index + 1:]:
            right_low, right_high = parsed[right_name]
            pair_corners: dict[str, dict[str, object]] = {}
            for left_side, left_value in (("low", left_low), ("high", left_high)):
                for right_side, right_value in (("low", right_low), ("high", right_high)):
                    scenario = dict(values)
                    scenario[left_name] = left_value
                    scenario[right_name] = right_value
                    value, model_score, direction = evaluate(scenario)
                    pair_corners[f"{left_side}_{right_side}"] = {
                        "value": value,
                        "model_score": model_score,
                        "direction": direction,
                    }
            interaction = (
                float(pair_corners["high_high"]["model_score"])
                - float(pair_corners["high_low"]["model_score"])
                - float(pair_corners["low_high"]["model_score"])
                + float(pair_corners["low_low"]["model_score"])
            )
            if not isfinite(interaction):
                raise ValueError(f"non-finite pairwise interaction for {left_name}/{right_name}")
            normalized_interaction = interaction / (left_high - left_low) / (right_high - right_low)
            if not isfinite(normalized_interaction):
                raise ValueError(f"non-finite normalized interaction for {left_name}/{right_name}")
            pairwise_interactions.append({
                "features": [left_name, right_name],
                "units": [requirements[left_name].unit, requirements[right_name].unit],
                "other_features_held_at_baseline": True,
                "corner_scenarios": pair_corners,
                "direction_bifurcation": len({
                    str(row["direction"]) for row in pair_corners.values()
                }) > 1,
                "difference_in_differences_score": interaction,
                "difference_in_differences_per_unit_product": normalized_interaction,
            })

    direction_counts: dict[str, int] = {}
    for row in corner_rows:
        direction = str(row["direction"])
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    corner_directions = set(direction_counts)
    one_dimensional_flips = sum(
        row["first_sampled_one_feature_direction_flip"] is not None
        for row in one_feature
    )
    pairwise_direction_bifurcations = sum(
        bool(row["direction_bifurcation"]) for row in pairwise_interactions
    )
    if spec.score_kind != "signed":
        stability = "direction_not_applicable_for_non_directional_score"
    elif len(corner_directions) > 1:
        stability = "direction_bifurcation_on_supplied_corners"
    elif pairwise_direction_bifurcations:
        stability = "pairwise_direction_bifurcation_with_other_features_at_baseline"
    elif one_dimensional_flips:
        stability = "interior_direction_flip_between_corners"
    else:
        stability = "single_direction_on_supplied_stress_surface"

    base_report.update({
        "status": "research_diagnostic",
        "stability": stability,
        "stress_range_origin": "caller_supplied_not_empirically_inferred",
        "direction_counts_are_probabilities": False,
        "one_dimensional_direction_flip_count": one_dimensional_flips,
        "pairwise_direction_bifurcation_count": pairwise_direction_bifurcations,
        "one_feature_sensitivity": one_feature,
        "pairwise_interaction_count": len(pairwise_interactions),
        "pairwise_interactions": pairwise_interactions,
        "joint_corner_scenario_count": len(corner_rows),
        "joint_corner_direction_counts": direction_counts,
        "joint_corner_scenarios": corner_rows,
        "interpretation": (
            "A sampled boundary flip identifies sensitivity to supplied assumptions, not likelihood; "
            "a narrow transition between sampled points may be missed. "
            "Pairwise difference-in-differences describe score interaction with other features "
            "held at baseline, not causal effects. "
            "Corner counts are unweighted scenario counts. Scores are uncalibrated and contain "
            "no price, transaction-cost, fill, or portfolio information."
        ),
    })
    return base_report
