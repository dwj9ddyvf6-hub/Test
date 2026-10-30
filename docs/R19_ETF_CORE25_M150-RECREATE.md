# R19_ETF_CORE25_M150: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "QQQ core with a momentum tilt · 150% exposure", type momentum, family etf. Aliases: `R19_ETF_CORE25_M150`, `ausar_pb84`, `ausar_r19_R19_ETF_CORE25_M150`. Algorithm grade FULL, no recorded gaps. Sources per the accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text. Merge evidence: Tier A, ausar_map row ausar_pb84 (variant "QQQ core with a momentum tilt · 150% exposure") lists r19 link R19_ETF_CORE25_M150; Tier C, the ausar_r19_ alias merges on the identical normalized form.
- The strategy runs in Test as the v3 sleeve `aster_etf_core25_m150`; the code-derived algorithm doc is `docs/ASTER_ETF_CORE25_M150-ALGORITHM.md` (derived from the sleeve code on 2026-10-29, no author spec on file).
- Deployed status per the accounting: mode=independent_local_paper, running=False; the md2 alias ausar_pb84 is recorded replaced, and the ausar_r19_ alias blocked.

## What this strategy is

A monthly R19 ETF rotation: keep 75% of the target portfolio in QQQ and tilt 25% to the basket's 126-session momentum leader, at 150% total exposure.

## Full algorithm

Selection and targets, in evaluation order (engine `desk3/aster_batch8.py`, policy CORE25; code-derived doc `docs/ASTER_ETF_CORE25_C098-ALGORITHM.md` / `..._M150-ALGORITHM.md` in this repo):

1. Timing: evaluation emits intents only inside the 09:35-09:40 America/New_York window (aware clock stamps are converted to ET; naive stamps are read as ET).
2. Monthly guard: when positions are held, no rebalance_due flag is set, and every held position was entered in the current month, no intents are emitted.
3. Leader selection: for each basket symbol with at least 127 daily bars and a positive close 127 bars back, score = the 126-session return close[-1] / close[-127] - 1. The leader is the best score; ties break alphabetically. (The accounting text records the same rule: "Ranks the configured ETF basket by its completed 126-session price return; equal scores use alphabetical ticker order.")
4. Weights (CORE25): 75% of the target portfolio in QQQ plus 25% in the selected leader; if QQQ leads, the two portions combine into QQQ.
5. Targets: whole shares, int(gross x equity x weight / price), where equity is account_value or net_value from extra when present, otherwise the slice capital (default $10,000). A target price at or below zero emits nothing. Gross is applied as coded and never silently capped in the sleeve; for gross above 1 the dispatcher buying-power check governs execution (for the 150% form the accounting adds: "The excess uses simulated borrowing.").
6. Order of operations: sells (held above target) are listed before buys. Intents are market, day; entries are buy_to_open, reductions and full exits are sell_to_close.
7. Exits: no price stop and no price target. The designed exit is the next monthly selection: a holding above its new target is reduced, and a holding with target zero is exited in full (accounting exit text agrees).

Parameters (accounting parameters block and engine spec agree): basket = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; lookback 126 sessions; core weight 0.75 QQQ / 0.25 leader; gross 1.5.

## Files in this repo

- This package: `docs/R19_ETF_CORE25_M150-RECREATE.md`
- Code-derived algorithm doc: `docs/ASTER_ETF_CORE25_M150-ALGORITHM.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_etf_core25_m150.py` (wrapper; delegates to the shared engine)
  - `adapters3/aster_etf_core25_m150.py` and `integration/aster_etf_core25_m150_adapter.py` (same wrapper)
  - `desk3/aster_batch8.py` (shared R19 ETF engine)
  - Family reference implementation also in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py` and `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`

## Configuration

Per the engine config row recorded in the code-derived doc: cadence_s 300, session rth, capital_usd 10000.0, cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false. Gross 1.5 (policy CORE25). State: held positions and their entry month / signal_month are read from the desk snapshot; no sleeve-private state file is recorded.

## Data inputs

Declared inputs: bars, positions, quotes. Producers named in the engine: bars (900s freshness), broker_readback (900s, positions), quotes (60s). Signals use completed historical ETF bars; execution uses separately labeled IEX quotes (accounting filter text).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test) so that `desk3/` and `sleeves/` sit side by side; the wrapper imports the shared engine from `desk3/` by module path.
2. No third-party package beyond the desk3 runtime is required by the wrapper or the engine (standard library only, per the engine source).
3. Standalone evaluation: build a `view` dict carrying the declared inputs (see Data inputs) and call the wrapper: `from sleeves.aster_etf_core25_m150 import evaluate; intents = evaluate(view, ctx)`. `ctx` may be None for a stateless read; the desk3 dispatcher supplies the snapshot view and context in production.
4. In the desk, the v3 dispatcher calls `evaluate` on the sleeve's cadence and routes the returned intent dicts (market, day, buy_to_open / sell_to_close) to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- Outside the 09:35-09:40 ET window, or when the monthly guard shows this month's rebalance complete, no intents are emitted.
- Given a basket where one non-QQQ symbol has the best 126-session return, targets are 75% QQQ and 25% leader at gross 1.5 of equity, in whole shares rounded down.
- When QQQ is the leader, the target is 100% QQQ at gross 1.5.
- Sells are emitted before buys; a holding whose new target is zero is exited in full at the next monthly selection.
- No intent ever carries a price stop or profit target.

