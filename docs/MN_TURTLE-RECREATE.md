# mn-turtle: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Turtle System 1", type breakout, family midna, universe "Midna's swing basket", asset US equities, timeframe 1d, creator "Midna's TypeScript desk (equity books), ported line for line to the master desk". Algorithm grade PARTIAL with entry, exit and sizing not in the accounting's consulted sources; the rules below are from the Test card and running Test code.
- Test catalog entry `mn-turtle`: card `strategies/midna/mn-turtle.md`, code `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`, `sleeves/midna/common.py`, status live. Card note: the master desk drops the original desk-wide red-day buy gate and desk halt.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

Buys 20- or 55-day closing breakouts with Turtle unit sizing and pyramiding, and exits on a 2N stop or a 10-day low (card summary).

## Full algorithm

Evaluation order, from the card and `sleeves/midna/board.py` (IDS turtle -> midna_turtle_s1; enter_turtle, stops on every regular-hours pass):

1. Entry signal: a close above the prior 20-day high (or the 55-day high), new today; at most 4 names, alphabetical order.
2. Skip rule: a 20-day breakout right after a winning exit is skipped once; the 55-day breakout is taken.
3. Pyramiding: add a unit at each +0.5N over the last add, up to 4 units. N = ATR(20).
4. Unit sizing: unit = min(floor(1% of equity / N), floor(cash / price)).
5. Exits: stop at entry - 2N (raised with adds), triggered on any regular-hours print; signal exit on a close under the prior 10-day low (the code's exit10 signal, reason Turtle 10-day exit).

## Files in this repo

- This package: `docs/MN_TURTLE-RECREATE.md`
- Strategy card: `strategies/midna/mn-turtle.md`
- Running code (already in Test; nothing vendored): `sleeves/midna/board.py` (BoardBook turtle), `sleeves/midna/vendor/midna/board_signals.py` (signals incl. exit10), `sleeves/midna/common.py`.

## Configuration

- Universe: Midna's swing basket (as configured in the board runtime; the specific list is not in the record beyond that name). Timeframe: daily. Max names: 4. Max units per name: 4. N = ATR(20).

## Data inputs

Completed daily bars of the swing basket, plus regular-hours quotes for the stop check (code).

## Install and run

1. Clone this repository (Test).
2. Import the turtle BoardBook from `sleeves/midna/board.py` (returned by that module's `sleeves()`) and register it with the desk runtime.
3. Configure the swing basket, equity and cash inputs, and daily bars plus regular-hours quotes.
4. Run the daily entry pass and the regular-hours stop pass.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- A fresh close above the prior 20-day high produces one unit sized min(floor(0.01 x equity / N), floor(cash / price)); a fifth name the same day is not taken (4-name cap, alphabetical).
- After a winning exit, the next 20-day breakout for that name is skipped once, while a 55-day breakout is taken.
- Price reaching entry - 2N on a regular-hours print exits the position; a close under the prior 10-day low produces the signal exit.
- Adds occur only at +0.5N steps over the last add and stop at 4 units.
