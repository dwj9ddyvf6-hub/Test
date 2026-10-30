# mk-atrlevelcascade — Recreation Package

## Provenance

- Canonical name: ATR level cascade (SPY); algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: mk_atrlevelcascade.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "ATR level cascade (SPY)" (also docs/ALL-SLEEVES.md); Test catalog entry 'mk-atrlevelcascade' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

ATR level cascade (SPY): an intraday trade sequence that enters at each successive ATR level of the day ladder and targets the next level, in both directions. Family milkman; type other; universe SPY; asset class US ETF; timeframe 1m. The accounting records no entry, exit or sizing rule and no code in its consulted sources (name-only evidence); the code in this repo below supplies the rule.

## Full algorithm

Engine: sleeves/milkman/intraday.py, detect21(), setup CASCADE, designated cell in SETUPS: "mk_atrlevelcascade": [(+1, "window=all"), (-1, "window=all")]. Constants: SYM = "SPY", LV = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.236], COST = 0.015 (the study's percent per side, parity only), LATE = 2 bars.
Evaluation order:
1. Day ladder: PDC = the prior day's close; A = the prior day's ATR14 (daily RTH aggregates of the 1-minute bars). If either is not finite, no trades that day. Level(x, side) = PDC + side x x x A.
2. For each side (+1, -1) and each level index i = 1..6 (levels 0.236, 0.382, 0.5, 0.618, 0.786, 1.0): find the first bar of the session whose high reaches the level (long side) or whose low reaches it (short side). Skip if there is no hit or the hit is the session's first bar.
3. Entry price: max(open of the hit bar, level) for the long side; min(open, level) for the short side (gap-through fills at the open).
4. Target = the next level out, Level(LV[i+1], side); stop = the previous level in, Level(LV[i-1], side); stop mode 0 in the study's trade record.
5. Designated cell window=all: both the pre-10:00 window and the all-day window record the trade (the window=pre10 variant requires the hit bar's minute < 30 after the open; the designated cell is window=all, so no time restriction applies).
No other filter (no Phase Oscillator, ribbon or confluence gate) applies to CASCADE in detect21().

## Files in this repo

- This package: `docs/MK_ATRLEVELCASCADE-RECREATE.md`
- Signal engine (intraday): `sleeves/milkman/intraday.py` (Panel, detect21(), SETUPS, LV levels)
- Signal engine (daily): `sleeves/milkman/daily.py` (HIS cells, feed_bars(), feed_quotes())
- Live SPY-options expression of the same ladder: `sleeves/saty_day.py` (CONFIG, F_TRIGGER/F_GATE/F_MID/F_TARGET/F_RUNNER/F_FULL, Phase Oscillator and Pivot Ribbon gates, QQQ confluence)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog entries in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/milkman/intraday.py, sleeves/milkman/daily.py and sleeves/saty_day.py in this repo); dwj9ddyvf6-hub/Silicon (21,337 entries; only Milkman research/teardown notes, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (47,379 entries; no milkman sleeve module); dwj9ddyvf6-hub/Midna (7,855 entries; milkman-study research/backtests only, no live sleeve code). Code was already in Test, so nothing was vendored.

## Configuration

- Sleeve id mk_atrlevelcascade (alias mk_atrlevelcascade); Test catalog status: waiting.
- Designated cell: window=all, both sides. Levels LV as above; ATR period 14 on the prior day; cost assumption 0.015% per side (study parity only).
- Sizing: not in the record for the intraday study module (it is per-trade, equal weight, every signal taken; the module carries CAPITAL = 1,000,000.0 as the study book). No per-trade dollar figure is recorded for this sleeve: not in the record.

## Data inputs

- SPY 1-minute bars (regular session) building the prior day's close and ATR14 and the live session's highs/lows/opens.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/milkman/intraday.py` at that path with its Panel inputs (1-minute SPY bars and the derived daily aggregates) wired as its header describes.
3. Register sleeve mk_atrlevelcascade with the designated cell window=all for both sides.
4. Run the desk cycle; detect21() emits CASCADE trades per the algorithm above.
5. First evaluation: fixture a day with prior close 100.00 and prior ATR14 2.00 where SPY first trades up through 100.764 (the 0.382 level) after the first bar; confirm one long CASCADE trade entered at max(open, 100.764) with target 101.00 (0.5 level) and stop 100.472 (0.236 level) for the i=2 step, and the corresponding records for each other level actually touched.

## Verification

- Fixture above: CASCADE records exactly for the levels touched, in level order, with next-level targets and previous-level stops.
- Fixture where a level is touched only on the session's first bar: no trade for that level.
- Fixture with a non-finite prior ATR or prior close: no trades that day.
- Short-side mirror: first low through a negative level enters short with the next negative level as target.
