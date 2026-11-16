# C5 Pair Audit, Run 2

Audit date: Sun 2026-11-15. Worker: leaf worker, no delegation.
Pre-registration: C5-RUNFILE.md in this program home, registered
2026-11-15T22:20:40Z, before any pair price was read.
Typed spend: $0.00.

## Step 2. Pair identification

Snapshot corpus found on disk at:
~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave7/eventmarkets/
Files: 2026-11-15.json (captured 2026-11-15T01:20:42-05:00, 639 markets,
163 series included, 68 series with open events), discovery_2026-11-15.json,
SCHEMA.json. Writer: w7c_event_snapshot.py, daily cron
w7-eventmarkets-snapshot-daily, source Kalshi public API.

Corpus structure finding: the snapshot captured the nearest event per
series (all open events only for the recession family). Touch style
(extremum) series present: KXU3MAX, KXHIGHINFLATION, KXLCPIMAXYOY,
KXGDPUSMAX. Within the snapshot file, every extremum series carries
exactly one captured event, so no two contracts in the file have two
different window start dates, and the file carries no rule fields and
no open_time field at all (see SCHEMA.json market_fields). The pair
below was identified in the snapshot by ticker, title, subtitle, and
close_time only; its rule fields, open times, and history were then
completed from the snapshot's own named source, the Kalshi public API
and Kalshi contract terms PDFs. That completion route is named here,
not hidden.

Chosen pair, identifiers exactly as they appear in the snapshot and
confirmed character for character in the Kalshi public API:

- Lower target contract (KL = 4.5 percent):
  Ticker: KXLCPIMAXYOY-27-P4.5
  Event: KXLCPIMAXYOY-27
  Series: KXLCPIMAXYOY
  Title as served: Inflation surge in 2026?
  Subtitle as served: At least 4.5%
  Snapshot close_time: 2027-02-14T13:29:00Z
- Higher target contract (KH = 5.0 percent):
  Ticker: KXHIGHINFLATION-26DEC-T5.0
  Event: KXHIGHINFLATION-26DEC
  Series: KXHIGHINFLATION
  Title as served: How high will CPI get this year?
  Subtitle as served: Above 5.0%
  Snapshot close_time: 2027-01-01T13:29:00Z

What the pair actually is, stated plainly: neither contract is a
continuous price touch contract of the index or crypto kind. Each is a
discrete extremum contract on a monthly data series: it pays $1 for
YES if any monthly BLS CPI year-over-year report attributed to 2026
crosses its threshold. The underlying observation is a sequence of
monthly prints, not a continuous path. The C5 state logic maps onto
this pair without modification, because the payout of each contract is
still a single YES indicator driven by whether a monotone threshold on
the same underlying was crossed at any observation inside its window,
and the position is still buy lower YES plus buy higher NO with payout
1 + L - H. The one adaptation: "hit" means a monthly report crossing
the threshold, and "history" means the sequence of reports already
released.

Position under audit: buy 1 x KXLCPIMAXYOY-27-P4.5 YES, buy 1 x
KXHIGHINFLATION-26DEC-T5.0 NO. Payout 1 + L - H dollars.

Incidental exposure note, per the runfile: the Kalshi API market
object bundles price fields with rule fields, so the rule extraction
reads in Step 3 incidentally displayed API price fields timestamped
2026-11-15 22:22 to 22:23 UTC. Those values are not used anywhere in
this audit. The executable price read is taken fresh in Step 6, after
Steps 3 to 5 were recorded, from the API market and orderbook
endpoints.

## Step 3. Rule fields, both contracts

Sources: Kalshi public API market and series objects (read
2026-11-15 22:22 to 22:24 UTC), Kalshi contract terms PDFs LCPIYOY.pdf
(for KXLCPIMAXYOY) and ECONSTAT.pdf (for KXHIGHINFLATION, named as the
contract_terms_url in the KXHIGHINFLATION series object), and the
Kalshi market page for event KXHIGHINFLATION-26DEC.

### Lower contract, KXLCPIMAXYOY-27-P4.5

- Settlement source: Bureau of Labor Statistics. Series object
  settlement_sources: Bureau of Labor Statistics, https://www.bls.gov/cpi/.
  LCPIYOY terms: Source Agency is the Bureau of Labor Statistics.
  Underlying: the set of signed one-month percent changes in the
  seasonally unadjusted CPI-U published by BLS for each month in the
  period, measured year-over-year. In practice the first sentence of
  each monthly BLS report (for example "Over the last 12 months, the
  all items index increased 3.1 percent before seasonal adjustment").
- Observation convention: extremum over monthly reports, the discrete
  analogue of touch. Market rules_primary, verbatim: "If
  year-over-year CPI inflation is at least 4.5% in any month in 2026,
  then the market resolves to Yes."
- Window start: period is the months of calendar 2026, first report
  the January 2026 report. Market open_time 2026-01-15T15:00:00Z,
  created_time 2026-01-14T23:09:54.748819Z (API fields).
- Window end: close_time 2027-02-14T13:29:00Z. Terms: Last Trading
  Date is the sooner of the first 8:31 AM ET after a payout event
  occurs, or the day the data for the last month of the period is
  expected to be released (Last Trading Time 8:29 AM). API
  expected_expiration_time 2027-02-14T15:00:00Z, expiration_time
  2027-02-28T13:31:00Z.
- Time zone: release and expiration conventions in ET (BLS releases
  8:30 AM ET; expiration time 8:31 AM ET per terms). API timestamps
  are UTC.
- Threshold inclusivity: at least 4.5 percent, greater than or equal,
  per rules_primary and subtitle "At least 4.5%". Named tension: the
  API field strike_type reads "greater" and the LCPIYOY PDF payout
  template reads "<above/below>", while the market level rules_primary
  and subtitle both read "at least". The market level text governs
  trading; the tension does not affect this audit because the higher
  contract requires strictly above 5.0, which satisfies either reading
  of the 4.5 line.
- Void and review rules: terms Contingencies: before Settlement,
  Kalshi may at its sole discretion initiate the Market Outcome Review
  Process under Rule 6.3(c). can_close_early is true; early close
  condition as served: "If this event occurs, the market will close
  the following 8:31am ET."
- Revision rules: terms Underlying: "Revisions to the Underlying made
  after Expiration will not be accounted for in determining the
  Expiration Value." Government shutdown clause: on a data delay
  caused by a federal shutdown impacting source reliability, the
  latest Expiration Date extends to the sooner of the release of the
  Underlying or six months after the end of the shutdown.
- Payment timing: Settlement Value $1.00. Terms: Settlement Date no
  later than the day after the Expiration Date unless the outcome is
  under review under Rule 7.1. API settlement_timer_seconds 3596
  (about 60 minutes after expiration determination).

### Higher contract, KXHIGHINFLATION-26DEC-T5.0

- Settlement source: Bureau of Labor Statistics. Series object
  settlement_sources include Bureau of Labor Statistics, Consumer
  Price Index, https://www.bls.gov/news.release/cpi.nr0.htm (and a
  BLS Employment Situation entry used by other stats in the same
  ECONSTAT family). ECONSTAT terms: Source Agencies are, in
  hierarchical order, the statistical agency responsible for the
  statistic (here BLS), then Trading Economics as fallback.
- Observation convention: extremum over monthly reports, same
  discrete touch analogue. Market rules_primary, verbatim: "If any
  Consumer Price Index (CPI YoY) report is above 5.0% for 2026, then
  the market resolves to Yes." ECONSTAT temporal operator "for": the
  value must correspond to a statistic attributed to the specified
  period, regardless of when it is released. Attribution, not release
  timing, defines the window.
- Window start: period is calendar 2026 reports, first report the
  January 2026 report, counted regardless of release date per the
  "for" operator. Market open_time 2026-06-03T22:00:00Z,
  created_time 2026-06-03T21:02:25.929678Z (API fields). This is the
  different start date: the higher contract was created and opened
  about four and a half months AFTER the lower contract (2026-01-15).
  The dangerous C5 direction (higher window starting earlier) is
  reversed here, and under the "for" operator neither contract's
  observation window is truncated by its listing date.
- Window end: close_time 2027-01-01T13:29:00Z. Kalshi market page:
  "it closes by Jan 1, 2027 at 8:29am EST" if the event has not
  occurred. API expected_expiration_time 2027-01-01T15:00:00Z,
  expiration_time and latest_expiration_time 2027-04-02T15:00:00Z.
  ECONSTAT terms: latest Expiration Date is three months after the
  scheduled release date for the period; expiration time 10:00 AM ET.
  Named tension: the market level fields point to Jan 1, 2027, which
  precedes the December 2026 CPI release (scheduled Jan 2027), while
  the generic ECONSTAT terms would allow expiration as late as
  2027-04-02. Either reading is safe for this audit: if the December
  report is outside the higher window, the higher window is a strict
  subset of the lower window; if it is inside, it is also inside the
  lower window (lower closes 2027-02-14). No reading puts a higher
  contract observation outside the lower contract window.
- Time zone: ET conventions (expiration time 10:00 AM ET per terms;
  15:00 UTC expected expiration matches 10:00 AM EST). API timestamps
  are UTC.
- Threshold inclusivity: strictly above 5.0 percent. Subtitle "Above
  5.0%"; ECONSTAT operator definitions: "Above" means greater than
  (>); floor_strike 5.
- Void and review rules: terms Contingencies: Market Outcome Review
  Process under Rule 6.3(d); if an Expiration Value cannot be
  determined on the Expiration Date, Kalshi may determine payouts
  under Rule 6.3(b). can_close_early is true; early close condition
  as served: "This market will close and expire early if the event
  occurs."
- Revision rules: ECONSTAT Payout Criterion: "only the first
  non-preliminary release of the relevant econ stat will be used to
  resolve the market, and subsequent revisions will not affect
  resolution", and Underlying: revisions made after Expiration will
  not be accounted for. CPI is a non-preliminary release; the first
  release figure governs.
- Payment timing: Settlement Value $1.00. Terms: Settlement Date no
  later than the day after the Expiration Date unless under review.
  API settlement_timer_seconds 1800; Kalshi market page: "Projected
  payout 30 minutes after closing."

### Rule agreement check (C5 elimination condition 2)

- Same underlying measure: yes. Both are the BLS seasonally
  unadjusted CPI-U 12-month percent change, read from the monthly
  BLS report.
- Same settlement source: yes, BLS for both (ECONSTAT adds Trading
  Economics as a hierarchical fallback for the higher contract only;
  named, and immaterial while BLS publishes).
- Same remaining window at the end: no, and the divergence is in the
  safe direction. The higher window ends at or before 2027-01-01
  expected expiration; the lower window runs to 2027-02-14 and covers
  every 2026 month including December. The higher contract observes
  no 2026 report the lower contract does not.
- Threshold conventions: different words (at least 4.5 versus above
  5.0) but strictly monotone: any report above 5.0 is a report at
  least 4.5. No state can cross the higher line without crossing the
  lower line on the same report.

## Step 4. History verification

Standard (from the runfile): only the stipulated source, BLS, at the
rule granularity, which is the one-decimal 12-month percent change in
the first sentence of each monthly BLS CPI report.

What must be verified: whether any BLS CPI YoY report attributed to
2026, released up to today (Sun 2026-11-15), was above 5.0 percent.
The reports released before the higher contract existed (January
through April 2026 reports, released 2026-02-13 through 2026-05-12)
are the closest analogue of a distinct earlier window in this pair,
and they count for the higher contract under its "for" operator, so
they are checked, not skipped.

BLS 12-month all items percent changes for 2026, as published in the
monthly BLS releases and cross-checked in three independent tables
built from BLS data (release calendar table, tracker table, and
index table, all citing BLS CPI-U not seasonally adjusted):
- January 2026: 2.4 percent (released 2026-02-13)
- February 2026: 2.4 percent (released 2026-03-11)
- March 2026: 3.3 percent (released 2026-04-10)
- April 2026: 3.8 percent (released 2026-05-12)
- May 2026: 4.2 percent (released 2026-06-10)
- June 2026: 3.5 percent (released 2026-07-14)
- July 2026: 3.4 percent (released 2026-08-12)
- August 2026: 3.4 percent (released 2026-09-11)
- September 2026: 3.7 percent (released 2026-10-14)
- October 2026: NO 12-month figure exists. BLS news release
  USDL-26-1685 (embargoed 2026-11-10) states verbatim in substance:
  BLS did not collect survey data for October 2025 because of a lapse
  in appropriations, so BLS cannot publish 12-month percent changes
  for October 2026. The October report therefore cannot be a report
  above 5.0 percent on the stipulated source. A third party estimate
  of about 4.0 percent exists but is not the stipulated source and is
  not relied on.

Maximum published 2026 value: 4.2 percent (May 2026). No released
2026 report was above 5.0 percent, and none reached 4.5 percent
either, so neither contract has triggered yet; both are still live
on the November 2026 report (scheduled release 2026-12-10) and, for
the lower contract, the December 2026 report (scheduled Jan 2027).

History verdict: VERIFIED for every month for which the stipulated
source publishes a figure, with one named source fact, not a gap in
effort: October 2026 has no BLS 12-month figure by BLS's own
statement, so there is no BLS report for October that could carry a
value above 5.0. The higher target was NOT hit in any already
released report, including all reports released before the higher
contract was created.

## Step 5. State enumeration

Remaining observations that can change either indicator: the
November 2026 report (in both windows) and the December 2026 report
(in the lower window on every reading; in the higher window only
under the generic ECONSTAT latest expiration reading, and still
inside the lower window). Every future report that could put the
higher indicator to 1 (a value above 5.0) is a report inside the
lower window with a value at least 4.5, which puts the lower
indicator to 1 on the same report. The October no-figure fact cannot
create a higher hit, per Step 4.

Admissible states for (L, H), payout 1 + L - H:
- (0,0) pays 1: admissible (no remaining report reaches 4.5).
- (1,0) pays 2: admissible (a remaining report lands at least 4.5
  and none lands above 5.0).
- (1,1) pays 1: admissible (a remaining report lands above 5.0).
- (0,1) pays 0: ELIMINATED, on the combined evidence of Step 3
  (same source, same measure, higher window a subset of the lower
  window at the end, no truncation at the start under the "for"
  operator, strictly monotone thresholds) and Step 4 (no already
  released report above 5.0, and no BLS October figure exists that
  could be one).

Floor: $1.00 per pair, conditional on Kalshi honoring its own rule
texts (market outcome review under Rule 6.3 is a named residual risk
on both legs, as is any settlement deduction, of which the terms name
none).

Timing of the floor on a common cash clock: in state (0,0) the $1
arrives from the higher NO leg at the higher settlement, expected
2027-01-01 plus about 30 minutes. In state (1,1) the $1 arrives from
the lower YES leg at its early close, the first 8:31 AM ET after the
triggering release, which is earlier. The binding (latest) floor
arrival is therefore about 2027-01-01, which is 47 days after the
audit date 2026-11-15. Financed floor value at the runfile rate of
5 percent per year simple: 1.00 / (1 + 0.05 x 47/365) = $0.9936.

## Step 6. Executable price read (taken only after Steps 3 to 5 above)

Read time: 2026-11-15T22:24 UTC (17:24 EST), fresh reads from the
Kalshi public API orderbook endpoints for both tickers, cross-checked
against the API market objects. The orderbook endpoint returns bids
on both sides; a YES ask equals 1 minus the best NO bid, and a NO ask
equals 1 minus the best YES bid. Sizes below are the resting sizes at
those best bids, which are the executable quantities for a taker.

- Lower contract KXLCPIMAXYOY-27-P4.5:
  Best YES bid 0.0710, size 204.22. Best NO bid 0.9110, size 134.98.
  Executable YES ask: $0.089, depth 134.98 contracts.
- Higher contract KXHIGHINFLATION-26DEC-T5.0:
  Best YES bid 0.0200, size 122.63. Best NO bid 0.9600, size 1526.05.
  Executable NO ask: $0.980, depth 122.63 contracts.
- Executable pair size at top of book: 122.63 pairs (the smaller
  depth). A one pair unit trade sits far inside displayed depth, so
  acquisition impact for the unit pair is $0.00 as displayed.

## Step 7. Verdict in numbers

Per pair (1 lower YES plus 1 higher NO), floor $1.00 from Step 5:
- Acquisition cost: 0.089 + 0.980 = $1.0690
- Trading fees: both series carry fee_multiplier 1 and fee_type
  quadratic in the Kalshi API, and the Kalshi fee schedule formula
  for a taker is round up(M x 0.07 x C x P x (1 - P)). Lower leg:
  0.07 x 0.089 x 0.911 = $0.005676, rounds up to $0.01 on a one
  contract order. Higher NO leg: 0.07 x 0.980 x 0.020 = $0.001372,
  rounds up to $0.01. Total fees, one pair as two one contract
  orders: $0.0200. (At 100 pairs in single orders the same formula
  gives $0.57 plus $0.14 = $0.71, or $0.0071 per pair; the verdict is
  identical either way.)
- Acquisition impact: $0.0000 at displayed depth for a unit pair.
- Capital cost: $1.0690 carried 47 days at 5 percent per year simple
  = 1.0690 x 0.05 x 47/365 = $0.0069.
- Settlement deductions: $0.0000. Neither contract's terms name any,
  and the Kalshi fee schedule carries no settlement fee.
- Total cost stack on top of acquisition: $0.0269.
- Financed floor value: $0.9936 (Step 5).

Net per pair: 1.0000 - 1.0690 - 0.0200 - 0.0069 = minus $0.0959
undiscounted, equivalently financed floor 0.9936 versus total
acquisition outlay 1.0890, a shortfall of $0.0954 per pair. The pair
costs about 9.5 to 9.6 cents MORE than the guaranteed $1 it returns.
The gross gap alone (acquisition 1.0690 versus floor 1.0000) is
$0.0690, so the negative verdict does not depend on any fee, impact,
or capital assumption.

Final verdict: NO SURPLUS, PRICES CONSISTENT (runfile verdict rule).
The conditional $1 floor is real and proven in Steps 3 to 5, and the
market already charges more than the floor is worth: the higher NO
leg alone costs $0.980 against a pair floor of $1.000, leaving only
$0.020 of room for the lower YES leg, which is offered at $0.089.
No feasible arbitrage exists in this pair at the read prices and
depths. Under the runfile, GREEN was reserved for SURPLUS PROVEN and
is not claimed; the audit itself is complete with every row closed.

Residual risks named, not hidden: Kalshi market outcome review
(Rule 6.3) on either leg; the ECONSTAT Trading Economics fallback if
BLS ceased publishing; the higher contract expiration tension named
in Step 3 (immaterial to the floor, and immaterial to this verdict,
which is driven by price).

## Trial ledger

Trials charged to Cell C5 tonight: 2.
- 1 registration: C5-RUNFILE.md, one pre-registered audit design,
  written before any pair price was read.
- 1 pair audit: this audit of KXLCPIMAXYOY-27-P4.5 plus
  KXHIGHINFLATION-26DEC-T5.0, counted once regardless of its negative
  outcome.
No other pair was audited. No price was read before registration;
the one incidental exposure (API rule objects bundling price fields
at 22:22 to 22:23 UTC) is named in Step 2 and none of those values
is used in Step 6 or Step 7.

STATUS: PARTIAL by the runfile's own verdict rule (GREEN reserved for
a proven surplus; the proven result is NO SURPLUS, PRICES CONSISTENT,
shortfall $0.0954 to $0.0959 per pair). EVIDENCE POINTER: this file,
Steps 3 to 7, and C5-RUNFILE.md, both in
~/workspace/research_notes/six-constructions-20261115/.
