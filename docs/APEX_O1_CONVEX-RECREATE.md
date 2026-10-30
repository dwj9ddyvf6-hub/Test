# apex-o1-convex: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX O1: CONVEX", family apex, creator "APEX research desk (Cursor2), options study O1 / O1b", universe "QQQ, TQQQ, BIL; QQQ listed options", asset US ETFs and ETF options. Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those gaps are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-o1-convex`: status counts {'live': 2}.

## What this strategy is

Holds the first 1x of the APEX-50F exposure in QQQ and the rest in 3-month at-the-money calls (card summary). Two rows: O1 (close-and-reopen re-sizing) and O1b (incremental adjustment).

## Full algorithm

From the card and the vendored `o1_convex` / `o1b_convex` in `sleeves/apex/vendor/apex/opt_strategies.py` (rows `apex_o1_convex` and `apex_o1b_convex_incremental`):

Common:
1. L* = the APEX-50F target on the last finished session (trend score x min(4, 50% / volatility)), read at t-1 in the source.
2. Core: QQQ at min(L*, 1) with a 0.20 band.
3. Calls cover the rest: want = max(L* - 1, 0), delta-sized as want x NAV / (delta x spot) shares, at the money.

O1 (o1_convex):
4. Re-strike at each month's first session or when the calls' delta exposure differs from want by at least 0.5: close all calls and, if want > 0, reopen at the expiry nearest 91 days (at least 45 days), strike = spot, only if delta > 0.05.

O1b (o1b_convex):
5. Opens only when want >= 0.5: expiry nearest 91 days (at least 60 days), size min(want x NAV / (delta x spot), 99.5% of NAV / price).
6. A held call is closed / rolled when it has under 45 days left or its delta is outside 0.30-0.85; otherwise, when |want - have| >= 0.5, adjust the held call by whole contracts toward the target (toward 0 when nothing is wanted).

Exit: O1 closes the calls on a re-strike with nothing wanted; O1b rolls under 45 days or outside 0.30-0.85 delta, and adjusts toward 0 when nothing is wanted.

## Files in this repo

- This package: `docs/APEX_O1_CONVEX-RECREATE.md`
- Strategy card: `strategies/apex/apex-o1-convex.md`
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

- With L* = 1.6, the core holds QQQ at 1.0 and calls are sized to 0.6 of NAV in delta exposure.
- O1 closes and reopens its calls at a month start or at a 0.5 delta-exposure miss; O1b instead adjusts the held call, rolling only under 45 days or outside 0.30-0.85 delta, and opens only at want >= 0.5.
- With L* <= 1, want is 0 and no calls are held.
- Rule lines in `docs/verify/apex.md` for this row must match the recreation's decisions.
- Whole contracts only; a leg sizing to under one contract is skipped; option structures are decided only in the 15:15-15:45 ET window.
