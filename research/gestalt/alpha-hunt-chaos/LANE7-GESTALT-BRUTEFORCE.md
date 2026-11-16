# LANE 7: THE GESTALT BRUTE-FORCE SWEEP

Owner order Sun 2026-11-15 08:18 ET: brutally brute force the Full Gestalt with the Decisions API, every facet, every variable, every combination of variables, graded only on resolved outcomes in estate records, with trial accounting as the spine. Built on Lane 6's variable register and combination map (LANE6-GESTALT-FULL.md, 133 variables, 34 graded axes). Read-only on strategies; no trading.

Register of record: `GESTALT-SWEEP-REGISTER.jsonl` in this folder, 24,517 rows, one row per combination tested or accounted. Seat run records: `GESTALT-SWEEP-SEAT-RUNS.jsonl` in this folder.

## 1. HONEST POWER STATEMENT (read this first)

The estate's resolved-outcome base is thin, and this sweep does not pretend otherwise:

- Book resolved trades: **4** (SHOP, MO, ELF, NVDA; all losses, total −$2,460.13). Nothing about expression, sizing, or exit behavior can be graded on n=4.
- Ghost Book: 21 priced fires, **0 resolved**. Ungradable until the Lane 8 resolver is built.
- Forecast resolutions: the log's own day tallies total **319** (239 hits, 79 misses, 1 untestable) across 7 grading days. This sweep's parser recovered **311** of them mechanically (232 hits, 79 misses, 2 untestable). All 79 misses reconcile exactly; the 7-hit shortfall is leg counting (tallies count a two-leg index call as 2, the parser counts the call as 1). Parsed base hit rate 0.746.
- Night-study indicator panel: **499 name-night observations, but only 8 independent nights** (study nights 2026-11-03 through 2026-11-12), and the 5-session horizon resolves for only **4** of those nights (194 observations). Nights, not observations, are the effective sample. Every statistic in the panel block is clustered by night for exactly this reason.
- Pattern ledger: 35 records, **0 continuation resolutions** (70 checks pending). Section 11 self-audit: resolutions file **empty**. Forecast Twin book record: 37 calls, all pending in the book (this sweep resolved all 37 sweep-side from daily bars; the book record itself is not amended by that).
- Of Lane 6's **6,579 axis combinations** (34 singles, 561 pairs, 5,984 triples), **6,522 are UNGRADABLE-YET**: the axis states (dealer positioning, lens verdicts, Echo reads, engine agreement, wave fires, breadth, sector tide) were never persisted per resolved outcome. Only 41 axis combinations are graded via the panel, 1 via the forecast corpus, 1 via the control line.

Conclusion of the power statement: this sweep could only ever return two products, and it returns both: (a) the combinations that separate at honest N (there are none, Section 2), and (b) the gradability map with the accrual wiring each family needs (Section 9).

## 2. HEADLINE RESULT

**Separators found: ZERO.** Denominator printed beside it, as ordered: 17,790 panel state-cells tested (5,930 per horizon × 3 horizons), 128 forecast-corpus cells, 11 twin cells, under a separator rule fixed before any result was read:

- Panel: n ≥ 30 AND nights ≥ 4 AND |nightly-cluster t| ≥ 3 AND Benjamini-Hochberg q ≤ 0.10 within its (horizon, order) family.
- Forecast: n ≥ 20 AND BH q ≤ 0.10 across the 128-cell family.
- Twin: n ≥ 10 for a graded bucket.

No cell at any horizon, any order, in any corpus meets its rule. The strongest cells in the estate are named in Sections 4 and 5 as LEADS, with their q values printed; a lead is a reason to keep accruing, never a finding. The typed seat, asked independently, agrees: it rated the probability that any of the 24 strongest cells is a real repeatable effect at 0.01 to 0.04 (Section 8).

One graded object does separate, and it is a control, not a signal: the anti-Midna portfolio (the negation of Midna's own selection) returned +268.80bp at t 4.37 in its founding measurement (n=58), while Midna's selection excess over that control is −3.33bp. The anti portfolio separates from zero; Midna's selection does not separate from its own negation. That is the A29 control-line row, graded, and it is the most decision-relevant number in this report.

## 3. METHOD

**Battery arithmetic validated exact before use.** The panel's nine axes are computed with the gestalt's own published arithmetic, verified against the night study's recorded metrics to full float precision on overlapping nights: RSI is Cutler (SMA-based) RSI14; ATR is the simple 14-session mean of true range; volume ratio is today's volume over the mean of the PRIOR 20 sessions; RS10 is the name's 10-session return minus SPY's; range10 is hi10/lo10 − 1. The panel is therefore the gestalt grading itself, not a reimplementation of it.

**Panel.** Each study night's own bars pull (the point-in-time universe that night, no lookahead) joined to forward outcomes from the weekend study's daily_long bars (99 names + SPY + QQQ through 2026-11-13). Join loss is universe difference only: zero close mismatches above 1.5% on joined names. 499 observations. Outcomes are excess returns versus SPY at three horizons: overnight (close to next open), next session (fwd1), 5 sessions (fwd5). Axes (9): RSI (OS/LOW/NEU/HIGH/OB), MACD (BULL+/RECOV/FADE/BEAR− from histogram sign × line sign), VOLR (DRY/NORM/HEAVY/CLIMAX), RS10 (WEAK/LAG/LEAD/STRONG), DAY (BDOWN/DOWN/FLAT/UP/BUP), RNG10 (TIGHT/NORM/WIDE/EXT), ATRPCT (LOW/MID/HIGH/EXT), STACK (UP/MIX/DOWN), POS10 (BOT/MID/TOP). All singles, all pairs, all triples enumerated: 5,930 cells per horizon.

**Base rates (the pool every cell is graded against).** Overnight excess −5.25bp; fwd1 +36.37bp; fwd5 +180.35bp. The fwd5 window is a rising tape for this basket; a positive fwd5 cell mean is the base rate talking until its nightly t and q say otherwise.

**Deflation.** BH correction within each (horizon, order) family for the panel (families of roughly 4,500 tested cells at triple order) and across the 128-cell forecast family. Nightly clustering is the correlation discount: cells sharing a night share the tape, so the t statistic is computed on nightly cell means, not on pooled observations. Lane 6's interaction accounting stands behind the axis block: of 561 axis pairs, 545 (97.2%) had never been examined before this program.

**Register accounting.** 24,517 rows: Block P (panel cells) 17,790; Block F (forecast cells) 128; Block T (twin) 11; Block M (book, control line, and named ungradable objects) 9; Block A (Lane 6 axis space) 6,579. Statuses: GRADED 4,289; LOW-N 8,537 (statistics computed, below the reporting floor); EMPTY 5,105 (cell never occurred); UNGRADABLE-YET 6,522; GRADED-VIA-PANEL 41; EXAMINED-NOT-GRADED 11; CO-READ-NOT-GRADED 4; CURATED-SCREENED-NOT-GRADED 6; GRADED-VIA-FORECAST 1; GRADED-VIA-CONTROL-LINE 1.

## 4. PANEL RESULTS

Per horizon: graded cells 1,856 (overnight), 1,856 (fwd1), 524 (fwd5). The fwd5 pool is the thinnest and produces the largest raw numbers, which is exactly the trap the nights floor and BH exist for.

RSI singles, all horizons (the gestalt's most-used variable):

| Horizon | Cell | n | Nights | Excess | Hit | t (nightly) | q |
|---|---|---|---|---|---|---|---|
| overnight | RSI=OS | 64 | 8 | +48.19bp | 0.578 | 0.07 | 0.982 |
| overnight | RSI=NEU | 89 | 8 | −47.11bp | 0.461 | −0.72 | 0.982 |
| overnight | RSI=OB | 52 | 7 | +22.76bp | 0.577 | 0.71 | 0.982 |
| fwd1 | RSI=OS | 64 | 8 | +128.20bp | 0.656 | 0.55 | 0.983 |
| fwd1 | RSI=OB | 52 | 7 | +64.35bp | 0.654 | 1.11 | 0.983 |
| fwd5 | RSI=OS | 32 | 4 | +521.37bp | 0.813 | 3.09 | 0.691 |
| fwd5 | RSI=NEU | 25 | 4 | −121.10bp | 0.400 | −1.63 | 0.744 |

Read: at the horizons with 8 nights, oversold names do nothing separable (t 0.07 overnight, 0.55 next session). The fwd5 oversold number (+521bp, hit 0.81) is the sweep's largest lead and it rests on 4 nights; q 0.69 says the family cannot distinguish it from the best of thousands of nulls. STACK and VOLR singles are the same shape: fwd1 STACK=DOWN +142.06bp at t 0.72; VOLR=HEAVY +119.68bp at t 0.84; overnight, nothing exceeds |t| 1.1.

Strongest non-separating cells (LEADS, not findings):

- RSI=OS × MACD=BEAR−, fwd5: n=31, 4 nights, +527.49bp, t 3.17, q 0.715.
- RSI=OS × RS10=WEAK, fwd5: n=30, +532.65bp, t 3.01, q 0.715.
- VOLR=HEAVY, fwd5: n=70, 4 nights, +268.49bp, t 3.39, q 0.691.
- MACD=BULL+ × RS10=STRONG, fwd5: n=51, +146.52bp, t 3.36, q 0.691.
- RSI=HIGH × POS10=MID, fwd5: n=34, 3 nights, +144.04bp, t 10.01, q 0.715. Printed as the poster child for the nights floor: a t of 10 on 3 nights is a statement about one tape, not about a variable.
- DAY=UP × POS10=MID, fwd1: n=40, 7 nights, +42.88bp, t 3.26, q 0.995.
- VOLR=NORM × DAY=FLAT, overnight: n=35, 6 nights, +53.40bp, t 3.04, q 0.9998.

The pattern across leads is consistent: everything interesting sits at fwd5 on 3 to 4 nights, or carries a q indistinguishable from 1. Nothing at the overnight horizon, the horizon of the estate's one proven phenomenon (the Focus-names overnight edge, which lives in auction prints and a 2,229-session history this 8-night panel cannot see), separates at all.

## 5. FORECAST CORPUS RESULTS

311 resolved calls parsed and joined to their originating entries (slot, type, stated confidence). 128 cells (singles, pairs, triples over slot × type × confidence). Separators: zero at BH q ≤ 0.10. Singles:

| Cell | n | Hit rate | Excess vs base 0.746 | z | q |
|---|---|---|---|---|---|
| slot=midday | 61 | 0.902 | +15.6pp | 2.79 | 0.188 |
| slot=morning_sweep | 62 | 0.823 | +7.7pp | 1.39 | 0.527 |
| slot=open_pass | 57 | 0.772 | +2.6pp | 0.45 | 0.815 |
| slot=pre_open | 43 | 0.628 | −11.8pp | −1.78 | 0.387 |
| slot=pre_close | 43 | 0.605 | −14.1pp | −2.13 | 0.276 |
| slot=night_study | 38 | 0.579 | −16.7pp | −2.37 | 0.199 |
| conf=high (name calls) | 41 | 0.878 | +13.2pp | 1.94 | 0.322 |
| conf=medium | 129 | 0.775 | +2.9pp | 0.76 | 0.698 |
| conf=low | 93 | 0.688 | −5.8pp | −1.28 | 0.564 |
| type=index | 41 | 0.634 | −11.2pp | −1.65 | 0.415 |
| type=sector | 42 | 0.714 | −3.2pp | −0.47 | 0.815 |
| type=name | 228 | 0.772 | +2.6pp | 0.90 | 0.696 |

The midday slot is the corpus's strongest object (90.2% on n=61) and it still does not separate after BH over 128 cells (q 0.188), with a named confound: the same forecast lines are re-graded across slots as the day revises them, so slot cells are correlated by construction, and midday is where revised calls land. The slot gradient (night study and pre-close worst, midday best) matches the log's own narrative that unrevised level calls were the week's failure mode; the sweep confirms the direction and refuses the promotion. Confidence orders correctly (high 0.878 > medium 0.775 > low 0.688) without separating. Index calls at medium confidence are the weakest parsed cell (0.471, n=17, z −2.61, q 0.199), and the medium-confidence parsed calls are mostly index calls, so the two cells are the same calls read twice; the confound is printed, not hidden.

## 6. FORECAST TWIN, RESOLVED SWEEP-SIDE

All 37 twin poses resolved from daily closes (the book's own record still stands pending; these resolutions grade the twin for this sweep only and do not amend FORECAST-TWIN-RECORDS.md).

- Twin pooled: n=37, event rate 0.730, mean stated p 0.696, **Brier 0.2165 against a climatology Brier of 0.1972: skill −0.098**. The twin's probabilities are worse than always answering the base rate.
- Calibration by bucket: p<0.6 (n=13) events 0.692 against mean p 0.445 (badly underconfident); p 0.6-0.8 (n=10) events 0.500 against mean p 0.677 (overconfident); p 0.8-0.95 (n=5, LOW-N) events 1.000; p≥0.95 (n=9, LOW-N) events 0.889 against mean p 0.980.
- Midna's joined directional calls on the same 37 events: hit 0.811 pooled; conf=medium 0.857 (n=21); conf=low 0.714 (n=7, LOW-N); conf=high 1.000 (n=5, LOW-N).
- Agreement split: twin and Midna agree on 29 events, Midna hit 0.828; disagree on 8, Midna hit 0.750 (LOW-N).

On this sample the human-side forecaster beats the typed twin directionally, and the twin's probability scale is miscalibrated in both tails' directions. n=37 grades none of this past lead status either; the twin's own falsifier clock (300 poses) stands.

## 7. BLOCK M: BOOK, CONTROL LINE, NAMED UNGRADABLES

Nine rows, printed in full because the block is small:

- Book resolved trades pooled: n=4, all losses, −$2,460.13. LOW-N; no cell of expression, sizing, or gating is gradable on it.
- Anti-Midna founding measurement (A29): GRADED, n=58, selection excess −3.33bp versus the anti control (Section 2).
- Anti-Midna forward cohort: UNGRADABLE-YET; frozen at the 2026-11-13 close (29 names), reads overnight Mon 2026-11-16 and at 5 sessions Fri 2026-11-20 inside the night study control-line block, which is wired into the night study cron body.
- Ghost Book: UNGRADABLE-YET, 21 priced, 0 resolved; wiring is the Lane 8 resolver, unbuilt.
- Pattern ledger: UNGRADABLE-YET, 0 of 70 continuation checks resolved; wiring is a pattern panel resolver at 5 and 10 session horizons.
- Section 11 self-audit census: UNGRADABLE-YET, resolutions file empty; wiring is resolve_selfaudit.py plus the four-week census.
- Ledger vs. Surface: UNGRADABLE-YET here; 9,491 sealed rows grade Thu 2026-11-19 with its Lens page the same day.
- Desk sleeve outcomes × gestalt states: UNGRADABLE-YET per Lane 3 (intent records carried no symbol, side, or price); the intent-log cure landed Sun 2026-11-15 (desk commit 87a3956), so accrual starts Mon 2026-11-16.
- Forecast Twin book record: UNGRADABLE-YET in the book; Block T above is sweep-side only.

## 8. DECISIONS API (typed seats; flags and generation only, never selection)

Three governed-harness requests, bank `gestalt-bruteforce-sweep` v1, model gpt-6-luna. **Spend: 3 requests, 123 questions, 25,804 input tokens, $0.0027.** Run records in `GESTALT-SWEEP-SEAT-RUNS.jsonl`.

- **Plausibility flags (24 questions).** The seat scored the 24 strongest panel cells (by |nightly t|, n ≥ 30) for the probability that each separation is real rather than multiple-comparison noise. Every score landed between **0.01 and 0.04**. The seat's skepticism agrees with the deflated statistics; recorded as a disagreement-flag check that produced no disagreement.
- **Seat-twin forecasts (90 questions).** 90 panel observations, symbols and dates withheld, state vectors only; predicate: next-session return exceeds SPY's. Seat Brier **0.2516** versus climatology **0.2421** (skill −0.039); directional hit 0.511 against a 0.589 base rate of positive excess. Given exactly the states the gestalt reads, the seat has no next-session directional edge either. Its mean probability rises with the RSI bucket (OS 0.419, LOW 0.447, NEU 0.503, HIGH 0.569, OB 0.569): a momentum-continuation lean the panel does not support at 8 nights (RSI=OB fwd1 t 1.11, q 0.983). Disagreement preserved, not resolved.
- **Discretization defense (9 choice questions).** The seat defended the sweep's record-based buckets for VOLR, DAY, and STACK, and chose COARSER buckets for RSI, MACD, RS10, RNG10, ATRPCT, and POS10. Flag for the next sweep's design only; this sweep's buckets stand as run, since changing them mid-sweep would rewrite the denominator after the fact.

## 9. GRADABILITY MAP AND ACCRUAL WIRING

The binding constraint everywhere is independent nights (or grading days), not observations. Nights-needed below assumes the current effect and dispersion persist (t grows with the square root of nights; stated as an approximation, and BH over families of thousands still applies on top).

- **Panel fwd5 leads (RSI=OS and its pairs, VOLR=HEAVY, STACK=DOWN).** 4 eligible nights today; roughly 5 to 6 eligible nights reach t 3.5 at current dispersion, but honest separation needs the BH family beaten too, which argues for a re-run at about **20 study nights** (fwd5 pool near 17 eligible nights, roughly three trading weeks). Wiring: already live. Nightly metric pulls persist in the goals hidden_files tree; this sweep re-runs mechanically on the accumulated panel. No new wiring needed, only time.
- **Panel overnight and fwd1.** 8 nights today and the largest |t| is 1.11; at current dispersions these horizons need an order of magnitude more nights before any single can separate. Same wiring; re-run with the fwd5 re-run.
- **Forecast slot and confidence cells.** Midday needs about 11 grading days at current dispersion for t 3.5 (7 today); the corpus accrues daily through the existing forecast routine. Re-grade at 20 grading days with the slot-correlation confound handled by grading each forecast line once, at its final revision, alongside the as-written grade.
- **Dealer family (A12 gamma flip, A13 static GEX flip, A14 pin proximity).** UNGRADABLE-YET: session-only states, never persisted per outcome. Wiring needed: a per-name-night persistence row written by the open pass and night study (flip level, distance, pin distance) joined to the panel. The one examined pair in this family (A12×A13) still carries its unresolved 2026-11-12 disagreement (SPY 761.69 versus 759.69).
- **Lens, Echo, engine, and Tensor verdict axes (A17-A20 and their pairs/triples).** UNGRADABLE-YET: verdicts are read in prose, not persisted per name-night. Wiring needed: the night study writes each lens's verdict per name per night to a machine file; the panel then joins mechanically.
- **Event and IV axes (A21-A24).** The chain archive begins 2026-11-13; event-window and IV-percentile states become panel-joinable after roughly a month of archive accrual, with the first earnings cycle inside it.
- **Wave fires (A31) and fleet states (A32, A33).** Wave fires begin Mon 2026-11-16 under the sleeve signal wave program. Breadth and sector tide are computable from existing bars but were never persisted; wiring is one nightly row each.
- **Book-side objects.** Ghost Book, pattern ledger, and self-audit all wait on resolvers, not data: Lane 8 resolver (Ghost Book, counterfactual twins), the pattern panel resolver, and resolve_selfaudit.py. Until those run, every combination touching expression outcomes stays UNGRADABLE-YET regardless of accrual.
- **Desk sleeve outcomes.** Accrual starts Mon 2026-11-16 on cured intent records (symbol, side, ref_price at emission). First gradable desk-side cells after roughly 14 sessions of census, the same window the Placebo Fleet uses for its first percentile print.

## 10. WHAT THIS SWEEP DID NOT DO

It did not kill anything. Zero separators at honest N is a statement about the estate's resolved sample, not about the variables; every lead above keeps its accrual path and its forward read. It did not amend any book record (twin resolutions are sweep-side). It did not re-derive Lane 6's register; Block A accounts for Lane 6's full 6,579-combination space against this sweep's corpora and names the 6,522 that remain ungradable, with the reason carried per axis in the register rows. Seat outputs were used as flags and generation only; no cell was promoted, demoted, or selected by a seat.

STATUS: PARTIAL. The sweep executed in full and the register is complete: 24,517 combinations enumerated and accounted, every gradable combination graded against resolved outcomes, separators ZERO at every horizon, order, and corpus under the pre-registered rule. The bounded portion proven is the grading itself and the gradability map; the unproven remainder is named: 6,522 axis combinations UNGRADABLE-YET pending the persistence and resolver wiring in Section 9, and every lead awaits the accrual counts printed beside it.

EVIDENCE POINTERS: sweep register `~/workspace/research_notes/alpha-hunt-chaos-20261115/GESTALT-SWEEP-REGISTER.jsonl` (24,517 rows, counted back from the written file); seat run records `~/workspace/research_notes/alpha-hunt-chaos-20261115/GESTALT-SWEEP-SEAT-RUNS.jsonl` (3 requests, 123 questions, 25,804 input tokens, $0.0027); foundation map `~/workspace/research_notes/alpha-hunt-chaos-20261115/LANE6-GESTALT-FULL.md`; panel sources in `~/workspace/goals/midna-trading-her-own-simulated-book/hidden_files/` (night-study pulls 2026-11-03 to 2026-11-12; outcomes weekend-2026-11-14/daily_long.json); forecast corpus `~/workspace/midna-book/FORECAST-LOG.md` (tallies 319, parsed 311, misses reconciled 79 of 79); twin source `~/workspace/midna-book/FORECAST-TWIN-RECORDS.md` (37 poses, all resolved sweep-side).
