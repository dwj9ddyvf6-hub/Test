# mk-vomyivomy: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Vomy / iVomy (SPY)", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'waiting': 2}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-vomyivomy.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

Vomy / iVomy (SPY): one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: buys a 10-minute pullback to EMA13 within 3 candles of an EMA8/13 bull flip (iVomy shorts the bear mirror), with the stop at EMA13.

Evaluation order (card plus the engine cells in `sleeves/milkman/intraday.py`, SETUPS entry `VOMY`: sleeve `mk_vomyivomy`, both sides, cell `flipwithin=3`):

1. Work on 10-minute candles. Long setup: EMA(8) above EMA(13), the bull flip (EMA8 crossing above EMA13) came within the last 3 candles, the candle's low touched EMA(13), and the candle closed above EMA(8).
2. Short setup (iVomy): the exact mirror (EMA8 below EMA13, bear flip within the last 3 candles, high touched EMA13, close below EMA8).
3. Entry at the candle's close.
4. Exit: stop at that candle's EMA(13), on a 10-minute close beyond it; otherwise out at the close.
5. Card note: since master-desk commit 78fd79e5 (2026-10-26, after this catalog's pin) each side runs as its own book: `mk_vomyivomy` long, `mk_vomyivomy_short` short. The accounting records the base alias's variant as "variant not recorded in any source" and the `mk_vomyivomy_short` alias's variant as "short".
- Sizing and execution rendering (the study is per trade, every signal taken): $10,000 per trade on a $1,000,000 virtual book; lanes and overlapping trades net on SPY.
- Each minute of the session the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, and not if the study opens and closes it inside its deciding bar); open trades are closed by a market-on-close order 12 minutes before the close (their stops and targets are not watched after that pass and no trade enters after it).
- Early-close sessions are not traded.

## Files in this repo

- This package: `docs/MK_VOMYIVOMY-RECREATE.md`
- Strategy card: `strategies/milkman/mk-vomyivomy.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/intraday.py` (engine module; detection restated over the desk's SPY bar arrays)
  - `sleeves/milkman/vendor/milkman/mlib.py` (the study's own library, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_intraday.py` runs the study's own scripts on synthetic vault files and compares every trade.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: SPY only. Asset class: US ETF. Timeframe: 10m.
- Status in the accounting/catalog: 2 waiting.
- State: the open trade's entry candle EMA(13) stop level.

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

- A bull flip 4 or more candles before the pullback candle produces no entry; a flip within 3 candles with the low touching EMA13 and a close above EMA8 produces exactly one long at that candle's close.
- A held long exits on the first 10-minute close beyond (below) the entry candle's EMA13, and otherwise at the session close.
- The short side mirrors every condition and level.