# free_kraken_link_basis: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-basis.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto spot + perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Basis arbitrage; Status 2 waiting. The v3 module's own header records that its order logic was designed (not ported) under the desk owner's 2026-10-24 ruling, with the constants named in the Full algorithm section.

## What this sleeve is
This is the LINK twin of the ADA basis sleeve: it shorts 1 PF_LINKUSD contract when the newest completed 4-hour perpetual-over-spot basis is at least 25 bps and covers on normalisation or after 16 hours. The existing doc's older spot-plus-perp package description does not describe the v3 module; a recreation follows the module below. Sources: desk3/strategies/free_kraken_link_basis.py and desk3/sleeves/free_kraken_link_basis.py on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_kraken_link_basis.py signal() (INSTRUMENT PF_LINKUSD, spot LINKUSD):

1. Position state from sleeve_state / sleeve_state_flat / slice_state for PF_LINKUSD. A long qty is never added to.
2. Short open: a valid live quote is required (bid > 0, bid <= ask), else hold. Cover the full short at the ask when the newest completed pair's basis_bps <= 5 (EXIT_BASIS_BPS 5) or now >= entry_time + 16h (HOLD_HOURS 16).
3. Flat entry: extra basis must be READY (aligned == required, required > 0), the quote valid, and basis_decision entry_ready.
4. basis_decision: only completed aligned 4h pairs (pair t + 4h <= now); basis_bps = (perp_close - spot_close) / spot_close * 10000 on the newest completed pair; entry_ready at basis_bps >= 25 (ENTRY_BASIS_BPS 25).
5. Entry intent: short QTY 1 PF_LINKUSD at the live bid. One open position at a time; malformed inputs fail closed.

## Files in this repo
- Strategy module: sleeves/free_kraken_link_basis.py (repo copy of desk3/strategies/free_kraken_link_basis.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_kraken_link_basis.py, also copied at integration/free_kraken_link_basis_adapter.py.
- Existing strategy doc: strategies/femto/femto-kraken-basis.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py) and engines/desk3/enhance15.py (desk3/enhance15.py, filter_entries applied by the adapter).
- Config: engines/config/sleeves.json (row id=free_kraken_link_basis).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_kraken_link_basis; strategy_module desk3.strategies.free_kraken_link_basis; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [kraken.basis, kraken.quote]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_link_basis.

## Data inputs
Kraken warm-time producer inputs via the adapter's Kraken inputs store: extra basis {aligned, required, series of {t, spot_close, perp_close}} (or extra series) and extra quote {bid, ask}; positions for state. Nothing is fetched during evaluation.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_link_basis` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: READY basis, newest completed pair basis 30 bps, valid quote, flat: one short of 1 PF_LINKUSD at the bid. Fixture B: short open, newest completed basis 4 bps: one cover at the ask.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
