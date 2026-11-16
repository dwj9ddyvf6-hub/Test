# STEP 5: RECONCILIATION WITH RUN 2 (coordinator, 2026-11-15)

Sources compared: the package's implementation specifications (specs/C2_REBOUND_BAND_SALE.md, specs/C3_REPAIR_ROTATION.md, specs/C4_FORECAST_TO_EXECUTION.md, specs/C5_HISTORY_CONDITIONED_HEDGE.md, specs/C6_SQUEEZE_TAIL_PRICING.md, plus contracts.json) against Run 2's pre-registered runfiles in ~/workspace/research_notes/six-constructions-20261115/ (C2C6-RUNFILE.md, C3-RUNFILE.md, C4-RUNFILE.md, C5-RUNFILE.md). Every difference below is recorded as a PROPOSED amendment with its effect. Nothing in any runfile is silently replaced; each amendment takes effect only when the owning cell adopts it in a dated addendum under its own trial rules.

## C2 and C6 (one cell in Run 2, one liability object)

Agreements:
1. Identical liability object: L = min(max(ST - K1, 0), K2 - K1) per share, same expiry, standard deliverable.
2. Identical executable credit convention: bid of the sold lower call minus ask of the bought upper call. The package calls it the conservative spread credit; the runfile bars mid prices from the credit. Same rule.
3. Identical identification rule: the physical conditional right-tail curve defines the estimand through E[L | I] as the integral of P(ST above k | I) over the strike interval, and option-implied probabilities are never used as physical probabilities. The package states it as "do not replace physical probabilities with raw implied probabilities"; the runfile carries it as a hard rule. Same rule.
4. Same comparator sets. C2: stock only, immediate overlay, recovery-stage overlay, exit to cash. C6: no trade, feasible share short with borrow, put purchased at the ask.
5. Same handling duties: assignment and early exercise modeled rather than excluded, adjusted deliverables never priced as standard, no-quote and no-depth rows retained as coverage outcomes.
6. Same counting discipline in substance: the package treats C6 as a standalone expression comparison distinct from C2's holdings context, and Run 2 charges C2/C6 as one cell whose premiums are never counted as two independent streams or as diversification.

Proposed amendments:
A1. Adopt the package's unset-parameter list as the checklist for the runfile's development lock addendum. The package deliberately leaves the recovery definition, strike and expiry family, forecast model, minimum surplus, and position size null in contracts.json, to be filled by a documented research decision. The runfile already requires a dated lock addendum before the first read (due before Tue 2026-11-17). Effect: the addendum must close each package-named parameter item by item, so no parameter is filled by a hidden default. No change to the registered claim.
A2. Record a portfolio reservation-compensation quantity as a secondary reported read. The package's C2 decision value allows portfolio utility to differ from the standalone credit minus liability minus costs; the runfile's primary test is the standalone claim. Effect: when the cell is ever run against a held book, the reservation price is reported alongside the primary test. The primary test does not change.
A3. Carry displayed quote size as a named coverage limitation. The package requires executable bid and ask sizes and a supported complex-order execution assumption; the estate chain panel supplies bid and ask but not decision-time displayed size for single names. Effect: the first read (Tue 2026-11-17, coverage and executability only) reports size as unmeasured rather than assuming the credit is attainable at size.
A4. Add interim loss-path reporting to the C6 context. The package warns that a bounded terminal payoff does not prove an affordable interim margin or assignment path and requires capital occupation, loss path, and capacity reporting. The runfile reports per share, per unit, and per dollar of capital committed. Effect: the C6 context gains a margin and assignment path row; terminal accounting is unchanged.

## C3 (repair, then rotate)

Agreements:
1. Same five arms on the same capital: retain the original asset, cash at repair, leadership basket at repair, leadership basket from entry, fixed-time switch.
2. Same repair definition family: repair fraction rho = x / d on cumulative market-adjusted log returns with beta fixed before entry; rho reaching 1 is an interpretable candidate transition, not a claim of fair value.
3. Same falsifier: if leadership-from-start or a fixed-time switch explains the gain, the repair observation has not earned its complexity.
4. Same accounting: pre-repair gains are embedded in capital V at transfer and are common to every comparator; the increment is V times the post-repair return difference minus transfer cost (package fixture: V 108, 4 percent versus 1 percent, cost 0.40, increment 2.84; the runfile's registered formula is the same object).

Proposed amendments:
A5. Record the parameter mapping, no change. The package leaves the beta window, entry and horizon definitions, and leadership lookback and weighting unset; the runfile freezes one concrete instance (252-session beta window, 5-session shock window, damage at least 0.10 log points, price and dollar-volume floors, entry at the S+1 close, 126-session common endpoint, basket from bars alive at the decision date). Effect: the runfile stands as one registered instance of the package's design family; any package-level variant is a new trial under the runfile's ledger, never a silent edit.
A6. Keep the membership limitation named at package strength. The package requires historical universe membership and delistings as inputs; the estate holds no point-in-time membership table and only partial delisting coverage (Run 2 inventory: bars for 2,240 of 18,419 inactive names). Effect: unchanged from the runfile, which already carries this limitation into every later verdict; if a membership table is ever sourced, the replay must be re-registered before use.
A7. State the rotation timing convention explicitly in the replay report. The package's state machine schedules the comparison at the next feasible execution time after a qualifying observation; the runfile works in a close-to-close log-return frame with the repair observed at a session close. Effect: a one-line convention statement when the deferred replay is built, so its timing is never conflated with an intraday execution claim.

## C4 (volatility forecast spent on execution)

Agreements:
1. Identical accounting identity, including the unfilled term charging missed participation at the deadline reference, the mirrored sell form, and attainable completion prices under a completion mandate.
2. Identical grading population: all original intents, never filled-trade averages alone.
3. Identical router comparison: a price-aware baseline (spread, depth, time of day, ordinary volatility, the original thesis) against the same router augmented with the movement forecast, at matched budget and action menu.
4. Identical cautions: a fill is not evidence of a good price; fill probability and value conditional on fill are both required; simulated fills are labeled simulations; a randomized routing study is a future, separately authorized experiment with logged assignment probabilities.

Proposed amendments:
A8. Adopt the package's order-state vocabulary for the prospective capture build. The package specifies explicit states (intent recorded, route decided, pending or resting or partially filled, completed or expired or canceled), unresolved acknowledgments kept explicit, a pending cancel never treated as a completed cancel, and multiple pending orders consuming one exposure budget. The runfile's capture schema covers intent-time fields and strata but not this state machine. Effect: the capture schema gains the package's state list when the prospective intent-time capture (Run 2's named open row for this cell) is built.
A9. Add terminal-wealth reporting for discretionary intents as a secondary read. The package requires it so a no-order outcome cannot win by default; the runfile's unfilled term already charges missed participation against the deadline reference. Effect: both quantities reported for discretionary intents; the primary identity is unchanged.
A10. Record the estate constraint as the binding difference of circumstance, not of design. The package assumes an order-level ledger with quote event and receipt clocks; the runfile's verified inventory shows this estate holds fills without contemporaneous quotes (67,612 dispatcher lines across five generations, 8,930 ledger fills, quote cache empty, no depth archive, no forecast-to-intent join). Effect: none on the design; the study remains prospective-only on this estate, exactly as Run 2 registered it.

## C5 (verified history for prediction-market hedges)

Agreements:
1. Same four-state table and the same elimination standard: the (0,1) state is retained unless verified history from the stipulated settlement source removes it.
2. Same build sequence, which Run 2's audit in fact executed on a live pair: rules first, history second, state enumeration third, executable prices last.
3. Same economics: financed value of the floor against the full cost stack on one cash-flow clock; a conditional floor is not automatically a feasible arbitrage. Run 2's verdict on the Kalshi CPI pair (floor real at 1.00, financed 0.9936, acquisition 1.0690, net minus 0.0959 per pair, NO SURPLUS, PRICES CONSISTENT) is the verdict shape the package's accounting predicts when the market has already done the elimination work.
4. Same evidence boundary: the package states its price archives end October 31 and cannot prove a November 15 history; Run 2's audit took its history from the stipulated source (BLS) directly, which is the package's own required standard.

Proposed amendments:
A11. Extend the cell's registered elimination standard with the package's second floor route and its exception states. The package establishes a floor also when a verified irreversible lower YES already holds, and requires a richer model where void, cancellation, or revision states exist. Effect: both are added to the C5 standard before any second pair audit; the first audit's verdict is unaffected, since neither route applied to its pair.
A12. Record the implementation gap as an open row. The audited original conditional_contracts.py implements the supplied-state enumeration only; the package's reference.py carries the fuller machinery (TouchRule, HistoryFact, conditional_pair) with a complete-coverage requirement before a verified fact is accepted. That fuller machinery reproduces its synthetic cases (Step 3) but has not been run against a real pair on this estate. Effect: open row, owner the C5 cell, due when a second pair audit is registered.

## C1 cell status update (supersedes the status lines of C1-RUNFILE.md sections 1 and 8; the registered text itself is untouched)

1. Route 1 (audit Astra's own artifacts): UNBLOCKED by this landing on Sun 2026-11-15, and now CLOSED with the Step 4 verdict REPRODUCED (see STEP3-4-AUDIT.md and the consolidated report). The claimed table is an audited artifact: his code on his archived inputs produces his numbers.
2. Route 2 (reconstruction from the specification on estate data): RETIRED AS MOOT under the rule registered for this audit, because the audit reproduced. The estate data rows named in the runfile (C1-DATA-01 to C1-DATA-05: BTC spot 4h bars, BTC perpetual bars, BTC perpetual funding) remain OPEN, but their role changes: they no longer gate an audit; they gate only the fresh-data protocol's forward sample, per asset, exactly as the runfile's section 3.10 provides.
3. Standing of the claimed result: UNCHANGED. Exploratory, adaptive (12 policies, 4 inverse policies added after viewing the first results), every incremental bootstrap interval includes zero, fifth-percentile outcomes worse than the immediate hedge, no untouched holdout. The audit grades the artifact's fidelity, not the strategy. The fresh-data protocol in C1-RUNFILE.md remains the forward test, frozen as registered.

STATUS: GREEN for this reconciliation. Evidence pointers: the package specs and contracts.json in the mirror; the four Run 2 runfiles; STEP3-4-AUDIT.md for every number cited.
