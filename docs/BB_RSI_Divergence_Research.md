# BB touch plus RSI divergence — research record

**Status:** hypothesis / paper-enabled code; no forward paper run  
**As of:** 2026-10-24  
**Mode:** CREATE  
**Decision:** whether to advance a multi-symbol, 1-hour mean-reversion sleeve into shadow and paper qualification  
**Current decision:** do not promote. The exploratory replay is too small and too weak to establish net expectancy.

## Edge contract

| Field | Current assessment |
|---|---|
| Instrument and horizon | Liquid US-listed ETFs/equities; completed 1-hour bars |
| Proposed pattern | A price pivot extends beyond the previous swing at a 2-sigma Bollinger touch while Wilder RSI forms a higher low (bullish) or lower high (bearish) |
| Economic mechanism | **Hypothesis:** temporary price pressure or exhaustion reverses toward the intermediate mean |
| Our measurable advantage | None established. The rule is public and mechanical; no information or execution advantage is claimed |
| Strongest rival | Trend continuation / band-walking causes losses before price returns to the mean |
| Benchmark | The same pivot-and-band-touch setup without the RSI-divergence filter |
| Falsifier | The divergence filter fails to improve forward net R over the matched touch-only control after realistic execution costs, or the result disappears in a chronological holdout |
| Capacity | Expected to be low turnover; only one position is allowed at a time |
| Adverse state | Persistent trend, overnight gap through stop, wide quote, or stale/missing hourly bars |

## Primary-source findings

- Bollinger's own rules say band tags are not signals, prices can walk a band in trends, and closes outside the band initially act as continuation signals. The 20-bar / 2-standard-deviation settings are defaults, and the band construction does not imply normally distributed returns.  
  Source: [Bollinger Band Rules](https://www.bollingerbands.com/bollinger-band-rules)
- TradingView documents RSI as the ratio of Wilder-smoothed average gains and losses. It defines regular bullish divergence as price making a lower low while RSI makes a higher low, and bearish divergence as price making a higher high while RSI makes a lower high.  
  Source: [TradingView RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/)
- TradingView's Pine documentation notes that pivot highs/lows are confirmed only after the specified right-side bars have elapsed. This sleeve timestamps the signal on that confirmation bar and never trades a back-plotted pivot marker.  
  Source: [TradingView pivot documentation](https://www.tradingview.com/pine-script-docs/faq/visuals/)
- Mean-reversion results are highly sensitive to frictions. A broad equity-market study found mean-reversion portfolio rules could fail in recent data, especially with explicit or implicit transaction costs. A separate high-frequency futures study found the apparent profits in its technical-rule family disappeared after transaction costs. Neither paper tests this exact signal; both motivate adversarial cost testing.  
  Sources: [Moon, Kim and Moon (2019)](https://arxiv.org/abs/1909.04327); [Chen, Zhou and Xi (2017)](https://arxiv.org/abs/1710.07470)

## Adaptive enhancement study — 2026-10-24

### Decision

**Evidence stage:** research candidate; no v2 performance result.  
**Decision:** keep the original v1 signal frozen and add a transparent v2 risk/context layer for evaluation. The changes improve state awareness, stale-data defense, and decision auditability. They do not establish positive net expectancy.

### Internet research findings

- **Bollinger Bands:** the source author's rules caution that a band touch alone is not a signal, prices can walk a band during trends, and an outside close can initially indicate continuation. This supports preserving divergence as the trigger while adding a trend-risk awareness layer. It does not prescribe this sleeve's efficiency-ratio rule. [Bollinger Band Rules](https://www.bollingerbands.com/bollinger-band-rules)
- **Technical-rule evaluation:** Lo, Mamaysky, and Wang formalized chart patterns and statistically examined their conditional information content. Their work supports precise, reproducible definitions and inferential testing; it does not test this BB/RSI implementation or show that this particular payoff survives costs. [NBER paper](https://www.nber.org/papers/w7613) · [Journal of Finance version](https://doi.org/10.1111/0022-1082.00265)
- **Volatility scaling:** Moreira and Muir found that volatility-managed versions of the factor portfolios they studied improved risk-adjusted results. Their evidence motivates testing risk reduction in higher-volatility states, but it is monthly/factor-portfolio research, not evidence for this hourly divergence sleeve. [Journal of Finance paper](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.12513)
- **Model selection:** Bailey et al. show how selecting among tried strategies can make backtest performance overstate future performance. Therefore thresholds and variants must be frozen and every attempted v1/v2/control recorded. [Probability of Backtest Overfitting](https://escholarship.org/uc/item/4w1110bb)
- **Execution:** Alpaca documents that a limit order can remain unfilled even when it limits the price. A valid replay must model fills and missed fills, not assume the displayed quote was executable. [Alpaca order documentation](https://docs.alpaca.markets/us/docs/orders-at-alpaca)
- **Bar time:** Alpaca explains that bars represent aggregation intervals and timestamps refer to the interval start. The integration logic uses that boundary when deciding whether an hourly bar has closed. Verify this with the actual provider configuration. [Alpaca market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)

### Implemented v2 changes

1. **Preserve v1 signal identity.** Band, RSI, pivot, divergence, spacing, and confirmation rules are unchanged in the Pine indicator and sleeve.
2. **Add a bounded volatility scale.** Compare latest ATR(14)/close with its trailing 60-bar median. Apply (\operatorname{clip}(1/\sqrt{\max(1, ratio)}, 0.5, 1.0)). It can reduce the 0.25% base equity risk, never increase it.
3. **Add a local trend/band-walk risk flag.** Calculate a signed 12-bar efficiency ratio. For bullish candidates, if ER ≤ −0.55 and at least two of the last four closes are at/below the lower band, classify `downtrend_band_walk` and halve risk. Combine both scalers with a 0.25 minimum multiplier.
4. **Improve candidate ordering and audit records.** Rank candidates deterministically using risk scale, planned reward/risk, divergence size, normalized band penetration, spread, and ticker. Record regime inputs, risk components, bar/quote times, and per-symbol rejection reasons.
5. **Require order lifecycle awareness.** In addition to fill history, the code now requires session order state and blocks entries while a prior opening order is active or partially filled. This prevents the signal loop from treating an unfilled resting order as no activity.
6. **Fix the hourly cache contract.** Code review found that the earlier wiring example fetched only symbols missing from a per-session cache. If the cache survived each evaluation, it could stop seeing later bars. The v2 wiring instructions now require fresh rolling frames each evaluation and permit only provider-side caching that refreshes the latest closed interval.
7. **Retain abstention.** The wider 12-ETF scan improves opportunity coverage but imposes no daily trade quota. Missing, stale, wide, unreconciled, or unfavorable candidates remain no-trade outcomes. The decision path stays deterministic; an LLM may explain or research cases but cannot override risk/data/order gates.

The regime thresholds and scaling formula are engineering hypotheses. The volatility-management paper motivates the experiment, not the chosen constants. No parameter sweep or v2 replay has been run; no profitability or hit-rate improvement is claimed.

### Multi-asset opportunity-coverage scan

A separate one-year IEX scan used the 12 default ETFs, filtered to complete hourly intervals within 09:30–16:00 ET, and applied the entry-close window plus a 1.2 reward/risk gate using the next hourly open with a 5 bp per-side cost proxy. It found **5 candidate long entries across 268 observed sessions**, each on a different session: QQQ 1, DIA 1, USO 1, and XLK 2. GLD had no qualifying candidate. The median adaptive risk scale among those five was 1.00; the minimum was 0.86, and no qualifying setup activated the trend/band-walk reduction. There were no simultaneous qualified candidates, so the v1/v2 ranking rule selected the same symbol in this sample.

This was an opportunity-coverage scan, not a P&L backtest: it did not model stops, targets, fills, active-position time, or portfolio returns. The 5 bp proxy is an assumption. IEX data and next-open execution differ from the sleeve's SIP, displayed-quote limit entry. Three UUP raw setups were blocked by the recent-hourly-gap guard in this IEX sample. The result shows that a broad 12-ETF basket still does not create daily signals. The runtime-configurable universe is now supported, but any broader universe must be defined point-in-time, liquid-screened, and evaluated as a new research choice. Do not relax the divergence rules solely to reach a daily trade count.

### Decisive next evaluation

Freeze three policies before the next run:

- **v1:** original BB/RSI trigger and fixed 0.25% sizing.
- **v2a:** v1 plus volatility scale only.
- **v2b:** v2a plus trend/band-walk scale.

Compare them with the same eligible timestamps, 12-symbol universe, sizing and exits, and a lower-band-pivot touch-only control. Use chronological development, validation, and untouched final periods; record every attempted variant. Include SIP data parity, quote-side prices, actual or conservative limit-fill probabilities, partial/nonfills, costs, same-bar stop priority, one-position constraint, order-state recovery, and portfolio-level correlation.

Report incremental net R versus v1, trade and no-trade opportunity counts, exposure, fill rate, missed opportunities, drawdown/tails, turnover/costs, and confidence intervals clustered by signal episode and time. Reject the added layer if it fails to improve the frozen benchmark after costs, if results rely on one symbol/regime, or if its apparent gain disappears in the final period. Until that evaluation and paper qualification pass, keep execution confined to the broker's paper-only route. `CONFIG.parked=False` enables the controlled paper qualification run; it is not live-money authorization.

## Exploratory multi-asset replay

**Data:** Alpaca IEX 1-hour bars for SPY, QQQ, GLD and TLT, 2025-10-01 through 2026-10-23. The replay kept complete bars inside 09:30–16:00 ET. Each symbol had 1,603–1,604 eligible bars. IEX is not the desk's SIP input, and the replay did not use live quotes or actual fills.

**Frozen signal parameters:** 20-bar SMA and population standard deviation, 2 sigma, Wilder RSI(14), 3-left/3-right price pivots, RSI alignment radius 1, 5–60 pivot spacing, 2-point RSI divergence, no minimum price extension beyond a strict higher/lower swing, no close-back-inside requirement.

**One candidate execution model:** long-only; enter at next RTH hourly open; stop 0.5 ATR(14) below the swing low; target the confirmation bar's Bollinger basis; time stop after 24 RTH hourly bars; require at least 1.2 planned reward/risk; charge 5 bp on entry and exit; if stop and target both appear inside one bar, assume stop first. Bearish divergence closes an open long. This is a conservative bar replay, not a simulation of the sleeve's displayed-quote limit order.

| Symbol | Bullish divergence signals | Entries after reward/risk gate | Replay result at 5 bp/side |
|---|---:|---:|---|
| GLD | 4 | 0 | No qualifying trade |
| QQQ | 7 | 2 | 50% wins; +0.47 R mean; PF 1.84 |
| SPY | 3 | 0 | No qualifying trade |
| TLT | 4 | 1 | −1.93 R; stopped out |
| **Total** | **18** | **3** | **Too few trades to infer an edge** |

The matched long-only control removed the RSI-divergence requirement but kept the lower-band price pivot and exits. It produced 56 trades and negative net R in each symbol: GLD −7.80 R, QQQ −2.42 R, SPY −1.90 R and TLT −1.37 R. The filter reduced activity substantially; the three qualifying divergence trades do not demonstrate that it adds value. The first half of the replay produced no qualifying entries; the last half produced all three.

### Limits of this replay

- Only one year, four ETFs, and three qualifying entries. The result has no useful statistical power and no untouched holdout.
- No quotes, order queue, partial fills, market impact, dividends, borrow cost, or actual broker execution were modeled. The 5 bp cost is a scenario assumption, not an observed fill cost.
- Per-symbol results were simulated separately. The sleeve's global one-position rule and cross-symbol signal ranking were not replayed as a portfolio.
- The replay used IEX data, while the desk integration note specifies the desk's SIP hourly bars. Feed differences may change pivots and signals.
- The next-bar-open replay differs from the sleeve's fresh-quote limit entry. This execution mismatch must be measured before promotion.
- The research looked at the same period reported here; it is exploratory, not a preregistered confirmatory study.

## Promotion work still required

1. Freeze the universe, signal version, exit policy, cost model, benchmark, dates, and trial ledger.
2. Replay a longer history per symbol on the exact SIP data path; include delisted or changed symbols where relevant.
3. Compare the divergence sleeve with the matched touch-only control, buy-and-hold exposure, and cash using identical timestamps and sizing.
4. Use chronological development, validation, and untouched final periods. Keep the portfolio one-position constraint and correlated signals in the replay.
5. Reconcile quote-side, spread, latency, gaps, limit non-fills, and paper fills; preserve every attempt and abstention.
6. Run shadow and then paper qualification with no live-money route. Keep the module parked until the desk's ordinary promotion review accepts the evidence.

## Decision record

No positive expected net payoff, benchmark excess return, or portfolio-utility improvement has been established. The implementation is a research candidate. The sleeve is paper-enabled in code but its runtime branch remains unmerged and undeployed; no forward paper run has occurred.
