# DATA CENSUS for the ALPHA HUNT X10 Program

Date: Sat 2026-11-14 (America/New_York)
Scope: read-only inventory of data stores on this box held by the trading estate. No desk tree or live state was edited. Counts and date ranges below were proven by reading the files (wc, head, jq style parsing in python, grep counts), never guessed. Where a full parse was too expensive, the counting method is named.
For each store: absolute path, format, row or file count, date range, whether any program is known to have mined it (from file names and READMEs nearby), and the cheapest honest probe.

Headline surprises up front: the forecast ledger is 431,124 rows and 834 MB and is by far the largest single tradeable history on the box. The per sleeve journals total 1,330,125 lines across 338 files and dwarf the curated fill ledger. The REA master index is 114,823 rows. The desk options chain cache covers only 65 symbols with one current chain.json each, while the morgue chain archive is only 6 symbols by 12 sessions for SPY.

## 1. Fill ledger (desk)

- Path: /home/hatch/workspace/muse-desk-v3/state/fill_ledger/
- Format: JSONL segments plus manifest.json (format fill-ledger/1)
- Count: 8,928 fills total. fills-000001.jsonl 5,000 rows, fills-000002.jsonl 3,928 rows. Manifest total_fills 8,928 agrees, duplicates_dropped 0, with sha256 per segment.
- Date range: 2026-10-27T13:30:00.290346Z to 2026-11-13T19:14:02.359304Z (ts field)
- Distinct: 65 sleeves (union of both segments), 99 symbols (union). Segment 1 alone: 61 sleeves, 65 symbols. Segment 2 alone: 48 sleeves, 79 symbols.
- Top sleeves (segment counts): tensor_swing 1,912 plus 1,866, aster_native_btc_eth_sma200 548 in segment 1, aster_tensor_d20_tensor 459 plus 225, aster_tensor_d20_pv 262 plus 158, momentum 412 in segment 2.
- Top symbols: BTC/USD 788 in segment 1, SPY261211P00735000 257 plus 256, ANF 273, OUST 213, AXTI 173 in segment 2, SOXL 170 in segment 2.
- Fields per row: broker_order_id, client_order_id, event, imported, intent_id, position_intent, price, qty, side, sleeve, symbol, ts.
- Built from: dispatcher.jsonl.4, .3, .2, .1 and dispatcher.jsonl (per manifest built_from).
- Mined? Yes, at least once. /home/hatch/workspace/research_notes/decisions-api-leverage-20261114/runs/execution_alpha_v1.json records fills 8,928, entry_markout_n 5,024, exit_markout_n 1,413, inwindow_trips 18, unmatched_close_fills_prewindow 1,509, sleeves 54. No evidence of a full sleeve by symbol by horizon mining pass beyond that execution alpha run.
- Cheapest honest probe: join fills to forward SIP bars at 1, 5 and 20 sessions by sleeve and symbol, report median forward return net of the recorded fill price, split entry versus exit fills. One pass over 8,928 rows, no new data needed.

## 2. Desk state stores

### 2a. Gate distance

- Path: /home/hatch/workspace/muse-desk-v3/state/gate_distance.jsonl
- Format: JSONL, fields asof, sleeve, symbol, gate, measured, threshold, distance, unit, passed, probe, note
- Count: 101 records only. This is a single day snapshot, not a history.
- Date range: asof 2026-11-14T21:10:30Z to 2026-11-14T22:13:51Z
- Distinct: 20 sleeves, 7 symbols (QQQ 40, ADAUSDT 20, ADA/USD 20, LINK/USD 6, LINKUSDT 5, ETH/USD 5, BTC/USD 5), 6 gates: rsi2_below_10_and_close_over_sma200 40, funding_max 20, vol_shock_mult 16, close_over_20bar_high 10, close_over_sma200 10, funding_min 5. Passed 20, failed 81.
- Companion file: /home/hatch/workspace/research_notes/sleeve-activation-calibration-20261111/improvement/gate_distance_2026-11-14.jsonl plus a summary json in the same folder (found by search, not separately counted here).
- Mined? Partially, by construction on 2026-11-14 (the calibration improvement lane). No multi day gate distance history exists in the main file to mine.
- Cheapest honest probe: for the 81 failed rows, measure distance as a fraction of threshold and rank near misses within 10 percent of passing. Those are the calibration candidates. Do not loosen anything from 101 rows alone.

### 2b. Dispatcher log (the reject and intent store)

- Path: /home/hatch/workspace/muse-desk-v3/state/dispatcher.jsonl plus rotations .1 to .4
- Format: JSONL event log
- Count: 65,607 rows total. Current 10,777, .1 23,715, .2 7,408, .3 21,462, .4 2,245.
- Date range: earliest seen 2026-10-27T13:30:00Z (.2), latest 2026-11-13T19:14:02Z (current). Note .4 carries submitted_at style rows with no ts in the sampled schema, so its range is not dated here.
- Intent rejects: intent_rejected events total 29,302 (current 2,181, .1 13,437, .2 4,013, .3 9,671, .4 0). Fill events in the dispatcher total 8,928 across rotations, matching the fill ledger.
- Top reject reasons (reason field, summed by file, truncated broker error strings grouped by prefix):
  - exit_already_resting_at_broker: 7,318 (.1) plus 4,427 (.3) plus smaller counts elsewhere, the single largest class
  - exit_satisfied_no_broker_position: 4,121 (.1), 4,001 (.3), 879 (current), 364 (.2)
  - reconcile_halt: 3,637 (.2), 2,106 (.3), 1,910 (.1), 203 (current)
  - exit_satisfied_no_sleeve_position: 104 (.1), plus 328 (current)
  - insufficient_slice_bp: 606 (current), 87 (.3), 12 (.1)
  - exit_storm_suppressed: 337 (current)
  - Broker FetchError HTTP 403 (existing order or zero available) and HTTP 422 (options market orders, market closed, untradeable asset): hundreds across rotations, 321 plus 40 in current alone for the two 403 forms
  - bad_qty, bad_kind, position_intent_mismatch_terminal, options_market_closed_hold, exit_blocked_opposite_side_resting: all under 100 each per file
- Other event classes: virtual_book_dual_read 2,439 current and 5,855 in .1, broker_unavailable 1,354 current, order_submitted 2,245 in .4 and 4,547 in .3, exit_reconciled_to_broker_book, drained_terminal, virtual_book_enforced, symbol_normalized.
- Mined? Used as the source to build the fill ledger (see manifest) and for reconcile and health. No record found of a systematic reject reason mining pass that asks what the rejected intents would have done.
- Cheapest honest probe: take intent_rejected rows with a symbol and a timestamp, price the rejected intent forward 1 and 5 sessions from bars already in cache, split by reason. reconcile_halt and insufficient_slice_bp rejects are the interesting counterfactuals. exit_already_resting rejects are bookkeeping, not alpha, and should be excluded first.

### 2c. Per sleeve journals (the largest desk store nobody totals)

- Path pattern: /home/hatch/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl
- Format: JSONL per sleeve, events include eval, unfed, last_evaluation with paired_records carrying entry, stop, target, reward_risk, symbol
- Count: 338 journal.jsonl files, 1,330,125 lines total (wc summed). All jsonl under state totals 1,374,554 lines. State holds 348 subdirectories and 2,399 files at maxdepth 2, of which 350 are jsonl and 105 are json.
- Examples: tensor_swing journal.jsonl 3,729 lines plus journal.jsonl.1 16,170 lines, momentum 7,166 lines, aurelia_ndx 4,125 lines. Most sleeves carry exactly one journal.jsonl.
- Date range: sampled journals start 2026-10-24T21:15:09Z (cycle-1) and run to the latest runner cycle on 2026-11-14.
- Mined? Read individually by the runner and inspections for liveness. No evidence of a cross sleeve journal mining pass (for example, extracting every last_evaluation paired_record and grading it forward).
- Cheapest honest probe: extract only last_evaluation paired_records across all 338 journals, deduplicate by sleeve, symbol and entry, grade each against forward bars. That converts an operational log into a labelled signal corpus for free.

### 2d. Producer outputs and ingest (fires.json and friends)

- Path: /home/hatch/workspace/muse-desk-v3/state/ingest/
- Files and live counts (generated 2026-11-14 unless noted):
  - fires.json: 46 fires, plus moonshot_pick and stamped_reconstructions fields. Generated 2026-11-14T22:10:07Z. A single archived copy also exists at state/curator_input via ingest/fires.json path noted in the state listing (only one fires.json at maxdepth 2 in state).
  - rule_fires.json: rule_fires 43, rule_fires_1h 109, log_mcap entries 126, trading_days 346. Generated 2026-11-14T15:07:48Z.
  - alt_data.json: alt_data 126 entries, provenance 4 keys. Same generation time as rule_fires. This is the tag source: sampled fires carry tags ats_z with src finra-ats-weekly-z26-reconstruction, wiki_views, wiki_spike, insider_buys, insider_cluster_10d, tier and tier_src composer-tier-v1-reconstruction.
  - midna_signals.json: signals 157. Generated 2026-11-14T21:53:53Z.
  - timing_signals.json: signals 41. Generated 2026-11-14T19:52:39Z.
  - r5_events.json: events 15, session 2026-11-13.
  - opening_events_replay.json: events 1, session 2026-10-30.
  - lazarus_fires.json: fires 0.
- Archive: /home/hatch/workspace/muse-desk-v3/state/ingest/archive/ holds 2026-11-12, 2026-11-13 and 2026-11-14 only (3 sessions). 2026-11-12 and 2026-11-13 carry alt_data.json and rule_fires.json. 2026-11-14 carries the full 8 file set. So the producer history is 3 days deep, not a long archive.
- Sample fire (fires.json via ingest): sleeve s_q07w_s52_ml_deep70_wlow, symbol ABT, price 109.93, signal_date 2026-11-06, family swing, band midlarge, with the full tag block above.
- Mined? These are live producer outputs consumed the same day by the desk. The 3 day archive shows no sign of a historical mining pass.
- Cheapest honest probe: join the 46 current fires plus the 43 rule_fires to the alt_data tags and grade forward 5 and 20 sessions, split by tier and by ats_z sign. Small n, so report it as a screen, not a verdict.

### 2e. Other desk state files

- reconcile_history.jsonl: 200 rows, fields cycle_id, fill_sweep, generated_at, report.
- stage_timings.jsonl: 347 rows, fields run_id, runner, stages, total_s, started_at, finished_at.
- watchdog.jsonl: 433 rows, 2026-10-25T02:31:45Z to 2026-11-14T22:44:07Z.
- tensor_bundle_history.jsonl: 59 rows, fields session, generated_at, symbols_evaluated, fires. First sampled session 2026-11-11 with 41 symbols evaluated and 21 fires, repeated at 3 generation times.
- broker_pending.jsonl: 0 rows (empty at census time). broker_pending.json also present.
- health.json, runner.json, terminal.json: single object snapshots, not histories. terminal.json keys include entered_setups, setups, sleeves, unfed, evidence_packet, reconcile.
- iv_ledger.json: single json object, 13 top level keys.
- earnings_events_hist.json: single json object, 4 top level keys. earnings_calendar.json also present.
- coinalyze_funding_history.json: single json object, 2 top level keys. kraken_funding.json and coinalyze_funding_current.json also present.
- snapshots/: /home/hatch/workspace/muse-desk-v3/state/snapshots/ holds 8 files (3 final json, 5 json.tmp).
- curator_input/ledger.jsonl: 0 rows. curator_input also holds a live/ folder and slices.json plus terminal_snapshot.json under state/ghost (see section 10).
- Cheapest honest probe for this group: none for alpha directly. stage_timings and watchdog are efficiency data. iv_ledger and earnings history are worth one join each against fills before any new data purchase.

## 3. Options chain archives

### 3a. Desk chain cache (the przm adjacent store)

Note on naming: no directory literally named przm holds chains. PRZM is two parked sleeves (przm_zero, przm_fade_edges) whose build report at /home/hatch/workspace/muse-desk-v3/PRZM-RECREATION-BUILD.md states the desk options_chain producer serves delta only rows with no greeks and no open interest. The chain store itself is the cache below.

- Path: /home/hatch/workspace/muse-desk-v3/cache/options/
- Format: one directory per symbol, each with a single chain.json (sampled SPY chain.json is a dict with a quotes key)
- Count: 65 symbol directories. No per symbol date archive was found inside a symbol directory (SPY holds only chain.json). This is a current snapshot cache, not a dated chain archive.
- Mined? Consumed live by producers and selectors. No dated history means no historical chain mining is possible from this store alone.
- Cheapest honest probe: start snapshotting chain.json daily per symbol from today. Historically, the only dated chains are in the morgue archive (3c) and in ghost ledger selector rows (section 7).

### 3b. Tensor bundle archives

- Path: /home/hatch/workspace/muse-desk-v3/cache/tensor/archive/
- Format: JSON bundles, one per session, plus current bundle.json in cache/tensor/
- Count: 4 archived sessions. bundle-2026-11-11.json fires 21, bundle-2026-11-12.json fires 21, bundle-2026-11-13.json fires 0, bundle-2026-11-14.json fires 0. Bundle keys include session, generated_at, sleeves, fires, tensor_universe, tensor_analysis, tensor_census, plus per symbol entries.
- Book side capture: /home/hatch/workspace/midna-book/ghost-capture/ holds capture_log.jsonl 16 rows, all session 2026-11-14, all fires 0, source cache/tensor/bundle.json, plus 2026-11-14/first-serve.json (the bundle as first served, 0 lines as a text file, valid JSON object).
- Mined? Yes on the book side. The ghost book ledger (section 7) is built from bundle-2026-11-12. The 2026-11-11 bundle with 21 fires has no ghost ledger rows sampled (ghost rows sampled are all dated 2026-11-12 from the 2026-11-12 bundle).
- Cheapest honest probe: diff the 21 fires in the 2026-11-11 bundle against the ghost ledger. Any fire not in the ledger is an unpriced, ungraded orphan.

### 3c. Morgue chain archive (dated, gzipped)

- Path: /home/hatch/workspace/morgue/state/morgue/chains/
- Format: JSON.gz, one file per symbol per session, named YYYY-MM-DD.json.gz
- Count: 6 symbol directories. SPY holds 12 session files, sampled range starting 2026-10-29, 2026-10-30, 2026-11-02, 2026-11-03, 2026-11-04. Total file count across all 6 symbols was not enumerated file by file (directory listing only), so no total is claimed here.
- Also in morgue state: iv_history.jsonl 33 rows, ledger.jsonl 171 rows, state_vectors.jsonl 11 rows, plus folders echo, facts, news, pername_tape, shortvol, and files ext.json, short_interest_nasdaq.json.
- Mined? Yes, as a source artifact. Forecast ledger rows cite chains/QQQ/2026-11-13.json.gz by path and sha256 as source_artifacts.
- Cheapest honest probe: for the 6 symbols, extract the at the money implied volatility and the 25 delta skew per session and join to the forecast grades for the same symbols. Twelve SPY sessions is a pilot, not a study.

## 4. Disagreement ledger and NSM artifacts (hunt and runs)

Base: /home/hatch/workspace/research_notes/decisions-api-leverage-20261114/

### Hunt folder

- disagreement_index_v2.json: rows 68 symbol days with multiple sleeves, both_sides_days 25, with_fwd1 50, with_fwd5 41, spearman D versus abs fwd1 minus 0.226, versus abs fwd5 minus 0.190. Extension of v1 with identical headline counts.
- nsm_fleet_v2.json (negative space mining): dict with coverage (3 keys) and families (11 families).
- conveyor_ledger.jsonl: 23 rows.
- typed_seats_ledger.jsonl: 13 rows. Sampled row is a typed seat call record (model gpt-6-luna, bank hunt-edge-review-v1) dated 2026-11-14.
- holdout_features_v1.jsonl: 61 rows. holdout_outcomes_SEALED.jsonl: 60 rows. Sealed means do not unseal for tuning.
- chain_screen_v1.json: names_ranked 32, gaps 4, ghost_reprice 21 entries, plus index_iv_history and pinning_archive_fri sections.
- calibration_table_v1.json: sections 6, honest_totals 5 keys.
- clv_twins_v2.json, decay_atlas_forward_seed.json, fit_proxy_v1.json, forced_events_calendar.json, exam_results.json, h4_raw.json: single json artifacts, sizes 3 KB to 50 KB. fit_proxy is the largest at 50 KB, h4_raw 43 KB.
- Markdown runs: H1-CONVEYOR-RUN-1.md, H2-MEASUREMENT-RUN-2.md, H3-OPPONENT-ENGINE-1.md, H4-CHAIN-FIRST-RUN-1.md, H5-CORPUS-TRANCHE-1.md.

### Runs folder

- disagreement_index_v1.json: identical headline counts to v2 (68, 25, 50, 41, same spearman values). So v2 added no new symbol days over v1 on the headline numbers.
- attribution_ledger_v1.json: 339 entries (JSON list). Largest runs artifact at 96 KB.
- execution_alpha_v1.json: see section 1 (fills 8,928, sleeves 54).
- ghost_estate_map_v1.json: 48 entries (JSON list).
- falsifier_review_ledger.jsonl: 23 rows.
- gestalt_dryrun_ledger.jsonl: 29 rows. gestalt_dryrun_packs.json: dict with 2 keys.
- triage_ledger.jsonl: 3 rows. triage_labels.json also present.
- first_wave_deterministic.json, truth_serum_v1.json: single json artifacts.
- Markdown runs: 14 run reports including DISAGREEMENT-INDEX-RUN-1.md, GHOST-BOOK-ESTATE-RUN-1.md, EXECUTION-ALPHA-RUN-1.md, ORPHAN-SCAN-1.md, TRUTH-SERUM-RUN-1.md, VITAL-SIGN-1.md.

- Mined? These files ARE the mining output of 2026-11-14. The unmined part is the follow through: disagreement rows with forward outcomes (50 at fwd1, 41 at fwd5) leave 18 symbol days with no fwd1 and 27 with no fwd5, and the NSM 11 families have no forward seed beyond decay_atlas_forward_seed.json.
- Cheapest honest probe: complete the forward grading for the 18 missing fwd1 disagreement rows from bars in cache. That closes the index before any new index is built.

## 5. Gestalt corpus

### 5a. H5 tranche 1 (hunt)

- Path: /home/hatch/workspace/research_notes/decisions-api-leverage-20261114/hunt/read_corpus_tranche1.jsonl
- Format: JSONL with a schema header row
- Count: 31 lines total. Schema row declares record_count_reads 29, record_count_gap_records 1, asof 2026-11-13, focus30 list of 30 symbols (SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC, AAOI, SIVE, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE, FCEL, BE, OKLO, VST, CEG, XLE). Parsed record types: read 29, schema 1, gap 1. So 29 reads plus 1 gap equals 30 focus names accounted for, with SIVE noted in H5 as having no SIP bars.
- Mined? It is itself a mined corpus (built by build_h5.py). The calibration table v1 is its starter grading. No tranche 2 exists in the folder.

### 5b. Composite confidence reads home

- Path: /home/hatch/workspace/research/composite-confidence/
- reads/: 333 files. Naming pattern per read is a folder or stem per symbol date plus a .md and a _passa.json (sampled AAOI 2026-10-08, then 2026-11-04, 06, 09, 10, 11, 12 and onward). So roughly 111 dated reads if grouped in threes. The exact read count is the file count 333, not a parsed record count, and is stated as such.
- live-reads/: 4 files. charts/: 1 file entry at top level.
- calibration/: mining_rows.json is a list of 30 rows, mining_labels.json a dict with 1 key, outcomes_batch1 to 3 each a dict with 10 keys, predictions_batch1 to 3 each a dict with 1 key, samples_batch1 to 3 dicts with 3 to 4 keys.
- zoo_results.json: dict with 3 keys.
- Method files: GESTALT.md, HOLISTIC_METHOD.md, CHART_ANALYST_PROTOCOL.md, CHART_READING_METHOD.md, calibration MINING.md, SCORECARD files for batches 1 to 3 and combined, AUTOPSY files for batches 1 to 3.
- Older gestalt home: /home/hatch/workspace/research_notes/gestalt-100-20261110/ holds only lane1-conditioners, lane2-sentiment, lane4-soxx and sive-options-summary.md at top level. It is a partial lane archive, not a 100 read corpus on disk at that path.
- Book chart studies (related corpus): /home/hatch/workspace/midna-book/chart-study-*.md counts 12 files (2026-11-03 to 2026-11-13 plus 2 weekend files), and FULL-GESTALT-INVENTORY.md is in the book home.
- Mined? Partially. The calibration batches and scorecards show 3 batches mined. The 333 read files span 2026-10-08 to November, well beyond 3 batches of 10 outcomes, so most reads have no outcome row in the calibration folder.
- Cheapest honest probe: list reads with no matching outcome in calibration outcomes_batch files, grade the oldest 30 forward from bars, and extend mining_rows beyond 30. Report the hit rate by read type before building any new reads.

## 6. Forecast record

### 6a. Forecast Engines 30 ledger (terminal lineup, the big one)

- Path: /home/hatch/workspace/terminal-lineup/forecast/ledger.jsonl
- Format: JSONL, hash chained (prev_hash, row_hash, row_id), append only
- Count: 431,124 rows, 834 MB. Row types by grep count: forecast 354,950, grade 69,916, correction 6,257, genesis 1.
- Engines: 26 distinct engine_id values (engine_01 style) in the ledger, against a program name of Forecast Engines 30 and a registry at forecast/registry.json (1,831 lines as counted by wc on the json file).
- Date range: genesis note dated 2026-10-28, program Forecast Engines 30. issued_ts values run from 2026-05-07 (backfilled horizons) to 2026-11-16 (forward horizons issued ahead). Last row sampled is a forecast for QQQ 2026-11-20 strike 737.0, issued 2026-11-13, horizon 2026-11-13 to 2026-11-20.
- So resolved count, honestly stated: 69,916 grade rows are the graded population, against 354,950 forecast rows. Most forecasts are ungraded, many because their horizons have not closed and many by volume per strike.
- Mined? Graded mechanically by its own grading.py and run_grading.py in the same folder. No evidence in the folder names of a cross engine mining pass that asks which engines beat their own degenerate baselines net of the strike by strike volume.
- Cheapest honest probe: sample 1,000 graded forecasts stratified by engine, recompute hit rate and Brier score from the grade rows alone, rank engines. Full file parses are slow (a full JSON parse exceeded 30 seconds in this census), so stream it.

### 6b. Book forecast record

- Path: /home/hatch/workspace/midna-book/FORECAST-LOG.md (551 lines) and FORECAST-TWIN-RECORDS.md (44 lines)
- Content proven by reading: day tallies of resolved calls, for example 38 calls resolved with 25 hits and 13 misses on one Friday, 45 resolved with 33 hits, 50 resolved with 43 hits, 43 resolved with 38 hits, 63 resolved with 43 hits, 59 resolved with 48 hits, and a final tally of 64 calls resolved with 44 hits, 20 misses, 0 untestable. These are per day tallies in prose, not a single summed total, and no grand total is claimed here.
- Forecast twin: 37 calls in the 2026-11-12 pose (bank forecast-twin-bank v1), all marked pending in the records file, resolutions to be graded mechanically from SIP closes. The typed layer ledger below shows 74 forecast_twin_ledger rows, so the twin program ran beyond the 37 recorded in the markdown.
- Mined? Yes, daily, by the close reviews in the book (section 7). The twin pending set is the unmined residue.

## 7. Book journal and ledger (midna-book)

Base: /home/hatch/workspace/midna-book/

- ledger.json: single JSON object. Keys and counts: fills 14, positions 7, realised 4, equity_history 11, exception_ledger 2, pods 7 keys, book_ladder 5 keys, cash 77,545.68, starting_equity 100,000, inception is a 10 character date string. This is the live book state, small and current.
- JOURNAL.md: 3,055 lines. Distinct journal card IDs matching J-YYYYMMDD pattern: 136 unique IDs, earliest J-20261030, latest full ID J-20261113-18, plus one truncated J-20261116- prefix. Total J- mentions 715. So the honest count is 136 distinct cards, not 715.
- ghost-book-ledger.jsonl: 21 rows, all sampled rows dated 2026-11-12 from source bundle cache/tensor/archive/bundle-2026-11-12.json. Each row is a priced expression: symbol, direction, fire with entry, stop, target, confidence, regime, phenotype, votes, plus structure, strikes, expiry 2026-11-27, debit, max_loss, breakeven, r_to_target, chain_ts, selector_verdict and selector_rows. Sampled rows carry resolved null, realized_r null, realized_pnl null. So 21 priced ghost trades, none resolved in the sampled rows.
- expression-shadow-ledger.jsonl: 27 rows. Sampled rows are dated 2026-11-12, session night-study, status drafted, with expression, debit_mid, max_loss, width, baseline and exit_rules.
- trial-registry.jsonl: 15 rows. Sampled rows are CAND-ROT-01, 02, 03 and onward, with status killed, killed, dormant and full falsifier and grade blocks.
- strategy-candidates/: 23 markdown files (2026-11-09 biotech rotation through the 2026-11-14 forced, invention and c1 candidate set).
- chart-study files: 12 (see 5b).
- typed-layer/: ledger.jsonl 206 rows, forecast_twin_ledger.jsonl 74, trail_grader_ledger.jsonl 40, pattern_ledger.jsonl 35, selfaudit_runs.jsonl 12, visual_card_ledger.jsonl 8, rule_taxonomy_ledger.jsonl 6, selfaudit_ledger.jsonl 5, canary_runs.jsonl 3, and 1 row each for coverage_prescreen, exit_census, inspection_quality and pattern_runs, 0 for selfaudit_resolutions. Total typed layer jsonl 393 rows. Plus 10 plus bank json files (bank_v2, pattern, selfaudit, inspection_quality, forecast_twin, visual_card, exit_census, rule_taxonomy, trail_grader, coverage_prescreen).
- ghost-capture/: see 3b. capture_log.jsonl 16 rows, 1 session folder.
- reviews/: 14 files (9 close reviews 2026-11-03 to 2026-11-13, weekly W44, W45, W46, monthly 2026-11, reconciliation 2026-10-31, skip log).
- reflections/: 9 daily files, 2026-11-05 to 2026-11-13.
- experiments/: 1 file EXP-2026-01-resize-at-fill-gate.md plus INDEX.md and PIPELINE.md (3 entries listed).
- Mined? The journal and ledger are mined daily by close reviews and grading runs (runs/JOURNAL-GRADING-RUN-1.md). The ghost ledger 21 rows are priced but unresolved, which is the clearest unmined residue in the book.
- Cheapest honest probe: resolve the 21 ghost rows against bars to expiry or to target and stop, compute realized R per row. They expire 2026-11-27, so the probe has a hard date.

## 8. Morgue and REA archives (file counts only, per task)

- /home/hatch/workspace/morgue/: 5,321 files total by find (all depths), 241 files at maxdepth 2, 3.7 GB. Top level is a working terminal (board, flow, tape, squeeze, insider, inst, finra, sec facts lanes) plus data_cache and state (see 3c and section 9).
- /home/hatch/workspace/terminal-lineup/: 4,224 files total by find, 545 files at maxdepth 2, 15 GB. Includes forecast (section 6a), deep_store (95 entries listed, mostly deep_bars.json payload files and sidecar json files), records (2 entries: forecast-search-2026-10-27, picker-replay-2026-10-27), oracle, specs, site, psychology-engine.
- REA master index: /home/hatch/workspace/rea-master-index/MASTER-INDEX.jsonl 114,823 rows, manifest.jsonl 74,785 rows.
- REA teardowns: /home/hatch/workspace/opt/rea-teardowns/ holds 132 entries at top level (named targets from ai-fund through the long tail, plus DRAGON_MAP, GENOME, IDEA_LEDGER, SCOREBOARD, TARGET-LIST and intake and vault folders). TrendSpider teardown home: /home/hatch/workspace/thestrat-rea-20261027/ holds SCOPE, TEARDOWN-REPORT, PROGRESS files and a workflow script at top level. Note: thestrat is TheStrat, not TrendSpider. No folder named trendspider was found in the listings taken, so no count is claimed for a TrendSpider specific home.
- Mined? REA is mined by index (the master index exists). The morgue and terminal lineup are live terminals, mined daily by their own boards. Their data_cache payloads (below) are the unmined part.
- Cheapest honest probe: none at the archive level. Probe the specific caches in section 9 instead.

## 9. Tag corpora (altdata, FINRA ATS, wiki features)

- Altdata producer store: /home/hatch/workspace/muse-desk-v3/state/ingest/alt_data.json, 126 entries with provenance (see 2d). Tags are attached per fire in fires.json, not stored as a standalone symbol by date table. Tag fields proven in a sampled fire: ats_z (FINRA ATS weekly, z26 reconstruction), wiki_views (25,745 for ABT in the sample), wiki_spike, wiki_spike2, wiki_cov, wiki_low, insider_buys, insider_cluster_10d, insider_distinct_90d, tier.
- Archive depth: alt_data.json also in ingest/archive for 2026-11-12, 2026-11-13, 2026-11-14. So the tag history on disk is 3 sessions, 126 symbols per session at most. There is no long FINRA ATS or wiki time series in the desk ingest store.
- Morgue data_cache: /home/hatch/workspace/morgue/data_cache/ holds board_bt_bars.json, deep_bars.json, plus folders 13f, edgar, deep_expansion, deep_cure_e, deep_hookup_inactive, ownnorm_cache, selfanalogue_cache, squeezemetrics (series.json inside). Morgue output holds insider_trades.json, inst_bundle.json, short_interest_pit.jsonl 822 rows, ledger.jsonl 2,630 rows, board and scorecard json files.
- Wiki features as a standalone store: none found beyond the wiki tags above. No directory named wiki was found in the listings taken.
- FINRA as a standalone store: no FINRA cache directory was found in the desk tree. In the morgue, FINRA is code (finra_daily.py, finra_wait.py, lanes/finra_shortvol.py) plus the short interest PIT file above, not a cached ATS dataset. The ATS numbers live only as reconstructed tags in alt_data.
- Mined? Tags are consumed by the fires composer the same day (tier_src composer-tier-v1-reconstruction). No forward grading by tag value was found.
- Cheapest honest probe: with only 3 sessions of tags, the honest probe is accumulation, not mining. Snapshot alt_data.json daily into a dated table starting now, and after 20 sessions grade ats_z and wiki_spike against forward returns. Any claim before that is underpowered and should be labelled as such.

## 10. Other stores holding tradeable history (surprises)

1. Sleeve journal paired_records (already in 2c). 1.33 million journal lines is the single largest unmined signal corpus on the desk side.
2. Alpaca swing desk fills file: /home/hatch/workspace/alpaca-swing-desk/desk/hidden_state/fills_tca.jsonl exists but is 0 rows. Named as a surprise because it looks like a TCA store and is empty. Do not mine it, note it as a dead store.
3. Desk bars cache: /home/hatch/workspace/muse-desk-v3/cache/bars/ holds 51 symbol folders (sampled SPY holds 1Hour.jsonl). Plus cache/quotes, cache/scan, cache/earnings, cache/kraken, cache/qulla and cache/meta.json (per symbol meta dict). This is the grading substrate for every probe above, not a signal store itself.
4. Terminal lineup deep_store: 95 entries of deep_bars payloads and sidecars under /home/hatch/workspace/terminal-lineup/deep_store/. A bar archive separate from the desk bars cache. Counts are file entries, not bars.
5. Ghost state in desk: /home/hatch/workspace/muse-desk-v3/state/ghost/ holds sleeves, slices.json and terminal_snapshot.json. Listed, not parsed in this census.
6. Space data: /home/hatch/workspace/space_data/ mirrors research space folders (chart reading, desk terminal, options frontier scan and others). Research corpora, not tradeable history, listed so nobody re-censuses them as data.
7. Claim ledger: /home/hatch/workspace/research_notes/claim-ledger.json is 0 lines by wc. Empty store, named so it is not mistaken for evidence.
8. Research notes alpha hunt waves: /home/hatch/workspace/research_notes/ contains alpha-hunt-dive-three-20261114, alpha-hunt-dive-four-20261114, alpha-hunt-x10-dive-20261114 and frontier-trading-research-deep-dive-20261114-2036 folders. They are research text, not row data, and were not counted as stores.
9. Tensor replica and release mirror: /home/hatch/workspace/tensor-replica/bundle and /home/hatch/workspace/teal-diamond-watch/mirror/foliotend-tensor-release/archive-2026-09-19/library/research-bundles exist as bundle archives outside the desk cache. Listed from directory search, not parsed, no counts claimed.
10. PRZM teardown evidence: /home/hatch/workspace/opt/rea-teardowns/przm/ plus the goal home /home/hatch/workspace/goals/przm-zero-teardown-and-strategy-recreations. Evidence archive, not chain data (see 3a naming note).

## Census method and limits

- Counts came from wc -l, python JSON and JSONL parsing, and grep -c style counts, run read only on 2026-11-14.
- The forecast ledger full JSON parse timed out at 30 seconds, so its type counts are grep counts over the raw file and its row count is wc. Both agree at 431,124 total rows (354,950 plus 69,916 plus 6,257 plus 1 equals 431,124).
- Morgue chain total file count across all 6 symbols, ghost state parsing, tensor replica bundles, and the gate distance companion file in the calibration folder were listed but not fully counted. Those rows are marked as such above rather than filled with estimates.
- No sqlite databases were found at maxdepth 3 in the desk, book, morgue or terminal lineup trees in the search that completed. Deeper sqlite stores, if any, are an open row for a follow up census.

## Priority order for mining, cheapest first

1. Ghost book 21 priced rows, resolve to R before their 2026-11-27 expiry.
2. Disagreement index missing forwards, 18 rows at fwd1, close the index.
3. Fill ledger forward grading by sleeve and symbol (8,928 rows, substrate already in cache).
4. Dispatcher reject counterfactuals for reconcile_halt and insufficient_slice_bp only.
5. Sleeve journal paired_records extraction (largest corpus, needs one deduplication pass).
6. Forecast engines per engine Brier ranking on a stratified 1,000 grade sample.
7. Tag accumulation starting now (alt_data daily snapshot), mining deferred until 20 sessions exist.
