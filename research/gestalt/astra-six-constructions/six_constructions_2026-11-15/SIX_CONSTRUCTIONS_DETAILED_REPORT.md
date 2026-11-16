> Export note: this report predates the later GitHub-save request. Exact originals are in `original/`; the current save scope is in README. Archival filenames in prose refer to `original/` unless linked otherwise.

**Six strategy constructions: economic mechanisms, trade designs, evidence, and experiments.** Report prepared November 15, 2026. This report is local; the repositories are read-only sources for this work. It expands the six constructions already presented. It introduces no live orders, production changes, or GitHub changes.

The common idea is to separate decisions that a conventional strategy often bundles together: which asset to buy, when to hold market exposure, when to transfer capital, which part of a payoff to sell, and how to execute. Different participants can pay for different services at different stages. A useful signal can also become valuable when applied to a different decision.

These are proposed combinations within this research, not claims of priority over the financial literature. Positive expected profit, excess return over a feasible benchmark, and improvement in the existing portfolio are different objectives. Each construction needs to identify which one it can deliver.

Throughout this report, **historical result** means an output of the local model, **archived finding** means a statement in the recovered research that was read but not independently reproduced for this report, **derivation** means a mathematical implication of stated assumptions, and **hypothesis** means a proposed mechanism or strategy. Numerical illustrations are explicitly hypothetical.

| Construction | Economic question | Present evidence |
|---|---|---|
| 1. Buy panic; hedge reassurance | Can market recovery and asset-specific recovery be held at different times? | Exploratory historical prototype |
| 2. Sell the middle of a rebound | Will someone pay enough for an upside interval that the stockholder can surrender? | Payoff derivation and proposed experiment |
| 3. Repair, then rotate | Does the best use of capital change after a measured dislocation closes? | Proposed strategy; related archived findings |
| 4. Use volatility information for execution | Can a movement forecast improve the price paid for an independently desired position? | Proposed execution experiment |
| 5. Use history to establish contract relationships | Can verified past observations eliminate a losing settlement state? | Conditional state-enumeration prototype |
| 6. Price the squeeze tail | Is the premium for a specific upside band rich relative to its conditional payout? | Payoff derivation and proposed experiment |

**1. Buy panic; hedge reassurance.** This construction separates the asset entry from the market hedge. Buy an unusually damaged asset immediately after the qualifying shock. Initially retain its market exposure. If recovery appears, add the original beta-sized market hedge and keep it through the fixed endpoint.

**Economic mechanism — hypothesis.** A distressed sale can produce two recoveries: a common-market rebound and a repair of the asset's additional discount. An immediate market hedge can surrender the first recovery while waiting for the second. Delaying the hedge could retain the first component and later reduce exposure to a market reversal. The potential payer at entry is a seller who values immediate liquidity or must reduce inventory. The hedge itself is purchased risk transfer; its cost must be justified separately.

The strongest rival explanation is ordinary long exposure during rebounds. A higher mean than a fully hedged position does not establish market-timing alpha. The critical comparison includes no hedge, a fixed fractional hedge, and delayed hedges with simpler clocks.

**What the prototype actually does — historical specification.** It uses six spot assets—ETH, DOGE, LINK, XRP, ADA, and SOL—with BTC as the market reference and a BTC perpetual as the hedge. The source panel includes seven current surviving symbols; it is not a historical all-assets universe.

- The inherited event family identifies a negative market-residual shock on four-hour bars. Beta uses the preceding 180 bars. The residual score subtracts its lagged 180-bar mean and divides by lagged root-mean-square residual, not by conventional standard deviation. The selected score is below −3.
- The source family requires an absolute BTC move of at least 1.5 times its lagged 180-bar root-mean-square return. The local experiment then retains events with a negative BTC bar.
- The asset entry is modeled at the next bar open. The highlighted policy adds its hedge at the next open after two consecutive completed positive BTC bars following entry. It adds the hedge once; if the trigger never occurs, the position remains unhedged.
- The hedge's BTC units are fixed using the original entry price and the lagged beta. It is not continuously rebalanced to maintain perfect neutrality.
- The asset exits at a fixed 24- or 72-hour endpoint. The hedge exits there too. The 24-hour comparison reuses the parent event list, whose per-symbol spacing was selected for 72-hour holding periods.

The values 180 bars, −3, 1.5, two positive bars, and the two holding periods are research choices. Some were inherited from the earlier search. They are not established optima or universal economic boundaries. The parent event list was selected before the additional negative-BTC filter; an independently rebuilt live stream would need to reproduce that event-selection convention or be evaluated as a new policy.

For initial asset notional N, a positive initial beta β, market price B0 at entry, hedge activation price Bτ, and terminal market price BT, the simplified contribution is:

`P&L / N = asset return − β × (BT − Bτ) / B0 + funding / N − costs / N`.

The hedge term is zero when no hedge is activated. This expression makes the trade-off explicit: a short hedge helps when the market falls after activation and costs money when it keeps rising. Actual residual risk depends on changing beta, basis, and the asset's own path.

**Completed historical result.** The table shows modeled mean net event P&L as a percentage of initial asset-leg notional. It is not an account-equity return, portfolio CAGR, or return on margin.

| Available partition | Events / entry dates | Immediate full beta hedge | Delayed hedge after two positive bars | No hedge | Fixed half hedge |
|---|---:|---:|---:|---:|---:|
| 2020–2022, within the original 2019–2022 partition | 44 / 29 | 2.032% | 2.169% | 3.845% | 2.938% |
| 2023–2024 | 59 / 26 | 1.266% | 2.362% | 2.153% | 1.710% |
| 2025–October 2026 | 37 / 26 | 1.888% | 3.539% | 4.442% | 3.165% |

The table is for 72 hours. The retained events run from January 16, 2020, to October 13, 2026; the underlying archive extends through October. The half-hedge results follow from linear scaling of the fixed hedge under this model's linear fees and funding.

At 24 hours, the delayed-hedge means are 3.587%, 1.922%, and 2.595%. Immediate-hedge means are 3.169%, 0.735%, and 0.977%; unhedged means are 4.901%, 1.609%, and 2.555%. These are the same three partitions and event counts, not an independent replication.

The model charges 10 basis points per one-way turnover at marked execution notional on both legs. It uses archived perpetual prices and funding. At a funding timestamp coinciding with a position change, it takes the less favorable cash flow under the before/after position alternatives. Trade-bar opens proxy funding marks. Actual spread, impact, latency, collateral requirements, and liquidation are not established by these assumptions.

**What the result supports.** Separating entry timing from hedge timing is an implementable research direction. It improved mean P&L over the immediate hedge in these comparisons. It did not consistently beat the unhedged or half-hedged positions.

The paired approximate 95% bootstrap intervals for the 72-hour incremental mean over the immediate hedge are −2.545 to +1.958 percentage points, −0.100 to +2.592 points, and −1.232 to +2.569 points. All include zero. The delayed hedge's fifth-percentile event outcomes are −8.31%, −5.82%, and −4.92%, compared with −6.13%, −5.69%, and −4.00% for the immediate hedge. It is not a demonstrated tail-risk improvement.

Twelve policies at two horizons were explored. Four inverse policies, including the highlighted delayed hedge, were added after viewing the first results. Events were inherited from an earlier broad search. The bootstrap uses seven-calendar-day blocks and 500 draws; it does not correct the complete adaptive search. No partition here remains an untouched holdout.

**Next experiment.** Freeze the current rule and compare it with no hedge, a prespecified fractional hedge, a fixed-time delayed hedge, and a random activation clock specified before future outcomes. Add actual executable quotes, collateral use, and liquidation/open-interest observations where available. Evaluate whether the timing adds net value at comparable exposure and whether the forced-flow explanation predicts differences beyond price and volatility alone. A simple benchmark matching its outcome would weaken the case for the extra timing rule; wide uncertainty would leave the question unresolved.

Sources: [prototype](original/two_clocks.py), [results](original/results.json), [event paths](original/event_paths.json), [fractional comparison](original/static_fraction_comparison.json), and [parent event definition](inputs/parent_events.json).

**2. Sell the middle of the rebound while retaining large upside.** Start with a stock recovery position. After the initial recovery, consider selling a call spread: sell a lower-strike call and buy a higher-strike call with the same expiry and compatible contract terms. Keep the stock.

**Economic mechanism — hypothesis.** The first trade supplies capital to a distressed seller. The later option trade supplies an upside interval to someone willing to pay for it. Those buyers could be expressing bullish views, managing exposure, or seeking a particular payoff. Their identities and willingness to overpay are hypotheses requiring evidence from prices and trading activity.

The construction becomes interesting if the stock still deserves to be held, but the quoted premium for a middle band of future gains exceeds that band's value to this portfolio. It can preserve exposure to a very large upside surprise while surrendering a narrower interval. The option structure is conventional; the proposed research contribution is the recovery-dependent timing and the forecast of which payoff band is sufficiently expensive to sell.

**Trade mechanics.** At a decision time τ after recovery, compare three feasible actions: keep the stock unchanged, sell the stock, or keep it and sell the call spread. Let K1 < K2 be the strikes and c the executable credit per share before additional costs. A conservative acquisition estimate uses the bid for the sold call and the ask for the purchased call; a midpoint credit is not an observed fill.

For a stock bought at S0 and held to expiry T, ignoring dividends, interest, exercise complications, and trading costs for this illustration:

`P&L = ST − S0 + c − max(ST − K1, 0) + max(ST − K2, 0)`.

The terminal payoff has stock-like slope below K1, zero slope between K1 and K2, and stock-like slope again above K2. The stock's downside remains. Above K2, the position remains behind stock-only by the spread width minus the credit. Regaining upside slope does not recover the upside already sold.

**Hypothetical example, not market quotes.** Buy stock at $90. After it reaches $100, sell a $105/$115 call spread for $2.20 per share. The following are total P&L from the original stock entry, before the omitted costs:

| Stock at expiry | Stock only | Stock plus short call spread | Increment over stock |
|---:|---:|---:|---:|
| $80 | −$10.00 | −$7.80 | +$2.20 |
| $105 | +$15.00 | +$17.20 | +$2.20 |
| $110 | +$20.00 | +$17.20 | −$2.80 |
| $115 | +$25.00 | +$17.20 | −$7.80 |
| $125 | +$35.00 | +$27.20 | −$7.80 |

At the second decision, the earlier stock gain is already common to all alternatives. It cannot be counted as evidence that the option overlay adds value.

**Break-even economics.** Define the spread liability `L = min(max(ST − K1, 0), K2 − K1)`. The incremental expected option payoff is `c − E[L | information at τ] − costs`, with financing handled on a common clock. A portfolio may require more or less compensation than the standalone expectation suggests because the liability is correlated with existing wealth. A stockholder already benefits in the states where the call spread pays out; that can change its reservation price, but does not make the overlay automatically attractive.

**Failure modes.** The rebound can continue through the sold band; the credit can be too small; purchasing the far call can consume the entire apparent premium; and stock downside can dwarf the credit. Earnings, dividends, early assignment, stale quotes, and partial fills can change the cash and exposure path. The terminal equation assumes the specified position is maintained or its equivalent payoff is replicated; American exercise needs an explicit path model.

**Evidence and experiment.** This design has not been historically tested here. The recovered research records failures of several option expressions, including results sensitive to model-implied volatility. Those observations motivate using actual chains; they do not establish this overlay's outcome. Compare stock-only, immediate overlay, recovery-stage overlay, and exit-to-cash over identical endpoints and capital conventions. Select the recovery definition and strike/expiry family using development data, then evaluate untouched observations. The claim is weakened if the quoted premium fails to cover the independently forecast liability and costs, or if simply holding or reducing the stock offers a better portfolio outcome.

Source context: [archived option-expression and volatility findings, AD-59, AD-69, AD-74 and AD-75](sources/equity_evidence_archive.md). These are archived claims, not newly reproduced results.

**3. Repair, then rotate.** Use a reversal strategy to buy temporary damage. When the measured dislocation closes, consider transferring the same capital or risk allocation into a liquid leadership basket. Compare that transfer with holding the original asset, moving to cash, or holding the leadership basket from the beginning.

**Economic mechanism — hypothesis.** The first phase can be paid by urgent sellers. The later phase may be supported by slower reallocations into persistent leaders. The asset best suited to a short recovery need not be the asset best suited to the next stage. Reversal and momentum can be sequential policies without having to agree as simultaneous entry filters.

This is a hypothesis about changing relative opportunity. A repaired price is not proof of improving fundamentals, and leadership can also become crowded. The strongest rival is that the rotation merely adds market exposure or selects a fortunate switching time.

**A concrete research specification.** Let d be the magnitude of a negative market-adjusted shock observed before entry. Fix the benchmark and beta using information available then. Track cumulative market-adjusted recovery x since entry, and define a repair fraction `ρ = x / d`. The reference event `ρ ≥ 1` means the measured initial shock has been recovered. This is an interpretable candidate, not a proven optimal exit or an estimate of fundamental fair value.

For an equity study, x could use cumulative log returns of the stock minus its fixed pre-entry beta times benchmark log returns. That definition would be a new specification; it should not silently replace the simple-return conventions in the crypto prototype. Corporate actions, publication timing, and benchmark membership need point-in-time treatment.

At repair, form the leadership basket using only information available at that decision. Fix its selection and trading rules before evaluation. Do not use the later winners to define leadership. Transfer the existing allocation rather than counting two independently funded profitable trades as one strategy. Keep the original research endpoint so both policies receive the same opportunity to earn returns.

**Payoff comparison — derivation.** Let Vτ be the value of the original position when repair is observed, RA its subsequent return to the common endpoint, RB the leadership basket's return, and K the incremental transfer/implementation cost in the same terminal units. The additional terminal wealth from rotating is:

`ΔW = Vτ × (RB − RA) − K`.

Cash is another B with its attainable cash return. Existing gains before τ cancel in the comparison. The economic question is whether information available at repair predicts sufficient relative performance afterward.

**Hypothetical example.** A position has recovered from $100 to $108. Over the remaining evaluation period, suppose the original asset earns 1%, the leadership basket earns 4%, and the transfer incurs $0.40 of additional terminal-equivalent costs. The proposed rotation adds `$108 × (4% − 1%) − $0.40 = $2.84`. These assumed returns illustrate the accounting; they are not forecasts. A reversal in leadership can make the same decision lose.

**Evidence boundary.** The archive reports that a fear-day stock-selection strategy could look better at the trade level while failing to outperform as a capital-constrained portfolio. It also reports that a particular SPY core/fear-day rotation did not beat SPY. Those findings make capital occupation and benchmark exposure essential. They do not validate the new repair-triggered transfer, which has not been tested here.

**Next experiment.** Build the complete same-capital path for four policies: retain the original asset, move to cash at repair, move to the predefined leadership basket at repair, and own that basket from the original entry. Add a fixed-time switch to test whether the repair observation contributes information. Use historical constituents and delisted names; include both sides of the transfer, basket turnover, concentration, and concurrent positions. The construction needs incremental post-repair relative value after costs or a demonstrated portfolio improvement. If a simple basket held throughout explains the gain, the proposed switching mechanism has not earned its complexity.

Source context: [AD-63 and AD-66](sources/equity_evidence_archive.md). Their reported tests were not rerun for this report.

**4. Spend the volatility forecast on execution.** Use a forecast of movement to decide how to acquire or dispose of an independently justified position. The available actions can include crossing the spread now, resting a limit order, staging the order, waiting, or abstaining when the investment mandate permits it.

**Economic mechanism — hypothesis.** A model can predict unusually large movement and still fail to identify a profitable option purchase because the option price already charges for that movement. The same forecast might improve urgency, limit distance, order duration, or the choice to wait. It can preserve an existing directional edge through better implementation.

The source of value may be avoided spread and impact, reduced adverse selection, or appropriately supplied immediacy. Potential counterparties are traders whose deadlines or inventory needs differ from ours. A willingness to wait is useful only when its expected reward exceeds missed opportunity and inventory risk.

**Decision specification.** Begin with an investment intent generated independently of the routing experiment: instrument, side, quantity, deadline, and reason for wanting exposure. At that time, record the bid/ask, available depth, volatility forecast, directional forecast if any, and recent order flow. Compare feasible order policies using information then available. High forecast volatility must not automatically mean 'post a limit': it can also mean that waiting is particularly expensive.

The central model needs both fill probability and value conditional on filling. A passive order can fill precisely because informed sellers know the price is likely to fall further. An attractive average limit price on filled orders can coexist with a poor policy over all intents.

**Accounting — derivation.** For a buy intent of Q shares, decision benchmark P0, fills qj at prices Pj, and deadline reference PT, a useful implementation-shortfall measure is:

`IS = Σ qj × (Pj − P0) + (Q − Σ qj) × (PT − P0) + fees`.

The second term charges missed participation relative to the intended exposure. If the mandate requires completion at the deadline, replace the reference with attainable completion prices and their costs. For a discretionary intent, compare the resulting portfolio outcomes explicitly; 'no order' cannot be declared best just because it paid no spread. The sign convention reverses for a sale.

**Hypothetical example.** A 100-share buy intent has a $100.00 decision price. Crossing at $100.02 costs $2.00 before fees. A passive policy fills 60 shares at $99.98 and leaves 40 unfilled. If the deadline reference is $101.00, its shortfall is `60 × (−$0.02) + 40 × $1.00 = $38.80`. The partial fills look cheap, but the whole intent was implemented poorly. A different subsequent path could favor the passive policy.

**What the forecast must add.** Compare a price-aware routing baseline using spread, depth, ordinary volatility, time of day, and the original thesis with an otherwise comparable router that also receives the proposed movement signal. Predicting high volatility already known from these inputs may add no decision value. The relevant metric is net outcome across all original intents, including no fills and partial fills, together with inventory and downside consequences.

**Evidence and experiment.** The archive's AD-69 reports movement forecasts whose long-straddle expressions failed; this is motivation for another use, not evidence that execution will improve. No execution experiment for this construction has been run here. Collect timestamped quotes, depth, order events, and subsequent prices. Begin with replay and paper shadow policies, recognizing that simulated fills are not observed counterfactual executions. A later authorized randomized routing experiment would be stronger evidence and would need its assignment probabilities logged. This report authorizes no such orders.

The claim weakens if its apparent benefit disappears when missed fills, fill-conditioned markouts, realistic queue position, and latency are included. It also weakens if an ordinary spread/volatility router performs equally well. Improvement in execution is economically useful even when it is not a new directional forecast.

Source context: [AD-69](sources/equity_evidence_archive.md).

**5. Use verified history to establish prediction-market hedges.** Treat historical observations as inputs to the set of possible settlement states. Two contracts whose monitoring windows originally differed can sometimes acquire a useful logical relationship after their past histories are resolved.

**Economic mechanism — hypothesis.** Related markets can require different rule documents, timestamps, and price histories to compare correctly. Acquiring and combining those facts can reveal a payoff relationship overlooked in headline comparisons. The potential advantage is contract interpretation and verified information. It exists economically only if executable prices leave compensation after costs, collateral, and settlement uncertainty.

**Contract model.** Consider two contracts paying $1 for YES on touching an upper target before expiry. The lower threshold is KL and the higher threshold KH, with KL < KH. Their past starting dates may differ. For the simplified model, both monitoring windows have already started, their remaining observation window and end time agree, they use the same source and inclusive threshold convention, and their binary payment terms are compatible.

Let L and H be their terminal YES indicators. The proposed position buys lower-target YES and higher-target NO. Its terminal payout is `L + (1 − H) = 1 + L − H`.

| Lower target L | Higher target H | Pair payout | Admissible when higher target is verified not to have hit previously? |
|---:|---:|---:|---|
| 0 | 0 | $1 | Yes |
| 1 | 0 | $2 | Yes |
| 1 | 1 | $1 | Yes |
| 0 | 1 | $0 | No, under the shared-future rules |

Why the zero-payout state disappears: a future observation at or above KH is also at or above KL. If the higher contract has not already become true during its distinct past window, it cannot later settle YES while the lower settles NO under these assumptions. Separately, a verified irreversible lower-target hit would also establish a payout floor, because L would already equal one. The past facts matter; merely assuming a missing state away would manufacture a guarantee.

For example, suppose the higher-target contract began in January and the lower-target contract began in February. A January high could make H = 1 even if the lower target never hits after its own start. Without the historical record, the adverse state must remain possible.

**Completed local calculation.** The supplied-state prototype explicitly enumerates these alternatives. With hypothetical asks of $0.40 for lower-target YES and $0.55 for higher-target NO, acquisition costs $0.95. Unknown histories permit a minimum terminal payout of zero, so the modeled worst P&L is −$0.95. Supplying a verified 'higher target has not previously hit' fact removes that adverse state and gives a minimum payout of $1, or +$0.05 before omitted costs.

Those are supplied example prices, not captured executable quotes. The calculation validates an implication of the assumptions. It does not verify any actual market's history or establish a live arbitrage. The recovered price history ends October 31 and cannot establish a complete history through a November 15 decision.

**Full economics.** The financed value of the minimum payout must exceed both executable asks, fees, acquisition impact, capital cost, and any settlement-related deductions. Different payment dates require a common cash-flow clock. A positive-cost funded pair with a conditional terminal floor is not automatically a feasible self-financing arbitrage. Every leg, its available quantity, its payment path, and financing must be established.

**Next experiment.** Extract the exact rule fields for a specific contract pair: source, observation convention, start and end times, time zone, threshold inclusivity, void rules, revisions, and payment timing. Verify the entire necessary history from the stipulated source, including boundary intervals and gaps. Compile all admissible states and independently check the logical implication. Only then read both executable sides and depth to compute the complete price bound. If history remains uncertain, retain the adverse state and value the pair accordingly. The useful extension is that data acquisition can change the feasible hedge set itself.

Sources: [conditional compiler](original/conditional_contracts.py) and [supplied-state results](original/conditional_payoff_examples.json).

**6. Price the squeeze tail instead of shorting the whole stock.** Use bearish information to forecast the payout of a specific call spread, then compare that payout with its executable credit. This is a separate application of the option liability in construction 2, here evaluated without assuming an existing stock position.

**Economic mechanism — hypothesis.** A stock can have an unfavorable expected return and still be dangerous or expensive to short because of borrow, recalls, and occasional extreme rallies. A bounded call spread changes the terminal liability. Possible upside-lottery demand might make a particular band expensive. That must be observed in the quotes: an expensive protective wing can consume the apparent opportunity.

The new forecast target is the entire payout of the chosen band. A negative average stock return, an 'avoid' label, or a high probability of finishing below a strike is insufficient. The spread's price may already fully incorporate the bearish evidence, and financing or borrow economics can appear inside option prices.

**Trade mechanics and derivation.** Sell a call at K1 and buy a same-expiry call at K2 > K1. Let w = K2 − K1 and c be the net executable credit before additional costs. Under the specified terminal payoff model:

`P&L = c − min(max(ST − K1, 0), w)`.

For 0 < c < w, maximum terminal option profit is c, maximum terminal option loss is w − c, and the expiry break-even stock price is K1 + c. These are per-share values before costs. Contract multipliers and adjusted deliverables must be applied correctly.

For the hypothetical $105/$115 spread at a $2.20 credit, the maximum terminal gain is $2.20, maximum terminal loss $7.80, and break-even $107.20. This bound assumes the matched option payoff is maintained. American assignment, exercise decisions, short-stock exposure after assignment, margin calls, and broker liquidation require a separate interim-path analysis.

The conditional expected liability has a useful representation:

`E[L | I] = integral from K1 to K2 of P(ST > k | I) dk`.

Therefore, the needed object is the physical conditional right-tail curve over the entire strike interval. Option-implied prices are useful market information, but cannot simply be treated as physical probabilities to claim a forecasting advantage.

**Why bearishness alone is insufficient — hypothetical counterexample.** Start with a $100 stock. Suppose it ends at $85 with probability 90% and $180 with probability 10%. Its expected ending price is $94.50, a negative expected stock return. Yet the $105/$115 call spread has expected liability `$10 × 10% = $1.00`. Selling it for $0.60 loses $0.40 in expectation before costs despite winning 90% of the time. A correct bearish mean forecast can coexist with an unattractive call-spread sale.

**What would create the edge.** The executable credit must exceed the independently estimated liability and implementation costs by enough to compensate this portfolio for uncertainty and adverse-state capital use. Estimate that requirement jointly with other positions. A spread liability that hurts during an existing short book's squeeze is materially different from the same liability beside a long-stock book. A high percentage return on a broker's margin requirement is not a substitute for this calculation.

**Evidence and experiment.** The archive reports bearish/avoid signals that did not support profitable short books after costs and extreme upside moves. That motivates investigating another payoff; it does not validate call spreads. This construction has not been tested here.

Build a point-in-time sample of flagged names with actually listed, usable options. Retain the missing-option cohort when describing coverage so the results are not generalized to untradeable names. Obtain bid/ask depth, expiries, adjusted deliverables, earnings and dividend dates, and assignment assumptions. Compare the spread with no trade, a feasible share short including borrow and recall, and a put purchase at its ask. Forecast band payouts on development data, then test actual executable net payoffs and capital paths on new data. If the spread credit fails to cover its tail liability and costs, the bearish signal has not created this particular trade.

Source context: [AD-60 through AD-62](sources/equity_evidence_archive.md) and [AD-68](sources/equity_evidence_archive.md).

**How the six constructions fit together.** They are six research directions, not six independent return streams. The useful connection is a sequence of economic questions: what creates the entry opportunity, what exposure remains worth holding, what payoff someone else will buy, and how to implement the decision at an attainable price.

| Decision stage | Relevant construction | Economic comparison |
|---|---|---|
| Acquire a position | 1, with execution research from 4 | Immediate dislocation purchase versus feasible delayed/hedged alternatives |
| Change market exposure | 1 | Delayed hedge versus fixed exposure with comparable capital constraints |
| Reallocate after repair | 3 | Original asset versus leadership basket or cash from the same decision time |
| Alter a stockholder's payoff | 2 | Credit received versus surrendered upside interval and portfolio utility |
| Express a bearish distribution | 6 | Call-spread credit versus forecast band liability, other expressions, and no trade |
| Resolve contractual relationships | 5 | Full feasible settlement states versus executable acquisition and financing costs |

Constructions 2 and 6 use the same option liability with different existing holdings. Their expected premiums cannot be counted as separate sources of diversification. Constructions 1 and 3 can both retain substantial market and recovery exposure. Construction 4 is an implementation layer that needs intent-level evaluation. Construction 5 is a distinct contract-semantics problem, with its own settlement and execution risks.

A possible combined policy would enter a recovery, later adjust its hedge, and then choose among holding, rotating, selling an upside band, or exiting. That combined policy has not been tested. Its alternatives must be chosen using information available at each decision, and its entire capital path must be evaluated. Adding together the best outcomes from separate historical experiments would not reproduce an executable policy.

For any option sale, a portfolio-specific reservation price can be expressed as the smallest premium π for which `E[U(W + π − L)] ≥ E[U(W)]`, after expressing cash flows in common units. Here W is existing state-dependent wealth, L is the proposed liability, and U represents the owner's actual objective. No utility function, risk tolerance, or allocation is estimated in this report. The expression clarifies the missing inputs rather than supplying an invented position size.

**Research handoff.** The immediate continuation with the most existing infrastructure is to preserve construction 1's current rule and compare it with simple exposure-matched alternatives on fresh observations, including realistic execution and collateral. In parallel within the research plan—not as newly launched work here—the inexpensive first discriminator for construction 5 is a complete rule/history/quote audit of one candidate pair. Constructions 2 and 6 share the need for executable option chains and conditional band-payout forecasts; construction 3 needs a complete equity portfolio replay; construction 4 needs quote and order-event data.

The report is complete as an account of the six constructions. Its historical figures were read from the stored prototype outputs, and its numerical examples were checked arithmetically. No new historical backtest, live execution experiment, or external market-data refresh was performed to write it. Profitability remains unverified.
