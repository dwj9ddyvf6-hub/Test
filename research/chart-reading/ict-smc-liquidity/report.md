# Evidence base for discretionary trading setups — research report

**Research date:** 2026-10-08. All sources read via web index (`index` flag); nothing was live-verified in a trading platform. Academic papers are cited from their abstracts/indexed text; practitioner/community sources are labeled as such.

**Scope note:** Four separate investigations, each with its own claim set, evidence, criticisms, and takeaways. A per-investigation note file in `notes/` holds the URL-by-URL record.

---
---

# INVESTIGATION 1: ICT/SMC-style intraday setup (liquidity sweep → FVG → SMT → timed entry)

## Core claims under investigation
1. Wait for price to sweep a higher-timeframe (daily or 4H) swing point — "liquidity sweep" / stop-hunt.
2. Wait for price to return into a "fair value gap" (FVG — an imbalanced 3-candle range) on a lower timeframe (1H or 30min).
3. Require the higher-timeframe candle to be in "expansion."
4. Require SMT (intermarket divergence, e.g. ES making a lower low while NQ doesn't) at the level.
5. Enter on a V-shaped reversal signature at specific times (9:30, 10:00, 10:30, 12:00 ET).
6. Target the opposite swing point. "Works on any asset," price moves "from liquidity pool to liquidity pool," no indicators.
7. Philosophy: mastering ONE setup beats knowing ten.

## Findings

### (a) Liquidity sweeps / stop-loss hunting — real phenomenon, real mechanism, overstated narrative
**Strongest academic support in the whole mission.** Carol Osler's market-microstructure work provides the closest thing to a rigorous foundation for "liquidity sweep" logic:
- Osler, "Stop-Loss Orders and Price Cascades in Currency Markets" (NY Fed Staff Report; published JIMF 2005) — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf — finds, in high-frequency FX data: (1) trends are unusually rapid at levels where stop-loss orders are documented to cluster; (2) the price response to stop-loss orders is larger than to take-profit orders (which are negative-feedback); (3) the response lasts longer — significant for hours, not days. Very large stop-loss orders cluster tightly at round numbers (over 62% of their face value near rates ending in 00). Conclusion: stop-loss orders propagate trends and are sometimes triggered in waves ("price cascades"), helping explain fat tails. *Index, abstract + indexed text.*
- Osler, "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis" (2001) — http://www.technicalanalysis.org.uk/momentum/Osle01.pdf — gives the direct microstructural account of S/R: take-profit orders mirror trends (causing reversals at predictable levels), stop-loss orders intensify trends (causing momentum once levels break); both cluster at round numbers, which is why round numbers behave as support/resistance. *Index.*
- Fett & McPhail (2017), "Stop Orders in Select Futures Markets" (CFTC, proprietary CME data 2014–16) — listing at https://WWW.cftc.gov/About/EconomicAnalysis/ResearchPapers/index.htm?page=0 — a reality check on magnitudes: executed stop orders were a *small* share of volume (ES ~0.9%, WTI ~2%, 10Y ~0.3%), ~95–99% were stop-*limit* (not stop-market), stops fire more on volatile days and "provide liquidity in the direction of the price move," and slippage "can be significant at times" (findings via secondary summary https://medium.com/@pterido/are-they-really-hunting-your-stop-what-futures-data-actually-say-about-stop-orders-e879bd83dfc7, *index*).
- Practitioner explainers converge on the same distinction: stop clusters are real and their price effect is real, but deliberate targeting of individual retail accounts is not supported; the mechanism is structural (large participants trading toward visible liquidity to fill size), not conspiratorial — https://blog.traderspost.io/article/stop-loss-hunting-detection and http://rivantacaptial.blogspot.com/2026/09/why-price-moves-against-you-before-it.html (*index*).
- What the literature does NOT support: the ICT-specific elaborations — that sweeps are orchestrated by a central "algorithm"/market-maker to harvest retail stops before a scripted reversal, that they are reliably followed by V-shaped reversals to the opposite swing point, or that "expansion" candles can be identified in advance. Osler's cascades describe *continuation* after stops trigger (the opposite of the fade-the-sweep entry), and effects are intraday-hours scale.

### (b) Fair value gaps / imbalance zones as reversal areas
**No rigorous evidence found.** The only quantified backtest of FVG entries located is a community quant weekly report (https://github.com/mayastraglobal-ui/crypto-signal-agent/blob/HEAD/reports/claude/weekly/2026-09-26.md, *index*) whose SMC strategy family lost money in every regime tested (-0.44R over 748 trades in RANGE; -0.67R/117 in WEAK_BULL; -0.09R/746 in TRANSITION), whose FVG-specific combos had 1 and 0 trades (too few to judge), and whose source README claims no profitability ("educational purposes only"). BuildAlpha (https://www.buildalpha.com/backtest-ict-and-smc/, *index*) supplies testable FVG definitions and warns to normalize gap size by ATR — useful methodologically, but presents no performance evidence. Academic literature has no FVG construct; the nearest neighbors are gap/overreaction studies (see (d)). Honest status: FVG-as-reversal-zone is an untested practitioner hypothesis. Related honest observation from that same community report: gaps are everywhere on low timeframes, so unfiltered FVG entries are mostly noise and costs dominate.

### (c) Intermarket divergence (SMT) predicting reversals
**No rigorous evidence found.** SMT is well-defined in the ICT community (https://innercircletrader.net/tutorials/ict-smt-divergence-smart-money-technique/ and https://github.com/kmshdev/traders-knowledge-kit/blob/HEAD/concepts/16-smt-divergence/smt-divergence.md, *index*): for positively correlated pairs (ES/NQ, EURUSD/GBPUSD, XAU/XAG), one asset printing a new high/low while the other fails to confirm signals a reversal. But neither source gives performance statistics, and no academic paper testing ES-vs-NQ (or EURUSD-vs-GBPUSD) swing-point divergence as a reversal predictor was located. Note the base rate problem: ES and NQ are extremely highly correlated intraday, so genuine divergences at swing points are rare by construction — the signal's sample size is inherently small, which is exactly when hindsight labeling thrives.

### (d) Time-of-day effects at 9:30/10:00/10:30/12:00
**Real intraday time-of-day effects exist, but they do not match the claim.** What the literature actually shows:
- Gao, Han, Li & Zhou (2018), "Market Intraday Momentum" (JFE) — the first half-hour's return predicts the *last* half-hour's return on SPY (1993–2013; timing Sharpe ~1.08 vs 0.29 buy-and-hold) — via https://github.com/ullasgh/nifty-intraday-quant-research/blob/HEAD/specs/h1_market_intraday_momentum.md and https://github.com/definitelymikey/orb-strategy/blob/HEAD/Market_Intraday_Momentum/CLAUDE.md (*index*). This is intraday *momentum* (continuation), driven by late-day rebalancing/gamma-hedging flows (Baltussen et al. 2021) — not a reversal signature at 9:30/10:00/10:30/12:00. Caveat: McLean & Pontiff (2016) document ~58% post-publication decay of anomalies, and a 2026 replication ("Intraday Momentum, Eight Years Later," via https://quantocracy.com/recent-quant-links-from-quantocracy-as-of-09302026/) suggests the effect has weakened.
- Heston, Korajczyk & Sadka (2010), "Intraday patterns in the cross-section of stock returns" (J. Finance 65(4):1369–1407) — half-hour returns show cross-sectional autocorrelation at weekly lags, strongest in the 09:30–10:30 and 15:00–16:00 buckets, weakest midday — via https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/62_intraday_half_hour_seasonality.md (*index*). A 2025 follow-up (Haendler et al., https://www.kellogg.northwestern.edu/academics-research/research/detail/2025/the-intra-day-stock-return-periodicity-puzzle/, *index*) attributes open periodicity to VWAP execution and close periodicity to market-on-close flows — i.e., institutional *execution scheduling*, not reversal timing.
- The genuine *reversal* literature points the other way: "Intraday time series reversal" (https://paperswithbacktest.com/api/paper/intraday-time-series-reversal/pdf, *index*) finds the *overnight* return predicts the *first-30-minute* return (a reversal: fade the overnight gap), stronger when the overnight move is negative; and a 2025 arXiv paper (https://arxiv.org/pdf/2501.16772.pdf, *index*) finds markets mean-revert more than tick-size effects imply at horizons *below ~30 minutes*, while trends persist above ~1 hour. The BIST-100 thesis (https://open.metu.edu.tr/bitstream/handle/11511/89731/12626166.pdf, *index*) finds overreaction in the first minute after an overnight gap, reversing over 7–30 minutes.
- Verdict: 9:30/10:00/10:30/12:00 as *reversal times* is practitioner lore (cf. the BabyPips "major reversal times" thread, https://forums.babypips.com/t/what-are-the-major-reversal-times/19981, *index*), not an academic finding. The documented regularities are: momentum from first half-hour to last half-hour, reversal of the overnight gap in the first 30 minutes, and sub-30-minute mean reversion.

### (e) The specialization claim ("one setup beats ten")
**Indirect evidence; cuts against the guru framing.** The two landmark day-trader studies:
- Barber, Lee, Liu & Odean, "The Cross-Section of Speculator Skill: Evidence from Day Trading" — https://7251530cx666163756c7479x68616173x6265726b656c6579x656475.gateway.web.tr/http/odean/papers/Day%20Traders/Day%20Trading%20Skill%20110523.pdf (*index*) — document *large, persistent* skill differences: the top 500 Taiwanese day traders earned +49.5 bps/day before fees (+28.1 after), the bottom-ranked −17.5/−34.2 bps/day. Skill exists and persists — consistent with "repetition builds competence."
- Barber, Lee, Liu & Odean, "Do Day Traders Rationally Learn About Their Ability?" — http://2tradersclub.com/wp-content/uploads/2016/12/Day-Trading-and-Learning-110217.pdf (*index*) — the sobering companion: the *most experienced* day traders lose money; over half of all day trading volume traces to traders with a history of losses; persistent losing is inconsistent with rational learning; the authors write that "trading to learn" is no more rational than playing roulette to learn.
- Net: repetition can build skill in the tiny minority who have edge, but repetition alone does not create edge — most repeaters just lose more slowly. No study was found testing "one setup vs many setups" as a treatment. The honest reading: specialization is a plausible *learning* strategy, not an *edge*.

### (f) Criticisms of ICT/SMC as doctrine
1. **No verified track record.** Multiple independent sources note the absence of audited performance: a 2025 review (https://medium.com/@phillipescott10/the-inner-circle-trader-scam-review-1f7f62d02bc4, *index*) cites opaque pricing and no transparent audited reports, quoting a user review that zero students have confirmed successful records; a BabyPips community thread (https://forums.babypips.com/t/the-downfall-of-ict-inner-circle-trader/834125?page=3, *index*) echoes "never met ICT profitable trader," referencing the Robbins Cup episode.
2. **Alleged fabrication and invalid backtesting.** A long-form video critique (https://www.youtube.com/watch?v=9UUFlSE8Ztg, *index*) catalogs claims of photoshopped statements and argues ICT teaches invalid backtesting methods (the critique's timestamps list admissions of teaching flawed backtesting); a summary (https://www.nutshellapp.com/publicsummaries/exposing-ict's-fraudulent-trading-practices%3A-a-deep-dive-into-deception-and-manipulation, *index*) adds failed trading competitions and selective example-picking. Treat the fraud allegations as *allegations* (single-source, adversarial), but the structural point stands: the doctrine's evidence base is curated chart examples, not audited results.
3. **Unfalsifiability / hindsight labeling.** The framework's vocabulary (liquidity, displacement, "smart money intent") is applied after the fact with enough degrees of freedom (any swing can be relabeled a liquidity pool; any failed signal can be re-narrated) that it cannot be cleanly falsified — a criticism consistent with the broader academic complaint about TA jargon (Lo, Mamaysky & Wang 2000 note the "impenetrable jargon" problem).
4. **Incentive structure.** Revenue comes from education/mentorship and content, not from trading — the classic guru-economics critique; when the teacher's income doesn't depend on the method working, the method faces no market test.
5. **Mechanism mismatch.** The one rigorous pillar (Osler's stop-cascade work) predicts *continuation* after stop clusters trigger, while the ICT entry fades the sweep expecting *reversal* — the doctrine's trade direction is the opposite of what its best evidence implies.

## Practical takeaways (Inv. 1)
1. The "liquidity sweep" concept has the strongest foundation of any ICT component — order clustering at visible levels is real (Osler) — but treat the sweep as *information about positioning*, not a reversal signal: the academic mechanism favors continuation, so fading every sweep is fighting the documented effect.
2. FVGs have no evidence base; if you use them, treat them as untested and demand your own logged, out-of-sample stats before sizing up (the only quantified test found lost money).
3. SMT divergence is extremely rare by construction (ES/NQ barely diverge) — beware of hindsight selection; log every occurrence prospectively or don't trade it.
4. Time filters should follow the literature, not lore: the documented edges are overnight-gap reversal in the first 30 minutes and first-to-last-half-hour momentum — not V-reversals at 10:00/10:30/12:00.
5. Specialization helps learning but doesn't manufacture edge: track expectancy per setup in your own journal; if 100+ logged trades show no edge, switching setups isn't the fix — the fix is admitting there's no edge.

## Could not verify / open questions (Inv. 1)
- No study tests the full 6-component setup or FVGs or SMT as predictors; no verified track record for ICT or any prominent student was found.
- Whether retail stop clusters specifically (vs institutional stops) move ES/NQ intraday is unmeasured — Osler's data is FX dealer orders; the CFTC data shows stops are a small share of futures volume.

---
---

# INVESTIGATION 2: Intraday reference levels (PDH/PDL/PDC, open, PMH/PML; polarity; VWAP)

## Core claims under investigation
Six levels (previous day high/low/close, open price, premarket high/low) serve as intraday context/decision points; tactics like "reclaim the open, ride it"; the polarity principle (broken support becomes resistance and vice versa).

## Findings

### (a) Evidence that prior-day H/L/close, open, premarket extremes act as intraday levels
**No rigorous study was found testing PDH/PDL/PDC/open/PMH/PML specifically as intraday support/resistance.** The nearest academic evidence concerns the *open* and the *overnight gap*:
- "Intraday time series reversal" (https://paperswithbacktest.com/api/paper/intraday-time-series-reversal/pdf, *index*): the overnight return (prior close → open) predicts the first-30-minute return — a reversal effect on the S&P 500 ETF averaging 8.2%/yr vs benchmark (Sharpe 0.95–1.51), surviving transaction costs for SPY. Mechanism: opposing clienteles — retail buying overnight vs daytime arbitrageur selling (Berkman et al. 2012; Lou et al. 2019; Akbas et al. 2022).
- Dangl & Salbrechter, "Overnight Reversal and the Asymmetric Reaction to News" (https://paperswithbacktest.com/api/paper/overnight-reversal-and-the-asymmetric-reaction-to-news/pdf, *index*): overnight news moves the open; opens that overshoot (news confirming the prior day's direction) reverse during the day.
- Berkman, Koch, Tuttle & Zhang (2012) (via https://arxiv.org/pdf/2507.04481, *index*): retail investors bid up high-attention stocks at the open; high overnight return → low intraday return.
- Akbas, Boehmer, Jiang & Koch (2022) (via https://redfame.com/journal/index.php/aef/article/download/7705/6965, *index*): positive overnight returns followed by negative daytime reversals; the pattern predicts next-month returns.
- Important decay note: an extension of Branch & Ma (2012) (https://assets.super.so/e46b77e7-445e-b43f-4ffd88ae0a0e/files/bc092535-b30f-4f56-90b1-fa8235af015b.pdf, *index*) finds the overnight→intraday reversal *disappeared for large caps (S&P 500)* in recent data while persisting for small caps — consistent with improving efficiency at the index level.
- Heston, Korajczyk & Sadka (2010) (via https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/62_intraday_half_hour_seasonality.md, *index*): same-half-hour returns autocorrelate at weekly lags, strongest at the open bucket — i.e., the open *time* matters, though this is about clock time, not the open *price* level.
- Bottom line: the open price matters because the overnight gap creates a documented reversal/overreaction dynamic — not because PDH/PDL/PDC/PMH/PML are validated S/R levels. For the six specific levels, the honest answer is "no direct evidence; plausible as focal points given order-clustering logic (Osler), but untested."

### (b) Polarity principle
**No peer-reviewed evidence found.** The claim appears only in practitioner education (e.g. https://fastercapital.com/topics/introduction-to-support-and-resistance.html, https://entri.app/blog/support-and-resistance-explained/, *index*). The microstructure logic gives it *some* plausibility — trapped longs from a broken support level create supply on a retest (their breakeven exits) — but equally, a broken level means the resting liquidity was consumed, which argues the other way. Untested either way; treat as folk wisdom, not a finding.

### (c) VWAP as intraday benchmark
**Well-documented as an execution benchmark; thin evidence as a trading signal.** Berkowitz, Logue & Noser (1988, J. Finance) originated VWAP as the institutional execution-quality benchmark (via https://blog.forexcommand.com/en/vwap-vs-obv-vs-volume-profile-what-each-one-measures-on-a-forex-chart/, *index*). A secondary source cites Harris (2003) for ~30–40% of institutional equity flow explicitly targeting VWAP (via https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/60_intraday_vwap_mean_reversion.md, *index* — treat the percentage cautiously). Haendler et al. (2025) (https://www.kellogg.northwestern.edu/academics-research/research/detail/2025/the-intra-day-stock-return-periodicity-puzzle/, *index*) find open-period return periodicity is driven by VWAP-benchmarked trading — the closest thing to evidence that VWAP exerts a gravitational pull intraday. Practitioner backtests (e.g. https://onetradejournal.com/strategies/vwap-trading-strategy, *index*) claim 65–68% win rates but with weak methodology (no cost accounting). Verdict: VWAP's institutional relevance is real; "fade VWAP deviations" as a retail edge is plausible-mechanism but unproven.

### (d) How much edge survives costs
- Bessembinder & Chan (1998), "Market Efficiency and the Returns to Technical Analysis" (Financial Management 27(2)) — https://ideas.repec.org/a/fma/fmanag/bessembinder98.html (*index*): simple technical rules show statistically significant forecast power, but "the returns do not appear large enough to outweigh the trading costs."
- A breakeven-cost analysis of Brock-et-al.-style rules (https://repository.hkust.edu.hk/ir/bitstream/1783.1-362/1/tech.pdf, *index*) finds breakeven costs fell from 0.54% (1926–43) to 0.22% (1976–91) — at or below actual trading costs, implying no net edge in-sample.
- Practitioner illustration of the cost problem: an 8-year Nifty opening-range-breakout backtest (https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest, *index*) reports its raw edge *excluding* transaction costs — the standard way level-trading edges evaporate.
- The documented intraday effects are small (basis points per trade, one trade per day) — consistent with costs being the binding constraint.

### (e) Criticisms
1. **Self-fulfilling vs genuine liquidity:** Osler's (2001) microstructure account actually favors a genuine mechanism — conditional orders cluster at round/prior levels regardless of chart-reading — which is stronger than "everyone draws the same line." But for PDH/PDL/PMH/PML specifically, no order-flow study confirms clustering there.
2. **Data-snooping across candidate levels:** with six levels × two sides (break vs hold) × multiple tactics, a trader is implicitly testing dozens of hypotheses; any "level that worked" is selected ex post. The ORB look-ahead-bias case study (https://github.com/danielsaarva/orb-backtest-audit, *index* — a bug inflated expectancy from +0.283R to ~0.001R) is a concrete demonstration of how easily level-trading backtests deceive.
3. **Decay:** the large-cap overnight-reversal edge has already decayed (Branch & Ma extension); intraday momentum has decayed ~58%+ post-publication (McLean & Pontiff 2016; 2026 replication).

## Practical takeaways (Inv. 2)
1. The open/gap deserves your attention more than the other five levels: the overnight-gap reversal in the first 30 minutes is the best-documented intraday regularity touching these levels — plan around the gap, not the lines.
2. Use PDH/PDL/open as *context for invalidation* (where your idea is wrong), not as forecast levels; none is validated as S/R.
3. VWAP is the one intraday reference with institutional order flow behind it — above/below VWAP is a meaningful regime read; deviations are fades only with a stop and cost awareness.
4. Any level strategy must be costed: one- to two-trades-a-day signals have a chance; high-turnover level-scalping does not (Bessembinder & Chan).
5. Beware the six-level multiple-comparisons trap: pre-commit to which level and which behavior (break vs hold) *before* the session, and log results.

## Could not verify / open questions (Inv. 2)
- Direct tests of PDH/PDL/PDC/PMH/PML as intraday S/R; the polarity principle; whether premarket extremes influence regular-session price action.

---
---

# INVESTIGATION 3: Short-EMA scalping (9EMA, 5-min; volume filter)

## Core claims under investigation
9-period EMA on 5-minute: below = sellers in control; break above + retest = buyers take control; enter first bounce candle after retest; pullbacks only on lower volume than the breakout; EMA slope curling up confirms the new trend.

## Findings

### (a) Evidence on short-EMA trend/scalp systems on 5-minute
**None found at this timeframe.** The moving-average literature is daily/weekly:
- Brock, Lakonishok & LeBaron (1992) found strong MA-rule predictability over ~90 years of DJIA — but Urquhart et al. ("How Exactly Do Markets Adapt?", https://eprints.soton.ac.uk/377140/1/Urquhart_How.pdf, *index*) show the edge *diminished after 1986* in the DJIA, FT30, and TOPIX, with markets reacting to signals the day *before* they trigger — the Adaptive Market Hypothesis in action.
- Lo, Mamaysky & Wang (2000) (https://web.mit.edu/wangj/www/pap/LoMamayskyWang00.pdf, *index*) found some predictive ability for automated technical patterns "especially when moving averages are concerned" — again daily data, 1962–96.
- The FX exception: rigorous studies find MA/momentum rules profitable even after costs in *currencies* (Menkhoff & Taylor survey; Kho 1996 — profits too large for costs, though Kho attributes them to time-varying risk premia; sources via https://www.brandeis.edu/economics/RePEc/brd/doc/Brandeis_WP48.pdf and https://ijbss.thebrpi.org/journals/Vol_3_No_20_Special_Issue_October_2012/20.pdf, *index*), while equities generally show no net edge (Bessembinder & Chan 1998; Park & Irwin 2007, per the same Brandeis survey).
- No paper tests a 9-period EMA on 5-minute bars. The number 9 has no theoretical basis in the literature; it is a practitioner convention.

### (b) EMAs as dynamic support/resistance intraday
**No rigorous evidence found.** The literature tests MA *crossovers* as trend signals, not MAs as bounce levels. The only channel by which a 9EMA could "work" as support is self-fulfilling: Taylor & Allen (1992) (via https://www.scribd.com/document/57008705/96-006, *index*) found 90% of London FX dealers used chartist input at sub-weekly horizons, 60% rating it at least as important as fundamentals — with moving averages the most-cited tool. If enough participants watch the 9EMA, reactions at it become possible — but that is a popularity contest, not a structural property, and it decays as algos front-run it (cf. Urquhart's "day before" finding).

### (c) The volume condition (low-volume pullback after high-volume breakout)
**No peer-reviewed test of this specific filter found.** What exists:
- Practitioner consensus treats it as confirming evidence, not proof (https://www.gwcindia.in/blog/how-can-traders-combine-price-action-and-volume-to-evaluate-the-quality-of-a-market-move/, *index*); a Wyckoff-oriented writeup (https://www.binance.com/en/square/post/370301945682596, *index*) describes declining volume on pullbacks as a weaker-supply clue but explicitly cautions against reducing it to a mechanical bar-by-bar volume check.
- A genuine counterpoint: a V-day pivot study (https://github.com/juststeve/strader/blob/HEAD/docs/measurement/greek-discovery-plan.md, *index*) found that reversal troughs were characterized by volume *climax* (1.57× time-of-day-expected volume, d=0.842, p=0.014), while continuation days showed normal or below-normal volume — i.e., decisive turns arrive *with* volume, not on its absence. This doesn't directly refute the pullback filter (different event), but it warns against the folk model that "low volume = healthy."
- Theoretical support for volume mattering at all: Blume, Easley & O'Hara (1994) give volume a role in traders' learning process.
- Honest status: the filter is plausible microstructure intuition (breakout volume = commitment; pullback volume = absence of counter-pressure) with no quantified validation.

### (d) The cost question at scalp frequencies
This is where the setup faces its hardest arithmetic:
- Roll (1984) (via https://github.com/kanar11/hft-infra-lab/commit/febd1632ce803bcea578d0360999ee932559bd9c and https://www.dir.uniupo.it/pluginfile.php/1460498/mod_folder/content/0/The%20Journal%20of%20Finance%20-%20September%201984%20-%20ROLL%20-%20A%20Simple%20Implicit%20Measure%20of%20the%20Effective%20Bid%E2%80%90Ask%20Spread%20in%20an%20Efficient.pdf, *index*): bid-ask bounce induces negative serial covariance in trade prices — pure microstructure noise unrelated to information. At 5-minute horizons this noise is a large fraction of the signal.
- French & Roll (1986) (http://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf, *index*): trading itself generates return noise; a nontrivial share of short-horizon variance is mispricing.
- A 2026 Stanford student HFT study (https://algoinsights.medium.com/stanford-students-built-5-hft-strategies-and-tested-them-on-real-market-data-heres-what-happened-1460cfc89d1e, *index*): most backtest alpha disappeared once costs, spreads, and execution were included; only order-book pressure survived.
- A moving-average research note (https://github.com/neel-error404/strategylab/blob/HEAD/docs/SMA_CROSSOVER_STRATEGY_RESEARCH.md, *index*): at 0.06–0.12% round-trip, costs quickly erode frequent signals, and shorter-period MAs are the worst affected.
- A Swiss-stock MA study (http://moving-averages.technicalanalysis.org.uk/IsHo99.pdf, *index*): MA rules profitable at 0.3% one-way costs, unprofitable at 1.6% — edge, where it exists, lives or dies on costs.
- A 5-minute 9EMA system trades many times per day for moves of a few basis points — the exact profile the cost literature kills.

### (e) Criticisms
1. **Noise-to-signal:** at 5 minutes, bid-ask bounce and microstructure noise (Roll 1984; French & Roll 1986) dominate; the 9EMA is mostly smoothing noise and will whipsaw.
2. **Overtrading:** high-frequency discretionary systems maximize commission/slippage bleed; the Stanford study and Bessembinder & Chan both show costs as the binding constraint.
3. **Curve-fit parameters:** 9 periods, 5 minutes, "first bounce candle," "lower than breakout volume" — four free parameters with no theory; classic data-snooping setup (the literature's standard antidote is White's reality check / bootstrap, which no EMA-scalping vendor applies).
4. **Regime blindness:** MA systems fail in ranges (widely acknowledged even by practitioners: https://github.com/neel-error404/strategylab/blob/HEAD/docs/SMA_CROSSOVER_STRATEGY_RESEARCH.md); the setup has no regime filter beyond EMA slope, which is itself lagging.
5. **Adaptivity:** Urquhart et al.'s finding that markets now react *before* MA signals trigger implies widely-watched MA levels get front-run.

## Practical takeaways (Inv. 3)
1. Don't trade a 9EMA/5-min system with real money until you've logged 100+ trades *with* spread and commission accounted for — the literature says costs are the most likely outcome-determiner.
2. The volume filter is the most defensible part of the setup (it at least proxies commitment vs apathy), but it has no quantified validation — treat it as a confidence weight, not a gate, and note the V-climax counterpoint.
3. If you must scalp with an EMA, trade it as a *trend-bias* tool on liquid instruments in already-established intraday trends, not as a reversal-catcher; and define the regime where you stand aside.
4. Any EMA length is arbitrary — if 9 works but 8 and 10 don't in your backtest, you have curve-fit, not edge.
5. Fewer, larger trades beat many tiny ones: the cost math strictly favors lower frequency.

## Could not verify / open questions (Inv. 3)
- Any test of 9EMA-on-5-min specifically; the low-volume-pullback filter as a quantified predictor; whether retail 5-min scalping survives costs on any specific instrument (no study found — the retail outcome data we do have, e.g. SEBI's 87.7% F&O loss rate via https://entri.app/blog/support-and-resistance-explained/, is damning in aggregate).

---
---

# INVESTIGATION 4: Classical support/resistance (horizontal zones, "more touches," MAs, fixed R:R)

## Core claims under investigation
Horizontal S/R zones where price repeatedly reacts; dynamic S/R from moving averages in trends; "multiple price reactions" = stronger level (more touches = stronger); trade with confirmation; plan entry/stop/target at 1:2 or 1:3 risk-reward.

## Findings

### (a) Do horizontal S/R zones exist as more than folk wisdom?
**Yes — the strongest academic footing of the four investigations,** via order-flow microstructure rather than chart mysticism:
- Osler (2001), "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis" (http://www.technicalanalysis.org.uk/momentum/Osle01.pdf, *index*): take-profit orders cluster at levels and *cause* reversals (negative feedback); stop-loss orders cluster at levels and *cause* acceleration once broken (positive feedback). This is a causal, order-driven account of why S/R levels work — and why breaks accelerate.
- Round-number effects: Donaldson & Kim (1993) found psychological barriers in the DJIA at multiples of 100 and 1000 acting as S/R zones with measurable return-distribution effects (via https://github.com/waterfirst/chimera-ai/blob/HEAD/papers/round_number_barrier_v2.md, *index*); a "Magic numbers in the Dow" working paper (https://agc.asuis.workers.dev/read-https-openaccess.city.ac.uk/id/eprint/16276/1/magic%20numbers%20in%20the%20dow.pdf, *index*) confirms price clustering at round numbers across FX (de Grauwe & Decupere 1992) and indices (Donaldson & Kim 1993; Ley & Varian 1994; Cyree & Domian 1999; Mitchell 2001), citing Osler's market-driven reasons: conditional orders (stops/limits) are placed at round numbers, and option strikes cluster at round numbers, inducing hedging flows.
- Harris (1991): trade prices cluster on integers > half-dollars > quarters (price-resolution/negotiation hypotheses; via https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf, *index*).
- The mechanism is *memory in order flow*, not memory in price: resting conditional orders placed at salient levels are what make levels "work." This is a genuine effect, though documented mainly in FX and index round numbers — not for arbitrary hand-drawn zones on any chart.

### (b) "More touches = stronger level" — both sides, carefully
**No peer-reviewed study directly tests whether touch count predicts hold probability.** The two camps:
- FOR (practitioner consensus): more touches = more confirmation = more significant level (e.g. https://fastercapital.com/topics/introduction-to-support-and-resistance.html; https://medium.com/@financialterminalastro/support-and-resistance-in-technical-analysis-a-practical-trading-guide-f3c035a00c92, *index*). Behavioral logic: visibility grows with touches, attracting more participants (Schelling focal point).
- AGAINST (order-flow logic): each test *consumes* resting liquidity, so a much-tested level is closer to exhaustion — the supply/demand view (https://www.tradingview.com/chart/NAS100/LcVGbA22-Trading-Framework-Support-Resistance-vs-Supply-Demand/, *index*); the first touch is the most reliable and each subsequent test weakens the level (https://www.linkedin.com/pulse/support-resistance-why-obvious-levels-often-fail-dr-trade-i0wze, *index*); repeated tests accumulate *stops* behind the level, so the level becomes "liquidity, not protection," and the eventual break cascades (https://medium.com/@Blastslot/what-most-traders-call-a-strong-level-is-often-just-a-visible-cluster-of-resting-orders-33c37ef13517, *index* — directly consistent with Osler's stop-cascade evidence).
- Assessment: the microstructure logic favors the AGAINST side (orders are finite; each fill depletes the book), while the FOR side relies on ever-growing participation. The testable prediction distinguishing them — hold probability declining in touch count — has apparently never been published. A discretionary trader should therefore *not* size up on the 4th test; if anything, the literature suggests reducing size or demanding a better rejection signal on later tests.

### (c) Moving averages as dynamic support/resistance
**No rigorous evidence found for MAs as bounce levels.** The MA literature (Brock et al. 1992; Lo et al. 2000; Bessembinder & Chan 1998) tests crossovers, not support-bounces, and finds decaying/after-cost-negative results in equities. The self-fulfilling channel (Taylor & Allen 1992: 90% of FX dealers use chartist input) gives long MAs (50/200-day) some plausibility as focal points in *trending* markets, but nothing validates the 20/50-EMA bounce intraday. Verdict: dynamic S/R from MAs is practitioner convention, not a finding.

### (d) Fixed risk-reward ratios (1:2, 1:3)
**The math is tautological; no study validates mandating a minimum R:R as an edge.**
- The expectancy arithmetic is correct and useful as accounting: at 1:2, breakeven win rate ≈ 33.3%; at 1:3, ≈ 25% (https://www.profitxresearch.com/blog/why-a-positive-risk-reward-ratio-matters-for-the-long-term-survival-of-a-trading-system; https://tradergibkey.eu/blog/posts/win-rate-vs-risk-reward, *index*).
- But mandating a minimum R:R is a *trade filter*, not an edge creator: it skips setups where structure doesn't permit the ratio. The critique (https://dev.to/propfirmkey/risk-reward-ratio-why-12-isnt-always-the-answer-14a5; https://damnpropfirms.com/trading-guides/risk-to-reward-lies-traders-tell-themselves/, *index*): fixed targets land "in the middle of nowhere" (not at structural levels); win rate and R:R are inversely correlated (pushing targets out lowers hit rate); expectancy = (WR × avg win) − (LR × avg loss) is what matters, and a 70%-at-1:0.8 system beats a 35%-at-1:2.5 system. Costs and slippage further erode the textbook breakeven math.
- No academic paper was found testing a "minimum 1:2 R:R" rule. Sound practice per the critics: place stops/targets at structure, let the market quote the R:R, and only take the trade if the resulting expectancy (from your own logged data) is positive.

### (e) Criticisms of classical S/R
1. **Subjectivity:** where zones start/end, which touches count, which timeframe dominates — all judgment calls. Lo, Mamaysky & Wang (2000) were partly motivated by the need to *automate* subjective pattern definitions.
2. **Hindsight bias:** levels are usually drawn after the reaction is visible; the ORB look-ahead-bias case study (https://github.com/danielsaarva/orb-backtest-audit, *index*) shows how easily backtested level strategies deceive (+0.283R → ~0.001R after fixing the bug).
3. **Unfalsifiability in practice:** "zones not lines" plus "role reversal" gives the analyst an alibi for every outcome — a level that breaks was "weak," one that holds was "strong."
4. **Generality overreach:** the rigorous evidence (Osler, round numbers) covers FX dealer orders and index round numbers — not arbitrary zones on any asset/timeframe. "Works on any asset" is asserted, not shown.
5. **Base rates:** most touches of most levels do nothing; practitioners remember the photogenic bounces (selection bias). Aggregate retail outcomes remain poor (SEBI FY26: 87.7% of individual F&O traders with net losses, via https://entri.app/blog/support-and-resistance-explained/, *index*).

## Practical takeaways (Inv. 4)
1. S/R is real where *orders* cluster — round numbers, prior extremes, option strikes — not wherever you can draw a line. Weight levels by independent reasons orders would rest there.
2. Invert the "more touches" rule: treat the first test as the highest-quality one and later tests as progressively more dangerous (liquidity-consumption logic + Osler cascades). Never add size because a level "held three times."
3. Use MAs for trend regime, not as bounce levels; if you fade into an MA, you're trading an untested folk pattern.
4. Set stops and targets at structure; compute the implied R:R; then check it against *your logged* win rate for that setup type — expectancy, not a mandated 1:2, is the decision variable.
5. Pre-draw levels before the session and log every touch outcome; your own touch-count statistics are the only version of the "more touches" debate that matters for your trading.

## Could not verify / open questions (Inv. 4)
- Touch-count vs hold-probability (no published test); MA-as-support bounce rates; any academic test of fixed-R:R mandates; whether Osler-style order clustering holds in modern equity intraday data (her data is FX, 1990s–2000s).

---
---

# Cross-investigation synthesis

| Claim | Evidence status | Best source |
|---|---|---|
| Stop-loss clusters move price (sweeps) | Supported (FX microstructure; hours-scale) | Osler (2005); CFTC Fett & McPhail (2017) |
| Sweep → reliable V-reversal | Not supported; mechanism favors continuation | Osler (2005) |
| FVG as reversal zone | No rigorous evidence; one quantified test lost money | mayastraglobal-ui weekly report (community) |
| SMT divergence predicts reversals | No rigorous evidence | — (absence) |
| Reversals at 9:30/10:00/10:30/12:00 | Not supported as stated; real effects are overnight-gap reversal (first 30 min) and first→last-half-hour momentum | Gao et al. (2018); Intraday-reversal paper; HKS (2010) |
| PDH/PDL/PDC/open/PMH/PML as S/R | No direct evidence; open/gap has reversal literature | Berkman et al. (2012); Akbas et al. (2022) |
| Polarity principle | No rigorous evidence | — (absence) |
| VWAP matters intraday | Supported as execution benchmark; signal use unproven | Berkowitz et al. (1988); Haendler et al. (2025) |
| 9EMA/5-min scalping edge | No evidence; cost arithmetic hostile | Roll (1984); French & Roll (1986); Bessembinder & Chan (1998) |
| Low-volume pullback filter | No rigorous evidence; one counterpoint (V-climax) | strader V-day study (community) |
| Horizontal S/R exists (order-flow basis) | Supported (FX, round numbers) | Osler (2001); Donaldson & Kim (1993) |
| More touches = stronger | No published test; microstructure logic favors weaker | — (both sides practitioner) |
| MAs as dynamic S/R | No rigorous evidence | — (absence) |
| Mandated 1:2/1:3 R:R improves outcomes | No evidence; it's a filter, not an edge | — (expectancy math only) |
| One-setup specialization beats many | Indirect; repetition builds skill only where edge exists | Barber et al. (2014, 2017) |
| ICT/SMC has verified track records | None found; multiple critical reports | Medium/BabyPips/YouTube critiques (adversarial, single-source) |

## Universal practical takeaways (all four investigations)
1. **Costs are the binding constraint** on every intraday claim here (Bessembinder & Chan 1998; Roll 1984). Any setup must be evaluated net of spread/commission/slippage, at the frequency it actually trades.
2. **The best-supported ideas are order-flow ideas** (stop clusters, round numbers, VWAP execution, overnight gaps) — all from peer-reviewed microstructure. The worst-supported are the most specific practitioner recipes (FVG, SMT, 9EMA bounces, polarity, touch-count rules).
3. **Direction of the documented effect matters:** stop cascades predict continuation, not reversal; sub-30-min horizons mean-revert while multi-hour horizons trend. Trade *with* the documented direction.
4. **Effects decay** (intraday momentum ~58%+ post-publication; large-cap overnight reversal gone). A setup that "worked" in backtests from 2015 needs re-validation on recent data.
5. **Your own log is the only evidence that counts for your trading:** pre-commit rules, log every occurrence prospectively (no hindsight labeling), 100+ trades, net of costs. Nothing in these four investigations substitutes for that.

---

# Sources (master list — all read 2026-10-08 via web index)

**Academic / institutional (primary):**
- Osler, C.L. "Stop-Loss Orders and Price Cascades in Currency Markets" — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Osler, C.L. "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis" (2001) — http://www.technicalanalysis.org.uk/momentum/Osle01.pdf
- Fett, N. & McPhail, L. (2017) "Stop Orders in Select Futures Markets" (CFTC) — listing: https://WWW.cftc.gov/About/EconomicAnalysis/ResearchPapers/index.htm?page=0
- "Intraday time series reversal" — https://paperswithbacktest.com/api/paper/intraday-time-series-reversal/pdf
- "Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades" — https://arxiv.org/pdf/2501.16772.pdf
- METU thesis, intraday reversals on BIST 100 — https://open.metu.edu.tr/bitstream/handle/11511/89731/12626166.pdf
- Barber, Lee, Liu & Odean, "The Cross-Section of Speculator Skill" — https://7251530cx666163756c7479x68616173x6265726b656c6579x656475.gateway.web.tr/http/odean/papers/Day%20Traders/Day%20Trading%20Skill%20110523.pdf
- Barber, Lee, Liu & Odean, "Do Day Traders Rationally Learn About Their Ability?" — http://2tradersclub.com/wp-content/uploads/2016/12/Day-Trading-and-Learning-110217.pdf
- Dangl & Salbrechter, "Overnight Reversal and the Asymmetric Reaction to News" — https://paperswithbacktest.com/api/paper/overnight-reversal-and-the-asymmetric-reaction-to-news/pdf
- Branch & Ma (2012) extension on overnight/intraday autocorrelation — https://assets.super.so/e46b77e7-445e-b43f-4ffd88ae0a0e/files/bc092535-b30f-4f56-90b1-fa8235af015b.pdf
- Overnight-news predictability paper — https://arxiv.org/pdf/2507.04481
- Redfame summary of Akbas et al. (2022) overnight/daytime reversal — https://redfame.com/journal/index.php/aef/article/download/7705/6965
- Heston, Korajczyk & Sadka (2010) half-hour seasonality — secondary: https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/62_intraday_half_hour_seasonality.md
- Haendler, Heston, Korajczyk & Sadka (2025) periodicity puzzle — https://www.kellogg.northwestern.edu/academics-research/research/detail/2025/the-intra-day-stock-return-periodicity-puzzle/
- Bessembinder & Chan (1998), "Market Efficiency and the Returns to Technical Analysis" — https://ideas.repec.org/a/fma/fmanag/bessembinder98.html
- Technical-analysis breakeven costs working paper — https://repository.hkust.edu.hk/ir/bitstream/1783.1-362/1/tech.pdf
- Lo, Mamaysky & Wang (2000), "Foundations of Technical Analysis" — http://web.mit.edu/wangj/www/pap/LoMamayskyWang00.pdf
- Urquhart et al., "How Exactly Do Markets Adapt?" (MA rule decay) — https://eprints.soton.ac.uk/377140/1/Urquhart_How.pdf
- Moving-average rules on Swiss stocks (cost sensitivity) — http://moving-averages.technicalanalysis.org.uk/IsHo99.pdf
- MA crossover in Malaysia equities — http://carrels.distantreader.org/journal-internationalJournalOfEconomicsAndFinancialIssues-ojsoai/cache/ijefi-3598.pdf
- Kho (1996) / MA-rule survey material — https://ijbss.thebrpi.org/journals/Vol_3_No_20_Special_Issue_October_2012/20.pdf
- Osler Brandeis working paper on microstructure & TA (surveys Taylor & Allen 1992, Menkhoff & Taylor) — https://www.brandeis.edu/economics/RePEc/brd/doc/Brandeis_WP48.pdf
- "Magic numbers in the Dow" (round-number clustering) — https://agc.asuis.workers.dev/read-https-openaccess.city.ac.uk/id/eprint/16276/1/magic%20numbers%20in%20the%20dow.pdf
- Bhattacharya, Holden & Jacobsen (2012) (round-number/price-clustering references incl. Harris 1991) — https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf
- Gao, Han, Li & Zhou (2018) "Market Intraday Momentum" — secondaries: https://github.com/ullasgh/nifty-intraday-quant-research/blob/HEAD/specs/h1_market_intraday_momentum.md and https://github.com/definitelymikey/orb-strategy/blob/HEAD/Market_Intraday_Momentum/CLAUDE.md
- Dead Signals Lab replication note (via Quantocracy) — https://quantocracy.com/recent-quant-links-from-quantocracy-as-of-09302026/
- Komarov "Intra-Day Momentum" (SSRN) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2905713

**Practitioner / community / secondary:**
- https://medium.com/@pterido/are-they-really-hunting-your-stop-what-futures-data-actually-say-about-stop-orders-e879bd83dfc7
- https://blog.traderspost.io/article/stop-loss-hunting-detection
- http://rivantacaptial.blogspot.com/2026/09/why-price-moves-against-you-before-it.html
- https://www.traderfaculty.com/guides/liquidity-sweep
- https://github.com/mayastraglobal-ui/crypto-signal-agent/blob/HEAD/reports/claude/weekly/2026-09-26.md
- https://www.buildalpha.com/backtest-ict-and-smc/
- https://innercircletrader.net/tutorials/ict-smt-divergence-smart-money-technique/
- https://github.com/kmshdev/traders-knowledge-kit/blob/HEAD/concepts/16-smt-divergence/smt-divergence.md
- https://forums.babypips.com/t/what-are-the-major-reversal-times/19981
- https://medium.com/@phillipescott10/the-inner-circle-trader-scam-review-1f7f62d02bc4
- https://www.nutshellapp.com/publicsummaries/exposing-ict's-fraudulent-trading-practices%3A-a-deep-dive-into-deception-and-manipulation
- https://forums.babypips.com/t/the-downfall-of-ict-inner-circle-trader/834125?page=3
- https://www.youtube.com/watch?v=9UUFlSE8Ztg
- https://blog.forexcommand.com/en/vwap-vs-obv-vs-volume-profile-what-each-one-measures-on-a-forex-chart/
- https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/60_intraday_vwap_mean_reversion.md
- https://onetradejournal.com/strategies/vwap-trading-strategy
- https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest
- https://github.com/danielsaarva/orb-backtest-audit
- https://digital.wpi.edu/downloads/12579s947?locale=en
- https://github.com/wojtek0110/opening_range_breakout_backtest/blob/HEAD/docs/orb_rules.md
- https://www.thetransparenttrader.com/blog-articles/how-to-backtest-a-day-trading-strategy-hourly-breakout-part-1/
- https://github.com/juststeve/strader/blob/HEAD/docs/measurement/greek-discovery-plan.md
- https://www.gwcindia.in/blog/how-can-traders-combine-price-action-and-volume-to-evaluate-the-quality-of-a-market-move/
- https://www.binance.com/en/square/post/370301945682596
- https://algoinsights.medium.com/stanford-students-built-5-hft-strategies-and-tested-them-on-real-market-data-heres-what-happened-1460cfc89d1e
- https://github.com/neel-error404/strategylab/blob/HEAD/docs/SMA_CROSSOVER_STRATEGY_RESEARCH.md
- https://papertradingjournal.com/2026/10/01/does-technical-analysis-work-and-why-risk-management-matters-more/
- https://papertradingjournal.com/2026/10/05/should-i-be-using-mutliple-timeframes-when-trading/
- https://www.tradingview.com/chart/NAS100/LcVGbA22-Trading-Framework-Support-Resistance-vs-Supply-Demand/
- https://www.linkedin.com/pulse/support-resistance-why-obvious-levels-often-fail-dr-trade-i0wze
- https://medium.com/@Blastslot/what-most-traders-call-a-strong-level-is-often-just-a-visible-cluster-of-resting-orders-33c37ef13517
- https://fastercapital.com/topics/introduction-to-support-and-resistance.html
- https://entri.app/blog/support-and-resistance-explained/
- https://medium.com/@financialterminalastro/support-and-resistance-in-technical-analysis-a-practical-trading-guide-f3c035a00c92
- https://www.profitxresearch.com/blog/why-a-positive-risk-reward-ratio-matters-for-the-long-term-survival-of-a-trading-system
- https://tradergibkey.eu/blog/posts/win-rate-vs-risk-reward
- https://dev.to/propfirmkey/risk-reward-ratio-why-12-isnt-always-the-answer-14a5
- https://damnpropfirms.com/trading-guides/risk-to-reward-lies-traders-tell-themselves/
- https://github.com/waterfirst/chimera-ai/blob/HEAD/papers/round_number_barrier_v2.md
- https://medium.com/@amo_pbl/stocks-earn-their-gains-while-you-sleep-068b0bc30d42

**Detailed per-source notes:** `notes/inv1-ict-smc.md`, `notes/inv2-intraday-levels.md`, `notes/inv3-ema-scalping.md`, `notes/inv4-classical-sr.md`.
