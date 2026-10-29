# Third-pass source audit and forecast-engine design

**Date:** 2026-10-29

**Code/data snapshot:** Silicon `origin/main` `aad9d2148752a6862ce7a6c44685311aa7310947`; implementation branch is separate.

**Scope:** second look for hidden dependencies and operational failure modes across Silicon REA, the referenced research branches and public repositories, the supplied Ausar sleeve concepts, Saty, TheStrat, and Edge.

## Reference census and source boundaries

The bounded text search across both REA trees found 118 Markdown files with 1,388 matches for reverse-engineering, teardown, or REA terms; including CSV and text indexes/registers, 133 text files matched. The high-count files are predominantly the corpus file index, generated family-requirement locators, review matrices, convergence synthesis, vault manifests, and work queues. I cross-walked those counts with the existing index/status audit instead of treating generated locator rows as semantically verified product requirements. The active target-report set remains 86 files with all 86 hashes matched to the pinned snapshot. The 39 vault streams remain structurally indexed; the existing audit explicitly distinguishes integrity/parse state from source-rights review and semantic adjudication.

This is the source map used for the new designs: the two Silicon trees and the 86 current target reports; the verified Femto research refs and curated research records; the public-only Saty and TheStrat rules; the seven original GitHub repositories plus Vibe-Trading and Edge; and the user's supplied 100-sleeve specifications. Snapshot counts, branch SHAs, mirror/vault status, and unresolved index contradictions are retained in [CORPUS_AUDIT.md](CORPUS_AUDIT.md) and [SECOND_PASS_AUDIT.md](SECOND_PASS_AUDIT.md).

## What changed in the third pass

The first two passes concentrated on corpus coverage, point-in-time data, and forecast targets. This pass looked for failures that can survive those controls: false consensus from repeated data, forecast horizons that are themselves stale, “more agents” mistaken for more evidence, and attractive gross forecasts that cannot survive a real holding path.

Three design changes follow:

1. **Forecast agreement must be lineage-aware.** Several agents or vendor products can transform the same source event. A headcount vote is not independent confirmation. The new collision map groups only comparable forecasts, exposes shared hashes/source IDs/declared groups, reports disagreement between potential dependency clusters, and suppresses a descriptive aggregate when the panel repeats an engine. It emits magnitude medians only when forecast and target units match; signed-score agreement remains a direction diagnostic. A shared label is a dependency warning, never proof of correlation; distinct labels are not proof of independence.
2. **Input freshness needs its own forecast clock.** A field can pass a maximum-age gate and still be likely to change before the prediction horizon. The new source-refresh estimator learns that event frequency only from matured, rights-approved historical observations, stratified by source or source family and age-to-horizon band. Thin histories return no estimate. It is a refresh diagnostic, not market alpha, and does not relax the existing timestamp gate.
3. **Every engine needs an economic payer and a falsifier.** The Edge Ledger now holds a complete pre-registered card for each FE01–FE30: mechanism, precise outcome, price-aware baseline, payer, scarcity/transfer, bad state, holdability/co-loss, executable net, decisive comparison, kill rule, and traceable sources. All are explicitly `HYPOTHESIS` until an evidence record supports promotion.

## Source-by-source design synthesis

| Source | What is useful in its design | What it changes here | What does not transfer as evidence |
|---|---|---|---|
| Silicon REA, synthesis, target reports and registers | Broad workflow coverage from scanners and event calendars through options normalization, replay, action gates, and evidence envelopes. The target reports and their hash inventory keep vendor claims bounded to a captured source. | Forecast targets are kept distinct from current-state widgets; source and publication clocks stay attached; evidence is connected to each engine through exact report references. Index discrepancies stay visible in the prior audit record. | A product feature, vendor score, generated locator, parsed vault stream, or mirror bundle is not a validated forecast or cleared training dataset. |
| Femto `research/2026-10-20-eyes` | Matched-control and risk/avoid framing makes the negative case measurable. | FE09, FE10, FE12, FE14, FE24, FE28 and FE30 forecast risk states and failure transitions rather than only positive direction. | Exploratory winners and artifact rows do not become independent confirmation or desk sleeves. |
| Femto `research/gestalt-trading-engine-2026-10-26`, `research-data`, `research-archive` | Repeated-search accounting, simple incumbent comparisons, costs, and time-blocked validation are central to adjudicating a claimed edge. | Each Edge card states a decisive baseline comparison and a kill rule; tests across variants remain one declared family. | A retrospective best cell does not survive by being renamed or wrapped in an agent ensemble. |
| Femto `master-desk` / `desk-state` | Execution and state are separate operational surfaces with their own ownership and secret boundaries. | These forecasts stay in a research namespace and have no desk, broker, or OMS integration. | No desk state, credentials, or position state is imported into this work. |
| TheStrat public teardown and Saty research | Public setups can be made into event clocks and path labels. Saty's prior-period levels and EMA ordering are more precise than an informal chart description. | FE01 and FE03 make continuation/failure path definitions explicit; FE04 separates auction and regular-open clocks. The ambiguity between daily-open and kicking-bar-open triggers is carried as a blocking definition in the affected card. | A visual example or published rule does not establish expectancy; ambiguous triggers are not silently resolved after outcomes are seen. |
| TradingAgents | Specialized analysts can surface different causal views, with a separate risk/portfolio decision stage. | Agent output is treated as a hypothesis producer. Evidence lineage and the collision map are what determine whether views add distinct information. | Bull/bear/analyst count is not sample size, calibration, or an edge. |
| OpenBB | Extension-discovered data providers and normalized outputs create a useful provider boundary. | Connector adapters should preserve provider ID, field semantics, timestamps, rights, and hashes before features enter these contracts. | A common normalized schema does not make vendors' coverage, clocks, or licensing identical. |
| AI Hedge Fund | A single point-in-time advance path, loud missing-data failure, append-only record, and deterministic non-LLM sizing are useful separation-of-concerns patterns. | Forecast creation, outcome arrival, and any future portfolio action remain separate records and code paths. | An LLM-generated company thesis or model panel is not a probability until calibrated against outcomes. |
| Freqtrade | Backtest and dry-run differ through latency, missing fills, and timing; look-ahead checks are necessary. | Edge cards price next-executable marks, no-fills, turnover, and delay rather than assuming a bar-close fill. | A candle backtest cannot certify live execution or eliminate data leakage. |
| Microsoft Qlib | Data handlers, explicit train/valid/test segments, and recorded workflow artifacts support reproducibility. | Every forecast/outcome pair is append-only and carries the as-of cutoff; future experiments should retain their complete trial family and untouched time block. | A reusable workflow is not proof that input vintages or universe membership are point-in-time correct. |
| NautilusTrader | Event-sourced caches and reconciliation make order/fill/position state explicit; duplicate and out-of-order events require ownership and idempotence handling. | Forecast identifiers and lineage remain distinct from eventual order, fill, or position identifiers; a future desk integration must reconcile rather than infer position ownership from a signal. | A backtest event loop does not guarantee exactly-once external broker events. |
| RD-Agent | Research and development agents can propose hypotheses and implement experiments. | A generated idea is logged as a trial and inherits its card's baseline, source lineage, and kill rule before it can count as evidence. | Number of agent-generated variants is not an independent trial count unless the full search is accounted for. |
| Vibe-Trading | The current repository has a deterministic `paper_trade_step` simulator and a separate connector-first runner with profile-specific connectors, source routing, operator-set usage limits, and a kill switch. The current skill page lists 82 MCP tools and 90 finance skills, demonstrating why tool counts are version-bound. | Keep brokerless paper matching separate from a connector-backed paper/live path; version tool schemas and connector state, preserve source selection and operator limits, and do not let generated strategy code edit operator limits. | A paper simulator or configured connector is not evidence of fill quality or forecast edge. |
| Edge Trading Edge Lab | The v4 ledger requires the payer, type of information/risk transfer, bad state, ability to hold, execution net, decisive test, and kill rule before a strategy is called an edge. Its own README says its cases do not establish profitability. | Implemented as 30 typed EdgeCards with source-path validation and an `edge-ledger` command. | Edge's casebook and performance-control examples are not imported as outcomes for these engines. |
| Ausar's supplied 100 sleeves | The ideas span microstructure, stat-arb, events, momentum, volatility, macro, alternative data, overlays, and niche markets; many specify tail/cost/kill controls. | Their categories informed coverage, but the cards translate those concepts into forecast questions, competing outcomes, data availability, and falsifiers. | The supplied specifications do not provide a common clean history, fills, or independent sleeve P&L. |

Official public project documentation used for the repository design observations is linked in [SOURCES.md](SOURCES.md). Branch names and pinned SHAs for Femto and the separate TheStrat source are recorded in [CORPUS_AUDIT.md](CORPUS_AUDIT.md).

## Practitioner principles that changed the design

- **Independent discovery over idea count (Jim Simons).** Simons describes adding predictors for their incremental information and treating transaction-cost modeling as a research problem. That is why the collision map keys on raw lineage and the Edge cards compare incremental skill against a frozen simple baseline. An agent swarm only adds value when its evidence source or conditional mechanism is new.
- **Reflexivity over static flow labels (George Soros).** Participants' expectations can change the state they are forecasting. FE24's lagged ownership and FE26's index-flow path therefore include crowding/anticipated flow in the bad state: expected forced demand can be capitalized before the benchmark event, and publication or adoption of the signal can reduce its own residual. An event forecast cannot assume predicted flow is exogenous.
- **Survivability over theoretical sizing (Edward Thorp).** An estimated edge can disappear under parameter error, drawdown, and capacity constraints. Every card records holding path, co-losses, capacity or exit depth, and a kill condition before any future sizing layer is considered.
- **Style diversity with shared risk discipline (Jack Schwager's interviews).** The engines are not forced into one universal signal model. They do share source provenance, baseline comparison, loss-path accounting, and an explicit stop/retirement condition.

The first-person and archival sources are linked under “Practitioner research” in [SOURCES.md](SOURCES.md).

## Thirty engine hypotheses: third-pass mechanisms

| ID | Engine | Distinct forecast question introduced by the card |
|---|---|---|
| FE01 | Multi-horizon trend persistence | Which barrier is touched first: continuation or thesis invalidation? |
| FE02 | Regime-gated residual reversion | Does a factor/event-clean residual converge before a structural break? |
| FE03 | Breakout acceptance and survival | Does the level persist through a participation-and-depth dwell test? |
| FE04 | Overnight gap decomposition | Does issuer-specific gap residual continue or resolve across auction/open clocks? |
| FE05 | Breadth participation impulse | Does index leadership broaden beyond the largest return contributors? |
| FE06 | Sector leadership diffusion | Which sector receives leadership next, conditional on breadth and dispersion? |
| FE07 | Cross-asset lead-lag graph | Does the information edge arrive before it decays or flips? |
| FE08 | HAR-style realized-volatility forecast | Does a multi-scale variance surface retain skill under alternate sampling clocks? |
| FE09 | Jump and overnight-tail hazard | Which jump cause arrives first: scheduled, unscheduled, or ordinary-volatility path? |
| FE10 | Volatility/correlation transition | After a detected change, does correlation contagion follow? |
| FE11 | Closing-auction pressure | Does imbalance revision velocity predict clearing shortfall better than a snapshot? |
| FE12 | Liquidity fragility | How long does depth take to recover after a shock, and does that precede liquidity failure? |
| FE13 | OFI adverse selection | Is observed flow impact informed pressure or a temporary imbalance that replenishes? |
| FE14 | Options tail surface | Do risk-neutral tail prices anticipate physical tail frequency, conditional on events/quality? |
| FE15 | Dealer-gamma scenario map | How does the path differ under long, short, or unknown dealer sign? |
| FE16 | Options-flow response | Does the underlying confirm a probabilistic flow-intent hypothesis after the print? |
| FE17 | Earnings absolute move | What is the realized-minus-implied move after separating event-clock and jump history? |
| FE18 | Post-earnings drift | Do revision and price response diverge after isolating the event jump? |
| FE19 | Revision diffusion | Do estimate revisions lead price or merely trail it? |
| FE20 | Alternative-data nowcast | Is panel movement real activity or panel-composition/measurement drift? |
| FE21 | XBRL cash conversion | Does the linked accrual-to-cash chain strengthen or deteriorate? |
| FE22 | Filing semantic delta | Do narrative changes conflict with structured line items after parser quality controls? |
| FE23 | Insider flow | Does discretionary open-market activity carry information after plan/grant/tax-sale separation? |
| FE24 | 13F unwind hazard | Does stale crowd ownership meet deterioration and insufficient exit depth? |
| FE25 | Executed buyback support | Is reported repurchase pace supporting price, and when does that support exhaust? |
| FE26 | Index rebalance pressure | How much flow is forced versus anticipated, and does pressure reverse after effectiveness? |
| FE27 | Macro reaction function | Does the surprise coefficient change with market pricing, cycle, and release vintage? |
| FE28 | Rates/credit transition | Does the sequence of re-steepening, credit impulse, and lending stress foreshadow a regime transition? |
| FE29 | COT/inventory/supply | Does crowded positioning diverge from physical scarcity under the release clock actually in force? |
| FE30 | Crypto squeeze risk | How does a venue-specific liquidation cascade propagate through funding, depth, and basis? |

The machine-readable source of the full per-engine cards is `edge_cards.py`, queryable with `python -m research.forecast_engines.cli edge-ledger`. The full record has an individual target, baseline, payer hypothesis, bad state, co-loss, execution-net definition, decisive test, kill rule, and report refs for each row.

## Implemented diagnostic behavior

- `forecast_collision_map` only compares records with the same symbol, cutoff, target, target unit, horizon, and forecast unit. It detects duplicate record IDs, duplicate engine records, overlapping exact hashes/source IDs/declared groups, unknown lineage, cluster-level direction conflict, and a same-unit descriptive cluster median. It refuses decision-eligible records and never creates an action.
- `estimate_source_refresh` ignores labels not yet available by its `as_of`, rejects unapproved labels from the estimate, requires source hashes, groups by source age relative to target horizon, prefers source-specific history and falls back to family history, and withholds the point estimate until the sample floor. It emits a smoothed rate, Wilson interval, sample counts, and a hash fingerprint for the exact history used.
- `edge-ledger` validates coverage of FE01–FE30 and checks every local source reference exists. Each forecast includes its novel mechanism and payer hypothesis in the record, including abstentions, so the forecast log preserves the hypothesis that was evaluated.

These are research and audit functions. The forecast outputs remain outside the order queue and do not select positions. The most important next evidence work is to reconcile the stale requirement indexes on one pinned tree, semantically adjudicate the 557 generated requirement locators and the 39 large source streams within their rights scope, then collect a point-in-time, source-lineaged outcome panel to evaluate the 30 frozen cards.
