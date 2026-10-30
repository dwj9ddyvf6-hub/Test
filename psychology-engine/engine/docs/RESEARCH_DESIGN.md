# Measurement, inference and validation design

This technical companion specifies the research contract. The parent study supplies the broader behavioral literature and cited synthesis; this document does not claim to be a completed doctoral empirical study.

## Separate latent states from observable proxies

Let latent state z(t) include belief direction, attention, uncertainty, disagreement, positioning constraints and narrative prevalence. Each observed source x(s,t) reflects z(t), population selection, measurement error, institutional constraints and its own publication process. A useful conceptual measurement model is x(s,t)=loading(s)*z(t)+controls(s,t)+error(s,t). The current implementation deliberately exposes raw compatible-unit summaries; it does not pretend these latent loadings have been estimated.

Directional sentiment is not attention. Uncertainty is not negative valence. Disagreement is cross-observer dispersion, which can be high when average sentiment is neutral. Positioning is behavior subject to hedging and constraints. Stress combines risk pricing, liquidity and leverage channels and need not reflect pessimism. Narrative change concerns distributions of topics and causal stories, not a count of negative words.

Potential measures include repeated representative surveys; expectations and forecast dispersion; fund flows and holdings; futures positioning; options skew and term structure; liquidity and spreads; public news stance and uncertainty; search/pageview attention; topic transitions and narrative diffusion; earnings-call language; analyst revisions; prediction-market contracts; and public social discussion. Each requires a distinct population, unit, horizon, license and timestamp definition. Private personal profiles and covert individual mental-state inference are outside scope.

## Mechanisms and identification

Limited attention and underreaction suggest delayed adjustment; salience and overreaction may suggest reversals; herding, social transmission and career incentives can synchronize behavior; overconfidence can increase turnover; loss aversion and reference dependence can alter realization choices; ambiguity and uncertainty can increase required compensation; leverage and collateral constraints can mechanically amplify selling. These mechanisms may coexist with rational responses to fundamentals. The same price path does not identify which mechanism operated.

The causal graph includes fundamentals -> news, beliefs and prices; prices -> attention and expressed sentiment; liquidity/constraints -> positioning and prices; publication and selection -> observed data. A sentiment-return correlation is therefore not evidence that sentiment caused returns. Use event timing, predetermined survey release schedules, quasi-experimental attention shocks where defensible, matched controls, negative controls and alternative explanations. Granger prediction is not structural causation.

## Pattern research contract

For each registered hypothesis fix entity universe, source populations, lag, target, horizon, direction, interaction, training window, costs, inclusion/exclusion rules and invalidation before inspecting test outcomes. The registry provides falsifiable starting hypotheses, not discovered facts. Train trend-following and reversal alternatives with regime controls rather than selecting whichever story fits retrospectively.

Forecast next observable survey distribution, narrative prevalence, realized volatility, drawdown probability or return distribution. Do not claim to forecast the unobservable private thoughts of everyone. Produce calibrated probabilities and intervals only after suitable held-out calibration; the current engine emits no such probabilities.

## Point-in-time discipline

Maintain event time, publication time and first-seen time separately. Revised data must remain versioned. Historical acquisition time does not establish historic availability. Evaluation may use a supplied historical first-seen value only if independently audited. Index constituent and delisting histories, exchange calendars, timezones, holidays, publication delays and entity mapping versions must also be point-in-time for real studies. Freshness thresholds are source-specific and require sensitivity analysis. A missing source is not a neutral observation.

## Evaluation and model risk

Use temporal outer holdouts and nested inner selection, purge overlapping labels, embargo when required by feature dependencies, and retain a final untouched test. Compare against price-only, volatility-only, historical-mean and persistence baselines on identical samples. Run source and feature ablations, reverse-time/placebo tests, duplicate-source stress tests, costs and latency sensitivities, and comparisons across regimes and assets. Use block bootstrap or HAC-aware uncertainty and control family-wise/FDR multiple testing for exploratory searches. Report all attempted hypotheses and failed results.

The included evaluator is a minimal fixed-hyperparameter expanding-window example. It respects explicit label availability and non-overlap but does not implement nested model selection, block bootstrap, full market calendars, survivorship correction, corporate actions, funding/borrow/impact, portfolio risk or full inferential testing. Its complete-case common sample can be selected; report the missingness process before any market claim. Synthetic generated dependence demonstrates plumbing only.

## NLP validation and monitoring

The included small English lexicon is auditable but misses finance-specific meaning, sarcasm, negation scope, quoted speakers, entities, multilingual context, topic relevance and stance toward specific assets. Zero matched directional tokens is unknown. An uncertainty-token fraction of zero means none of these terms appeared, not absence of latent uncertainty. For a replacement financial model freeze version, training cutoff, license and prompts; use human labels and inter-rater agreement, entity-level evaluation, domain/language subgroups, probability calibration, drift checks and an abstention path. Treat external text as data, never instructions.

Exact normalized-text deduplication does not detect paraphrased syndication, bot networks or common ownership. Version source families manually and compare with correlation clustering. Consider population weights and sampling changes rather than weighting by posting volume. Report effective sample size and overlapping source dependence.

## Advisory integration boundary

The immutable advisory record contains the cutoff, evidence identifiers, units, exclusions, state, model/schema identifiers and a decision mode. It is eligible for human or existing workflow review only. Tensor retains timing authority; no direct trade entry, order sizing or execution is implemented. Before production, define validation gates, integration contract, source budgets, alert delivery approval, retention and deletion policies, secrets management, access reviews, resource limits and fail-closed behavior. None of those operations is activated by this package.
