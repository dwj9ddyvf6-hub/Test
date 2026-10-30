# aster_native_eth_sma200: recreation package

Provenance: Source: Ausar R14/R15 Coinbase research (existing Test doc strategies/ausar/coinbase-sma200.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_batch1.py and the desk config/sleeves.json row for this sleeve id.

## What this sleeve is

A crypto spot trend sleeve that holds ETH-USD only, while each symbol's completed daily close is above its 200-day simple moving average, and holds cash otherwise. It is a thin adapter over the desk3/aster_batch1.py native engine on a $10,000 slice, evaluated once a day.

## Full algorithm

Evaluation order in desk3/aster_batch1.py for the native kind (SPECS weights=(("ETH-USD", 1.0),), cadence_s=86400, session=24h):
1. Gate per symbol: the latest completed daily close is strictly above the inclusive SMA200 (the 200-day simple moving average including that close).
2. Targets: a symbol whose gate is on targets its weight of post-fee NAV; a symbol whose gate is off targets zero. Weights for this sleeve: (("ETH-USD", 1.0),).
3. Rebalance: the fee-funded rebalance (bisection ported in the engine) computes trades to the post-fee targets; sells are emitted before buys. The existing family doc records rebalancing at 00:00-00:05 UTC, once per day, and a 0.2% fee per side with lot floors.
4. Exit: a symbol whose gate turns off is sold in full; there is no other exit, stop, or target.

## Files in this repo

- This doc: docs/ASTER_NATIVE_ETH_SMA200-RECREATE.md
- Sleeve module in Test: sleeves/aster_native_eth_sma200.py
- Adapter in Test: adapters3/aster_native_eth_sma200.py (mirrored as integration/aster_native_eth_sma200_adapter.py)
- Shared engine in Test: desk3/aster_batch1.py (evaluate, SPECS, INPUTS_BY_KIND native = bars, positions; PRODUCERS)
- Config in Test: config/sleeves.json (row id=aster_native_eth_sma200); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/coinbase-sma200.md

## Configuration

- Universe / weights: (("ETH-USD", 1.0),) (crypto spot, Coinbase symbols as written in the engine SPECS).
- Timeframe: 1d; SMA period 200 sessions.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); targets are the weights above applied to post-fee NAV.
- Cadence: cadence_s 86400. Session: 24h. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: bars, positions.
- Parked: false (parked flag in the desk config row).

## Data inputs

Producers declared by desk3/aster_batch1.py PRODUCERS for the native kind:
- bars (producer name: bars): daily bars, at least 200 completed sessions per symbol for the SMA200; freshness SLA 900 s.
- positions (producer name: broker_readback): freshness SLA 900 s.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. With every weighted symbol's latest completed daily close strictly above its SMA200 and a flat book, evaluate returns buys reaching the weights (("ETH-USD", 1.0),) of post-fee NAV, sells (none) before buys.
2. With a held symbol's latest completed daily close at or below its SMA200, evaluate returns a full sell of that symbol and no buy for it.
3. With fewer than 200 completed daily bars for a symbol, no SMA200 gate can pass for that symbol and no entry is produced for it.
4. On a day when all targets already match current holdings, evaluate returns no intents.
