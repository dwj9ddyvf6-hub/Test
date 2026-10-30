# apex-e3-defensive-treasuries: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX E3 / v1.1: defensive Treasuries", type volatility, family apex, style "Trend x volatility targeting", universe "QQQ, TQQQ, IEF, BIL", creator "APEX research desk (Cursor2), APEX-NDX extension E3 and the v1.1 candidate". Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-e3-defensive-treasuries`: status live (see the card). Alias in the running code is the row id named in the Files section.
- Search record: Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, docs/) plus Silicon, quant-research-backup and Midna trees were searched by filename for the canonical id, its alias and its distinguishing tokens. The strategy's code was found already in Test; nothing was vendored for this package.

## What this strategy is

APEX Nasdaq exposure with idle capital in 7-10-year Treasuries while they trend up, else T-bills: E3 at APEX-30, the v1.1 candidate at APEX-50F with a wide band. Running rows `apex_e3_defensive_treasuries` and `apex_v11_defensive_bond`.

## Full algorithm

From the card and `sleeves/apex/vendor/apex/strategies.py` `e3_defensive_bonds` / `bond_trend` / `apex_v11`, in evaluation order:

1. Exposure = trend score x min(max, target / volatility), with the variant's parameters: E3 = APEX-30 (target 30%, max 3x, band 0.20, row `apex_e3_defensive_treasuries`); v1.1 candidate = APEX-50F (target 50%, max 4x, band 0.50, row `apex_v11_defensive_bond`, params APEX_V11).
2. Bond trend: 1.0 when the 7-10-year Treasury total-return level (cumulated IEF return) is above its 200-day average, else 0; the held idle choice is lagged (shift lag+1 in the source).
3. Idle capital earns the Treasury return while the bond trend is on, else the T-bill (cash) return less the cash spread; switching the idle asset costs the trade bps on the idle share.
4. Exit: no stop; exposure follows the target; a trend score of 0 holds only the idle asset.

Common APEX core (from the card and `sleeves/apex/vendor/apex/strategies.py`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days (`F.har_vol_forecast`, `F.trend_score` via `sleeves/femto/vendor/aurelia/features.py`). APEX-50F target = trend score x min(4, 50% / volatility); APEX-30 target = trend score x min(3, 30% / volatility). Decided on the last finished session; the held exposure moves to the target only on a change of the recorded band or more, or to 0. Execution mapping (card and `sleeves/apex/apex.py` header): market-on-close in the next session (orders from the open to 20 minutes before the close); Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L, above 3x TQQQ alone at L / 3 on margin; idle capital in BIL unless the rule names another idle asset; shares = floor(weight x book equity / last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_E3_DEFENSIVE_TREASURIES-RECREATE.md`
- Strategy card: `strategies/apex/apex-e3-defensive-treasuries.md`
- Running code (already in Test): `sleeves/apex/apex.py` (the row for this sleeve, its decision / execution machinery, CADENCE 1800, SCHEDULE rth&close-400:close-20, job apex_decisions after each close), `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored source function (already in Test): the function named in the Full algorithm in `sleeves/apex/vendor/apex/strategies.py`
- Vendored source (already in Test): `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`. Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block in the vendor files.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, IEF, BIL. Timeframe: 1d unless the algorithm states otherwise. Book: $100,000.
- Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" (the next session, from the open until 20 minutes before the close); decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s). State: the held exposure / book positions, re-derived from the planned exposure every decision.

## Data inputs

Yahoo full daily histories: ^NDX and QQQ, ^IRX and ^TNX, recomputed after each close; IEF total return (before IEF, a duration model on ^TNX), per the card.

## Install and run

1. Clone the Test repo.
2. Read the strategy card `strategies/apex/apex-e3-defensive-treasuries.md` and the rule lines in `docs/verify/apex.md` for this row.
3. Open `sleeves/apex/apex.py`, locate this sleeve's row id, and follow its decision path into the vendored function named in the Full algorithm.
4. Provide the data inputs named below (full Yahoo daily histories, recomputed after each close, via `sleeves/apex/feedlib/apex.py`).
5. Run the desk engine so the apex_decisions job computes the session's decisions after the close and the sleeve trades market-on-close in the next session on its recorded schedule.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash). Behaviour checklist from the card and code:

- Both recorded variants must be present with their own parameters (E3: 30% / 3x / band 0.20; v1.1: 50% / 4x / band 0.50); do not collapse them into one book.
- Idle capital is in IEF only while the Treasury total-return level is above its 200-day average, else in BIL.
- The held exposure changes only on a target change of the recorded band or more, or to 0; shares are floor(weight x book equity / last close), frozen per decision.
