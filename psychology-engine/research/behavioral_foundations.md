# Psychology Engine: behavioral foundations and falsifiable market mechanisms

**Research date:** 2026-10-30. **Status:** research specification, not a validated trading strategy. **Scope:** selective deep reading of foundational and directly relevant primary research; not an exhaustive literature review. Twenty-two source records, including version/access qualifications, accompany this report in `sources.json`.

## Executive conclusion

Human psychology affects markets through several different objects: what participants believe, which information they notice, the utility they assign to outcomes, how they learn from one another, the identities and incentives attached to positions, and their capacity to finance decisions. These objects interact with institutions. A psychology model that omits funding, mandates, transaction costs, and the distribution of wealth will regularly mistake rational necessity for irrationality.

The defensible foundation for the **Psychology Engine** is therefore a conditional mechanism engine, not a universal fear/greed number. Its central question is: **Which population is changing which decision, because of which new information or constraint, over which horizon, and what observable consequence would disprove that account?** A persuasive psychological explanation is not yet a forecast; a good forecast is not yet a profitable executable policy.

The research supports investigating attention-driven demand, reference-dependent selling, extrapolative expectations, social information segregation, emotional changes in risk taking, and funding-amplified feedback. It does not establish that any combination proposed here earns positive net returns today. The most valuable initial product is an auditable event-level research system that separates competing explanations and learns where psychological measurements add information beyond prices, fundamentals, and liquidity.

## 1. What must be explained: beliefs, preferences, actions, prices

### 1.1 A market is not a person

“The market is afraid” is shorthand, not a psychological diagnosis. A price is an equilibrium outcome of heterogeneous orders and the available supply of immediacy. The loudest participants need not have the largest positions; the wealthiest participants need not be marginal traders; the marginal trader in a stock need not be marginal in its options. A participant can be bullish about a company, bearish about its valuation, short its stock as a hedge, and anxious about a different portfolio exposure simultaneously.

For engineering purposes, preserve at least six separate state families:

1. **Beliefs:** distributions over cash flows, macroeconomic states, prices, policy, and other participants' future actions.
2. **Preferences:** risk tolerance, loss/reference dependence, ambiguity attitudes, and willingness to wait.
3. **Attention and processing:** what enters the decision set, which facts are encoded, and processing delay.
4. **Social structure:** information exposure, narrative adoption, identity norms, and strategic expectations about others.
5. **Constraints:** cash, leverage, collateral, mandates, redemption obligations, short availability, and career incentives.
6. **Actions and implementation:** desired positions, submitted orders, executed trades, cancellations, and realized financing needs.

Do not infer all six from a single text score. In particular, a negative sentence is not proof of pessimistic beliefs, risk aversion, a short position, or an intention to sell.

### 1.2 A disciplined causal graph

Use a time-indexed graph rather than a one-way sentiment-to-return story:

`fundamental news → beliefs → desired positions → order flow → prices`

with additional paths:

`attention → information acquisition and consideration set`

`emotion/reference state → preferences and perception`

`prices → wealth/collateral/attention/narratives → future decisions`

`mandates/redemptions → feasible positions → order flow`

`network exposure → beliefs and expression`, while `beliefs → chosen network exposure`.

These feedback paths explain why contemporaneous correlation is ambiguous. Falling prices can produce negative headlines; headlines can disseminate new information; both can respond to an omitted deterioration in cash flows. Conditioning on a variable caused by both sentiment and fundamentals can also introduce bias. Every empirical design should specify which arrow it tries to estimate and which variables are confounders, mediators, or outcomes.

### 1.3 A minimal structural thought experiment

As a **model assumption**, suppose group g chooses a risky position using mean-variance preferences subject to a feasible set K:

\[
q^*_{g,t}=\arg\max_{q\in K_{g,t}}\left[q\{\mu_{g,t}-P_t(1+r_f)\}-\tfrac12\gamma_{g,t}q^2\sigma^2_{g,t}\right].
\]

Here μ is the group's subjective next-period payoff expectation, γ its risk-aversion parameter, and σ² its perceived payoff variance. Without constraints, position demand is proportional to `(subjective expected payoff − financed purchase price)/(risk aversion × perceived variance)`. This is deliberately not a complete behavioral model. It reveals an identification problem: reduced buying can arise from lower μ, higher γ, higher perceived variance, or a tighter K. Price data alone generally do not identify which changed.

Aggregate demand must clear against supply; marginal price sensitivity depends on the slopes and constraints of the participating groups. A headcount-weighted poll cannot be substituted for this demand system. Weighting social posts by follower counts does not solve it either: followers, capital, credibility, attention, and executable order size are distinct quantities.

## 2. Standards of evidence

**Theory** establishes what follows under specified assumptions. It does not establish prevalence. **Randomized experiments** can identify effects of manipulated conditions on measured choices in their experimental population, but do not automatically identify effects on aggregate prices. **Quasi-experiments and event studies** require defensible exclusion, timing, and counterfactual assumptions. **Observational account records** measure behavior more directly than prose but do not fully reveal motives. **Predictive associations** can be useful without being causal, provided they survive genuinely prospective testing and realistic implementation.

Confidence should therefore have separate dimensions: source integrity; construct validity; causal identification; population relevance; temporal relevance; predictive replication; and executable economic value. Averaging these into one “confidence” hides important failure modes. Strong laboratory identification can coexist with weak external validity; a useful forecasting proxy can coexist with an unresolved psychological mechanism.

All candidate mechanisms below are research hypotheses at the implementation stage. No historical effect size should become a production coefficient without point-in-time re-estimation and validation.

## 3. Mechanisms, measurements, and failure conditions

### 3.1 Reference dependence, loss aversion, and the disposition effect

Kahneman and Tversky's original prospect theory assigns value to changes relative to a reference point and uses decision weights rather than simply objective probabilities. Its framing and reference-point discussions make the reference state central, not an incidental feature. The paper is a descriptive choice theory, not a proof that every investor always avoids losses. [Kahneman and Tversky, 1979](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf)

A schematic parameterization is `v(x)=x^α` for gains and `v(x)=−λ(−x)^β` for losses, with λ>1 representing loss aversion. This is an illustrative functional form, not an estimated parameter set. Curvature, loss aversion, and probability weighting are different components; conflating them produces incorrect predictions.

Odean's brokerage-account study documents greater realization of gains than losses, with December tax-related variation and checks against rebalancing and trading-cost explanations. Its direct behavioral measure is `PGR = realized gains/(realized + paper gains)` versus the corresponding PLR. It does not uniquely identify loss aversion as the cause. [Odean, 1998](https://faculty.haas.berkeley.edu/odean/papers/disposition/disposit.pdf)

**Engine hypothesis:** position-level acquisition prices, investor experience, taxes, and liquidity jointly shape selling pressure around reference states. With only market data, estimated aggregate cost bases are noisy proxies—not observed mental reference points. Test whether gain/loss state adds explanatory power to subsequent selling after controlling for momentum, volatility, taxes, and portfolio rebalancing. Failure includes no incremental selling discontinuity, reference-point instability, or predictive disappearance outside the estimation market. Never infer that an investor who holds a loser must be irrational; information, taxes, hedges, and long horizons can justify holding.

### 3.2 Overconfidence is not the same as bullishness

Overconfidence can concern precision of information, relative skill, or control over outcomes. A pessimistic trader can be overconfident in a short thesis. Barber and Odean's account evidence shows a substantial net-performance penalty among highly active households in their historical sample. Their comparison of turnover and gross versus net performance is consistent with overconfidence-based excessive trading; overconfidence itself was not randomly assigned or directly measured for every account. [Barber and Odean, 2000; author draft inspected](https://citeseerx.ist.psu.edu/document?doi=2b611939318c6ad09f7f88ccea5df08311493ec0&repid=rep1&type=pdf)

**Engine hypothesis:** confident language coupled with narrow stated forecast intervals, rapid turnover, and repeated failure to revise forecasts may identify a different state from optimism alone. Operationalize confidence only where observable: explicit probability statements, interval width, forecast revision, or consented account behavior. “Certain,” capitalization, or posting frequency alone are weak instruments. Compare stated calibration against realized outcomes, controlling for task difficulty and selection into public posting. The trade implication is not automatically to oppose confident people: genuine expertise and private information also produce confidence. Failure occurs when the feature merely captures expertise, publicity, volatility, or a profitable strategy's legitimate turnover. For the Engine itself, require explicit costs and a no-trade baseline so increased activity is not confused with increased intelligence.

### 3.3 Attention changes the opportunity set before it changes beliefs

Barber and Odean find individual investors disproportionately buying attention-grabbing stocks, measured using news, unusual volume, and extreme returns, with institutional behavior varying by style. Their published analysis also considers heterogeneous beliefs and selling constraints as alternatives. Attention is not equivalent to positive news: salient bad news can still bring a stock into more buyers' consideration sets. [Barber and Odean, 2008](https://faculty.haas.berkeley.edu/odean/Papers%20current%20versions/AllThatGlitters_RFS_2008.pdf)

DellaVigna and Pollet compare earnings responses across announcement days and find evidence consistent with less immediate and more delayed response around Friday releases. Announcement timing is selected by firms, so this is not a randomized attention treatment; the paper addresses selection with controls and a more comparable subsample. [DellaVigna and Pollet, 2005 working paper, published 2009](https://www.nber.org/papers/w11683.pdf)

**Engine hypothesis:** attention has distinct extensive-margin and processing-speed effects. Measure unique engaged accounts, new-to-topic participants, readership/search changes, announcement congestion, and time to forecast revision. Separate attention volume from message valence. Candidate tests are short-run demand pressure after attention shocks and slower fundamental assimilation under congestion. Failure conditions include real news causing both attention and returns, artificial amplification, information leakage before measured publication, or institutional automation eliminating the delay. Signals must be evaluated after realistic receipt and decision latency; an effect captured before the feed arrives is not an available opportunity.

### 3.4 Extrapolation, diagnostic beliefs, and learning from experience

Greenwood and Shleifer compare six survey measures of return expectations with market history and model-based expected returns. Reported expectations tend to rise after strong markets, while their relation to expected-return proxies is often opposite. This distinguishes what surveyed people expect from the compensation inferred from valuation models; neither is a direct observation of the true future distribution. [Greenwood and Shleifer, 2014](https://scholar.harvard.edu/files/shleifer/files/expectations_of_returns_public._feb_2014_print.pdf)

Bordalo and coauthors model diagnostic expectations as overweighting states made relatively more representative by news, and confront predictions with analyst forecasts, fundamentals, and returns. Importantly, high-growth groups can contain genuinely exceptional future performers even while expectations overstate their prevalence. The model also has acknowledged empirical shortcomings. [Bordalo et al., 2019](https://shleifer.scholars.harvard.edu/sites/g/files/omnuum10626/files/shleifer/files/bordalo_et_al-2019-the_journal_of_finance.pdf)

Malmendier and Nagel relate lifetime market experiences to risk taking and participation using household data and cross-cohort variation with age/year controls. The research is consistent with persistent experience effects, not random assignment of life histories. [Malmendier and Nagel, 2009 working paper, published 2011](https://www.nber.org/papers/w14813.pdf)

**Engine hypothesis:** estimate expectations separately by target and horizon; test forecast revisions against subsequent forecast errors and distinguish genuine fundamental persistence from exaggerated persistence. Track distribution tails, not just average growth. Failure includes regime shifts that make recent observations genuinely more informative, omitted fundamentals, changing survey samples, and analyst incentive distortions. Do not assume all trend-following reflects cognitive bias: it can be a rational policy under an explicit model.

### 3.5 Informational cascades, coordination, and career herding

Bikhchandani, Hirshleifer, and Welch show how sequential agents observing actions rather than underlying signals can rationally stop using their own information. Once choices cease revealing private signals, a long run of agreement need not contain much independent evidence. Cascade fragility is a model prediction conditional on its information structure. [Bikhchandani et al., 1992](https://snap.stanford.edu/class/cs224w-readings/bikhchandani92fads.pdf)

Anderson and Holt test a controlled urn-based sequential prediction environment. Their observed cascade behavior demonstrates a mechanism under known signals and incentives, not the frequency of cascades in modern order books. [Anderson and Holt, 1997](https://econweb.ucsd.edu/~jandreon/Econ264/papers/Holt%20Anderson%20AER%201997.pdf)

Scharfstein and Stein provide a different mechanism: managers may imitate because labor-market reputation makes shared mistakes less revealing of low ability. Similar actions can thus arise from strategic incentives rather than social irrationality. [Scharfstein and Stein, 1990](https://www.hbs.edu/ris/Publication%20Files/Herd%20Behavior%20and%20Investment_1f30fd71-a48f-4751-b267-ba97ec9b6160.pdf)

**Engine hypothesis:** distinguish independent information, copied conclusions, common fundamentals, benchmark mandates, and reputational conformity. Measure source genealogies, quote/repost chains, synchronized revisions, and timing relative to incentives. A thousand articles syndicating one wire are one informational origin, not a thousand confirmations. Potential opportunity arises when a crowd's apparent evidence is fragile and an independently verified contradiction arrives. Failure includes accurate common learning, unobserved independent evidence, endogenous prices that reveal information, or reputational incentives that remain binding after contradiction. Agreement alone supplies neither timing nor direction.

### 3.6 Identity and information segregation

Cookson, Engelberg, and Mullins observe selective exposure on StockTwits: users disproportionately follow others expressing matching stock views. Their within-firm/date and user fixed-effects designs help rule out several common-news and stable-user explanations, but the returns and trading associations are not equivalent to a randomized feed intervention. [Cookson et al., 2022 author version; published 2023](https://willmullins.net/papers/Echo_public_Feb2022.pdf)

Benjamin, Choi, and Strickland use randomized identity salience in laboratory choice tasks. The published findings are not a universal claim that identity primes increase risk taking; notably, the published summary reports no gender-salience effect on intertemporal or risk choices. Retrieved drafts differ, so detailed obsolete group claims are deliberately excluded here. [Published author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC2944260/), [NBER version record](https://www.nber.org/papers/w13309)

**Engine hypothesis:** publicly expressed investment identities—such as commitment to a thesis, community affiliation, or a self-described investment style—can affect information selection and willingness to revise. Use aggregate, consent-compatible behavioral measures: exposure diversity, cross-community transmission, disagreement persistence, and response to disconfirming news. Do not infer sensitive personal identities or hidden mental traits from names or language. An identity-linked position may have nonfinancial utility, but that does not reveal when it will be sold. Failure includes platform-selection bias, bots, performative rhetoric without positions, or capital-weighted behavior diverging from conversation. A useful falsifier is unchanged trading or belief revision despite large measured community shifts.

### 3.7 Narratives are causal models people communicate, not merely positive words

Shiller proposes studying narrative diffusion and uses epidemic models as a framework for propagation, forgetting, and recurrence. The address offers historical interpretation and a research program, not a clean causal estimate of narrative-driven returns. [Shiller, 2017](https://projects.iq.harvard.edu/files/pegroup/files/shiller2017.pdf)

Tetlock constructs a media-pessimism measure from a recurring newspaper column and studies lagged relationships with returns and volume. The paper explicitly discusses the column's timing and its partly retrospective nature. Predictive content does not make every negative article an exogenous market shock. [Tetlock, 2007](https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf)

**Engine hypothesis:** encode a narrative as `{claim, causal link, beneficiary, antagonist/obstacle, horizon, catalyst, falsifier}`, with separate fields for evidence quality and emotional framing. Track new adoption, repetition, mutation, cross-community spread, and abandonment. As a model analogy, `dI/dt = βSI/N − γI` separates propagation from decay; neither β nor γ is known from keyword counts alone. Trade relevance requires an additional path from narrative adoption to spending, financing, demand, or risk bearing. Failure includes mere reporting of a fundamental change, search-interest measurement shifts, overlapping narratives, endogenous selection, or an enduring belief whose mentions fall because it is already common knowledge. Falling attention is not necessarily falling conviction.

### 3.8 Emotions and ambiguity: different mechanisms with different observables

Cohn and coauthors randomly prime financial professionals with boom or bust scenarios while holding the subsequent choice environment fixed, and report increased fear and risk aversion under the bust condition. Additional fear manipulation strengthens the proposed mechanism. This is stronger causal evidence about experimental risk choice than ordinary sentiment-return correlation, but not a market-level elasticity estimate. [Cohn et al., 2015](https://neuroeconomist.net/wp-content/uploads/2015/07/Cohn-et-al-AER-2015.pdf)

Kuhnen and Knutson associate anticipatory neural activity with subsequent financial choices in a controlled task. The neural associations are not evidence that a text model can observe traders' brain states; their optimal-choice benchmark also embeds a rational risk-neutral objective. [Kuhnen and Knutson, 2005](https://web.stanford.edu/~knutson/bad/kuhnen05.pdf)

Ellsberg's argument separates uncertain probabilities from risks with well-specified probabilities. Ambiguity concerns the reliability and adequacy of information, not simply a high variance estimate. The original paper's thought experiments should not be described as a modern randomized market trial. [Ellsberg, 1961](https://sites.socsci.uci.edu/~bskyrms/bio/readings/ellsberg.pdf)

**Engine hypothesis:** distinguish fear about a known adverse distribution from uncertainty about which distribution applies. Candidate measures include explicitly stated forecast ranges, model disagreement, missing information, revisions, and independent survey responses. Option prices contain risk-neutral weights and hedging demand, not pure fear probabilities. Failure includes language-style shifts, rational response to increased background risk, or liquidity changes masquerading as preference changes. The near-term consequence of fear may be lower demand; the longer-term consequence may be higher offered compensation, not a guaranteed immediate reversal.

### 3.9 Institutions, limits to arbitrage, and reflexive amplification

Shleifer and Vishny model specialized arbitrage funded by outside investors. Adverse performance can trigger capital withdrawals precisely when perceived mispricing widens, limiting stabilizing trades. This is a theory of financing and agency, not a license to call every convergence position riskless. [Shleifer and Vishny, 1997](https://web.stanford.edu/~piazzesi/Reading/ShleiferVishny1997.pdf)

Brunnermeier and Pedersen distinguish funding liquidity from market liquidity and derive conditions under which losses and margin changes reinforce one another. The destabilizing result is conditional; collateral rules are not always destabilizing in their model. [Brunnermeier and Pedersen, 2009](https://markus.scholar.princeton.edu/document/98)

**Engine hypothesis:** apparent panic is amplified when leveraged holders, correlated collateral, short financing horizons, and weak liquidity coincide. Track verified margin changes, financing spreads, redemption evidence, market depth, borrowing availability, and liquidation-related flows separately from emotional language. “Reflexivity” should mean a specified feedback loop—price changes affect collateral or business financing, which alters actions or fundamentals—not an unfalsifiable explanation for any chart.

A candidate contrarian policy supplies liquidity or patient capital only if its own financing survives adverse paths. Failure includes permanent fundamental impairment, withdrawal of the Engine's own capital, unmodeled basis/borrow risk, or capacity too small to absorb impact. A price gap can persist for rational reasons. The risk premium earned for bearing bad-state liquidity risk must not be mislabeled psychological alpha.

### 3.10 Cross-sectional susceptibility and expectations versus surprise

Baker and Wurgler connect broad sentiment proxies to subsequent cross-sectional returns, emphasizing assets whose valuations are subjective and difficult to arbitrage. Their composite includes market and issuance variables; it is not a direct psychological survey, and orthogonalization against selected macroeconomic variables cannot eliminate every rational explanation. [Baker and Wurgler, 2006](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.00885.x)

Bernanke and Kuttner separate expected policy changes from surprises using futures data, with explicit attention to timing, outliers, and endogeneity. Their decomposition illustrates why the same announced policy action can produce different price responses. It does not establish a timeless coefficient for modern monetary-policy events. [Bernanke and Kuttner, 2004 working paper, published 2005](https://www.federalreserve.gov/pubs/feds/2004/200416/200416pap.pdf)

**Engine hypothesis:** use surprise relative to a timestamped prior distribution, not absolute news tone. A standardized surprise can be written `z=(realization−prior mean)/prior standard deviation`, but only when comparable units and a meaningful prior dispersion exist. Distinguish survey disagreement from uncertainty of an individual forecast. A favorable outcome can disappoint an even more favorable prior; the price response also depends on positioning, risk premiums, and implications for other variables. Failure includes stale consensus, revisions, information leakage, prior-distribution misspecification, and the use of prices themselves to construct a circular “surprise.”

## 4. Interaction logic: why opposite predictions can both be plausible

The Engine must not make a mechanism list and vote across it. Several mechanisms are observationally similar but imply different time paths.

**Underreaction followed by overreaction:** one population processes news slowly while another extrapolates a sequence of confirming observations. Immediate continuation and later reversal can coexist without contradiction. The relevant test estimates a response surface over horizons and participant composition, rather than selecting whichever horizon looks best after seeing outcomes.

**Loss aversion versus fear:** being below a reference point can increase willingness to gamble in some choice frames, while a frightening environment can reduce willingness to bear risk. These are not interchangeable predictions. Reference state, available choices, financing constraints, and the elicitation context determine which mechanism is relevant. A single “loss aversion” feature cannot dictate direction.

**Attention versus information:** more coverage can broaden speculative demand, accelerate accurate valuation, or expose previously hidden bad news. The distinction requires content novelty, source quality, participation changes, and the path of fundamental expectations. Treating all increased attention as bullish or all extreme attention as a short signal is mechanically unsound.

**Crowding versus consensus accuracy:** agreement can arise from independent high-quality observations or from repeated copies. Even an accurately informed crowd can become fragile if leverage and exit deadlines align. A crowding warning concerns resilience and possible price impact, not necessarily incorrect beliefs.

**Volatility versus expected return:** a fearful environment can raise the price of insurance and lower risky-asset prices. Compensation for risk may increase after this adjustment, but the transition can continue and realized losses can remain severe. Distinguish level, change, acceleration, and exhaustion in every state variable.

**Retail versus institutions:** these categories are too coarse to be psychological types. Separate discretionary households, informed specialists, systematic funds, liability hedgers, market makers, benchmarked managers, and long-horizon allocators where evidence permits. The same entity can occupy multiple roles. Segment by decision rule, information, financing, and horizon—not stereotypes.

**Timescale:** milliseconds-to-minutes effects require tradable latency and market-microstructure data; days-to-weeks effects require event timing and flow persistence; quarters-to-years effects require valuation, financing, and cohort or institutional changes. A quarterly survey cannot honestly support a millisecond mechanism without another bridge. Match measurement frequency to causal process before modeling.

## 5. Measurement architecture for the Psychology Engine

### 5.1 Observation records before latent scores

Each observation should store original source, immutable content/hash where permitted, event time, publication time, receipt time, version, language, asset mapping, geographic coverage, available population labels, and access limitations. Store the original words or numeric response separately from the model's interpretation. An extracted probability, its target outcome, and its horizon must travel together.

Deduplicate at both document and claim levels. A syndicated article, a quote of that article, and a social reaction to the quote are different diffusion events but may share one factual origin. Maintain this graph so information novelty and attention propagation can be measured independently.

Preserve missingness rather than silently imputing sentiment. No public posts can mean no interest, privacy, platform outage, deletion, or unavailable access. Record the coverage denominator: observed messages are not all investors. Track platform rules, data vendors, extraction models, and language coverage because measurement shifts can resemble market regime changes.

### 5.2 Separate descriptive, inferred, and predictive outputs

**Descriptive:** observed bullish/bearish declarations, forecast distributions, publication counts, quote concentration, measured flows, verified collateral changes.

**Inferred:** estimated attention, narrative adoption, belief persistence, or constraint tightness, with measurement uncertainty and alternative explanations.

**Predictive:** a distribution over specified future outcomes conditional on information available now.

**Decision:** whether any feasible action improves net portfolio outcomes relative to a benchmark.

Never let a descriptive observation bypass the inference and validation layers. An LLM's fluent explanation does not upgrade an inferred state to a measured fact.

### 5.3 Latent-state models are optional, not magic

A possible state-space representation is:

\[
Z_t=f(Z_{t-1},X_t)+\eta_t,\qquad O_t=h(Z_t,X_t)+\epsilon_t.
\]

Here Z contains latent behavioral and institutional states, O contains observations, and X contains measured fundamentals and market conditions. Both transition and observation errors matter. Identifiability requires multiple informative channels or credible restrictions; fitting a hidden state to returns and naming it “fear” does not validate that name. Start with transparent features and regularized baselines. Adopt complex latent models only when they improve held-out calibration, interpretation stability, or decisions.

For network inputs, estimate dependence explicitly. Ten highly correlated commentators should not shrink uncertainty as if they were ten independent witnesses. For forecasts, retain disagreement across models and populations rather than washing it out into a mean. For text, validate negation, sarcasm, quotations, conditional statements, target entity, and whether the author describes their own view or another person's.

### 5.4 The output contract

Every research signal should contain:

- Asset/universe, decision timestamp, intended horizon, and evidence-stage label.
- Observed change, plausible participant segment, and hypothesized causal mechanism.
- Alternative explanation and the observable distinction between the two.
- Conditional outcome distribution, uncertainty, and baseline forecast.
- Expected available capture window and realistic transaction/financing costs.
- Relevant tail states, crowding, capacity, and invalidation conditions.
- A permitted conclusion: observe, investigate, maintain baseline, or advance to a specified validation stage.

The Engine is permitted to say **unidentified**. That is often the correct conclusion when sentiment, fundamentals, and liquidity all move simultaneously. Unidentified cause does not forbid predictive research, but it changes what can be claimed and how fragile extrapolation may be.

## 6. A falsifiable research program

### Experiment A: sentiment's incremental information

**Question:** Do behavioral features improve forecasts beyond price, volatility, liquidity, and timestamped fundamentals?

Freeze an asset universe and outcome horizon. Build a baseline using only market/fundamental variables, then add one feature family at a time. Fit preprocessing and extraction calibration only on training periods. Use chronological splits, event-level clustering, and purging where labels overlap. Compare probability calibration and proper scores as well as implementation-aware outcomes. Report the incremental effect with uncertainty, not only the full model's performance.

**Falsifier:** improvement disappears with timestamp corrections, source deduplication, costs, a later untouched period, or a stronger simple baseline. If a social feature adds only a delayed echo of price, it may be useful descriptively but has not established new tradable information.

### Experiment B: attention pressure versus fundamental information

**Question:** Does an attention shock change participation or order flow after conditioning on the information event?

Separate new factual disclosures from repetition and unrelated visibility. Use prespecified matched event cohorts; where legitimately available, evaluate plausibly exogenous attention variation and inspect pre-trends. Outcomes include new participant share, buy/sell imbalance, liquidity, and subsequent reversal versus continued fundamental revisions. Negative controls can include unrelated assets and content published after the measured response.

**Falsifier:** there is no participation/flow bridge, the response precedes exposure, or all effects are explained by information novelty. A regression on volume alone is insufficient because volume can be both an attention proxy and an endogenous response.

### Experiment C: belief updating and forecast-error structure

**Question:** Do specific populations systematically underreact or overreact to identifiable news?

Collect repeated forecasts for the same target and horizon. Estimate revisions conditional on publicly available information, then compare later errors against earlier revisions. Keep forecast-target changes and selection into issuing a forecast explicit. Contrast a transparent Bayesian or statistical updating benchmark with flexible alternatives. Analyze the distribution of exceptional outcomes rather than assuming every optimistic forecast is false.

**Falsifier:** predictability vanishes after target alignment, revised-data corrections, or controls for incentives and genuine persistence. A rational model is a comparator under assumptions, not an oracle of true probabilities.

### Experiment D: narrative diffusion versus copied evidence

**Question:** Does cross-community adoption add information about future flows or fundamentals beyond raw mention counts?

Pre-register narrative definitions and a human-audited extraction sample. Compare unique origins, community breadth, conversion of neutral participants, and source diversity. Evaluate diffusion measures against simple counts and price trends. A narrative model must forecast a specific intervening behavior—capital raising, purchases, portfolio demand, or forecast revisions—before claiming a path to prices.

**Falsifier:** performance is driven by one platform, one memorable episode, post hoc story labels, or duplicated content. If conversation spreads without a measurable decision response, the economic mechanism remains unestablished.

### Experiment E: sentiment under constrained intermediation

**Question:** Is negative sentiment more persistent or economically consequential when funding and liquidity are tight?

Specify an interaction between measured sentiment changes and independently measured constraint variables. Compare continuation, reversal, liquidity deterioration, and financing costs across states. Distinguish forecasting a price move from earning compensation by supplying liquidity. Simulate margin calls, borrow changes, correlated losses, and exit liquidity for any proposed position.

**Falsifier:** the sentiment variable adds nothing after constraints, apparent profits are merely uncompensated crash exposure, or the position cannot survive the path required for eventual convergence. A compelling terminal valuation does not make interim funding irrelevant.

### Experiment F: the Engine's own psychological failure modes

The system is itself exposed to confirmation and narrative-selection errors. Maintain a hypothesis registry, record failed variants, freeze evaluation windows, and require competing accounts before reviewing outcomes. Keep research explanations separate from execution authority. Evaluate whether a second agent contributes independent evidence or merely restates the same source. Deliberately test contradictory cases: positive tone with falling expectations, negative tone with improving cash flows, rising engagement with no orders, and confident language from genuinely accurate forecasters.

**Falsifier:** explanations remain equally persuasive after asset names or outcome directions are swapped, or the system cannot state what evidence would change its conclusion. Such a model is producing stories, not a discriminating theory.

### Economic promotion criteria

Advance from hypothesis to retrospective support, then untouched out-of-sample support, then forward simulation. Promotion requires enough independent opportunities to resolve economically meaningful uncertainty, not an arbitrary universal trade count. Evaluate costs, slippage, borrow, funding, adverse selection, tails, and overlap with the existing portfolio. A higher hit rate or attractive gross Sharpe is insufficient. Research here authorizes no real-money deployment.

## 7. Compact evidence ledger

The JSON companion records exact URLs, read scope, version, design class, and limitations. The table below summarizes the epistemic boundary; “read” means the relevant sections inspected, not a claim to have read every appendix or all subsequent literature.

| ID | Primary work | Evidence class and usable lesson | Main limitation |
|---|---|---|---|
| B01 | Kahneman–Tversky 1979 | Choice evidence/theory: reference coding and decision weighting | Not an aggregate-price model |
| B02 | Odean 1998 | Account records: asymmetric gain/loss realization | Motive not uniquely identified |
| B03 | Barber–Odean 2000 | Account records: turnover and net performance | Historical sample; indirect overconfidence evidence |
| B04 | Barber–Odean 2008 | Account/order evidence: attention-related buying | Attention proxies are endogenous |
| B05 | DellaVigna–Pollet 2009 | Event comparison: delayed information response | Selected announcement timing; working version read |
| B06 | Greenwood–Shleifer 2014 | Survey/time-series evidence: expectations differ from return proxies | Respondent and model dependence |
| B07 | Bordalo et al. 2019 | Formal model plus analyst/fundamental tests | Not randomized; incomplete model fit |
| B08 | Malmendier–Nagel 2011 | Household/cohort evidence: experience-related risk taking | Life experiences not randomized |
| B09 | Bikhchandani et al. 1992 | Theory: action imitation can suppress information | Specific sequential-information assumptions |
| B10 | Anderson–Holt 1997 | Controlled laboratory cascade evidence | Limited bridge to continuous-price markets |
| B11 | Scharfstein–Stein 1990 | Theory: reputational herding | Prevalence requires separate evidence |
| B12 | Cookson et al. 2023 | Social-network evidence: selective exposure | Platform selection and endogenous networks |
| B13 | Tetlock 2007 | Text/time-series evidence: media and market interaction | Feedback and publication timing |
| B14 | Shiller 2017 | Framework/historical synthesis: narrative diffusion | Not identified return causality |
| B15 | Cohn et al. 2015 | Randomized priming/fear experiments | Experimental treatment differs from full market crisis |
| B16 | Kuhnen–Knutson 2005 | Neural/choice association in controlled task | No text-to-brain inference; benchmark dependence |
| B17 | Ellsberg 1961 | Decision-theoretic counterexample and informal evidence | Not a contemporary randomized trial |
| B18 | Benjamin et al. 2010 | Randomized identity-salience choice experiments | Version discrepancy; context-specific findings |
| B19 | Baker–Wurgler 2006 | Composite-proxy/cross-sectional evidence | Sentiment not directly observed |
| B20 | Shleifer–Vishny 1997 | Theory: delegated capital limits convergence | Assumptions determine amplification |
| B21 | Brunnermeier–Pedersen 2009 | Theory: funding/market-liquidity feedback | Destabilizing margins are conditional |
| B22 | Bernanke–Kuttner 2005 | Futures-surprise event study and decomposition | Endogeneity/outliers; historical policy regime |

## 8. Research boundaries and next decision

This report deliberately does not claim complete coverage of cross-cultural finance, developmental psychology, sleep and physiology, clinical conditions, deception, all asset classes, or every replication dispute. Nor does it diagnose individual traders. Those topics require separate evidence selection and are not interchangeable with an operational market signal. The strongest inference available here is that psychological mechanisms are plural, heterogeneous, and mediated by institutions.

Several technical retrieval limits occurred: a Harvard repository returned a rate-limit error; an NBER information-rigidity landing page returned a forbidden response; a PMC direct page presented a browser challenge. No challenge was bypassed. Public author/working-paper sources and indexed published text were used where available, with limitations recorded. The NBER identity-paper endpoint inconsistently exposed older and newer versions; detailed superseded findings were not used. Coibion–Gorodnichenko was considered but is not counted in the core ledger because the relevant full-text sections were not inspected in this pass.

**Highest-value next action:** create a small point-in-time event corpus with verified priors, information novelty, participant/flow proxies, and funding/liquidity context. Run Experiment A with prespecified ablations before building a single composite psychology score. The first success criterion is not profit or an impressive dashboard: it is evidence that a precisely defined behavioral observation improves an independently evaluated forecast or decision beyond a credible baseline.
