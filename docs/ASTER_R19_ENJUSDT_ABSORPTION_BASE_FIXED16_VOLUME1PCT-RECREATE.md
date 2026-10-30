# aster_r19_enjusdt_absorption_base_fixed16_volume1pct - RECREATE

Provenance: Ausar crypto research: the original absorption books and the R19 funding-filter books (Source row of the existing Test doc `strategies/ausar/crypto-absorption.md`); v3 engine header in `desk3/aster_batch7.py` describes this batch as a faithful port of archive source/backend/r19_crypto.py plus strategies/absorption/signals.py plus strategies/r19/crypto_rules.json (ASTER-B7).

## What this sleeve is

This sleeve buys ENJUSDT crypto spot on a confirmed 4 hour absorption pattern: a high-volume down shock bar followed by a bar closing back above the shock midpoint. This specific variant is `aster_r19_enjusdt_absorption_base_fixed16_volume1pct`: family `absorption_base` (the funding-off control), a fixed 16 hour exit, and sizing cap `volume1pct`. It runs on a 300 second cadence in session `always` with a $10,000 slice, long only, one position per book.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_enjusdt_absorption_base_fixed16_volume1pct.py` sets `SLEEVE_ID="aster_r19_enjusdt_absorption_base_fixed16_volume1pct"`, sets `INPUTS = inputs_for(SLEEVE_ID)`, and delegates to `desk3.aster_batch7.evaluate`. The SPECS row in that engine for this sleeve is exactly: `sym="ENJUSDT", fam="absorption_base", exit="fixed16", cap="volume1pct", hold_h=16`. Engine fee constant `FEE = 0.001` (10 bps). This engine does not translate the symbol: intents carry `ENJUSDT` as written in the code.

Evaluation order in `evaluate`:

1. Load inputs: bars via `_bars` (view `bars` keys `ENJUSDT|4Hour`, then `ENJUSDT|4h`, then `ENJUSDT|240min`, then `ENJUSDT`, sorted by time); funding via `_funding` (`view.funding[ENJUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, with the code default if absent).
2. Exit handling first: positions are filtered to `p.get("symbol", "ENJUSDT") == "ENJUSDT"` (a position with no symbol field is therefore treated as this symbol) and quantity not zero. For each such position, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0. If held >= 16, exit with reason `aster_deadline_fixed16_16h`. No structural exit and no stop are evaluated for this sleeve in this engine: `fixed16` is a fixed deadline only, and the deadline is checked before any bar or funding validation in the exit loop.
   - An exit intent is an `Intent(kind="exit", symbol="ENJUSDT", qty=absolute quantity, price_hint=last bar close if bars exist otherwise None, side="sell", position_intent="sell_to_close")` with the reason naming the sleeve.
   - If any exit is produced, or any such position remains, return the exits (possibly empty) and do not evaluate an entry.
3. Entry signal (no such position): Absorption signal `_absorption(brs)` (same definition in all three engines used in this batch): at least 300 bars are required. Volumes and closes are taken in bar order; EMA20 of volume and EMA50 of close use `_ema` seeded on the first value with alpha = 2 / (n + 1), current-inclusive. The shock bar is the second-last bar: its volume > 2 times EMA20(volume) at that bar, its close < its open, and its close < EMA50(close) at that bar. The confirmation is the last bar: close > open and close > (shock high + shock low) / 2. All conditions must hold. That absorption test is the signal for this sleeve; no breakout test is applied.
4. Funding gate: none for this sleeve. Family `absorption_base` is a funding-off control in the engine header and in the code: a funding outage cannot veto it, and `inputs_for` does not declare funding for it.
5. Freshness enhancement (ENH-ASTER-R19-B7-20261024, `signal_window`, default ON; switch `view["extra"]["aster_r19_improve"][<sleeve>]["signal_window"]` or the flat key in that dict): signal age is `(now - (last bar time + 4 hours))` in seconds. Fresh means 0 <= age <= 900 (`ENTRY_WINDOW_S = 900`). A paired record is appended to `view["extra"]["aster_r19_exp_journal"]["records"]` when that journal is supplied. If the switch is ON and the signal is not fresh (including a bar with no parseable time, which fails closed), no entry. With the switch OFF, the pre-change rule is restored exactly: entry at any signal age.
6. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Quantity = `cash / (price * (1 + 0.001))`. Cap for this sleeve: volume1pct: quantity is the minimum of the full cash quantity and 1 percent of the volume of the second-last bar (`0.01 * bars[-2].v` in code; the engine header describes this as 1 percent of the preceding 4h bar volume). Reject if quantity <= 0.
7. Entry intent: `Intent(kind="enter", symbol="ENJUSDT", qty=round(quantity, 8), price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, family `absorption_base`, the close, the funding value and the cap `volume1pct`. Note the quantity is rounded to 8 decimals in this engine, not floored to a whole unit.

Differences from the family card that the v3 translation records in the engine header: the source's 4 hour entry delay, 300 second entry window and observed-quote clocks are producer/dispatcher-layer mechanics in the source; the v3 sleeve evaluates the latest completed-bar signal on the snapshot it is given and sizes off the signal close, subject to the 900 second freshness enhancement above. The code rules above are the recreation standard.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_enjusdt_absorption_base_fixed16_volume1pct.py`, `sleeves/aster_r19_enjusdt_absorption_base_fixed16_volume1pct.py`, and `integration/aster_r19_enjusdt_absorption_base_fixed16_volume1pct_adapter.py`. Desk original: `adapters3/aster_r19_enjusdt_absorption_base_fixed16_volume1pct.py`, delegating to `desk3.aster_batch7.evaluate`.
- Shared engine that runs the logic: `desk3/aster_batch7.py` (contains the SPECS row for this sleeve, `_absorption`, `_breakout`, `inputs_for`, `PRODUCERS` and `evaluate`).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by the engine). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/crypto-absorption.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_enjusdt_absorption_base_fixed16_volume1pct`).

## Configuration

- Sleeve id: `aster_r19_enjusdt_absorption_base_fixed16_volume1pct`; module: `adapters3.aster_r19_enjusdt_absorption_base_fixed16_volume1pct` (roster row in desk `config/sleeves.json`).
- Universe: ENJUSDT (in code, `sym="ENJUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all R19 rows, and this row is the ENJUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed UTC 4 hour bars). Session: `always`. Cadence: 300 seconds (`cadence_s=300`).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `volume1pct` and fee 0.001 as in the sizing step above. Roster `params` for this row: `family="absorption_base", exit_policy="fixed16", capacity="volume1pct", symbol="ENJUSDT", fee_bps=10`.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and by `inputs_for` in the engine for this sleeve: `bars`, `positions`.

Producers declared in `desk3/aster_batch7.py` (`PRODUCERS`): `bars` (outputs `bars`, freshness SLA 900 s), `funding` (outputs `funding`, 900 s), and `broker_readback` (outputs `positions`, 900 s). The engine header states funding-filtered sleeves are unfed without funding, never fake-fed; funding-off controls are not vetoed by a funding outage. The existing card lists the underlying data for this family; the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_batch7.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_enjusdt_absorption_base_fixed16_volume1pct.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_enjusdt_absorption_base_fixed16_volume1pct` from `config/sleeves.json` (module `adapters3.aster_r19_enjusdt_absorption_base_fixed16_volume1pct`, cadence 300, session always, $10,000 slice, inputs as listed in Configuration, parked false, with the roster params shown there).
4. Wire the producers above so the view contains `bars` under one of the ENJUSDT keys listed in the algorithm, `positions` from broker readback, a `slice`, a current time in the view or context, and `funding` for ENJUSDT if this sleeve's family is funding-gated.
5. First evaluation: call `adapters3.aster_r19_enjusdt_absorption_base_fixed16_volume1pct.evaluate(view, ctx)`; it delegates to `desk3.aster_batch7.evaluate("aster_r19_enjusdt_absorption_base_fixed16_volume1pct", view, ctx)`. Run every 300 seconds; the first check is the exit scan for an ENJUSDT position, then the entry signal, funding and freshness tests in that order.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check the entry signal for family `absorption_base` exactly as defined above, including its bar-count requirement.
- Check the funding condition for family `absorption_base` exactly as stated, including that absent funding is never treated as 0 where a gate applies.
- Check the freshness gate: with the switch ON, an age below 0, above 900 seconds, or unparseable blocks entry, and an age in 0 to 900 allows it; with the switch OFF, age does not block.
- Check entry quantity: cash divided by (price times 1.001), with the cap for this sleeve applied exactly as stated (volume1pct), rounded to 8 decimals, and that a result at or below 0 produces no intent.
- Check that intents carry the symbol `ENJUSDT` in this engine (no broker-symbol translation is present in `desk3/aster_batch7.py`).
- Check the fixed exit: a position held 16 hours or more exits at the deadline even when bars or funding are missing, a position held less than 16 hours does not, and holding a position blocks a new entry.
