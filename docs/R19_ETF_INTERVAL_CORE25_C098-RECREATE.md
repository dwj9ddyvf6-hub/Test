# R19_ETF_INTERVAL_CORE25_C098: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "QQQ core with a two-source momentum tilt · 98% exposure", type momentum, family etf. Aliases: `R19_ETF_INTERVAL_CORE25_C098`, `ausar_pb91`, `ausar_r19_R19_ETF_INTERVAL_CORE25_C098`. Algorithm grade FULL, no recorded gaps. Sources per the accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text. Merge evidence: Tier A, ausar_map row ausar_pb91 (variant "QQQ core with a two-source momentum tilt · 98% exposure") lists r19 link R19_ETF_INTERVAL_CORE25_C098; Tier C, the ausar_r19_ alias merges on the identical normalized form.
- The strategy runs in Test as the v3 sleeve `aster_etf_interval_core25_c098`; the code-derived algorithm doc is `docs/ASTER_ETF_INTERVAL_CORE25_C098-ALGORITHM.md` (derived from the sleeve code on 2026-10-29, no author spec on file).
- Deployed status per the accounting: mode=independent_local_paper, running=False; the md2 alias ausar_pb91 is recorded replaced, and the ausar_r19_ alias blocked.

## What this strategy is

A monthly R19 ETF rotation: keep 75% of the target portfolio in QQQ and tilt 25% to the basket's 126-session momentum leader, at 98% total exposure.

## Full algorithm

Selection and targets, in evaluation order (engine `desk3/aster_etf_b9.py`, policy INTERVAL_CORE25; code-derived doc `docs/ASTER_ETF_INTERVAL_CORE25_C098-ALGORITHM.md` / `..._M150-ALGORITHM.md` in this repo):

1. Scores: for each basket symbol, the 126-session log return log(close[-1] / close[-127]) is computed separately from the primary bars (Alpaca daily histories) and the secondary bars (Yahoo daily histories); the two sources are compared, never joined. Eligibility requires at least 252 sessions of history and all closes in the last 252 sessions positive.
2. Eligibility agreement: the secondary eligible set must equal the primary eligible set and must include QQQ, or the sleeve refuses and emits nothing (the archive PROVIDER_ELIGIBILITY_DISAGREEMENT condition). If bars_secondary is empty, the sleeve emits nothing. Per the code-derived doc: no v3 producer produces bars_secondary yet, so INTERVAL sleeves are UNFED by design in the live registry and emit nothing until that input exists; the code does not fake-feed it.
3. Leader choice: each symbol's provider interval is [min(primary, secondary), max(primary, secondary)]. A robust leader is a symbol whose interval low is strictly above every other symbol's interval high. If exactly one robust leader exists, it is selected. Otherwise the incumbent (a position flagged incumbent/selected, else the holding with the largest held value at last close) is selected if it is still possible (its interval high is at or above the highest interval low); otherwise QQQ is selected. This matches the accounting text: "A new leader is chosen only when its lower return exceeds every competitor's higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ."
4. Weights: 75% of the target portfolio in QQQ and 25% in the selected leader; if QQQ leads, the portions combine into 100% QQQ.
5. Targets: desired shares = floor(weight x gross x NAV / price), whole shares, never capped inside the sleeve; NAV is the slice capital (capital_usd when the slice row carries it, else the cash figure). Price is the last close, falling back to the position average price for a held symbol with no bars. If any needed price is at or below zero, the sleeve emits nothing.
6. Timing guards: intents are emitted only inside the 09:35-09:40 America/New_York execution window (when a clock time is known; aware stamps convert to ET, naive stamps read as ET, date-only/midnight stamps ungated) and only when the monthly guard does not already show this month's signal completed (every held position carries signal_month equal to the latest bar month).
7. Exits: sell-then-settle. When any holding is above its desired shares, only sell intents are emitted on that evaluation (kind exit, sell_to_close, market, day); buys follow on a later evaluation. There is no price stop and no profit target; the designed exit is the next monthly selection reducing or replacing a holding (accounting exit text agrees).

Parameters (accounting parameters block and engine spec agree): basket = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; lookback 126 sessions; core weight 0.75 QQQ / 0.25 leader; gross 0.98.

## Files in this repo

- This package: `docs/R19_ETF_INTERVAL_CORE25_C098-RECREATE.md`
- Code-derived algorithm doc: `docs/ASTER_ETF_INTERVAL_CORE25_C098-ALGORITHM.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_etf_interval_core25_c098.py` (wrapper; delegates to the shared engine)
  - `adapters3/aster_etf_interval_core25_c098.py` and `integration/aster_etf_interval_core25_c098_adapter.py` (same wrapper)
  - `desk3/aster_etf_b9.py` (shared R19 ETF engine)
  - Family reference implementation also in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py` and `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`

## Configuration

Per the engine config row recorded in the code-derived doc: cadence_s 300, session rth, capital_usd 10000.0, cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false. Gross 0.98 (policy INTERVAL_CORE25). State: held positions and their entry month / signal_month are read from the desk snapshot; no sleeve-private state file is recorded.

## Data inputs

Declared inputs: bars, bars_secondary, positions. Producers named in the engine: bars (900s freshness), broker_readback (900s, positions). Primary bars are Alpaca daily histories; secondary bars are Yahoo daily histories, compared without joining (accounting filter text agrees).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test) so that `desk3/` and `sleeves/` sit side by side; the wrapper imports the shared engine from `desk3/` by module path.
2. No third-party package beyond the desk3 runtime is required by the wrapper or the engine (standard library only, per the engine source).
3. Standalone evaluation: build a `view` dict carrying the declared inputs (see Data inputs) and call the wrapper: `from sleeves.aster_etf_interval_core25_c098 import evaluate; intents = evaluate(view, ctx)`. `ctx` may be None for a stateless read; the desk3 dispatcher supplies the snapshot view and context in production.
4. In the desk, the v3 dispatcher calls `evaluate` on the sleeve's cadence and routes the returned intent dicts (market, day, buy_to_open / sell_to_close) to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- Outside the 09:35-09:40 ET window, or when the monthly guard shows this month's rebalance complete, no intents are emitted.
- Given a basket where one non-QQQ symbol has the best 126-session return, targets are 75% QQQ and 25% leader at gross 0.98 of equity, in whole shares rounded down.
- When QQQ is the leader, the target is 100% QQQ at gross 0.98.
- Sells are emitted before buys; a holding whose new target is zero is exited in full at the next monthly selection.
- No intent ever carries a price stop or profit target.
- With bars_secondary empty or its eligible set differing from the primary set, no intents are emitted.
- When return intervals overlap and no robust leader exists, the incumbent is retained if still possible; otherwise QQQ is selected.
