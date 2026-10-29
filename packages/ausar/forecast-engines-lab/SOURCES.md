# Research sources

These sources inform validation and data-timing requirements. They do not validate the 30 formulas in this package.

## Silicon and linked research

- Silicon current REA convergence: `research/rea-teardowns/synthesis/CONVERGENCE-ENGINE-2026-10-28.md`.
- Silicon second-pass cross-vendor synthesis: `research/rea-teardowns/synthesis/SECOND-PASS-2026-10-27.md`.
- Silicon Gestalt / convergence limitations: `research/rea-teardowns/synthesis/GESTALT-2026-10-27.md`.
- Silicon Saty public-source research: `research/saty_mahajan/README.md`, `START_HERE.md`, `ALGORITHM_SPEC.md`.
- Femto forecasts, eyes, Gestalt, edge-audit, and source-dated research branches are summarized in `TRACEABILITY.md`; their output is exploratory research rather than independent validation of these engines.
- TheStrat's local public-only teardown files are described in `TRACEABILITY.md`; no gated product materials are used.

## Statistical validation and trading process

- Campbell R. Harvey, Yan Liu, and Heqing Zhu, “...and the Cross-Section of Expected Returns,” NBER Working Paper 20592. Multiple testing changes the evidentiary bar for new factors. [NBER](https://www.nber.org/papers/w20592)
- David H. Bailey and Marcos López de Prado, “The Deflated Sharpe Ratio.” Selection bias and non-normality matter when ranking many trials. [Author-hosted paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- CFA Institute interview with Jack Schwager: fit, discipline, exits, risk control, and evidence of an edge. [CFA Institute](https://blogs.cfainstitute.org/blog/2014/04/16/what-makes-a-great-trader-an-interview-with-jack-schwager/)
- Edward O. Thorp's Kelly-criterion papers: optimal growth sizing can carry severe drawdown/ruin risk; this package therefore does not size positions. [Thorp archive](https://www.edwardothorp.com/articles/) and [paper PDF](https://www.edwardothorp.com/wp-content/uploads/2016/11/TheKellyCriterionAndTheStockMarket.pdf)
- Cont, Kukanov, and Stoikov, “The Price Impact of Order Book Events.” Order-flow imbalance is interpreted jointly with depth and market mechanics, not as raw trade volume. [arXiv](https://arxiv.org/abs/1011.6402)

## Point-in-time data and market-data boundaries

- SEC EDGAR APIs: filing/submission and XBRL access; accession and filing timestamps support point-in-time handling. [SEC](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- FRED real-time periods and ALFRED: vintage and revision-aware macro series. [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html), [ALFRED](https://fred.stlouisfed.org/docs/api/fred/alfred.html)
- CFTC COT release schedule: use the schedule actually in force for each historical observation. [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm)
- CFTC COT timing FAQ and release schedule: published position snapshots are generally as of the preceding Tuesday and released Friday at 3:30 p.m. ET; holidays can move dates. [CFTC COT FAQ](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) and [release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm)
- CFTC announcement, October 27, 2026: planned move to twice-weekly publication by year-end, with Monday data planned for Wednesday and Wednesday data for Friday. This is a planned transition; verify actual effective dates before changing the source clock. [CFTC announcement](https://www.cftc.gov/PressRoom/PressReleases/9316-26)
- FINRA short-interest reporting cadence and publication dates. Short interest is a periodic position snapshot, not daily short-sale volume; the two should not be substituted for one another. Rights and permitted model use must be reviewed before using any FINRA-sourced dataset. [FINRA reporting schedule](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest) and [FINRA: Short Interest—What It Is, What It Is Not](https://syndication.finra.org/content/short-interest-what-it-what-it-not)
- Options Industry Council FAQ: open interest describes matched outstanding contracts and is not a directional/dealer-side measure. [OIC](https://www.optionseducation.org/referencelibrary/faq/general-information)
- Cboe auction-process and depth/PITCH specifications: exchange-specific feeds are distinct entitlements. [Auction process](https://www.cboe.com/document/tech-spec/document/technical-specifications/cboe-titanium-u.s.-equities-auction-process), [PITCH specification](https://www.cboe.com/document/tech-spec/document/technical-specifications/cboe-titanium-u.s.-equities-tcp-depth-of-book-pitch-specification)

## Third-pass repository design sources

These official repository sources were used to compare system architecture. Repository descriptions and casebooks are implementation evidence, not proof of predictive performance.

- [TradingAgents README](https://github.com/TauricResearch/TradingAgents/blob/main/README.md): specialist analyst/researcher/trader/risk roles. Used to separate hypothesis generation from evidence lineage and risk approval.
- [OpenBB platform core](https://github.com/openbq-org/OpenBB/blob/develop/openbb_platform/core/README.md): extension and provider architecture. Used as a model for adapters that retain provider identity, field definition, timestamps, and rights rather than treating normalized outputs as interchangeable.
- [AI Hedge Fund README](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/README.md): point-in-time advance path, missing-data handling, and append-only portfolio records. Used for deterministic boundaries between research outputs and later actions.
- [Freqtrade backtesting guide](https://github.com/freqtrade/freqtrade/blob/develop/docs/backtesting.md): backtest assumptions and lookahead analysis. Used to require executable marks, no-fill handling, and frozen timing assumptions in each Edge card.
- [Microsoft Qlib workflow guide](https://github.com/microsoft/qlib/blob/main/docs/component/workflow.rst): explicit workflow segments and artifact recording. Used to require time-separated evaluation and complete trial records.
- [NautilusTrader reconciliation guide](https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/concepts/execution/reconciliation.md) and [event documentation](https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/concepts/events/index.md): event-driven order/fill/position cache and reconciliation concepts. Used to keep forecast IDs separate from any future order/position ownership state.
- [Microsoft RD-Agent README](https://github.com/microsoft/RD-Agent/blob/main/README.md): research/development agent workflow. Used to count generated variants as searched hypotheses rather than independent evidence.
- [Vibe-Trading release history](https://github.com/HKUDS/Vibe-Trading/releases), [agent skill](https://github.com/HKUDS/Vibe-Trading/blob/main/agent/SKILL.md), [data routing skill](https://github.com/HKUDS/Vibe-Trading/blob/main/agent/src/skills/data-routing/SKILL.md), and [execution model skill](https://github.com/HKUDS/Vibe-Trading/blob/main/agent/src/skills/execution-model/SKILL.md): versioned research tools, paper simulation, connector profiles, and market-data routing. Used to distinguish brokerless paper matching from a separately configured broker connector and to preserve explicit operator limits.
- [Edge Trading Edge Lab README](https://github.com/dwj9ddyvf6-hub/Edge), [research protocol](https://github.com/dwj9ddyvf6-hub/Edge/blob/main/skills/engineer-trading-edge/references/research-protocol.md), and [field casebook](https://github.com/dwj9ddyvf6-hub/Edge/blob/main/skills/engineer-trading-edge/references/field-casebook.md): payer/transfer/bad-state/holdability/execution-net ledger, pre-registration, and declared experiments. Its own README says its cases do not show that a strategy is profitable. Applied to the 30 cards without importing its outcomes as evidence.
- Separate public-source TheStrat extraction: [pinned public teardown repository](https://github.com/dwj9ddyvf6-hub/thestrat-ai-public-teardown/tree/3e0cb192cda3a5e88d6bea48edaeda4b65959727). The relevant extracted file inventory and unresolved trigger semantics are recorded in [CORPUS_AUDIT.md](CORPUS_AUDIT.md); this feature branch has no local copy of that separate checkout.

## Forecast selection and refresh research

- Raffaella Giacomini and Halbert White, conditional predictive ability. Supports comparing forecasts conditionally on information available at the decision time rather than selecting one unconditional winner. [Econometrica](https://onlinelibrary.wiley.com/doi/10.1111/j.1468-0262.2006.00718.x)
- Isaac Gibbs and Emmanuel Candès, adaptive conformal inference under distribution shift. The source-refresh tool is deliberately not an application of this method; the work motivates treating regime/source change as a rolling process and keeping coverage claims empirical to their conditions. [arXiv](https://arxiv.org/abs/2106.00170)
- Forecast combination literature emphasizes dependence and forecast coherence; repeated inputs should not be counted as independent votes. [Forecast combination and coherence](https://www.sciencedirect.com/science/article/pii/S0169207018301869)

## Practitioner research translated into design rules

- Jim Simons, first-person Science Lives interview: discusses the search for predictors independent of existing ones and the intellectual work in modeling costs. The collision map and execution-net fields apply those two ideas directly. [Interview transcript](https://www.bishoprockcap.com/assets/library/jim-simons/December%202025%20Jim%20Simons%20-%20Science%20Lives%20Interview%20(transcript))
- George Soros, *General Theory of Reflexivity* lecture transcript: participants' beliefs can alter the conditions they observe. FE24 and FE26 therefore treat crowd positioning and anticipated index demand as feedback into the price effect, rather than fixed exogenous predictors. [Open Society Foundations transcript](https://www.opensocietyfoundations.org/uploads/9ae17912-2262-4646-8ffc-d01afc934c36/george-soros-general-theory-of-reflexivity-transcript.pdf)
- Edward O. Thorp, work on Kelly sizing and quantitative investing: estimation error and ruin risk constrain how an observed edge can be held. The cards therefore require loss path, capacity, and adverse-state analysis before any sizing discussion. [Thorp's papers and archive](https://www.edwardothorp.com/articles/)
- Jack Schwager's trader interviews and CFA Institute discussion emphasize differing trader styles but recurring discipline and risk control. They inform the kill-rule and drawdown language, not a ranking model. [CFA Institute interview](https://blogs.cfainstitute.org/blog/2014/04/16/what-makes-a-great-trader-an-interview-with-jack-schwager/)

The repository links above are primary project or paper sources. The dated branch SHAs, local reports, and exact scope notes remain in `CORPUS_AUDIT.md` and `TRACEABILITY.md` so future refreshes can detect source drift.

## Fourth-pass source review

- Freqtrade official docs: [lookahead analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/) and [recursive analysis](https://www.freqtrade.io/en/latest/recursive-analysis/). They describe separate checks for future leakage and feature sensitivity to startup-history length.
- NautilusTrader official docs: [execution reconciliation](https://nautilustrader.io/docs/latest/concepts/execution/reconciliation/), [backtest event flow](https://nautilustrader.io/docs/latest/concepts/backtesting/execution-flow/), [fill prices and matching](https://nautilustrader.io/docs/nightly/concepts/backtesting/fill-prices-and-matching/), and [event sourcing](https://nautilustrader.io/docs/latest/concepts/event_sourcing/). These keep historical market data, simulated fills, and reconciled positions distinct.
- OpenBB official docs: [V5 provider extensions](https://docs.openbb.co/odp/python/extensions/providers) and [provider FAQ](https://docs.openbb.co/odp/python/faqs/data_providers). Provider coverage and source access remain package/provider-specific.
- Microsoft Qlib [workflow guide](https://qlib.readthedocs.io/en/latest/component/workflow.html) records handler fit windows and dataset segments as part of experiment configuration.
- Microsoft [RD-Agent repository](https://github.com/microsoft/RD-Agent) and [R&D-Agent-Quant paper](https://arxiv.org/abs/2505.15155) describe iterative factor/model research; generated variants remain part of one declared search family.
- Thomson et al., [Combining Forecasts: Performance and Coherence](https://doi.org/10.1016/j.ijforecast.2018.10.006), analyze how forecast dependence affects combination coherence. This supports exposing lineage edges while leaving realized error correlation as a separate empirical calculation.

## Fifth-pass source review

- El-Yaniv and Wiener, [On the Foundations of Noise-free Selective Classification](https://jmlr.org/papers/v11/el-yaniv10a.html), formalize the risk-coverage tradeoff when a predictor can reject uncertain cases.
- Gangrade, Kag, and Saligrama, [Selective Classification via One-Sided Prediction](https://proceedings.mlr.press/v130/gangrade21a.html), study coverage and one-sided empirical risk for abstaining classifiers. The forecast-lab audit borrows the coverage framing but does not implement their learning procedure or claim its guarantees.

## Sixth-pass source review

- Diebold and Mariano, [Comparing Predictive Accuracy](https://doi.org/10.1080/07350015.1995.10524599), allow forecast-loss differences to be serially and contemporaneously correlated. This motivates measuring repeated horizon exposure before interpreting per-row forecast comparisons; the new diagnostic does not implement their test.
- Hansen and Hodrick, [Forward Exchange Rates as Optimal Predictors of Future Spot Rates](https://www.journals.uchicago.edu/doi/pdf/10.1086/260910), analyze inference when observations are sampled more finely than the forecast interval. This motivates explicit realized-window geometry; the overlap audit is descriptive and does not reproduce their estimator.

## Seventh-pass source review

- Gneiting and Raftery, [Strictly Proper Scoring Rules, Prediction, and Estimation](https://doi.org/10.1198/016214506000001437), formalize scoring a predictive distribution against its realized observation. This motivates freezing one estimand and endpoint per forecast; the target hashes and label-window enforcement are local engineering choices, not procedures proposed by the paper.

## Eighth-pass source review

- Center for Research in Security Prices, [Calculations and Index Methodologies](https://www.crsp.org/wp-content/uploads/guides/CRSP_Calculations_and_Index_Methodologies.pdf), documents return and distribution calculations and corporate-action flags. It motivates freezing the measurement and adjustment basis of a realized outcome.
- Federal Reserve Bank of St. Louis, [ALFRED overview](https://fred.stlouisfed.org/docs/api/fred/alfred.html) and [series observations API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html), describe retrieving observations as they existed on historical vintage dates. This motivates a versioned data-vintage policy for revised series.
- Nasdaq Trader, [Trading Calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar), publishes holidays and early-close notices. This motivates a calendar identifier when a target endpoint is session-based.

See [EIGHTH_PASS_AUDIT.md](EIGHTH_PASS_AUDIT.md) for the finding and implementation. These sources motivate the convention fields; they do not prescribe the local label-context schema or its hash protocol.

## Reading rules

Research papers and official source documentation are preferred to vendor marketing. Vendor statements found in REA reports are treated as statements made by the vendor, not facts about predictive performance. This package makes no OPRA bypass, scraping of gated interfaces, or reuse of proprietary vendor code/data.
