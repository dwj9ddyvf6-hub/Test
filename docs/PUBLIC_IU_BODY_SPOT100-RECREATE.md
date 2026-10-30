# PUBLIC_IU_BODY_SPOT100: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Canonical id: `PUBLIC_IU_BODY_SPOT100`; canonical name: PUBLIC_IU_BODY_SPOT100; aliases: PUBLIC_IU_BODY_SPOT100.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type momentum, family unrecorded, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "PUBLIC_IU_BODY_SPOT100" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: none recorded; alias record sources: ausar_deployed
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path for these ids, only the femto-lean forward ports noted where relevant); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/ausar/ausar_spot_recipes.py + sleeves/ausar/vendor/public_recipes/public_source_sleeves.py + packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

IU Big Body Bar spot book: the original Binance spot implementation of the IU BBB Pine recipe on ENJUSDT 5-minute bars, on a 100,000 USDT book at 100 percent equity sizing. Accounting grade PARTIAL and UNRESOLVED: the accounting recorded no entry, exit or sizing rule; the code cited above records all three, and the code is the truth here.

## Full algorithm

Source signal, from the Pine source and identically from the reducer `source_features('iu_body', ...)` with DEFAULTS {big_body_threshold: 4.0, atr_length: 14, atr_factor: 2.0, body_baseline: 'source_inclusive21_div20'}:
1. body = |close - open| per bar. Baseline: sum of the last 21 bodies divided by 20 (the Pine loop sums body[0..20] and divides by 20); fewer than 21 bars gives no baseline and no signal.
2. strong: last body > baseline x 4.0. long_signal: strong and last close > last open. short_signal: strong and last close < last open.
3. Entry (reducer, flat only): a long signal sets the pending target long ('source_body_impulse'); the short signal sets a short target in the reducer, which the spot wrapper vetoes for opening (long spot only).
4. Exit / stop (reducer, held position, bars completed after the position opened): ATR = Wilder RMA ATR14. Candidate stop: long = average price - ATR x 2.0 initially, then ratcheted to max(previous stop, close - ATR x 2.0); short mirrors with min. A non-positive stop is not submitted ('source_stop_nonpositive_not_submitted'). The reducer emits STOP_PLAN; the wrapper states the exit as the trailing 2 x ATR stop triggered by the observed bid.

Common wrapper rules from `sleeves/ausar/ausar_spot_recipes.py` (header and code), in evaluation order:
1. Capture, in order: exchange metadata, completed native bars, last trade, book ticker. Every completed native bar of the capture (the 299 of a klines limit-300 read) is validated as a batch, then new bars advance the runtime IndicatorStream and the reducer in order. A corrected or out-of-order bar, an invalid batch, or a failed acquisition (exchange metadata, bars, a last trade missing or more than 60 s before the quote, or a non-trading contract) blocks this capture's entries: a pending entry target is dropped (an opposite owned position is flattened instead) and working opening orders are cancelled.
2. Reducer step (`public_source_sleeves.step`) on BAR / QUOTE / FILL / CANCEL events only; state changes only on real events. The install config is `install_config`: symbol from MARKETS, market_kind spot, initial_cash 100000, quantity_mode equity_percent, quantity_value 100.
3. An entry target is good for 300 s from its bar's completion (and the reducer's own 300 s entry TTL). The QUOTE event sizes it from the reducer's book cash (100 percent including 10 bps) at the observed ask, floored to the venue lot (the native LOT_SIZE x MARKET_LOT_SIZE intersection) and capped by the venue maximum; venue minimum / notional refusals cancel it; each fill is bounded by the displayed size net of what earlier fills took from the same displayed book; an opening remainder is cancelled (no pyramid).
4. Long spot only: a short target from the source signal is vetoed by the reducer (no short capability on spot) in this book; the short signal's role is the exit / reversal logic the reducer records.
5. Closing orders continue on later quotes. Sleeve cadence in the wrapper: SleeveConfig cadence_s=20, family ausar_spot_recipes, universe the single symbol.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Book wrapper (already in Test): `sleeves/ausar/ausar_spot_recipes.py`; its header names this book verbatim: "PUBLIC_IU_BODY_SPOT100 (ENJUSDT 5m)", strategy key `iu_body`, sleeve id `ausar_public_iu_body_spot100`, install config hash prefix 29d4526f.
- Reducer (already in Test, two copies): `sleeves/ausar/vendor/public_recipes/public_source_sleeves.py` and `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/public_source_sleeves.py` (strategy `iu_body`).
- Pine source (already in Test): `packages/ausar/aster-execution-r15/desk/strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine` (SOURCE_BINDING.json sha256 d3fafcced33085d54a7a50e669d9543d3cc5de47e2121c1d81327fdddb045048).
- Runtime (already in Test): `sleeves/ausar/vendor/public_recipes/public_recipe_runtime.py` (MARKETS iu_body = ENJUSDT, 5m, 300000 ms).
- Related ports (already in Test): `sleeves/aster_pub_enj_iu_body.py` / `desk3/aster_b4.py` evaluate_enj_iu_body, and `sleeves/fwd_alpaca_enj_iu_body.py`, whose status() states it preserves PUBLIC_IU_BODY_SPOT100 and is BLOCKED because ENJ/USD is unlisted at Alpaca and the original ENJUSDT sleeve stays blocked on Binance HTTP 451; that block is the forward port's state, recorded here, not a rule of the spot book's signal. Existing docs: `strategies/ausar/iu-body.md`, `docs/ASTER_PUB_ENJ_IU_BODY-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "PUBLIC_IU_BODY_SPOT100" (UNRESOLVED, PARTIAL).

## Configuration

- Book: PUBLIC_IU_BODY_SPOT100; strategy key iu_body; symbol ENJUSDT; interval 5m (step 300000 ms); market_kind spot; initial_cash 100000 USDT; quantity_mode equity_percent, quantity_value 100.
- Source params: big_body_threshold 4.0, atr_length 14, atr_factor 2.0, body_baseline source_inclusive21_div20. Pine header also declares initial_capital 100000, slippage 1, commission_value 0.002 for the Pine strategy itself.
- Wrapper: cadence_s 20; entry TTL 300 s; quote sizing 100 percent of book cash including 10 bps, lot-floored, venue-max capped.
- Accounting status history: ausar_deployed, mode=original_independent_local_paper, running=False.

## Data inputs

Binance spot data through the wrapper capture: exchangeInfo contract metadata, completed 5m klines (limit-300 read, last 299 used), last trade, and book ticker quote; the reducer consumes BAR / QUOTE / FILL / CANCEL events built from that capture.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state, never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- Fewer than 21 bars, or a last body at or below 4.0 x the 21-bar baseline divided by 20, produces no signal.
- A bullish strong body while flat sets a long pending target good for 300 s, sized at the observed ask from 100 percent of book cash including 10 bps, floored to the venue lot; a bearish strong body opens nothing on spot.
- A held long's stop starts at average price minus 2 x ATR14 and only ratchets up with close minus 2 x ATR14; the exit fires on the observed bid at or through the stop.
- A failed capture drops a pending entry target and cancels working opening orders.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
