# apex-o11-apex-vv: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O11: APEX + Variance Value", type volatility, family apex, style "Trend x volatility + volatility", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe "1d (monthly options)", creator "APEX research desk (Cursor2), options study O11". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-o11-apex-vv` (`docs/CATALOG.json`): card `strategies/apex/apex-o11-apex-vv.md`.
- Aliases: `apex_o11_apex_vv`.

## What this strategy is

APEX-50F Nasdaq exposure plus the monthly Variance Value trade.

## Full algorithm

From `strategies/apex/apex-o11-apex-vv.md`, in evaluation order:

1. Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. APEX-50F exposure = trend score x min(4, 50% / volatility).
2. Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ.
3. Variance Value, at a month's first session with none held, on the next monthly expiry >= 15 days out: at-the-money implied vol / the HAR forecast >= 1.25 sells the at-the-money straddle and buys wings 1.5 sigma sqrt(T) out (an iron fly), NAV / spot shares a leg; <= 0.95 buys the at-the-money straddle with 2% of NAV.
4. Exit: option structures are held to expiry. No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).
5. Sizing: Core: T-bills (BIL). Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. The core trades market-on-close on the equity less the options' value.

## Files in this repo

- This doc: `docs/APEX_O11_APEX_VV-RECREATE.md`
- Strategy card: `strategies/apex/apex-o11-apex-vv.md`
- Code (already in Test): sleeves/apex/apex_options.py, sleeves/apex/apex.py, sleeves/apex/feedlib/apex.py, sleeves/apex/feedlib/apex_book.py, sleeves/apex/vendor/apex/opt_strategies.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d (monthly options). Asset class: US ETFs and ETF options.
- Book: $1,000,000. Core trades on the equity less the options' value.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-o11-apex-vv.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- The core follows APEX-50F with the 0.20 band and holds only BIL at a trend score of 0.
- Variance Value fires only at a month's first session with none held, at the recorded 1.25 / 0.95 ratios.
- Option structures are held to expiry; under one whole contract is skipped.
