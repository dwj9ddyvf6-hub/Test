# W7B. FIT-PROXY-PIT BUILD AND PEAD FAIR FIGHT (Wave 7, Lane B, Sun 2026-11-15 night)

SCOPE: Surface: keepgoing2/wave7/ only, two legs. W7-4 executes FIT-PROXY-PIT-v1 exactly per the W6B scoping data contract (keepgoing2/wave6/W6B-FIT-LO14-SCOPING.md) and faces the rebuilt member to the fleet admission exam at trial count 46. W7-6 runs the PEAD fair fight at the authors' 60-session horizon on the broadest universe the held earnings corpus supports. Constraints: held data only, no fetches made, shadow only, no desk edits, every output labeled PROXY where the FIT proxy is concerned, no em dashes in this record. Outcome: one verdict per leg, in numbers. Proof: the scripts and result JSONs named at the end of this record, plus the graveyard cross-check inside the PEAD leg. Edges: the true Coval-Stafford FIT stays blocked on fund holdings and flow data (open row OR-1, due 2026-12-12) and is not claimed anywhere in this lane; what was built is the PROXY, labeled at every step.

X10 RESTORATION NOTE (owner order 2026-11-15 01:15 ET): nothing in this lane was scoped down for speed, so nothing needed restoring. The FIT pass ran the full held name-day pass over the full 2018 to 2026 window and the exam ran at count 46 with unchanged hurdles. The PEAD leg ran every filer in the held corpus with computable 60-session legs, full window and post-2020. The only wait in the lane was the load rail: the box sat above the 2.5 load ceiling for about 43 minutes (1-minute load 7.12 at first check, falling to 2.39 at 06:57 UTC) and the heavy FIT pass started only after the ceiling cleared, FIT first and PEAD second, one heavy job at a time.

## W7-4. FIT-PROXY-PIT-v1 (PROXY): BURIAL AS A FIND, ON ONE NAMED HURDLE

Build, per the contract: split-adjusted SIP daily bars with volume from keepgoing2/wave3/focus_bars.json (29 Focus names plus SPY and QQQ, no fetches). Per name per session, trailing 20-session mean volume and trailing 60-session population stdev of daily returns from prior data only (at least 20 prior returns or the day is unscored), excess return versus SPY in percent, and the FIT-PROXY-v1 gates unchanged (volume ratio at least 1.5, absolute excess at least 2.0 percent, absolute excess at least 1.0 times sigma; contribution on a gated down day is absolute excess times volume ratio minus 1). Membership for every overnight leg inside quarter Q is the fixed split from the completed prior quarter Q minus 1: the 14 lowest prior-quarter FIT-PROXY-SELL scores form ON_fit_lo14_pit. Unscored names rank as highest pressure and are excluded from the lo half until they have a fully scored quarter; the operationalization used, stated in the build script, is at least 20 scoreable days inside the prior quarter. Membership quarters: Q2 2018 through Q4 2026, 35 quarters (Q1 2018 flat, no completed prior quarter in the held bars). Scored name counts per prior quarter run from 17 (Q1 2018) to 29 (from Q2 2025 onward). Series construction is the family exam's universe() construction (mean overnight leg over members present, minimum 5 names, flat 0.0 below the floor): 2,229 grid sessions, 2018-01-03 to 2026-11-13, formed on 2,169 sessions.

Rebuilt member standalone numbers (PROXY): mean +13.72bp per night, annualized Sharpe 1.462, t 4.35. The as-stamped lookahead column it replaces printed mean +19.32bp, Sharpe 1.918, t 5.70 in the Wave 4 exam. Point-in-time stamping therefore costs the member about 5.6bp per night and about 0.46 of Sharpe; a real overnight premium survives in the rebuilt column, smaller than the stamped artifact claimed.

Exam (tools/admission_exam.py, the full 42-column family matrix of keepgoing2/wave4/v2_family_exam.py with the single change that ON_fit_lo14 is replaced by the rebuilt column, benchmarks SPY and QQQ total returns, new-family form, SPA bootstrap 1000, trial count 46):

| Hurdle | Bar | Rebuilt member (PROXY) | Read |
|---|---|---|---|
| DSR at count 46 | at least 0.95 | 0.99688 (N_eff 6.57, 6 clusters) | PASS |
| SPA vs SPY | below 0.05 | 0.002 | PASS |
| SPA vs QQQ | below 0.05 | 0.003 | PASS |
| Absolute t | above 3 | 4.35 | PASS |
| Family PBO on the same matrix | below 0.2 | 0.222 | FAIL |

Exam tool verdict for the rebuilt member: REJECT (PBO 0.222 >= 0.2), and the family verdict on this matrix is REJECT. PBO is a family-level statistic: in the as-stamped Wave 4 matrix it printed 0.000, and replacing the one column moved it to 0.222, which also blocks every other column in this run (ON_focus29 prints DSR 0.99956, Sharpe 1.671, t 4.97 here and is likewise REJECT on the PBO row alone). Under the tasking's binary and the scoping contract's own falsifier (any hurdle missed closes the rebuilt member as a find), the verdict is: BURIAL. FIT-PROXY-PIT-v1 (PROXY) is not promoted as a lawful family member. It is a REJECT, not a family KILL (PBO 0.222 is below the 0.5 kill bar), and the burial is narrow and named: four of five hurdles clear, including DSR at the honest count 46, and the single failing row is the family PBO of the matrix it was examined in. The as-stamped ON_fit_lo14 column stays in the record as a labeled lookahead artifact, never cited as evidence either way, per the scoping decision.

Friction context, printed beside the exam result as tasked (held table, keepgoing2/wave4/v1_friction.json, via the Wave 6 scoping record): the stamped lo14 basket carries an equal-weight gross of +19.21bp per night, a basket auction cost of +2.68bp, and a net at auction of +16.53bp per night on the mean-of-per-name basis (crossing is dead: net at crossing -32.03bp). That context describes the stamped basket's names, not the rebuilt rotating membership, and no tradable-form verdict is taken on the rebuilt member: the exam burial above closes it as a find before any friction exercise, and no accrual is wired for it.

Trial cost charged: 1 (the primary quarterly rebuilt variant), family combined count 45 to 46, exactly as scoped. The daily quarter-to-date alternative form was not run; if it ever is, it is counted as 47 before grading.

## W7-6. PEAD FAIR FIGHT AT 60 SESSIONS: THE AUTHORS' HORIZON DOES NOT REVIVE THE LEG

Construction: the graveyard leg (foundry/c3_graveyard.py) kept identical in every part except the axis in dispute. Event mapping from the held corpus keepgoing2/wave5/w5c_earnings_edgar.json (673 prints) with the graveyard's own acceptance-time approximation, surprise as the reaction-signed event-session excess close return versus SPY, drift as excess return versus SPY from the event close. An analyst-consensus surprise measure was searched for on the box and none exists as held data, so the sort is the reaction-signed measure and the fair fight runs on the horizon axis, as the tasking allows. Universe: the corpus itself contains exactly 24 filers, so the broadest universe the held corpus supports is all 24 of them (AAOI, ALAB, AMAT, AMD, AVGO, AXTI, BE, CEG, COHR, CRDO, CRWV, EOSE, FCEL, FLNC, LITE, MRVL, MU, NVDA, OKLO, PLTR, RKLB, SNDK, VST, WDC); widening beyond them would need a new fetch and none was made. Events with a computable 60-session leg: 649 of 673 full window, 544 post-2020.

Cross-check that the machine is the graveyard's machine: recomputed on the graveyard's own drift21 event set (655 events), leg at +5 is -78.79bp and leg at +21 is -61.05bp, matching foundry/c3_results.json to the printed digit on both horizons.

60-session results, terciles sorted by reaction-signed surprise within each window (friction 10bp round trip; headline net subtracts 10bp once from the long-short leg, and the per-side alternative of 20bp total is printed beside it):

Full window (649 events, terciles of 216, 217, 216):
- Top surprise tercile drift60: +874.08bp mean, sd 4,231.79bp, t 3.04, n 216.
- Middle tercile drift60: +750.56bp mean, t 2.77, n 217.
- Bottom surprise tercile drift60: +1,647.91bp mean, sd 6,243.72bp, t 3.88, n 216.
- LEG (top minus bottom): gross -773.83bp, Welch t -1.51. Net at 10bp: -783.83bp. Net at 20bp per side: -793.83bp.
- Sign class: positive surprise (n 301) +872.70bp, t 3.68; negative surprise (n 348) +1,278.56bp, t 4.30; positive minus negative gross -405.86bp, Welch t -1.07, net at 10bp -415.86bp.

Post-2020 (544 events, terciles of 181, 182, 181):
- Top surprise tercile drift60: +1,027.59bp mean, t 3.09, n 181.
- Middle tercile drift60: +907.97bp mean, t 2.89, n 182.
- Bottom surprise tercile drift60: +2,002.90bp mean, t 4.03, n 181.
- LEG (top minus bottom): gross -975.31bp, Welch t -1.63. Net at 10bp: -985.31bp. Net at 20bp per side: -995.31bp.
- Sign class: positive surprise (n 251) +1,034.04bp, t 3.76; negative surprise (n 293) +1,550.25bp, t 4.47; positive minus negative gross -516.21bp, Welch t -1.17, net at 10bp -526.21bp.

Read, in numbers: every tercile drifts up strongly against SPY over 60 sessions on this high-beta Focus filer sample, and the ordering is the reverse of PEAD: the worst reaction names drift the most (+1,647.91bp full window, +2,002.90bp post-2020), the best reaction names the least of the extremes (+874.08bp, +1,027.59bp). The 60-session leg is therefore large and negative (gross -773.83bp full window, -975.31bp post-2020) but statistically indistinguishable from zero at event grain (Welch t -1.51 and -1.63; sign-class t -1.07 and -1.17), because 60-session excess drifts carry standard deviations of roughly 4,200 to 6,700bp. Verdict: the fair fight at the authors' own horizon does not revive PEAD on this estate's data. The graveyard's -61.05bp at +21 was not an artifact of a short horizon; at +60 the spread is wider in the same wrong direction for the published strategy and still not significant. The leg stays buried, now with its open flank closed on the record.

Trial cost charged: 1 new trial for the +60 horizon read (the sign-class cut is a reporting cut of the same read, not a separate trial). PEAD family cumulative horizon reads on this corpus after this leg: 3 (+5 and +21 from the graveyard casting, +60 here).

## FILES AND SPEND

- keepgoing2/wave7/w7b_fit_pit_build.py and w7b_fit_pit_series.json (membership by quarter, prior-quarter scores, the rebuilt series) and w7b_fit_build.log.
- keepgoing2/wave7/w7b_fit_pit_exam.py and w7b_fit_pit_exam.json (full 42-variant exam output at count 46) and w7b_fit_exam.log.
- keepgoing2/wave7/w7b_pead60.py and w7b_pead60_results.json and w7b_pead60.log.
- This record: keepgoing2/wave7/W7B-FITPIT-PEAD.md.
- Fetches made: none. Typed spend: none, $0. No desk files edited.

STATUS: GREEN for W7-4 as an executed build and exam with a burial verdict in full numbers (the verdict is a burial; the lane's work is complete and proven on the final artifacts), and GREEN for W7-6 as an executed fair fight with the leg's numbers in full. EVIDENCE POINTER: keepgoing2/wave7/w7b_fit_pit_exam.json (rebuilt member DSR 0.99688, SPA 0.002 and 0.003, t 4.35, PBO 0.222, verdict REJECT), keepgoing2/wave7/w7b_fit_pit_series.json (mean +13.72bp, Sharpe 1.462, 2,169 formed of 2,229), keepgoing2/wave7/w7b_pead60_results.json (leg60 gross -773.83bp, Welch t -1.51, n 649; post-2020 -975.31bp, t -1.63, n 544; graveyard cross-check exact at -78.79bp and -61.05bp). Open rows named: (1) the true Coval-Stafford FIT remains blocked, OR-1 due 2026-12-12, untouched by this lane; (2) the daily quarter-to-date PIT form remains unrun and uncounted (it becomes trial 47 if ever graded); (3) no analyst-consensus surprise series exists on the box, so the consensus-surprise axis of the PEAD fair fight remains untested here, named rather than silently skipped.
