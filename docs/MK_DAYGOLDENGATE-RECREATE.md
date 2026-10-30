# mk-daygoldengate — Recreation Package

## Provenance

- Canonical name: Day Golden Gate (SPY); algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: mk_daygoldengate.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Day Golden Gate (SPY)" (also docs/ALL-SLEEVES.md); Test catalog entry 'mk-daygoldengate' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

Day Golden Gate (SPY): the first intraday crossing of the +/-38.2% daily-ATR Golden Gate level, targeting the 61.8% level. Family milkman; type breakout; universe SPY; asset class US ETF; timeframe 1m (daily ATR levels). The accounting records no entry, exit or sizing rule in its consulted sources; the code in this repo below supplies the rule.

## Full algorithm

Engine: sleeves/milkman/intraday.py, detect21(), setup DGG, designated cell "mk_daygoldengate": [(+1, "cohort=live;filter=none"), (-1, "cohort=live;filter=none")]. The same ladder and gates in live options form are in sleeves/saty_day.py (see the Bilbo package for that expression; the plain Golden Gate there is the mid-zone case).
Evaluation order:
1. Day ladder: PDC = prior day's close, A = prior day's ATR14; Level(x, side) = PDC + side x x x A. If A or PDC is not finite, no trades.
2. For each side: gate = Level(0.382, side); find the first session bar whose high reaches the gate (long) or whose low reaches it (short). Cohort live requires the session open inside the gate (open < gate for long, open > gate for short); the designated cell is cohort=live.
3. Entry price: max(open of the hit bar, gate) for long (min for short) when the hit is after the first bar, else the session open.
4. Record DGG filter=none with target Level(0.618, side) and stop Level(0.236, side), stop mode 10. (detect21 also records a filter=before11 variant when the hit bar's minute <= 90; it is not the designated cell.)
5. No Phase Oscillator, ribbon or confluence filter applies to DGG in detect21() (filter=none); the oscillator only separates the Bilbo variant.

## Files in this repo

- This package: `docs/MK_DAYGOLDENGATE-RECREATE.md`
- Signal engine (intraday): `sleeves/milkman/intraday.py` (Panel, detect21(), SETUPS, LV levels)
- Signal engine (daily): `sleeves/milkman/daily.py` (HIS cells, feed_bars(), feed_quotes())
- Live SPY-options expression of the same ladder: `sleeves/saty_day.py` (CONFIG, F_TRIGGER/F_GATE/F_MID/F_TARGET/F_RUNNER/F_FULL, Phase Oscillator and Pivot Ribbon gates, QQQ confluence)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog entries in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/milkman/intraday.py, sleeves/milkman/daily.py and sleeves/saty_day.py in this repo); dwj9ddyvf6-hub/Silicon (21,337 entries; only Milkman research/teardown notes, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (47,379 entries; no milkman sleeve module); dwj9ddyvf6-hub/Midna (7,855 entries; milkman-study research/backtests only, no live sleeve code). Code was already in Test, so nothing was vendored.

## Configuration

- Sleeve id mk_daygoldengate (alias mk_daygoldengate); Test catalog status: waiting.
- Designated cell: cohort=live;filter=none, both sides; gate 0.382, target 0.618, stop 0.236 (fractions of the prior day's ATR14 from the prior close).

## Data inputs

- SPY 1-minute bars; daily aggregates for the prior day's close and ATR14.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/milkman/intraday.py` at that path with its Panel inputs wired as its header describes.
3. Register sleeve mk_daygoldengate with the designated cell cohort=live;filter=none for both sides.
4. Run the desk cycle; the first gate touch of the session emits the DGG trade per the algorithm.
5. First evaluation: fixture prior close 100.00, prior ATR14 2.00, session open 100.10, and a later bar trading up through 100.764; confirm one long DGG record entered at max(open, 100.764), target 101.236, stop 100.472.

## Verification

- Fixture above: exactly one long DGG record with those levels; a second touch later in the session emits nothing (first crossing only).
- Fixture with the session open at or above the gate: no live-cohort trade.
- Short-side mirror holds with negative levels.
- Fixture with non-finite prior ATR or close: no trades.
