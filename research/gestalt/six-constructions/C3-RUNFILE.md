# CELL C3, REPAIR THEN ROTATE, RUNFILE

Six Constructions Run 2, ordered Sun 2026-11-15.
Cell: C3, "Repair, then rotate".
Registered: Sun 2026-11-15, before any replay code in this cell was run
and before any result in this cell was read.
Typed Decisions API spend for this cell: $0.00, and no Decisions API
call will be made by this cell.
Research artifacts only. Nothing in this cell touches the desk repo,
the book, or any trading state, and nothing in this cell changes any
trade. The module desk/research/bilbo-options/iv_snapshot.py is never
imported by this cell. No em dash character appears in any artifact of
this cell.

## DEFERRED REPLAY STATEMENT

The replay itself is DEFERRED to a later run. Tonight delivers
pre-registration plus data inventory only. No replay was run tonight,
no event was computed tonight, and no result is claimed tonight.
Trial ledger: tonight's registration is charged as 1 trial.

## SCOPE

Surface: this cell only, in
~/workspace/research_notes/six-constructions-20261115/ : this runfile
tonight; the replay code and results files belong to the later run and
do not exist yet.
Constraints: the definitions in sections 1 to 7 are frozen by this
registration and may not be tuned after results are seen; the desk
repo, the book, and all trading state stay untouched; held data is
used as inventoried in section 8, with its limitations carried into
every later verdict; light compute only in the later run until the
panel reader question in section 8 is settled.
Outcome: in the later run, one observable answer: on complete capital
paths, does rotating at repair add incremental terminal wealth after
costs, beyond holding the original asset, beyond cash at repair,
beyond owning the leadership basket from entry, and beyond switching
at a fixed elapsed time.
Proof in the later run: per policy portfolio paths and per event
incremental wealth read back from the results artifact, the falsifier
check in section 7 applied exactly as written, and the trial ledger
updated with every variant actually run.
Edges: the estate holds no point in time index membership table and
no complete delisting record (section 8). The basket in section 3 is
therefore defined by rules computed from bars alive at the decision
date, never by index membership, and the missing delisted class in
section 8 is a named limitation on every later verdict, not a
footnote.

## 1. Hypothesis

A reversal strategy buys temporary damage. If the damage measurably
repairs, the reason for holding a damaged name may be spent, and the
recovered capital may earn more in current leadership than in the
original name. The claim under test is narrow: the repair observation
itself, rho reaching 1 as defined below, is the information that
times the transfer. If a basket owned from entry, or a switch at a
fixed elapsed time, explains the same gain, the repair timed switch
has not earned its complexity.

## 2. Entry event, shock, beta, repair fraction, endpoint

Benchmark: SPY, from the same panel and the same adjustment basis as
the stock, throughout. No second benchmark is used in the primary
replay.

Beta estimation window, fixed in advance: for an event with shock
window defined below, beta_hat is the ordinary least squares slope of
the stock's daily log close to close returns on SPY's daily log close
to close returns over the 252 trading sessions ending on the session
immediately before the shock window starts. A name with fewer than
252 valid paired sessions in that window, or with a non positive beta
estimation variance, is not an event and is counted as excluded.

Shock window: the 5 trading sessions ending at the signal close,
session S. The market adjusted shock return over the window is

  shock = sum over the 5 sessions of (r_stock minus beta_hat times r_SPY)

using daily log close to close returns. The damage magnitude is
d = minus shock. An entry event requires all of the following, using
only information available at the signal close:

1. d is at least 0.10 (ten log points of negative market adjusted
   return over 5 sessions).
2. The stock close at S is at least 5 dollars.
3. The stock's mean daily dollar volume over the 63 sessions ending
   at S is at least 5 million dollars.
4. The stock has a valid bar at S and at every session of the shock
   and beta windows.
5. The same stock has not already produced an admitted event whose
   common endpoint (below) is still open at S; overlapping events in
   one name are suppressed and counted.

Entry: capital is allocated at the close of session S plus 1, at that
close price. The one session delay is registered deliberately: the
signal is known only at the close of S, and every return in the
replay is then a clean close to close log return with no intraday
execution assumption.

Recovery and repair fraction: for each session k after the entry
session, the cumulative market adjusted recovery is

  x_k = sum from the session after entry through k of
        (r_stock minus beta_hat times r_SPY)

with beta_hat frozen at its pre entry value. The repair fraction is
rho_k = x_k divided by d. The repair event tau is the first session
close at which rho_k is at least 1, that is, the measured initial
shock has been recovered in market adjusted log terms. Tau is a
reference transition, an interpretable candidate event, not a claim
about fair value. If rho never reaches 1 before the common endpoint,
tau does not occur for that event and the rotation policies coincide
with holding for that event; such events are counted and reported
separately, never dropped silently.

Common endpoint: T is the close of the 126th trading session after
the entry session. Every policy for an event is valued at the same T,
so pre tau gains are common to the policies and cancel in the
incremental comparison. If a name has no bar at T because it left the
panel before T, its terminal value is its last available close,
flagged as an early termination, with no delisting return invented;
the count and identity of early terminations are reported, and a
sensitivity that excludes early terminated events entirely is a
registered part of the later run, not an optional extra.

## 3. Leadership basket, point in time rules

The basket is formed at a decision close, which is tau for the
rotation policies, the entry close for the basket from entry policy,
and the fixed time close for the fixed time policy. Only information
available at that decision close may be used. Membership is never
defined by later winners, by later index membership, or by any table
dated after the decision.

Universe at a decision close D: every name in the deep panel
(section 8) that satisfies all of the following at D:

1. A valid bar at D and at least 200 valid bars in the 252 sessions
   ending at D.
2. Close at D of at least 5 dollars.
3. Mean daily dollar volume over the 63 sessions ending at D of at
   least 10 million dollars.
4. It is not the original asset of the event being rotated.
5. Its own trailing record is complete enough that the selection
   metric below is computable at D.

Selection metric, fixed in advance: trailing leadership is the
126 session close to close log return ending at D, computed from
bars at or before D only. Eligible names are ranked by that metric,
highest first, and the top 20 form the basket. Ties are broken by
higher 63 session mean dollar volume, then by symbol in alphabetical
order, so the rule is deterministic. Basket weights are equal,
1 divided by 20 per member, set at formation.

Holding rule: the basket is formed once, at the decision only. There
is no rebalancing and no reselection between the decision and the
common endpoint. A basket member that leaves the panel before T is
liquidated in the accounting at its last available close and its
proceeds are held as cash to T, flagged; no replacement is bought,
because a replacement would import later information and later
turnover the construction does not claim.

Execution timing: selection uses information through the decision
close D; the transfer trades execute at the close of the next
trading session, D plus 1, at that close. Basket membership is fixed
at D even though execution is at D plus 1. Returns for the basket
leg are measured from the execution close to T.

## 4. The five same capital policies

All five policies are run on the same admitted events, the same
entry, the same allocated capital per event, and the same common
endpoint T. Comparisons are on complete capital paths, never on
trade level averages alone.

Policy A, hold: buy the original asset at entry, hold it to T.
Policy B, cash at repair: hold the original asset until tau; if tau
occurs, sell at the tau plus 1 close and hold cash to T. Cash earns
a zero nominal return in the primary replay, because no risk free
rate series is held in the inventoried data and none will be
invented. If tau does not occur, policy B equals policy A.
Policy C, rotate at repair: hold the original asset until tau; if
tau occurs, sell at the tau plus 1 close and buy the basket formed
at tau, held static to T. If tau does not occur, policy C equals
policy A.
Policy D, basket from entry: form the basket at the entry close
under section 3, buy it at the entry plus 1 close, and hold it
static to T, never holding the original asset.
Policy E, fixed time switch: hold the original asset until the
close of the 21st trading session after the entry session, then
sell at the next session close and buy the basket formed at that
fixed time close, held static to T, regardless of the value of rho
at that time. Policy E exists to test whether the repair observation
itself carries information beyond the mere passage of time.

The incremental terminal wealth of rotating, per event, is as
specified for this construction:

  incremental = V_tau times (R_B minus R_A) minus K

where V_tau is the position value at repair, R_A is the original
asset's subsequent return from the transfer execution to T, R_B is
the basket's (or, for policy B, cash's) return over the same span,
and K is the incremental transfer cost expressed in terminal units,
that is, the cash cost at the trade plus the growth that cash would
have had in the destination leg to T. Gains before tau are common
and cancel, exactly as this formula states.

## 5. Portfolio accounting, complete capital paths

Initial portfolio capital is 1,000,000 dollars, a normalization, not
a claim about any real account. Events are processed in entry date
order. At most 10 positions may be open concurrently; an event that
arrives while 10 positions are open is not admitted, and skipped
events are logged with their dates and names and counted in the
report. Each admitted event is allocated one tenth of the initial
capital, 100,000 dollars, at entry. No leverage, no margin, no
reinvestment of one event's proceeds into another event, and no
sizing change based on any result. Idle cash earns zero.

Charged on every policy, on both sides of every transfer: a cost
per side traded, applied to the dollar amount traded at that trade.
The primary cost is 5 basis points per side. Two registered
sensitivities, 0 and 15 basis points per side, are part of the later
run. Policy A pays entry cost only. Policies B and C pay entry cost
plus both sides of the transfer at tau. Policy D pays entry cost
into 20 basket names. Policy E pays entry cost plus both sides of
its transfer. Basket formation turnover is therefore fully charged:
buying 20 names costs 20 trades in the accounting model, charged as
the per side rate on the total basket amount, and any early
termination liquidation of a basket member or of the original asset
before T is charged the same per side rate.

Reported for every policy, without exception: total terminal wealth
and total return on the initial capital; capital occupation, meaning
the time integral of deployed capital and the mean and maximum
number of concurrent positions; turnover, meaning total dollars
traded divided by initial capital; concentration, meaning the
largest single name weight reached on any date and the share of
terminal profit contributed by the top 5 events; the count of
admitted, skipped, repaired, unrepaired, and early terminated
events; and benchmark exposure context, meaning each policy path's
realized beta to SPY measured over the replay span, reported as
description, never used to adjust the primary verdict.

Delisted names are included to the extent the held panel includes
them (section 8 names exactly how far that goes). Corporate actions:
the deep panel is split adjusted only, with no dividend adjustment,
so all returns in the replay are split adjusted price returns on a
consistent basis for stock, basket, and SPY; no total return claim
will be made. Publication timing: every input is a daily bar dated
on or before the decision that uses it; no fundamental, membership,
or news data enters the primary replay at all, so no publication lag
rule beyond the bar date rule is needed, and any later addition of
such data would require its own amendment before use.

## 6. Statistics and decision rules for the later run

Unit of independence: the calendar quarter of entry. Per event
incremental wealth is reported as a mean with a block bootstrap by
entry quarter, and the portfolio level difference in terminal wealth
is the primary number, with the per event mean as supporting detail.
This ordering is registered because of the archived warning on
record: a fear day stock strategy looked better at trade level while
failing as a capital constrained portfolio, and a particular SPY
core and fear day rotation did not beat SPY. Trade level wins that
do not survive the capital constrained path do not count here.

Primary comparison: policy C terminal wealth minus policy A
terminal wealth, net of the primary 5 basis point per side cost.
Secondary comparisons, all registered now: C minus B (is the basket
better than cash after repair), C minus D (does waiting for repair
beat owning the basket throughout), C minus E (does the repair
timing beat a fixed time switch), and each policy against simply
holding SPY over the same calendar span as context only.

## 7. Falsifier

The switching mechanism has not earned its complexity, and C3 will
be reported as falsified in the form registered here, if any of the
following holds in the later run at the primary cost:

1. Policy C does not exceed policy A in terminal wealth, that is,
   there is no incremental post repair relative value after costs.
2. Policy D terminal wealth is at least policy C terminal wealth,
   that is, a basket held throughout explains the gain and the
   repair wait added nothing.
3. Policy E terminal wealth is at least policy C terminal wealth,
   that is, a fixed elapsed time switch does as well and the repair
   observation itself carries no timing information.

A positive C minus A that fails condition 2 or 3 is reported as a
basket effect or a time effect, not as evidence for repair timed
rotation. No threshold, horizon, basket size, shock size, or cost
assumption may be changed after results are seen to escape this
falsifier; any such change is a new registration and a new trial.

## 8. Data inventory, tonight, named by source

Searched tonight: the morgue data cache panels, the four mechanisms
focus bars, the biotech rotation pull, the board panel, and a
workspace wide search for constituent and membership files. Findings,
concrete and by source:

1. Deep panel, primary candidate source.
   Path: ~/workspace/morgue/data_cache/deep_bars.json
   Shape: one JSON object keyed by symbol, each value a list of
   rows [date, open, high, low, close, volume], split adjusted
   only, no dividend adjustment, no trade count field.
   Recorded coverage, from
   ~/workspace/morgue/data_cache/deep_cure_e/coverage.json and
   ~/workspace/morgue/data_cache/deep_hookup_inactive/coverage.json
   and ~/workspace/research_notes/deep-panel-acquisition-20261029/REPORT.md :
   after the active expansion, 13,575 names and 20,423,755 rows,
   2015-01-02 to 2026-10-28; after the inactive leg merged on
   2026-10-30, a combined 15,815 names and 22,346,713 rows over the
   same date range, with 9,782 names at or above 813 sessions.
   The file on disk tonight is newer and larger than that recorded
   coverage (modified 2026-11-13, 1,150,547,745 bytes), consistent
   with a daily advance past 2026-10-28; the post October counts
   were not re-audited tonight under the light compute rule, and
   the later run must recount before use.
   Delisting coverage, partial and named: the universe was built
   from Alpaca asset snapshots dated 2026-10-30, active
   (assets_active.json) and inactive (assets_inactive.json) in
   ~/workspace/morgue/data_cache/deep_expansion/ . The inactive leg
   requested 18,419 names and obtained bars for 2,240 of them,
   with 16,179 named as residual no bars. A direct key scan of the
   panel tonight found XLNX and AABA present, and BBBY, TWTR, SIVB,
   FRC, and ATVI absent. Names absent from the Alpaca asset list
   entirely, the BBBY and TWTR class, are missing from this panel,
   and no held source supplies them. Symbol identity is the current
   ticker only: a delisted name whose ticker was later reused, or a
   name that changed tickers mid history, is not separated into
   distinct securities anywhere in the held data.
   Membership: there is no historical index or basket membership
   in this source at all. The asset snapshots are current snapshots
   as of 2026-10-30, not point in time membership. The section 3
   basket is computable point in time only because its rules use
   dated bars alone; any index membership version of the basket is
   NOT computable from held data.

2. Board panel.
   Path: ~/workspace/morgue/data_cache/board_bt_bars.json
   Counted tonight: 1,833 names, SPY, QQQ, AAPL, and NVDA each with
   414 sessions, 2025-03-25 to 2026-11-13. Same row shape as the
   deep panel. This is a current board universe with short history:
   survivors only in practice, no delisted names found in it
   (BBBY, TWTR, XLNX, SIVB, and FRC all absent tonight), and far too
   short for the 252 session beta window plus 126 session endpoint
   at any scale. Not a replay source for C3; usable only as a
   cross check of recent prices.

3. Focus bars, four mechanisms cell M1.
   Path: ~/workspace/research_notes/four-mechanisms-20261115/m1/focus_bars/
   Counted tonight: 31 per symbol JSON files, the Focus 30 names
   plus SPY, each a list of daily bars with trade count and volume
   weighted price fields the deep panel lacks. Longest histories
   run 2017-01-03 to 2026-02-13 (2,292 bars, for example AAOI);
   shorter for later listings (CRWV from 2025-03-28, SNDK from
   2025-02-13, ARM from 2023-09-14). This is a fixed current list of
   30 names chosen in 2026, so it is survivors only and current
   only by construction: it cannot form a point in time universe
   for earlier years, and names that left the market are absent.
   Not a replay source for the C3 universe or basket; at most a
   named robustness subset in a later amendment, never the primary.

4. Biotech rotation pull.
   Path: ~/workspace/research_notes/biotech2k-rotation-tests-20261109/data/
   Counted tonight: 101 per symbol JSON files plus _pull_report.json;
   SPY carries 2,728 bars, 2016-01-04 to 2026-11-06, and the pull
   report gives the same span for most names. The file list is a
   current large cap list (index style names and sector funds as
   listed in that directory). Current only selection, no delisted
   names by construction, no membership history. Not a replay
   source for C3 beyond benchmark cross checks.

5. Point in time constituent and membership data.
   Finding: none held. A workspace search for constituent and
   membership files found no historical index constituent table, no
   dated basket membership table, and no point in time universe
   file. The only membership like artifacts found were unrelated
   software teardown files and one psychology engine membership
   notes file, none of which is market data. Historical SPY, QQQ,
   Russell, or any other index membership as of past dates is
   therefore unavailable on this estate, and any basket rule that
   needs it is blocked until such data is acquired; the section 3
   rules were written to need none of it.

6. Delisting and corporate action reference data.
   Finding: no standalone delisting table, no delisting return
   series, and no dividend or corporate action table is held with
   the panels above. Delisting information exists only implicitly,
   as a series ending early inside the deep panel for the 2,240
   inactive names that returned bars. Early termination handling in
   section 2 is written for exactly this limit.

Inventory verdict: the later replay is feasible on the deep panel
for events from 2016 onward, with two named limitations carried into
its verdict: one, the delisted class absent from the Alpaca asset
list is missing, so the event universe is survivorship affected at
its edges even though 2,240 inactive names are present; two, no
point in time index membership exists, so leadership must mean the
rule based basket of section 3 and nothing else.

## 9. Trial ledger and status

Trials charged to C3 so far: 1 (this registration, tonight).
Results: none. Replay: deferred to a later run, as stated above.
Typed spend: $0.00. PII gate: this file contains no personal name,
email, address, or phone number.

STATUS: PARTIAL. The registration and inventory portions are proven
by the read back of this final file; the replay portion is named
open and deferred by design, with its unblocker being a later run
that first recounts the deep panel in its current on disk state.
EVIDENCE POINTER: this file,
~/workspace/research_notes/six-constructions-20261115/C3-RUNFILE.md ,
sections 2 to 7 for the frozen registration, section 8 for the
inventory counts and the named sources behind them.
