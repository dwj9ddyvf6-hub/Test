# free_opt_parity: Recreation package

Provenance: Source row in strategies/femto/femto-free-opt-parity.md in this repo: Family Femto-lean; Source Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean; Asset ETF options; Timeframe 1d (5-minute passes); Universe SPY (SPY / QQQ for the pair); Style Arbitrage; Status waiting. That doc's Notes record that the v3 desk expresses parity as a SPY box spread instead of the original conversion / reversal, with entry edge $0.30 a share, exit $0.05 and 1 box; the module header records the box logic was designed under the desk owner's 2026-10-24 ruling.

## What this sleeve is
This sleeve trades SPY box spreads as a pure put-call parity instrument: a box has a locked payout equal to its strike width at expiry, so a box priced at least $0.30 per share away from its width is a parity edge. It holds at most one box and unwinds it when nearly all the locked value is capturable or at expiry. Sources: desk3/strategies/free_opt_parity.py and desk3/sleeves/free_opt_parity.py on the desk.

## Full algorithm
Evaluation order in desk3/strategies/free_opt_parity.py signal() (UNDERLYING SPY; the whole signal is wrapped to fail closed and never raise):

1. Quote normalisation (_normalize_quotes): extra parity_quotes (a list of {symbol, expiration, strike, right, bid, ask} rows, or an OCC-keyed dict; OCC parsing fills missing fields) is grouped by (expiry, strike), keeping only strikes where both the call and the put have valid non-crossed quotes (bid > 0, ask >= bid).
2. Open box first: the one open box is reconstructed from held OCC positions in sleeve_state / positions / slice_state: four legs at one expiry, strikes K1 < K2, equal absolute quantities, with sign pattern (+call K1, -put K1, -call K2, +put K2) for a long box or the mirror for a short box.
3. Open-box exit (parity_decision with the position): exit when today is on or after the expiry date (even when leg quotes are missing, as a market unwind), or when the executable unwind value >= width - 0.05 per share (EXIT_EDGE 0.05; unwind = short-box credit for a long box, width - long-box debit for a short box). A missing leg quote before expiry blocks the exit (hold). The exit is one intent unwinding all 4 legs (each qty equal to the box qty) with the package_id spy-box-<expiry>-<K1>-<K2>-<direction>.
4. Flat scan: expiries at least 7 DTE only (MIN_DTE 7); SPY spot (extra parity_spot) must be present and positive. For every strike pair K1 < K2 at one expiry with width = K2 - K1 <= 5.0 (MAX_WIDTH 5.0): long-box executable debit per share = C(K1).ask - P(K1).bid - C(K2).bid + P(K2).ask, long edge = width - debit; short-box executable credit = C(K1).bid - P(K1).ask - C(K2).ask + P(K2).bid, short edge = credit - width. The pair with the largest edge is taken.
5. Entry: best edge >= 0.30 per share (ENTRY_EDGE 0.30) produces ONE entry intent carrying 4 legs, each QTY 1: a long box buys C(K1), sells P(K1), sells C(K2), buys P(K2) at the executable debit as the limit; a short box is the mirror at the executable credit. One open position at a time.
6. Adapter addition (desk3/sleeves/free_opt_parity.py): the adapter fills parity_quotes from the snapshot SPY options chain and parity_spot from the newest SPY close (1Day, then 1Hour bars), expands the package intent into one intent dict per leg, and applies the enh2_edge16 filter_parity_max_dte filter refusing boxes expiring more than 60 DTE out.

## Files in this repo
- Strategy module: sleeves/free_opt_parity.py (repo copy of desk3/strategies/free_opt_parity.py; the strategy logic).
- v3 adapter: desk3/sleeves/free_opt_parity.py, also copied at integration/free_opt_parity_adapter.py.
- Existing strategy doc: strategies/femto/femto-free-opt-parity.md.
- Shared engine files: engines/desk3/bridge.py (desk3/bridge.py) and engines/desk3/enh2_edge16.py (desk3/enh2_edge16.py).
- Config: engines/config/sleeves.json (row id=free_opt_parity).
- Note: desk3/contract.py (the BaseSleeve, Intent and SleeveConfig definitions the strategy imports) is recorded in engines_map.json as gate_blocked for engines/desk3/contract.py, so that one shared file is not present in this repo; a recreation must supply the same contract definitions from a fresh desk.

## Configuration
Module desk3.sleeves.free_opt_parity; strategy_module desk3.strategies.free_opt_parity; cadence_s 300; session 24h; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [options.chain, bars]; parked false. Source: muse-desk-v3/config/sleeves.json row id=free_opt_parity.

## Data inputs
SPY options chain quotes produced at warm time by runtime/options_warm.py and injected by the adapter from the snapshot options chain (extra parity_quotes), plus the newest SPY close from the bar cache (extra parity_spot); held OCC positions from sleeve_state / positions for box reconstruction. Note: the existing doc's FRED T-bill financing and share-leg inputs describe the original model, not this module, which needs only chain quotes and spot.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `free_opt_parity` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A: a chain with a width-5 box whose long debit is 4.60 (edge 0.40): one entry intent with 4 legs, qty 1 each, limit 4.60 and the spy-box package id. Fixture B: best edge 0.20: no entry. Fixture C: that box held with unwind value 4.96 (>= 5 - 0.05): one 4-leg exit intent; held with unwind 4.80 before expiry: no exit.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
