# apex-o10-leaps-vv: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O10: LEAPS + Variance Value", type volatility, family apex, style "Trend x volatility in LEAPS + volatility", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe "1d (monthly options)", creator "APEX research desk (Cursor2), options study O10". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-o10-leaps-vv` (`docs/CATALOG.json`): card `strategies/apex/apex-o10-leaps-vv.md`.
- Aliases: `apex_o10_leaps_vv`.

## What this strategy is

The whole APEX-50F exposure in 1-year 0.80-delta QQQ calls, adjusted by contracts, plus the monthly Variance Value trade.

## Full algorithm

From `strategies/apex/apex-o10-leaps-vv.md`, in evaluation order:

1. L* = the APEX-50F target on the last finished session (trend score x min(4, 50% / volatility); see the APEX-50F definition in the other APEX packages / the card).
2. Calls: the expiry nearest 365 days (>= 300), the strike for 0.80 delta.
3. Calls = L* x NAV / (delta x spot), at most 99.5% of NAV in premium; adjusted by whole contracts when 0.5 off.
4. Variance Value, at a month's first session with none held, on the next monthly expiry >= 15 days out: at-the-money implied vol / the HAR forecast >= 1.25 sells the at-the-money straddle and buys wings 1.5 sigma sqrt(T) out (an iron fly), NAV / spot shares a leg; <= 0.95 buys the at-the-money straddle with 2% of NAV.
5. Exit: L* <= 0 sells the calls; rolled under 183 days or outside 0.60-0.95 delta; the Variance Value structures are held to expiry.
6. Sizing: Core: T-bills (BIL). Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. The core trades market-on-close on the equity less the options' value. Book $1,000,000 for this options study (see Configuration).

## Files in this repo

- This doc: `docs/APEX_O10_LEAPS_VV-RECREATE.md`
- Strategy card: `strategies/apex/apex-o10-leaps-vv.md`
- Code (already in Test): sleeves/apex/apex_options.py, sleeves/apex/apex.py, sleeves/apex/feedlib/apex.py, sleeves/apex/feedlib/apex_book.py, sleeves/apex/vendor/apex/opt_strategies.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d (monthly options). Asset class: US ETFs and ETF options.
- Book: $1,000,000. Core: T-bills (BIL).

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-o10-leaps-vv.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Calls use the expiry nearest 365 days (at least 300) and the 0.80-delta strike.
- No adjustment unless the position is 0.5 off the target contract count.
- Calls are sold when L* <= 0 and rolled under 183 days or outside 0.60-0.95 delta.
- Variance Value fires only at a month's first session with none held, at the recorded 1.25 / 0.95 ratios, and its structures are held to expiry.
