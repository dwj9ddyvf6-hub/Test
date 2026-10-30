# ema_vwap_options: Recreation package

Provenance: Source row in strategies/femto/femto-ema-vwap-options.md in this repo: Family Femto-lean; Source The old Alpaca swing desk, via Femto-lean; Asset Equity options; Timeframe 1d (hourly checks); Universe 41-name old-desk basket; Style Mean reversion (options); Status live.

## What this sleeve is
This sleeve takes the same 20-day VWAP deviation signal as ema_vwap and expresses it as a call debit spread instead of stock. It buys the spread on the nearest 14 to 30 DTE expiry and manages it with value, DTE, reversion and hold exits. Sources: sleeves/ema_vwap_options.py and adapters3/ema_vwap_options.py on the desk.

## Full algorithm
Evaluation order in sleeves/ema_vwap_options.py signal(), per symbol:

1. Held spread first. exit_due checks, in this order: (a) profit target: conservative live value (long bid - short ask) minus entry debit >= 50% of max profit (PROFIT_TARGET_PCT 0.50, max profit = width - debit); (b) DTE time stop: days to expiry <= 7 (EXIT_DTE 7); (c) VWAP reversion: last close at or above the 20-bar VWAP, subject to the enhancement gate below; (d) max hold: 21 sessions since the entry date (MAX_HOLD_DAYS 21). First trigger wins; the exit intent is for the full spread qty.
2. Enhancement gate (ENH, on by default; context.extra["ema_vwap_options_improve"]["reversion_value_gate"]): the reversion exit (c) fires only when the spread's conservative live value is at or above the entry debit.
3. Entry gate: fewer than 5 open positions (MAX_POSITIONS 5), equity > 0, at least 30 bars (WARMUP_BARS 30), and the same deviation signal as the equity sleeve: at least 21 bars, valid 20-bar rolling VWAP (any zero or missing volume bar in the window makes it None), last close strictly below VWAP * 0.98 (DEV_PCT 0.02).
4. Spread selection (pick_spread / select_debit_spread, pure form): target price = spot * 1.02 (LONG_OTM_PCT 0.02); nearest expiry with 14 <= DTE <= 30 (DTE_MIN 14, DTE_MAX 30); long leg = highest strike <= target (or the lowest strike if none); short leg = first strike >= long strike * 1.06 (WIDTH_PCT 0.06); long-leg liquidity gate (ask - bid) / mid <= 10% when bid > 0 (LIQ_GATE_FRAC 0.10); debit = long ask - short bid must be > 0 and < width (a debit at or above width is refused); no debit/width ratio band (debit_range None).
5. Sizing: contracts = floor(equity * 0.0025 / (debit * 100)) (RISK_FRACTION 0.0025, sized on debit paid); zero contracts skips the entry. Long options are defined-risk: there is no disaster stop.

## Files in this repo
- Sleeve module: sleeves/ema_vwap_options.py (the strategy logic; CONFIG sleeve_id=ema_vwap_options).
- v3 adapter: adapters3/ema_vwap_options.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-ema-vwap-options.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=ema_vwap_options).

## Configuration
Module adapters3.ema_vwap_options; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close true; flatten_time_et 15:55; params {}; inputs [bars, positions, options]; parked false. Source: muse-desk-v3/config/sleeves.json row id=ema_vwap_options.

## Data inputs
Daily bars as for ema_vwap; option chains via context.extra chains {SYM: [{symbol, strike, expiration}]} (calls) and quotes {OCC: {bid, ask}} from the core data door / chain snapshot producer; sleeve_state positions from desk records. The roster inputs are bars, positions and options, and the roster flattens this sleeve by 15:55 ET.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `ema_vwap_options` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): a name meeting the deviation test with a 14 to 30 DTE call chain meeting the strike, liquidity and debit rules produces one call debit spread entry with contracts = floor(equity * 0.0025 / (debit * 100)). Fixture B: the same chain with debit >= width, or long-leg spread over 10% of mid, produces no entry.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
