# H3: THE OPPONENT ENGINE, FIRST BUILD (Alpha Hunt workstream H3)

Built: Sat 2026-11-14. Lane: research only, paper and shadow only.
Nothing in this file changes a strategy, a size, a risk setting, or
any desk file. The desk tree was read, never written. Scope line:
surface is this hunt directory only; outcome is a defined and
computed forced-flow proxy, a borrow-fee veto spec, a dated forced
events clock, and a first reading, each with provenance.

Evidence base: designs/OPPONENT-MODEL-EVIDENCE-2026-11-15.md and
the Trade the Forced family (CAND-FORCED-01 through 05 under the
CAND-INV-12 umbrella, registered 2026-11-14). Standing exclusions
carried from that annex without relitigation: VPIN is excluded by
name (failed replication, Andersen and Bondarenko) and is not
computed, not dashboarded, and not used anywhere in this build.
GEX is a regime variable only and is not built in this pass.

## 1. FIT MEASURE v1: WHAT IT ACTUALLY IS, STATED PLAINLY

FIT v1 is a PROXY. It is not the Coval-Stafford FIT, and it must
never be cited under the FIT name without the PROXY label.

The true FIT, per the evidence annex: for each stock, pressure
equals the sum over funds of (fund flow x fund weight in the
stock), from public fund flow data plus lagged holdings. Funds
with extreme outflows cut positions pro-rata, the commonly held
names take price pressure, and liquidity provision to those
forced sellers earned about 6.95 percent per year risk-adjusted
in the lowest holder-heterogeneity quintile, with the reversal
playing out over subsequent quarters.

Those inputs are not on this box. There is no mutual fund flow
series and no fund holdings file anywhere in the local caches
this lane was given (the sleeve-activation research home holds
EDGAR company facts, insider, FINRA ATS, and Wikipedia caches;
none of them is a fund holdings or fund flow source). Rather
than borrow the FIT name for different math, this build defines
and computes FIT-PROXY-v1 from what the box honestly holds:
SIP daily bars.

### FIT-PROXY-v1, the definition in writing

Universe: the Focus 30. Window: the current quarter to date,
Q4 2026, sessions 2026-10-01 through 2026-11-13 (the last
completed session on the box). Benchmark leg: SPY.

For each name and each session in the window:

- Excess return: the name's daily return minus SPY's daily
  return, in percent, on split-adjusted SIP daily bars.
- Volume ratio: the session's volume divided by the mean volume
  of the prior 20 sessions.
- Sigma: the standard deviation of the name's own daily returns
  over the prior 60 sessions (a day is scored only with at least
  20 prior returns on record).
- Pressure day: a session where all three gates hold at once:
  volume ratio at least 1.5, absolute excess return at least
  2.0 percent, and absolute excess return at least 1.0 times
  sigma. Extreme volume plus a return dislocation, the tape
  signature a forced seller or forced buyer leaves behind.
- Day contribution: absolute excess return in percent, times
  (volume ratio minus 1).
- FIT-PROXY-SELL: the sum of contributions over gated down days.
  FIT-PROXY-BUY: the same over gated up days. FIT-PROXY-NET:
  sell minus buy; positive means net forced selling pressure in
  the proxy's terms.

The three gate constants (1.5, 2.0 percent, 1.0 sigma) are round
numbers fixed in writing for v1 before the run. They were not
tuned and not swept, and any future change is a new version with
its own registration, not an edit to this one.

Full per-name scores, every gated day with its tape facts, and
the machine-readable definition live in fit_proxy_v1.json,
computed by hunt/work/compute_fit_proxy.py.

### Data quality: one fabricated reading, caught and voided

The first pass ran on raw (unadjusted) bars and produced a SOXX
sell score of 367.62, six times the next name. It was false. The
raw SIP series prints SOXX at 450.41 on 2026-11-04 and 131.90 on
2026-11-05, a split-scale discontinuity that fabricated a minus
70.7 percent day. A return-based measure cannot run across
splits on raw prices, so the final computation fetches every
name on the estate Alpaca bars CLI with adjustment set to split,
feed sip, and the raw SOXX score is void; it must not be cited.
On split-adjusted bars SOXX scores 31.52 with a quarter return
of minus 21.23 percent, in line with SMH at minus 20.07 percent,
which is what two semiconductor ETFs in the same drawdown should
look like. The desk warm file's 2026-11-13 closes cross-check
clean against the split-adjusted closes for every name the warm
file carries. One route failure inside the cure is also on
record: an unclamped future end timestamp drew Alpaca 403
"subscription does not permit querying recent SIP data" for all
31 symbols; replicating the wave1_bars end clamp (now minus 20
minutes) cured it, and the clamped run is the one reported.

### What the true FIT still needs (dated build row OR-1)

Missing inputs, named exactly: per-fund flows by quarter, lagged
fund holdings (fund by stock weights), and holder heterogeneity
(the concentration conditioner that carries the 6.95 percent
result). The source that would supply them is public: SEC EDGAR
N-PORT filings for fund holdings and EDGAR Form 13F for
institutional holdings, with fund flows derived from EDGAR share
class filings. Build row OR-1, due 2026-12-12: an EDGAR N-PORT
and 13F holdings pull for the funds holding the Focus 30, a flow
derivation, and the true FIT computed for Q4 2026 once the
quarter closes and filings land. Until that row lands, every
forced-flow number in this estate is the proxy, labeled as such.

## 2. BORROW-FEE VETO FILTER: IMPLEMENTABLE SPEC

Status: SPEC ONLY. No borrow-fee series exists on this box, and
the filter vetoes nothing until a real fee source is verified
live. What follows is the spec a builder can implement without
further design decisions, with its thresholds registered as
hypotheses from the evidence annex, not tuned on local data.

### What the evidence says (from the annex, carried verbatim in substance)

Rising fee together with rising loan quantity predicts negative
next-month returns (Cohen, Diether and Malloy 2007). Holders of
high-fee names lost about 20 percent per episode on average,
across 1,200 plus episodes at fees of 25 percent or more, 2005
to 2023 (JFQA 2026). New borrowers pay the marginal fee, not the
average, which cuts short-side strategy returns by about a third
value-weighted and eliminates them equal-weighted (2026 draft).
Rulings carried: the filter is a long exclusion and a short
veto. Direct shorts on fee signals are not an estate strategy.

### Inputs (per name, per week, the fee market's own cadence)

1. Borrow fee, annualized percent, marginal where the source
   distinguishes marginal from average; the field used must be
   named in the output, never blended.
2. Loan quantity: shares on loan, and its 4-week change.
3. Utilisation where the source carries it (shares on loan over
   lendable supply).
4. Fee history: the same fields 4 and 8 weeks back, so "rising"
   is a computed fact, not an impression.

### Candidate sources, none verified live on this box (build row OR-2, due 2026-11-28)

- FINRA short interest (public, biweekly settlement dates, via
  the same FINRA API family the ATS builder already uses):
  supplies loan-quantity direction, not fees. Half the filter.
- A public daily borrow-fee file of the kind Interactive Brokers
  publishes for its securities lending program: candidate fee
  route, to be verified for coverage, licensing, and field
  definitions before any use.
- Commercial securities lending data (for example S&P Global
  Market Intelligence or FIS): the complete route, and a paid
  commitment, so it is a decision for the owner, not this lane.

The local ATS cache is NOT an input and must not be substituted
for one: it is a FINRA ATS weekly dark-pool volume z-score
(finra-ats-weekly-z26-reconstruction) covering 10 names as of
2026-11-13, none of them in the Focus 30. Dark-pool volume is
not a borrow fee and not a loan balance. Naming it as one would
be exactly the borrowed-identity error this workstream exists
to refuse.

### Registered thresholds (hypotheses, fixed before any local data)

- HIGH_FEE: fee at or above 25 percent annualized (the JFQA
  episode threshold).
- RISING: fee up over both the 4-week and the 8-week lookback,
  and loan quantity up over the 4-week lookback.
- LONG VETO fires when HIGH_FEE and RISING both hold: the name
  is excluded from new long entries and flagged for underweight
  review on existing longs. This is the side the evidence sits
  on; the predicted effect is in the left tail (fewer losers),
  not in bigger winners.
- SHORT VETO fires when RISING holds at any fee level: never
  open a short into a rising fee plus a rising loan balance,
  and an existing short in a name that turns RISING is flagged
  for exit review. The marginal-fee result is the reason: the
  short pays more than the average fee advertises, into a
  crowded and appreciating borrow.
- No state between: a name is vetoed or it is not. Missing fee
  data means NOT EVALUATED, printed as such, never treated as a
  pass. Fail-closed on absence, per estate practice.

### Falsifier (registered, from the annex forward test, item b)

Run as a conditioner on existing long books for 6 months,
shadow-logged weekly: the prediction is that applying the LONG
VETO improves long-book excess return by reducing losers, with
the effect concentrated in the left tail of the trade
distribution rather than the mean winner. If, over the 6-month
forward window, vetoed names do not underperform held names, or
the long book's left tail does not improve against the
unfiltered shadow book, the filter is removed, not retuned.
First grading checkpoint: 2027-05-15 (six months from the
2026-11-15 forward test start in the annex).

## 3. FORCED-EVENTS CALENDAR: COVERAGE AND CONFIDENCE

File: forced_events_calendar.json. Window: 2026-11-14 through
2027-05-14, two quarters forward, with later anchors carried in
a separate beyond-horizon section so nothing is silently cut.

Inside the window, 19 dated events:

- Month-end rebalance windows (CAND-FORCED-01): the final three
  sessions of November 2026 through April 2027, six windows,
  with the flow-spent marker (second session of the new month)
  on each. December and March are quarter-end strong forms.
  First window: 2026-11-25, 2026-11-27, 2026-11-30.
- Options expiry Fridays (CAND-FORCED-03): 2026-11-20,
  2026-12-18 (quarterly), 2027-01-15, 2027-02-19, 2027-03-19
  (quarterly), 2027-04-16. Calendar rule, high confidence.
- Russell December 2026 reconstitution (CAND-FORCED-02): the
  first December cycle under the semi-annual regime begun in
  2026. Rank day was 2026-10-30, preliminary lists began
  2026-11-13 with updates 2026-11-20, 2026-11-27 and 2026-12-04,
  effective after the US close on 2026-12-11, new membership
  live 2026-12-14. Source: the LSEG FTSE Russell reconstitution
  page, read today. Confidence high.
- S&P quarterly rebalances: announcement expected 2026-12-04,
  effective before the open 2026-12-21; announcement expected
  2027-03-05, effective before the open 2027-03-22. Source: the
  S&P DJI methodology rule (after the close on the third Friday
  of the quarter month) plus the observed 2026 announcement
  pattern, via secondary sources. Confidence medium-high on the
  effective dates, medium on the announcement dates; the final
  word is the S&P DJI announcement itself.
- Nasdaq-100: annual reconstitution with reference date
  2026-11-30, announcement expected after the close 2026-12-11,
  effective at the open 2026-12-21 (source: Nasdaq-100
  methodology, high confidence); March 2027 quarterly rebalance
  effective at the open 2027-03-22, announcement expected after
  the close 2027-03-12 (rule-derived, medium-high).
- Tax-loss windows (CAND-FORCED-05): harvest pressure over the
  final ten sessions of December 2026, rebound window over the
  first ten sessions of January 2027, both session-counted in
  the file.

Earnings, Focus 30: the desk state earnings_calendar.json was
readable (read only) and is stamped in the file with its own
provenance: generated 2026-11-14T04:23Z from the Nasdaq earnings
calendar API, session 2026-11-13, horizon 100 calendar days, and
its own fresh flag reads false. It dates six Focus names inside
the window: NVDA 2026-11-17 (after the close), MRVL and CRDO
2026-12-01 (after), AVGO 2026-12-09 (after), MU 2026-12-16,
FCEL 2026-12-17. The other 24 names carry null in that file,
which means the file carries no date for them, not that they
have no earnings: most printed in October and November before
the file's forward window, and the February to May 2027 season
is beyond its horizon. That gap is open row OR-3.

Session arithmetic throughout assumes an explicit NYSE holiday
set, listed in the file (Thanksgiving, Christmas, New Year,
MLK Day, Washington's Birthday, Good Friday 2027-03-26,
Memorial Day at the May anchor). The set is an assumption, not
a verified official calendar; verifying it is open row OR-6,
due before the first window it affects.

Beyond-horizon anchors: May 2027 OpEx (2027-05-21) and month-end
window, the Russell June 2027 cycle (rank day expected
2027-04-30, effective expected after the close 2027-06-25,
rule-derived, medium confidence; the provider's 2027 schedule
was not yet published today), the June 2027 S&P and Nasdaq-100
effectives (expected before the open 2027-06-28), and the June
2027 quarterly expiry (2027-06-18).

## 4. FIRST READING: FIT-PROXY-v1 ON THE CURRENT UNIVERSE

29 of 30 names scored. SIVE is unscored: the SIP route returns
zero bars for the Swedish listing (the exact CLI error is
preserved in fit_proxy_v1.json), the same named gap the gestalt
lane carries. No score was invented for it.

The tape context first, because it disciplines everything
below: Q4 2026 to date is a broad semiconductor and AI complex
drawdown. Every scored name shows some gated sell pressure, and
quarter returns run from minus 49.7 percent (AAOI) to plus 10.3
percent (CEG). The proxy therefore ranks relative pressure
inside a falling complex; it does not certify that any single
name's flow was forced rather than informed, and earnings
prints inside the window are a standing confound the proxy
cannot separate. The Coval-Stafford trade form is to provide
liquidity AFTER the pressure quarter, and this quarter does not
end until 2026-12-31, so every name below is a provisional
candidate for the January list, not a completed signal.

Top forced-sale candidates by FIT-PROXY-SELL:

| Name | Sell | Buy | Net | Sell days | Quarter return | Since last sell day |
|---|---|---|---|---|---|---|
| MRVL | 68.70 | 10.36 | 58.35 | 5 | minus 40.67% | plus 17.38% |
| CRWV | 59.82 | 29.70 | 30.12 | 3 | minus 39.02% | minus 4.44% |
| SNDK | 55.57 | 0.00 | 55.57 | 2 | minus 49.13% | plus 9.74% |
| NVDA | 55.25 | 0.00 | 55.25 | 5 | minus 28.69% | minus 2.01% |
| LITE | 53.07 | 4.83 | 48.24 | 4 | minus 38.57% | plus 17.05% |
| ALAB | 50.80 | 9.91 | 40.89 | 5 | minus 37.68% | plus 23.60% |
| WDC | 48.88 | 0.00 | 48.88 | 3 | minus 34.94% | plus 10.47% |
| AAOI | 46.94 | 5.06 | 41.88 | 3 | minus 49.74% | plus 6.40% |

The tape facts behind the top of the list:

- MRVL (z 2.13, the clear leader): five gated sell days
  clustered 2026-10-29 through 2026-11-05, including minus
  12.85 percent excess on 2.05 times ADV (2026-10-29), minus
  12.25 percent excess on 2.67 times ADV (2026-11-02), and
  minus 12.02 percent excess on 2.56 times ADV (2026-11-05).
  Drawdown from the quarter high is minus 47.97 percent. But
  the last pressure day is 2026-11-05 and the name is already
  up 17.38 percent since that close: if this was forced flow,
  the reversal the strategy waits for may already be running,
  eight sessions before the quarter even ends. MRVL prints
  earnings 2026-12-01, inside the remaining quarter.
- CRWV: the single largest day contribution in the universe,
  minus 14.38 percent excess on 3.60 times ADV on 2026-10-14
  (contribution 37.38 of its 59.82 total), then a gated BUY day
  on 2026-11-11 (plus 23.39 percent excess on 2.27 times ADV)
  that cuts its net to 30.12. Two-sided forced flow, or news;
  the proxy cannot tell, and the net rank (tenth, against
  second on the gross sell side) is the honest one for CRWV.
- SNDK: only two sell days, but the second is the largest
  single down day in the complex: minus 17.86 percent excess,
  minus 22.26 percent on the day, on 3.37 times ADV on
  2026-11-05. Quarter return minus 49.13 percent, and up 9.74
  percent since that close.
- NVDA: the most current pressure on the list. Five sell days
  and none older than 2026-10-30, with volume ratios rising
  into the present: 2.95 times ADV on 2026-11-05, 3.92 times on
  2026-11-09, 3.12 times on 2026-11-10, 4.50 times on
  2026-11-12 (748.8 million shares). The name is down 2.01
  percent since its last pressure close, so unlike MRVL and
  ALAB this pressure has not yet reversed. NVDA prints earnings
  2026-11-17, the next session but one, which is both the
  obvious catalyst confound and the reason no conclusion is
  drawn tonight.
- LITE and ALAB: four and five sell days respectively, each
  with a capitulation-scale day (LITE minus 18.11 percent
  excess on 2.94 times ADV, 2026-11-02; ALAB minus 15.21
  percent excess on 2.74 times ADV, 2026-11-05), and each
  already up sharply since (17.05 and 23.60 percent). Same
  reading as MRVL: pressure in the past tense.
- WDC and AAOI: clean one-sided profiles (buy scores 0.00 and
  5.06), deep quarter losses, early reversals underway (plus
  10.47 and plus 6.40 percent since the last sell day).

The other side of the book, for completeness: the largest
forced-BUY pressure sits in OKLO (buy 52.30, net minus 39.57)
and CEG (buy 49.31, net minus 38.88, quarter return plus 10.31
percent). Under the annex, fire purchases are the short
side of the original study, and this estate does not run
direct shorts on flow signals; these names are recorded as
context, not candidates. The lowest sell pressure in the
universe is PLTR (4.62), then XLE (9.33) and AVGO (11.41).

Forward grading, registered now so the reading can be wrong in
public: recompute FIT-PROXY-v1 on the completed quarter at
2026-12-31, take the top-quintile sell names as the provisional
liquidity-provision list, and grade their excess return versus
SPY over the following two quarters against the bottom half of
the universe, first checkpoint 2027-04-03 and final grade
2027-07-03. The annex prediction stands: any effect appears on
a quarterly horizon, not weekly. If the top quintile does not
outperform, the proxy joins VPIN on the refused list.

## 5. OPEN ROWS (all named, all dated)

- OR-1, true FIT build from EDGAR N-PORT and 13F holdings plus
  a derived fund flow series, including the heterogeneity
  conditioner. Due 2026-12-12 for construction; Q4 2026 true
  FIT computable only after quarter-end filings land in
  January 2027.
- OR-2, borrow-fee data route verification (FINRA short
  interest route and the public borrow-fee file route, coverage
  and field definitions proven on a sample pull). Due
  2026-11-28. The veto filter stays spec-only until this lands.
- OR-3, Focus 30 earnings dates for the February to May 2027
  season; the desk calendar file's horizon ends near
  2027-02-21 and its fresh flag reads false. Refresh due
  2027-01-16, before the season opens.
- OR-4, SIVE price source: the SIP route serves zero bars for
  the Swedish listing. A non-SIP source must be registered
  before SIVE can be scored; carried from the gestalt lane.
  Due 2026-12-05.
- OR-5, Russell June 2027 provider schedule: rule-derived dates
  in the calendar are medium confidence until FTSE Russell
  publishes the 2027 schedule. Recheck due 2027-03-01.
- OR-6, NYSE holiday assumption set in the calendar file:
  verify against the official NYSE calendar before the first
  affected window (the November month-end window opens
  2026-11-25). Due 2026-11-20.
- OR-7, FIT-PROXY forward grading as registered in section 4:
  recompute at quarter end 2026-12-31, checkpoints 2027-04-03
  and 2027-07-03.

## STATUS

PARTIAL, with the bounded portion proven and the rest named.
Proven on the final artifacts: FIT-PROXY-v1 defined in writing
and computed for 29 of 30 Focus names on split-adjusted SIP
bars (fit_proxy_v1.json, with the raw-bar SOXX fabrication
caught, voided, and cured at the source); the borrow-fee veto
spec complete and implementable (section 2); the forced-events
calendar built for two quarters with per-event source and
confidence (forced_events_calendar.json); the first reading
reported with tape facts (section 4). Named open: the true
Coval-Stafford FIT (OR-1, blocked on fund holdings and flow
data that is not on the box, source and build date named), the
borrow filter's live data (OR-2), earnings coverage past
February 2027 (OR-3), SIVE (OR-4), and the verifications and
forward grades in OR-5 through OR-7. VPIN computed nowhere.
Evidence pointer: hunt/fit_proxy_v1.json and
hunt/forced_events_calendar.json, read back after writing.
