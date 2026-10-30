# aster_r19_linkusdt_absorption_base_fixed16_volume1pct - RECREATE

Provenance: Ausar crypto research: the original absorption books and the R19 funding-filter books (Source row of the existing Test doc `strategies/ausar/crypto-absorption.md`); v3 engine header in `desk3/aster_b11_crypto.py` states the rules were source-verified against the staged archive r19_crypto.py, absorption signals.py and crypto_rules.json.

## What this sleeve is

This sleeve buys LINKUSDT crypto spot on a confirmed 4 hour absorption pattern: a high-volume down shock bar followed by a bar closing back above the shock midpoint. This specific variant is `aster_r19_linkusdt_absorption_base_fixed16_volume1pct`: family `absorption_base` (the funding-off control), fixed 16 hour exit, and sizing cap `volume1pct`. It runs 24 hours on a 14400 second cadence with a $10,000 slice, long only.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py` sets `SLEEVE_ID="aster_r19_linkusdt_absorption_base_fixed16_volume1pct"` and delegates to `desk3.aster_b11_crypto.evaluate`. The SPECS row in that engine for this sleeve is exactly: `sym="LINKUSDT", fam="absorption_base", cap="volume1pct", hold_h=16`. There is no exit field in this SPECS row; the engine header and the exit code implement fixed16 for all batch 11 arms. Engine fee constant `FEE = 0.001` (10 bps). This engine does not translate the symbol: intents carry `LINKUSDT` as written in the code.

Evaluation order in `evaluate`:

1. Load inputs: bars via `_bars` (view `bars` keys `LINKUSDT|4Hour`, then `LINKUSDT|4h`, then `LINKUSDT|240min`, then `LINKUSDT`, sorted by time); funding via `_funding` (`view.funding[LINKUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, with the code default if absent).
2. Exit handling first: `poss` is the list of all positions with quantity not zero (the list itself is not symbol-filtered). The loop skips a position whose symbol is not `LINKUSDT`, is not None, and does not contain `LINKUSDT` as a substring. For each remaining position, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0. If held >= 16, exit with reason `aster_deadline_fixed16`.
   - An exit intent is an `Intent(kind="exit", symbol="LINKUSDT", qty=absolute quantity, price_hint=last bar close if bars exist otherwise the position avg_price or 0, converted to None if that value is 0, side="sell", position_intent="sell_to_close")` with the reason naming the sleeve.
   - If any exit is produced, or `poss` is non-empty at all (including a position the loop skipped for a different symbol), return the exits (possibly empty) and do not evaluate an entry, exactly as the code's `if out or poss: return out` does.
3. Entry signal (no positions at all): Absorption signal `_absorption(brs)` (same definition in all three engines used in this batch): at least 300 bars are required. Volumes and closes are taken in bar order; EMA20 of volume and EMA50 of close use `_ema` seeded on the first value with alpha = 2 / (n + 1), current-inclusive. The shock bar is the second-last bar: its volume > 2 times EMA20(volume) at that bar, its close < its open, and its close < EMA50(close) at that bar. The confirmation is the last bar: close > open and close > (shock high + shock low) / 2. All conditions must hold.
4. Funding gate: none for this sleeve. Family `absorption_base` is the funding-off control in the engine header and in the code: the negative and non-negative funding checks in `evaluate` apply only to those named families, so funding never gates this sleeve even though `funding` is a declared input.
5. Stale-signal gate (ENH-B8 in the engine header, default ON; switch `view["extra"]["aster_edge"]["aster_r19_linkusdt_absorption_base_fixed16_volume1pct"]["stale_signal_gate"]`, where only the value False turns it off): signal age in hours is `(now - (last bar time + 4 hours)) / 3600`. If the switch is OFF, the gate never blocks. If the switch is ON: an age that is None (no parseable bar time) does not block, an age <= 4.0 does not block, and an age > 4.0 blocks the entry. A paired record is appended to `view["extra"]["aster_edge_journal"]` when that journal is supplied as a list. Exits are never gated by this rule.
6. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Quantity = `cash * (1 - 0.001) / price`. Cap for this sleeve: volume1pct: quantity is the minimum of the full cash quantity and 1 percent of the volume of the second-last bar (`0.01 * bars[-2].v` in code; the engine header describes this as 1 percent of the preceding 4h bar volume). Reject if quantity <= 0.
7. Entry intent: `Intent(kind="enter", symbol="LINKUSDT", qty=round(quantity, 8), price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, family `absorption_base`, the close, the funding value and the cap `volume1pct`. Note the quantity is rounded to 8 decimals in this engine, not floored to a whole unit.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py`, `sleeves/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py`, and `integration/aster_r19_linkusdt_absorption_base_fixed16_volume1pct_adapter.py`. Desk original: `adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py`, delegating to `desk3.aster_b11_crypto.evaluate`.
- Shared engine that runs the logic: `desk3/aster_b11_crypto.py` (contains the SPECS row for this sleeve, `_absorption`, `_stale_blocked` and `evaluate`).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by the engine). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/crypto-absorption.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_linkusdt_absorption_base_fixed16_volume1pct`).

## Configuration

- Sleeve id: `aster_r19_linkusdt_absorption_base_fixed16_volume1pct`; module: `adapters3.aster_r19_linkusdt_absorption_base_fixed16_volume1pct` (roster row in desk `config/sleeves.json`).
- Universe: LINKUSDT (in code, `sym="LINKUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all rows, and this row is the LINKUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed UTC 4 hour bars). Session: `24h`. Cadence: 14400 seconds (`cadence_s=14400`, 4 hours).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `volume1pct` and fee 0.001 as in the sizing step above. Roster `params` for this row is empty; the parameters live in the engine SPECS row above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS = ("bars", "funding", "positions")` in `desk3/aster_b11_crypto.py`, also imported by the adapter): `bars`, `funding`, `positions`.

No producer tuple with freshness SLAs is declared in `desk3/aster_b11_crypto.py` or the adapter, so no SLA is stated here. The engine header states funding is a declared producer input and funding-gated sleeves refuse entry without it; this `absorption_base` sleeve is not funding-gated. The existing card lists the underlying data as Binance spot 4 hour klines, book ticker and last trade, plus funding for the filtered R19 books; the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_b11_crypto.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_linkusdt_absorption_base_fixed16_volume1pct` from `config/sleeves.json` (module `adapters3.aster_r19_linkusdt_absorption_base_fixed16_volume1pct`, cadence 14400, session 24h, $10,000 slice, inputs bars/funding/positions, parked false).
4. Wire inputs so the view contains `bars` under one of the LINKUSDT keys listed in the algorithm (at least 300 bars for an absorption entry), `funding` for LINKUSDT, `positions` from broker readback, a `slice`, and a current time in the view or context.
5. First evaluation: call `adapters3.aster_r19_linkusdt_absorption_base_fixed16_volume1pct.evaluate(view, ctx)`; it delegates to `desk3.aster_b11_crypto.evaluate("aster_r19_linkusdt_absorption_base_fixed16_volume1pct", view, ctx)`. Run every 14400 seconds, 24 hours; the first check is the exit and position-blocking scan, then the absorption, stale-signal and sizing tests in that order.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check that fewer than 300 bars, a shock bar failing any one of volume, close below open, or close below EMA50, or a confirmation bar failing close above open or close above the shock midpoint, each independently blocks entry.
- Check that funding, whether absent, negative or non-negative, does not block this `absorption_base` sleeve.
- Check the stale-signal gate: with the switch ON, an age over 4.0 hours blocks and an age at or below 4.0 hours or an unparseable bar time does not; with the switch set to False, age never blocks.
- Check entry quantity: cash times 0.999 divided by price, with the cap for this sleeve applied exactly as stated (volume1pct), rounded to 8 decimals, and that a result at or below 0 produces no intent.
- Check that intents carry the symbol `LINKUSDT` in this engine (no broker-symbol translation is present in `desk3/aster_b11_crypto.py`).
- Check the fixed exit and blocking rule: a LINKUSDT position held 16 hours or more exits at the deadline even when bars or funding are missing, and any non-zero position at all (even a different symbol the loop skips) blocks a new entry, exactly as `if out or poss` does in the code.
