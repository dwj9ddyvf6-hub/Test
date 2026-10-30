# aster_pub_link_ai_volume - RECREATE

Provenance: AI Volume Strategy (TradingView Pine), adapted by Ausar (Source row of the existing Test doc `strategies/ausar/ai-volume.md`); v3 engine header in `desk3/aster_b4.py` describes the public_recipe spot port for `ai_volume`.

## What this sleeve is

This sleeve buys LINK crypto spot on a 4 hour bar whose volume is more than twice its average, closing up and above its 50 bar EMA, and exits after 5 bars or on an opposite spike. In the v3 desk it is the long-only spot sleeve `aster_pub_link_ai_volume` for LINKUSDT, evaluated hourly on a $10,000 slice. The bearish counterpart is an exit, never a short entry.

## Full algorithm

Delegation: the adapter `adapters3/aster_pub_link_ai_volume.py` imports `evaluate_link_ai_volume` from `desk3/aster_b4.py` and calls it with `SLEEVE_ID="aster_pub_link_ai_volume"`. All rules below are that function as applied to symbol `LINKUSDT`.

Evaluation order:

1. Load bars via `_spot_bars`: the view `bars` dict is searched for keys `LINKUSDT|4Hour`, then `LINKUSDT|4H`, then `LINKUSDT`. Require at least 50 bars, otherwise return no intents.
2. Compute EMA20 of volume and EMA50 of close with `_ema` (seeded on the first value, alpha = 2 / (n + 1)). Spike: last volume `> EMA20(volume) * 2.0`. Long signal: spike and last close > EMA50(close) and last close > last open. Short (counterpart) signal: spike and last close < EMA50(close) and last close < last open.
3. Position handling first: find a position with `sleeve_id` equal to this sleeve or None, symbol `LINKUSDT`, and quantity not zero.
   - Held count: `bars_held` if present. If absent, held starts at 0; if the held-bars enhancement is ON (default; `_link_enh_on`, switch `enhance_held_bars`, ENH-B6-HELDBARS-20261024), held is derived from `opened_at` by counting bars whose close time (bar time plus 14400 seconds) is after the open time.
   - If the short signal is true, exit the whole absolute quantity with reason `source_bearish_counterpart_exit`.
   - Otherwise, if held >= 5, exit the whole quantity with reason `source_signal_reset_counter_exit_bars5` (the source 5 bar time exit).
   - Otherwise return no intents.
4. Entry (no position): if the long signal is true, quantity = `int(spot_cash // last close)`, where spot cash is `view.slice.cash_usd` if present otherwise 10000. Reject if quantity < 1. Entry intent is market, `time_in_force="gtc"`, `position_intent="buy_to_open"`, price hint = last close, reason `source_entry_long volume_spike trend_up bullish`.

Note on sizing versus the existing card: the card states Binance sizing as 100 percent of cash including 10 bps. The v3 function computes `floor(cash / close)` with no fee deduction in the quantity formula; the code formula is the recreation standard here.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_pub_link_ai_volume.py`, `sleeves/aster_pub_link_ai_volume.py`, and `integration/aster_pub_link_ai_volume_adapter.py`. Desk original: `adapters3/aster_pub_link_ai_volume.py`, delegating to `desk3.aster_b4.evaluate_link_ai_volume`.
- Shared engines that run the logic: `desk3/aster_b4.py` (contains `evaluate_link_ai_volume`, `_spot_bars`, `_ema`) and `desk3/aster_b2.py` (imported by aster_b4 at module load).
- Existing family card: `strategies/ausar/ai-volume.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_pub_link_ai_volume`).

## Configuration

- Sleeve id: `aster_pub_link_ai_volume`; module: `adapters3.aster_pub_link_ai_volume` (roster row in desk `config/sleeves.json`).
- Universe: LINKUSDT (Binance) in the existing card; in code the symbol is fixed to `LINKUSDT`. Asset: crypto spot.
- Timeframe: 4h (existing card). Session: `24h`. Cadence: 3600 seconds (`cadence_s=3600`).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; entry quantity is floor(cash / close) as above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the adapter (`PUB_INPUTS` in `desk3/aster_b4.py`): `bars`, `positions`.

Producers declared in `desk3/aster_b4.py` (`PRODUCERS`): `bars` (outputs `bars`, freshness SLA 900 s), `options_chain` (outputs `options`, 900 s), and `broker_readback` (outputs `positions`, 900 s). The function itself consumes only bars and positions. The existing card lists the underlying data as Binance 4 hour klines and Alpaca crypto bars for the forward variant; this v3 sleeve reads the LINKUSDT bars in the view.

## Install and run

1. Place `desk3/aster_b4.py` and `desk3/aster_b2.py` in a fresh desk under `desk3/`.
2. Place the adapter as `adapters3/aster_pub_link_ai_volume.py` (copy any repo copy listed above).
3. Register the roster row for `aster_pub_link_ai_volume` from `config/sleeves.json` (module `adapters3.aster_pub_link_ai_volume`, cadence 3600, session 24h, $10,000 slice, inputs bars/positions, parked false).
4. Wire producers so the view contains `bars` under one of the LINKUSDT keys listed in the algorithm and `positions` from broker readback, plus a `slice` with cash.
5. First evaluation: call `adapters3.aster_pub_link_ai_volume.evaluate(view, ctx)`; it returns `desk3.aster_b4.evaluate_link_ai_volume(view, ctx, "aster_pub_link_ai_volume")`. Run hourly; the first check with at least 50 bars and no position is the volume-spike entry test.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check that fewer than 50 bars produces no intent.
- Check that volume equal to or below 2 times EMA20(volume), or a close at or below EMA50, or a close at or below the open, each independently blocks the entry.
- Check entry quantity equals floor(cash / close) and is at least 1.
- Check that a held position exits on a bearish spike (spike, close below EMA50, close below open) even before 5 bars, and exits at held >= 5 bars even without a spike.
- Check that when `bars_held` is absent, the derived count from `opened_at` drives the 5 bar exit when the held-bars enhancement is ON, and held is read as 0 when the switch is OFF.
