# Build instructions for a new LLM or engineer

## Objective

Reconstruct the six research constructions without guessing missing settings, silently promoting exploratory findings, or depending on the previous agent's machine. The owner wants inventive strategy development and complete preservation of the usable work. This package supplies auditable derivations, specifications, examples, and evidence. It is not a broker-connected trading system.

There are two different completion targets. **Reproduction** means recovering the existing research outputs from the bundled source and raw inputs. **New empirical development** means implementing the specified untested policies against appropriate new data. A successful reproduction is evidence of recoverability, not an untouched confirmation of alpha.

## First commands

Run the standard-library example and tests in README. Read `contracts.json`, which separates frozen measured parameters, proposed research definitions, and unset deployment requirements. A null setting is a missing input, not an invitation to supply a convenient constant. The synthetic examples supply all their own numerical assumptions and are marked as such.

For C1, restore data, install the pinned scientific dependencies, run the portable replay, and compare complete outputs. Do this before changing any signal or parameter. Preserve `original/` byte-for-byte. Give each subsequent hypothesis a new ID and output directory.

## Architecture to build next

Use ordinary Python modules with explicit input records and pure policy functions. The reference kernels already implement the payoff mathematics. Keep the following responsibilities separate:

| Layer | Required responsibility | Required output |
|---|---|---|
| Source adapters | Read timestamped bars, quotes, rules, historical facts, corporate actions | Immutable records with source IDs, availability clocks, units, raw hashes |
| Feature builder | Compute only from information available at a decision; retain version and fitting window | Point-in-time feature rows; missingness reason |
| Forecast provider | Estimate the particular return, fill, or liability distribution needed by the construction | Forecast ID, fitting window, target, uncertainty, supported action cohort |
| Candidate builder | Produce feasible same-clock action alternatives | Candidate ID, legs, quantity, horizon, comparator, assumptions |
| Portfolio evaluator | Compare complete cash paths, collateral and existing exposure | Net payoff, opportunity cost, risk, feasibility, counterfactual scope |
| Research recorder | Keep every intent and alternative, including abstentions and failed variants | Decision/event table, trial ledger, artifact hashes |
| Execution adapter | Future separately authorized work | Order intent and reconciliation, never implicit inside a research function |

Do not call an LLM in the numerical payoff path. An LLM can extract rules and propose hypotheses; the extracted rules and model outputs still require verification. No API credential is necessary for this package.

## Common event record

Use stable `opportunity_id`, `instrument_id`, `construction_id`, `policy_version`, `source_event_id`, `decision_epoch`, `information_cutoff_epoch`, `feature_available_epoch`, `quote_epoch`, `forecast_id`, `input_hash`, `action`, `reason`, `quantity`, `unit`, `terminal_epoch`, `cost_components`, `net_payoff`, and `evidence_stage`. UTC epochs are seconds. A quote's event time and receipt time may differ; record both when available. Missing outcomes are explicit, never zero P&L by default.

For candidate comparisons, persist the full feasible menu and its constraints at the same decision time. Include the incumbent action, cash/hold where feasible, and applicable deadlines. A portfolio comparison must use the same capital and horizon. A shorter holding period does not earn the return of a longer strategy without accounting for what capital does afterward.

## C1 implementation route

The complete executable research route exists in `run_historical.py`. It changes paths from the frozen prototype and leaves calculations intact. The source feature engine and loader dependencies are under `vendor/`. Both replay outputs must match the originals. `reference.delayed_hedge_fractions` is the minimal independent standard-library timing kernel for the highlighted two-positive-bar policy, not a replacement for the full event selector.

After reproducing, implement a chronological event-stream adapter for prospective data. Specify whether it preserves the parent selection's 72-hour spacing before negative-BTC filtering or defines a new stream. Include all eligible assets historically, handle delistings and unavailable funding explicitly, and distinguish incomplete source data from zero funding. Evaluate fixed/no/fractional hedges and full margin-capital usage before integration. Do not replace the original prototype's funding-boundary convention without creating a new version.

## C2/C6 shared implementation route

Build one option contract and quote layer reused by both constructions. Require immutable contract ID, underlying ID, strike, expiry, option type, exercise style, settlement method, currency, multiplier, deliverable, bid/ask sizes, quote time, and adjustments. Pair only economically compatible calls. A default multiplier of 100 is not safe for adjusted contracts.

Implement executable credit as the sale proceeds at the lower-call bid less purchase cost at the upper-call ask, with contract multipliers and all costs. Implement physical conditional liability forecasts separately. A quoted/implied option probability is not a physical-probability estimate supplied by fiat. The policy must compare the actual credit with a portfolio-specific required compensation; the latter is an explicit input until estimated under an approved objective.

C2 includes an existing stock position and an overlay decision after recovery. C6 starts from a bearish candidate and compares standalone expressions. They share the spread liability but have different endowments and comparators. Never count them as independent diversification merely because they have different names. See their specifications for missing historical data and acceptance experiments.

## C3 implementation route

Implement a point-in-time stock/benchmark panel with corporate actions and delistings. Record the original shock definition and estimate beta before entry. Track repair without fitting to the eventual exit. At the repair decision, construct the leadership basket using then-available membership and information. Compare retain/rotate/cash/leadership-from-start/fixed-time-switch over one common endpoint and capital path.

The reference's repair fraction of one is a proposed interpretable definition, not a validated threshold. The actual leadership rule, maximum horizon, basket weighting, and capital limits are unset. Estimate or choose them in an explicitly recorded development experiment. Do not copy the archived failed SPY-rotation verdict onto this new strategy; also do not ignore that benchmark failure.

## C4 implementation route

Create an intent ledger independent of routing decisions. An intent includes side, desired quantity, decision benchmark, deadline, completion requirement, and underlying thesis. Add full quote/order-event data. Implement all partial/no-fill branches, queue assumptions, cancellation latency, and markouts. A router that improves only the filled subset has not demonstrated intent-level improvement.

Start with a simple spread/depth/ordinary-volatility baseline, then add the proposed forecast with the same fitting budget and action menu. Paper and historical fill simulations remain models. Later randomized real routing, if separately authorized, needs logged action probabilities and a supported action set; no such execution is enabled here.

## C5 implementation route

Represent exact rule fields, compile the complete admissible state set, and store the evidence supporting each history fact. `reference.conditional_pair` deliberately supports only a simple upper-touch binary model. Unsupported void/revision states require model expansion; they cannot be discarded. The original compiler is also retained unchanged.

A caller-supplied `verified=True` flag is a provenance boundary, not an automatic verification of the world's history. Implement that upstream proof: complete source coverage, correct thresholds, timestamps, revisions, and actual rule documents. Then collect executable asks/depth and financeable cash flows. Preserve `(lower NO, higher YES)` whenever it remains feasible. Every rule or history change must trigger recomputation from the full state set.

## Build acceptance versus strategy acceptance

Software acceptance: deterministic supplied-input outcomes; chronological inputs; all economic units explicit; invalid contracts and incomplete history cannot manufacture a floor; comparisons include unfilled intents; original replay reproduced; every output traced to its inputs and version.

Research acceptance: an independently chosen test protocol evaluates the stated estimand against a feasible benchmark, with realistic costs and dependence. Economic hurdle, uncertainty tolerance, risk budget, and monitoring policy are derived from the actual decision. They are not hardcoded to universal Sharpe, win-rate, trade-count, or t-statistic cutoffs.

Deployment acceptance: not performed or authorized by this handoff. It additionally requires validated data feeds, account identity, available capital, reconciled positions and orders, assignment/collateral paths, and a separately approved execution policy.

## Copyable task for the next LLM

> Work from this package. Read README, the detailed report, contracts.json, DATA_CONTRACTS.md, and the relevant construction specification. First run the synthetic checks and reproduce the frozen C1 results. Preserve all original artifacts. Then implement one named construction's missing research adapter against identified data, using the specified inputs, units, state transitions, comparators, and failure cases. Keep proposed parameters distinct from measured values. Record every changed hypothesis and every evaluated variant. Return the source changes, exact commands, all experiment outputs, and a precise evidence statement. No live orders or production configuration changes are part of this task.
