# Three catalogue-inspired public-rule sleeves

The owner explicitly authorized three new sleeves after researching the Trader.dev catalogue. They extend the four frozen Tensor sleeves with separately owned local paper books. The original Tensor indicators, model assets, enrollment, thresholds, clocks and book ownership remain unchanged.

These are independently implemented public-rule adaptations. Anonymous public reports disclose backtest summaries and trade lists, but exact Trader.dev Pine source and forks require an authorized owner or paid account. Consequently, the desk does not claim byte-for-byte source parity, identical trades, or transfer of the catalogue's crypto returns to equities.

The fixed version-one universe consists of SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH and SOXX. It is a present-day liquid ETF universe, not a historical point-in-time constituent database. All three sleeves use completed XNYS daily bars and at least 252 observations. Each sleeve has its own $100,000 virtual paper book. Construction installs and funds nothing; installation is an explicit operator action.

## Frozen rules

**Donchian trend:** Enter after a completed daily close exceeds the highest high of the preceding 55 bars and exceeds the 200-bar simple moving average. The breakout channel excludes the decision bar. Exit after a close below the preceding 20-bar lowest low or below the 200-bar average, after 126 observed holding bars, or at the first admissible observed quote that breaches the fixed initial stop two entry-signal ATRs below the fill. Risk sizing limits the initial nominal stop loss to 0.5% of marked sleeve equity before the shared cash/notional/liquidity caps. An observed gap can lose more than that nominal budget.

**RSI(2) pullback:** Enter when Wilder RSI(2) is at most 5, price is above its 200-bar simple average, and price is below its 5-bar average. Exit after a completed close above the 5-bar average or ten observed holding bars. There is no invented intrabar trailing stop. Rank the lowest RSI first, then the defined ATR-normalized pullback and symbol tie-break.

**BB/KC squeeze breakout:** Use 20-bar Bollinger bands with population standard deviation multiplied by two, and a modern Keltner channel centered on EMA(20) with 1.5 times Wilder ATR(20). Enter on release from containment, with positive and increasing endpoint regression momentum and a close above the preceding 20-bar high. Momentum follows the separately documented public LazyBear-style calculation. Exit on a close below the Keltner center, nonpositive momentum, twenty observed holding bars, or a fixed two-ATR initial observed-quote stop. This modern formula and the exit/risk controls are declared adaptations; they are not asserted to match Carter's original TTM formula or inaccessible Trader.dev Pine code.

The implementation's canonical definitions, arithmetic and ranking are authoritative in `backend/trader_signals.py` and `strategies/trader_catalogue/rules-v1.json`. A version/configuration identity binds the installed rule and universe; historical testing does not refit them.

## Execution

Signals originate from fully observed completed source periods. Entries are eligible at the following XNYS opening within the fixed 300-second observed-quote window. Historical opening opportunities are not replayed. Each book permits ten held or pending whole-share positions and limits fee/slippage-inclusive entry debit to the minimum of 10% of current equity, 1% of mean 20-bar dollar volume, settled available cash, and any rule-specific stop-risk size. The normal paper fill engine rechecks the durable debit cap when prices gap and blocks a quantity that would exceed it; it does not promise automatic resizing or a fill. Simulation uses ten basis points of slippage on each side.

These sleeves require the normal whole-order local fill policy. If the policy changes after admission, a no-network preflight cancels the affected pending entry. An unexpected measured first partial is retained and binds the actual first-fill stop, while the unfilled remainder is cancelled before a later supervisor fill. This avoids raising the aggregate nominal stop risk by purchasing later shares at a higher price against an unchanged stop anchor.

Sale proceeds follow the existing conservative T+1 spendable-cash convention. Corporate action provenance, quantity/basis changes, dividend receivables and uncertainty gates use the existing owned-book accounting service. Initial stops are compared in current split-adjusted share units without overwriting their original measured anchor. Disabling entries preserves held positions, risk service and durable owed exits. Closing-bar exits submit for the following opening; missed owed exits remain recoverable. A held name's own healthy data can generate its rule exit independently of failures elsewhere in the entry universe. Quote-triggered stops fill at an observed executable quote, not a retrospectively favorable OHLC path or the theoretical stop price.

Daily broad acquisition is bounded and gives the existing hourly Tensor opening its protected time budget. Separate families share the normal fenced execution engine, with a processing boundary between families to avoid stranding already authorized orders behind unrelated research.

## Evidence and limits

Catalogue engine validation is a compatibility/execution claim, not independent out-of-sample validation of alpha. Public reports contain repeated variants, parameter searches, partial-exit trade rows and very tight trailing exits. A clock-only-entry control also reports substantial returns with a micro-trail; such returns cannot by themselves identify predictive entry edge.

Trend following has substantial independent cross-asset evidence; the exact daily long-only ETF rule is a new implementation. RSI(2) has public reproducible rules but mixed results and material turnover/cost risk. Squeeze mechanics are public, while independently replicated net-of-cost evidence for this exact ETF sleeve is weak. All three remain paper research strategies until forward evidence supports promotion. Profitability and beating QQQ or SPY are goals, not established outcomes.

The study archive contains the catalogue census scope, winning and losing representative reports, explicit source gaps, fixed-rule real-data tests, cost sensitivity, benchmark comparisons and verification receipts. The historical test's adjusted-bar stop simulation is distinguished from actual quote-triggered forward execution.
