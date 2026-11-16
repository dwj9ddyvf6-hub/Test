# C4 Capture: Wiring Point and Operations

Workstream W4. Typed spend: $0.00. Date: 2026-11-15 (America/New_York).

## The wiring point, stated exactly

The book has no programmatic intent hook. Book intents originate as
decision entries in ~/workspace/midna-book/JOURNAL.md (the card
convention: a dated header carrying a J-id, an Instrument line, a
Setup line, and a Decision line), and fills land in
~/workspace/midna-book/ledger.json through fill_engine.record_fill.
No callback exists that capture could attach to without changing book
behavior, so capture attaches as a watcher on the book's own intent
artifacts:

1. Trigger: watcher.py runs on a 15 minute cron cycle
   (c4-capture-cycle). Each cycle it scans JOURNAL.md for decision
   entries whose header type begins with ENTRY or EXIT and whose
   Instrument field names a single symbol (not the book itself), with
   a J-id that is neither in the arming baseline nor already captured.
   Each such entry triggers exactly one intent_capture record, built
   by capture.build_record at detection time.
2. Quote timing honesty: the quote is fetched at detection time, not
   at the journal decision timestamp, and every record carries
   detection_lag_seconds so the gap is a graded property of the data.
   Nothing is backfilled.
3. Prospective only: the 130 journal entries present at arming
   (2026-11-15T23:52:44Z) form the baseline in state.json and are
   never captured. Capture covers intents written after arming only.
4. Fill linkage: each cycle also scans ledger.json fills. A fill
   whose decision_id matches a captured intent produces one append
   only outcome_link row. The book's fills are simulated fills under
   its bar based charter rule, and the row says so.
5. Fail open and read only: the watcher opens book files read only,
   writes only inside this folder, and logs a capture fault and moves
   on. The book cannot be blocked, slowed, or altered by capture;
   the book does not know the watcher exists.

## Files

1. SCHEMA.md: the record schema (c4-capture/1), field by field.
2. capture.py: quote routes, record builder, ledger append, and the
   synthetic demonstration entry point.
3. watcher.py: the trigger and fill linkage described above.
4. run_cycle.sh: one watcher cycle.
5. capture_ledger.jsonl: the append only capture store.
6. state.json: armed_at, baseline J-ids, captured and linked sets.
7. watcher.log: cycle log.
8. DESK-TAP-DESIGN.md: the desk side design (PARTIAL by design).
9. VERIFICATION.md: the proof record for this build.
