# apex-e4-rolling-tail-puts: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX E4: rolling tail puts", type volatility, family apex, style "Trend x volatility targeting, tail hedge", universe "QQQ, TQQQ, BIL; QQQ listed options", creator "APEX research desk (Cursor2), APEX-NDX extension E4". Algorithm grade PARTIAL in the accounting, with gaps entry, exit and sizing in its consulted sources; those are gaps of the accounting's consulted sources only: the full rule is in the Test strategy card and the running / vendored Test code cited below, and this package follows those Test records.
- Test catalog entry `apex-e4-rolling-tail-puts`: status live (see the card). Alias in the running code is the row id named in the Files section.
- Search record: Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, docs/) plus Silicon, quant-research-backup and Midna trees were searched by filename for the canonical id, its alias and its distinguishing tokens. The strategy's code was found already in Test; nothing was vendored for this package.

## What this strategy is

APEX-30 Nasdaq exposure plus QQQ puts 15% out of the money, bought each month while the exposure is above 1.5x. Running row: the E4 extension (source function `e4_tail_hedge`); the desk's listed-options execution is in `sleeves/apex/apex_options.py` as named on the card.

## Full algorithm

From the card and `sleeves/apex/vendor/apex/strategies.py` `e4_tail_hedge` (which calls `tail_hedge_overlay` in `sleeves/apex/vendor/apex/backtest_options.py`), in evaluation order:

1. Core: APEX-30 exposure = trend score x min(3, 30% / volatility), with its 0.20 band.
2. Puts: at a month's first session, while the APEX-30 exposure held after this close is above 1.5, buy QQQ puts 15% under spot, the listed expiry nearest 63 sessions, sized on exposure x NAV / spot shares, in whole contracts.
3. Exit: at each month's first session the held puts are sold before any new ones are bought; between months they are held.
4. Note on the card: the source priced its puts with Black-Scholes, a 0.7-point skew and a 5% spread on the Nasdaq-100 level; the desk buys listed QQQ puts at the market.

Common APEX core (from the card and `sleeves/apex/vendor/apex/strategies.py`): trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days (`F.har_vol_forecast`, `F.trend_score` via `sleeves/femto/vendor/aurelia/features.py`). APEX-50F target = trend score x min(4, 50% / volatility); APEX-30 target = trend score x min(3, 30% / volatility). Decided on the last finished session; the held exposure moves to the target only on a change of the recorded band or more, or to 0. Execution mapping (card and `sleeves/apex/apex.py` header): market-on-close in the next session (orders from the open to 20 minutes before the close); Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L, above 3x TQQQ alone at L / 3 on margin; idle capital in BIL unless the rule names another idle asset; shares = floor(weight x book equity / last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_E4_ROLLING_TAIL_PUTS-RECREATE.md`
- Strategy card: `strategies/apex/apex-e4-rolling-tail-puts.md`
- Running code (already in Test): `sleeves/apex/apex.py` (the row for this sleeve, its decision / execution machinery, CADENCE 1800, SCHEDULE rth&close-400:close-20, job apex_decisions after each close), `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored source function (already in Test): the function named in the Full algorithm in `sleeves/apex/vendor/apex/strategies.py`
- Options source / execution (already in Test): `sleeves/apex/apex_options.py`, `sleeves/apex/vendor/apex/backtest_options.py` (`tail_hedge_overlay`)
- Vendored source (already in Test): `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`. Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block in the vendor files.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, BIL; QQQ listed options. Timeframe: 1d unless the algorithm states otherwise. Book: $1,000,000 (per the card's Sizing section for this options-carrying sleeve).
- Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" (the next session, from the open until 20 minutes before the close); decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s). State: the held exposure / book positions, re-derived from the planned exposure every decision.
- Options timing: puts trade once a session in the last 45 minutes (15:15-15:45 ET), marketable limits; the core trades market-on-close on the equity less the puts' value (per the card).

## Data inputs

Yahoo full daily histories: ^NDX and QQQ and ^IRX, recomputed after each close; the live QQQ quote and the listed QQQ puts (per the card).

## Install and run

1. Clone the Test repo.
2. Read the strategy card `strategies/apex/apex-e4-rolling-tail-puts.md` and the rule lines in `docs/verify/apex.md` for this row.
3. Open `sleeves/apex/apex.py`, locate this sleeve's row id, and follow its decision path into the vendored function named in the Full algorithm.
4. Provide the data inputs named below (full Yahoo daily histories, recomputed after each close, via `sleeves/apex/feedlib/apex.py`).
5. Run the desk engine so the apex_decisions job computes the session's decisions after the close and the sleeve trades market-on-close in the next session on its recorded schedule.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash). Behaviour checklist from the card and code:

- No puts are bought in a month whose first-session held exposure is at or below 1.5.
- Held puts are sold at the next month's first session before any new purchase; strikes are 15% under spot and the expiry is the listed one nearest 63 sessions; whole contracts only.
- The held exposure changes only on a target change of the recorded band or more, or to 0; shares are floor(weight x book equity / last close), frozen per decision.
