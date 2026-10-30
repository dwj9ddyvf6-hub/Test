# Pivot Ribbon 13/48 cross (mk-pivotribbon1348cross): recreation package

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): canonical name 'Pivot Ribbon 13/48 cross', type trend following, family milkman, algorithm grade PARTIAL, unresolved false. Test catalog entry 'mk-pivotribbon1348cross' in docs/CATALOG.json. Strategy card in Test: strategies/milkman/mk-pivotribbon1348cross.md. Accounting gaps recorded: entry/signal rule, exit rule, and sizing not recorded in any consulted source in the accounting itself; the Test card and the Test code below record them, and this package uses those Test sources.

## What this strategy is

A daily trend following cross strategy from the Milkman v2 study, built on the Pivot Ribbon 13/48 conviction arrow: it buys when EMA13 crosses above EMA48, shorts the cross below, and exits on the opposite cross, holding at most 120 sessions. Universe recorded in the accounting and the card: 1,822 US stocks plus 14 index ETFs and futures. Asset class: US equities, index ETFs and futures. Timeframe: 1d.

## Full algorithm

Evaluation order, from the Test card (strategies/milkman/mk-pivotribbon1348cross.md) and the RIB rule in sleeves/milkman/rules.py (cell RIB, exitm=opposite):

1. Exits are evaluated before entries on each daily bar (RIB.close in sleeves/milkman/rules.py).
2. Exit: if exitm is 'opposite', a long position exits at the close when EMA13 is no longer above EMA48 and was above on the prior bar; a short exits at the close on the mirror cross. A position also exits at the close when it reaches the holding cap: cap = 120 sessions by default in the code (cell cap, default 120).
3. Entry: only at bar index t >= 60. A long entry fires at the close when EMA13 crosses above EMA48 on that bar (up[t] true and up[t-1] false, where up means EMA13 > EMA48); a short entry fires on the mirror cross.
4. Liquidity filter: an entry requires the recorded liquidity flag for that bar. The card records the filter as: stocks trade only while their 20-day mean dollar volume is at least $5M and the close is at least $3.
5. No price stop and no profit target are recorded for this rule; the only exits are the opposite cross and the 120 session cap above.
6. Sizing as recorded on the card: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open (card, Sizing section).

## Files in this repo

- This doc: docs/MK_PIVOTRIBBON1348CROSS-RECREATE.md
- Strategy card in Test: strategies/milkman/mk-pivotribbon1348cross.md
- Catalog entry in Test: docs/CATALOG.json, id mk-pivotribbon1348cross
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'Pivot Ribbon 13/48 cross'
- Code in Test (named by the card and the catalog code list): sleeves/milkman/daily.py, sleeves/milkman/rules.py (the RIB rule class, section 9 Pivot Ribbon), sleeves/milkman/vendor/milkman/dstrats.py, sleeves/milkman/vendor/milkman/dlib.py, sleeves/milkman/vendor/milkman/mlib.py, sleeves/milkman/vendored.py
- No code was vendored for this package; all code above was already in Test.

## Configuration

- Universe: 1,822 US stocks plus 14 index ETFs and futures (accounting and card).
- Timeframe: 1d. EMA periods: 13 and 48. Minimum bars before entry: 60 (card: at least 60 bars; code: t >= 60).
- Holding cap: 120 sessions. Exit mode in the code cell: exitm=opposite.
- Liquidity: 20-day mean dollar volume at least $5M and close at least $3 for stocks.
- Sizing: $10,000 per trade on a $1,000,000 book (card).
- Cadence, session, and state files beyond the above: not in the record.

## Data inputs

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history (card).
- Stocks: the desk split-adjusted daily bars, at least 260 bars since 2016 (card).
- Live quotes for the session so far (card). EMA13 and EMA48 series are computed by the code from those bars.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Read this package and the strategy card or algorithm doc named in the Files section.
3. Install the code paths named in the Files section at the same relative paths in a desk3-compatible runtime; the sleeve wrapper imports its shared engine by the module path recorded there, so keep the repo directory layout unchanged.
4. Configure the sleeve with the exact parameters in the Configuration section; do not substitute values from a different variant.
5. Provide the data inputs named in the Data inputs section through the runtime view (bars, positions, and quotes where the engine declares them).
6. Call the sleeve module's evaluate(view, ctx) function on the cadence recorded in the Configuration section and route the returned intents through the desk dispatcher; this package does not include a standalone broker connector.
7. Run the Verification checklist before trusting any output.

## Verification

Behavior checklist (no test file for this sleeve was located in Test):
1. Feed a daily series where EMA13 crosses above EMA48 at bar t >= 60 with the liquidity flag on: exactly one long entry at that close.
2. Continue until EMA13 crosses back below EMA48: the long exits at that close.
3. Hold a position with no opposite cross: it exits at the close 120 sessions after entry.
4. A cross before bar 60, or with the liquidity flag off, produces no entry.
5. A short entry on a downward cross exits on the upward cross or at the 120 session cap.
