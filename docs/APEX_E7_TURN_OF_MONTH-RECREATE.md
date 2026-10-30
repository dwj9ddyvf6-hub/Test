# apex-e7-turn-of-month: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX E7: turn-of-month boost", type market timing and rotation, family apex, style "Trend x volatility targeting, calendar", universe "QQQ, TQQQ, BIL", asset class US ETFs (incl. 3x leveraged), timeframe "1d", creator "APEX research desk (Cursor2), APEX-NDX extension E7". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-e7-turn-of-month` (`docs/CATALOG.json`): card `strategies/apex/apex-e7-turn-of-month.md`, status live.
- Alias: `apex_e7_turn_of_month`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start and searched by filename for the canonical id, its alias and its distinguishing tokens, across sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, laz_sleeves/, config/ and docs/; the Silicon, quant-research-backup and Midna trees in this run's workspace were searched the same way. The code is already in Test; no distinct code for this strategy was found in Silicon, quant-research-backup or Midna.

## What this strategy is

APEX-30 Nasdaq exposure plus 0.5x over each turn of the month while the trend score is at least 0.5.

## Full algorithm

From `strategies/apex/apex-e7-turn-of-month.md`, in evaluation order:

1. Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
2. APEX-30: exposure = trend score x min(3, 30% / volatility), + 0.5 held over the turn of the month (its last session and the next month's first three) while the trend score is >= 0.5, at most 3x.
3. Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
4. Exit: the 0.5x leaves after the month's third session; no stop.
5. Sizing: market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ (QQQ + 3 x TQQQ = L), above 3x TQQQ alone at L / 3 on margin; idle capital in BIL. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_E7_TURN_OF_MONTH-RECREATE.md`
- Strategy card: `strategies/apex/apex-e7-turn-of-month.md`
- Code (already in Test): `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, BIL. Timeframe: 1d. Asset class: US ETFs (incl. 3x leveraged).
- Book: $100,000.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-e7-turn-of-month.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / study.
4. Provide the data inputs listed above.
5. Run on the recorded cadence and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Base exposure equals trend score x min(3, 30% / volatility), capped at 3x including the boost.
- The +0.5 boost is present only on the last session of a month and the next month's first three sessions, and only while the trend score is >= 0.5.
- No trade unless the target changes by 0.20 or more, or the target is 0.
- The QQQ / TQQQ split follows the 1x / 1-3x / above-3x rule in the algorithm.
