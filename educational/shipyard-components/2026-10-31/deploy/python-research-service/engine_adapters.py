"""Research-only adapters for the pinned Saty and Raschke engines.

No broker, portfolio, order, fill, or execution modules are imported here.
Inputs must carry explicit data, session, reference, and event-coverage lineage.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

# Pinned Saty modules use the historical top-level import ``saty_reference``.
# Share those exact classes with the package modules instead of loading duplicate
# Bar/Session classes under two different module names.
_SATY_ENGINE_DIR = Path(__file__).resolve().parent / "research" / "saty_mahajan" / "engine"
if str(_SATY_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_SATY_ENGINE_DIR))

from saty_reference import Bar as SatyBar
from saty_reference import Session as SatySession
from research.saty_mahajan.engine.saty_system.models import (
    Observation as SatyObservation,
    Reference as SatyReference,
)
from research.saty_mahajan.engine.saty_system.structure import FeatureBook, StructureConfig
from research.saty_mahajan.engine.saty_system.strategies import StrategyConfig, StrategyEngine
from research.linda_raschke.v02.engine.rre.raschke_core import Bar as RreBar
from research.linda_raschke.v02.engine.rre.raschke_core import Session as RreSession
from research.linda_raschke.v02.engine.rre.raschke_engine import (
    PolicyConfig,
    PolicyEngine,
    PriorSessionReference,
)


UTC = timezone.utc
MAX_ROWS = 12000
MAX_EVENT_ROWS = 4096
MAX_SOURCE_AGE_SECONDS = 900


def _dt(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name}: ISO timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{name}: timezone-aware timestamp required")
    return result.astimezone(UTC)


def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: number required")
    result = float(value)
    if not (result == result and abs(result) != float("inf")):
        raise ValueError(f"{name}: finite number required")
    if positive and result <= 0:
        raise ValueError(f"{name}: positive number required")
    return result


def _coverage(payload: dict[str, Any], *, require_events: bool) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    source = payload.get("source")
    if not isinstance(source, dict):
        blockers.append("SOURCE_LINEAGE_MISSING")
    else:
        for key in ("provider", "feed", "adjustment", "venue"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                blockers.append("SOURCE_" + key.upper() + "_MISSING")
        if source.get("provider") != "alpaca":
            blockers.append("UNEXPECTED_PROVIDER")
        if source.get("feed") not in ("iex", "sip"):
            blockers.append("UNEXPECTED_FEED")
        if source.get("adjustment") != "raw":
            blockers.append("UNEXPECTED_ADJUSTMENT")
    coverage = payload.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("status") != "complete":
        blockers.append("DATA_COVERAGE_NOT_COMPLETE")
    elif not coverage.get("captured_at") or not coverage.get("provider_received_at"):
        blockers.append("SOURCE_RECEIPT_TIME_MISSING")
    else:
        now = datetime.now(UTC)
        for label, value in (("CAPTURE", coverage["captured_at"]),
                             ("PROVIDER_RECEIPT", coverage["provider_received_at"])):
            stamp = _dt(value, "coverage." + label.lower())
            age = (now - stamp).total_seconds()
            if age < -60:
                blockers.append(label + "_TIME_IN_FUTURE")
            elif age > MAX_SOURCE_AGE_SECONDS:
                blockers.append("STALE_" + label + "_TIME")
    calendar = payload.get("calendar")
    if not isinstance(calendar, dict) or not calendar.get("version") or not calendar.get("provider"):
        blockers.append("OFFICIAL_CALENDAR_LINEAGE_MISSING")
    elif not calendar.get("retrieved_at"):
        blockers.append("OFFICIAL_CALENDAR_RECEIPT_TIME_MISSING")
    else:
        _dt(calendar["retrieved_at"], "calendar.retrieved_at")
    if require_events:
        events = payload.get("event_coverage")
        if not isinstance(events, dict) or (events.get("status") != "complete" or events.get("scope_complete") is not True):
            blockers.append("EVENT_COVERAGE_UNKNOWN_OR_INCOMPLETE")
        elif not events.get("source") or not events.get("version") or not events.get("captured_at"):
            blockers.append("EVENT_COVERAGE_LINEAGE_MISSING")
        else:
            event_capture = _dt(events["captured_at"], "event_coverage.captured_at")
            event_age = (datetime.now(UTC) - event_capture).total_seconds()
            if event_age < -60:
                blockers.append("EVENT_COVERAGE_TIME_IN_FUTURE")
            elif event_age > MAX_SOURCE_AGE_SECONDS:
                blockers.append("STALE_EVENT_COVERAGE")
            if not isinstance(events.get("events"), list):
                blockers.append("EVENT_LIST_MISSING")
            elif len(events["events"]) > MAX_EVENT_ROWS:
                blockers.append("EVENT_LIST_EXCEEDS_LIMIT")
            if not events.get("covered_from") or not events.get("covered_until"):
                blockers.append("EVENT_COVERAGE_WINDOW_MISSING")
            else:
                _dt(events["covered_from"], "event_coverage.covered_from")
                _dt(events["covered_until"], "event_coverage.covered_until")
    return coverage if isinstance(coverage, dict) else {}, blockers


def _event_overlaps(event_coverage: dict[str, Any], start: datetime, end: datetime) -> bool:
    events = event_coverage.get("events", [])
    for event in events:
        if not isinstance(event, dict) or not event.get("start") or not event.get("end"):
            raise ValueError("event records require start and end timestamps")
        if _dt(event["start"], "event.start") < end and _dt(event["end"], "event.end") > start:
            return True
    return False



def _json_value(value: Any) -> Any:
    """Serialize the pinned Signal dataclass without changing its source model."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def run_saty(payload: dict[str, Any]) -> dict[str, Any]:
    coverage, blockers = _coverage(payload, require_events=False)
    symbol = payload.get("symbol")
    observations = payload.get("observations")
    sessions = payload.get("sessions")
    windows = payload.get("reference_windows")
    references = payload.get("references")
    if not isinstance(symbol, str) or not symbol.strip():
        blockers.append("SYMBOL_MISSING")
    if not all(isinstance(x, list) for x in (observations, sessions, windows, references)):
        blockers.append("SCHEDULE_OR_BAR_INPUTS_MISSING")
    if blockers:
        return {"status": "blocked", "blockers": sorted(set(blockers)), "signals": [], "coverage": coverage}
    if len(observations) > MAX_ROWS or len(sessions) > 4096 or len(windows) > 4096 or len(references) > 4096:
        raise ValueError("Saty request exceeds bounded input limits")
    receipt_at = _dt(coverage["provider_received_at"], "coverage.provider_received_at")

    by_tf: dict[str, list[dict[str, Any]]] = {"10m": [], "1H": []}
    for row in observations:
        if not isinstance(row, dict) or row.get("symbol") != symbol:
            raise ValueError("Saty observations must match the request symbol")
        tf = row.get("timeframe")
        if tf not in by_tf:
            raise ValueError("Saty accepts independently supplied 10m and 1H observations only")
        by_tf[tf].append(row)
    counts = {tf: len(rows) for tf, rows in by_tf.items()}
    warmup_blockers = [f"WARMUP_INCOMPLETE:{tf}:{count}/1000" for tf, count in counts.items() if count < 1000]
    if warmup_blockers:
        return {"status": "blocked", "blockers": warmup_blockers, "signals": [], "bar_counts": counts,
                "coverage": coverage}

    session_rows = [SatySession(**{**row, **{k: _dt(row[k], f"session.{k}") for k in
                       ("open", "entry_start", "entry_cutoff", "flat_at", "close")}}) for row in sessions]
    reference_rows = [SatyReference(**{**row, **{k: _dt(row[k], f"reference.{k}") for k in
                         ("period_end", "available_at", "valid_from", "valid_until")}}) for row in references]
    cfg = StructureConfig(required_timeframes=("10m", "1H"), warmup_bars=1000,
                          warmup_by_timeframe={"10m": 1000, "1H": 1000},
                          require_session=True, require_same_provider=True, max_history=2048,
                          carry_previous_session_timeframes=("1H",))
    book = FeatureBook(cfg)
    for session in session_rows:
        book.register_session(session)
    for row in windows:
        if row.get("symbol") != symbol:
            raise ValueError("reference calendar symbol mismatch")
        book.register_reference_period(
            symbol, row["horizon"], _dt(row["valid_from"], "reference_window.valid_from"),
            _dt(row["valid_until"], "reference_window.valid_until"),
            _dt(row["previous_period_end"], "reference_window.previous_period_end"),
            _dt(row["known_at"], "reference_window.known_at"),
        )
    parsed: list[SatyObservation] = []
    for row in observations:
        bar = dict(row["bar"])
        for key in ("start", "end"):
            bar[key] = _dt(bar[key], "bar." + key)
        observation = SatyObservation(
            symbol=row["symbol"], timeframe=row["timeframe"], bar=SatyBar(**bar),
            available_at=_dt(row["available_at"], "observation.available_at"),
            provider=row["provider"], venue=row["venue"], session_policy=row["session_policy"],
            adjustment=row["adjustment"], revision=row["revision"],
        )
        if observation.available_at != receipt_at:
            raise ValueError("historical availability is unknown; use the actual snapshot receipt time")
        observation.validate()
        parsed.append(observation)
    parsed.sort(key=lambda o: (o.available_at, 0 if o.timeframe == "1H" else 1, o.bar.end))
    strategy = StrategyEngine(StrategyConfig())
    signals: list[dict[str, Any]] = []
    ref_by_time = sorted(reference_rows, key=lambda r: r.valid_from)
    sessions_by_id = {s.session_id: s for s in session_rows}
    for observation in parsed:
        book.update(observation)
    # Historical bars build present-time features only. Historical provider
    # availability is unknown, so evaluate once at the latest completed bar.
    latest_10m = max((o for o in parsed if o.timeframe == "10m"), key=lambda o: o.bar.end)
    evaluated_at = receipt_at
    session = sessions_by_id.get(next(
        (s.session_id for s in session_rows if s.open <= latest_10m.bar.start < s.close), ""))
    reference = next((r for r in reversed(ref_by_time)
                      if r.valid_from <= evaluated_at < r.valid_until and r.available_at <= evaluated_at), None)
    if session is None:
        blockers.append("CURRENT_SESSION_UNAVAILABLE")
    elif not session.open <= evaluated_at <= session.close:
        blockers.append("SNAPSHOT_OUTSIDE_CURRENT_SESSION")
    elif reference is None:
        blockers.append("CURRENT_SESSION_REFERENCE_UNAVAILABLE")
    elif (evaluated_at - latest_10m.bar.end).total_seconds() > MAX_SOURCE_AGE_SECONDS:
        blockers.append("LATEST_10M_BAR_STALE")
    else:
        context = book.context(symbol, "10m", evaluated_at, reference, session)
        signals.extend(_json_value(asdict(signal)) for signal in strategy.update(context))
    final_bar = max(parsed, key=lambda o: o.bar.end)
    if counts["10m"] < 1000 or counts["1H"] < 1000:
        blockers.append("WARMUP_INCOMPLETE")
    return {
        "status": "blocked" if blockers else "complete",
        "blockers": sorted(set(blockers)),
        "signals": signals,
        "bar_counts": counts,
        "engine": {"name": "Saty Adaptive Opportunity Engine", "version": "0.3.0",
                   "source_commit": "d59263b75b0aed4f69c56b56dd78c7c436d23c5c"},
        "input_timestamps": {"latest_bar_end": final_bar.bar.end.isoformat(),
                             "latest_available_at": final_bar.available_at.isoformat(),
                             "source_capture_at": coverage.get("captured_at")},
        "coverage": coverage,
        "diagnostics": strategy.counters,
    }


def run_rre(payload: dict[str, Any]) -> dict[str, Any]:
    coverage, blockers = _coverage(payload, require_events=True)
    symbol = payload.get("symbol")
    bars = payload.get("bars")
    sessions = payload.get("sessions")
    reference_data = payload.get("prior_session_reference")
    if not isinstance(symbol, str) or not symbol.strip():
        blockers.append("SYMBOL_MISSING")
    if not isinstance(bars, list) or not isinstance(sessions, list) or not isinstance(reference_data, dict):
        blockers.append("RRE_BASELINE_OR_BAR_INPUTS_MISSING")
    if blockers:
        events = payload.get("event_coverage")
        event_summary = None
        if isinstance(events, dict):
            event_summary = {key: events.get(key) for key in
                             ("source", "version", "captured_at", "covered_from", "covered_until", "status", "scope_complete", "exclusions")}
        return {"status": "blocked", "blockers": sorted(set(blockers)), "intents": [],
                "coverage": coverage, "event_coverage": event_summary}
    if len(bars) > MAX_ROWS or len(sessions) > 4096:
        raise ValueError("RRE request exceeds bounded input limits")

    session_rows = [RreSession(row["id"], _dt(row["open"], "session.open"),
                               _dt(row["close"], "session.close"), row.get("previous_id"))
                    for row in sessions]
    session_by_id = {s.id: s for s in session_rows}
    current_id = reference_data.get("session_id")
    current_session = session_by_id.get(current_id)
    previous_session_id = reference_data.get("previous_session_id")
    previous_session = session_by_id.get(previous_session_id)
    if current_session is None or previous_session is None:
        return {"status": "blocked", "blockers": ["CURRENT_OR_PRIOR_SESSION_NOT_IN_OFFICIAL_CALENDAR"],
                "intents": [], "coverage": coverage}
    if reference_data.get("complete") is not True:
        return {"status": "blocked", "blockers": ["PRIOR_SESSION_BASELINE_INCOMPLETE"],
                "intents": [], "coverage": coverage}
    series_id = reference_data.get("series_id")
    calendar_version = reference_data.get("calendar_version")
    if not series_id or not calendar_version:
        return {"status": "blocked", "blockers": ["REFERENCE_SERIES_OR_CALENDAR_VERSION_MISSING"],
                "intents": [], "coverage": coverage}
    reference = PriorSessionReference(
        symbol=symbol, session_id=current_session.id, previous_session=previous_session,
        available_at=_dt(reference_data["available_at"], "prior_session_reference.available_at"),
        high=_finite_number(reference_data["high"], "prior_session_reference.high", positive=True),
        low=_finite_number(reference_data["low"], "prior_session_reference.low", positive=True),
        close=_finite_number(reference_data["close"], "prior_session_reference.close", positive=True),
        series_id=series_id, calendar_version=calendar_version, complete=True,
    )
    event_coverage = payload["event_coverage"]
    receipt_at = _dt(coverage["provider_received_at"], "coverage.provider_received_at")
    covered_from = _dt(event_coverage["covered_from"], "event_coverage.covered_from")
    covered_until = _dt(event_coverage["covered_until"], "event_coverage.covered_until")
    if not covered_from <= current_session.open <= current_session.close <= covered_until:
        return {"status": "blocked", "blockers": ["EVENT_COVERAGE_DOES_NOT_SPAN_SESSION"],
                "intents": [], "coverage": coverage}
    if not current_session.open <= receipt_at <= current_session.close:
        return {"status": "blocked", "blockers": ["SNAPSHOT_OUTSIDE_CURRENT_SESSION"],
                "intents": [], "coverage": coverage}

    policy = PolicyEngine(PolicyConfig(
        tick_size=_finite_number(payload.get("tick_size"), "tick_size", positive=True),
        series_id=series_id, calendar_version=calendar_version,
        variant=payload.get("variant", "RRE2"),
        cost_reserve_price=_finite_number(payload.get("cost_reserve_price", 0), "cost_reserve_price"),
    ))
    intents: list[dict[str, Any]] = []
    ordered = sorted(bars, key=lambda row: _dt(row["available_at"], "bar.available_at"))
    for row in ordered:
        if _dt(row["available_at"], "bar.available_at") != receipt_at:
            raise ValueError("historical availability is unknown; use the actual snapshot receipt time")
        if row.get("symbol") != symbol or row.get("session_id") != current_session.id:
            raise ValueError("RRE bars must match the request symbol and current session")
        bar = RreBar(
            symbol=symbol, start=_dt(row["start"], "bar.start"), end=_dt(row["end"], "bar.end"),
            available_at=receipt_at, session_id=current_session.id,
            open=_finite_number(row["open"], "bar.open", positive=True),
            high=_finite_number(row["high"], "bar.high", positive=True),
            low=_finite_number(row["low"], "bar.low", positive=True),
            close=_finite_number(row["close"], "bar.close", positive=True),
            volume=_finite_number(row["volume"], "bar.volume"),
        )
        output = policy.update(bar, current_session, reference, receipt_at)
        if _event_overlaps(event_coverage, bar.start, bar.end):
            continue
        intents.extend(item.to_dict() for item in output)
    return {
        "status": "complete",
        "blockers": [],
        "intents": intents,
        "engine": {"name": "Raschke Research Engine", "version": "0.2.0",
                   "source_commit": "d59263b75b0aed4f69c56b56dd78c7c436d23c5c"},
        "input_timestamps": {"latest_bar_available_at": max(
            (_dt(row["available_at"], "bar.available_at") for row in bars), default=None
        ).isoformat() if bars else None, "source_capture_at": coverage.get("captured_at")},
        "coverage": coverage,
        "event_coverage": {"source": event_coverage["source"], "version": event_coverage["version"],
                           "captured_at": event_coverage["captured_at"], "status": "complete"},
        "policy_status": policy.status(),
    }


def run_job(engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("job payload must be a JSON object")
    if engine == "saty":
        return run_saty(payload)
    if engine == "rre":
        return run_rre(payload)
    raise ValueError("engine must be saty or rre")
