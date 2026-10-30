# mk-legendsbuyday: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Legend's Buy Day", type mean reversion, family milkman. Algorithm grade in the accounting: PARTIAL, with the gaps "entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Test catalog entry (Test `docs/CATALOG.json`): id in the card path below; status counts {'live': 1, 'waiting': 1}; code list as in the Files section.
- Test strategy card: `strategies/milkman/mk-legendsbuyday.md`.
- Running code in Test (verified present at batch start by tree listing and file read): the engine module's setup table names this sleeve id with its designated cell (see Full algorithm).

## What this strategy is

Legend's Buy Day: one sleeve of the Milkman v2 study's rule set as installed on the master desk in this repo. The card summary and the full rule follow.

## Full algorithm

Card summary: after a run of down days, buys the close and sells the next open (overnight leg), or buys the next open and sells its close (day leg). The accounting merges the two rows (Tier A) under this one catalog entry: `mk_legendsbuydaydailyproxy` (overnight leg) and `mk_legendsbuydaydayleg` (day leg).

Evaluation order (card plus the engine tables in `sleeves/milkman/daily.py`: HIS entry `LBD` = (`mk_legendsbuydaydailyproxy`, `k=3;exact=True`), and the day-leg sleeve built with sid `mk_legendsbuydaydayleg`):

Overnight leg (daily proxy, stocks and index set, long and short):
1. Setup: exactly 3 lower closes in a row (long); exactly 3 higher closes in a row (short lane).
2. Entry: buy (or short) at the close of the third session.
3. Exit: sold (covered) at the next open.
4. Stock liquidity gate: stocks trade only while their 20-day mean dollar volume is at least $5M and the close is at least $3.

Day leg (SPY, long only):
1. Setup: exactly 4 sessions that each made a lower low than the one before (the session before them did not).
2. Entry: buy the next open if it is under the prior close + 0.15 x ATR (ATR here is the mean of the last 20 daily ranges) and above the stop.
3. Exit: stop one cent under the prior day's low; otherwise sold at that session's close.
4. Card note: the day leg reads SPY's regular-session bars in place of ES's full sessions (his ATR and stop use full-session ranges).
- Sizing and execution rendering (the study itself is per-trade, equal weight, every signal taken): a fixed $10,000 per trade on a $1,000,000 virtual book; each lane keeps its own trade ledger and the sleeve trades the net per symbol.
- Close rules are decided 15 to 11 minutes before the close on the provisional bar (open / high / low so far, last price as close, volume so far) and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.
- Engine phases (sleeves/milkman/daily.py header): watch (open to close-16: open phase, then touch phase on the session range so far), close (close-15 to close-11: touch phase, then close phase on the provisional bar), after (completed bar: missed touches, close phase not taken late, end phase; its events execute next open). Bars missed while the desk was down are replayed for state; their entries are not taken late and their exits execute at the next open.

## Files in this repo

- This package: `docs/MK_LEGENDSBUYDAY-RECREATE.md`
- Strategy card: `strategies/milkman/mk-legendsbuyday.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/daily.py` (engine module; carries the rule decisions to the desk engine by session phase)
  - `sleeves/milkman/rules.py` (the rule programs)
  - `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py` (the study's own code, vendored byte-exact in this repo)
  - `sleeves/milkman/vendored.py` (the vendored loader)
  - `sleeves/milkman/vendor/milkman/store_v1_1d_index.json` (the 1,822-name stock universe index)
- Parity replay tool (also in Test): `packages/claude/master-desk-parity-tools/tools/parity/milkman_daily.py` replays the rule programs against the study's own functions.
- Rule lines: `docs/verify/milkman.md`.

## Configuration

- Universe: overnight leg 1,822 US stocks plus 14 index instruments; day leg SPY. Asset class: US equities, index ETFs and futures. Timeframe: 1d.
- Status in the accounting/catalog: 1 live, 1 waiting.
- State: per-lane trade ledgers per symbol; the sleeve trades the net per symbol.

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

- Exactly 3 lower closes (not 2, not 4) produce an overnight-leg long at the third close and an exit at the next open; exactly 3 higher closes produce the short mirror.
- Four consecutive lower lows with the next open under prior close + 0.15 x ATR produce a day-leg long on SPY; an open at or above that band produces no day-leg entry.
- A day-leg position exits at one cent under the prior day's low when touched, else at that session's close.
- A stock failing the $5M / $3 liquidity gate produces no overnight-leg entry.