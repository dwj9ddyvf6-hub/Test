#!/usr/bin/env python3
"""Grading report phase, isolated (GRADING-STREAM-20261106).

The overlap, paired-baseline, HAR-control and cell-family
reports are pure aggregations over the whole ledger: they need
the parsed rows, and at 253,163 rows that parse is 1.83 GB of
resident memory. They used to run inside the grading process,
on top of the grading phase's own resident set, for the whole
of a 44-plus minute run; that co-residence is what the
2026-11-06 grading step died of (exit -9). The grading runner
now runs this module as a child process AFTER the appends are
on the ledger: it loads the rows exactly once, prints the same
lines the runner always printed, and exits, freeing everything.
If this child is ever the process a memory kill takes, the
grades stand on the ledger and only the report lines are lost,
which the runner reports as its own failure, honestly.

Usage: python3 -m forecast.run_grading_reports
   or: python3 forecast/run_grading_reports.py
"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

from forecast import grading, ledger as ledger_mod, registry as registry_mod

LEDGER_PATH = os.path.expanduser(
    "~/workspace/terminal-lineup/forecast/ledger.jsonl")


def main():
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    prices = grading.PriceSource()
    rows = led.rows()
    # Horizon overlap (DEEP-PASS 3.2 item 4): the independent
    # window count printed beside the row count for the 20 and 21
    # session windows, measured on the weekday session axis the
    # record's own horizon dates were issued under (the price
    # panel's calendar ends before the record begins, so it cannot
    # place a single window).
    overlap = grading.record_horizon_overlap(rows)
    for engine_id, by_length in overlap["by_engine"].items():
        for length, cell in by_length.items():
            print(f"overlap {engine_id} {length} sessions: "
                  f"rows {cell['rows']}, independent windows "
                  f"{cell['independent_windows']}")
    if overlap["unplaced"]:
        print(f"overlap unplaced rows (horizon dates off the "
              f"panel calendar): {overlap['unplaced']}")
    # BH family, paired baselines and the attestation gate
    # (DEEP-PASS 3.2 item 5).
    baselines = grading.paired_baseline_report(rows)
    for engine_id, entry in baselines.items():
        print(f"baseline {engine_id}: pairs {entry['pairs']}, "
              f"mean delta {entry['mean_delta']}, "
              f"p {entry['p_value']} ({entry['state']})")
    # FE08 HAR control (DEEP-PASS 3.2 item 14): Engines 1 and 7
    # against the fixed weight HAR control on QLIKE.
    har = grading.har_control_report(rows, prices)
    for engine_id, entry in har.items():
        print(f"har control {engine_id}: pairs {entry['pairs']}, "
              f"mean engine QLIKE {entry['mean_engine_loss']}, "
              f"mean control QLIKE {entry['mean_baseline_loss']}, "
              f"mean delta {entry['mean_delta']} ({entry['state']})")
        for s in entry["skipped"]:
            print(f"har control skipped {s['row_id']}: {s['reason']}")
    families = grading.engine_cell_family(rows)
    for engine_id, fam in sorted(families.items()):
        decision = grading.probability_render_decision(
            reg.engines[engine_id])
        rendering = ("probability allowed (attestation on record)"
                     if decision["render_as_probability"] else
                     "uncalibrated scores only (no attestation)")
        print(f"family {engine_id}: cells {len(fam['cells'])}, "
              f"BH tested {fam['tested_cells']}, rendering: "
              f"{rendering}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
