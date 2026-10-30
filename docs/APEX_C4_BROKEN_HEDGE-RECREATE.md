# apex-c4-broken-hedge: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX C4: Broken Hedge", type volatility, family apex, style "Trend x volatility targeting, correlation hedge", universe "QQQ, TQQQ, IEF, GLD, UUP, BIL", creator "APEX research desk (Cursor2), round 3 C4". Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-c4-broken-hedge`: status live (see the card). Alias in the running code is the row id named in the Files section.
- Search record: Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, docs/) plus Silicon, quant-research-backup and Midna trees were searched by filename for the canonical id, its alias and its distinguishing tokens. The strategy's code was found already in Test; nothing was vendored for this package.

## What this strategy is

APEX-50F Nasdaq exposure, halved when Treasuries and gold stop hedging it, with idle capital in whichever of Treasuries, gold and the dollar hedges best. Running row `apex_c4_broken_hedge`.

## Full algorithm

From the card and `sleeves/apex/vendor/apex/round3.py` `c4_broken_hedge` (gate=0.20, corr_cut=-0.10, params APEX_50F, switch_bps=3.0), in evaluation order:

1. Compute the APEX-50F base target.
2. Correlations: 63-day rolling correlations of Nasdaq returns with Treasury (tsy), gold and dollar (dxy) returns.
3. Hedge-broken multiplier: x 0.5 while both the Treasury and gold 63-day correlations are above 0.20; otherwise x 1.0.
4. Idle asset: the most negatively correlated of Treasuries (IEF), gold (GLD) and the dollar index (UUP) when that minimum correlation is below -0.10, else cash (BIL); the choice is lagged the same way as the book (shift 2 in the source), and switches of the idle asset cost 3.0 bps on the idle share.
5. Exit: no stop; exposure follows the target; a trend score of 0 holds only the idle asset.

Common APEX core (from the card and `sleeves/apex/vendor/apex/strategies.py`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days (`F.har_vol_forecast`, `F.trend_score` via `sleeves/femto/vendor/aurelia/features.py`). APEX-50F target = trend score x min(4, 50% / volatility); APEX-30 target = trend score x min(3, 30% / volatility). Decided on the last finished session; the held exposure moves to the target only on a change of the recorded band or more, or to 0. Execution mapping (card and `sleeves/apex/apex.py` header): market-on-close in the next session (orders from the open to 20 minutes before the close); Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L, above 3x TQQQ alone at L / 3 on margin; idle capital in BIL unless the rule names another idle asset; shares = floor(weight x book equity / last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_C4_BROKEN_HEDGE-RECREATE.md`
- Strategy card: `strategies/apex/apex-c4-broken-hedge.md`
- Running code (already in Test): `sleeves/apex/apex.py` (the row for this sleeve, its decision / execution machinery, CADENCE 1800, SCHEDULE rth&close-400:close-20, job apex_decisions after each close), `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored round-3 source (already in Test): `sleeves/apex/vendor/apex/round3.py`
- Vendored source also named on the card: `sleeves/apex/vendor/apex/inventions.py`
- Vendored source (already in Test): `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`. Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block in the vendor files.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, IEF, GLD, UUP, BIL. Timeframe: 1d unless the algorithm states otherwise. Book: $100,000.
- Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" (the next session, from the open until 20 minutes before the close); decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s). State: the held exposure / book positions, re-derived from the planned exposure every decision.

## Data inputs

Yahoo full daily histories: ^NDX and QQQ, ^IRX, GC=F, DX-Y.NYB and ^TNX, recomputed after each close; IEF total return (before IEF, a duration model on ^TNX), per the card.

## Install and run

1. Clone the Test repo.
2. Read the strategy card `strategies/apex/apex-c4-broken-hedge.md` and the rule lines in `docs/verify/apex.md` for this row.
3. Open `sleeves/apex/apex.py`, locate this sleeve's row id, and follow its decision path into the vendored function named in the Full algorithm.
4. Provide the data inputs named below (full Yahoo daily histories, recomputed after each close, via `sleeves/apex/feedlib/apex.py`).
5. Run the desk engine so the apex_decisions job computes the session's decisions after the close and the sleeve trades market-on-close in the next session on its recorded schedule.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash). Behaviour checklist from the card and code:

- The multiplier is exactly 0.5 only while BOTH 63-day correlations (Treasuries and gold) are above 0.20.
- Idle capital sits in BIL unless the best (most negative) of the three correlations is below -0.10, in which case it sits in that asset (IEF / GLD / UUP).
- The held exposure changes only on a target change of the recorded band or more, or to 0; shares are floor(weight x book equity / last close), frozen per decision.
