# free_kraken_enj_spot: Recreation package

Provenance: Source row in strategies/femto/femto-free-kraken-enj-spot.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) ENJ spot row; order logic designed for the v3 desk; Asset Crypto spot; Timeframe 1h checks; Universe ENJ/USD (Kraken); Style Order-book imbalance; Status desk only (the module header records the order logic was designed under the desk owner's 2026-10-24 ruling, with the constants named below).

## What this sleeve is
This sleeve buys ENJ spot on Kraken when the top-10 order book is tight and bid-heavy, and sells on a depth flip, a spread blowout or after 24 hours. There is no ENJ perpetual on the checked Kraken list, so this is a spot-only book. Sources: desk3/strategies/free_kraken_enj_spot.py (strategy) and desk3/sleeves/free_kraken_enj_spot.py (adapter) on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_kraken_enj_spot.py signal() (INSTRUMENT ENJUSD):

1. Book metrics from extra book (Kraken depth): top 10 levels per side (DEPTH_LEVELS 10); depth = sum of sizes over those levels; mid = (best bid + best ask) / 2; spread_bps = (ask - bid) / mid * 10000. An empty, malformed or crossed book (ask < bid, or a nonpositive best price) is not ok and no priced action is taken.
2. Long open (qty > 0): exit the full qty at the bid when any of: ask_depth >= 2.0 * bid_depth (IMBALANCE_RATIO 2.0, depth flip); spread_bps > 200 (EXIT_SPREAD_BPS 200); or held >= 24h (HOLD_HOURS 24, entry time from entry_due_at / opened_at). Every exit requires a valid non-crossed book with bid > 0. A short qty is ignored.
3. Flat: enj_status must be QUALIFIED/AWAITING SIGNAL (a live, non-crossed book) and enj_decision entry_ready: spread_bps <= 50 (SPREAD_MAX_BPS 50) and bid_depth >= 2.0 * ask_depth, with ask > 0.
4. Sizing: qty = floor(min(slice equity, 10000) / ask); below 1 there is no intent. Entry intent: buy ENJUSD at the ask. One open position at a time.

## Files in this repo
- Strategy module: sleeves/free_kraken_enj_spot.py (repo copy of desk3/strategies/free_kraken_enj_spot.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_kraken_enj_spot.py, also copied at integration/free_kraken_enj_spot_adapter.py.
- Existing strategy doc: strategies/femto/femto-free-kraken-enj-spot.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py, ViewCtx) and engines/desk3/enhance15.py (desk3/enhance15.py, filter_entries applied by the adapter).
- Config: engines/config/sleeves.json (row id=free_kraken_enj_spot).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_kraken_enj_spot; strategy_module desk3.strategies.free_kraken_enj_spot; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [kraken.book, bars]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_enj_spot.

## Data inputs
Kraken ENJUSD depth book (top levels per side) produced at warm time by runtime/kraken_warm.py and injected by the adapter from the Kraken inputs store (params extra book takes precedence); ENJUSD bars (240Min, 10 requested) through the snapshot for state context; sleeve_state from position records. Nothing is fetched during evaluation.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_enj_spot` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: a book with spread 40 bps and top-10 bid depth 2.5x ask depth, flat state: one buy of floor(min(equity, 10000) / ask) at the ask. Fixture B: long open with ask depth 2x bid depth: one exit of the full qty at the bid; long open with an empty book: no exit.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
