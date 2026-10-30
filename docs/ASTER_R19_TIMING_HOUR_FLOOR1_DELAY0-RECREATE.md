# aster_r19_timing_hour_floor1_delay0: Recreation package

Provenance: Ausar R17 hourly geometry research on the v625 engine (Source row in strategies/ausar/r19-timing-hourly.md in this repo).

## What this sleeve is
This sleeve buys a confirmed hourly swing signal on US equities with the engine's stop and target. This book uses stop floor 1 ATR and signal delay 0 bar(s). It is a thin wrapper delegating to desk3/aster_batch15.py, and its swing input is not produced by a v3 producer yet, so it lands visibly UNFED rather than fake-fed.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch15.py): kind="hourly", floor=1, delay=0, risk=0.0025, notional=0.1, fee_bps=5, slots=8, inputs=("bars", "positions", "quotes", "timing_signals"), cadence_s=300.

Exit evaluation in desk3/aster_batch15.py::_eval_timing, before entries, for every non-zero position: bid is the sell quote, else the last close of the kind's timeframe. In order: if stop is set and bid <= stop, exit reason `observed_stop_trigger`; else if target is set and bid >= target, exit reason `observed_target`; else if exit_at is set and now >= exit_at, exit reason `scheduled_time_exit`; else (hourly only) if 20 native bars have ended after the position's signal_end, exit reason `original_20_native_bar_deadline`. Any exit suppresses entries that cycle. Exit intents are market day sell_to_close unless a sleeve-specific rule below states otherwise.
Entry sizing (all timing kinds): fee = fee_bps / 10000; budget = min(cash, 10000.0 * notional); qty = floor(budget / (price * (1 + fee))); if a stop exists, qty = min(qty, floor(10000.0 * risk / (price - stop))). Refuse if qty <= 0. At most slots=8 held-plus-new positions, one per symbol, symbols scanned in UNIVERSE42 order. Where a signal carries stop and target, entry also requires stop < bid <= price < target using the actual quotes.

Hourly signal (hourly_signal in desk3/aster_batch15.py), per symbol in UNIVERSE42 order, skipping held symbols; at least 60 + delay hourly bars are required:
1. Index i = last bar index - delay (0). Require i >= 59.
2. The swing record for the symbol (view["timing_signals"][symbol]["swing"]) must be confirmed, must not use future data, must have score >= 8, and must have no bearishConflict.
3. Entry price is the close of bar i; the swing invalidation (stop) and target must both exist and satisfy stop < entry < target.
4. ATR is the seeded ATR14 over bars up to i (mean true range of the last 14 bars, refusing non-positive source ATR).
5. TRANSITION phenotype skip: if the swing phenotype is TRANSITION and (entry - open of bar i) / ATR > 0.5 or (high - low of bar i) / ATR > 1.5, no signal.
6. Delay invalidation (the delay=0 rule as coded for any delay): if any bar after i touches the stop (low <= stop) or the target (high >= target), no signal.
7. Stop floor: floorstop = min(stop, entry - 1 * ATR). With floor=0 this is the engine stop unless the engine stop is above entry; with floor=1 this widens the stop to at most entry - 1 ATR. The intent carries stop=floorstop and target=the swing target, deadline_bars=20, and signal_end = end of bar i.
Actionable window: actionable_at is the end of the last hourly bar; entry only when actionable_at <= now < actionable_at + 5 minutes, extended to 15 minutes by the actionable-grace enhancement (switch enhance_actionable_grace, default ON; OFF restores 5 minutes).
Entry intent: market day buy_to_open with stop and target on the intent, reason naming hourly_qualified_actual_quote, plus exit_at not set, signal_end and deadline_bars=20 carried for the deadline exit.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_r19_timing_hour_floor1_delay0.py` (also `sleeves/aster_r19_timing_hour_floor1_delay0.py` and `integration/aster_r19_timing_hour_floor1_delay0_adapter.py`).
- Shared engine: `desk3/aster_batch15.py` (this sleeve's SPECS entry and _eval_timing).
- Existing family card: `strategies/ausar/r19-timing-hourly.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: the frozen 42-name list in desk3/aster_batch15.py UNIVERSE42: AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI. Asset: US equities.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac=0.02; per-sleeve notional, risk, fee and slots are in the Full algorithm section.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Producers in the engine PRODUCERS tuple: tensor_bundle -> tensor_fires (93600s), bars -> bars (900s), broker_readback -> positions (900s), quotes -> quotes (60s). The roster inputs for this sleeve are stated in the Full algorithm / Configuration sections.
- timing_signals: view["timing_signals"] keyed by symbol, each with a swing record (confirmed, usesFutureData, score, bearishConflict, invalidation, target, phenotype). The engine header states no v3 producer emits timing_signals yet, so the hourly sleeves land visibly UNFED rather than fake-fed.
- bars: view["bars"] keyed by `<symbol>|<timeframe>` or symbol, for the timeframes named in the algorithm.
- quotes: view["quotes"][symbol] with bid/ask; the buy quote is the entry price and the sell quote (bid) is the exit witness, each falling back to the last close of the relevant timeframe.
- positions: view["positions"] rows with symbol, qty, and stop/target/exit_at or the same fields under meta, plus signal_end/deadline_bars under meta for hourly positions.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_r19_timing_hour_floor1_delay0.py` with SLEEVE_ID = "aster_r19_timing_hour_floor1_delay0" (the repo also carries `sleeves/aster_r19_timing_hour_floor1_delay0.py` and `integration/aster_r19_timing_hour_floor1_delay0_adapter.py` copies).
2. Register the roster row for `aster_r19_timing_hour_floor1_delay0` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_r19_timing_hour_floor1_delay0, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch15.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check each swing gate on fixtures: unconfirmed, usesFutureData, score 7, bearishConflict, and stop/target not bracketing the close of bar i each produce no entry.
- Check the delay rule for this book (delay=0): bar i is the bar 0 before the last, and a post-i touch of stop or target kills the signal.
- Check the floor rule for this book (floor=1): the carried stop equals min(engine stop, entry - 1 * ATR).
- Check the TRANSITION skips at body > 0.5 ATR and range > 1.5 ATR.
- Check sizing with risk=0.0025, notional=0.1, fee 5 bps and slots=8, and the 20-bar deadline exit counting bars ending after signal_end.
- Check exits in precedence order: stop, then target, then the 20-bar deadline (there is no scheduled exit_at for hourly).
