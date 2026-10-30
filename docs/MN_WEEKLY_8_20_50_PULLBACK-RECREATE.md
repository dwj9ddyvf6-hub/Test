# mn-weekly-8-20-50-pullback: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Weekly 8/20/50 pullback", type mean reversion, family midna, style evidence "Trend pullback", universe "19 ETFs (the funds of the public Portfolio T page)", US ETFs, timeframe "1w signal · 1d management", creator "Midna's TypeScript desk: the weekly 8/20/50 pullback, ported line for line; a recorder made a book by the owner's D32". Test catalog entry `mn-weekly-8-20-50-pullback`, status waiting (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/midna/mn-weekly-8-20-50-pullback.md`. The card does record entry, exit and sizing in full (quoted below) and lists both the ported code and the TypeScript source, all in this repo. The accounting gaps are gaps of the accounting pass, not of this repo's record.
- Card notes: the source study left this book unfunded (a performance verdict); ruling D32 (2026-10-26) funds it as a paper book to forward-test it, and its first live signal is pending. The source file's QLD trend book is a separate rule with no row of its own and is not converted.

- Sanitized for the public repo: 2 mention(s) of the originating research family name were replaced with a neutral placeholder; no rule, parameter, or code content was changed.

## What this strategy is

A weekly trend-pullback book over 19 ETFs: buy an ETF whose completed week pulled back to its 8-week EMA inside an 8 > 20 > 50 EMA uptrend, with a weekly-ATR stop, a quarter off at one ATR of gain, and the rest out five weeks later.

## Full algorithm

From the strategy card, in evaluation order:

1. Signal, on a completed week (its last session a Friday, else once the next week begins): EMA8 > EMA20 > EMA50 of the weekly closes, the close above EMA50, the week's low at or under EMA8 and the close above the low; at least 60 weeks of history required.
2. Levels: entry at the week's close; stop = entry - weekly ATR(5); target = entry + ATR; deadline = the last session of the fifth week after.
3. Selection and entry: decided after that week's close; at most 10 names held; the week's signals are ordered by RSI(14) ascending, then symbol; bought at the book's first pass of the next session, skipped when the price is already at or under the stop.
4. Exit: the stop at entry - weekly ATR(5) is held by the engine on the live price; a quarter is sold the first time the live price reaches the target; the rest exits by a market-on-close order on the deadline session.
5. Sizing: a tenth of equity per name, never more than the cash, divided by 1.001 for the source's cost; $100,000 book.

## Files in this repo

- This package: `docs/MN_WEEKLY_8_20_50_PULLBACK-RECREATE.md`
- Strategy card: `strategies/midna/mn-weekly-8-20-50-pullback.md`
- Running code (already in Test; nothing vendored for this package), per the card: `sleeves/midna/monitor/midna_books.py`, `sleeves/midna/monitor/midna_mon.py`, `sleeves/the family research line/monitor.py`
- TypeScript source of record, also in Test: `sleeves/midna/vendor/midna_mon/src/lib/felipe/pullback.ts`
- Rule lines referenced by the card: `docs/verify/midna.md`

## Configuration

- Universe: 19 ETFs. Timeframe: 1w signal, 1d management. Book $100,000; one tenth of equity per name; at most 10 names held.
- Stop: weekly ATR(5) under entry; target: entry + ATR with a quarter sold there; deadline: last session of the fifth week after entry week.
- Status: waiting; funded as a paper book by ruling D32 (2026-10-26), first live signal pending (card).

## Data inputs

Yahoo daily bars (1,600 sessions), adjusted as the live board adjusts them (OHLC x adjclose / close), built into weeks (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The book runs in `sleeves/midna/monitor/midna_books.py` under the monitor in `sleeves/midna/monitor/midna_mon.py` (with `sleeves/the family research line/monitor.py`); the TypeScript source it was ported from is `sleeves/midna/vendor/midna_mon/src/lib/felipe/pullback.ts`.
3. Feed the adjusted Yahoo daily bars described in Data inputs; run the weekly signal pass after a completed week and the daily management passes.
4. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A week with EMA8 at or below EMA20, or EMA20 at or below EMA50, or a close at or below EMA50, or a low above EMA8, produces no signal; fewer than 60 weeks of history produces no signal.
- Signals in one week are taken in RSI(14) ascending order, then symbol, up to 10 held names; a name already at or under its stop at the first pass of the next session is skipped.
- Position size is one tenth of equity, capped at available cash, divided by 1.001.
- The first live touch of entry + ATR sells exactly one quarter; the stop exits in full on the live price; any remainder exits market-on-close on the deadline session (the last session of the fifth week after).
