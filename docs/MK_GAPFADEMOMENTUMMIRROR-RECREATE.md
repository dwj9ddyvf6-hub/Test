# mk-gapfademomentummirror: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Gap fade / momentum mirror (SPY)", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'waiting': 1}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-gapfademomentummirror.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

Gap fade / momentum mirror (SPY): one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: trades SPY's opening gap by size: fades it toward the prior close, or rides it half an ATR, by the lane's gap bucket.

Evaluation order (card plus the engine cells in `sleeves/milkman/intraday.py`, SETUPS entry `GAP`: long lane cell `bucket=0.0-0.1;stopATR=0.5;target=full`, short lane cell `bucket=0.25-0.5;stopATR=0.5;target=full`):

1. Gap = the open against the prior close, measured as a percentage.
2. Long lane (gap bucket 0-0.1%): gap down: fade long toward the prior close; gap up: mirror long, target +0.5 ATR.
3. Short lane (gap bucket 0.25-0.5%): gap up: fade short toward the prior close; gap down: mirror short, target -0.5 ATR.
4. Entry at the open. Fade trades: stop 0.5 ATR beyond the open. Mirror trades: target 0.5 ATR, stop the prior close.
5. Exit: target and stop by touch; otherwise out at the close.
- Sizing and execution rendering (the study is per trade, every signal taken): $10,000 per trade on a $1,000,000 virtual book; lanes and overlapping trades net on SPY.
- Each minute of the session the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, and not if the study opens and closes it inside its deciding bar); open trades are closed by a market-on-close order 12 minutes before the close (their stops and targets are not watched after that pass and no trade enters after it).
- Early-close sessions are not traded.

## Files in this repo

- This package: `docs/MK_GAPFADEMOMENTUMMIRROR-RECREATE.md`
- Strategy card: `strategies/milkman/mk-gapfademomentummirror.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/intraday.py` (engine module; detection restated over the desk's SPY bar arrays)
  - `sleeves/milkman/vendor/milkman/mlib.py` (the study's own library, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_intraday.py` runs the study's own scripts on synthetic vault files and compares every trade.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: SPY only. Asset class: US ETF. Timeframe: 1d gap, 1m exits.
- Status in the accounting/catalog: waiting.
- State: the open trade's side, target and stop levels for the session.

## Data inputs

Yahoo SPY 1-minute bars with the extended session (7 days), Yahoo clock-grid hours (59 days) and Yahoo daily bars; full sessions only (sessions with at least 300 RTH bars; half days dropped). 3m / 10m / 1h / 4h candles are built from the all-hours bars (before 20:00, bins from midnight) and their indicators run continuously across sessions.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine's dependencies (numpy and pandas for the intraday module; the vendored study code runs as plain Python when numba is absent, via the stand-in registered by `sleeves/milkman/vendored.py`).
3. Import the engine module named in the Files section inside the desk engine; it registers one sleeve per rule with the sleeve id and designated cells recorded in the Full algorithm section.
4. Serve the declared data inputs (daily or intraday bars per the Data inputs section) and the sleeve's book state.
5. Run the desk engine; the sleeve evaluates on its session phases / per-minute cadence as recorded in the Full algorithm section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test; the parity tools named in the Files section replay the rule programs against the study's own functions. Behavior checklist, from the algorithm section:

- A gap down inside the 0-0.1% bucket produces a long fade toward the prior close with its stop 0.5 ATR beyond the open; a gap outside both buckets produces no trade.
- A gap up inside the 0.25-0.5% bucket produces a short fade toward the prior close; a gap down in that bucket produces a short mirror with target -0.5 ATR and stop at the prior close.
- An open trade that touches neither target nor stop exits at the close (via the close-12 market-on-close pass).