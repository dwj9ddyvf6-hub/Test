# apex-trend-har-tiers: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX-50F Nasdaq trend x volatility", type volatility, family apex, style "Trend x volatility targeting", universe "QQQ, TQQQ, BIL", asset class US ETFs (incl. 3x leveraged), timeframe "1d", creator "APEX research desk (Cursor2), APEX-NDX v1.0 (its live tier)". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-trend-har-tiers` (`docs/CATALOG.json`): card `strategies/apex/apex-trend-har-tiers.md`.
- Aliases: `apex_trend_har_tiers`.

## What this strategy is

Holds the Nasdaq-100 at trend score x min(4, 50% / forecast volatility), from all T-bills up to 4x through QQQ and TQQQ. This is the base APEX-50F strategy that the N and O APEX packages reference. Each decision also records the other five pre-registered tiers: APEX-20 (20%, max 2), APEX-25 (25%, 2.5), APEX-30 (30%, 3), APEX-40 (40%, 3) and APEX-K (25%, 3, volatility squared); APEX-50F is the live tier.

## Full algorithm

From `strategies/apex/apex-trend-har-tiers.md`, in evaluation order:

1. Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. APEX-50F exposure = trend score x min(4, 50% / volatility).
2. Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
3. Exit: no stop; exposure follows the target; a trend score of 0 holds only T-bills (BIL).
4. Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ (QQQ + 3 x TQQQ = L), above 3x TQQQ alone at L / 3 on margin; idle capital in BIL. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This doc: `docs/APEX_TREND_HAR_TIERS-RECREATE.md`
- Strategy card: `strategies/apex/apex-trend-har-tiers.md`
- Code (already in Test): sleeves/apex/apex.py, sleeves/apex/feedlib/apex_rules.py, sleeves/apex/feedlib/apex.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL. Timeframe: 1d. Asset class: US ETFs (incl. 3x leveraged).
- Book: $100,000. Live tier APEX-50F (50%, max 4); the other five tiers are recorded at each decision, not traded.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-trend-har-tiers.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Exposure equals trend score x min(4, 50% / volatility) exactly, capped at 4x.
- No trade unless the target changes by 0.20 or more, or the target is 0.
- A trend score of 0 holds only BIL.
- The QQQ / TQQQ split follows the 1x / 1-3x / above-3x rule in the algorithm.
