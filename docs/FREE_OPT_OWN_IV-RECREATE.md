# free_opt_own_iv: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-own-iv.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean; Asset ETF options; Timeframe 1d (5-minute passes); Universe SPY (SPY / QQQ for the pair); Style Volatility; Status waiting.

## What this sleeve is
This sleeve buys a producer-supplied at-the-money straddle package (one call and one put, always together) when the package's realized-volatility forecast beats its implied volatility by at least 2 points. The package selection (expiry, strikes, forecast) is done by the producer; this module validates freshness, skew and the forecast gate, then holds the package for 10 sessions or to expiry. Sources: desk3/strategies/free_opt_own_iv.py and desk3/sleeves/free_opt_own_iv.py on the desk. The existing doc's 21 to 35 DTE and 760-close details describe the producer side, not checks in this module.

## Full algorithm
Evaluation order in desk3/strategies/free_opt_own_iv.py signal() (account free_options, BUDGET_USD 100000.0 pool):

1. Exits first (_exit_intents): held legs are grouped by entry date; a group exits together when sessions since entry >= 10 (dates strictly after the entry date, from extra session_dates) or the session is at or past the earliest leg expiry parsed from the OCC symbols. Before expiry, every held leg needs a two-sided quote in extra quotes (ask > 0, bid >= 0, ask >= bid) or the group is retained; at or past expiry that gate is bypassed. Long legs exit sell_to_close at the bid, short legs buy_to_close at the ask.
2. One package per session: if any held record was entered this session, or last_exit_date equals this session, no new entry is evaluated.
3. Freshness gate on extra quote: source age at most 90 seconds (SOURCE_MAX_SECONDS 90), receipt age at most 30 seconds (RECEIPT_MAX_SECONDS 30), future tolerance 2 seconds, receipt not earlier than source, and a non-crossed positive quote (ap >= bp > 0).
4. Package shape (straddle_legs): extra package must carry exactly 2 legs with rights {call, put} and pass package_skew: consecutive leg source stamps at most 30 seconds apart (SKEW_MAX_SECONDS 30), with source stamps present.
5. Enhancement gate (on by default; context.extra["free_opt_own_iv_improve"]["forecast_iv_gate"]): the package must carry forecast and iv values (aliases forecast_vol / implied_iv) with forecast - iv >= 2.0 points (FORECAST_IV_MIN_SPREAD 2.0); missing or unparseable values fail closed.
6. Leg tradability: every leg needs a symbol, a finite ask > 0, and its own source stamp fresh under the same 90-second / 2-second windows.
7. Entry: one intent per leg, qty 1, buy at the leg ask, each with ExitRule time_bars 10, sharing the reason tag package FREE_OPT_OWN_IV_V1 with the forecast, iv and spread stamped in.

## Files in this repo
- Strategy module: sleeves/free_opt_own_iv.py (repo copy of desk3/strategies/free_opt_own_iv.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_opt_own_iv.py, also copied at integration/free_opt_own_iv_adapter.py.
- Existing strategy doc: strategies/femto/femto-free-opt-own-iv.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py).
- Config: engines/config/sleeves.json (row id=free_opt_own_iv).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_opt_own_iv; strategy_module desk3.strategies.free_opt_own_iv; cadence_s 300; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [options]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_opt_own_iv.

## Data inputs
The options producer supplies extra package {legs (2, with symbol, right, ask, source_at), forecast, iv}, the freshness quote via extra quote {t or source_at, received_at, ap, bp}, and for exits extra quotes and session_dates; sleeve_state held records from the desk. The snapshot options input is the roster input for this sleeve.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_opt_own_iv` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: a fresh quote, a 2-leg call+put package with stamps within 30s and forecast - iv = 2.5: two entry intents of qty 1, one per leg, each with time_bars 10. Fixture B: forecast - iv = 1.0, or a package with only a call leg: no entry. Fixture C: a held group at 10 sessions with two-sided quotes: both legs exit together.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
