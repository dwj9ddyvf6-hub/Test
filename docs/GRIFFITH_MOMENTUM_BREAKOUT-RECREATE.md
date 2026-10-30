# griffith-momentum-breakout: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Momentum breakout (legacy setup)", type breakout, family griffith, universe "SPY, QQQ, IWM, the SCOPE radar's top 100, held names", asset US equities, timeframe "1m (15-minute cycle)", creator "Griffith / Ledge desk agentic runtime, SetupAgents momentum_breakout". Algorithm grade PARTIAL with entry, exit and sizing not in the accounting's consulted sources; the rules below are from the Test card and running Test code.
- Test catalog entry `griffith-momentum-breakout`: card `strategies/griffith/griffith-momentum-breakout.md`, code `sleeves/griffith/griffith_intraday.py` plus `desk/vendor/griffith/config.json`; that config path was NOT found in the Test tree at batch start and a fetch of it failed, so it is recorded here as not in this repo (per the card itself). Status waiting.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

Buys $100 of a scanned name pressing its 20-bar high on rising volume, with a 1.5% stop and a 3% target (card summary).

## Full algorithm

Evaluation order, from the card and the legacy cycle in `sleeves/griffith/griffith_intraday.py` (LEGACY map griffith_momentum_breakout -> momentum_breakout; one agentic cycle every 15 minutes):

1. Scan every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread <= 0.6%; score = 0.8 x |gap| + |intraday move| + min(relative volume, 5) + log10(dollar volume) / 3.
2. The 15 best get a headline score (positive less negative words, +0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars.
3. Setup (momentum_breakout in `decide`): price >= 99.9% of the 20-bar high, relative volume >= 1.5 and RSI(14) < 78 (+3 points).
4. BUY when scan + headline + setup points >= 5, price not over EMA20 + 2.5 x max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day is not under -0.6%.
5. Order: $100 (round(100 / price, 6) shares) as a DAY limit at price x 1.001; at most 30 positions; never a held or working name.
6. Exit: stop 1.5% under the entry, target 3% over it.

## Files in this repo

- This package: `docs/GRIFFITH_MOMENTUM_BREAKOUT-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-momentum-breakout.md`
- Running code (already in Test; nothing vendored): `sleeves/griffith/griffith_intraday.py` (legacy_cycle, decide, broad_scan, market_regime, funnel). The catalog's `desk/vendor/griffith/config.json` is not in this repo (see Provenance).

## Configuration

- Universe: SPY, QQQ, IWM, SCOPE radar top 100, held names. Timeframe: 1-minute bars, 15-minute cycle. Size: $100 per trade. Max positions: 30. Stop 1.5%, target 3%.

## Data inputs

Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes, per the card).

## Install and run

1. Clone this repository (Test).
2. Import the legacy setup sleeve for griffith_momentum_breakout from `sleeves/griffith/griffith_intraday.py` (returned by `sleeves()`) and register it with the desk runtime.
3. Configure snapshot, news and 1-minute bar feeds for the scan universe.
4. Run the 15-minute cycle during the regular session.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- A candidate below 99.9% of its 20-bar high, or with relative volume below 1.5, or RSI(14) >= 78, earns no setup points and cannot reach the BUY threshold on setup alone.
- With total points >= 5, price within the EMA20 + 2.5 x max(ATR, 0.2% of price) cap, and the index average day at or above -0.6%, exactly one DAY limit for round(100 / price, 6) shares at price x 1.001 is emitted.
- A held or working name is never re-bought; the book never exceeds 30 positions.
- A position exits at 1.5% under entry (stop) or 3% over entry (target).
