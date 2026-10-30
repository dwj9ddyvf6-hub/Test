# mk-bilbogoldengate — Recreation Package

## Provenance

- Canonical name: Bilbo Golden Gate (SPY); algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: mk_bilbogoldengate.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Bilbo Golden Gate (SPY)" (also docs/ALL-SLEEVES.md); Test catalog entry 'mk-bilbogoldengate' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

Bilbo Golden Gate (SPY): the Day Golden Gate entry whose last completed 1-hour Phase Oscillator sits in the aligned extreme zone, rising. Family milkman; type breakout; universe SPY; asset class US ETF; timeframe 1m with a 1h Phase Oscillator. The accounting records no entry, exit or sizing rule in its consulted sources; the code in this repo below supplies the rule (the accounting classification evidence names the same mechanism: entry in the touch direction at the +/-38.2% ATR level with same-direction QQQ confluence, Bilbo being its Phase Oscillator extreme tag, in sleeves/saty_day.py).

## Full algorithm

Two code expressions of the same setup exist in this repo; both are recorded, and where they differ the difference is stated.
A. Study engine (sleeves/milkman/intraday.py, detect21(), setup BGG, designated cell "mk_bilbogoldengate": [(+1, "cohort=live;filter=zone_rising"), (-1, "cohort=live;filter=zone_rising")]):
1. Day ladder: PDC = prior day's close, A = prior day's ATR14; Level(x, side) = PDC + side x x x A; levels used: 0.236 (stop), 0.382 (gate), 0.618 (target), 1.0 (extended target variant).
2. Gate touch: first session bar whose high reaches Level(0.382, +1) (long) or whose low reaches Level(0.382, -1) (short). Cohort live requires the session open to start inside the gate (open < gate for long, open > gate for short). Entry price: max(open of hit bar, gate) if the hit is after the first bar, else the open.
3. Bilbo tag: p1 = the last completed 1-hour Phase Oscillator value at the hit bar, p0 = the previous one. Zone: p1 > 61.8 (long) or p1 < -61.8 (short). Rising: p1 > p0 (long) or p1 < p0 (short). The designated cell filter=zone_rising requires zone AND rising.
4. On a qualifying touch, record BGG with target Level(0.618, side) and stop Level(0.236, side), stop mode 10. (detect21 also records zone-only and zone-with-target-1.0 variants; the designated cell is zone_rising at the 0.618 target.)
B. Live desk expression (sleeves/saty_day.py, SPY 0DTE options): ladder frozen before the open from the previous completed regular-session daily bar (anchor = that close, unit = ATR(14); F_TRIGGER 0.236, F_GATE 0.382, F_MID 0.500, F_TARGET 0.618, F_RUNNER 0.786, F_FULL 1.000). A Golden Gate touch is gated by the last completed 1h Phase Oscillator (aligned extreme, PO_EXTREME 61.8, tags the trade Bilbo and earns runner rights; the opposite extreme blocks it; mid-zone is a plain Golden Gate), by the 10m Pivot Ribbon Pro (a full opposing stack or a chop read stands the trade down), and by SPX/NQ confluence via QQQ (no entry without QQQ moving the same way). Exits: a 10-minute close back through the 0.236 trigger kills the position; half comes off at the 0.500 midpoint; the rest exits at 0.618 unless Bilbo or trend runner rights keep a runner to 0.786 and the full ATR; everything is flat by the close. Instrument: SPY same-day-expiry options, at-the-money or nearest strike; sizing: premium budget 4% of slice equity (BUDGET_PCT 0.04, 1 contract minimum), midday bull Golden Gates at half size, sleeve daily stop $10,000 (DAILY_STOP_USD), spread gate 0.05.

## Files in this repo

- This package: `docs/MK_BILBOGOLDENGATE-RECREATE.md`
- Signal engine (intraday): `sleeves/milkman/intraday.py` (Panel, detect21(), SETUPS, LV levels)
- Signal engine (daily): `sleeves/milkman/daily.py` (HIS cells, feed_bars(), feed_quotes())
- Live SPY-options expression of the same ladder: `sleeves/saty_day.py` (CONFIG, F_TRIGGER/F_GATE/F_MID/F_TARGET/F_RUNNER/F_FULL, Phase Oscillator and Pivot Ribbon gates, QQQ confluence)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog entries in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/milkman/intraday.py, sleeves/milkman/daily.py and sleeves/saty_day.py in this repo); dwj9ddyvf6-hub/Silicon (21,337 entries; only Milkman research/teardown notes, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (47,379 entries; no milkman sleeve module); dwj9ddyvf6-hub/Midna (7,855 entries; milkman-study research/backtests only, no live sleeve code). Code was already in Test, so nothing was vendored.

## Configuration

- Sleeve id mk_bilbogoldengate (alias mk_bilbogoldengate); Test catalog status: waiting.
- Designated cell (study engine): cohort=live;filter=zone_rising, both sides; target 0.618 level, stop 0.236 level.
- Live expression (saty_day CONFIG): cadence_s 60, universe (SPY,), risk_pct 0.04; constants as in algorithm B.

## Data inputs

- SPY 1-minute bars; daily bars for the prior close and ATR14; completed 1-hour bars for the Phase Oscillator; (live expression) 10-minute bars for the Pivot Ribbon, QQQ bars for confluence, and same-day SPY option quotes.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/milkman/intraday.py` at that path (study engine) and, for the live options expression, `sleeves/saty_day.py` with its core/saty_bars, core/saty_indicators and core/saty_primitives imports.
3. Register sleeve mk_bilbogoldengate with the designated cell cohort=live;filter=zone_rising for both sides.
4. Run the desk cycle; a gate touch with the Phase Oscillator in the aligned extreme zone and rising emits the BGG trade per the algorithm.
5. First evaluation: fixture a live-cohort day where the 0.382 level is touched with the last completed 1h Phase Oscillator at +70 and rising; confirm exactly one long BGG record, target at the 0.618 level, stop at the 0.236 level; the same touch with the oscillator at +40 (mid-zone) emits a plain Day Golden Gate record and no BGG record.

## Verification

- Fixture above: BGG only when zone and rising both hold; zone without rising records only the non-designated zone variant, not the designated cell.
- Fixture with the oscillator in the opposite extreme: no BGG (and, in the live expression, the Golden Gate itself is blocked).
- Fixture with the session open already beyond the gate (cohort not live): no designated-cell trade.
- Live expression: a 10-minute close back through the 0.236 trigger after entry kills the position; half exits at the 0.500 midpoint.
