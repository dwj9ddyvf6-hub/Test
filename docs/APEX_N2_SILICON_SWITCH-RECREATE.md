# apex-n2-silicon-switch: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX N2: Silicon Switch", type volatility, family apex, style "Trend x volatility targeting, relative strength switch", universe "QQQ, TQQQ, SMH, BIL", asset class US ETFs (incl. 3x leveraged), timeframe "1d", creator "APEX research desk (Cursor2), invention N2". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-n2-silicon-switch` (`docs/CATALOG.json`): card `strategies/apex/apex-n2-silicon-switch.md`.
- Aliases: `apex_n2_silicon_switch`.

## What this strategy is

Holds whichever of the Nasdaq-100 and the semiconductor index leads by 5 points over 126 days, at that index's own APEX-50F exposure.

## Full algorithm

From `strategies/apex/apex-n2-silicon-switch.md`, in evaluation order:

1. Switch: to the SOX when its 126-day return beats the Nasdaq-100's by more than 5 points; back when the Nasdaq-100 leads by more than 5.
2. Exposure: APEX-50F of the index held (trend score x min(4, 50% / volatility) from its own votes and HAR forecast; trend score and HAR as defined for APEX-50F: 6 votes above 50/100/200-day averages and up over 63/126/252 days, HAR forecast of the next 5 days).
3. Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
4. Exit: no stop; a switch moves the whole exposure between the two indexes.
5. Sizing: Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This doc: `docs/APEX_N2_SILICON_SWITCH-RECREATE.md`
- Strategy card: `strategies/apex/apex-n2-silicon-switch.md`
- Code (already in Test): sleeves/apex/apex.py, sleeves/apex/feedlib/apex_rules.py, sleeves/apex/feedlib/apex.py, sleeves/apex/vendor/apex/inventions.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, SMH, BIL. Timeframe: 1d. Asset class: US ETFs (incl. 3x leveraged).
- Book: $100,000. Held index is either the Nasdaq-100 or the SOX (held as SMH).

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^SOX and SMH; recomputed after each close. The SOX total return: ^SOX + 1% a year until SMH's history starts, then SMH's.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-n2-silicon-switch.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No switch unless the other index leads by more than 5 points over 126 days.
- The held exposure always equals the held index's own APEX-50F target, subject to the 0.20 band.
- A switch moves the whole exposure; no partial switch is recorded.
