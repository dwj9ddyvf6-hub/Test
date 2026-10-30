# Psychology Engine: Design

Commissioned by the owner, 2026-10-30. Design stage only. Nothing in this document
changes any desk sleeve, any sizing rule, or the Tensor engine. The engine is
an information system. Its consumers are Midna's own book (her pre-open read
and her trade cards) and one terminal reader page.

Inputs to this design, both verified against the files on disk at design time:

* `STUDY-THEORY.md` in this folder (159,189 bytes, 538 lines). Cited below as
  THEORY, with its section and proposition numbers (P1 to P22).
* `STUDY-MEASUREMENT.md` in this folder (102,346 bytes, 366 lines). Cited
  below as MEASUREMENT, with its Part 1 estate census, Part 2 catalog
  families (a) to (h), and Part 3 ranked shortlist items 1 to 10.

Where this design states an archive depth, the VERIFIED or UNVERIFIED label
is carried over from MEASUREMENT Part 2 unchanged. An UNVERIFIED depth is a
lead the build must confirm at download time and record, never a fact the
design asserts.

## SCOPE

* Surface: a new program at `~/workspace/psychology-engine/` containing
  collectors, a history store, a gauge compiler, a forecast ledger interface,
  daily outputs, calibration exhibits, and a terminal page feed. Plus one
  consumer file written daily into `~/workspace/midna-book/`.
* Constraints, untouched: every desk sleeve, all sizing, the Tensor engine,
  Midna's risk constitution in `~/workspace/midna-book/CHARTER.md`, and the
  estate forecast engines and their machinery except where this design joins
  them as a user (Section 5).
* Outcome: a daily Psychological State, built from nine named gauges, each
  gauge shown with its current percentile in its own backfilled history,
  plus 2 to 4 falsifiable forecasts per Section 4 of this design, graded on
  the estate ledger discipline.
* Proof: the acceptance tests in Section 7, run against the final built
  state. A gauge is not done because its collector ran. It is done when its
  stored history, its bands, its reconstruction exhibits, and its live daily
  value all check out as specified there.
* Edges: free and public sources only, plus keys the desk already holds
  (Alpaca, TastyTrade read-only, Coinalyze). Paid sources named in
  MEASUREMENT (Investors Intelligence depth, Bank of America Fund Manager
  Survey, EPFR, Lipper detail, RavenPack, X firehose, full transcript
  archives) are named gaps in this design. They are never silently replaced
  by a substitute that measures something else.

## The four standing rules

These come from the commission and from the two studies. Every later section
is an application of them.

1. History ruling (the owner, 2026-10-30): historical INPUT data is backfilled as
   deep as the real published record honestly goes, from the original
   sources, with provenance per series. Gauges are calibrated on that
   history. Percentile bands, extreme zones, and regime history come from
   the backfilled distribution, never from a cold start.
2. Reconstruction label: a historical gauge value computed from historical
   inputs with a formula written today is a RECONSTRUCTION wherever it
   appears: in the store, in exhibits, on the page, in the consumer file.
   It is never presented as a forecast the engine made at the time.
3. The one line that never moves: the forecast and outcome ledger is never
   backfilled. A prediction exists only if it was written before its
   horizon. Backfilled inputs calibrate gauges. They do not create a track
   record. Historical propositions may be tested on the history store only
   in the separate backtest record defined in Section 4.4 of this design.
4. Independence accounting (MEASUREMENT Part 2, cross-family trap 4, and the
   estate Second Opinion rule): channels that share inputs cast one vote,
   not two. CNN Fear and Greed is a context tile, never a gauge of record,
   because it is built from inputs this engine already counts. The modelled
   IV ledger, the Morgue Map, and any other modelled estate lane is labelled
   modelled wherever it feeds a gauge.

## Uniform conventions for all gauges

These conventions are stated once here and apply to every gauge in
Section 1. A gauge section may add gauge-specific rules. It may not quietly
override these.

### Orientation

Every mood gauge is oriented so that a high value means risk seeking,
confident, greed-side crowd behaviour, and a low value means fearful,
risk-averse, capitulation-side behaviour. Inputs that naturally run the
other way (put/call ratios, VIX, credit spreads, bearish share) are inverted
at ingestion, and the inversion is written in the gauge formula, not left to
the reader. Two gauges are not mood gauges and keep their own orientation,
stated on their face wherever they appear:

* G4 Leverage and Fragility: high means fragile, meaning a given adverse
  move forces more flow. It is a second axis, never averaged into mood.
* G8 Belief Markets: values are event probabilities, not mood scores. It is
  never averaged into mood either.

### Percentile rule (the only percentile rule in the engine)

For gauge `g` and date `t`:

    percentile(g, t) = 100 * (number of historical observations of g
                       on dates <= t with value <= value(g, t))
                       / (number of historical observations of g
                       on dates <= t)

* The historical set is the gauge's stored reconstruction series plus its
  live series, in date order. For a live reading, the set includes every
  observation up to and including the prior observation, and the current
  value is ranked against that set plus itself, exactly as the formula
  says. No observation dated after `t` is ever in the set. Bands never use
  the future relative to the reading being banded (MEASUREMENT Part 2,
  cross-family trap 3).
* A gauge shows NO BAND, with the words `insufficient history`, until its
  stored series holds at least 250 observations at its native cadence, or,
  for monthly gauges, at least 120 monthly observations. The value still
  displays. The percentile does not.
* Percentiles are computed on the full stored history, not on a trailing
  window, because the commission is calibration on the whole honest record.
  One exception, stated where it applies: the options gauge also reports a
  trailing 3 year percentile, because THEORY Section 3.3 documents
  structure breaks in put/call behaviour in 2020 and 2022, and P5 is
  written against a trailing 3 year 95th percentile. Both percentiles
  display, labelled `full history` and `trailing 3y`. They are never
  averaged together.

### Reading scale (the only zone table in the engine)

Applied to the full-history percentile of an oriented mood gauge:

| Percentile | Zone name |
|---|---|
| 0 to 2 | Extreme fear |
| 2 to 5 | Severe fear |
| 5 to 20 | Fear |
| 20 to 40 | Cautious |
| 40 to 60 | Neutral |
| 60 to 80 | Confident |
| 80 to 95 | Greed |
| 95 to 98 | Severe greed |
| 98 to 100 | Extreme greed |

Extreme means the deepest few percent of the actual backfilled record, by
construction of this table. For G4 the same percentile bands carry the
labels: 95 to 100 `Extreme fragility`, 80 to 95 `High fragility`, 40 to 80
`Ordinary leverage`, 5 to 40 `Low leverage`, 0 to 5 `Minimal leverage`. For
gauges whose native cadence is monthly or weekly, the zone is computed from
the latest published observation and carries its true as-of date (see the
clock rule next).

### Clock rule

Every input enters the daily state with its true as-of date, never its
download date (MEASUREMENT Part 2, cross-family trap 2; the same clock
lineage the estate forecast ledger already enforces). A Tuesday COT
position published Friday enters as Tuesday's position. A Michigan final
print enters as a reading about the month it describes. If an input is
older than two of its own cadence periods at state time, the gauge tile
flags it `stale` and prints the as-of date. Stale is a factual state, not
an apology, and it never blocks the rest of the state.

### Absence rule

A missing input is stored and displayed as absent, named, never as zero.
This is the estate forecast ledger convention (MEASUREMENT Part 1.2) and it
applies to every store, gauge, and page in this program. A gauge with a
missing core input computes from its remaining inputs only if its formula
below says so, and flags `partial` with the missing input named.

---

# 1. THE GAUGE SET

Nine gauges. Six are core mood gauges and vote in the composite
(G1, G2, G3, G5, G6, G7). One is the fragility axis (G4). One is the belief
anchor (G8). One is the overnight transfer panel (G9). G8 and G9 display
from day one and vote in nothing until their own ledger grades, recorded
through the forecast hooks in Section 4, argue otherwise. That exclusion is
the MEASUREMENT shortlist ranking rule applied honestly: social and belief
channels are collected from day one because uncollected history is
unrecoverable, and they are ranked out of the v1 composite because their
estate history starts at collection.

Each gauge below states: what it measures, its exact inputs, its
computation, its cadence, and its reading scale. Reading scale means the
uniform zone table above unless the gauge says otherwise.

## G1. What People Say (stated sentiment)

* What it measures: what investors say they expect, in surveys, before any
  money moves. Stated belief, type SB in MEASUREMENT terms, with NAAIM
  shading to revealed positioning because respondents report exposure they
  claim to hold.
* Exact inputs, all FREE:
  * AAII Sentiment Survey weekly spreadsheet (bullish, bearish, neutral
    shares), AAII public download. Archive July 1987, VERIFIED.
  * NAAIM Exposure Index weekly file (mean, median, quartiles, respondent
    dispersion), NAAIM public file, published Thursday for Wednesday
    exposure. Archive July 2006, VERIFIED.
  * AAII neutral share, from the same AAII file, stored as the confusion
    proxy per MEASUREMENT Part 3, idea 3.10.
  * Investors Intelligence is NOT an input. It is PAID. It is named here as
    the gap, per MEASUREMENT family (a).
* Computation:
  * `aaii_spread = bullish_pct - bearish_pct`, weekly.
  * `naaim_mean` as published, weekly. NAAIM is structurally bullish
    (historical median near 72 percent long per MEASUREMENT family (a)),
    so its raw level is never thresholded. Only its percentile is read.
  * Sub-scores: the full-history percentile of `aaii_spread`, and the
    full-history percentile of `naaim_mean`, each on its own history.
  * Gauge value: the mean of the available sub-score percentiles. If one
    survey is missing for a week, the gauge computes from the other and
    flags `partial`.
  * Stored alongside, never inside the gauge value: NAAIM dispersion
    (interquartile range as published) and AAII neutral share, displayed
    as the disagreement line. Rising dispersion at a flat mean is a
    headline fact on the tile, per idea 3.10.
* Cadence: weekly, updated on the Thursday publications, carried into every
  daily state with its as-of Wednesday date.
* Reading scale: uniform zone table on the gauge percentile. Tile also
  prints both raw inputs (the spread, the NAAIM mean) so no reader has to
  trust the composite blind.

## G2. Slow Climate (the regime spine)

* What it measures: the slow mood of households and the slow speculation
  climate of the market itself, at monthly frequency. This gauge sets the
  regime context inside which every faster gauge is read. It is
  MEASUREMENT shortlist item 7, and it is the deepest history in the
  engine.
* Exact inputs, all FREE:
  * University of Michigan Index of Consumer Sentiment, FRED series
    UMCSENT (with UMCSENT1 for the early quarterly portion), plus
    preliminary prints from the Surveys of Consumers site stored as a
    separate vintage. Archive November 1952, VERIFIED via FRED.
    Quarterly to 1977, monthly from January 1978.
  * Baker and Wurgler investor sentiment index, level and orthogonalised
    versions, from Jeffrey Wurgler's NYU Stern faculty spreadsheet.
    Monthly from July 1965, VERIFIED as published span. Every pull stores
    its download date and file hash, because the index is recomputed when
    its components revise (MEASUREMENT family (a) vintage trap).
* Computation:
  * Each series is converted to its own full-history percentile, using
    only observations up to that month (the uniform percentile rule
    stated before Section 1).
    Michigan's quarterly era (1952 to 1977) is computed at quarterly
    cadence and labelled as such in the store; it is never interpolated
    to monthly.
  * Gauge value: the mean of the two percentiles where both exist. Before
    July 1965 the gauge is Michigan alone and flags `single source era`.
  * The gauge value is a regime label input, not a timing input. The tile
    and the consumer file must never attach directional return language to
    G2 alone. THEORY Section 3.2 and the Zhou (2018) figure carried in
    MEASUREMENT family (a) are the reason: the Baker and Wurgler index
    explains about 0.3 percent of monthly market return variance. Its job
    is cross-sectional and regime context (P3), and the guardrail
    proposition P4 caps what any composite here may claim.
* Cadence: monthly. Preliminary Michigan enters when published, marked
  `preliminary`, and is replaced by the final print as a new vintage,
  never by overwriting.
* Reading scale: uniform zone table, with the additional printed rule that
  a G2 zone change is a regime note, not an event. The daily state shows
  G2 once, as the spine line, not repeated inside other gauges.

## G3. Where Money Sits (positioning)

* What it measures: revealed positioning, type RP. Where leveraged and
  institutional money actually sits in index futures, where fund money is
  flowing, and how much off-exchange volume is being sold short. A
  crowding and forced-flow map first, a return signal second (MEASUREMENT
  family (b) evidence note on COT).
* Exact inputs, all FREE unless marked:
  * CFTC Commitments of Traders, Legacy report, futures only, for the
    S and P 500, Nasdaq 100, and Dow index contracts, plus VIX futures.
    Annual compressed files and the public reporting environment. Futures
    only from 1986, VERIFIED, with the pre-September-1992 caveat stored in
    the series header (mid-month and month-end observations only before
    that date, with the CFTC's own warning about uncorrectable errors in
    the pre-1992 mid-month data).
  * CFTC Traders in Financial Futures (TFF) report, dealer, asset manager,
    and leveraged fund categories for the same contracts. Published from
    2006; complete annual files listed from September 2009, VERIFIED as
    stated on the CFTC page. Coverage for 2006 to 2009 must be checked
    file by file at backfill and the checked result recorded.
  * ICI weekly estimated flows and monthly long-term flows, equity, hybrid,
    bond, and money market categories, free published tables. Weekly
    estimates and monthly finals are stored as separate vintages
    (MEASUREMENT family (b) flow revision trap). Archive depths for ICI
    are UNVERIFIED in MEASUREMENT and must be recorded as downloaded.
  * Estate lane, reused, not rebuilt: the Morgue DIX reading
    (`~/workspace/morgue/`, `map_dix.py`, FINRA FNQC file), the index
    short share of off-exchange volume. Live for the index reading per
    MEASUREMENT Part 1.1. The per-name dark values the Morgue computes and
    discards are stored by this program's FINRA collector (Section 5)
    rather than recomputed, which cures the Part 1 gap at the store, not
    by duplicating the DIX computation.
* Computation:
  * For each index contract family, TFF leveraged fund net position and
    Legacy noncommercial net position, each scaled by total open interest
    of that contract, weekly: `net_scaled = net / open_interest`.
  * Gauge positioning sub-score: the mean full-history percentile of
    `net_scaled` across the S and P 500 and Nasdaq 100 contract families,
    TFF form where it exists, Legacy form before it, with the 2006 to
    2009 junction marked as a series break in the store and on any exhibit
    that crosses it.
  * Flow sub-score: ICI equity plus hybrid net flow over the trailing
    4 weeks, scaled by prior month-end category assets where ICI
    publishes them, converted to its own full-history percentile.
  * Short pressure sub-score: the DIX index reading, inverted (a high
    short share is pressure, not a mood direction by itself), converted
    to its percentile over the estate DIX record, which is short. Until
    the DIX record reaches 250 sessions this sub-score displays with
    NO BAND status under the percentile rule and does not enter the
    gauge value.
  * Gauge value: the mean of the positioning and flow sub-scores. The
    short pressure line displays on the tile as context from day one.
  * Roll weeks are flagged in the COT store, because contract rolls create
    false positioning jumps (MEASUREMENT family (b) trap). A gauge move
    in a flagged roll week carries the flag onto the tile.
* Cadence: weekly for COT (positions as of Tuesday, published Friday
  15:30 ET), weekly for ICI estimates, daily for the DIX context line.
  The daily state carries each with its own as-of date.
* Reading scale: uniform zone table. High means crowded long and flowing
  in. Low means crowded short, hedged, or flowing out.

## G4. Leverage and Fragility (the forced-flow axis)

* What it measures: how much selling a move would force. Not mood.
  Leverage stock in brokerage accounts, fast leverage in crypto
  perpetuals, and the dealer hedging configuration that amplifies or
  damps a move. This gauge is the v1 form of MEASUREMENT Part 3, idea
  3.2 (positioning convexity) and idea 3.4 (dealer exposure as amplifier):
  a qualitative panel of named inputs in their own zones. The quantified
  forced-flow index with published elasticities is a separate future
  commission (Section 7.3), because an elasticity this program has not
  estimated is theatre if printed as a number.
* Exact inputs:
  * FINRA margin statistics, monthly Excel download: debit balances, free
    credit in cash accounts, free credit in margin accounts. From
    January 1997, VERIFIED. The February 2010 collection break (separate
    NYSE and FINRA collection before, one FINRA Rule 4521 collection
    after) is marked in the store.
  * Crypto perpetual funding rates for BTC and ETH, Coinalyze aggregated
    (desk key already held; the auth header must be named exactly
    `api_key` and sent via curl or `http.client`, never `urllib`, per
    desk law recorded in MEASUREMENT family (h)), with direct exchange
    APIs (Binance, Bybit, OKX public endpoints, FREE) as the cross-check
    and fallback. Liquid history from about 2019, per-venue starts NOT
    individually verified in MEASUREMENT and recorded as downloaded.
  * Estate lane, reused, not rebuilt: Morgue Map net gamma exposure sign
    and size for SPY, QQQ, IWM (`map_gex.py`, Alpaca options contracts and
    snapshots, KEYED FREE with the desk Alpaca key). Modelled, convention
    signed, from overnight open interest. The tile says `modelled` every
    time, per the Morgue design rule in MEASUREMENT Part 1.1. Estate
    record is thin (9 map cards at census) so this leg displays with
    NO BAND until its own record matures, exactly like the G3 short
    pressure line.
* Computation:
  * Margin leverage ratio: `debit_balances / (debit_balances +
    free_credit_cash + free_credit_margin)`, monthly, plus its
    12 month change. Both are percentile-ranked on the full FINRA
    history from 1997. Level without scaling is never displayed as a
    signal (MEASUREMENT family (b) trap).
  * Funding pressure: the 7 day mean of the BTC and ETH funding rates,
    annualised by the venue convention stated in the store, percentile
    ranked on the stored funding history. Signed: persistently positive
    extreme funding is crowded long leverage, negative extreme is
    crowded short leverage. The tile prints the sign in words
    (`crowded long`, `crowded short`), because fragility lives on both
    sides.
  * Amplifier state: Morgue Map net GEX sign per index ETF, printed as
    `damping` (positive) or `amplifying` (negative), with net GEX in
    dollars per 1 percent move as published by the Map. No percentile
    until the record matures.
  * Gauge value: the mean of the margin percentile and the absolute
    funding pressure percentile, displayed as the fragility percentile.
    The signed funding direction and the amplifier state are separate
    printed fields, never folded into that mean. Folding a sign into a
    fragility level would hide exactly the information this gauge
    exists to show.
* Cadence: monthly for margin (published in the third week of the
  following month, carried with its true month as-of date), every funding
  interval (8 hours) aggregated daily for funding, daily pre-open for the
  amplifier state.
* Reading scale: the fragility labels defined in the uniform conventions.
  G4 never votes in the mood composite. It modifies the composite's
  interpretation through the overlay rules in Section 3.

## G5. What Protection Costs (options psychology)

* What it measures: the price of insurance and the speculation mix in
  options volume. Priced revealed positioning, type RP priced. It
  conflates expected volatility, risk premium, and hedging demand, and
  the tile says so in plain words, per MEASUREMENT family (c).
* Exact inputs:
  * Cboe daily statistics and historical files, FREE: total, equity-only,
    and index-only put/call volume ratios, stored as three separate
    series, never averaged together (MEASUREMENT family (c) trap).
    Archive starts commonly cited as 2003 (total) and 2006 (revised
    equity series), UNVERIFIED by download in MEASUREMENT. The backfill
    records what the download actually contained.
  * Cboe SKEW index history file, FREE. From 1990 as reported by Cboe,
    UNVERIFIED by download in MEASUREMENT.
  * Estate lanes, reused, not rebuilt: the Morgue Tape for SPY, QQQ, IWM
    (Alpaca OPRA prints, KEYED FREE) as the live intraday context line,
    and the modelled IV ledger, which is the IV source of record by the
    2026-10-30 ruling recorded in MEASUREMENT Part 1.3 (RC-17), feeding
    the SPY, QQQ, IWM implied volatility context. TastyTrade chain
    snapshots are NOT an input to this gauge: the nested chain route
    carries no open interest, no volume, and no implied volatility
    (MEASUREMENT Part 1.3, Chain Explorer), and conflating the two chain
    routes is forbidden by that census.
* Computation:
  * Equity put/call ratio, inverted, ranked two ways: full-history
    percentile and trailing 3 year percentile (the dual reporting rule
    in the uniform conventions, from THEORY 3.3 and P5).
  * Index put/call ratio, inverted, full-history percentile. Index and
    equity ratios are different objects (hedging versus speculation
    mix) and the gauge keeps them as two printed lines.
  * SKEW percentile, full history: high SKEW means expensive tail
    insurance. It enters the gauge inverted like the other protection
    prices, and displays raw as well.
  * Gauge value: the mean of the equity put/call full-history percentile
    and the SKEW percentile. The index put/call line and the trailing
    3 year equity percentile display beside it. The VIX leg of options
    psychology lives in G6, not here, so the same VIX input never votes
    twice (independence rule).
* Cadence: daily after the close from Cboe files. The Morgue Tape context
  line is intraday and is labelled with its session and its capped-batch
  floor status where the Tape declares one (MEASUREMENT Part 1.1).
* Reading scale: uniform zone table on the gauge value. A top-decile
  trailing 3 year equity put/call reading is also one of the two trigger
  inputs to forecast hook F2 in Section 4, stated there, not improvised
  on the tile.

## G6. Breadth and Volatility Mood (the price-derived state)

* What it measures: what prices themselves reveal about participation and
  stress. This is MEASUREMENT shortlist item 1 (the daily price-derived
  mood spine) joined to item 2 (the VIX complex) and the confirmation
  half of item 8 (credit). It is the gauge that cures the estate's proven
  defect named in MEASUREMENT Part 1.3: the daily state record that held
  zero sessions while being written six times. This program's daily state
  store is that cure, built once, here, and consumed by State Analogue,
  Fear Day, and Family Fracture (estate engines 30, 24, and 17
  territory) as a store, never as a re-derivation.
* Exact inputs:
  * Daily bars for the estate price panel, Alpaca SIP (KEYED FREE, desk
    key). The shipped panel at census: 1,833 names, 399 sessions to
    2026-10-23 (MEASUREMENT Part 1.3). The build extends the panel
    backward from Alpaca SIP daily bars as far as that source honestly
    serves, and every breadth value before the shipped panel's own start
    is a RECONSTRUCTION computed on the extended panel, with the
    panel's survivorship caveat printed in the store header (breadth on
    today's members flatters history, MEASUREMENT family (d) trap).
    Yahoo data is used for no volume-bearing computation in this gauge,
    per desk law: Yahoo hourly volume is corrupt and disqualified
    desk-wide, and Yahoo is permitted only for price-only series such
    as VIX-adjacent daily closes where Alpaca has no series.
  * Cboe index history files, FREE: VIX closes from 1990, VERIFIED
    (close only from 1990, OHLC from 1992, methodology change on
    22 September 2003, old construction continued as VXO with history
    from 1986 until its 2021 discontinuation), VIX9D, VIX3M, and VVIX
    where Cboe publishes history (VVIX from 2007, reported, UNVERIFIED).
  * VIX futures settlement files, Cboe, FREE: futures from 2004,
    VERIFIED, for the front versus third month curve.
  * FRED credit series, FREE (FRED keyed free for API): ICE Bank of
    America high yield OAS (BAMLH0A0HYM2, from December 1996 as
    published on the FRED series page) and investment grade OAS
    (BAMLC0A0CM family). Vintage dates stored, because FRED series
    revise (MEASUREMENT family (d) trap).
* Computation:
  * Breadth block, daily: percent of panel names above their 50 day and
    200 day averages, advancers minus decliners as a share of panel,
    new 52 week highs minus new lows as a share of panel. Each
    percentile-ranked on its own stored history.
  * Breadth thrust flag: the Zweig form, 10 day advance share moving
    from below 40 percent to above 61.5 percent, printed as a rare
    event flag with its historical event count beside it (roughly two
    dozen since the 1940s in published counts, varying by data source,
    per MEASUREMENT family (d)). The flag is a flag. It is never a
    probability and never a forecast outside the ledger.
  * Volatility block, daily: VIX close percentile (full history, with
    the 2003 methodology break marked and a VXO-bridged context line
    for 1986 to 2003 exhibits only), term structure state
    (`VIX / VIX3M`, above 1 means near-term fear priced above deferred
    fear, with inversion duration in sessions as the regime clock),
    and the VIX futures curve state (front versus third month).
  * Credit confirmation, daily, printed as a verdict word, not folded
    into the gauge value: high yield OAS 20 session change percentile.
    `confirms` when credit widens alongside an equity fear reading,
    `denies` when it does not, `neutral` otherwise. A fear reading that
    credit denies and a fear reading that credit confirms are different
    situations (MEASUREMENT shortlist item 8) and the state document
    prints the verdict in the same sentence as the fear reading.
  * Gauge value: the mean of the breadth block percentile (itself the
    mean of its four components) and the inverted VIX percentile,
    equally weighted. Term structure and credit display as named
    sub-states beside the value.
* Cadence: daily after the close. This gauge is the timestamp spine of
  the daily state: every other gauge's as-of date is printed relative
  to the G6 session date.
* Reading scale: uniform zone table. Inversion duration has its own
  printed scale: 1 session `flash`, 2 to 5 sessions `stress`, more than
  5 sessions `sustained stress`.

## G7. Attention and Narrative (what the crowd is looking at)

* What it measures: attention, type AT, with a fear subset that behaves
  like stated belief. What households are worried or excited enough to
  search for, what the news hole is occupied by, and what the social
  surfaces are amplifying. Attention is directionless until tone or
  imbalance supplies the sign (THEORY Sections 1.5 and 4.3), and this
  gauge's formula respects that: it measures the level and the fear
  share of attention, not a direction of the market.
* Exact inputs, all FREE or KEYED FREE:
  * Google Trends, via web export or the unofficial API wrapper, for two
    frozen baskets: a FEARS-style fear basket (recession, bankruptcy,
    crisis, and kin terms, frozen at build, per Da, Engelberg, and Gao
    2015 as catalogued in MEASUREMENT family (e)) and a maintained
    market topic set. Trends data begins January 2004 as published by
    Google. Every pull stores its exact query set, geography, time
    window, and pull timestamp, because Trends values are relative
    indices rescaled per request and two pulls are not automatically
    comparable (the central trap of this channel). Collection breaks in
    2011, 2016, and 2022 in Google's own collection are marked in the
    store.
  * GDELT, FREE: GKG themes and tone (GKG 1.0 from 2013, GKG 2.1
    tone-rich fields from February 2015, as documented by the project,
    VERIFIED for the events archive from 1 January 1979), DOC 2.0 API
    for the rolling live window. Pre-2013 tone does not exist in GKG
    form and is never implied. Events counts from 1979 are context
    counts only, because the source universe of 1979 and of today are
    not the same newspaper universe.
  * Wikipedia pageviews API, FREE: a maintained concept set (crash,
    recession, and named company pages for names in Midna's book
    universe). API from July 2015, VERIFIED as the API's stated start.
  * Social collection, from collection start only, stored from day one,
    displayed as context lines in v1 and promoted into the gauge value
    only by the rule at the end of this section: StockTwits message
    volume and self-tagged bullish and bearish labels (KEYED FREE
    developer access), and Reddit finance mention counts via the
    official API free tier (KEYED FREE). X is NOT an input: serious read
    access is PAID since 2023 and no free archive of record exists
    (MEASUREMENT family (f)). TikTok, Discord, and Telegram are named
    habitats that are not built on, for the access and terms reasons
    MEASUREMENT family (f) states.
  * Estate lane, reused as method, not as data: the Morgue news lane
    (`news_lane.py`, `news_direction.py`) and the Loughran and McDonald
    finance dictionary (FREE from the authors) for any estate-computed
    tone. A generic sentiment word list is never used on financial text
    (MEASUREMENT family (e) evidence note).
* Computation:
  * Fear attention sub-score: the FEARS basket index level, built with
    pinned pull parameters, percentile-ranked on its stored history
    from 2004, inverted (more fear searching means a lower mood score).
  * News tone sub-score: GDELT GKG mean tone over the maintained finance
    theme set, 7 day mean, percentile-ranked on its stored history
    from 2015 (tone era only).
  * Curiosity sub-score: Wikipedia pageviews for the concept set,
    7 day mean against its own history from 2015, displayed, and
    entering the gauge only as a spike flag (top decile means
    `attention spike`, printed in words), because pageview level is a
    poor cross-era comparable.
  * Gauge value in v1: the mean of the fear attention and news tone
    sub-scores. Social context lines (StockTwits labelled split,
    Reddit mention counts) print on the tile from day one with
    `collecting, not yet in gauge` status. Promotion rule, stated now
    so it cannot be improvised later: a social sub-score enters the
    gauge value only after 250 stored sessions and only as a design
    amendment to this document, recorded with its date.
  * Narrative registry: the engine maintains a frozen phrase set per
    named narrative (THEORY Sections 2.4 and 4.2). A narrative is added
    by a written registry entry before its prevalence series is graded
    for anything. Prevalence level and its growth rate are both stored
    daily from GDELT and Trends. The saturation checklist of THEORY
    Section 4.2 is computed and displayed as a checklist. It issues no
    forecast in v1 except through hook F3's family coincidence, because
    P12 and P13 grade it, and P13 is live-ledger-only in its frozen
    form.
* Cadence: daily, with Trends values lagging 1 to 2 days as Google
  serves them, stated on the tile.
* Reading scale: uniform zone table on the gauge value, plus the printed
  spike flag. High means attention is risk seeking or euphoric in tone.
  Low means attention is fear dominated.

## G8. What Bettors Price (belief markets)

* What it measures: money-weighted probabilities for the scheduled macro
  events that move narratives and positioning: Fed decisions, CPI
  prints, recession calls, and major policy events. Belief aggregates
  with a stake, type RP with money at stake. The engine's use is
  anchoring (THEORY Section 4.3 and P17): where a liquid belief market
  exists, its price anchors the belief state, and any engine view that
  departs from it must name its edge.
* Exact inputs:
  * Kalshi market data, KEYED FREE (free account key). Exchange launched
    publicly in 2021. Series history from each series start.
  * Polymarket public APIs (Gamma and CLOB), FREE, no key for reads.
    Platform launched 2020. Per-market history from market creation.
  * Metaculus public API and exports, FREE. From 2015 as platform
    reported. Scored forecaster aggregates, included because it is the
    one belief channel that grades its own participants.
  * Benchmark, not a belief market input: Fed funds futures implied
    probabilities from CME delayed free summaries where obtainable, so
    no Kalshi or Polymarket Fed price is ever displayed alone
    (MEASUREMENT family (g)). Where the free summary is not obtainable
    on a given day, the tile prints `futures benchmark unavailable`
    rather than substituting another venue's price silently.
  * Manifold is collected as a context line only in v1 (play money,
    from 2022). PredictIt is NOT an input: the platform wound down, and
    it stands in this design as the reason belief prices are stored
    daily from day one (MEASUREMENT family (g) trap).
* Computation: no composite score. For each watched event series the
  gauge stores the daily closing implied probability per venue, the
  cross-venue spread, and a liquidity flag (`thin` when the venue's own
  published volume or open interest for that market falls below the
  threshold recorded in the series header at build). A thin price is
  labelled a quote, not a consensus, wherever it displays. The gauge's
  daily output is a table of events, probabilities, spreads, and flags,
  plus one summary line: the largest 7 day probability move among liquid
  watched events, named in words.
* Cadence: daily snapshot at a fixed time after the US close, stored
  forever. Intraday prices are not collected in v1.
* Reading scale: probabilities are read as probabilities, with the
  premium caveat of THEORY Section 4.3 printed where the page explains
  the gauge: these are prices of events, and prices carry hedging and
  expressive demand. No percentile zones apply until the estate holds a
  year of its own stored history, at which point probability move sizes,
  not levels, may be percentile-ranked by an amendment to this design.

## G9. Crypto Mood Overnight (the transfer panel)

* What it measures: the only live crowd readings that exist while US
  equity markets are closed. Crypto fear and greed, and the weekend and
  overnight state that Midna's Monday 08:00 pre-open read would
  otherwise have no instrument for (MEASUREMENT Part 3, idea 3.12).
* Exact inputs:
  * Alternative.me Crypto Fear and Greed Index, public API, FREE,
    returning its full history as JSON. Daily from 1 February 2018,
    VERIFIED. Its published recipe (volatility 25 percent, momentum and
    volume 25 percent, social 15 percent, surveys 15 percent with that
    component reported paused in later years, Bitcoin dominance
    10 percent, Trends 10 percent) is stored in the series header,
    because the gauge is partly reflexive: the crowd watches the number
    (MEASUREMENT family (h) trap).
  * BTC and ETH spot prices and realised weekend moves, from Alpaca
    (KEYED FREE, desk key) or free exchange APIs, for the transfer
    record: the Friday equity close to Monday pre-open crypto state,
    stored as a paired record.
  * Funding rates are NOT a G9 input. They live in G4, once. The G9 tile
    cross-references the G4 funding line by name rather than recounting
    it (independence rule).
* Computation: the Alternative.me value percentile-ranked on its full
  stored history from 2018, plus the paired weekend record (BTC percent
  move Friday 16:00 ET to Monday 04:00 ET, ETH same window, and the
  Fear and Greed change over the weekend). No transfer claim is computed
  in v1. The association between the weekend crypto state and the Monday
  equity state is a graded question for the ledger (idea 3.12), and
  until it is graded the tile prints the pair and the word `ungraded`.
* Cadence: daily, plus the weekend pair record written Monday before
  04:00 ET so the pre-open consumer file can carry it.
* Reading scale: uniform zone table on the percentile, labelled
  `crypto crowd`, never merged into the equity mood wording on any
  surface.

### Gauge set summary

| Gauge | Name | Type | Cadence | History start (stored) | Votes in composite |
|---|---|---|---|---|---|
| G1 | What People Say | Stated belief | Weekly | 1987 (AAII), 2006 (NAAIM) | Yes |
| G2 | Slow Climate | Stated belief plus behaviour composite | Monthly | 1952 (Michigan), 1965 (Baker and Wurgler) | Yes, as regime spine |
| G3 | Where Money Sits | Revealed positioning | Weekly | 1986 (COT Legacy) | Yes |
| G4 | Leverage and Fragility | Revealed positioning, leverage | Monthly, daily, 8h legs | 1997 (margin), about 2019 (funding) | No. Second axis |
| G5 | What Protection Costs | Priced positioning | Daily | As downloaded from Cboe, 1990 (SKEW, reported) | Yes |
| G6 | Breadth and Volatility Mood | Price-derived | Daily | Panel depth (breadth), 1990 (VIX) | Yes |
| G7 | Attention and Narrative | Attention | Daily | 2004 (Trends), 2015 (GKG tone) | Yes |
| G8 | What Bettors Price | Belief markets | Daily | 2020 and 2021 (platform starts) | No. Anchor only |
| G9 | Crypto Mood Overnight | Composite, crypto | Daily | 2018 | No. Transfer panel |

---

# 2. THE HISTORY STORE AND CALIBRATION

## 2.1 Store layout

Root: `~/workspace/psychology-engine/`

    history/
      series/
        aaii_weekly.csv
        naaim_weekly.csv
        michigan_umcsent_monthly.csv
        baker_wurgler_monthly.csv
        cot_tff_weekly.csv
        cot_legacy_weekly.csv
        ici_flows_weekly.csv
        ici_flows_monthly.csv
        finra_margin_monthly.csv
        cboe_putcall_daily.csv
        cboe_skew_daily.csv
        cboe_vix_daily.csv
        cboe_vix_term_daily.csv
        cboe_vix_futures_curve.csv
        fred_hy_oas_daily.csv
        fred_ig_oas_daily.csv
        breadth_daily.csv
        panel_membership_notes.md
        fred_... (one file per FRED series actually pulled)
        trends_fears_weekly.csv
        trends_topics_daily.csv
        gdelt_gkg_tone_daily.csv
        wikipedia_pageviews_daily.csv
        stocktwits_daily.csv
        reddit_mentions_daily.csv
        kalshi_daily.csv
        polymarket_daily.csv
        metaculus_daily.csv
        altme_fear_greed_daily.csv
        crypto_funding_daily.csv
        dix_index_daily.csv
        morgue_map_gex_daily.csv
      gauges/
        g1_stated_sentiment.csv
        g2_slow_climate.csv
        ... one file per gauge, G1 to G9 ...
      provenance/
        PULL-LOG.md
      backtests/
        BACKTEST-RECORD.md
        (one folder per backtested proposition)
    live/
      raw/            (one folder per collector, raw snapshots, dated)
      state/          (daily state JSON files, one per session)
    exhibits/
      CALIBRATION-EXHIBITS.md
      exhibits.json
    output/
      state-latest.json
      STATE.md        (the one-page state document, latest)
      state-archive/  (dated copies of STATE.md)

One file per input series. The file list above is the v1 set: a series
not listed here is not silently added by a collector, and a listed series
that a source fails to deliver is created with its header and an absence
note, so the store enumerates its own gaps.

## 2.2 Provenance header (every series file, no exceptions)

Every series file begins with a comment header block (CSV files use
leading `#` lines) carrying, in this order:

    # series: <series name>
    # source: <publisher and exact product or file>
    # source_url_or_route: <the route used, copied from the pull code>
    # retrieved: <YYYY-MM-DD of first retrieval>
    # last_pull: <YYYY-MM-DD>
    # revision_policy: <as-published stored / latest revised stored /
    #   both vintages stored, per the rule below>
    # as_of_meaning: <what the date column means for this series>
    # archive_claim: <start date> <VERIFIED or UNVERIFIED, and by whom>
    # downloaded_span: <first and last observation actually in this file>
    # breaks: <dated methodology or collection breaks, one per line>
    # transforms: <any scaling, inversion, or unit change applied>
    # file_sha256: <hash of the source file as downloaded, where a
    #   single source file exists>

Rules:

* Vintage rule: series that revise (FRED, ICI, FINRA margin, Baker and
  Wurgler, Michigan preliminary versus final) store both the first
  published value and the latest value in separate columns
  (`value_first`, `value_latest`) wherever the source makes the first
  published value obtainable. Where it does not, the header says so, and
  every backtest on that series carries the note `revised values, live
  vintage unavailable`. A value is never overwritten in place: a revision
  arrives as a new column value with its own retrieval date in the pull
  log.
* The pull log (`history/provenance/PULL-LOG.md`) records every pull,
  live or backfill: date, series, route, rows added, rows revised, the
  downloaded span, and any failure, in the collector's own words at pull
  time.
* A gauge file under `history/gauges/` carries its own header naming its
  formula version (this design, Section 1, by gauge number), its input
  series files, and the single word RECONSTRUCTION on every row dated
  before the engine's live start, carried in a `kind` column whose only
  values are `reconstruction` and `live`. There is no third value.

## 2.3 Per-gauge backfill plan

| Gauge | Feeding archives | Target start | Notes the build must honour |
|---|---|---|---|
| G1 | AAII weekly spreadsheet; NAAIM weekly file archive | AAII July 1987; NAAIM July 2006 | AAII mail to online break in 2000 marked. Long-run AAII means (about 38.8 bullish, 30.5 neutral, 30.6 bearish, as AAII publishes) recorded in the header as a sanity anchor. |
| G2 | FRED UMCSENT and UMCSENT1 plus Surveys of Consumers preliminary prints; Wurgler faculty spreadsheet | Michigan November 1952; Baker and Wurgler July 1965 | Quarterly era stays quarterly. Baker and Wurgler pull stores download date and file hash. This pair is the long spine: the composite's regime history is anchored here to 1965. |
| G3 | CFTC annual compressed files, Legacy then TFF; ICI published tables; Morgue DIX record plus this program's stored FINRA per-name dark values going forward | COT futures only 1986; TFF 2006 to 2009 checked file by file; ICI as downloaded | Pre-1992 COT cadence and error caveat in header. No COT value is interpolated across the 1992 cadence change. |
| G4 | FINRA margin statistics Excel; Coinalyze and exchange funding history; Morgue Map record going forward | Margin January 1997; funding about 2019 per venue | February 2010 collection break marked. Funding per-venue starts recorded individually. GEX history before the estate record does not exist and is never reconstructed from expired contract archives, whose free completeness does not support it (MEASUREMENT family (c) trap). The margin and funding legs carry the historical gauge. |
| G5 | Cboe historical put/call files; Cboe SKEW history file; estate OPRA and modelled IV from collection start | Put/call as actually contained in the download (cited 2003 and 2006, UNVERIFIED until the download is in hand); SKEW 1990 as reported | Volume-based and open-interest-based ratios are different series and are never merged. Estate options history starts at estate collection and is never backfilled as a record. |
| G6 | Alpaca SIP daily bars for the extended panel; Cboe VIX, VIX9D, VIX3M, VVIX files; Cboe VIX futures settlements; FRED OAS series | Breadth: as deep as the extended panel honestly serves, labelled RECONSTRUCTION with the survivorship caveat; VIX 1990 (VXO bridge 1986 to 2021 for exhibits); VIX futures 2004; high yield OAS December 1996 | The 2003 VIX methodology break is a store-level break marker. Any breadth exhibit names the panel it was computed on. |
| G7 | Google Trends pinned pulls; GDELT GKG files and BigQuery free tier; Wikipedia pageviews API; StockTwits and Reddit from collection start | Trends January 2004; GKG tone February 2015 (GKG 1.0 themes 2013); pageviews July 2015; social: collection start, stated as such | Trends pulls are stitched only within pinned parameter sets, and every stitch point is a break marker. GDELT events counts from 1979 are context only and feed no gauge value. |
| G8 | Kalshi, Polymarket, Metaculus: estate daily snapshots only | Platform starts 2020 and 2021 are the honest floor, and even those are not backfilled for grading (P17: uncaptured historical market prices cannot be graded honestly and will not be reconstructed for grading). Published per-market price history may be stored for display context, in a separate file, labelled `display only, not graded`. | The gauge's graded history begins at the engine's first snapshot. This is the PredictIt lesson applied before the fact. |
| G9 | Alternative.me API full history; Alpaca or exchange BTC and ETH prices | February 2018 | Recipe changes reported by the publisher (survey component pause) are break notes in the header as they are announced. Earlier crypto mood history does not exist in this form and is not simulated. |

Young sources are named young wherever they appear: G8 (2020 and 2021),
the social legs of G7 (collection start), the funding leg of G4 (about
2019), and G9 (2018). A young gauge beside a 1965 spine is a feature of
the honest record, not a defect to be papered over with a longer fake
history.

## 2.4 Computing the historical gauge series

For each gauge, the compiler's historical mode runs the exact Section 1
formula over the stored input series, in date order, producing the
`history/gauges/` file. Three rules:

1. Point-in-time discipline inside the reconstruction: the gauge value
   for date `t` is computed only from input observations whose as-of
   date is `<= t` and whose publication date is `<= t` where the source
   publishes on a lag (COT, margin, ICI finals, Michigan finals). A
   reconstruction that uses Friday's publication of Tuesday's position
   as if it were Tuesday's knowledge is a lookahead error, and the
   exhibits in Section 2.5 are checked for exactly this at the COT and
   margin legs. Where a source's historical publication lag cannot be
   reconstructed honestly, the header states the assumed lag and the
   gauge rows for the affected era carry the flag `lag assumed`.
2. Percentiles inside the reconstruction follow the uniform percentile
   rule with the expanding set, so a 1990 percentile means `of the
   record to 1990`, and the exhibit table in Section 2.5 additionally
   prints the full-history percentile (the rank of that date's value in
   the whole stored record to today) in a separate column, labelled as
   such. The two numbers answer different questions and are never
   mixed in one column.
3. Formula changes after live start create a new formula version. The
   historical series is recomputed under the new version as a new file
   version, the old file is kept, and live grading under the old version
   is closed out, never rewritten. This is the THEORY Section 4.2
   freezing rule applied to gauges as well as narratives.

## 2.5 Calibration exhibits (part of the build, not an afterthought)

The build produces `exhibits/CALIBRATION-EXHIBITS.md` and
`exhibits/exhibits.json`: for each episode date below, the reconstructed
reading of every gauge that has data for that date, its expanding
percentile and its full-history percentile, its zone, and a sanity
verdict per gauge (`as expected`, `surprising, noted`, or `no data`,
with absence named, never zero filled). Episodes where a gauge did not
yet exist print `no data, series starts <year>`.

Stress and euphoria episodes:

| Episode | Anchor dates | What the record must show, or the build stops and says why |
|---|---|---|
| Dot-com peak | 2000-03-10 (Nasdaq peak 5048.62); margin peak month March 2000 | G2 in its top zones; G4 margin percentile at or near its record high; G1 in greed zones in the surrounding weeks; G6 breadth deteriorating into the peak is acceptable and, if present, is noted as the classic divergence, not treated as an error. |
| Dot-com trough | 2002-10-09 area (Nasdaq trough after a fall of about 78 percent peak to trough) | G6 and G5 in fear zones; G2 fallen from its peak readings; issuance climate cold inside the Baker and Wurgler components. |
| Crisis break | 2008-10-10 area and 2008-11-20 (VIX close 80.86, the modern-methodology record to that date) | G6 volatility block at its extreme: the stored VIX close for 2008-11-20 must equal 80.86 as published, a hard numeric check on the Cboe file. G1 bearish share in the mid 50 percent range at its crisis extremes, per THEORY Section 3.10. G6 credit verdict `confirms`. |
| Crisis bottom, the lesson | 2009-03-09 | The exhibit prints, in words, that the extreme zone was entered in October 2008 and the market fell for roughly five more months and about a further quarter of its value before this date (THEORY Section 3.10). This row exists to keep every future reader, and the consumer file, from reading an extreme as a date. It is tied to forecast hook F4. |
| Covid crash | 2020-02-19 (closing high), 2020-03-16 (VIX close 82.69, hard numeric check), 2020-03-23 (closing low, about 34 percent down) | Speed is the exhibit: G6 must travel from neutral or confident zones to extreme fear in about five weeks, the fastest such transit in the stored record. Bands computed without 2020 would call ordinary stress unprecedented (THEORY Section 3.10), so this row is also the proof that 2020 is in the calibration set. |
| Meme peak | 2021-01-27 and 2021-01-28 | G1 and G7 in greed and spike states; G9 in greed zones; G3 and G5 context lines showing the options and short pressure fingerprints the SEC staff report documents (THEORY Section 3.10). Gauges sampled monthly alone would have missed the episode, and the exhibit says so: sampling frequency is a theory choice. |
| The 2022 bear | 2022-06-16 area and 2022-10-12 (closing low) | G2 at or near its record lows (Michigan printed its all-time low in June 2022 in the published series, and the stored file must reproduce that fact); high sentiment beta segments falling far more than the broad index, noted as the Baker and Wurgler cross-section prediction operating live (THEORY Section 3.10), which is the historical company hook F3 keeps. |

Quiet controls (a calibration that only fires at extremes is a
calibration that always fires):

| Control | Anchor date | Expected |
|---|---|---|
| Quiet bull, low volatility year | A monthly anchor in 2017 (for example 2017-09-29) | G6 volatility block in its lowest deciles; no gauge in an extreme zone except, permissibly, G2 or G4 at greed-side readings that persisted for years, which, if present, is noted as the known behaviour of slow gauges in long bulls. |
| Mid-cycle calm | 2019-07-31 area | All core gauges between the 20th and 80th percentiles, or each exception named with its reason. |
| Post-crisis normalisation | 2023-07-31 area | G7 attention normal; G9 recovered from 2022 lows; no fear extremes anywhere. |

Sanity gate for the whole exhibit set: if any hard numeric check fails
(the two VIX closes, the Michigan 2022 low, the March 2000 margin peak
month), the build does not proceed to bands or to the page. The failure
is reported with the file, the expected value, and the stored value. A
calibration exhibit set with a wrong VIX close in it proves the store is
wrong, and nothing built on the store outranks that proof.

---

# 3. THE COMPOSITE: THE DAILY PSYCHOLOGICAL STATE

## 3.1 What is published

Every session, after the close and before 04:00 ET the next morning
(Section 5 sets the pipeline clock), the compiler publishes one
Psychological State:

* A named regime (Section 3.2).
* The gauge table: all nine gauges, each with its current value, its
  full-history percentile, its zone in words, its as-of date, and its
  status flags (`live`, `stale`, `partial`, `no band`, `collecting`,
  `modelled` where a modelled estate lane feeds it).
* The fragility axis reading (G4) and the belief anchor summary (G8),
  printed as their own lines, never inside the regime score.
* The disagreement statement (Section 3.3), in words, always present,
  even when it reads `gauges agree`.
* The extremes list: every gauge currently in a 0 to 5 or 95 to 100
  zone, named, with the date it entered the zone. Extremes mark
  regimes, not dates (THEORY Section 3.10), and the state document
  prints zone entry dates and durations precisely so that no reader
  mistakes an extreme for a turning call.
* The forecast hooks due, fired, or graded that day (Section 4), each
  with its ledger reference.

## 3.2 The combination rule, stated plainly

1. Take the six core mood gauges: G1, G2, G3, G5, G6, G7. Use each
   gauge's current oriented percentile (0 to 100, high means greed
   side).
2. The composite score is the median of the available core
   percentiles. The median, not the mean, because one gauge at a
   broken or spiking extreme must not drag the state with it, and
   because the median is the rule a reader can recompute from the
   printed table by hand.
3. If fewer than four core gauges are available (not stale beyond two
   cadence periods, not absent), no composite score is published. The
   state publishes the gauge table with the regime named
   `Insufficient data`, and says which gauges are missing. A state
   built on three gauges wearing the clothing of six is a provenance
   violation.
4. The regime name comes from the median, on this table:

| Median percentile | Regime name |
|---|---|
| 0 to 5 | Capitulation zone |
| 5 to 20 | Deep fear |
| 20 to 40 | Fearful |
| 40 to 60 | Neutral mix |
| 60 to 80 | Risk seeking |
| 80 to 95 | Greed |
| 95 to 100 | Euphoric excess |

5. G2's role is printed, not hidden in the median: the state document
   carries the line `Slow climate: <G2 zone>`, because the same fast
   fear reading means one thing inside a slow greed climate and
   another inside a slow fear climate, and THEORY's coincidence logic
   (P22) is built on exactly that distinction.
6. G4 overlay, applied after the regime name, in this order:
   * If G4 fragility percentile is 90 or above and the regime is
     Neutral mix or higher, the regime name becomes
     `Complacent fragility` when G6's volatility block is in its
     lowest tercile, and otherwise gains the suffix `, fragile`.
     Complacency is the Minsky build phase of THEORY Sections 2.3 and
     3.10 (2003 to 2007), and it gets its own name so it cannot hide
     inside a benign median.
   * If G4 is 90 or above and the regime is Deep fear or Capitulation
     zone, the regime gains the suffix `, forced flow active`, and the
     state document names the forcing legs that are in their extreme
     zones (margin contraction, funding, amplifying GEX). While
     forcing dominates, contrary readings carry no force (THEORY
     Section 4.4, forcing condition), and the state says so in those
     words.

## 3.3 The disagreement case, handled by naming it

Averaging a conflict away is the failure this section exists to
prevent.

* Spread: the state computes the interquartile range and the full
  range of the six core percentiles, and prints both.
* Contested rule: if the full range is 60 percentile points or more,
  or if at least one core gauge sits in a 0 to 20 zone while another
  sits in an 80 to 100 zone, the regime name gains the prefix
  `Contested:` and the state document must name the poles in words:
  which gauge is fearful, which is greedy, and each one's one-line
  reason from its own inputs. Example shape, not a template to copy
  blindly: `Contested: Fearful. Surveys are at capitulation levels
  while positioning remains crowded long.` The median still prints. It
  prints second, after the poles.
* Family fracture note: when the stated family (G1, G2) and the
  revealed family (G3, G5, G6) disagree by the contested rule between
  families specifically, the state prints the sentence `People say one
  thing and hold another`, with both sides' percentiles. This is the
  daily, named form of the disagreement geometry estate Engine 17
  (Family Fracture) forecasts range from. This program supplies that
  engine its stored daily fracture reading. It does not duplicate its
  forecast.
* No resolution language: a contested state is a complete state. The
  document never writes `on balance` over a contested reading, and the
  consumer file (Section 6) carries the contest into the pre-open read
  unresolved, because Midna's judgment, not an average, is the
  consumer of a disagreement.

## 3.4 What the composite is not

* It is not a return forecast. It enters no sizing, no sleeve, and no
  order path. Its only forecast content is the four hooks of Section
  4, each separately ledgered and graded.
* It is not a single fear and greed dial of the CNN kind. CNN's index
  is a display composite over inputs this engine counts separately,
  with no published archive to audit standard (MEASUREMENT family
  (a)). It may appear on the terminal page as a context tile labelled
  with that provenance. It never enters a store, a gauge, or the
  median.
* Its claimed skill is capped in advance by P4 (THEORY Section 5):
  no composite this engine builds is expected to beat a 2 percent
  monthly out-of-sample R squared for broad index returns over any
  five year live window, and any internal or public wording that
  implies more is a defect to be corrected on sight.

---

# 4. THE FORECAST HOOKS

Four hooks. Each is drawn from THEORY Section 5 propositions, each
states its horizon, its grading rule, and its ledger write, and each is
written into the ledger before its horizon starts. Belief forecasts and
return forecasts are graded on separate boards, and fragility forecasts
on the accuracy of the conditional map (THEORY Section 4.5, fourth
rule). Every hook carries the kill condition of its parent proposition,
restated in hook form. A hook that meets its kill condition is retired
in public, on the page and in the state document, with its full record
shown.

All four hooks write through the estate forecast machinery inventoried
in MEASUREMENT Part 1.2: the append-only, hash-chained ledger
(`forecast/ledger.py` and `forecast/ledger.jsonl`), the registry
(`forecast/registry.json`, with this program's forecasts registered
under the existing evidence families: surveys and positioning under
filings and positioning, options under options prints and distributional
and volatility, attention under events and calendar where it fits and
otherwise under price), and the grading module (`forecast/grading.py`).
This program adds a forecaster to that machinery. It does not build a
second ledger.

## F1. Next survey print, belief board (from P1)

* Cadence: weekly, issued on Thursday after the AAII print is stored
  and before the next survey week's voting closes.
* Forecast: the direction and a probability distribution over three
  buckets (spread widens bullish, spread narrows or falls, spread
  within plus or minus 2 points) for next week's AAII bull minus bear
  spread. The engine's model is the trailing-return revision model of
  THEORY Sections 1.7 and 4.3: the spread forecast is a stated function
  of trailing 3 month and trailing 1 month index returns, with its
  coefficients fitted only on data before the forecast date and refit
  on a stated annual schedule, each refit starting a new model version
  in the registry.
* Horizon: one week, to the next AAII print.
* Grading: Brier score on the three buckets, against two named
  baselines graded alongside every week: the base-rate forecaster
  (historical bucket frequencies) and the persistence forecaster (next
  week equals this week). Belief board only. A season of beating
  persistence on beliefs says nothing about returns, and the grade
  display says so.
* Kill: the parent P1 kill condition, in hook form: if the
  trailing-return model loses to a releases-only comparison model on
  pre-registered error over 36 consecutive live months at the monthly
  Michigan leg of P1, or loses to persistence on Brier over the first
  52 weekly AAII forecasts, F1 is retired and survey forecasting
  reverts to measurement only.

## F2. Stress predicts variance, not direction (from P5)

* Cadence: event-triggered, checked daily after the close. Trigger:
  the G5 equity put/call ratio enters above its trailing 3 year 95th
  percentile, with the 2020 and 2022 regime break flags of THEORY
  Section 3.3 attached to the trigger record.
* Forecast: a probability, stated as a number between 1 and 99
  percent, that SPX realised volatility over the next 20 trading days
  exceeds its unconditional median realised volatility for 20 day
  windows, computed from the history store. The forecast explicitly
  makes no directional claim, and the ledger entry's direction field
  is the registered value `none, variance only`.
* Horizon: 20 trading days from the session after the trigger.
* Grading: Brier score against the base rate (the historical frequency
  of above-median realised volatility windows, about 50 percent by
  construction, adjusted for the overlapping-window convention stated
  in the registry entry). Graded on the variance board. Separately,
  and for information only, the grader records the 20 day index return
  and its trailing 5 day return control, so that if directional
  content ever appears it is visible in the record rather than
  asserted. That record is not a forecast and is never scored as one.
* Kill: the parent P5 kill condition: if directional content survives
  the trailing-return control with a stable sign across both the
  pre-2020 and post-2022 regimes in the backtest record, or across 30
  live triggers, F2 is replaced by the directional version that earned
  it, through a design amendment, never by editing F2 in place.

## F3. Coincidence at extremes, cross-section board (from P22 and P3)

* Cadence: monthly, issued on the first session after the Baker and
  Wurgler monthly value used is published and stored.
* Forecast: conditional, and silent in most months. When at least two
  of the four registered families (surveys: G1 or G2 in a 95 plus
  zone; flows and leverage: G3 flow sub-score or G4 margin leg in a
  at or above the 95th percentile; issuance: the Baker and Wurgler issuance components in
  their top quartile, read from the stored index components where the
  published file carries them, otherwise from the G2 level as the
  registered fallback, named as a fallback in the entry; options
  stress: G5 at or below the 5th percentile, the fear side, because options stress
  confirms a top differently from euphoria, and this asymmetry is
  registered, not improvised), when at least two of those families are
  simultaneously in their high-sentiment extreme, the hook forecasts
  that over the next 6 months a high sentiment beta basket
  underperforms a low sentiment beta basket. Baskets are the
  characteristic sorts of P3, built from the Ken French data library
  (FREE): small, young, high volatility, unprofitable, non-dividend
  paying against the opposite characteristics, as the library's
  published sorts allow, with the exact sort files named in the
  registry entry. The mirror forecast (bottom extremes, high beta
  outperforms) is registered as the same hook with the sign field
  flipped.
* Horizon: 6 months, non-overlapping episodes counted separately from
  overlapping observations, with the independent episode count printed
  at every grading (THEORY Section 4.5, third rule). Any display
  resting on fewer than ten independent episodes is labelled
  `preliminary`.
* Grading: the conditional spread against zero, and against the best
  single family gauge alone, which is graded alongside as the named
  competitor, because P22's claim is that coincidence beats its best
  component, not merely that coincidence works. Cross-section board.
  The index's own return over the window is recorded and is not the
  grade: a bearish call on speculative segments can be right in a
  rising index year (THEORY Section 4.4).
* Kill: the parent P22 kill condition: if the coincidence rule fails
  to beat its best component on the pre-registered metric in the
  backtest record (Section 4.4), F3 never enters the live ledger at
  all, and the engine ships its family gauges with no composite
  forecast claim, with that outcome recorded in this design's build
  log. Live, the hook is retired if the sign reverses over the first
  six independent live episodes.

## F4. Capitulation is a zone, not a date (from P19)

* Cadence: event-triggered, checked daily after the close. Trigger,
  the joint capitulation signature of P19: index volume in its top
  decile against its own history, VIX in its top decile, and down-day
  breadth in its bottom decile, all on the G6 store, on the same
  session or within three sessions of each other, registered as one
  signature with its first date named.
* Forecast: a probability, 1 to 99 percent, that the index trades at
  least 5 percent below the first signature close at some point within
  the following 60 sessions. The base rate from the backtest record
  (P19's historical board, to 1990 on the modern VIX form and to the
  panel's depth on the reduced volume and breadth form, labelled
  reduced) is printed inside the forecast itself. The forecast's plain
  language, fixed in the registry, is: `capitulation signature seen.
  History says the low is a zone measured in weeks and percent, not
  this date.`
* Horizon: 60 sessions.
* Grading: Brier score against the printed base rate, plus the path
  record (days to the eventual low, depth below the signature close)
  published at grading. Graded on the return board, because this one
  is a claim about price path, and it is the hook whose grading the
  2008 to 2009 exhibit row (Section 2.5) exists to keep honest.
* Kill: the parent P19 kill condition, deliberately the hardest in
  this design to meet: if first signatures mark final lows within
  5 percent in more than 70 percent of graded episodes across backtest
  and live boards combined, the engine may, with the record shown,
  upgrade capitulation to a timing input, through a design amendment.
  Until then, any wording anywhere in this program's outputs that
  treats a capitulation signature as a bottom call is a defect.

## 4.4 The backtest record (separate, labelled, never the ledger)

Historical propositions (P2, P3, P5, P9, P10, P11 where its corpus
honestly reaches, P14 in coarse monthly form, P18, P19, P21, P22) may
be run against the history store, in `history/backtests/`, one folder
per proposition, each containing its code, its frozen specification,
its input series versions, and its result. Rules:

* The backtest record is a different file, a different folder, and a
  different word. Results from it are labelled BACKTEST and
  RECONSTRUCTION in every display, including the terminal page, where
  backtest grades and live grades never share a table.
* Passing a backtest earns a proposition the right to enter the live
  ledger as a hook. It earns nothing else (THEORY Section 5 preamble).
* Propositions whose data cannot honestly support a backtest get none,
  and say so: P6 (no free historical signed option volume archive at
  the required quality), P8 (the original platform dataset is no
  longer published), P15 (no free historical chain archive), P17
  (uncaptured belief prices), P4 (a claim about this engine, testable
  only live). P7, P12, P13, P16, and P20 run partial backtests with
  their coverage printed on the result, per their THEORY entries.
* F3's gate lives here: the P22 backtest runs as part of the build
  (Section 7), and its result decides whether F3 ships live.

---

# 5. THE PIPELINE

Five stages, in order, each independently runnable, each failing in
isolation. Code home: `~/workspace/psychology-engine/`, with
`collectors/`, `backfill/`, `compiler/`, and `publish/` folders mirroring
the stages.

## 5.1 Live collectors (one per source, isolated failures)

One collector process per source family, no shared fate:

| Collector | Sources | Schedule (ET) |
|---|---|---|
| `collect_surveys` | AAII file, NAAIM file | Thursday, after each publication, plus a Friday catch-up run |
| `collect_michigan_bw` | Surveys of Consumers prints, FRED UMCSENT, Wurgler spreadsheet | Daily check, acts only when a new vintage appears (hash or date change) |
| `collect_cot` | CFTC Legacy and TFF files | Friday after 15:30 release, plus a Saturday catch-up |
| `collect_flows_margin` | ICI tables, FINRA margin Excel | Weekly for ICI, monthly watch for margin |
| `collect_finra` | FINRA daily short volume files, FINRA short interest files, FINRA FNQC file (the DIX input the Morgue consumes) | Daily after FINRA publication for short volume; on FINRA's publication clock for the rest |
| `collect_cboe` | Cboe put/call, SKEW, VIX family, VIX futures settlements | Daily after the close |
| `collect_prices` | Alpaca SIP daily bars for the panel, FRED OAS series | Daily after the close |
| `collect_attention` | Trends pinned pulls, GDELT GKG and DOC, Wikipedia pageviews | Daily, after GDELT's day file closes |
| `collect_social` | StockTwits stream sample, Reddit API mentions | Daily aggregation of intraday samples |
| `collect_belief` | Kalshi, Polymarket, Metaculus daily snapshots | Daily at a fixed time after the US close |
| `collect_crypto` | Alternative.me index, Coinalyze and exchange funding, BTC and ETH prices | Daily, plus the Monday 04:00 weekend pair run |
| `collect_estate` | Morgue Map card (GEX), Morgue Tape session summary, modelled IV ledger summary | Daily after the Morgue's own cycle, reading its published outputs only |

Rules for every live collector:

* Raw snapshots are kept: every download lands in `live/raw/<collector>/`
  under its retrieval date, byte for byte, before any parsing. Parsing
  reads the snapshot, never the network. A re-parse years later must be
  able to reproduce the stored series value or name the parser change.
* Isolated failure: a collector that fails writes a failure record into
  the pull log and exits non-zero for itself only. The compiler runs on
  what exists, flags the affected gauges `stale` or `partial` under the
  clock and absence rules, and the state still publishes. One dead
  source never silences the state, and a silent collector is itself a
  defect the next state document names (the estate's liveness
  discipline: silent equals open defect).
* Idempotent re-runs: a collector run twice over the same source file
  adds zero duplicate rows. The natural key of each series (date, plus
  contract or series identifiers where applicable) is unique in the
  store, enforced at write.
* Credential discipline: Coinalyze calls use curl or `http.client` with
  the header named exactly `api_key`, never `urllib` (desk law). All
  other keyed routes use the keys the desk already holds, through their
  existing local routes. No new key is requested for v1.
* The FINRA collector is also a cure, not only a feed: it writes the
  per-name daily short volume store that the Short Volume Ledger tool
  has never accrued (MEASUREMENT Part 1.3), and the per-name dark
  values the Morgue DIX computes and discards, into
  `history/series/`-adjacent per-name stores under
  `~/workspace/psychology-engine/history/per_name/`, in the shapes the
  existing tools and engines 9 and 26 already expect, so those
  consumers read a store rather than this program's internals.

## 5.2 Backfill collectors (one-time, idempotent, resumable)

One backfill script per archive in Section 2.3, sharing one harness:

* Checkpointed: each backfill writes a checkpoint file (archive, last
  completed chunk, rows written, source hashes seen) after every chunk,
  so a killed run resumes from its checkpoint instead of restarting.
  Long pulls run detached, per desk practice for long processes, and
  are monitored by their effects (checkpoint growth, rows in store),
  never by a process-name pattern.
* Idempotent: re-running a completed backfill over the same archive
  adds zero rows and reports `already complete` with its span.
* Provenance-stamped: the first act of every backfill is writing the
  series header (Section 2.2) from what the download actually
  contains, including the downloaded span, which may be shorter than
  the archive claim. A span shorter than the claim is recorded, and
  the claim in the header is corrected to the span with the original
  claim kept as a note. The store describes the download, not the
  brochure.
* Verification at the seam: backfills that join eras (Legacy to TFF,
  VXO to VIX, quarterly to monthly Michigan, pre-1992 to weekly COT)
  write the overlap or junction rows with a break marker and a short
  junction note in the pull log, and never smooth across the seam.

## 5.3 The compiler

`compiler/build_state.py`, run daily after the last scheduled collector
window, and in historical mode for Section 2.4 and the exhibits:

1. Reads the series store (never the network, never raw snapshots
   directly, except in a declared re-parse).
2. Computes each gauge at its native cadence up to today, appends any
   new live gauge rows to `history/gauges/` with `kind: live`, and
   computes today's percentiles by the uniform rule.
3. Applies the composite rule (Section 3.2), the overlays, and the
   disagreement rules (Section 3.3).
4. Checks the forecast hook triggers (F2, F4 event triggers; F1, F3
   calendar triggers), writes any issued forecast to the estate ledger
   through its interface, and collects any grades that fall due, so
   the state document can report them the day they land.
5. Writes `output/state-latest.json` and the dated copy in
   `live/state/`, then renders `output/STATE.md` and its archive copy,
   then writes the consumer file (Section 6) and the terminal page feed
   (Section 5.5).
6. Prints a one-line run receipt (gauges computed, gauges stale, hooks
   fired, grades landed, failures named) that the scheduling lane
   files with the run. A run that computes the state from a store it
   also silently repaired is forbidden: the compiler never writes to
   `history/series/`. Repairs happen in collectors, in the open.

Failure rule: if the compiler cannot reach four core gauges, it still
writes the state, named `Insufficient data`, with the gaps named. It
never writes yesterday's state with today's date.

## 5.4 The ledger interface

* Writes go through the estate ledger module's own append path, with
  its hash chain and its five-clock lineage envelope (as inventoried
  in MEASUREMENT Part 1.2). The Psychology Engine's registry entries
  name: the hook (F1 to F4), the parent proposition (P1, P5, P22 and
  P3, P19), the variable, the segment, the horizon, the threshold or
  buckets, the base rate and its source in the history store, the
  board (belief, variance, cross-section, return), and the kill
  condition, verbatim from Section 4.
* The interface is append-only from this program's side. It exposes no
  edit and no delete, and this program's code contains no code path
  that opens the ledger file for writing directly.
* Grades are computed by the estate grading module where a resolver
  exists for the outcome kind, and by this program's `grading_hooks.py`
  only for outcome kinds the estate module does not yet resolve
  (survey prints, realised volatility windows, basket spreads from the
  French library), with those resolvers registered in the registry
  like any other, so the Record and the terminal audit layer
  (MEASUREMENT Part 1.3) can recompute them.

## 5.5 Outputs

1. State JSON: `output/state-latest.json`, the machine form of the
   Section 3.1 state, schema versioned (`schema: psychology-state/1`),
   containing the regime, the composite score, the gauge table with
   percentiles and flags, the G4 and G8 lines, the disagreement
   statement, the extremes list with entry dates, the hooks summary,
   and the full provenance block (per-gauge as-of dates, store spans,
   formula versions).
2. The one-page state document: `output/STATE.md`, rendered from the
   JSON, one page in the plain sense: regime and disagreement first,
   the gauge table, the extremes, the slow climate and fragility
   lines, the belief anchor summary, the crypto overnight line, the
   hooks and grades, and a short `what changed since yesterday`
   section naming every gauge that crossed a zone boundary.
3. The terminal reader page: a new page in the terminal lineup,
   working name `Market Mood`, fed by a feed file this program
   publishes next to the existing terminal feeds, in the lineup's
   established style: simple, clear, plain words, no disclaimer-style
   copy, factual state labels (dates, coverage, `no data`, `stale`,
   `preliminary`) printed as information. The page shows:
   * today's regime, disagreement statement, and gauge table with
     historical percentiles, exactly as in the state document;
   * the calibration exhibits (Section 2.5) as a fixed panel, each
     historical reading labelled RECONSTRUCTION;
   * the forecast record in two separate tables, live grades and
     backtest grades, never merged, each row carrying its board and
     its independent episode count;
   * the named paid gaps (Investors Intelligence, Bank of America
     Fund Manager Survey, EPFR) as a short `not measured` list, so a
     reader knows the shape of what is missing;
   * the CNN Fear and Greed value, if shown at all, as a context tile
     labelled as an outside composite with no audited archive, never
     in the gauge table.
4. The consumer file: Section 6.

Scheduling: the whole pipeline runs as one lane in Midna's personal
quant schedule, daily after the close, completing before 04:00 ET,
with a weekly Thursday and monthly legs handled by the collectors' own
schedules. A Saturday deep-work slot re-runs the exhibits check and
the backtest record's standing gates (Section 7) so calibration drift
is caught weekly, not discovered at grading time.

---

# 6. THE CONSUMER: MIDNA'S OWN BOOK

Fixed paths, written by the compiler's publish step, overwritten daily
as a state file (the file is a snapshot, its history lives in the
engine's own archive, and the book's journal discipline supplies the
point-in-time record):

* `~/workspace/midna-book/SENTIMENT-STATE.md` (the read)
* `~/workspace/midna-book/SENTIMENT-STATE.json` (the same state, machine
  form, for any book tooling that wants percentiles without parsing
  prose)

Contents of the markdown file, in this order:

1. Header: date, regime name (with any `Contested:` prefix and any G4
   suffix), composite percentile, slow climate line.
2. The gauge table: all nine gauges, percentile, zone, as-of date,
   flags. Identical numbers to the state document. One source of
   truth, two renderings.
3. Extremes flagged: every gauge in a 0 to 5 or 95 to 100 zone, with
   its zone entry date and duration in sessions, and, for G4, the
   forcing legs in their extreme zones named.
4. The disagreement paragraph, verbatim from the state.
5. Hooks: any forecast fired, due, or graded, with its plain language
   and its board. F4's fixed sentence appears here word for word when
   it fires.
6. `How this bears on today's trading`: a short section, three to six
   lines, written by rule from the state, in this discipline:
   * It names the crowd state and depth fields the book's trade cards
     already carry (CHARTER Amendment 6 game layer: crowd state,
     crowding grade with named evidence, pre-declared flow reading).
     This file is the supplier of those fields from stored
     measurements, replacing judgment-only fills (MEASUREMENT
     Part 1.6).
   * It states capacity and forcing facts where they bind: leverage
     extremes, funding extremes, amplifier state, credit confirmation
     or denial. These bear on how a move may travel, and the section
     says that, in those words, rather than implying a direction.
   * It states the contrary-versus-momentum classification of the
     current reading under THEORY Section 4.4's four conditions
     (horizon, crowding and capacity, forcing, who holds it), in one
     line, with its horizon printed. Directional language without a
     horizon is forbidden in this file, as everywhere in the program.
   * It never orders. It contains no position, no size, no entry, no
     exit. Words like `buy` and `sell` appear only inside quoted
     descriptions of what the crowd is doing. Midna's risk
     constitution is untouched by this file, and the file's last line
     states its own status in factual words: `Information for the
     pre-open read. Not an order.`
7. Monday addition: the weekend crypto pair record (G9) printed at the
   top of section 3, labelled `ungraded` until the ledger grades the
   transfer question.

Timing: the file must exist, fresh for the prior session, before the
08:00 ET pre-open slot in Midna's schedule (MEASUREMENT Part 1.6). A
Friday weekly summary block appends to the same file before Friday
grading: the week's zone crossings, the week's hook grades, and the
state's percentile path for the week. The clock discipline of the book
applies in full: a reading used on a trade card is the reading as it
stood before the decision, and this file's write timestamp is stored
in the JSON so that claim can be checked.

---

# 7. THE BUILD LIST FOR V1

Ordered. Each item is built and accepted before the next is called
done, though collectors for independent sources may be written in
parallel inside item 2. Every acceptance test is stated so it can
fail. Status language follows house law: an item is GREEN only on its
acceptance evidence from the final state, PARTIAL only with the
unproven part named, and nothing below is a half-wired stub: v1 ships
complete for everything it includes, and Section 7.3 names everything
it does not include as separate future commissions.

## 7.1 The list

1. **Store skeleton and provenance harness.** The folder layout of
   Section 2.1, the header writer and checker of Section 2.2, the pull
   log, and the unique-key write path.
   Acceptance: the header checker passes on every series file present
   and fails, by name, on a test file with a missing provenance field
   and on a test file with a duplicate natural key. Both failure
   directions are demonstrated, not asserted.
2. **Backfill collectors and the history store.** One backfill per
   archive in Section 2.3, on the Section 5.2 harness, producing the
   full series store.
   Acceptance: every series file's downloaded span matches its
   header's `downloaded_span`; the four hard numeric checks pass
   (VIX close 82.69 on 2020-03-16; VIX close 80.86 on 2008-11-20;
   Michigan's all-time low falling in June 2022; FINRA margin debit
   balances peaking in March 2000 within the stored monthly file); a
   re-run of two named backfills (AAII and Cboe VIX) adds zero rows;
   a killed-and-resumed backfill (COT annual files) completes with a
   checkpoint trail and a row count equal to the uninterrupted run's.
3. **Live collectors.** The twelve collectors of Section 5.1, with raw
   snapshot retention and isolated failure.
   Acceptance: over five consecutive sessions, every collector either
   lands its snapshot or files its failure record, with no silent
   collector; a deliberately broken source (credentials revoked in a
   test copy of the config) degrades exactly its own gauges to `stale`
   or `partial` in the state and no others; the FINRA per-name short
   volume and per-name dark stores accrue rows for those five
   sessions, curing the two named Part 1 gaps at the store level.
4. **Gauge compiler, historical mode, and bands.** The Section 1
   formulas over the store, producing `history/gauges/` with the
   `kind` column, and the uniform percentile and zone machinery.
   Acceptance: every pre-live row in every gauge file carries
   `kind: reconstruction`; hand-checkable recomputation of three
   named gauge values (one weekly, one monthly, one daily) from the
   stored inputs matches the compiler's output to rounding; the
   percentile rule's no-future property is proven by a test that
   truncates the store at a past date and shows the percentile for
   that date is unchanged by the presence of later data; gauges under
   the minimum-history rule show NO BAND and no percentile.
5. **Calibration exhibits.** Section 2.5, produced by the compiler's
   historical mode, published to `exhibits/`.
   Acceptance: every episode and control row is present; every hard
   numeric check inside the exhibits matches the store; every
   `as expected` verdict traces to the expectation written in
   Section 2.5, and every deviation is printed as `surprising, noted`
   with its note, with zero rows silently dropped; gauges without
   data on an episode date print their start year.
6. **The P22 backtest gate.** The backtest record harness of
   Section 4.4, with P22 and P3 run first, then P5, P19, P2, and P14
   in coarse monthly form, each in its own folder with frozen
   specification and coverage printed.
   Acceptance: every result file states its board, its coverage, its
   independent episode count, and its kill-condition verdict; F3's
   ship or no-ship outcome is decided by the P22 result and recorded
   in the build log either way; no backtest number appears anywhere
   in the live ledger, verified by a ledger scan for the backtest
   run identifiers.
7. **Composite and daily state.** The Section 3 compiler on live
   inputs, the state JSON, and the one-page state document.
   Acceptance: over the same five sessions as item 3, a state file
   exists for every session with a write time before 04:00 ET the
   next morning; the regime in each state is recomputed by hand from
   its printed gauge table and matches; a synthetic contested input
   set (core gauges forced to both poles in a test store) produces a
   `Contested:` state naming both poles; a synthetic four-gauge
   outage produces `Insufficient data` and no composite score.
8. **Forecast hooks and the ledger interface.** F1, F2, F4 live, and
   F3 live if and only if item 6 gates it in. Registry entries,
   append path, hook grading resolvers.
   Acceptance: each hook's registry entry carries every field
   Section 5.4 names, with the kill condition verbatim; a test
   forecast written through the interface appears in the estate
   ledger with its hash chain intact, verified by the ledger's own
   check; the ledger file contains no forecast dated before the
   engine's live start (the never-backfilled line, scanned); F2's
   ledger entries carry the registered `none, variance only`
   direction value; a matured test hook grades end to end and its
   grade appears in the next state document.
9. **The consumer file.** Section 6, both files, on the compiler's
   publish step.
   Acceptance: for the same five sessions, `SENTIMENT-STATE.md`
   exists before 08:00 ET each morning with numbers identical to
   that morning's state JSON (checked by a diff of the gauge tables);
   the file contains no position, size, or order language, checked by
   a written word scan whose hit list is eyeballed, not merely
   counted; the Friday run carries the weekly summary block; a
   Monday run carries the weekend crypto pair, labelled `ungraded`.
10. **The terminal page.** The `Market Mood` page and its feed, per
    Section 5.5.
    Acceptance: the page renders today's state from the feed with
    percentiles matching the state JSON; the exhibits panel labels
    every historical reading RECONSTRUCTION; live and backtest grade
    tables are separate on the page, verified in the rendered output,
    not only in the feed; the paid gaps list and the CNN context
    labelling render as specified; a feed outage renders the page's
    `no data` state rather than yesterday's numbers under today's
    date.
11. **The scheduling lane.** The daily lane in Midna's personal quant
    schedule, the collector schedules of Section 5.1, and the
    Saturday exhibits and gates re-check.
    Acceptance: five consecutive unattended sessions produce the full
    output set (state, consumer file, feed) with receipts filed; the
    Saturday re-check reproduces the exhibits from the store and
    reports any drift by name; one missed day, simulated by disabling
    the lane for a session in a test window, is named as a gap in the
    next state document rather than backfilled (the state archive
    shows the hole).
12. **The v1 close-out audit.** A single audit pass over the built
    engine against this design, section by section.
    Acceptance: a written audit file in this research folder records,
    per section of this design, `built as designed` or the deviation
    with its reason; every gauge's live percentile on audit day is
    recomputed independently from the store and matches the page;
    the audit names every UNVERIFIED archive depth that the backfills
    confirmed, corrected, or failed to reach, closing the loop the
    studies opened.

## 7.2 What v1 deliberately includes at context rank

Collected and displayed from day one, in the gauge or on the tile, but
carrying no composite vote and no forecast claim until their own rules
promote them: the G7 social lines (StockTwits, Reddit), the G8 belief
tables beyond the summary line, the G9 transfer pair, the Morgue Tape
context line inside G5, the DIX short pressure line inside G3, and the
GEX amplifier line inside G4. Each carries its status in words
(`collecting`, `no band`, `ungraded`, `modelled`). Context rank is a
rank, printed, not a quiet demotion.

## 7.3 Not in v1: separate future commissions, named now

Each of these is a real build with a real mechanism, excluded from v1
so that v1 is complete rather than broad. None of them is stubbed,
half-wired, or pre-claimed anywhere in v1 outputs.

1. The quantified positioning convexity index (MEASUREMENT idea 3.2,
   THEORY P14 at full frequency): forced-flow estimates per 1, 2, and
   5 percent move, with published elasticities estimated on the
   estate's own accrued record.
2. Narrative velocity and saturation as graded instruments (ideas 3.1,
   THEORY P12 and P13 in full): the saturation checklist ships in v1
   as a displayed checklist inside G7. Its forecasts are a later
   commission, entered through the frontier discipline of Midna's
   book if she takes them up.
3. The attention-to-flow lead-time model (idea 3.3, THEORY P7 and P8
   as live hooks): needs months of joint accrual of attention, tape,
   and FINRA stores that v1 creates. The collection is v1. The model
   is not.
4. Dealer gamma as a graded historical family (THEORY P15 as a hook
   beyond Engine 8's existing grading): live-ledger-only by its data
   reality, and properly an extension of the Morgue's own engines,
   not of this program.
5. Language shift metrics (idea 3.5): the FOMC statement variant
   first, social text second, earnings calls only if a free corpus of
   audit standard ever exists.
6. The crowding overlap map (idea 3.14): 13F plus short interest plus
   options per name, as a risk map for the book, after the per-name
   stores of item 3 have widened coverage beyond the current board
   universe.
7. The revision breadth gauge (idea 3.13): a byproduct of correct
   vintage storage, which v1 builds. Reading it as a gauge is v2.
8. Social gauge promotion (family (f) as a voting gauge): only by the
   G7 promotion rule, after 250 stored sessions and a design
   amendment.
9. Weather, daylight, and sports displacement tiles (ideas 3.8 and
   3.9): graded SPECULATIVE and LATER in MEASUREMENT. They are not in
   v1 at any rank, and the weather tile in particular must never share
   a composite with serious gauges if it is ever built.
10. Any paid source (Investors Intelligence depth, Bank of America
    Fund Manager Survey, EPFR, RavenPack, X firehose): only on a
    future explicit commission that changes the house rule. Until
    then they remain named gaps, which is information, not failure.

## Closing note to the builder

Build the panel, in the order above. Backfill the inputs and label the
reconstructions. Keep the ledger sacred and the backtest record in its
own folder with its own name. Let the gauges disagree in print. The
engine's worth is not a number that is right about the market. It is a
state that is honest about the crowd, calibrated on the crowd's actual
history back to 1952 and 1965 where the record honestly goes, and a
small set of forecasts that were written down before their horizons
and graded where everyone can see the grade. Anything more claimed
than that, P4 has already capped. Anything less built than that, this
design has already named.

End of ENGINE-DESIGN. Companion documents: STUDY-THEORY.md and
STUDY-MEASUREMENT.md, same folder, same commission, same date.
