"""Measure shared future-path exposure in labeled forecast attempts."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from heapq import heappop, heappush
from math import isfinite
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


def _interval_metrics(intervals: Sequence[tuple[datetime, datetime]]) -> dict[str, int | float]:
    ordered = sorted(intervals)
    active_ends: list[datetime] = []
    overlap_pairs = 0
    max_concurrent = 0
    for start, end in ordered:
        while active_ends and active_ends[0] <= start:
            heappop(active_ends)
        overlap_pairs += len(active_ends)
        heappush(active_ends, end)
        max_concurrent = max(max_concurrent, len(active_ends))

    max_component = 0
    component_end: datetime | None = None
    component_size = 0
    for start, end in ordered:
        if component_end is None or start >= component_end:
            max_component = max(max_component, component_size)
            component_end = end
            component_size = 1
        else:
            component_end = max(component_end, end)
            component_size += 1
    max_component = max(max_component, component_size)

    nonoverlap_count = 0
    selected_end: datetime | None = None
    for start, end in sorted(intervals, key=lambda item: (item[1], item[0])):
        if selected_end is None or start >= selected_end:
            nonoverlap_count += 1
            selected_end = end

    pair_count = len(intervals) * (len(intervals) - 1) // 2
    return {
        "labeled_window_count": len(intervals),
        "overlapping_window_pair_count": overlap_pairs,
        "possible_window_pair_count": pair_count,
        "overlap_pair_rate": overlap_pairs / pair_count if pair_count else 0.0,
        "max_concurrent_windows": max_concurrent,
        "max_connected_overlap_component": max_component,
        "maximum_nonoverlapping_window_count": nonoverlap_count,
    }


def horizon_overlap_audit(
    records: Sequence[Mapping[str, Any]],
    *,
    evaluation_as_of: str,
) -> dict[str, Any]:
    """Describe repeated exposure to the same labeled future-price paths.

    Current intervals run from the frozen target-window start to end. Legacy
    intervals without a declared window fall back to ``as_of`` and outcome
    ``observed_at``. This is descriptive geometry, not an effective-sample-size
    estimator or an independence test. Outcomes should come from the verified,
    cutoff-filtered ``ForecastLedger.coverage_records`` view.
    """
    cutoff = parse_timestamp(evaluation_as_of)
    if cutoff > datetime.now(timezone.utc):
        raise ValueError("evaluation cutoff cannot be in the future")

    group_rows: dict[tuple[str | None, ...], list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    missing_count = 0
    ambiguous_count = 0
    invalid_count = 0

    for record in records:
        forecast_id = record.get("forecast_id")
        if not isinstance(forecast_id, str) or not forecast_id.strip():
            raise ValueError("every forecast attempt requires a forecast_id")
        if forecast_id in seen_ids:
            raise ValueError(f"duplicate forecast_id in overlap records: {forecast_id}")
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
        symbol_value = record.get("symbol")
        if not isinstance(symbol_value, str) or not symbol_value.strip():
            raise ValueError(f"forecast {forecast_id} is missing group or symbol metadata")
        symbol = symbol_value.strip().upper()
        try:
            forecast_as_of = parse_timestamp(record["as_of"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"forecast {forecast_id} has an invalid as_of timestamp") from exc

        interval: tuple[datetime, datetime] | None = None
        outcomes = record.get("outcomes", [])
        if not isinstance(outcomes, list):
            raise ValueError(f"outcomes for {forecast_id} must be a list")
        if not outcomes:
            missing_count += 1
        elif len(outcomes) > 1:
            ambiguous_count += 1
        elif not isinstance(outcomes[0], Mapping):
            invalid_count += 1
        else:
            outcome = outcomes[0]
            try:
                start = forecast_as_of
                observed = parse_timestamp(outcome["observed_at"])
                available = parse_timestamp(outcome["available_at"])
                ingested = parse_timestamp(outcome["ingested_at"])
                realized_raw = outcome["realized_value"]
                if isinstance(realized_raw, bool) or not isinstance(realized_raw, (int, float)):
                    raise ValueError("realized outcome must be numeric")
                realized = float(realized_raw)
                label_start = (
                    parse_timestamp(record["target_window_start_at"])
                    if record.get("target_window_start_at") else forecast_as_of
                )
            except (KeyError, TypeError, ValueError, OverflowError):
                invalid = True
            else:
                source_hash = str(outcome.get("source_hash") or "").removeprefix("sha256:")
                expected_role = "forecast_skill" if status == "forecast" else "abstention_audit"
                target_contract = record.get("target_contract_fingerprint")
                if target_contract is not None:
                    try:
                        frozen_start = parse_timestamp(record["target_window_start_at"])
                        outcome_start = parse_timestamp(outcome["target_window_start_at"])
                        frozen_end = parse_timestamp(record["target_window_end_at"])
                        outcome_end = parse_timestamp(outcome["target_window_end_at"])
                        transform_hash = str(outcome.get("label_transform_hash") or "").removeprefix("sha256:")
                        transform_bound = (
                            re.fullmatch(r"sha256:[a-fA-F0-9]{64}", target_contract) is not None
                            and
                            outcome.get("target_contract_fingerprint") == target_contract
                            and outcome.get("target_contract_binding") == "bound_attested"
                            and outcome.get("target_window_id") == record.get("target_window_id")
                            and outcome.get("label_context_fingerprint") == record.get("label_context_fingerprint")
                            and isinstance(record.get("label_context_fingerprint"), str)
                            and re.fullmatch(r"sha256:[a-fA-F0-9]{64}", record["label_context_fingerprint"]) is not None
                            and label_context_binding_is_valid(
                                record.get("label_context"), record.get("label_context_fingerprint")
                            )
                            and outcome.get("label_transform_id") == record.get("label_transform_id")
                            and "sha256:" + transform_hash.lower() == record.get("label_transform_hash")
                            and re.fullmatch(r"[a-fA-F0-9]{64}", transform_hash) is not None
                        )
                        window_bound = (
                            record.get("target_label_status") == "labelable"
                            and bool(record.get("target_window_id"))
                            and forecast_as_of <= frozen_start < frozen_end
                            and label_start == frozen_start == outcome_start
                            and frozen_end == outcome_end == observed
                        )
                    except (KeyError, TypeError, ValueError):
                        transform_bound = False
                        window_bound = False
                else:
                    transform_bound = (
                        outcome.get("target_contract_fingerprint") is None
                        and outcome.get("target_contract_binding", "legacy_unbound") == "legacy_unbound"
                    )
                    if (record.get("label_transform_id") is not None
                            or record.get("label_transform_hash") is not None):
                        frozen_transform_id = record.get("label_transform_id")
                        frozen_transform_hash = str(record.get("label_transform_hash") or "").removeprefix("sha256:")
                        outcome_transform_hash = str(outcome.get("label_transform_hash") or "").removeprefix("sha256:")
                        transform_bound = transform_bound and (
                            isinstance(frozen_transform_id, str)
                            and bool(frozen_transform_id.strip())
                            and re.fullmatch(r"[a-fA-F0-9]{64}", frozen_transform_hash) is not None
                            and outcome.get("label_transform_id") == frozen_transform_id.strip()
                            and outcome_transform_hash.lower() == frozen_transform_hash.lower()
                        )
                    if all(value is None for value in (
                        record.get("target_window_id"), record.get("target_window_start_at"),
                        record.get("target_window_end_at"), outcome.get("target_window_id"),
                        outcome.get("target_window_start_at"), outcome.get("target_window_end_at"),
                    )):
                        window_bound = True
                    else:
                        try:
                            window_bound = (
                                bool(record.get("target_window_id"))
                                and record.get("target_window_id") == outcome.get("target_window_id")
                                and forecast_as_of <= label_start
                                and parse_timestamp(record["target_window_start_at"])
                                == parse_timestamp(outcome["target_window_start_at"])
                                and parse_timestamp(record["target_window_end_at"])
                                == parse_timestamp(outcome["target_window_end_at"])
                                == observed
                            )
                        except (KeyError, TypeError, ValueError):
                            window_bound = False
                invalid = not (
                    outcome.get("evaluation_role") == expected_role
                    and outcome.get("rights_approved") is True
                    and outcome.get("horizon_complete") is True
                    and outcome.get("realized_unit") == group_key[4]
                    and isinstance(outcome.get("source_id"), str)
                    and bool(outcome["source_id"].strip())
                    and re.fullmatch(r"[a-fA-F0-9]{64}", source_hash) is not None
                    and transform_bound
                    and window_bound
                    and label_start < observed <= available <= ingested <= cutoff
                    and isfinite(realized)
                )
                if not invalid:
                    interval = (label_start, observed)
            if invalid:
                invalid_count += 1

        normalized_cutoff = forecast_as_of.isoformat()
        group_rows[group_key].append({
            "symbol": symbol,
            "interval": interval,
            "forecast_as_of": normalized_cutoff,
        })

    reports: list[dict[str, Any]] = []
    sort_key = lambda item: tuple((value is not None, value or "") for value in item[0])
    for key, rows in sorted(group_rows.items(), key=sort_key):
        by_symbol: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
        symbol_attempts: dict[str, int] = defaultdict(int)
        cutoff_symbols: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            symbol = row["symbol"]
            symbol_attempts[symbol] += 1
            interval = row["interval"]
            if interval is not None:
                by_symbol[symbol].append(interval)
                cutoff_symbols[str(row["forecast_as_of"])].add(symbol)

        symbol_metrics = {symbol: _interval_metrics(intervals)
                          for symbol, intervals in by_symbol.items()}
        possible_pairs = sum(int(metrics["possible_window_pair_count"])
                             for metrics in symbol_metrics.values())
        overlap_pairs = sum(int(metrics["overlapping_window_pair_count"])
                            for metrics in symbol_metrics.values())
        top_symbols = sorted(
            symbol_metrics.items(),
            key=lambda item: (-int(item[1]["overlapping_window_pair_count"]), item[0]),
        )[:20]
        same_cutoff_pairs = sum(len(symbols) * (len(symbols) - 1) // 2
                                for symbols in cutoff_symbols.values())
        reports.append({
            "engine_id": key[0],
            "model_fingerprint": key[1] if key[1] is not None else "legacy-unfingerprinted",
            "target_contract_fingerprint": key[2],
            "target": key[3],
            "target_unit": key[4],
            "horizon": key[5],
            "target_window_id": key[6],
            "label_transform_hash": key[7],
            "label_context_fingerprint": key[8],
            "attempt_count": len(rows),
            "labeled_interval_count": sum(len(intervals) for intervals in by_symbol.values()),
            "attempts_without_usable_interval_count": sum(
                1 for row in rows if row["interval"] is None
            ),
            "same_symbol_overlapping_pair_count": overlap_pairs,
            "same_symbol_possible_pair_count": possible_pairs,
            "same_symbol_overlap_pair_rate": overlap_pairs / possible_pairs if possible_pairs else 0.0,
            "symbols_with_overlapping_windows": sum(
                int(metrics["overlapping_window_pair_count"] > 0)
                for metrics in symbol_metrics.values()
            ),
            "max_concurrent_same_symbol_windows": max(
                (int(metrics["max_concurrent_windows"]) for metrics in symbol_metrics.values()),
                default=0,
            ),
            "max_connected_overlap_component": max(
                (int(metrics["max_connected_overlap_component"])
                 for metrics in symbol_metrics.values()), default=0,
            ),
            "maximum_nonoverlapping_window_count_by_symbol_sum": sum(
                int(metrics["maximum_nonoverlapping_window_count"])
                for metrics in symbol_metrics.values()
            ),
            "unique_labeled_cutoff_count": len(cutoff_symbols),
            "max_symbols_at_one_exact_cutoff": max(
                (len(symbols) for symbols in cutoff_symbols.values()), default=0,
            ),
            "same_cutoff_cross_symbol_pair_count": same_cutoff_pairs,
            "most_overlapped_symbols": [
                {"symbol": symbol, "attempt_count": symbol_attempts[symbol], **metrics}
                for symbol, metrics in top_symbols
            ],
        })

    return {
        "schema_version": "1.1",
        "status": "research_diagnostic",
        "decision_eligible": False,
        "evaluation_as_of": cutoff.isoformat(),
        "attempt_count": len(seen_ids),
        "missing_label_count": missing_count,
        "ambiguous_label_count": ambiguous_count,
        "invalid_label_count": invalid_count,
        "engine_model_group_count": len(reports),
        "groups": reports,
        "interpretation": (
            "Overlapping same-symbol intervals reuse portions of the same future target path. "
            "Exact-cutoff cross-symbol pairs reveal shared forecast cohorts that may share shocks. "
            "The maximum nonoverlapping-window count is a geometric anchor, not an effective "
            "sample size; no independence claim, p-value, or trading conclusion is emitted."
        ),
    }
