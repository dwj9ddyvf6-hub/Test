# mk-weekdayopentocloseproxy: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Weekday open-to-close (Monday)", type market timing and rotation, family milkman, style "Calendar", universe "14 index ETFs and futures", asset class US index ETFs and futures, timeframe "1d", creator "Milkman Trades (milkmantrades.com), ES Monday; the Milkman v2 study". Algorithm grade PARTIAL, gaps entry/exit/sizing in the accounting; filled here from the Test card and code. Variants: long row `mk_weekdayopentocloseproxy`, short row `mk_weekdayopentocloseproxy_short`.
- Test catalog entry `mk-weekdayopentocloseproxy`: card `strategies/milkman/mk-weekdayopentocloseproxy.md`, status waiting: 2.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Buys (the short row: shorts) each index instrument at Monday's open and exits at Monday's close.

## Full algorithm

From `strategies/milkman/mk-weekdayopentocloseproxy.md`, in evaluation order:

1. Entry: every Monday, enter at the open of each of the 14 index instruments (long row long, short row short).
2. Exit: out at that session's close, market-on-close.
3. Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This doc: `docs/MK_WEEKDAYOPENTOCLOSEPROXY-RECREATE.md`
- Strategy card: see Provenance.
- Code (already in Test): `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: 14 index ETFs and futures. Timeframe: 1d. Book: $1,000,000, $10,000 a trade. Status: waiting (2 rows).

## Data inputs

- Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Net the long and short lanes per symbol before trading.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Entries occur only on Mondays, at the open, in all 14 instruments, on the correct side per row.
- Every position exits at that same session's close, market-on-close; nothing is held overnight.
