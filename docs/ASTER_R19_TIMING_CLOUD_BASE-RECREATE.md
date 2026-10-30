# aster_r19_timing_cloud_base: Recreation package

Provenance: Ausar R17 intraday geometry research (Source row in strategies/ausar/r19-timing-cloud.md in this repo).

## What this sleeve is
This sleeve is an intraday US-equity pullback sleeve: on an hourly EMA uptrend it buys the first 10-minute reclaim of the EMA 5/12 cloud, targeting the prior day's high. This book is the base variant, with risk 0.0025 and notional 0.1 of the slice. It is a thin wrapper delegating to desk3/aster_batch15.py.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch15.py): kind="cloud", risk=0.0025, notional=0.1, fee_bps=5, slots=8, inputs=("bars", "positions", "quotes"), cadence_s=300.

Exit evaluation in desk3/aster_batch15.py::_eval_timing, before entries, for every non-zero position: bid is the sell quote, else the last close of the kind's timeframe. In order: if stop is set and bid <= stop, exit reason `observed_stop_trigger`; else if target is set and bid >= target, exit reason `observed_target`; else if exit_at is set and now >= exit_at, exit reason `scheduled_time_exit`; else (hourly only) if 20 native bars have ended after the position's signal_end, exit reason `original_20_native_bar_deadline`. Any exit suppresses entries that cycle. Exit intents are market day sell_to_close unless a sleeve-specific rule below states otherwise.
Entry sizing (all timing kinds): fee = fee_bps / 10000; budget = min(cash, 10000.0 * notional); qty = floor(budget / (price * (1 + fee))); if a stop exists, qty = min(qty, floor(10000.0 * risk / (price - stop))). Refuse if qty <= 0. At most slots=8 held-plus-new positions, one per symbol, symbols scanned in UNIVERSE42 order. Where a signal carries stop and target, entry also requires stop < bid <= price < target using the actual quotes.

Cloud entry clock: entries are evaluated only when 09:50 <= ET time <= 15:30.
Cloud signal (cloud_signal in desk3/aster_batch15.py), per symbol in UNIVERSE42 order, skipping held symbols:
1. Require at least 30 10-minute bars and at least 53 hourly bars (hourly bars are first truncated to those ending at or before the last 10-minute bar's end), and at least one prior daily bar; the target is the prior daily bar's high.
2. Hourly bias: EMA34 of hourly closes > EMA50 of hourly closes at each of the last 3 hourly closes.
3. Reclaim episode scan over 10-minute bars: starting indices from max(15, len(ten)-3) to the end; the bar before the start must dip with low <= the upper edge of the EMA5/EMA12 cloud formed from the prior bar's EMAs, the start bar's low must be above that upper edge and its high at or above the lower edge; ATR is the RMA ATR14 of the 10-minute bars before the start.
4. The episode (start bar to the last bar) must be at most 3 bars and its minimum low must not be below lower - 0.5 * ATR.
5. The last 10-minute close must be above the upper cloud edge and the EMA5-EMA12 spread must be widening versus the prior bar; no earlier bar in the episode after the start may already satisfy that reclaim condition.
6. On a signal: stop = episode minimum low - 0.1 * ATR, target = prior day high, signal_end = end of the last 10-minute bar, deadline 100 minutes.
Actionable window: entry only when signal_end <= now < signal_end + 5 minutes, extended to 15 minutes by the actionable-grace enhancement (switch enhance_actionable_grace, default ON; OFF restores 5 minutes).
Additional cloud guard: refuse entry if (target - price) < 2 * (price - stop) (target less than two actual risk).
Scheduled exit time stored on entry: min(now + 100 minutes, 15:50 ET today); refuse entry if that time is already past.
Entry intent: market day buy_to_open with the signal stop and target carried on the intent, reason naming cloud_qualified_actual_quote.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_r19_timing_cloud_base.py` (also `sleeves/aster_r19_timing_cloud_base.py` and `integration/aster_r19_timing_cloud_base_adapter.py`).
- Shared engine: `desk3/aster_batch15.py` (this sleeve's SPECS entry and _eval_timing).
- Existing family card: `strategies/ausar/r19-timing-cloud.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: the frozen 42-name list in desk3/aster_batch15.py UNIVERSE42: AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI. Asset: US equities.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac=0.02; per-sleeve notional, risk, fee and slots are in the Full algorithm section.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Producers in the engine PRODUCERS tuple: tensor_bundle -> tensor_fires (93600s), bars -> bars (900s), broker_readback -> positions (900s), quotes -> quotes (60s). The roster inputs for this sleeve are stated in the Full algorithm / Configuration sections.
- bars: view["bars"] keyed by `<symbol>|<timeframe>` or symbol, for the timeframes named in the algorithm.
- quotes: view["quotes"][symbol] with bid/ask; the buy quote is the entry price and the sell quote (bid) is the exit witness, each falling back to the last close of the relevant timeframe.
- positions: view["positions"] rows with symbol, qty, and stop/target/exit_at or the same fields under meta, plus signal_end/deadline_bars under meta for hourly positions.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_r19_timing_cloud_base.py` with SLEEVE_ID = "aster_r19_timing_cloud_base" (the repo also carries `sleeves/aster_r19_timing_cloud_base.py` and `integration/aster_r19_timing_cloud_base_adapter.py` copies).
2. Register the roster row for `aster_r19_timing_cloud_base` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_r19_timing_cloud_base, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch15.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the hourly bias, dip, episode length (at most 3 bars), 0.5 ATR depth limit and widening-spread reclaim each block a fixture that violates only that rule.
- Check the 2R guard: a fixture with target - price < 2 * (price - stop) produces no entry.
- Check this book's sizing with risk=0.0025 and notional=0.1: qty is the smaller of the notional floor and the risk floor stated above, fee 5 bps.
- Check exits in precedence order (stop, then target, then scheduled time) and that the stored scheduled exit is min(entry + 100 minutes, 15:50 ET).
- Check the entry clock (09:50 to 15:30 ET) and the actionable window (5 minutes with grace OFF, 15 minutes with grace ON).
