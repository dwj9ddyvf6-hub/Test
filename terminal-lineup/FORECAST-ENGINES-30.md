# Forecast Engines 30: the top 30 predictive engines designed from the REA corpus

Date: 2026-10-28. Phase: converge. Sources actually read for this phase:
`REA-ANALYSIS.md`, `REA-ANALYSIS-SUMMARY.md`, `analysis/01-CORPUS-MAP.md`,
`analysis/02-FIDELITY-AND-EVIDENCE.md`, `analysis/03-CONFLICTS-AND-NOVELTY.md`
(conflicts C1-C18, novelty N1-N12), `THE-70-TOOLS.md`,
`forecast30-inventory.md`, and all six candidate files
(`forecast30-candidates-lens-crossfamily.md`,
`forecast30-candidates-lens-distributional.md`,
`forecast30-candidates-lens-inversion.md`,
`forecast30-candidates-lens-meta.md`,
`forecast30-candidates-lens-selfrelative.md`,
`forecast30-candidates-lens-temporal.md`): 72 candidates in total.
Status: design only. Nothing below is built, and nothing below has a
forward record yet.

## The program's discipline, in plain words

Nothing in the corpus this program draws on has a validated directional
edge. The Board score does not rank returns (C11). The picker replay,
296,093 cases, passed nothing. The textbook pullback lost to random
entries in the same names (C13). The Forecast Factory promoted 1,217
cells and its own pre-registered rerun kept 63 at grade A (C12). Any
engine that forgets that record is marketing, not forecasting.

So every engine below obeys the same law, with no exceptions:

1. **A forecast is a number that can be wrong.** Each engine states a
   quantity, a horizon, and a form (direction, distribution,
   probability, or timing) precise enough to grade without judgement.
2. **Ledger before display, always (N1).** Every forecast is written to
   the append-only ledger before its horizon opens. A figure that
   cannot be recomputed from the ledger does not ship. No forecast is
   edited, backdated, or quietly dropped.
3. **Graded forward, at fixed horizons, losers included.** Grades run
   at the horizons stated in advance. Losers, abstentions where the
   engine chose to publish, expired and unresolved cases stay in the
   denominator. No horizon shopping, no best-excursion grading.
4. **Proving state until its own record matures.** Every engine ships
   labelled proving. It earns stronger language only from its own
   ledgered forward record, never from a backtest, a vendor claim, or
   a neighbouring engine's record. The corpus's own method warning
   stands over all of them: skill-less best-of selection can show
   Sharpe about 3.1 at one year, and the minimum track record for
   Sharpe 1.0 is about 2.7 years, so no young record proves skill
   quickly.
5. **Agreement is discounted by evidence family (N3).** Signals that
   share an underlying primitive count once. Price, options prints,
   modelled chain inventory, filings and positioning, events and
   calendar, and distributional or volatility constructions are the
   families. Ten price tools agreeing is one confirmation, not ten.
6. **Only real data routes.** Each engine names what it reads, what
   exists today, and what must accrue from machinery already running.
   No fantasy feeds. Where a route is thin, stopped, or partial, the
   engine says so on its own card and its claim is narrowed to match.
7. **A kill criterion is part of the design.** Each engine states in
   advance the result that retires it to the Graveyard (tool 50) with
   its record intact. An engine that cannot fail cannot be trusted
   when it claims to succeed.

Ranking used for the convergence and the build order: falsifiability
sharpness first, then mechanism plausibility against the corpus's
kills and survivors, then data in hand today, then novelty against
the whole corpus and the 70 built tools, then grading cost. Cheap,
sharp, daily-graded engines that ride the corpus's strongest evidence
(volatility and distribution calibration, the grade A stress reversal,
the grade B own-norm survivor) build first. Slow, episodic, and
event-bound engines build later, however novel they are, because
their verdicts arrive slowly.

## Shared machinery: build once, before Engine 1

No engine starts until these three exist, because every engine
depends on all three:

- **The forecast ledger.** One append-only ledger in the N1 form:
  engine id, forecast issued timestamp, horizon open and close,
  the exact forecast quantity and value, the data snapshot or lineage
  hash it was computed from (N4 five-clock envelope), and its family
  labels. Identical republications count once. Grading rows append to
  the same ledger; nothing is ever rewritten.
- **The grading runner.** One runner that, each session, finds every
  matured forecast, grades it by the engine's pre-registered rule
  (coverage, pinball or CRPS for distributions; Brier or log loss for
  probabilities; median and mean error for points; rank scores where
  stated), writes the grade back to the ledger, and recomputes every
  published figure from the ledger only. One wall-grading definition,
  imported, never forked (N8).
- **The family registry.** One registry assigning every input of every
  engine to exactly one evidence family (N3), with the C14 caveat
  carried openly: abstentions or no-data states caused by the three
  named fail-open Femto functions are tagged as defect states, not
  market states, until those functions are cured at the source.
  The registry also records each engine's kill criterion and proving
  threshold, so retirement is mechanical, not editorial.

After that machinery, the build order is the order of the 30 below.

---

## Engine 1. Corrected Band Engine

- **One job:** Publish an expected-move band whose stated percentage is a claim it is graded against, not a vendor label.
- **THE FORECAST:** For SPY and QQQ, daily pre-open: 50, 68, 81 and 95 percent close-to-close move bands at 1, 5 and 21 sessions, as explicit prices. Distribution form. Pre-committed claim: the 68 percent band covers 63 to 73 percent at 5 sessions in its first 120 live forecasts.
- **Mechanism:** HAR realised-vol forecast times sqrt(h/252) times k (k 0.87, 0.88, 0.91 by horizon, the AD-56 out-of-sample calibration) as the spine. The VIX divided by 15.87 construction enters only as a regime input scaled by its measured 0.71 to 0.75 factor, never labelled 1 sigma (AD-55). VIX backwardation (V3) widens only the 95 percent band, by a fixed pre-registered factor.
- **Corpus lineage:** AD-55 and AD-56 calibration studies; V1 (HAR, grade A); V3; the Azrael 15.87 construction as a vendor-verbatim input (N11, not claimed as ours); ascends tool 7 Expected Move Map, which publishes the vendor construction as a reading and grades nothing.
- **Why new:** No corpus part issues a corrected multi-quantile band set, demotes the vendor band to an input, and stakes its product on forward coverage.
- **Data route:** SPY and QQQ daily plus VIX, VXN, VIX9D, HV30, HAR and GARCH series 2010 to 2026-10, all on record; daily VIX readings accrue in the shipped terminal record. Exists today.
- **Grading protocol:** Ledger pre-open daily. Coverage per band per horizon, band width against the vendor band at equal coverage, and pinball loss, over rolling 60 and at 120 forecasts. Kill: the 68 percent band's coverage at any horizon sits outside its binomial interval after 120 graded forecasts, or a plain HAR band beats it on pinball at equal width.
- **Honest prior:** Strongest distributional prior in the set. HAR is grade A and the corrected band held 68 percent out of sample in the study. The prior is good for calibration, and says nothing about direction, which this engine never claims.

## Engine 2. Touch Surface

- **One job:** Forecast whether price will touch a level, with a probability that is calibrated, replacing the vendor touch model the corpus killed.
- **THE FORECAST:** For SPY and QQQ daily pre-open, and per name where the data route supports it: probability of touching plus and minus 0.5, 1.0 and 1.5 expected moves (EM from Engine 1) within 1, 5 and 21 sessions, plus probability of touching either side. Probability form, per distance and horizon cell.
- **Mechanism:** Fused from distributional candidate D3 and inversion candidate 7 (Touch Lie Detector), which were the same engine from two lenses. Empirical first-passage frequencies from daily high and low bars, conditioned on distance in EM units and vol regime, blended with a driftless barrier estimate shrunk hard toward the empirical rate. The vendor reflection formula 2N(.) enters only as a published benchmark carrying its measured 13 to 30 point overstatement (AD-57) as a fixed haircut, never quoted raw. GEX sign enters as a damping or amplification conditioner.
- **Corpus lineage:** AD-57 (reflection model killed as calibrated: 63.5 percent claimed against 32 to 33 percent realised at plus or minus 1 EM on VIX vol); AD-55 and AD-56; Studies S1 and S2 path fixtures; Map GEX sign; Morgue strip.p_touch as the named dead construction being replaced.
- **Why new:** The corpus contains the kill and no replacement. No tool among the 70 forecasts touch probability at all; tool 6 Payoff Sketch is expiration payoff only.
- **Data route:** Daily OHLC in the DEEP panel (touch is decidable from high and low against the barrier) and the 2010 to 2026 index panel; live barriers from Engine 1's ledgered bands. Intraday grading, if used, runs on the SIP route the Morgue already fetches for gap and ORB work, not on any new feed.
- **Grading protocol:** Ledger pre-open. Brier score and reliability bins per cell at fixed horizons, touched and untouched both counted, scored beside the reflection model's Brier on the same days. Kill: after 100 sessions per index cell, it does not beat the dead model's Brier score, or its reliability error exceeds 10 points.
- **Honest prior:** Good. It starts life with a beaten benchmark already measured, the sharpest falsifier in the candidate pool. The risk is regime change in first-passage behaviour, which the reliability bins exist to expose.

## Engine 3. Own-Norm Depth Forecaster

- **One job:** Turn the corpus's lead survivor, pullback depth against the stock's own norm, into a calibrated per-name probability engine.
- **THE FORECAST:** For each uptrend name at each close: probability that its 20-session excess return against SPY is positive, and its predicted median 20-session excess return, as a function of today's pullback depth percentile against that name's own trailing 750-session depth distribution. Direction and distribution form. Sharp claim: the deepest own quintile beats the shallowest own quintile by at least 0.8 points of median excess at 20 sessions, matching the 2023+ cross-era spread on record.
- **Mechanism:** Depth is the distance from the name's own 63-session high in units of its own median true range, converted to an own-history percentile, leave-today-out. The percentile maps to the forecast through a monotone curve fitted only on DEEP 2016-22 and frozen. Fear-day interaction is a published sub-forecast, not a separate confirmation: same family.
- **Corpus lineage:** xcheck F3 and N10 (IC plus 0.026 and plus 0.031, t 4.3 and 4.3, at 20 days across two eras; 60-day 2023+ IC plus 0.062, t 9.8); the killed fixed-band picker families A0 to A2 that this replaces; N1; E3 horizon discipline. Ascends tools 17 Pullback Norm (a descriptive pane whose local study never ran), 43 and 49, which publish cohorts and issue no calibrated per-name probability.
- **Why new:** No vendor in the corpus normalises pullback depth by the name's own distribution; that normalisation is exactly the difference between the killed textbook version and the surviving one.
- **Data route:** DEEP daily bars 2016-2026, 6,385 names including delisted, for fitting; shipped daily history, 1,833 names by 399 sessions, for the live feed. Exists today.
- **Grading protocol:** Ledger before next open; grade at exactly 20 sessions, secondary 60. Brier on the probability, median error on the point forecast, quintile spread against the 0.8 point claim, and the picker standard beside every grade: random entries in the same names. Kill: after 200 matured forecasts, the quintile spread's confidence interval includes zero.
- **Honest prior:** The best directional prior in the whole set, and it is still only grade B, on one dataset family, explicitly unproven forward. Expect a small effect if any, not a strong one.

## Engine 4. Stress-Reversal Staging

- **One job:** Decompose the corpus's only grade A directional effect into an ordered, staged script that can fail early and visibly.
- **THE FORECAST:** Only in the deepest SPY-drawdown tercile (T2's exact condition), at day 0 for each name in yesterday's loser cohort: probability the reversal begins by plus 1 session, probability the peer-gap component closes by plus 3, and median cumulative return at plus 1, plus 3 and plus 5 sessions, as three separately graded stage forecasts per name. Timing and distribution form.
- **Mechanism:** Temporal candidate T12, kept whole. The original T2 study graded one blended effect; this engine stages it, so a user can see which stage failing kills the script. Cohort definition supported by F5 and F7 RESET laggard relative strength.
- **Corpus lineage:** EV T2 (grade A: last-day return IC minus 0.058 and minus 0.028 in stress; 393 stress-reversal confirmations against a null of 17; peer-gap reversal IC plus 0.017, t 4.4); F5 and F7 (grade B); the fear-day machinery of tools 16 and 43. Ascends tool 49 Survivors Wire, which republishes survivors as a feed and stages nothing.
- **Why new:** No corpus part decomposes an effect into a graded stage sequence with early-kill staging.
- **Data route:** Daily bars plus the drawdown tercile computed from SPY history 2010 to 2026, on record today. Forward instances are episodic by construction.
- **Grading protocol:** Stage-wise at plus 1, plus 3, plus 5; every day-0 cohort name in every stage's denominator; episode count printed beside every rate (the T6 and T7 small-episode trap: grade C precedents rested on 5 to 13 episodes). Kill: stage 1 fails its pre-registered bar in the first 3 forward episodes, and the script retires as a whole.
- **Honest prior:** Best evidence grade in the corpus, with two named caveats carried on the card: the discovery ran on a survivors roster (D3 caveat), and forward accrual is event-paced, so the proving state may span few episodes and a long calendar.

## Engine 5. Honest POP Engine

- **One job:** Attach a calibrated probability of finishing above each strike to the chain, and grade the whole surface at expiry.
- **THE FORECAST:** For SPY and QQQ weekly expiries, at each day's close: for every listed strike within plus or minus 2 EM, the probability the final close finishes above that strike at expiry. Probability form, per strike, each day's surface ledgered separately.
- **Mechanism:** HV30 driftless N(d2), the best-calibrated POP construction in the corpus (AD-58: 82.4 predicted against 83.0 realised at 1 session), blended with the index's own empirical finish distribution, with the IV-based POP's measured 12 to 15 point understatement applied as a correction when IV is the input.
- **Corpus lineage:** AD-58 (grade B, calibration only); the Option Alpha teardown, the corpus's most test-backed vendor teardown at 20.2 percent backed; payoff.py deterministic expiration math; tool 25 Chain Explorer snapshots. Ascends tool 6 (payoff with no probability attached) and tool 28 Premium Meter (move size, not finish probability).
- **Why new:** Vendors print POP; none in the index grades theirs. No corpus part ledgers a per-strike probability surface and grades it at expiry.
- **Data route:** Chain snapshots on record via the chain archive lane, plus the HV30 series. Index only: per-name chain depth is a named accrual gap, so the per-name extension is excluded from this engine's claim until that depth exists.
- **Grading protocol:** Ledger at each close; graded at expiry close, every ledgered strike in the denominator including strikes expiring worthless. Brier and log loss per strike and a reliability curve across strikes. Kill: after 26 weekly expiries, its Brier is no better than the uncorrected IV POP's.
- **Honest prior:** Good for calibration, by AD-58's own numbers. Its caveat rides on the card in the study's own words: a win rate is not an edge, and this engine says nothing about loss size or whether any trade pays.

## Engine 6. Exceedance Forecaster

- **One job:** Forecast tail size, never direction: how likely a move bigger than the priced move is.
- **THE FORECAST:** Daily pre-open, for SPY, QQQ, IWM and per name in the shipped universe: probability the absolute 5-session return exceeds 1 EM, probability it exceeds 2 EM, and probability the 21-session maximum drawdown exceeds 1.5 EM. Probability form. Pre-committed claim: its 2 EM exceedance probabilities beat the unconditional base rate's Brier score by a stated margin, or it reports itself failed.
- **Mechanism:** Empirical exceedance rates conditioned on the corpus's downside-only precursors (overnight gap size with its 1.6 to 1.9 times tail multiplier, down-day trade-count surge, weekly divergence at the low, AD-30) plus vol state (HAR level, backwardation, breadth-washout flags). Precursors enter as distribution shifters only; any directional reading is suppressed by construction.
- **Corpus lineage:** AD-30 (grade C, downside precursors forecast tail size, for stops and puts, not direction); V3; V4 (shapes forecast volatility, not direction: 172 of 384 vol cells against 2 of 384 direction cells); T7 extremes; A9's trade-count surge reused as a size input. Ascends tools 31 Breadth Meter and 33 Regime Dial, which describe state and forecast nothing.
- **Why new:** The corpus grades these precursors as study rows and vetoes. No engine converts them into a ledgered exceedance probability, and no vendor in the index sells tail-size-without-direction as the headline.
- **Data route:** DEEP daily bars and trade counts, the 2010 to 2026 index panel, shipped daily history live. All on record.
- **Grading protocol:** Ledger pre-open; Brier, log loss and reliability at plus 5 and plus 21, exceedances and non-exceedances both counted. Precursors are price and breadth family: one family in any consensus use. Kill: after 120 index forecasts, no Brier improvement over the base rate.
- **Honest prior:** Mixed. The target class (size) is the corpus's validated class, but the precursor evidence itself is grade C. That is why the claim is a Brier margin against the base rate, not an accuracy boast.

## Engine 7. Realised-Vol Term Shape Forecaster

- **One job:** Forecast the shape of future volatility across horizons: which horizon's vol is underpriced.
- **THE FORECAST:** Weekly, for SPY and QQQ: the 25th, 50th and 75th percentiles of realised vol over the next 5, 21 and 63 sessions, plus the probability that 21-session realised vol exceeds 5-session realised vol (the term-shape call). Distribution and probability form.
- **Mechanism:** HAR components (daily, weekly, monthly realised vol) projected per horizon. The implied level enters corrected by the measured realised-to-implied ratio (0.87 liquid, V2) as a level prior, so implied vol's known high bias is a calibrated input.
- **Corpus lineage:** V1 (HAR, grade A, the corpus's strongest vol result: long-scale R-squared gain plus 0.127 and plus 0.116, t 19 and 20); V2; V4. Ascends tools 26 IV Weather and 28 Premium Meter, which are readings, not ledgered term-structure forecasts.
- **Why new:** Term shape is addressed nowhere in the 70 tools or the indexed vendors. Everyone quotes a vol level; nobody forecasts and grades the curve.
- **Data route:** Index leg full: 2010 to 2026 SPY and QQQ plus vol series on record. The per-name leg from the candidate file is cut from the claim: the IV ledger stopped 2026-10-14 with 60 names at at most 12 readings each, so per-name forecasts ship only as history-building with a stale-ledger flag until 20 fresh readings per name exist.
- **Grading protocol:** Ledger weekly pre-open; quantile coverage per horizon and Brier on the shape call at plus 5, plus 21, plus 63, all cohorts counted. One vol family. Kill: after 52 weekly cohorts, quantile coverage misses its stated rates by more than 10 points at two or more horizons.
- **Honest prior:** Strongest single-study prior in the set (the only grade A vol result), for the index leg. The per-name prior is unknown and is not claimed.

## Engine 8. Wall Lifetime and Break Forecaster

- **One job:** Forecast a wall's life and its failure, before the fact, instead of grading respect after it.
- **THE FORECAST:** For each Morning Map card (SPY, QQQ, IWM, daily): probability the call wall is touched and closes through within 1, 3, 5 and 10 sessions, the same for the put wall, probability the flip is crossed and closed beyond in the same windows, a median lifetime per level, and, for the same-session window, the predicted side of first failure (up, down, neither). Probability and timing form.
- **Mechanism:** Fused from distributional candidate D4 (Wall Lifetime Clock) and inversion candidate 2 (Wall-Break Forecaster), which forecast the same levels on different horizons. Kaplan-Meier style empirical hazard from the accruing map-card record, seeded with a distance and vol prior (hazard rising as distance in EM units shrinks), conditioned on net GEX sign: in negative GEX, dealer hedging amplifies a touch into a through move; in positive GEX it damps it. Features include overnight gap share of the distance, days to the dominant expiry, and the wall strike's concentration against neighbouring strikes.
- **Corpus lineage:** Morning Map GEX, walls and flip (SpotGamma published construction); the N8 wall-validation harness, grading definitions imported from scorecards.py, never forked; tool 14 Wall Check's young record (9 cards, 6 graded tests: flip respected 6 of 6, put wall held 6 of 6, IWM call wall reached and broke in both its tests); AD-55 corrected EM units.
- **Why new:** Wall Check grades respect after the fact, as rates. Nothing in the corpus forecasts a level's lifetime or break probability before the fact. SpotGamma sells the wall as a level to respect; this engine sells the calibrated probability that respect fails, and when.
- **Data route:** Map cards accrue daily from machinery already running (publish_feed and daily_cycle); chain snapshots accrue via the chain lane. Partial today, stated plainly: only 9 cards and 6 graded tests exist, so the prior dominates for months and the engine ships as an accrual counter with its prior labelled, like P_NN's 126-session floor. Grading runs through wall_study.py's own fetch path, never through studies_card.main, whose wall input is still an empty bars dict on main (C2).
- **Grading protocol:** Ledger at card publication; survival calibration and median-lifetime error at 1, 3, 5 and 10 sessions, still-untouched levels carried as censored, never dropped; same-session break calls scored by Brier. One modelled-inventory family, with the price and vol family beneath it counted once (shared with Engine 2). Kill: after 60 cards per index, its 5-session touch calibration error exceeds 10 points or its break Brier is no better than the unconditional break rate.
- **Honest prior:** Poor to unknown, honestly. Six graded tests prove only that the grading loop closes in public. The IWM call-wall breaks (2 of 2 reached) motivate the asymmetry and prove nothing at that count.

## Engine 9. Intake-Bias Reversal

- **One job:** Forecast the fade that follows when a vendor flow score's bullishness is manufactured by its own intake.
- **THE FORECAST:** Each session, for the cohort of names with the largest gap between the buys-only Algo Score and the all-prints Algo Score, where FINRA short volume is also in its top tercile: the cohort's mean 5-session excess return against SPY will be at least 1.0 point negative, with a predicted cohort median stated as a number. Direction form, cohort level, avoid side only. Fused companion claim, from inversion candidate 3 (Bias Spread): the top-gap quintile's 5-session median excess is negative, graded on the same ledger.
- **Mechanism:** Fused from cross-family candidate XF-3 and inversion candidate 3, the same gap read by two lenses. FlowAlgo's buys-only intake hides the prints that would lower its score. When the manufactured score and the honest score diverge most, and shorts are simultaneously active, the visible bullish flow is distribution dressed as accumulation. The corpus's avoid evidence is the prior: A2 loud attention days fade, A9 trade-count surges are a strong avoid, A11 heavily shorted names lag in healthy markets (grade B).
- **Corpus lineage:** N2 dual-population Algo Score (genuinely novel; tallies verbatim, the sum the extraction's inference, the vendor sub-1 floor bug explicitly not copied, C16); A2, A9, A11; tool 4 Flow Tape, which displays both scores and forecasts nothing from their difference.
- **Why new:** No vendor reports both populations at all. Crossing the bias gap with short volume turns a measurement of vendor dishonesty into a forecast.
- **Data route:** Tape cards accruing daily; FINRA short-volume history 2018-08 to 2026-10 in the reset studies, plus the exchange republication route. Named caveat: tool 22 Short Volume Ledger itself has stored 0 days, so this engine reads the study and republication route, not the empty ledger, and says so on its card. Side labels inherit the declared latest-quote limitation (C16).
- **Grading protocol:** Cohort ledgered at the close completing the prints; graded at exactly plus 5 sessions, mean and median both published, all cohort names in the denominator including halted names at last price. Baselines: the bias-only cohort and the short-volume-only cohort. One options-prints family plus one positioning family. Kill: after 80 fires, the interaction mean is zero or positive, or no better than short volume alone. This is a cohort fade forecast, never a short book: A16 killed shorting picked names after borrow costs.
- **Honest prior:** Moderate. Each parent (the avoid stack, short volume in context) carries grade B evidence; the interaction itself is untested, which is the point of ledgering it.

## Engine 10. Insider-Flow Divergence

- **One job:** Price independent disagreement between the two best-informed families, insiders and options flow, as the signal.
- **THE FORECAST:** Names where insider summaries show heavy net selling (sells at least 10 times buys by count across the record) while options Heat is simultaneously in its top bucket will underperform SPY by a mean of at least 1.5 points over 21 sessions; the reverse divergence (an insider buy present, Heat absent or cold) will outperform by at least 1.0 point. Both arms are forecasts; agreement cases are ledgered as the control cohort. Direction form.
- **Mechanism:** When insiders and flow disagree, one is wrong in a specific way: insiders sell into manufactured heat (distribution), or accumulate quietly before flow notices (sponsorship). This is N3 read backwards: instead of discounting correlated agreement, it prices independent disagreement.
- **Corpus lineage:** Insider summaries on record (18 buys against 326 sells across the record: that asymmetry is the base rate the forecast must beat), tool 21 Insider Wire; InsiderFinance Heat Score, 8 live components, fixture-proven in Morgue tape.py; N3.
- **Why new:** Every vendor product in the corpus grades only its own family's agreement with itself. No teardown contains a divergence engine, and the corpus never grades a disagreement.
- **Data route:** Insider summaries on record 2026-10-26 for 43 of 50 names (coverage gap named); tape cards accruing. Partial, stated: insider summaries carry counts and values, not trader identity or dates, so divergence is measured at summary grain; per-name tape coverage is index-heavy today, so single-name fires accrue slowly, index constituents first.
- **Grading protocol:** Ledger at fire; 21-session excess per arm against the agreement control; all fires counted. Kill: after 60 fires per arm, either arm's mean sign is wrong.
- **Honest prior:** Weak to moderate. Insider buying is explicitly untested in the registry, and Heat has never been graded as a forecaster. The mechanism is plausible and the base rates are known, but neither parent carries a forward grade. Ranked on novelty and falsifiability, not on prior strength.

## Engine 11. Gamma-Pressure Earnings Trap

- **One job:** Forecast earnings-day move size when dealer gamma will amplify the shock, and never forecast its direction.
- **THE FORECAST:** For index constituents reporting earnings within 5 sessions while index net GEX is negative: the name's absolute earnings-day move will exceed its priced expected move in at least 55 percent of cases, and the median ratio of realised to priced move will be at least 1.10. Horizon: the earnings session. Distribution form.
- **Mechanism:** Negative dealer gamma amplifies hedging flow into any shock; an earnings print is the largest scheduled per-name shock. Neither family alone makes this claim: gamma suites never condition on the earnings calendar, earnings tools never condition on dealer inventory.
- **Corpus lineage:** Morgue map_gex and tools 1 Morning Map and 54 Gamma Ladder (modelled inventory); tool 35 Earnings Calendar with priced expected move (events); AD-55 and AD-56 band calibration as the grading yardstick (distributional).
- **Why new:** No vendor in the corpus crosses chain inventory with the earnings calendar. The interaction, amplifier times scheduled shock, is the forecast.
- **Data route:** Map cards and chain snapshots on record; earnings calendar on record. Index-level GEX exists today; per-name GEX accrues from the chain archive lane already running, and the engine states which level it used on every forecast.
- **Grading protocol:** Ledger pre-report per event; the ratio distribution graded against the same ratio for positive-GEX earnings events, a control arm ledgered at the same time. Kill: after 60 events, the exceedance confidence interval includes 50 percent or the median ratio is below 1.0.
- **Honest prior:** Moderate for size, by the same logic as Engine 6: dealer-hedging amplification is a physical mechanism, and size is the corpus's validated target class. There is no direct study of this interaction in the record; it is a new claim, graded as one.

## Engine 12. Earnings Move Distribution Engine

- **One job:** Forecast the whole distribution of a name's earnings move for the coming report, and grade each season as a season.
- **THE FORECAST:** For every name on the earnings calendar, at the close before its report: the decile distribution of its earnings-day absolute move and of its signed 5-session post-report move, plus the probability the realised earnings-day move exceeds the chain-priced expected move. Distribution and probability form. Season claim: the 80 percent band covers 75 to 85 percent of a season's reports.
- **Mechanism:** The name's own past report-day distribution from DEEP (with the D5 one-session-late earnings-date defect fixed, not inherited) blended with the cross-sectional distribution for its size tier, centred on zero drift, because the record holds no drift edge, and scaled by the priced expected-move ratio for that tier. A12's small-cap earnings-gap fade enters only as a signed-tail conditioner for small caps.
- **Corpus lineage:** Studies S3 earnings distributions; tool 35 priced expected moves; A12 (grade B); tool 13 Earnings Drift Pane (three names' past report days, descriptive) as the ancestor this ascends.
- **Why new:** Neither the calendar nor the drift pane forecasts a per-name move distribution for the coming report, ledgers it, and grades the season.
- **Data route:** Earnings calendar and chain expected moves on record; DEEP report-day history. Exists today.
- **Grading protocol:** Ledger at the pre-report close; per-season coverage, pinball loss and exceedance Brier; every reporting name in the denominator, including halts and no-data expected-move rows marked abstain-at-issue. Price and chain families reported as two. Kill: after two full seasons, the 80 percent band's coverage sits outside 70 to 90 percent, or exceedance Brier is no better than quoting the priced move's implied rate.
- **Honest prior:** Good for the absolute-move distribution (own-history earnings moves are a stable object), poor for the signed leg, which is centred on zero precisely because the corpus offers no drift edge to centre it on.

## Engine 13. Idiosyncratic-or-Liquidity Splitter

- **One job:** Separate declines that persist from declines that reverse, by whether the drop was the name's own news or the market's weather.
- **THE FORECAST:** For each name down at least 2 own-residual-vol units today: if the drop is idiosyncratic (SPY flat or up, the name's residual move dominates), median 20-session excess at most minus 0.5 points (persistence); if the same own-norm drop is liquidity-driven (market-coincident, on a fear day), median 20-session excess at least plus 0.5 points (reversal). Either leg landing on the wrong side of zero falsifies that leg. Direction form, opposite-signed by design.
- **Mechanism:** Self-relative candidate SR-8. It joins F4 (company-specific declines do worse) to T2 (reversal in stress) and resolves their apparent contradiction the way the corpus itself separates them: information-driven declines persist, liquidity-driven declines reverse. The split variable is the name's own residual share, scaled by its own residual-vol history, never a fixed percent threshold. Leave-out centred means wherever an own mean is used (the D2 method law).
- **Corpus lineage:** F4 filed as avoid A15 (grade B); T2 (grade A); new10 N1 innocent bystander as the liquidity leg's cousin; D2.
- **Why new:** The corpus holds both halves as separate findings and never combines them into one conditional, opposite-signed forecaster. No vendor teardown conditions reversal against persistence on the name's own residual decomposition.
- **Data route:** DEEP daily bars plus SPY daily. Exists today.
- **Grading protocol:** Ledger at drop close; each leg graded separately at 20 sessions, legs never netted against each other. Kill: a leg is retired independently if its median confidence interval includes zero after 150 episodes.
- **Honest prior:** The strongest constructed prior among the directional engines, because it is built from the corpus's only grade A directional row and a grade B avoid that agree once conditioned. Still one dataset family behind both parents, and stated as such.

## Engine 14. Own-Volatility Normalisation Clock

- **One job:** Forecast how long a name's volatility spike will take to come home, in that name's own time.
- **THE FORECAST:** When a name's 10-session realised vol exceeds the 90th percentile of its own 3-year vol distribution: the distribution (median and 10 to 90 band) of sessions until its 10-session realised vol returns below its own median. Timing and distribution form. Claims: realised normalisation time falls inside the band 80 percent of the time, plus or minus 5 points, and the median forecast beats the name's own unconditional median normalisation time by at least 20 percent in mean absolute error.
- **Mechanism:** Self-relative candidate SR-4. A per-name first-passage time driven by the name's own vol-of-vol percentile, its spike size in own-norm units, and its own historical decay rate after its own past spikes. V6's snap-back scaling enters as a covariate only (grade C).
- **Corpus lineage:** V1 and V4 (vol from vol's own past, grade A for size, never direction); AD-56's calibration method transferred from SPY bands to per-name decay; V6.
- **Why new:** Every built vol version forecasts a level for the market or a tier. A time-to-normal forecast per name exists in no vendor teardown and none of the 70 (tool 7 gives a price band for an index, not a per-name vol clock).
- **Data route:** DEEP daily bars; shipped daily history live. Exists today.
- **Grading protocol:** Ledger at spike close; grade at realised normalisation, or censor at 63 sessions with censored cases kept in the denominator as band misses when the band's 90th percentile is under 63. Coverage plus MAE against the own-unconditional baseline. One price and vol family. Kill: after 200 matured forecasts, coverage error exceeds 10 points or MAE does not beat the baseline.
- **Honest prior:** Good. It rides the corpus's one grade A family without claiming direction, which is exactly where that family's evidence applies.

## Engine 15. Per-Name Self-Analogue

- **One job:** Forecast a name's next 21 sessions from the times that same name was last in the state it is in now.
- **THE FORECAST:** For each name: the 10th, 50th and 90th percentiles of its own plus-21-session return, taken from the returns that followed the nearest one-sixth of that name's own past states. Distribution form. Calibration claim: realised returns fall inside the published 10 to 90 band 80 percent of the time, plus or minus 5 points.
- **Mechanism:** Self-relative candidate SR-2, ascending N5 and Studies S6 inward. The state vector is four own-norm coordinates (price position, volume, gap, drawdown and range compressed as specified in the candidate, all own-history z-scores using the desk-fixed MAD-to-z constant 1.4826, stamped OURS in S6), matched only within the same ticker's history, minimum 750 own sessions or the engine abstains. The IV coordinate of S6 is dropped: the IV ledger cannot support it, and the engine says so.
- **Corpus lineage:** SqueezeMetrics A106 to A110 published coordinates via Morgue studies.py S6 (N5, recombined); N1; AD-57's lesson enforced as the calibration kill rule. Contrasts: tool 20 State Analogue is market-level and has accrued 0 of its 126 sessions, so it has never rendered; the per-name version has no accrual wait because each name's library is its own completed DEEP history.
- **Why new:** Every analogue in the corpus matches a name against other names or the market against itself. Self-only matching appears in no vendor entry and no built tool.
- **Data route:** DEEP daily bars, own histories to 2016. Exists today.
- **Grading protocol:** Ledger before next open; grade at 21 sessions; coverage pooled and per name; a name whose band coverage misses by more than 15 points over 100 forecasts is suspended publicly, not silently kept. One price family, and never counted as independent of Engines 3 or 16 in any consensus. Kill: pooled coverage error over 10 points after 200 forecasts.
- **Honest prior:** Poor to fair, named plainly. The cross-sectional analogue was killed (S21: mined analogs, IC plus 0.0046). This is a different construction, self-only, but it must beat that prior in public or join it in the Graveyard.

## Engine 16. Own Capitulation Volume Clock

- **One job:** Forecast return and exhaustion together when a beaten-down name prints its own capitulation volume.
- **THE FORECAST:** When a name in a drawdown (own price below its own 200-session mean) prints down-volume above the 95th percentile of its own down-volume distribution and activity above its own 90th percentile: predicted median 20-session excess against SPY at least plus 1.0 point, and probability at least 60 percent that its volume returns below its own median within 10 sessions. Direction and probability form; either half failing falsifies that half.
- **Mechanism:** Self-relative candidate SR-9. F6 (high recent down volume in resets is better) and new10 N6 (volume-confirmed capitulation), with both thresholds converted from cross-sectional ranks to own-history percentiles. The A9 mirror is the gate: trade-count surges are a strong avoid in stretched names, so this engine fires only inside a drawdown, never on an up-move. The reset2 tension is printed on the card: its f_voldie pass defines the volume state differently and points the other way; this engine follows F6's definition verbatim and says so.
- **Corpus lineage:** F6 (IC plus 0.040 and plus 0.020, both eras; quintile spreads plus 0.95 and plus 1.28 points); N6 (IC plus 0.016, t 4.2, and plus 0.015, t 3.9, all days); A9 as context gate.
- **Why new:** Tool 38 Unusual Volume flags abnormality descriptively. No corpus part issues a dual return-plus-exhaustion forecast from own-percentile capitulation inside own drawdowns.
- **Data route:** DEEP daily bars, volume on daily bars only. No hourly-volume variant: the standing desk law bars Yahoo hourly volume as corrupt, and Alpaca SIP hourly history is shallow. Exists today.
- **Grading protocol:** Ledger at trigger close; return leg at 20 sessions, exhaustion leg at 10; episodes deduplicated per name with a 10-session lockout. Kill: after 200 episodes, either leg's confidence interval includes its null.
- **Honest prior:** Fair to good. Two definitions of the same idea carry same-sign cross-era evidence, which is more than most directional candidates have. Effect sizes on record are about a point, and the forecast claims about a point.

## Engine 17. Family Fracture

- **One job:** Forecast range expansion from the geometry of disagreement between evidence families, never from their agreement and never a direction.
- **THE FORECAST:** Daily pre-open for SPY and QQQ: predicted 5-session realised range as a percent of price, and probability the absolute 5-session return exceeds 1 EM, computed only from the day's cross-family disagreement pattern. Distribution and probability form.
- **Mechanism:** Fused from inversion candidate 4 (Family Fracture) and meta candidate M2 (Disagreement Barometer), the same object from two lenses. The five families' signed readings on the index are grouped per N3, one vote per family; the signal is the specific disagreement geometry (for example price positive while modelled inventory is negative and prints are one-sided: a leveraged-consensus state) plus dispersion of family-level trailing hit rates, not the agreement count. Tool 18 Second Opinion counts agreeing families; this engine inverts it.
- **Corpus lineage:** N3 family grouping; V1 and V4 (vol is the validated target class; shapes and weak internals forecast vol, not direction); AD-56 HAR as the benchmark it must beat; tools 1, 4, 18 and the volatility bench (26 to 28) as input producers.
- **Why new:** Every vendor consensus product in the corpus sums agreement. None models the pattern of disagreement as the signal, and none grades a meta-signal against the HAR control it must beat.
- **Data route:** All family readings are produced daily by Map, Tape, Board and the vol bench. The filings family is slow (13F quarterly) and is carried as its last reading with its age printed, per N4 absence discipline. Exists today.
- **Grading protocol:** Ledger pre-open; graded at plus 5 sessions on range error against the HAR-only benchmark and on breach-probability calibration. Kill: after 100 sessions, fracture does not beat HAR alone on range error. That comparison is the falsifier, stated in advance.
- **Honest prior:** Fair. The target class is validated and disagreement-as-information is plausible, but no corpus study measures forecaster or family dispersion directly; the HAR bar is deliberately hard, because HAR is grade A.

## Engine 18. The Living Router

- **One job:** Replace a verdict with a weighted, calibrated distribution over what a name does next, where the weights are themselves a public graded record.
- **THE FORECAST:** For every name where at least two tracked forecasters disagree: a probability distribution over the name's 21-session SPY-excess return tercile (bottom, middle, top), produced by Bayesian model averaging over forecasters with live weights. Distribution form, graded by ranked probability score.
- **Mechanism:** Meta candidate M3, ascending tool 44. Each forecaster's weight is its exponentially decayed forward Brier or log score from the ledger (half-life 63 sessions), shrunk toward equal weights by a factor set by the D10 track-record math, and capped per evidence family so three price-family forecasters cannot outvote one prints forecaster (N3 as a weight cap, not a footnote). A forecaster whose lineage or clocks fail the N4 eligibility check gets weight zero, not a guess. When total effective weight falls below a pre-registered floor, the distribution is published flat and graded as flat: abstention is an output with mass, not a default.
- **Corpus lineage:** Tool 44 The Router (one verdict per name, Abstain default, replay-book proof BLOCKED: the named defect this design cures by construction, because the proof is the forward ledger); N1; N3; N4; Factory P3.
- **Why new:** The Router is a classifier with a blocked proof. No vendor in the corpus publishes live model-averaging weights over its own competitors, and no tool's weights are a graded public record.
- **Data route:** Exists today for Board, Map and Wall, Tape, grade-A cells and Strat labels, all ledgered or carded. Populations not yet ledgered enter at weight zero until they are.
- **Grading protocol:** Every distribution ledgered before the session opens; graded at plus 21 sessions against two controls: an equal-weight average, and the best single forecaster chosen in-sample (the selection-bias control D10 demands). The card prints both name count and independent-window count, because overlapping 21-session windows inflate apparent sample size (the C11 study's 29 weekly dates are the cautionary precedent). Kill: after 126 graded name-windows, it does not beat the equal-weight control; weights then freeze and it publishes the equal-weight distribution labelled as such.
- **Honest prior:** Fair as a calibration device, unproven as an edge device. Model averaging reliably beats picking a winner; whether the underlying population has anything to average is the corpus's open question, and this engine's controls are designed to answer it honestly.

## Engine 19. In-Regime Oracle

- **One job:** Forecast whether a forecaster is about to have a good window or a bad one, from its own grading curve alone.
- **THE FORECAST:** Each Monday pre-open, for each tracked forecaster population (the 63 grade-A cells grouped by family, the Board gate, Tape Heat cohorts, Strat labels, Echo Board posters with at least 10 graded calls): the probability that its next-21-session hit rate exceeds its own trailing-126-session hit rate. Probability form, scored by Brier.
- **Mechanism:** Meta candidate M1. A two-state regime estimate per forecaster built only from its own grading series: recent Brier trend, hit-rate autocorrelation, calibration slope, call-volume change. No price inputs. This deliberately inverts a corpus kill: per-name price HMM regimes were ruled out (AD-39, V7); regimes here are estimated on grading series, which are low-dimensional and directly observed, not on price.
- **Corpus lineage:** N1 ledger and scorecards (the grading curves); Factory cell families (C12); tool 48 Horizon Grades' per-family horizon data as input features; D10 (the 2.7-year minimum-track-record warning, printed on the card as the reason no state is ever called proven). Ascends tool 47 Decay Watch, which reports decay after it appears; this stakes a probability on the next window before it opens.
- **Why new:** No vendor and none of the 70 forecasts a forecaster's near-term competence.
- **Data route:** The append-only ledger (Morgue output ledger.jsonl), published Board rows, Record grades at 1, 5 and 21 sessions. Exists today. Populations with thin ledgers (Golden Sweeps: 0 prints in 2 sessions) are excluded until at least 30 graded calls exist, and the exclusion is printed.
- **Grading protocol:** Ledger Monday before the window; grade at window close from the ledger only; Brier and calibration slope per forecaster and pooled; forecasters whose state was misjudged stay in the denominator. Kill: after 12 windows, pooled Brier is no better than climatology (each forecaster's trailing rate, unchanged), and the engine is demoted to the Graveyard with its record intact.
- **Honest prior:** Unknown, and the card says so. Forecaster skill persistence is exactly what the corpus has not established; D10 warns that 12 windows cannot prove skill either way. This engine is ranked on the sharpness and cheapness of its test.

## Engine 20. Calibration League

- **One job:** Forecast how wrong every other forecaster's stated confidence is about to be, and stake its own record on it.
- **THE FORECAST:** Monthly, for every distributional forecaster publishing to the ledger (Engines 1, 2, 5, 6, 12 and 15, plus the vendor band and vendor POP constructions entered as contestants): a forecast interval for that entrant's coverage or calibration error over its next 60 graded forecasts (example form: the vendor 15.87 band's stated-68 coverage will land between 76 and 86 percent). Distribution form, falsified directly when the 60 forecasts mature. The fused companion claim from meta candidate M7: a ranking of forecasters by predicted next-month calibration error, scored by rank correlation against the realised ranking.
- **Mechanism:** Fused from distributional candidate D10 (Calibration League) and meta candidate M7 (Calibration Weather). A meta-model over the ledger itself: each entrant's running reliability curve, sample size, regime mix and known structural biases (AD-55's 13 to 17 point over-cover, AD-57's touch overstatement, AD-58's IV-POP 12 to 15 point understatement) projected forward with binomial sampling width. Rankings use Brier and CRPS skill against the climatology baseline, discounted by family (N3) so five price-family entrants agreeing counts once. An entrant whose lineage fails the N4 five-clock check is listed ineligible, never silently dropped.
- **Corpus lineage:** N1, N3, N4; AD-55 to AD-58 as the entrants' priors; tools 2 The Record and 48 Horizon Grades as display ancestors (both report the past; neither forecasts the graders' future calibration).
- **Why new:** A league that must predict its members' honesty, in public, and is itself graded by the same rule, exists in no vendor teardown and none of the 70.
- **Data route:** The append-only ledger plus the site Record receipts. Exists today and is young by construction (22 matured 1-day Board outcomes at the last snapshot), so early intervals are honestly wide and say so.
- **Grading protocol:** Recursive and non-negotiable: the League's own monthly forecasts are ledgered before the month opens, graded by the same rule it grades others. Interval hit rate and width published at each month's close; missed and ineligible entrants both listed. Kill: after 12 monthly rounds, its interval hit rate is no better than a no-change forecast of each entrant's trailing error.
- **Honest prior:** Good for the known-bias entrants (the vendor band's over-cover is a measured, stable fact), unknown for the rest. It is the cheapest engine in the back half to grade and among the fastest to an honest verdict.

## Engine 21. Streak Trap

- **One job:** Forecast the future value of the terminal's own young headline numbers, before they are quoted at face value.
- **THE FORECAST:** Whenever any terminal surface is about to display a hit rate or success share computed on fewer than 30 matured outcomes: a ledgered predicted range for that figure's value after the next 30 outcomes mature, and a probability of at least 0.7 that the figure moves toward its family's long-run base rate by at least one third of its current deviation. Probability and distribution form.
- **Mechanism:** Meta candidate M12. A shrinkage forecaster aimed at the publisher: the forecast is computed from the relevant family base rate and the Wilson interval width at issuance. The corpus's recurring failure is not only bad mechanisms, it is young numbers quoted at face value (C10's undated test counts; C11's 64 and 67 percent hit rates on 22 outcomes with Wilson intervals of roughly 43 to 80 and 39 to 86 percent; the wall record's 6 of 6 on 6 tests).
- **Corpus lineage:** C10, C11; the section 2.8 wall record in the inventory; N1 (figures recomputed from the log; these forecasts are log entries like any other); D10. Tools 2 The Record grades calls and 19 The Receipts state provenance; neither forecasts the future value of the terminal's own displayed statistics.
- **Why new:** A publisher staking dated predictions on its own headlines is in no vendor teardown in the corpus.
- **Data route:** Every published figure with its matured count is already on the site receipts spot-read for the inventory (wall-check, record, golden-sweep-wire, grade-a-board). Exists today.
- **Grading protocol:** Trigger and forecast ledgered at the figure's first display; the figure's definition is frozen at issuance, and if the definition later changes the forecast grades as void-by-redefinition, counted separately, never silently dropped. Graded when the next 30 outcomes for that exact figure mature. Kill: over the first 10 matured triggers, shrinkage forecasts are not better calibrated than a no-change forecast.
- **Honest prior:** Good. Shrinkage toward a base rate is the statistically conservative direction, and the corpus supplies both the base rates and repeated demonstrations that young figures regress. This is the fastest engine in the set to a first honest verdict.

## Engine 22. Half-Life Clock

- **One job:** Publish a signal's obituary in advance: when a live forecaster will decay to half its promoted strength.
- **THE FORECAST:** At the start of each month, for each named forecaster family on the Record (each Factory family, F3, the RESET composite, Board gate cohorts, Tape cohorts): the predicted number of sessions until its rolling 21-session information coefficient falls to half its value at promotion (a half-life date, plus or minus 10 sessions), and a binary call, ledgered that day, on whether it crosses that half value within the next 60 sessions. Timing and probability form.
- **Mechanism:** Inversion candidate 1. Decay is modelled, not awaited: inputs are age since promotion, IC trajectory slope and variance since promotion, regime distance between the discovery window and today, and family crowding (how many sibling cells share its evidence family). The starting model is a survival curve fitted on the Factory rerun's own life histories, refit only on matured ledgered outcomes. The prior is the corpus's base rate: of 1,217 promoted cells, only 63 reached grade A and 564 did not replicate (C12); most promoted signals are already dying at promotion.
- **Corpus lineage:** Forecast Factory replication record (N9, C12); tool 47 Decay Watch's underlying grade series as data source (the tool reports decay observed; it is not this engine); tool 33 Regime Dial state; N3 family labels. Kept separate from Engine 23 by design: this engine clocks live families continuously on a monthly cadence; Engine 23 prices a Factory cohort at a discrete promotion or rerun event. Their horizons, data and grading events differ, and merging them would blur both falsifiers.
- **Why new:** Vendors retire dead products silently. No tool or vendor in the corpus forecasts a death date for a signal and stakes a gradeable claim on it.
- **Data route:** The Record and Grade-A Board ledgers and the Factory rerun record exist today; forward grades accrue from the daily cycle already running. No new feed.
- **Grading protocol:** Ledgered monthly before the 60-session window opens; graded at day 60 exactly: half-life date error in sessions, and Brier on the binary call, per family, families counted once. Families that die before day 60 stay in the denominator: that is a hit on the binary call, not an exit. Kill: after 24 monthly cohorts, its date error is no better than predicting the family's median historical half-life for every family.
- **Honest prior:** Good for the direction of the bet (most signals die: that is the corpus's dominant empirical fact), unproven for the timing precision, which is the part being graded.

## Engine 23. Promoted-Book Mortality Curve

- **One job:** Never let a promotion headline travel without its predicted mortality attached.
- **THE FORECAST:** Two arms. Forward arm: at any future Factory-style promotion event, within 24 hours and before any rerun data exists, per promoted cell a probability of replicating under the pre-registered rerun rule, and for the cohort a predicted grade-A count with a 90 percent interval. Event arm, quarterly until the next rerun: all 63 current grade-A cells ranked by predicted probability of failing that rerun, with a predicted failure count. Probability and distribution form. Backcast registration, labelled as such: the same model form, fitted only on run 1 promotion-time features, must retrodict a grade-A interval covering 63 and a not-replicated interval covering 564, or the form is rejected before any forward use.
- **Mechanism:** Fused from meta candidates M5 (Decay Prophet) and M11 (Promoted-Book Mortality Curve) and inversion candidate 12 (Consensus Autopsy): three lenses produced the same actuarial object, and the fusion is stronger than any one because it carries M11's backcast gate, M5's per-cell survival features, and the Autopsy's full-ranked-list grading. Features are promotion-time only: pass margin, family, horizon, stretch consistency, capacity margin, family redundancy (AD-32: weak 6-month momentum is 97 percent distance from the 250-day high, so near-duplicate cells share one fate), and whether the cell's family has any A or B registry support outside the Factory. Untestable is a predicted outcome class with its own probability mass (253 of 1,217, about 21 percent, printed as the prior), never dropped.
- **Corpus lineage:** C12 in full (run 1 and the pre-registered rerun); N9; N1; AD-32; the EV registry as cross-family corroboration; tools 42 Grade-A Board (lists the survivors), 45 Promoted Book (the cohort surface this forecast rides on; the Book lists, this predicts) and 48 Horizon Grades.
- **Why new:** The Factory grades after the fact by design. The actuarial layer that prices a claim's survival at promotion time exists nowhere in the corpus, and it cures C12's presentational defect prospectively: the 1,217 figure can never again travel without its replication outcome, predicted or realised, beside it.
- **Data route:** Run 1 and rerun records exist today and are sha-pinned in the corpus. The forward arm's route exists conditional on a future promotion event occurring; the event arm's grading waits on the next pre-registered rerun.
- **Grading protocol:** Backcast verdict published first. Forward and quarterly lists ledgered before any rerun data for that cycle is touched; graded by the rerun's own published rule, all cells in the denominator, scored by rank correlation of predicted against realised failure order, Brier per cell, and count error per cohort.
- **Honest prior:** The best-anchored meta prior in the set: it is fitted on the corpus's one complete promotion-to-replication life cycle. Its weakness is equally plain: one life cycle is one sample, and both grading arms are event-bound, not time-bound, so its proving state is marked in part unmet until a rerun or promotion event grades it.

## Engine 24. Fear-Day Triangulation

- **One job:** Test, in public and with a self-retirement rule, whether three independent families can carve selection out of a pure timing effect.
- **THE FORECAST:** On fear days (tool 16's definition), uptrend names satisfying all three of: pullback depth in the deepest quintile against the stock's own norm (F3), gap share in the top tercile (S15), and zero insider sells on record, will beat the fear-day random-entry control (T1: any uptrend name on a fear day, plus 0.29 to plus 0.36R) by at least plus 0.10R mean at 20 sessions. Direction form, R-based, same exits as the picker replay for comparability.
- **Mechanism:** Cross-family candidate XF-6. T1 proved the lift belongs to the day, not the setup (grade B, shared with random entries). This engine is the honest counter-test. Family discount enforced on its own card: F3 and gap share share bar data, so they count as at most 1.5 families, and the card says so.
- **Corpus lineage:** Price (F3, N10); gap share (S15, grade B, top-VIX-third IC plus 0.069 and plus 0.074); filings (insider silence, summary grain); T1 as the control's source. Every vendor stacks confirmations and calls the stack stronger; price-only stacks were killed (S19). A cross-family stack with a pre-registered self-retirement rule and a random-entry control is the opposite product.
- **Why new:** The conjunction, the control, and the self-retirement rule together appear nowhere in the corpus.
- **Data route:** DEEP bars and shipped daily history; insider summaries at summary grain. Fear-day accrual is slow: the shipped local record holds 1 qualifying day (2026-10-16), so grading is event-driven, likely quarters, and fires-to-date is published on the card. The proving state will be long, stated, not hidden.
- **Grading protocol:** Ledgered per fear-day cohort; controls ledgered at the same time: random fear-day entries and the F3-only cohort. Kill, pre-registered as the engine's own verdict: if the triple conjunction does not beat the single best component (F3 alone) once three cohorts mature, triangulation adds nothing and the engine retires itself.
- **Honest prior:** Fair to poor, by design. It is built to be able to fail, on the corpus's clearest timing-versus-selection question. Its value if it dies is a clean, public answer; that is stated here so its death is later read as the design working, not as a surprise.

## Engine 25. Sponsored Reset

- **One job:** Sharpen the RESET survivor by separating washed-out-and-held names from washed-out-and-abandoned ones, using filings sponsorship.
- **THE FORECAST:** Deep-reset names (35 to 80 percent off their high) matching the N9 RESET composite on a fear day, and showing institutional sponsorship (13F holder count not falling, or an insider buy on record), while SPY is above its rising 200-day average (the T4 gate): mean 20-session SPY excess of at least plus 2.0 points. Direction form.
- **Mechanism:** Cross-family candidate XF-10. The N9 composite's components (laggard relative strength F7, down-volume capitulation F6) describe a washed-out name. Sponsorship is the new family against that price-only composite, and F4 is its avoid twin: idiosyncratic, unsponsored declines persist. The T4 gate keeps the cohort out of the regime where leader setups lose (grade B: plus 0.1 to plus 0.2 percent in up markets against minus 1.2 to minus 1.3 percent otherwise).
- **Corpus lineage:** N9 RESET composite (fear-day IC plus 0.053 and plus 0.028, holdout confirmed, grade B; its UP version faded in holdout and is not used); F6 and F7; T4; 13F direction (tool 40) and insider buys (tool 21). Ascends tool 49 Survivors Wire, which publishes the survivors and crosses them with no filings condition and no regime gate.
- **Why new:** The RESET composite is price-only by construction in the corpus. Whether a filings condition sharpens a survivor is a new, gradeable question.
- **Data route:** DEEP bars; 13F two quarters on record (8,857 and 8,871 filers); insider summaries. Partial, stated: summaries cannot identify cluster buying (named on tool 21 itself), so sponsorship uses holder-count direction and any-buy flags at summary grain only.
- **Grading protocol:** Ledgered per fear-day cohort; baselines ledgered alongside: N9 alone, and N9 plus the T4 gate without the filings condition. Kill: after 3 fear-day cohorts, the filings condition adds less than 0.5 points of mean excess over the gated baseline.
- **Honest prior:** Fair. The parent composite is a genuine grade B survivor and the gate is grade B; the filings increment is untested and, at summary grain, coarse. Cohort accrual is fear-day paced, so verdicts are slow.

## Engine 26. Silent Accumulation

- **One job:** Forecast from three accumulation footprints that leave no price trace, where the signal in one family is an absence.
- **THE FORECAST:** Names where constituent DIX or dark pressure is in the top quintile, insider summary shows zero sells in the trailing record window, and 13F holder count or aggregate position rose between the two quarters on record: their 21-session SPY-excess return distribution will have a median above zero and a top-quartile frequency at least 5 points above the unconditional rate. Distribution form.
- **Mechanism:** Cross-family candidate XF-2. Off-exchange buying, insiders not distributing, and institutions building between filings are three genuinely independent primitives (N3), and no vendor treats an absence (zero sells) as a reading. The conjunction is rare by construction, which is the point.
- **Corpus lineage:** Constituent-weighted DIX (N6, recombined; live-graded 0.4365 over 501 of 503 names on its recorded day, with its construction labelled, C8); tool 24 Dark Prints per-name dark pressure; tool 21 insider summaries; tool 40 13F sets. Price is used only for grading, never as an input.
- **Why new:** InsiderFinance scores prints, SqueezeMetrics scores dark flow, 13F trackers report drift. Nobody requires all three to agree and grades the conjunction.
- **Data route:** DIX live-computed; insider summaries on record for 43 of 50 names; 13F two quarters on record, which means crowding and drift have exactly one observation per name today. Partial, stated at summary grain throughout, and the engine sharpens only as quarters accrue.
- **Grading protocol:** Cohort ledgered at each 13F publication plus the weekly DIX refresh; 21-day median and top-quartile rate against the all-names baseline and against each single condition alone. Kill: after 100 cohort names, the interaction adds less than 2 points over the best single condition.
- **Honest prior:** Weak. None of the three parents has a forward grade as a forecaster in this corpus (13F changes and insider summaries are both untested in the registry), and the grain is coarse. It survives the convergence on novelty and on the independence of its families, ranked accordingly, near the back of the build order.

## Engine 27. Pin-or-Escape

- **One job:** Forecast when expiration gravity holds and when it fails, conditional on the dealer's book, instead of publishing the pin as an unconditional level.
- **THE FORECAST:** Into weekly expiry, when spot opens within 0.3 percent of the open-interest gravitation pin level and net GEX is positive and the variance risk premium is in its bottom half: SPY closes within plus or minus 0.25 percent of the pin in at least 40 percent of weeks. In the same pin proximity with net GEX negative: closes within that band in at most 20 percent of weeks. Companion claim, from inversion candidate 10 (Pin-Failure): probability the close lands more than 0.5 EM from the pin, and the predicted absolute close-to-pin distance in percent, ledgered on the same mornings. Distribution and probability form, both arms ledgered.
- **Mechanism:** Fused from cross-family candidate XF-7 and inversion candidate 10. Pinning is a dealer-hedging phenomenon, so its success must be conditional on the sign of the dealer's book and on whether vol is priced for escape. Failure-mode inputs are named and pre-registered as one score, never tuned per week: negative gamma at the pin strike, a macro-calendar event inside the session, a gap opening beyond the pin's strike neighbourhood, and pin-strike open interest small against neighbouring strikes (a weak pin).
- **Corpus lineage:** Tool 30 Expiry Pin Watch (the level, published untested: this engine grades it); tools 1 and 54 (GEX by strike); VRP evidence T3 and V2; tool 34 Week Ahead calendar (coverage 2026-01-01 to 2027-12-31 on record); S15 gap evidence.
- **Why new:** No vendor conditions its own pin level on its own gamma sign. Pin products present the level as the forecast; the conditional split and the failure probability are the engine.
- **Data route:** Chain snapshots and Map cards on record; VRP from the SPY and VIX daily series 2010 to 2026. Exists today. Cohorts accrue at roughly three index forecasts per week.
- **Grading protocol:** Ledgered on expiration morning before the open; graded at that close: close-distance distribution per arm, breach Brier, and distance error, against the unconditional pin-hit baseline. One modelled-inventory family plus one distributional family, plus the calendar as a third, each counted once. Kill: after 52 weeks, the two arms' in-band rates are statistically indistinguishable.
- **Honest prior:** Unknown. The pin level itself has no forward grading anywhere in the grounding files. The conditional structure is mechanically motivated, but this engine's first year is the first test the pin claim has ever had, and its prior is stated as untested rather than borrowed from the level's popularity.

## Engine 28. Gap Destiny

- **One job:** Take today's actual gap and issue a ledgered probability set for this session, where the built tool only shows how gaps like it behaved historically.
- **THE FORECAST:** At each open, for SPY, QQQ, IWM and any shipped-universe name gapping at least 0.5 percent: probability the gap fills the same session, probability it closes above the open and below the open, and the decile distribution of the session's range as a multiple of the gap, stated per gap-size band (0.5 to 1, 1 to 2, over 2 percent) by weekday, matching the Studies S1 partition. Probability and distribution form.
- **Mechanism:** Distributional candidate D7. The S1 gap-fill empirical distributions re-estimated on DEEP daily OHLC (a fill is decidable from the day's high and low against the prior close), conditioned additionally on fear state (T1) and on gap share's top-VIX-third conditioning (S15) as distribution shifters.
- **Corpus lineage:** Studies S1 and tool 11 Gap-Fill Pane (the descriptive ancestor this ascends); S15 (grade B); T1. The per-name variant from self-relative candidate SR-10 (each name's own gap habits, stability-gated) is recorded as this engine's second arm once pooled grading matures, not as a separate engine: the pooled and per-name forms grade the same event and splitting them would double-count one family.
- **Why new:** A pane shows history. This engine stakes probabilities on this session, before it unfolds, and is graded on this session.
- **Data route:** DEEP and shipped daily OHLC: full route today. Marked limitation, carried from the candidate: a time-of-fill variant (fills by 10:30 against by close) cannot meet the data clause today, because the live intraday route was no-data in the recorded run and hourly history is shallow. That variant is excluded, not promised.
- **Grading protocol:** Ledgered at the open print, before the fill window opens; graded at that session's close, fills and non-fills both counted; Brier on the fill and close probabilities, coverage on the range deciles, per 60-forecast block. One price family. Kill: after 120 index gaps, fill-probability Brier is no better than the unconditional per-band base rate.
- **Honest prior:** Fair for the fill probability (the underlying distributions are fixture-proven and the event is mechanically decidable the same day, so grading is the cheapest in the set), weaker for the range deciles in the largest gap band, where the historical counts are thinnest.

## Engine 29. Completion Clock

- **One job:** Forecast how long an in-flight move takes to resolve, and which barrier it reaches first, instead of what it pays on average.
- **THE FORECAST:** Whenever a ledgered cohort event fires (a fear day per tool 16's definition; a deep-reset name entering the RESET cohort; a defined event of the kind temporal candidate T2 catalogues): the timing density: probability the cohort's median name reaches plus 1 EM before minus 1 EM within 5, 10, 21 and 60 sessions, and the decile distribution of sessions to the first of those barriers, expiring at 60. Timing and distribution form. The sessions-since hazard curve from T2 (probability of resolution at each elapsed session k from 1 to 21, with median sessions to resolution) is ledgered as the same forecast's second panel, not a separate engine.
- **Mechanism:** Fused from distributional candidate D9 (Completion Clock) and temporal candidate T2 (Sessions-Since Clock), which are one object: a first-passage timing distribution over an event cohort. Empirical barrier-race and hazard distributions from the picker replay corpus (296,093 graded cases) and DEEP, conditioned on cohort type and vol state. The 60-session cap is the corpus's own best-horizon finding (E3); the 1 to 5 session decay facts (X family) shape the early hazard. Duration dependence, hazard rising or falling with elapsed sessions, is the falsifiable claim, distinct from a horizon mean.
- **Corpus lineage:** Picker replay corpus and tool 46 Odds Cards' distributions (what a setup family paid; nothing in the corpus times it); T1 and T2 timing evidence; E3; the N9 RESET cohort definition (grade B); tool 16's fear-day definition. Shares Engine 2's first-passage machinery and family: the two are never counted as two confirmations.
- **Why new:** Timing densities are absent from the entire corpus, vendor and desk alike. Position sizing and patience consume exactly this quantity, and no tool supplies it.
- **Data route:** DEEP plus the picker corpus on record for priors; forward cohorts fire from machinery already running (the fear-day definition, shipped daily history, Map cards for the wall-break event class). That one class is partial today: 9 map cards on record, so its hazard prior dominates until cards accrue, and it is stamped as such.
- **Grading protocol:** Ledgered at cohort entry, before the first barrier session opens; survival calibration and barrier-race Brier at 5, 10, 21 and 60, scored per elapsed session against the unconditional historical hazard for that event class; unresolved-at-60 cases stay in the denominator as their own outcome class, censored cases never dropped. Kill: after 30 matured cohorts, its timing Brier is no better than the unconditional hazard.
- **Honest prior:** Fair. The component facts (decay in 1 to 5 sessions, best horizon near 60) are measured, but no corpus study has ever graded a timing density, so the calibration claim is genuinely open.

## Engine 30. Abstention Signal

- **One job:** Forecast the market from forecasters going quiet, a signal that exists only because this corpus records absence honestly.
- **THE FORECAST:** Daily: when the family-discounted abstention rate across tracked forecasters (Router Abstain verdicts, Board no-data categories, Tape no-print days, Factory cells untestable that window) exceeds its trailing-63-session 80th percentile, a ledgered probability that SPY's 21-session realised volatility will exceed its trailing-63-session median, secondarily graded at 5 sessions. Probability form.
- **Mechanism:** Meta candidate M9. The fail-closed law (N4) makes absence a state, never a number. Forecasters go quiet when their inputs degrade, coverage floors fail (C1: Institutional Positioning no-data at 4 of 7 leaves, under the verbatim 60 percent floor), or conditions leave their registered domain: exactly the conditions under which the near future is less ordinary. The historical shape is on record: the Factory's 253 untestable cells (C12) cluster rather than scatter.
- **Corpus lineage:** N4 and its absence states; C1; tool 44 The Router's Abstain default; V1 and V4 (vol as the target class). C14 is a named contamination, handled by the shared family registry: abstentions caused by the three uncured fail-open Femto functions are tagged defect-abstentions and excluded, or this engine learns the desk's bugs instead of the market. Until that tagging is live, the engine ships proving with the contamination disclosed on its card.
- **Why new:** Every vendor fills gaps silently. A forecast built from the gaps themselves is possible only in a corpus that records absence honestly, and exists nowhere in the 129 vendor labels.
- **Data route:** Daily cards already record no-data states explicitly across Map, Board, Tape and Studies. Exists today, with the one partial input named above: defect against genuine abstention is not yet separable in the record.
- **Grading protocol:** Ledgered daily pre-open with the abstention rate and its percentile printed; graded against realised vol at the fixed horizons; control is the VIX level alone, the trivial predictor it must beat. Kill: after 80 graded days, its probability adds no Brier improvement over the VIX-only control.
- **Honest prior:** Speculative, and ranked last for that reason despite high novelty. The clustering premise is supported by one historical episode class (the Factory's untestables), not by a graded study. It is included because it is the only candidate in the 72 that could not exist in any other corpus, and its falsifier is cheap and pre-registered.

---

## Build queue order

Build the shared machinery first (forecast ledger, grading runner,
family registry, as specified above), then the engines in the order
numbered: 1 to 30 as listed. The order is forecast-worthiness order,
which here is also roughly verdict-speed order at the front and
accrual-speed order at the back:

- **First wave (daily grading, data in hand, strongest priors):**
  1 Corrected Band Engine, 2 Touch Surface, 3 Own-Norm Depth
  Forecaster, 4 Stress-Reversal Staging (episodic grading, but the
  build is small and the prior is the corpus's best), 5 Honest POP
  Engine, 6 Exceedance Forecaster, 7 Realised-Vol Term Shape
  Forecaster, 8 Wall Lifetime and Break Forecaster (build early
  precisely because its record is thin: every week of delay is a
  week of map cards unledgered for this purpose).
- **Second wave (cohort and cross-family engines):** 9 Intake-Bias
  Reversal, 10 Insider-Flow Divergence, 11 Gamma-Pressure Earnings
  Trap, 12 Earnings Move Distribution Engine, 13
  Idiosyncratic-or-Liquidity Splitter, 14 Own-Volatility
  Normalisation Clock, 15 Per-Name Self-Analogue, 16 Own
  Capitulation Volume Clock, 17 Family Fracture.
- **Third wave (meta engines, which need the first waves' ledgers as
  their population):** 18 The Living Router, 19 In-Regime Oracle,
  20 Calibration League, 21 Streak Trap, 22 Half-Life Clock,
  23 Promoted-Book Mortality Curve.
- **Fourth wave (slow accrual, event-bound, or summary-grain):**
  24 Fear-Day Triangulation, 25 Sponsored Reset, 26 Silent
  Accumulation, 27 Pin-or-Escape, 28 Gap Destiny (fast grading, but
  its per-name second arm waits on the pooled record), 29 Completion
  Clock, 30 Abstention Signal (waits on defect-abstention tagging in
  the family registry).

No engine in any wave is described as predictive in public until its
own ledgered record matures past its stated proving threshold. The
waves are build order, not permission to soften that rule for later
waves.

---

## Appendix: convergence notes, what was killed or fused and why

72 candidates entered (XF 1-12, D 1-12, inversion 1-12, M 1-12,
SR 1-12, T 1-12). 30 engines leave. Every candidate is accounted for
below.

**Fusions (two or more candidates became one stronger engine):**

- D3 + inversion 7 became Engine 2 (Touch Surface): the same
  corrected touch probability, proposed independently by the
  distributional and inversion lenses.
- D4 + inversion 2 became Engine 8 (Wall Lifetime and Break): lifetime
  distribution and same-session break probability are one hazard
  object over the same levels.
- XF-3 + inversion 3 became Engine 9 (Intake-Bias Reversal): the
  cross-family version contributed the short-volume interaction, the
  inversion version the quintile-median claim; both grade the same
  dual-population gap.
- Inversion 4 + M2 became Engine 17 (Family Fracture): disagreement
  geometry and forecaster-dispersion vol forecasting are one signal
  with one falsifier (beat HAR).
- XF-7 + inversion 10 became Engine 27 (Pin-or-Escape): the
  conditional pin-hold split and the pin-failure probability are two
  arms of one expiry forecast.
- M5 + M11 + inversion 12 became Engine 23 (Promoted-Book Mortality
  Curve): three lenses produced the same actuarial object; the fusion
  keeps the backcast gate, the per-cell features, and the ranked-list
  grading.
- D10 + M7 became Engine 20 (Calibration League): forecasting an
  entrant's coverage error and ranking forecasters by predicted
  calibration error are one monthly object.
- D9 + T2 became Engine 29 (Completion Clock): barrier-race timing
  and sessions-since hazard are one timing density.
- D1 was folded into Engine 3's family, not kept separate: its
  state-conditioned per-name distribution is Engine 3's mechanism
  generalised past the point of separate falsifiability, and keeping
  both would have counted one price-family bet twice. Engine 15
  carries its distributional ambition in self-analogue form.
- SR-10 was folded into Engine 28 as its per-name second arm: pooled
  and per-name gap-fill grade the same event.
- XF-11 (Band-Trust Regime) was folded into Engines 1 and 20: a
  forecast about a band's reliability, conditioned on the wall
  record, is the Calibration League's job with a thinner input (6
  graded wall tests) than the League's own; as a standalone it would
  have been the same meta-claim on the least data in the pool.
- XF-4 (Wall-Breadth Fracture) was folded into Engine 17: breadth
  deterioration crossed with flip proximity is one fracture geometry
  among the family-disagreement geometries Engine 17 already grades,
  with the same HAR falsifier.

**Killed for failing the honesty law today (not padding, just not yet
buildable as claimed):**

- XF-9 (Squeeze Weather): conditional on the IV ledger, which stopped
  2026-10-14. It cannot meet the data clause until that ledger resumes
  and accrues. Revivable on that event, and its squeeze-gate cohort
  should be ledgered by tool 15 in the meantime so the history is not
  lost.
- T5 (Intraday Shape Echo): marked UNMET on data by its own author.
  The intraday route was no-data in the recorded run and hourly
  history is shallow. It ships, if at all, as an accrual counter, not
  as one of the 30.
- Inversion 6 (Crowding Unwind Gauge): one load-bearing input, the
  desk's own book, is internal and cannot be shown on a public card.
  It may run as an internal risk forecaster; it is not a public
  engine under N4 provenance discipline.
- Inversion 11 (Silence Forecaster): degenerates if golden sweeps
  never print, and a forecaster of a never-occurring event is
  unfalsifiable in practice. The December 8, 2026 proving decision on
  tool 5 governs whether anything in this space lives.

**Killed as duplicates, renames, or thinner versions of a kept
engine:**

- XF-5 (Hot Tape into the Print): an earnings-proximity flow fade
  whose distinct content is absorbed by Engine 11's earnings
  conditioning and Engine 9's flow-fade grading; as a standalone it
  was the sparsest-fire candidate in the cross-family file.
- XF-8 (Crowded Silence Breaks Louder): a tail claim resting on one
  13F observation per name and on tape absence; its tail-size ambition
  is carried, on better data, by Engine 6.
- XF-2's and XF-10's siblings were kept (Engines 26 and 25); XF-8 was
  the third filings-grain candidate and the weakest of the three.
- SR-3 (Personal Seasonality): answers a grade X market-wide kill
  with an untested idiosyncratic variant whose per-name forecasts are
  near-zero by its own admission. Falsifiable but weak is padding at
  the margin of a top 30.
- SR-5 (Deviation-from-Self Index): a composite of Engine 3's and
  Engine 15's inputs with frozen weights; the convergence judged it a
  variant of the self-relative bet, not a separate engine, under the
  lens author's own warning that the file's 12 are one family.
- SR-6 (Fear Personality): its forward score is Engine 24's cohort
  question asked per name on the rarest event class in the set; the
  cohort form grades first.
- SR-7 (Own Drawdown Anatomy): the RESET anatomy claim is carried by
  Engines 25 and 29 in cohort and timing form; the per-name reclaim
  probability was the third expression of the same survivor family.
- SR-11 (Own Trend-Age Hazard): answers a grade C sign flip with a
  normalisation fix. Plausible, but the weakest prior among the
  self-relative candidates and the least sharp forecast.
- SR-12 (Own Mean-Reversion Half-Life): a textbook quantity graded as
  a point forecast against baselines; honest, but its information
  content overlaps Engine 14's timing claim on a weaker construction.
- SR-1, SR-2, SR-4, SR-8 and SR-9 were kept (Engines 3, 15, 14, 13
  and 16): five self-relative engines is the family-discounted
  maximum this lens contributes, per its own summary.
- T1 (Strat Grammar): the largest teardown in the corpus has zero
  backing, and a sequence-grammar test, however well controlled, asks
  the programme to spend a top-30 slot re-testing the corpus's
  least-evidenced vendor. Its shuffle controls are adopted as grading
  discipline for any future Strat work, outside the 30.
- T3 (Family Ignition Order): genuinely novel, but its conditional
  tables stay insufficient-history until at least 126 multi-family
  sessions accrue on a tape record that today holds 2 sessions.
  Engine 17 grades the disagreement those days carry in the meantime.
- T4 (Index Relay): its own author pre-commits it to die if it
  collapses to the killed breadth result (T11, grade X), and the
  convergence judged that collapse the likely outcome. Not a top-30
  spend.
- T6 (Streak Hazard): a clean duration table, but AD-35's trap
  (probability lifts, no mean R) is its most probable terminus, and
  Engine 29 carries the duration claim in event form where the prior
  is stronger.
- T7 (Propagation Wave): names tomorrow's followers against T2's
  peer-gap reversal as an anti-control; the confrontation is real,
  but Engine 4 already stages T2 forward, and the wave's added claim
  is the weaker side of that pair.
- T8 (Overnight-Intraday Leg Relay): scoped by its own author as a
  replication-or-death test of a family AD-41 already killed for
  direction. The 30 do not spend a slot re-killing a kill.
- T9 (Earnings Path Script): the path-vector form is elegant, but its
  content is Engine 12's distribution plus A12 and A13 fragments
  graded jointly; the joint grading is adopted inside Engine 12's
  season protocol (the signed 5-session leg), and the 16-session
  vector did not earn a separate slot.
- T10 (Leadership Rotation Markov): a transition matrix over sector
  leadership whose honest favourite is the persistence null; ranked
  below every kept engine on mechanism plausibility per unit of
  novelty.
- T11 (Print-to-Price Delay Clock): a new and attractive object on a
  tape record of 2 sessions. It accrues inside Engine 9's and tool 4's
  ledgering; if the tape record matures, it is the first revival
  candidate named here.
- M3 was kept (Engine 18); M1 (Engine 19), M9 (Engine 30) kept;
  M4 (Crowd-of-Forecasts Thermometer) killed: its crowding episodes
  are a special case of Engine 17's disagreement geometry read at the
  extreme, and its 20-episode grading horizon is slower than
  Engine 17's daily one.
- M6 (Echo Decay): regression to the mean after a caller's best call
  is true almost by construction, which makes it the least
  informative forecast in the meta file; Engine 21 covers the same
  shrinkage discipline aimed at figures the terminal itself publishes.
- M8 (Horizon Migration): forecasting where an edge moves before
  establishing that it is anywhere; Engine 22's half-life claim
  subsumes its decay content with a sharper binary falsifier.
- M10 (Family Rotation): a quarterly composition forecast needing
  four quarters to a kill decision, forecasting an allocation
  question rather than a market quantity. Valuable internally,
  below the line for the 30.
- Inversion 5 (Mean-Median Split): a sharp idea on 26 weekly Board
  cohorts minimum to a verdict, forecasting the shape of one tool's
  own cohorts; Engine 21 generalises the young-figure discipline it
  depends on.
- Inversion 8 (Non-Fill Forecaster): the plan stream on record is 88
  live plans; the object is real but the stream is too thin to grade
  inside this programme's horizon. Second revival candidate, after
  T11, if the published plan stream grows.
- Inversion 9 (Avoid-Stack Failure Alarm): forecasting the veto
  layer's failure is the best idea killed here, and it is killed only
  on grading cost: 18 monthly cohorts to a proving verdict on a rare
  event. It is named the third revival candidate, and Engine 24's
  fear-day cohorts will incidentally ledger much of its input.

**Padding check, stated once:** every kept engine was checked against
all 70 tools by name. The nearest neighbours (tools 7, 11, 13, 14, 17,
20, 28, 30, 35, 42, 44, 45, 47, 48, 49) publish readings, panes,
lists, or after-the-fact grades. Every engine above ledgers a
forecast before its horizon opens and is graded on it. That
difference, and no other, is what each ascent claim rests on.
