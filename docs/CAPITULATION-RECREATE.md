# capitulation: Recreation package

Provenance: Source row in strategies/femto/femto-capitulation.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset US equities, timeframe 1h with 1d filters, universe 41-name old-desk basket, style mean reversion).

## What this sleeve is
This sleeve buys the first green hourly bar after an RSI(14) washout below 20 on climax volume into the daily 200-day EMA, half size first and the rest when the daily 5/20 EMAs turn up. Exits are the session VWAP, +5 percent, -8 percent or 3 trading days, with a 25 percent disaster stop carried as exit-rule data. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/capitulation.py signal(bars, slice_state, context).

## Full algorithm
Constants (sleeves/capitulation.py): RSI_PERIOD = 14, RSI_OVERSOLD = 20, VOL_CLIMAX_MULT = 2.0, VOL_LOOKBACK = 20, EMA200_PERIOD = 200, EMA_TOLERANCE = 0.02, ATR_PCT_FILTER = 0.05, ATR_PERIOD = 14, PROFIT_TARGET = 0.05, STOP_LOSS = 0.08, HOLD_DAYS = 3, DISASTER_STOP = 0.25, RISK_FRACTION = 0.0025, MAX_POSITIONS = 5, SLEEVE_NOTIONAL_CAP = 0.25, DAILY_BARS_LIMIT = 260, TRANCHE1_FRACTION = 0.5, TRANCHE2_MAX_WAIT = 5, TURN_FAST = 5, TURN_SLOW = 20, BLACKOUT_DAYS_BEFORE = 3 (pre-earnings veto). CONFIG: cadence_s 300, universe (), risk_pct RISK_FRACTION. Closed 1-hour regular-hours bars only.

Signal (detect_capitulation), all parts required, in code order:
1. A climax bar whose 1-hour RSI(14) is below 20 and whose volume is greater than 2.0 x the mean volume of the 20 bars BEFORE it.
2. The climax bar's low is within 2 percent of the daily 200-day EMA (EMA_TOLERANCE = 0.02; the 5 percent shadow band is telemetry only, never an entry).
3. The signal bar is the first green 1-hour bar after the climax with RSI turning up.
4. Choppiness filter: daily ATR(14) / close greater than 5 percent (atr_filter_ok, over the 260 daily bars).

Entries, in code order:
1. Fear gate: entries defer unless the desk composite is FEAR+; core supplies extra["fear_ok"], produced from the desk mood ring, and absence fails closed in the lean port. The earnings veto refuses entries within BLACKOUT_DAYS_BEFORE = 3 days before earnings.
2. Enhancement (ENH-CAPITULATION-20261024, on by default; switch extra["capitulation_improve"] {"vwap_refusal": bool}): tranche 1 is refused when the entry close is already at or above the session VWAP, or when VWAP is not computable (fail closed); OFF restores the pre-change rule. Tranche 2 is untouched by the enhancement.
3. Scale-in: tranche 1 is TRANCHE1_FRACTION = half the full size on the signal bar's close; tranche 2 is the remainder when turn_confirmed fires (daily EMA 5 above EMA 20) within TRANCHE2_MAX_WAIT = 5 sessions.
4. Sizing: full size from RISK_FRACTION = 0.25 percent of equity divided by the 8 percent stop distance (size_qty), at most MAX_POSITIONS = 5 positions and SLEEVE_NOTIONAL_CAP = 25 percent of equity.

Exits (check_exit, first trigger wins): 1-hour close at or above the session VWAP; +5 percent profit target; -8 percent stop; HOLD_DAYS = 3-trading-day time stop (_time_stop_due). The -25 percent disaster stop is carried as ExitRule data (a GTC disaster stop), not as a signal-level check.

Position management: at most 5 positions, 25 percent sleeve notional cap, two-tranche scale-in only as above, no averaging beyond tranche 2.

## Files in this repo
- Sleeve module (desk sleeves/capitulation.py): `sleeves/capitulation.py`.
- v3 adapter (desk adapters3/capitulation.py): `adapters3/capitulation.py`; also present as `integration/capitulation_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- No separate engine file: the full logic is in `sleeves/capitulation.py` itself (audit engine_files_needed is empty for this sleeve).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-capitulation.md`.

## Configuration
- Universe: the 41-name old-desk basket (served as the bars keys; CONFIG universe is ()). Asset: US equities. Timeframe: 1h signal with 1d filters (EMA200, ATR, 5/20 turn).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.0025 in CONFIG (0.25 percent of equity per trade on the 8 percent stop distance).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, earnings, positions.

## Data inputs
- bars: daily bars (260 per symbol) and closed regular-hours 1-hour bars per symbol, served through the snapshot context; the module computes RSI(14), EMA200, ATR(14) and session VWAP from them.
- fear_ok: context.extra["fear_ok"] from core (desk composite FEAR+; produced by core.bars_universe from the mood ring per the module header).
- earnings: the earnings calendar input for the 3-day pre-earnings veto; sleeve_state positions with entry price, entry date and tranche state arrive through the snapshot context.

## Install and run
1. Place the sleeve module at sleeves/capitulation.py and the adapter at adapters3/capitulation.py (repo copies at the same paths). The module needs the desk BaseSleeve / SleeveConfig / Intent plumbing it imports in the fresh desk.
2. Register the roster row for `capitulation` exactly as in the Configuration section in config/sleeves.json (module adapters3.capitulation).
3. Wire the producers so every snapshot carries: daily (260) and 1-hour bars per basket symbol, the earnings calendar, this sleeve's positions, and extra fear_ok.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the 5-part signal on fixtures: removing any one part (RSI below 20, climax volume over 2 x the prior 20, climax low within 2 percent of EMA200, first green bar with RSI turning up, daily ATR over 5 percent of close) produces no entry.
- Check the gates: fear_ok absent or false, or earnings within 3 days, each defer or refuse the entry; with the enhancement on, an entry close at or above session VWAP refuses tranche 1.
- Check the scale-in and sizing: tranche 1 is exactly half the size from 0.25 percent risk over the 8 percent stop distance, tranche 2 fires only on the 5/20 EMA turn within 5 sessions, and the 6th position or a position breaching the 25 percent cap is refused.
- Check exit precedence: session VWAP, +5 percent, -8 percent and the 3-trading-day stop each close the position, first trigger wins.
