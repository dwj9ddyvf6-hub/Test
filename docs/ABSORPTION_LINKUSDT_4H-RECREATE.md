# ABSORPTION_LINKUSDT_4H: Recreation Package

## Provenance

- ALL-SLEEVES accounting: this canonical id is the deployed original-book id for the LINKUSDT four-hour confirmed absorption strategy (aliases include ausar_pb6 and the R19 LINKUSDT absorption / breakout / squeeze variant ids listed in the accounting entry). Accounting algorithm grade for the merged entry: FULL, sources ausar_map params/variant and md2 catalog entry/exit/strategy text. The accounting entry for this id records, for the base form: family absorption_base, exit_policy fixed16, capacities fullcash and volume1pct, symbol LINKUSDT, fee_bps 10; the original book documented here is the fullcash form (card: original books size at 100% of book cash).
- Test records: strategy card `strategies/ausar/crypto-absorption.md`, algorithm doc `docs/ASTER_ABS_LINK_4H-ALGORITHM.md` (derived from the sleeve code 2026-10-29), wrapper `sleeves/aster_abs_link_4h.py`, engine `desk3/aster_batch1.py` SPECS aster_abs_link_4h (kind absorption, symbol LINKUSDT, cadence_s 14400, session 24h).
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

A four-hour confirmed-absorption mean-reversion book on LINKUSDT spot: it buys the 4-hour bar that closes back above the midpoint of a high-volume down bar, then sells 16 hours later (card summary).

## Full algorithm

Shock and confirmation (card `strategies/ausar/crypto-absorption.md` and engine `desk3/aster_batch1.py`, Decimal EMAs seeded at the first bar, current-inclusive):
- Shock bar: volume > 2 x EMA20(volume) AND close < open AND close < EMA50(close).
- Confirmation bar (the immediately following completed bar): close > open AND close > (shock high + shock low) / 2.
- Warmup: no entry unless at least 300 completed bars.
- Entry (engine `desk3/aster_batch1.py` `_eval_absorption`): there is no timing window on entry. The entry fires on the first sleeve evaluation that sees the confirming last bar. Entry price is the quote ask when a quote with an ask is present; otherwise it falls back to the last bar close (`bars[-1]` close). If that price is missing or not positive, no entry is emitted. The desk engine also carries a one-bar catch-up, on by default: when the confirmation was one bar ago and the current close still holds the shock midpoint, it buys late and keeps the original 16 h deadline (card Notes; engine `_eval_absorption`).
- Exit: sell from 16 h after the confirmation bar's close; the deadline never resets; partial exits retain it. No stop, no pyramiding. Exit price (engine `_eval_absorption`) is the quote bid when a quote with a bid is present; otherwise it falls back to the last bar close. Exit deadline (engine `_eval_absorption`) is taken, in order, from a stored `exit_due_at` or `deadline_at` when present, or from a stored `confirm_close_at` plus 16 h; when no stored deadline exists, it falls back to `opened_at` plus 16 h. When no deadline can be derived, no exit is emitted.
- Sizing (engine `_eval_absorption`): quantity is the raw fractional value `cash / (price * 1.001)`, which is 100% of book cash including the 10 bps fee. There is no lot floor and no cap by the displayed ask size. If the resulting quantity is not positive, no entry is emitted. Sleeve slice in the engine: $10,000, cadence 14400 s, session 24h.

## Files in this repo

- This package: `docs/ABSORPTION_LINKUSDT_4H-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Algorithm doc: `docs/ASTER_ABS_LINK_4H-ALGORITHM.md`
- Running code (already in Test; nothing vendored): `sleeves/aster_abs_link_4h.py` (wrapper, SLEEVE_ID aster_abs_link_4h), `adapters3/aster_abs_link_4h.py` and `integration/aster_abs_link_4h_adapter.py` (same wrapper), `desk3/aster_batch1.py` (shared engine, `_eval_absorption`).

## Configuration

- Universe: LINKUSDT only (Binance spot). Timeframe: 4h bars. Slice: $10,000 (engine/algorithm doc). Cadence: 14400 s. Session: 24h, not flat by close. Fee: 10 bps per side.
- State: held position and its stored confirmation-anchored exit deadline.

## Data inputs

Binance spot completed 4h klines (at least 300 bars warmup), book ticker / depth quote and last trade (card and engine INPUTS bars, quotes, positions).

## Install and run

1. Clone this repository (Test).
2. Import the wrapper: `from sleeves.aster_abs_link_4h import evaluate`, which delegates to `desk3/aster_batch1.py` `evaluate(SLEEVE_ID, view, ctx)`.
3. Configure symbol LINKUSDT, slice cash $10,000 and the fixed16 exit.
4. Serve completed 4h bars, quotes and positions.
5. Run on the 14400 s cadence; it emits at most one entry per confirmed signal and the fixed-deadline exit.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A shock bar (volume > 2 x EMA20 volume, close < open, close < EMA50 close) followed by a confirmation bar (close > open, close above the shock midpoint), after at least 300 warmup bars, produces exactly one entry on the first evaluation that sees the confirming last bar (no 300-second or other timing window), priced at the quote ask when present and otherwise at the last bar close, sized as the raw fractional quantity `cash / (price * 1.001)` (100% of book cash including the 10 bps fee, with no lot floor and no ask-size cap).
- A shock bar without a following confirmation bar, or any signal before 300 warmup bars, produces no entry.
- A held position produces exactly one full exit at the first eligible evaluation at or after the exit deadline, and no new entry while held. The exit price is the quote bid when present and otherwise the last bar close. The exit deadline is the stored `exit_due_at` or `deadline_at` when present, otherwise a stored `confirm_close_at` plus 16 h, otherwise (when no stored deadline exists) `opened_at` plus 16 h; the normal stored deadline is confirmation close + 16 h.
