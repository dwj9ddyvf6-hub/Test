# W5C: TWO UNLOOKED DECOMPOSITIONS OF THE FIND (Wave 5, Lane C)

SCOPE: Surface: the ON_focus29 overnight basket series only, decomposed two ways (calendar span of the leg; earnings prints into the leg). Constraints: Wave 3 and Wave 4 files read-only, desk tree untouched, paper and shadow only, no new variants beyond the ledger below. Outcome: a verdict per class in the brief's taxonomy (carries / contributes / closed), with every number recountable from the artifacts named. Proof: w5c_stats.json (class statistics), w5c_exam.json (exam tool output at both trial counts, per-series SPA, Welch difference tests), w5c_series.json (every series and every event leg), w5c_earnings_edgar.json (the print corpus). Edges: the earnings corpus covers the 24 domestic filers among the 29 names; the 5 excluded names are named with their reason in Part 2.

## Trial count: the augmentation, stated once

Wave 4 family count: 45. New decomposition variants computed by this lane: Part 1 gives 7 (weekday-only, weekend-only, Tue-open, Wed-open, Thu-open, Fri-open, span-2 holiday class); Part 2 gives 2 (earnings-event-only basket, non-event basket). Total new: 9. **Augmented count for both decompositions: 54.** Every DSR below is printed at 45 and at the augmented count. One definitional note that governs both parts: DSR is a property of a series inside a matrix at a count, not of a series alone, because the exam tool scales the effective trial count by the matrix's cluster ratio and deflates by the matrix's Sharpe dispersion. Each part below exams its own decomposition matrix (the Wave 4 usage pattern: one matrix per family question), and the matrix composition is stated beside every DSR so the parent can recount or re-matrix.

Verdict bar used uniformly: a class **carries** only if it clears DSR 0.95 at the augmented count inside its decomposition matrix, its standalone SPA rejects against both SPY and QQQ, and (where it is proposed as a conditioner) it separates from its complement class. A class is **contributes** when it is positive with significant raw statistics but fails any leg of that bar. A class is **closed** when there is nothing there to carry forward.

## Reproduction check (before any decomposition is trusted)

The basket was rebuilt exactly as Wave 3 built it (per-name overnight return open over prior close from focus_bars.json, equal-weight mean over names with both prints, minimum 10 names). The rebuilt headline reproduces the record asserted in w5c_analysis.py: 2,229 sessions, 2018-01-03 to 2026-11-13, mean +16.46bp per night, Sharpe 1.67, t 4.97. Decomposition proceeds from this verified series.

## PART 1: WEEKDAY VERSUS WEEKEND LEGS

Classification: a leg's span is the calendar days between its open date and the prior basket session's close date (the first leg's prior close is the 2018-01-02 SPY bar). Weekend class = span of 3 or more calendar days (Friday close to Monday open plus every holiday-spanning leg of 3 or more days, per the brief; its opens are 418 Mondays and 44 Tuesdays after Monday holidays). Weekday class = span exactly 1, split by open weekday. Span exactly 2 (24 legs, midweek single-holiday spans such as Wednesday close to Friday open) is its own class and sits in neither headline series.

| Class | n legs | Mean bp/night | Std bp | t | Sharpe (frequency-annualized) | Share of total return |
|---|---|---|---|---|---|---|
| Full basket | 2,229 | +16.46 | 156.38 | 4.97 | 1.67 | 100% |
| Weekday (span 1) | 1,743 | +17.28 | 151.06 | 4.78 | 1.61 | 82.1% |
| Weekend class (span 3+) | 462 | +13.47 | 176.34 | 1.64 | 0.55 | 17.0% |
| Span 2 (holiday) | 24 | +14.27 | 131.04 | 0.53 | 0.18 | 0.9% |
| Weekday, Tue opens | 415 | +20.75 | 148.64 | 2.84 | 0.96 | |
| Weekday, Wed opens | 453 | +28.71 | 143.74 | 4.25 | 1.43 | |
| Weekday, Thu opens | 442 | +7.72 | 163.94 | 0.99 | 0.33 | |
| Weekday, Fri opens | 433 | +11.75 | 146.68 | 1.67 | 0.56 | |

Weekday minus weekend mean difference: +3.81bp, Welch t 0.42, p 0.671. The two classes do not separate from each other, even though their standalone strengths differ sharply.

Exam (admission_exam.exam on the 8-column decomposition matrix: full, weekday-only, weekend-only, the four weekday splits, span-2; sub-series are flat 0.0 on nights outside their class; benchmarks are SPY and QQQ total returns on the same grid, Wave 3 construction). Matrix facts: 5 clusters of 8 columns, N_eff 28.13 at count 45 and 33.75 at the augmented count, CPCV PBO 0.244, family SPA 0.000 vs SPY and 0.002 vs QQQ.

| Series | DSR at 45 | DSR at augmented | Sharpe (flat-filled) | t | Per-series SPA vs SPY | Per-series SPA vs QQQ |
|---|---|---|---|---|---|---|
| ON_full (in this matrix) | 0.9090 | 0.8866 | 1.67 | 4.97 | (family leg) | (family leg) |
| Weekday-only | 0.8795 | 0.8516 | 1.60 | 4.77 | p 0.000 | p 0.010 |
| Weekend-only | 0.0334 | 0.0252 | 0.55 | 1.64 | p 0.511 (stat 0.0) | p 0.509 (stat 0.0) |
| Wed-open only | 0.7336 | 0.6875 | 1.41 | 4.19 | p 0.387 | p 0.491 |
| Tue-open only | 0.2244 | 0.1871 | 0.95 | 2.82 | p 0.467 | p 0.486 |
| Thu-open only | 0.0052 | 0.0035 | 0.33 | 0.99 | not run (raw t below 1) | not run |
| Fri-open only | 0.0265 | 0.0194 | 0.56 | 1.66 | not run | not run |
| Span-2 only | 0.0012 | 0.0008 | 0.18 | 0.54 | not run | not run |

The ON_full row is the matrix-dependence warning made concrete: the same series that printed DSR 0.9995 at count 45 inside Wave 4's 42-column family matrix prints 0.9090 at the same count inside this 8-column matrix, because this matrix clusters to 5 of 8 (effective count 28.13) where the family matrix clustered to about 6.4 of 42. Neither number is an error; they answer different selection questions. The decomposition matrix is the harsher and, for a decomposition claim, the relevant one, because the decomposition variants are what was selected among here.

### Part 1 verdicts

- **Weekday legs: CONTRIBUTES, and is the economic carrier.** 82.1 percent of the find's cumulative return sits in span-1 legs at +17.28bp a night, t 4.78, and the weekday-only series rejects SPA against both benchmarks standalone (p 0.000 and 0.010). It does not carry under the bar above: its DSR at the augmented count inside the decomposition matrix is 0.8516, below 0.95, and it does not separate from the weekend class (difference t 0.42). Forward cell named on the typed seat's advice (seat 1 below): **W5C-WEEKDAY-FWD**, a shadow cell graded from the already-armed on-focus29 shadow accrual by leg span, first integrity read at 20 weekday legs, verdict alongside the parent falsifier at its 60 sessions, demoted if the weekday-leg mean net of the registered 5bp is not positive. It is a contributes-class cell, not a promotion.
- **Weekend class: CLOSED as a standalone conditioner.** Positive mean (+13.47bp) but t 1.64, DSR 0.0252 at the augmented count, SPA statistic 0.0 against both benchmarks. Nothing here supports a weekend-only cell, and nothing here supports excluding weekend legs either (the separation test fails in both directions), so weekend legs stay inside the unconditioned basket falsifier and the weekend conditioner cell is closed for the map write-back.
- **Weekday splits: no cells.** Wednesday opens are the strongest single split (+28.71bp, conditional t 4.25) and Thursday opens the weakest (+7.72bp, t 0.99), but both splits fail standalone SPA and DSR by wide margins on their flat-filled series. They are recorded as observations inside the weekday class; naming either a conditioner would be trial creep on eyeballed splits.
- **Span-2 holiday class: CLOSED.** n 24, t 0.53, DSR 0.0008. Nothing there.

## PART 2: OVERNIGHT INTO EARNINGS

Corpus route: estate records first. The estate's earnings stores (the desk's earnings.json and phase_earnings.json) hold only the next upcoming print date per name in late 2026, no history, so they cannot cover the window; that is a coverage fact about those files, not an absence claim about earnings data. The corpus was therefore built from EDGAR: data.sec.gov/submissions per company CIK (CIKs resolved from www.sec.gov/files/company_tickers.json under the SEC-declared User-Agent "Muse Research research@example.com", the Wave 4 verified pattern), filtering form exactly "8-K" (8-K/A amendments excluded) with "2.02" in the filing's items string, window 2018-01-01 to 2026-11-13, the full bar window with no bounding needed. The submissions payload carries acceptanceDateTime per filing, so no per-filing index fetch was required.

Coverage: 24 of 29 names are domestic 8-K filers and all are covered. Excluded, named: SMH, SOXX, XLE (funds, no earnings 8-Ks) and ARM, TSM (foreign private issuers reporting on Form 6-K and 20-F, not 8-K Item 2.02). **Total prints: 673, and all 673 mapped to an overnight leg** under the convention below (per-name mapped counts equal per-name filing counts for every name; w5c_stats.json carries the full per-name table and w5c_series.json carries every event leg with its accession).

Per-name print counts (filings = mapped event legs): NVDA 37, AVGO 34, AMD 38, MRVL 25, AMAT 35, MU 35, SNDK 7, WDC 36, AAOI 37, COHR 36, LITE 40, CRDO 19, ALAB 11, AXTI 46, CRWV 7, PLTR 25, RKLB 22, FLNC 21, EOSE 33, FCEL 37, BE 34, OKLO 3, VST 36, CEG 19. (Counts track listing history: SNDK and CRWV list in 2025, OKLO in 2024, CEG spins off in 2022.)

Event convention, applied uniformly: a name's event overnight leg is the first overnight leg whose open (09:30 ET on the open date) is strictly after the filing's acceptance timestamp converted from UTC to America/New_York. A print after the close on day T and a print before the open on day T+1 therefore map to the same leg, the close of the last session before the print to the open of the first session after it. A basket session is an event session when at least one Focus name has its event leg on that session: 508 of 2,229 sessions.

| Series | n | Mean bp/night | Std bp | t | Sharpe (frequency-annualized) |
|---|---|---|---|---|---|
| Basket on event sessions | 508 | +27.58 | 182.24 | 3.41 | 1.15 |
| Basket on non-event sessions | 1,721 | +13.18 | 147.79 | 3.70 | 1.24 |
| Pooled per-name event legs | 673 | +46.73 | 960.11 | 1.26 | 0.43 |
| Pooled per-name non-event legs | 51,292 | +16.55 | 231.43 | 16.20 | (pooled t is not a graded statistic; legs are clustered by session) |

Event minus non-event at basket level: +14.40bp, Welch t 1.63, p 0.104. Not significant. The pooled per-name row shows why the basket level is the graded level: a single name's earnings overnight leg is a gap event with a 960bp standard deviation, so the reporter-level mean of +46.73bp carries a t of only 1.26 even pooled, before any clustering correction that would lower it further.

Exam (admission_exam.exam on the 3-column matrix: full, event-only, non-event-only, flat-filled outside their class; same benchmarks). Matrix facts: 1 cluster of 3 columns, N_eff 15.0 at count 45 and 18.0 at the augmented count, CPCV PBO 0.467, family SPA 0.000 vs SPY and 0.003 vs QQQ.

| Series | DSR at 45 | DSR at augmented | Sharpe (flat-filled) | t | Per-series SPA vs SPY | Per-series SPA vs QQQ |
|---|---|---|---|---|---|---|
| ON_full (in this matrix) | 0.9996 | 0.9995 | 1.67 | 4.97 | (family leg) | (family leg) |
| Event-only | 0.9684 | 0.9633 | 1.14 | 3.38 | p 0.342 | p 0.487 |
| Non-event-only | 0.9835 | 0.9806 | 1.24 | 3.70 | p 0.022 | p 0.166 |

### Part 2 verdict

- **Earnings-event class: CONTRIBUTES as a subset, CLOSED as a conditioner.** Event nights are richer on average (+27.58bp against +13.18bp) and the event-only series is positive and significant raw (t 3.41 conditional, 3.38 flat-filled) with a DSR that clears 0.95 at the augmented count inside its small matrix (0.9633). It still fails the carries bar twice over: its standalone SPA does not reject against either benchmark (p 0.342 and 0.487; the series is invested on only 22.8 percent of nights and cannot outrun the benchmarks' full daily returns on the SPA comparison), and, decisively for a decomposition, the event increment over non-event nights is not significant (Welch p 0.104) while the non-event subset itself carries the premium at +13.18bp, t 3.70, DSR 0.9806. The premium does not need earnings nights to exist. Conditioning the basket on earnings prints would discard 77.2 percent of sessions in exchange for an unproven increment. No forward conditioner cell. Open row for the parent, named not landed: the running shadow accrual does not flag earnings sessions, so the forward read of this decomposition requires an earnings flag on the accrual before any forward event-session count can accrue; the historical corpus in w5c_earnings_edgar.json is the flag source when that wiring is done.

## TYPED SEATS (advisory only)

Via ~/workspace/midna-book/typed-layer/decisions_harness.py, bank "w5c-decompositions" version 1, full probability vectors in w5c_typed_seats.json. Spend: **2 requests, $0.000098 total** (seat 1 $0.000053, seat 2 $0.000045).

- Seat 1, weekday forward cell: **open_cell, probability 0.97** (no_cell 0.01, insufficient_evidence 0.02). The cell named in Part 1 follows this advice, labeled contributes-class.
- Seat 2, earnings-leg reading: **unproven_increment, probability 1.0** (conditioner_candidate 0.0, nothing_there 0.0, insufficient_evidence 0.0). This matches the Part 2 verdict exactly.

## ARTIFACTS (all in keepgoing2/wave5/)

| File | Contents |
|---|---|
| w5c_analysis.py, w5c_stats.json | Basket rebuild with reproduction assertion, Part 1 class statistics, Part 2 event mapping and statistics, the augmentation ledger |
| w5c_series.json | Dates, prior close dates, spans, all 10 daily series, both benchmark total-return series, the 508 event session dates, all 673 event legs with accessions |
| w5c_exam.py, w5c_exam.json, w5c_exam_run.log | Both exam matrices at both trial counts, per-series SPA, Welch difference tests |
| w5c_fetch_earnings_edgar.py, w5c_earnings_edgar.json | EDGAR submissions corpus build and the 673-print corpus with acceptance timestamps and route log |
| w5c_typed_seats.py, w5c_typed_seats.json | The two advisory seats and their full records |

## SUMMARY FOR THE PARENT (lift-ready)

Decomposing ON_focus29 by leg span and by earnings prints leaves the find standing but reshapes where it lives: weekday (span-1) legs are the economic carrier with 82.1 percent of the cumulative return at +17.28bp a night (t 4.78, standalone SPA rejecting against both benchmarks), yet the weekday-only series does not clear deflation at the augmented count inside its own decomposition matrix (DSR 0.8516, N_eff 33.75), so it grades CONTRIBUTES with a shadow conditioner cell (W5C-WEEKDAY-FWD) opened on the typed seat's 0.97 advice; weekend-class legs (+13.47bp, t 1.64, DSR 0.0252, SPA statistic 0.0) are CLOSED as a conditioner, with the weekday-weekend difference itself insignificant (t 0.42), so weekends stay in the unconditioned falsifier. Earnings nights, built honestly from 673 EDGAR Item 2.02 prints over the full 2018-2026 window (all mapped, 508 event sessions), are richer on average (+27.58bp vs +13.18bp on non-event nights) but the increment is not significant (Welch p 0.104), the event-only series fails standalone SPA (p 0.342 and 0.487), and the non-event subset carries the premium by itself (DSR 0.9806 at the augmented count), so the earnings conditioner is CLOSED, a reading the second typed seat endorsed at probability 1.0; total typed spend 2 requests, $0.000098.

STATUS: PARTIAL in the doctrine sense: both decompositions are computed, examed at both counts, and verdicted with recountable artifacts (evidence pointers: w5c_stats.json, w5c_exam.json, w5c_earnings_edgar.json, w5c_typed_seats.json), and the named open rows are the forward ones: W5C-WEEKDAY-FWD grades only as forward sessions accrue from Monday 2026-11-16, and the earnings decomposition has no forward read until the shadow accrual carries an earnings flag.
