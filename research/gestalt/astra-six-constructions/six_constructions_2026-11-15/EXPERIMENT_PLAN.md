# Experiments to implement after recovery

The entries below are test specifications. Except for the preserved C1 replay and supplied-state/synthetic examples, their results are unknown. Do not display an unrun experiment as passed or rejected.

| ID | Primary comparison | Inputs still required | Decision-relevant outcome |
|---|---|---|---|
| C1-FRESH | Delayed hedge vs fixed/no/fractional/time/random-clock policies | Fresh event stream, execution quotes, actual funding marks, capital constraints | Net same-capital improvement or explicitly measured portfolio utility |
| C2-CHAIN | Recovery-stage band sale vs stock-only/immediate sale/stock exit | Point-in-time equity and option chains, physical payoff forecast, assignment model | Incremental option/portfolio value from overlay time |
| C3-PATH | Repair rotation vs retain/cash/fixed-time/leadership-from-start | Historical members, adjusted/executable prices, contemporaneous leaders, costs | Whole-path capital result and post-repair paired difference |
| C4-INTENT | Forecast-augmented router vs ordinary price-aware router | Intent ledger, quotes/depth/order events, fill and no-fill outcomes | Complete intent shortfall/wealth and inventory consequences |
| C5-PAIR | History-conditioned state set vs conservative unknown-history set | Actual rules, complete specified-source history, executable asks/depth | Financeable worst-case payoff across all admitted states |
| C6-TAIL | Spread vs no-trade/feasible share short/put | Actual option availability, physical tail forecasts, borrow, assignment/capital | Net liability pricing, tails, coverage and capital usage |

## Shared protocol

Create a trial ID before evaluating each new variant. Record parent ID, rationale, data/version hashes, universe definition, all parameters, available-at rules, benchmark, primary estimand, fitting periods, evaluation periods, costs, risk/capital convention, dependence unit, planned contrasts and uncertainty method. Record every result and every reason for missing/excluded observations.

The economic hurdle, false-promotion tolerance, capital-loss limit and uncertainty tolerance are unset until derived from the actual decision. Do not insert a universal t-statistic, Sharpe, win rate, count or duration threshold. A failed input/semantic check is not evidence of no edge; an inconclusive estimate is not a negative result.

Compare policies on the same opportunities and calendar, preserving cash and no-action paths. Fit transformations inside training periods. Purge overlapping outcome labels when constructing chronological tests; account for same-event cross-sectional exposure and overlapping holds in uncertainty estimates. Reused evaluation data become development data.

Random variables are controls or explicit candidate inputs. Their seeds and timing must be outcome-independent. A random clock should be specified from training/entry information, not selected afterward to match favorable observed transitions. Keep noise controls in the ledger even when they outperform economically motivated ideas in-sample.

For each candidate evaluate the simple alternative first: fixed exposure for C1, stock-only for C2, leadership-from-start for C3, a simple spread/volatility router for C4, the conservative state set for C5, and no trade for C6. A simpler policy matching a complicated policy's benefit reduces the case for the added mechanism without proving the entire research area empty.

## Integration experiment

After individual components have evidence, compare a combined policy using a common information set and action clock: entry -> market exposure decision -> hold/rotate/overlay/exit. Freeze transition logic before testing the integrated path. Include all legs, interim cash, capital constraints and rejected actions. Do not splice the most profitable realized action from each separate study into an impossible hindsight portfolio.

Software acceptance and research acceptance remain separate. Arithmetic/chronology tests prove implementation behavior. A complete replay proves recoverability of the specified experiment. Neither alone demonstrates prospective profitability or authorizes live trading.
