# ausar_g_ABSORPTION_ENJUSDT_4H: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Four-hour confirmed absorption · ENJUSDT", type mean reversion, family confirmed_absorption. Algorithm grade in the accounting: PARTIAL; recorded gap: "sizing not recorded in any consulted source". The accounting records the full entry and exit text for this id (quoted in the algorithm section); sizing is in fact recorded in the Test strategy card and the running Test code cited below.
- Test strategy card: `strategies/ausar/crypto-absorption.md` (the original books: ENJ and LINK; buy at the ask within 300 s of the confirmation bar's close; sell at the bid from 16 h after the confirmation bar's close; sizing 100% of book cash including the 10 bps fee, floored to the lot, capped by the displayed ask size).
- Test algorithm doc derived from the sleeve code on 2026-10-29: `docs/ASTER_ABS_ENJ_4H-ALGORITHM.md`.
- Status history in the accounting: installed (md2_catalog).

## What this strategy is

The original (non-R19) four-hour confirmed-absorption book on ENJUSDT spot: it buys the 4-hour bar that closes back above the midpoint of a high-volume down bar, then sells 16 hours after the confirmation bar completed. No funding filter, no stop, no pyramiding.

## Full algorithm

Evaluation order, from the accounting entry/exit text, the card, and the running engine `desk3/aster_batch1.py` (`_eval_absorption`):

1. Owned-exit check first: if a position is held, its deadline is the confirmation bar's completion + 16 h (stored at entry as `confirm_close_at` / `exit_due_at`; it never resets, and partial exits retain it). At the first evaluation at or after the deadline, sell the full held quantity at the observed bid if a quote is present, else at the latest bar close. A held position that is not yet due produces no other intent.
2. Warmup: no entry with fewer than 300 completed 4h bars.
3. Indicators (Decimal, precision 34, current-inclusive, seeded at the first bar): EMA20 of volume, `ema_v = (2*v + 19*ema_v)/21` after seeding; EMA50 of close, `ema_c = (2*c + 49*ema_c)/51` after seeding.
4. Shock bar: `volume > 2 * EMA20(volume)` AND `close < open` AND `close < EMA50(close)`.
5. Confirmation (the immediately following bar): `close > open` AND `close > (shock high + shock low) / 2`. No confirmation volume or EMA filter (the accounting states this explicitly).
6. Entry: buy at the ask within 300 s of the confirmation bar's close (card); the v3 engine prices the entry at the quote ask when a quote is present, else at the last bar's close, and buys at the latest close when it evaluates. Engine enhancement present in the Test code and on by default (ENH-ABS4H-CATCHUP-20261024): a one-bar catch-up: if the confirmation fired one bar ago and the current bar still closes at or above the shock bar's midpoint, enter at the current close, with the exit deadline still anchored to the original confirmation close + 16 h. Switching the enhancement off restores the confirmation-bar-only rule.
7. Sizing: 100% of book cash including the 10 bps fee allowance: quantity = cash / (price x 1.001), floored to the lot and capped by the displayed ask size (card). The engine's sleeve capital is $10,000.
8. Exit: fixed: the first eligible observed bid at or after confirmation completion + 16 h. No stop, no target, no pyramiding.

Accounting-recorded gap note: the accounting graded this algorithm PARTIAL with sizing "not in the record" in its consulted sources; the sizing above is from the Test card and the Test code, not from the accounting.

## Files in this repo

- This package: `docs/AUSAR_G_ABSORPTION_ENJUSDT_4H-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Algorithm doc: `docs/ASTER_ABS_ENJ_4H-ALGORITHM.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_abs_enj_4h.py` (wrapper; SLEEVE_ID `aster_abs_enj_4h`)
  - `adapters3/aster_abs_enj_4h.py` and `integration/aster_abs_enj_4h_adapter.py` (same wrapper)
  - `desk3/aster_batch1.py` (shared engine; SPECS row kind absorption, symbol ENJUSDT; `_eval_absorption`)
- Master-desk family form (also already in Test): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_crypto.py` (the native-row recurrence the capture builds).

## Configuration

- Universe: ENJUSDT only (Binance spot). Asset class: crypto spot. Timeframe: native UTC 4h bars.
- Sleeve capital: $10,000 (engine spec and algorithm doc agree). Cadence: 14400 s. Session: 24h. Flat by close: no.
- Fee: 10 bps per side allowance in the sizing formula.
- State: per-symbol record of the confirmation close time, the exit deadline and the entry time (the engine's sleeve state), plus the broker position.

## Data inputs

Binance spot completed 4h bars (at least 300 for warmup), quotes (bid/ask; producers in the engine: bars 900 s freshness, quotes 60 s) and positions from broker readback (900 s). The accounting's recorded filter text: posted runtime inputs; the card records Binance spot 4h klines, book ticker and last trade.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Import the wrapper: `from sleeves.aster_abs_enj_4h import evaluate`, which delegates to `desk3/aster_batch1.py` `evaluate(SLEEVE_ID, view, ctx)` with SLEEVE_ID `aster_abs_enj_4h`.
3. Configure the cell with the engine SPECS row for `aster_abs_enj_4h` (kind absorption, symbol ENJUSDT, capital $10,000, cadence 14400 s, session 24h).
4. Serve completed ENJUSDT 4h bars, quotes and positions.
5. Run on the 14400 s cadence; verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- With at least 300 completed bars, a shock bar followed immediately by a confirmation bar produces exactly one buy at the ask, sized at cash / (price x 1.001) floored to the lot and capped by the displayed ask size.
- A shock bar without the following confirmation, or any sequence before 300 bars, produces no entry.
- The position exits in full at the first evaluation at or after confirmation completion + 16 h, at the observed bid; a partial exit keeps the same deadline.
- With the catch-up enhancement on, a confirmation one bar old whose current close still holds the shock midpoint enters late with the original deadline; with it off, that opportunity produces no entry.
