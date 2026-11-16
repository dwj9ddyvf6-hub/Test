# H5: Gestalt as the Perceptual Organ (ALPHA HUNT, Sat 2026-11-14)

SCOPE: Surface, the book lane's gestalt research files under
research_notes/decisions-api-leverage-20261114/hunt/ only. Constraints,
no desk tree edits, no Tensor or saty contact, no ledger.json positions
touched, no orders, paper only. Outcome, three deliverables: the labeled
read corpus tranche 1, the starter per-pattern calibration table, and
the entry-craft sealed holdout v1. Proof, the files below, parsed and
recomputed after writing. Edges, SIVE has no SIP bars, the chart-study
prose carries no forward outcome field, and the pattern panel's forward
legs have not reached their horizons.

Discipline, stated once and applied throughout: under Kahneman-Klein,
this corpus trains discrimination and calibration, never prophecy.
Every agreement rate below is a discrimination measurement between
readers. No rate in this file is a predictability claim.

## Part 1: Labeled read corpus, tranche 1

File: read_corpus_tranche1.jsonl, 31 lines: 1 schema header record,
29 read records (one per built dry-run pack), and 1 gap record for
SIVE. Each read record carries, per name, at the Fri 2026-11-13 close:

- Pass A geometry fields parsed field-for-field from the dry-run pack
  (close, change, OHLC, volume and ratio, 10 and 50 session ranges,
  SMA and EMA stacks, RSI now and 10 sessions ago, MACD line, signal,
  histogram and its 3-session-ago value, divergence check, 5, 10 and
  21 session returns, relative strength versus SPY at the same three
  horizons, ATR and ATR percent, anchored VWAP). Provenance: code.
- The code MA-stack stage (wave1_bars.stage_truth). Provenance: code.
- The typed pre-read: stage value, the full stage probability
  distribution, and the upside_first probability with its frozen
  bank v2 predicate. Posed 2026-11-14, model gpt-6-luna, before the
  tape it resolves against. Provenance: typed.
- ChartsLector's Friday machine stage where it exists: the six ranked
  basket names (MU rank 29, ALAB 43, CRDO 47, AXTI 50, SNDK 52,
  AAOI 55, all 4A_declining, mapped to stage 4). The other 23 names
  carry an explicit null with the absence reason on the record: SMH,
  SOXX and SIVE sit outside his 55-row US universe by construction,
  and the remaining names have no Lector stage in the sources read.
  Provenance: lector.
- Resolution fields, blank by design, provenance tape-pending:
  next-session verdict (session 2026-11-16), plus-5-session verdict
  (session 2026-11-20), and the upside_first 10-session predicate
  (horizon through 2026-11-30, with hi10 and anchored VWAP levels
  copied onto the record so the harvester needs nothing else).
- Agreement flags (typed versus code, typed versus Lector), labeled
  on the record as discrimination, not correctness.

Spot proof: the MU record reproduces the dry run's instructive row
exactly (typed stage none, code stage 3, Lector stage 4, close
778.31), and the corpus-wide typed versus code agreement recomputes
to the dry-run report's 14 of 29 from the corpus's own source files.

GAP, named first as ordered: SIVE. No pack, no pre-read, no corpus
read: the SIP route serves zero bars for the Swedish listing. The
gap record carries the builder's exact failure string and the
unblocker (register a non-SIP source; the basket lane's Nasdaq
Stockholm route is the named candidate). Monday's live W6 run
inherits this gap by name.

## Part 2: Per-pattern calibration tables, started

File: calibration_table_v1.json. The honest computable set is small
and the table says so in its own totals: 96 resolved
probability-bearing records exist in the estate, of which only 37
are forward-resolved; 99 probability records are tape-pending.
Buckets with n below 10 print counts only and are graded anecdotes.

- Section A, canary stage and verdict (n 24, discrimination against
  the study's own words, packs at 2026-11-09): stage agreement 21 of
  24 (0.875), stage multiclass Brier 0.1582. Per truth stage, all
  anecdotes at n of 8: stage 2, 8 of 8; stage 4, 8 of 8; none, 5 of
  8. Verdict agreement 14 of 24 (0.5833), which exactly equals the
  always-WATCH degenerate baseline on the same set (0.5833): the
  typed verdict leg shows no excess over its baseline here, and the
  table prints that rather than smoothing it.
- Section B, forecast twin level calls (n 37, the estate's only
  forward-resolved probability set; poses of 2026-11-12, resolved on
  SIP closes): outcome base rate 0.7838. Typed twin Brier 0.2197,
  worse than climatology Brier 0.1695 on the same set; hit rate at
  the 0.5 line 26 of 37 (0.7027), below the base rate. The bands
  split honestly: the 0.90 to 1.00 band (n 11) is the one calibrated
  band (mean probability 0.9691, observed 0.9091, Brier 0.0889),
  while the 0.50 to 0.70 band (n 14) carries Brier 0.2672. Three
  bands sit below the rate line and print counts only, including a
  below-0.30 band that went 0 of 4 at the 0.5 line (anecdote).
  By direction: above calls (n 24) Brier 0.1934, below calls (n 13)
  Brier 0.2683. Midna's own twin calls, confidence words only so no
  Brier exists: 32 of 37 hits (0.8649); medium confidence 18 of 21
  (0.8571); high 5 of 5 and low 5 of 7 are anecdotes. Three
  percent-string confidences and one null are named as data dirt in
  the bucket label, not cleaned away.
- Section C, pattern panel form (n 35, discrimination against the
  autopsies' own form claims, move dates 2026-11-11 to 2026-11-13):
  exact match 32 of 35 (0.9143), form multiclass Brier 0.1624. The
  one rate-grade pattern bucket, downtrend_reversal, is 25 of 25
  (n 25). uptrend_pullback 6 of 8 and breakout_extension 1 of 2 are
  anecdotes. Two caveats ride on the record: the panel autopsies
  winners only, so selection is built into the set, and form truth
  is the autopsy's claim, not tape. The forward legs
  (continuation_5 and continuation_10, 70 probabilities) are
  tape-pending with zero resolved: horizons complete 2026-11-18 to
  2026-11-30, and the move-day levels they resolve against live in
  the autopsy pack files, a join the harvester still owes.
- Section D, dry-run stage discrimination (tranche 1 itself, n 29):
  typed versus code overall 14 of 29 (0.4828). By code stage: stage
  4, 10 of 13 (0.7692); none, 4 of 13 (0.3077); stage 3, 0 of 3
  (anecdote). Typed versus Lector on the six ranked names, 5 of 6
  (anecdote). The disagreement concentrates in the code-none class,
  where the typed reader calls a stage the MA rule will not: that is
  the shape the W6 registered falsifier watches, named here as a
  watch row, not a verdict. The 29 upside_first probabilities are
  tape-pending through 2026-11-30.
- Section E, journal grading run 1 (anecdote, n 4 closed trades):
  entry selection 0 of 4 paid, exits on written lines 4 of 4. This
  is the set the entry-craft curriculum was built from.
- Section F, the chart-study prose corpus (12 files, 1,032 Pass A
  geometry lines): graded not computable as a calibration input
  tonight, named rather than forced. The prose carries stage
  postures but no per-read forward outcome field, and names repeat
  across days, so any hit rate computed from it would be fabricated
  precision. Section A is the bridge that exists, because the
  canary packs were built from study entries.

What accrual fills the table, named in the file: tranche 1
resolutions from 2026-11-16 (29 predicates plus next-session and
plus-5 tape verdicts), the 70 pattern continuation legs through
2026-11-30, Drill B nightly probabilities from the 2026-11-16 night
study (30 names a night, Brier-scored as plus-5 resolutions land),
and the sealed holdout monthly re-tests.

## Part 3: Entry-craft sealed holdout v1

Files: holdout_features_v1.jsonl (1 schema record plus 60 windows)
and holdout_outcomes_SEALED.jsonl (60 outcome records).

- Draw rule, stated and seeded: seed 20261114; a random.Random
  shuffle of every eligible (symbol, end index) pair; greedy
  acceptance under a per-symbol cap of 4 and a minimum 12-session
  separation between accepted end indices of one symbol; ids
  assigned after sorting by symbol and date. The draw is
  deterministic: a full builder rerun reproduced the outcomes file
  byte-for-byte (same seal hash).
- Eligibility: SIP-served Focus 30 names (SIVE excluded, no bars);
  window end on or before 2026-09-30; at least 216 sessions of
  history in the window; at least 10 sessions already printed after
  the window end; no single-session close move beyond plus 80 or
  minus 45 percent inside the last 60 window sessions or the
  outcome span (the split and artifact guard; the SOXX raw-basis
  split print is the named case it exists for); exact canary
  (symbol, last bar date) pairs excluded.
- Disjointness: the September 2026 cutoff predates every drill
  practice set identified in the estate as of tonight (canary packs
  at 2026-11-09, pattern panel moves 2026-11-11 to 2026-11-13,
  dry-run packs at 2026-11-13, and Drill A's first draws, which the
  curriculum schedules during the week of 2026-11-16). The window
  registry is published in the features file precisely so future
  Drill A draws can exclude it; only the outcomes are sealed.
- Features per window: the same Pass A geometry field set as the
  corpus, computed point-in-time on bars truncated at the window
  end, plus the code stage at the window and the pack hash. Window
  records were verified to contain zero outcome fields or tokens.
- Outcomes (sealed file only): close at plus 1 and plus 5 sessions,
  returns at both horizons, above-close-at-plus-5, max close
  excursions over 5 sessions, and the frozen upside_first predicate
  over 10 sessions with its event and session offset. Definitions
  are close-based on the standing raw adjustment basis and are
  written in the features file's schema record.
- Seal: sha256 of holdout_outcomes_SEALED.jsonl is
  70f68d50c3127454c4f7d65697e4a31b7c86efd9bbc6692a8240cf3dedb80a6a.
  Sealed means sealed: no drill reads this file until the monthly
  re-test, and this report deliberately prints no outcome aggregate
  from it.
- Coverage gap, named: the draw landed on 25 of the 29 SIP-served
  names. AVGO, OKLO, PLTR and WDC drew zero windows under the stated
  rule and were not hand-added after the fact, because redrawing to
  taste would break the seed's honesty. Window end dates span
  2025-08-11 to 2026-09-30. The curriculum's sealed set is 300
  windows; this v1 is the first 60, and v2 accrual toward 300
  should stratify by symbol so the four missing names enter by
  rule, not by hand.

## Files

- hunt/H5-CORPUS-TRANCHE-1.md (this report)
- hunt/read_corpus_tranche1.jsonl (31 records: schema, 29 reads, 1 gap)
- hunt/calibration_table_v1.json (sections A to F plus honest totals)
- hunt/holdout_features_v1.jsonl (61 records: schema plus 60 windows)
- hunt/holdout_outcomes_SEALED.jsonl (60 records, seal hash above)
- hunt/build_h5.py (the builder; reruns deterministically and
  reproduces every file above from the named sources)

## Open rows

1. SIVE corpus record: blocked on a non-SIP bars source (gap record
   H5-T1-SIVE carries the unblocker).
2. Tranche 1 resolutions: tape-pending; the harvester fills
   next-session fields from 2026-11-16, plus-5 from 2026-11-20, and
   upside_first through 2026-11-30.
3. Pattern continuation legs: 70 probabilities tape-pending, and
   their resolution needs the autopsy pack join named in section C.
4. Chart-study prose: no calibration until a harvester joins dated
   study reads to printed tape (section F).
5. Holdout coverage: AVGO, OKLO, PLTR, WDC absent from v1; the set
   stands at 60 of the curriculum's 300.
6. Forecast twin finding, carried not buried: on the only
   forward-resolved cohort, typed probabilities scored worse than
   climatology (Brier 0.2197 against 0.1695). The 0.90-plus band is
   the exception and the accrual above is what tests whether it
   holds.

STATUS: PARTIAL. The corpus tranche and the sealed holdout are
complete and verified as chartered; the calibration table is a
starter by design, with its honest n (96 resolved records, 37 of
them forward) and every unfilled row named above rather than
rounded up. EVIDENCE POINTER: hunt/read_corpus_tranche1.jsonl
(31 lines, parsed and spot-checked against the dry-run report),
hunt/calibration_table_v1.json (every figure recomputed from the
typed-layer ledgers by hunt/build_h5.py), hunt/holdout_features_v1.jsonl
and hunt/holdout_outcomes_SEALED.jsonl (60 windows, ids matched,
seal sha256 70f68d50c3127454c4f7d65697e4a31b7c86efd9bbc6692a8240cf3dedb80a6a,
reproduced identically on a full builder rerun).
