# mk-premarketathmorningfade: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Premarket all-time-high fade (SPY)", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'waiting': 1}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-premarketathmorningfade.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

Premarket all-time-high fade (SPY): one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: shorts SPY's open when its premarket high tops every prior session's high, unless the 10-minute Phase Oscillator is already overbought, and covers at noon.

Evaluation order (card plus the engine cell in `sleeves/milkman/intraday.py`, SETUPS entry `PMATH`: sleeve `mk_premarketathmorningfade`, side -1, cell `filter=kill;exit=12:00;stopATR=0.0`):

1. Premarket high: the 04:00-09:29 ET high must be above the highest high of every prior session (the all-time-high reference: Yahoo daily highs plus the clock-hour and 1-minute highs served).
2. Filter: the 10-minute Phase Oscillator at 09:30 must be under 61.8 (the cell's kill filter blocks the trade when the oscillator is already overbought).
3. Entry: short the open.
4. Exit: out at the last bar before 12:00 ET; no stop (stopATR = 0.0).
- Sizing and execution rendering (the study is per trade, every signal taken): $10,000 per trade on a $1,000,000 virtual book; lanes and overlapping trades net on SPY.
- Each minute of the session the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, and not if the study opens and closes it inside its deciding bar); open trades are closed by a market-on-close order 12 minutes before the close (their stops and targets are not watched after that pass and no trade enters after it).
- Early-close sessions are not traded.

## Files in this repo

- This package: `docs/MK_PREMARKETATHMORNINGFADE-RECREATE.md`
- Strategy card: `strategies/milkman/mk-premarketathmorningfade.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/intraday.py` (engine module; detection restated over the desk's SPY bar arrays)
  - `sleeves/milkman/vendor/milkman/mlib.py` (the study's own library, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_intraday.py` runs the study's own scripts on synthetic vault files and compares every trade.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: SPY only. Asset class: US ETF. Timeframe: 1m bars, 10m Phase Oscillator.
- Status in the accounting/catalog: waiting.
- State: the day's premarket high and all-time-high reference; the open short and its noon exit.

## Data inputs

Yahoo SPY 1-minute bars with the extended session (7 days), Yahoo clock-grid hours (59 days) and Yahoo daily bars; full sessions only (sessions with at least 300 RTH bars; half days dropped). 3m / 10m / 1h / 4h candles are built from the all-hours bars (before 20:00, bins from midnight) and their indicators run continuously across sessions. The all-time-high reference adds Yahoo daily highs over the full history.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine's dependencies (numpy and pandas for the intraday module; the vendored study code runs as plain Python when numba is absent, via the stand-in registered by `sleeves/milkman/vendored.py`).
3. Import the engine module named in the Files section inside the desk engine; it registers one sleeve per rule with the sleeve id and designated cells recorded in the Full algorithm section.
4. Serve the declared data inputs (daily or intraday bars per the Data inputs section) and the sleeve's book state.
5. Run the desk engine; the sleeve evaluates on its session phases / per-minute cadence as recorded in the Full algorithm section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test; the parity tools named in the Files section replay the rule programs against the study's own functions. Behavior checklist, from the algorithm section:

- A premarket high that does not exceed every prior session's high produces no entry.
- A qualifying premarket high with the 10-minute Phase Oscillator at 09:30 at or above 61.8 produces no entry.
- A qualifying signal produces exactly one short at the open, exited at the last bar before 12:00 ET, with no stop firing before then.