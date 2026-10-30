# free_kraken_link_breakdown: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-breakdown.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Breakdown short; Status 2 live.

## What this sleeve is
This is the LINK twin of the ADA breakdown sleeve: it shorts PF_LINKUSD after a 4-hour close breaks below the prior 20 bars' lows, entering two bars after the signal opened and covering 16 hours after the entry was due. Sources: desk3/strategies/free_kraken_link_breakdown.py and desk3/sleeves/free_kraken_link_breakdown.py on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_kraken_link_breakdown.py signal() (INSTRUMENT PF_LINKUSD, account free_kraken, BUDGET_USD 100000.0, MAX_EXPOSURE 0.10):

1. Short open (qty < 0): cover the full short at the live ask when now >= entry_due_at + 16h (HOLD) and the quote is valid (bid > 0, bid <= ask); otherwise hold.
2. Flat: breakdown_decision on completed 4h bars only; at least 22 completed bars and at least 20 bars before the signal bar are required, else WARMING_UP.
3. Signal bar: the latest completed bar whose entry is due (entry due = signal open + 8h, open(i+2)); it fires when the signal close is strictly below the minimum low of the prior 20 bars.
4. Entry requires a valid live quote. Enhancement gate (on by default; context.extra["free_kraken_link_breakdown_improve"]["breakdown_validity_gate"]): refuse when the live bid >= the prior 20-bar low; a paired record is appended on every entry_ready decision.
5. Entry intent: short 1 contract at the live bid. One short at a time.

## Files in this repo
- Strategy module: sleeves/free_kraken_link_breakdown.py (repo copy of desk3/strategies/free_kraken_link_breakdown.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_kraken_link_breakdown.py, also copied at integration/free_kraken_link_breakdown_adapter.py.
- Existing strategy doc: strategies/femto/femto-kraken-breakdown.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py).
- Config: engines/config/sleeves.json (row id=free_kraken_link_breakdown).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_kraken_link_breakdown; strategy_module desk3.strategies.free_kraken_link_breakdown; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, kraken.quote]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_link_breakdown.

## Data inputs
Kraken 4h bars for PF_LINKUSD (the adapter reads 4Hour bars, 500, through old_bars); live quote via extra quote, which the adapter takes from the LINK basis sleeve's Kraken inputs entry when not supplied directly; sleeve_state {PF_LINKUSD: {qty, entry_due_at}} from position records.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_link_breakdown` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: 22+ completed 4h bars, latest due signal close below the prior 20 lows, live bid below that low: one short of 1 at the bid. Fixture B: same bars with live bid at or above the prior 20 low: no entry while the validity gate is on.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
