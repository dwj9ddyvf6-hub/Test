# red_day_reversal: Recreation package

Provenance: Source row in strategies/femto/femto-red-day-reversal.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This is a daily washout-reversal equity sleeve: a name that falls at least 3 percent in a day with RSI(2) at or below 10, while still closing above its 200-day average, is bought for a 4 percent rebound, with a 2 percent hard stop and a 3-day time exit. Entries pass the desk3/enhance18 entry filter in the v3 adapter. Sources: sleeves/red_day_reversal.py and desk_sleeves/red_day_reversal.py on the desk.

## Full algorithm
Constants (sleeves/red_day_reversal.py): RED_DAY_THRESHOLD -0.03, RSI_PERIOD 2, RSI_MAX 10.0, SMA_LONG 200, RISK_FRACTION 0.0025, STOP_PCT 0.02, SLEEVE_NOTIONAL_CAP 0.25, PROFIT_TARGET_PCT 0.04, TIME_EXIT_DAYS 3, MAX_POSITIONS 8, EARNINGS_BLACKOUT_DAYS 5, NO_EARNINGS_ETFS {QQQ, SPY, SOXL, TQQQ, VXX, UVXY}. CONFIG: cadence_s 300, universe (), risk_pct 0.0025. The RSI is Wilder's with a textbook SMA seed (different from the rsi_meanrev sleeve's seeding; both are preserved as written).
Evaluation order in signal(), per symbol (universe override, else the bars keys):
1. Held position first (exits run on however many bars are delivered; the 202-bar entry minimum never gates an exit): exit the full qty when the last close is at or above entry x 1.04 (+4 percent target), or at or below entry x 0.98 (-2 percent stop), or sessions held (delivered dates strictly after the entry date) reach 3.
2. Entry warmup: fewer than 202 daily bars skips the symbol.
3. Washout (detect_washout): day return <= -0.03 AND RSI(2) <= 10 AND the close is above the 200-day SMA.
4. Enhancement gate (switch in context.extra, range-within-target gate, on by default in the ENH idiom): refuse the entry when the washout day's own range, (high - low) / last close, exceeds the 0.04 profit target.
5. Earnings veto: an earnings date within 5 days blocks the entry when earnings data is present in context.extra (absent data means no sleeve-level veto; the ETF set above is exempt).
6. Caps and sizing: at most 8 open positions and equity above 0; quantity from the 0.25 percent risk budget on the 2 percent stop (about 12.5 percent of equity notional), capped at 25 percent of equity per name; quantity 0 skips. The entry intent carries ExitRules for the stop (entry x 0.98), the target (entry x 1.04) and time_bars 3.
The v3 adapter (desk_sleeves/red_day_reversal.py) universe is the 41-name basket (AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR) plus the bridge CANDIDATES, any roster universe additions and held symbols, with 202 1-day warmup bars requested; entries then pass desk3/enhance18.filter_entries.

## Files in this repo
- Strategy module (desk sleeves/red_day_reversal.py): `sleeves/red_day_reversal.py` in this repo (the strategy logic; CONFIG sleeve_id=red_day_reversal).
- v3 adapter (desk desk_sleeves/red_day_reversal.py): `integration/red_day_reversal_adapter.py` in this repo; the adapter re-shapes the snapshot via the port bridge and applies the enhance18 entry filter to entries.
- Shared engine files (engines_map.json): `engines/desk3/enhance18.py` (desk desk3/enhance18.py, vendored; filter_entries) and `engines/desk3/bridge.py` (desk desk3/bridge.py, vendored; the port bridge).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=red_day_reversal); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module red_day_reversal; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars_1day', 'positions']; parked false. Source: muse-desk-v3/config/sleeves.json row id=red_day_reversal (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending), 202 requested by the adapter for the basket plus candidates; sleeve_state {SYM: {position: {entry_px, entry_date, qty}}}; earnings {SYM: date|None} via context.extra when present; positions via the snapshot (the adapter maps avg_price / opened_at onto entry_px / entry_date).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `red_day_reversal` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the washout: a day return of -0.029, RSI(2) of 10.5, and a close below the 200-day SMA each fail on their own; -0.03 with RSI(2) of exactly 10 above the average passes.
- Check exits on short history: a held position with only a few bars still exits at +4 percent, -2 percent, or 3 held sessions.
- Check the range gate: a washout day whose (high - low) / close exceeds 0.04 is refused with the gate ON and taken with it OFF.
- Check sizing and caps: qty follows the 0.25 percent risk / 2 percent stop formula capped at 25 percent notional, and the 9th position is refused.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
