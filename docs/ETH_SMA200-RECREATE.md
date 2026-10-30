# ETH_SMA200: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Daily SMA200 spot allocation", type trend following, family native_trend. Aliases: `ETH_SMA200`, `ausar_pb7`. Algorithm grade PARTIAL; recorded gap: "sizing not recorded in any consulted source". Merge evidence (Tier A): the md2 catalog records `ausar_pb7` status=replaced, merged into the genuine hosted book `ETH_SMA200` ("md2 reimplementation retired; hosted by posted Ausar prospective_native (ETH_SMA200), rules match the TSV entry/exit text").
- Test strategy card: `strategies/ausar/coinbase-sma200.md`, row ETH_SMA200: "`ausar_eth_sma200_coinbase`; Midna v3 `aster_native_eth_sma200` | ETH | close vs the 200-day SMA". Card sizing line: "Weights: ETH_SMA200 0/1, BTC_ETH_SMA200 0.5/0.5 of post-fee NAV; 0.2% fee per side; lot floors."
- CONFLICT IN THE RECORD, stated plainly: the accounting's entry text for this canonical id (sourced from alias `ausar_pb7`) reads "Target weights: Bitcoin 50%, Ether 50%", while the Test card, the v3 engine spec in `desk3/aster_batch1.py` (weights ((ETH-USD, 1.0),)), and the hosting map in `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py` (ausar_pb7 -> prospective_native book ETH_SMA200) all describe this book as ETH only, weight 0/1. This package follows the code, the card, and the hosting map (ETH 100% when gated on), and flags the accounting text as inconsistent rather than silently resolving it.

## What this strategy is

A daily trend-filter spot allocation over ETH-USD only: ETH is held at full target weight while its completed daily close is above its 200-day simple moving average, and is out (cash) while the close is at or below it. Rebalanced once per day.

## Full algorithm

From the accounting entry/exit text, the Test card, and the running engine `desk3/aster_batch1.py` (kind "native"; the engine header states it is a port of `backend/prospective_native.py` + `prospective_native_math.py`, with the fee-funded `rebalance()` bisection ported and sells before buys):

1. Take completed daily closes for ETH-USD; at least 200 completed bars are required or the SMA200 is undefined and the evaluation emits nothing (fail closed).
2. Gate: ETH qualifies when its last completed daily close is strictly above the SMA of its last 200 completed closes (inclusive SMA200). Target weight = 1.0 when qualified, 0.0 when not.
3. Rebalance to the fee-funded target: post-fee NAV is solved by bisection (70 iterations in the code) with a 0.2% (0.002) fee per side. Deltas within $0.01 are not traded.
4. Exit: when the gate turns off, the whole ETH holding is sold (the accounting exit text for the alias adds "sell reductions before buying increases", which the single-asset book satisfies trivially).
5. Engine enhancement present in the Test code and on by default (switchable via `extra[f"enh_{sid}"]` / `ctx["enhance"][sid]`, default ON; OFF restores the pre-change rule): ENH-B5 no-trade deadband for the single-asset book: while invested and gated on, drift adjustments within 0.5% of book value are refused; initial entries and full exits are never banded.

Accounting-recorded gap: position sizing beyond the target weight and the fee is "not in the record" in the accounting; the engine's fee-funded bisection above is what the Test code implements.

## Files in this repo

- This package: `docs/ETH_SMA200-RECREATE.md`
- Strategy card: `strategies/ausar/coinbase-sma200.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_native_eth_sma200.py` (wrapper; SLEEVE_ID `aster_native_eth_sma200`)
  - `adapters3/aster_native_eth_sma200.py` and `integration/aster_native_eth_sma200_adapter.py` (same wrapper)
  - `desk3/aster_batch1.py` (shared engine, kind "native"; SPECS weights ((ETH-USD, 1.0),), cadence_s 86400, session 24h)
- Hosting record: `packages/grokbot/master-desk-md2/mdesk/engines/ausar_genuine.py` (maps ausar_pb7 to the genuine book ETH_SMA200)

## Configuration

- Universe: ETH-USD (Coinbase spot), per the card. The accounting records universe/asset class/timeframe as "not recorded in consulted sources"; the card records asset Crypto spot, timeframe 1d.
- Weight: ETH 0/1 of post-fee NAV (see the conflict note in Provenance).
- Fee: 0.2% per side (card and engine agree). Lot floors per the card.
- Cadence: once per day; the card records rebalances at 00:00-00:05 UTC for the book family; the v3 engine config row is cadence_s 86400, session 24h.
- State: positions and cash are read from the desk snapshot (`bars`, `positions` inputs); no sleeve-private state file is recorded.

## Data inputs

Coinbase USD spot completed daily bars and actual bid/ask (accounting filter text and card agree). Engine declared inputs: bars, positions. Producers named in the engine: bars (900s freshness), broker_readback (900s, positions).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test) so that `desk3/` and `sleeves/` sit side by side; the wrapper imports the shared engine from `desk3/` by module path.
2. No third-party package beyond the desk3 runtime is required by the wrapper or the engine (standard library only, per the engine source).
3. Standalone evaluation: build a `view` dict carrying the declared inputs (see Data inputs) and call the wrapper: `from sleeves.aster_native_eth_sma200 import evaluate; intents = evaluate(view, ctx)`. `ctx` may be None for a stateless read; the desk3 dispatcher supplies the snapshot view and context in production.
4. In the desk, the v3 dispatcher calls `evaluate` on the sleeve's cadence and routes the returned intent dicts (market, day, buy_to_open / sell_to_close) to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- With 200+ completed daily bars and the last close above the SMA200, one rebalance targets ETH at 100% of post-fee NAV.
- With the last close at or below the SMA200 while ETH is held, the rebalance sells the entire ETH holding.
- With fewer than 200 completed bars, no intent is emitted.
- While invested and gated on, a drift adjustment of 0.5% of book value or less produces no intent (deadband enhancement on); with the enhancement off, the same drift is traded.
- Deltas of $0.01 or less produce no intent.
