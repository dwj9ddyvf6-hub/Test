# apex-n7-omni: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX N7: OMNI", family apex, creator "APEX research desk (Cursor2), invention N7", universe "QQQ, TQQQ, BIL; QQQ listed options", asset US ETFs and ETF options. Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those gaps are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-n7-omni`: status counts {'live': 1}.

## What this strategy is

N1's Duration Shield Nasdaq exposure plus a monthly Variance Value options trade on the whole book (card summary).

## Full algorithm

From the card and Test code (`sleeves/apex/apex.py` row `apex_n7_omni`, VV_ROWS; the Variance Value overlay `_variance_value` in `sleeves/apex/vendor/apex/opt_strategies.py`):

Core (N1 Duration Shield form as stated on this card):
1. Trend score = share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = walk-forward HAR forecast of the next 5 days.
2. Core exposure = trend score x min(4, 50% / volatility), times 0.5 when the 10-year yield is up more than 0.50 over 63 sessions; traded with a 0.20 band. A trend score of 0 holds only T-bills (BIL).

Variance Value (at a month's first session, with none held, on the whole book's NAV):
3. On the next monthly expiry at least 15 days out, compute ratio = at-the-money implied vol / HAR forecast.
4. Ratio >= 1.25: sell the at-the-money straddle and buy wings 1.5 sigma sqrt(T) out (an iron fly), NAV / spot shares a leg.
5. Ratio <= 0.95: buy the at-the-money straddle with 2% of NAV (code: units = 0.02 x NAV / (call price + put price)).
6. Between 0.95 and 1.25: no Variance Value trade.

Exit: option structures are held to expiry. No stop: core exposure follows the target.

## Files in this repo

- This package: `docs/APEX_N7_OMNI-RECREATE.md`
- Strategy card: `strategies/apex/apex-n7-omni.md`
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

- At a month start with IV / HAR >= 1.25, one iron fly opens (short ATM straddle, long wings 1.5 sigma sqrt(T) out), NAV/spot shares a leg.
- With IV / HAR <= 0.95, a long ATM straddle opens sized to 2% of NAV; between the thresholds, no options trade opens.
- The core is halved when the 10-year yield has risen more than 0.50 over 63 sessions, and is BIL only at trend score 0.
- Rule lines in `docs/verify/apex.md` for this row must match the recreation's decisions.
- Whole contracts only; a leg sizing to under one contract is skipped; option structures are decided only in the 15:15-15:45 ET window.
