# aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct - RECREATE

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row of the existing Test doc `strategies/ausar/r19-crypto-breakout.md`); v3 engine header in `desk3/aster_crypto.py` describes the R19 crypto rules implemented from the TSV spec for this family.

## What this sleeve is

This sleeve buys ADAUSDT crypto spot on a completed 4 hour breakout above the prior 20 bar high when the latest perpetual funding rate is negative (a negative-funding squeeze). This specific variant is `aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct`: exit rule `normalization_failure` with a 96 hour hold, and sizing cap `volume1pct`. It runs 24 hours on a 14400 second cadence with a $10,000 slice, long only, one position per book.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.py` sets `SLEEVE_ID="aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct"` and delegates to `desk3.aster_crypto.evaluate`. The SPECS row in that engine for this sleeve is exactly: `sym="ADAUSDT", fam="nfs", exit="normalization_failure", cap="volume1pct", hold_h=96`. Engine fee constant `FEE = 0.001` (10 bps).

Broker symbol translation (in the engine, BLOCKED-EXIT-20261029 cure): intents are created for `ADA/USD` (a symbol ending in USDT with no slash is translated to the base plus `/USD`); bars, funding and internal state keep the `ADAUSDT` form.

Evaluation order in `evaluate`:

1. Load inputs: bars via `_bars` (view `bars` keys `ADAUSDT|4Hour`, then `ADAUSDT|4h`, then `ADAUSDT|240min`, then `ADAUSDT`, sorted by time); funding via `_funding` ( `view.funding[ADAUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, default recorded in code if absent).
2. Exit handling first, restricted to this sleeve's own symbol: positions are filtered to quantity not zero and broker symbol equal to this sleeve's broker symbol. For each such position, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0.
- Deadline backstop: if held hours >= 96, exit with a deadline reason naming `normalization_failure` and 96h.
- Otherwise, structural exit: if funding is not None, funding >= 0, and at least 4 bars are present, and the last bar close < the minimum low of the prior 3 bars (`bars[-4:-1]`), and now >= last bar time plus 8 hours, exit with the delayed normalization_failure reason.
- Latched scan (enhancement ENH-B6-LATCH-20261024, default ON; switch `enhance_trigger_latch`): if the above does not trigger and the enhancement is ON, scan post-entry bars; a bar at index >= 3 whose close is below the minimum low of its prior 3 bars, with now >= that bar time plus 8 hours and current funding >= 0, triggers a latched normalization_failure exit. With the switch OFF, only the latest bar logic above applies.
   - An exit intent is an `Intent(kind="exit", symbol="ADA/USD", qty=absolute quantity, price_hint=last bar close if bars exist, side="sell", position_intent="sell_to_close")` with the reason prefixed by the sleeve id.
   - If any exit is produced, or any position for this symbol remains, return the exits (possibly empty) and do not evaluate an entry.
3. Entry (no position for this symbol), family `nfs` gates in code order:
   - Funding must be observed and negative: if funding is None or funding >= 0, no entry. Absent funding is never assumed.
   - At least 21 bars are required.
   - Breakout: the last bar close must be strictly greater than the maximum high of the prior 20 bars (`bars[-21:-1]`). Otherwise no entry.
4. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Full quantity = `cash * (1 - 0.001) / price`. Cap for this sleeve: volume1pct: quantity is the minimum of the full cash quantity and 1 percent of the volume of the second-last bar (`0.01 * bars[-2].v` in code; the engine header describes this as 1 percent of the preceding 4h bar volume). Then quantity is floored to a whole unit with `int(qty)`; reject if the result is <= 0.
5. Entry intent: `Intent(kind="enter", symbol="ADA/USD", qty=quantity, price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, the nfs family, the close, the funding value and the cap `volume1pct`.

Differences from the family card that the v3 code implements (recorded in the card Notes and the engine): the v3 engine buys at the signal bar close when it evaluates, not 4 hours later; its deadlines count from the fill / open time; and for volume1pct it reads the bar before the signal bar in the card's wording (code: `bars[-2]`). The code rules above are the recreation standard.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.py`, `sleeves/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.py`, and `integration/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct_adapter.py`. Desk original: `adapters3/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.py`, delegating to `desk3.aster_crypto.evaluate`.
- Shared engine that runs the logic: `desk3/aster_crypto.py` (contains the SPECS row for this sleeve and `evaluate`).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by aster_crypto). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/r19-crypto-breakout.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct`).

## Configuration

- Sleeve id: `aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct`; module: `adapters3.aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct` (roster row in desk `config/sleeves.json`).
- Universe: ADAUSDT (in code, `sym="ADAUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all R19 rows, and this row is the ADAUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed UTC 4 hour bars). Session: `24h`. Cadence: 14400 seconds (`cadence_s=14400`, 4 hours).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `volume1pct` and fee 0.001 as in the sizing step above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS = ("bars", "funding", "positions")` in `desk3/aster_crypto.py`, also imported by the adapter): `bars`, `funding`, `positions`.

The engine header states funding is a declared producer input: absent funding means no entry and the sleeve is unfed in the registry, never fake-fed. No producer tuple with freshness SLAs is declared in `desk3/aster_crypto.py` or the adapter, so no SLA is stated here. The existing card lists the underlying data as Binance spot 4 hour klines, depth and last trade, and Binance USD-M funding history (with a relay note for US hosts); the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_crypto.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct` from `config/sleeves.json` (module `adapters3.aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct`, cadence 14400, session 24h, $10,000 slice, inputs bars/funding/positions, parked false).
4. Wire inputs so the view contains `bars` under one of the ADAUSDT keys listed in the algorithm (at least 21 bars for an entry), `funding` for ADAUSDT, `positions` from broker readback, a `slice`, and a current time in the view or context.
5. First evaluation: call `adapters3.aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct.evaluate(view, ctx)`; it delegates to `desk3.aster_crypto.evaluate("aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct", view, ctx)`. Run every 14400 seconds, 24 hours; the first check is the exit scan for an ADA position, then the negative-funding breakout entry test.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check that entry is blocked when funding is absent or >= 0, when fewer than 21 bars are present, and when the last close is at or below the maximum high of the prior 20 bars.
- Check entry quantity: floor of cash times 0.999 divided by price, with the cap for this sleeve applied exactly as stated (volume1pct), and that a result of 0 produces no intent.
- Check that intents carry the broker symbol `ADA/USD` while bar and funding lookups use `ADAUSDT`.
- Check that a position in a different symbol is not exited by this sleeve, and that holding this symbol's position blocks a new entry.
- Check the exit for this sleeve's rule `normalization_failure` at its 96 hour deadline and, where the algorithm above defines a structural exit, that structural condition and timing exactly; also check there is no price stop beyond those rules.
