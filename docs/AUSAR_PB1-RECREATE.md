# ausar_pb1: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "RSI2 dip rebound - 1d", type mean reversion, family public_recipe. Algorithm grade in the accounting: PARTIAL, with the single gap "sizing not recorded in any consulted source". Algorithm sources per the accounting: ausar_map params/variant and md2 catalog entry/exit/strategy text. Alias status: present in roster (md2_ausar_map); replaced (md2_catalog). No Test catalog entry exists for this strategy (test_entries empty in the accounting).
- Successor record (the accounting's meta, `successor_external`): `ausar_pb1` was merged into the external hosted identity `trader_rsi2_public_v1` with the reason "md2 reimplementation retired; hosted by posted Ausar trader_cli (trader_rsi2_public_v1), rules match the TSV entry/exit text". That hosted runtime is vendored into Test under `packages/ausar/` (verified present at batch start), so the code that runs this strategy's rules is in this repo.
- The accounting entry text for `ausar_pb1` is identical to the hosted rule: "Entry: wilder_rsi2 <= 5 and close > sma200 and close < sma5. Exit: close > sma5 or 10_completed_holding_bars_no_initial_atr_stop."
- Accounting-recorded data note specific to this entry: "Completed Yahoo bars, canonical v698 where applicable, actual received execution quotes."

## What this strategy is

The md2-roster form of the RSI(2) dip rebound: buy an extreme short-term pullback inside a long-term uptrend, exit on the first close back above the 5-day average or after 10 bars. Retired as a separate reimplementation and replaced by the hosted `trader_rsi2_public_v1` runtime, whose rules match this entry's recorded text exactly.

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

Difference recorded for this alias: its data note (above) names completed Yahoo bars and actual received execution quotes, where the hosted catalogue's data contract names strict ordered completed daily OHLCV. No other difference is in the record: not in the record.

## Files in this repo

- This package: `docs/AUSAR_PB1-RECREATE.md`
- Running code (already in Test; nothing vendored for this package): the hosted successor runtime that the accounting names as this entry's replacement:
  - `packages/ausar/aster-execution-r15/desk/backend/trader_signals.py` (the rule definitions and signal computation; rule id `trader_rsi2_public_v1`)
  - `packages/ausar/aster-execution-r15/desk/strategies/trader_catalogue/rules-v1.json` (the frozen rule catalogue, including this rule's full parameter set)
  - `packages/ausar/aster-execution-r15/desk/backend/trader_runtime.py` and `packages/ausar/aster-execution-r15/desk/backend/trader_cli.py` (the hosting runtime and CLI)
  - `packages/ausar/aster-execution-r15/desk/docs/TRADER_SLEEVES.md` (the hosted sleeves' own doc)
  - The same set also exists under `packages/ausar/aster-desk-r13-baseline/desk/` (earlier baseline copy).
- Tests in Test: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `packages/ausar/aster-execution-r15/desk/tests/test_trader_runtime.py` (copies also under the r13-baseline tree).

## Configuration

- Universe / timeframe in the accounting for this entry: not recorded in consulted sources; the hosted successor catalogue records the 15-ETF universe and 1d frame listed in the Full algorithm section, and this package does not claim those were the retired reimplementation's own settings beyond the successor record.
- Status: present in roster (ausar_map); replaced (md2_catalog) by the hosted successor.

## Data inputs

Per this entry's own accounting note: completed Yahoo bars (canonical v698 where applicable) and actual received execution quotes. The hosted successor's data contract is in the Full algorithm section.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. This entry's own reimplementation is retired; install its hosted successor instead: use the desk under `packages/ausar/aster-execution-r15/desk/`, whose `backend/trader_cli.py` is the operator entry point; construction installs and funds nothing, installation is an explicit operator action (per `TRADER_SLEEVES.md`).
3. Install rule `trader_rsi2_public_v1` from `strategies/trader_catalogue/rules-v1.json`.
4. Serve completed daily bars (at least 252 per name) and opening quotes.
5. Run the runtime on the daily cadence.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

- Run the hosted tests: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `test_trader_runtime.py` must pass.
- A completed daily bar with Wilder RSI(2) of exactly 5, close above SMA200 and below SMA5, on at least 252 bars, produces an entry signal executed at the next exchange open; RSI(2) of 5.1, or a close at or below SMA200, produces none.
- A held position exits at the next open after the first completed close above SMA5, and in all cases after 10 completed holding bars; no price stop ever fires.
- With two simultaneous signals, the lower RSI(2) ranks first.
- The recreation is of the hosted successor's rules; the retired reimplementation's code is not in any GitHub repo searched for this batch (Test, Silicon, quant-research-backup, Midna trees), and this package does not present reconstructed code as the original.