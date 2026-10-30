# aster_pub_enj_iu_body - RECREATE

Provenance: IU Big Body Bar (TradingView Pine), adapted by Ausar (Source row of the existing Test doc `strategies/ausar/iu-body.md`); v3 engine header in `desk3/aster_b4.py` describes the public_recipe spot port for `iu_body`.

## What this sleeve is

This sleeve buys ENJ crypto spot on a bar whose body is more than four times the average body, then trails a 2 times ATR stop. In the v3 desk it is the long-only spot adaptation `aster_pub_enj_iu_body` for ENJUSDT, evaluated hourly on a $10,000 slice. The bearish strong-body counterpart is an exit, never a short entry.

## Full algorithm

Delegation: the adapter `adapters3/aster_pub_enj_iu_body.py` imports `evaluate_enj_iu_body` from `desk3/aster_b4.py` and calls it with `SLEEVE_ID="aster_pub_enj_iu_body"`. All rules below are that function (and its helpers in the same file) as applied to symbol `ENJUSDT`.

Evaluation order:

1. Load bars via `_spot_bars`: the view `bars` dict is searched for keys `ENJUSDT|4Hour`, then `ENJUSDT|4H`, then `ENJUSDT`. The existing card states a 5 minute timeframe for the original recipe; the v3 helper named above is the bar lookup the code actually uses and imposes no other timeframe check. Require at least 21 bars, otherwise return no intents.
2. Compute bodies `|close - open|` for every bar. Baseline `base = sum(last 21 bodies) / 20`. Strong bar: last body `> base * 4.0`. Long signal: strong and last close > last open. Short (counterpart) signal: strong and last close < last open.
3. Position handling first: find a position with `sleeve_id` equal to this sleeve or None, symbol `ENJUSDT`, and quantity not zero.
   - If a position exists and the short signal is true, exit the whole absolute quantity with reason `source_opposite_body_exit`.
   - Otherwise evaluate the ATR trailing stop: ATR series is `_atr_series(bars, 14)` (true range with Wilder RMA smoothing, period 14). Held count is the position `bars_held` field; if that field is absent and the held-bars enhancement is ON (default; shared helper `_link_enh_on`, switch `enhance_held_bars`), held is derived from `opened_at` by counting bars whose close time (bar time plus 14400 seconds in `_bar_close_ts`) is after the open time. This derived path is ENH-B5-ENJ-HELDBARS-20261024 in the code comments.
   - If held is not None, held >= 1, and the ATR at index -2 is not None: entry index = `len(bars) - 1 - held`. If that index is in range before the last bar, average price is `avg_price` if present otherwise the close at the entry index. Build the stop by scanning bars from the entry index to the second-last bar: candidate = `close_i - ATR_i * 2.0`, initial = `average - ATR_i * 2.0`; the stop starts at the initial value and then only ratchets up (`max`). If the resulting stop is > 0 and the last bar low <= stop, exit the whole quantity with reason `source_atr_trailing_stop stop=<stop>`.
   - If a position exists and neither exit fires, return no intents.
4. Entry (no position): if the long signal is true, quantity = `int(spot_cash // last close)`, where spot cash is `view.slice.cash_usd` if present otherwise 10000. Reject if quantity < 1. Entry intent is market, `time_in_force="gtc"`, `position_intent="buy_to_open"`, price hint = last close, reason `source_body_impulse_long`.

Note on sizing versus the existing card: the card states 100 percent of book cash including 10 bps, lot-floored. The v3 function above computes `floor(cash / close)` with no fee deduction in the quantity formula; the code formula is the recreation standard here.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_pub_enj_iu_body.py`, `sleeves/aster_pub_enj_iu_body.py`, and `integration/aster_pub_enj_iu_body_adapter.py`. Desk original: `adapters3/aster_pub_enj_iu_body.py`, delegating to `desk3.aster_b4.evaluate_enj_iu_body`.
- Shared engines that run the logic: `desk3/aster_b4.py` (contains `evaluate_enj_iu_body`, `_spot_bars`, `_atr_series`) and `desk3/aster_b2.py` (imported by aster_b4 for shared helpers at module load).
- Existing family card: `strategies/ausar/iu-body.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_pub_enj_iu_body`).

## Configuration

- Sleeve id: `aster_pub_enj_iu_body`; module: `adapters3.aster_pub_enj_iu_body` (roster row in desk `config/sleeves.json`).
- Universe: ENJUSDT (Binance), per the existing card; in code the symbol is fixed to `ENJUSDT`. Asset: crypto spot.
- Timeframe: 5m in the existing card (see the bar-lookup note in the algorithm for what the v3 code accepts). Session: `24h`. Cadence: 3600 seconds (`cadence_s=3600`).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; entry quantity is floor(cash / close) as above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the adapter (`PUB_INPUTS` in `desk3/aster_b4.py`): `bars`, `positions`.

Producers declared in `desk3/aster_b4.py` (`PRODUCERS`): `bars` (outputs `bars`, freshness SLA 900 s), `options_chain` (outputs `options`, 900 s), and `broker_readback` (outputs `positions`, 900 s). The function itself consumes only bars and positions. The existing card lists the underlying data as Binance 5 minute klines and book ticker; the v3 function reads completed bars from the view and the last bar low for the stop, with no book-ticker call inside the function.

## Install and run

1. Place `desk3/aster_b4.py` and `desk3/aster_b2.py` in a fresh desk under `desk3/` (aster_b4 imports from aster_b2).
2. Place the adapter as `adapters3/aster_pub_enj_iu_body.py` (copy any repo copy listed above).
3. Register the roster row for `aster_pub_enj_iu_body` from `config/sleeves.json` (module `adapters3.aster_pub_enj_iu_body`, cadence 3600, session 24h, $10,000 slice, inputs bars/positions, parked false).
4. Wire producers so the view contains `bars` under one of the ENJUSDT keys listed in the algorithm and `positions` from broker readback, plus a `slice` with cash.
5. First evaluation: call `adapters3.aster_pub_enj_iu_body.evaluate(view, ctx)`; it returns `desk3.aster_b4.evaluate_enj_iu_body(view, ctx, "aster_pub_enj_iu_body")`. Run hourly; the first check with at least 21 bars and no position is the strong-body entry test.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check that fewer than 21 bars produces no intent.
- Check that a last body equal to or below 4 times the 21 bar baseline divided by 20 produces no entry, and a bullish strong body produces an entry of floor(cash / close).
- Check that a bearish strong body with no position produces no short entry, and with a position produces the opposite-body exit.
- Check the trailing stop: with a held position, the stop starts at average price minus 2 times ATR14, only moves up with close minus 2 times ATR14, and an exit fires only when the last bar low is at or below the stop.
- Check that when `bars_held` is absent, the derived held count from `opened_at` is used when the held-bars enhancement is ON, and the stop is not evaluated from that derivation when the switch is OFF.
