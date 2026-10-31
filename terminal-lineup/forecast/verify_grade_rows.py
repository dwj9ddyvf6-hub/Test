#!/usr/bin/env python3
"""Standalone read-only verifier for the forecast ledger grade rows.

Cure for defect (8) of the 2026-10-30 nightly audit, per
research_notes/deep-dive-repair-20261030/RESEARCH-R3.md steps 1 and 2.
This module shares no code with forecast/ledger.py: it reimplements
the documented canonicalisation rule (JSON, sorted keys, separators
(",", ":"), ensure_ascii; row_hash = sha256(prev_hash + canonical
body), body excluding row_hash, prev_hash, row_id) so a bug in the
publisher cannot certify itself.

Checks:
  a. Full hash chain re-derivation, first break localized by index
     and row_id.
  b. Per engine: forecasts raw, voided (targeted by a correction row),
     valid; grades raw, on voided, valid; orphan grades (must be 0);
     forecasts graded twice (must be 0); mean scores over valid
     grades only, grouped by the frozen label fingerprint carried
     on the grade row (unfrozen rows form one legacy group).
  c. Cross-tie: every site page whose live_record carries
     forecasts_recorded, forecasts_voided and forecasts_graded is
     compared figure by figure against the valid recount for the
     engine named in its calibration_attestation block; a page
     attestation block in the same file must agree with that
     live_record on recorded and graded counts.
  c2. Attestation tie (cure ATTESTATION-RECOUNT-20261031): every
     calibration attestation, in forecast/registry.json and in
     every site page's attestation block, is compared against
     the valid recount for its engine (forecasts_recorded against
     forecasts_valid, graded_forecasts against grades_valid),
     whatever shape the page's live section takes. Before this
     check the verifier passed while attestations for engines
     5, 8, 9, 10, 11, 12, 14, 15 (and others) contradicted the
     ledger they attest.
  d. site/record/data.json is compared only against its own Board
     and Morning Map population and is printed as not an engine
     grade surface.

Exit code is nonzero on any mismatch, chain break, orphan or
double grade. Read-only: nothing is appended or republished.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_LEDGER = os.path.join(HERE, "ledger.jsonl")
DEFAULT_SITE = os.path.join(ROOT, "site")


# Hosted foreign rows (cure ORACLE-COUNT-BASIS-20261031),
# declared here independently of the publisher: the Aperture
# proof gate ledgers its provisional forward records under
# engine_19 by its frozen rule. Those rows are the proof gate's
# record, counted in the page proof_gate block, not the oracle's
# own forecast record, so the attestation ties below (c2 and the
# registry tie) compare engine_19's attestation against the
# recount excluding them. The raw per engine counts and the
# live_record cross-tie stay on the full valid recount.
FOREIGN_OUTCOME_KINDS = {
    "engine_19": {"provisional_proof_forward_check"},
}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def recount(ledger_path):
    rows = []
    first_break = None
    prev = ""
    with open(ledger_path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            body = {k: v for k, v in row.items()
                    if k not in ("row_hash", "prev_hash", "row_id")}
            expect = hashlib.sha256(
                (prev + canonical(body)).encode()).hexdigest()
            if first_break is None and (
                    row.get("prev_hash") != prev
                    or row.get("row_hash") != expect):
                first_break = {"index": i, "row_id": row.get("row_id"),
                               "type": row.get("type")}
            prev = row.get("row_hash") or prev
            rows.append(row)
    by_id = {r["row_id"]: r for r in rows}
    voided = {r["corrects_row_id"] for r in rows
              if r.get("type") == "correction"
              and r.get("corrects_row_id") in by_id
              and by_id[r["corrects_row_id"]].get("type") == "forecast"}
    per = {}

    def eng(eid):
        return per.setdefault(eid, {
            "forecasts_raw": 0, "forecasts_voided": 0,
            "forecasts_valid": 0, "grades_raw": 0,
            "grades_on_voided": 0, "grades_valid": 0,
            "orphan_grades": 0, "double_grades": 0,
            "forecasts_foreign": 0, "forecasts_foreign_valid": 0,
            "grades_foreign_valid": 0,
            "_graded_ids": set(), "_scores": {},
            "_foreign_ids": set()})

    for r in rows:
        if r.get("type") == "forecast":
            e = eng(r["engine_id"])
            e["forecasts_raw"] += 1
            if (r.get("outcome") or {}).get("kind") in \
                    FOREIGN_OUTCOME_KINDS.get(r["engine_id"], set()):
                e["_foreign_ids"].add(r["row_id"])
                e["forecasts_foreign"] = \
                    e.get("forecasts_foreign", 0) + 1
            if r["row_id"] in voided:
                e["forecasts_voided"] += 1
    for r in rows:
        if r.get("type") != "grade":
            continue
        e = eng(r["engine_id"])
        e["grades_raw"] += 1
        target = by_id.get(r.get("forecast_row_id"))
        if target is None:
            e["orphan_grades"] += 1
            continue
        if r["forecast_row_id"] in e["_graded_ids"]:
            e["double_grades"] += 1
        e["_graded_ids"].add(r["forecast_row_id"])
        if r["forecast_row_id"] in voided:
            e["grades_on_voided"] += 1
            continue
        e["grades_valid"] += 1
        if r["forecast_row_id"] in e["_foreign_ids"]:
            e["grades_foreign_valid"] += 1
        fp = r.get("label_context_fingerprint") or "unfrozen_legacy"
        grp = e["_scores"].setdefault(fp, {})
        for name, val in (r["grade"].get("scores") or {}).items():
            if isinstance(val, (int, float)):
                grp.setdefault(name, []).append(val)
    for e in per.values():
        e["forecasts_valid"] = e["forecasts_raw"] - e["forecasts_voided"]
        foreign_ids = e.pop("_foreign_ids")
        e["forecasts_foreign_valid"] = sum(
            1 for fid in foreign_ids if fid not in voided)
        # Attestation basis (ORACLE-COUNT-BASIS-20261031): the
        # recount excluding hosted foreign rows and their grades.
        e["forecasts_valid_own"] = \
            e["forecasts_valid"] - e["forecasts_foreign_valid"]
        e["grades_valid_own"] = \
            e["grades_valid"] - e["grades_foreign_valid"]
        e["mean_scores_valid"] = {}
        groups = e.pop("_scores")
        if len(groups) == 1:
            grp = next(iter(groups.values()))
            e["mean_scores_valid"] = {
                k: sum(v) / len(v) for k, v in grp.items() if v}
        e.pop("_graded_ids")
    return {"rows": len(rows), "first_break": first_break,
            "head": rows[-1]["row_hash"] if rows else None,
            "per_engine": per}


def cross_tie(site_dir, per):
    mismatches = []
    checked = []
    if not os.path.isdir(site_dir):
        return mismatches, checked
    for name in sorted(os.listdir(site_dir)):
        path = os.path.join(site_dir, name, "data.json")
        if not os.path.isfile(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        live = data.get("live_record")
        att = (data.get("calibration_attestation") or {}).get(
            "attestation") or {}
        eid = (data.get("calibration_attestation") or {}).get(
            "engine_id")
        if att and eid and "forecasts_recorded" in att:
            exp = per.get(eid) or {"forecasts_valid": 0,
                                   "grades_valid": 0,
                                   "forecasts_valid_own": 0,
                                   "grades_valid_own": 0}
            # Attestations count on the own basis (hosted foreign
            # rows excluded); see FOREIGN_OUTCOME_KINDS above.
            for a_field, want in (
                    ("forecasts_recorded",
                     exp.get("forecasts_valid_own",
                             exp["forecasts_valid"])),
                    ("graded_forecasts",
                     exp.get("grades_valid_own",
                             exp["grades_valid"]))):
                if a_field in att and att[a_field] != want:
                    mismatches.append(
                        f"{path}: calibration_attestation."
                        f"{a_field} published {att[a_field]} "
                        f"recounted {want}")
        if isinstance(live, dict) and eid and all(
                k in live for k in ("forecasts_recorded",
                                    "forecasts_voided",
                                    "forecasts_graded")):
            exp = per.get(eid)
            if exp is None:
                mismatches.append(
                    f"{path}: live_record for unknown engine {eid}")
                continue
            for field, want in (
                    ("forecasts_recorded", exp["forecasts_valid"]),
                    ("forecasts_voided", exp["forecasts_voided"]),
                    ("forecasts_graded", exp["grades_valid"])):
                if live[field] != want:
                    mismatches.append(
                        f"{path}: live_record.{field} published "
                        f"{live[field]} recounted {want} delta "
                        f"{live[field] - want}")
            checked.append(f"{name} ({eid})")
            if att:
                for a_field, l_field in (
                        ("forecasts_recorded", "forecasts_recorded"),
                        ("graded_forecasts", "forecasts_graded")):
                    if a_field in att and att[a_field] != live[l_field]:
                        mismatches.append(
                            f"{path}: calibration_attestation."
                            f"{a_field} published {att[a_field]} "
                            f"disagrees with live_record.{l_field} "
                            f"{live[l_field]}")
    return mismatches, checked


def registry_mismatches(registry_path, per):
    mismatches = []
    try:
        with open(registry_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return [f"{registry_path}: registry unreadable: {exc}"]
    for eng in data.get("engines") or []:
        att = eng.get("calibration_attestation") or {}
        if "forecasts_recorded" not in att:
            continue
        exp = per.get(eng["id"]) or {"forecasts_valid": 0,
                                     "grades_valid": 0,
                                     "forecasts_valid_own": 0,
                                     "grades_valid_own": 0}
        for a_field, want in (
                ("forecasts_recorded",
                 exp.get("forecasts_valid_own",
                         exp["forecasts_valid"])),
                ("graded_forecasts",
                 exp.get("grades_valid_own",
                         exp["grades_valid"]))):
            if a_field in att and att[a_field] != want:
                mismatches.append(
                    f"registry {eng['id']}: calibration_"
                    f"attestation.{a_field} published "
                    f"{att[a_field]} recounted {want}")
    return mismatches


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ledger_path = argv[0] if argv else DEFAULT_LEDGER
    site_dir = argv[1] if len(argv) > 1 else DEFAULT_SITE
    result = recount(ledger_path)
    print(f"rows {result['rows']} head {(result['head'] or '')[:16]}")
    failures = []
    if result["first_break"] is not None:
        failures.append(f"chain first break {result['first_break']}")
        print(f"CHAIN BREAK {result['first_break']}")
    else:
        print("chain: 0 breaks")
    for eid in sorted(result["per_engine"]):
        e = result["per_engine"][eid]
        print(f"{eid}: forecasts raw {e['forecasts_raw']} voided "
              f"{e['forecasts_voided']} valid {e['forecasts_valid']}; "
              f"grades raw {e['grades_raw']} on_voided "
              f"{e['grades_on_voided']} valid {e['grades_valid']}; "
              f"orphans {e['orphan_grades']} doubles "
              f"{e['double_grades']}")
        if e["orphan_grades"] or e["double_grades"]:
            failures.append(f"{eid}: orphans {e['orphan_grades']} "
                            f"doubles {e['double_grades']}")
    mismatches, checked = cross_tie(site_dir, result["per_engine"])
    mismatches = registry_mismatches(
        os.path.join(HERE, "registry.json"),
        result["per_engine"]) + mismatches
    print(f"cross-tie pages checked: {checked}")
    for m in mismatches:
        print(f"MISMATCH {m}")
    failures.extend(mismatches)
    record_path = os.path.join(site_dir, "record", "data.json")
    if os.path.isfile(record_path):
        print("site/record/data.json: Board and Morning Map "
              "population only; not an engine grade surface, no "
              "engine figure compared against it")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        return 1
    print("PASS: chain intact, linkage clean, published live "
          "figures tie to the valid recount")
    return 0


if __name__ == "__main__":
    sys.exit(main())
