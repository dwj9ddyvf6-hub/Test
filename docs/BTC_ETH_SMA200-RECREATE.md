# BTC_ETH_SMA200: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Daily SMA200 spot allocation", type trend following, family native_trend. Aliases: `BTC_ETH_SMA200`, `ausar_pb8`. Algorithm grade PARTIAL; recorded gap: "sizing not recorded in any consulted source". Merge evidence (Tier A): the md2 catalog records `ausar_pb8` status=replaced, merged into the genuine hosted book `BTC_ETH_SMA200` ("md2 reimplementation retired; hosted by posted Ausar prospective_native (BTC_ETH_SMA200), rules match the TSV entry/exit text").
- Test strategy card: `strategies/ausar/coinbase-sma200.md`, row BTC_ETH_SMA200: "`ausar_btc_eth_sma200_coinbase`; Midna v3 `aster_native_btc_eth_sma200` | BTC and ETH, half each | close vs the 200-day SMA".
- CONFLICT IN THE RECORD, stated plainly: the accounting's entry text for this canonical id (sourced from alias `ausar_pb8`) reads "Target weights: Ether 100%", while the Test card, the v3 engine spec in `desk3/aster_batch1.py`, and the hosting map in `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py` (ausar_pb8 -> prospective_native book BTC_ETH_SMA200) all describe this book as BTC 50% / ETH 50%, with the ETH-only book carried by the sibling canonical id `ETH_SMA200`. This package follows the code, the card, and the hosting map (50/50), and flags the accounting text as inconsistent rather than silently resolving it.

## What this strategy is

A daily trend-filter spot allocation over BTC-USD and ETH-USD: each asset is held at its target weight while its completed daily close is above its 200-day simple moving average, and is out (weight 0) while the close is at or below it. Rebalanced once per day.

## Full algorithm

From the accounting entry/exit text, the Test card, and the running engine `desk3/aster_batch1.py` (kind "native"; the engine header states it is a port of `backend/prospective_native.py` + `prospective_native_math.py`, with the fee-funded `rebalance()` bisection ported and sells before buys):

1. For each leg (BTC-USD weight 0.5, ETH-USD weight 0.5 in the engine SPECS for `aster_native_btc_eth_sma200`), take completed daily closes; a leg needs at least 200 completed bars or its SMA200 is undefined.
2. Gate: a leg qualifies when its last completed daily close is strictly above the SMA of its last 200 completed closes (inclusive SMA200). Qualified leg target weight = its book weight; unqualified leg target weight = 0.
3. Rebalance to the fee-funded targets: post-fee NAV is solved by bisection (70 iterations in the code) with a 0.2% (0.002) fee per side, so targets are net of the fee on the traded amount. Deltas within $0.01 are not traded.
4. Order of operations: sells (reductions) are emitted before buys (increases), per the archive rule recorded in the engine.
5. Engine enhancements present in the Test code and on by default (switchable via `extra[f"enh_{sid}"]` / `ctx["enhance"][sid]`, default ON; OFF restores the pre-change rule): ENH-B5 per-leg warmup (a leg with at least 200 completed bars trades on its own fee-funded target even if the other leg's history is short or stale; the unqualified leg is left untouched). The accounting predates this enhancement note; it is part of the code that runs in Test and is recorded here for fidelity.
6. Exit: a leg whose gate turns off is reduced to weight 0 at the next rebalance (sold in full at the bid, per the card's exit text for the book family).

Accounting-recorded gap: position sizing beyond the target weights and the fee is "not in the record" in the accounting; the engine's $10,000-slice desk convention and the fee-funded bisection above are what the Test code implements.

## Files in this repo

- This package: `docs/BTC_ETH_SMA200-RECREATE.md`
- Strategy card: `strategies/ausar/coinbase-sma200.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_native_btc_eth_sma200.py` (wrapper; SLEEVE_ID `aster_native_btc_eth_sma200`)
  - `adapters3/aster_native_btc_eth_sma200.py` and `integration/aster_native_btc_eth_sma200_adapter.py` (same wrapper)
  - `desk3/aster_batch1.py` (shared engine, kind "native"; SPECS weights BTC-USD 0.5 / ETH-USD 0.5, cadence_s 86400, session 24h)
- Hosting record: `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py` (maps ausar_pb8 to the genuine book BTC_ETH_SMA200)

## Configuration

- Universe: BTC-USD, ETH-USD (Coinbase spot), per the card. The accounting records universe/asset class/timeframe as "not recorded in consulted sources"; the card records asset Crypto spot, timeframe 1d.
- Weights: BTC 0.5 / ETH 0.5, each gated by its own SMA200 (see the conflict note in Provenance).
- Fee: 0.2% per side (card and engine agree). Lot floors per the card.
- Cadence: once per day; the card records rebalances at 00:00-00:05 UTC for the book family; the v3 engine config row is cadence_s 86400, session 24h.
- State: positions and cash are read from the desk snapshot (`bars`, `positions` inputs); no sleeve-private state file is recorded.

## Data inputs

Coinbase USD spot completed daily bars and actual bid/ask (accounting filter text and card agree). Engine declared inputs: bars, positions. Producers named in the engine: bars (900s freshness), broker_readback (900s, positions).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test) so that `desk3/` and `sleeves/` sit side by side; the wrapper imports the shared engine from `desk3/` by module path.
2. No third-party package beyond the desk3 runtime is required by the wrapper or the engine (standard library only, per the engine source).
3. Standalone evaluation: build a `view` dict carrying the declared inputs (see Data inputs) and call the wrapper: `from sleeves.aster_native_btc_eth_sma200 import evaluate; intents = evaluate(view, ctx)`. `ctx` may be None for a stateless read; the desk3 dispatcher supplies the snapshot view and context in production.
4. In the desk, the v3 dispatcher calls `evaluate` on the sleeve's cadence and routes the returned intent dicts (market, day, buy_to_open / sell_to_close) to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- With 200+ completed daily bars for both legs and both closes above their SMA200, one rebalance targets BTC at 50% and ETH at 50% of post-fee NAV.
- With the ETH close at or below its SMA200 and BTC above, the rebalance sells ETH to zero and leaves BTC at its 50% target.
- Sells are emitted before buys in the same evaluation.
- A leg with fewer than 200 completed bars does not block the qualified leg (per-leg warmup enhancement on), and with the enhancement off the evaluation emits nothing until both legs have 200 bars.
- Deltas of $0.01 or less produce no intent.
