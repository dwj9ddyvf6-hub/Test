# free_opt_pair: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-pair.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean; Asset ETF options; Timeframe 1d (5-minute passes); Universe SPY (SPY / QQQ for the pair); Style Relative value; Status waiting.

## What this sleeve is
This sleeve trades a producer-supplied two-leg cross-underlying options package (the existing doc describes the SPY / QQQ residual pair behind it) only after a hedge ratio has been frozen from prior closes. The residual, beta and strike selection are producer-side; this module validates the frozen package, sizes the second leg from the frozen ratio, and holds the package for 10 sessions or to expiry. Sources: desk3/strategies/free_opt_pair.py and desk3/sleeves/free_opt_pair.py on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_opt_pair.py signal() (account free_options, BUDGET_USD 100000.0 pool):

1. Exits first (_exit_intents): held legs grouped by entry date exit together at 10 sessions since entry (extra session_dates, dates strictly after entry) or at or past the earliest leg expiry; before expiry every leg needs a two-sided quote in extra quotes or the group is retained; at or past expiry that gate is bypassed. Long legs sell_to_close at the bid, short legs buy_to_close at the ask.
2. One package per session, as in free_opt_own_iv: a package entered or exited this session blocks a new entry.
3. Freshness gate on extra quote: source age at most 90 seconds, receipt age at most 30 seconds, future tolerance 2 seconds, non-crossed positive quote (ap >= bp > 0).
4. Package shape (pair_legs): extra package must carry exactly 2 legs with 2 distinct underlyings, hedge_frozen true, and a hedge value present; otherwise no entry.
5. Leg tradability: every leg needs a symbol and a finite ask > 0.
6. Enhancement hedge sizing (on by default; context.extra["free_opt_pair_improve"]["hedge_sizing"]): the hedge ratio is read from package hedge as a scalar or a mapping's ratio / hedge_ratio / value field; second-leg qty = round-half-up of the absolute ratio (floor(|ratio| + 0.5)); a result of 0 (ratio below 0.5, or an unreadable ratio with the gate on) refuses the package. With the gate off, both legs are qty 1.
7. Declared leg direction: a leg's side / position_intent is passed through when declared; a contradictory pair (side buy with sell_to_open, or the reverse) fails closed and no intents at all are returned.
8. Entry: one intent per leg (first leg qty 1, second leg qty as sized), at the leg ask, each with ExitRule time_bars 10 and the reason tag package FREE_OPT_PAIR_V1. The adapter then applies the enh2_edge16 package expiry-coherence filter (engines/desk3/enh2_edge16.py): packages whose legs expire on different dates are refused.

## Files in this repo
- Strategy module: sleeves/free_opt_pair.py (repo copy of desk3/strategies/free_opt_pair.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_opt_pair.py, also copied at integration/free_opt_pair_adapter.py.
- Existing strategy doc: strategies/femto/femto-free-opt-pair.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py) and engines/desk3/enh2_edge16.py (desk3/enh2_edge16.py).
- Config: engines/config/sleeves.json (row id=free_opt_pair).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_opt_pair; strategy_module desk3.strategies.free_opt_pair; cadence_s 300; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [options]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_opt_pair.

## Data inputs
The options producer supplies extra package {legs (2, distinct underlyings, with symbol, ask, optional side / position_intent), hedge, hedge_frozen}, the freshness quote via extra quote, and for exits extra quotes and session_dates; sleeve_state held records from the desk.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_opt_pair` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: a fresh quote and a frozen 2-leg package with hedge ratio 1.6: entries of qty 1 and qty 2 at the leg asks, each time_bars 10. Fixture B: hedge ratio 0.4 with the sizing gate on, hedge_frozen false, or legs expiring on different dates at the adapter filter: no entry.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
