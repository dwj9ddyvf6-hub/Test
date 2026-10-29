Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_etf_interval1_m150

## What it is
A monthly Aster R19 ETF rotation sleeve (batch 9). The local core at sleeves/aster_etf_interval1_m150.py is a thin wrapper: it sets SLEEVE_ID to "aster_etf_interval1_m150", takes INPUTS from inputs_for(SLEEVE_ID), and delegates evaluate(view, ctx) to desk3/aster_etf_b9.evaluate. That shared engine is already saved in this repo at desk3/aster_etf_b9.py, and the same wrapper is saved as the integration adapter at integration/aster_etf_interval1_m150_adapter.py (byte-identical to the local adapters3 file).

## What it trades
One or more symbols from the 14-symbol ETF universe (see Common engine), selected monthly by the policy below. This sleeve's policy is INTERVAL1, gross target 1.5, source_id R19_ETF_INTERVAL1_M150.

## Indicators and parameters
- Policy: INTERVAL1
- Gross target: 1.5 (so a gross of 1.5 targets USD 15,000 of exposure on the USD 10,000 slice; the dispatcher's buying-power check, not the sleeve, governs execution)
- Source id: R19_ETF_INTERVAL1_M150

## Entry rules
Selection (INTERVAL policies in desk3/aster_etf_b9.py):
- Primary scores come from the primary bars (ALPACA daily histories) and secondary scores from bars_secondary (YAHOO daily histories).
- The secondary eligible set must equal the primary eligible set and must include QQQ, or the sleeve refuses and emits nothing (the archive PROVIDER_ELIGIBILITY_DISAGREEMENT condition). If bars_secondary is empty, the sleeve emits nothing. Note: no v3 producer produces bars_secondary yet, so INTERVAL sleeves are UNFED by design in the live registry and emit nothing until that input exists. The code does not fake-feed it.
- For each symbol the provider interval is [min(primary score, secondary score), max(primary score, secondary score)]. A robust leader is a symbol whose interval low is strictly above every other symbol's interval high. If there is exactly one robust leader, it is selected. Otherwise the incumbent is selected if it is still possible (its interval high is at or above the highest interval low); otherwise QQQ is selected.

- Weights: see the sizing note for this policy below.
- Intents are emitted only inside the execution window and only when the monthly guard does not already show this month's signal completed.

## Exit and rebalance rules
Sell-then-settle, as in the Common engine. There is no intraday, price-based, stop, or target exit.

## Sizing
NAV basis for this sleeve (ENH-NAVBASE, in ENH_NAVBASE_IDS): NAV is the slice capital (capital_usd when the slice row carries it, else the cash figure, which in v3 is the capital proxy). Held value is part of that budget and is never added on top. Desired shares = floor(weight x gross x NAV / price). Weights: 100% to the selected symbol, except INTERVAL_CORE25, which is stated separately for that sleeve.

## Session, cadence, and data inputs
- Data inputs declared by the wrapper: bars, bars_secondary, positions. Primary bars are daily histories keyed as "<symbol>|1Day", "<symbol>|1D", or the bare symbol.
Common engine (desk3/aster_etf_b9.py, batch 9):
- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- Score: 126-session log return, log(close[-1] / close[-127]). Eligibility requires at least 252 sessions of history and all closes in the last 252 sessions positive. Ties break alphabetically.
- Execution window: 09:35-09:40 America/New_York, when a clock time is known. Aware timestamps are converted to ET, naive timestamps are read as ET, and a date-only or midnight stamp is ungated.
- Monthly guard: if every held position carries signal_month equal to the latest bar month, no rebalance is emitted.
- Incumbent: a position flagged incumbent/selected, otherwise the holding with the largest held value at last close.
- Sizing: desired shares = floor(weight x gross x NAV / price), whole shares, never capped inside the sleeve. Price is the last close, falling back to the position average price for a held symbol with no bars. If any needed price is at or below zero, the sleeve emits nothing.
- Exits: sell-then-settle. When any holding is above its desired shares, only sell intents are emitted on that evaluation (kind exit, sell_to_close, market, day). Buys follow on a later evaluation. There is no price stop and no price target; the designed exit is the next monthly selection reducing or replacing a holding.
- Session and cadence (config row): cadence 300 s, session rth, slice capital USD 10,000 and cash USD 10,000, bp_buffer_frac 0.02, flat_by_close false, parked false.

## Ambiguities
- The wrapper itself implements no strategy logic; every rule above is read from the shared engine desk3/aster_etf_b9.py and from this sleeve's config row and engine SPECS row. Where the engine and the config row disagree on inputs, both are stated above.
