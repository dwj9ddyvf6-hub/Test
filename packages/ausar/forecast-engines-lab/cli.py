"""Small local CLI; this module only lists and evaluates research forecasts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .catalog import ENGINES
from .boundary_map import forecast_boundary_map
from .abstention_audit import abstention_coverage_audit
from .contracts import FeatureObservation, FeatureUse, Forecast, ForecastRequest
from .diagnostics import forecast_collision_map
from .edge_cards import edge_cards_as_dicts, validate_edge_cards
from .engine import ForecastEngine
from .horizon_overlap import horizon_overlap_audit
from .ledger import ForecastLedger
from .source_clock import estimate_source_refresh, refresh_observation_from_dict
from .target_provenance import target_contract_inventory, target_provenance_audit


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value!r} is not allowed")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> Any:
    """Read strict JSON so duplicate keys and NaN/Infinity cannot be hidden."""
    try:
        contents = path.read_text(encoding="utf-8")
        return json.loads(
            contents,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"invalid JSON input {path}: {exc}") from exc


def _forecast_file(path: Path) -> int:
    raw = _read_json(path)
    features = {name: FeatureObservation(**value) for name, value in raw["features"].items()}
    request = ForecastRequest(
        raw["engine_id"], raw["symbol"], raw["as_of"], features,
        raw.get("target_window_id"), raw.get("target_window_start_at"), raw.get("target_window_end_at"),
        raw.get("label_transform_id"), raw.get("label_transform_hash"), raw.get("label_context"),
    )
    forecast = ForecastEngine().forecast(request)
    print(json.dumps(forecast.to_dict(), indent=2, sort_keys=True, allow_nan=False))
    return 0


def _forecast_from_dict(raw: dict[str, object]) -> Forecast:
    payload = dict(raw)
    for name in ("abstain_reasons", "assumptions", "kill_conditions"):
        payload[name] = tuple(payload.get(name, ()))
    payload["feature_manifest"] = tuple(
        FeatureUse(**item) for item in payload.get("feature_manifest", ())
    )
    return Forecast(**payload)  # type: ignore[arg-type]


def _collision_file(path: Path) -> int:
    raw = _read_json(path)
    records = raw["forecasts"] if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise ValueError("collision input must be a JSON array or an object with forecasts")
    report = forecast_collision_map([_forecast_from_dict(item) for item in records])
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def _boundary_file(path: Path) -> int:
    raw = _read_json(path)
    request_raw = raw["request"]
    features = {
        name: FeatureObservation(**value)
        for name, value in request_raw["features"].items()
    }
    request = ForecastRequest(
        request_raw["engine_id"], request_raw["symbol"], request_raw["as_of"], features,
        request_raw.get("target_window_id"), request_raw.get("target_window_start_at"),
        request_raw.get("target_window_end_at"),
        request_raw.get("label_transform_id"), request_raw.get("label_transform_hash"),
        request_raw.get("label_context"),
    )
    report = forecast_boundary_map(request, raw["stress_ranges"])
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def _coverage_audit_file(path: Path) -> int:
    raw = _read_json(path)
    ledger_path = Path(raw["ledger_path"])
    if not ledger_path.is_file():
        raise ValueError(f"forecast ledger does not exist: {ledger_path}")
    evaluation_as_of = raw["evaluation_as_of"]
    ledger_view = ForecastLedger(ledger_path).coverage_records(evaluation_as_of)
    report = abstention_coverage_audit(
        ledger_view["records"],
        evaluation_as_of=evaluation_as_of,
        tail_thresholds=raw.get("tail_thresholds", {}),
    )
    report["ledger_integrity"] = ledger_view["ledger_integrity"]
    report["unmatched_outcome_count"] = ledger_view["unmatched_outcome_count"]
    report["unmatured_outcome_count"] = ledger_view["unmatured_outcome_count"]
    report["out_of_scope_outcome_count"] = ledger_view["out_of_scope_outcome_count"]
    report["invalid_ledger_outcome_count"] = ledger_view["invalid_outcome_count"]
    report["invalid_ledger_forecast_count"] = ledger_view["invalid_forecast_count"]
    report["not_yet_recorded_forecast_count"] = ledger_view["not_yet_recorded_forecast_count"]
    report["not_yet_recorded_outcome_count"] = ledger_view["not_yet_recorded_outcome_count"]
    report["unbound_target_contract_outcome_count"] = ledger_view["unbound_target_contract_outcome_count"]
    report["target_contract_mismatch_outcome_count"] = ledger_view["target_contract_mismatch_outcome_count"]
    report["invalid_label_transform_outcome_count"] = ledger_view["invalid_label_transform_outcome_count"]
    report["invalid_target_window_outcome_count"] = ledger_view["invalid_target_window_outcome_count"]
    report["invalid_label_context_outcome_count"] = ledger_view["invalid_label_context_outcome_count"]
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def _horizon_overlap_file(path: Path) -> int:
    raw = _read_json(path)
    ledger_path = Path(raw["ledger_path"])
    if not ledger_path.is_file():
        raise ValueError(f"forecast ledger does not exist: {ledger_path}")
    evaluation_as_of = raw["evaluation_as_of"]
    ledger_view = ForecastLedger(ledger_path).coverage_records(evaluation_as_of)
    report = horizon_overlap_audit(
        ledger_view["records"], evaluation_as_of=evaluation_as_of
    )
    report["ledger_integrity"] = ledger_view["ledger_integrity"]
    report["unmatched_outcome_count"] = ledger_view["unmatched_outcome_count"]
    report["unmatured_outcome_count"] = ledger_view["unmatured_outcome_count"]
    report["out_of_scope_outcome_count"] = ledger_view["out_of_scope_outcome_count"]
    report["invalid_ledger_outcome_count"] = ledger_view["invalid_outcome_count"]
    report["invalid_ledger_forecast_count"] = ledger_view["invalid_forecast_count"]
    report["not_yet_recorded_forecast_count"] = ledger_view["not_yet_recorded_forecast_count"]
    report["not_yet_recorded_outcome_count"] = ledger_view["not_yet_recorded_outcome_count"]
    report["unbound_target_contract_outcome_count"] = ledger_view["unbound_target_contract_outcome_count"]
    report["target_contract_mismatch_outcome_count"] = ledger_view["target_contract_mismatch_outcome_count"]
    report["invalid_label_transform_outcome_count"] = ledger_view["invalid_label_transform_outcome_count"]
    report["invalid_target_window_outcome_count"] = ledger_view["invalid_target_window_outcome_count"]
    report["invalid_label_context_outcome_count"] = ledger_view["invalid_label_context_outcome_count"]
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def _target_provenance_file(path: Path) -> int:
    raw = _read_json(path)
    ledger_path = Path(raw["ledger_path"])
    if not ledger_path.is_file():
        raise ValueError(f"forecast ledger does not exist: {ledger_path}")
    evaluation_as_of = raw["evaluation_as_of"]
    ledger_view = ForecastLedger(ledger_path).coverage_records(evaluation_as_of)
    report = target_provenance_audit(
        ledger_view["records"], evaluation_as_of=evaluation_as_of
    )
    report["ledger_integrity"] = ledger_view["ledger_integrity"]
    report["unmatched_outcome_count"] = ledger_view["unmatched_outcome_count"]
    report["unmatured_outcome_count"] = ledger_view["unmatured_outcome_count"]
    report["out_of_scope_outcome_count"] = ledger_view["out_of_scope_outcome_count"]
    report["invalid_ledger_outcome_count"] = ledger_view["invalid_outcome_count"]
    report["invalid_ledger_forecast_count"] = ledger_view["invalid_forecast_count"]
    report["not_yet_recorded_forecast_count"] = ledger_view["not_yet_recorded_forecast_count"]
    report["not_yet_recorded_outcome_count"] = ledger_view["not_yet_recorded_outcome_count"]
    report["unbound_target_contract_outcome_count"] = ledger_view["unbound_target_contract_outcome_count"]
    report["target_contract_mismatch_outcome_count"] = ledger_view["target_contract_mismatch_outcome_count"]
    report["invalid_label_transform_outcome_count"] = ledger_view["invalid_label_transform_outcome_count"]
    report["invalid_target_window_outcome_count"] = ledger_view["invalid_target_window_outcome_count"]
    report["invalid_label_context_outcome_count"] = ledger_view["invalid_label_context_outcome_count"]
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def _source_refresh_file(path: Path) -> int:
    raw = _read_json(path)
    current = raw["current"]
    history = [refresh_observation_from_dict(row) for row in raw.get("history", ())]
    report = estimate_source_refresh(
        source_id=current["source_id"],
        source_family=current["source_family"],
        age_seconds=current["age_seconds"],
        horizon_seconds=current["horizon_seconds"],
        as_of=raw["as_of"],
        history=history,
        min_samples=raw.get("min_samples", 30),
    )
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Research-only forecasts; no broker or order support.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the 30 registered forecast hypotheses")
    sub.add_parser("edge-ledger", help="print the 30 pre-registered Edge hypothesis cards")
    forecast_parser = sub.add_parser("forecast", help="evaluate one point-in-time JSON request")
    forecast_parser.add_argument("request", type=Path)
    collision_parser = sub.add_parser(
        "collision-map", help="diagnose compatible forecast overlap and disagreement"
    )
    collision_parser.add_argument("forecasts", type=Path)
    clock_parser = sub.add_parser(
        "source-refresh", help="estimate a source-refresh frequency from matured history"
    )
    clock_parser.add_argument("request", type=Path)
    boundary_parser = sub.add_parser(
        "boundary-map", help="map score/direction changes across caller-supplied input ranges"
    )
    boundary_parser.add_argument("request", type=Path)
    coverage_parser = sub.add_parser(
        "coverage-audit", help="audit outcomes during forecasted and abstained attempts"
    )
    coverage_parser.add_argument("request", type=Path)
    overlap_parser = sub.add_parser(
        "horizon-overlap", help="audit repeated exposure to overlapping forecast windows"
    )
    overlap_parser.add_argument("request", type=Path)
    provenance_parser = sub.add_parser(
        "target-provenance", help="audit target-contract and label-transform versions"
    )
    provenance_parser.add_argument("request", type=Path)
    sub.add_parser("target-contracts", help="print all 30 frozen target contracts and hashes")
    args = parser.parse_args()
    if args.command == "list":
        for spec in ENGINES:
            print(f"{spec.engine_id}\t{spec.name}\t{spec.maturity}\t{spec.horizon}")
        return 0
    if args.command == "edge-ledger":
        errors = validate_edge_cards()
        if errors:
            raise SystemExit("\n".join(errors))
        print(json.dumps(edge_cards_as_dicts(), indent=2, sort_keys=True, allow_nan=False))
        return 0
    if args.command == "collision-map":
        return _collision_file(args.forecasts)
    if args.command == "source-refresh":
        return _source_refresh_file(args.request)
    if args.command == "boundary-map":
        return _boundary_file(args.request)
    if args.command == "coverage-audit":
        return _coverage_audit_file(args.request)
    if args.command == "horizon-overlap":
        return _horizon_overlap_file(args.request)
    if args.command == "target-provenance":
        return _target_provenance_file(args.request)
    if args.command == "target-contracts":
        print(json.dumps(target_contract_inventory(), indent=2, sort_keys=True, allow_nan=False))
        return 0
    return _forecast_file(args.request)


if __name__ == "__main__":
    raise SystemExit(main())
