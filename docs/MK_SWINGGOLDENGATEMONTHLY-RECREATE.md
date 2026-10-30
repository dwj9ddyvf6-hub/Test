# mk-swinggoldengatemonthly — Recreation Package

## Provenance

- Canonical name: Swing Golden Gate (monthly ATR); algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: mk_swinggoldengatemonthly.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Swing Golden Gate (monthly ATR)" (also docs/ALL-SLEEVES.md); Test catalog entry 'mk-swinggoldengatemonthly' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

Swing Golden Gate (monthly ATR): the Golden Gate level-crossing trade run on monthly periods, entry at the 0.618 monthly-ATR level, with an EMA gate and a pivot stop. Family milkman; type breakout; universe 1,822 US stocks + 14 index ETFs and futures (the daily module's index and univ sets); asset class US equities, index ETFs and futures; timeframe 1d (monthly ATR levels). The accounting records no entry, exit or sizing rule in its consulted sources; the code in this repo below supplies the rule. Note the accounting classification text described the monthly form through the intraday ladder (0.382 entry); the daily code's designated cell for this sleeve is entry_lvl=0.618, and the code is the truth.

## Full algorithm

Engine: sleeves/milkman/daily.py, rule SGG, designated cell: "freq=M;entry_lvl=0.618;ema_gate=with;stop=pivot".
Evaluation order (the daily module's session phases, carrying the study rules as its header states):
1. Periods: monthly Golden Gate periods; a period's levels come from the prior period (anchor and ATR of the prior monthly period; the module header notes the Swing GG monthly ATR is seeded from the genome-cache history rather than from 2016-01). Golden Gate periods are opened at the first look of the day.
2. Entry: the period's first touch of the entry level, anchor +/- 0.618 x ATR, in the touch direction, decides the period once (done_period: a period is decided once and entered once); entry_lvl = 0.618.
3. Gate: ema_gate = with (the study rule's EMA gate applies; the gate's own parameters live in the study rules the module imports and are not further specified in the cell: not in the record beyond ema_gate=with).
4. Stop: pivot (stop=pivot). Target: no tgt_lvl is recorded in the SGG cell (unlike MDGG's 0.618); the target rule is therefore not in the record beyond the study rule the module imports.
5. Execution phases: watch (open to close-16) open phase then touch phase on the session range so far; close (close-15 to close-11) touch phase again then close phase on the provisional bar, market-on-close; after (after the close) the completed bar, late events executing at the next open. An entry on a period's last session that does not exit on that bar is closed at that session's close (named divergence 7 in the module header).

## Files in this repo

- This package: `docs/MK_SWINGGOLDENGATEMONTHLY-RECREATE.md`
- Signal engine (intraday): `sleeves/milkman/intraday.py` (Panel, detect21(), SETUPS, LV levels)
- Signal engine (daily): `sleeves/milkman/daily.py` (HIS cells, feed_bars(), feed_quotes())
- Live SPY-options expression of the same ladder: `sleeves/saty_day.py` (CONFIG, F_TRIGGER/F_GATE/F_MID/F_TARGET/F_RUNNER/F_FULL, Phase Oscillator and Pivot Ribbon gates, QQQ confluence)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog entries in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/milkman/intraday.py, sleeves/milkman/daily.py and sleeves/saty_day.py in this repo); dwj9ddyvf6-hub/Silicon (21,337 entries; only Milkman research/teardown notes, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (47,379 entries; no milkman sleeve module); dwj9ddyvf6-hub/Midna (7,855 entries; milkman-study research/backtests only, no live sleeve code). Code was already in Test, so nothing was vendored.

## Configuration

- Sleeve id mk_swinggoldengatemonthly (alias mk_swinggoldengatemonthly); Test catalog status: live.
- Cell: freq=M, entry_lvl=0.618, ema_gate=with, stop=pivot.
- Sizing (daily module header): the study has none (per trade, equal weight, every signal taken); the desk rendering is a fixed $10,000 per trade on a $1,000,000 virtual book (NOTIONAL = 10,000.0, CAPITAL = 1,000,000.0); each lane keeps its own trade ledger and the sleeve trades the net per symbol.

## Data inputs

- Daily bars: index set from Yahoo daily OHLC (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD + ES=F, NQ=F, RTY=F, YM=F); univ set from split-adjusted daily bars for the store_v1 survivors (1,822 names, >= 260 bars since 2016-01-01, liquidity-gated).
- Quotes per session phase (Yahoo full quotes for the index set; the desk equity source for the univ set).

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/milkman/daily.py` at that path with its milkman package siblings (rules, vendored) from the same directory in this repo.
3. Register sleeve mk_swinggoldengatemonthly with the SGG cell exactly as in Configuration.
4. Run the desk cycle through its watch, close and after phases; the first monthly gate touch of a period (with the EMA gate satisfied) emits the entry per the algorithm.
5. First evaluation: fixture a monthly period with known prior-period anchor and ATR where a session first touches anchor + 0.618 x ATR with the EMA gate satisfied; confirm one entry with a pivot stop, and no second entry in the same period.

## Verification

- Fixture above: exactly one entry per period (done_period), at the 0.618 level (not 0.382).
- Fixture where the EMA gate is not satisfied at the touch: no entry.
- A position open at a period's last session without an exit on that bar is closed at that session's close.
- Sizing on every trade is the fixed $10,000 notional rendering; the sleeve trades the net per symbol across its lanes.
