# Psychology Engine: measurement, belief forecasting, and falsifiable trade context

Research date: 2026-10-30 UTC. **Status: research design / HYPOTHESIS, not a tested strategy or deployed engine.** No historical market dataset was fitted and no return, accuracy, or profitability result is claimed. Companion machine-readable specifications: `pattern_registry.json` and `engine_contract.json`.

## 1. Decision and economic boundary

**Verdict: promising research architecture; current trading edge unproven.** The useful objective is not to determine what “the market” privately thinks. It is to estimate what specified observable populations express, what evidence they attend to, how their expressed beliefs may change, and when that change adds information beyond price. Retail social contributors, news editors, corporate managers, professional survey respondents, options participants, and marginal liquidity providers are different populations. Silence is not neutrality; public advocacy is not a position; price is not an average survey response.

The proposed edge contract is **information/inference**: original, correctly timed evidence may reveal a change in expectations before it is fully reflected in prices or before a broader audience adopts it. The potential counterparty wedge is slow or costly interpretation, not an assumption that other investors are foolish. Alternative explanations are compensation for risk, changing liquidity, reverse causality from returns to text, promotional manipulation, or an apparent signal created by the data vendor. Competition, data latency, spreads, borrow, and position capacity can consume the entire benefit. A model that forecasts tomorrow's conversation but not incremental net returns can still be a useful risk/context instrument; label that result honestly.

**Tensor remains timing authority.** Psychology may annotate or rank research candidates and explain a hypothesis. It cannot create an entry, relax no-chase, use an unclosed bar, change an exit, increase risk, or override a rejected Tensor signal. Any future psychology-based veto or sizing change is itself a strategy change requiring separate approval and matched-policy evaluation. Until then it is advisory-only, including during severe fear or an apparent squeeze.

## 2. What the primary research supports—and does not

Araci's FinBERT establishes a financial-language classification approach, not a model of investor portfolios or a return guarantee. The separate Yang–Uy–Huang FinBERT also makes model/checkpoint identity important: “FinBERT” is not one interchangeable artifact. Use a pinned checkpoint, license, training-data description, and calibration version. [Araci, 2019](https://arxiv.org/abs/1908.10063); [Yang et al., 2020](https://arxiv.org/abs/2006.08097).

Loughran–McDonald document financial text categories including uncertainty and modality. Their domain lexicon is a valuable transparent comparator, not an adequate solution to negation, sarcasm, or entity attribution. FinEntity explicitly annotates sentiment toward individual financial entities, supporting entity-level rather than whole-headline scoring. [Dictionary documentation](https://www3.nd.edu/~mcdonald/Word_Lists_files/Documentation/Documentation_LoughranMcDonald_MasterDictionary.pdf); [Tang et al., 2023](https://aclanthology.org/2023.emnlp-main.956/). The dictionary documentation was available through search extraction; a direct-open attempt failed, so no unobserved detail is relied upon.

Tetlock investigates media pessimism and market activity; his stale-news research motivates distinguishing information novelty from repetition. Barber–Odean find attention-related differences in individual buying behavior, not universal profitable attention trading. Shiller motivates studying narrative contagion but does not provide this engine's forecasting coefficients. These papers justify falsifiable feature families rather than mechanical trading rules. [Tetlock, 2007](https://www.columbia.edu/~pt2238/papers/Tetlock_Media_Sentiment_JF.pdf); [Tetlock, stale-news manuscript](https://columbia.edu/~pt2238/papers/Tetlock_SSRN_Fit_to_Reprint.pdf); [Barber and Odean, 2008](https://faculty.haas.berkeley.edu/odean/Papers%20current%20versions/AllThatGlitters_RFS_2008.pdf); [Shiller, 2017](https://www.nber.org/papers/w23075).

Hong–Stein link disagreement with trading and constraints in explicit models. Their assumptions do not establish that high observed disagreement always predicts falling prices. Surveys that elicit probability distributions help distinguish personal uncertainty from differences among respondents. The Fed also cautions that market-implied risk measures include premia and that disagreement can be a poor uncertainty proxy. [Hong and Stein, 1999/2003](https://www.nber.org/papers/w7376); [Hong and Stein, 2007](https://swlb2.aeaweb.org/articles?id=10.1257%2Fjep.21.2.109); [New York Fed SCE](https://www.newyorkfed.org/microeconomics/sce/background); [Federal Reserve, 2025](https://www.federalreserve.gov/econres/feds/files/2025073pap.pdf).

LLM return research is encouraging but study-specific. Importantly, later work by Lopez-Lira, Tang, and Zhu shows historical economic information can be memorized; asking an LLM to “pretend it is 2020” is not a leakage control. Prospective frozen-model outputs are the strongest practical protection. [Lopez-Lira and Tang](https://arxiv.org/abs/2304.07619); [Lopez-Lira et al., 2025 preprint](https://arxiv.org/abs/2504.14765). This design does not import any reported paper performance into its own evidence stage.

## 3. State is multidimensional, population-specific, and horizon-specific

For instrument i, source population g, decision time t, and explicitly stated forecast horizon h, retain the following separately:

| Dimension | Measurable representation | What it is not |
|---|---|---|
| Directional stance | Calibrated probabilities of bullish / bearish / neutral / mixed, with unresolved attribution separately missing | Emotional positivity or probability the stock rises |
| Fundamental expectation | Extracted variable, unit, period, expected value/range and revision | An unsupported inference from adjectives |
| Emotion | Multi-label expressed fear, anger, excitement, regret, confidence probabilities | Diagnosed mental state or mutually exclusive classes |
| Uncertainty | Explicit hedging, modal strength, distribution width where actually elicited | Disagreement or high volatility by definition |
| Attention | Unique original items/authors, share of covered discourse, query counts where licensed | Absolute population attention inferred from a normalized search index |
| Disagreement | Within-population stance dispersion and between-population divergence | Average uncertainty or LLM sampling variability |
| Narrative composition | Versioned claim/theme shares, novelty, concentration, entropy | Arbitrary topic labels renamed after a move |
| Narrative diffusion | First-seen receipt, independent origin count, cross-population adoption lag | Syndication counted as independent corroboration |
| Conviction/persistence | Same-source stance persistence, explicit strength, revision frequency | Willingness/capacity to hold risk |
| Expressed intent | Verbatim evidence of buying/selling/holding intention | Actual transaction or holdings |
| Position/constraint context | Published short interest, verified borrow, fund exposures/flows, options measures with their separate clocks | “Smart money” or signed dealer gamma inferred from raw open interest |
| Price incorporation | Price-aware residual, event response, liquidity and volatility state | Proof that sentiment caused returns |

Report observed aggregates and latent model estimates in different fields. “Observed sampled social stance became more negative” is defensible; “investors are 83% fearful” generally is not. An illustrative dashboard can show several tiles, but never manufacture a universal fear/greed scalar. If an end-user needs a summary, use a sentence with conflicting dimensions and coverage caveats.

The latent state is only partially identified. Fix sign/scale anchors and population loadings before fitting; otherwise rotated factors have no unique psychological meaning. A slowly released survey can anchor a matching population/horizon, but a household inflation survey cannot directly calibrate intraday professional equity positioning. Where no defensible anchor exists, call the factor a **text-derived proxy**, not a recovered belief.

## 4. Evidence ledger and NLP pipeline

Every document needs immutable raw content/hash, original URL and provider ID; original publisher and upstream source; event time if known; first publication, update, vendor receipt, local receipt, extraction, decision, and expiry times; timezone; retrieval path; licensing constraints; revision lineage; instrument/entity mapping; and source-population classification. The actionable availability time is the latest necessary receipt/extraction clock, not the article's displayed publication date. Historical backfill availability is not proved by today's successful retrieval.

Pipeline: **ingest → validate clocks → resolve entities → deduplicate → extract attributable claims → calibrate/abstain → aggregate by population → forecast → advisory explanation**. Resolve common-word tickers and share classes against point-in-time identifiers. Associate each proposition with subject, speaker, target, economic variable, time horizon, comparison baseline, conditionality, polarity, evidence span, and factual/reporting/opinion status. “Lower oil is good for airlines but bad for producers” requires opposite entity implications, not one positive headline score. Historical mentions, quoted critics, and issuer boilerplate must not become current author endorsement.

Maintain a transparent lexicon baseline, a pinned domain classifier, and a constrained structured LLM extractor. The LLM is strongest for separating actuals from expectations, speaker attribution, comparison direction, and causal claims; deterministic checks handle units, dates, schema, and arithmetic. It must output `unknown` for unsupported quantities. Its self-reported confidence is not a calibrated probability. Raw emotion and stance probabilities are calibrated on labeled examples, independently of return forecasts. Temperature scaling is a baseline calibration method, not a permanent fix for distribution shift. [Guo et al., 2017](https://arxiv.org/abs/1706.04599).

Annotate a source-stratified, time-stratified test set with two independent annotators and adjudication. Retain disagreement, not only “easy” unanimous samples. Test exact entity spans, speaker, target horizon, entailment of numeric values, neutral-versus-missing, negation scope, comparative changes (“loss narrowed”), conditional forecasts, sarcastic enthusiasm, mixed entities, slang, and multilingual text separately. Hard cases may abstain. Audit false actionable positives more heavily than harmless neutral errors. Preserve prompt/model/hash and sampled decoding settings; a checkpoint change invalidates comparability until re-evaluated.

For prompt injection, all fetched text is untrusted data. No document instruction may alter tools, policy, source selection, timestamps, or execution. The extractor receives only the necessary content in a non-executable envelope. Evidence citations are verified against stored spans. No third-party script, model loader with remote code, or unreviewed repository is needed for this design.

## 5. Dependence, manipulation, and population bias

Use exact hashes plus normalized text similarity and shared quote/claim lineage to identify copies. Form an **information-origin cluster** and a separate **distribution-exposure cluster**: one release copied 200 times is one factual origin but potentially broad attention. Do not erase exposure; do not multiply evidence. Store uncertain lineage explicitly. Repeated articles that add new facts produce a linked revision with the increment isolated.

Within a population, cap a prolific author's contribution and compute both equal-author and equal-origin aggregates. Source weights must be fixed from past validation, not granted because a source agrees with the forecast. For weights w and an estimated dependence matrix R, `(sum w)^2/(w' R w)` is a diagnostic effective sample size under a normalized common-variance approximation—not a literal count of independent investors. Report raw documents, unique authors, origin clusters, and concentration alongside it. Correlation estimates are uncertain; run conservative shared-origin sensitivity analyses.

Bot/promotional likelihood uses behavioral evidence such as synchronized timing, near-duplicate language, abnormal account activity, and link networks where collection is permitted. It is not proof of identity or malicious intent. Report results with and without suspect clusters. A burst can still affect attention even if artificial, so it belongs in manipulation/exposure context rather than being silently deleted.

Correct known sampling changes, not unknowable representativeness. Platforms exclude silent holders and may change API coverage or recommendation algorithms. Report the actual sampling frame; do not extrapolate to all investors. Separate genuine stance changes within a stable author panel from changes caused by new authors entering. A source outage can lower document count without lowering attention. Covariate balancing across observable source strata helps only under explicit selection assumptions. Test platform/source leave-one-out and stable-panel estimates before calling a shift broad-based.

## 6. Exact feature families

All rolling fits use observations available strictly before t. Intraday windows are 5/15/60 completed minutes; daily windows are completed sessions. Different clocks never share a misleading “live” badge. Use trailing medians/MAD or empirical percentiles fit in training; preserve denominator and sample count. Sparse or zero denominators yield missing, not infinite conviction.

For origin/author-weighted stance probabilities, `S=sum w*(p_bull-p_bear)/sum w`. Track neutral and mixed mass separately. Disagreement is weighted variance of source-level expected stance; across populations use Jensen–Shannon divergence of class distributions, with a fixed class alphabet and explicit zero handling. Narrative entropy is `-sum q_k log(q_k)`; normalized entropy uses a fixed taxonomy K and is undefined when K<2. A dynamic clusterer must version its taxonomy so a cluster split does not fabricate rising entropy.

Attention uses `A=log(1+unique_origin_count)` and, separately, `log(1+unique_author_count)` and share of all covered items. Deseasonalize by time-of-day/day-of-week using training history. `velocity=A_t-A_(t-w)`; `acceleration=A_t-2*A_(t-w)+A_(t-2w)` uses nonoverlapping comparable windows. Novelty is one minus maximum similarity to **prior available** same-entity claim embeddings in a prespecified lookback; factual novelty also requires a newly supported proposition. Embedding novelty alone can be stylistic novelty.

Diffusion measures the fraction of observed populations adopting a claim, number of independent origins, origin-to-adoption lags, and new-adopter rate. A Hawkes/branching model is an optional challenger only: observed excitation is not identified interpersonal causation when all sources react to a common release. Expected surprise is a distribution: pre-event `P(actual-consensus > delta | I_t)` or a standardized expected difference. It requires a timestamped expectation distribution and comparable economic definitions. Post-release actual-minus-consensus is a different feature and cannot appear in a pre-event forecast.

Sentiment-price divergence must not subtract arbitrary units. Fit the expected current/next return from the price-aware baseline and text increment in training, or fit expected stance conditional on lagged return and compute a residual. Compare both formulations. A negative-text/flat-price pattern is a conditional observation, not automatic bullish absorption. Match on event severity, beta, volatility, liquidity, time since release, and price move already realized.

Positioning is a **constraint vector**, not a signed mood score. FINRA short interest is a periodically reported stock of positions; daily short-sale volume is transaction flow and cannot simply be accumulated into outstanding shorts. Open interest alone is not bullish/bearish. Unknown buyer/seller initiation and dealer inventory mean gamma sign is unknown. [FINRA explanation](https://syndication.finra.org/content/short-interest-what-it-what-it-not); [FINRA reporting](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest); [OIC guidance](https://www.optionseducation.org/referencelibrary/faq/general-information).

## 7. Nowcast and forecast architecture

Start with simple, inspectable baselines: persistence, seasonal attention, exponentially weighted stance, and regularized direct-horizon regressions. Then test a hierarchical state-space model:

`x_t = F(r_t)x_(t-1) + B u_t + eta_t`

`y_(s,t) = H_s x_(g,t) + b_s + epsilon_(s,t)`.

Here x contains a small number of named states; u contains only already-known calendar/events and price context; r is a filtered regime probability, never a future-confirmed regime label. Observation noise depends on source quality, effective sample size, and annotation error; its covariance includes shared source lineage. Model assumptions and fitted covariance must be disclosed. Missing observations remove measurement rows; old survey observations are not repeatedly reintroduced as new independent data. A stale prior may propagate with widening uncertainty, visibly marked `model_propagated`.

Mixed-frequency state-space methods offer a principled way to handle publication lags and missing observations, but transfer to psychological proxies is our hypothesis, not a result of the macroeconomic paper. Use filtering for live/replay states; retrospective smoothing may be shown only as retrospective. [Bańbura and Modugno, ECB working paper 1189](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1189.pdf).

Issue distributions at explicit horizons—30 minutes, next session, five sessions—only where source cadence supports them. Forecast next-window stance by population, narrative share, attention growth, disagreement, and probabilities of prespecified transitions. Label targets independently through future sampled/annotated evidence, not merely by rerunning the same classifier and claiming it predicts human minds. Text forecast quality and return forecast quality remain separate scorecards. A fast source cannot turn a weekly survey into a verified intraday belief observation.

Return challengers use `P(Y_h|Z_t,S_t)` versus the same-capacity `P(Y_h|Z_t)`, where Z includes current/lagged returns, realized volatility, volume, spread/liquidity, calendar, market/sector exposures and event information. Psychology must add value after what price already knows. Regime interactions are sparse and preregistered: trend/range, high/low volatility, event/non-event, liquidity, and market stress. Shrink thin cells instead of displaying confident regimes. Attention may predict activity more reliably than direction; disagreement can forecast tails without sign.

## 8. Falsifiable pattern registry

The companion JSON gives 16 exact research cards, each with feature definitions, comparator, target/horizon, mechanism, rival, timing/execution hazard, and falsifier. None is an entry rule. The families are:

1. **Verified-new versus stale-echo diffusion:** genuine incremental claims should differ from repeated claims with equal headline sentiment.
2. **Attention ignition:** accelerating independent attention plus low prior attention may precede belief adoption; price response is a separate test.
3. **Consensus exhaustion:** highly concentrated optimistic narrative plus decelerating new adopters may precede reversal in expressed stance.
4. **Polarization rupture:** high between-group disagreement with low within-group uncertainty may predict larger belief redistribution and realized tails.
5. **Cross-population migration:** professional/editorial-to-social adoption lag may forecast diffusion, without assuming one group is always informed.
6. **Horizon dissonance:** near-term bearish but long-term bullish language may resolve differently from uniformly bearish language.
7. **Negative-news absorption:** repeated verified negative surprises with smaller conditional price response may precede less-negative stance.
8. **Optimism beyond expectations:** positive language alongside negative actual-versus-expected fundamentals may predict adverse revisions despite upbeat tone.
9. **Squeeze vulnerability, not squeeze certainty:** new positive evidence, documented shorts/borrow constraints, and improving stance may predict asymmetric upside tails.
10. **Squeeze exhaustion:** cooling new adoption after an attention/price burst may predict a worsening tail distribution; short execution remains dangerous.
11. **Uncertainty compression:** a verified resolution can reduce uncertainty even when average stance does not change.
12. **Narrative rotation:** new causal drivers replacing an old theme may predict changing cross-sectional return associations.
13. **Credibility-weighted contradiction:** correction of a widely shared false claim may move beliefs differently from quiet correction of a low-reach claim.
14. **Stable-panel versus entrant disagreement:** apparent consensus driven only by incoming authors should be less persistent than within-author revision.
15. **Event-expectation asymmetry:** the same realized surprise may produce different revisions conditional on prior expected surprise and confidence.
16. **Narrative immunity:** repeated same-sign claims with declining marginal adoption may lose forecasting power; new verified facts should reset this only if the mechanism is real.

For every card, the falsifier is an out-of-sample, precision-aware decision rule. A wide interval is inconclusive, not evidence of no effect; an upper bound below the preregistered economic minimum rejects deployability. A mechanism contradicted by its negative control is not rescued by one profitable subgroup.

## 9. Validation, economics, and evidence promotion

Freeze eligible universe, source coverage, model/checkpoint, extraction policy, label definitions, horizon, event clustering, split dates, parameter/search budget, and incumbent Tensor outputs. Use chronological development, walk-forward validation, and an untouched final interval. Purge training observations whose feature or label information overlaps validation events; choose embargo from actual dependency/holding horizons rather than an arbitrary universal percentage. Put whole syndicated/event families on one side where necessary. Fit dedup thresholds, embeddings/clustering policy, preprocessing, feature selection, hyperparameters, and calibration inside each training fold.

Use date/event blocks and cross-asset clusters for uncertainty, not independent row bootstrap. Report effective opportunities, market conditions covered, block lengths and sensitivity, power/minimum detectable economic improvement, and all tried variants. Multiple-testing controls and a full trial ledger matter; PBO or selection-adjusted Sharpe diagnostics do not certify a chosen strategy. [Bailey et al., 2015](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

NLP scorecard: entity/attribution F1, class confusion, calibration, missingness, evidence-span entailment, and abstention quality by source/time. Belief scorecard: log loss/Brier for transitions, CRPS or quantile losses for continuous states, interval coverage/sharpness, skill versus persistence and seasonal baselines. Return scorecard: price-aware incremental proper-score improvement, calibration in prespecified Tensor-eligible cohorts, gross/net expectancy, turnover, factor exposure, drawdown/tails and capacity. Calibration means frequency agreement, not predictive power; a base-rate forecast can be calibrated and useless.

Ablate one conceptual family at a time: price-only; price plus attention; plus stance; plus novelty/diffusion; plus positioning; full model; full model without each source. Compare simple lexicon, FinBERT, structured LLM, and ensemble under matched chronology and cost. Controls: delayed news, duplicated news, stale-copy placebo, entity-shuffled within-sector text, source outages, stable-author panel, and signals permuted within appropriate date/event blocks. A signal that improves only when future updates are used fails immediately.

Economic comparison uses **identical frozen Tensor opportunities and execution authority**, not a new psychology entry. Shadow-report outcomes for all eligible opportunities and all abstentions, avoiding survivor/fill selection. Any later approved gating policy is evaluated against the same baseline after spreads, fees, slippage, impact, borrow/funding, partial/no fills, latency and gaps. Use executable prices after all necessary evidence is available; an article timestamp does not grant a fill at the preceding bar close. Report whether improvements remain under conservative delay/cost stress and whether they simply add beta or short-volatility exposure.

For drift, monitor source mix, extraction error, feature distributions, matured forecast residuals, calibration and net incremental utility separately. Delay labels until horizons mature. Adaptive conformal methods are possible interval challengers; long-run coverage does not imply reliable conditional coverage in today's crisis or every instrument. [Gibbs and Candès, 2021](https://arxiv.org/abs/2106.00170). Respond first to data failures by removing affected measurements and widening uncertainty, not by inventing neutral readings. Retraining is a new version with replay and promotion gates; no automatic live policy mutation.

## 10. Quality contract and next decisive experiment

Each output carries `as_of`, `information_cutoff`, `available_at`, `expires_at`, source coverage, raw/unique/origin counts, max/min source age, correlated-source groups, model/calibration versions, evidence spans, confidence components, missing features, and evidence stage. Status distinguishes `observed`, `model_estimated`, `stale`, `partial`, `unavailable`, and `not_applicable`. Freshness is source- and horizon-specific; retrieval time never resets observation age. Forecast probability, extraction confidence, data completeness, and model uncertainty are separate fields—not a single impressive “confidence 92%.”

**First experiment:** capture an immutable, authorized prospective stream for an agreed limited universe; dual-label a stratified sample; build deduplication, entity attribution, and price-aware persistence baselines; then preregister P01/P02/P08 as a small initial family. These distinguish information novelty, attention, and expectation-relative meaning at modest complexity. P09 requires verified short/borrow inputs and remains unavailable without them. Reserve a prospective interval sufficient to estimate the chosen minimum improvement; duration follows opportunity frequency and uncertainty, not an arbitrary trade count.

Acceptance is staged: schema/clock correctness → extraction validity → retrospective support with leakage caveats → untouched/prospective forecast support → forward simulation and net utility → explicit authorization for any behavioral integration. **Current achieved stage is design only.** The user can receive an auditable description now; the engine must not display synthetic live readings or infer that a written contract has been implemented.

## 11. Forecast objectives and adversarial examples

The primary belief estimand should be explicit: for a frozen sampling policy, forecast the distribution of the **next observed window's independently assessed stance share**, not the unobservable stance of every holder. A model can use a beta-binomial/count model for category shares with overdispersion or a multinomial state model, but dependent authors and sources require clustered measurement error. Forecast both the latent share and the noisy sample realization when the distinction matters; a sparse future sample should produce wider predictive intervals. Record whether apparent error arose from a mistaken forecast, annotation error, changed audience composition, or too few observations. These diagnoses are hypotheses until checked, not excuses to discard losing cases.

For narrative transitions, define an event such as “theme k's author share rises above its prior-window share by at least delta” with delta fixed in development data. For stance transitions, define direction, population, minimum change, and horizon. For attention, forecast counts or growth relative to seasonal exposure. A forecast that a topic becomes popular is not necessarily a forecast that readers believe it. For pricing, define total versus market/sector-residual return and entry/exit clocks independently of future outcomes. Do not choose an advantageous horizon after seeing when a move ended.

An exact decomposition of performance is useful: extraction model → observed-feature construction → proxy forecast → incremental price forecast → executable advisory-policy value. Ablating the LLM only at the last stage can miss an attribution failure upstream. Conversely, a better extractor need not improve returns if competitors already price the information. Track computational expense and decision latency, too: an expensive model that improves classification after the capture window may be operationally inferior to a simple one.

**Illustrative audit fixtures—not current readings or trading examples:**

* A headline says profits grew, but the release contains earnings below a timestamped comparable consensus. Positive absolute tone and negative expectation-relative surprise must coexist. If consensus is missing, the engine cannot manufacture disappointment.
* One press release appears on twenty news sites. Origin count remains one; observed distribution exposure can be twenty. An independent analyst's new calculation may add an origin-supported interpretation, but its quoted release facts are still shared evidence.
* Social discussion becomes more bearish because a platform adds a bearish community to the feed. Aggregate stance changes, stable-panel stance does not, and composition alarms rise. The correct result is not “the whole market turned bearish.”
* A twice-monthly short-interest report is downloaded this morning. Its settlement and publication dates remain visible. Fresh download time does not create fresh positioning; lack of borrow data blocks the constrained-short pattern.
* Text correctly forecasts rising attention during the next hour, but price has already jumped beyond Tensor's no-chase limit. The admissible outcome is useful context and no new entry, not a relaxed threshold.
* At decision time a document exists, but structured extraction completes later. That extraction cannot be used in the earlier replay. A cached earlier lightweight extractor is eligible only if its own output was genuinely available and versioned.

These fixtures should become executable contract tests in an authorized implementation. The current artifact validates JSON syntax and static authority/card assertions only; it does **not** establish that any production service passes these behavioral tests. Before implementation, agree the actual source entitlements, retention rights, limited universe, source-specific freshness policy, intended horizons, labeled-data budget, and unchanged Tensor baseline identifier. Those are dependencies, not missing parameters to invent.
