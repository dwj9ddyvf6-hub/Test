# C2 — sell the middle of the rebound

**Evidence:** payoff derivation and proposed study. **Reference:** `stock_with_band_sale`, `call_spread_pnl`, `expected_band_liability` in `reference.py`. **No historical option test for this construction is bundled.**

## Transfer and state

The stock entry may supply liquidity to a distressed seller; the later spread sells an upside interval to a willing buyer. Those are two proposed sources of compensation at different times. The second must justify itself at its decision time. Already-earned stock gains cannot subsidize the measured incremental return of the overlay.

States: `NO_STOCK`, `RECOVERY_STOCK_HELD`, `OVERLAY_ELIGIBLE`, `SPREAD_INTENT_PENDING`, `STOCK_PLUS_SPREAD`, `EXITED`, plus explicit partial-leg/assignment states in a future execution model. Recovery is measured from point-in-time inputs; the specific recovery rule is a proposed configuration, not an optimized parameter supplied here. An eligible state merely opens the comparison menu; it does not force an overlay.

At the overlay decision compare keep stock, reduce/exit stock, and stock plus compatible call spread. Hold alternative policies to a common evaluation endpoint and account for cash after early exits. The long stock and both calls must be measured in compatible share/deliverable units. For adjusted contracts use actual deliverables rather than assuming 100 shares.

## Quote and distribution contracts

Require contract IDs, underlying, strikes K1<K2, same expiry/settlement/exercise/currency, actual multiplier and deliverables, executable bid/ask sizes and times. The conservative spread credit per share is lower-call bid minus upper-call ask. Include exchange/broker fees, impact, exercise costs, financing, and any legging exposure. A simultaneous complex-order fill can be modeled only from a supported execution assumption, not from two independent favorable mids.

Require a physical conditional terminal distribution fitted on information available at decision, and the existing portfolio's reservation compensation or explicitly stated objective. Keep forecast ID, model version, training window, and uncertainty. The candidate decision value is credit minus expected band liability and costs; portfolio utility can differ from that standalone expectation.

## Payoff

For matched units, ignoring carry and early exercise only in the elementary derivation:

`stock P&L + spread P&L = ST - S0 + c - min(max(ST-K1,0),K2-K1)`.

Below K1, downside remains stock-like. Within the band, terminal slope is zero. Above K2, unit slope resumes but the width-minus-credit has been surrendered permanently versus stock-only. The hypothetical 90 entry, 105/115 strikes, 2.20 credit gives P&L −7.80 at 80, 17.20 throughout 105–115, and 27.20 at 125. These examples are arithmetic fixtures, not market prices.

## Implement the study

Build stock-only, immediate overlay, recovery-stage overlay, and recovery-stage stock exit arms. Predefine a small economically motivated strike/expiry family using development data; preserve every trial. Align option quotes to executable decision times and keep no-quote/no-depth rows as coverage outcomes. Do not exclude adverse expiries after seeing their returns. Model dividends, assignment and positions after each exercise before relying on a terminal bound.

Fit the liability forecast conditional on contemporaneous market prices and context. Compare the augmented forecast to a price-aware baseline with the same modeling budget. The potential payer can be bullish demand or a hedger with different needs; an assumption that buyers are irrational is unnecessary and unproven.

## Acceptance and missing choices

Arithmetic acceptance: terminal slopes, long-wing cap on option liability, incremental overlay attribution, actual multipliers, costs, and incompatible-contract rejection. Research acceptance: enough incremental net or portfolio value over the simpler alternatives at the actual quoted size. It remains inconclusive when uncertainty cannot distinguish the desired economic improvement.

Unset: stock-entry universe and rule, recovery definition, expiry menu, strike menu, forecast model, minimum surplus, position size, assignment policy, capital objective. They are deliberately null in `contracts.json`. Fill them through a documented research/mandate decision, not an arbitrary hidden default.
