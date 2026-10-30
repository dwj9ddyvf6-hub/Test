# Daily SMA200 spot allocation (BTC_ETH_SMA200): recreation package

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): canonical name 'Daily SMA200 spot allocation', type trend following, family native_trend, algorithm grade PARTIAL, unresolved false. Test strategy card: strategies/ausar/coinbase-sma200.md. Accounting gap recorded for every SMA200 variant in this batch: sizing not recorded in any consulted source; the Test card and the Test engine below do record weights and sizing rules, and this package uses those Test sources and names the conflict where the accounting entry text differs. This canonical entry carries aliases BTC_ETH_SMA200 and ausar_pb8. Recorded conflict, not resolved here: the accounting entry text for alias ausar_pb8 records 'Target weights: Ether 100 percent', while the Test card row for the BTC_ETH_SMA200 book and the Test engine spec in desk3/aster_batch1.py both record BTC-USD 0.5 and ETH-USD 0.5. The code in Test implements 0.5 / 0.5.

## What this strategy is

A daily crypto spot trend filter on Coinbase products BTC-USD and ETH-USD: each asset is held only while its completed daily close is above its 200-day simple moving average; otherwise that leg is cash.

## Full algorithm

Evaluation order:

1. For each leg (BTC-USD, ETH-USD), compute the 200-day simple moving average over completed daily closes, inclusive of the latest completed close (engine: desk3/aster_batch1.py, sleeve aster_native_btc_eth_sma200).
2. Gate: a leg qualifies only when its latest completed daily close is strictly above its SMA200.
3. Target weights (engine spec and Test card): BTC-USD 0.5, ETH-USD 0.5 of post-fee NAV when the leg qualifies; 0 when it does not.
4. Rebalance once per day in the 00:00-00:05 UTC window (card). Sells are executed before buys (accounting exit text and engine).
5. Exit: a leg whose gate turns off is reduced to zero; the card records a symbol whose gate turns off is sold in full at the bid.
6. Fees and sizing as recorded on the card: 0.2 percent fee per side; lot floors apply. Engine cadence: 86400 seconds, session 24h.
7. Warmup: with fewer than 200 completed daily closes for a leg, the SMA200 is undefined and the engine fails closed for that leg (no entry).

## Files in this repo

- This doc: docs/BTC_ETH_SMA200-RECREATE.md
- Strategy card in Test: strategies/ausar/coinbase-sma200.md
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'Daily SMA200 spot allocation'
- Code in Test: sleeves/aster_native_btc_eth_sma200.py (wrapper, sleeve id aster_native_btc_eth_sma200) delegating to the shared engine desk3/aster_batch1.py (spec weights BTC-USD 0.5, ETH-USD 0.5, cadence_s 86400, session 24h; inputs bars and positions)
- Family code in Test: packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/coinbase_sma200.py (books ETH_SMA200 and BTC_ETH_SMA200) and packages/claude/master-desk-parity-tools/tools/parity/coinbase_sma200.py
- No code was vendored for this package; the code above was already in Test.

## Configuration

- Universe: BTC-USD and ETH-USD on Coinbase (card).
- Timeframe: daily. SMA period: 200. Weights: BTC 0.5, ETH 0.5 of post-fee NAV.
- Cadence: 86400 seconds, session 24h (engine spec). Rebalance window 00:00-00:05 UTC (card).
- Fee: 0.2 percent per side (card). Lot floors apply (card).
- Account size for this book: not in the record.

## Data inputs

- Coinbase daily candles (200) for BTC-USD and ETH-USD, products and quotes (card). Engine inputs declared: bars and positions, with bars and broker readback producers at 900 second freshness (desk3/aster_batch1.py).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Read this package and the strategy card or algorithm doc named in the Files section.
3. Install the code paths named in the Files section at the same relative paths in a desk3-compatible runtime; the sleeve wrapper imports its shared engine by the module path recorded there, so keep the repo directory layout unchanged.
4. Configure the sleeve with the exact parameters in the Configuration section; do not substitute values from a different variant.
5. Provide the data inputs named in the Data inputs section through the runtime view (bars, positions, and quotes where the engine declares them).
6. Call the sleeve module's evaluate(view, ctx) function on the cadence recorded in the Configuration section and route the returned intents through the desk dispatcher; this package does not include a standalone broker connector.
7. Run the Verification checklist before trusting any output.

## Verification

Behavior checklist (no test file for this sleeve was located in Test):
1. With 200 or more completed closes and the last close above SMA200 for both legs, targets are BTC 0.5 and ETH 0.5 of post-fee NAV.
2. With the BTC close at or below its SMA200 and ETH above, the BTC target is 0 and the ETH target stays 0.5.
3. Reductions are emitted before increases in the same evaluation.
4. With fewer than 200 completed closes for a leg, no entry is emitted for that leg.
