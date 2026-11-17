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

Streaming compaction (GRADING-REPORTS-STREAM-20261116): the
child's one remaining full parse became the kill point itself.
On 2026-11-16 the ledger stood at 435,910 rows / 837 MB and
this phase died OOM (exit 137 standalone, zero lines printed)
before its first report line, on two consecutive refresh runs:
led.rows() materialises every parsed row with every field,
but the four report aggregations read only a small, known
field set. This module now makes ONE streaming pass with
Ledger.iter_rows() and retains only compact rows carrying
exactly the fields the aggregations read (full rows only for
the two HAR-control engines, whose report reconstructs from
the whole forecast row). The aggregation functions in
forecast.grading are called unchanged, on the compact rows,
and print the same lines; no outcome, score, or report
definition changes. The regression blocker is
forecast/tests/test_grading_reports_stream_20261116.py.

Usage: python3 -m forecast.run_grading_reports
   or: python3 forecast/run_grading_reports.py
"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

from forecast import grading, ledger as ledger_mod, registry as registry_mod

LEDGER_PATH = os.path.expanduser(
    "~/workspace/terminal-lineup/forecast/ledger.jsonl")

# Engines whose report (the FE08 HAR control) reconstructs its
# inputs from the whole forecast row: their rows are retained
# in full. Every other forecast row is compacted to the fields
# the four aggregations read.
_FULL_ROW_ENGINES = ("engine_01", "engine_07")


def _compact_value(value):
    """The forecast value reduced to what the aggregations
    read: the declared-baseline control probability
    (paired_baseline_report), and the stated coverage inputs
    (_stated_coverage reads stated_coverage, or the presence
    of the 0.1/0.9 quantile keys -- the quantile values
    themselves are never read on this path)."""
    if not isinstance(value, dict):
        return value
    out = {}
    if "p_control_vix_only" in value:
        out["p_control_vix_only"] = value["p_control_vix_only"]
    if value.get("stated_coverage") is not None:
        out["stated_coverage"] = value["stated_coverage"]
    quants = value.get("quantiles")
    if isinstance(quants, dict) and quants:
        out["quantiles"] = {str(k): 0 for k in quants}
    return out


def compact_rows(led):
    """One streaming pass over the ledger (iter_rows: the
    parsed ledger is never held) retaining only the rows and
    fields the four report aggregations read, in ledger order:

    - forecast rows: type, row_id, engine_id, quantity,
      subject, horizon_open, horizon_close, absence_state and
      the compacted value (record_horizon_overlap,
      _baseline_pairs_by_cell, engine_cell_family); forecast
      rows of the HAR engines are retained in full
      (har_control_report).
    - grade rows: type, forecast_row_id and the grade dict
      (_baseline_pairs_by_cell, engine_cell_family).
    - every other row type is read by none of the four
      aggregations and is not retained.
    """
    out = []
    for row in led.iter_rows():
        rtype = row.get("type")
        if rtype == "forecast":
            if row.get("engine_id") in _FULL_ROW_ENGINES:
                out.append(row)
                continue
            out.append({
                "type": "forecast",
                "row_id": row.get("row_id"),
                "engine_id": row.get("engine_id"),
                "quantity": row.get("quantity"),
                "subject": row.get("subject"),
                "horizon_open": row.get("horizon_open"),
                "horizon_close": row.get("horizon_close"),
                "absence_state": row.get("absence_state"),
                "value": _compact_value(row.get("value") or {}),
            })
        elif rtype == "grade":
            out.append({
                "type": "grade",
                "forecast_row_id": row.get("forecast_row_id"),
                "grade": row.get("grade"),
            })
    return out


def main():
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    prices = grading.PriceSource()
    rows = compact_rows(led)
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
