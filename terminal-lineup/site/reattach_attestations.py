#!/usr/bin/env python3
"""Re-attach calibration attestations to engine pages from the
registry, after the final ledger state of a refresh run is known.

Cure WEEK-READINESS-R2-20261102-N: refresh_engines.py recounts the
registry attestations BEFORE the engine loop, but the engines
append their own new forecast rows to the ledger during the loop,
so the attestation each page attached at its own write time is
stale by the end of the same run and the smoke check
(verify_grade_rows) fails on the final tree (2026-11-02: engines
10, 11, 12 and 19 all mismatched after an otherwise clean run).
The runner now recounts the registry again after the loop and runs
this script: every page data.json that already carries a
calibration_attestation block is re-attached from the recounted
registry, keyed by the engine_id inside its own block. Pages with
no attestation block are untouched. Nothing else in a page changes.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import attestation_block as _ab


def reattach(site_dir=HERE):
    changed = []
    for path in sorted(glob.glob(os.path.join(site_dir, "*", "data.json"))):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        block = data.get("calibration_attestation")
        if not isinstance(block, dict) or not block.get("engine_id"):
            continue
        new = _ab.attach(data, block["engine_id"])
        if new.get("calibration_attestation") != block:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(new, fh, indent=1, sort_keys=True)
                fh.write("\n")
            os.replace(tmp, path)
            changed.append(os.path.basename(os.path.dirname(path)))
    return changed


if __name__ == "__main__":
    changed = reattach()
    print(f"reattach_attestations: {len(changed)} pages re-attached"
          + (": " + ", ".join(changed) if changed else ""))
