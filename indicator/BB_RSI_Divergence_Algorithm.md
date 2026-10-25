# BB touch plus RSI divergence — algorithm v2.2

## Purpose and scope

This package turns the screenshot's public BB-touch/RSI-divergence pattern into a configurable chart indicator and a transparent, multi-symbol desk sleeve. The Pine script is the frozen raw indicator. The desk sleeve layers data-integrity, local regime, execution, and risk controls around that same raw trigger.

The Pine script can run on chart symbols/timeframes supported by TradingView. The desk sleeve is currently scoped to liquid US-listed equities and ETFs on completed 1-hour regular-session bars. Its default universe is SPY, QQQ, IWM, DIA, GLD, SLV, TLT, IEF, USO, UUP, XLF, and XLK; the runtime may pass a broader approved active universe, while held symbols remain monitored for exits. Direct FX, futures, options, crypto, and non-US sessions need their own market-data, tick-size, calendar, and execution adapters.

## Frozen raw indicator (v1)

- Bollinger basis: 20-bar SMA of close.
- Bands: basis ± 2 × 20-bar population standard deviation of close.
- RSI: Wilder RSI(14) on close.
- Price swing: 3-left / 3-right confirmed pivot on low or high.
- RSI match: lowest RSI within one bar either side of a low pivot; highest RSI within one bar either side of a high pivot.
- Pivot spacing: 5–60 bars between accepted pivots.
- Minimum RSI difference: 2 points.
- Minimum price extension: any strict lower low for bullish divergence or higher high for bearish divergence.
- Bullish raw signal: lower-band touch at the pivot low, price makes a lower low, and matched RSI makes a higher low.
- Bearish raw signal: upper-band touch at pivot high, price makes a higher high, and matched RSI makes a lower high.
- Close-back-inside requirement: off.
- Marker/alert timestamp: pivot confirmation-bar close, never the historical pivot candle.

Bollinger's rules caution that a band tag alone is not a signal and that price can walk a band during trends. The pivot's right-side bars are needed before its status is knowable. [Bollinger Band Rules](https://www.bollingerbands.com/bollinger-band-rules) and [TradingView pivot documentation](https://www.tradingview.com/pine-script-docs/faq/visuals/) TradingView's RSI documentation describes the Wilder-style average gain/loss calculation used here. [TradingView RSI documentation](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/)

## Desk sleeve v2.2 policy

The sleeve preserves the raw trigger and makes the *risk and opportunity selection* adaptive. No new filter is credited with alpha until replay proves incremental net value.

### 1. Data and event state

On every five-minute sleeve evaluation, refresh the latest completed 1-hour frame for the approved universe and held symbols. Do not reuse a per-session cached frame as current market data. Normalize timestamps, keep completed regular-session bars, and reject malformed, stale, or recently gapped frames. A new hourly cursor is required for entries; an open position is re-evaluated for exits on each scan while the current completed bar remains fresh.

The last bar must be no more than 10 minutes past its close for a new entry decision. Quotes must be no more than 60 seconds old and spreads no wider than 15 bp. The fill and order snapshots must be available; missing or ambiguous own-state blocks new entries. A working/partially filled entry blocks another, and one opening fill per session is allowed.

### 2. Local volatility adaptation

Let (a_t = ATR_{14,t}/C_t), where ATR uses Wilder smoothing. Let (m_t) be the median (a) over the current and prior 59 completed bars. Define:

[
v_t = operatorname{clip}left(rac{1}{sqrt{max(1,a_t/m_t)}},,0.5,,1ight).
]

This only reduces the base risk when current ATR-percent is elevated relative to its own recent history. Quiet conditions do not increase risk. The existing 0.25% equity risk budget and 5% notional cap remain hard ceilings. The volatility-managed portfolio literature motivates testing reduced risk in high-volatility states, but does not establish that this intraday sleeve benefits from this specific rule. [Moreira and Muir, *Volatility-Managed Portfolios*](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.12513)

### 3. Trend and band-walk awareness

For the latest confirmation bar, define a signed 12-bar efficiency ratio:

[
ER_t = \frac{C_t-C_{t-12}}{\sum_{j=t-11}^{t}|C_j-C_{j-1}|}.
]

For a bullish candidate, count lower-band closes across the latest four bars. If (ER_t \le -0.55) and at least two of those closes are at/below the lower band, label the state `downtrend_band_walk` and set (g_t=0.5). Otherwise (g_t=1). The bearish mirror is used for diagnostics and exits. This is a bounded risk reduction, not a signal veto.

Combined scale:

[
r_t = \max(0.25, v_t g_t), qquad
\text{risk dollars} = \text{equity} \times 0.25\% \times r_t.
]

The thresholds are explicit research parameters, not empirically optimized values.

### 4. Candidate selection and execution

For each fresh bullish setup, compute an entry limit at the current ask, stop at pivot low minus (0.5 ATR), and target at the confirmation bar's Bollinger basis. Require positive reward and risk, at least 1.2 planned reward/risk, spread ≤15 bp, fresh quote, current completed bar, valid equity, and reconciled position/order state.

Rank qualified candidates by adaptive risk scale, planned reward/risk, RSI divergence magnitude, band-touch depth divided by ATR, quoted spread, and ticker (deterministic tie-break). Open at most one sleeve position globally. Bearish divergence closes an existing long in the same symbol; it does not open shorts. Exit triggers are the primary stop, Bollinger basis target, 24 completed RTH hourly bars, or bearish divergence. If a single hourly candle touches both stop and target, treat the stop as first. Entries are deduplicated by the persistent bar cursor; active close orders suppress duplicate closes and block new entries until resolved. The target and time exit are evaluated by the five-minute desk scan from completed hourly bars; they are not broker-native OCO orders.

Limit orders can remain unfilled, so the execution ledger must preserve working, canceled, rejected, and missed-fill outcomes rather than treating the displayed ask as a guaranteed fill. [Alpaca order types](https://docs.alpaca.markets/us/docs/orders-at-alpaca)

## Autonomy contract

Each evaluation exposes per-symbol states, candidate/abstention reasons, raw signal measures, regime features, selected instrument, quote timestamp/spread, risk scale, planned reward/risk, and size. The deterministic sleeve owns signal qualification and risk boundaries. An LLM may explain or research logged cases; it cannot override data, order, or risk gates, or send an order outside the versioned deterministic policy.

The system scans a broader universe to improve opportunity coverage. It has no daily trade quota; “more active” is not a valid objective if expected net payoff is negative or own-state/data are uncertain.

## Evidence status

The v1 one-year exploratory replay covered SPY, QQQ, GLD, and TLT and produced only three entries after its reward/risk gate. That sample cannot establish a repeatable edge. The v2 risk overlay is a proposed enhancement with no replay result yet. Adjacent research on volatility management does not validate this sleeve, and backtest selection can overstate performance when many variants are tried. Freeze v1, v2, the touch-only control, costs, universe, and final period before further parameter review. [Bailey et al., *The Probability of Backtest Overfitting*](https://escholarship.org/uc/item/4w1110bb)

See [the research record](../docs/BB_RSI_Divergence_Research.md) and [Femto-lean wiring and promotion gates](../integration/Femto-lean_Wiring.md). The module is enabled for paper in the staged branch, but it has not been deployed to a paper runner and no paper forward run has occurred. Runtime paper qualification and real-money promotion remain distinct; live-money promotion still requires indicator parity, chronological fill-aware replay, broker lifecycle qualification, portfolio-level risk controls, and shadow/paper evidence.
