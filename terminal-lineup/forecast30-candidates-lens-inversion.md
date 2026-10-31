# Forecast-30 Candidates — Lens: Inversion and Failure Geometry

Phase: invent. Lens: predict from how things fail, break, decay and unwind.
Date: 2026-10-28. Sources read: `forecast30-inventory.md`,
`REA-ANALYSIS-SUMMARY.md`, `analysis/03-CONFLICTS-AND-NOVELTY.md`
(C1–C18, N1–N12), `THE-70-TOOLS.md`.

SCOPE — Surface: 12 new candidate engines, none a rename of a vendor
product or of any of the 70 tools. Constraints: the corpus kill list is
not resurrected unmarked; no fantasy feeds; every engine ships in
proving state. Outcome: each candidate states a forecast precise
enough to grade. Proof: grading protocols below, all ledger-first
(N1). Edges: directional claims are the weakest class in the corpus
(2 of 384 direction cells vs 172 of 384 volatility cells, V4), so this
lens deliberately aims most engines at failure, magnitude, timing and
distribution, where the corpus's own evidence is strongest.

Honesty-law key, applied per candidate: (a) falsifiable forecast,
(b) ledger before horizon opens, (c) fixed-horizon grading, losers in
the denominator, (d) agreement discounted by evidence family (N3),
(e) named data route existing today, (f) proving state until the
forward record matures. Any requirement an engine cannot yet meet is
marked inline as UNMET with the reason.

---

## 1. Half-Life Clock — forecasting when a live signal dies

- **Forecast (a):** For each named forecaster family on the Record
  (each of the 63 Grade-A cells, each Factory family, F3, RESET N9),
  publish at the start of each month: the predicted number of sessions
  until its rolling 21-session information coefficient falls to half
  its value at promotion (its half-life date, ±10 sessions), and a
  binary call, ledgered that day, on whether it will cross that
  half-value within the next 60 sessions. Both are gradeable on the
  stated date whether or not the crossing happens.
- **Mechanism:** Decay is modelled, not awaited. Inputs are the
  signal's age since promotion, its IC trajectory slope and variance
  since promotion, the regime distance between its discovery window
  and today (volatility regime, breadth tercile), and family crowding
  (how many sibling cells share its evidence family). The corpus's
  base rate is the prior: of 1,217 promoted cells only 63 reached
  Grade A and 564 did not replicate (C12) — most promoted signals are
  already dying at promotion. A survival curve fitted on the Factory
  rerun's own life histories is the starting model; it is refit only
  on matured, ledgered outcomes.
- **Corpus parts combined:** Forecast Factory replication record (N9,
  C12) + Decay Watch's underlying grade series (tool 47 is the data
  source, not the engine) + Regime Dial state (tool 33) + N3 family
  labels.
- **Why new:** Tool 47 Decay Watch reports decay already observed.
  No tool or vendor in the corpus forecasts a death date for a signal
  and stakes a gradeable claim on it. Vendors retire dead products
  silently; this engine publishes the obituary in advance.
- **Data route (e):** The Record / Grade-A Board ledgers and the
  Factory rerun record exist today; forward grades accrue from the
  daily cycle already running. No new feed.
- **Grading (b, c, d, f):** Ledgered monthly before the 60-session
  window opens. Graded at day 60 exactly: half-life-date error in
  sessions, and Brier score on the binary call, per family, with
  family treated as one confirmation (d). All families forecast stay
  in the denominator, including families that die before day 60 (that
  is a hit on the binary call, not an exit). Proving state until 24
  monthly cohorts mature.

## 2. Wall-Break Forecaster — predicting the break, not the respect

- **Forecast (a):** For each Morning Map card (SPY, QQQ, IWM), before
  the open, publish P(call wall is touched AND closes through within
  that session) and P(put wall is touched AND closes through), as
  probabilities to two decimals, plus the predicted side of first
  failure (up / down / neither). The young record motivates the
  asymmetry: in the 6 graded tests on record the flip held 6 of 6,
  the put wall was never reached, and the call wall broke in both
  tests where it was reached, both times in IWM.
- **Mechanism:** Walls fail for reasons respect-rates hide: approach
  geometry. Features are distance-to-wall in expected-move units at
  the open, overnight gap share of that distance, net-GEX sign and
  distance to the flip, days to the dominant expiry, and the wall's
  own strike concentration relative to neighbouring strikes. In
  negative-GEX territory dealer hedging amplifies a touch into a
  through-move; in positive GEX it damps it. The forecast is the
  interaction, not the wall level itself.
- **Corpus parts combined:** Morgue Map GEX/walls/flip construction
  (SpotGamma published construction) + Wall Check grading definition
  imported, never forked (N8) + Azrael expected-move units (AD-55
  corrected: the band is ~81%, and the engine uses it as a unit, not
  as a 1-sigma claim) + gap-share evidence (S15).
- **Why new:** Tool 14 Wall Check grades walls after the fact; Tool 1
  Morning Map publishes the levels. Nothing in the corpus or any
  vendor teardown issues a pre-open break probability. SpotGamma
  sells the wall as a level to respect; this engine sells the
  calibrated probability that respect fails.
- **Data route (e):** Map cards publish daily today; chain snapshots
  and SIP bars for grading exist. Caveat carried from C2: grading
  must use `wall_study.py`'s own fetch path, not `studies_card.main`,
  whose wall input is still an empty dict on main.
- **Grading (b, c, d, f):** Ledgered pre-open, graded at that day's
  close only (horizon = 1 session, fixed). Brier score and calibration
  bins per index and per side; never-reached walls grade as
  no-break, exactly as the Wall Check card's own fields define it.
  GEX, walls and flip are one modelled-inventory family (d): the
  engine may not count them as three confirmations. Proving state
  until 60 graded cards per index (the existing record is 6 tests).

## 3. Bias Spread — the dual-population gap as an unwind forecast

- **Forecast (a):** Each session, for the 20 names with the largest
  absolute gap between the buys-only Algo Score and the all-prints
  Algo Score (N2), publish: predicted 5-session excess return vs SPY
  will be negative for the top-gap quintile cohort, with a predicted
  cohort median excess return (a number, in %). One cohort forecast
  per session, not 20 stock picks.
- **Mechanism:** FlowAlgo's buys-only intake is an invisible selection
  that manufactures bullishness: prints that would lower the score
  never enter it. When the manufactured score and the honest score
  diverge most, the tape is most one-sidedly presented — the exact
  condition under which the corpus's avoid evidence bites (A2 loud
  attention days fade; A9 trade-count surges are a strong avoid). The
  gap is a measured presentation bias, and the forecast is that
  extreme presentation bias precedes fade, not continuation.
- **Corpus parts combined:** N2 dual-population Algo Score (Morgue
  Tape, tallies verbatim, sum OURS, C16) + avoid stack A2/A9 + Tape
  tags. Side labels inherit the declared latest-quote limitation
  (C16) and the engine says so on its card.
- **Why new:** N2 publishes the bias as a transparency figure. No
  vendor reports both populations at all, and no corpus mechanism
  trades the gap itself as a forecaster. Tool 4 Flow Tape displays
  both scores; it makes no forecast from their difference.
- **Data route (e):** Tape prints and both score populations are
  computed live today in the Morgue Tape slice.
- **Grading (b, c, d, f):** Cohort ledgered at the close that
  completes the prints; graded at exactly +5 sessions, median and
  mean excess both published, all 20 names in the denominator
  including halted or delisted names at their last price. Prints,
  side and sweeps are one options-prints family (d). Proving state
  until 40 cohorts mature. This is a cohort fade forecast, never a
  short book: A16 killed shorting picked names after borrow, and the
  engine claims no tradable short.

## 4. Family Fracture — disagreement geometry forecasts the break in size

- **Forecast (a):** Each session, from the five evidence families'
  signed readings on SPY (price, options prints, modelled inventory,
  filings/positioning, distributional/volatility), publish a fracture
  score and a distributional forecast: predicted realised 5-session
  SPY range (high minus low) as a percentage, and P(|5-session SPY
  return| exceeds 1 expected move). No direction is forecast.
- **Mechanism:** The Second Opinion (tool 18) counts agreeing
  families. This engine inverts it: specific disagreement geometries
  are breakdown precursors. Price-family positive while inventory
  (GEX/flip) negative and prints one-sided is a leveraged-consensus
  state; the corpus shows shapes and weak internals forecast
  volatility while forecasting no direction (V4, 172 vs 2 cells), and
  that breadth forecasts volatility, not direction (T11 killed for
  direction). Fracture is the cross-family version of that fact:
  consensus can fail quietly (drift) or loudly (range expansion),
  and the geometry, not the count, separates them.
- **Corpus parts combined:** N3 evidence-family grouping + tool 18's
  family readings as inputs + V1/V4 volatility evidence + HAR
  realised-vol companion (AD-56) as the benchmark to beat.
- **Why new:** Every vendor consensus product in the corpus sums
  agreement. None models the pattern of disagreement as the signal.
  Tool 18 counts; tool 33 Regime Dial narrates state; neither issues
  a range forecast from fracture geometry.
- **Data route (e):** All five family readings are already produced
  daily by Map, Tape, Board and the volatility bench tools (26–28).
  The filings family is slow (13F quarterly) and is carried as its
  last reading with its age printed, per N4 absence discipline.
- **Grading (b, c, d, f):** Ledgered pre-open; graded at +5 sessions
  on range error vs the HAR-only benchmark and on breach-probability
  calibration. If fracture cannot beat HAR alone on range, it dies in
  public — that comparison is the falsifier. Families are the unit of
  counting throughout (d). Proving state until 100 sessions mature.

## 5. Mean–Median Split Forecaster — when a gate's winners stop carrying it

- **Forecast (a):** For each weekly Qualified Board cohort, publish
  before the cohort's 21 sessions run: predicted sign of the cohort's
  median SPY excess at 21d, and P(cohort mean exceeds cohort median
  by more than 2 points) — i.e., a forecast that the cohort's result
  will be right-tail-carried again, or will not.
- **Mechanism:** The Board gate's one positive result is a mean-only
  effect with negative medians at every horizon (C11: 21d mean
  +2.41% vs unqualified +0.52%, median SPY excess −1.16%). A gate
  whose mean and median disagree is a lottery-ticket machine, and
  the split itself varies: when qualifiers cluster in a few sectors,
  sit far above their 50-day (A3 stretched, an avoid), or qualify on
  thin leaf coverage, the tail thins. The engine forecasts the
  shape of the cohort outcome, which is the honest question the
  gate raises, instead of re-forecasting returns with a score proven
  not to rank them (Spearman ≈ −0.01 to −0.02, killed, unresurrected
  here).
- **Corpus parts combined:** Board gate cohorts (tool 3) + C11's
  full mean/median record + A3/A5 avoid measures as cohort-shape
  inputs + The Record's cohort grading.
- **Why new:** No vendor grades, let alone forecasts, the distributional
  shape of its own picks. Tools 2 and 3 report the split after it
  matures; this engine stakes a claim on the split in advance.
- **Data route (e):** Board cards and the Record ledger exist today;
  29 weekly cohorts of history (2026-04-08 to 2026-10-23) seed the
  base rates, with survivorship bias declared exactly as the source
  study declares it.
- **Grading (b, c, d, f):** Ledgered at cohort publication; graded at
  exactly +21 sessions; both calls scored, cohort kept whole. One
  price-family confirmation only (d): Board leaves span families,
  but the cohort-shape inputs are stamped per family and discounted.
  Proving state until 26 weekly cohorts mature.

## 6. Crowding Unwind Gauge — forecasting the exit, not the entry

- **Forecast (a):** Weekly, for QQQ and for the 20 most-held genome
  names in the desk's own book record: publish P(a drawdown of at
  least 2× the name's 21-session expected move within the next
  21 sessions that begins with a down day on rising down-volume) —
  an unwind-shaped drawdown, defined mechanically so grading needs
  no judgement — as a probability, plus the predicted largest
  5-session decline in % inside that window.
- **Mechanism:** Crowding is measured in the corpus, not theorised:
  about 55 sleeves long QQQ at 31% of gross, 20 groups / 46 sleeves
  with identical fills (AD-45). Identical positioning unwinds
  identically. The gauge combines position concentration (desk book),
  one-sided Tape flow (prints family), FINRA short-volume falling
  while price rises (the crowd is long and unhedged), and distance
  above the 50-day (A3). No single input forecasts; the joint state
  — crowded, unhedged, stretched — is the precursor geometry.
- **Corpus parts combined:** AD-45 crowding census + Tape flow +
  FINRA short volume (A11 context) + A3 stretch + F6's down-volume
  signature used in reverse (capitulation volume marks the unwind's
  start, not a buy).
- **Why new:** Vendors sell crowding as a sentiment gauge with no
  graded forecast attached. No corpus tool forecasts an unwind as a
  defined event. Tool 37 Correlation Web maps static co-movement;
  this forecasts the dynamic failure of a crowded state.
- **Data route (e):** Desk book and sleeve-fill records exist today
  (AD-45 was measured from them); Tape and FINRA routes exist.
  **UNMET (partial, e):** the desk book is internal, so the public
  version can publish the forecast and its grade but not the full
  position inputs; the engine is buildable now for the terminal's
  own record, and its public card must stamp the input it cannot
  show, per N4. If that stamp is judged disqualifying for a public
  tool, the engine still runs as an internal risk forecaster.
- **Grading (b, c, d, f):** Ledgered weekly before the window;
  graded at +21 sessions against the mechanical event definition;
  probability scored by Brier, decline by absolute error; all 21
  names stay in the denominator. Sleeve fills from 46 sleeves with
  identical fills count as one position family, never 46
  confirmations (d, applied to ourselves). Proving state until
  26 weekly cohorts mature.

## 7. Touch Lie Detector — the corrected touch-probability forecaster

- **Forecast (a):** For SPY and QQQ each session, for the ±0.5, ±1
  and ±1.5 expected-move bands: publish the predicted probability
  that price touches each band edge intraday within 1 and within
  5 sessions — a corrected number, issued against the vendor
  reflection model's number published beside it.
- **Mechanism:** The corpus killed the reflection formula
  `2N(·)` as calibrated: it overstates touch by 13–30 points and
  saturates near 100% for narrow bands; at ±1 EM it says 63.5%
  where realised is 32–33% on VIX-based EM and ~50% on HAR (AD-57).
  The engine inverts the kill: a touch model fitted on the realised
  side — HAR vol (AD-56, k≈0.88 holds 68%), intraday range
  distributions from the Opening Range and Gap-Fill studies (S1/S2),
  and GEX sign (amplification vs damping) — issues the honest touch
  curve. The forecast is a probability distribution over a defined
  event, the class the corpus grades best.
- **Corpus parts combined:** AD-57 kill record + AD-55/AD-56 band
  calibrations + Studies S1/S2 distributions + Map GEX sign.
- **Why new:** Tool 7 Expected Move Map publishes the band; no tool
  publishes a calibrated touch probability, and the vendor model
  that does is proven wrong in the corpus's own record. This is the
  only candidate that begins life with a beaten benchmark already
  measured.
- **Data route (e):** Daily bars and chain-derived EM exist today;
  intraday touch grading needs SIP intraday bars, which the Morgue
  already fetches for gap/ORB (C2, Fix B path).
- **Grading (b, c, d, f):** Ledgered pre-open daily; graded at +1
  and +5 sessions on touch/no-touch per band; calibration curves
  published against the reflection model's scores on the same days —
  the engine must beat the dead model's Brier score or join it in
  the Graveyard (tool 50). All inputs are price + modelled-inventory
  families, counted as two, not five (d). Proving state until 100
  sessions mature.

## 8. Non-Fill Forecaster — the trades that never happen predict the move

- **Forecast (a):** For every pullback plan the desk/terminal
  publishes (name, limit level, session): publish P(plan does not
  fill within 5 sessions) before the first session opens, and for
  the predicted-non-fill cohort, a distributional forecast: median
  5-session return of the non-filled names will exceed that of the
  filled names by a stated number of points.
- **Mechanism:** Filled pullback plans beat other plan forms
  (+0.231R / +0.134R, S17/X4) but only about one-third fill — and
  the source itself names fill selection bias as part of the
  mechanism. Inversion: non-fill is information. A name that never
  pulls back to the plan is running away; a name that fills
  instantly through the level is falling, not dipping. The plan
  book is a set of resting hypotheses about paths, and the path
  taken (no-touch, touch-and-hold, touch-and-blow-through) is a
  three-state forecaster nobody in the corpus grades as one.
- **Corpus parts combined:** S17/X4 plan evidence + F3 pullback
  depth vs own norm (depth states define the touch-and-hold band) +
  Odds Cards replay machinery (tool 46) for base rates.
- **Why new:** Tool 46 publishes historical odds for setup families;
  vendors publish entry signals. Neither treats the unexecuted plan
  as the forecast. The corpus's execution evidence (X family: one
  bar late costs $502/trade) says path matters more than signal;
  this engine is built entirely on path.
- **Data route (e):** Published plan levels and SIP bars exist
  today. **UNMET (partial, a/e):** the live plan stream is thin
  (the live real-support record on record is n=88 plans); the engine
  starts on the terminal's published plan cohorts and its first
  months are accrual, stamped as such. The forecast form is exact
  from day one; the cohort size is the unmet part.
- **Grading (b, c, d, f):** Every plan ledgered at publication,
  filled or not — non-fills are the denominator, not an exclusion.
  Graded at +5 sessions: fill-probability Brier, and the cohort
  median-spread call scored as stated. One price family (d).
  Proving state until 200 plans mature.

## 9. Avoid-Stack Failure Alarm — forecasting when the best layer stops working

- **Forecast (a):** Monthly, publish P(the avoid stack's bottom-tenth
  cohort — crashed/volatile/illiquid small caps, A1 — will OUTPERFORM
  the genome-universe median over the next 21 sessions), as a
  probability, with a binary regime call: vetoes-on vs vetoes-failing.
- **Mechanism:** The avoid stack is the corpus's most robust layer
  (A1 grade A; A2, A3, A5 grade A). Robust layers fail in a specific
  way: violently and at regime turns, when the crashed names become
  the short-covering fuel (the same reversal that T2, grade A, finds
  in the deepest drawdown tercile). The alarm watches the stack's
  own vital signs — the veto cohort's relative strength inflecting,
  fear-personality names (S9) leading, short volume collapsing in
  the cohort — and forecasts the veto layer's failure window. A
  system that forecasts its own best defence's death is worth more
  than a tenth buy signal.
- **Corpus parts combined:** A1–A15 avoid stack + T2 stress reversal
  + S9 fear personality (grade C, used as an input, never quoted as
  a survivor) + FINRA short volume.
- **Why new:** Tools 44 (Router) and 50 (Graveyard) apply and bury
  vetoes. Nothing forecasts the veto regime itself. Vendors never
  forecast the failure of their own flagship filter.
- **Data route (e):** Daily bars over the genome universe and the
  avoid cohorts are computed today for tools 8/44. Short volume
  route is the declared frail one (FINRA 12-month compliant window,
  AD-11/D7); the engine runs on the bars-based inputs if that route
  lapses, and stamps the loss.
- **Grading (b, c, d, f):** Ledgered monthly; graded at +21 sessions
  on the stated cohort comparison, full cohort in the denominator.
  Probability scored by Brier against the base rate (vetoes failing
  is rare; beating the base rate is the bar). Inputs span price and
  positioning families, counted as two (d). Proving state until
  18 monthly cohorts mature — slow by design, and the card says so.

## 10. Pin-Failure Forecaster — when expiration gravity loses

- **Forecast (a):** On each weekly expiration morning, for SPY, QQQ
  and IWM: publish P(close is more than 0.5 expected moves from the
  published pin level) and the predicted absolute close-to-pin
  distance in %. A pin that holds is the null; the engine forecasts
  the failure of the null.
- **Mechanism:** Tool 30 Expiry Pin Watch presents open-interest
  gravitation as a reading; its forecasting value is untested in
  the record. Inversion asks what breaks gravity: net-GEX sign at
  the pin strike (negative gamma at the pin means hedging pushes
  away from it), a macro-calendar event inside the session
  (tool 34's calendar: Fed, CPI, auctions), a gap that opens beyond
  the pin's strike neighbourhood, and pin-level OI concentration
  that is small relative to neighbouring strikes (a weak pin).
  Each is a named failure mode, combined as one pre-registered
  score, not tuned per week.
- **Corpus parts combined:** Tool 30 pin construction + Map GEX by
  strike (tool 54 Gamma Ladder data) + Week Ahead calendar +
  gap evidence (S15).
- **Why new:** Pin products across the vendor corpus present the
  level as the forecast. No corpus mechanism forecasts pin failure
  probability or expected miss distance. It ascends tool 30 rather
  than duplicating it: tool 30 reads, this stakes.
- **Data route (e):** Chain snapshots the Pin Watch already uses;
  calendar on record through 2027-12-31. Expiries are weekly, so
  cohorts accrue at ~3 index forecasts per week.
- **Grading (b, c, d, f):** Ledgered on expiration morning before
  the open; graded at that close. Distance error and Brier on the
  breach call, published against the naive always-holds baseline.
  Chain-derived inputs are one modelled-inventory family (d); the
  calendar is a second. Proving state until 40 expirations per
  index mature.

## 11. Silence Forecaster — absence of signal as the signal

- **Forecast (a):** Each session, for the Golden Sweep Wire's tape:
  publish the running drought length (sessions since the last
  golden sweep print; on record: 0 prints in 2 recorded sessions,
  decision date 2026-12-08) and a forecast: P(at least one golden
  sweep print occurs in the next 5 sessions), plus, for SPY,
  P(next 5-session realised range exceeds the trailing 60-session
  median range) conditional on the drought being in its longest
  decile.
- **Mechanism:** The corpus's fail-closed law (N4) treats absence as
  a state, never a zero. This engine treats absence as data: large,
  aggressive, defined-threshold prints cluster in stressed or
  informed tape; a long drought is a compression state, and
  compression states end in range expansion ( consistent with V3:
  VIX backwardation precedes bigger moves; V1: vol is forecastable
  from its own past). The second forecast is deliberately
  distributional, the corpus's strong class.
- **Corpus parts combined:** Tool 5 Golden Sweep Wire tape and its
  proving record + Tape print stream + V1/V3 volatility evidence.
- **Why new:** Every flow vendor forecasts from prints that exist.
  No corpus mechanism forecasts from a defined print's continued
  non-existence, and none grades a drought. Tool 5 counts toward a
  proving decision; it issues no forecast.
- **Data route (e):** The Tape stream runs today; the drought is
  computable from its ledger from day one.
- **Grading (b, c, d, f):** Ledgered daily; both probabilities
  graded at +5 sessions, Brier-scored, drought-decile claim graded
  only on days it is actually made (the days are ledgered, so the
  denominator cannot be gamed). One prints family plus one
  volatility family (d). Proving state until 100 sessions mature.
  **Honest limit, stated on the card:** if golden prints stay at
  zero, the first forecast degenerates to a base-rate claim and the
  engine must say so — a forecaster of a never-occurring event is
  unfalsifiable in practice, and the December 8 proving decision
  governs whether this engine lives.

## 12. Consensus Autopsy — forecasting which Grade-A cells die next

- **Forecast (a):** Quarterly, rank the 63 Grade-A cells by predicted
  probability of failing the next pre-registered replication
  (demotion or non-replication), publishing the full ranked list and
  the predicted count of failures (a number). Graded when the next
  rerun lands: rank correlation of predicted vs actual failure, and
  count error.
- **Mechanism:** The Factory's rerun is the corpus's cleanest
  contradiction handling (C12): 564 of 1,217 promotions died under a
  rule written before the run. The autopsy reads the corpses:
  cells died at different rates by family, horizon, stretch
  consistency and after-cost margin. Those death covariates,
  measured on run 1 → run 2, are applied to the surviving 63. This
  is Candidate 1 (Half-Life Clock) at the replication timescale and
  for the Factory specifically; the two are kept separate because
  their horizons, data and grading events differ, and merging them
  would blur both falsifiers.
- **Corpus parts combined:** Factory run 1 and rerun records in full
  (N9) + Grade-A Board (tool 42) + N3 family labels + Horizon Grades
  (tool 48) horizon data.
- **Why new:** Tool 42 publishes the survivors; tool 45 Promoted Book
  tracks decay state as observed. No mechanism predicts the next
  replication's casualty list in advance. The Factory grades
  forecasters; this forecasts the grader's next verdict.
- **Data route (e):** Both run records exist today and are
  sha-pinned in the corpus. **UNMET (partial, c):** grading waits on
  the next pre-registered rerun, whose date is not on record; until
  a rerun is scheduled, the quarterly lists ledger and accrue but
  cannot mature. The engine's first act is to ledger its ranking
  now, against whenever the rerun runs, under the rerun's own rule.
- **Grading (b, c, d, f):** Ledgered quarterly, before any rerun is
  announced for that cycle; graded solely by the rerun's published
  rule, all 63 cells in the denominator. Family is a covariate, not
  a confirmation count (d). Proving state until two reruns grade it.

---

## Coverage note

Twelve candidates, all from the inversion lens. Strongest on the
commission's ranking inputs: #7 Touch Lie Detector (a beaten benchmark
already measured, sharpest falsifier), #2 Wall-Break (daily cohorts,
asymmetric young record), #1 Half-Life Clock (the corpus's dominant
empirical fact — most signals die — turned into the forecast), #4
Family Fracture (aimed at the distributional class the corpus
validates). Weakest / most conditional: #11 Silence (degenerates if
the print never occurs), #12 Consensus Autopsy (grading hostage to a
rerun schedule), #6 Crowding Unwind (one input is internal-only).
No candidate resurrects a killed directional signal as a buy; the
three that touch direction (#3, #5, #9) forecast cohort fades and
outcome shapes, which is where the corpus's surviving evidence
actually lives.
