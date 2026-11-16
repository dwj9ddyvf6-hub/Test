# Data and output contracts

All proposed application records use UTC epoch seconds and explicit economic units. Keep event, publication, receipt, decision, fill, and settlement clocks separate. Source snapshots and inputs are immutable; corrections create a new version. JSON examples are strict JSON, with nonfinite numbers rejected rather than serialized as NaN.

## Bundled historical source data

`data_archive/manifest.json` lists 799 exact files and all hashes. Source retrieval manifests inside the restored `binance/` and `perp_history/` folders preserve attempted URLs and missing months. Public Binance spot archive timestamps are milliseconds before the documented switch and microseconds in later files; the frozen loader normalizes by magnitude. Perpetual/funding timestamps in the retained loader are milliseconds. These are input-specific conventions, not a universal timestamp heuristic to apply to new vendors.

Spot columns used: bar-start time, open, high, low, close, base volume, quote volume, taker-buy base volume. Perpetual columns used: bar-start time, open, close. Funding columns: timestamp, interval hours, signed rate. Positive funding is received by the short hedge in this model. Nonexistent funding rows cannot be filled with zero.

`inputs/parent_events.json`: policy plus original event tuples `[entry_epoch, original_gross_return, symbol]`. The replay uses event clock and symbol; it computes its own asset/perpetual P&L. The parent gross-return field is not the new strategy's net return. Parent event selection has 72-hour per-symbol exclusion and forward-data availability conditions; the additional negative-BTC filter is applied afterward.

## Historical output dictionary: important legacy names

`original/event_paths.json` has one row per retained event/horizon: `t` entry epoch, `symbol`, `h` four-hour bars, `beta` lagged coefficient, `asset_gross`, and results for each policy. Each result contains `net`, hedge price P&L/funding/cost/net/trade count, and mean hedge fraction. All P&L fields are per initial dollar of asset-leg notional. Summing across overlapping names does not produce a funded portfolio return.

`original/results.json.rows` has 24 entries: 12 policies times two horizons. Each holds period summaries and paired differences versus `fixed_beta`. The shared aggregator retains historical field names:

- `mean_gross` inside `net` is actually the mean of already-net event P&L supplied to the aggregator. Label it net in presentations.
- `block_bootstrap_ci95_gross` similarly describes the supplied net quantity or paired net difference, despite the legacy suffix.
- `net_at_cost_bps` subtracts an **additional** flat event cost from that already-net series. Do not treat it as the original execution-cost model or subtract the original costs twice.
- `break_even_round_trip_bps` is the supplied mean times 10,000. It is not a solved break-even per-leg fee for a strategy with variable turnover.
- `n` is event count. `days` is the number of entry dates represented. Neither establishes independent observation count.
- `p05` is an event-return quantile. It is not portfolio drawdown, expected shortfall, or a future loss bound.
- `hac_t` and the seven-day/500-draw bootstrap are exploratory approximations and do not adjust the entire adaptive research search.

`static_fraction_comparison.json` interpolates fixed hedge contributions under the linear fee/funding model. It does not model margin or nonlinear impact.

## Proposed equity and option records

An equity observation needs immutable security ID, symbol history, timestamp, available-at time, raw and appropriately adjusted prices, adjustment factors, currency, volume, historical membership, and delisting treatment. A benchmark has its own point-in-time identity and total-return convention. Do not mix adjusted signal prices with unadjusted executable prices without an explicit mapping.

An option record needs immutable contract and underlying IDs; call/put; strike; expiry timestamp; exercise style; settlement method; multiplier; deliverable; currency; corporate-action version. A quote needs bid, ask, sizes, quote event time, receipt time, venue, and a stale/invalid reason. A contract pair must share all economically required terms, not just its printed expiry date.

An option forecast needs forecast ID, information cutoff, fitting-window bounds, target liability definition, physical scenario distribution or calibrated conditional tail, and uncertainty. A price can be an input to the model but is not automatically a physical probability. Portfolio reservation values need the current portfolio, cash-flow clock, hedge rights, and risk objective; these are not estimated in this package.

## Proposed execution records

Intent: ID, creation/available-at clock, asset, side, quantity, benchmark price, deadline, completion requirement, thesis ID, and constraints. Order: intent ID, action policy, quantity/limit, decision and send times, acknowledgment, cancel request/acknowledgment, fills with price/size/time/fee, and remaining quantity. A pending cancel does not release exposure. Keep all no-fill and rejected intents.

Markouts and deadline prices need their own measurement convention. State whether unfilled quantity represents forgone exposure or is completed later at an attainable price. `reference.implementation_shortfall` implements the stated benchmark accounting, not an order-book simulator.

## Proposed prediction-market records

Rule: market/contract ID, versioned source text and hash, source ID, observation definition, start/end timestamps, time zone, threshold and inclusivity, revision policy, void treatment, currency, payout amount, and payment timing. History: coverage interval, evidence ID/hash, source ID, completeness, revisions, truth value and who established verification. A price-history gap leaves the relevant fact unknown.

The supplied reference supports equal future end, source, upper-touch convention, currency and payout, with both windows active and no additional void/revision states. Verified history facts must be computed for exactly the contract start through the decision time: future observations or earlier off-contract observations cannot enter their truth values. It deliberately rejects unsupported semantic differences. Supporting them requires a larger state model, not relabeling them compatible.

## Required outputs for new experiments

Every run should save configuration, input hashes, data availability, trial lineage, all opportunities and candidate actions, forecasts with provenance, simulated/observed fills, costs, cash/collateral path, baseline outputs, paired differences, uncertainty, and unresolved failure reasons. Missing data, semantic incompatibility, insufficient evidence, and an economically unfavorable result are different outcomes.
