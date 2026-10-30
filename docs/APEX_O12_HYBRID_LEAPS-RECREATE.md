# apex-o12-hybrid-leaps: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O12: hybrid LEAPS + QQQ trim", type volatility, family apex, style "Trend x volatility in LEAPS", universe "QQQ, TQQQ, BIL; QQQ listed options", asset class US ETFs and ETF options, timeframe "1d", creator "APEX research desk (Cursor2), options study O12". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-o12-hybrid-leaps` (`docs/CATALOG.json`): card `strategies/apex/apex-o12-hybrid-leaps.md`.
- Aliases: `apex_o12_hybrid_leaps`.

## What this strategy is

1-year 0.80-delta QQQ calls for 75% of the APEX-50F exposure, with the rest as a QQQ share trim. Note on the card: the source's trim was a futures position; the desk trades it in QQQ shares.

## Full algorithm

From `strategies/apex/apex-o12-hybrid-leaps.md`, in evaluation order:

1. L* = the APEX-50F target on the last finished session (trend score x min(4, 50% / volatility)).
2. Calls: the expiry nearest 365 days (>= 300), the strike for 0.80 delta.
3. Calls for 75% of L*: 0.75 x L* x NAV / (delta x spot), at most 99.5% of NAV in premium, opened when none are held and L* > 0; after an L* <= 0 exit, only at a month's first session.
4. Trim: QQQ shares (long or short) for L* less the calls' delta exposure, traded on a change of 0.20 or more, or to 0.
5. Exit: L* <= 0 sells the calls; they roll under 183 days or outside 0.60-0.95 delta.
6. Sizing: Core: T-bills (BIL). Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. The core trades market-on-close on the equity less the options' value.

## Files in this repo

- This doc: `docs/APEX_O12_HYBRID_LEAPS-RECREATE.md`
- Strategy card: `strategies/apex/apex-o12-hybrid-leaps.md`
- Code (already in Test): sleeves/apex/apex_options.py, sleeves/apex/apex.py, sleeves/apex/feedlib/apex.py, sleeves/apex/feedlib/apex_book.py, sleeves/apex/vendor/apex/opt_strategies.py, sleeves/apex/vendor/apex/strategies.py, sleeves/femto/vendor/aurelia/features.py
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d. Asset class: US ETFs and ETF options.
- Book: $1,000,000. Calls carry 75% of L*; the QQQ trim carries the remainder.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-o12-hybrid-leaps.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / invention / options study.
4. Provide the data inputs listed above.
5. Run daily after the close, deciding on the last finished session, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Calls are sized at exactly 75% of L* by the recorded formula and capped at 99.5% of NAV in premium.
- After an L* <= 0 exit, calls reopen only at a month's first session.
- The trim equals L* less the calls' delta exposure and trades only on a change of 0.20 or more, or to 0.
- Calls roll under 183 days or outside 0.60-0.95 delta.
