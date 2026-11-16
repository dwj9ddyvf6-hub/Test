> Export note: this report predates the later GitHub-save request. Exact originals are in `original/`; the current save scope is in README. Archival filenames in prose refer to `original/` unless linked otherwise.

# New strategy constructions from the recovered research

This follow-up is local only. No GitHub write, commit, push, branch change or remote rollback was performed. The repositories were used as source material. The earlier GitHub additions remain as previously reported; no attempt was made to alter them under the new boundary.

The central invention is to stop treating an entry, a hedge, a holding period and an option expression as one indivisible strategy. Different participants can pay at different stages. The desk can change the exposure as the source of compensation changes.

These are new constructions within this work, not claims of unprecedented financial inventions. One has now been prototyped against historical data; the others have explicit mechanisms and experiments. No prospective profitability is established.

## 1. Buy the panic; hedge the reassurance

**Construction.** Enter a cash asset position immediately after an unusually negative return relative to Bitcoin, during a negative Bitcoin shock. Initially leave the market exposure open. After two consecutive completed positive Bitcoin four-hour bars, add the original lagged-beta perpetual hedge at the next bar open. Hold the asset and any added hedge to the original 72-hour endpoint. The hedge is added once, rather than repeatedly toggled with every bar.

**Why the reversal of intuition matters.** An immediate hedge can sell away the very market rebound that pays first. The remaining opportunity may later be the asset-specific recovery. A separate hedge clock can capture the first source of return and then isolate the second. This is a proposed mechanism; the bar data do not identify forced sellers or prove their liquidation.

**What was executed locally.** Twelve hedge policies at two horizons, including opposite sequences, constant/no hedge, a fixed-time switch, and repeated switching. The inverse policies were added after inspecting the initial release-policy results; both result sets are retained. Selected events come from the preceding broad search, so none of these periods is an untouched holdout.

| Available historical partition | Events | Full hedge throughout | Add hedge after two positive BTC bars | No hedge |
|---|---:|---:|---:|---:|
| 2019–2022 partition, available perp/funding history | 44 | 2.032% | 2.169% | 3.845% |
| 2023–2024 | 59 | 1.266% | 2.362% | 2.153% |
| 2025–October 2026 | 37 | 1.888% | 3.539% | 4.442% |

These are modeled net event P&L per initial dollar of the asset leg, not account-equity returns. The model charges 10bp per one-way marked turnover on both legs, uses archived perpetual prices/funding, and takes the adverse funding ordering when a trade coincides with a funding timestamp. Exact funding marks, fills, margin and liquidation remain unmeasured.

The new policy improves the mean over the full hedge in all three partitions, but it does not dominate the unhedged or fractional-hedge alternatives. Its early-partition fifth-percentile outcome is worse than the full hedge. Paired bootstrap intervals for its incremental mean include zero. The useful discovery is a concrete phase-dependent policy to test, not a declaration that the best-looking sequence is proven.

**Next decisive experiment.** Distinguish common-market rebound from residual repair using finer quotes, liquidation/open-interest observations and a new prospective event stream. Compare with fixed fractional hedges and a frozen random transition clock. Target the exposure path and full capital usage, not just its mean return.

Evidence: `two_clocks.py`, `results.json`, `event_paths.json`, `static_fraction_comparison.json`. Six arithmetic/chronology checks pass in `test_two_clocks.py`.

## 2. Rent out the middle of the rebound while retaining large upside

**Ingredients.** The archives distinguish fear-day selection, rebound timing, overnight implementation, and insurance premiums. They also show why buying a short-dated call can consume a small underlying drift.

**Construction.** Start with a cash-funded stock recovery position. After the initial discount repairs, consider selling a call vertical against the stock: short a lower-strike call, long a higher-strike call, same expiry. Enter this second phase only when its executable credit exceeds a separately estimated conditional expected spread payout and costs. Compare with holding the stock and with selling the stock at the same decision time.

**Payoff.** Per share, with initial stock price S0, call strikes K1<K2 and net credit c, expiration P&L is:

`S_T - S0 + c - max(S_T-K1,0) + max(S_T-K2,0)`.

The stock keeps downside exposure, has a flat payoff through the middle interval, and regains unit upside slope above K2. This is not a free hedge. The construction sells a particular upside band rather than giving away all extreme upside through a plain covered call.

**Potential payer.** Distressed inventory sellers may pay the first discount; later upside buyers may pay for the call-spread exposure. The strategy changes the service it supplies as participants change.

**New experiment.** Replay the stock-only, immediate overwrite, delayed overwrite, and exit-to-cash alternatives using matched chain quotes, actual event timing and assignment/margin paths. A recovery-stage quote can still be cheap; the phase label alone does not establish overpricing. This construction has not been backtested here.

## 3. Rotate only after the original discount is repaired

**Construction.** Use a reversal engine to buy temporary damage, then transfer the same risk budget to a liquid leadership/momentum basket when the original market-adjusted price discount has substantially closed. Keep a cash alternative and the original position as comparators.

**Why this differs from adding confirmations.** The reversal and momentum engines need not agree at entry. They may be appropriate at different points in the same recovery. Holding the damaged name long after the discount closes may retain deterioration risk while surrendering the opportunity to participate in continuing leadership.

**Potential payer.** Forced sellers create the initial inventory transfer; slow reallocation into leadership can create the later demand. Both explanations require evidence.

**New experiment.** Define the repair event using only information known at the decision time. Compare complete same-capital paths through a fixed endpoint, including all transfer costs and lost opportunities. The archive's failed SPY rotation does not establish this particular transition rule, and its existence is not ignored. This design remains untested because the complete original equity panel is unavailable here.

## 4. Spend a volatility forecast on execution before buying volatility

**Construction.** When a signal forecasts unusually large movement but weak direction, use it to choose between crossing now, a passive entry, a staged entry and no order. Pair it with a separately formed directional thesis or existing inventory requirement. Evaluate the entire set of intents, including missed fills.

**Potential source of edge.** The forecast may improve the price paid for an exposure the desk already wants. That can have economic value even if the forecast cannot overcome the price of a straddle. Urgent traders pay for immediacy; a desk able to wait may provide it at a worthwhile price.

**Critical distinction.** Larger movement also makes adverse selection worse. A filled passive order is not automatically a good fill. Measure execution shortfall, later markout, missed-opportunity cost and inventory risk jointly.

**New experiment.** On future paper intents, assign matched execution alternatives before outcomes. Test whether the magnitude signal adds decision value beyond spread, own volatility and ordinary order-flow variables. This uses the dispersion result for a different objective rather than relabeling it as option alpha.

## 5. Let verified history change which prediction-market hedges are valid

**Construction.** Two touch markets with different start dates can still become nested conditional on observed history. If the higher target has not yet been hit, both monitoring windows have now started, and their future source/cutoff/threshold conventions agree, any future higher-target hit also hits the lower target.

**Payoff consequence.** Buy lower-target YES plus higher-target NO. With verified higher-target history, the admissible terminal outcomes are `(0,0), (1,0), (1,1)`, giving payouts `[1,2,1]` per pair. With unknown or incompatible past history, `(0,1)` may also be admissible and creates a zero-payout state.

**Why this is new in this pass.** The earlier exact-rule compiler conservatively excluded different monitoring clocks. This construction can recover some excluded relationships by acquiring a specific missing fact. It does not simply waive the clock difference.

**Executed calculation.** `conditional_contracts.py` enumerates supplied states and demonstrates that the past-history observation can change the modeled worst-case payoff. The example prices are explicitly hypothetical. No new executable arbitrage is asserted. Our recovered BTC four-hour history ends October31 and cannot certify the complete later history required by a current November decision.

**Potential payer.** Traders may value related contracts inconsistently when the necessary state is scattered across histories and rules. The practical opportunity exists only if executable acquisition cost, fees, funding and settlement risk leave a surplus.

## 6. Price the squeeze tail instead of shorting the whole stock

**Construction.** For a stock that the existing down/avoid engines flag, compare a defined-risk call credit spread with a share short, a put purchase, and no trade. The proposed signal is not merely a negative average stock return: it is a discrepancy between the quoted upside-band premium and the conditional probability/severity of paying that band.

**Why it may matter.** The archives show cases where bearish information and a costly or dangerous share short coexist. A call spread changes the payoff, capital path and maximum option loss. It does not remove financing economics by magic; borrow and exercise effects can already be embedded in option prices.

**Potential payer.** Upside-lottery demand may pay more for the particular band than its conditional payout warrants. The desk must establish this from quotes and a right-tail forecast. Negative average stock returns do not establish it.

**New experiment.** Estimate the entire conditional right tail, including squeezes, and compare executable spread credit with realized spread payout over the same horizon. Include event calendars, dividends, assignment, fees and width-specific liquidity. This is a preserved research construction, not an instruction to open a bearish option trade.

## Immediate research focus

The useful next work is the interaction between **entry timing, hedge timing and payoff changes**. The new local prototype makes one such interaction explicit. The wider invention set translates the source material into different economic actions rather than treating each old strategy's historical verdict as the end of the search.
