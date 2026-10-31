# Forecast-30 Candidates — Lens: TIME, SEQUENCE AND PATH

Date: 2026-10-28. Lens rule: forecast from order, rhythm and path, not levels.
Grounding: `forecast30-inventory.md` (verdicts, survivors, kills, data-in-hand §4),
03 (C1–C18, N1–N12), THE-70-TOOLS.md. No candidate duplicates a built tool:
where a tool already labels, describes or grades (51/52 Strat, 11/12 Studies panes,
14 Wall Check, 20 State Analogue, 32 Sector Rotation, 43 Fear-Day Forecaster),
the candidate adds a ledgered *forward sequence forecast* none of them makes.
Honesty law applied per candidate: (a) falsifiable forecast, (b) ledger before
horizon (N1), (c) fixed-horizon grading, losers in denominator, (d) N3 family
discounting, (e) data route on record today or accruing from running machinery,
(f) proving state until its own forward record matures. Exceptions are marked
UNMET / PARTIAL with the exact letter. Corpus prior stated once for all: nothing
has a validated directional edge; picker replay passed nothing; textbook
patterns, breadth-as-direction (T11), calendar effects (T10) and stacked
confirmations (S19) are killed — no candidate resurrects them unmarked.

---

## T1. Strat Grammar Engine — label-sequence n-grams, not single labels

- **Forecast (a):** At each close, for SPY/QQQ/IWM and the sector ETFs the Strat
  Scanner already labels, ledger the trailing 5-session TheStrat label sequence
  (e.g. 2U–2D–1–2U–3) and publish: P(SPY-equivalent ETF return over next 5
  sessions > 0), the median and 25/75pct of that 5-session return, conditional
  on that exact sequence (falling back to 4- then 3-grams at a printed minimum
  n). Graded at exactly +5 sessions.
- **Mechanism:** Tools 51/52 label bars and fire named combos; nobody in the
  corpus tests *order* — whether a sequence carries information its constituent
  labels do not. A grammar (transition counts with shrinkage to the shorter
  suffix) is the sequence-native form. Prior is hostile and stated: single
  patterns are killed (S20/AD-04, patterns fire on random walks at real rates),
  so the engine must beat two controls or die: (i) the same labels shuffled in
  time, (ii) the last-label-only forecast. That shuffle control is built into
  grading, not optional.
- **Corpus parts:** thestrat teardown (3,615 entries, vendor-claim-only, zero
  backing — inventory §1.1); Strat Scanner replica (21/21 fixture tests);
  Forecast Factory law-check/pre-registered replication discipline (N9);
  ledger (N1).
- **Why new:** Largest extraction in the corpus has never had a single forward
  test; this is a test of sequence grammar, not a re-presentation of labels or
  combos (52 fires discrete named combos only, makes no probabilistic forecast).
- **Data route (e):** Daily bars on record: shipped 1,833 names × 399 sessions
  and DEEP 2016–2026 (6,385 names incl. delisted) for grammar estimation;
  labels computable by the shipped scanner. Forward ledger accrues from the
  daily cycle already running.
- **Grading (b,c,d):** Ledger-before-close-of-horizon; Brier score and median
  error vs the two controls above, per ETF and pooled; all sequences ledgered
  stay in the denominator, including rare n-grams graded as a pooled tail.
  One price family only — no confirmation counted from any other price tool.

## T2. Sessions-Since Clock — event-clock hazard atlas

- **Forecast (a):** For each defined event (fear day per tool 16's definition,
  first tag of own-norm pullback depth extreme, earnings day, gap ≥1× own norm,
  wall break on a Map card), ledger at event close: the hazard curve
  h(k) = P(the name/index first closes back above its event-day high, for
  losers: below event-day low) at each sessions-since k = 1…21, plus median
  sessions-to-resolution. One curve per event instance, graded session by
  session to +21 or resolution, whichever first.
- **Mechanism:** The corpus grades almost everything in calendar horizons
  (1/5/21) and found edges decay in 1–5 sessions (E3/X family) and the best
  horizon from next open is ~60 sessions — but never made *elapsed sessions
  since the event* the variable. Duration dependence (hazard rising/falling
  with k) is a different, falsifiable claim than a horizon mean.
- **Corpus parts:** Fear-day definition and T1 timing lift (B, shared with
  random entries — the clock must therefore forecast *timing*, never claim the
  lift as selection); F3 own-norm pullback depth (N10, lead survivor);
  Odds Cards' replay distributions (tool 46) as the historical prior shape.
- **Why new:** No vendor or tool publishes a sessions-since hazard; tools 11–13
  publish outcome distributions by size/weekday, 46 publishes per-family odds —
  none conditioned on elapsed-since-event as a live, per-instance forecast.
- **Data route (e):** DEEP + shipped daily bars; earnings dates on record
  (with the D5 winter-date caveat); Map cards (9 on record) for the wall-break
  event class only — that class is PARTIAL (e): thin until map cards accrue.
- **Grading (b,c,d):** Each ledgered curve scored by log-loss per k against the
  unconditional historical hazard for that event class; unresolved-at-21 stays
  in the denominator as censored, never dropped. Price family = 1.

## T3. Family Ignition Order — which family lights up first

- **Forecast (a):** On any session where at least two evidence families newly
  trigger for SPY/QQQ/IWM or a Board name (families per N3: price, options
  prints, chain inventory, filings/positioning, events), ledger the observed
  ignition *order* (e.g. prints → price → chain) and publish, for the modal
  historical orders, P(index 5-session return > 0) and its median, conditional
  on today's order. Forecast is issued only on multi-family ignition days;
  abstention days are ledgered as abstentions.
- **Mechanism:** Every corpus mechanism asks *how much* a family says; none
  asks whether the *sequence* in which families arrive carries the signal —
  informed flow plausibly prints before price confirms, positioning after.
  N3 exists to stop counting correlated families as confirmations; this engine
  uses the same family partition to study order instead of count.
- **Corpus parts:** N3 evidence-family grouping; Morgue Tape (Heat/Algo, N2
  dual population), Map (chain inventory), Board (price), insider/13F
  summaries (positioning, summary grain only); The Second Opinion (tool 18)
  counts families — it does not order them or forecast.
- **Why new:** Order-permutation conditioning appears in no teardown, tool or
  study in the inventory. Genuinely novel combination of N3 + N1.
- **Data route (e):** Tape cards, Map cards and Board runs already produced by
  the daily cycle (young: 9 map cards, 2 tape sessions of record) — so
  PARTIAL (f): proving state will be long; the engine can ledger from day one
  but its conditional tables stay `insufficient-history` until ≥126
  multi-family sessions accrue, printed as such.
- **Grading (b,c,d):** +1/+5/+21 fixed horizons; accuracy vs (i) unconditional
  base rate, (ii) an order-shuffled null (same triggers, permuted order).
  Families are the unit throughout — vendor counts never enter.

## T4. Index Relay — constituent-to-index lead–lag sequence

- **Forecast (a):** Daily, ledger for SPY/QQQ/IWM: the ranked lag profile —
  which constituent cohort (top-weight decile, median names, sector leaders)
  moved on day 0 — and publish P(index next-session return > 0) and median
  next-session return conditional on the day-0 leader cohort, plus a specific
  relay call: the cohort predicted to lead on day +1.
- **Mechanism:** A relay claim (big names → broad names, or growth → cyclicals,
  in sequence) is narrower than the killed claim. Kill marked explicitly:
  breadth/internals as index direction is grade X (T11, "no internal calls
  SPY"); this engine does not use breadth levels. It tests *who moved first*
  (identity/order of the leading cohort), against a same-day-breadth-matched
  control, and is pre-committed to die if it collapses to the breadth result.
- **Corpus parts:** Index membership effect S12 (B, roster caveat); peer-gap
  reversal in T2 (A); sector/index constituent map (1,498 of 1,833 names —
  335 names have no sector on record, and are excluded, printed).
- **Why new:** Sector Rotation (32) describes who is leading now over 5/21
  sessions; no tool forecasts the next leg of a relay or grades a lead–lag
  order claim.
- **Data route (e):** Shipped daily bars for the three index ETFs and roster
  constituents; constituent map as above. Fully on record today.
- **Grading (b,c,d):** Next-session grading only at first (the relay claim is
  short); hit rate and median vs the breadth-matched control and vs a
  cohort-label permutation null. Price family = 1 confirmation maximum.

## T5. Intraday Shape Echo — today's morning shape vs whole-day ghosts

- **Forecast (a):** By 11:30 ET, classify SPY/QQQ/IWM's morning path into a
  small shape alphabet (trend-up, V, inverted-V, range, trend-down, gap-and-go,
  gap-and-fade — from 5-minute closes), ledger it, and publish the conditional
  distribution of the *afternoon* path: P(close in top/bottom third of the
  day's eventual range) and median return 11:30→close, from prior days whose
  morning shape matched.
- **Mechanism:** Gap-Fill (11) and Opening Range (12) panes reduce the morning
  to a gap or a range break. The echo claim is that the morning's *path shape*
  (order of highs/lows, not its endpoints) selects which historical afternoons
  follow. Intraday momentum standalone is killed (AD-39) — marked: this is
  shape-conditional distribution, tested against the endpoint-only (gap +
  first-hour range) conditioning of tools 11/12 as its control.
- **Corpus parts:** Studies S1/S2 distributions; Bilbo-lane Alpaca bar
  conventions in AGENTS.md (SIP for history, IEX real-time, explicit start +
  pagination on the bars API).
- **Why new:** No tool or vendor in the inventory conditions on intraday path
  shape; 11/12 are descriptive panes with no ledgered intraday forecast.
- **Data route (e): UNMET today, named.** Inventory §4.1: hourly history is
  shallow/gap-prone (from 2026-03-17, 41 names), live intraday figures were
  no-data in the recorded Studies run (Alpaca 401). The 5-minute index route
  must accrue from the running Alpaca SIP/IEX machinery before any forecast
  issues; until then this candidate ships only as an accrual counter.
  It cannot meet (e) or (f) yet — included because the accrual lane exists
  and the shape alphabet/fixtures can be built now.
- **Grading (b,c,d):** When live: ledger timestamped before 11:35 ET, graded
  at that day's close, every classified morning in the denominator including
  range days; Brier vs the tools-11/12 endpoint-conditioned distribution.

## T6. Streak Hazard — duration of runs as the forecast

- **Forecast (a):** For SPY/QQQ/IWM and each roster name, on the close of the
  k-th consecutive same-sign session (k = 2…8), ledger: P(run extends one
  more session), P(reversal ≥0.5× the name's own-norm daily move within
  3 sessions), each as a function of k and run size in own-norm units.
- **Mechanism:** Markets are usually modelled memoryless per session; a
  duration-dependent run hazard is a pure sequence statistic no corpus study
  isolates. Distinguished from killed calendar effects (T10, grade X — dates,
  not durations) and from killed hit-rate features (AD-35: RSI/distance add
  hit rate, no mean R — so this engine forecasts *extension/reversal
  probabilities and timing*, and must additionally report mean R to prove it
  is not repeating AD-35's trap; if probability lifts but mean R is zero, it
  grades as timing-only, in T1's honest category).
- **Corpus parts:** Own-norm normalisation from F3/N10; T2 stress reversal (A)
  as the stress-tercile slice of the same table; shipped closes.
- **Why new:** No streak/duration table exists in the 70 tools or the studies;
  State Analogue (20) matches state points, not run durations.
- **Data route (e):** Shipped + DEEP daily closes. On record today.
- **Grading (b,c,d):** Per-k calibration (predicted vs realised extension
  rate, Wilson intervals printed), losers and run-continuations both in the
  denominator; one row per run, overlapping runs de-duplicated by construction.

## T7. Propagation Wave — leader-first, laggard-next, by name

- **Forecast (a):** When a sector/index cohort posts a day-0 move ≥1× its
  own norm, ledger the wave call: the specific not-yet-moved peer names
  (same sector, day-0 move <0.25× norm) predicted to move in the same
  direction within +1 to +3 sessions, with P(move ≥0.5× own norm by +3)
  per name. Names that never move grade as misses.
- **Mechanism:** Cross-sectional studies grade cohorts, not sequences across
  names. The wave claim is temporal contagion in a stated order (leaders,
  then named laggards). It must beat its own anti-control: T2's peer-gap
  *reversal* (A — peers that gapped *against* the move revert) predicts the
  opposite for one slice; both cannot win on the same names, and the ledger
  forces the confrontation the corpus never staged (cf. C13's open pattern).
- **Corpus parts:** T2 peer-gap reversal; S10/S11 momentum (B) as the slow
  version of the same intuition; constituent/sector map; Correlation Web
  (37) clusters as wave membership (descriptive today, no forecast).
- **Why new:** No vendor/tool names the *next names in sequence* in advance;
  scanners rank today's movers, this forecasts tomorrow's followers by name.
- **Data route (e):** Shipped daily bars + sector map (335 unmapped names
  excluded, printed). On record today.
- **Grading (b,c,d):** Per-name +3 grading, precision/recall of the wave list
  vs a random same-sector laggard list of equal size (picker-replay control
  discipline); sector-level clustering counted once per wave (N3).

## T8. Overnight–Intraday Leg Relay

- **Forecast (a):** Decompose each session for SPY/QQQ/IWM into overnight leg
  (prior close→open) and intraday leg (open→close). Ledger at each open the
  forecast for today's intraday leg (sign + median, in own-norm units)
  conditional on the overnight leg's sign/size *sequence* over the last
  3 sessions (e.g. three positive overnight legs in a row); and at each close,
  the mirror forecast for tonight's overnight leg.
- **Mechanism:** The two legs are different auctions with different
  participants; their *alternation rhythm* (overnight strength borrowed from,
  or repaid by, the intraday leg) is a sequence claim about legs, not a level
  claim. Kill marked: the overnight family as a direction predictor is in
  AD-41's killed set (X) and T9's Legend Buy Day overnight effect (B) exists
  only index-level for one named setup. This candidate is therefore scoped
  index-only, framed as a *replication-or-death* test of leg-sequence
  conditioning, and pre-registered to be killed publicly if its first 126
  ledgered sessions do not beat the single-leg base rate.
- **Corpus parts:** T9 (B, index only); AD-41 kill; Gap-Fill pane's gap
  machinery (S1) for leg measurement; E3 (edges include the overnight move).
- **Why new:** No tool splits the return stream into an alternating leg
  sequence and forecasts leg-to-leg; 11 conditions on gap size/weekday only.
- **Data route (e):** Daily open/close on record (shipped + DEEP + SPY/QQQ
  2010–2026 band-study history). On record today.
- **Grading (b,c,d):** Ledger at the leg boundary (open/close timestamps are
  the horizon gates); per-leg Brier + median error; both legs graded, neither
  dropped when flat.

## T9. Earnings Path Script — the ordered −5…+10 path around a report

- **Forecast (a):** At −5 sessions before a scheduled report for any calendar
  name, ledger the full predicted path script: expected sign and own-norm
  size for each relative session −5…−1 (run-up/ fade), the report-day gap
  distribution (median, 25/75), and +1…+10 drift signs — as one ledgered
  vector, graded session by session.
- **Mechanism:** Corpus earnings knowledge is fragments at single horizons:
  pre-earnings trail (A13, C, −0.43%), small-cap/EP gap fade (A12, B),
  descriptive drift panes for 3 names (13). Nobody assembles or grades the
  *whole ordered path* as one forecast object, so compensating errors across
  horizons stay invisible. Path-vector grading exposes them.
- **Corpus parts:** A12/A13; Earnings Calendar (35, priced expected move
  attached); Earnings Drift Pane (13, AAPL/MSFT/NVDA descriptive only);
  DEEP earnings dates (D5 caveat: winter dates were one session late for
  4.2% of events, fixed — the fix, not the defect, is inherited).
- **Why new:** 35 lists who reports with an expected move; 13 shows what 3
  names did. Neither forecasts a per-name path, and no vendor teardown in
  the inventory grades an event-relative path vector.
- **Data route (e):** Earnings calendar + chain-derived expected moves on
  record; daily bars on record. Forward accrual from the running calendar.
- **Grading (b,c,d):** Per-relative-session calibration plus a path score
  (mean absolute error across the 16-session vector); every scheduled name
  ledgered at −5 stays in, including names whose report moves (date changes
  ledgered as amendments, original kept — N1 as-was rule). Events family = 1.

## T10. Leadership Rotation Markov — next sector up, by transition order

- **Forecast (a):** Weekly, ledger the current sector-leadership state
  (rank order of sector ETFs by 21-session own-norm return) and publish the
  transition forecast: P(each sector enters the top-3 within the next
  5 sessions), naming the single most likely *new* entrant and the single
  most likely exit.
- **Mechanism:** Rotation is universally shown as a snapshot ranking (tool
  32, 5/21 sessions). A first-order transition model over leadership *states*
  turns the snapshot into a sequence claim: some rotations follow a habitual
  order (e.g. defensives follow growth peaks), most rankings assume none.
  Tested against the persistence null (tomorrow's leaders = today's), which
  is the honest favourite and the bar the engine must clear.
- **Corpus parts:** Sector Rotation (32, descriptive); Momentum Clock (70,
  description only, explicitly no performance language); S10 momentum (B)
  as the name-level cousin whose sector-state form is untested.
- **Why new:** No tool/vendor in the inventory publishes a leadership
  transition matrix or grades rotation calls forward.
- **Data route (e):** Sector ETFs inside the shipped daily history
  (399 sessions) + DEEP for transition estimation. On record today.
- **Grading (b,c,d):** Weekly ledger, +5 grading; top-3 entry/exit precision
  vs the persistence null and vs a uniform null; 21-session overlapping
  states de-overlapped by grading entry events, not states.

## T11. Print-to-Price Delay Clock — how long flow takes to matter, if it does

- **Forecast (a):** When the Tape prints an extreme reading for an index ETF
  or Board name (Heat or dual-population Algo Score in its top historical
  decile for that name), ledger at print-session close: P(price first moves
  ≥0.5× own norm in the print-implied direction at lag k), k = 0…5 sessions —
  a delay distribution, with P(never within 5) printed as a first-class
  outcome, forecast to be the modal outcome until evidence says otherwise.
- **Mechanism:** Flow tools assert contemporaneous meaning; the corpus has
  never measured the *lag structure* of prints→price, and its execution
  record (X family: edges decay in 1–5 sessions, one bar late is costly)
  says lag is where value lives or dies. A delay clock converts every flow
  claim into a timing claim that can be graded cheaply and killed cleanly.
  Side labels inherit the C16 latest-quote limitation, printed on the card.
- **Corpus parts:** Morgue Tape scorer (fixture-proven, Heat 18.5 asserted);
  N2 dual-population score (both populations clocked separately — if only
  the buys-only population "leads", the intake bias is exposed by timing);
  Flow Tape/Golden Sweep Wire (4/5) as print sources.
- **Why new:** Tape Heatmap/Flow Board (55/56) rank today's flow; none
  forecasts or grades a lag. The delay distribution is a new object.
- **Data route (e):** PARTIAL (e/f): tape sessions on record are 2, golden
  prints 0 — the clock ledgers from the daily cycle going forward and stays
  in proving state with its session counter printed (mirroring tool 5's
  30-session decision discipline, decision date set at first ledger entry).
- **Grading (b,c,d):** Per-lag log-loss vs the unconditional 5-session move
  distribution; "never" outcomes in the denominator; prints family = 1,
  never stacked with Tape-derived tools as separate confirmations (N3).

## T12. Stress-Reversal Staging — the T2 survivor as an ordered script

- **Forecast (a):** In the deepest SPY-drawdown tercile only (T2's exact
  condition), ledger at day 0 for each of yesterday's loser cohort: the
  staged script — P(reversal begins by +1), P(peer-gap component closes by
  +3), median cumulative return at +1/+3/+5 — as three separately graded
  stage forecasts per name, not one blended call.
- **Mechanism:** T2 is the corpus's only grade-A directional survivor
  (last-day IC −0.058/−0.028 in stress; 393 stress-reversal confirmations vs
  null 17; peer-gap IC +0.017, t 4.4). Every other engine here starts
  unproven; this one starts from the strongest evidence and asks the
  temporal question the original study did not: in what *order and at what
  lag* do the reversal's components arrive, so a user knows which stage
  failing kills the script early. Roster caveat D3 (survivors roster)
  carried on the card.
- **Corpus parts:** EV T2 (A); F5/F7 RESET laggard RS (B) as cohort
  definition support; fear-day machinery (16/43) for the stress gate.
- **Why new:** Survivors Wire (49) republishes survivor candidates as a
  feed; Fear-Day Forecaster (43) issues fear-day names. Neither decomposes
  the one A-grade effect into a graded stage sequence with early-kill
  staging. Ascends, does not duplicate.
- **Data route (e):** Daily bars + drawdown tercile computable from the
  SPY history on record (2010–2026). On record today; forward instances
  are episodic (stress tercile), so accrual is event-paced — PARTIAL (f)
  in speed only, marked: proving state may span few episodes, exactly the
  T6/T7 small-episode trap (grade C precedents had 5–13 episodes), and the
  card must print episode count beside any rate.
- **Grading (b,c,d):** Stage-wise grading at +1/+3/+5, all day-0 cohort
  names in every stage's denominator; script killed as a whole if stage 1
  fails its pre-registered bar in the first 3 forward episodes.

---

## Lens summary for the ranking phase

- Strongest evidence anchor: T12 (only grade-A survivor, staged).
- Cheapest to grade, fully data-in-hand: T1, T2, T6, T8, T10.
- Genuinely novel objects: T3 (ignition order), T7 (named propagation wave),
  T11 (delay distribution), T9 (path vector).
- Honest exceptions: T5 UNMET (e) — intraday route must accrue first;
  T3/T11 PARTIAL (f) — young tape/map records, long proving states;
  T2 wall-break class PARTIAL (e) — 9 map cards; T12 PARTIAL (f) — episodic.
- Kill-discipline carried in-engine: T1 shuffle control, T4 breadth-matched
  control (T11 kill), T5 endpoint control (AD-39), T6 mean-R disclosure
  (AD-35), T7 anti-control vs T2, T8 pre-registered death (AD-41).
