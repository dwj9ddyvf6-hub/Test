# mk-milkmancryptolinkedstockvariant: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Milkman daily rules on crypto-linked stocks", type crypto basis and funding (as classified in the accounting), family milkman, style "Rule basket", universe "134 crypto-linked US stocks", asset class US equities, timeframe "1d", creator "The Milkman v2 study's crypto variant, on the desk research crypto-linked stock list". Algorithm grade PARTIAL, gaps entry/exit/sizing in the accounting; filled here from the Test card and code.
- Test catalog entry `mk-milkmancryptolinkedstockvariant`: card `strategies/milkman/mk-milkmancryptolinkedstockvariant.md`, status live: 1.
- Alias: `mk_milkmancryptolinkedstockvariant`.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Runs nine of the study's daily rules, long and short, on 134 crypto-linked US stocks.

## Full algorithm

From `strategies/milkman/mk-milkmancryptolinkedstockvariant.md`, in evaluation order:

1. Universe filter: the crypto-linked stock list's symbols among the 1,822 stocks (134 names). Stocks trade only while their 20-day mean dollar volume is >= $5M and the close >= $3.
2. Entry rules, each long and short: Connors Double 7 (7, SMA200), Legend's Buy Day overnight (3), Daily Bilbo Box (5, EMA50 trail), Swing and Multi-day Golden Gates, EMA21 deviation (2 ATR, 10 sessions), Phase Oscillator accumulation (20 sessions), Pivot Ribbon 13/48, compression expansion (10 bars, 5 sessions). The per-rule entry formulas are in the code listed in Files (`daily.py` / `rules.py` / vendor files); the card records the rule names and parameters above and no further entry formula: any finer entry detail beyond those parameters is not in the record on the card.
3. Exit: each rule exits by its own rule: a 7-day closing extreme, the next open, the EMA50 trail, a gate target, stop or period end, an EMA21 touch, a fixed hold, the opposite cross.
4. Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This doc: `docs/MK_MILKMANCRYPTOLINKEDSTOCKVARIANT-RECREATE.md`
- Strategy card: see Provenance.
- Code (already in Test): `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Crypto universe list in Test: `sleeves/milkman/vendor/milkman/crypto_universe.csv`

## Configuration

- Universe: 134 crypto-linked US stocks. Timeframe: 1d. Book: $1,000,000, $10,000 a trade. Filters: 20-day mean dollar volume >= $5M, close >= $3.

## Data inputs

- The desk's split-adjusted daily bars (>= 260 since 2016) and live quotes.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Load the crypto universe from `sleeves/milkman/vendor/milkman/crypto_universe.csv` and intersect it with the 1,822-stock store as recorded.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No name outside the 134-name intersection trades, and no name trades while its 20-day mean dollar volume is under $5M or its close is under $3.
- All nine recorded rules run long and short with the parameters in step 2.
- Each position exits only by its own rule's exit in step 3.
