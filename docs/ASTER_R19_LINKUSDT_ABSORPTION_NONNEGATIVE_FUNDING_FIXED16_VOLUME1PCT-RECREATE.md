# aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct - RECREATE

Provenance: Ausar crypto research: the original absorption books and the R19 funding-filter books (Source row of the existing Test doc `strategies/ausar/crypto-absorption.md`); v3 engine header in `desk3/aster_b11_crypto.py` describes batch 11 as source-verified against the staged archive r19_crypto.py, absorption signals and crypto_rules.json.

## What this sleeve is

This sleeve is a LINKUSDT crypto spot R19 variant in batch 11, family `absorption_nonnegative_funding` with a fixed 16 hour exit and sizing cap `volume1pct`. It buys the bar that confirms absorption after a high-volume down shock bar, gated to non-negative funding. It runs 24 hours on a 14400 second cadence with a $10,000 slice, long only.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.py` sets `SLEEVE_ID="aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct"`, imports `INPUTS` from `desk3.aster_b11_crypto`, and delegates to `desk3.aster_b11_crypto.evaluate`. The SPECS row in that engine for this sleeve is exactly: `sym="LINKUSDT", fam="absorption_nonnegative_funding", cap="volume1pct", hold_h=16`. Engine fee constant `FEE = 0.001` (10 bps). Note: unlike some other R19 engines, batch 11 does not define an `exit` key in SPECS; the fixed16 exit is the only exit path in its `evaluate`.

Evaluation order in `evaluate(sid, view, ctx)`:

1. Load inputs: bars via `_bars` (view `bars` keys `LINKUSDT|4Hour`, then `LINKUSDT|4h`, then `LINKUSDT|240min`, then `LINKUSDT`, sorted by bar time `t`); funding via `_funding` (`view.funding[LINKUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, default `"2026-10-24T00:00:00+00:00"` recorded in code if absent).
2. Exit handling first: positions are the view `positions` with quantity not zero. For each such position whose symbol is `LINKUSDT` or None, or whose symbol string contains `LINKUSDT`, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0. If held >= 16, exit the whole absolute quantity with reason naming the sleeve and `aster_deadline_fixed16` and the held hours. Price hint is the last bar close if bars exist, otherwise the position average price. The deadline fires even when bars or funding are missing. There is no structural exit and no stop for this sleeve.
   - Exit intent: `Intent(kind="exit", symbol="LINKUSDT", qty=absolute quantity, price_hint=price or None, side="sell", position_intent="sell_to_close")`.
   - If any exit is produced, or any non-zero position exists in the view at all (the code tests the unfiltered positions list), return the exits (possibly empty) and do not evaluate an entry.
3. Entry (no positions), in code order:
   - Family signal for `absorption_nonnegative_funding` (see the signal definition below).
- Funding gate for this family: after the absorption signal passes, if funding is None or funding < 0, no entry. Absent funding is never assumed.
   - Stale-signal gate (below) must not block.
4. Signal definition for this family:
   - Absorption families (`absorption_negative_funding`, `absorption_nonnegative_funding`): `_absorption` requires at least 300 bars. EMAs are seeded on the first value with alpha = 2 / (n + 1) (`_ema`). The shock bar is the second-last bar (`bars[-2]`): its volume > 2 times EMA20(volume) at index -2, its close < its open, and its close < EMA50(close) at index -2. The confirmation bar is the last bar: close > open and close > (shock high + shock low) / 2. All three shock conditions and both confirmation conditions must hold.
   - Breakout family (`breakout_base`): `_breakout` requires at least 21 bars and the last bar close strictly greater than the maximum high of the prior 20 bars (`bars[-21:-1]`).
   - For this sleeve the applicable branch is `absorption_nonnegative_funding` only; the other branch in the engine does not apply.
5. Stale-signal entry gate (ENH-B8, in `desk3/aster_b11_crypto.py`, applied by both engines; default ON): signal age is `(now - (last bar time + 4 hours))` in hours. If the switch is ON and age > 4.0 hours (`STALE_GATE_MAX_AGE_H = 4.0`), the entry is refused. The switch is `extra["aster_edge"][<sleeve>]["stale_signal_gate"]`; setting it to False restores the pre-change rule exactly. Exits are untouched by this gate. If the caller supplies `extra["aster_edge_journal"]` as a list, a paired record with the enhanced decision, the shadow faithful decision and the signal age is appended; the shadow arm never emits an intent.
6. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Full quantity = `cash * (1 - 0.001) / price`. Cap for this sleeve: volume1pct: quantity is the minimum of the full cash quantity and 1 percent of the volume of the second-last bar (`0.01 * bars[-2].v` in code; the engine header describes this as 1 percent of the preceding 4h bar volume). Reject if quantity <= 0.
7. Entry intent: `Intent(kind="enter", symbol="LINKUSDT", qty=round(quantity, 8), price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, the family `absorption_nonnegative_funding`, the close, the funding value and the cap `volume1pct`.

Differences from the family card that the v3 code implements (recorded in the card Notes and the engine header): the v3 engine buys at the signal bar close when it evaluates, not 4 hours later; its deadline counts from the fill / open time; and for volume1pct it reads the bar preceding the signal bar (code: `bars[-2]`). The code rules above are the recreation standard.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.py`, `sleeves/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.py`, and `integration/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct_adapter.py`. Desk original: `adapters3/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.py`, delegating to `desk3.aster_b11_crypto.evaluate`.
- Shared engine that runs the logic: `desk3/aster_b11_crypto.py` (contains the SPECS row for this sleeve, `_absorption`, `_breakout`, `_bars`, `_funding`, the stale-signal gate and `evaluate`; engines map status already_present).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by aster_b11_crypto). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/crypto-absorption.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct`).

## Configuration

- Sleeve id: `aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct`; module: `adapters3.aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct` (roster row in desk `config/sleeves.json`).
- Universe: LINKUSDT (in code, `sym="LINKUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all absorption rows, and this row is the LINKUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed 4 hour bars). Session: `24h`. Cadence: 14400 seconds (`cadence_s=14400`, 4 hours).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `volume1pct` and fee 0.001 as in the sizing step above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS = ("bars", "funding", "positions")` in `desk3/aster_b11_crypto.py`, also imported by the adapter): `bars`, `funding`, `positions`.

The engine header states funding is a declared producer input: absent funding means funding-gated sleeves refuse entry and land UNFED in the registry, never fake-fed. No producer tuple with freshness SLAs is declared in `desk3/aster_b11_crypto.py` or the adapter, so no SLA is stated here. The existing card lists the underlying data as Binance spot 4h klines, book ticker and last trade, and funding for the filtered R19 books; the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_b11_crypto.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct` from `config/sleeves.json` (module `adapters3.aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct`, cadence 14400, session 24h, $10,000 slice, inputs bars/funding/positions, parked false).
4. Wire inputs so the view contains `bars` under one of the LINKUSDT keys listed in the algorithm (at least 300 bars for an absorption entry, at least 21 for a breakout entry), `funding` for LINKUSDT, `positions` from broker readback, a `slice`, and a current time in the view or context.
5. First evaluation: call `adapters3.aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct.evaluate(view, ctx)`; it delegates to `desk3.aster_b11_crypto.evaluate("aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct", view, ctx)`. Run every 14400 seconds, 24 hours; the first check is the exit scan for a LINKUSDT position, then the family entry test (funding must be observed and >= 0).

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check that a LINKUSDT position held 16 hours or more exits with the fixed16 deadline reason even when bars and funding are absent, and that any non-zero position in the view blocks a new entry.
- Check the family signal for `absorption_nonnegative_funding` exactly: for absorption, fewer than 300 bars, a shock bar failing any of volume > 2 times EMA20(volume), close < open, or close < EMA50(close), or a confirmation bar failing close > open or close > shock midpoint, each independently blocks entry; for breakout, fewer than 21 bars or a last close at or below the prior 20 bar maximum high blocks entry.
- Check the funding gate for this sleeve: funding must be observed and >= 0; absent funding blocks a funding-gated entry and never blocks `breakout_base`.
- Check the stale-signal gate: with the switch ON, a signal bar that closed more than 4 hours before now produces no entry; with the switch OFF, the same opportunity is evaluated under the faithful rule.
- Check entry quantity: cash times 0.999 divided by price, with the cap for this sleeve applied exactly as stated (volume1pct), rounded to 8 decimals in the intent, and that a result of 0 or less produces no intent.
- Check that intents carry symbol `LINKUSDT` (this engine performs no broker-symbol translation) and the side and position_intent values stated above.
