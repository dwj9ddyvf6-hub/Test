# W7C. VINTAGE JOBS AND PRINT COMPANION (Wave 7, Lane C, 2026-11-15)

SCOPE: Surface: keepgoing2/wave7/ (new): the CB-20 vintage archive store and its daily capture script, the CB-34 Kalshi event-market snapshot job, the first backward-signal read, the focus29 venue validation, and the W6A-PRINT-COMPANION first run for Friday 2026-11-13. Constraints: public sources only, no accounts, no credentials; no wave4, wave5, or wave6 file modified; the companion is filed BESIDE the accrual ledgers in wave7, never inside them; no dead-drop write. Outcome: both vintage stores captured and proven by read-back, both daily crons armed and read back, the backward read computed at its true n with its gaps named, the print route validated across the whole basket, and the companion leg written for every validated name. Proof: the manifest hash verification (256 files, 0 mismatches), the snapshot and discovery read-backs, the validation JSON, the companion JSON, and the cron read-backs below. Edges: the CB-20 and CB-34 falsifiers are forward objects (two quarters of vintages; 20 print-eve nights) and accrue from tonight; nothing in this record grades them.

SCOPE RESTORATION NOTE (owner x10 order, 2026-11-15 01:15 ET): the first vintage capture earlier tonight took only the latest ATS week, and the first event snapshot covered 8 hand-picked series. Both were restored to full scope in this same run, before this record was written: the ATS archive now holds every weekly file the route currently publishes (255 weeks), and the event snapshot now runs an exhaustive series discovery (16,448 series scanned) with capture across every included series. The print companion was full basket from the start and was not narrowed. The superseded first snapshot file was overwritten by the exhaustive run of the same capture date, as the store schema provides for same-date refresh; the discovery file records both counts.

## W7-3a. CB-20 LAG DETECTOR ARCHIVE

Store: keepgoing2/wave7/vintage/, schema in vintage/SCHEMA.md: one directory per capture date, never overwrite an earlier date. Writer: keepgoing2/wave7/w7c_vintage_capture.py (daily mode: latest published week plus the SI snapshot; --full mode: every published week).

First capture, 2026-11-15 (directory vintage/2026-11-15/, manifest.json):

- FINRA ATS, full archive: 255 weekly files, as-of weeks 2021-12-06 through 2026-10-19, 3,533,299 rows total, saved as published through the estate route (POST api.finra.org/data/group/otcMarket/name/weeklySummary, summaryTypeCode ATS_W_SMBL, whole-week pulls paginated at 5000, the route of keepgoing2/wave4/v6_ats_series_build.py). The latest week (2026-10-19, initialPublishedDate 2026-11-09, 2,711 rows) is stored plain; the other 254 weeks are stored gzipped. Route range discovery: 2021-11-29 and earlier Mondays return 0 rows; 2021-12-06 is the first published week. The walk stopped after 8 consecutive empty weeks. One route lesson, recorded: adding a sixth field (totalWeeklyTransactionQuantity) to the estate route's field set returns HTTP 400; the capture uses the estate route's exact five fields.
- Short interest: held-corpus snapshot short_interest_pit_snapshot.jsonl, 822 rows, a byte copy of ~/workspace/morgue/output/short_interest_pit.jsonl (the Wave 3 PIT file, Nasdaq short-interest table, FINRA SI republished). GAP, named: no live public short-interest route exists on this estate. The FINRA API equity shortInterest dataset answers 401 without FINRA API credentials (probed 2026-11-15), and the otcMarket shortInterest path answers 404. The SI vintage series therefore accrues as dated snapshots of the held file, so any future change to that file becomes a visible vintage difference; the gap stays open until a credentialed or public live SI route lands.
- Proof: manifest read-back with every hash recomputed: 256 files listed (255 ATS weeks plus the SI snapshot), 0 mismatches, byte sizes match, store 30,286,485 bytes on disk. The manifest records capture timestamps, per-file source route, as-of week, published dates, row counts, and sha256.

Cron: w7-vintage-capture-daily, daily 20:46 America/New_York, enabled, read back after arming: next run Sun 2026-11-15 20:46:00 EST. Its body runs the script in daily mode and reports the manifest line. (Arming note: the cron write path timed out on sync three times tonight; each write was verified by read-back rather than assumed, and the final state above is the read-back state.)

### First backward-signal read (CB-20, partial, true n stated)

Script keepgoing2/wave7/w7c_backward_read.py, output keepgoing2/wave7/w7c_backward_read.json, bars in w7c_backward_bars.json. Held corpora: v6_ats_series.json (8 symbols: ABT, CRML, MNDY, TLN, TMDX, TSLA, WMT, XNCR; Wave 4 proved its stamps match 8 of 8) plus tonight's archive.

Three findings, each at its true n:

1. Literal revisions in the held series: zero. No (symbol, week) in v6_ats_series.json carries two different quantities, and the two-vintage check below confirms it independently.
2. Vintage-versus-final z reconstruction: degenerate, and the degeneracy is the finding. Per symbol-week event (168 events with at least 8 prior usable weeks; 152 with full forward bars), the point-in-time z (prior window gated on initial_published at or before the event's own publication date) and the final-view z (all prior weeks in the held series) are identical in every event: max absolute delta z 0.0, sign disagreements 0 of 152, disagreement rate 0.0. Reason: in the held final pull, publication is strictly chronological, so no prior week was ever published after a later week's own publication; the final view contains no late-published prior week for the vintage view to miss. The agreement group's forward 10-session numbers are recorded for completeness (mean vol 331.82bp, mean drift +132.73bp, n 152); with an empty disagreement group, no disagreement-versus-agreement comparison exists tonight. This is a partial first read with n 152 events and an empty treatment group, labeled as such; it does not test the CB-20 falsifier, which needs two quarters of true vintages from the archive that starts tonight.
3. True two-vintage check (one-day revision window): the 8 symbols' 232 symbol-weeks in the Wave 4 pull of 2026-11-14 were compared against tonight's archived week files from the independent 2026-11-15 pull: 232 compared, 0 quantity differences, 0 missing. FINRA revised none of these weeks between the two pulls. The revision signal, if it exists, operates on a longer window than one day; the daily archive is the instrument that will measure it.

## W7-3b. CB-34 PREDICTION-MARKET SNAPSHOTS

Script keepgoing2/wave7/w7c_event_snapshot.py, store keepgoing2/wave7/eventmarkets/ with SCHEMA.json and a discovery file per capture date. Source: Kalshi public API (api.elections.kalshi.com/trade-api/v2), public endpoints, no account, no credentials. Prices as served are the dollars fields (yes_bid_dollars, yes_ask_dollars, last_price_dollars) with volume_fp and open_interest_fp; the legacy cent fields are null on this API view and are not used. Implied probability is the mid of yes bid and ask when both are served, else the last price.

Exhaustive discovery (discovery_2026-11-15.json): full public series list scanned, 16,448 series. Keyword families (fed/fomc/federal reserve; cpi/inflation/pce; recession; rate cut/rate hike; unemployment/jobless/payroll/nonfarm; gdp): 332 hits, each recorded with families, inclusion flag, and exclusion reasons. Inclusion rule (mechanical, recorded in the discovery file): category Economics, no foreign token in the title, not a mention market: 163 series included. Capture rule: nearest open event by earliest market close_time with all its markets; recession-family series capture all open events; series with no open events are recorded with open_events_found 0.

First capture (2026-11-15.json, captured 2026-11-15T01:20:42 ET, read back and verified): 163 series included, 68 with open events, 639 markets captured, every captured market priced (implied probability present). The eight core series from the brief, all present: KXFEDDECISION (nearest event KXFEDDECISION-26DEC, 5 markets), KXFED (KXFED-26DEC, 11), KXRATECUT (KXRATECUT-26DEC31, 1), KXCPI (KXCPI-26NOV, 9), KXCPICORE (KXCPICORE-26NOV, 11), KXRECSSNBER (both open events: KXRECSSNBER-26 implied 0.025, KXRECSSNBER-27 implied 0.225, 1 market each), KXNBERRECESSQ (6 markets), KXGDP (KXGDP-27JAN28, 9). Absences recorded, not substituted: KXRECESSION, RECESSION, KXUSRECESSION, KXRECESSIONY, KXFOMC, and KXINFLATION returned 404 on the public series endpoint; the recession series that exist (KXRECSSNBER, RECSSNBER, KXNBERRECESSQ, KXQRECESS, plus the world and Canada recession series in the discovery file, the latter two excluded from capture by the foreign-scope rule and recorded) were found by the scan. RECSSNBER and KXQRECESS are included series with zero open events tonight, recorded as such.

Cron: w7-eventmarkets-snapshot-daily, daily 20:51 America/New_York, enabled, read back after arming: next run Sun 2026-11-15 20:51:00 EST. (Arming note: the job first landed at 20:46 because a flexible-time add snapped to the estate's :46 convention; it was corrected by an exact-time update and the 20:51 state above is the final read-back.)

First read: none possible beyond the snapshot itself. The CB-34 falsifier needs 20 print-eve nights of snapshots; tonight is n 1 snapshot. Stated plainly: n = 1.

## W7-8. PRINT COMPANION

Script keepgoing2/wave7/w7c_print_companion.py; validation output keepgoing2/wave7/w7c_venue_validation.json; companion output keepgoing2/wave7/print_companion_2026-11-13.json, filed in wave7 beside the ledgers' program home, never inside the accruals (the W6A D2 terms).

### Step 1, venue validation: 29 of 29 validated

Venues as served by the Alpaca assets endpoint, grouped: NASDAQ 23 names (SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, AMAT, MU, SNDK, WDC, AAOI, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, CEG), NYSE 5 (TSM, COHR, BE, OKLO, VST), ARCA 1 (XLE). SIP primary exchange codes Q, N, P respectively.

The Wave 5 condition-code route generalizes unchanged: opening cross is the first primary-exchange trade carrying condition O in 14:30:00Z..14:30:03Z (fallback ..14:30:12Z); closing cross is the first primary-exchange trade carrying condition 6 in 20:59:59Z..21:00:06Z (the close window is 2 seconds wider than Wave 5's because NYSE closing crosses print up to about 21:00:03Z, probed on TSM and BE before the run). Probe evidence before the run (TSM, BE, XLE on 2026-11-13): on every venue the O print sits at cross size and is followed by a same-price same-size Q-condition republication, and the 6 print likewise by an M-condition republication, the same signature Wave 5 found on Nasdaq.

Validation table (both sessions, 2026-11-13 primary and 2026-11-12 supporting; check: both crosses identified AND bar close exactly equal to the closing cross print):

| Venue | Names | Validated | Bar close exact | Bar open exact (recorded, not a gate) |
|---|---|---|---|---|
| NASDAQ | 23 | 23 of 23 | 23 of 23 both sessions | 2026-11-13 and 2026-11-12 detail in the JSON |
| NYSE | 5 | 5 of 5 | 5 of 5 both sessions | detail in the JSON |
| ARCA | 1 | 1 of 1 | 1 of 1 both sessions | detail in the JSON |
| Total | 29 | 29 of 29 | 58 of 58 name-sessions | 6 of 29 on 2026-11-13, 3 of 29 on 2026-11-12 |

No name failed validation; the not_validated set is empty. The bar-close result extends Wave 5's 60 of 60 on the CARRY six to 58 of 58 across the whole basket and all three venues. The bar-open result extends Wave 5's warning the other way: across 29 names the bar open equals the opening cross in only 9 of 58 name-sessions, so the bar-based gross leg and the print-based gross leg are different measurements basket-wide, not only on CRWV.

### Step 2, companion capture: Friday 2026-11-13 leg, 29 of 29 names

Construction, stated: closing cross print of 2026-11-12 to opening cross print of 2026-11-13, per name. This companions the exact leg the accruals recorded from bars for 2026-11-13 (previous close to this open, per keepgoing2/wave5/w5a_handcheck.json). An open-to-next-open construction was not used: it spans a full extra session and is not the recorded leg.

Result (n = 1 session): equal-weight print leg -71.775bp; the bar leg over the same 29 names -61.921bp (the accrual's own recorded basket gross for the session, reproduced by the Wave 5 hand-check); gap (print minus bar) mean -9.853bp, median -0.354bp. The mean is pulled by a handful of names whose bar open sat far from their opening cross: OKLO -57.260bp (print leg -4.090 vs bar +53.170), EOSE -55.249 (+441.989 vs +497.238), CRDO -50.783 (-112.295 vs -61.512), FLNC -42.239 (-31.679 vs +10.560), VST -24.905 (-8.178 vs +16.727). The median name's gap is a third of a bp: for most of the basket the two legs nearly agree on this session, and the basket-level difference is a tail effect in the wide names, the same shape as Wave 5's CRWV finding (+28.765bp systematic on the open side there). Names excluded: none; all 29 validated names are in the companion, and the exclusion set is recorded empty rather than omitted.

Reading, kept to what one session supports: on 2026-11-13 the auction-print form of the recorded leg was 9.853bp worse than the bar form at equal weight, entirely from the opening-cross side (every closing print equals its bar close by the validation check). This is a measurement of the print definition on one session, filed beside the ledgers per the D2 decision; it changes nothing in the accruals, and its forward weight accrues only as the companion is run over the recorded forward sessions before the falsifier's session-60 close.

## FILES

- keepgoing2/wave7/W7C-VINTAGE-PRINTS.md (this record)
- keepgoing2/wave7/w7c_vintage_capture.py; keepgoing2/wave7/vintage/SCHEMA.md; keepgoing2/wave7/vintage/2026-11-15/ (255 ATS week files, SI snapshot, manifest.json); keepgoing2/wave7/vintage_full_run.log
- keepgoing2/wave7/w7c_backward_read.py; keepgoing2/wave7/w7c_backward_read.json; keepgoing2/wave7/w7c_backward_bars.json
- keepgoing2/wave7/w7c_event_snapshot.py; keepgoing2/wave7/eventmarkets/SCHEMA.json; keepgoing2/wave7/eventmarkets/2026-11-15.json; keepgoing2/wave7/eventmarkets/discovery_2026-11-15.json; keepgoing2/wave7/event_snapshot_run.log
- keepgoing2/wave7/w7c_print_companion.py; keepgoing2/wave7/w7c_venue_validation.json; keepgoing2/wave7/print_companion_2026-11-13.json; keepgoing2/wave7/print_companion_run.log
- Crons: w7-vintage-capture-daily (daily 20:46 ET, next run Sun 2026-11-15 20:46 EST); w7-eventmarkets-snapshot-daily (daily 20:51 ET, next run Sun 2026-11-15 20:51 EST). Both read back enabled after arming.

## OPEN ROWS

- SI-LIVE-ROUTE: no public no-credential live short-interest route exists on this estate (FINRA equity shortInterest is 401 without FINRA API credentials). The archive accrues held-file snapshots until a route lands.
- CB-20 falsifier accrual: two quarters of true vintages from the daily archive, started 2026-11-15. The one-day two-vintage check found 0 revisions in 232 symbol-weeks; the disagreement group is empty at every horizon measured tonight.
- CB-34 falsifier accrual: 20 print-eve nights of snapshots, started 2026-11-15, n 1.
- PRINT-COMPANION accrual: the companion is a one-session first run (n 1). Running it over each recorded forward session, before the falsifier's session-60 close, remains the W6A-PRINT-COMPANION row's forward half.

STATUS: GREEN for the three landings as scoped (archive, snapshot job, companion first run), each proven on its final artifact tonight by read-back: manifest hash verification 256 of 256, snapshot and discovery read-backs (639 markets, 68 series with open events), validation 29 of 29, companion 29 of 29 names, both crons read back armed. The forward falsifier accruals above are named open by design. EVIDENCE POINTER: keepgoing2/wave7/vintage/2026-11-15/manifest.json, keepgoing2/wave7/eventmarkets/2026-11-15.json, keepgoing2/wave7/eventmarkets/discovery_2026-11-15.json, keepgoing2/wave7/w7c_backward_read.json, keepgoing2/wave7/w7c_venue_validation.json, keepgoing2/wave7/print_companion_2026-11-13.json.
