# TRADER_RSI2 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "TRADER_RSI2", type mean reversion, algorithm grade PARTIAL with gaps: ["entry/signal rule not recorded in any consulted source", "exit rule not recorded in any consulted source", "sizing not recorded in any consulted source"], and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Alias status: ausar_deployed, "mode=original_independent_local_paper running=False". Classification evidence on the accounting entry: "Classification 2026-10-30: mean reversion (code evidence): muse-desk-v3 desk3/aster_batch1.py read: RSI2 pullback rule, entry when RSI(2) is at or below 5 while close is above SMA200, the frozen trader_rsi2_public_v1 dip rebound"
- The rule this deployed id names is the frozen public rule `trader_rsi2_public_v1`, whose full record is already in Test: the sibling recreation package `docs/AUSAR_G_TRADER_RSI2_PUBLIC_V1-RECREATE.md` (the catalog form of the same rule) documents it from the hosted rule catalogue and signal code, and `desk3/aster_batch1.py` ports it as sleeve `aster_rsi2_1d` (its header: backend/trader_signals.py frozen rule trader_rsi2_public_v1, indicator math ported function-for-function). Every parameter below is taken from those in-repo records, read for this package.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `desk3/aster_batch1.py` and the AUSAR_G package above; no file is named for the uppercase deployed id itself, the code lives under the rule id and the aster sleeve id); dwj9ddyvf6-hub/Silicon (recursive tree; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree; no path named for this id).

## What this strategy is

A public-recipe Connors-style RSI(2) dip rebound on a fixed 15-ETF universe: buy an extreme short-term pullback inside a long-term uptrend, exit on the first close back above the 5-day average or after 10 bars. The accounting records no strategy description for this deployed id itself: "No strategy description recorded in consulted sources."

## Full algorithm

Evaluation order (from `desk3/aster_batch1.py` `_trader_features` / `_eval_trader`, kind rsi2, confirmed against the hosted catalogue record in the sibling package):

1. Indicators on completed daily bars: Wilder RSI(2), SMA200, SMA5, ATR14 (RMA), DV20. Features require at least 252 bars; the desk port drops bars dated the current session from the feature set (completed-bar rule).
2. Entry signal: RSI(2) <= 5.0 AND close > SMA200 AND close < SMA5.
3. Ranking when several names signal: ascending RSI(2), then descending (SMA5 - close) / ATR14, then symbol ascending.
4. Entry execution in the hosted runtime: next actual exchange opening, within 300 seconds. In the desk port the sleeve runs on a 300-second cadence in regular trading hours and emits the entry intent at its pass.
5. Exit (first that fires): a completed close above SMA5, or 10 completed holding bars. No initial price stop (stop_distance is None for rsi2 in the code; the hosted catalogue records initial_stop_atr_multiple null).
6. Sizing (code): cap = min(0.10 x equity, 0.01 x DV20, cash); shares = floor(cap / close); at most 10 positions held. RSI2 has no risk-cap divisor because it has no stop.
7. Universe (code UNIVERSE15): SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX.
8. Accounting gaps for this deployed id (entry/exit/sizing "not recorded in any consulted source" in the accounting itself) are filled above only from the in-repo code and catalogue records named in Provenance; anything beyond them is not in the record.

## Files in this repo

- This package: `docs/TRADER_RSI2-RECREATE.md`
- Code (already in Test; nothing vendored): `desk3/aster_batch1.py` (sleeve `aster_rsi2_1d`, `_trader_features`, `_eval_trader`, `_rsi`); hosted rule code `packages/ausar/aster-execution-r15/desk/backend/trader_signals.py` (rule id `trader_rsi2_public_v1`), catalogue `packages/ausar/aster-execution-r15/desk/strategies/trader_catalogue/rules-v1.json`, runtime `packages/ausar/aster-execution-r15/desk/backend/trader_runtime.py` and `trader_cli.py`, doc `packages/ausar/aster-execution-r15/desk/docs/TRADER_SLEEVES.md` (the same set also exists under `packages/ausar/aster-desk-r13-baseline/desk/`).
- Sibling package: `docs/AUSAR_G_TRADER_RSI2_PUBLIC_V1-RECREATE.md`.
- Tests in Test: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `test_trader_runtime.py`.
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

- Universe: the 15 ETFs in step 7. Timeframe 1d, completed XNYS daily bars (hosted catalogue). Sleeve spec in the desk port: kind rsi2, cadence_s 300, session rth.
- Hosted book: each hosted sleeve with its own $100,000 virtual paper book (per TRADER_SLEEVES.md, as recorded in the sibling package).
- Deployed status for this id (accounting): mode=original_independent_local_paper, running=False.
- Any further configuration for the deployed form: not in the record.

## Data inputs

- Strict ordered completed daily OHLCV with consistent price/volume units, at least 252 bars per name, and actual exchange opening prices for executions (the hosted catalogue's data contract, per the sibling package).
- Accounting data note for this entry: posted Ausar runtime inputs.

## Install and run

1. Clone this repository (Test) and check out the main branch.
2. Read the sibling package `docs/AUSAR_G_TRADER_RSI2_PUBLIC_V1-RECREATE.md` for the hosted-runtime record.
3. Desk port path: open `desk3/aster_batch1.py`, locate the `aster_rsi2_1d` spec and the rsi2 branch of `_trader_features` / `_eval_trader`, and provide completed daily bars (at least 252 per symbol), equity, cash and positions in the snapshot shape that module documents; run every 300 seconds in regular trading hours.
4. Hosted path: use `packages/ausar/aster-execution-r15/desk/`, install rule `trader_rsi2_public_v1` from the catalogue with the 15-ETF universe, and run `backend/trader_runtime.py` via `backend/trader_cli.py` on the daily cadence.
5. Verify against the Verification section before treating any recreation as faithful.

## Verification

- Run the hosted tests: `packages/ausar/aster-execution-r15/desk/tests/test_trader_signals.py` and `test_trader_runtime.py` must pass.
- A completed daily bar with Wilder RSI(2) of exactly 5, close above SMA200 and below SMA5, on at least 252 bars, produces an entry signal; RSI(2) of 5.1, or a close at or below SMA200, produces none.
- A held position exits after the first completed close above SMA5, and in all cases after 10 completed holding bars; no price stop ever fires.
- Shares never exceed floor(min(0.10 x equity, 0.01 x DV20, cash) / close), and holdings never exceed 10 positions.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.

