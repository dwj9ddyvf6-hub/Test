"""Input validation and forecast emission; all failures become explicit abstains."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from math import isfinite
import re

from .catalog import EngineSpec, get_engine
from .contracts import FeatureObservation, FeatureUse, Forecast, ForecastRequest, new_forecast_id, parse_timestamp
from .edge_cards import get_edge_card
from .fingerprint import engine_model_fingerprint
from .label_context import label_context_fingerprint, normalize_label_context
from .scorers import score
from .target_contract import target_contract_fingerprint, target_label_contract

_EVIDENCE_KINDS = {"observed", "published", "reproduced", "inferred"}
_DERIVED_EVIDENCE_KINDS = {"reproduced", "inferred"}
ENGINE_VERSION = "0.9.2-hypothesis"


class ForecastEngine:
    """Evaluate a registered forecast hypothesis with strict as-of validation."""

    def forecast(self, request: ForecastRequest) -> Forecast:
        spec = get_engine(request.engine_id)
        model_fingerprint = engine_model_fingerprint(spec)
        target_fingerprint = target_contract_fingerprint(spec.engine_id)
        now = datetime.now(timezone.utc)
        try:
            as_of = parse_timestamp(request.as_of)
            reasons: list[str] = []
        except (TypeError, ValueError, OverflowError):
            # Preserve the no-score contract even when the caller supplies a
            # malformed cutoff. The fallback timestamp is explicitly marked
            # as an abstention reason and is never used to emit a forecast.
            as_of = now
            reasons = ["invalid_as_of"]
        symbol = self._normalized_symbol(request.symbol)
        if not symbol:
            reasons.append("invalid_symbol")
        if not isinstance(request.features, Mapping):
            reasons.append("invalid_feature_collection")
            features: Mapping[str, FeatureObservation] = {}
        else:
            features = request.features
        label_contract = target_label_contract(spec.engine_id)
        target_window_id: str | None = None
        target_window_start_at: str | None = None
        target_window_end_at: str | None = None
        label_transform_id: str | None = None
        label_transform_hash: str | None = None
        label_context: dict[str, str] | None = None
        label_context_hash: str | None = None
        if request.target_window_id is not None and not isinstance(request.target_window_id, str):
            reasons.append("invalid_target_window_id")
            raw_window_id = None
        else:
            raw_window_id = (request.target_window_id or "").strip() or None
        if bool(raw_window_id) != bool(request.target_window_start_at) or bool(raw_window_id) != bool(request.target_window_end_at):
            reasons.append("incomplete_target_window_binding")
        elif raw_window_id:
            if label_contract["status"] != "labelable":
                reasons.append("target_contract_not_labelable")
            elif raw_window_id not in label_contract["allowed_window_ids"]:
                reasons.append("target_window_id_not_allowed")
            else:
                try:
                    parsed_window_start = parse_timestamp(request.target_window_start_at)
                    parsed_window_end = parse_timestamp(request.target_window_end_at)
                except (AttributeError, TypeError, ValueError):
                    reasons.append("invalid_target_window_end")
                else:
                    if parsed_window_start < as_of:
                        reasons.append("target_window_start_before_as_of")
                    elif parsed_window_end <= parsed_window_start:
                        reasons.append("target_window_end_not_after_start")
                    else:
                        target_window_id = raw_window_id
                        target_window_start_at = parsed_window_start.isoformat()
                        target_window_end_at = parsed_window_end.isoformat()
        if request.label_transform_id is not None and not isinstance(request.label_transform_id, str):
            reasons.append("invalid_label_transform_id")
            raw_transform_id = None
        else:
            raw_transform_id = (request.label_transform_id or "").strip() or None
        if request.label_transform_hash is not None and not isinstance(request.label_transform_hash, str):
            reasons.append("invalid_label_transform_hash")
            raw_transform_hash = None
        else:
            raw_transform_hash = (request.label_transform_hash or "").strip() or None
        if bool(raw_transform_id) != bool(raw_transform_hash):
            reasons.append("incomplete_label_transform_binding")
        elif raw_transform_id:
            if label_contract["status"] != "labelable":
                reasons.append("label_transform_for_nonlabelable_target")
            else:
                digest = raw_transform_hash.removeprefix("sha256:")
                if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
                    reasons.append("invalid_label_transform_hash")
                else:
                    label_transform_id = raw_transform_id
                    label_transform_hash = "sha256:" + digest.lower()
        if request.label_context is not None:
            try:
                label_context = normalize_label_context(request.label_context)
                label_context_hash = label_context_fingerprint(label_context)
            except (TypeError, ValueError):
                reasons.append("invalid_label_context")
        if (target_window_id or label_transform_hash) and not label_context_hash:
            reasons.append("missing_label_context")
        if label_contract["status"] == "scenario_only" and label_context_hash:
            reasons.append("label_context_for_nonlabelable_target")
            label_context = None
            label_context_hash = None
        values: dict[str, float] = {}
        uses: list[FeatureUse] = []
        quality_components: list[float] = []
        independent_groups: set[str] = set()
        source_group_counts: dict[str, int] = {}

        for requirement in spec.inputs:
            raw = features.get(requirement.name)
            if raw is None:
                reasons.append(f"missing:{requirement.name}")
                uses.append(FeatureUse(requirement.name, None, None, None, None, None, None, None, None))
                continue
            if not isinstance(raw, FeatureObservation):
                reasons.append(f"invalid_observation:{requirement.name}")
                uses.append(FeatureUse(requirement.name, None, None, None, None, None, None, None, None))
                continue
            try:
                obs = raw.normalized()
            except (TypeError, ValueError, OverflowError, AttributeError):
                reasons.append(f"invalid_observation:{requirement.name}")
                uses.append(FeatureUse(
                    requirement.name, None,
                    raw.unit if isinstance(raw.unit, str) else None,
                    raw.source_id if isinstance(raw.source_id, str) else None,
                    raw.source_hash if isinstance(raw.source_hash, str) else None,
                    raw.evidence_kind if isinstance(raw.evidence_kind, str) else None,
                    raw.independence_group if isinstance(raw.independence_group, str) else None,
                    None,
                    None,
                    transform_id=raw.transform_id if isinstance(raw.transform_id, str) else None,
                    transform_hash=raw.transform_hash if isinstance(raw.transform_hash, str) else None,
                ))
                continue

            age = (as_of - obs.observed_at).total_seconds()
            available_age = (as_of - obs.available_at).total_seconds()
            publication_lag = (obs.available_at - obs.observed_at).total_seconds()
            bad: list[str] = []
            if not isfinite(obs.value):
                bad.append("non_finite")
            if obs.unit != requirement.unit:
                bad.append("unit_mismatch")
            if (requirement.value_range is not None and isfinite(obs.value)
                    and not requirement.value_range[0] <= obs.value <= requirement.value_range[1]):
                bad.append("value_out_of_range")
            if age < 0 or obs.available_at > as_of or obs.ingested_at > as_of:
                bad.append("future_or_late_data")
            if obs.available_at < obs.observed_at or obs.ingested_at < obs.available_at:
                bad.append("timestamp_order_invalid")
            if age > requirement.max_age_seconds:
                bad.append("stale")
            if not obs.source_id or not obs.independence_group or len(obs.source_hash) < 32:
                bad.append("missing_provenance")
            if not obs.rights_approved:
                bad.append("data_rights_not_approved")
            if obs.evidence_kind not in _EVIDENCE_KINDS:
                bad.append("unknown_evidence_kind")
            if obs.evidence_kind in _DERIVED_EVIDENCE_KINDS and not obs.transform_hash:
                bad.append("missing_transform_provenance")
            if not isfinite(obs.quality) or not 0.0 <= obs.quality <= 1.0:
                bad.append("invalid_quality")
            elif obs.quality < requirement.min_quality:
                bad.append("quality_below_floor")

            for cause in bad:
                reasons.append(f"{cause}:{requirement.name}")
            uses.append(FeatureUse(requirement.name, obs.value if isfinite(obs.value) else None,
                                   obs.unit, obs.source_id, obs.source_hash,
                                   obs.evidence_kind, obs.independence_group, age,
                                   obs.quality if isfinite(obs.quality) else None,
                                   available_age, publication_lag, obs.transform_id, obs.transform_hash))
            if not bad:
                values[requirement.name] = obs.value
                freshness = max(0.0, 1.0 - age / requirement.max_age_seconds)
                evidence_haircut = 0.65 if obs.evidence_kind == "inferred" else 1.0
                quality_components.append(obs.quality * (0.5 + 0.5 * freshness) * evidence_haircut)
                independent_groups.add(obs.independence_group)
                source_group_counts[obs.independence_group] = source_group_counts.get(obs.independence_group, 0) + 1

        # Prevent an invalid historical as-of request from masquerading as a live forecast.
        if as_of > now:
            reasons.append("as_of_in_future")
        valid_feature_count = sum(source_group_counts.values())
        source_group_concentration = None
        effective_source_groups = None
        if valid_feature_count:
            source_group_concentration = sum(
                (count / valid_feature_count) ** 2 for count in source_group_counts.values()
            )
            effective_source_groups = 1.0 / source_group_concentration
        if reasons:
            return self._abstain(request, spec, as_of, reasons, uses, len(independent_groups),
                                 source_group_concentration, effective_source_groups, model_fingerprint,
                                 target_fingerprint, label_contract["status"], target_window_id,
                                 target_window_start_at, target_window_end_at,
                                 label_transform_id, label_transform_hash,
                                 label_context, label_context_hash)

        try:
            signal = score(spec.formula, values)
        except (ArithmeticError, ValueError):
            reasons.append("score_computation_failed")
            return self._abstain(
                request, spec, as_of, reasons, uses, len(independent_groups),
                source_group_concentration, effective_source_groups,
                model_fingerprint, target_fingerprint, label_contract["status"],
                target_window_id, target_window_start_at, target_window_end_at,
                label_transform_id, label_transform_hash, label_context,
                label_context_hash,
            )
        input_quality = sum(quality_components) / len(quality_components) if quality_components else 0.0
        direction = self._direction(spec, signal.value)
        card = get_edge_card(spec.engine_id)
        assumptions = spec.assumptions + (
            f"Edge hypothesis only: {card.novel_mechanism}",
            f"Payer hypothesis only: {card.payer_hypothesis}",
            f"Research card: {spec.engine_id}; status={card.status}.",
            "Direction reports score orientation only; it is not a calibrated return, event probability, or trade instruction.",
        )
        if any(use.evidence_kind == "inferred" for use in uses):
            assumptions = assumptions + ("At least one required input is inferred; treat the result as a conditional scenario.",)
        unversioned_features = [
            use.name for use in uses
            if use.value is not None and use.transform_hash is None
        ]
        if unversioned_features:
            assumptions = assumptions + ("No feature-transform fingerprint supplied for: " + ", ".join(unversioned_features) + ".",)
        if label_contract["status"] == "labelable" and not target_window_id:
            assumptions = assumptions + ("No exact target window was frozen; this forecast cannot accept a verified outcome label.",)
        if label_contract["status"] == "labelable" and not label_transform_hash:
            assumptions = assumptions + ("No label-transform hash was frozen; this forecast cannot accept a verified outcome label.",)
        if label_contract["status"] == "labelable" and not label_context_hash:
            assumptions = assumptions + ("No label-context fingerprint was frozen; this forecast cannot accept a verified outcome label.",)

        return Forecast(
            schema_version="1.6",
            forecast_id=new_forecast_id(),
            engine_id=spec.engine_id,
            engine_version=ENGINE_VERSION,
            maturity=spec.maturity,
            symbol=self._normalized_symbol(request.symbol),
            issued_at=now.isoformat(),
            as_of=as_of.isoformat(),
            horizon=spec.horizon,
            target=spec.target,
            target_unit=spec.target_unit,
            status="forecast",
            forecast_value=signal.value,
            forecast_unit=spec.forecast_unit,
            model_score=signal.model_score,
            direction=direction,
            direction_semantics=spec.score_semantics,
            input_quality_score=input_quality,
            independent_source_groups=len(independent_groups),
            calibrated_probability=None,
            decision_eligible=False,
            drivers=signal.drivers,
            assumptions=assumptions,
            kill_conditions=spec.kill_conditions,
            feature_manifest=tuple(uses),
            declared_source_group_concentration=source_group_concentration,
            effective_declared_source_groups=effective_source_groups,
            model_fingerprint=model_fingerprint,
            target_contract_fingerprint=target_fingerprint,
            target_label_status=label_contract["status"],
            target_window_id=target_window_id,
            target_window_start_at=target_window_start_at,
            target_window_end_at=target_window_end_at,
            label_transform_id=label_transform_id,
            label_transform_hash=label_transform_hash,
            label_context=label_context,
            label_context_fingerprint=label_context_hash,
        )

    @staticmethod
    def _direction(spec: EngineSpec, value: float) -> str:
        """Report score orientation without implying calibrated predictions."""
        if spec.score_kind == "signed":
            return "POSITIVE_SCORE" if value > 0.0 else "NEGATIVE_SCORE" if value < 0.0 else "ZERO_SCORE"
        if spec.score_kind == "risk":
            return "RISK_RANK_ONLY"
        return "NOT_DIRECTIONAL"

    @staticmethod
    def _normalized_symbol(value: object) -> str:
        return value.strip().upper() if isinstance(value, str) else ""

    @staticmethod
    def _abstain(request: ForecastRequest, spec: EngineSpec, as_of: datetime, reasons: list[str],
                 uses: list[FeatureUse], independent_groups: int,
                 source_group_concentration: float | None,
                 effective_source_groups: float | None,
                 model_fingerprint: str,
                 target_fingerprint: str,
                 target_label_status: str,
                 target_window_id: str | None,
                 target_window_start_at: str | None,
                 target_window_end_at: str | None,
                 label_transform_id: str | None,
                 label_transform_hash: str | None,
                 label_context: dict[str, str] | None,
                 label_context_hash: str | None) -> Forecast:
        card = get_edge_card(spec.engine_id)
        return Forecast(
            schema_version="1.6",
            forecast_id=new_forecast_id(),
            engine_id=spec.engine_id,
            engine_version=ENGINE_VERSION,
            maturity=spec.maturity,
            symbol=ForecastEngine._normalized_symbol(request.symbol),
            issued_at=datetime.now(timezone.utc).isoformat(),
            as_of=as_of.isoformat(),
            horizon=spec.horizon,
            target=spec.target,
            target_unit=spec.target_unit,
            status="abstain",
            forecast_value=None,
            forecast_unit=spec.forecast_unit,
            model_score=None,
            direction="ABSTAIN",
            direction_semantics=spec.score_semantics,
            input_quality_score=None,
            independent_source_groups=independent_groups,
            calibrated_probability=None,
            decision_eligible=False,
            abstain_reasons=tuple(sorted(set(reasons))),
            assumptions=spec.assumptions + (
                f"Edge hypothesis only: {card.novel_mechanism}",
                f"Research card: {spec.engine_id}; status={card.status}.",
            ),
            kill_conditions=spec.kill_conditions,
            feature_manifest=tuple(uses),
            declared_source_group_concentration=source_group_concentration,
            effective_declared_source_groups=effective_source_groups,
            model_fingerprint=model_fingerprint,
            target_contract_fingerprint=target_fingerprint,
            target_label_status=target_label_status,
            target_window_id=target_window_id,
            target_window_start_at=target_window_start_at,
            target_window_end_at=target_window_end_at,
            label_transform_id=label_transform_id,
            label_transform_hash=label_transform_hash,
            label_context=label_context,
            label_context_fingerprint=label_context_hash,
        )
