"""R4 preregistered, evidence-only strategy champion/challenger tournament."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from strategy_system import valid_bars
from validation_factory import VERSIONS, canonical, digest
from r4_parallel_strategy_lab import SPECS as PARALLEL_SPECS


AUTHORITY = "OFFLINE_SHADOW_NO_PROMOTION_NO_RISK_NO_BROKER"
VERSION = "r4-strategy-tournament/1.0.0"

# These are hypotheses, not enabled strategies. The specification hash freezes
# every rule before an outcome may be admitted to the tournament.
CANDIDATES: dict[str, dict[str, Any]] = {
    **{version: {"family": family, "implementation": "EXISTING_M7_VERSION", "role": role}
       for version, (family, role) in VERSIONS.items()},
    "SIMPLE_TREND_1_0_0": {
        "family": "SIMPLE_TREND", "implementation": "R4_DAILY_PURE_FUNCTION",
        "rule": "close_above_sma200_and_sma50_above_sma200", "horizonSessions": 20,
    },
    "LIQUID_MOMENTUM_TREND_1_0_0": {
        "family": "LIQUID_MOMENTUM_TREND", "implementation": "R4_DAILY_PURE_FUNCTION",
        "rule": "close_above_sma200_positive_12m_ex_last_month_and_adv20_ge_20m", "horizonSessions": 20,
    },
    "PEAD_1_0_0": {
        "family": "PEAD", "implementation": "POINT_IN_TIME_EARNINGS_REQUIRED",
        "rule": "positive_standardized_earnings_surprise_with_post_event_drift", "horizonSessions": 20,
    },
    "MOMENTUM_PEAD_COMBINATION_1_0_0": {
        "family": "MOMENTUM_PEAD_COMBINATION", "implementation": "POINT_IN_TIME_EARNINGS_REQUIRED",
        "rule": "liquid_momentum_trend_and_positive_pead", "horizonSessions": 20,
    },
    **{version_id: {**spec, "implementation": "R4_PARALLEL_STRATEGY_LAB"}
       for version_id, spec in PARALLEL_SPECS.items()},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sma(values: list[float], n: int) -> float | None:
    return sum(values[-n:]) / n if len(values) >= n else None


def evaluate_daily_candidate(version: str, raw_bars: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure, completed-daily-bar candidate evaluation; never submits orders."""
    if version not in {"SIMPLE_TREND_1_0_0", "LIQUID_MOMENTUM_TREND_1_0_0"}:
        raise ValueError("candidate requires a different point-in-time evidence contract")
    bars = valid_bars(raw_bars)
    minimum = 253
    if len(bars) < minimum:
        return {"versionId": version, "status": "UNAVAILABLE", "reason": "INSUFFICIENT_COMPLETED_DAILY_BARS"}
    closes = [float(bar["c"]) for bar in bars]
    sma50, sma200 = _sma(closes, 50), _sma(closes, 200)
    trend = closes[-1] > float(sma200) and float(sma50) > float(sma200)
    metrics: dict[str, Any] = {"close": closes[-1], "sma50": sma50, "sma200": sma200, "trend": trend}
    passed = trend
    if version == "LIQUID_MOMENTUM_TREND_1_0_0":
        momentum = closes[-22] / closes[-253] - 1
        adv20 = sum(float(bar["c"]) * float(bar["v"]) for bar in bars[-20:]) / 20
        metrics.update(momentum12mEx1m=momentum, adv20Dollars=adv20)
        passed = trend and momentum > 0 and adv20 >= 20_000_000
    evidence = {"versionId": version, "asOf": bars[-1]["t"], "metrics": metrics}
    return {**evidence, "status": "SETUP" if passed else "WAIT", "evidenceHash": digest(evidence)}


class StrategyTournament:
    VERSION = VERSION
    AUTHORITY = AUTHORITY

    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(sqlite3.connect(path, timeout=10)) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS r4_candidate_registry(
              version_id TEXT PRIMARY KEY, family TEXT NOT NULL, spec_hash TEXT NOT NULL,
              registered_at TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS r4_trial_ledger(
              trial_id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, version_id TEXT NOT NULL,
              evidence_hash TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS r4_tournament_runs(
              run_id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, status TEXT NOT NULL,
              passed INTEGER NOT NULL, total INTEGER NOT NULL, evidence_hash TEXT NOT NULL,
              payload TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS r4_trial_identity
              ON r4_trial_ledger(version_id,evidence_hash);
            CREATE TRIGGER IF NOT EXISTS r4_registry_no_update BEFORE UPDATE ON r4_candidate_registry BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS r4_registry_no_delete BEFORE DELETE ON r4_candidate_registry BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS r4_trials_no_update BEFORE UPDATE ON r4_trial_ledger BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS r4_trials_no_delete BEFORE DELETE ON r4_trial_ledger BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS r4_runs_no_update BEFORE UPDATE ON r4_tournament_runs BEGIN SELECT RAISE(ABORT,'append-only');END;
            CREATE TRIGGER IF NOT EXISTS r4_runs_no_delete BEFORE DELETE ON r4_tournament_runs BEGIN SELECT RAISE(ABORT,'append-only');END;
            """)
            for version_id, spec in CANDIDATES.items():
                spec_payload = {"versionId": version_id, **spec, "frozen": True, "authority": AUTHORITY}
                spec_hash = digest(spec_payload)
                existing = db.execute("SELECT spec_hash FROM r4_candidate_registry WHERE version_id=?", (version_id,)).fetchone()
                if existing and existing[0] != spec_hash:
                    raise RuntimeError(f"frozen R4 candidate drift: {version_id}")
                db.execute("INSERT OR IGNORE INTO r4_candidate_registry VALUES(?,?,?,?,?)",
                           (version_id, str(spec["family"]), spec_hash, utc_now(), canonical(spec_payload)))
            db.commit()

    def evaluate(self, studies: dict[str, Any], robustness: dict[str, Any], candidate_evidence: dict[str, Any] | None = None, candidate_studies: dict[str, Any] | None = None) -> dict[str, Any]:
        study_versions = studies.get("versions") or {}
        robust_versions = robustness.get("versions") or {}
        candidate_evidence = candidate_evidence or {}; candidate_versions = candidate_evidence.get("perVersion") or {}; candidate_studies = candidate_studies or {}; candidate_study_versions = candidate_studies.get("versions") or {}
        candidates: dict[str, Any] = {}
        stamp = utc_now()
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            for version_id, spec in CANDIDATES.items():
                study = study_versions.get(version_id)
                robust = robust_versions.get(version_id)
                if study is None:
                    candidate = candidate_versions.get(version_id) or {}
                    candidate_study = candidate_study_versions.get(version_id) or {}
                    if candidate_study: state = str(candidate_study.get("status") or "INSUFFICIENT_EVIDENCE")
                    elif candidate.get("outcomes",0): state = "INSUFFICIENT_EVIDENCE"
                    elif version_id.startswith("PEAD") or "PEAD" in version_id: state = str(candidate_evidence.get("peadState") or "AWAITING_POINT_IN_TIME_EARNINGS")
                    else: state = "AWAITING_TIMESTAMP_PURE_OUTCOMES"
                    observed = {"study": candidate_studies.get("status") or "R4_CANDIDATE_EVIDENCE", "robustness": "PENDING", **candidate, "studyRows":candidate_study.get("datasetRows"), "studyDates":candidate_study.get("decisionDates")}
                else:
                    state = "PASS" if study.get("status") == "PASS" and robust and robust.get("benchmark", {}).get("passed") and robust.get("regimePassed") else ("FAIL" if study.get("status") == "FAIL" else "INSUFFICIENT_EVIDENCE")
                    observed = {"study": study.get("status"), "robustness": "PASS" if robust and robust.get("benchmark", {}).get("passed") and robust.get("regimePassed") else "NOT_PASS", "datasetRows": study.get("datasetRows", 0)}
                trial_evidence = digest({"versionId": version_id, "spec": spec, "observed": observed})
                trial_id = f"r4trial:{version_id}:{trial_evidence[:16]}"
                db.execute("INSERT OR IGNORE INTO r4_trial_ledger VALUES(?,?,?,?,?,?)",
                           (trial_id, stamp, version_id, trial_evidence, state, canonical(observed)))
                candidates[version_id] = {"family": spec["family"], "state": state, **observed}
            db.commit()
            charged = int(db.execute("SELECT COUNT(*) FROM r4_trial_ledger").fetchone()[0])
        criteria = [
            {"name": "frozen_registry_complete", "passed": len(candidates) == len(CANDIDATES), "observed": len(candidates), "required": len(CANDIDATES)},
            {"name": "all_trials_charged", "passed": charged >= len(CANDIDATES), "observed": charged, "required": f">={len(CANDIDATES)}"},
            {"name": "all_candidates_have_timestamp_pure_outcomes", "passed": all(item["state"] in {"PASS", "FAIL"} for item in candidates.values()), "observed": sum(item["state"] in {"PASS", "FAIL"} for item in candidates.values()), "required": len(CANDIDATES)},
            {"name": "frozen_candidate_survives_all_gates", "passed": any(item["state"] == "PASS" for item in candidates.values()), "observed": sum(item["state"] == "PASS" for item in candidates.values()), "required": ">=1"},
        ]
        passed = sum(item["passed"] for item in criteria)
        status = "ELIGIBLE_FOR_HUMAN_REVIEW" if passed == len(criteria) else "INSUFFICIENT_EVIDENCE"
        evidence_basis = digest({"studies":studies.get("evidenceHash"),"robustness":robustness.get("evidenceHash"),"candidateEvidence":{"perVersion":candidate_evidence.get("perVersion"),"peadState":candidate_evidence.get("peadState"),"earningsReady":candidate_evidence.get("earningsReady")},"candidateStudies":candidate_studies.get("evidenceHash")})
        result = {"version": VERSION, "authority": AUTHORITY, "status": status, "passed": passed, "total": len(criteria), "observedAt": stamp, "candidateCount": len(candidates), "chargedTrials": charged, "evidenceBasisHash":evidence_basis, "candidates": candidates, "criteria": criteria, "automaticPromotion": False, "strategyAuthority": False, "riskAuthority": False, "brokerAuthority": False, "multipleTestingPolicy": "EVERY_FROZEN_VERSION_AND_EVIDENCE_HASH_IS_CHARGED"}
        evidence_hash = digest(result)
        run_id = f"r4run:{evidence_hash[:24]}"
        result.update(runId=run_id, evidenceHash=evidence_hash)
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            db.execute("INSERT OR IGNORE INTO r4_tournament_runs VALUES(?,?,?,?,?,?,?)", (run_id, stamp, status, passed, len(criteria), evidence_hash, canonical(result)))
            db.commit()
        return result

    def health(self) -> dict[str, Any]:
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            row = db.execute("SELECT payload FROM r4_tournament_runs ORDER BY observed_at DESC LIMIT 1").fetchone()
            registered = int(db.execute("SELECT COUNT(*) FROM r4_candidate_registry").fetchone()[0])
            trials = int(db.execute("SELECT COUNT(*) FROM r4_trial_ledger").fetchone()[0])
        if not row:
            return {"version": VERSION, "authority": AUTHORITY, "status": "PENDING", "registeredCandidates": registered, "chargedTrials": trials, "automaticPromotion": False, "brokerAuthority": False}
        result = json.loads(row[0])
        result["registeredCandidates"] = registered
        result["chargedTrials"] = trials
        return result

    def evaluate_if_due(self, studies: dict[str, Any], robustness: dict[str, Any], candidate_evidence: dict[str, Any] | None = None, candidate_studies: dict[str, Any] | None = None, hours: float = 24) -> dict[str, Any] | None:
        health = self.health()
        basis = digest({"studies":studies.get("evidenceHash"),"robustness":robustness.get("evidenceHash"),"candidateEvidence":{"perVersion":(candidate_evidence or {}).get("perVersion"),"peadState":(candidate_evidence or {}).get("peadState"),"earningsReady":(candidate_evidence or {}).get("earningsReady")},"candidateStudies":(candidate_studies or {}).get("evidenceHash")})
        if health.get("evidenceBasisHash") == basis:
            return None
        return self.evaluate(studies, robustness, candidate_evidence, candidate_studies)
