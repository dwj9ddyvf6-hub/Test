# QQQ core with a two-source momentum tilt (R19_ETF_INTERVAL_CORE25_M150): recreation package

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): type momentum, family etf, algorithm grade FULL, unresolved false. Test strategy card: strategies/ausar/r19-etf.md. Sources recorded in the accounting: ausar_map params/variant, femto land-wt config params, md2 catalog entry/exit/strategy text.

## What this strategy is

A monthly R19 ETF momentum rotation book: it holds a 75 percent QQQ core plus a 25 percent tilt to the strongest of a 14-fund ETF basket by 126-session return, at 150 percent exposure. Selection uses two independent price sources (Alpaca and Yahoo) and only switches leader on a strict interval win.

## Full algorithm

Evaluation order, from the accounting entry text, the Test card (strategies/ausar/r19-etf.md), and the engine header of desk3/aster_etf_b9.py:

1. Evaluation emits intents only inside the 09:35-09:40 America/New_York window on the monthly rebalance. Monthly frequency in the engine: positions whose signal_month equals the latest bar month are this month's completed signal; no rebalance.
2. Two-source scoring: calculate each ETF's completed 126-session return separately from Alpaca and from Yahoo (engine score: log(close[-1] / close[-127]); eligibility requires at least 252 sessions of history). The two values form a range (interval) per fund. The secondary eligible set must equal the primary set or the sleeve refuses.
3. Leader selection: a new leader is chosen only when its lower return exceeds every competitor's higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ.
4. CORE25 weights (policy INTERVAL_CORE25): 75 percent QQQ plus 25 percent selected leader; if QQQ leads, the two portions combine into QQQ.
5. Targets: whole shares floored from gross x NAV x weight, with gross 1.5. NAV in the engine is slice cash plus held value at last close. Gross above 1 is never capped in the sleeve; the dispatcher buying-power check governs execution.
6. Sell-then-settle: when any holding is above target, only sell intents are emitted in that evaluation; buys follow on a later evaluation.
7. Exit: no price stop and no price target. The designed exit is the next monthly selection reducing or replacing a holding.
8. Recorded engine limitation: INTERVAL rows declare a bars_secondary input (Yahoo histories) for which no v3 producer exists yet, so the INTERVAL sleeves land visibly UNFED in the registry and are never fake-fed (desk3/aster_etf_b9.py header).

## Files in this repo

- This doc: docs/R19_ETF_INTERVAL_CORE25_M150-RECREATE.md
- Strategy card in Test: strategies/ausar/r19-etf.md
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'QQQ core with a two-source momentum tilt'
- Code in Test: sleeves/aster_etf_interval_core25_m150.py (wrapper, sleeve id aster_etf_interval_core25_m150) delegating to the shared engine desk3/aster_etf_b9.py (SPECS policy INTERVAL_CORE25, gross 1.5, source_id R19_ETF_INTERVAL_CORE25_M150)
- Family code in Test: packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py and packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py
- No code was vendored for this package; all code above was already in Test.

## Configuration

- Basket (accounting parameters and engine): QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- Policy: INTERVAL_CORE25. Gross: 1.5 (150 percent). Weights: QQQ 0.75, leader 0.25.
- Score window: 126 sessions. Rebalance: monthly, 09:35-09:40 America/New_York window; the card records trading on the month's first session on the prior month's last close, retrying for up to 5 sessions in the source book.
- Slice capital in the v3 config rows: $10,000, cadence 300 seconds, session rth, cash $10,000, buying-power buffer fraction 0.02, not flat by close (code-derived doc, CORE25 rows). For the INTERVAL engine, cadence and slice follow the same v3 sleeve form; the engine header records the $10,000 slice for M150 targets.
- State: current holdings and their entry month or signal month, held in the runtime positions view.

## Data inputs

- Completed historical ETF bars for signals (Alpaca; Yahoo as the second source for INTERVAL rows) and separately labeled IEX quotes for execution (accounting filter text and card). Engine declared inputs: bars, positions, quotes; INTERVAL rows also declare bars_secondary (Yahoo histories), which has no v3 producer yet (engine header).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Read this package and the strategy card or algorithm doc named in the Files section.
3. Install the code paths named in the Files section at the same relative paths in a desk3-compatible runtime; the sleeve wrapper imports its shared engine by the module path recorded there, so keep the repo directory layout unchanged.
4. Configure the sleeve with the exact parameters in the Configuration section; do not substitute values from a different variant.
5. Provide the data inputs named in the Data inputs section through the runtime view (bars, positions, and quotes where the engine declares them).
6. Call the sleeve module's evaluate(view, ctx) function on the cadence recorded in the Configuration section and route the returned intents through the desk dispatcher; this package does not include a standalone broker connector.
7. Run the Verification checklist before trusting any output.

## Verification

Behavior checklist (no test file for this sleeve was located in Test):
1. Outside the 09:35-09:40 ET monthly window, no intents are emitted.
2. The leader is the basket fund with the best completed 126-session return, ties alphabetical; for INTERVAL rows a challenger wins only when its lower return beats every other fund's higher return, otherwise the incumbent or QQQ is kept.
3. Targets equal 75 percent QQQ and 25 percent leader at gross 1.5, floored to whole shares; when QQQ is the leader the target is 100 percent QQQ at that gross.
4. Sells are emitted before buys; a holding with target zero is exited in full at the next monthly selection.
5. No stop or profit-target intent is ever emitted by this sleeve.
