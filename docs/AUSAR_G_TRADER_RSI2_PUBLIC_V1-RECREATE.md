# ausar_g_trader_rsi2_public_v1: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "RSI2 dip rebound - 1d", type mean reversion, family public_recipe. Algorithm grade in the accounting: PARTIAL, with the single gap "sizing not recorded in any consulted source". Algorithm sources per the accounting: md2 catalog entry/exit/strategy text. Alias status: installed (md2_catalog). No Test catalog entry exists for this strategy (test_entries empty in the accounting).
- The accounting entry text names this id directly: "Entry: wilder_rsi2 <= 5 and close > sma200 and close < sma5. Exit: close > sma5 or 10_completed_holding_bars_no_initial_atr_stop."
- Hosted code in Test: this rule is rule id `trader_rsi2_public_v1` in the posted Ausar trader runtime vendored into Test under `packages/ausar/` (verified present at batch start by tree listing and file read; the rule text and every parameter below match the accounting entry exactly).

## What this strategy is

A public-recipe Connors-style RSI(2) dip rebound on a fixed 15-ETF universe: buy an extreme short-term pullback inside a long-term uptrend, exit on the first close back above the 5-day average or after 10 bars.

## Full algorithm

Evaluation order (accounting entry text, confirmed verbatim in the hosted rule catalogue `rules-v1.json` and the signal code `trader_signals.py`, rule id `trader_rsi2_public_v1`):

1. Indicators on completed daily bars: Wilder RSI(2) (seeded by the first period's actual price changes; flat convention: both zero 50, loss zero and gain positive 100, gain zero and loss positive 0), SMA200, SMA5, ATR14. Minimum 252 bars.
2. Entry signal: Wilder RSI(2) <= 5 AND close > SMA200 AND close < SMA5.
3. Ranking when several names signal: ascending RSI(2), then descending (SMA5 - close) / ATR14, then symbol ascending.
4. Entry execution: next actual exchange opening, within 300 seconds.
5. Exit: a completed close above SMA5, or after 10 completed holding bars. Signal exits execute at the next actual exchange opening. This version has no initial price stop (initial_stop_atr_multiple is null in the catalogue; risk_budget_fraction is null).
6. Caps from the catalogue: at most 10 positions; max notional fraction 0.1 of the book per position; max dollar-volume fraction 0.01 (20-day dollar volume); whole shares, fee-and-slippage-inclusive, settled cash only.
7. Universe (catalogue): SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX (15 liquid US ETFs). Frame 1d. The rules were frozen on 2026-10-09 before historical performance evaluation, with no return optimization.
8. Sizing gap: the accounting records "sizing not recorded in any consulted source" for this entry; the position caps in step 6 are the hosted catalogue's recorded limits, and no per-trade sizing formula beyond them is in the record: not in the record.

## Files in this repo

- This package: `docs/AUSAR_G_TRADER_RSI2_PUBLIC_V1-RECREATE.md`
- Running code (already in Test; nothing vendored for this package):
  - `packages/ausar/aster-execution-r15/desk/backend/trader_signals.py` (the rule definitions and signal computation; rule id `trader_rsi2_public_v1`)
  - `packages/ausar/aster-execution-r15/desk/strategies/trader_catalogue/rules-v1.json` (the frozen rule catalogue, including this rule's full parameter set)
  - `packages/ausar/aster-execution-r15/desk/backend/trader_runtime.py` and `packages/ausar/aster-execution-r15/desk/backend/trader_cli.py` (the hosting runtime and CLI)
  - `packages/ausar/aster-execution-r15/desk/docs/TRADER_SLEEVES.md` (the hosted sleeves' own doc)
  - The same set also exists under `packages/ausar/aster-desk-r13-baseline/desk/` (earlier baseline copy).
- Tests in Test: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `packages/ausar/aster-execution-r15/desk/tests/test_trader_runtime.py` (copies also under the r13-baseline tree).

## Configuration

- Universe: the 15 ETFs listed in step 7. Asset class / timeframe in the accounting: not recorded in consulted sources; the hosted catalogue records frame 1d on completed XNYS daily bars, each hosted sleeve with its own $100,000 virtual paper book (per `TRADER_SLEEVES.md`).
- Accounting-recorded data note for this entry: "posted Ausar runtime inputs".
- Status: installed (md2_catalog).

## Data inputs

Strict ordered completed daily OHLCV with consistent price/volume units (the catalogue's data contract), at least 252 bars per name, and actual exchange opening prices for executions.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Use the hosted desk under `packages/ausar/aster-execution-r15/desk/`: its `backend/trader_cli.py` is the operator entry point and `backend/trader_runtime.py` runs the installed rules; construction installs and funds nothing, installation is an explicit operator action (per `TRADER_SLEEVES.md`).
3. Install rule `trader_rsi2_public_v1` from `strategies/trader_catalogue/rules-v1.json` with the 15-ETF universe.
4. Serve completed daily bars (at least 252 per name) and opening quotes.
5. Run the runtime on the daily cadence; signals execute at the next actual exchange opening within 300 seconds.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

- Run the hosted tests: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `test_trader_runtime.py` must pass.
- A completed daily bar with Wilder RSI(2) of exactly 5, close above SMA200 and below SMA5, on at least 252 bars, produces an entry signal executed at the next exchange open; RSI(2) of 5.1, or a close at or below SMA200, produces none.
- A held position exits at the next open after the first completed close above SMA5, and in all cases after 10 completed holding bars; no price stop ever fires.
- With two simultaneous signals, the lower RSI(2) ranks first.