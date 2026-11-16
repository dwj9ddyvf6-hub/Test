# Source notes — Investigation 3 (short-EMA scalping)
All read via web index on 2026-10-08; all flagged `index`.

1. Brock, Lakonishok & LeBaron (1992) "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns," J. Finance 47:1731–1764
   Found strong predictive power of MA rules over ~90 years of DJIA. Via: https://eprints.soton.ac.uk/377140/1/Urquhart_How.pdf
   Urquhart et al. ("How Exactly Do Markets Adapt?"): post-1986 the MA rule's predictive power diminished in DJIA, FT30, TOPIX — consistent with Adaptive Market Hypothesis; markets react to signals the day BEFORE they generate.

2. Lo, Mamaysky & Wang (2000) "Foundations of Technical Analysis," J. Finance
   URL: http://web.mit.edu/wangj/www/pap/LoMamayskyWang00.pdf
   Automated pattern recognition on daily stocks 1962–96; "some predictive ability especially when moving averages are concerned" (cited in scribd summary https://www.scribd.com/document/474897577/Market-Timing-with-Moving-Averages-pdf).

3. Bessembinder & Chan (1998) — see inv2 notes. Forecast power yes, net-of-costs no.

4. Kho (1996) on MA rules in currency futures (via https://ijbss.thebrpi.org/journals/Vol_3_No_20_Special_Issue_October_2012/20.pdf): profits too large for transaction costs but explained by time-varying risk premia.

5. Isler & Hollenstein (1999?) moving-average rules on Swiss stocks (http://moving-averages.technicalanalysis.org.uk/IsHo99.pdf): rules profitable at 0.3% one-way cost, unprofitable at 1.6% — profitability critically cost-dependent. (Daily data.)

6. Taylor & Allen (1992) "The use of technical analysis in the foreign exchange market," JIMF 11:304–314 (via https://www.scribd.com/document/57008705/96-006 and ideas.repec https://ideas.repec.org/a/fip/fedlrv/y1997isepp23-38.html): at horizons ≤1 week, 90% of London FX dealers used some chartist input, 60% rated it at least as important as fundamentals. Self-fulfilling-potential channel. Also: Menkhoff & Taylor (2006/2007) survey; Brandeis WP48 (https://www.brandeis.edu/economics/RePEc/brd/doc/Brandeis_WP48.pdf): FX TA profitable even after costs in rigorous studies; equities generally not (Bessembinder & Chan 1998; Park & Irwin 2007; Bender, Osler & Simon 2012).

7. Volume condition (low-volume pullback after high-volume breakout):
   - NO peer-reviewed study found testing this specific filter.
   - Practitioner/secondary: https://www.gwcindia.in/blog/how-can-traders-combine-price-action-and-volume-to-evaluate-the-quality-of-a-market-move/ (volume as supporting evidence, not proof); Binance "Aunt Kong's Classroom" https://www.binance.com/en/square/post/370301945682596 (Wyckoff spring/shakeout logic; declining volume on pullback as weaker-supply clue; author cautions against mechanical volume-bar checks).
   - Counterpoint: https://github.com/juststeve/strader/blob/HEAD/docs/measurement/greek-discovery-plan.md — V-day pivot study found troughs characterized by VOLUME CLIMAX (1.57x expected, d=0.842, p=0.014), continuation days normal/below-normal volume. Suggests decisive turns come with volume, not its absence.
   - Theory: Blume, Easley & O'Hara (1994) — volume has a role in trader learning / technical analysis framework.

8. Costs at scalp frequency:
   - Roll (1984) "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market," J. Finance 39:1127–1139 (via https://www.dir.uniupo.it/pluginfile.php/1460498/... and https://github.com/kanar11/hft-infra-lab/commit/febd1632ce803bcea578d0360999ee932559bd9c): bid-ask bounce induces negative serial covariance in trade prices = pure microstructure noise, unrelated to information.
   - French & Roll (1986) (http://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf): trading itself generates noise in returns; large fraction of daily variance is mispricing/noise.
   - Stanford HFT student study (Oct 2026): https://algoinsights.medium.com/stanford-students-built-5-hft-strategies-and-tested-them-on-real-market-data-heres-what-happened-1460cfc89d1e — most backtest alpha disappeared after costs, spreads, execution.
   - SMA crossover research note: https://github.com/neel-error404/strategylab/blob/HEAD/docs/SMA_CROSSOVER_STRATEGY_RESEARCH.md — at 0.06–0.12% round-trip, costs erode frequent signals; shorter-period MAs worse.

9. Curve-fit / parameter criticism: EMA length (9) has no theoretical basis found in literature; parameter-sensitivity concern standard in TA literature (data-snooping critique; Brock et al. used bootstrap to address it).
