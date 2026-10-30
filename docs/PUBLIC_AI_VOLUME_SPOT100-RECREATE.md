# PUBLIC_AI_VOLUME_SPOT100: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Canonical id: `PUBLIC_AI_VOLUME_SPOT100`; canonical name: PUBLIC_AI_VOLUME_SPOT100; aliases: PUBLIC_AI_VOLUME_SPOT100.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type momentum, family unrecorded, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "PUBLIC_AI_VOLUME_SPOT100" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: none recorded; alias record sources: ausar_deployed
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path for these ids, only the femto-lean forward ports noted where relevant); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/ausar/ausar_spot_recipes.py + sleeves/ausar/vendor/public_recipes/public_source_sleeves.py + packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/AI_Volume_Strategy.pine. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

AI Volume spot book: the original Binance spot implementation of the AI Volume Strategy Pine recipe on LINKUSDT 4-hour bars, on a 100,000 USDT book at 100 percent equity sizing. Accounting grade PARTIAL and UNRESOLVED: the accounting recorded no entry, exit or sizing rule; the code cited above records all three, and the code is the truth here. The classification evidence in the accounting itself reads the mechanism from the forward port of this same recipe.

## Full algorithm

Source signal, from the Pine source and identically from the reducer `source_features('ai_volume', ...)` with DEFAULTS {volume_ema_length: 20, volume_multiplier: 2.0, price_ema_length: 50, exit_bars: 5}:
1. volume_ema = EMA20 of volume; price_ema = EMA50 of close.
2. volume_spike: last volume > volume_ema x 2.0.
3. long_signal: spike and last close > price_ema and last close > last open. short_signal: spike and last close < price_ema and last close < last open.
4. On a signal bar the reducer resets its source counter to 0 and, if flat or held on the opposite side, sets the pending target to that side ('source_entry_or_reversal'); same-side entries are suppressed. The counter then increments each bar; when the counter reaches exit_bars=5 and a position or pending target exists, the target becomes flat ('source_signal_reset_counter_exit'), except that a bar completed at or before the position's open is skipped ('prefill_completed_bar_owned_exit_skipped'). This is the 5-bar exit; there is no stop in the source recipe.

Common wrapper rules from `sleeves/ausar/ausar_spot_recipes.py` (header and code), in evaluation order:
1. Capture, in order: exchange metadata, completed native bars, last trade, book ticker. Every completed native bar of the capture (the 299 of a klines limit-300 read) is validated as a batch, then new bars advance the runtime IndicatorStream and the reducer in order. A corrected or out-of-order bar, an invalid batch, or a failed acquisition (exchange metadata, bars, a last trade missing or more than 60 s before the quote, or a non-trading contract) blocks this capture's entries: a pending entry target is dropped (an opposite owned position is flattened instead) and working opening orders are cancelled.
2. Reducer step (`public_source_sleeves.step`) on BAR / QUOTE / FILL / CANCEL events only; state changes only on real events. The install config is `install_config`: symbol from MARKETS, market_kind spot, initial_cash 100000, quantity_mode equity_percent, quantity_value 100.
3. An entry target is good for 300 s from its bar's completion (and the reducer's own 300 s entry TTL). The QUOTE event sizes it from the reducer's book cash (100 percent including 10 bps) at the observed ask, floored to the venue lot (the native LOT_SIZE x MARKET_LOT_SIZE intersection) and capped by the venue maximum; venue minimum / notional refusals cancel it; each fill is bounded by the displayed size net of what earlier fills took from the same displayed book; an opening remainder is cancelled (no pyramid).
4. Long spot only: a short target from the source signal is vetoed by the reducer (no short capability on spot) in this book; the short signal's role is the exit / reversal logic the reducer records.
5. Closing orders continue on later quotes. Sleeve cadence in the wrapper: SleeveConfig cadence_s=20, family ausar_spot_recipes, universe the single symbol.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Book wrapper (already in Test): `sleeves/ausar/ausar_spot_recipes.py`; its header names this book verbatim: "PUBLIC_AI_VOLUME_SPOT100 (LINKUSDT 4h): the originals, each a 100k USDT book", strategy key `ai_volume`, sleeve id `ausar_public_ai_volume_spot100`, install config hash prefix 028dfd0a.
- Reducer (already in Test, two copies): `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py` and `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/public_source_sleeves.py` (strategy `ai_volume`, DEFAULTS and `source_features`).
- Pine source (already in Test): `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/AI_Volume_Strategy.pine` (SOURCE_BINDING.json sha256 d83e7f5990090f0dce9dc4ac08292b459f019c661620ca6c57c6e783128f07d1).
- Runtime (already in Test): `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py` (MARKETS ai_volume = LINKUSDT, 4h, 14400000 ms).
- v3 port of the same recipe (already in Test): `sleeves/aster_pub_link_ai_volume.py` / `desk3/aster_b4.py` evaluate_link_ai_volume, and the forward port `sleeves/fwd_alpaca_link_ai_volume.py`, whose header states it "preserves PUBLIC_AI_VOLUME_SPOT100". Existing docs: `strategies/ausar/ai-volume.md`, `docs/ASTER_PUB_LINK_AI_VOLUME-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "PUBLIC_AI_VOLUME_SPOT100" (UNRESOLVED, PARTIAL).

## Configuration

- Book: PUBLIC_AI_VOLUME_SPOT100; strategy key ai_volume; symbol LINKUSDT; interval 4h (step 14400000 ms); market_kind spot; initial_cash 100000 USDT; quantity_mode equity_percent, quantity_value 100.
- Source params: volume_ema_length 20, volume_multiplier 2.0, price_ema_length 50, exit_bars 5.
- Wrapper: cadence_s 20; entry TTL 300 s; quote sizing 100 percent of book cash including 10 bps, lot-floored, venue-max capped.
- Accounting status history: ausar_deployed, mode=original_independent_local_paper, running=False.

## Data inputs

Binance spot data through the wrapper capture: exchangeInfo contract metadata, completed 4h klines (limit-300 read, last 299 used), last trade, and book ticker quote; the reducer consumes BAR / QUOTE / FILL / CANCEL events built from that capture.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state, never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A bar with volume at or below 2.0 x EMA20(volume), or a close at or below EMA50, or a close at or below the open, produces no long signal; the bearish mirror produces no spot opening (short vetoed on spot).
- A long signal sets a pending target good for 300 s, sized at the observed ask from 100 percent of book cash including 10 bps, floored to the venue lot.
- The position exits flat when the source counter reaches 5 bars, or on the opposite-spike reversal logic; an opening remainder after a partial fill is cancelled.
- A failed capture (stale last trade over 60 s, invalid bars, non-trading contract) drops a pending entry target and cancels working opening orders.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
