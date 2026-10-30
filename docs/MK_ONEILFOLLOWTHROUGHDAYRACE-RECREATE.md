# mk-oneilfollowthroughdayrace: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "O'Neil follow-through-day race", type market timing and rotation, family milkman, style "Market-timing breakout", universe "14 index ETFs and futures", asset class US index ETFs and futures, timeframe "1d", creator "William O'Neil's follow-through day, as coded by the Milkman v2 study". Algorithm grade PARTIAL, gaps entry/exit/sizing in the accounting; filled here from the Test card and code. Variants recorded: long row `mk_oneilfollowthroughdayrace` and short row `mk_oneilfollowthroughdayrace_short`.
- Test catalog entry `mk-oneilfollowthroughdayrace`: card `strategies/milkman/mk-oneilfollowthroughdayrace.md`, status waiting: 2.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

After a 10% correction, a follow-through day (day 4+ of a rally, up 1.25% on rising volume) starts a race: the long row targets the same distance up, the short row the correction low.

## Full algorithm

From `strategies/milkman/mk-oneilfollowthroughdayrace.md`, in evaluation order:

1. Correction: a close 10% under the highest close of the last 63 sessions; the lowest low since is the correction low.
2. Rally: the first up close is day 1; a low under day 1's low restarts the count; from day 4, a close up >= 1.25% on higher volume than the day before is the follow-through day; enter at its close. Distance = close - correction low.
3. Reset: a close back within 0.1% of the 63-day high resets the setup.
4. Exit, long row: target close + distance, stop the correction low. Short row: target the correction low, stop close + distance. From the next bar, stop is checked first; otherwise exit at the close after 120 sessions.
5. Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This doc: `docs/MK_ONEILFOLLOWTHROUGHDAYRACE-RECREATE.md`
- Strategy card: see Provenance.
- Code (already in Test): `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: 14 index ETFs and futures. Timeframe: 1d. Book: $1,000,000, $10,000 a trade (see algorithm step 5). Status: waiting (2 rows).

## Data inputs

- Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Net the long and short lanes per symbol before trading, as recorded in step 5.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry before day 4 of a rally, and no entry unless the follow-through close is up >= 1.25% on higher volume than the prior day.
- A low under day 1's low restarts the rally count; a close within 0.1% of the 63-day high resets the setup.
- Long target / stop and short target / stop are exactly the mirror values in step 4; the stop is checked before the target from the next bar, and any surviving trade exits at the close after 120 sessions.
