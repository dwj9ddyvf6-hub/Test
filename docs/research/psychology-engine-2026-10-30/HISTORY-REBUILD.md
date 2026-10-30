# HISTORY REBUILD SHEET: Psychology Engine history store

Purpose: rebuild the Psychology Engine history store (the `history/series/`
files) from public sources alone, with no access to the original local
files. Each entry below gives the series name, its source, the exact
re-pull route as recorded in the series file's provenance header (quoted
verbatim from the `source_url_or_route` header line), the archive span
the source claims, the span actually downloaded on 2026-10-30, recorded
breaks, and transforms.

Compiled 2026-10-30 from the provenance headers of the 37 stored series
files and the pull log (`history/provenance/PULL-LOG.md`, saved with the
engine package). Where the header and the pull log disagree or the
header carries no concrete route, that is stated plainly. Nothing here
is invented: a route that could not be recovered from the header or the
pull log is marked as under-specified.

Conventions used by every series file: the first lines of each file are
a `#` comment provenance header (series, source, source_url_or_route,
retrieved, last_pull, revision_policy, as_of_meaning, archive_claim,
downloaded_span, breaks, transforms, file_sha256), then a CSV column
header row, then data. The date column is always the observation date
(as-of), not the download date. Recursive instruction: after re-pulling,
rewrite the header with the new retrieved date and the span actually
obtained.

## Verification anchors (check a re-pull against these)

From the build audit (exhibits), against the stored files:

- Cboe VIX close on 2020-03-16 is 82.69. Stored file matches.
- Cboe VIX close on 2008-11-20 is 80.86. Stored file matches.
- Michigan UMCSENT for June 2022 is 50.0 in the stored file, exactly the
  published print. It is no longer the series all-time low in the latest
  FRED vintage: the stored series prints 44.8 in 2026-05.
- FINRA margin debit balances for March 2000 are 299,933 (million) in
  the stored file and present. The nominal peak of the stored series is
  2026-06, because nominal balances grow over decades.

## Series with downloaded data

### michigan_umcsent_monthly
- File: history/series/michigan_umcsent_monthly.csv
- Source: FRED (Federal Reserve Bank of St. Louis)
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=UMCSENT&cosd=1950-01-01
- Columns: date, value_first, value_latest
- Archive claim: archive November 1952 VERIFIED via FRED
- Downloaded: 1952-11-01 to 2026-09-01, 677 rows
- Breaks: quarterly to 1977, monthly from 1978
- Transforms: none
- Revision policy (header): both vintages stored where obtainable; the
  FRED route serves the latest vintage; value_first set equal at first
  pull and preserved on later pulls
- Rebuild note: one GET of the route returns the whole series as CSV
  (two columns, date and UMCSENT). Expect early FRED timeouts; retry.

### fred_hy_oas_daily
- File: history/series/fred_hy_oas_daily.csv
- Source: FRED (Federal Reserve Bank of St. Louis), chunked 2 year windows
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&cosd=1950-01-01
- Columns: date, value_first, value_latest
- Archive claim: HY OAS from Dec 1996 as published
- Downloaded: 2023-10-31 to 2026-10-29, 786 rows
- Breaks: none known
- Transforms: none
- Rebuild note: the FRED graph route caps a single pull near 800
  points, and in the 2026-10-30 build most 2 year chunk windows were
  refused, so only the most recent chunk landed. The Dec 1996 archive
  depth is UNREACHED: this is a named gap (FRED OAS depth). A rebuild
  should still attempt chunked windows with cosd and coed set per
  window and record whatever span actually lands.

### fred_ig_oas_daily
- File: history/series/fred_ig_oas_daily.csv
- Source: FRED (Federal Reserve Bank of St. Louis), chunked 2 year windows
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A0CM&cosd=1950-01-01
- Columns: date, value_first, value_latest
- Archive claim: IG OAS as published
- Downloaded: 2023-10-31 to 2026-10-29, 785 rows
- Breaks: none known
- Transforms: none
- Rebuild note: same FRED graph point cap as the HY series above; the
  pre-2023 depth is subject to the same named gap.

### cboe_vix_daily
- File: history/series/cboe_vix_daily.csv
- Source: Cboe index history file
- Route (header): https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv
- Columns: date, open, high, low, close
- Archive claim: VIX from 1990 VERIFIED
- Downloaded: 1990-01-02 to 2026-10-29, 9305 rows
- Breaks: none known
- Transforms: none

### cboe_skew_daily
- File: history/series/cboe_skew_daily.csv
- Source: Cboe index history file
- Route (header): https://cdn.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv
- Columns: date, close
- Archive claim: SKEW from 1990 as reported
- Downloaded: 1990-01-02 to 2026-10-29, 9259 rows
- Breaks: none known
- Transforms: none

### cboe_vix3m_daily
- File: history/series/cboe_vix3m_daily.csv
- Source: Cboe index history file
- Route (header): https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv
- Columns: date, open, high, low, close
- Archive claim: as published by Cboe
- Downloaded: 2009-09-18 to 2026-10-30, 4306 rows
- Breaks: none known
- Transforms: none

### cboe_vix9d_daily
- File: history/series/cboe_vix9d_daily.csv
- Source: Cboe index history file
- Route (header): https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv
- Columns: date, open, high, low, close
- Archive claim: as published by Cboe
- Downloaded: 2011-01-04 to 2026-10-29, 3979 rows
- Breaks: none known
- Transforms: none

### cot_tff_weekly
- File: history/series/cot_tff_weekly.csv
- Source: CFTC Traders in Financial Futures annual files (futures only)
- Route (header): https://www.cftc.gov/files/dea/history/fut_fin_txt_<year>.zip
- Columns: date, net_scaled_mean, families
- Archive claim: published from 2006; complete annual files listed from
  September 2009 VERIFIED in design; this pull covers the years listed
  in the pull log
- Downloaded: 2015-01-06 to 2026-10-27, 617 rows, from the annual files
  for 2015 through 2026
- Breaks: 2006 to 2009 junction with Legacy marked as a series break;
  coverage for 2006 to 2009 checked file by file is a named gap in the
  v1 pull (2015 forward pulled)
- Transforms: leveraged fund net scaled by open interest per contract
  family, averaged across S and P 500 and Nasdaq 100 families

### finra_margin_monthly
- File: history/series/finra_margin_monthly.csv
- Source: FINRA margin statistics monthly Excel
- Route (header): https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx
- Columns: date, debit_balances, free_credit_cash, free_credit_margin
- Archive claim: from January 1997 VERIFIED in design
- Downloaded: 1997-01-01 to 2026-09-01, 357 rows
- Breaks: February 2010 collection break: separate NYSE and FINRA
  collection before, one FINRA Rule 4521 collection after
- Transforms: none

### altme_fear_greed_daily
- File: history/series/altme_fear_greed_daily.csv
- Source: Alternative.me Crypto Fear and Greed Index API
- Route (header): https://api.alternative.me/fng/?limit=0&format=json
- Columns: date, value, classification
- Archive claim: daily from 2018-02-01 VERIFIED in design
- Downloaded: 2018-02-01 to 2026-10-30, 3190 rows
- Breaks: survey component reported paused by publisher in later years
  (recipe note)
- Transforms: none; recipe stored in the header: volatility 25,
  momentum/volume 25, social 15, surveys 15 (paused), dominance 10,
  Trends 10

### gdelt_gkg_tone_daily
- File: history/series/gdelt_gkg_tone_daily.csv
- Source: GDELT DOC 2.0 API timelinetone for the stock market query
- Route (header): https://api.gdeltproject.org/api/v2/doc/doc?query=%22stock%20market%22&mode=timelinetone&timespan=3m&format=json
- Columns: date, tone
- Archive claim: GKG tone-rich fields from February 2015 VERIFIED in
  design; the DOC API serves a rolling recent window, recorded as
  downloaded
- Downloaded: 2026-08-02 to 2026-10-27, 71 rows (rolling window only)
- Breaks: pre-2013 tone does not exist in GKG form and is never implied
- Transforms: none
- Rebuild note: the deep GKG file backfill was not pulled in v1; only
  the DOC rolling window is in the store. This is a named gap.

### wikipedia_pageviews_daily
- File: history/series/wikipedia_pageviews_daily.csv
- Source: Wikimedia pageviews API (concept set mean)
- Route (header): wikimedia.org api rest_v1 pageviews
- Columns: date, views_mean, pages
- Archive claim: API from July 2015 VERIFIED in design
- Downloaded: 2015-07-01 to 2026-10-29, 4139 rows
- Breaks: none known
- Transforms: mean daily views across the frozen concept set
- Rebuild note: the header names the host and API family only, not a
  full URL: route under-specified in header. The frozen concept set, as
  evidenced by the raw snapshot files kept from the build, is the four
  English Wikipedia articles Bear market, Bull market, Recession, and
  Stock market crash (the data column `pages` reads 4 throughout). Use
  the Wikimedia pageviews REST API per-article daily endpoint for each
  of the four, then average per day.

### price_fred_sp500_daily
- File: history/series/price_fred_sp500_daily.csv
- Source: FRED daily index close (price only)
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2025-01-01&coed=2026-12-31
- Columns: date, close
- Archive claim: as published on FRED, chunked past the graph point cap
- Downloaded: 2016-10-31 to 2026-10-28, 2512 rows
- Breaks: none known
- Transforms: close only
- Rebuild note: the header URL shows one example window; the pull log
  records the method as FRED chunked pulls (repeat the graph CSV route
  in windows with cosd and coed set per window) to get past the point
  cap.

### price_fred_nasdaqcom_daily
- File: history/series/price_fred_nasdaqcom_daily.csv
- Source: FRED daily index close (price only)
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=2026-01-01&coed=2027-12-31
- Columns: date, close
- Archive claim: as published on FRED, chunked past the graph point cap
- Downloaded: 1990-01-02 to 2026-10-29, 9276 rows
- Breaks: none known
- Transforms: close only
- Rebuild note: same chunked-window method as the SP500 file above.

### price_fred_djia_daily
- File: history/series/price_fred_djia_daily.csv
- Source: FRED daily index close (price only)
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=DJIA&cosd=2025-01-01&coed=2026-12-31
- Columns: date, close
- Archive claim: as published on FRED, chunked past the graph point cap
- Downloaded: 2016-10-31 to 2026-10-30, 2514 rows
- Breaks: none known
- Transforms: close only
- Rebuild note: same chunked-window method as the SP500 file above.

### price_fred_nasdaq100_daily
- File: history/series/price_fred_nasdaq100_daily.csv
- Source: FRED daily index close (price only)
- Route (header): https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100&cosd=2025-01-01&coed=2026-12-31
- Columns: date, close
- Archive claim: as published on FRED, chunked past the graph point cap
- Downloaded: 2013-01-02 to 2026-10-29, 3479 rows
- Breaks: none known
- Transforms: close only
- Rebuild note: same chunked-window method as the SP500 file above.

### breadth_daily
- File: history/series/breadth_daily.csv
- Source: computed from the stored index price panel (FRED SP500,
  NASDAQCOM, DJIA, NASDAQ100 closes)
- Route (header): local computation over price_fred_*_daily.csv
- Columns: date, pct_above_50, pct_above_200, adv_share, panel_names
- Archive claim: as deep as the panel honestly serves, recorded as
  downloaded
- Downloaded: 2013-10-17 to 2026-10-29, 3279 rows
- Breaks: narrow 4-index panel, not the 1833-name estate panel;
  survivorship and narrowness caveat applies
- Transforms: percent of panel above 50 and 200 day averages; advancer
  share; price only, no volume
- Rebuild note: pull the four price_fred series above first, then
  compute. The companion file history/series/panel_membership_notes.md
  records the panel caveat and names the estate 1833-name panel
  extension as a gap (no Alpaca key was found in the desk key store at
  build time).

### crypto_funding_btc_daily
- File: history/series/crypto_funding_btc_daily.csv
- Source (header): OKX public API (Binance route refused from this
  network; OKX is the design fallback) (cross-check and fallback for
  Coinalyze per design)
- Route (header): exchange public funding-rate history
- Columns: date, funding_rate_daily_mean
- Archive claim: liquid history from about 2019, per-venue starts
  recorded as downloaded
- Downloaded: 2026-07-27 to 2026-10-30, 96 daily rows (286 funding
  intervals)
- Breaks: none known
- Transforms: none
- Rebuild note: the header route is a description, not an endpoint:
  route under-specified in header. The header and the pull log
  disagree about the venue that produced the stored rows: the header
  names OKX as the working fallback, while the pull log records the
  successful pull as "binance fapi fundingRate" after an earlier
  Binance attempt failed with curl exit 22, with the concrete endpoint
  https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000&startTime=1567900800000
  appearing in the failed attempt line. Both records are carried here
  unresolved; a rebuild should try the Binance endpoint as recorded
  and the OKX public funding-rate history endpoint, and record which
  venue actually served the rows.

### crypto_funding_eth_daily
- File: history/series/crypto_funding_eth_daily.csv
- Source (header): OKX public API (Binance route refused from this
  network; OKX is the design fallback) (cross-check and fallback for
  Coinalyze per design)
- Route (header): exchange public funding-rate history
- Columns: date, funding_rate_daily_mean
- Archive claim: liquid history from about 2019, per-venue starts
  recorded as downloaded
- Downloaded: 2026-07-27 to 2026-10-30, 96 daily rows (286 funding
  intervals)
- Breaks: none known
- Transforms: none
- Rebuild note: same venue discrepancy as the BTC file above. The
  Binance endpoint recorded in the pull log is
  https://fapi.binance.com/fapi/v1/fundingRate?symbol=ETHUSDT&limit=1000&startTime=1567900800000
  (failed attempt line); the log's success line reads "binance fapi
  fundingRate". Route under-specified in header.

### polymarket_daily
- File: history/series/polymarket_daily.csv
- Source: Polymarket Gamma API (free reads)
- Route (header): https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&order=volume24hr&ascending=false
- Columns: date, venue, event, probability, volume
- Archive claim: platform from 2020; graded history begins at first
  snapshot, never backfilled
- Downloaded: 2026-10-30 only, snapshot of 20 events
- Breaks: none known
- Transforms: none
- Rebuild note: this is a snapshot series. History is accrued by
  running the route on later dates, never by backfilling.

### kalshi_daily
- File: history/series/kalshi_daily.csv
- Source: Kalshi public market data
- Route (header): https://api.elections.kalshi.com/trade-api/v2/markets?limit=10&series_ticker=KXFEDDECISION
- Columns: date, venue, event, probability, volume
- Archive claim: exchange public from 2021; graded history begins at
  first snapshot
- Downloaded: 2026-10-30 only, snapshot of 10 markets
- Breaks: none known
- Transforms: none
- Rebuild note: snapshot series, same handling as polymarket_daily.

## Series absent in v1: refusals and named gaps

Each file below exists in the store as a header plus a column row, with
downloaded_span "absent". Absence is recorded, never zero filled.

### aaii_weekly (REFUSED)
- File: history/series/aaii_weekly.csv
- Source: AAII public download
- Route (header): https://www.aaii.com/files/surveys/sentiment-survey.xlsx
- Archive claim: July 1987 VERIFIED
- Downloaded: absent
- What happened: both the .xlsx route in the header and the .csv
  variant (https://www.aaii.com/files/surveys/sentiment-survey.csv)
  returned HTTP 404 from this network (curl exit 22), repeatedly.
  Publisher bot wall suspected; no substitute source was used.
- Breaks: none known. Transforms: none.

### naaim_weekly (ROUTE UNRESOLVED)
- File: history/series/naaim_weekly.csv
- Source: NAAIM public file
- Route (header): https://naaim.org/programs/naaim-exposure-index/
- Archive claim: July 2006 VERIFIED
- Downloaded: absent
- What happened: the header route is the program page; the build found
  no data file link on that page (pull log: "no data file link found
  on NAAIM page"). The direct file route behind the page is not
  recorded anywhere in the header or the pull log: route
  under-specified in header.

### baker_wurgler_monthly (REFUSED)
- File: history/series/baker_wurgler_monthly.csv
- Source: Wurgler NYU Stern spreadsheet
- Route (header): pages.stern.nyu.edu/~jwurgler
- Archive claim: July 1965 VERIFIED
- Downloaded: absent
- What happened: the header route is the author page root only. The
  file routes tried, per the pull log, were
  https://pages.stern.nyu.edu/~jwurgler/data/Investor_Sentiment_Data_20251028_Post.xlsx
  (HTTP 404) and https://pages.stern.nyu.edu/~jwurgler/data/SENTIMENT.xls
  (curl exit 22; the Stern page returns 403 and current file names
  404 from this network). The dated file name changes over time; a
  rebuild should list the author page's data directory links first,
  then pull the current sentiment workbook.

### cboe_putcall_daily (REFUSED)
- File: history/series/cboe_putcall_daily.csv
- Source: Cboe put/call files
- Route (header): https://cdn.cboe.com/resources/us/options/market_statistics/historical_data/totalpc.csv
- Archive claim: 2003 and 2006 UNVERIFIED
- Downloaded: absent
- What happened: the header route and the www variant
  (https://www.cboe.com/us/options/market_statistics/historical_data/totalpc.csv)
  both returned HTTP 404 (curl exit 22) at build. No substitute was
  used. Because this leg is absent, gauge G5 runs on the SKEW leg only
  and forecast hook F2 cannot evaluate its trigger.

### cot_legacy_weekly (NAMED GAP: COT Legacy depth)
- File: history/series/cot_legacy_weekly.csv
- Source: CFTC Legacy annual files
- Route (header): see PULL-LOG.md
- Archive claim: futures only from 1986 VERIFIED in design
- Downloaded: absent
- What happened: the pull log carries only an absence note: "Legacy
  deep archive not pulled in this build; TFF 2015 forward pulled."
  No concrete Legacy file route appears in the header or the pull
  log: route under-specified in header. The CFTC publishes Legacy
  futures-only annual files from 1986; recovering the exact file route
  is part of closing this gap.

### cboe_vix_futures_curve (NAMED GAP: VIX futures)
- File: history/series/cboe_vix_futures_curve.csv
- Source: Cboe VIX futures settlements
- Route (header): see PULL-LOG.md
- Archive claim: futures from 2004 VERIFIED in design
- Downloaded: absent
- What happened: the pull log carries only an absence note:
  "settlement file route not resolved in this build." No concrete
  route appears in the header or the pull log: route under-specified
  in header.

### ici_flows_weekly and ici_flows_monthly (NAMED GAP: ICI)
- Files: history/series/ici_flows_weekly.csv,
  history/series/ici_flows_monthly.csv
- Source: ICI published flow tables
- Route (header, both files): see PULL-LOG.md
- Archive claim: archive depth UNVERIFIED in design
- Downloaded: absent (both)
- What happened: the pull log carries only absence notes: "ICI table
  route not resolved in this build." No concrete route appears in the
  headers or the pull log: route under-specified in header.

### trends_fears_weekly (NAMED GAP: Trends FEARS)
- File: history/series/trends_fears_weekly.csv
- Source: Google Trends pinned pulls
- Route (header): see PULL-LOG.md
- Archive claim: from January 2004 as published by Google
- Downloaded: absent
- What happened: the pull log records: "Trends values are rescaled
  per request and pytrends is not installed; pinned pull harness is
  code present, first pull pending." No concrete query route is
  recorded: route under-specified in header. The pinned pull harness
  is code in the engine package (pipeline.py, saved with the package).

### trends_topics_daily (NAMED GAP, same class as FEARS)
- File: history/series/trends_topics_daily.csv
- Source: Google Trends pinned pulls
- Route (header): see PULL-LOG.md
- Archive claim: from January 2004
- Downloaded: absent
- What happened: pull log: "v1 pull gap, see fears basket." Route
  under-specified in header, same handling as trends_fears_weekly.

### metaculus_daily (REFUSED)
- File: history/series/metaculus_daily.csv
- Source: Metaculus public API
- Route (header): see PULL-LOG.md
- Route (pull log): https://www.metaculus.com/api2/questions/?limit=10&search=recession
- Archive claim: platform from 2015 as reported
- Downloaded: absent
- What happened: the API route returned an HTTP error (curl exit 22)
  at build. The pull log also notes graded history begins at first
  snapshot; this is a snapshot leg, so a successful later pull starts
  the record rather than backfilling it.

### cboe_vix_term_daily (DERIVED, not pulled)
- File: history/series/cboe_vix_term_daily.csv
- Source: Cboe VIX9D and VIX3M history files
- Route (header): see PULL-LOG.md
- Archive claim: as published by Cboe
- Downloaded: absent as a stored pull
- What happened: the pull log records that term values are computed
  at gauge stage from cboe_vix_daily and companion files when landed.
  Rebuild path: pull cboe_vix9d_daily and cboe_vix3m_daily by their
  routes above; the term series is derived from them, not downloaded.

### dix_index_daily (ESTATE REUSE, not pulled)
- File: history/series/dix_index_daily.csv
- Source: Morgue DIX record (estate lane, reused)
- Route (header): see PULL-LOG.md
- Archive claim: estate record, short
- Downloaded: absent
- What happened: the pull log records that the estate DIX record
  lives in the Morgue and is not duplicated here; it displays as
  context with NO BAND until 250 sessions. No external route exists
  to record: route under-specified in header by design (internal
  estate source).

### morgue_map_gex_daily (ESTATE REUSE, not pulled)
- File: history/series/morgue_map_gex_daily.csv
- Source: Morgue Map GEX (estate lane, modelled)
- Route (header): see PULL-LOG.md
- Archive claim: estate record from collection
- Downloaded: absent
- What happened: the pull log records a read-only estate lane read:
  21 Morgue output files present; GEX and DIX values stay in the
  Morgue record, labelled modelled, NO BAND. No external route
  exists to record: route under-specified in header by design
  (internal estate source).

### reddit_mentions_daily (COLLECTING, no key)
- File: history/series/reddit_mentions_daily.csv
- Source: Reddit official API free tier
- Route (header): see PULL-LOG.md
- Archive claim: collection start only
- Downloaded: absent
- What happened: the pull log records: no key configured in this
  build; collecting from engine start; context rank only in v1. No
  concrete endpoint is recorded: route under-specified in header.

### stocktwits_daily (COLLECTING, no key)
- File: history/series/stocktwits_daily.csv
- Source: StockTwits API (keyed free developer access)
- Route (header): see PULL-LOG.md
- Archive claim: collection start only
- Downloaded: absent
- What happened: the pull log records: no key configured in this
  build; collecting status recorded, not faked. No concrete endpoint
  is recorded: route under-specified in header.

## Additional stores recorded in the pull log (no series header file)

### FINRA per-name short volume (history/per_name/)
- Route (pull log): https://cdn.finra.org/equity/regsho/daily/FNSQshvol20261030.txt
- Pattern: the dated file name is FNSQshvol<YYYYMMDD>.txt under
  https://cdn.finra.org/equity/regsho/daily/
- Downloaded: 2026-10-30 file, 12266 rows, stored as
  history/per_name/finra_short_volume_2026-10-30.txt
- Rebuild note: pull one dated file per session date; the store
  accrues forward.

### Coinalyze funding snapshot (live snapshot only)
- Route (pull log): api.coinalyze.net/v1/future-markets, called with
  curl and the exact-case `api_key` header (the header name is case
  sensitive; a capitalized variant gets HTTP 401)
- Downloaded: one snapshot on 2026-10-30, kept under live/raw/, not a
  history series.

### Dead route, recorded so it is not retried as the breadth spine
- Yahoo chart API monthly pulls (range=max) returned monthly bars,
  not daily; the files were removed as a failed route. The breadth
  spine is the FRED index panel above. Yahoo 10 year daily pulls also
  failed with curl exit 22 at build.

## Gap index (the named gaps in one place)

- AAII: refused, HTTP 404 on both the .xlsx and .csv routes.
- NAAIM: route unresolved, no data file link found on the program page.
- Baker-Wurgler: refused, Stern page 403 and current file names 404;
  G2 therefore runs on Michigan alone in v1.
- Cboe put/call: refused, HTTP 404 on both routes; G5 is SKEW only.
- ICI flows (weekly and monthly): route not resolved in this build.
- COT Legacy depth (1986 forward): not pulled; only TFF 2015 forward
  is in the store, and the TFF 2006 to 2009 junction is unchecked.
- VIX futures curve: settlement file route not resolved in this build.
- Trends FEARS and topics: first pull pending; pytrends not installed;
  pinned harness code present in the collectors.
- Metaculus: refused, HTTP error on the api2 questions route.
- FRED OAS depth: HY and IG series land only from 2023-10-31 through
  the graph route; the Dec 1996 HY archive depth is unreached.
- GDELT deep GKG: only the DOC rolling window (about 3 months) is in
  the store; the GKG file backfill was not pulled.
- Social legs (Reddit, StockTwits): no API keys configured; collecting
  status only.
- Crypto funding venue record: header names OKX, pull log success
  lines name Binance; unresolved, carried as recorded.
