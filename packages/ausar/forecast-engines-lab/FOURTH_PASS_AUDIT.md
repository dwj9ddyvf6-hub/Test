# Fourth-pass audit: forecast fragility and provenance closure

**Date:** 2026-10-29
**Silicon snapshot:** origin/main remains aad9d2148752a6862ce7a6c44685311aa7310947; previous forecast branch commit is 1a829097c479f535f444e77ec138d73acff56189.
**Scope:** a new cross-source review of the 30 FE01–FE30 hypotheses, current forecast contracts, the seven original GitHub repos, Vibe-Trading, Edge, current REA indexes/reports, and latest live Femto branch tips. The fenced Morgue Engine, market terminal, desks, broker, and orders remain outside this implementation surface.

## New source-state check

The Silicon main tip and forecast feature branch still resolve to the pinned commits above. Five Femto research/desk refs match the third-pass audit. The desk-state branch advanced from a66598e9dd2abdc37d6cd8f24e7d45326195bdc8 to ede793aef6f26b6717ea2a6f889eca68b2a06f82 (two commits). GitHub's compare reports changes only in cache manifests/parts, desk health/state snapshots, sleeve state JSON, and state/ledger/open.jsonl; it lists no added research documents. The current tip was not copied into this repo and the desk state was not modified. This is a state-tree update, not a new research finding. Updated branch refs remain in CORPUS_AUDIT.md.

## Live upstream repository refs

At the 2026-10-29 ref check, the reviewed heads were:

| Repository | Ref | Commit |
|---|---|---|
| TradingAgents | main | c4544913a14ed3df5f1ed7b9e8483270ce20682a |
| OpenBB | develop | 7df7d0c5592bf25be88e87e130a05c71e243d2d8 |
| AI Hedge Fund | main | b33175caa1289e180b535d663c89b7a0c04b4726 |
| Freqtrade | main | a2f7475982de1d1e90127a18567965563de9724f |
| Microsoft Qlib | main | 54355232463878d2eebb91fe0ee5fa7fa1f5976c |
| NautilusTrader | main | fa26a1b227c0c184b55741b5365585454ca8dd8c |
| Microsoft RD-Agent | main | 484776c211e4fbbeef03e0ec00d6bbee7362a4f4 |
| Vibe-Trading | main | 956ade09c9cd1c1d2c0c484a0916aca68e6acb3f |
| Edge Trading Edge Lab | main | dd6a59248c7413b1759e2e9efaf9f85a0a9a64de |
| TheStrat public teardown | main | 8fb531d03c03879b0e9c297b80a216f5bfdadf02 |

The source concepts below were checked against current official documentation; this table pins the repository heads for follow-up comparison and does not claim that every upstream file at each head was line-by-line re-reviewed during this pass.

## Findings that changed the build

### 1. A raw-data hash did not make a forecast reproducible

Before this pass, a FeatureObservation carried a hash for its source record, while the forecast only named engine version 0.3.0-hypothesis. That left two gaps: a derived feature could change while the raw source hash stayed fixed, and the engine-version label did not bind a concrete scoring implementation. A caller could also mark an input inferred or reproduced without identifying the transformation that created it.

The record now preserves three separate identities:

1. Source hash — which upstream observation was used.
2. Transform ID/hash — which feature-building transformation produced a derived value.
3. Model fingerprint — exact engine specification, validation path, scoring and Edge-card source, and Python runtime.

The model fingerprint is deterministic across Windows and Unix line endings. Missing transform lineage makes inferred and reproduced evidence abstain. Older JSON remains readable because the new fields are optional for legacy records and direct observed/published values. The record schema is now 1.2; engine label is 0.4.0-hypothesis.

This distinction follows the engineering lesson across OpenBB, Qlib, NautilusTrader, and RD-Agent: a normalized value, a recorded run, a market event stream, and the code that made a forecast are different artifacts. OpenBB provider packages are independent and may be absent from an installation; the provider owns coverage and access semantics. Qlib workflow records configurations and time segments. Nautilus separates market-data catalogs from execution-state event stores and makes reconciliation provenance explicit. RD-Agent's self-evolving loop creates more candidate experiments, so every generated change needs its own trial identity rather than inheriting its parent's evidence.

### 2. A score was not a robustness map

The 30 formulas return point scores. Two equal scores can have very different geometry: one may stay on the same side across a meaningful input envelope, while another flips after one feature moves a small distance. No observed distribution is available here to define such an envelope, so the new tool refuses to invent one.

The boundary-map command accepts caller-supplied low/high ranges in each input's declared unit. It reports:
- the output at each one-feature endpoint;
- the first sampled direction change along each one-feature path from the baseline;
- the secant change in model score per input unit;
- pairwise difference-in-differences for every stressed feature pair, holding all remaining features at baseline;
- all joint corners of the supplied hyperrectangle, with an explicit scenario count;
- whether directions split across those corners.

This is boundary tomography, not a probability forecast. Pairwise interactions describe score geometry, not causal effects; higher-order interactions inside the range are not exhaustively sampled. Every result stays decision_eligible=false; no weights are assigned to corners. If input support ranges are unavailable, the analyst must provide them from a rights-cleared, point-in-time development sample before the output has an empirical interpretation. A baseline that abstains gets no stress result.

### 3. Transformation overlap is not the same thing as shared evidence

The earlier collision map joined forecasts when source hashes, source IDs, or declared groups overlapped. The fresh pass adds transformation IDs and hashes as a separate evidence edge. A shared transform implementation by itself no longer merges source clusters: the same standardization routine can process independent sources. The report still exposes those transform overlaps so an analyst can investigate shared model assumptions without mistaking them for shared raw evidence.

The 30 formulas remain separated by their target, horizon, units, and input clocks. The tool does not turn different targets into a consensus. It does not treat common code, repeated vendor coverage, agent count, or source labels as measured residual correlation.

## Cross-repository second lens

| Source | Freshly checked design detail | Specific consequence for FE01–FE30 |
|---|---|---|
| TradingAgents | Role debate is candidate generation and critique; more roles do not prove independent data or correct consensus. | Keep exact input/source and model lineage in every record; FE15/FE16 retain explicit latent dealer/intent assumptions. |
| OpenBB | V5 provider namespaces are separate extension packages; installed coverage can be incomplete, and connectors do not supply identical source rights or coverage. | Provider identity, field meaning, installed-version identity, publication clock, and source hash must survive into feature construction. |
| AI Hedge Fund | Agent-written thesis and portfolio selection are model outputs, distinct from observed market data and deterministic order controls. | Treat generated theses as inferred; require a transform/model hash and never convert one into calibrated probability by ensemble count. |
| Freqtrade | Official lookahead analysis compares baseline and sliced runs; recursive analysis checks indicator values under different startup histories. | A forecast can be point-in-time at the final input yet still be historically contaminated by a feature builder. Transform fingerprints are now recorded; a later panel audit should replay features over cutoffs and startup lengths. |
| Microsoft Qlib | Workflow configuration separates handler fit dates from dataset segments and stores run artifacts. | FE07/FE10/FE19–FE30 experiments must bind model, data vintage, universe membership, and time split; experiment artifacts need a stable fingerprint. |
| NautilusTrader | Backtest matching updates the book from data before callbacks; historical order-book data are immutable unless liquidity consumption is enabled. Live reconciliation distinguishes authoritative position reports from missing reports and retains event provenance. | Historical depth must not be credited to every sleeve repeatedly. Any later portfolio replay should share one liquidity budget and keep simulation assumptions distinct from actual forecast skill. |
| Microsoft RD-Agent | The finance scenario iteratively proposes factors/models and runs code in configured isolated environments. | Count each generated candidate and environment as part of the search family; a proposed improvement remains a hypothesis until its paired, untouched test. |
| Vibe-Trading | The project separates a deterministic paper-trading simulator from connector-backed runners; tool/skill counts change with repository version. | Simulator output, connector status, and market-data rights stay separate. A paper fill does not validate forecast edge. |
| Edge Trading Edge Lab | Each idea needs a named payer, transferred information/risk, bad state, holdability, execution net, paired test, and retirement rule. | Existing 30 cards remain the economic contract. The boundary map adds the missing score-fragility falsifier without weakening the Edge gates. |

The original seven repositories and the later-added Vibe-Trading/Edge design are in SOURCES.md and the prior three pass reports. This review added no claim that any repository's strategy wins after costs.

## Engine-specific stress map

The boundary-map command is available for all thirty catalog entries. The low/high ranges must be supplied in the exact units declared by each EngineSpec. Focus the first empirical envelope on the feature most likely to flip the causal interpretation:

- FE01–FE07 (trend, reversion, breakout, gap, breadth, sector, lead/lag): vary gating variables with the direction-bearing input—trend efficiency/Hurst, acceptance and false-break rate, fair-gap error/open acceptance, constituent breadth, and lag stability/R².
- FE08–FE10 (realized variance, tail hazard, regime transition): vary sampling-consistent realized-variance scales, event density, change-point confidence, and correlation shift. Keep risk ranking separate from event probability until calibrated.
- FE11–FE16 (auction, fragility, OFI, option tail, dealer gamma, option flow): vary timestamp reliability/depth, quote-condition quality, surface quality, inferred dealer sign, intent confidence, and open-interest age. Treat these primarily as data/assumption stress tests; never treat latent sign as fact.
- FE17–FE25 (earnings, drift, revisions, alternative data, XBRL, filing NLP, insider, 13F, buyback): vary announcement clock, consensus vintage, panel coverage/drift, parser confidence, plan classification, filing staleness, and reported execution pace.
- FE26–FE30 (index flow, macro reaction, rates/credit, COT/inventory, crypto squeeze): vary days-to-effective/crowding, market pricing/cycle sign, macro vintage, publication schedule, venue depth/funding, and chain-label confidence.

The list is a data-collection design. It does not assert those inputs have known distributions or that a stable flip boundary is profitable. The exact field names and accepted units remain machine-readable in catalog.py.

## What remains an open experiment

1. Run a rights-cleared, time-blocked feature replay to attach transformation hashes to derived observations and learn empirical support ranges for each FE input.
2. Use matured forecast/outcome pairs to estimate conditional error dependence and forecast horizon decay, with the exact target, unit, symbol, and event clock aligned.
3. Add a shared-depth replay only when market data and fill assumptions are specified; Nautilus demonstrates why liquidity consumption and event ordering must be explicit.
4. Promote no card from HYPOTHESIS until its Edge comparison, costs, falsifier, and untouched period pass.

## Source reading log

Primary/current references added in this pass:

- Freqtrade [lookahead analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/) and [recursive analysis](https://www.freqtrade.io/en/latest/recursive-analysis/) describe distinct checks for future leakage and startup-history sensitivity.
- NautilusTrader [execution reconciliation](https://nautilustrader.io/docs/latest/concepts/execution/reconciliation/), [backtest event flow](https://nautilustrader.io/docs/latest/concepts/backtesting/execution-flow/), [fill matching](https://nautilustrader.io/docs/nightly/concepts/backtesting/fill-prices-and-matching/), and [event sourcing](https://nautilustrader.io/docs/latest/concepts/event_sourcing/) document the separation between recorded market data, generated execution events, and reconciled state.
- OpenBB [V5 provider extensions](https://docs.openbb.co/odp/python/extensions/providers) and [provider FAQ](https://docs.openbb.co/odp/python/faqs/data_providers) describe separate provider packages and source-owned coverage/credentials.
- Qlib [workflow guide](https://qlib.readthedocs.io/en/latest/component/workflow.html) makes fit windows and dataset segments part of recorded experiment configuration.
- Microsoft's [RD-Agent repository](https://github.com/microsoft/RD-Agent) and [R&D-Agent-Quant paper](https://arxiv.org/abs/2505.15155) describe iterative data/model factor research; generated iteration count is not independent evidence.
- Thomson et al., [Combining Forecasts: Performance and Coherence](https://doi.org/10.1016/j.ijforecast.2018.10.006), analyze dependence and coherence between component forecasts. That supports exposing lineage edges while keeping empirical error correlation a separate calculation.

## Change boundary and status

Changes are confined to research/forecast_engines/. No REA report/index, vault content, Femto branch, Ausar Desk, research/morgue-engine/, apps/silicon-market-terminal/, credentials, broker, or order state was changed. The next empirical step depends on a rights-cleared point-in-time input/outcome panel; this pass adds tooling to examine an explicit caller-supplied envelope, not to fabricate one.
