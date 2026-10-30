# aster_r19_linkusdt_breakout_base_fixed16_volume1pct - RECREATE

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row of the existing Test doc `strategies/ausar/r19-crypto-breakout.md`); v3 engine header in `desk3/aster_b12_crypto.py` describes batch 12 as source-verified against the staged archive r19_crypto.py and crypto_rules.json, with shared primitives imported from the batch 11 engine.

## What this sleeve is

This sleeve buys LINKUSDT crypto spot on a completed 4 hour breakout above the prior 20 bar high with no funding filter (the price-only breakout_base control). This specific variant is `aster_r19_linkusdt_breakout_base_fixed16_volume1pct`: family `breakout_base`, exit rule `fixed16` with a 16 hour hold, and sizing cap `volume1pct`. It runs 24 hours on a 14400 second cadence with a $10,000 slice, long only, one position per book.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_r19_linkusdt_breakout_base_fixed16_volume1pct.py` sets `SLEEVE_ID="aster_r19_linkusdt_breakout_base_fixed16_volume1pct"` and delegates to `desk3.aster_b12_crypto.evaluate` (`INPUTS_BREAKOUT` as `INPUTS`). The SPECS row in that engine for this sleeve is exactly: `sym="LINKUSDT", fam="breakout_base", exit="fixed16", cap="volume1pct", hold_h=16`. Engine fee constant `FEE = 0.001` (10 bps). Shared bar, funding, now, timestamp, breakout and stale-gate helpers are imported from `desk3.aster_b11_crypto` (one source of truth, per the batch 12 header).

Evaluation order in `evaluate(sid, view, ctx)`:

1. Load inputs: bars via `_bars` imported from batch 11 (view `bars` keys `LINKUSDT|4Hour`, then `LINKUSDT|4h`, then `LINKUSDT|240min`, then `LINKUSDT`, sorted by bar time); funding via `_funding` (`view.funding[LINKUSDT]`, unwrapping a dict `rate`, otherwise `view.extra.funding_rate`, otherwise None); current time via `_now` (view or ctx `now`, default `"2026-10-24T00:00:00+00:00"` recorded in the batch 11 helper if absent).
2. Exit handling first, restricted to this sleeve's own symbol: positions are filtered to quantity not zero. For each such position whose symbol is `LINKUSDT` or None, or whose symbol string contains `LINKUSDT`, held hours are `(now - opened_at) / 3600` if an open time (`opened_at` or `entry_time`) parses, otherwise `age_hours` or 0.
- Fixed deadline only: if held hours >= 16, exit with a deadline reason naming `fixed16` and 16h. No structural exit is evaluated for this sleeve, and there is no stop. The deadline fires even when bars or funding are missing.
   - An exit intent is an `Intent(kind="exit", symbol="LINKUSDT", qty=absolute quantity, price_hint=last bar close if bars exist otherwise position average price, side="sell", position_intent="sell_to_close")` with the reason prefixed by the sleeve id. This engine performs no broker-symbol translation; the symbol stays `LINKUSDT`.
   - If any exit is produced, or any position remains in the filtered positions list, return the exits (possibly empty) and do not evaluate an entry.
3. Entry (no position), in code order:
   - Breakout: `_breakout` requires at least 21 bars and the last bar close strictly greater than the maximum high of the prior 20 bars (`bars[-21:-1]`). Otherwise no entry. This check runs before the funding gate in batch 12.
- Funding never gates this family: the code checks `spec["fam"] == "nfs"` only, so `breakout_base` entries ignore funding entirely. Its adapter imports `INPUTS_BREAKOUT` (bars, positions) instead of the full INPUTS tuple.
   - Stale-signal gate (below) must not block.
4. Stale-signal entry gate (ENH-B8, in `desk3/aster_b11_crypto.py`, applied by both engines; default ON): signal age is `(now - (last bar time + 4 hours))` in hours. If the switch is ON and age > 4.0 hours (`STALE_GATE_MAX_AGE_H = 4.0`), the entry is refused. The switch is `extra["aster_edge"][<sleeve>]["stale_signal_gate"]`; setting it to False restores the pre-change rule exactly. Exits are untouched by this gate. If the caller supplies `extra["aster_edge_journal"]` as a list, a paired record with the enhanced decision, the shadow faithful decision and the signal age is appended; the shadow arm never emits an intent.
5. Sizing: price = last bar close. Cash = `view.slice.cash_usd` if present, otherwise 10000. Full quantity = `cash * (1 - 0.001) / price`. Cap for this sleeve: volume1pct: quantity is the minimum of the full cash quantity and 1 percent of the volume of the second-last bar (`0.01 * bars[-2].v` in code; the engine header describes this as 1 percent of the preceding 4h bar volume). Reject if quantity <= 0.
6. Entry intent: `Intent(kind="enter", symbol="LINKUSDT", qty=round(quantity, 8), price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve, the family `breakout_base`, the breakout close, the funding value and the cap `volume1pct`.

Differences from the family card that the v3 code implements (recorded in the card Notes and the engine headers): the v3 engine buys at the signal bar close when it evaluates, not 4 hours later; its deadlines count from the fill / open time; and for volume1pct it reads the bar before the signal bar (code: `bars[-2]`). The code rules above are the recreation standard.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_r19_linkusdt_breakout_base_fixed16_volume1pct.py`, `sleeves/aster_r19_linkusdt_breakout_base_fixed16_volume1pct.py`, and `integration/aster_r19_linkusdt_breakout_base_fixed16_volume1pct_adapter.py`. Desk original: `adapters3/aster_r19_linkusdt_breakout_base_fixed16_volume1pct.py`, delegating to `desk3.aster_b12_crypto.evaluate`.
- Shared engines that run the logic: `desk3/aster_b12_crypto.py` (contains the SPECS row for this sleeve and `evaluate`; engines map status already_present) and `desk3/aster_b11_crypto.py` (imported by aster_b12 for `_bars`, `_funding`, `_now`, `_ts`, `_breakout` and `_stale_blocked`; engines map status already_present).
- Engine dependency not in this repo at build time: desk `desk3/contract.py` (the `Intent` class imported by both crypto engines). Its intended repo path in the engines map is `engines/desk3/contract.py`, recorded with status gate_blocked, and it was absent from the fresh Test tree. A recreation must supply an `Intent` with the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent) from that source; do not invent its other behaviour.
- Existing family card: `strategies/ausar/r19-crypto-breakout.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_r19_linkusdt_breakout_base_fixed16_volume1pct`).

## Configuration

- Sleeve id: `aster_r19_linkusdt_breakout_base_fixed16_volume1pct`; module: `adapters3.aster_r19_linkusdt_breakout_base_fixed16_volume1pct` (roster row in desk `config/sleeves.json`).
- Universe: LINKUSDT (in code, `sym="LINKUSDT"`; the family card universe is ADAUSDT, ENJUSDT and LINKUSDT across all R19 rows, and this row is the LINKUSDT row). Asset: crypto spot.
- Timeframe: 4h (completed UTC 4 hour bars). Session: `24h`. Cadence: 14400 seconds (`cadence_s=14400`, 4 hours).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; cap `volume1pct` and fee 0.001 as in the sizing step above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row for this sleeve: `bars`, `positions`. The engine declares `INPUTS = ("bars", "funding", "positions")` and, for breakout_base, `INPUTS_BREAKOUT = ("bars", "positions")` in `desk3/aster_b12_crypto.py`; the adapter for this sleeve imports `INPUTS_BREAKOUT` as `INPUTS`.

The engine header states funding is a declared producer input: absent funding means the NFS sleeves land visibly UNFED, never fake-fed. No producer tuple with freshness SLAs is declared in `desk3/aster_b12_crypto.py`, `desk3/aster_b11_crypto.py` or the adapter, so no SLA is stated here. The existing card lists the underlying data as Binance spot 4h klines, depth and last trade, and Binance USD-M funding history (with a relay note for US hosts); the v3 function itself reads only the bars, funding and positions supplied in the view, plus the slice cash and the current time.

## Install and run

1. Place `desk3/aster_b12_crypto.py` and `desk3/aster_b11_crypto.py` in a fresh desk under `desk3/`, and supply `desk3/contract.py` (see the dependency note in Files; its repo copy is gate_blocked and absent, so obtain it from the desk source tree, read only, do not modify the desk).
2. Place the adapter as `adapters3/aster_r19_linkusdt_breakout_base_fixed16_volume1pct.py` (copy any repo copy listed above).
3. Register the roster row for `aster_r19_linkusdt_breakout_base_fixed16_volume1pct` from `config/sleeves.json` (module `adapters3.aster_r19_linkusdt_breakout_base_fixed16_volume1pct`, cadence 14400, session 24h, $10,000 slice, inputs `bars`, `positions`, parked false).
4. Wire inputs so the view contains `bars` under one of the LINKUSDT keys listed in the algorithm (at least 21 bars for an entry), `funding` for LINKUSDT where the family requires it, `positions` from broker readback, a `slice`, and a current time in the view or context.
5. First evaluation: call `adapters3.aster_r19_linkusdt_breakout_base_fixed16_volume1pct.evaluate(view, ctx)`; it delegates to `desk3.aster_b12_crypto.evaluate("aster_r19_linkusdt_breakout_base_fixed16_volume1pct", view, ctx)`. Run every 14400 seconds, 24 hours; the first check is the exit scan for a LINKUSDT position, then the breakout entry test (funding does not gate entry).

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check that entry is blocked when fewer than 21 bars are present and when the last close is at or below the maximum high of the prior 20 bars.
- Check the funding gate for this sleeve: funding does not gate entry; for `nfs`, absent funding also blocks entry.
- Check the stale-signal gate: with the switch ON, a signal bar that closed more than 4 hours before now produces no entry; with the switch OFF, the same opportunity is evaluated under the faithful rule.
- Check entry quantity: cash times 0.999 divided by price, with the cap for this sleeve applied exactly as stated (volume1pct), rounded to 8 decimals in the intent, and that a result of 0 or less produces no intent.
- Check that intents carry symbol `LINKUSDT` (this engine performs no broker-symbol translation), and that holding a LINKUSDT position blocks a new entry while a position in a different symbol is not exited by this sleeve.
- Check that a LINKUSDT position held 16 hours or more exits with the fixed16 deadline reason even when bars and funding are absent, and that no structural exit fires for this sleeve.
