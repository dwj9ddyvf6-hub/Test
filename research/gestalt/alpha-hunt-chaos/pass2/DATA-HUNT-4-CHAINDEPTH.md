# DATA HUNT 4: OPTIONS CHAIN HISTORY DEPTH MEASUREMENT

Ordered Sun 2026-11-15 18:26 ET as one of the four data hunts, Tier A standard. Home: pass2/ of the Alpha Hunt Chaos pass.

SCOPE: Surface is this measurement report and its register only; the hunt is read-only and changed nothing in any store. Constraints: gzip snapshots read directly with python; no terminal module imported (the bilbo iv_snapshot.py file was read as text only, never imported, per the house rule in ~/workspace/AGENTS.md). Outcome: the stored chain depth of the estate, counted exactly, and one bound per Wave 4 candidate (G1, G20, G21) graded against that count. Proof: the counts below were computed from the final files on disk on Sun 2026-11-15, and the machine readable register is pass2/DH4-CENSUS-REGISTER.jsonl (78 rows). Edges: the estate hunt was a filename search plus targeted reads of every location named in the brief; it was not a content grep of every file in the workspace, and the coverage ledger in section 5 states exactly what was searched.

## POTENTIAL EDGE FOUND (candidate, unproven): a Focus panel chain store nobody had counted in the chain depth accounting

The wave4 report's open row 6 and this hunt's brief both treat the morgue store as the known chain store. The census found a second chain store, built Sat 2026-11-14 for a Decisions API panel and never entered in any chain depth accounting:

- Location: ~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave4/dry_capture/store/
- Shape: identical layout and basis to the morgue store (same collector family, same [occ, oi, volume, iv] rows, its own manifest.jsonl and iv_ledger_modelled.jsonl).
- Breadth: 31 underlyings in one capture: the Focus 30 minus SIVE, plus SPY and QQQ as controls. Symbol list: SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, BE, OKLO, VST, CEG, XLE, SPY, QQQ.
- Size: 115,718 contracts across the 31 ok manifest lines; 27,405 modelled IV ledger rows carrying quote_bid, quote_ask and quote_mid; pooled coverage with_iv 23.68 percent, with_oi 39.86 percent, with_volume 44.63 percent.
- Depth: exactly 1 session, dated 2026-11-14, capture_kind panel_close, and honestly labelled inside the file itself: dry_capture true, "chains served are the next session's layout on the prior close. Not a session accrual record." Spot is the 2026-11-13 close (freshness stale), oi_date 2026-11-12.
- Errors: 4 manifest error lines in the same run (WDC and FCEL, 2 each: a chain item count ValueError and an OCC parse ValueError), both symbols then stored ok in the same run.

Why this counts as a potential edge candidate and not as proven edge: it is the only stored cross-section of Focus name chains in the estate, and G21's fit sample was assumed to be index ETFs only. It gives G21 a 31-underlying, 27,405-row quote-carrying fit cross-section today. It is one session deep, so it cannot supply any time series, any next-day score, or any hedge replay. The method-ledger autopsy should grade it as a breadth find produced by a side capture, and the reusable lesson is the one this hunt keeps teaching: side captures from other programs are chain stores too, and the estate count is wrong until they are swept.

Two smaller uncounted items ride with it, both inside the morgue directory but outside the chains store the brief named:

1. iv_history.jsonl (~/workspace/morgue/state/morgue/iv_history.jsonl): 33 rows, 11 sessions times SPY, QQQ and IWM, carrying iv30, iv60, slope_30_60, rr25, strangle15 and butterfly25 per underlying per day. That is G20's three surface state variables (level, term slope, skew shape) already computed and stored, in summary form, for the full 11-session span.
2. The modelled IV ledger's quote fields: snapshot rows carry no bid or ask, but every one of the ledger's 134,857 rows carries quote_bid, quote_ask and quote_mid from Alpaca indicative quotes. See section 2. Any bound written from the snapshot rows alone understates what the store holds.

## 1. The three candidate bounds

### G1. Corrected-Cost Retrain (Vilkov adjudication)

The candidate's own data requirement, quoted from the wave4 report: "Data: needs SPXW intraday quotes at 10:00 ET with bid and ask per leg; the desk's stored chain snapshots cover part of this and the stored-depth measurement (open row) bounds the burn-in window. Where stored depth is insufficient, the forward shadow arm substitutes: price the 7 structures live at 10:00 ET daily from Mon 2026-11-16 and accumulate the sample forward." Its rules also fix the sample: "Train the sign classifier twice on a 252-day burn-in."

What the store CAN support:

- A SPY proxy replay at approximately the right clock time, on indicative quotes: the modelled IV ledger holds one capture per session whose rows all carry bid, ask and mid. Capture times in ET: 2026-10-29 at 22:27 (evening, stale spot session), 2026-10-30 at 06:48 (premarket), then 09:57 or 09:58 on 2026-11-02, 03, 04, 05, 06, 09 and 10 (7 sessions at 3 minutes before the 10:00 entry), a second partial capture on 2026-11-10 at 10:27 (2,132 rows), 2026-11-12 at 13:27, and 2026-11-13 at 09:31. Total ledger rows 134,857 (SPY 57,855, QQQ 54,186, IWM 22,816).
- The 0DTE slice of that proxy: 4,029 ledger rows have expiry equal to date (SPY 1,549, QQQ 1,850, IWM 630), median quoted spread 0.10, minimum 0.009, maximum 8.70. Median spread across all ledger rows is 0.16.
- Intraday chain snapshots at 09:57 ET exist on the 9 fuller sessions (2026-11-02 to 2026-11-13, with 2026-11-12 partial from 13:27 ET), 333 intraday captures in total across the 3 symbols, but their rows carry no quotes (see cannot list).

What the store CANNOT support:

- The instrument itself: stored SPXW contracts, 0. Stored SPX contracts, 0. Every store searched holds equity or ETF underlyings only. SPY options are American style and share settled; SPXW is European and cash settled; a SPY replay is a proxy with a different settlement and exercise basis, and the candidate as written prices SPXW.
- The burn-in: 11 sessions stored against a 252-day burn-in. Shortfall 241 sessions. Even the interim checkpoint form (120 forward-priced sessions) is 10.9 times the stored depth.
- Executable prices in the snapshot rows: 0 of 313,786 pooled daily snapshot contract rows carry a bid or an ask. The quote-carrying subset is the ledger only, and the ledger is restricted to expiries within 120 days inside the 0.75 to 1.25 moneyness band.
- Greeks: 0 rows in any store carry a delta or gamma; the snapshot options_gate block records every contract as greek undated.

Cheapest route that closes the gap: the collector already runs every 30 minutes in market hours and the ledger already captures bid and ask for the IV subset. Two collector-side additions close the field gap at zero purchase cost: add SPX (the TastyTrade nested chain root for SPXW) to the collected symbols, and persist quote bid and ask into the snapshot rows the way the ledger already does. The depth gap closes only by accrual: at the observed rate (11 sessions stored out of 12 trading days in the span, with 2026-11-11 lost entirely, see section 2) a 252-session burn-in is roughly 12 months away, so the registered forward arm at 10:00 ET from Mon 2026-11-16 remains the deciding sample, exactly as the candidate already provides. The stored bound for G1 is therefore: proxy replay possible today on 11 sessions of SPY indicative quotes near 09:57 ET; the candidate's own test, on its own instrument and burn-in, is not runnable from the store at all.

### G20. Surface-State Linear Hedge Test

The candidate's own data requirement, quoted: "Data: book position history and chain snapshots; bounded by stored chain depth (open row), with the forward shadow as the fallback sample." Its rules fix the inputs and the design: "augment the standard delta-gamma hedge rule with three surface state variables (implied vol level, term structure slope, skew curvature, each from the day's chain snapshot)", "Train on the first half of the replay sample, freeze, test on the second half", and a small-data arm that repeats the test "training on 256 historical 30-day windows only".

What the store CAN support:

- The three state variables, precomputed: iv_history.jsonl carries iv30 and iv60 (level), slope_30_60 (term slope), and rr25, strangle15 and butterfly25 (skew and curvature shape) for 11 sessions times 3 underlyings, 33 rows, span 2026-10-29 to 2026-11-13.
- The full surfaces behind them: 11 daily snapshots per symbol (313,786 contract rows pooled, 132,484 with modelled IV) plus 333 intraday captures, so level, slope and curvature are computable per capture, not only per day. An intraday form of the split is arithmetically possible: about 166 captures of train against 167 of test.
- A daily train and test split in form only: 5 sessions of train against 6 of test per underlying.

What the store CANNOT support:

- The small-data arm at all: 256 historical 30-day windows required; complete 30-day windows in the store, 0. The entire history is 11 sessions inside 16 calendar days.
- A credible daily replay: the candidate's falsifier requires the gain to be checked for concentration in COVID-class windows; the sample contains no stress window of any class (11 consecutive calm autumn sessions, 2026-10-29 to 2026-11-13), so that check is unrunable, not merely weak.
- The hedge side of the test from this store: the store carries no book position history and no hedge fills (that input lives in the book's own records, outside this hunt's measurement), and no greeks, so hedge ratios must be recomputed from the modelled IV, which is the same modelled surface the state variables come from.

Cheapest route that closes the gap: accrual on the collector that already runs. Nineteen more sessions reach the first single 30-day window (mid December 2026). Overlapping 30-day windows reach 256 only at 285 stored sessions, roughly 13 months, so the small-data arm is a 2027 object on accrual alone. The zero cost interim form is the intraday one: state variables per 30-minute capture give 333 observations today, and windows of 30 captures (about 2.5 sessions) can be built now, with the window definition relabelled as an adaptation, in the same spirit as G16's minute-bar adaptation in the wave4 report. The forward shadow the candidate names as fallback is already the binding sample. Stored bound for G20: the state variable history exists and is exactly shaped (33 summary rows, 333 full surfaces); the replay depth does not (0 of 256 windows).

### G21. Jump-Aware Pricer, Miniature Replication

The candidate's own data requirement, quoted: "Data: the binding constraint is stored chain history depth (open row); the test runs on whatever depth exists and reports the depth beside the result." Its rules fix the fit and the score: "fit three fair-value models on our Focus 30 and index chains", scored "strictly out of sample on next-day mid error in vol points bucketed by delta, and on delta-hedged P and L after half-spread cost on entry and exit".

What the store CAN support:

- An index fit sample today: 132,484 contract rows with modelled IV in the daily snapshots (SPY 57,155, QQQ 52,846, IWM 22,483), and the same population in ledger form with quote_mid attached (134,857 rows, the small excess over the snapshot count is a second partial capture on 2026-11-10).
- A Focus fit cross-section today: the dry capture store of the lead section, 115,718 contracts and 27,405 quote-carrying IV rows across 31 underlyings for 1 session (2026-11-14). Without that store the Focus 30 fit sample in the estate would be zero rows; with it, the fit is cross-sectional only.
- A genuine next-day out-of-sample score for the index ETFs: consecutive daily snapshots share 103,675 contracts carrying IV on both days (SPY 45,322, QQQ 40,402, IWM 17,951, summed over the 10 consecutive day pairs per symbol). Next-day mid error in vol points is computable on those pairs today, because the ledger supplies the mid the IV was inverted from.
- A second, independent IV history for single names: the bilbo ledger (section 4), 1,198 rows of measured Alpaca snapshot IV for 20 names over 12 nights, calls only, 21 to 37 DTE, 5 strikes around a target. Too narrow for a surface fit, but it is a real same-tenor IV time series the index stores do not have.

What the store CANNOT support:

- Option prices as a stored field in the snapshots: snapshot rows carry [occ, oi, volume, iv] and no price at all. Prices across days exist only as the ledger's quote_mid, restricted to the 0.75 to 1.25 moneyness band and expiries within 120 days, and the IV is a Black-Scholes inversion of that same mid (r 0.045 flat), so fitting a fair-value model to the IV and scoring it against the mid is partly circular. The candidate's delta-hedged P and L arm has no stored greeks to hedge with; deltas must be derived from the modelled IV itself.
- A Focus 30 time series: Focus names have exactly 1 stored session (the dry capture). Next-day pairs for Focus names: 0.
- Jump identification: the whole index sample is 11 sessions and 10 next-day pairs per underlying. A jump component fitted and validated inside 10 out-of-sample days per underlying is a miniature in the strict sense; the paper's reference margins (NJSDE MAE 2.4688 against NSDE 2.6794 against SVCJ 4.2944 on SPX) come from a sample orders of magnitude deeper, and SPX itself is absent here (0 contracts).

Cheapest route that closes the gap: accrual, plus one collector field. If the Focus panel capture that produced the dry store is rerun as a per-session accrual instead of a one-off, each session adds about 27,405 Focus quote rows and about 12,000 index IV rows; a 60-session fit sample (the desk's own Bilbo pre-registration standard) arrives in about 49 more sessions, around late January 2027, at zero purchase cost. Persisting bid and ask into the snapshot rows (the ledger already captures them for the subset) removes the moneyness band restriction on the price sample. Stored bound for G21: the miniature is runnable today on index ETFs (132,484 IV rows, 103,675 next-day pairs) and cross-sectionally on 31 Focus underlyings for 1 session; it is not runnable as a Focus time series, and its price basis is indicative midpoints inverted through the desk's own Black-Scholes assumptions, which must be printed beside any result.

## 2. Census: the morgue chain store, exactly

Store: ~/workspace/morgue/state/morgue/chains/ (README read first; collector terminal-lineup/site/collect_chains.py, TastyTrade nested chains, every 30 minutes in market hours).

### Daily snapshots

All three symbols hold the same 11 dates: 2026-10-29, 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-09, 2026-11-10, 2026-11-12, 2026-11-13. Span 2026-10-29 to 2026-11-13, 11 sessions. The span holds 12 trading days: 2026-11-11 is absent entirely (no snapshot, no intraday capture, and no manifest line of any status with an ET date of 2026-11-11; the manifest ET-date counts are 2026-10-29: 6, 10-30: 45, 11-02: 36, 11-03: 39, 11-04: 42, 11-05: 42, 11-06: 42, 11-09: 42, 11-10: 41, 11-12: 18, 11-13: 45, 11-11: 0). The neighbouring pername tape store does hold 2026-11-11, so the session traded and was collected elsewhere; the chain collector simply has no record of it.

### Intraday captures

Counts below group captures by ET day (converted from the UTC filename stamp), which is the session they belong to; grouping by the filename's UTC date shifts the evening captures of 2026-10-29 and 2026-10-30 by one day and is not used.

- SPY: 111 captures. Per ET day: 2026-10-29: 2, 10-30: 2, 11-02: 11, 11-03: 12, 11-04: 13, 11-05: 13, 11-06: 13, 11-09: 13, 11-10: 13, 11-12: 5, 11-13: 14.
- QQQ: 113 captures. Per ET day: 2026-10-29: 2, 10-30: 4, 11-02: 11, 11-03: 12, 11-04: 13, 11-05: 13, 11-06: 13, 11-09: 12, 11-10: 13, 11-12: 6, 11-13: 14.
- IWM: 109 captures. Per ET day: 2026-10-29: 2, 10-30: 2, 11-02: 11, 11-03: 12, 11-04: 13, 11-05: 12, 11-06: 13, 11-09: 12, 11-10: 12, 11-12: 6, 11-13: 14.
- Total 333 captures, matching the manifest's 333 ok lines exactly. Earliest capture stamp 2026-10-29T223941Z and latest 2026-11-13T205732Z for all three symbols. On full sessions the capture grid runs 09:57 to 15:57 ET at 30-minute spacing (13 captures); 2026-11-12 is a partial day starting 13:27 ET.

### Manifest

398 lines total: 333 status ok, 65 status error. By symbol: SPY 133 lines (111 ok, 22 error), QQQ 133 (113 ok, 20 error), IWM 132 (109 ok, 23 error). Error census: every one of the 65 error lines is the same failure, a stale spot quote refusal, in the form "RuntimeError: spot quote for SYM is stale (quote_ts=...); refusing to store a snapshot on a stale live quote". Because each line embeds its own symbol and quote timestamp, the 65 lines are 65 distinct verbatim texts occurring once each; normalised to the failure template they are 1 distinct error counted 65 times. No other error text appears in the manifest. The stale failures cluster at the open and the close of 2026-10-30 and at the 21:00 UTC close print on later days, which is the freshness gate doing what the README says it does.

### Snapshot size and coverage

Contracts per daily snapshot (row counts read from the files; identical to the manifest's per-run figures): SPY min 12,030, median 12,890, max 13,000. QQQ min 9,832, median 10,456, max 11,578. IWM min 4,962, median 5,124, max 5,268.

Expirations per snapshot (parsed from the OCC codes in the rows; identical to the manifest figures): SPY min 33, median 34, max 35. QQQ min 30, median 32, max 33. IWM min 31, median 33, max 34.

Strikes per snapshot, two honest counts. The manifest's strikes field counts strike entries across expirations (contracts divided by 2, calls and puts): SPY min 6,015, median 6,452, max 6,500; QQQ min 4,916, median 5,526, max 5,789; IWM min 2,481, median 2,559, max 2,634. Distinct strike prices across the whole chain (parsed from OCC codes): SPY min 491, median 491, max 556; QQQ 524 on every snapshot; IWM min 184, median 185, max 192.

Field coverage, from the snapshots' own field_coverage blocks:

- SPY: pooled with_iv 57,155 of 139,752 (40.90 percent), with_oi 58,240 (41.67 percent), with_volume 68,379 (48.93 percent). Latest session (2026-11-13): with_iv 5,206 of 12,738 (40.87 percent), with_oi 5,495 (43.14 percent), with_volume 6,158 (48.34 percent).
- QQQ: pooled with_iv 52,846 of 117,766 (44.87 percent), with_oi 54,273 (46.09 percent), with_volume 68,338 (58.03 percent). Latest: with_iv 5,013 of 11,052 (45.36 percent), with_oi 5,614 (50.80 percent), with_volume 6,536 (59.14 percent).
- IWM: pooled with_iv 22,483 of 56,268 (39.96 percent), with_oi 22,567 (40.11 percent), with_volume 26,435 (46.98 percent). Latest: with_iv 1,810 of 5,024 (36.03 percent), with_oi 2,105 (41.90 percent), with_volume 2,297 (45.72 percent).
- All symbols pooled: 313,786 contract rows; with_iv 132,484 (42.22 percent), with_oi 135,080 (43.05 percent), with_volume 163,152 (51.99 percent). The uncovered remainder is by design per the README: enrichment covers expiries within 120 days, IV only inside the 0.75 to 1.25 moneyness band, and absent fields are stored as null, never as fabricated zeros. No snapshot's content block carries an error.

Spot: present in all 33 daily snapshots (11 per symbol). Source in every case: yahoo chart regularMarketPrice (price only). Freshness: stale on 2026-10-29 for all three symbols (that day's canonical file is the 22:27 ET evening capture), fresh on the other 10 days. The underlying chain layout source in every snapshot is tastytrade GET /option-chains/SYM/nested; OI is Alpaca contracts open interest dated by oi_date (2 sessions behind the snapshot day throughout); volume is Alpaca indicative snapshot dailyBar.

## 3. Census: iv_ledger_modelled.jsonl

File: ~/workspace/morgue/state/morgue/chains/iv_ledger_modelled.jsonl, 63 MB, 134,857 rows.

- Rows by symbol: SPY 57,855, QQQ 54,186, IWM 22,816.
- Dates: the same 11 sessions as the snapshots. Rows per date: 2026-10-29: 10,143; 10-30: 10,033; 11-02: 11,173; 11-03: 12,686; 11-04: 12,485; 11-05: 12,690; 11-06: 13,418; 11-09: 13,439; 11-10: 13,329 (two captures, 11,197 at 09:57 ET and 2,132 at 10:27 ET); 11-12: 13,099; 11-13: 12,362. Twelve distinct captured_at_utc values in total, listed in the G1 bound above.
- Fields per row, identical on all 134,857 rows (one field set, no variants): captured_at_utc, date, expiry, iv, iv_basis, model, occ, quote_ask, quote_bid, quote_mid, side, spot, strike, underlying. quote_bid and quote_ask are present on 100 percent of rows; iv is null on 0 rows; iv_basis is MODELLED on every row.
- Sample row, printed in full (no credential-like content present, nothing redacted): {"captured_at_utc": "2026-10-30T02:27:34Z", "date": "2026-10-29", "expiry": "2026-10-29", "iv": 0.0677, "iv_basis": "MODELLED", "model": "MODELLED Black-Scholes inversion of the Alpaca indicative quote midpoint; r=0.045 flat; dividend yield SPY 0.013, QQQ 0.005, IWM 0.014, else 0.0; expiry 21:00 UTC; European, no early exercise", "occ": "SPY261029C00770000", "quote_ask": 0.04, "quote_bid": 0.03, "quote_mid": 0.035, "side": "call", "spot": 769.36, "strike": 770.0, "underlying": "SPY"}

## 4. The rest of the estate: every other store found, and every empty location

Found, in descending depth:

1. Bilbo IV snapshots: ~/workspace/alpaca-swing-desk/desk/research/bilbo-options/iv_snapshots.jsonl (the brief's femto-lean desk/research/bilbo-options path resolves to this desk tree; the femto-lean repo itself holds no bilbo-options directory). 1,198 rows, 20 underlyings (AAPL, AMD, AMZN, AVGO, BAC, COIN, DIS, GOOGL, HOOD, INTC, JPM, META, MSFT, MU, NFLX, NVDA, PLTR, SMCI, TSLA, UBER; 60 rows each except INTC at 58), 12 nightly dates 2026-10-02 to 2026-10-14 (including the weekend dates 2026-10-03, 04 and 10; the ledger appends by calendar night, not by session), no duplicate (date, symbol, strike) keys in the file as it stands. Fields: date, symbol, expiry_dte, strike, iv, underlying (the spot), target_strike, atr14. Price basis: none (no prices at all). IV basis: measured, not modelled: the module (read as text) takes impliedVolatility from Alpaca v1beta1 options snapshots on the indicative feed, for calls only, 21 to 37 DTE, the target strike (spot plus 0.75 times ATR14) and its 2 nearest strikes each side. No bid, ask, OI or volume. This is the longest single-name IV time series in the estate and the only measured (not modelled) IV store.
2. Decisions dry capture Focus panel: section 1 lead. 31 underlyings, 1 session (2026-11-14), 115,718 contracts, modelled IV basis identical to the morgue, ledger rows with bid, ask and mid.
3. Morgue iv_history.jsonl: section 1 lead, item 1. 33 rows, surface summaries only, no contracts.
4. Morgue pername tape: ~/workspace/morgue/state/morgue/pername_tape/, 12 daily files, 2026-10-29 to 2026-11-13 including 2026-11-11, universe of 103 names (insider-wire watchlist plus SPY, QQQ, IWM). Not a chain store: per name it stores options trade print aggregates (prints, multileg prints, total premium, heat) plus a top-alerts list carrying OCC symbol, executed price, size and timestamp. Source: Alpaca v1beta1 options trades. It holds executed print prices, no quotes, no IV, no chain layout, and direction is explicitly unjudged in the file because no print-time quote source exists on hand. Sessions counted here because it is stored options history, but it contributes 0 chain depth to every bound above.
5. Muse desk v3 scalar IV ledger: ~/workspace/muse-desk-v3/state/iv_ledger.json, 816 bytes. 13 symbols (AEHR, ARM, ARQQ, AXTI, CORZ, DGXX, HIVE, IREN, NBIS, POET, SNDK, VELO, WYFI), 1 session (2026-11-13), one scalar iv per name. No strike, expiry or price. Not a chain; a one-day reading.

Searched, nothing (or nothing independent) found:

- Terminal-lineup state and outputs (~/workspace/terminal-lineup/site/ tool data files, forecast/, deep_store/): no independent chain store. The chain-explorer data.json republishes the morgue store and says so in its own coverage line: 33 snapshot days on record across SPY, QQQ and IWM, most recent 2026-11-13. The remaining tool outputs (iv-weather, expected-move and siblings) are current-session derivatives of the same store. deep_store holds underlying bar panels, not options.
- Muse desk v3 state (~/workspace/muse-desk-v3/state/): the iv_ledger.json of item 5 above, and state/bilbo_options/journal.jsonl, which is a sleeve cycle journal (4,219 event rows from 2026-10-24: cycle_id, event, missing, stale, ts) carrying no chain, quote or IV rows. Nothing else chain-shaped in the state tree.
- Midna book (~/workspace/midna-book/): searched in full at the top two levels and in memory/, reviews/ and tools/. The ledger.json is book accounting (pods, fills, equity history). No stored options chain history found.
- Femto-lean desk tree (~/workspace/femto-lean/): no bilbo-options directory exists there, and state/live/ holds sleeve state only. Its *.chain.jsonl files (state/live/sleeves/aurelia_ndx.json.chain.jsonl and siblings) are sleeve state chains (base_hash, base_state, consumed signal keys), not option chains. No stored options chain history found.
- Backup and staging copies (the light-save staging parts of iv_ledger_modelled.jsonl, the .jarvis workflow-run test fixtures with toy chains directories, the wave6 desk-copy of v3 state): duplicates or test fixtures of the stores above, excluded from the census by definition; they add no sessions and no underlyings.

SPX and SPXW, explicit line: searched in every store above (morgue chains directory listing, dry capture symbol list, bilbo symbol list, v3 iv ledger keys, pername tape universe, terminal-lineup outputs) and in an estate-wide filename search for IV ledger and chain files. Found: absent everywhere. Stored SPX contracts: 0. Stored SPXW contracts: 0. The nearest index exposure in any store is SPY, QQQ and IWM options, plus XSP and SPX underlying bar and sleeve state files in the v3 tree, which are not option chains.

## 5. Coverage ledger for this hunt

- Searched and counted in full: morgue chains (33 daily gzip files read, 333 intraday files counted and spot-checked, manifest 398 lines, iv ledger 134,857 rows), morgue iv_history (33 rows), morgue pername tape (12 files, manifest 17 lines), dry capture store (31 daily gzip files via its manifest, ledger 27,405 rows), bilbo iv_snapshots (1,198 rows), v3 iv_ledger.json (13 entries).
- Searched and classified: terminal-lineup site outputs, v3 state tree, midna-book, femto-lean state, decisions-api-leverage research tree (which produced the dry capture find).
- Excluded by definition: backup seals, light-save staging parts, .jarvis test fixtures, published-tree copies under terminal-lineup/site/.published-trees (copies of code, not data).
- Unavailable: nothing in scope was unreadable. One limit stands: the estate hunt was filename and targeted-directory based, so a chain store hidden under an unrelated filename in an unsearched tree would not have been caught; every location the brief named was read directly.

## 6. Verdict

The measurement is complete for every location named in the brief plus the estate sweep, and every number above was computed from the files themselves on 2026-11-15. The headline bound, one line per candidate:

- G1: 11 sessions of SPY indicative quotes near 09:57 ET exist in ledger form (4,029 0DTE rows); SPXW depth is 0 and the 252-day burn-in is short by 241 sessions, so the candidate runs on its forward arm, not on the store.
- G20: the surface state history exists in exactly the candidate's shape (33 summary rows, 333 full surfaces over 11 sessions); the replay depth does not (0 of 256 thirty-day windows).
- G21: the miniature is runnable today on index ETFs (132,484 IV rows, 103,675 next-day IV pairs) and cross-sectionally on 31 Focus underlyings for 1 session; Focus time series depth is 1 session and the price basis is indicative mids inverted through the desk's own model.

STATUS: GREEN. Evidence pointer: this file plus pass2/DH4-CENSUS-REGISTER.jsonl (78 rows: one per store per symbol, plus one per searched-empty location), both in ~/workspace/research_notes/alpha-hunt-chaos-20261115/pass2/. No candidate is killed by this measurement; the output is bounds, as ordered.
