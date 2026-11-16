# C6 — price the squeeze tail

**Evidence:** proposed study and payoff derivation. **Reference:** `band_liability`, `expected_band_liability`, `call_spread_pnl`. This is a standalone expression comparison for bearish candidates, whereas C2 includes an existing stock position.

## Forecast target and economic mechanism

A bearish mean or an avoid flag does not price a call spread. The relevant target is the conditional liability of a specific upside band. Potential upside demand may overpay for that band, but the protective upper call and embedded financing/borrow can consume the premium. The forecast must improve on information already present in the executable price and market context.

Require a physical conditional terminal distribution or calibrated right-tail curve across the selected strikes. The expected liability is the integral of `P(ST>k | information)` from K1 to K2. Do not replace physical probabilities with raw implied probabilities. A well-calibrated average forecast may still fail on the actual fill/action cohort.

## Contract and state requirements

Use the common option records in DATA_CONTRACTS. Sell the lower-strike call at an attainable bid, buy the upper-strike call at its ask, and respect actual size, multiplier, deliverables, exercise style, settlement and expiry. A share-short alternative additionally needs a real locate, borrow rate/recall treatment and margin. A put alternative uses its actual ask and exercise/carry path.

States: `BEARISH_CANDIDATE -> QUOTED_ALTERNATIVES -> FORECASTED_LIABILITIES -> RESEARCH_DECISION -> SPREAD_PENDING/HELD -> EXITED`, with partial-leg and assignment states in an execution-aware model. There is no automatic action at `BEARISH_CANDIDATE`. No-trade is a feasible comparator. Position size and required compensation are inputs from a specified portfolio objective, not defaults inferred from confidence in the signal.

## Payoff and size

For width w=K2-K1 and credit c, terminal per-share P&L is `c-min(max(ST-K1,0),w)`, less costs. For 0<c<w, maximum terminal profit is c, maximum terminal option loss is w-c, and expiry break-even is K1+c. Scale with the actual contract units. A bounded final payoff does not prove an affordable interim margin/assignment path.

At 105/115 strikes and 2.20 credit, synthetic bounds are +2.20/−7.80 and break-even 107.20. In the separate counterexample, a stock at 100 ends at 85 with probability 0.9 or 180 with probability 0.1: mean ending price 94.50, yet a 10-wide spread has liability expectation 1.00. Selling it for 0.60 loses 0.40 on average despite 90% winning outcomes. Preserve this test against a tempting win-rate or bearish-mean shortcut.

The same spread may be more or less costly to this portfolio depending on existing wealth in squeeze states. Compute required premium jointly with exposures and obligations. It is not estimated here. Report capital occupation, loss path and capacity, not only return divided by initial broker margin.

## Empirical build

Create a historical cohort of the bearish candidates with point-in-time option availability. Retain records for unavailable/unusable options so results cannot be generalized to all flagged names. Include delistings and corporate actions. Model earnings, dividends, liquidity, execution sides, early exercise and resulting positions. Evaluate spread, feasible short, put, and no-trade over aligned endpoints and capital constraints.

Fit the conditional band-liability model on development observations; record all strike, expiry, context and forecast variants. Compare with a market-price-aware baseline. Test on fresh observations with the candidate menu and principal outcome fixed. Costs and unfavorable quote coverage must remain visible.

The construction has not earned an edge if credit fails to compensate for the forecast liability, costs, uncertainty and portfolio burden. Missing chains or inadequate tail precision leave the specified claim unresolved. Prior failure of a share short does not logically establish either success or failure for this contract.
