"""Edge-ledger blueprints for the 30 forecast hypotheses.

These records are research contracts: each names a transfer mechanism, payer
hypothesis, baseline, target, bad state, and falsifier before any return claim.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class EdgeCard:
    engine_id: str
    edge_source: str
    novel_mechanism: str
    target_definition: str
    price_aware_baseline: str
    payer_hypothesis: str
    scarcity_or_transfer: str
    bad_state: str
    holdability_and_co_losses: str
    execution_net: str
    decisive_test: str
    kill_rule: str
    source_refs: tuple[str, ...]
    status: str = "HYPOTHESIS"


_REPORT = "research/rea_teardowns/targets/"
_CORPUS_AUDIT = "research/forecast_engines/CORPUS_AUDIT.md"
_TRACEABILITY = "research/forecast_engines/TRACEABILITY.md"


EDGE_CARDS: tuple[EdgeCard, ...] = (
    EdgeCard(
        "FE01", "accuracy",
        "Blend 21-, 63-, and 252-session return orientation, then shrink the signed return score when path efficiency is weak or volatility is elevated.",
        "Benchmark-adjusted return from as_of to the selected fixed session close.",
        "Same-name drift, ATR-matched names, and a frozen 21/63/252-day trend rule.",
        "Hypothesis: scheduled allocators and late rebalancers pay for continuation that survives pullbacks.",
        "No access edge claimed; value must come from path geometry beyond price trend and realized volatility.",
        "Gap reversal, bear-rally failure, or volatility expansion that crosses the invalidation barrier first.",
        "Record maximum adverse excursion and time-to-exit; aggregate loss with every trend sleeve.",
        "Next-open marks, actual spread/impact at intended size, borrow, fees, and delay capture.",
        "Freeze the benchmark-adjusted return window; issuer-clustered walk-forward against drift and trend baselines. Score first-passage barriers only as a separately named secondary outcome.",
        "Retire if the holdout adds no net decision value over the simple trend baseline or reverses sign.",
        (_REPORT + "saty-ecosystem.md", _REPORT + "trendspider.md"),
    ),
    EdgeCard(
        "FE02", "accuracy",
        "Fade a residual only when supplied Hurst and trend features indicate a range; suppress the reversion score as trend strength or volatility rises.",
        "Residual spread return from as_of to the selected fixed session close.",
        "Same-name residual history, sector-adjusted return, and a no-trade rule during trend acceleration.",
        "Hypothesis: liquidity providers and benchmark rebalancers supply the opposing flow.",
        "Potential accuracy only when residual dislocation remains after common-factor and event information.",
        "A genuine repricing, constituent event, borrow squeeze, or trend regime that makes the old mean irrelevant.",
        "Require borrow and exit-depth stress; count correlated pair/sleeve losses as one book risk.",
        "Enter at next executable mark; charge both legs, borrow, turnover, impact, and failed convergence.",
        "Freeze the residual-return endpoint and benchmark; compare its forecast to AR(1), sector-adjusted, and no-trade baselines. Score convergence-before-break separately.",
        "Retire after two consecutive out-of-sample windows with no incremental residual-return value over the frozen AR(1)/sector baselines or with persistent sign instability.",
        (_REPORT + "market-chameleon.md", _REPORT + "stock-rover.md"),
    ),
    EdgeCard(
        "FE03", "accuracy",
        "Model acceptance as a dwell-time process: a level is accepted only if price remains beyond it while participation and depth survive.",
        "Underlying return from the pre-cutoff breakout reference to the selected fixed session close.",
        "A simple close-above-range rule conditioned on the same symbol's volatility and market direction.",
        "Hypothesis: delayed discretionary entrants pay for evidence that the move has survived its first supply test.",
        "Potential accuracy from the sequence after the trigger, not from another indicator label.",
        "Thin-market wick, opening gap, scheduled news, or high-volume exhaustion.",
        "Measure the adverse excursion before acceptance; overlap with trend, gap, and small-cap warning sleeves.",
        "Score next-bar entry, unfilled opportunities, spread, adverse markouts, and capacity by dollar-volume tier.",
        "Freeze the pre-cutoff breakout reference and return endpoint; compare return forecasts to a level-only baseline under matched volatility/session controls. Keep acceptance/failure events separate.",
        "Kill if the return forecast adds no value over the level-only baseline or if apparent skill is confined to an illiquid size tier; score acceptance events separately.",
        (_REPORT + "saty-ecosystem.md", _REPORT + "tradingview-desktop.md", _CORPUS_AUDIT, _TRACEABILITY),
    ),
    EdgeCard(
        "FE04", "accuracy",
        "Decompose the opening gap into market, sector, after-hours, and issuer residual components, then forecast the residual's auction-to-open resolution path.",
        "Opening-gap residual return from the declared open reference to the selected intraday/session endpoint.",
        "Index/sector gap, same-name overnight volatility, and a plain opening-gap reversal baseline.",
        "Hypothesis: overnight risk transfer and scheduled opening orders create a temporary price concession.",
        "Potential edge is a correct information decomposition before the first liquid price discovery, not gap size alone.",
        "Material news revision, halt, stale premarket quote, or ambiguous session anchor.",
        "Bound gap-tail loss and overnight inventory; co-loss with index-flow and event sleeves.",
        "Use first executable post-open quote; include auction slippage, spread widening, halts, and no-fill cash.",
        "Pre-register event clocks and gap decomposition; next-open replay with matched index/sector controls.",
        "Retire if the residual fails to beat the market-plus-sector baseline or trigger semantics are unresolved.",
        (_REPORT + "saty-ecosystem.md", _REPORT + "trade-ideas.md", _CORPUS_AUDIT, _TRACEABILITY),
    ),
    EdgeCard(
        "FE05", "accuracy",
        "Combine point-in-time breadth participation, advance/decline, new-high/low, and index trend into a directional index-return score.",
        "Index return relative to the predeclared market benchmark from as_of to the selected fixed session close.",
        "Index return, volatility, and equal-weight/cap-weight spread without a breadth overlay.",
        "Hypothesis: benchmark-tracking flows pay when leadership broadens or narrows faster than their rebalance schedule.",
        "Potential accuracy from hidden concentration in the index move, not breadth indicators counted as independent votes.",
        "Constituent changes, stale membership, mega-cap event, or breadth data with uneven timestamps.",
        "Co-loss with trend and sector rotation; stress concentration in a few names and rebalance turnover.",
        "Next-session marks with constituent spreads, index/basket basis, and rebalance impact.",
        "Use point-in-time membership and issuer-clustered dates; score benchmark-relative index return, with equal-weight/cap-weight spread as a predictor and baseline control.",
        "Kill if improvement disappears after membership, sector, and mega-cap controls or if the sign is era-specific.",
        (_REPORT + "finviz-screener.md", _REPORT + "trendspider.md"),
    ),
    EdgeCard(
        "FE06", "accuracy",
        "Combine sector momentum rank, sector flow, and leadership breadth; attenuate the score when cross-sector dispersion is elevated.",
        "Sector return relative to the predeclared benchmark from as_of to the selected fixed session close.",
        "Sector momentum rank and market beta with point-in-time sector membership.",
        "Hypothesis: benchmark managers and thematic allocators trade the lag between leadership evidence and scheduled review.",
        "Potential accuracy from transition timing and diffusion breadth beyond a sector momentum score.",
        "One-stock sector concentration, macro shock, classification change, or common-factor reversal.",
        "Track sector overlap and joint drawdowns; cap concentration and count each issuer once.",
        "Net long/short basket returns at next executable marks with turnover, borrow, and rebalance costs.",
        "Freeze sector membership, benchmark, and return endpoint; compare sector-relative return forecasts to momentum-only and equal-weight sector baselines. Score handoff events separately.",
        "Retire if transition forecasts do not improve rank/log score and net spreads in the untouched era.",
        (_REPORT + "finviz-screener.md", _REPORT + "stock-rover.md"),
    ),
    EdgeCard(
        "FE07", "speed",
        "Treat cross-asset links as expiring edges: a leader matters only when its impulse reaches the follower before the follower's own price absorbs it.",
        "Follower residual return at the single selected lag endpoint, using a predeclared leader/follower pair.",
        "Follower's own lagged return, common-index return, and a no-edge model.",
        "Hypothesis: slower-market hedgers and cross-market rebalancers transfer information with measurable delay.",
        "Speed is only present if lead time exceeds data-arrival, compute, and order latency; public co-movement alone is not access.",
        "Clock skew, venue outage, macro release, or a correlation break that reverses the edge.",
        "Shared macro/market beta creates co-loss with trend, rates, and crypto sleeves; measure cluster loss.",
        "Replay deliberate delays and next-executable marks; include feed latency, spread, market impact, and missed fills.",
        "Freeze one leader/follower pair and lag endpoint; compare follower residual-return loss to follower-only and zero-lag baselines with block-bootstrap uncertainty.",
        "Kill at rolling sign instability, no improvement over follower-only baseline, or edge capture erased by realistic delay.",
        (_REPORT + "quant-data.md", _REPORT + "unusual-whales-original.md"),
    ),
    EdgeCard(
        "FE08", "accuracy",
        "Forecast realized variance as a scale-invariant surface across 1-, 5-, and 22-session components, then check if the forecast survives sampling-clock changes.",
        "Realized variance accumulated over the selected fixed session window, with a frozen sampling and adjustment rule.",
        "Symbol's own HAR(1,5,22) history, current implied variance, and unconditional variance.",
        "Hypothesis: option sellers and risk-budget allocators pay for better second-moment estimates.",
        "Accuracy about risk can improve sizing or pricing, but does not imply return direction or monetizable payoff.",
        "Jump, bad print, corporate action, sampling change, or volatility regime transition.",
        "Model portfolio variance and joint stress with every volatility and tail sleeve; assess funding path.",
        "For any later payoff test, charge real option spread, hedge slippage, theta, and margin funding.",
        "Compare against the stock's own HAR baseline on a frozen next-open sample with QLIKE and interval coverage.",
        "Kill if no incremental variance skill over HAR or the apparent gain depends on a sampling definition.",
        (_REPORT + "squeezemetrics.md", _REPORT + "spotgamma.md"),
    ),
    EdgeCard(
        "FE09", "accuracy",
        "Rank large-move risk from jump intensity, absolute overnight gap, left-tail asymmetry, and event density; the starter score does not separate event causes.",
        "One if absolute return exceeds the predeclared volatility-scaled barrier by the selected window end; otherwise zero.",
        "Same-name overnight gap history, realized-volatility hazard, and event-calendar base rates.",
        "Hypothesis: protection buyers and overnight inventory holders pay to identify concentrated jump windows.",
        "Value is lower tail forecast error or avoided loss beyond the known event schedule, not high AUC alone.",
        "Unannounced news, halt, event-time error, and fat-tail clustering.",
        "Stress overnight liquidation and cross-sleeve gap co-loss; cash/margin must survive the gap.",
        "Score actual next-open liquidation values with wide spreads, halted-name marks, and hedge basis.",
        "Lock the absolute-return barrier and window before cutoff; compare binary event scores to HAR and public-calendar base-rate hazards. Keep cause-specific jump labels separate.",
        "Kill if no calibrated tail-loss reduction versus baseline or labels leak post-event timing.",
        (_REPORT + "optionstrat.md", _REPORT + "squeezemetrics.md"),
    ),
    EdgeCard(
        "FE10", "accuracy",
        "Rank near-term regime-change risk from change-point evidence, vol-of-vol, cross-asset dispersion, and correlation shifts without assigning transition direction.",
        "One if the predeclared volatility/correlation regime transition occurs by the selected window end; otherwise zero.",
        "Fixed rolling-vol/correlation threshold and current regime persistence.",
        "Hypothesis: risk-budget committees pay for earlier evidence that diversification is about to fail.",
        "Potential accuracy is warning lead time beyond a static threshold; no market-access claim.",
        "False transition alarms, clustered shocks, or repeated state flips.",
        "Measure margin and joint book losses in transition states; volatility, options, and trend sleeves co-load.",
        "Measure alert value as avoided loss net of de-risk turnover, hedge cost, and whipsaw.",
        "Freeze the binary transition criterion and horizon; compare event ranking and false-alarm burden to fixed rolling-volatility/correlation thresholds. Score transition direction separately.",
        "Retire if warning lead vanishes after false alarms and transaction costs or is driven by one crisis.",
        (_REPORT + "squeezemetrics.md", _REPORT + "spotgamma.md"),
    ),
    EdgeCard(
        "FE11", "speed",
        "Orient the close-to-next-open score with auction imbalance and rebalance flow, then shrink it for unreliable imbalance data or unusually deep closing liquidity.",
        "Close-to-next-open return for the declared instrument and venue session.",
        "Closing price, prior auction imbalance, index-flow calendar, and simple close-to-open drift.",
        "Hypothesis: benchmark funds with fixed closing deadlines transfer a temporary liquidity premium.",
        "The imbalance snapshot must arrive before the venue cutoff; this scorer uses a snapshot and does not estimate revision velocity.",
        "Auction imbalance cancellation, venue-specific rule change, stale feed, or index rebalance.",
        "Inventory is overnight and can gap; aggregate with index flow and gap exposure.",
        "Auction order type, queue priority, imbalance cutoff, partial fill, and next-open exit all enter net value.",
        "Use entitled timestamped auction data; compare next-open return error for the weighted imbalance/rebalance score against an imbalance-only baseline at the actual decision cutoff.",
        "Kill if late-arriving data, adverse auction fills, or realistic cutoffs erase incremental value.",
        (_REPORT + "trade-ideas.md", _REPORT + "quant-data.md"),
    ),
    EdgeCard(
        "FE12", "accuracy",
        "Rank persistent liquidity impairment from spread widening, depth loss, realized volatility, and volume concentration; no recovery half-life is estimated by this scorer.",
        "One if depth remains impaired or spread remains outside the predeclared band by the selected endpoint; otherwise zero.",
        "Spread/depth levels, realized volatility, and volume concentration for the same instrument.",
        "Hypothesis: liquidity demanders pay to avoid crossing into a fragile book.",
        "Potential accuracy from recovery dynamics; access is not assumed unless a venue-specific advantage is measured.",
        "Halts, limit states, stale quotes, hidden depth, and volatility shocks.",
        "Assess exit liquidity for all sleeves holding the instrument; no position may assume the pre-shock depth.",
        "Net avoided loss against the identical entry set, including spread widening, partial fills, and no-fill cost.",
        "Define the impaired-depth/spread event before cutoff; compare the composite rank from declared spread, depth, volatility, and concentration inputs to static thresholds.",
        "Kill if the binary impaired-depth/spread event rank does not beat static thresholds or produces excessive false alarms.",
        (_REPORT + "quant-data.md", _REPORT + "cheddar-flow.md"),
    ),
    EdgeCard(
        "FE13", "accuracy",
        "Blend normalized order-flow imbalance with only pre-as-of historical post-fill drift, then attenuate it for visible depth and depth replenishment.",
        "Midquote return from the first eligible post-signal quote to the selected fixed elapsed-time endpoint.",
        "Depth-normalized OFI, historical prior-fill drift, and a no-OFI price baseline.",
        "Hypothesis: passive liquidity providers pay to avoid adverse selection from informed aggressors.",
        "Negative-selection avoidance is the edge claim; raw trade direction or flow volume is not intent.",
        "Quote/trade timestamp mismatch, hidden liquidity, venue mix shift, or high toxicity.",
        "Include fill-conditioned co-loss with market-making and options-flow positions.",
        "Use realized post-fill markouts at 1s/1m/5m and real queue/fill assumptions; do not credit unfilled quote edge.",
        "Use same-clock quote/trade windows; score the fixed-endpoint midquote return and compare OFI-only with replenishment-adjusted forecasts on a locked cohort. Keep execution markouts separate.",
        "Kill if fixed-endpoint midquote-return forecasts do not improve over OFI-only or quote/trade clock uncertainty exceeds the capture interval.",
        (_REPORT + "quant-data.md", _REPORT + "cheddar-flow.md"),
    ),
    EdgeCard(
        "FE14", "accuracy",
        "Rank downside-tail conditions from put skew, term inversion, and downside variance, gated by surface quality; the score is not a physical probability.",
        "One if the underlying realizes the predeclared left-tail barrier within the selected window; otherwise zero.",
        "Same-name realized tail rate, volatility baseline, and index tail state.",
        "Hypothesis: protection buyers pay a premium for convexity; a better physical-vs-priced tail estimate may identify relative richness.",
        "The candidate edge is better tail calibration, not interpreting option-implied probabilities as physical probabilities.",
        "Surface arbitrage, stale quote, jump, event timing, or a sudden correlation spike.",
        "Measure portfolio tail loss, hedge basis, and cost drag; co-losses with short-vol and correlation sleeves.",
        "Include option bid/ask, skew, hedge slippage, theta, borrow, and capital usage before any payoff claim.",
        "Freeze surface construction and labels; score physical tail calibration by underlying, tenor, and regime against realized history.",
        "Kill if surface quality fails or physical tail calibration does not improve versus realized-history baseline.",
        (_REPORT + "optionstrat.md", _REPORT + "squeezemetrics.md", _REPORT + "quant-data.md"),
    ),
    EdgeCard(
        "FE15", "accuracy",
        "Turn dealer-gamma displays into a scenario fan with sign uncertainty: calculate the path under long-, short-, and unknown-dealer exposure assumptions.",
        "Conditional price/hedge-flow sensitivity under a caller-specified spot path; no unconditional realized outcome label is defined.",
        "Underlying realized volatility, open-interest distribution, and a no-dealer-feedback scenario.",
        "Hypothesis: users of option structure pay for a better conditional map of hedging pressure.",
        "No edge unless one sign scenario predicts incremental outcomes and the sign is independently observable or robust.",
        "Wrong dealer-side sign, OI staleness, expiration pin, or surface/contract-multiplier error.",
        "Scenario outputs are not netted as positions; correlate with all options-tail/flow exposures.",
        "Any future trade test prices the actual option/underlying legs and rejects unavailable quote depth.",
        "Replay caller-specified spot paths under positive, negative, and unknown dealer-gamma assumptions; validate the conditional hedge-flow arithmetic and units. A realized-outcome skill test requires a separate label contract.",
        "Kill directional language when sign is latent; retire if results depend on the chosen sign assumption.",
        (_REPORT + "spotgamma.md", _REPORT + "menthorq.md", _REPORT + "gammaedge.md"),
    ),
    EdgeCard(
        "FE16", "accuracy",
        "Use as-of confidence over open/close, aggressor side, sweep, and quote condition to forecast the subsequent underlying response; confirmation is an outcome, never an input.",
        "Underlying residual return from the classified flow event to the selected fixed endpoint.",
        "Underlying momentum, contemporaneous quote/mid, and a no-intent baseline.",
        "Hypothesis: slower analysts pay for correctly classified flow that is not already reflected in the underlying.",
        "Information advantage must survive quote-condition uncertainty and shared-vendor tape dependence.",
        "Closing trades, spreads crossing stale NBBO, multi-leg prints, and systematic flag drift.",
        "Co-loss with dealer-gamma, tail, and cross-venue flow sleeves; never count multiple vendor labels as independent.",
        "Use actual consolidated quote at event time, spread, delay capture, and next executable mark.",
        "Reclassify a frozen sample with quote context; compare to price-only baseline and count source-lineage clusters once.",
        "Kill if intent posterior is uncalibrated or flow adds no incremental net forecast value.",
        (_REPORT + "cheddar-flow.md", _REPORT + "unusual-whales-original.md", _REPORT + "trade-echo.md"),
    ),
    EdgeCard(
        "FE17", "accuracy",
        "Forecast the absolute underlying move from the timestamped release; use implied move as a comparator, not as a subtracted component of the primary target.",
        "Absolute underlying return from the timestamped earnings release to the selected next-session close.",
        "Option-implied move, same-name event history, and volatility-matched event base rate.",
        "Hypothesis: event-risk hedgers pay for identifying names where priced convexity systematically misstates realized move.",
        "Potential accuracy in the residual, not long-straddle direction or option seller profitability.",
        "Wrong announcement time, stale surface, corporate action, or post-event quote used in the pre-event estimate.",
        "Defined-risk event exposure only in any future economic test; co-loss across correlated sector earnings.",
        "Measure fill at real option touch, IV crush, fees, spread, and max loss; report no-fill as cash.",
        "Use time-stamped earnings and pre-event option surface; compare absolute-return forecasts to implied-move-only and historical-event baselines.",
        "Kill if any event clock or pre-event surface is ambiguous or absolute-move skill fails against implied-move/history baselines; charge option costs only in a separate payoff test.",
        (_REPORT + "optionstrat.md", _REPORT + "option-alpha.md", _REPORT + "trade-ideas.md"),
    ),
    EdgeCard(
        "FE18", "accuracy",
        "Separate the announcement jump from post-event drift, then ask if revisions and price response disagree after sector and own-volatility controls.",
        "Sector-residual return from the first executable post-release open to the selected fixed session close.",
        "Price reaction, sector return, own volatility, and simple standardized surprise.",
        "Hypothesis: slow analysts and mandate-constrained institutions under-adjust to a material earnings surprise.",
        "Potential accuracy from delayed belief updating only after price-aware and event-time controls.",
        "Restatement, confounded event, one-time special item, or initial price reaction already exhausts drift.",
        "Sector overlap and short-side squeezes create co-loss with revisions and factor sleeves.",
        "Next-open entry, spread, turnover, borrow, and overnight gaps; compare per opportunity, not filled trade only.",
        "Freeze surprise vintage and event cohort; use issuer-clustered walk-forward and an untouched era.",
        "Kill if post-event drift is not incremental to price reaction and sector/volatility controls.",
        (_REPORT + "danelfin.md", _REPORT + "quantix.md"),
    ),
    EdgeCard(
        "FE19", "accuracy",
        "Estimate revision breadth as a diffusion process: track analyst-level arrival times, disagreement, and whether revisions precede or merely follow price.",
        "Issuer return less the frozen sector/market benchmark from revision availability to the selected fixed session close.",
        "Price momentum, sector drift, and consensus level without revision timing.",
        "Hypothesis: institutional investors with slow committee cycles pay for early and reliable estimate dispersion changes.",
        "Potential accuracy requires estimate-vintage access before the price update; consensus snapshots alone are not an access edge.",
        "Coverage turnover, stale/backfilled estimates, analyst departure, or price-led revisions.",
        "Issuer and sector concentration; group with PEAD and fundamental-quality losses.",
        "Next-open or next-session mark with short borrow, spread, turnover, and source subscription cost.",
        "Lock estimates by publication timestamp and compare revision arrival to the price's own response in each era.",
        "Kill if revisions follow price, point-in-time history is unavailable, or net value does not beat price momentum.",
        (_REPORT + "tipranks.md", _REPORT + "quantix.md", _REPORT + "tickeron.md"),
    ),
    EdgeCard(
        "FE20", "access",
        "Forecast the panel's own sampling error: distinguish real activity change from who entered, disappeared, or changed reporting behavior in the alternative-data panel.",
        "Next-period fundamental surprise z-score using the frozen consensus vintage and standardization population.",
        "Public company fundamentals, price, sector, and a no-panel-change base model.",
        "Hypothesis: data users pay for timely nonpublic-but-authorized measurements with demonstrably stable coverage.",
        "Access is only present if rights permit the use and the panel's lead survives public price/fundamental baselines.",
        "Provider methodology change, participant churn, coverage drift, privacy/rights restriction, or survivorship.",
        "Measure vendor concentration and common panel exposure across sleeves; do not count derived vendor panels as independent.",
        "Net any later value against subscription, ingestion, storage, and execution latency.",
        "Freeze covered entities and panel vintages; test incremental forecast value after price, sector, and release-date controls.",
        "Kill on unclear rights, unstable panel lineage, or no incremental out-of-sample value.",
        (_REPORT + "altindex.md", _REPORT + "danelfin.md"),
    ),
    EdgeCard(
        "FE21", "accuracy",
        "Combine the declared cash-conversion, receivables-gap, deferred-revenue, and free-cash-flow features into a directional cash-quality change score.",
        "Change in cash-conversion measure between the frozen accession vintage and the next comparable filing.",
        "Prior cash conversion, sector seasonality, and a simple cash-flow trend baseline.",
        "Hypothesis: investors with stale accounting screens pay for earlier detection of cash-quality deterioration.",
        "Potential accuracy comes from reconstructing filing facts sooner or mapping them better, not from ratios already in price.",
        "Restatement, taxonomy change, fiscal-period mismatch, acquisition, or unusual working-capital seasonality.",
        "Issuer concentration and sector accounting conventions; no claim that a low ratio implies return direction.",
        "For any later equity test, next-open marks, spread, liquidity tier, and short/borrow cost.",
        "Use accession IDs and filing availability; compare the declared four-feature cash-conversion score to lagged cash-flow and sector baselines.",
        "Kill if restatement handling or period alignment fails, or if the next-vintage target is not better predicted.",
        (_REPORT + "finviz-screener.md", _REPORT + "stock-rover.md"),
    ),
    EdgeCard(
        "FE22", "accuracy",
        "Score same-section disclosure change only after multiplying by parser confidence, novelty, and section relevance; numeric contradiction is not yet an input.",
        "Parser-normalized disclosure delta in the same predeclared filing section/type at the next comparable filing.",
        "Prior same-section text, XBRL numeric changes, and an unchanged-boilerplate baseline.",
        "Hypothesis: analysts pay for a reliable reconciliation of long filings before consensus catches up.",
        "Potential accuracy from semantic-to-numeric disagreement and time saved; generic NLP sentiment is not an edge.",
        "Parser drift, document-type mismatch, OCR error, boilerplate, or language-model memorization.",
        "Co-loss with XBRL, revisions, and PEAD at the same issuer; cluster by filing event.",
        "Subtract data/parser operations and, for any trade test, real liquidity and next-open costs.",
        "Blind parser versions to the outcome; compare to filing-count and simple numeric-delta baselines.",
        "Kill if parser quality, section alignment, or same-vintage replication fails.",
        (_REPORT + "quantix.md", _REPORT + "danelfin.md"),
    ),
    EdgeCard(
        "FE23", "accuracy",
        "Estimate insider information content only after separating plan sales, grants, tax withholding, gifts, and discretionary open-market activity.",
        "Issuer residual return from filing availability to the selected fixed session close.",
        "Own-price drift, scheduled plan activity, insider role, and base-rate filing effect.",
        "Hypothesis: slower investors pay for correctly classified discretionary conviction and may underweight administrative trades.",
        "Public filing access is not scarce; only faster processing or materially better transaction classification could be.",
        "Form coding error, late filing, 10b5-1 plan change, clustered selling, or liquidity squeeze.",
        "Aggregate insider event risk with filing and PEAD sleeves; measure short-side squeeze.",
        "Start from filing availability, not trade date; include next-open spread, borrow, and event gap.",
        "Use time-stamped forms and predeclared transaction taxonomy; score issuer residual return for class-aware versus raw-net-flow models on the same available-at cutoff.",
        "Kill if results depend on transaction dates unavailable at the cutoff or classification precision falls below its pre-set floor.",
        (_REPORT + "insiderfinance.md", _REPORT + "unusual-whales-original.md"),
    ),
    EdgeCard(
        "FE24", "access",
        "Treat 13F as a lagged crowd inventory, not current holdings: forecast forced-unwind vulnerability when stale crowding meets deteriorating fundamentals and poor exit depth.",
        "One if the predeclared crowded-position unwind event occurs by the selected quarter end; otherwise zero.",
        "Filing-age baseline, issuer liquidity, own volatility, and known filing-date schedule.",
        "Hypothesis: market makers and liquidity providers price the risk of crowded holders needing to exit.",
        "No speed edge for public 13F unless filing processing is faster; value could be risk triage, not prediction.",
        "Holdings changed after report date, options/short exposure omitted, issuer mapping error, or crowded exits.",
        "Stress gap and depth loss jointly with all ownership and small-cap sleeves; inventory may be unholdable.",
        "Any implementation needs realistic borrow/exit depth and no assumption that filing shares remain current.",
        "Replay only from filing availability; test unwind hazard against stale-holdings and liquidity-only baselines.",
        "Kill if stale holdings do not incrementally predict stress or if position ownership is described as current.",
        (_REPORT + "unusual-whales-original.md", _REPORT + "altindex.md"),
    ),
    EdgeCard(
        "FE25", "accuracy",
        "Weight reported buyback pace by execution confidence and blackout risk, then damp it when liquidity is anomalous; announcements alone are not executed demand.",
        "Issuer residual return from buyback-report availability to the selected fixed session close, conditional on verified executed pace.",
        "Announcement size, issuer volume, own price trend, and no-execution-support baseline.",
        "Hypothesis: issuers transfer a temporary bid to remaining holders while they actually repurchase.",
        "Potential edge comes from observed execution pace versus the market's assumed pace.",
        "Authorization suspended, blackout, missing reports, or a liquidity/price shock that overwhelms the bid.",
        "Concentration in issuer beta and corporate-action risk; co-loss with index and event sleeves.",
        "Use report-date timestamps, next-open price, spread, impact, and capacity; compare notional to ADV.",
        "Freeze filings by available_at; compare issuer residual-return forecasts using verified execution pace against announcement-only and price-trend baselines in matched issuers.",
        "Kill if actual pace cannot be observed or does not outperform announcement/price baselines.",
        (_REPORT + "finviz-screener.md", _REPORT + "stock-rover.md"),
    ),
    EdgeCard(
        "FE26", "access",
        "Decay an estimated index-flow score by confidence, time to effective date, and crowding; the starter does not separately identify forced and anticipated flow.",
        "Constituent return relative to the frozen index benchmark from announcement to the selected effective-date close.",
        "Index return, ordinary volume, known announcement response, no-flow baseline, and announced-flow-only baseline.",
        "Hypothesis: passive funds with fixed benchmark deadlines shed liquidity to earlier, capacity-limited event traders.",
        "Access is constrained capacity or timing; widely anticipated rebalance flow is not automatically mispriced.",
        "Rule change, stale constituents, crowded front-run, or order-flow estimate already embedded in price.",
        "Stress correlated basket holdings and stock-borrow concentration; cross-sleeve loss can be simultaneous.",
        "Use basket constituents and real market impact; report missed or cancelled event trades as cash.",
        "Freeze event calendar, flow model, consensus/crowding snapshot, and effective-date close; compare constituent-relative return forecasts with announced-flow-only and no-flow baselines. Score post-effective reversal separately.",
        "Kill if rule revisions, crowding, or actual net flow erase the price effect.",
        (_REPORT + "trade-ideas.md", _REPORT + "finviz-screener.md"),
    ),
    EdgeCard(
        "FE27", "accuracy",
        "Estimate the conditional reaction coefficient to macro surprise; the sign can flip with policy pricing, cycle state, and the exact release vintage.",
        "Return of the declared cross-asset instrument from the first executable post-release mark to 30 minutes after release.",
        "Surprise-only regression, market-implied policy path, and asset's own event history.",
        "Hypothesis: macro hedgers pay for faster, better mapping from a release surprise into the current reaction function.",
        "Speed matters only if consensus and release vintages are aligned and usable before the price response.",
        "Revised release, policy shock, simultaneous headline, wrong consensus timestamp, or reaction sign whipsaw.",
        "Duration, FX, credit, and equity positions can co-lose; test joint stress and funding needs.",
        "Include event spread, slippage, fill latency, and delayed execution; no hypothetical release-time mid fills.",
        "Use release-by-release vintages; compare conditional reaction to a fixed surprise coefficient on untouched events.",
        "Kill if the sign is unstable out of sample or release/consensus clocks are not proven.",
        (_REPORT + "finviz-screener.md", _REPORT + "market-chameleon.md"),
    ),
    EdgeCard(
        "FE28", "accuracy",
        "Rank stress transition from curve slope, curve-change direction, credit impulse, and the declared macro-transition feature rather than curve level alone.",
        "One if the predeclared market-stress transition criterion is met by the selected quarter end; otherwise zero.",
        "Curve slope alone, credit spread alone, and a base-rate macro hazard.",
        "Hypothesis: risk committees pay for earlier de-risking evidence before growth and funding stress become obvious.",
        "Potential accuracy is transition timing after point-in-time macro vintages, not a precise recession date claim.",
        "Policy regime change, fiscal shock, benchmark discontinuity, or revised macro history.",
        "Portfolio co-loss in equities, credit, rates, and FX; assess collateral and mark-to-market path.",
        "Value any overlay as avoided portfolio loss less hedge carry, slippage, and rebalance churn.",
        "Lock vintages at release; use expanding/rolling origins and compare to single-curve and base-rate models.",
        "Kill if point-in-time vintages fail or conditional transition skill does not persist across eras.",
        (_REPORT + "market-chameleon.md", _REPORT + "stock-rover.md"),
    ),
    EdgeCard(
        "FE29", "access",
        "Forecast a positioning/physical-flow squeeze when trader crowding diverges from inventory scarcity, while honoring the release schedule actually in force.",
        "Commodity excess return from the selected publication-time reference to the fixed week endpoint.",
        "Roll yield, seasonality, own volatility, and publication-calendar base rates.",
        "Hypothesis: physical-market users and futures intermediaries pay for earlier synthesis of public positioning and inventory.",
        "Public data creates no access by itself; value requires faster synthesis or capacity to warehouse the resulting risk.",
        "Supply shock, benchmark roll, delayed release, revised seasonal factor, or crowd already on one side.",
        "Stress margin, delivery/roll mechanics, and correlated commodity exposures; assume no easy exit in the squeeze.",
        "Use point-in-time contract rolls, fees, margin, slippage, and delayed COT availability.",
        "Use as-of release dates and compare the joint model with roll-yield-only and inventory-only baselines.",
        "Kill if publication vintage is wrong, supply shocks dominate the relationship, or holdout value is not net of roll and margin.",
        (_REPORT + "quant-data.md", _REPORT + "squeezemetrics.md"),
    ),
    EdgeCard(
        "FE30", "accuracy",
        "Rank venue-specific squeeze risk from funding extremes, open-interest change, depth loss, and absolute on-chain flow; cross-venue cascade propagation is outside this scorer.",
        "One if a venue-specific liquidation/depth squeeze event occurs by the selected endpoint; otherwise zero.",
        "Per-venue realized volatility, funding, and depth-only hazard without cross-venue propagation.",
        "Hypothesis: market makers and collateral-constrained traders pay for early identification of forced-flow cascades.",
        "Potential speed/access must survive venue-specific clocks and cannot be inferred from a pooled price feed.",
        "Exchange outage, withdrawal freeze, depeg, mislabeled on-chain flow, or funding/mark-index divergence.",
        "Measure venue custody, liquidation margin, cross-venue basis, and aggregate crypto co-loss before any position test.",
        "Price each venue separately with fees, funding, liquidation, withdrawal, and latency; no atomicity assumption.",
        "Replay venue-synchronized events; compare to single-venue depth/funding baselines with incident-blocked holdouts.",
        "Kill if event lineage or venue clock is uncertain, or cascade forecasts do not beat the single-venue baseline.",
        (_REPORT + "nansen.md", _REPORT + "arkham-intelligence.md"),
    ),
)

_BY_ID = {card.engine_id: card for card in EDGE_CARDS}


def get_edge_card(engine_id: str) -> EdgeCard:
    try:
        return _BY_ID[engine_id]
    except KeyError as exc:
        raise KeyError(f"unknown forecast edge card: {engine_id}") from exc


def validate_edge_cards(engine_ids: Iterable[str] | None = None) -> tuple[str, ...]:
    """Return contract violations without implying that any hypothesis has edge."""
    if engine_ids is None:
        from .catalog import ENGINES

        engine_ids = (spec.engine_id for spec in ENGINES)
    expected = set(engine_ids)
    actual = set(_BY_ID)
    errors: list[str] = []
    if len(actual) != len(EDGE_CARDS):
        errors.append("duplicate edge-card engine_id")
    if actual != expected:
        errors.append(
            f"engine coverage differs: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    required_fields = (
        "edge_source", "novel_mechanism", "target_definition", "price_aware_baseline",
        "payer_hypothesis", "scarcity_or_transfer", "bad_state",
        "holdability_and_co_losses", "execution_net", "decisive_test", "kill_rule",
        "source_refs",
    )
    for card in EDGE_CARDS:
        for field_name in required_fields:
            value = getattr(card, field_name)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"{card.engine_id}: missing {field_name}")
        if card.edge_source not in {"speed", "accuracy", "access", "variance"}:
            errors.append(f"{card.engine_id}: invalid edge_source {card.edge_source!r}")
        if card.status != "HYPOTHESIS":
            errors.append(f"{card.engine_id}: non-hypothesis status requires evidence review")
        for ref in card.source_refs:
            if ref.startswith(("https://", "http://")):
                continue
            source_path = Path(__file__).resolve().parents[2] / ref
            if not source_path.is_file():
                errors.append(f"{card.engine_id}: missing source reference {ref}")
    return tuple(errors)


def edge_cards_as_dicts() -> list[dict[str, object]]:
    """Serialize the ledger for review or a research registry."""
    return [asdict(card) for card in EDGE_CARDS]
