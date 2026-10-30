# apex-c5-reflex: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX C5: REFLEX", type forecast and ML models, family apex, style Analog (nearest-neighbour) forecast, universe QQQ, TQQQ, BIL, asset class US ETFs (incl. 3x leveraged), timeframe 1d, creator APEX research desk (Cursor2), round 3 C5. Algorithm grade PARTIAL in the accounting, with gaps: entry/signal rule, exit rule and sizing not recorded in the accounting's consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card and the code below, both named here; nothing is filled from outside Test.
- Test catalog entry (Test `docs/CATALOG.json`): id `apex-c5-reflex`, status live (status_counts live: 1), card `strategies/apex/apex-c5-reflex.md`, rows master_desk: [`apex_c5_reflex`], code list as in Files.
- Strategy card in Test: `strategies/apex/apex-c5-reflex.md` (full Entry / Exit / Sizing / Data text, reproduced in the Full algorithm).
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b23_Test_tree.txt in the run workspace) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, adapters3/, integration/, desk3/, packages/, strategies/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for these ids (no aster_tensor, aster_r19 or r19_tensor filename in any of those three trees). The code is already in Test (see Files); the apex sleeve files are also present under `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/apex.py` and the feedlib / parity packages in Test.

## What this strategy is

The GESTALT analog engine with a recency check: Nasdaq leverage is set from the 150 most similar past market states, then cut to a quarter when recent analogs turn negative, or raised 25% when they run stronger.

## Full algorithm

From the strategy card in Test (`strategies/apex/apex-c5-reflex.md`), in evaluation order:

1. State: trend score, log volatility and its 21-day change, the 252-day drawdown, the 21-day return, the 63-day change in the 10-year yield, VIX against its 252-day median, and semiconductors' 63-day return over the Nasdaq's.
2. Refit and recency (C5 = the GESTALT analog engine with a recency check): every 5 sessions from 2001: leverage = 0.5 x the shrunk mean forward 21-day excess return of the 150 nearest past states / max(volatility, 5%) squared, clipped to 0-4. Recency: with at least 15 of the 150 in the last 1,260 sessions, a negative mean among those while all 150 average positive cuts leverage to a quarter; a recent mean more than 10 points above the 150's raises it 25% (max 4). The held exposure moves to it only on a change of 0.20 or more, or to 0.
3. Exit: no stop: a negative analog mean takes the exposure to 0.
4. Sizing and execution:
- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1x is QQQ, 1-3x is QQQ + TQQQ (QQQ + 3 x TQQQ = L), above 3x TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight x book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_C5_REFLEX-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/apex/apex-c5-reflex.md`
- Code (already in Test):
- `sleeves/apex/apex.py`
- `sleeves/apex/feedlib/apex_rules.py`
- `sleeves/apex/feedlib/apex.py`
- `sleeves/apex/vendor/apex/round3.py`
- `sleeves/apex/vendor/apex/inventions.py`
- `sleeves/apex/vendor/apex/strategies.py`
- Rule lines: `docs/verify/apex.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe QQQ, TQQQ, BIL; asset class US ETFs (incl. 3x leveraged); timeframe 1d; book $100,000 (card sizing); leverage clipped to 0-4; refit every 5 sessions from 2001; exposure moves only on a change of 0.20 or more, or to 0.
- Cadence and state beyond the above: not in the record.

## Data inputs

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close (card Data section).

## Install and run

1. Clone the Test repo.
2. Place the code files listed in Files at their repo paths (`sleeves/apex/apex.py` is the sleeve entry; the sleeve id inside it is `apex_c5_reflex`).
3. Wire the daily data inputs above so the state vector can be computed after each close.
4. First run: compute the state and the 150 nearest past states on a completed history; confirm that with a negative analog mean the target exposure is 0 and that no order is produced when the exposure change is below 0.20 (and not to 0), then run the Verification checklist.

## Verification

No per-sleeve test file for this id was found in Test. Behaviour checklist from the recorded algorithm:

- The state vector contains exactly the eight recorded components, and the neighbour set is the 150 nearest past states whose forward 21-day excess log return is known.
- Leverage equals the recorded formula, clipped to 0-4, and the held exposure changes only on a move of 0.20 or more, or to 0.
Refit and recency (C5 = the GESTALT analog engine with a recency check): every 5 sessions from 2001: leverage = 0.5 x the shrunk mean forward 21-day excess return of the 150 nearest past states / max(volatility, 5%) squared, clipped to 0-4. Recency: with at least 15 of the 150 in the last 1,260 sessions, a negative mean among those while all 150 average positive cuts leverage to a quarter; a recent mean more than 10 points above the 150's raises it 25% (max 4). The held exposure moves to it only on a change of 0.20 or more, or to 0.
- Instrument mapping follows the recorded sizing bands (QQQ up to 1x; QQQ + TQQQ for 1-3x; TQQQ alone above 3x; idle capital in BIL), with shares = floor(weight x book equity / last close) on a $100,000 book.
