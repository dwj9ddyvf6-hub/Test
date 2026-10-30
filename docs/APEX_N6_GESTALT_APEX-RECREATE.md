# apex-n6-gestalt-apex: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX N6: GESTALT × APEX", type "forecast and ML models", family "apex", style evidence "Trend × volatility + analog forecast", universe "QQQ, TQQQ, BIL", asset class "US ETFs (incl. 3× leveraged)", timeframe "1d", creator/source "APEX research desk (Cursor2), invention N6". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `apex-n6-gestalt-apex` in `docs/CATALOG.json` (card and code list as in Files).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A daily Nasdaq exposure book that averages two leverage targets: the APEX-50F trend/volatility target and the GESTALT analog-forecast leverage (invention N6). Exposure runs 0 to 4x; idle capital sits in BIL (T-bills).

## Full algorithm

From the card `strategies/apex/apex-n6-gestalt-apex.md`, with rule lines in `docs/verify/apex.md` (APEX N6 section), in evaluation order:

1. Compute the trend score on the Nasdaq-100 total return: the share of 6 bullish votes (price above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days). Compute volatility as a walk-forward HAR forecast of the next 5 days (features in `sleeves/femto/vendor/aurelia/features.py`; `sleeves/apex/vendor/apex/strategies.py:41-43`).
2. APEX-50F target: as defined in the APEX code (`strategies.py` / `inventions.py` APEX_50F params: sigma_target 0.5, l_max 4.0 in the N6 ensemble call).
3. GESTALT leverage: every 5 sessions from 2001, take the 150 most similar past states (z-scored distance over the GESTALT state features), take the mean of their known forward 21-day excess returns, annualise and shrink halfway (shrink 0.5) to the all-history mean; leverage = 0.5 x that mean / max(volatility, 5%)^2, clipped to 0-4 (half-Kelly form in `inventions.py:202-245`, `n5_gestalt` / `gestalt_leverage`). Held between refits.
4. N6 target exposure = 0.5 x (APEX-50F target + GESTALT leverage) (`inventions.py:248-251` `n6_ensemble`; `feedlib/apex_rules.py:364-369`).
5. Decision timing/band: decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
6. Exit: no stop. Exposure follows the target; a trend score of 0 holds only BIL.
7. Execution/sizing: market-on-close in the next session (orders from the open to 20 minutes before the close). Nasdaq exposure up to 1x is QQQ; 1-3x is QQQ + TQQQ with QQQ + 3 x TQQQ = L; above 3x TQQQ alone at L/3 on margin; idle capital in BIL. Shares = floor(weight x book equity / last close), frozen per decision; $100,000 book; debits pay 7.75% a year.

## Files in this repo

- This doc: `docs/APEX_N6_GESTALT_APEX-RECREATE.md`
- Strategy card: `strategies/apex/apex-n6-gestalt-apex.md`
- Rule lines: `docs/verify/apex.md` (APEX N6 section)
- Code (already in Test): `sleeves/apex/apex.py` (row `apex_n6_gestalt_apex`), `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/inventions.py` (`n6_ensemble`, `gestalt_leverage`), `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QQQ, TQQQ, BIL. Timeframe: 1d. Book: $100,000.
- GESTALT: k=150 neighbours, refit every 5 sessions, shrink 0.5, leverage clipped 0-4, start 2001-01-02 in the N5/GESTALT defaults used by the ensemble.
- Rebalance band: 0.20. Margin debit rate: 7.75% a year.
- Cadence/state: recomputed after each close; state is the held exposure and the frozen per-decision share counts.

## Data inputs

Yahoo full daily histories: ^NDX and QQQ (Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close (card Data section).

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `apex-n6-gestalt-apex` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/apex/vendor/apex/inventions.py` (`n6_ensemble`, lines 248-251) and the `apex_n6_gestalt_apex` row in `sleeves/apex/apex.py`; confirm the 0.5 averaging, the 0-4 clip and the 0.20 band match Configuration. Serve the Yahoo daily histories listed under Data inputs and run the sleeve's evaluate/run entry per session after the close.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- With trend score 0, the book holds only BIL.
- The target equals 0.5 x (APEX-50F target + GESTALT leverage) and never exceeds 4 or goes below 0.
- A target change under 0.20 (and not to 0) produces no trade; a change of 0.20 or more, or to 0, does.
- Exposure mapping: L <= 1 all QQQ; 1 < L <= 3 QQQ + TQQQ with QQQ + 3 x TQQQ = L; L > 3 TQQQ alone at L/3; residual in BIL.
- Share counts equal floor(weight x equity / last close) and are frozen per decision.
