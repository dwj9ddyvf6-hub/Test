# C4 Capture: Verification Record

Workstream W4. Typed spend: $0.00. Date: 2026-11-15 (America/New_York).
All checks below ran after the last code change to capture.py and
watcher.py, except where a check is itself the event recorded.

## Book capture half

1. Synthetic end to end record: capture.py --synthetic-demo wrote one
   intent_capture row for SYNTH-C4-20261115-01 (SPY, buy 10 shares),
   labeled synthetic in its flag and its reason, through the live
   quote path. Read back from capture_ledger.jsonl: quote status ok
   via feed iex after the sip attempt failed with HTTP 403
   (subscription does not permit querying recent SIP data), the
   failure recorded in the record's attempts list; quote labeled IEX
   top of book only, not consolidated NBBO, is_consolidated_nbbo
   false; quote_ts 2026-11-13T21:00:00Z with quote_age_seconds_at_
   capture 183158.2 and quote_stale true, so the stale after hours
   quote is flagged on the record's face, never presented as live.
2. Watcher arming: first run armed at 2026-11-15T23:52:44Z with a
   baseline of 130 pre-existing journal entries excluded from
   capture. A second consecutive run wrote 0 new rows (idempotent).
3. Real intent trigger, proven on a temporary copy of JOURNAL.md (the
   real journal was never modified): after baselining the copy, one
   appended ENTRY entry (J-20261115-T2, SPY) produced exactly one
   capture record with side buy and qty 10 parsed from the Decision
   line, a live quote fetch, and detection_lag_seconds recorded; a
   third run wrote 0 new rows.
4. Fill linkage, proven on temporary copies: a temp ledger.json fill
   with decision_id J-20261115-T2 produced exactly one outcome_link
   row carrying fill_price 100.05 and the simulated fill class label;
   a repeat run wrote 0 new rows.
5. Defect found and cured during verification: capture.append_rows
   bound its default ledger path at function definition time, so the
   first trigger test's row landed in the real capture_ledger.jsonl
   instead of the test ledger. Cure: the default now resolves at call
   time in capture.py, the fixed path was retested (check 3 above ran
   after the cure), and the stray row (J-20261115-T1, a test fixture
   on a temp journal copy, not a book decision) is retained in the
   real ledger under an append only correction row that names it,
   excludes it from every grade, and excludes it from the watcher's
   captured set (watcher.py honors correction rows; the real watcher
   rerun after the cure shows captured_intent_ids empty and
   capture_rows_total 3: synthetic, fixture, correction).
6. Cron arming: job c4-capture-cycle, interval 15m, timezone
   America/New_York, enabled, created 2026-11-15 and read back with
   cron view: body runs run_cycle.sh, reads back state.json and the
   ledger tail, and forbids changes outside this folder. Next run at
   creation: Sun 2026-11-15 19:09:24 EST. The add call itself timed
   out on the tool path; the job's existence and body were verified
   by cron status and cron view rather than assumed from the call.
7. No real book intent occurred during this run (the book's last
   journal entries are dated 2026-11-13), so the first records are
   the synthetic demonstration plus the excluded test fixture, as
   labeled. The first real capture lands on the next ENTRY or EXIT
   journal entry written after arming, via the armed cron.

## Desk tap half

Design only, per DESK-TAP-DESIGN.md. Verdict PARTIAL by design. No
desk code was read for modification and none was touched; component
names in the design were verified by directory listing and by the
C4-RUNFILE.md inventory only.

## Named open rows

1. Consolidated NBBO (SIP) quotes are blocked by the current
   subscription (HTTP 403 on recent SIP data). Until that changes,
   equity records carry IEX top of book, labeled as such, or record
   unavailable. This is the same blocker named in the desk design.
2. No numeric per intent volatility forecast exists to join
   (forecast field records unavailable with the reason, per schema).
3. Depth beyond the top of book has no lawful source in the estate.
4. Detection lag: the watcher polls every 15 minutes, so a real
   record's quote is the quote at detection, with the lag recorded
   per record. A landing that needs tighter lag must shorten the
   cadence, not edit records.
5. Option intent capture is implemented (DXLink route in capture.py)
   but not exercised tonight: no option intent occurred and the
   synthetic demonstration used an equity intent. The options path
   is therefore UNVERIFIED as a code path, named here rather than
   implied green by the equity proof.

STATUS, book half: GREEN. Evidence pointer: capture_ledger.jsonl
(synthetic record read back, check 1), state.json (armed_at,
baseline 130, captured set after correction handling), watcher.log,
and the temp copy trigger and linkage results in checks 3 and 4, all
in or cited from this folder, produced after the last code change.
STATUS, desk half: PARTIAL by design. Evidence pointer:
DESK-TAP-DESIGN.md in this folder.
