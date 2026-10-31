# Forecast-30 candidates — Lens: CROSS-FAMILY SYNTHESIS (N3 inverted)

Date: 2026-10-28. Lens rule: the forecast must exist only in the interaction of
evidence families that no single vendor combines. Families per N3 / inventory
§1: Price, Options prints, Modelled inventory (chain-derived), Filings/
positioning, Events/calendar, Cross-sectional, Distributional/vol. Correlated
signals inside one family count once; every candidate below multiplies at
least two genuinely independent families, and its grading tests the
interaction term against each family alone (an engine whose interaction adds
nothing over its parts dies on its own record).

Honesty law applied to every candidate: (a) falsifiable forecast stated with
quantity, horizon, direction or distribution; (b) every forecast ledgered
append-only before the horizon opens (N1); (c) graded at fixed horizons,
losers kept in the denominator; (d) agreement discounted by evidence family;
(e) data route named and on record today, or accruing from machinery already
running; (f) ships under proving state until its own forward record matures.
Any requirement a candidate cannot yet meet is marked inline.

Common grading protocol (stated once, applies to all): forecast written to
the Morgue ledger before the horizon opens; fixed horizons as stated per
candidate (no horizon shopping); grade = stated quantity vs realised value
from the same data route; report hit rate / mean error with Wilson or
bootstrap intervals, the full denominator including no-fire and expired
forecasts, and the two baselines (each parent family alone, and the
unconditional base rate). Kill rule pre-registered per candidate.

---

## XF-1. Gamma-Pressure Earnings Trap

- **Forecast (falsifiable):** For SPY/QQQ/IWM constituents reporting earnings
  within 5 sessions while index net GEX is negative: the name's absolute
  earnings-day move will exceed its priced expected move (tool 35 figure) in
  at least 55% of cases, and the median |realised| / priced-EM ratio will be
  ≥ 1.10. Horizon: the earnings session. Direction of the move is NOT
  forecast (the corpus killed direction; this is a distributional claim).
- **Mechanism:** Negative dealer gamma amplifies hedging flows into any
  shock; an earnings print is the largest scheduled per-name shock. Neither
  family alone makes this claim: gamma suites never condition on the
  earnings calendar, earnings tools never condition on dealer inventory.
- **Corpus parts combined:** Modelled inventory (SpotGamma construction,
  Morgue `map_gex`, tools 1/54) × Events (earnings calendar + priced EM,
  tool 35) × Distributional (AD-55/56 band calibration method as the grading
  yardstick).
- **Why new:** No vendor in the corpus crosses chain inventory with the
  earnings calendar; the interaction (amplifier × scheduled shock) is the
  forecast, not either input.
- **Data route:** Map cards + chain snapshots on record (inventory §4.2);
  earnings calendar on record (§4.4). Exists today at index level; per-name
  GEX accrues from the chain archive lane already running.
- **Grading:** Per event, ledgered pre-report; ratio distribution vs the
  same ratio for positive-GEX earnings events (control arm ledgered too).
  Kill: after 60 events, exceedance rate CI includes 50% or median ratio
  < 1.0.

## XF-2. Silent Accumulation (dark × insider silence × 13F drift)

- **Forecast:** Names where (i) constituent DIX / dark pressure is in the top
  quintile, (ii) insider summary shows zero sells in the trailing record
  window, and (iii) 13F holder count or aggregate position rose between the
  two quarters on record, will show a 21-session SPY-excess return
  distribution whose median is > 0 and whose top-quartile frequency exceeds
  the unconditional rate by ≥ 5 points. Horizon: 21 sessions from ledger date.
- **Mechanism:** Three independent accumulation footprints that leave no
  price trace: off-exchange buying, insiders NOT distributing into strength,
  and institutions building between filings. Silence is the signal in family
  two; no vendor treats an absence as a reading.
- **Corpus parts combined:** Modelled inventory (constituent DIX, N6) ×
  Filings (insider summaries, tool 21; 13F sets, tool 40) — two distinct
  filings sub-routes — with Price used only for grading, never as an input.
- **Why new:** InsiderFinance scores prints; SqueezeMetrics scores dark;
  13F trackers report drift. Nobody requires all three to agree and grades
  the conjunction. The conjunction is rare by construction, which is the
  point: family-discounted consensus (N3) with three truly separate
  primitives.
- **Data route:** DIX live-computed (501/503 names, §4.3/§1.3); insider
  summaries on record 2026-10-26 (43/50 names — coverage gap named);
  13F two quarters on record (8,857 / 8,871 filers). **Partial (e):** insider
  summaries carry counts/values, not trader identity or dates, so "silence"
  is measured at summary grain only; the candidate is marked accordingly
  and cannot sharpen until the filings lane deepens.
- **Grading:** Cohort ledgered at each 13F publication + weekly DIX refresh;
  21d median and top-quartile rate vs all-names baseline and vs each single
  condition alone. Kill: after 100 cohort names, interaction adds < 2 points
  over the best single condition.

## XF-3. Intake-Bias Reversal (dual-population flow × short volume)

- **Forecast:** Names where the buys-only Algo Score is bullish but the
  all-prints Algo Score (N2 dual population) is neutral-or-bearish — i.e.
  the intake bias itself is doing the bullishness — AND FINRA short volume
  is in its top tercile, will underperform SPY over the next 5 sessions by
  a mean of ≥ 1.0 point. This is an avoid-side forecast, the corpus's
  strongest direction (A11, grade B).
- **Mechanism:** The vendor intake hides sell prints; when the hidden
  population disagrees and shorts are simultaneously active, the visible
  "bullish flow" is distribution dressed as accumulation.
- **Corpus parts combined:** Options prints (dual-population Algo Score,
  N2 — genuinely novel) × Filings/positioning (FINRA short volume, A11) ×
  Cross-sectional tercile ranking.
- **Why new:** N2's bias figure exists in no vendor product; crossing it
  with short volume turns a measurement of vendor dishonesty into a
  forecast. No teardown combines tape intake bias with short data.
- **Data route:** Tape cards accruing daily (§4.2); FINRA short-volume
  history 2018-08→2026-10 in the reset studies + exchange republication
  route for SI (§4.3). **Caveat (e):** the Short Volume Ledger tool itself
  has stored 0 days; the engine must read the study/republication route,
  not the empty ledger, and says so on its card.
- **Grading:** 5d SPY-excess mean, ledgered at fire; baselines = bias-only
  cohort and short-volume-only cohort. Kill: after 80 fires, interaction
  mean ≥ 0 or no better than short-volume alone.

## XF-4. Wall–Breadth Fracture (geometry × deterioration → vol, not direction)

- **Forecast:** On sessions where the SPY flip sits within 0.5% of spot
  (wall geometry: price balanced on the dealer-inventory knife edge) AND
  breadth (% above 50-day) has fallen for 3+ consecutive sessions, the next
  5 sessions' realised SPY range will exceed the HAR 68% band's upper edge
  in ≥ 45% of cases (vs ~16% unconditional above a 68% band's top).
  Pure size forecast; no direction claimed.
- **Mechanism:** Breadth deterioration alone was killed for direction (T11)
  but survives for volatility (V4: weak internals forecast vol). A nearby
  flip removes the dealer's stabilising flow exactly when the internals
  are rotting: the interaction predicts fracture size, not side.
- **Corpus parts combined:** Modelled inventory (walls/flip, tools 1/14) ×
  Price-internals (breadth, tool 31 — re-aimed from its killed directional
  use to its surviving vol use) × Distributional (HAR band, AD-56,
  validated calibration).
- **Why new:** Gamma vendors publish geometry statically; breadth tools
  publish health statically. Conditioning a calibrated vol band on flip
  proximity × breadth trend is in no teardown.
- **Data route:** Map cards daily; breadth from shipped daily history
  (1,833 × 399 sessions); HAR from SPY daily 2010-2026 on record. Exists
  today.
- **Grading:** Band-exceedance rate at 5d, ledgered pre-session; control =
  flip-proximity alone and breadth-trend alone. Kill: after 40 fires,
  exceedance CI includes the unconditional rate.

## XF-5. Hot Tape into the Print (flow heat × earnings proximity fade)

- **Forecast:** Small/mid names whose InsiderFinance Heat Score fires in
  the top bucket during the 2 sessions immediately before their earnings
  report will, on average, give back the pre-report run: mean 5-session
  post-report SPY-excess ≤ −2.0 points, extending A12 (small-cap earnings
  gaps fade, grade B) with a flow-heat interaction the A12 study never had.
- **Mechanism:** A12 says the gap fades; heat says someone is paying up
  into the print. Paying up into a scheduled binary event in names whose
  gaps historically fade is the crowd buying the ticket at the top price.
- **Corpus parts combined:** Options prints (Heat Score, 8 live components,
  fixture-proven) × Events (earnings calendar, tool 35) × Cross-sectional
  (A12 avoid evidence as prior, not as input).
- **Why new:** Flow vendors do not condition on days-to-earnings;
  earnings tools do not read print heat. The 2-session window is the
  invention: heat far from a catalyst is a different animal and is
  explicitly out of scope.
- **Data route:** Tape cards accruing; earnings calendar on record.
  Per-name tape coverage is the binding constraint (tape record is
  index-heavy today) — fires will be sparse at first; sparsity is
  published, not papered over.
- **Grading:** 5d post-report excess, ledgered at heat fire (pre-report);
  baseline = A12 cohort without the heat condition. Kill: after 50 fires,
  heat-conditioned mean is not worse than the A12 baseline.

## XF-6. Fear-Day Triangulation (the interaction is the test)

- **Forecast:** On fear days (tool 16 definition), uptrend names that
  satisfy ALL THREE of: pullback depth in the deepest quintile vs the
  stock's own norm (F3), gap_share in the top tercile (S15), and zero
  insider sells on record — will beat the fear-day random-entry control
  (T1: any uptrend name on a fear day, +0.29 to +0.36R) by ≥ +0.10R mean
  at the 20-session horizon. If the triple conjunction does not beat the
  single best component (F3 alone), the engine's own pre-registered
  verdict is that triangulation adds nothing and it retires itself.
- **Mechanism:** T1 proved the lift belongs to the day, not the setup.
  This engine is the honest counter-test: can three independent families
  (price-norm, tape-gap, filings-silence) carve selection out of a pure
  timing effect? It is designed to be able to fail, publicly.
- **Corpus parts combined:** Price (F3, N10 survivor) × Price/tape hybrid
  gap_share (S15, grade B) × Filings (insider silence) — with the family
  discount enforced: F3 and gap_share share bar data, so they count as
  1.5 families at most in the card's own accounting, and the card says so.
- **Why new:** Every vendor stacks confirmations and calls the stack
  stronger (killed, S19, for price-only stacks). A cross-family stack
  with a pre-registered self-retirement rule and a random-entry control
  is the opposite product.
- **Data route:** DEEP bars + shipped daily history; fear-day record is
  thin locally (1 qualifying day in the shipped window) so accrual is
  slow — marked: grading horizon is event-driven, likely quarters, and
  the card publishes fires-to-date. **(f) note:** proving state will be
  long; that is stated, not hidden.
- **Grading:** R-based, same exits as the picker replay for comparability;
  controls = random fear-day entries and F3-only cohort, both ledgered.

## XF-7. Pin-or-Escape (expiry geometry × gamma sign × VRP)

- **Forecast:** Into weekly expiry, when spot opens within 0.3% of the
  OI-gravitation pin level AND net GEX is positive AND VRP is in its
  bottom half, SPY will close within ±0.25% of the pin in ≥ 40% of weeks;
  when net GEX is negative (same pin proximity), closes within that band
  fall to ≤ 20% — the pin holds only when dealers are long gamma and
  implied vol is not paying for escape. Distribution forecast, both arms
  ledgered.
- **Mechanism:** Pin Watch (tool 30) publishes the level untested. Pinning
  is a dealer-hedging phenomenon, so its success must be conditional on
  the sign of the dealer's book and on whether vol is priced for a move;
  the unconditional pin claim is exactly the kind of claim this programme
  exists to grade.
- **Corpus parts combined:** Modelled inventory (pin + GEX, tools 30/1) ×
  Distributional (VRP, T3/V2 evidence) — two families, one interaction.
- **Why new:** No vendor conditions its own pin level on its own gamma
  sign; the level is sold as unconditional. The conditional split is the
  engine.
- **Data route:** Chain snapshots + Map cards on record; VRP from the
  SPY/VIX daily series on record (2010-2026). Exists today.
- **Grading:** Weekly, both arms, close-distance distribution; baseline =
  unconditional pin-hit rate. Kill: after 52 weeks, the two arms' rates
  are statistically indistinguishable.

## XF-8. Crowded Silence Breaks Louder (13F crowding × tape absence × short rise → tail size)

- **Forecast:** Names with rising 13F crowding (holder count up QoQ),
  NO tape-heat fire in the trailing 20 sessions, and rising short volume
  will show a fatter left tail over the next 21 sessions: their 10th-
  percentile 21d return will be at least 3 points worse than matched
  crowded names WITH tape-heat presence. Tail forecast, not mean
  direction.
- **Mechanism:** Crowding with live sponsorship (heat) is supported;
  crowding abandoned by the tape while shorts build is a held-up price
  with the buyers gone — the unwind, when it comes, is a size event.
  Downside precursors forecasting tail size is a corpus-supported claim
  shape (AD-30, grade C, upgraded here by crossing three families).
- **Corpus parts combined:** Filings (13F drift, tool 40) × Options
  prints (heat ABSENCE as a reading — the negative space of tool 4) ×
  Positioning (short volume trend).
- **Why new:** Every flow product reads presence. Reading a structured
  absence (crowded + unsponsored + shorted) as the forecast is a
  combination no teardown contains.
- **Data route:** 13F two quarters on record; tape cards accruing;
  short-volume study route (§4.3). **Partial (e):** with only two 13F
  quarters, crowding drift has exactly one observation per name today;
  the engine ledgers its first cohort now and sharpens as quarters accrue.
- **Grading:** 21d return deciles per cohort vs matched control; kill
  after 2 quarterly cohorts if the tail gap < 1 point.

## XF-9. Squeeze Weather (SI gate × IV repricing × dark pressure → move size)

- **Forecast:** Names passing the Squeeze v6 gate (SI ≥ 15%) whose IV
  percentile vs own history rises ≥ 20 points in 5 sessions while dark
  pressure (DIX-style per-name reading) is above its median will realise
  a 5-session absolute move at least 1.3× their HAR-implied move in
  ≥ 50% of cases. Size only; squeeze direction is explicitly not claimed.
- **Mechanism:** The squeeze formula (vendor-verbatim, N11) finds the
  fuel. IV repricing says the options market has started paying for the
  fire; dark pressure says off-exchange flow is leaning. Fuel alone sat
  untested; fuel × repricing × flow is a combustion forecast.
- **Corpus parts combined:** Positioning (Squeeze Score v6, tool 15) ×
  Distributional (IV percentile + HAR, tools 26/premium meter) ×
  Modelled inventory (per-name dark pressure, tool 24 building).
- **Why new:** Tapeboard's score is static and self-contained; nobody
  gates it on the options market's own repricing and dark flow jointly.
- **Data route:** SI via exchange republication (frailest route, named);
  chain snapshots accruing. **Cannot yet fully meet (e):** the IV ledger
  stopped 2026-10-14 with ≤ 12 readings per name (§4.5 gap 7), so IV
  percentile is unreliable until the ledger resumes and accrues ~60
  readings. Candidate is submitted as CONDITIONAL: it activates only
  when the IV ledger restarts; until then it ledgers squeeze-gate
  membership alone so the cohort history is not lost.
- **Grading:** |realised| / HAR-implied ratio distribution at 5d;
  baseline = gate-only cohort. Kill: after 60 fires, exceedance CI
  includes the gate-only rate.

## XF-10. Sponsored Reset (RESET composite × filings sponsorship × leader gate)

- **Forecast:** Deep-reset names (35-80% off high) matching the N9 RESET
  composite on a fear day AND showing institutional sponsorship (13F
  holder count not falling, or an insider buy on record) while SPY is
  above its rising 200-day (T4 gate) will post a mean 20-session
  SPY-excess ≥ +2.0 points, vs the N9 composite's fear-day record
  (IC +0.053/+0.028) achieved without any filings condition.
- **Mechanism:** N9's components (laggard RS, down-volume capitulation)
  describe a washed-out name; sponsorship separates washed-out-and-held
  from washed-out-and-abandoned (F4: idiosyncratic declines persist —
  the avoid twin). The T4 gate keeps the cohort out of the regime where
  leader setups lose (grade B).
- **Corpus parts combined:** Price/cross-sectional (N9 RESET + F7/F6) ×
  Filings (13F direction + insider buys) × Price-regime (T4) — filings
  is the genuinely new family against N9's price-only composite.
- **Why new:** The RESET composite is price-only by construction in the
  corpus. Adding a filings sponsorship veto/confirmation and grading
  whether it sharpens the survivor is a new engine, not a rename of
  tool 49 (Survivors Wire publishes the survivors; it does not cross
  them with filings or gate them).
- **Data route:** DEEP bars; 13F two quarters; insider summaries.
  **Partial (e):** insider summaries cannot identify cluster buying
  (named on tool 21); sponsorship uses holder-count direction and any-
  buy flags at summary grain only.
- **Grading:** 20d excess mean + IC, ledgered per fear-day cohort;
  baselines = N9 alone, N9 + T4 without filings. Kill: after 3 fear-day
  cohorts, filings condition adds < 0.5 points of mean excess.

## XF-11. Band-Trust Regime (wall respect record × HAR calibration, live-conditioned)

- **Forecast:** The HAR 68% band's realised coverage over the next 21
  sessions will be ≥ 65% in weeks when the trailing wall record shows
  flip respected (tool 14) AND net GEX positive, and ≤ 55% when flip
  has been broken twice in the trailing 20 wall tests with net GEX
  negative. A forecast about the reliability of another forecast —
  graded on coverage, the corpus's best-validated quantity (AD-56).
- **Mechanism:** Bands assume a vol regime; dealer positioning is a
  physical stabiliser/destabiliser of realised vol. The wall record is
  young (6 graded tests) but it is a live behavioural read on whether
  the stabiliser is working, which historical vol cannot see.
- **Corpus parts combined:** Distributional (HAR band) × Modelled
  inventory (wall/flip respect record, N8 harness) — meta-forecast
  crossing.
- **Why new:** Calibration studies condition on vol's own past only.
  Conditioning a band's trust on the live positioning record is a
  second-order forecast no vendor ships (vendors sell the band and the
  map side by side, never multiplied).
- **Data route:** Map/wall ledger on record (9 cards, 6 graded, accruing
  daily); SPY daily history. Exists today; wall record thinness is
  printed on every forecast until 60 tests accrue.
- **Grading:** Rolling 21-session coverage per regime arm, ledgered
  weekly. Kill: after 26 weekly forecasts per arm, coverage gap < 5
  points.

## XF-12. Insider–Flow Divergence (the disagreement engine)

- **Forecast:** Names where insider summaries show heavy net selling
  (sells ≥ 10× buys by count across the record) while options Heat is
  simultaneously in its top bucket will underperform SPY by a mean
  ≥ 1.5 points over 21 sessions; the reverse divergence (insider buys
  present, heat absent/cold) will outperform by ≥ 1.0 point. Both arms
  are forecasts; agreement cases are ledgered as the control cohort.
- **Mechanism:** When the two best-informed families disagree, one is
  wrong in a specific way: insiders sell into manufactured flow heat
  (distribution), or accumulate quietly before flow notices
  (sponsorship). The corpus never grades a disagreement; every vendor
  product grades only its own family's agreement with itself.
- **Corpus parts combined:** Filings (insider summaries, 18 buys vs 326
  sells across the record — the asymmetry is the base rate the forecast
  must beat) × Options prints (Heat Score).
- **Why new:** This is N3 read backwards: instead of discounting
  correlated agreement, it prices INDEPENDENT DISAGREEMENT as the
  signal. No teardown contains a divergence engine.
- **Data route:** Insider summaries on record (43/50 names); tape cards
  accruing. **Partial (e):** per-name tape coverage is index-heavy
  today, so divergence fires on single names accrue slowly; index-
  constituent names first.
- **Grading:** 21d excess per arm vs agreement control; kill after 60
  fires per arm if either arm's mean sign is wrong.

---

## Lens summary

12 candidates, all cross-family by construction (minimum 2 independent
families; median 3). Family-pair coverage: inventory×events (XF-1, XF-7),
dark×filings×13F (XF-2), prints×short (XF-3, XF-12), inventory×breadth×vol
(XF-4, XF-11), prints×events (XF-5), price×tape×filings (XF-6, XF-10),
13F×prints-absence×short (XF-8), squeeze×IV×dark (XF-9).
Honesty-law exceptions, named not hidden: XF-9 cannot meet (e) until the
IV ledger resumes (conditional activation stated); XF-2, XF-8, XF-10 meet
(e) at summary grain only (insider/13F record limits stated inline);
XF-6's proving state will be long because fear days are rare in the
shipped window. All 12 ship under proving state (f); none duplicates a
tool in THE-70-TOOLS.md (nearest neighbours — Wall Check, Pin Watch,
Squeeze Watch, Survivors Wire, Second Opinion — publish readings or
single-family cohorts; every candidate here forecasts only from an
interaction those tools do not compute).
