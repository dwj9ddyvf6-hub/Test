#!/usr/bin/env python3
"""Rationale entries: record the why, not just the what. Discipline 11,
built 2026-11-03 (schema adopted from oliver-zehentleitner/keep-the-why;
the tool itself not imported).

Every decision that closes a path is stored with the path it closed.
An entry's identity is a stable UUID, never a heading: headings get
reworded and files split, and references must survive both. Structure is
enforced mechanically here and checked in the existing gate (tools_gate
validates the store on every run and only issues its "why store valid"
evidence when the store is clean). Whether a rationale is TRUE stays
human judgement; this module enforces only that the entry carries the
fields a future reader needs to not re-litigate settled ground.

Store: JSONL, default ~/workspace/tools/memory_store/decisions.jsonl.
Unattended capture writes entries flagged pending_confirmation; it does
not drop the finding and does not ask into the void. Superseded entries
are never injected as current context (injection_view returns active
entries only).

CLI: why_record.py validate [path] | selftest
"""
import json, os, sys, tempfile, uuid

TYPES = ("decision", "workaround", "incident", "constraint", "undefined")
STATUSES = ("active", "superseded", "open", "needs-review", "pending-confirmation")
EVIDENCE = ("confirmed", "inferred", "unknown")
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "memory_store", "decisions.jsonl")

def new_entry(decision, rejected, reason, type_, source, revisit_when, see,
              evidence="unknown", pending_confirmation=True):
    """Mint an entry with a fresh UUID. rejected: [{alternative, why_lost}]."""
    return {"id": str(uuid.uuid4()), "decision": decision, "rejected": rejected,
            "reason": reason, "type": type_, "status": "active",
            "evidence": evidence, "source": source, "revisit_when": revisit_when,
            "see": see, "pending_confirmation": bool(pending_confirmation)}

def validate_entry(e):
    errs = []
    if not isinstance(e, dict):
        return ["entry is not an object"]
    try:
        uuid.UUID(str(e.get("id", "")))
    except Exception:
        errs.append("id missing or not a UUID (identity is a stable UUID, never a heading)")
    if not e.get("decision"):
        errs.append("decision missing")
    rej = e.get("rejected")
    if not isinstance(rej, list) or not rej:
        errs.append("rejected alternatives missing (the path this decision closed)")
    else:
        for r in rej:
            if not r.get("alternative") or not r.get("why_lost"):
                errs.append("each rejected alternative needs alternative + why_lost")
                break
    if not e.get("reason"):
        errs.append("reason missing (why the winner won)")
    if e.get("type") not in TYPES:
        errs.append(f"type must be one of {TYPES}")
    if e.get("type") == "undefined" and not e.get("type_reason"):
        errs.append("type undefined requires type_reason (why it is undefined)")
    if e.get("status") not in STATUSES:
        errs.append(f"status must be one of {STATUSES}")
    if e.get("status") == "superseded" and not e.get("superseded_by"):
        errs.append("superseded entry requires superseded_by (successor id, or 'none' with superseded_by_note)")
    if e.get("status") == "superseded" and e.get("superseded_by") == "none" and not e.get("superseded_by_note"):
        errs.append("superseded_by 'none' requires superseded_by_note (why nothing replaced it)")
    if e.get("evidence") not in EVIDENCE:
        errs.append(f"evidence must be one of {EVIDENCE}")
    for f in ("source", "revisit_when", "see"):
        if not e.get(f):
            errs.append(f"{f} missing")
    return errs

def load_store(path):
    entries, errors = [], []
    if not os.path.isfile(path):
        return entries, errors
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except Exception as ex:
            errors.append({"line": i, "errors": [f"unparseable: {ex}"]})
            continue
        entries.append(e)
        errs = validate_entry(e)
        if errs:
            errors.append({"line": i, "id": e.get("id"), "errors": errs})
    return entries, errors

def validate_store(path):
    entries, errors = load_store(path)
    return {"entries": len(entries), "errors": errors,
            "active": sum(1 for e in entries if e.get("status") == "active"),
            "pending_confirmation": sum(1 for e in entries if e.get("pending_confirmation"))}

def append_entry(path, entry):
    errs = validate_entry(entry)
    if errs:
        raise ValueError(f"rationale entry refused: {errs}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry["id"]

def injection_view(path):
    """Entries safe to inject as current context: active only. A
    superseded decision reads as current if injected; it never is."""
    entries, _ = load_store(path)
    return [e for e in entries if e.get("status") == "active"]

def selftest():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "decisions.jsonl")
        good = new_entry("Use the generic endpoint for the fee walk",
                         [{"alternative": "page the typed FEE endpoint",
                           "why_lost": "drops same-date rows past page one"}],
                         "proven complete against the live journal",
                         "decision", "halt-cure 2026-11-03", "a reconcile shows missing FEE rows again",
                         "BUGLOG_2026-11-03.md, FEE-WALK-20261103", evidence="confirmed")
        assert validate_entry(good) == [], validate_entry(good)
        append_entry(p, good)
        bad = dict(good); del bad["id"]
        try:
            append_entry(p, bad); raise SystemExit("entry without an Id must be refused")
        except ValueError:
            pass
        assert any("UUID" in e for e in validate_entry(bad))
        for field in ("decision", "rejected", "reason", "revisit_when", "see", "source"):
            stripped = dict(good); stripped[field] = "" if field != "rejected" else []
            assert validate_entry(stripped), f"missing {field} must be an error"
        noreason = dict(good); noreason["rejected"] = [{"alternative": "y"}]
        assert any("why_lost" in e for e in validate_entry(noreason))
        undef = new_entry("x", [{"alternative": "y", "why_lost": "z"}], "r",
                          "undefined", "s", "w", "see")
        assert any("type_reason" in e for e in validate_entry(undef))
        sup = dict(good); sup["status"] = "superseded"
        assert any("superseded_by" in e for e in validate_entry(sup))
        sup2 = dict(good); sup2["id"] = str(uuid.uuid4()); sup2["status"] = "superseded"
        sup2["superseded_by"] = "none"
        assert any("superseded_by_note" in e for e in validate_entry(sup2))
        sup2["superseded_by_note"] = "the lane was retired, nothing replaced it"
        assert validate_entry(sup2) == [], validate_entry(sup2)
        append_entry(p, sup2)
        view = injection_view(p)
        assert [e["id"] for e in view] == [good["id"]], "superseded entries are never injected"
        rep = validate_store(p)
        assert rep["entries"] == 2 and rep["errors"] == [] and rep["active"] == 1, rep
        print("SELFTEST PASS why_record: UUID identity enforced, rejected alternatives + reason + revisit trigger required, undefined needs its reason, superseded needs a successor or a note, injection view is active-only")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        print(json.dumps(validate_store(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH), indent=1))
    else:
        print(__doc__)
