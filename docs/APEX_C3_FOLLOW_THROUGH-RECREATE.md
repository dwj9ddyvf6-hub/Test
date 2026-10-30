# apex-c3-follow-through: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX C3: Follow-through", type volatility, family apex, style "Trend x volatility targeting, follow-through boost", universe "QQQ, TQQQ, BIL", creator "APEX research desk (Cursor2), round 3 C3". Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-c3-follow-through`: status live (see the card). Alias in the running code is the row id named in the Files section.
- Search record: Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, docs/) plus Silicon, quant-research-backup and Midna trees were searched by filename for the canonical id, its alias and its distinguishing tokens. The strategy's code was found already in Test; nothing was vendored for this package.

## What this strategy is

APEX-50F Nasdaq exposure, lifted to at least 2x for 20 sessions after a follow-through day out of a 10% correction. Running row `apex_c3_follow_through`.

## Full algorithm

From the card and `sleeves/apex/vendor/apex/round3.py` `c3_follow_through` / `follow_through_mask` (arm=-0.10, jump=0.0125, hold=20, params APEX_50F), in evaluation order:

1. Compute the APEX-50F base target.
2. Follow-through mask: arm when the Nasdaq-100 level closes at or below its 63-day high x (1 - 0.10); re-arm only after a new 63-day high. While armed and not yet used, the first session with a daily return >= 1.25% that closes at its 10-day high triggers the boost; one follow-through per correction.
3. Boosted target = max(base target, 2.0) on the trigger session and the following 19 sessions (20 sessions total).
4. Exit: the boost ends after 20 sessions; no stop. Exposure otherwise follows the target; a trend score of 0 holds only BIL.

Common APEX core (from the card and `sleeves/apex/vendor/apex/strategies.py`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days (`F.har_vol_forecast`, `F.trend_score` via `sleeves/femto/vendor/aurelia/features.py`). APEX-50F target = trend score x min(4, 50% / volatility); APEX-30 target = trend score x min(3, 30% / volatility). Decided on the last finished session; the held exposure moves to the target only on a change of the recorded band or more, or to 0. Execution mapping (card and `sleeves/apex/apex.py` header): market-on-close in the next session (orders from the open to 20 minutes before the close); Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L, above 3x TQQQ alone at L / 3 on margin; idle capital in BIL unless the rule names another idle asset; shares = floor(weight x book equity / last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_C3_FOLLOW_THROUGH-RECREATE.md`
- Strategy card: `strategies/apex/apex-c3-follow-through.md`
- Running code (already in Test): `sleeves/apex/apex.py` (the row for this sleeve, its decision / execution machinery, CADENCE 1800, SCHEDULE rth&close-400:close-20, job apex_decisions after each close), `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored round-3 source (already in Test): `sleeves/apex/vendor/apex/round3.py`
- Vendored source (already in Test): `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`. Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block in the vendor files.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, BIL. Timeframe: 1d unless the algorithm states otherwise. Book: $100,000.
- Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" (the next session, from the open until 20 minutes before the close); decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s). State: the held exposure / book positions, re-derived from the planned exposure every decision.

## Data inputs

Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return) and ^IRX (T-bills), recomputed after each close (per the card), plus the series named in the Full algorithm.

## Install and run

1. Clone the Test repo.
2. Read the strategy card `strategies/apex/apex-c3-follow-through.md` and the rule lines in `docs/verify/apex.md` for this row.
3. Open `sleeves/apex/apex.py`, locate this sleeve's row id, and follow its decision path into the vendored function named in the Full algorithm.
4. Provide the data inputs named below (full Yahoo daily histories, recomputed after each close, via `sleeves/apex/feedlib/apex.py`).
5. Run the desk engine so the apex_decisions job computes the session's decisions after the close and the sleeve trades market-on-close in the next session on its recorded schedule.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash). Behaviour checklist from the card and code:

- No boost unless the level first closed at least 10% under its 63-day high, and no second boost in the same correction.
- On a trigger (up >= 1.25% closing at a 10-day high) the target is at least 2.0 for exactly 20 sessions.
- The held exposure changes only on a target change of the recorded band or more, or to 0; shares are floor(weight x book equity / last close), frozen per decision.
