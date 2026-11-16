# Source notes — Investigation 2 (intraday reference levels)
All read via web index on 2026-10-08; all flagged `index`.

1. "Intraday time series reversal" (paperswithbacktest PDF) URL: https://paperswithbacktest.com/api/paper/intraday-time-series-reversal/pdf
   Overnight return predicts first-half-hour return (reversal) for SPY; 8.2% annual return difference vs benchmark (Sharpe 0.95–1.51), survives transaction costs for SPY (8.5%); reversal stronger when overnight sign negative; strengthened in GFC/COVID; mechanism: retail overnight buying vs daytime arbitrageur selling (Berkman et al. 2012; Lou et al. 2019).

2. Dangl & Salbrechter "Overnight Reversal and the Asymmetric Reaction to News" URL: https://paperswithbacktest.com/api/paper/overnight-reversal-and-the-asymmetric-reaction-to-news/pdf
   Overnight news moves the open; overshooting opens reverse during the day when news confirms prior day's direction.

3. Branch & Ma (2012) extension URL: https://assets.super.so/e46b77e7-445e-b43f-4ffd88ae0a0e/files/bc092535-b30f-4f56-90b1-fa8235af015b.pdf
   Negative overnight→intraday autocorrelation persisted for small caps but DISAPPEARED for large caps (S&P 500) in recent data — supports market efficiency for the index.

4. Berkman, Koch, Tuttle & Zhang (2012) — via arxiv summary https://arxiv.org/pdf/2507.04481
   Retail investors bid up high-attention stocks at the open → high overnight return followed by low intraday return.

5. Akbas, Boehmer, Jiang & Koch (2022) — via https://redfame.com/journal/index.php/aef/article/download/7705/6965
   Positive overnight returns followed by negative daytime reversals in US stocks; predicts next-month returns.

6. Heston, Korajczyk & Sadka (2010) "Intraday patterns in the cross-section of stock returns," J. Finance 65(4):1369–1407
   Secondary: https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/62_intraday_half_hour_seasonality.md
   Half-hour returns autocorrelated at weekly lags (same half-hour bucket predicts same bucket 5,10,15... days out); t>4 in most buckets; strongest at open (09:30–10:30) and pre-close (15:00–16:00), weakest midday.

7. Haendler, Heston, Korajczyk & Sadka (2025) "The intra-day stock return periodicity puzzle"
   URL: https://www.kellogg.northwestern.edu/academics-research/research/detail/2025/the-intra-day-stock-return-periodicity-puzzle/
   Open periodicity driven by VWAP trading; close periodicity by market-on-close trading. Institutional execution flows create time-of-day effects.

8. VWAP: Berkowitz, Logue & Noser (1988) J. Finance — measured institutional trade costs vs day's VWAP (~14,000 NYSE trades); origin of VWAP as execution benchmark.
   Secondary: https://blog.forexcommand.com/en/vwap-vs-obv-vs-volume-profile-what-each-one-measures-on-a-forex-chart/
   Harris (2003) cited for 30–40% of institutional equity order flow explicitly targeting VWAP — via https://github.com/marcohwlam/quant-zero/blob/HEAD/research/hypotheses/60_intraday_vwap_mean_reversion.md (secondary claim, treat cautiously).

9. VWAP backtests (practitioner): https://onetradejournal.com/strategies/vwap-trading-strategy (Nifty, Jan 2024–Oct 2026, win rates 65–68% claimed; weak methodology — no cost detail; low-quality evidence).

10. Bessembinder & Chan (1998) "Market Efficiency and the Returns to Technical Analysis," Financial Management 27(2)
    URL: https://ideas.repec.org/a/fma/fmanag/bessembinder98.html
    Simple technical rules have statistically significant forecast power, but returns "do not appear large enough to outweigh the trading costs."

11. Technical-analysis breakeven-costs working paper (HKUST repository) URL: https://repository.hkust.edu.hk/ir/bitstream/1783.1-362/1/tech.pdf
    Breakeven costs for Brock et al.-style rules declined 0.54% (1926–43) to 0.22% (1976–91) — similar to or smaller than actual trading costs, implying no net edge in sample.

12. ORB backtests (practitioner): https://intradaylab.com/blog/nifty-orb-breakout-strategy-backtest (8-year Nifty ORB backtest, 2,122 trades, costs NOT included — raw edge only); https://github.com/danielsaarva/orb-backtest-audit (look-ahead bias case study: EV +0.283R → ~0.001R after fix); WPI student project https://digital.wpi.edu/downloads/12579s947?locale=en.

13. Polarity principle: NO peer-reviewed study found. Practitioner statements only: FasterCapital (https://fastercapital.com/topics/introduction-to-support-and-resistance.html), entri.app (https://entri.app/blog/support-and-resistance-explained/), Medium guides.

14. PDH/PDL/PDC/open/PMH/PML as levels: NO rigorous academic study found directly testing these specific levels as intraday S/R. Nearest academic neighbors: overnight/open reversal literature (items 1–5) and HKS periodicity (item 6).
