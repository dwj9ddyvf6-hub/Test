# rule_1d_green_tom: Recreation package

Provenance: Source row in strategies/femto/femto-rule-1d-green-tom.md in this repo: Family Femto-lean; Source The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean; Asset US equities; Timeframe 1d; Universe 1,838-name genome; Style Tensor signal + frozen rule; Status waiting.

## What this sleeve is
This sleeve buys daily Tensor Green fires that pass a frozen momentum and dispersion rule on an exact turn-of-month trading day, and holds each name 63 sessions. Fire detection is done by the external Node GBM rule scorer; the fires arrive as a data product and the sleeve never shells out. Sources: sleeves/rule_1d_green_tom.py and desk_sleeves/rule_1d_green_tom.py on the desk.

## Full algorithm
Evaluation order in sleeves/rule_1d_green_tom.py signal() (rule V4-1D-GREEN-RAW-H63-ALL-c10e07a0, tier A; LANE 1D, SIGNAL_KIND green):

1. Held positions first: sessions_since counts delivered daily bar dates strictly after the entry date; when sessions >= HOLD_BARS - 1 = 62 (HOLD_BARS 63, staged one bar early), exit the full qty at the last close with ExitRule time_bars 63. No stop in the source rule.
2. Entry gate: equity > 0 and fires present; symbols already held are skipped and entries stop at MAX_POSITIONS 10.
3. Fire match: a fire dict for the symbol whose date equals the last delivered daily bar date. Its features are tested with cond_pass (a missing, non-numeric or non-finite feature fails): mom121 >= 0.6500771284103396; disp between 0.02075970731675625 and 0.02862246334552765 inclusive; tom == 1 after the recomputation in step 4.
4. TOM recomputation (the scorer's tom feature is vacuous on the live bar, always 1): turn-of-month is the last trading day of the month OR one of the first 3 trading days of the month. First-3 is counted exactly off the market day list; last-trading-day is decided by the NEXT trading day (weekday plus the module's own NYSE holiday calendar, including Good Friday) falling in a new month. The calendar-day proxy (day >= 28 or day <= 3) is NOT used. Enhancement (ENH, on by default; context.extra["rule_1d_green_tom_enhance"]["tom_fail_closed"]): the first-3 branch may only be satisfied from the supplied market day list extra trading_days and fails closed when that list is absent or empty; the last-trading-day branch is unchanged, and OFF restores the pre-change fallback to the symbol's own bar dates. On a date-parse failure the scorer's tom value is kept.
5. Eligibility on the signal day: last close >= $5 (MIN_PX 5.0) and dv20 >= $1,000,000 (MIN_DV20), dv20 being the mean of close * volume over the last 20 bars (0 when fewer than 20 bars).
6. Sizing: qty = int((equity * 0.01) // last close) (NOTIONAL_FRACTION 0.01); qty below 1 takes no position, with no forced 1-share floor. Entry intent: buy at the last close (price_hint rounded to 2dp) with ExitRule time_bars 63 and no stop.

## Files in this repo
- Sleeve module: sleeves/rule_1d_green_tom.py (the strategy logic; rule conditions and constants in the Full algorithm section).
- v3 adapter: integration/rule_1d_green_tom_adapter.py (repo copy of the desk adapter desk_sleeves/rule_1d_green_tom.py; evaluate(view, ctx) via port.bridge run_old_signal).
- Shared bridge: engines/desk3/bridge.py (the port.bridge helpers the adapter imports).
- Base sleeve contract used by the module: sleeves/muse/core/sleeve.py (BaseSleeve, ExitRule, Intent, SleeveConfig).
- Adapter post-filter engine: engines/desk3/enhance18.py (desk3/enhance18.py; the adapter applies enhance18.filter_entries to entries).
- Existing strategy doc: strategies/femto/femto-rule-1d-green-tom.md.
- Config: engines/config/sleeves.json (row id=rule_1d_green_tom).

## Configuration
Module rule_1d_green_tom (adapter_dir desk_sleeves); cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, rule_fires, trading_days]; parked false. Source: muse-desk-v3/config/sleeves.json row id=rule_1d_green_tom. The module's own SleeveConfig also carries cadence_s 300 and universe () (the adapter supplies the universe: the 41-name basket AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR, plus candidates, params universe, held symbols and fire symbols).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending; the adapter requests 1Day, 400 bars, warmup 21) for the universe symbols; rule fires via context.extra rule_fires {SYM: [{date, features}]} from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; the existing doc lists split-adjusted daily bars, 200); the market trading_days list via context.extra for the TOM first-3 count; sleeve_state {SYM: {position: {entry_px, entry_date, qty}}} and equity from the desk's position records and slice. No data is fetched during evaluation.

## Install and run
1. Place the sleeve module at sleeves/rule_1d_green_tom.py and the v3 adapter at its repo path integration/rule_1d_green_tom_adapter.py (the adapter is the desk_sleeves/rule_1d_green_tom.py adapter on a fresh desk), and place the shared files listed under Files in this repo at their listed paths.
2. Register the config row for `rule_1d_green_tom` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides (params {}).
3. Wire the producers named in Data inputs so the fires, bars and sleeve_state arrive in context.extra / the snapshot in the shapes the algorithm section describes; the sleeve never fetches data or shells out to the scorer itself.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which reshapes the snapshot through port.bridge (ViewCtx, old_bars, run_old_signal) into the sleeve module's signal(bars, slice_state, context) and passes entry intents through desk3.enhance18.filter_entries.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): a green fire dated on the last bar date with mom121 and disp inside the stated bands, on a day that is TOM under the exact trading-day test with the market day list supplied, close at or above $5 and dv20 at or above $1M, produces one buy sized int((equity * 0.01) // close). Fixture B: the same fire on a non-TOM day, or with the market day list absent and only the first-3 branch available under the enhancement, produces no entry. Fixture C (exit): a position with 62 or more sessions since entry produces one full exit.

- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated partial quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
