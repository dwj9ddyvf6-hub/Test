# NVDA EARNINGS SCREENER LIVE PREP PACK: FIRST RUN, TUE 2026-11-17

Print: NVDA (NVIDIA), Tue 2026-11-17, after the close (desk
calendar; the H4 chain run records the same date and a priced
move of 8.7 percent in the weekend study).
Source of truth: the screener registration,
~/workspace/midna-book/strategy-candidates/2026-11-14-earnings-underpricing-screener.md
(registered Sat 2026-11-14, Continuation workstream C4; source
in full: Alpha Hunt Dive Three, Territory 1). Every constant
and rule below is copied from that registration. Where this
pack specifies a run mechanic the registration does not spell
out, the line is tagged METHOD (this pack).
Observation record built with this pack:
~/workspace/research_notes/decisions-api-leverage-20261114/conversion/nvda_observation_record.json
That record is the artifact the run fills. This pack is the
procedure that fills it.
Status: registration only, observation only. See section 7,
What is NOT done.

## 1. Version A constants, EXACT as registered

The calendar leg gates registered in section 3 of the
registration, labeled Version A there. Quoted in the
registration's own terms:

- Volume: minimum average volume 1,500,000 shares per day,
  mean over the latest 30 sessions.
- IV30/RV30: minimum 1.25, where IV30 is at the money IV
  interpolated at 30 DTE and RV30 is annualized 30 session
  Yang-Zhang volatility.
- Slope: maximum term structure slope minus 0.00406, in decimal
  IV per calendar day, defined as slope equals (IV45 minus IV
  front) divided by (45 minus DTE front). A pass requires slope
  at or below minus 0.00406; a more negative slope means
  stronger front backwardation. IV45 must be interpolated from
  bracketing expirations, never clamped to the last point below
  45 DTE.

Decision rule from the specification, registered as the gate
reading: all three filters passing is recommended, term slope
plus exactly one other is consider, all else avoid.

Version B is not run here. The registration logs Version B
(volume at or above 500k, IV/RV above 1.5, term slope described
with the sign convention reversed) as a lossy paraphrase and as
a third arm for one season only under the falsifier. This first
NVDA run is a Version A observation; no Version B reading is
taken on it.

## 2. The straddle leg rules that grade this print

The screener's other leg, registered in sections 1 and 2 of
the registration, is what places NVDA in a quintile. Stated
here in full so the run is graded by the filed rules, not by a
summary of them.

- Synthetic edge proxy: implied move minus realized absolute
  move. The proxy is computed before the print from the implied
  move, and graded after the print against the realized move.
  A name enters either pool only through the proxy sort on its
  own print. No discretionary additions, no mid season
  threshold moves.
- Vendor round trip construction, as registered: entry cost is
  call ask plus put ask and exit value is call bid plus put bid
  on the real chain fetched per event, strike nearest spot,
  expiry nearest 9 DTE inside a 4 to 14 DTE window widened if
  needed.
- Quintile construction: earnings events are sorted by the
  synthetic edge proxy. Q1 is the most underpriced quintile
  (median edge minus 4.83 points in the primary; mean long
  profit and loss plus 36.68 percent, win rate 80.0 percent).
  Q2 median edge minus 1.11 points, mean long minus 12.28
  percent. Q3 median edge plus 0.83 points, mean long minus
  31.71 percent. Q4 mean long minus 40.34 percent. Q5 is the
  most overpriced quintile (median edge plus 3.82 points, mean
  long minus 44.46 percent, win rate 0.3 percent). The top of
  the sort is a short volatility candidate pool, the bottom
  extreme (Q1) is the only longable pool, and the middle is a
  veto zone for long straddles.
- Q1 ONLY LONGABLE, a hard rule of the registration, not a
  default: the long straddle side is open in the extreme
  underpriced quintile only, Q1, with edge at or below about
  minus 2.3 points (the Q1 boundary in sample) and historical
  mean crush at or below 30 points. Q2 is already minus
  12.3 percent per trade in the primary, so no long straddle is
  taken in Q2, Q3, Q4 or Q5 under this registration for any
  reason, including a strong story on the name.
- Crush filter, registered with it: an underpriced flag with
  historical mean crush above plus 30 points is graded AVOID
  for long straddles, not LONG. In the primary, 6 of the 15
  most underpriced symbols failed to confirm on real long
  profit and loss (AKAM, CIEN, GEN, CVNA, DECK, LULU) and carried
  mean IV crush of plus 20 to plus 57 points.
- Defined risk only, registered in the same section: no naked
  short volatility under this registration, in any size, at any
  confidence. The short side (Q4 and Q5 names) is expressed only
  in defined risk form, and only under a separate expression
  registration. Nothing in this pack builds an expression.
- Timing note, registered: AMC prints lose more than BMO prints
  in real profit and loss (minus 19.68 percent versus minus
  17.55 percent), because overnight crush is larger (plus 18.54
  points versus plus 13.43 points). NVDA is an AMC print; that
  fact is recorded in the observation record's timing field and
  carried into any later sizing discussion, which this run does
  not have.
- Accounting mandate (registration section 5), governing this
  run: entry at ask, exit at bid, on every leg, no exceptions.
  Mid prices, last trade prices and theoretical values are not
  accounting prices here and may not be substituted in any test,
  forward log or grade. Any result produced on mid pricing is
  void and is re run, not footnoted. Commissions and spread cost
  actually paid are recorded beside the bid and ask prices on
  every forward record; for this hypothetical observation the
  commission field is recorded as not applicable, hypothetical,
  with the spread cost being the ask to bid accounting itself.

## 3. The negative replication, carried on the face of this pack

The only independent executable replication of the calendar leg
located in dive three was negative. It is attached to the
registration at full weight as the standing warning on the
calendar leg, and it is carried here, on this pack's face, so
the first live run is read against it and not against the
video claim.

Quoted from the registration, section 4:

"First, an independent QuantConnect backtest of this exact
strategy, author u shock_and_awful on Reddit, creator Volatility
Vibes, using the Version A thresholds verbatim, over 2024-06-01
to 2024-11-03, produced 77 orders, average win 0.21 percent,
average loss minus 0.25 percent, expectancy minus 0.165,
compounding annual return minus 1.275 percent, net profit minus
0.544 percent on a 1,000,000 dollar paper account, estimated
capacity 260,000 dollars, lowest capacity asset PG. The window
is short, five months, and one implementation, so it does not
refute a 17 year claim. It is, however, the only independent
executable replication located, and it is negative."

Provenance, as the registration states it: INDEX grade in dive
three (search excerpt and forum attribution, not a full primary
read), single implementation, five month window, Version A
thresholds used verbatim. No other independent replication of
either leg was located.

Reading rule for Tue 2026-11-17: a clean Version A pass on NVDA
does not outweigh this replication, and a fail does not confirm
it. One print is one observation inside the two season falsifier
in section 6. The pack prints the replication here precisely so
neither reading is available on the day without the warning
beside it.

## 4. Inputs staged for NVDA, Tue 2026-11-17

Fill each line from the run in section 5 and mirror the values
into the observation record. Values are null in the record
until the run supplies them.

Pre print inputs (computed before the print, from the pre print
chain and bars):

- [ ] Spot at the pre print snapshot, with timestamp ET: ______
- [ ] Average volume, latest 30 sessions, shares per day, and
  the pass reading against 1,500,000: ______
- [ ] IV30: at the money IV interpolated at 30 DTE: ______
- [ ] RV30: annualized 30 session Yang-Zhang volatility, from
  OHLC daily bars over the latest 30 sessions: ______
- [ ] IV30/RV30 ratio, and the pass reading against 1.25: ______
- [ ] IV front: at the money IV at the front expiry used for
  the slope, with that expiry and its DTE recorded: ______
- [ ] IV45: at the money IV interpolated at 45 DTE from
  bracketing expirations (never clamped), with both bracketing
  expiries recorded: ______
- [ ] Term slope: (IV45 minus IV front) divided by (45 minus
  DTE front), in decimal IV per calendar day, and the pass
  reading against at or below minus 0.00406: ______
- [ ] Gate reading under the registered decision rule:
  RECOMMENDED (all three pass), CONSIDER (slope plus exactly
  one other), or AVOID (all else): ______
- [ ] Implied move for the straddle proxy: from the ATM
  straddle at the expiry nearest 9 DTE inside the 4 to 14 DTE
  window (strike nearest spot), stated in percent and in
  points, with expiry and strike recorded: ______
- [ ] NVDA historical mean IV crush over its prior prints, if
  an estate source supplies it, with the source named. If no
  estate source supplies it on the day, record NOT AVAILABLE
  and leave the Q1 longable derivation incomplete rather than
  substituting a vendor figure. The crush line decides LONG
  versus AVOID inside Q1, so an unavailable crush means no
  longable flag can be set to true. METHOD (this pack) for the
  unavailability handling; the 30 point line itself is the
  registration's.
- [ ] FIT-PROXY conditioner, grading only: the synthesis order
  (rank 8) carries FIT-PROXY's first pressure reading, naming
  NVDA among MRVL, CRWV, SNDK and NVDA, into the Nov 17 print
  as a grading conditioner only. Record NVDA's FIT reading if
  the estate route supplies a current one on the day, labeled
  conditioner, with no effect on the gate, the quintile or the
  flag. Owner of the reading: ______ Value: ______

Print inputs:

- [ ] Print acceptance timestamp ET (the time the print is
  accepted as released, not the time it is read here): ______
- [ ] Headline figures as released, recorded for context only
  and never as a screener input: ______

Post print inputs:

- [ ] Realized absolute move: the absolute spot move graded
  against the implied move, in percent, with both spot
  endpoints and their timestamps recorded: ______
- [ ] Synthetic edge: implied move minus realized absolute
  move, in points: ______
- [ ] Hypothetical long straddle exit pricing: call bid plus
  put bid on the same strike and expiry as the entry, at the
  exit snapshot in section 5: ______
- [ ] Quintile placement: assigned only after the season cohort
  sort in section 6. On print night this field stays PENDING
  COHORT SORT in the pack and null in the record, by design.
- [ ] Q1 longable flag: a boolean derived by the registered
  rule in section 6, set only when every component exists.

## 5. Run procedure for Tue 2026-11-17

Routes, named once, used throughout. Both routes are estate
routes that work on this box. No other route is substituted
silently; a failed route is recorded as failed, with its error,
and the field it supplies is left null.

Route 1, the live options route (primary for this run):
desk3 credential env (run_live.credential_env, vault surrogate,
values never printed) plus desk3.producers
fetch_option_contracts and fetch_option_snapshots with
feed=indicative, read only. Implied vol and delta by
Black-Scholes inversion at r = 4 percent, labeled indicative
in every record. This route supplies: the contract list
(strikes and expiries), per contract bid and ask snapshots,
spot referenced IV work, and therefore IV front, IV30, IV45,
the term slope inputs, the implied move straddle, and the
hypothetical straddle entry ask and exit bid. The bilbo-options
iv_snapshot.py module is never imported (house rule).
Route 2, the chain panel capture (canonical close snapshot):
cron chain-panel-close-capture, weekdays 16:46 ET, writing the
panel store at ~/workspace/morgue/state/morgue/chains_panel/.
This route supplies: the canonical close snapshot for the
session, modelled IV panel rows for NVDA, and the accrual row
that later chain work grades against. It is a close snapshot,
not a live pre print pull.
Bars and volume route: estate daily bars for NVDA (split
adjusted where the route states it, basis recorded on the
day), supplying the latest 30 sessions of OHLC for RV30
(Yang-Zhang) and the latest 30 sessions of volume for the
average volume gate. METHOD (this pack) for naming the bars
route as a separate line; the registration defines RV30 and
the volume mean, and does not name a bars vendor.

Steps, in time order (all times ET):

- [ ] Step A, staging, Tue morning 2026-11-17: open the
  observation record, confirm every field is present and null
  where the print has not happened, confirm the Version A
  constants embedded in the record match section 1 of this
  pack character for character. Pull the 30 session bars and
  compute average volume and RV30. Record both, with the bar
  window dates.
- [ ] Step B, pre print chain snapshot, Tue 2026-11-17 in the
  final hour before the close and in any case before the print
  is released: Route 1 pull for NVDA. Compute IV front, IV30
  (interpolated at 30 DTE), IV45 (interpolated from bracketing
  expirations, never clamped), the term slope, and the
  IV30/RV30 ratio. Select the straddle strike nearest spot and
  the expiry nearest 9 DTE inside the 4 to 14 DTE window
  (widen only if no expiry sits inside it, and record the
  widening). Record the hypothetical long straddle entry as
  call ask plus put ask at that snapshot. Record the implied
  move from that straddle. Timestamp every value. This snapshot
  is the primary pre print source for grading.
- [ ] Step C, panel capture, Tue 2026-11-17 16:46 ET: confirm
  the chain-panel-close-capture run landed for NVDA and record
  its manifest pointer. Caution, METHOD (this pack): the
  capture runs after the 16:00 close and an after close print
  may be released before or during the capture window. Record
  the capture timestamp beside the print acceptance timestamp.
  If the capture timestamp is after the print acceptance
  timestamp, label the panel row POST PRINT in the record notes
  and do not use it as the pre print chain; Step B remains the
  pre print source of record.
- [ ] Step D, the print, Tue 2026-11-17 after the close:
  record the acceptance timestamp, the timing flag AMC, and
  the headline context. Take no other action on print night.
  No chain pull in the first minutes after the release is used
  for the exit; the exit snapshot is Step E.
- [ ] Step E, post print chain and tape, Wed 2026-11-18:
  Route 1 pull at about 15 minutes after the next open (the
  exit timing the registration registers for the calendar leg;
  METHOD (this pack) in applying the same exit timestamp to
  the hypothetical straddle exit, because the registration
  defines the straddle round trip by its bid and ask legs and
  does not name a separate straddle exit clock). Record call
  bid and put bid for the Step B strike and expiry, the spot
  at that snapshot, and the tape move from the pre print spot
  to that spot. Compute the realized absolute move, the
  synthetic edge, and the hypothetical round trip at ask in,
  bid out. Record every value in the observation record.
  A second snapshot at the Wed close may be recorded as a
  secondary line, labeled secondary, and never substituted for
  the primary exit.
- [ ] Step F, grading inputs closed, Wed 2026-11-18 after
  Step E: compute the gate reading (section 4), the edge, and
  the Q1 derivation components (section 6). Leave the quintile
  placement and the verdict as specified in section 6. File
  the completed record back at its path in the header and note
  the byte size in the run note.

## 6. Quintile placement, the Q1 flag, and the falsifier counter

Quintile placement. METHOD (this pack), applying the
registration's construction: a quintile is a sort position
inside a cohort, so NVDA's placement cannot be computed from
NVDA alone. The registration's forward log covers every S and
P 500 and Focus 30 earnings event over two full earnings
seasons, logging synthetic edge, quintile, historical mean
crush, BMO or AMC, and the real bid and ask round trip. NVDA's
placement is therefore assigned when the season 1 cohort is
sorted by synthetic edge, and until then the record's quintile
field stays null with its method note attached. Any single
print quintile assigned on print night would be invented, and
this pack does not invent it.

Q1 longable flag, derivation (the registration's rule, stated
as a boolean formula): the flag is true only if all of the
following hold: (1) quintile placement is Q1; (2) synthetic
edge is at or below about minus 2.3 points; (3) historical
mean crush is at or below 30 points. If any component is
missing, the flag stays null in the record, not false, because
false would assert the name was graded and failed, and null
asserts it has not yet been graded. If all components exist
and any one fails, the flag is false. If the name lands in Q1
with edge passing and crush above 30 points, the registration
grades it AVOID for long straddles; record that word in the
record notes beside a false flag.

Falsifier counter, as registered (registration section 7):
the forward log runs for two full earnings seasons. This run
is season index 1 of 2. Prints graded count starts at 0 in the
pre built record and increments only when a print has been
fully graded (edge, quintile, crush, timing and round trip all
recorded), which for NVDA cannot happen before the season
cohort sort. The falsifier itself, carried here so the counter
has its terms beside it: the straddle leg claim is falsified
over two seasons if the Q5 minus Q1 spread in long profit and
loss compresses below 20 percentage points, or the Q1 win rate
falls below 60 percent, or the short side defined risk twin
fails to beat the middle quintiles net of full spread cost.
The calendar leg is falsified, over the same two seasons with
a minimum of 100 gated events, if gated expectancy net of entry
at ask and exit at bid on every leg is at or below the ungated
twin, or if the slope tercile ordering inverts. On any falsifier
firing, the affected leg is recorded falsified at the Friday B5
grading that follows the second season close; it is not retuned
in place.

Verdict field: null. It stays null in the observation record
through this run, this season, and until the falsifier's own
grading point. A verdict on one print is not available under
the registration, and this pack does not supply one.

## 7. What is NOT done

- Nothing is traded. No order is placed, no card is opened, no
  sleeve is built, no code is wired, and no sizing is computed
  under this pack or under the registration. The registration
  states it plainly: registration only, and the forward log is
  a measurement commitment, not a trading authorization.
- The hypothetical long straddle in the record is an accounting
  exercise at ask in and bid out, built to grade the screener.
  It is not a position, not a recommendation, and not an
  expression. Any expression built later is a separate
  registration under its own falsifier.
- The book's options only rails and the registration's own
  terms govern throughout: defined risk only if anything is
  ever expressed, Q1 only longable as a hard rule, no naked
  short volatility at any confidence.
- The observation record is an observation, not a card. It does
  not enter the book, the ghost book, or any sleeve ledger.
- No mid price is recorded as an accounting price anywhere in
  the run. A field that can only be filled at mid is left null
  and named, per the accounting mandate in section 2.
- Version B is not run, the gate constants are not moved mid
  season, and no discretionary name is added to the cohort.

End of pack. Source of truth remains the screener registration
cited in the header. Where this pack and the registration
differ, the registration governs and the difference is flagged
in the run note, not resolved silently.
