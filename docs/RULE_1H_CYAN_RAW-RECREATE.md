# rule_1h_cyan_raw: Recreation package

Provenance: Source row in strategies/femto/femto-rule-1h-cyan-raw.md in this repo: Family Femto-lean; Source The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean; Asset US equities; Timeframe 1h; Universe 41-name old-desk basket; Style Tensor signal + frozen rule; Status waiting.

## What this sleeve is
This sleeve buys hourly Tensor Cyan fires printed on a wide-range bar with a strong WaveTrend gap while semis are up, and holds each name 7 hourly bars. Fire detection is done by the external Node 1H scorer (dcg_rule_1h.mjs); fires arrive as a data product. Sources: sleeves/rule_1h_cyan_raw.py and desk_sleeves/rule_1h_cyan_raw.py on the desk.

## Full algorithm
Evaluation order in sleeves/rule_1h_cyan_raw.py signal() (rule V3-1H-CYAN-RAW-H7-aab0a308):

1. Held positions first: bars after entry are counted with the old _bar_after law (a bare-date entry_time counts only bars whose ET date is LATER than the entry date; a timestamp entry counts bars strictly after it); when the count reaches HOLD_BARS 7, exit the full qty at the last close with ExitRule time_bars 7. No stop in the source rule (the enhancement stop below rides on the entry intent).
2. Entry gate: equity > 0 and fires present; held symbols skipped; entries stop at MAX_POSITIONS 10; a symbol needs at least 100 delivered 1H bars.
3. Fire match: only the latest CLOSED bar can be the signal bar: a fire whose t does not equal the last bar's timestamp (epoch comparison tolerating Z/offset spellings within 1 second) is ignored. fire_passes requires the fire to be a dict with finite numeric rangeatr >= 2.05 (RANGE_ATR_MIN, signal-bar range / ATR14) and wtgap >= 6.88 (WTGAP_MIN, WaveTrend wt1-wt2), and smhUp == 1 exactly; non-dict rows, missing or non-numeric values and NaN scores are skipped per fire.
4. Eligibility: last close >= $5 (MIN_PX 5.0) and point-in-time dv20 >= $1,000,000 (MIN_DV20): dv20 is computed from the DAILY bars ending at the latest daily bar on or before the signal bar's ET session date (0 when fewer than 20 such bars).
5. Sizing: qty = int((equity * 0.01) // last close) (NOTIONAL_FRACTION 0.01); qty below 1 takes no position, with no forced floor.
6. Entry intent: buy at the last close (price_hint 2dp) with ExitRule time_bars 7. Enhancement (ENH, on by default; context.extra["rule_1h_cyan_raw_enhance"]["signal_low_stop"]): the entry intent additionally carries ExitRule stop at the signal bar's low (rounded 2dp) and stop= that low; OFF restores the time-exit-only rule exactly.

## Files in this repo
- Sleeve module: sleeves/rule_1h_cyan_raw.py (the strategy logic; rule conditions and constants in the Full algorithm section).
- v3 adapter: integration/rule_1h_cyan_raw_adapter.py (repo copy of the desk adapter desk_sleeves/rule_1h_cyan_raw.py; evaluate(view, ctx) via port.bridge run_old_signal).
- Shared bridge: engines/desk3/bridge.py (the port.bridge helpers the adapter imports).
- Base sleeve contract used by the module: sleeves/muse/core/sleeve.py (BaseSleeve, ExitRule, Intent, SleeveConfig).
- Adapter post-filter engine: engines/desk3/enhance18.py (desk3/enhance18.py; the adapter applies enhance18.filter_entries to entries).
- Existing strategy doc: strategies/femto/femto-rule-1h-cyan-raw.md.
- Config: engines/config/sleeves.json (row id=rule_1h_cyan_raw).

## Configuration
Module rule_1h_cyan_raw (adapter_dir desk_sleeves); cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1hour, bars_1day, positions, rule_fires_1h]; parked false. Source: muse-desk-v3/config/sleeves.json row id=rule_1h_cyan_raw. Adapter warmup {'1Hour': 100, '1Day': 20}; the adapter universe is the 41-name basket AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR, plus candidates, params universe, held symbols and fire symbols. The existing doc adds that the desk scans hourly at :26 and buys at the next :04 pass, 10:00-15:59 ET.

## Data inputs
Hourly bars (dicts with t as epoch seconds of the bar open, o, h, l, c, v, ascending, regular-hours, closed bars only; the adapter requests 1Hour, 500 bars) and daily bars (1Day, 60) for the dv20 filter, supplied through the snapshot; hourly fires via context.extra rule_fires_1h {SYM: [{t, rangeatr, wtgap, smhUp}]} from the hourly DCG fire file, and daily bars via context.extra daily_bars as reshaped by the adapter; sleeve_state positions from desk records; equity from the slice. The existing doc lists regular-hours hourly bars (1,000) and daily bars for dollar volume. No data is fetched during evaluation.

## Install and run
1. Place the sleeve module at sleeves/rule_1h_cyan_raw.py and the v3 adapter at its repo path integration/rule_1h_cyan_raw_adapter.py (the adapter is the desk_sleeves/rule_1h_cyan_raw.py adapter on a fresh desk), and place the shared files listed under Files in this repo at their listed paths.
2. Register the config row for `rule_1h_cyan_raw` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so the fires, bars and sleeve_state arrive in context.extra / the snapshot in the shapes the algorithm section describes; the sleeve never fetches data or shells out to the scorer itself.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which reshapes the snapshot through port.bridge (ViewCtx, old_bars, run_old_signal) into the sleeve module's signal(bars, slice_state, context) and passes entry intents through desk3.enhance18.filter_entries.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): at least 100 hourly bars, a fire timestamped on the last bar with rangeatr at or above 2.05, wtgap at or above 6.88 and smhUp 1, close at or above $5 and point-in-time dv20 at or above $1M, produces one buy sized int((equity * 0.01) // close) carrying, with the enhancement on, a stop at the signal bar low. Fixture B: the same fire timestamped on any earlier bar, or with a NaN rangeatr, produces no entry. Fixture C (exit): a position with 7 bars after entry produces one full exit.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
