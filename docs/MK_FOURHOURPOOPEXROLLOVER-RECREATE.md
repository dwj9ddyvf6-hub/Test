# mk-fourhourpoopexrollover: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Four-hour Phase Oscillator OpEx rollover (SPY)", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'waiting': 1}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-fourhourpoopexrollover.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

Four-hour Phase Oscillator OpEx rollover (SPY): one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: in the week after monthly options expiry, shorts SPY when its 4-hour Phase Oscillator rolls over from 80 while price is stretched above last week's or month's close, and holds 10 sessions.

Evaluation order (card plus the engine cell in `sleeves/milkman/intraday.py`, SETUPS entry `OPX4`: sleeve `mk_fourhourpoopexrollover`, side -1, cell `ext=0.618;H=10`):

1. Window: only on the session on or after the third Friday (monthly options expiry) or the 5 sessions after it.
2. Signal: a 4-hour candle whose Phase Oscillator is under 80 after a candle at 80 or above (rollover), the first such signal per day.
3. Stretch filter: the 4-hour close is at least 0.618 ATR above the prior completed week's or month's close (the greater of the two; their ATR14).
4. Entry: short at the market at the next pass; when the candle closes outside the regular session, at the next regular open.
5. Exit: at the close of the 10th full session after the signal day, market-on-close. No stop or target is recorded for this sleeve.
- Sizing and execution rendering (the study is per trade, every signal taken): $10,000 per trade on a $1,000,000 virtual book; lanes and overlapping trades net on SPY.
- Each minute of the session the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, and not if the study opens and closes it inside its deciding bar); open trades are closed by a market-on-close order 12 minutes before the close (their stops and targets are not watched after that pass and no trade enters after it).
- Early-close sessions are not traded.

## Files in this repo

- This package: `docs/MK_FOURHOURPOOPEXROLLOVER-RECREATE.md`
- Strategy card: `strategies/milkman/mk-fourhourpoopexrollover.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/intraday.py` (engine module; detection restated over the desk's SPY bar arrays)
  - `sleeves/milkman/vendor/milkman/mlib.py` (the study's own library, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_intraday.py` runs the study's own scripts on synthetic vault files and compares every trade.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: SPY only. Asset class: US ETF. Timeframe: 4h candles (Phase Oscillator), daily-hold exit.
- Status in the accounting/catalog: waiting.
- State: the open trade's signal day and its 10-session exit deadline; per-day first-signal latch.

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

- A 4-hour Phase Oscillator rollover (a candle under 80 after one at 80 or above) outside the post-expiry window produces no entry.
- The same rollover inside the window but with the 4-hour close less than 0.618 ATR above the greater of the prior week's / month's close produces no entry.
- A qualifying signal produces exactly one short, and exactly one exit at the close of the 10th full session after the signal day.
- A second rollover candle on the same day produces no second entry.