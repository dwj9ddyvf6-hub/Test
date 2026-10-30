# rsi_meanrev: Recreation package

Provenance: Source row in strategies/ausar/public-rsi2.md in this repo: Larry Connors' RSI(2), via trader.dev, StockCharts and Tomazetti's Pine script; the old swing desk via Femto-lean.

## What this sleeve is
This is a daily RSI(2) mean-reversion equity sleeve: it buys a name whose RSI(2) is strictly below 10 while its close is above the 200-day SMA, and exits on a close above the 5-day SMA, an RSI(2) snapback above 70, a 5 percent target, an 8 percent stop, or 5 trading days, whichever fires first. Entries pass the desk3/enhance18 entry filter in the v3 adapter. Sources: sleeves/rsi_meanrev.py and desk_sleeves/rsi_meanrev.py on the desk.

## Full algorithm
Constants (sleeves/rsi_meanrev.py): RSI_PERIOD 2, RSI_OVERSOLD 10.0, RSI_OVERBOUGHT 70.0, MA200_PERIOD 200, MA5_PERIOD 5, PROFIT_TARGET 0.05, TIME_STOP_DAYS 5, STOP_LOSS 0.08, RISK_FRACTION 0.0025, MAX_POSITIONS 8, EARNINGS_BLACKOUT_DAYS 3. CONFIG: cadence_s 300, universe (), risk_pct 0.0025. The Wilder RSI uses the module's exact seeding (pandas ewm alpha = 1/period, adjust=False; the first output equals the first input, not the textbook SMA seed).
Evaluation order in signal(), per symbol (universe override, else the bars keys):
1. Held position first (exits are never gated by bar count). First trigger wins, in this precedence: close above the 5-day SMA (primary); RSI(2) > 70; last close >= entry x 1.05; last close <= entry x 0.92; sessions held >= 5. Sessions held counts delivered dates strictly after the entry date.
2. Enhancement departure (switch in context.extra, sma5_exit_removed, on by default in the ENH idiom): the SMA5 first-trigger exit is deleted, so the position is managed only to +5 percent / RSI(2) > 70 / -8 percent / the 5-day clock; with the switch OFF the original stack runs exactly as above.
3. Entry: at most 8 open positions and equity above 0. RSI(2) strictly below 10 on the last closed bar (10.0 exactly does not qualify); then the trend filter: the close must be above the 200-day SMA, failing closed when fewer than 200 bars make the average uncomputable; then the earnings veto (the earnings day and the 3 days before it; a stale or unserved calendar fails entries closed).
4. Sizing: quantity from the 0.25 percent risk budget on the 8 percent stop; quantity 0 skips. The entry intent carries ExitRules for the stop (entry x 0.92), the target (entry x 1.05) and time_bars 5. The -8 percent stop is evaluated in-signal on closes; it is never a broker stop.
The v3 adapter universe is the 41-name basket (AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR) plus the bridge CANDIDATES, roster additions and held symbols, with 200 1-day warmup bars requested; entries then pass desk3/enhance18.filter_entries.

## Files in this repo
- Strategy module (desk sleeves/rsi_meanrev.py): `sleeves/rsi_meanrev.py` in this repo (the strategy logic; CONFIG sleeve_id=rsi_meanrev).
- v3 adapter (desk desk_sleeves/rsi_meanrev.py): `integration/rsi_meanrev_adapter.py` in this repo; the adapter re-shapes the snapshot via the port bridge and applies the enhance18 entry filter to entries.
- Shared engine files (engines_map.json): `engines/desk3/enhance18.py` (desk desk3/enhance18.py, vendored; filter_entries) and `engines/desk3/bridge.py` (desk desk3/bridge.py, vendored; the port bridge).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=rsi_meanrev); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module rsi_meanrev; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars_1day', 'positions', 'earnings']; parked false. Source: muse-desk-v3/config/sleeves.json row id=rsi_meanrev (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending), 200 requested by the adapter; sleeve_state {SYM: {position: {entry_px, entry_date, qty}}}; earnings {SYM: date|None} and earnings_fresh, served from the desk EDGAR calendar (absent or stale fails entries closed); positions via the snapshot.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `rsi_meanrev` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the entry: RSI(2) of exactly 10.0 does not enter; 9.99 above the SMA200 does (subject to the other gates); a close at or below SMA200, and fewer than 200 bars, each fail closed.
- Check the earnings veto: an entry 3 days before the print and on the print day are vetoed; a stale calendar vetoes all entries.
- Check exit precedence: with the SMA5 exit present (switch OFF), a close above SMA5 exits before the target and stop checks; with the switch ON that same fixture holds until one of the remaining triggers fires.
- Check the remaining exits: RSI(2) above 70, +5 percent, -8 percent and 5 held sessions each exit the full qty.
- Check caps: the 9th position is refused.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
