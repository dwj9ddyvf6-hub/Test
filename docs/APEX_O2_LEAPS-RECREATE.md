# apex-o2-leaps: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O2: LEAPS-APEX", type volatility, family apex, style "Trend x volatility in LEAPS", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe "1d", creator "APEX research desk (Cursor2), options study O2 / O2b". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-o2-leaps` (`docs/CATALOG.json`): card `strategies/apex/apex-o2-leaps.md`.
- Aliases: `apex_o2_leaps_apex`, `apex_o2b_leaps_incremental`.

## What this strategy is

Holds the whole APEX-50F exposure in 1-year 0.80-delta QQQ calls. Two rows: O2 (`apex_o2_leaps_apex`, re-sizing: close and reopen 0.5 off, roll: under 183 days) and O2b (`apex_o2b_leaps_incremental`, re-sizing: adjust the held call 0.5 off, roll: under 183 days or delta outside 0.60-0.95).

## Full algorithm

From `strategies/apex/apex-o2-leaps.md`, in evaluation order:

1. L* = the APEX-50F target on the last finished session (trend score x min(4, 50% / volatility)).
2. Calls: the expiry nearest 365 days (>= 300), the strike for 0.80 delta.
3. O2: calls = L* x NAV / (max(delta, 0.5) x spot) shares, re-struck when none are held, under 183 days, or 0.5 off L*.
4. O2b: calls = L* x NAV / (delta x spot), at most 99.5% of NAV in premium; adjusted by whole contracts when 0.5 off.
5. Exit: L* <= 0 sells the calls; O2b rolls under 183 days or outside 0.60-0.95 delta.
6. Sizing: Core: T-bills (BIL). Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. The core trades market-on-close on the equity less the options' value.

## Files in this repo

- This doc: `docs/APEX_O2_LEAPS-RECREATE.md`
- Strategy card: `strategies/apex/apex-o2-leaps.md`
- Code (already in Test): sleeves/apex/apex_options.py, sleeves/apex/apex.py, sleeves/apex/feedlib/apex.py, sleeves/apex/feedlib/apex_book.py, sleeves/apex/vendor/apex/opt_strategies.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d. Asset class: US ETFs and ETF options.
- Book: $1,000,000. O2 and O2b differ only as recorded in algorithm steps 3-5.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-o2-leaps.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- O2 uses max(delta, 0.5) in its sizing denominator; O2b uses delta and the 99.5% premium cap.
- O2 re-strikes when none are held, under 183 days, or 0.5 off L*; O2b adjusts by whole contracts when 0.5 off.
- L* <= 0 sells the calls in both rows.
