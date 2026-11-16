# Source notes — Investigation 1 (ICT/SMC)
All read via web index on 2026-10-08. All flagged `index` (not live-verified).

1. Osler, C.L. "Stop-Loss Orders and Price Cascades in Currency Markets" (NY Fed Staff Report / JIMF 2005)
   URL: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
   Key facts (from abstract + text): (i) FX trends unusually rapid at levels where stop-loss orders cluster; (ii) price response to stop-loss orders larger than to take-profit orders; (iii) response lasts longer (hours, not days); (iv) very large stop-loss orders cluster at round numbers (62%+ of face value near rates ending in 00); supports "price cascades" / fat tails via non-informative order flow.

2. Osler, C.L. "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis" (2001)
   URL: http://www.technicalanalysis.org.uk/momentum/Osle01.pdf
   Abstract: microstructural explanation for two TA predictions — (1) trends reverse at predictable S/R levels, (2) trends gain momentum once S/R crossed. Take-profit orders reflect/mirror trends (cause reversals); stop-loss orders intensify trends. Both order types cluster at round numbers, often used as S/R.

3. Fett & McPhail (2017) "Stop Orders in Select Futures Markets" (CFTC)
   Listing: https://WWW.cftc.gov/About/EconomicAnalysis/ResearchPapers/index.htm?page=0
   Findings (via secondary summaries): proprietary CME data 2014–16 on ES, 10Y Treasury, WTI. Executed stops were a small share of volume (ES ~0.9%, WTI ~2%, 10Y ~0.3%); ~95–99% were stop-limit not stop-market; stops execute more on volatile days and "provide liquidity in the direction of the price move"; slippage can be significant at times.

4. Medium (pterido, ~2026-10) "Are They Really Hunting Your Stop?"
   URL: https://medium.com/@pterido/are-they-really-hunting-your-stop-what-futures-data-actually-say-about-stop-orders-e879bd83dfc7
   Secondary explainer of CFTC study + Osler currency research on stop-loss cascades. Position: stop clusters real, their price effects real, broker misconduct real and prosecuted; deliberate personal targeting of retail accounts not supported.

5. TradersPost blog "Stop-Loss Hunting: Can Algorithms Detect It?" URL: https://blog.traderspost.io/article/stop-loss-hunting-detection
   Distinguishes broker-side misconduct vs market-side liquidity-seeking; detection at retail level statistically intractable.

6. Rivanta Capital blog "Why Price Moves Against You Before It Moves Your Way" (2026-09)
   URL: http://rivantacaptial.blogspot.com/2026/09/why-price-moves-against-you-before-it.html
   Microstructure explainer: wicks beyond a level show exploration + rejection; not proof of intentional hunting.

7. mayastraglobal-ui crypto-signal-agent weekly report (2026-09-26)
   URL: https://github.com/mayastraglobal-ui/crypto-signal-agent/blob/HEAD/reports/claude/weekly/2026-09-26.md
   Only quantified FVG backtest found: SMC family -0.44R over 748 trades (RANGE), -0.67R/117 (WEAK_BULL), -0.09R/746 (TRANSITION); FVG sweep combos had ~1 and 0 trades (too few to judge). Source README claims no profitability ("educational purposes only").

8. BuildAlpha "How to Backtest ICT and Smart" URL: https://www.buildalpha.com/backtest-ict-and-smc/
   Formal testable definitions: FVG = Low[0] > High[2]; sweep = Low < PriorLow and Close > PriorLow; displacement = range > k*ATR. Warns to normalize by ATR.

9. innercircletrader.net "ICT SMT Divergence Explained" URL: https://innercircletrader.net/tutorials/ict-smt-divergence-smart-money-technique/
   Community definition of SMT: one correlated asset makes new high/low while the other fails to confirm → reversal signal. Pairs: ES/NQ, EURUSD/GBPUSD, XAU/XAG, EURUSD/DXY inverse.

10. kmshdev traders-knowledge-kit "SMT Divergence" URL: https://github.com/kmshdev/traders-knowledge-kit/blob/HEAD/concepts/16-smt-divergence/smt-divergence.md
    Formal criteria (bullish: A new low + B higher low). "ICT Confidence: high." No performance statistics given.

11. Gao, Han, Li & Zhou (2018) "Market Intraday Momentum," JFE — first-half-hour return predicts last-half-hour return on SPY 1993–2013 (timing Sharpe ~1.08 vs 0.29 buy-and-hold).
    Secondaries: https://github.com/ullasgh/nifty-intraday-quant-research/blob/HEAD/specs/h1_market_intraday_momentum.md ; https://github.com/definitelymikey/orb-strategy/blob/HEAD/Market_Intraday_Momentum/CLAUDE.md
    Related: Baltussen, Da, Lammers & Martens (2021) gamma-hedging mechanism; Dead Signals Lab replication "Intraday Momentum, Eight Years Later" (via https://quantocracy.com/recent-quant-links-from-quantocracy-as-of-09302026/); McLean & Pontiff (2016) ~58% post-publication decay.

12. "Intraday time series reversal" (paperswithbacktest PDF) URL: https://paperswithbacktest.com/api/paper/intraday-time-series-reversal/pdf
    Finds overnight return predicts first-30-min return (REVERSAL) for S&P 500 ETF; strengthened in GFC/pandemic; weakened after 2010s. Cites Gao et al. (2018), Huang et al. (2023), Berkman et al. (2012), Lou et al. (2019), Akbas et al. (2022).

13. arxiv 2501.16772 "Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades"
    URL: https://arxiv.org/pdf/2501.16772.pdf
    Reversion regime ends at ~30-min time scales; below ~30 min, markets revert more strongly than tick-size effect implies; above 1h, weak trends persist.

14. METU thesis "Intraday Price Reversals with High Frequency Data: Applied to BIST 100" URL: https://open.metu.edu.tr/bitstream/handle/11511/89731/12626166.pdf
    Overreaction in first minute after overnight gap, then reversal completing over ~7–30 minutes.

15. Barber, Lee, Liu & Odean "The Cross-Section of Speculator Skill: Evidence from Day Trading" (2014)
    URL: https://7251530cx666163756c7479x68616173x6265726b656c6579x656475.gateway.web.tr/http/odean/papers/Day%20Traders/Day%20Trading%20Skill%20110523.pdf
    Top 500 day traders (Taiwan, 1992–2006): +49.5 bps/day before fees (+28.1 after); bottom-ranked: -17.5/-34.2 bps/day; spread >60 bps/day. Large persistent skill differences; average investor loses.

16. Barber, Lee, Liu & Odean "Do Day Traders Rationally Learn About Their Ability?" (RFS 2017)
    URL: http://2tradersclub.com/wp-content/uploads/2016/12/Day-Trading-and-Learning-110217.pdf
    Most experienced day traders lose money; over half of all day trading traceable to traders with a history of losses; persistent losing inconsistent with rational learning; "trading to learn is no more rational or profitable than playing roulette to learn."

17. ICT criticisms:
    - https://medium.com/@phillipescott10/the-inner-circle-trader-scam-review-1f7f62d02bc4 (unverified track record, opaque pricing, no audited performance)
    - https://www.nutshellapp.com/publicsummaries/exposing-ict's-fraudulent-trading-practices%3A-a-deep-dive-into-deception-and-manipulation (photoshopped statements alleged, failed competitions, invalid backtesting methods)
    - https://forums.babypips.com/t/the-downfall-of-ict-inner-circle-trader/834125?page=3 (community thread; "never met ICT profitable trader"; Robbins Cup reference)
    - https://www.youtube.com/watch?v=9UUFlSE8Ztg ("Exposing ICT and his concepts once and for all" — claims of fabricated statements, teaching invalid backtesting)
