# free_kraken_ada_basis: Recreation package

Provenance: Source row in strategies/femto/femto-kraken-basis.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean; Asset Crypto spot + perpetual; Timeframe 4h; Universe ADA, LINK (Kraken); Style Basis arbitrage; Status 2 waiting. The v3 module's own header records that its order logic was designed (not ported) under the desk owner's 2026-10-24 ruling, with the constants named in the Full algorithm section.

## What this sleeve is
This sleeve trades the ADA perpetual premium over spot on Kraken: it shorts 1 PF_ADAUSD contract when the newest completed 4-hour basis is at least 25 bps and covers when the basis normalises or 16 hours pass. Note the existing doc describes an older spot-plus-perp package at 2 standard deviations; the v3 module that actually runs is the designed short-only logic below, and a recreation must follow the module. Sources: sleeves/free_kraken_ada_basis.py and adapters3/free_kraken_ada_basis.py on the desk.

## Full algorithm
Evaluation order in sleeves/free_kraken_ada_basis.py signal() (INSTRUMENT PF_ADAUSD, spot ADAUSD):

1. Position state is read from sleeve_state / sleeve_state_flat / slice_state for PF_ADAUSD (qty and entry time). A long qty is never added to; only flat or short states act.
2. Short open: a valid live quote is required (bid > 0 and bid <= ask), else hold. Cover the full short at the ask when the newest completed pair's basis_bps <= 5 (EXIT_BASIS_BPS 5) or now >= entry_time + 16h (HOLD_HOURS 16).
3. Flat entry: the basis book must be READY: extra basis aligned == required and required > 0; the quote must be valid; and basis_decision must return entry_ready.
4. basis_decision: only completed aligned 4h pairs count (pair t + 4h <= now); basis_bps = (perp_close - spot_close) / spot_close * 10000 on the newest completed pair; entry_ready when basis_bps >= 25 (ENTRY_BASIS_BPS 25).
5. Entry intent: short QTY 1 PF_ADAUSD at the live bid (sell_to_open in the reason string). One open position at a time; malformed pairs or quotes fail closed.

## Files in this repo
- Sleeve module: sleeves/free_kraken_ada_basis.py (the strategy logic; CONFIG sleeve_id=free_kraken_ada_basis).
- v3 adapter: adapters3/free_kraken_ada_basis.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-kraken-basis.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=free_kraken_ada_basis).
- For this sleeve adapters3/free_kraken_ada_basis.py applies enhance15.filter_entries (engines/desk3/enhance15.py).

## Configuration
Module adapters3.free_kraken_ada_basis; cadence_s 3600; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [kraken, positions]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_kraken_ada_basis.

## Data inputs
Kraken producer inputs persisted at warm time by runtime/kraken_warm.py into the Kraken inputs store and served via the adapter: extra basis {aligned, required, series of {t, spot_close, perp_close}} (or extra series) and extra quote {bid, ask} for the perpetual; 4h bars for PF_ADAUSD through the bar cache; positions for state. Nothing is fetched during evaluation.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_kraken_ada_basis` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: READY basis (aligned == required > 0), newest completed pair basis 30 bps and a valid quote, flat state: one short entry of 1 PF_ADAUSD at the bid. Fixture B: short open with newest completed basis 4 bps: one cover at the ask; with basis 20 bps and under 16h held: no intent.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
