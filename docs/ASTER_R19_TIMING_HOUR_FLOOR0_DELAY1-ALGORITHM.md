Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_r19_timing_hour_floor0_delay1: Algorithm

## What it is
A thin v3 wrapper (adapters3/aster_r19_timing_hour_floor0_delay1.py) that delegates to the shared Aster batch 15 timing engine in desk3/aster_batch15.py (evaluate with SLEEVE_ID = aster_r19_timing_hour_floor0_delay1). It is an hourly confirmed-swing timing sleeve, long-only equities, paper trading on a $10,000 slice. The engine header states no v3 producer emits timing_signals yet, so this sleeve lands visibly UNFED rather than fake-fed in the live registry.

## Variant parameters
- kind = hourly, floor = 0, delay = 1
- risk = 0.0025 of the slice, notional = 0.1 of the slice, fee_bps = 5, slots = 8
- Config row: cadence_s = 300, session = rth, slice capital_usd = 10000, cash_usd = 10000, bp_buffer_frac = 0.02, flat_by_close = False, params = {}.
- Wrapper inputs: bars, positions, quotes, timing_signals.

## Universe
The 42-name timing universe in the engine, in order: AAOI, AEHR, AG, ALAB, ANF, ARM, ARQQ, ASPI, AXTI, CLS, CORZ, CRDO, CRML, CVNA, FCEL, FFIV, HIVE, HUT, IREN, KEEL, LASR, LITE, MU, NBIS, OKLO, OUST, POET, SATL, SHAZ, SIVEF, SKYQ, SNDK, SOXL, TE, TEM, TSEM, TTMI, USAR, VELO, VRT, WDC, WYFI.

## Entry rules
- The signal is hourly_signal() in desk3/aster_batch15.py, a port of the archive r19_timing hourly signal using the v625 swing report supplied as timing_signals (not recomputed by the sleeve).
- Bar index used is i = len(bars) - 1 - delay, so delay = 1; i must be at least 59 and at least 60 + delay hourly bars are required.
- The swing report must be confirmed, must not use future data, must have score at least 8, and must have no bearish conflict.
- Entry price is the close of bar i. The swing invalidation is the stop and the swing target is the target; entry requires stop < entry < target.
- ATR is the 14-bar seed ATR (mean true range of the last 14 bars in the window). For a TRANSITION phenotype, the signal is rejected if (entry - open) / ATR > 0.5 or (high - low) / ATR > 1.5.
- The signal is rejected if any bar after bar i already touched the stop or the target.
- The effective stop is floor-adjusted: stop = min(original stop, entry - floor * ATR), with floor = 0 for this variant.
- A signal is actionable at the end of the latest hourly bar. Entry is only emitted inside the actionable window: 15 minutes with the engine's actionable-grace enhancement on by default (the original archive window was 5 minutes).
- At entry the engine re-checks stop < bid <= price < target using the actual quote.

## Sizing
- Budget is min(available cash, slice * notional) = at most $1,000.
- Quantity is floor(budget / (price * (1 + 5 bps fee))), also capped by floor(slice * risk / (price - stop)) = floor($25 / (price - stop)) when a stop is present.
- At most 8 slots; symbols already held are skipped; the universe is scanned in its listed order.

## Exit rules
Exits are evaluated before entries, in this order in the engine:
- Observed bid at or below the stop: observed_stop_trigger.
- Observed bid at or above the target: observed_target.
- A scheduled time exit if a stored exit_at has passed.
- The original 20 native bar deadline: 20 hourly bars after signal_end (deadline_bars = 20).

## Data inputs
Bars (1Hour for this sleeve), positions, quotes, and timing_signals (the v625 swing report). Where a quote is missing, the engine falls back to the last close of the relevant timeframe for pricing checks.

## Ambiguity note
The wrapper itself implements no rules; every rule above is implemented in the shared engine desk3/aster_batch15.py, which is already present in this repo under desk3/. Variant differences for the hourly family are only floor and delay.
