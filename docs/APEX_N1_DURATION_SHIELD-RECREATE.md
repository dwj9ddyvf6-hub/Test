# apex-n1-duration-shield: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX N1: Duration Shield", type volatility, family apex, style "Trend x volatility targeting, rates gate", universe "QQQ, TQQQ, BIL", asset class US ETFs (incl. 3x leveraged), timeframe "1d", creator "APEX research desk (Cursor2), invention N1". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-n1-duration-shield` (`docs/CATALOG.json`): card `strategies/apex/apex-n1-duration-shield.md`.
- Aliases: `apex_n1_duration_shield`.

## What this strategy is

APEX-50F Nasdaq exposure, halved while the 10-year yield is more than half a point above its level 63 sessions ago.

## Full algorithm

From `strategies/apex/apex-n1-duration-shield.md`, in evaluation order:

1. Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. APEX-50F exposure = trend score x min(4, 50% / volatility).
2. APEX-50F exposure as above, x 0.5 when the 10-year yield (^TNX) is up more than 0.50 over 63 sessions.
3. Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
4. Exit: no stop; exposure follows the target; a trend score of 0 holds only T-bills (BIL).
5. Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ (QQQ + 3 x TQQQ = L), above 3x TQQQ alone at L / 3 on margin; idle capital in BIL. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This doc: `docs/APEX_N1_DURATION_SHIELD-RECREATE.md`
- Strategy card: `strategies/apex/apex-n1-duration-shield.md`
- Code (already in Test): sleeves/apex/apex.py, sleeves/apex/feedlib/apex_rules.py, sleeves/apex/feedlib/apex.py, sleeves/apex/vendor/apex/inventions.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL. Timeframe: 1d. Asset class: US ETFs (incl. 3x leveraged).
- Book: $100,000. Sizing as in algorithm step 5.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-n1-duration-shield.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Exposure equals trend score x min(4, 50% / volatility), and is exactly halved when ^TNX is up more than 0.50 over 63 sessions and not otherwise.
- No trade unless the target changes by 0.20 or more, or the target is 0.
- A trend score of 0 holds only BIL.
- The QQQ / TQQQ split follows the 1x / 1-3x / above-3x rule in the algorithm.
