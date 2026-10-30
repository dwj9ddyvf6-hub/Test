# R19_TIMING_HOUR_FLOOR1_DELAY0 - Recreation Package

Grade: PARTIAL (accounting) - code present in Test; see Files and Verification

## Provenance

- Canonical ID: `R19_TIMING_HOUR_FLOOR1_DELAY0`
- Canonical name: Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay
- Aliases: R19_TIMING_HOUR_FLOOR1_DELAY0, ausar_pb153
- Type: forecast and ML models; Family: hourly; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of sleeves/aster_r19_timing_hour_floor1_delay0.py, desk3/aster_batch15.py (tree), and the existing docs/ASTER_R19_TIMING_HOUR_FLOOR1_DELAY0-RECREATE.md package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for this canonical id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record: entry: ['[R19_TIMING_HOUR_FLOOR1_DELAY0] ausar variant: Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay', '[ausar_pb153] Requires a causal confirmed Tensor swing with score at least 8, no bearish conflict and valid stop < entry < target. Transition candles have additional ATR geometry checks. A delayed variant waits one bar and discards geometry invalidated during that wait.']; exit: []; filters: ['[ausar_pb153] data: Completed hourly bars and canonical Tensor v698 swing geometry.']; parameters: {'R19_TIMING_HOUR_FLOOR1_DELAY0': {'kind': 'hourly', 'slots': 8, 'notional': 0.1, 'floor': 1, 'delay': 0, 'fee_bps': 5}}; gaps: ['exit rule not recorded in any consulted source']. Where the accounting graded PARTIAL, the algorithm below is taken from the code and the strategy card in Test, which are the truth where they go beyond the accounting.

## What this strategy is

Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay. Universe: not recorded in consulted sources; Asset: not recorded; Timeframe: not recorded.

Strategy card in Test (verbatim body):

Confirmed hourly swing · minimum 1-ATR stop distance, no extra bar delay

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

Canonical-variant note: this canonical id is the same code as the v3 sleeve aster_r19_timing_hour_floor1_delay0; its accounting parameters are kind=hourly, slots=8, notional=0.1, floor=1, delay=0, fee_bps=5 (ausar_map). The accounting record holds no exit rule of its own; the exit rules above are the engine's coded exits. The swing input (timing_signals) has no v3 producer yet, so the sleeve lands visibly UNFED rather than fake-fed.

## Files in this repo

- Sleeve wrapper: `sleeves/aster_r19_timing_hour_floor1_delay0.py` (in Test); also `adapters3/aster_r19_timing_hour_floor1_delay0.py` and `integration/aster_r19_timing_hour_floor1_delay0_adapter.py`
- Engine: `desk3/aster_batch15.py` (in Test)
- Config: `config/sleeves.json` (also `engines/config/sleeves.json`), row id `aster_r19_timing_hour_floor1_delay0`
- Existing package for the same code: `docs/ASTER_R19_TIMING_HOUR_FLOOR1_DELAY0-RECREATE.md` (in Test)
- Family card: `strategies/ausar/r19-timing-hourly.md` (in Test)

## Configuration

- Config row: id aster_r19_timing_hour_floor1_delay0, module adapters3.aster_r19_timing_hour_floor1_delay0, cadence_s 300, session rth, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, parked false, params {}, inputs [bars, positions, quotes, timing_signals].
- Engine SPECS: kind hourly, floor 1, delay 0, risk 0.0025, notional 0.1, fee_bps 5, slots 8 (see Full algorithm).

## Data inputs

Completed hourly bars and canonical Tensor v698 swing geometry via view timing_signals (confirmed, usesFutureData, score, bearishConflict, invalidation, target, phenotype per symbol); quotes (bid/ask) and broker positions. No v3 producer emits timing_signals yet: UNFED by design.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the configuration in the Configuration section against the code constants and, where one exists, the config/sleeves.json row.
3. Wire the data inputs named in Data inputs so the sleeve receives them at evaluation time in the form the code expects.
4. Register / enable the sleeve in the host desk exactly as its code entry point expects (see the strategy card Code section).
5. Run one evaluation on fixture data and confirm the emitted behaviour matches the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this canonical strategy is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Swing-gate check: unconfirmed, usesFutureData, score 7, bearishConflict, or stop/target not bracketing the close of bar i each produce no entry.
- Delay check (delay=0): bar i is the last bar index minus 0; a post-i touch of stop or target kills the signal.
- Floor check (floor=1): the carried stop equals min(engine stop, entry - 1 x ATR14).
- TRANSITION check: body > 0.5 ATR or range > 1.5 ATR skips the signal.
- Sizing / exit check: risk 0.0025, notional 0.1, fee 5 bps, slots 8; exits in precedence order stop, target, then the 20-native-bar deadline.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
