# QQQ core with a momentum tilt (R19_ETF_CORE25_M150): recreation package

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): type momentum, family etf, algorithm grade FULL, unresolved false. Test strategy card: strategies/ausar/r19-etf.md. Sources recorded in the accounting: ausar_map params/variant, femto land-wt config params, md2 catalog entry/exit/strategy text.

## What this strategy is

A monthly R19 ETF momentum rotation book: it holds a 75 percent QQQ core plus a 25 percent tilt to the strongest of a 14-fund ETF basket by 126-session return, at 150 percent exposure.

## Full algorithm

Evaluation order, from the accounting entry text, the Test card (strategies/ausar/r19-etf.md), and the code-derived docs/ASTER_ETF_CORE25_M150-ALGORITHM.md:

1. Evaluation emits intents only inside the 09:35-09:40 America/New_York window on the monthly rebalance (engine: desk3/aster_batch8.py). Monthly guard: when positions are held, no rebalance_due flag is set, and every held position was entered in the current month, no intents are emitted.
2. Leader selection: rank the 14-fund basket by completed 126-session price return (code: close[-1] / close[-127] minus 1, requiring at least 127 daily bars and a positive close 127 bars back; the card records the score as log(close / close 126 sessions earlier) on total-return closes with 252 sessions of history required for eligibility in the source book). Ties break alphabetically.
3. CORE25 weights: 75 percent QQQ plus 25 percent selected leader; if QQQ leads, the two portions combine into QQQ.
4. Targets: whole shares, int(gross x equity x weight / price), with gross 1.5. Equity is account_value or net_value when present, otherwise the $10,000 slice capital. A target price at or below zero emits nothing.
5. Order of execution: sells (held above target) are listed before buys. Market, day intents; entries are buy_to_open, reductions and full exits are sell_to_close.
6. Exit: no price stop and no price target. The designed exit is the next monthly selection: a holding above its new target is reduced, and a holding with target zero is exited in full.
7. Costs recorded on the card for the source book: buys wait for settled cash and the displayed ask size; 15 bps per side; margin rows (gross 1.5) carry a 10 percent per year debit in the source book. The code-derived doc records that gross above 1 is never silently capped in the sleeve; the dispatcher buying-power check governs execution.

## Files in this repo

- This doc: docs/R19_ETF_CORE25_M150-RECREATE.md
- Strategy card in Test: strategies/ausar/r19-etf.md
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'QQQ core with a momentum tilt'
- Code-derived algorithm doc in Test: docs/ASTER_ETF_CORE25_M150-ALGORITHM.md
- Code in Test: sleeves/aster_etf_core25_m150.py (wrapper, sleeve id aster_etf_core25_m150) delegating to the shared engine desk3/aster_batch8.py (ETF_SPECS policy CORE25, gross 1.5); the same wrapper also appears at adapters3/aster_etf_core25_m150.py and integration/aster_etf_core25_m150_adapter.py
- Family code in Test: packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py and packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py
- No code was vendored for this package; all code above was already in Test.

## Configuration

- Basket (accounting parameters and engine): QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- Policy: CORE25. Gross: 1.5 (150 percent). Weights: QQQ 0.75, leader 0.25.
- Score window: 126 sessions. Rebalance: monthly, 09:35-09:40 America/New_York window; the card records trading on the month's first session on the prior month's last close, retrying for up to 5 sessions in the source book.
- Slice capital in the v3 config rows: $10,000, cadence 300 seconds, session rth, cash $10,000, buying-power buffer fraction 0.02, not flat by close (code-derived doc, CORE25 rows). For the INTERVAL engine, cadence and slice follow the same v3 sleeve form; the engine header records the $10,000 slice for M150 targets.
- State: current holdings and their entry month or signal month, held in the runtime positions view.

## Data inputs

- Completed historical ETF bars for signals (Alpaca; Yahoo as the second source for INTERVAL rows) and separately labeled IEX quotes for execution (accounting filter text and card). Engine declared inputs: bars, positions, quotes.

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
2. The leader is the basket fund with the best completed 126-session return, ties alphabetical.
3. Targets equal 75 percent QQQ and 25 percent leader at gross 1.5, floored to whole shares; when QQQ is the leader the target is 100 percent QQQ at that gross.
4. Sells are emitted before buys; a holding with target zero is exited in full at the next monthly selection.
5. No stop or profit-target intent is ever emitted by this sleeve.
