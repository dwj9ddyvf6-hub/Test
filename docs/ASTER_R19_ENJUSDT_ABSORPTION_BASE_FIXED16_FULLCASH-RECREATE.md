# aster_r19_enjusdt_absorption_base_fixed16_fullcash - RECREATE

Provenance: Ausar crypto research: the original absorption books and the R19 funding-filter books (Source row of the existing Test doc `strategies/ausar/crypto-absorption.md`); v3 engine header in `desk3/aster_crypto.py` describes the R19 crypto rules implemented from the TSV spec for this family (ASTER-B6).

## What this sleeve is

This sleeve buys ENJUSDT crypto spot on a confirmed 4 hour absorption pattern: a high-volume down shock bar followed by a bar closing back above the shock midpoint. This specific variant is `aster_r19_enjusdt_absorption_base_fixed16_fullcash`: family `absorption` with no funding gate in this engine, a fixed 16 hour exit, and sizing cap `fullcash`. It runs 24 hours on a 14400 second cadence with a $10,000 slice, long only, one position per book.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_enjusdt_absorption_base_fixed16_fullcash.py` sets `SLEEVE_ID="aster_r19_enjusdt_absorption_base_fixed16_fullcash"` and delegates to `desk3.aster_crypto.evaluate`. The SPECS row in that engine for this sleeve is exactly: `sym="ENJUSDT", fam="absorption", exit="fixed16", cap="fullcash", hold_h=16`. Engine fee constant `FEE = 0.001` (10 bps).

Broker symbol translation (in the engine, BLOCKED-EXIT-20261029 cure): intents are created for `ENJ/USD` (a symbol ending in USDT with no slash is translated to the base plus `/USD`); bars, funding and internal state keep the `ENJUSDT` form.

Evaluation order in `evaluate`:

1. Load inputs: bars via `_bars` (view `bars` keys `ENJUSDT|4Hour`, then `ENJUSDT|4h`, then `ENJUSDT|240min`, then `ENJUSDT`, sorted by time); funding via `_funding` (`view.funding[ENJUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, with the code default if absent).
2. Exit handling first, restricted to this sleeve's own symbol: positions are filtered to quantity not zero and broker symbol equal to this sleeve's broker symbol (`ENJ/USD`). For each such position, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0.
   - Fixed deadline only: if held hours >= 16, exit with reason `aster_deadline_fixed16_16h`. No structural exit is evaluated for this sleeve, and there is no stop.
   - An exit intent is an `Intent(kind="exit", symbol="ENJ/USD", qty=absolute quantity, price_hint=last bar close if bars exist, side="sell", position_intent="sell_to_close")` with the reason prefixed by the sleeve id.
   - If any exit is produced, or any position for this symbol remains, return the exits (possibly empty) and do not evaluate an entry.
3. Entry (no position for this symbol), in code order:
   - Absorption only, with no funding gate in this engine for family `absorption`: if `_absorption(brs)` is false, no entry. The definition is below.
Absorption signal `_absorption(brs)` (same definition in all three engines used in this batch): at least 300 bars are required. Volumes and closes are taken in bar order; EMA20 of volume and EMA50 of close use `_ema` seeded on the first value with alpha = 2 / (n + 1), current-inclusive. The shock bar is the second-last bar: its volume > 2 times EMA20(volume) at that bar, its close < its open, and its close < EMA50(close) at that bar. The confirmation is the last bar: close > open and close > (shock high + shock low) / 2. All conditions must hold.
4. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Full quantity = `cash * (1 - 0.001) / price`. Cap for this sleeve: fullcash: quantity is the full cash quantity above, with no volume cap. Then quantity is floored to a whole unit with `int(qty)`; reject if the result is <= 0.
5. Entry intent: `Intent(kind="enter", symbol="ENJ/USD", qty=quantity, price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, the `absorption` family, the close, the funding value and the cap `fullcash`.

Differences from the family card that the v3 code implements (recorded in the card Notes and the engine): the v3 engine buys at the signal bar close when it evaluates, not 4 hours later; its deadlines count from the fill / open time; and for volume1pct it reads the bar before the signal bar in the card's wording (code: `bars[-2]`). The code rules above are the recreation standard.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_enjusdt_absorption_base_fixed16_fullcash.py`, `sleeves/aster_r19_enjusdt_absorption_base_fixed16_fullcash.py`, and `integration/aster_r19_enjusdt_absorption_base_fixed16_fullcash_adapter.py`. Desk original: `adapters3/aster_r19_enjusdt_absorption_base_fixed16_fullcash.py`, delegating to `desk3.aster_crypto.evaluate`.
- Shared engine that runs the logic: `desk3/aster_crypto.py` (contains the SPECS row for this sleeve and `evaluate`).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by the engine). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/crypto-absorption.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_enjusdt_absorption_base_fixed16_fullcash`).

## Configuration

- Sleeve id: `aster_r19_enjusdt_absorption_base_fixed16_fullcash`; module: `adapters3.aster_r19_enjusdt_absorption_base_fixed16_fullcash` (roster row in desk `config/sleeves.json`).
- Universe: ENJUSDT (in code, `sym="ENJUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all R19 rows, and this row is the ENJUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed UTC 4 hour bars). Session: `24h`. Cadence: 14400 seconds (`cadence_s=14400`, 4 hours).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `fullcash` and fee 0.001 as in the sizing step above. Roster `params` for this row is empty; the parameters live in the engine SPECS row above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS = ("bars", "funding", "positions")` in `desk3/aster_crypto.py`, also imported by the adapter): `bars`, `funding`, `positions`.

The engine header states funding is a declared producer input: absent funding means no entry for a funding-gated sleeve and the sleeve is unfed in the registry, never fake-fed. No producer tuple with freshness SLAs is declared in `desk3/aster_crypto.py` or the adapter, so no SLA is stated here. The existing card lists the underlying data as Binance spot 4 hour klines, depth and last trade, and Binance USD-M funding history (with a relay note for US hosts); the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_crypto.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_enjusdt_absorption_base_fixed16_fullcash.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_enjusdt_absorption_base_fixed16_fullcash` from `config/sleeves.json` (module `adapters3.aster_r19_enjusdt_absorption_base_fixed16_fullcash`, cadence 14400, session 24h, $10,000 slice, inputs bars/funding/positions, parked false).
4. Wire inputs so the view contains `bars` under one of the ENJUSDT keys listed in the algorithm, `funding` for ENJUSDT, `positions` from broker readback, a `slice`, and a current time in the view or context.
5. First evaluation: call `adapters3.aster_r19_enjusdt_absorption_base_fixed16_fullcash.evaluate(view, ctx)`; it delegates to `desk3.aster_crypto.evaluate("aster_r19_enjusdt_absorption_base_fixed16_fullcash", view, ctx)`. Run every 14400 seconds, 24 hours; the first check is the exit scan for a ENJUSDT position, then the entry test for family `absorption`.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check the entry signal for family `absorption` exactly as defined above, including every bar-count and funding condition that applies to it.
- Check entry quantity: floor of cash times 0.999 divided by price, with the cap for this sleeve applied exactly as stated (fullcash), and that a result of 0 produces no intent.
- Check that intents carry the broker symbol `ENJ/USD` while bar and funding lookups use `ENJUSDT`.
- Check that a position in a different symbol is not exited by this sleeve, and that holding this symbol's position blocks a new entry.
- Check the exit for this sleeve's rule `fixed16` at its 16 hour deadline and, where the algorithm above defines a structural exit, that structural condition exactly; also check there is no price stop beyond those rules.
