# fear_premium: Recreation package

Provenance: Source row in strategies/femto/femto-fear-premium.md in this repo: Family Femto-lean; Source The old Alpaca swing desk, via Femto-lean; Asset Equity options; Timeframe 1d (hourly checks); Universe SOXL, TQQQ + the 10 highest-beta basket names; Style Premium selling; Status live.

## What this sleeve is
This sleeve sells a put credit spread after a sharp red day on a high-beta name, collecting premium when fear is elevated. Its universe is re-ranked weekly by 60-day beta to QQQ, with SOXL and TQQQ always included. Sources: sleeves/fear_premium.py and adapters3/fear_premium.py on the desk. Note: the existing doc also lists an earnings-calendar entry condition; the v3 sleeve module read for this package contains no earnings check, so a faithful recreation follows the module (no earnings gate in the code).

## Full algorithm
Evaluation order in sleeves/fear_premium.py signal():

1. Universe: extra universe override, else rank_universe(bars): 60-day beta (BETA_LOOKBACK_DAYS 60) of each name's daily returns against QQQ, top 10 by beta (UNIVERSE_BETA_COUNT 10), plus SOXL and TQQQ always (ALWAYS_INCLUDE), deduped in that order. Exits are evaluated for held names even if they have rotated out of the ranking; entries only for ranked names.
2. Held spread exits, in exit_due order: (a) profit target: entry credit - conservative close cost (short ask - long bid) >= 50% of entry credit (PROFIT_TARGET_FRAC 0.50); (b) time exit: 8 sessions since entry (TIME_EXIT_DAYS 8), subject to the enhancement gate below; (c) DTE floor: days to expiry <= 21 (DTE_FLOOR 21). First trigger wins, full qty.
3. Enhancement gate (ENH, on by default; context.extra["fear_premium_improve"]["time_exit_profit_gate"]): the 8-session time exit fires only when the close cost is at or above the entry credit (flat to losing); an unpriceable spread keeps the ungated rule.
4. Entry signal (detect_red_day): last completed daily bar down at least 5% (RED_DAY_THRESHOLD -0.05, day_pct <= -0.05) and Wilder RSI(14) < 50 (RSI_PERIOD 14, RSI_CEILING 50.0); needs at least 16 bars.
5. Entry gates: fewer than 5 open positions (MAX_POSITIONS 5), equity > 0.
6. Spread selection (select_spread_legs): puts only, at least 2 strikes; strike grid = smallest gap between listed strikes; short strike = strike nearest spot * 0.93 (SHORT_OTM_PCT 0.07 below the red-day close); width = max(grid, round(spot * 0.10 / grid) * grid) (WIDTH_PCT 0.10); long strike = strike nearest short - width, strictly below the short strike, same expiry (with the module's same-expiry fallback); expiry DTE accepted within 21 to 39 (DTE_MIN 25, DTE_MAX 35, selector tolerance plus/minus 4 days).
7. Quote and economics gates (validate_spread_quotes): both legs two-sided; per-leg (ask - bid) / mid <= 10% (SPREAD_GATE_FRAC 0.10); credit = short bid - long ask > 0 and credit >= 3% of capital at risk per share, where capital at risk = (width - credit) * 100 (MIN_CREDIT_FRAC 0.03).
8. Sizing: contracts = min(floor(equity * 0.005 / capital_at_risk), floor(equity * 0.25 / (short_strike * 100))) (RISK_FRACTION 0.005, SLEEVE_NOTIONAL_CAP 0.25); zero skips the entry.

## Files in this repo
- Sleeve module: sleeves/fear_premium.py (the strategy logic; CONFIG sleeve_id=fear_premium).
- v3 adapter: adapters3/fear_premium.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-fear-premium.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=fear_premium).

## Configuration
Module adapters3.fear_premium; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, positions, options]; parked false. Source: muse-desk-v3/config/sleeves.json row id=fear_premium.

## Data inputs
Daily bars for the basket plus QQQ (the v2 adapter requests 1Day bars; the existing doc lists split-adjusted daily bars, 90); put chains via context.extra chains and quotes {OCC: {bid, ask}} from the chain snapshot producer; sleeve_state positions from desk records. QQQ bars must be present or beta ranking yields no ranked names beyond the always-included pair.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `fear_premium` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): a ranked name with a last day at or below -5%, RSI(14) under 50, and a put chain passing the strike, quote and credit gates produces one put credit spread sized by the 0.5% risk and 25% notional formulas. Fixture B: the same signal with credit below 3% of capital at risk produces no entry.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
