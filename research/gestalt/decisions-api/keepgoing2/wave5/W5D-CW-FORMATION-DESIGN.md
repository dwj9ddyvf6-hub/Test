# W5-3 CW DAILY-FORMATION DESIGN, PRE-REGISTERED

Dated 2026-11-14. Wave 5 Lane D. Design only. No result is claimed
in this document, no return has been computed under it, and no
formation under it exists yet. The first live formation possible
under this design is Mon 2026-11-16, the first production capture
of the chain panel. This document is signed and dated before that
formation exists, and any later change to a rule below is a new
pre-registration, not an edit to this one.

SCOPE: Surface, a pre-registered daily-formation design for the
Cremers-Weinbaum (CW) call-minus-put implied-vol spread on the
chain panel that accrues from Mon 2026-11-16. Constraints, the CW
construction is mirrored from the Wave 4 proof, not reinvented;
the estate admission exam is the only grading instrument; no desk
tree edits; paper and shadow only. Outcome, a design exact enough
that a grader can run it without making a design decision.
Proof, this document plus the artifacts it cites. Edges,
dispersion is out of scope (it needs per-session index
constituent weights, which the panel does not carry); the dry
capture of 2026-11-14 is not a formation and never enters any
count below.

## 1. The signal, mirrored from the Wave 4 proof

Source of record: keepgoing2/wave4/V4-V7-RECORD.md (V4 section)
and keepgoing2/wave4/v4_proof.py, proven on
keepgoing2/wave4/v4_cw_proof.json (dry capture: 31 of 31 symbols,
115,718 contracts, 27,405 with modelled IV, CW spreads computed
for all 31).

Construction, mirrored exactly:

- For one symbol on one session, take the stored snapshot rows
  (occ, oi, volume, iv). IV is MODELLED, never measured: Black
  Scholes inversion of Alpaca indicative quote midpoints, flat
  r 0.045, dividend yield SPY 0.013, QQQ 0.005, all other names
  0.0, expiry 21:00 UTC, European; only contracts inside the
  chain_content band are modelled, namely moneyness 0.75 to 1.25
  and expiries within 120 days. Every use of the spread in this
  design is a use of modelled IV and is labeled as such.
- Pair matching: a pair is a call and a put at the same strike
  and the same expiry (the OCC parse key (expiry, strike)), both
  sides present with a modelled IV. Unmatched contracts do not
  enter.
- Sign convention: CW spread for the symbol that session is the
  mean over all matched pairs of (call IV minus put IV). Positive
  means calls are IV-rich against matched puts. Worked anchors
  from the proof file, dry capture 2026-11-14: NVDA minus 0.0129
  on 365 pairs, ALAB plus 0.0654 on 200 pairs, MU plus 0.0233 on
  924 pairs; controls SPY minus 0.0717 on 2,066 pairs, QQQ minus
  0.0945 on 2,048 pairs.
- Minimum pairs per name: a name is CW-rankable on a session only
  if it has at least 20 matched pairs that session. Justification
  from the dry cross-section: 29 of 31 symbols carried 67 or more
  pairs; only FLNC (8 pairs) and EOSE (17 pairs) fell below 20,
  so the floor excludes means built on a handful of modelled IVs
  while costing at most two names on the only cross-section in
  hand. The floor is a fixed construction choice, set tonight,
  not a tuned parameter (see section 8).

Hypothesis, from the source literature as recorded in Wave 3
Lane C: Cremers and Weinbaum (2010) define the spread as above, a
deviation from put-call parity; names with relatively expensive
calls beat names with relatively expensive puts by about 50 basis
points per week in their sample. The design therefore goes long
high CW and short low CW (the as-signed direction; the inverted
direction is a counted trial, section 8, and is not traded).

## 2. Universe and formation validity

- Ranking universe: the 29 Focus names of the panel (SMH, SOXX,
  NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI,
  COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE,
  FCEL, BE, OKLO, VST, CEG, XLE). SPY and QQQ are controls: their
  CW spreads are computed and printed in every grading artifact
  for reference, and they are never ranked and never traded in
  this design. They are the exam benchmarks (section 8).
- A name enters a session's ranking pool only if all of these
  hold that session: (a) its snapshot stored with status ok in
  the panel manifest; (b) at least 20 matched CW pairs; (c) a
  tradable pair (section 3) whose call and put both carry
  quote_bid and quote_ask in that session's IV ledger rows.
  Each failure excludes the name for that session only, and the
  exclusion is named in the grading artifact with its reason:
  no_snapshot, pairs_below_20, or no_priced_pair.
- A formation is valid only if at least 24 names are in the
  ranking pool. A session with fewer is not a formation: it is
  recorded as a skipped session with its exclusion census, and it
  does not advance the accrual count in section 9.

## 3. The traded expression and the traded pair

The book this design feeds is options-only, and the signal is
defined on a matched option pair, so the traded expression is
the pair itself, held as a synthetic forward:

- Long leg name: buy the call, sell the put, same strike and
  expiry (the traded pair). Net position delta is approximately
  plus one per unit of underlying notional.
- Short leg name: sell the call, buy the put, same strike and
  expiry. Net position delta approximately minus one.

Traded pair selection, one deterministic rule: among the name's
matched pairs (section 1) whose expiry is at least 7 calendar
days after the formation date and at most 120 days after it,
take the earliest such expiry; within that expiry take the
strike closest to the session spot; a distance tie takes the
lower strike. If no expiry satisfies the window, the name has no
traded pair that session (exclusion reason no_priced_pair if
quotes are also missing, else no_pair_in_window; both are named
in grading).

## 4. Formation rule

Daily, on each valid formation session, after that session's
panel capture (cron chain-panel-close-capture, weekdays 16:46
ET):

1. Compute the CW spread for every panel symbol from that
   session's stored rows, per section 1.
2. Build the ranking pool per section 2 and rank it by CW spread
   descending. Ties break by symbol ascending, so the ranking is
   fully deterministic from the stored rows.
3. Leg size k = max(1, int(n / 3 + 0.5)) where n is the ranking
   pool size; at the full pool of 29, k = 10. Long leg: the top
   k names by CW. Short leg: the bottom k names by CW. The
   middle names are not held.
4. Weighting: equal weight per name within a leg. Each leg
   carries 50 percent of the cohort's notional, so each held name
   carries 0.5 / k of cohort notional on its side. Gross notional
   is 200 percent of cohort capital (100 long, 100 short) before
   the cohort stacking of section 5.
5. The portfolio the rule implies, stated once: on any session
   the book holds up to five overlapping cohorts (section 5),
   each cohort long synthetic forwards on that formation day's
   top-tercile CW names and short synthetic forwards on its
   bottom-tercile CW names, equal weighted per name, each name
   expressed through the single matched pair of section 3.

## 5. Holding horizon and cohort structure

- Primary horizon: 5 sessions. A cohort formed on session t is
  exited at the close capture of session t + 5 (the fifth panel
  session strictly after formation). The 5-session horizon is
  the literature's weekly horizon (section 1) expressed in
  panel sessions.
- Cohorts overlap: a new cohort forms every valid formation
  session, each cohort carries one fifth of the design's capital,
  and up to five cohorts are live at once. There is no
  non-overlapping variant in the primary design; the 1, 10 and
  21 session horizons exist only as counted exam trials
  (section 8), computed at grade time on the same accrued panel.

## 6. Friction model

Per the dive law, every option leg crosses its spread at both
ends, priced from the bid and ask stored with the panel. The
stored quotes live in the panel IV ledger
(chains_panel/iv_ledger_modelled.jsonl: per OCC per session,
quote_bid, quote_ask, quote_mid), covering exactly the contracts
that carry modelled IV, which includes every traded pair by
construction (section 2, condition c).

- Entry, formation session t, from that session's ledger rows
  for the traded OCCs: a bought leg pays quote_ask; a sold leg
  receives quote_bid. Long synthetic entry debit per unit =
  ask(call) minus bid(put). Short synthetic entry credit per
  unit = bid(call) minus ask(put).
- Exit, session t + 5, from that session's ledger rows: a sold
  leg (closing a long) receives quote_bid; a bought leg
  (closing a short) pays quote_ask. Long synthetic exit proceeds
  per unit = bid(call) minus ask(put). Short synthetic exit cost
  per unit = ask(call) minus bid(put).
- Marks on intermediate sessions use liquidation value, the same
  side convention as exit: a live long synthetic marks at
  bid(call) minus ask(put); a live short synthetic's liability
  marks at ask(call) minus bid(put).
- A name whose traded legs cannot be priced at entry (either
  OCC missing quote_bid or quote_ask in the formation session's
  ledger) is excluded that day, named as no_priced_pair
  (section 2). A name whose legs cannot be priced at the exit
  session is not marked to a model: its exit slips to the first
  later session whose ledger prices both legs, the cohort record
  flags it hold_extended with the sessions slipped, and if no
  such session arrives within 5 further sessions the name exits
  at its last available liquidation mark, flagged
  exit_at_last_mark. Both flags are named per name in grading.
- No mid-price fills, no zero-friction variant, and no
  friction-free number is reported anywhere in grading. The
  gross (mid-to-mid) series may be printed beside the net series
  for attribution, labeled gross, and it is never the graded
  series.

## 7. Return series construction

- Per name, per cohort: signed P&L per unit of notional =
  (liquidation value at the mark date minus liquidation value
  at entry, taken on the position's own side per section 6)
  divided by the formation session's spot. The daily increment
  of that quantity is the name's daily return contribution for
  that cohort.
- Cohort daily return: the equal-weighted sum over held names
  of (0.5 / k per name) times the name's daily increment, long
  names positive-signed, short names taken on the short
  position's P&L.
- Portfolio daily return: the mean over live cohorts of the
  cohort daily returns (each live cohort is one fifth of
  capital; on sessions with fewer than five live cohorts, early
  in the accrual, the unformed fifths are cash at zero and the
  divisor stays 5, so the series is the design's true capital
  return from its first session).
- The graded series is this daily portfolio return series, net
  of the section 6 friction by construction. One row per panel
  session, starting with the second accrued session (the first
  mark).

## 8. The exam it will face, and the trial count

Instrument: tools/admission_exam.py, exam(), run on the variant
matrix built from the accrued forward panel only, benchmarks
SPY and QQQ daily returns over the same sessions, SPA legs
against both, is_new_family = True.

Trial count, stated and justified. The variants considered
tonight, and no others, are:

- Formation quantile: quintile, tercile, quartile (3). Tercile
  is the primary (section 4): on a 29-name pool the quintile
  legs hold about 6 names each, too concentrated for single
  name option spreads; the quartile is the middle option.
- Holding horizon: 1, 5, 10, 21 sessions (4). Five is the
  primary, per the source literature's weekly effect.
- Sign: as-signed (long high CW), inverted (long low CW) (2).

That grid is 3 x 4 x 2 = 24 combinations, and 24 is the
registered trial count. At grade time the exam matrix carries
all 24 variant series computed on the same accrued panel, and
exam() is called with trial_count = 24; the primary series is
the (tercile, 5-session, as-signed) column and its verdict is
read from its own row. Fixed construction choices are not in
the count because exactly one option was ever considered for
each, and each is recorded here so a future change enters the
count then: minimum pairs 20 (set from the dry cross-section's
pair counts, section 1); equal weighting (the only weighting
considered; a CW-proportional weighting was not considered and
would be a new trial if ever run); the traded-pair rule of
section 3 (a single rule, set by the options-only book and the
pair definition); the friction convention of section 6 (a law,
not a variant).

Promotion bars, from the exam tool itself: DSR at least 0.95
with correlation-clustered effective trials, CPCV PBO below
0.2, SPA p below 0.05 against SPY and against QQQ, and, as a
new family, absolute t above 3 on the primary series.

## 9. Minimum accrual for the first lawful grade

The first grade is lawful at 130 accrued panel sessions. The
reasoning, in three parts:

- Horizon resolution: at 130 sessions, cohorts formed in the
  first 125 sessions have fully exited; only the last 5
  sessions' cohorts are still in flight. A grade taken earlier
  grades a book whose recent fifth is unresolved.
- Independent information: the daily series of an overlapping
  5-session design carries about one independent block per 5
  sessions. 130 sessions is 26 non-overlapping blocks, which
  matches the estate's already-registered CW minimum of 26
  formations (Wave 3 Lane C: 30 or more names times 26 weekly
  formations, first testable week of Mon 2027-05-17). The daily
  design reaches the same independent depth sooner in calendar
  terms only because its formations are daily; it does not
  lower the depth bar.
- Exam sample needs: the exam's CPCV leg splits the sample
  into 10 groups and its SPA leg bootstraps a long-run
  variance; both are noise instruments on a few dozen daily
  rows. 130 sessions yields 129 daily portfolio returns, the
  smallest sample this lane will put in front of them.

Calendar expectation, stated as expectation only: counting
weekdays from Mon 2026-11-16, the 130th session falls on Fri
2027-05-14; market holidays push the real date later, and the
session count, not the calendar, governs. An accrual integrity
read (formations present, exclusion census sane, no silent
gaps) is taken at 26 formations, on or about Mon 2026-12-21,
with no exam run and no verdict of any kind.

## 10. Falsifier

At the first lawful grade, the primary series is DEMOTED if any
one of these holds: DSR below 0.95; CPCV PBO at or above 0.2;
SPA p at or above 0.05 against SPY or against QQQ; absolute t
at or below 3; or mean net daily return at or below zero. The
family is KILLED, in the exam's own language, if CPCV PBO is
above 0.5. Demoted means: no promotion, no trading, and the
design is not revised in place; any successor is a new
pre-registration whose trial count carries these 24 trials
forward. No grade, interim Sharpe, or partial-sample statistic
computed before 130 accrued sessions may be cited as evidence
for or against this design, by this lane or any other.

## 11. Data contract

Relied-on artifacts, all under
~/workspace/morgue/state/morgue/chains_panel/, written by
keepgoing2/wave4/v4_chain_panel.py on cron
chain-panel-close-capture (weekdays 16:46 ET):

- Per-symbol snapshot, <SYM>/<YYYY-MM-DD>.json.gz: fields
  underlying, day, spot, spot_source, spot_quote_ts,
  spot_freshness, captured_at_utc, captured_at_et, columns
  (exactly [occ, oi, volume, iv]), rows (one row per contract:
  OCC code, open interest or null, volume or null, modelled IV
  or null), field_coverage (contracts, with_oi, with_volume,
  with_iv), content (iv_moneyness_band [0.75, 1.25],
  enrichment_expiry_days 120, iv_source MODELLED text),
  oi_date, and, for WDC and FCEL, nonstandard_items_excluded
  where adjusted chains were refused.
- IV ledger, iv_ledger_modelled.jsonl: per contract per
  session, underlying, date, occ, expiry, strike, side, iv,
  quote_bid, quote_ask, quote_mid, spot. This is the friction
  price source of section 6.
- Manifest, manifest.jsonl: one line per symbol per session
  with status; a symbol whose line reads error is treated as
  no_snapshot for that session.

Accrual start: Mon 2026-11-16, the first production capture.
The 2026-11-14 dry capture (dry_capture true on every document)
is proof of machinery only and is excluded from every count.

Missing days: a session with no capture for a symbol is a gap,
never backfilled and never forward-filled. A formation that
would form on a missing day for the whole panel does not form
and does not count. A name missing on a mark day carries its
last liquidation mark for at most 2 sessions, flagged
mark_carried; beyond that the exit-slip rule of section 6
governs. A cohort whose exit session is a panel-wide gap exits
on the first later captured session, flagged hold_extended at
cohort level. Gaps are counted and named in every grading
artifact; a silent gap invalidates the grade.

## 12. What this design does not claim

No return, Sharpe, or spread-persistence claim is made. The dry
capture's CW values are a machinery proof on one cross-section,
not evidence about the signal. Whether modelled IV from
indicative midpoints carries the Cremers-Weinbaum effect at all
is part of what the forward exam tests, and the falsifier of
section 10 is written to be able to say no.

Pre-registered 2026-11-14, before the first live formation
exists. Signed: Wave 5 Lane D, Midna subagent, under the
decisions-api-leverage program, keepgoing2/wave5.
