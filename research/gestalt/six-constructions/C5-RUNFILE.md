# C5 Runfile, Run 2: Cheapest Live Discriminator, One Pair Audit

Registration time (UTC): 2026-11-15T22:20:40Z
Registration time (ET): 2026-11-15 17:20 ET approx, before pair selection

## Pre-registration statement

This runfile is written and saved BEFORE any price for any candidate pair
has been read by this worker. No snapshot file, market page, order book,
bid, ask, last trade, or volume figure for a candidate pair has been
inspected at the time of this writing. Pair identification in later steps
will use identifiers, titles, targets, and dates only until Step 6 of this
runfile is reached. If a search tool incidentally returns a price in a
snippet before Step 6, that value will not be used, will be named as an
incidental exposure in the audit file, and the executable price read will
still be taken fresh at Step 6 from the primary public source.

Typed spend: $0.00. No Decisions API call is planned or authorized in this
run. Compute: light, local file search and public web reads only.
House rule honored: desk/research/bilbo-options/iv_snapshot.py is not
imported, read, or executed in this run.

## SCOPE

- Surface: this runfile and one audit file, C5-PAIR-AUDIT.md, in this
  program home. No desk code, no other program files, no orders placed.
- Constraints: no trading, no account access, no live browser. Public web
  reads via browser.search and browser.open only. No personal data in any
  file. No em dash characters anywhere.
- Outcome: one actual Kalshi contract pair, on the same underlying, with
  two different targets and, if the corpus allows, two different window
  start dates, audited end to end under Construction C5.
- Proof: rule text quoted or closely paraphrased with its source named,
  history evidence named by source and coverage dates, state enumeration
  derived from verified facts only, and executable prices read only after
  Steps 1 to 5 are recorded.
- Edges: the snapshot corpus may hold no touch style pair. Many Kalshi
  markets are range or terminal above/below markets, not touch markets.
  A non-touch pair is reported as exactly what it is, with an explicit
  statement of whether the C5 state logic still applies, and is never
  forced into the touch template.

## Construction under test, restated

Two contracts each pay $1 for YES on touching an upper target before
expiry. Lower target KL, higher target KH, with KL strictly below KH.
Their monitoring windows may have started on different dates.
Position: buy lower target YES, buy higher target NO.
Terminal payout: L + (1 - H) = 1 + L - H, where L and H are the YES
indicators for the lower and higher contracts.
State table, before any history elimination:
- (L=0, H=0) pays 1
- (L=1, H=0) pays 2
- (L=1, H=1) pays 1
- (L=0, H=1) pays 0
The (0,1) state is admissible unless verified history eliminates it.
Elimination standard, all four conditions required together:
1. Both monitoring windows have already started.
2. Their remaining observation window, end time, settlement source, and
   threshold conventions agree.
3. A complete history from the stipulated settlement source verifies the
   higher target was NOT hit during its distinct earlier window, meaning
   the period when only the higher contract window was open, or any
   period not shared under identical conventions.
4. Given 1 to 3, a future hit above KH is necessarily also a hit above
   KL under the same source and conventions, so (0,1) cannot occur.
Only then does the pair carry a $1 floor. Without that verified fact,
the adverse state stays and the pair is valued with a $0 floor.
A positive cost pair with a conditional floor is not automatically a
feasible arbitrage. Feasibility requires, on a common cash flow clock:
financed value of the minimum payout, minus the full cost stack below,
strictly greater than total acquisition cost at executable size.

## Step plan, in mandatory order

Step 1. This pre-registration. Status: done at the time above.
Step 2. Pair identification. First route: search the workspace on disk
for the estate Kalshi snapshot corpus begun Sat 2026-11-14 (about 639
markets and 163 series in its first snapshot). Record the snapshot home
path exactly. Scan identifiers, titles, targets, and start dates only.
Pick ONE pair: same underlying, two different targets, different start
dates if available, touch style if available. Second route, only if the
corpus holds no usable pair: Kalshi public market data via
browser.search and browser.open, named as the fallback route in the
audit file. Record both tickers or market identifiers exactly as they
appear in the source, character for character.
Step 3. Rule extraction for BOTH contracts, each field separately:
- settlement source (named index, exchange, agency, or data provider)
- observation convention: touch at any time in window, versus terminal
  value at expiry, versus range or other, quoted from the rules
- window start date and time, window end date and time, and time zone
- threshold value and inclusivity (at or above, strictly above, at or
  below, strictly below, as written)
- void, cancellation, and market outcome review rules
- revision rules for the settlement source data
- payout amount, payout timing, and settlement timing after expiry
Any field not found in a primary rule document is recorded as NOT FOUND
with the document that was checked, never filled from assumption.
Step 4. History verification. Standard: only the stipulated settlement
source counts. A third party chart, a news report, or a different data
vendor does not certify the history. Coverage must be complete over the
higher contract distinct earlier window, at the granularity the rules
use (tick, minute, hourly fixing, or daily close, as written). If the
available history ends before today, or starts after the distinct
window opened, or uses a different convention, the verdict is
UNCERTIFIABLE with the exact coverage gap named, and the adverse state
is retained. If the source shows the higher target WAS hit in the
distinct window, the verdict is ELIMINATION FAILS, and the adverse
state is retained on positive evidence.
Step 5. State enumeration. Enumerate only states consistent with the
verified rules and the Step 4 verdict. State the resulting floor:
$1 if and only if (0,1) is eliminated under the standard above,
otherwise $0. If the pair is not touch style, state what the contracts
actually pay on and whether the four state table still maps, maps with
modification, or does not map.
Step 6. Price read, only now. Read both executable sides from the most
primary publicly readable source available: the ask for the lower
target YES contract, and the ask for the higher target NO contract
(equivalently 1 minus the YES bid only if the NO book itself is not
published, and that substitution is named). Record size at the ask if
published, the read time in UTC and ET, and the source URL or file.
If depth or a side is not publicly readable without interaction or
login, record that as a named gap. No price is inferred from a last
trade alone and called executable.
Step 7. Verdict computation, in numbers where Step 6 succeeded.
Cost stack, all items stated even when zero or unknown:
- acquisition cost: lower YES ask plus higher NO ask, per pair
- Kalshi trading fees per its published fee schedule for the series,
  or fee stated as not verified if the schedule is not read
- acquisition impact: zero only if displayed size at the ask covers
  the unit pair; otherwise named as unmeasured
- capital cost: acquisition cost carried from read time to the later
  of the two payout times, at a stated simple rate assumption of
  5 percent per year, shown as a formula and a number
- settlement deductions: any stated fee or deduction in the rules,
  else zero as written
Verdict rule:
- SURPLUS PROVEN: floor is $1, and financed floor value minus the full
  cost stack is strictly greater than total acquisition cost, at a
  size actually displayed. Verdict word GREEN only for this case with
  all numbers shown.
- NO SURPLUS, PRICES CONSISTENT: floor is $1 but cost meets or exceeds
  the financed floor net of the stack. Named with numbers.
- NO FLOOR: Step 4 verdict is UNCERTIFIABLE or ELIMINATION FAILS, so
  the floor is $0 and no positive cost pair can clear it. Named.
- NOT APPLICABLE AS TOUCH: the pair is not touch style and the state
  logic does not map. Named, with what it is instead.
- BLOCKED: a required rule field, the history source, or both
  executable sides cannot be read by any public route tried, with
  each route and its exact failure named.
Verdict words follow InfinityBlade: GREEN proven on the final
artifact, PARTIAL a bounded portion proven with the rest named,
BLOCKED missing access or input with the unblocker named, UNVERIFIED
changed but unproven.

## Trial ledger basis, pre-registered

Trials charged to this cell tonight, counted honestly:
- 1 registration: this runfile, one pre-registered audit design.
- 1 pair audit: the single pair carried through Steps 2 to 7, counted
  as one trial regardless of outcome, including a BLOCKED or NO FLOOR
  outcome.
Total pre-registered count: 2 trials. No additional pair may be
audited under this runfile. If pair identification fails on the first
candidate before any price read and a replacement pair is chosen, the
replacement is still the one pair audit, and the failed identification
is named in the audit file without adding a trial.
