# apex-o6-variance-value: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O6: Variance Value", type volatility, family apex, style "Volatility relative value", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe "1d (monthly options)", creator "APEX research desk (Cursor2), options study O6". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-o6-variance-value` (`docs/CATALOG.json`): card `strategies/apex/apex-o6-variance-value.md`.
- Aliases: `apex_o6_variance_value`.

## What this strategy is

A 1x QQQ core plus a monthly volatility trade: an iron fly when implied vol is rich, a straddle when it is cheap.

## Full algorithm

From `strategies/apex/apex-o6-variance-value.md`, in evaluation order:

1. Core: QQQ at 1x.
2. Variance Value, at a month's first session with none held, on the next monthly expiry >= 15 days out: at-the-money implied vol / the HAR forecast >= 1.25 sells the at-the-money straddle and buys wings 1.5 sigma sqrt(T) out (an iron fly), NAV / spot shares a leg; <= 0.95 buys the at-the-money straddle with 2% of NAV.
3. Exit: option structures are held to expiry.
4. Sizing: Core: T-bills (BIL). Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. The core trades market-on-close on the equity less the options' value.

## Files in this repo

- This doc: `docs/APEX_O6_VARIANCE_VALUE-RECREATE.md`
- Strategy card: `strategies/apex/apex-o6-variance-value.md`
- Code (already in Test): sleeves/apex/apex_options.py, sleeves/apex/apex.py, sleeves/apex/feedlib/apex.py, sleeves/apex/feedlib/apex_book.py, sleeves/apex/vendor/apex/opt_strategies.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d (monthly options). Asset class: US ETFs and ETF options.
- Book: $1,000,000. The equity core is a fixed 1x QQQ, not APEX-50F.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-o6-variance-value.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- The core is QQQ at exactly 1x.
- Variance Value fires only at a month's first session with none held, on the next monthly expiry >= 15 days out, at the recorded 1.25 / 0.95 ratios; between those ratios no trade is recorded.
- Option structures are held to expiry.
