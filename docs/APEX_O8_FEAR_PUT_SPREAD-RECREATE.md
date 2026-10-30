# apex-o8-fear-put-spread: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O8: FEAR put spread", family apex, creator "APEX research desk (Cursor2), options study O8", universe "QQQ, TQQQ, BIL; QQQ listed options", asset US ETFs and ETF options. Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those gaps are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-o8-fear-put-spread`: status counts {'live': 1}.

## What this strategy is

APEX-50F Nasdaq exposure plus a monthly short 90/80 QQQ put spread when fear is high and the trend weak (card summary).

## Full algorithm

From the card and the vendored `_fear` overlay in `sleeves/apex/vendor/apex/opt_strategies.py` (row `apex_o8_fear_put_spread`, overlay ("fear",)):

1. Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ; a trend score of 0 holds only BIL.
2. FEAR entry: at a month's first session, when 30-day implied vol is at or above its 252-day 80th percentile (code: vol30[t-1] >= vol30_p80[t-1]) and the trend score is at most 2 of 6, and no fear legs are held: sell the 90% put and buy the 80% put (strikes 0.90 x spot short, 0.80 x spot long), NAV / spot shares, on the expiry nearest 61 days (at least 45 days).
3. Exit: held to expiry. No stop: core exposure follows the target.

## Files in this repo

- This package: `docs/APEX_O8_FEAR_PUT_SPREAD-RECREATE.md`
- Strategy card: `strategies/apex/apex-o8-fear-put-spread.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/apex/apex_options.py` (rows table and the O1-O12 strategy dispatch; source functions unchanged from the vendored study)
  - `sleeves/apex/apex.py` (APEX-50F core, trend and HAR machinery for sleeves that carry a core)
  - `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
  - `sleeves/apex/vendor/apex/opt_strategies.py` (the O1-O12 source functions, including the functions named in the Full algorithm), `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/inventions.py` where the card names it, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/surface.py`, `sleeves/apex/vendor/apex/bs.py`, `sleeves/apex/vendor/apex/engine.py`
  - `sleeves/femto/vendor/aurelia/features.py` where the card lists it
- Rule lines: `docs/verify/apex.md`. Parity tools in Test: `packages/claude/master-desk-parity-tools/tools/parity/apex.py` and `apex_options.py`.

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d as in the card (monthly options where stated).
- Book: $1,000,000. Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly expiry and strike nearest the model's, whole contracts (under one contract skipped), a structure traded as one multi-leg package, marketable limits.
- Core trades market-on-close on the equity less the options' value.
- APEX-50F target L*: trend score (share of 6 bullish votes: Nasdaq-100 total return above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days) times min(4, 50% / volatility), where volatility is a walk-forward HAR forecast of the next 5 days, unless the specific card states the target differently.

## Data inputs

Yahoo full daily histories: ^NDX and QQQ (Nasdaq-100 total return), ^IRX (T-bills), plus ^TNX where the card names it; recomputed after each close. Live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend yield.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine dependencies for the files listed above (Python, numpy and pandas where those modules require them).
3. Import / register the sleeve or strategy module named in the Files section with the sleeve id and parameters recorded in the Full algorithm and Configuration sections.
4. Serve the data inputs named below and the sleeve's book / position state.
5. Run the desk engine on the cadence recorded in the Configuration section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated unit test for this single row was named in the card. Behavior checklist from the card and the vendored source function:

- At a month start with vol30 at/above its 252-day 80th percentile and trend at most 2 of 6, exactly one short 90/80 put spread opens, NAV/spot shares, expiry nearest 61 days and at least 45.
- If either condition fails, no spread opens.
- A held spread runs to expiry with no early close.
- Rule lines in `docs/verify/apex.md` for this row must match the recreation's decisions.
- Whole contracts only; a leg sizing to under one contract is skipped; option structures are decided only in the 15:15-15:45 ET window.
