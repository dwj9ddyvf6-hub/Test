# PUBLIC_TOMAZETTI_RSI2_SPOT100: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Canonical id: `PUBLIC_TOMAZETTI_RSI2_SPOT100`; canonical name: PUBLIC_TOMAZETTI_RSI2_SPOT100; aliases: PUBLIC_TOMAZETTI_RSI2_SPOT100.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type mean reversion, family unrecorded, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "PUBLIC_TOMAZETTI_RSI2_SPOT100" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: none recorded; alias record sources: ausar_deployed
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path for these ids, only the femto-lean forward ports noted where relevant); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/ausar/ausar_spot_recipes.py + sleeves/ausar/vendor/public_recipes/public_source_sleeves.py + packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/TOMAZETTI_RSI2.pine + aster_sleeves/aster_pub_rsi2_ada.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Tomazetti RSI2 spot book: the original Binance spot implementation of the Tomazetti RSI(2) Pine recipe on ADAUSDT hourly bars, long only, on a 100,000 USDT book at 100 percent equity sizing (the Pine declaration itself is default_qty_type percent_of_equity, default_qty_value 100). Accounting grade PARTIAL and UNRESOLVED: the accounting recorded no entry, exit or sizing rule; the code cited above records all three, and the code is the truth here.

## Full algorithm

Source signal, from the Pine source and identically from the reducer `source_features('tomazetti_rsi2', ...)` with DEFAULTS {rsi_length: 2, rsi_threshold: 10, short_ma_length: 5, long_ma_length: 200, rsi_ma_filter: true, rsi_ma_length: 4, rsi_ma_threshold: 30, stop_enabled: false, stop_percent: 10, window_start: 2009-01-02, window_end: 2020-12-30 in the reducer defaults}:
1. RSI = Wilder RSI(2) of close; SMA200 and SMA5 of close; SMA4 of the RSI series.
2. In-window test: the bar's open time must lie inside the source window. The install config in `ausar_spot_recipes.install_config` overrides window_end to 2030-12-30T00:00:00+00:00 for this strategy (the frozen install config whose fhash prefix is c56723c6); window_start stays 2009-01-02.
3. long_signal (entry, flat only in the reducer's BAR handling): in window and RSI(2) < 10 and close > SMA200 and (rsi_ma_filter on) SMA4(RSI(2)) < 30. Sets the pending target long ('source_rsi2_filtered'). short_signal is always False: long only.
4. Exit: long_close_signal: in window and close > SMA5; with a position or pending target it sets the target flat ('source_close_above_sma5'), except a bar completed at or before the position's open is skipped.
5. Optional stop: stop_enabled is false in the install, so no stop is active; the code's disabled branch would set a stop at average price x (1 - 10/100) only if the switch were on, which it is not.

Common wrapper rules from `sleeves/ausar/ausar_spot_recipes.py` (header and code), in evaluation order:
1. Capture, in order: exchange metadata, completed native bars, last trade, book ticker. Every completed native bar of the capture (the 299 of a klines limit-300 read) is validated as a batch, then new bars advance the runtime IndicatorStream and the reducer in order. A corrected or out-of-order bar, an invalid batch, or a failed acquisition (exchange metadata, bars, a last trade missing or more than 60 s before the quote, or a non-trading contract) blocks this capture's entries: a pending entry target is dropped (an opposite owned position is flattened instead) and working opening orders are cancelled.
2. Reducer step (`public_source_sleeves.step`) on BAR / QUOTE / FILL / CANCEL events only; state changes only on real events. The install config is `install_config`: symbol from MARKETS, market_kind spot, initial_cash 100000, quantity_mode equity_percent, quantity_value 100.
3. An entry target is good for 300 s from its bar's completion (and the reducer's own 300 s entry TTL). The QUOTE event sizes it from the reducer's book cash (100 percent including 10 bps) at the observed ask, floored to the venue lot (the native LOT_SIZE x MARKET_LOT_SIZE intersection) and capped by the venue maximum; venue minimum / notional refusals cancel it; each fill is bounded by the displayed size net of what earlier fills took from the same displayed book; an opening remainder is cancelled (no pyramid).
4. Long spot only: a short target from the source signal is vetoed by the reducer (no short capability on spot) in this book; the short signal's role is the exit / reversal logic the reducer records.
5. Closing orders continue on later quotes. Sleeve cadence in the wrapper: SleeveConfig cadence_s=20, family ausar_spot_recipes, universe the single symbol.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Book wrapper (already in Test): `sleeves/ausar/ausar_spot_recipes.py`; its header names this book verbatim: "PUBLIC_TOMAZETTI_RSI2_SPOT100 (ADAUSDT 1h)", strategy key `tomazetti_rsi2`, sleeve id `ausar_public_tomazetti_rsi2_spot100`, install config hash prefix c56723c6.
- Reducer (already in Test, two copies): `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py` and `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/public_source_sleeves.py` (strategy `tomazetti_rsi2`).
- Pine source (already in Test): `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/TOMAZETTI_RSI2.pine` (SOURCE_BINDING.json sha256 b8d8e844e2cddd2897ac3726b1c3c0ddb5add48eea2787b146bae018b0d356b4).
- Runtime (already in Test): `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py` (MARKETS tomazetti_rsi2 = ADAUSDT, 1h, 3600000 ms).
- v3 port (already in Test): `aster_sleeves/aster_pub_rsi2_ada.py`, whose header states verbatim "(TSV #46 / SM PUBLIC_TOMAZETTI_RSI2_SPOT100). Hourly Wilder RSI2<10, close>SMA200, SMA4(RSI2)<30; exit close>SMA5; stop disabled; long only; 100% available-cash sizing." Existing docs: `strategies/ausar/public-rsi2.md`, `docs/ASTER_PUB_RSI2_ADA-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "PUBLIC_TOMAZETTI_RSI2_SPOT100" (UNRESOLVED, PARTIAL).

## Configuration

- Book: PUBLIC_TOMAZETTI_RSI2_SPOT100; strategy key tomazetti_rsi2; symbol ADAUSDT; interval 1h (step 3600000 ms); market_kind spot; initial_cash 100000 USDT; quantity_mode equity_percent, quantity_value 100 (the reducer default for this strategy, kept by the install config).
- Source params as in the Full algorithm; install override: window_end 2030-12-30T00:00:00+00:00.
- Wrapper: cadence_s 20; entry TTL 300 s; quote sizing 100 percent of book cash including 10 bps, lot-floored, venue-max capped.
- Accounting status history: ausar_deployed, mode=original_independent_local_paper, running=False.

## Data inputs

Binance spot data through the wrapper capture: exchangeInfo contract metadata, completed 1h klines (limit-300 read, last 299 used), last trade, and book ticker quote; the reducer consumes BAR / QUOTE / FILL / CANCEL events built from that capture.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state, never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- Entry requires all of: bar inside the installed window (2009-01-02 to 2030-12-30), RSI(2) < 10, close > SMA200, SMA4(RSI(2)) < 30; failing any one blocks entry.
- A held position exits flat when close > SMA5; no stop exit can fire because stop_enabled is false.
- Entry sizing is 100 percent equity: at the observed ask from book cash including 10 bps, floored to the venue lot, target good for 300 s.
- A bar completed at or before the position's open does not trigger the SMA5 exit.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
