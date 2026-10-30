# free_kraken_ada_breakdown: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-breakdown.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Breakdown short; Status 2 live.

## What this sleeve is
This sleeve shorts the ADA perpetual on Kraken after a 4-hour close breaks below the prior 20 bars' lows, entering two bars after the signal bar opened and covering 16 hours after the entry was due. Sources: sleeves/free_kraken_ada_breakdown.py and adapters3/free_kraken_ada_breakdown.py on the desk.

## Full algorithm
Evaluation order in sleeves/free_kraken_ada_breakdown.py signal() (INSTRUMENT PF_ADAUSD, account free_kraken, BUDGET_USD 100000.0, MAX_EXPOSURE 0.10):

1. Short open (sleeve_state PF_ADAUSD qty < 0): cover the full short at the live ask when now >= entry_due_at + 16h (HOLD) and the quote is valid (bid > 0, bid <= ask); otherwise hold.
2. Flat: breakdown_decision on completed 4h bars only. Warmup: at least 22 completed bars and at least 20 bars before the signal bar, else WARMING_UP.
3. Signal bar: the latest completed bar whose entry is due, where entry due = signal open + 8h (ENTRY_SHIFT, that is open(i+2)). It fires when the signal close is strictly below the minimum low of the prior 20 bars.
4. Entry requires a valid live quote. Enhancement gate (on by default; context.extra["free_kraken_ada_breakdown_improve"]["breakdown_validity_gate"]): refuse the short when the live bid >= the prior 20-bar low (the breakdown has already failed); a paired control/treatment record is appended on every entry_ready decision.
5. Entry intent: short 1 contract at the live bid. One short at a time.

## Files in this repo
- Sleeve module: sleeves/free_kraken_ada_breakdown.py (the strategy logic; CONFIG sleeve_id=free_kraken_ada_breakdown).
- v3 adapter: adapters3/free_kraken_ada_breakdown.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-kraken-breakdown.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=free_kraken_ada_breakdown).

## Configuration
Module adapters3.free_kraken_ada_breakdown; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, kraken, positions]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_ada_breakdown.

## Data inputs
Kraken 4h bars for PF_ADAUSD (240Min, the v2 adapter requests 400, warmup 22) through the bar cache; live quote via extra quote {bid, ask} from the warm-time Kraken inputs; sleeve_state {PF_ADAUSD: {qty, entry_due_at}} from position records.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_ada_breakdown` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: 22+ completed 4h bars, latest due signal close below the prior 20 lows, live bid below that low: one short of 1 at the bid. Fixture B: same bars with live bid at or above the prior 20 low: no entry while the validity gate is on.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
