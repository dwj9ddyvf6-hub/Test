# killed-naive-20d-breakout: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Naive 20-day breakout", type breakout, family killed, universe "41-name old-desk basket", asset US equities, timeframe 1d. Algorithm grade PARTIAL with entry, exit and sizing not in the accounting's consulted sources; the rules below are from the Test card and running Test code.
- Test catalog entry `killed-naive-20d-breakout`: card `strategies/killed/killed-naive-20d-breakout.md`, code `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`, status live.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

Buys a strict new 20-day closing high on 41 names and holds it 20 sessions (card summary).

## Full algorithm

Evaluation order, from the card and `sleeves/killed/daily.py` (class Naive20dBreakout, listed in `sleeves/killed/killed_studies.py` sleeves()):

1. Signal on the completed session: a close strictly above the highest close of the prior 20 sessions (a tie is not a breakout).
2. Entry: bought at the next session's first pass; a signal during an existing hold is skipped. An open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.
3. Exit: sold market-on-close 20 sessions after the signal session.
4. Sizing: $100,000 / 41 per position (fractional shares long; shorts in whole shares, at least 1, per the card's sizing line for the killed daily books).

## Files in this repo

- This package: `docs/KILLED_NAIVE_20D_BREAKOUT-RECREATE.md`
- Strategy card: `strategies/killed/killed-naive-20d-breakout.md`
- Running code (already in Test; nothing vendored): `sleeves/killed/daily.py` (class Naive20dBreakout), `sleeves/killed/killed_studies.py` (registry), `sleeves/killed/common.py` (shared daily-book machinery).

## Configuration

- Universe: 41-name basket. Timeframe: daily. Hold: 20 sessions after the signal session. Size: $100,000 / 41 per position.

## Data inputs

Split-adjusted daily bars (60 sessions per the card).

## Install and run

1. Clone this repository (Test).
2. Import Naive20dBreakout via `sleeves/killed/killed_studies.py` `sleeves()` and register it with the desk runtime.
3. Configure the 41-name basket and split-adjusted daily bars.
4. Run the daily first pass and the market-on-close window (30-11 minutes before the close) each session.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- A close exactly equal to the prior 20-session highest close produces no signal; a close above it produces exactly one entry at the next session's first pass.
- A second breakout signal during the 20-session hold produces no additional entry.
- The position is sold market-on-close exactly 20 sessions after the signal session.
