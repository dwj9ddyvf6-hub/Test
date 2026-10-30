# mk-ema21deviationreversion: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "EMA21 deviation reversion", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'live': 1}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-ema21deviationreversion.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

EMA21 deviation reversion: one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: fades a close stretched k ATRs from its 21-day EMA and covers when price touches the EMA again, or after a set number of sessions.

Evaluation order (card plus the engine cell table in `sleeves/milkman/daily.py`, PLATEAU entry `E21`):

1. Indicators per symbol: EMA21 of close; ATR(14). Deviation = (close - EMA21) / ATR(14). At least 30 bars required.
2. Entry (at the close): long when the deviation first reaches -k or below; short when it first reaches +k or above. One trade at a time per symbol and lane.
3. Lane cells (engine: `("univ", +1): "k=2.0;H=10"`, `("univ", -1): "k=4.0;H=20"`, `("index", +1): "k=3.5;H=28"`, `("index", -1): "k=4.0;H=10"`; the card's variant table agrees):
   - Stocks, long: k = 2.0, max hold 10 sessions.
   - Stocks, short: k = 4.0, max hold 20 sessions.
   - Index set, long: k = 3.5, max hold 28 sessions.
   - Index set, short: k = 4.0, max hold 10 sessions.
4. Stock liquidity gate: stocks trade only while their 20-day mean dollar volume is at least $5M and the close is at least $3.
5. Exit: at a touch of the prior bar's EMA21 (or the open beyond it), else at the close after the lane's max hold.
- Sizing and execution rendering (the study itself is per-trade, equal weight, every signal taken): a fixed $10,000 per trade on a $1,000,000 virtual book; each lane keeps its own trade ledger and the sleeve trades the net per symbol.
- Close rules are decided 15 to 11 minutes before the close on the provisional bar (open / high / low so far, last price as close, volume so far) and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.
- Engine phases (sleeves/milkman/daily.py header): watch (open to close-16: open phase, then touch phase on the session range so far), close (close-15 to close-11: touch phase, then close phase on the provisional bar), after (completed bar: missed touches, close phase not taken late, end phase; its events execute next open). Bars missed while the desk was down are replayed for state; their entries are not taken late and their exits execute at the next open.

## Files in this repo

- This package: `docs/MK_EMA21DEVIATIONREVERSION-RECREATE.md`
- Strategy card: `strategies/milkman/mk-ema21deviationreversion.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/daily.py` (engine module; carries the rule decisions to the desk engine by session phase)
  - `sleeves/milkman/rules.py` (the rule programs)
  - `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py` (the study's own code, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
  - `sleeves/milkman/vendor/milkman/store_v1_1d_index.json` (the 1,822-name stock universe index)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_daily.py` replays the rule programs against the study's own functions.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: 1,822 US stocks (store_v1 survivors) plus the index set of 10 ETFs and 4 futures. Asset class: US equities, index ETFs and futures. Timeframe: 1d.
- Status in the accounting/catalog: live.
- State: per-lane trade ledgers per symbol (entry session, hold count); the sleeve trades the net position per symbol.

## Data inputs

Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history, auto_adjust=False. Stocks: the desk's split-adjusted daily bars for the store_v1 survivors (at least 260 bars since 2016-01-01), kept fresh by the genome job; a provisional (forming) stock bar comes from the quote source. Live quotes for the session so far.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Install the desk engine's dependencies (numpy and pandas for the intraday module; the vendored study code runs as plain Python when numba is absent, via the stand-in registered by `sleeves/milkman/vendored.py`).
3. Import the engine module named in the Files section inside the desk engine; it registers one sleeve per rule with the sleeve id and designated cells recorded in the Full algorithm section.
4. Serve the declared data inputs (daily or intraday bars per the Data inputs section) and the sleeve's book state.
5. Run the desk engine; the sleeve evaluates on its session phases / per-minute cadence as recorded in the Full algorithm section.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test; the parity tools named in the Files section replay the rule programs against the study's own functions. Behavior checklist, from the algorithm section:

- A daily series whose deviation first reaches -2.0 on a stock (with the liquidity gate passed and at least 30 bars) produces exactly one long entry at that close, and no second entry while it is open.
- The same series produces an exit at the first touch of the prior bar's EMA21, and in all cases an exit at the close after 10 sessions (stock long lane).
- A stock with 20-day mean dollar volume under $5M, or a close under $3, produces no entry.
- The index-long lane uses k = 3.5 and a 28-session max hold; the index-short lane k = 4.0 and 10 sessions; the stock-short lane k = 4.0 and 20 sessions.