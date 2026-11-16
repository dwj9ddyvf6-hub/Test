# Gestalt Pre-Read Dry Run (W6, Sunday Program S5)

Executed Sat 2026-11-14 evening under the Sunday Program charter,
ahead of W6's first live run at Monday's night study. Packs cut at
the Fri 2026-11-13 close; nothing in this run uses weekend or Monday
data. Tools: tools/build_gestalt_packs.py (packs),
tools/run_gestalt_dryrun.py (posing). Records:
runs/gestalt_dryrun_packs.json, runs/gestalt_dryrun_ledger.jsonl.

## Method

Packs for the Focus 30 were built in the frozen bank v2 format
(field-for-field the canary pack shape: sessions, OHLC, volume,
10 and 50 session ranges, SMA and EMA stacks, RSI, MACD, returns,
relative strength versus SPY, ATR, anchored VWAP) from SIP daily
bars fetched through the typed layer's own route
(wave1_bars.fetch_daily_bars), filtered to bars dated on or before
2026-11-13. 29 of 30 packs built, every one with last bar
2026-11-13. SIVE is the named failure: the SIP route serves zero
bars for the Swedish listing, the same limitation the AI basket
lane carries; SIVE gets no pre-read until a non-SIP source is
registered, and Monday's live run inherits this gap by name.

Posing seated exactly the two W6 questions from the frozen bank:
stage (choice, full probability distribution recorded) and the
tape-resolvable predicate upside_first (probability). The verdict
question was not posed; W6 does not seat it.

## Results

Stage, typed pre-read versus the code stage rule
(wave1_bars.stage_truth, the MA-stack rule): agreement 14 of 29,
48.3 percent. The disagreement has a shape: after a week in which
the whole complex fell 3 to 6 percent on Friday alone, the typed
reader calls stage 4 (declining) on 19 of 29 names, while the
strict MA-stack rule calls stage 4 on 13, stage 3 on 3 (MU, PLTR,
CEG), and none on 13. The typed reader reads the break; the code
rule waits for the averages to confirm it. Neither is graded
correct tonight: this is a discrimination measurement between two
readers, and under the Kahneman-Klein discipline adopted for this
lane, discrimination is not predictability.

Stage, typed pre-read versus the standing machine read
(ChartsLector's Friday stages for the six ranked basket names, all
4A_declining, mapping to 4): agreement 5 of 6. The one disagreement
is the most instructive row in the run: MU, where the typed reader
says none, the code rule says 3, and Lector says 4. Three readers,
three answers, on the name the book actually holds. Monday's study
entry for MU is where this disagreement gets its first human-grade
resolution.

Predicate: upside_first probabilities are on record for all 29
names (mean 0.233, range 0.01 for SOXX to 0.57 for CEG). These
resolve against the frozen predicate rule as the next ten sessions
print and are scored by the resolution harvester, not tonight. They
are the dry run's calibration seed: the first W6 cohort whose
probabilities were written before the tape they predict.

Context, stated exactly: the bank's canary stage figure (0.875,
21 of 24) was graded against study entries' own stage words. The
48.3 percent above is graded against a mechanical code rule. The
two rates measure different truths and are never blended. Monday's
full Focus 30 study creates the first same-session standing-read
set, which is the comparison W6 was designed for.

## Midna-verification protocol, exercised

Four checks, all by direct read: (1) every pack's last bar is
2026-11-13 (no leakage past Friday's close); (2) pack fields match
the canary format line by line on a sampled pack; (3) ledger
records carry the full stage probability distribution and the
predicate probability; (4) the one apparent failure of the run, a
predicate reading of None in the posing script's printout, was
traced to the print statement reading a "value" key the predicate
answer does not carry; the raw record shows probability 0.13 for
SMH present and correct. A print bug, not a data gap, proven from
the artifact.

## Spend

Harness budget file (date 2026-11-14): before posing 53 requests,
$0.01133; after 82 requests, $0.013506. The dry run: 29 requests,
$0.002176.

## Carried falsifier and Monday

W6's registered falsifier stands: if the typed stage's disagreement
with the study's own stage concentrates in one stage class across
the first live weeks, the pack spec is missing a field and the
missing field gets named. Monday's night study runs the seat live
on the full Focus 30 (29 SIP-served names plus SIVE named unseated)
beside the study's own reads, and the comparison set this dry run
could not build (a same-session standing stage for every name)
exists from that night forward.

STATUS: GREEN for the dry run as chartered (packs built, pre-reads
posed through the governed harness, verification protocol
exercised, agreement and disagreement rates delivered, spend
reported). EVIDENCE POINTER: runs/gestalt_dryrun_ledger.jsonl
(29 records), runs/gestalt_dryrun_packs.json (29 packs, 1 named
failure).
