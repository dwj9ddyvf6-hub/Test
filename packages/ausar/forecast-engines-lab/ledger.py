"""SQLite append-only, hash-chained forecast/outcome evidence ledger."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .contracts import Forecast, parse_timestamp
from .catalog import get_engine
from .engine import ENGINE_VERSION
from .fingerprint import engine_model_fingerprint
from .label_context import label_context_fingerprint, normalize_label_context
from .target_contract import (
    target_contract_fingerprint as registered_target_contract_fingerprint,
    target_label_contract,
)

_GENESIS = "0" * 64


def _event_digest(previous: str, event_type: str, event_id: str,
                  payload_json: str, created_at: str) -> str:
    envelope = json.dumps(
        {"event_type": event_type, "event_id": event_id,
         "payload": json.loads(payload_json), "created_at": created_at},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256((previous + envelope).encode("utf-8")).hexdigest()


def _sha256_hex(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    digest = value.removeprefix("sha256:")
    return digest.lower() if re.fullmatch(r"[a-fA-F0-9]{64}", digest) else None


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


class ForecastLedger:
    """Append-only event ledger with one final outcome per forecast attempt."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS ledger_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL CHECK(event_type IN ('forecast','outcome')),
                event_id TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )""")
            db.execute("CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger_events BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger_events BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END")
            db.execute("""CREATE TABLE IF NOT EXISTS ledger_final_outcomes (
                forecast_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE
            )""")
            db.execute("CREATE TRIGGER IF NOT EXISTS ledger_final_outcomes_no_update BEFORE UPDATE ON ledger_final_outcomes BEGIN SELECT RAISE(ABORT, 'append-only outcome index'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS ledger_final_outcomes_no_delete BEFORE DELETE ON ledger_final_outcomes BEGIN SELECT RAISE(ABORT, 'append-only outcome index'); END")
            db.execute("CREATE TABLE IF NOT EXISTS ledger_schema_migrations (version INTEGER PRIMARY KEY)")
            migrated = db.execute(
                "SELECT 1 FROM ledger_schema_migrations WHERE version=1"
            ).fetchone()
            if migrated is None:
                for row in db.execute(
                        "SELECT event_id,payload_json FROM ledger_events WHERE event_type='outcome'").fetchall():
                    forecast_id = json.loads(row["payload_json"]).get("forecast_id")
                    if isinstance(forecast_id, str) and forecast_id:
                        db.execute(
                            "INSERT OR IGNORE INTO ledger_final_outcomes(forecast_id,event_id) VALUES(?,?)",
                            (forecast_id, row["event_id"]),
                        )
                db.execute("INSERT INTO ledger_schema_migrations(version) VALUES(1)")
            db.execute("COMMIT")

    def append_forecast(self, forecast: Forecast) -> str:
        if not isinstance(forecast.forecast_id, str) or not forecast.forecast_id.strip():
            raise ValueError("forecast_id must be a non-empty string")
        if not isinstance(forecast.engine_id, str) or not forecast.engine_id.strip():
            raise ValueError("engine_id must be a non-empty string")
        if forecast.decision_eligible is not False:
            raise ValueError("research forecast ledger accepts no decision-eligible/trading records")
        if forecast.calibrated_probability is not None:
            raise ValueError("this research release does not accept calibrated-probability claims")
        if not isinstance(forecast.status, str) or forecast.status not in {"forecast", "abstain"}:
            raise ValueError("forecast status must be 'forecast' or 'abstain'")
        if forecast.status == "forecast":
            if not _finite_number(forecast.forecast_value):
                raise ValueError("emitted forecasts require a finite numeric forecast_value")
            if not _finite_number(forecast.model_score):
                raise ValueError("emitted forecasts require a finite numeric model_score")
        elif forecast.forecast_value is not None or forecast.model_score is not None or forecast.direction != "ABSTAIN":
            raise ValueError("abstentions cannot carry a score or directional output")
        as_of = parse_timestamp(forecast.as_of)
        issued_at = parse_timestamp(forecast.issued_at)
        now = datetime.now(timezone.utc)
        if forecast.status == "forecast" and as_of > issued_at:
            raise ValueError("forecast as_of cannot be later than issued_at")
        if issued_at > now:
            raise ValueError("forecast issued_at cannot be in the future")
        spec = None
        if forecast.target_contract_fingerprint is not None or forecast.model_fingerprint is not None:
            try:
                spec = get_engine(forecast.engine_id)
            except KeyError as exc:
                raise ValueError("forecast engine_id is not registered") from exc
        if forecast.target_contract_fingerprint is not None and forecast.model_fingerprint is None:
            raise ValueError("registered forecasts require a model fingerprint")
        if forecast.model_fingerprint is not None:
            model_digest = _sha256_hex(forecast.model_fingerprint)
            if model_digest is None or forecast.model_fingerprint != "sha256:" + model_digest:
                raise ValueError("forecast model fingerprint must use canonical sha256:<lowercase-hex> form")
            if spec is None or forecast.model_fingerprint != engine_model_fingerprint(spec):
                raise ValueError("forecast model fingerprint does not match the registered implementation")
            if forecast.engine_version != ENGINE_VERSION:
                raise ValueError("forecast engine version does not match its registered implementation")
        if forecast.target_contract_fingerprint is not None:
            try:
                expected = registered_target_contract_fingerprint(forecast.engine_id)
            except KeyError as exc:
                raise ValueError("forecast engine_id is not registered") from exc
            if spec is None:
                raise ValueError("forecast engine_id is not registered")
            if forecast.target_contract_fingerprint != expected:
                raise ValueError("forecast target contract does not match the registered target definition")
            expected_identity = (
                spec.target,
                spec.target_unit,
                spec.horizon,
                spec.forecast_unit,
                spec.score_semantics,
            )
            actual_identity = (
                forecast.target,
                forecast.target_unit,
                forecast.horizon,
                forecast.forecast_unit,
                forecast.direction_semantics,
            )
            if actual_identity != expected_identity:
                raise ValueError("forecast target metadata does not match its registered target contract")
            contract = target_label_contract(forecast.engine_id)
            if forecast.target_label_status != contract["status"]:
                raise ValueError("forecast label status does not match its registered target contract")
            window_fields = (
                forecast.target_window_id,
                forecast.target_window_start_at,
                forecast.target_window_end_at,
            )
            if len({bool(value) for value in window_fields}) > 1:
                raise ValueError("forecast target window ID, start, and end must be supplied together")
            if forecast.target_window_id:
                contract = target_label_contract(forecast.engine_id)
                if contract["status"] != "labelable" or forecast.target_window_id not in contract["allowed_window_ids"]:
                    raise ValueError("forecast target window is not allowed by its label contract")
                start = parse_timestamp(forecast.target_window_start_at)
                end = parse_timestamp(forecast.target_window_end_at)
                if start < parse_timestamp(forecast.as_of) or end <= start:
                    raise ValueError("forecast target window must start at/after as_of and end after its start")
            if bool(forecast.label_transform_id) != bool(forecast.label_transform_hash):
                raise ValueError("forecast label-transform ID and hash must be supplied together")
            if forecast.label_transform_id and _sha256_hex(forecast.label_transform_hash) is None:
                raise ValueError("forecast label-transform hash must be a SHA-256 digest")
            if forecast.label_transform_hash:
                canonical_transform_hash = "sha256:" + _sha256_hex(forecast.label_transform_hash)
                if forecast.label_transform_hash != canonical_transform_hash:
                    raise ValueError("forecast label-transform hash must use canonical sha256:<lowercase-hex> form")
            has_label_context = forecast.label_context is not None
            has_label_context_hash = forecast.label_context_fingerprint is not None
            if has_label_context != has_label_context_hash:
                raise ValueError("forecast label context and fingerprint must be supplied together")
            if has_label_context:
                try:
                    normalized_context = normalize_label_context(forecast.label_context)
                    expected_context_hash = label_context_fingerprint(normalized_context)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"forecast label context is invalid: {exc}") from exc
                if normalized_context != dict(forecast.label_context):
                    raise ValueError("forecast label context must use its canonical normalized form")
                if forecast.label_context_fingerprint != expected_context_hash:
                    raise ValueError("forecast label-context fingerprint does not match its frozen context")
            if forecast.target_label_status == "scenario_only" and (
                forecast.target_window_id or forecast.label_transform_id or has_label_context
            ):
                raise ValueError("scenario-only target contracts cannot carry outcome-label bindings")
        else:
            legacy_window_fields = (
                forecast.target_window_id,
                forecast.target_window_start_at,
                forecast.target_window_end_at,
            )
            if any(value is not None for value in legacy_window_fields):
                if (
                    not isinstance(forecast.target_window_id, str)
                    or not forecast.target_window_id.strip()
                    or forecast.target_window_start_at is None
                    or forecast.target_window_end_at is None
                ):
                    raise ValueError("legacy forecast target window fields must be supplied together")
                legacy_start = parse_timestamp(forecast.target_window_start_at)
                legacy_end = parse_timestamp(forecast.target_window_end_at)
                if legacy_start < as_of or legacy_end <= legacy_start:
                    raise ValueError("legacy forecast target window must start at/after as_of and have positive duration")
            transform_id = forecast.label_transform_id
            transform_hash = forecast.label_transform_hash
            if transform_id is not None or transform_hash is not None:
                if (
                    not isinstance(transform_id, str)
                    or not transform_id.strip()
                    or _sha256_hex(transform_hash) is None
                ):
                    raise ValueError("legacy forecast label transform requires a non-empty ID and SHA-256 hash")
            if forecast.label_context is not None or forecast.label_context_fingerprint is not None:
                raise ValueError("legacy forecasts without a target contract cannot freeze label context")
        return self._append("forecast", forecast.forecast_id, forecast.to_dict())

    def append_outcome(self, forecast_id: str, realized_value: float, realized_unit: str,
                       observed_at: datetime | str, available_at: datetime | str,
                       ingested_at: datetime | str, source_id: str, source_hash: str,
                       rights_approved: bool, horizon_complete: bool, *,
                       target_contract_fingerprint: str | None = None,
                       target_window_id: str | None = None,
                       target_window_start_at: datetime | str | None = None,
                       target_window_end_at: datetime | str | None = None,
                       label_transform_id: str | None = None,
                       label_transform_hash: str | None = None,
                       label_context_fingerprint: str | None = None) -> str:
        """Append a final label; current forecasts require frozen target provenance."""
        return self._append_final_outcome(
            forecast_id, realized_value, realized_unit, observed_at, available_at,
            ingested_at, source_id, source_hash, rights_approved, horizon_complete,
            target_contract_fingerprint, target_window_id, target_window_start_at,
            target_window_end_at,
            label_transform_id, label_transform_hash, label_context_fingerprint,
            expected_status="forecast", evaluation_role="forecast_skill",
        )

    def append_abstention_audit_outcome(
            self, forecast_id: str, realized_value: float, realized_unit: str,
            observed_at: datetime | str, available_at: datetime | str,
            ingested_at: datetime | str, source_id: str, source_hash: str,
            rights_approved: bool, horizon_complete: bool, *,
            target_contract_fingerprint: str | None = None,
            target_window_id: str | None = None,
            target_window_start_at: datetime | str | None = None,
            target_window_end_at: datetime | str | None = None,
            label_transform_id: str | None = None,
            label_transform_hash: str | None = None,
            label_context_fingerprint: str | None = None) -> str:
        """Label an abstained attempt for coverage audits, never forecast scoring."""
        return self._append_final_outcome(
            forecast_id, realized_value, realized_unit, observed_at, available_at,
            ingested_at, source_id, source_hash, rights_approved, horizon_complete,
            target_contract_fingerprint, target_window_id, target_window_start_at,
            target_window_end_at,
            label_transform_id, label_transform_hash, label_context_fingerprint,
            expected_status="abstain", evaluation_role="abstention_audit",
        )

    def _append_final_outcome(self, forecast_id: str, realized_value: float, realized_unit: str,
                       observed_at: datetime | str, available_at: datetime | str,
                       ingested_at: datetime | str, source_id: str, source_hash: str,
                       rights_approved: bool, horizon_complete: bool,
                       target_contract_fingerprint: str | None,
                       target_window_id: str | None,
                       target_window_start_at: datetime | str | None,
                       target_window_end_at: datetime | str | None,
                       label_transform_id: str | None,
                       label_transform_hash: str | None,
                       label_context_fingerprint: str | None, *,
                       expected_status: str, evaluation_role: str) -> str:
        if not isinstance(forecast_id, str) or not forecast_id.strip():
            raise ValueError("forecast_id must be a non-empty string")
        if not isinstance(rights_approved, bool):
            raise ValueError("outcome rights_approved must be an explicit boolean attestation")
        if rights_approved is not True:
            raise ValueError("outcome data use has not been approved")
        if horizon_complete is not True:
            raise ValueError("only a final, horizon-complete outcome may be appended")
        if not isinstance(realized_unit, str) or not realized_unit.strip():
            raise ValueError("outcome realized_unit is required")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("outcome source_id is required")
        if not isinstance(source_hash, str):
            raise ValueError("outcome source hash must be a SHA-256 string")
        for name, value in (
            ("target_contract_fingerprint", target_contract_fingerprint),
            ("target_window_id", target_window_id),
            ("label_transform_id", label_transform_id),
            ("label_transform_hash", label_transform_hash),
            ("label_context_fingerprint", label_context_fingerprint),
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"outcome {name} must be a string when supplied")
        digest = source_hash.removeprefix("sha256:")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            raise ValueError("outcome source hash must be SHA-256 hex")
        if isinstance(realized_value, bool) or not isinstance(realized_value, (int, float)):
            raise ValueError("realized outcome must be numeric, not boolean or coercible string")
        try:
            value = float(realized_value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("realized outcome must be finite") from exc
        if not math.isfinite(value):
            raise ValueError("realized outcome must be finite")
        observed = parse_timestamp(observed_at)
        available = parse_timestamp(available_at)
        ingested = parse_timestamp(ingested_at)
        if available < observed or ingested < available:
            raise ValueError("outcome timestamps must satisfy observed_at <= available_at <= ingested_at")
        if available > datetime.now().astimezone() or ingested > datetime.now().astimezone():
            raise ValueError("outcome cannot be published or ingested in the future")
        with closing(self._connect()) as db:
            row = db.execute("SELECT payload_json FROM ledger_events WHERE event_type='forecast' AND event_id=?", (forecast_id,)).fetchone()
        if row is None:
            raise ValueError("outcome must reference an existing forecast record")
        forecast_payload = json.loads(row["payload_json"])
        if forecast_payload.get("status") != expected_status:
            if expected_status == "forecast":
                raise ValueError("only emitted forecasts accept forecast-skill outcomes")
            raise ValueError("abstention audit outcomes require an abstained forecast")
        if observed <= parse_timestamp(forecast_payload["as_of"]):
            raise ValueError("outcome observation must occur after the forecast cutoff")
        if realized_unit != forecast_payload["target_unit"]:
            raise ValueError("outcome unit does not match the forecast target unit")
        expected_contract = forecast_payload.get("target_contract_fingerprint")
        if expected_contract:
            if target_contract_fingerprint != expected_contract:
                raise ValueError("outcome target contract does not match the forecast's frozen target contract")
            if forecast_payload.get("target_label_status") != "labelable":
                raise ValueError("scenario-only target contracts cannot accept outcome labels")
            expected_window_id = forecast_payload.get("target_window_id")
            expected_window_start = forecast_payload.get("target_window_start_at")
            expected_window_end = forecast_payload.get("target_window_end_at")
            if not expected_window_id or not expected_window_start or not expected_window_end:
                raise ValueError("forecast has no frozen target window and cannot accept an outcome label")
            if (
                target_window_id != expected_window_id
                or target_window_start_at is None
                or target_window_end_at is None
            ):
                raise ValueError("outcome target window does not match the frozen forecast window")
            supplied_window_start = parse_timestamp(target_window_start_at)
            supplied_window_end = parse_timestamp(target_window_end_at)
            frozen_window_start = parse_timestamp(expected_window_start)
            frozen_window_end = parse_timestamp(expected_window_end)
            if (
                supplied_window_start != frozen_window_start
                or supplied_window_end != frozen_window_end
                or observed != frozen_window_end
            ):
                raise ValueError("final outcome must resolve at the forecast's exact target-window end")
            if not isinstance(label_transform_id, str) or not label_transform_id.strip():
                raise ValueError("contract-bound outcomes require the frozen label_transform_id")
            normalized_transform_hash = _sha256_hex(label_transform_hash)
            if normalized_transform_hash is None:
                raise ValueError("contract-bound outcomes require the frozen SHA-256 label_transform_hash")
            transform_id = label_transform_id.strip()
            if transform_id != forecast_payload.get("label_transform_id") or (
                "sha256:" + normalized_transform_hash
            ) != forecast_payload.get("label_transform_hash"):
                raise ValueError("outcome label transform does not match the transform frozen at forecast time")
            expected_context_hash = forecast_payload.get("label_context_fingerprint")
            if (
                not expected_context_hash
                or label_context_fingerprint != expected_context_hash
                or not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", label_context_fingerprint or "")
            ):
                raise ValueError("outcome label context does not match the forecast's frozen measurement context")
            contract_binding = "bound_attested"
        else:
            if target_contract_fingerprint is not None:
                raise ValueError("legacy forecast has no target contract to bind")
            if label_context_fingerprint is not None:
                raise ValueError("legacy forecast has no frozen label context to bind")
            if bool(label_transform_id) != bool(label_transform_hash):
                raise ValueError("label_transform_id and label_transform_hash must be supplied together")
            if label_transform_id is not None and not label_transform_id.strip():
                raise ValueError("label_transform_id cannot be empty")
            transform_id = label_transform_id.strip() if label_transform_id else None
            normalized_transform_hash = _sha256_hex(label_transform_hash) if label_transform_hash else None
            if label_transform_hash and normalized_transform_hash is None:
                raise ValueError("label_transform_hash must be a SHA-256 digest")
            frozen_transform_id = forecast_payload.get("label_transform_id")
            frozen_transform_hash = _sha256_hex(forecast_payload.get("label_transform_hash"))
            if frozen_transform_id is not None or forecast_payload.get("label_transform_hash") is not None:
                if (
                    not isinstance(frozen_transform_id, str)
                    or not frozen_transform_id.strip()
                    or frozen_transform_hash is None
                    or transform_id != frozen_transform_id.strip()
                    or normalized_transform_hash != frozen_transform_hash
                ):
                    raise ValueError("legacy outcome label transform does not match the transform frozen at forecast time")

            frozen_window = (
                forecast_payload.get("target_window_id"),
                forecast_payload.get("target_window_start_at"),
                forecast_payload.get("target_window_end_at"),
            )
            supplied_window = (target_window_id, target_window_start_at, target_window_end_at)
            if any(value is not None for value in frozen_window):
                if (
                    not isinstance(frozen_window[0], str)
                    or not frozen_window[0].strip()
                    or any(value is None for value in frozen_window[1:])
                    or target_window_id != frozen_window[0]
                    or target_window_start_at is None
                    or target_window_end_at is None
                ):
                    raise ValueError("legacy outcome target window must match the window frozen at forecast time")
            elif any(value is not None for value in supplied_window):
                raise ValueError("legacy outcome cannot add a target window after forecast time")

            if any(value is not None for value in supplied_window):
                if not isinstance(target_window_id, str) or not target_window_id.strip():
                    raise ValueError("legacy outcome target window ID, start, and end must be supplied together")
                supplied_window_start = parse_timestamp(target_window_start_at)
                supplied_window_end = parse_timestamp(target_window_end_at)
                if supplied_window_start < parse_timestamp(forecast_payload["as_of"]):
                    raise ValueError("legacy outcome target window cannot start before the forecast cutoff")
                if (
                    supplied_window_end != observed
                    or supplied_window_end <= supplied_window_start
                    or supplied_window_start != parse_timestamp(frozen_window[1])
                    or supplied_window_end != parse_timestamp(frozen_window[2])
                ):
                    raise ValueError("legacy outcome must resolve at its exact frozen target-window end")
            contract_binding = "legacy_unbound"
        payload = {
            "forecast_id": forecast_id,
            "realized_value": value,
            "realized_unit": realized_unit,
            "observed_at": observed.isoformat(),
            "available_at": available.isoformat(),
            "ingested_at": ingested.isoformat(),
            "source_id": source_id,
            "source_hash": digest,
            "rights_approved": True,
            "horizon_complete": True,
            "evaluation_role": evaluation_role,
            "target_contract_fingerprint": expected_contract,
            "target_contract_binding": contract_binding,
            "target_window_id": target_window_id,
            "target_window_start_at": (
                parse_timestamp(target_window_start_at).isoformat()
                if target_window_start_at is not None else None
            ),
            "target_window_end_at": (
                parse_timestamp(target_window_end_at).isoformat()
                if target_window_end_at is not None else None
            ),
            "label_transform_id": transform_id,
            "label_transform_hash": normalized_transform_hash,
            "label_context_fingerprint": label_context_fingerprint,
        }
        return self._append(
            "outcome", f"outcome:{forecast_id}:{payload['observed_at']}", payload,
            unique_outcome_forecast_id=forecast_id,
        )

    def coverage_records(self, as_of: datetime | str) -> dict[str, Any]:
        """Join attempts to labels available by a cutoff after verifying the hash chain."""
        cutoff = parse_timestamp(as_of)
        if cutoff > datetime.now(timezone.utc):
            raise ValueError("evaluation cutoff cannot be in the future")
        with closing(self._connect()) as db:
            db.execute("BEGIN")
            events = db.execute(
                "SELECT seq,event_type,event_id,payload_json,prev_hash,event_hash,created_at "
                "FROM ledger_events ORDER BY seq"
            ).fetchall()
            integrity = self._verify_rows(events)
            db.execute("ROLLBACK")
        if not integrity["valid"]:
            raise ValueError(f"ledger hash chain is invalid at sequence {integrity['failed_seq']}")

        all_forecasts: dict[str, dict[str, Any]] = {}
        forecasts: dict[str, dict[str, Any]] = {}
        outcomes: dict[str, list[dict[str, Any]]] = {}
        unmatched_outcomes = 0
        unmatured_outcomes = 0
        out_of_scope_outcomes = 0
        invalid_outcomes = 0
        unbound_target_contract_outcomes = 0
        target_contract_mismatch_outcomes = 0
        invalid_label_transform_outcomes = 0
        invalid_target_window_outcomes = 0
        invalid_label_context_outcomes = 0
        invalid_forecasts = 0
        not_yet_recorded_forecasts = 0
        not_yet_recorded_outcomes = 0
        for row in events:
            payload = json.loads(row["payload_json"])
            if row["event_type"] == "forecast":
                forecast_id = payload.get("forecast_id")
                if not isinstance(forecast_id, str) or forecast_id != row["event_id"]:
                    invalid_forecasts += 1
                    continue
                all_forecasts[forecast_id] = payload
                forecast_value = payload.get("forecast_value")
                model_score = payload.get("model_score")
                status = payload.get("status")
                model_fingerprint = payload.get("model_fingerprint")
                model_digest = _sha256_hex(model_fingerprint)
                target_contract_fingerprint = payload.get("target_contract_fingerprint")
                model_identity_invalid = (
                    target_contract_fingerprint is not None and model_fingerprint is None
                ) or (
                    model_fingerprint is not None and (
                        model_digest is None
                        or model_fingerprint != "sha256:" + model_digest
                        or not isinstance(payload.get("engine_version"), str)
                        or not payload["engine_version"].strip()
                    )
                )
                numeric_forecast = _finite_number(forecast_value) and _finite_number(model_score)
                if (
                    payload.get("decision_eligible") is not False
                    or payload.get("calibrated_probability") is not None
                    or model_identity_invalid
                    or not isinstance(status, str)
                    or status not in {"forecast", "abstain"}
                    or any(
                        not isinstance(payload.get(field), str) or not payload[field].strip()
                        for field in (
                            "engine_id", "horizon", "target", "target_unit",
                            "forecast_unit", "direction", "direction_semantics",
                        )
                    )
                    or not isinstance(payload.get("symbol"), str)
                    or (status == "forecast" and not numeric_forecast)
                    or (status == "abstain" and (
                        forecast_value is not None or model_score is not None
                        or payload.get("direction") != "ABSTAIN"
                    ))
                ):
                    invalid_forecasts += 1
                    continue
                try:
                    created = parse_timestamp(row["created_at"])
                    issued = parse_timestamp(payload["issued_at"])
                    as_of_time = parse_timestamp(payload["as_of"])
                except (KeyError, TypeError, ValueError):
                    invalid_forecasts += 1
                    continue
                if created > cutoff:
                    not_yet_recorded_forecasts += 1
                    continue
                if as_of_time > issued and status == "forecast":
                    invalid_forecasts += 1
                    continue
                if issued <= cutoff:
                    forecasts[row["event_id"]] = payload
        for row in events:
            if row["event_type"] != "outcome":
                continue
            payload = json.loads(row["payload_json"])
            try:
                event_created = parse_timestamp(row["created_at"])
            except (TypeError, ValueError):
                invalid_outcomes += 1
                continue
            if event_created > cutoff:
                not_yet_recorded_outcomes += 1
                continue
            forecast_id = payload.get("forecast_id")
            if not isinstance(forecast_id, str) or forecast_id not in all_forecasts:
                unmatched_outcomes += 1
                continue
            if forecast_id not in forecasts:
                out_of_scope_outcomes += 1
                continue
            try:
                observed = parse_timestamp(payload["observed_at"])
                available = parse_timestamp(payload["available_at"])
                ingested = parse_timestamp(payload["ingested_at"])
                forecast_as_of = parse_timestamp(forecasts[forecast_id]["as_of"])
            except (KeyError, TypeError, ValueError):
                invalid_outcomes += 1
                continue
            if available > cutoff or ingested > cutoff:
                unmatured_outcomes += 1
                continue
            if not (forecast_as_of < observed <= available <= ingested):
                invalid_outcomes += 1
                continue
            forecast_payload = forecasts[forecast_id]
            realized_raw = payload.get("realized_value")
            if not _finite_number(realized_raw):
                invalid_outcomes += 1
                continue
            try:
                realized_value = float(realized_raw)
            except (OverflowError, ValueError):
                invalid_outcomes += 1
                continue
            if not math.isfinite(realized_value):
                invalid_outcomes += 1
                continue
            source_id = payload.get("source_id")
            source_digest = _sha256_hex(payload.get("source_hash"))
            expected_role = (
                "forecast_skill" if forecast_payload.get("status") == "forecast"
                else "abstention_audit"
            )
            role = payload.get("evaluation_role")
            if role is None and expected_role == "forecast_skill":
                role = expected_role  # legacy forecast labels predate explicit role tags
            if (
                payload.get("rights_approved") is not True
                or payload.get("horizon_complete") is not True
                or payload.get("realized_unit") != forecast_payload.get("target_unit")
                or not isinstance(source_id, str)
                or not source_id.strip()
                or source_digest is None
                or role != expected_role
            ):
                invalid_outcomes += 1
                continue
            expected_contract = forecast_payload.get("target_contract_fingerprint")
            outcome_contract = payload.get("target_contract_fingerprint")
            if expected_contract:
                if outcome_contract != expected_contract or payload.get("target_contract_binding") != "bound_attested":
                    invalid_outcomes += 1
                    target_contract_mismatch_outcomes += 1
                    continue
                expected_window_id = forecast_payload.get("target_window_id")
                expected_window_start = forecast_payload.get("target_window_start_at")
                expected_window_end = forecast_payload.get("target_window_end_at")
                if (
                    forecast_payload.get("target_label_status") != "labelable"
                    or not expected_window_id
                    or not expected_window_start
                    or not expected_window_end
                    or payload.get("target_window_id") != expected_window_id
                ):
                    invalid_outcomes += 1
                    invalid_target_window_outcomes += 1
                    continue
                try:
                    frozen_start = parse_timestamp(expected_window_start)
                    payload_start = parse_timestamp(payload.get("target_window_start_at"))
                    frozen_end = parse_timestamp(expected_window_end)
                    payload_end = parse_timestamp(payload.get("target_window_end_at"))
                except (TypeError, ValueError):
                    invalid_outcomes += 1
                    invalid_target_window_outcomes += 1
                    continue
                if payload_start != frozen_start or payload_end != frozen_end or observed != frozen_end:
                    invalid_outcomes += 1
                    invalid_target_window_outcomes += 1
                    continue
                transform_hash = _sha256_hex(payload.get("label_transform_hash"))
                transform_id = payload.get("label_transform_id")
                if (
                    transform_hash is None
                    or not isinstance(transform_id, str)
                    or not transform_id.strip()
                    or transform_id != forecast_payload.get("label_transform_id")
                    or "sha256:" + transform_hash != forecast_payload.get("label_transform_hash")
                ):
                    invalid_outcomes += 1
                    invalid_label_transform_outcomes += 1
                    continue
                expected_context_hash = forecast_payload.get("label_context_fingerprint")
                try:
                    frozen_context = normalize_label_context(forecast_payload.get("label_context"))
                    recomputed_context_hash = label_context_fingerprint(frozen_context)
                except (TypeError, ValueError):
                    recomputed_context_hash = None
                if (
                    not isinstance(expected_context_hash, str)
                    or not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", expected_context_hash)
                    or recomputed_context_hash != expected_context_hash
                    or payload.get("label_context_fingerprint") != expected_context_hash
                ):
                    invalid_outcomes += 1
                    invalid_label_context_outcomes += 1
                    continue
            else:
                if outcome_contract is not None:
                    invalid_outcomes += 1
                    target_contract_mismatch_outcomes += 1
                    continue
                transform_hash = _sha256_hex(payload.get("label_transform_hash"))
                transform_id = payload.get("label_transform_id")
                if bool(transform_id) != bool(payload.get("label_transform_hash")) or (
                    payload.get("label_transform_hash") and transform_hash is None
                ):
                    invalid_outcomes += 1
                    invalid_label_transform_outcomes += 1
                    continue
                frozen_transform_id = forecast_payload.get("label_transform_id")
                frozen_transform_hash = _sha256_hex(forecast_payload.get("label_transform_hash"))
                if frozen_transform_id is not None or forecast_payload.get("label_transform_hash") is not None:
                    if (
                        not isinstance(frozen_transform_id, str)
                        or not frozen_transform_id.strip()
                        or frozen_transform_hash is None
                        or transform_id != frozen_transform_id.strip()
                        or transform_hash != frozen_transform_hash
                    ):
                        invalid_outcomes += 1
                        invalid_label_transform_outcomes += 1
                        continue

                frozen_window = (
                    forecast_payload.get("target_window_id"),
                    forecast_payload.get("target_window_start_at"),
                    forecast_payload.get("target_window_end_at"),
                )
                outcome_window = (
                    payload.get("target_window_id"),
                    payload.get("target_window_start_at"),
                    payload.get("target_window_end_at"),
                )
                if any(value is not None for value in frozen_window + outcome_window):
                    try:
                        if (
                            not isinstance(frozen_window[0], str)
                            or not frozen_window[0].strip()
                            or any(not isinstance(value, str) for value in frozen_window[1:])
                            or not isinstance(outcome_window[0], str)
                            or not outcome_window[0].strip()
                            or any(not isinstance(value, str) for value in outcome_window[1:])
                            or outcome_window[0] != frozen_window[0]
                        ):
                            raise ValueError("legacy target window is not frozen to the forecast")
                        frozen_start = parse_timestamp(frozen_window[1])
                        frozen_end = parse_timestamp(frozen_window[2])
                        outcome_start = parse_timestamp(outcome_window[1])
                        outcome_end = parse_timestamp(outcome_window[2])
                        legacy_window_valid = (
                            forecast_as_of <= frozen_start < frozen_end
                            and outcome_start == frozen_start
                            and outcome_end == frozen_end == observed
                        )
                    except (TypeError, ValueError):
                        legacy_window_valid = False
                    if not legacy_window_valid:
                        invalid_outcomes += 1
                        invalid_target_window_outcomes += 1
                        continue
                unbound_target_contract_outcomes += 1
            outcomes.setdefault(forecast_id, []).append({
                "realized_value": realized_value,
                "realized_unit": payload.get("realized_unit"),
                "observed_at": payload.get("observed_at"),
                "available_at": payload.get("available_at"),
                "ingested_at": payload.get("ingested_at"),
                "source_id": payload.get("source_id"),
                "source_hash": source_digest,
                "rights_approved": payload.get("rights_approved"),
                "horizon_complete": payload.get("horizon_complete", True),
                "evaluation_role": role,
                "target_contract_fingerprint": outcome_contract,
                "target_contract_binding": payload.get("target_contract_binding", "legacy_unbound"),
                "target_window_id": payload.get("target_window_id"),
                "target_window_start_at": payload.get("target_window_start_at"),
                "target_window_end_at": payload.get("target_window_end_at"),
                "label_transform_id": transform_id,
                "label_transform_hash": transform_hash,
                "label_context_fingerprint": payload.get("label_context_fingerprint"),
            })

        fields = (
            "forecast_id", "engine_id", "symbol", "as_of", "issued_at", "horizon",
            "target", "target_unit", "status", "direction", "direction_semantics", "forecast_value",
            "forecast_unit", "model_fingerprint", "abstain_reasons",
            "target_contract_fingerprint",
            "target_label_status", "target_window_id", "target_window_end_at",
            "target_window_start_at",
            "label_transform_id", "label_transform_hash",
            "label_context", "label_context_fingerprint",
        )
        records = []
        for forecast_id, payload in forecasts.items():
            summary = {field: payload.get(field) for field in fields}
            summary["outcomes"] = outcomes.get(forecast_id, [])
            records.append(summary)
        return {
            "evaluation_as_of": cutoff.isoformat(),
            "ledger_integrity": integrity,
            "records": sorted(records, key=lambda item: (item["as_of"], item["forecast_id"])),
            "unmatched_outcome_count": unmatched_outcomes,
            "unmatured_outcome_count": unmatured_outcomes,
            "out_of_scope_outcome_count": out_of_scope_outcomes,
            "invalid_outcome_count": invalid_outcomes,
            "unbound_target_contract_outcome_count": unbound_target_contract_outcomes,
            "target_contract_mismatch_outcome_count": target_contract_mismatch_outcomes,
            "invalid_label_transform_outcome_count": invalid_label_transform_outcomes,
            "invalid_target_window_outcome_count": invalid_target_window_outcomes,
            "invalid_label_context_outcome_count": invalid_label_context_outcomes,
            "invalid_forecast_count": invalid_forecasts,
            "not_yet_recorded_forecast_count": not_yet_recorded_forecasts,
            "not_yet_recorded_outcome_count": not_yet_recorded_outcomes,
        }

    def _append(self, event_type: str, event_id: str, payload: Mapping[str, Any], *,
                unique_outcome_forecast_id: str | None = None) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            existing_events = db.execute(
                "SELECT seq,event_type,event_id,payload_json,prev_hash,event_hash,created_at "
                "FROM ledger_events ORDER BY seq"
            ).fetchall()
            integrity = self._verify_rows(existing_events)
            if not integrity["valid"]:
                db.execute("ROLLBACK")
                raise ValueError(
                    "cannot append to a ledger with an invalid hash chain "
                    f"at sequence {integrity['failed_seq']}"
                )
            if unique_outcome_forecast_id is not None:
                try:
                    db.execute(
                        "INSERT INTO ledger_final_outcomes(forecast_id,event_id) VALUES(?,?)",
                        (unique_outcome_forecast_id, event_id),
                    )
                except sqlite3.IntegrityError as exc:
                    db.execute("ROLLBACK")
                    raise ValueError("a final outcome is already recorded for this forecast") from exc
            row = db.execute("SELECT event_hash FROM ledger_events ORDER BY seq DESC LIMIT 1").fetchone()
            previous = row["event_hash"] if row else _GENESIS
            created_at = datetime.now().astimezone().isoformat()
            digest = _event_digest(previous, event_type, event_id, canonical, created_at)
            db.execute("INSERT INTO ledger_events(event_type,event_id,payload_json,prev_hash,event_hash,created_at) VALUES(?,?,?,?,?,?)",
                       (event_type, event_id, canonical, previous, digest, created_at))
            db.execute("COMMIT")
        return digest

    def verify(self) -> dict[str, Any]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT seq,event_type,event_id,payload_json,prev_hash,event_hash,created_at FROM ledger_events ORDER BY seq").fetchall()
        return self._verify_rows(rows)

    @staticmethod
    def _verify_rows(rows: list[sqlite3.Row]) -> dict[str, Any]:
        previous = _GENESIS
        for expected_seq, row in enumerate(rows, start=1):
            try:
                payload = json.loads(row["payload_json"])
                if not isinstance(payload, dict):
                    raise ValueError("ledger payload must be a JSON object")
                canonical = json.dumps(
                    payload, sort_keys=True, separators=(",", ":"), allow_nan=False
                )
                digest = _event_digest(
                    previous, row["event_type"], row["event_id"], canonical,
                    row["created_at"],
                )
            except (json.JSONDecodeError, TypeError, ValueError, OverflowError):
                return {"valid": False, "checked": expected_seq - 1, "failed_seq": row["seq"]}
            if (row["seq"] != expected_seq or row["prev_hash"] != previous
                    or row["payload_json"] != canonical or row["event_hash"] != digest):
                return {"valid": False, "checked": expected_seq - 1, "failed_seq": row["seq"]}
            previous = digest
        return {"valid": True, "checked": len(rows), "head_hash": previous}
