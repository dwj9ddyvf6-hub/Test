# free_kraken_ada_crowded: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-crowded.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Breakdown short (funding filter); Status 2 live.

## What this sleeve is
This sleeve is the ADA breakdown short with an added crowded-long funding gate: the breakdown must coincide with hourly Kraken funding that is positive and above its 90-day 75th percentile. Sources: sleeves/free_kraken_ada_crowded.py and adapters3/free_kraken_ada_crowded.py on the desk.

## Full algorithm
Evaluation order in sleeves/free_kraken_ada_crowded.py signal() (INSTRUMENT PF_ADAUSD, account free_kraken, BUDGET_USD 100000.0, MAX_EXPOSURE 0.10):

1. Short open: cover the full short at the live ask when now >= entry_due_at + 16h and the quote is valid (bid > 0, bid <= ask); otherwise hold. This exit is identical to the breakdown sleeve.
2. Flat: crowded_decision first runs the breakdown decision exactly as in free_kraken_ada_breakdown (at least 22 completed 4h bars, at least 20 prior bars, signal bar = latest completed bar with entry due at signal open + 8h, signal close strictly below the prior 20 bars' minimum low). If it is not entry_ready, there is no entry.
3. Funding gate: Kraken hourly funding prints (extra funding_rates [{timestamp, fundingRate}], prints after now ignored, malformed prints skipped). At least 30 prints within the last 90 days are required, else WARMING_UP.
4. Freshness enhancement (on by default; context.extra["free_kraken_ada_crowded_improve"]["funding_freshness_gate"]): refuse when the latest print is more than 2 hours old (FUNDING_MAX_AGE 2h).
5. Crowding test: the latest print must be > 0 and strictly above the 90-day 75th percentile, computed as sorted(window)[int(0.75 * (len(window) - 1))].
6. Entry intent, with a valid live quote: short 1 contract at the live bid. One short at a time.

## Files in this repo
- Sleeve module: sleeves/free_kraken_ada_crowded.py (the strategy logic; CONFIG sleeve_id=free_kraken_ada_crowded).
- v3 adapter: adapters3/free_kraken_ada_crowded.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-kraken-crowded.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=free_kraken_ada_crowded).

## Configuration
Module adapters3.free_kraken_ada_crowded; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, kraken, positions]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_ada_crowded.

## Data inputs
Kraken 4h bars for PF_ADAUSD (240Min, warmup 22); hourly funding prints via extra funding_rates from the Kraken producer; live quote via extra quote; sleeve_state {PF_ADAUSD: {qty, entry_due_at}} from position records.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_ada_crowded` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: an entry_ready breakdown plus 30+ funding prints in 90 days with the latest print fresh, positive and above the 75th percentile: one short of 1 at the bid. Fixture B: same breakdown with the latest print 3 hours old: no entry while the freshness gate is on.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
