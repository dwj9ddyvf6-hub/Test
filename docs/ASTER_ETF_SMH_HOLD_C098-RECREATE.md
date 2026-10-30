# aster_etf_smh_hold_c098: recreation package

Provenance: Source: Ausar R17/R18 ETF research, frozen as the R19 ETF books (existing Test doc strategies/ausar/r19-etf.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_etf.py (SPY sleeves: the ETF_SPECS entry in desk3/aster_batch11.py, which registers into desk3/aster_etf.py SPECS) and the desk config/sleeves.json row for this sleeve id.

## What this sleeve is

An Aster R19 ETF control book that holds {"SMH": 1.0} under policy SMH_HOLD at gross 0.98, rebalanced never after the initial buy (buy and hold). It runs on the shared desk3/aster_etf.py engine as a thin adapter sleeve on a $10,000 slice. It is one of the fixed-weight ETF books that run beside the momentum leader rotation as controls.

## Full algorithm

This is a BUY_HOLD sleeve: it acts only on initial allocation (flat book). Buy-and-hold sleeves never rebalance and never exit by design. Evaluation order in desk3/aster_etf.py evaluate(): (1) read this sleeve's SPECS entry; (2) check the time gate: entry only 09:35-09:40 ET (aware timestamps are converted to America/New_York; naive stamps are read as ET); (3) if the book already holds the target, emit nothing; (4) otherwise emit buys for the target weights.
- Policy: SMH_HOLD. Frequency: BUY_HOLD. Gross: 0.98. Weights: {"SMH": 1.0}.
- Target sizing: whole shares, floor(weight x gross x equity / price) per symbol, where equity is the sleeve slice; sells are emitted before buys.
- No price stop and no profit target. The 15 bps per side figure (cost_bps 15) is source-book accounting, not an order field.
- Exit rules: none: buy-and-hold sleeves never sell by design.

## Files in this repo

- This doc: docs/ASTER_ETF_SMH_HOLD_C098-RECREATE.md
- Sleeve module in Test: sleeves/aster_etf_smh_hold_c098.py
- Adapter in Test: adapters3/aster_etf_smh_hold_c098.py (mirrored as integration/aster_etf_smh_hold_c098_adapter.py)
- Shared engine in Test: desk3/aster_etf.py (evaluate, SPECS, INPUTS, PRODUCERS)
- Config in Test: config/sleeves.json (row id=aster_etf_smh_hold_c098); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/r19-etf.md

## Configuration

- Universe / weights: {"SMH": 1.0} (policy SMH_HOLD).
- Timeframe: 1d bars; rebalance frequency BUY_HOLD.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); target shares = floor(weight x gross x equity / price), gross 0.98.
- Cadence: cadence_s 300. Session: rth. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: bars, positions, quotes.
- Parked: false (parked flag in the desk config row).

## Data inputs

Producers declared by desk3/aster_etf.py PRODUCERS, consumed through the runtime view:
- bars (producer name: bars): daily bars keyed as `<SYM>|1Day`, `<SYM>|1D`, or `<SYM>`; freshness SLA 900 s. Absent bars means no intents (unfed upstream).
- positions (producer name: broker_readback): current holdings for this sleeve; freshness SLA 900 s.
- quotes (producer name: quotes): freshness SLA 60 s.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. Outside 09:35-09:40 ET, with no monthly rebalance due under the catch-up rule, evaluate returns no intents.
2. With a flat book in the 09:35-09:40 ET window, evaluate returns a buy targeting floor(1.0 x 0.98 x equity / price) whole SMH shares.
3. With SMH already held at target, evaluate returns no intents on every later session (no rebalance, no exit).
4. With bars absent for a target symbol, evaluate returns no intents for that symbol (unfed, not an error fill).
5. Sells are emitted before buys in the same evaluation, quantities are whole shares, and no price stop or target is attached to any intent.
