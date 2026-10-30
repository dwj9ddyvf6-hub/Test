# mk-multidaygoldengateweekly — Recreation Package

## Provenance

- Canonical name: Multi-day Golden Gate (weekly ATR); algorithm grade in the accounting: PARTIAL; unresolved: False.
- Aliases: mk_multidaygoldengateweekly.
- Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Multi-day Golden Gate (weekly ATR)" (also docs/ALL-SLEEVES.md); Test catalog entry 'mk-multidaygoldengateweekly' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code status: code present in dwj9ddyvf6-hub/Test (see Files in this repo); nothing vendored.

## What this strategy is

Multi-day Golden Gate (weekly ATR): the Golden Gate level-crossing trade run on weekly periods, entry at the 0.382 weekly-ATR level, target at the 0.618 level, pivot stop. Family milkman; type breakout; universe 1,822 US stocks + 14 index ETFs and futures (the daily module's index and univ sets); asset class US equities, index ETFs and futures; timeframe 1d (weekly ATR levels). The accounting records no entry, exit or sizing rule in its consulted sources; the code in this repo below supplies the rule.

## Full algorithm

Engine: sleeves/milkman/daily.py, rule MDGG, designated cell (HIS and PLATEAU registration): "freq=W;entry_lvl=0.382;tgt_lvl=0.618;stop=pivot;ema_gate=off;po_filter=True;min_left=1".
Evaluation order (the daily module's session phases, carrying the study rules in rules.py / dstrats.py gg_trade semantics as the module header states):
1. Periods: weekly Golden Gate periods; a period's levels come from the prior period (anchor and ATR of the prior weekly period). Golden Gate periods are opened at the first look of the day.
2. Entry: the period's first touch of the entry level, anchor +/- 0.382 x ATR, in the touch direction, decides the period once (done_period: a period is decided once and entered once); entry_lvl = 0.382.
3. Filters: ema_gate = off (no EMA gate); po_filter = True (the Phase Oscillator filter of the study rule applies); min_left = 1 (at least 1 session left in the period, per the cell parameter name and the module's period handling).
4. Target: anchor +/- 0.618 x ATR (tgt_lvl = 0.618). Stop: pivot (stop=pivot, the study rule's pivot stop).
5. Execution phases: watch (open to close-16) runs the open phase then the touch phase on the session range so far (stop entries, voids, stops, targets and touch exits executed at once); close (close-15 to close-11) runs the touch phase again then the close phase on the provisional bar, market-on-close; after (after the close) runs the completed bar, with late events executing at the next open. An entry on a period's last session that does not exit on that bar is closed at that session's close (named divergence 7 in the module header).
The underlying per-bar Golden Gate decision function itself lives in the study rules the module imports (rules.py, vendored in the same milkman package in this repo); its parameters are exactly the cell above. Any deeper rule detail not carried in the cell or the module header is not in the record.

## Files in this repo

- This package: `docs/MK_MULTIDAYGOLDENGATEWEEKLY-RECREATE.md`
- Signal engine (intraday): `sleeves/milkman/intraday.py` (Panel, detect21(), SETUPS, LV levels)
- Signal engine (daily): `sleeves/milkman/daily.py` (HIS cells, feed_bars(), feed_quotes())
- Live SPY-options expression of the same ladder: `sleeves/saty_day.py` (CONFIG, F_TRIGGER/F_GATE/F_MID/F_TARGET/F_RUNNER/F_FULL, Phase Oscillator and Pivot Ribbon gates, QQQ confluence)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog entries in `docs/CATALOG.json`
- Search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries; code found: sleeves/milkman/intraday.py, sleeves/milkman/daily.py and sleeves/saty_day.py in this repo); dwj9ddyvf6-hub/Silicon (21,337 entries; only Milkman research/teardown notes, no sleeve code); dwj9ddyvf6-hub/quant-research-backup (47,379 entries; no milkman sleeve module); dwj9ddyvf6-hub/Midna (7,855 entries; milkman-study research/backtests only, no live sleeve code). Code was already in Test, so nothing was vendored.

## Configuration

- Sleeve id mk_multidaygoldengateweekly (alias mk_multidaygoldengateweekly); Test catalog status: live.
- Cell: freq=W, entry_lvl=0.382, tgt_lvl=0.618, stop=pivot, ema_gate=off, po_filter=True, min_left=1.
- Sizing (daily module header): the study has none (per trade, equal weight, every signal taken); the desk rendering is a fixed $10,000 per trade on a $1,000,000 virtual book (NOTIONAL = 10,000.0, CAPITAL = 1,000,000.0); each lane keeps its own trade ledger and the sleeve trades the net per symbol.

## Data inputs

- Daily bars: index set from Yahoo daily OHLC (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD + ES=F, NQ=F, RTY=F, YM=F); univ set from split-adjusted daily bars for the store_v1 survivors (1,822 names, >= 260 bars since 2016-01-01, liquidity-gated by the study's liq_gate).
- Quotes per session phase (Yahoo full quotes for the index set; the desk equity source for the univ set).

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place `sleeves/milkman/daily.py` at that path with its milkman package siblings (rules, vendored) from the same directory in this repo.
3. Register sleeve mk_multidaygoldengateweekly with the MDGG cell exactly as in Configuration.
4. Run the desk cycle through its watch, close and after phases; the first weekly gate touch of a period emits the entry per the algorithm.
5. First evaluation: fixture a weekly period with known prior-period anchor and ATR where a session first touches anchor + 0.382 x ATR with at least 1 session left; confirm one entry, target anchor + 0.618 x ATR, pivot stop, and no second entry in the same period.

## Verification

- Fixture above: exactly one entry per period (done_period), at the 0.382 level, target 0.618 level.
- Fixture where the period's first touch occurs on its last session: no entry (min_left = 1), per the cell.
- A position open at a period's last session without an exit on that bar is closed at that session's close.
- Sizing on every trade is the fixed $10,000 notional rendering; the sleeve trades the net per symbol across its lanes.
