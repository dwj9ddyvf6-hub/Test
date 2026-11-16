# H1 CONVEYOR RUN 1, ALPHA HUNT (Sat 2026-11-14)

SCOPE: Surface: the 23 registered candidates in ~/workspace/midna-book/strategy-candidates/ (12 invention files, 5 forced files, 2 CTB spot expressions, C1 cool relaxed, squeeze redesign, washed-out scan, and the Biotech2k file carried by its surviving member CAND-ROT-04). Constraints: research lane only, no desk tree edits, no Tensor or saty code touched, candidates and shadows only, paper only, no strategy, sizing, risk or basket change. Outcome: every candidate classified by kind; every tradable rule with an honestly generatable daily return series run through the fleet admission exam (tools/admission_exam.py); every other candidate carrying a named missing input or a confirmed registered next step. Proof: hunt/exam_results.json (raw exam output), hunt/conveyor_run1.py (the series builder, rerunnable), hunt/conveyor_ledger.jsonl (one row per candidate). Edges: the exam needs at least 2 trial columns for its PBO leg, so each examined candidate ran as a small declared family (registered form plus named parameter neighbors); where that family is too thin for a fair PBO, the leg is named invalid rather than counted, per the Tempering Law (nothing dies without a fair attempt and the exam).

## Counts by verdict

| Verdict | Count | Candidates |
| --- | --- | --- |
| PROMOTE | 0 | none |
| REJECT (examined, not promoted, not killed) | 4 | CAND-ROT-04, CAND-WASH-01, CAND-FORCED-01, CAND-FORCED-05 |
| NOT_EXAMINED (missing input named) | 7 | CAND-CTB-SPOT-ADA, CAND-CTB-SPOT-LINK, CAND-FORCED-02, CAND-FORCED-03, CAND-FORCED-04, CAND-C1-COOL-RELAXED, CAND-SQUEEZE-REDESIGN-01 |
| NEXT_STEP_CONFIRMED (measurement or design-stage, no trading exam) | 12 | CAND-INV-01 through CAND-INV-12 |
| KILL | 0 | none. Three mechanical exam outputs said KILL on their PBO legs; each PBO leg is documented below as not a fair family test, and no kill is recorded from any of them. |

## Examined candidates

Exam bars: PROMOTE needs DSR at least 0.95 (correlation-clustered effective trials), CPCV PBO below 0.2, SPA rejection at p below 0.05 against both SPY and QQQ, and, for a new family, |t| above 3. Family KILL only at PBO above 0.5 on a fair trial family.

| Candidate | DSR | N eff (raw trials) | PBO | SPA vs SPY | SPA vs QQQ | Sharpe (ann) | t | n days | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAND-ROT-04 (basket a, registered) | 0.998 | 28.0 (56) | 0.889, leg invalid, see note | 0.216 | 0.453 | 0.953 | 2.98 | 2457 | REJECT |
| CAND-WASH-01 (registered condition) | 0.806 | 2.0 (6) | 0.511, leg weak, see note | 0.704 | 0.714 | 0.364 | 1.20 | 2728 | REJECT |
| CAND-FORCED-01 (registered form) | 0.855 | 1.0 (3) | 0.244 | 0.006 | 0.002 | 0.320 | 1.05 | 2728 | REJECT |
| CAND-FORCED-05 (registered form) | 0.996 | 1.0 (3) | 0.911, leg weak, see note | 0.015 | 0.004 | 0.758 | 2.49 | 2728 | REJECT |
| CAND-CTB-SPOT-ADA | undefined (zero series) | 3.0 (3) | degenerate, not counted | n/a | n/a | 0.000 | 0.00 | 91 | NOT_EXAMINED |
| CAND-CTB-SPOT-LINK | undefined (zero series) | 3.0 (3) | degenerate, not counted | n/a | n/a | 0.000 | 0.00 | 91 | NOT_EXAMINED |

### CAND-ROT-04, The Coffin Rebuilt (deepest pass, as briefed)

Series: daily equity reconstructed share by share from the oracle cross-check fills (qj/qj_trail15_fills.json for basket a, qj/qj_trail15_basket_fills.json for basket b) marked on the Alpaca SIP daily bars in the biotech test home, 2017-01-31 to 2026-11-06, commissions as recorded in the fills. Reconstruction proof: basket a total return +430.79 percent against the oracle record +430.79 percent; basket b +583.62 percent against +583.28 percent (the 0.34 point gap is one forward-filled mark, named here, immaterial to the exam). Trial discipline: trial_count 56, the ROT-01 sweep grid the candidate was selected from; the wider program grids (ROT-02, ROT-03, the options cells) are excluded, so the DSR of 0.998 is an upper bound and is labeled as such. Result: DSR passes at 0.998 and the Sharpe is 0.953 annualized, but SPA does not reject against either benchmark (SPY p 0.216, QQQ p 0.453): on a daily grain the sleeve, which sits in cash or one sector for months, does not beat buy and hold in the SPA sense over this window, however strong its return per unit drawdown (14.01 in the frozen record). Verdict REJECT at this pass, which changes nothing about its standing: the registered grading instrument for ROT-04 is its forward paper test (first signal 2026-11-30) and the live desk sleeve, and both continue untouched. PBO note: the mechanical family verdict printed KILL because the only persisted trial columns are the two basket forms of the same machine, near-identical series between which CPCV best-picking is a coin flip by construction. The fair PBO family is the 56-cell sweep grid, whose per-cell daily return matrix was never persisted (summary statistics only; the same record defect the S6 rerun cured for rotation lists). That matrix is the named missing input in the ledger; until it exists, no PBO verdict, promote or kill, is recorded for this candidate.

Triple expression (required for every REJECT):

- Share sleeve form: as built. The desk sleeve coffin_rebuilt and the isolated shadow forward test already are the share form: monthly worst-sector ranking at the 126-session window, lowage-only stopped-falling gate, sector ETF basket (a), month-end trail-15 close test, 18-month cap, entry-month-low invalidation.
- Options structure form: OPT-B2K-1 as registered in the family file, corrected by its own test result: the rank-1 exit was falsified (it leaves the move behind), so the options form rides the ROT-04 trailing exit instead: 12 to 18 month slightly in-the-money calls on the qualifying sector ETF, held while the share form holds, closed when the trail-15 month-end test or the 18-month cap closes the share form. Debit is the full risk; no short leg.
- Shadow form: the coffin-rebuilt-forward shadow simulation already running in files ($100,000 shadow capital, no broker orders, first signal month-end 2026-11-30), graded quarterly percent versus SPY and QQQ. It is the verdict-grade record; the desk sleeve record is bookkeeping beside it.

### CAND-WASH-01, Washed-Out Extremity Scan

Series: the conveyor's mechanical translation, stated plainly because the registration is a watch condition and not an entry signal: each night, names in the biotech SIP pull (about 150 large-cap names, 2016-01-04 to 2026-11-06; survivorship and large-cap bias named as limits) meeting RSI(14) at or below 32 and 10-session return at or below minus 15 percent form an equal-weight basket held exactly one session. The trial family is the registered condition, its registered parent condition (RSI at or below 37, 20-session return at or below minus 18 percent, at least 20 percent under the 20-session high), and RSI alone; trial_count 6 counts those three plus the nested census conditions named in the registration. The registered condition flagged on 594 days. Result: DSR 0.806, SPA 0.704 and 0.714 (no rejection), |t| 1.20. The one-session translation does not carry an examinable edge on this universe, which does not touch the candidate's registered use: it flags names for a full read, and its binding falsifier is the forward 20 flagged name-nights test, still to run from registration. PBO note: 0.511 on three nested columns is a coin flip, not a family kill; the REJECT rests on DSR and SPA. Verdict REJECT (exam translation), watch condition stands under its own falsifier.

Triple expression:

- Share sleeve form: none as an entry sleeve. The share form is the watchlist itself: flagged names enter the night study queue for a full section 5 read, and any card is decided under the standing card process. Registering it as an automatic share sleeve would contradict its own registration.
- Options structure form: for a flagged name that passes the full read, the options form is a defined-risk debit call spread dated past the next catalyst, sized by the card's registered stress loss; the extremity condition supplies the timing, the read supplies the thesis, neither alone is sufficient.
- Shadow form: a nightly shadow log of flagged name-nights with next-session and 5-session forward marks, which is exactly the instrument its falsifier grades (20 flagged name-nights, baseline-relative). Building that log is the candidate's real next step and is rowed below.

### CAND-FORCED-01, Month-End Rebalance Window

Series: SPY/QQQ 50/50 basket, causal form: at the close four sessions before month-end, the month-to-date return is ranked against the trailing 60 completed monthly returns; top quartile fades short, bottom quartile fades long, held five sessions (final three of the month plus the first two of the new month); middle months flat. Neighbors: 4-session hold, and tercile bands. 165 active days in 2,728. Result: SPA rejects against both benchmarks (p 0.006 and 0.002, the only SPA passes in this run besides FORCED-05), but DSR 0.855, PBO 0.244 and |t| 1.05 all fail their bars. The flow signature is real enough to beat the benchmarks in the SPA sense and far too weak, at this frequency, to deflate. Verdict REJECT; its registered falsifier (12 consecutive forward month-ends) remains the slow honest test and is unaffected.

Triple expression:

- Share sleeve form: the registered form itself as a paper sleeve on the book: fade SPY/QQQ in the final three sessions of top and bottom quartile months only, exit at the second session of the new month, no trade in middle months.
- Options structure form: the book form named in the registration: put spreads after a top-quartile month, call spreads after a bottom-quartile month, expiring just past the exit session, sized by registered stress loss, defined risk only.
- Shadow form: a month-end shadow ledger scoring the window fade and a mid-month control window on identical rules, which is what its falsifier's concentration leg grades (a strategy that makes its money mid-month is not trading this flow).

### CAND-FORCED-05, Tax-Loss Seasonality

Series: bottom-decile year-to-date basket over the same SIP pull, year-to-date measured causally 11 sessions before year-end, bought across the final December sessions and held through the first ten January sessions; neighbors: bottom quintile, and a 5-session January hold. 200 active days across 10 seasons. Result: DSR 0.996 and SPA passes against both benchmarks (0.015, 0.004), but |t| 2.49 fails the new-family hurdle of 3, and there are only 10 independent Decembers in sample, so no in-sample machinery can manufacture the missing independence. Verdict REJECT on the hurdle, with the strongest near-miss profile of the run. PBO note: 0.911 is recorded in the ledger with its caveat (CPCV splits cut across seasons, so the leg is weak evidence here); the REJECT does not need it. The first forward season opens within weeks (December 2026 selling window, January 2027 rebound), and the registration already accepts a two-season falsifier; this candidate is the conveyor's top forward-watch priority.

Triple expression:

- Share sleeve form: the registered basket exactly: bottom-decile liquid losers, equal weight, bought across the final December sessions, held through the first ten January sessions, exited on schedule, basket form only.
- Options structure form: none registered, and the conveyor registers none: the registration states the basket's breadth is the risk control, and an options form on single names would contradict it. The nearest lawful options expression, index call spreads over the January window, is a different candidate and would need its own registration.
- Shadow form: a December shadow basket papered from the first December session of 2026 with a matched mid-pack control basket marked on identical dates, which is precisely the comparison its falsifier grades over two seasons.

### CAND-CTB-SPOT-ADA and CAND-CTB-SPOT-LINK, the zero-fire finding

The basis series was built honestly: PF perp 4-hour closes from the latest desk snapshot (2,000 bars) against spot 4-hour closes from warm bars, overlap 546 bars, 2026-08-16 to 2026-11-14. Over the entire overlap the basis never reached the registered band on either side: ADA basis range minus 24.4 to plus 24.1 bps (mean plus 3.0, median plus 3.1), LINK minus 21.7 to plus 21.2 bps (mean plus 1.4). Bars at or beyond a 10 bps discount: ADA 4, LINK 12. Bars at the registered 25 bps discount: zero, both underlyings. The strategy return series is therefore identically zero, DSR is undefined, and the exam's mechanical PBO of 1.0 on zero-variance columns is an artifact, discarded and named in the ledger. Verdict NOT_EXAMINED for both: the trigger never fired, so there was no fair attempt to grade. Two named outputs: (1) the missing input is spot 4-hour history before 2026-08-16 (the perp leg already reaches 2025-12-16 in the snapshot), source Kraken spot OHLC archive or Alpaca crypto bars, owner desk feed lane; (2) a calibration observation for B5, not a conveyor change: on the served window the 25 bps band sits entirely outside the observed basis range, the same unreachable-gate shape the calibration program keeps finding, and whether the band or the window is wrong is a question the longer history answers.

## Not examined, missing inputs named (tradable)

| Candidate | Exact missing input | Source | Owner |
| --- | --- | --- | --- |
| CAND-FORCED-02 | Index reconstitution event calendar (announcement date, effective date, add or delete, index) for the last four events with ten or more qualifying names | FTSE Russell, S and P Dow Jones Indices, Nasdaq published lists | H1 conveyor lane (build the calendar file) |
| CAND-FORCED-03 | Historical open interest by strike for SPY, QQQ and high-OI names around expiries | TastyTrade chain archive or OPRA-derived vendor pull | Options data lane |
| CAND-FORCED-04 | Historical earnings surprises with implied move at print, at least 60 qualifying prints over two seasons (desk calendar carries forward dates only) | Earnings vendor history plus Truth Serum implied-move machinery at print time | Options data lane with book event-card lane |
| CAND-C1-COOL-RELAXED | Its registered first test is cadence, not returns: qualifying symbol-weeks per week at atr ceiling 1.5 on the C1 census feature table | Calibration lane census machinery (the conveyor does not touch Tensor code) | Calibration lane |
| CAND-SQUEEZE-REDESIGN-01 | (1) The bounded-grid cadence sweep on the 4-hour lever (daily sweep caps at 0.20 per week vs the 0.8 bar); (2) a registered exit and hold rule for return grading | 4-hour bars already served for ADA and LINK; wider served universe per the F4 cure | Calibration lane (sweep), candidate owner (exit spec) |

## Measurement inventions and design-stage items (no trading exam, by kind)

All 12 invention registrations carry a registered next step that this run confirms as present and correctly stated; none was missing its next step. Detail per row is in the ledger. The four that move because of this run or the calendar:

- CAND-INV-11 (Sleeve Genetics): its entry ticket was the admission exam as tested code. That ticket is now punched (tools/admission_exam.py with its proof script), so the registered next step advances to the comparative pilot: one evolved generation versus one random generation, identical gauntlet, identical forward window.
- CAND-INV-05 (Predator Sleeves): still staged on a precondition that does not exist yet, a verdict-grade champion (own closes at least 30, no NETTED flag; registered count zero). Next step is the champion census at the fleet flip, Mon 2026-11-16.
- CAND-INV-04 (Truth Serum) and CAND-INV-07 (Disagreement Index): forward accrual begins Mon 2026-11-16 per their registrations (serum scoring at capture; nightly disagreement accrual toward 200 symbol-days).
- CAND-INV-01 (Internal Market) and CAND-INV-09 (Base-Rate Engine): designs filed, nothing built, and no build date registered anywhere. The next step is confirmed but unscheduled; that scheduling gap is an open row below, not a silent pass.

## Open rows

| # | Row | Owner | Date |
| --- | --- | --- | --- |
| 1 | Persist the 56-cell ROT-01 sweep daily return matrix so CAND-ROT-04 gets a fair PBO leg | Biotech test lane | Next sweep rerun, before B5 Fri 2026-11-20 grading if the lane can land it |
| 2 | Backfill ADA/USD and LINK/USD spot 4-hour history to at least 2025-12-16 (matching the perp leg), then rerun both CTB exams | Desk feed lane | H1 conveyor run 2 |
| 3 | Build the index reconstitution event calendar file (FORCED-02) | H1 conveyor lane | H1 conveyor run 2 |
| 4 | Source historical OI by strike (FORCED-03) and historical earnings surprises with implied moves (FORCED-04) | Options data lane | Named at B5 Fri 2026-11-20 |
| 5 | Run the C1 cool relaxed cadence replay at atr ceiling 1.5 | Calibration lane | Named at B5 Fri 2026-11-20 |
| 6 | Run the squeeze redesign 4-hour cadence sweep; register an exit and hold rule | Calibration lane; candidate owner | Named at B5 Fri 2026-11-20 |
| 7 | Build the washed-out shadow log (flagged name-nights with forward marks) so its registered falsifier can bind | H1 conveyor lane | From Mon 2026-11-16 |
| 8 | FORCED-05 first forward season: shadow the December 2026 basket with its mid-pack control | H1 conveyor lane | December 2026 window |
| 9 | Schedule builds for CAND-INV-01 stage 2 and CAND-INV-09 first test (designs filed, no dates exist) | Invention lane | Named at B5 Fri 2026-11-20 |
| 10 | Sleeve Genetics comparative pilot (evolved versus random generation) now that the exam ticket is punched | Invention lane | Staged from Mon 2026-11-16 |

## Method limits, stated once

All non-ROT-04 series are gross of costs; the registered falsifiers are net of costs and forward, so every exam number here is an upper bound on the tradable claim. The SIP pull behind WASH and FORCED-05 is a roughly 150-name large-cap universe with survivorship limits, not the full market. SPA and DSR at the daily grain punish sparse, long-hold machines (ROT-04 is the case in point); the exam is one instrument, and where a candidate carries its own registered forward grading instrument, that instrument governs its life and death, per the Tempering Law.

STATUS: PARTIAL. Evidence pointer: hunt/exam_results.json (6 exam records with full statistics), hunt/conveyor_ledger.jsonl (23 rows, validated JSON), hunt/conveyor_run1.py (rerunnable series builder; ROT-04 reconstruction reproduces the oracle totals to the printed digit on basket a). Proven: 4 tradable candidates examined and rejected on named legs with triple expressions carried; the CTB zero-fire finding measured on 546 bars per underlying; 12 inventions confirmed to their registered next steps. Open: 7 candidates not examined, each with its exact missing input, source and owner rowed above; zero promotions, zero kills.
