#!/usr/bin/env python3
"""Regenerate every engine calibration attestation from the ledger.

Cure ATTESTATION-RECOUNT-20261031 (terminal total audit round 1,
sector engines-a defect D1; the same class as engines-b defect 5).

Before this module existed, registry attestations were a snapshot
taken by hand on 2026-10-30: for six engines the snapshot predated
that day's issuance batch, Engine 14's snapshot carried the raw
count including voided forecasts, and nothing ever refreshed the
snapshot, so registry.json and every engine page's attestation
block (a copy of the registry record, attached by
site/attestation_block.py) disagreed with the live sections on the
same pages and with the ledger itself.

The cure is at the source: the attestation is a derived record,
so it is regenerated from the same void aware recount the live
sections use (forecast/ledger.py recompute_figures, whose valid
counts forecast/verify_grade_rows.py independently re-derives),
through the existing builder forecast/grading.py
attestation_record. No second counting implementation is added.

Wiring: site/refresh_engines.py runs this module (registry only)
after grading and before the engine refreshers on every run, so
each refresh publishes pages whose attestation blocks carry the
current record. Standalone runs also re-sync the attestation
block copy on every engine page already on disk, so a manual
regeneration leaves registry and pages in agreement at once.
A page file modified within the last 10 minutes is deferred
(another program may be republishing it) and named, never fought.

Usage: python3 forecast/refresh_attestations.py [--registry-only]
"""
import json
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from forecast import grading, ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

REGISTRY_PATH = os.path.join(HERE, "registry.json")
LEDGER_PATH = os.path.join(HERE, "ledger.jsonl")
SITE_DIR = os.path.join(ROOT, "site")
DEFER_SECONDS = 600

# Hosted foreign rows (cure ORACLE-COUNT-BASIS-20261031): the
# Aperture proof gate ledgers its provisional forward records
# under engine_19 by its frozen rule (registry proof_gate_rule:
# forward_check.ledger_engine_id engine_19). Those rows are the
# proof gate's record, counted on the In-Regime Oracle page in
# its proof_gate block; they are not the oracle's own weekly
# window forecasts. An attestation that counts them presents a
# second, incompatible record for the engine (31,649 against the
# live record's 0), so this engine's attestation figures are
# recomputed, through the same recompute_figures, over the
# ledger with the hosted rows excluded, and the record stamps
# its counting basis. forecast/verify_grade_rows.py declares the
# same exclusion independently for its attestation tie.
FOREIGN_OUTCOME_KINDS = {
    "engine_19": {"provisional_proof_forward_check"},
}
COUNTING_BASIS = {
    "engine_19": (
        "the engine's own weekly window forecasts only (outcome "
        "kind next_window_hit_rate_exceeds_trailing); the Aperture "
        "proof-gate provisional rows hosted under this engine id "
        "(outcome kind provisional_proof_forward_check) are "
        "counted in the page proof_gate block, not in this "
        "engine's forecast record"),
}


def today_et():
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def regenerate(recorded_on=None, registry_path=REGISTRY_PATH,
               ledger_path=LEDGER_PATH):
    """Rewrite every engine's calibration_attestation in the
    registry from the ledger recount. Returns the list of engine
    ids whose record changed."""
    recorded_on = recorded_on or today_et()
    with open(registry_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    led = ledger_mod.Ledger(ledger_path)
    rows = led.rows()
    figures = ledger_mod.recompute_figures(rows)
    changed = []
    for eng in data["engines"]:
        fig = figures.get(eng["id"]) or {
            "forecasts": 0, "forecasts_valid": 0, "graded": 0,
            "mean_scores": {}}
        counting_basis = None
        foreign = FOREIGN_OUTCOME_KINDS.get(eng["id"])
        if foreign:
            excluded = {r["row_id"] for r in rows
                        if r.get("type") == "forecast"
                        and r.get("engine_id") == eng["id"]
                        and (r.get("outcome") or {}).get("kind")
                        in foreign}
            own_rows = [r for r in rows
                        if r.get("row_id") not in excluded
                        and r.get("forecast_row_id") not in excluded]
            fig = ledger_mod.recompute_figures(own_rows).get(
                eng["id"]) or {
                    "forecasts": 0, "forecasts_valid": 0,
                    "graded": 0, "mean_scores": {}}
            counting_basis = COUNTING_BASIS[eng["id"]]
        record = grading.attestation_record(
            eng, fig, recorded_on, counting_basis=counting_basis)
        if eng.get("calibration_attestation") != record:
            eng["calibration_attestation"] = record
            changed.append(eng["id"])
    if changed:
        tmp = registry_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, registry_path)
    # The rewritten registry must still validate.
    registry_mod.load(registry_path)
    return changed


def sync_pages(site_dir=SITE_DIR):
    """Re-attach the current registry attestation block to every
    engine page on disk. Returns (synced, deferred): page directory
    names updated, and names deferred because the file changed
    within DEFER_SECONDS (a live republish may be in flight)."""
    sys.path.insert(0, site_dir)
    import attestation_block as ab
    synced, deferred = [], []
    now = time.time()
    for name in sorted(os.listdir(site_dir)):
        path = os.path.join(site_dir, name, "data.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        block = data.get("calibration_attestation") or {}
        engine_id = block.get("engine_id")
        if not engine_id:
            continue
        fresh = ab.attestation_block(engine_id)
        if fresh is None or block == fresh:
            continue
        if now - os.path.getmtime(path) < DEFER_SECONDS:
            deferred.append(name)
            continue
        data["calibration_attestation"] = fresh
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
        synced.append(name)
    return synced, deferred


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    changed = regenerate()
    print(f"attestations regenerated: {len(changed)} changed "
          f"({', '.join(changed) if changed else 'none'})")
    if "--registry-only" not in argv:
        synced, deferred = sync_pages()
        print(f"page attestation blocks synced: {len(synced)} "
              f"({', '.join(synced) if synced else 'none'})")
        if deferred:
            print("page blocks deferred (file changed within "
                  f"10 minutes): {', '.join(deferred)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
