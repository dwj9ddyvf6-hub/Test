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

Streaming form (GRADING-STREAM-20261106): the classic form held
the whole parsed ledger in this process (1.83 GB measured at
253,163 rows) beside the price panel for the run's whole length,
through the report aggregations as well; on 2026-11-06 the step
died at exit -9 about 44 minutes in, with other lanes on the
host, after three straight failed refresh nights. This runner
now verifies and grades by streaming (Ledger.grading_stream_state
+ grading.run_grading_streaming: the parsed ledger is never
held), and the report aggregations run in a child process
(forecast.run_grading_reports) that loads the rows once and
exits. The counts, the skipped lines, the report lines and the
appended grade rows are unchanged.

Usage: python3 -m forecast.run_grading   (from terminal-lineup/)
   or: python3 forecast/run_grading.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

from forecast import grading, ledger as ledger_mod, registry as registry_mod

LEDGER_PATH = os.path.expanduser(
    "~/workspace/terminal-lineup/forecast/ledger.jsonl")


def main():
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    try:
        state = led.grading_stream_state()
    except ledger_mod.LedgerError:
        print("FAIL: forecast ledger chain does not verify; "
              "refusing to grade", file=sys.stderr)
        return 1
    prices = grading.PriceSource()
    before = state["grade_count"]
    skipped = []
    new_grades = grading.run_grading_streaming(led, prices, reg, state,
                                               skipped=skipped)
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
    # counted and named, never estimated. Streaming form
    # (GRADING-STREAM-20261106): the candidates are walked with
    # iter_rows() against the stream state's graded ids (kept
    # current by the generic pass above), and each grade appends
    # through the same state.
    from forecast import proof_gate
    graded_ids = state["graded_ids"]
    pg_graded = pg_waiting = pg_no_panel = 0
    for row in led.iter_rows():
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
        proof_gate.grade_forward_record(led, row, realised,
                                        stream_state=state)
        pg_graded += 1
    print(f"proof-gate forward checks: {pg_graded} graded, "
          f"{pg_waiting} waiting on their horizon, "
          f"{pg_no_panel} not on the price panel")
    # Report aggregations (overlap, paired baselines, HAR control,
    # cell families) run in a child process that loads the rows
    # once and exits (GRADING-STREAM-20261106); its lines are
    # relayed verbatim, and its failure is this step's failure.
    reports = subprocess.run(
        [sys.executable, "-m", "forecast.run_grading_reports"],
        cwd=os.path.expanduser("~/workspace/terminal-lineup"))
    if reports.returncode != 0:
        print("FAIL: grading report phase exited "
              f"{reports.returncode}", file=sys.stderr)
        return 1
    # Post-append attestation regeneration (HEALTH-R1-D06-20261031):
    # this runner appends grade rows outside refresh_engines, and
    # graded counts are attestation figures, so a grading run that
    # did not regenerate left every attestation contradicting the
    # ledger it attests (the 2026-10-31 evening appends did exactly
    # this to 7 engines). Every append path now closes with the
    # same regeneration refresh_engines runs.
    if new_grades or pg_graded:
        from forecast import refresh_attestations
        changed = refresh_attestations.regenerate()
        synced, deferred = refresh_attestations.sync_pages()
        print(f"attestations regenerated after grading appends: "
              f"{len(changed)} changed; page blocks synced "
              f"{len(synced)}, deferred {len(deferred)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
