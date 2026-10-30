# aster_r19_timing_overnight_25bp: Recreation package

Provenance: Ausar R18 overnight research (Source row in strategies/ausar/r19-timing-overnight.md in this repo).

## What this sleeve is
This sleeve buys US equities near the close when the early-afternoon move ranks in the top fifth of its own history, and sells at the next session's open. This book is the 25 bp cost variant (fee_bps=25 in the engine SPECS). It is a thin wrapper delegating to desk3/aster_batch15.py.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch15.py): kind="overnight", risk=0.0025, notional=0.1, fee_bps=25, slots=8, inputs=("bars", "positions", "quotes"), cadence_s=300.

Exit evaluation in desk3/aster_batch15.py::_eval_timing, before entries, for every non-zero position: bid is the sell quote, else the last close of the kind's timeframe. In order: if stop is set and bid <= stop, exit reason `observed_stop_trigger`; else if target is set and bid >= target, exit reason `observed_target`; else if exit_at is set and now >= exit_at, exit reason `scheduled_time_exit`; else (hourly only) if 20 native bars have ended after the position's signal_end, exit reason `original_20_native_bar_deadline`. Any exit suppresses entries that cycle. Exit intents are market day sell_to_close unless a sleeve-specific rule below states otherwise.
Entry sizing (all timing kinds): fee = fee_bps / 10000; budget = min(cash, 10000.0 * notional); qty = floor(budget / (price * (1 + fee))); if a stop exists, qty = min(qty, floor(10000.0 * risk / (price - stop))). Refuse if qty <= 0. At most slots=8 held-plus-new positions, one per symbol, symbols scanned in UNIVERSE42 order. Where a signal carries stop and target, entry also requires stop < bid <= price < target using the actual quotes.

For this sleeve the signal carries no stop and no target, so the only exit that can fire is the scheduled time exit at exit_at (the next session's 09:30 ET), stored on the entry intent.

Overnight entry clock: entries are evaluated only when 15:30 <= ET time < 15:35.
Overnight signal (overnight_signal in desk3/aster_batch15.py), per symbol in UNIVERSE42 order, skipping held symbols; at least 252 30-minute bars are required by the caller:
1. Today must be a weekday session present in the snapshot session calendar.
2. Build the 12:30 and 14:30 ET 30-minute bars per session. For each prior full session with both bars, the afternoon return is close(14:30 bar) / close(12:30 bar) - 1 (the existing card phrases the window as the 13:00-15:00 ET move from those bar closes).
3. Require at least 126 prior sessions of history; the threshold is the 80th percentile (linear interpolation) of the last 252 prior returns.
4. Signal only if today's afternoon return >= that threshold. signal_end is the end of today's 14:30 bar; actionable_at = signal_end + 30 minutes; exit_at = 09:30 ET on the next session. No next session means no signal.
Actionable window: entry only when actionable_at <= now < actionable_at + 5 minutes (no grace extension applies to the overnight kind in the code).
Entry sizing uses fee = 25 / 10000 in the common timing sizing formula above; with no stop there is no risk-cap term, so qty = floor(min(cash, 10000.0 * 0.1) / (price * 1.0025)).
Mid-price limit enhancement (ENH-ASTERB15-MIDLIMIT-20261024, this sleeve only, switch extra["enh_aster_r19_timing_overnight_25bp"] or extra["aster_b15_enh"] {"mid_limit": bool}, default ON): when both bid and ask are quoted, the entry becomes a limit order at round(mid, 2) instead of a market order, with the ask recorded as the control price; OFF restores the market order exactly. The scheduled exit keeps the market form in this sleeve (the mid-limit exit enhancement in the code applies only to the separate 5bp book).
Entry intent: day buy_to_open with exit_at carried, reason naming overnight_qualified_actual_quote.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_r19_timing_overnight_25bp.py` (also `sleeves/aster_r19_timing_overnight_25bp.py` and `integration/aster_r19_timing_overnight_25bp_adapter.py`).
- Shared engine: `desk3/aster_batch15.py` (this sleeve's SPECS entry and _eval_timing).
- Existing family card: `strategies/ausar/r19-timing-overnight.md`.
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
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_r19_timing_overnight_25bp.py` with SLEEVE_ID = "aster_r19_timing_overnight_25bp" (the repo also carries `sleeves/aster_r19_timing_overnight_25bp.py` and `integration/aster_r19_timing_overnight_25bp_adapter.py` copies).
2. Register the roster row for `aster_r19_timing_overnight_25bp` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_r19_timing_overnight_25bp, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch15.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the history gates: fewer than 126 prior sessions, a non-session today, and a missing next session each produce no entry.
- Check the threshold: today's 12:30-to-14:30-bar return below the interpolated 80th percentile of the last 252 prior returns produces no entry; at or above it produces one entry inside 15:30-15:35 ET only.
- Check sizing: qty equals floor(min(cash, 1000.0) / (price * 1.0025)) and slots are capped at 8.
- Check the mid-limit rule: with the enhancement ON and a two-sided quote, the entry is a limit at round(mid, 2); with it OFF, a market order.
- Check the only exit is the scheduled exit at the next session's 09:30 ET, and that it suppresses entries that cycle.
