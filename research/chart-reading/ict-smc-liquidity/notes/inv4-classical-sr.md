# Source notes — Investigation 4 (classical support/resistance)
All read via web index on 2026-10-08; all flagged `index`.

1. Osler (2001) "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis"
   URL: http://www.technicalanalysis.org.uk/momentum/Osle01.pdf
   Core academic support for S/R: take-profit orders "reflect price trends" (cause reversals at predictable levels); stop-loss orders "intensify trends" (cause momentum after breaks). Both cluster at round numbers, which "are often used as support and resistance levels."

2. Donaldson & Kim (1993) — psychological barriers in DJIA at multiples of 100 and 1000; levels act as S/R zones with measurable effects on return distributions. Via https://github.com/waterfirst/chimera-ai/blob/HEAD/papers/round_number_barrier_v2.md (secondary; also notes effect may be regime-dependent).

3. "Magic numbers in the Dow" working paper URL: https://agc.asuis.workers.dev/read-https-openaccess.city.ac.uk/id/eprint/16276/1/magic%20numbers%20in%20the%20dow.pdf
   Price clustering at round numbers confirmed in FX (de Grauwe & Decupere 1992) and indices (Donaldson & Kim 1993; Ley & Varian 1994; Cyree & Domian 1999; Mitchell 2001). Cites Osler (2001): market-driven reasons — conditional orders (stops/limits) set at round numbers; option strikes at round numbers induce hedging flows.

4. Harris (1991) trade-price clustering (integers > half-dollars > quarters > odd-eighths in 1/8-tick era); price resolution / negotiation hypotheses. Via https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf (secondary mention).

5. "More touches = stronger" FOR: practitioner consensus (FasterCapital https://fastercapital.com/topics/introduction-to-support-and-resistance.html; Medium guides https://medium.com/@financialterminalastro/support-and-resistance-in-technical-analysis-a-practical-trading-guide-f3c035a00c92 — "the more times a level is tested, the more important it becomes").
   AGAINST: (a) CandelaCharts TradingView https://www.tradingview.com/chart/NAS100/LcVGbA22-Trading-Framework-Support-Resistance-vs-Supply-Demand/ — supply/demand view: each test CONSUMES resting orders, so a 4-times-tested zone is weaker; (b) LinkedIn "Dr Trade" https://www.linkedin.com/pulse/support-resistance-why-obvious-levels-often-fail-dr-trade-i0wze — first touch most reliable, each subsequent test weakens; (c) BlastSlot Medium https://medium.com/@Blastslot/what-most-traders-call-a-strong-level-is-often-just-a-visible-cluster-of-resting-orders-33c37ef13517 — repeated tests attract more stops, level becomes liquidity not protection, breakdown then cascades (consistent with Osler 2002 cascades).
   NO peer-reviewed paper directly testing touch-count vs hold probability was found — report both sides as practitioner/microstructure-logic positions.

6. Moving averages as dynamic S/R: NO rigorous study found on MAs as bounce levels intraday. Trend-following profitability literature (Brock et al. 1992; Lo et al. 2000; Bessembinder & Chan 1998) is about MA crossovers, not MA-as-support. Popularity channel: Taylor & Allen (1992) 90% chartist use (self-fulfilling potential); Kho (1996) MA-rule profits in FX.

7. Fixed R:R (1:2, 1:3):
   - Math/expectancy: https://www.profitxresearch.com/blog/why-a-positive-risk-reward-ratio-matters-for-the-long-term-survival-of-a-trading-system (breakeven WR table: 1:2→33.3%, 1:3→25%); https://tradergibkey.eu/blog/posts/win-rate-vs-risk-reward (expectancy framing).
   - Critique: https://dev.to/propfirmkey/risk-reward-ratio-why-12-isnt-always-the-answer-14a5 (fixed targets land "in the middle of nowhere"; WR and RR inversely correlated; expectancy is what matters; trade to structure); https://damnpropfirms.com/trading-guides/risk-to-reward-lies-traders-tell-themselves/ (expectancy formula; transaction-cost erosion).
   - NO academic study found testing "mandate minimum 1:2 R:R" as a rule — mandating R:R is a trade FILTER (skips setups where structure doesn't permit it), not an edge creator; expectancy math is tautological.

8. Criticisms of classical S/R:
   - Subjectivity: Lo, Mamaysky & Wang (2000) partly motivated by automating subjective pattern definitions.
   - Hindsight bias: drawing levels after the fact; the orb-backtest-audit look-ahead case study (https://github.com/danielsaarva/orb-backtest-audit) as concrete illustration of how bias inflates results.
   - Self-fulfilling vs liquidity: Osler's microstructure account favors genuine order-flow mechanism over pure self-fulfilling prophecy (orders cluster at round numbers regardless of chart-reading).
   - Malkiel (1990) "amusing, often comforting, but of no real value" (via Brandeis WP48).
   - Retail outcomes: SEBI FY26 study — 87.7% of individual F&O traders had net losses (via https://entri.app/blog/support-and-resistance-explained/).
