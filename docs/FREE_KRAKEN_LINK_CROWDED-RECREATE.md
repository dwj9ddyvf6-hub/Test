# free_kraken_link_crowded: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-crowded.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Breakdown short (funding filter); Status 2 live.

## What this sleeve is
This is the LINK crowded-long failure short: the LINK breakdown signal plus a gate requiring hourly Kraken funding to be positive and above its 90-day 75th percentile. Sources: desk3/strategies/free_kraken_link_crowded.py and desk3/sleeves/free_kraken_link_crowded.py on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_kraken_link_crowded.py signal() (INSTRUMENT PF_LINKUSD, account free_kraken, BUDGET_USD 100000.0, MAX_EXPOSURE 0.10):

1. Short open: cover the full short at the live ask when now >= entry_due_at + 16h and the quote is valid (bid > 0, bid <= ask); otherwise hold.
2. Flat: crowded_decision runs the breakdown decision exactly as in free_kraken_link_breakdown (22 completed 4h bars, 20 prior bars, signal bar = latest completed bar with entry due at signal open + 8h, close strictly below the prior 20 bars' minimum low). Not entry_ready means no entry.
3. Funding gate: hourly funding prints (extra funding_rates [{timestamp, fundingRate}]); at least 30 prints within 90 days required, else WARMING_UP; malformed prints are skipped.
4. Freshness enhancement (on by default; context.extra["free_kraken_link_crowded_improve"]["funding_freshness_gate"]): refuse when the latest print is more than 2 hours old (FUNDING_MAX_AGE 2h).
5. Crowding test: latest print > 0 and strictly above sorted(window)[int(0.75 * (len(window) - 1))] over the 90-day window.
6. Entry intent, with a valid live quote: short 1 contract at the live bid. One short at a time.

## Files in this repo
- Strategy module: sleeves/free_kraken_link_crowded.py (repo copy of desk3/strategies/free_kraken_link_crowded.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_kraken_link_crowded.py, also copied at integration/free_kraken_link_crowded_adapter.py.
- Existing strategy doc: strategies/femto/femto-kraken-crowded.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py).
- Config: engines/config/sleeves.json (row id=free_kraken_link_crowded).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_kraken_link_crowded; strategy_module desk3.strategies.free_kraken_link_crowded; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, kraken.quote, kraken.funding]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_link_crowded.

## Data inputs
Kraken 4h bars for PF_LINKUSD (adapter reads 4Hour, 500); funding via the snapshot's kraken.funding map for PF_LINKUSD, which the adapter converts to extra funding_rates; live quote via extra quote (adapter fallback: the LINK basis sleeve's Kraken inputs quote); sleeve_state from position records.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_link_crowded` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: entry_ready breakdown plus 30+ fresh funding prints with the latest positive and above the 75th percentile: one short of 1 at the bid. Fixture B: same breakdown with the latest print 3 hours old: no entry while the freshness gate is on.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
