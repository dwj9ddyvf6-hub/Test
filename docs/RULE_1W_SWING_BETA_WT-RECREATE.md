# rule_1w_swing_beta_wt: Recreation package

Provenance: Source row in strategies/femto/femto-rule-1w-swing-beta-wt.md in this repo: Family Femto-lean; Source The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean; Asset US equities; Timeframe 1w; Universe 1,838-name genome; Style Tensor signal + frozen rule; Status waiting.

## What this sleeve is
This sleeve buys weekly Tensor Swing fires on high-beta names with a strong WaveTrend level and a rising EMA ribbon, and holds each name 126 sessions. Fire detection is done by the external Node GBM rule scorer; fires arrive as a data product. Sources: sleeves/rule_1w_swing_beta_wt.py and desk_sleeves/rule_1w_swing_beta_wt.py on the desk.

## Full algorithm
Evaluation order in sleeves/rule_1w_swing_beta_wt.py signal() (rule V2-1W-SWING-RAW-H126-727ea853, tier A; LANE 1W, SIGNAL_KIND swing):

1. Held positions first: sessions_since (delivered bar dates strictly after the entry date) >= HOLD_BARS - 1 = 125 (HOLD_BARS 126, staged one bar early) exits the full qty at the last close with ExitRule time_bars 126. No stop in the source rule.
2. Entry gate: equity > 0 and fires present; held symbols skipped; entries stop at MAX_POSITIONS 10.
3. Fire match: the first fire dict for the symbol dated on the last delivered daily bar date whose features all pass cond_pass (missing, non-numeric or non-finite fails): beta >= 1.3545490503311157 (beta to SPY); wt1 >= 25.92674789428711 (WaveTrend level); ribbons >= 0.009481946006417274 (EMA ribbon slope).
4. Eligibility: last close >= $5 (MIN_PX 5.0) and dv20 >= $1,000,000 (MIN_DV20), dv20 being the mean of close * volume over the last 20 delivered bars (0 when fewer than 20 bars).
5. Sizing: control qty = int((equity * 0.01) // last close) (NOTIONAL_FRACTION 0.01). Enhancement (ENH, on by default; context.extra["rule_1w_swing_beta_wt_enhance"]["beta_sizing"]): qty = int((equity * 0.01 / beta_fire) // last close), sizing by the passing fire's own beta so each slot carries equal SPY-equivalent exposure; quantities only ever shrink versus the control because beta >= 1.3545. OFF restores the flat control qty exactly. A qty below 1 takes no position, with no forced floor.
6. Entry intent: buy at the last close (price_hint 2dp) with ExitRule time_bars 126 and no stop.

## Files in this repo
- Sleeve module: sleeves/rule_1w_swing_beta_wt.py (the strategy logic; rule conditions and constants in the Full algorithm section).
- v3 adapter: integration/rule_1w_swing_beta_wt_adapter.py (repo copy of the desk adapter desk_sleeves/rule_1w_swing_beta_wt.py; evaluate(view, ctx) via port.bridge run_old_signal).
- Shared bridge: engines/desk3/bridge.py (the port.bridge helpers the adapter imports).
- Base sleeve contract used by the module: sleeves/muse/core/sleeve.py (BaseSleeve, ExitRule, Intent, SleeveConfig).
- Adapter post-filter engine: engines/desk3/enhance18.py (desk3/enhance18.py; the adapter applies enhance18.filter_entries to entries).
- Existing strategy doc: strategies/femto/femto-rule-1w-swing-beta-wt.md.
- Config: engines/config/sleeves.json (row id=rule_1w_swing_beta_wt).

## Configuration
Module rule_1w_swing_beta_wt (adapter_dir desk_sleeves); cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, rule_fires]; parked false. Source: muse-desk-v3/config/sleeves.json row id=rule_1w_swing_beta_wt. Adapter warmup {'1Day': 21}; the adapter universe is the 41-name basket AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR, plus candidates, params universe, held symbols and fire symbols.

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending; the adapter requests 1Day, 400 bars) for the universe symbols; rule fires via context.extra rule_fires {SYM: [{date, features}]} from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; the existing doc lists split-adjusted daily bars, 200); sleeve_state positions and equity from desk records and the slice. No data is fetched during evaluation.

## Install and run
1. Place the sleeve module at sleeves/rule_1w_swing_beta_wt.py and the v3 adapter at its repo path integration/rule_1w_swing_beta_wt_adapter.py (the adapter is the desk_sleeves/rule_1w_swing_beta_wt.py adapter on a fresh desk), and place the shared files listed under Files in this repo at their listed paths.
2. Register the config row for `rule_1w_swing_beta_wt` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so the fires, bars and sleeve_state arrive in context.extra / the snapshot in the shapes the algorithm section describes; the sleeve never fetches data or shells out to the scorer itself.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which reshapes the snapshot through port.bridge (ViewCtx, old_bars, run_old_signal) into the sleeve module's signal(bars, slice_state, context) and passes entry intents through desk3.enhance18.filter_entries.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): a swing fire dated on the last bar date with beta, wt1 and ribbons all inside the stated thresholds, close at or above $5 and dv20 at or above $1M, produces one buy sized int((equity * 0.01 / beta) // close) with the enhancement on, and int((equity * 0.01) // close) with it off. Fixture B (exit): a position with 125 or more sessions since entry produces one full exit.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
