#!/usr/bin/env python3
"""Validator for the research and forecast claim ledger. ADOPT A5.

Validator only: checks schema and acceptance rules, reports violations,
writes nothing. Scope is research and forecast claims only; facts about the
user are never entered (MEMORY.md stays canonical there).

Entry fields: claim_id (deterministic, dedup_ids.py convention), statement,
locations, supporting and contradicting source refs, authority per source,
independence_key per source, risk (ordinary or high), assessment (accepted,
provisional, contested, unsupported, deprecated), refresh_due (date).
A source ref is a dict: {source_id, authority, independence_key,
synthetic (optional bool), active (optional bool), fresh_until (optional
date)}. A plain string ref is accepted as a source_id with unknown
authority and its own independence_key.

Rules:
- accepted requires at least one fresh, active, non-synthetic supporting
  source;
- high-risk accepted requires supporting sources with at least two distinct
  independence_keys;
- unsupported is a valid assessment, not an error;
- contradictions are preserved: a claim with contradicting sources is
  contested unless the contradiction is itself resolved by a dated entry
  (resolution_date on the claim);
- staleness is computed from refresh_due at read time and reported as a
  warning, never stored as a flag.
Stdlib only.
"""
import json, sys
from datetime import date
from pathlib import Path

AUTHORITIES = {"official", "primary", "secondary", "community", "synthetic", "unknown"}
ASSESSMENTS = {"accepted", "provisional", "contested", "unsupported", "deprecated"}
RISKS = {"ordinary", "high"}
REQUIRED = ["claim_id", "statement", "locations", "supporting", "contradicting",
            "risk", "assessment", "refresh_due"]


def _parse_date(s):
    try:
        y, m, d = str(s).split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _norm_source(ref):
    if isinstance(ref, str):
        return {"source_id": ref, "authority": "unknown",
                "independence_key": ref, "synthetic": False, "active": True,
                "fresh_until": None}
    return {"source_id": ref.get("source_id", ""),
            "authority": ref.get("authority", "unknown"),
            "independence_key": ref.get("independence_key", ref.get("source_id", "")),
            "synthetic": bool(ref.get("synthetic", False)) or ref.get("authority") == "synthetic",
            "active": ref.get("active", True),
            "fresh_until": ref.get("fresh_until")}


def validate_entry(entry, reference) -> tuple:
    errors, warnings = [], []
    cid = entry.get("claim_id", "<missing>")
    for f in REQUIRED:
        if f not in entry:
            errors.append(f"{cid}: missing field {f}")
    if entry.get("risk") not in RISKS:
        errors.append(f"{cid}: risk must be one of {sorted(RISKS)}")
    if entry.get("assessment") not in ASSESSMENTS:
        errors.append(f"{cid}: assessment must be one of {sorted(ASSESSMENTS)}")
    supporting = [_norm_source(s) for s in entry.get("supporting", [])]
    contradicting = [_norm_source(s) for s in entry.get("contradicting", [])]
    for s in supporting + contradicting:
        if s["authority"] not in AUTHORITIES:
            errors.append(f"{cid}: source {s['source_id']} authority "
                          f"'{s['authority']}' not in {sorted(AUTHORITIES)}")
    rd = _parse_date(entry.get("refresh_due"))
    if entry.get("refresh_due") is not None and rd is None:
        errors.append(f"{cid}: refresh_due is not a YYYY-MM-DD date")
    if rd is not None and reference and rd < reference:
        warnings.append(f"{cid}: STALE (refresh_due {entry['refresh_due']} "
                        f"is past, computed at read time)")
    if entry.get("assessment") == "accepted":
        fresh = []
        for s in supporting:
            if s["synthetic"] or not s["active"]:
                continue
            fu = _parse_date(s["fresh_until"]) if s["fresh_until"] else None
            if s["fresh_until"] and (fu is None or (reference and fu < reference)):
                continue
            fresh.append(s)
        if not fresh:
            errors.append(f"{cid}: accepted requires at least one fresh, active, "
                          f"non-synthetic supporting source")
        if entry.get("risk") == "high":
            keys = {s["independence_key"] for s in fresh}
            if len(keys) < 2:
                errors.append(f"{cid}: high-risk accepted requires supporting "
                              f"sources with at least two distinct independence_keys "
                              f"(found {len(keys)})")
    if contradicting and entry.get("assessment") != "contested" \
            and not entry.get("resolution_date"):
        errors.append(f"{cid}: claim has contradicting sources but assessment is "
                      f"'{entry.get('assessment')}', not contested, and no dated "
                      f"resolution entry is recorded")
    return errors, warnings


def validate_ledger(data, reference=None) -> tuple:
    reference = reference or date.today()
    errors, warnings = [], []
    if not isinstance(data, dict) or "entries" not in data:
        return ["ledger has no entries list"], []
    seen = set()
    for entry in data.get("entries", []):
        cid = entry.get("claim_id")
        if cid in seen:
            errors.append(f"{cid}: duplicate claim_id")
        seen.add(cid)
        e, w = validate_entry(entry, reference)
        errors.extend(e); warnings.extend(w)
    return errors, warnings


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__); print("usage: claim_ledger.py <claim-ledger.json>")
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    errors, warnings = validate_ledger(data)
    for w in warnings:
        print(f"WARNING {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"counts: entries={len(data.get('entries', []))} errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
