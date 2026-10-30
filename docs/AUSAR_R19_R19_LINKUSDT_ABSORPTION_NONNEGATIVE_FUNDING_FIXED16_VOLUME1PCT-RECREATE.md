# ausar_r19_R19_LINKUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_VOLUME1PCT: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Absorption with nonnegative funding · LINKUSDT, 16-hour hold, 1% volume cap", type mean reversion, family absorption_nonnegative_funding. Algorithm grade in the accounting: PARTIAL. Recorded accounting entry text: "Requires confirmed absorption with at least 300 indicator bars and an observed funding rate at least zero." Recorded accounting gaps: the exit rule and (for the installed-alias entries) sizing were "not in the record" in the accounting's consulted sources; both are in fact recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- This canonical id is the installed-alias entry (accounting source: md2 catalog, status installed). The accounting records no separate parameters for this alias entry (parameters: not in the record for this entry); the ausar_map parameters for the underlying R19 book are family absorption_nonnegative_funding, exit_policy fixed16, capacity volume1pct, symbol LINKUSDT, fee_bps 10.
- Test strategy card: `strategies/ausar/crypto-absorption.md` (the R19 funding-filter books: funding filter none / negative / nonnegative, entry 4 h after the confirmation bar closes in a 5-minute window, sell 16 h after entry, sizing fullcash or volume1pct).
- Status history in the accounting: installed (md2_catalog).

## What this strategy is

A 4-hour confirmed-absorption mean-reversion book on LINKUSDT spot (Binance USDT spot), filtered to enter only when the latest actually-observed funding rate is nonnegative (>= 0), holding for a fixed 16 hours, sized by 1% of the entry bar's volume cap. No stop, no pyramiding.

## Full algorithm

Evaluation order, from the card and the running engine in this repo:

1. Owned-exit check first: if a position is held and its fixed deadline has arrived (entry time + 16 h; the deadline is stored at entry and never resets, and it fires even when bars or funding are missing), sell the full held quantity at the first eligible observed bid / latest price reference. Partial exits retain the original deadline. If a position is held and the deadline has not arrived, emit nothing else.
2. Shock and confirmation (archive `strategies/absorption/signals.py` advance(), Decimal arithmetic, current-inclusive EMAs seeded at the first bar):
- EMA20 of volume: `ema_v = v` on the first bar, else `ema_v = (2*v + 19*ema_v)/21`. EMA50 of close: `ema_c = c` on the first bar, else `ema_c = (2*c + 49*ema_c)/51`.
- Shock bar: `volume > 2 * EMA20(volume)` AND `close < open` AND `close < EMA50(close)`.
- Confirmation bar (the immediately following completed bar): `close > open` AND `close > (shock high + shock low) / 2`. No confirmation volume or EMA filter.
- Warmup: no entry unless the indicator count is at least 300 completed bars.
3. Funding gate (this variant): the latest actually-observed funding rate for LINKUSDT at the signal close must exist and be >= 0. Missing funding is never assumed to be 0: an unobserved rate blocks the entry (the sleeve is UNFED without its declared funding producer input).
4. Entry timing: the signal is read on the confirmation bar; entry follows 4 h after the confirmation bar closes (the archive `entry_delay_hours_after_signal_close=4`), inside the archive 300-second entry window. Engine enhancements present in the Test code and on by default are recorded in the engine source (for the ADA engine: the entry window extends to one full 3600 s cadence, ENH-ABS-WINDOW-20261024, and funding is revalidated at the entry bar, refusing entry if the nonnegative condition flipped during the delay; for the ENJ engine: entries only while the signal bar's close is fresh, age in [0, 900 s], ENH-ASTER-R19-B7-20261024; for the LINK engine: a stale-signal gate refusing entries when the signal bar closed more than 4 h ago, ENH-B8). Each enhancement is switchable off in the engine, restoring the pre-change rule.
5. Entry price reference: the entry bar's close (the ADA engine) / the signal close (the ENJ and LINK v3 translations size off the signal close, per their engine headers); the master-desk form buys at the ask.
6. Sizing (volume1pct): fullcash quantity (slice cash / (ask x (1 + 10bp fee)) in the source form; the v3 engine sizes off the signal close) additionally capped at 1% of the preceding 4h bar's volume. Fee: 10 bps per side (0.001). Quantities floor to the native lot grid (the ADA engine floors to whole ADA units).
7. Exit: fixed16 only: sell at or after entry + 16 h. No stop, no target, no pyramiding, one position at a time.

Accounting-recorded gap note: the accounting graded this algorithm PARTIAL with the exit rule "not in the record" in its consulted sources; the exit rule above is from the Test card and the Test code, not from the accounting.

## Files in this repo

- This package: `docs/AUSAR_R19_R19_LINKUSDT_ABSORPTION_NONNEGATIVE_FUNDING_FIXED16_VOLUME1PCT-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_r19_linkusdtusdt_absorption_nonnegative_funding_fixed16_volume1pct.py` (wrapper; delegates to the batch engine below)
  - `adapters3/aster_r19_linkusdtusdt_absorption_nonnegative_funding_fixed16_volume1pct.py` and `integration/aster_r19_linkusdtusdt_absorption_nonnegative_funding_fixed16_volume1pct_adapter.py` (same wrapper)
  - `desk3/aster_b11_crypto.py` (shared engine, SPECS row for this sleeve)
- Master-desk family form (also already in Test): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_crypto.py` (class `R19Crypto`; builds the same native rows with the persistent EMA recurrence, funding capture, and the R19 ledger execution).

## Configuration

- Universe: LINKUSDT only (Binance spot). Asset class: crypto spot. Timeframe: native UTC 4h bars.
- Family: absorption_nonnegative_funding. Exit policy: fixed16 (16-hour hold). Capacity: volume1pct. Fee: 10 bps per side.
- Engine: `desk3/aster_b11_crypto.py` (Aster crypto batch 11, LINKUSDT fixed16 arms); the wrapper's SPECS row fixes sym LINKUSDT, fam absorption_nonnegative_funding, hold_h 16.
- State: held position, its entry time and its stored exit deadline; consumed-signal / ledger state in the master-desk form. No other sleeve-private state is recorded.

## Data inputs

Binance spot completed 4h klines (at least 300 bars of indicator warmup; the master-desk capture reads 340 bars), book ticker / depth quote and last trade, native lot/tick/notional filters, and observed USD-M funding history for LINKUSDT. The accounting's recorded filter text agrees: completed spot OHLCV, observed funding context and actual quote.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Import the wrapper: `from sleeves.aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct import evaluate`, which delegates to `desk3/aster_b11_crypto.py` `evaluate(SLEEVE_ID, view, ctx)`. The view carries completed LINKUSDT 4h bars, positions, and funding.
3. Configure the sleeve with family absorption_nonnegative_funding, capacity volume1pct, symbol LINKUSDT, fee 10 bps per side, and the fixed16 exit.
4. Serve the declared inputs (bars, positions, and funding for this funding-filtered family; without funding the sleeve correctly refuses every entry).
5. Run the desk dispatcher / evaluate function on the sleeve's cadence; it emits at most one entry intent per confirmed signal and the fixed-deadline exit intent.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A bar sequence with a shock bar (volume > 2 x EMA20 volume, close < open, close < EMA50 close) followed by a confirmation bar (close > open, close above the shock midpoint), with at least 300 warmup bars and an observed funding rate of exactly 0, produces exactly one entry 4 h after the confirmation close, sized per the volume1pct rule net of the 10 bps fee.
- The same sequence with an observed funding rate below 0, or with funding unobserved, produces no entry.
- A shock bar without a following confirmation bar produces no entry; an entry before 300 warmup bars never occurs.
- A held position produces no new entry, and produces exactly one full exit at the first evaluation at or after entry + 16 h, even if bars or funding are then missing.
