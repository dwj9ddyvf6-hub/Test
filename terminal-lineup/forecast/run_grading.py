#!/usr/bin/env python3
"""Live grading runner (cure G1, 2026-10-29).

Before this script existed, the shared grading machinery was only
ever exercised inside refreshers' synthetic self-tests on throwaway
ledgers: nothing graded the live forecast ledger, which is why
8,970+ ledger rows carried 0 grades. This runner grades every
matured, not-yet-graded live forecast against the shipped price
panel, appends the grade rows to the same ledger, and prints the
counts plus every skipped row's reason (a matured row that cannot
resolve is named, never silently dropped and never fatal to the
rest of the run).

Usage: python3 -m forecast.run_grading   (from terminal-lineup/)
   or: python3 forecast/run_grading.py
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
    if not led.verify_chain():
        print("FAIL: forecast ledger chain does not verify; "
              "refusing to grade", file=sys.stderr)
        return 1
    prices = grading.PriceSource()
    before = sum(1 for r in led.rows() if r.get("type") == "grade")
    skipped = []
    new_grades = grading.run_grading(led, prices, reg, skipped=skipped)
    panel_last = max(
        (cal[-1] for cal in prices.calendars.values() if cal),
        default=None)
    print(f"grades before: {before}; new grades: {len(new_grades)}; "
          f"grades after: {before + len(new_grades)}; "
          f"panel last session: {panel_last}")
    for s in skipped:
        print(f"skipped {s['row_id']} ({s['engine_id']}, "
              f"{s['kind']}): {s['reason']}")
    print(f"skipped total: {len(skipped)}")
    # Proof-gate forward checks (hookup 2026-10-30): the Aperture
    # proof gate's forward records (kind
    # provisional_proof_forward_check) are not price-resolvable by
    # the generic resolvers; their realised value is the issuing
    # engine's own forward check, computed by forecast.proof_gate
    # from the frozen rule. That function had no production caller,
    # so the 4,641 records from 2026-10-28 could never grade. This
    # pass is the caller: a record grades only when its full frozen
    # horizon has traded on the price panel; anything else is
    # counted and named, never estimated.
    from forecast import proof_gate
    graded_ids = {r.get("forecast_row_id") for r in led.rows()
                  if r.get("type") == "grade"}
    pg_graded = pg_waiting = pg_no_panel = 0
    for row in led.rows():
        if row.get("type") != "forecast":
            continue
        if (row.get("outcome") or {}).get("kind") != \
                "provisional_proof_forward_check":
            continue
        if row["row_id"] in graded_ids:
            continue
        sym = (row.get("outcome") or {}).get("symbol") \
            or row.get("subject")
        cal = prices.calendars.get(sym)
        if not cal or row["horizon_open"] not in cal:
            pg_no_panel += 1
            continue
        closes = [prices.close(sym, d) for d in cal]
        realised = proof_gate.forward_return(
            closes, cal.index(row["horizon_open"]),
            reg.proof_gate_rule(row["engine_id"]))
        if realised is None:
            pg_waiting += 1
            continue
        proof_gate.grade_forward_record(led, row, realised)
        pg_graded += 1
    print(f"proof-gate forward checks: {pg_graded} graded, "
          f"{pg_waiting} waiting on their horizon, "
          f"{pg_no_panel} not on the price panel")
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
