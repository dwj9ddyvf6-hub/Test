# Momentum breakout (legacy setup)

Buys $100 of a scanned name pressing its 20-bar high on rising volume, with a 1.5% stop and a 3% target.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk agentic runtime, SetupAgents momentum_breakout |
| **Asset** | US equities |
| **Timeframe** | 1m (15-minute cycle) |
| **Universe** | SPY, QQQ, IWM, the SCOPE radar's top 100, held names |
| **Style** | Intraday breakout |
| **Status** | waiting |

## Entry

- Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread ≤ 0.6%; score = 0.8 × |gap| + |intraday move| + min(relative volume, 5) + log10(dollar volume) / 3.
- The 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars.
- Setup: price ≥ 99.9% of the 20-bar high, relative volume ≥ 1.5 and RSI(14) < 78 (+3 points).
- BUY: scan + headline + setup points ≥ 5, price not over EMA 20 + 2.5 × max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%.
- Order: $100 (round(100 / price, 6) shares) as a DAY limit at the price × 1.001; at most 30 positions, never a held or working name.

## Exit

- Stop 1.5% under the entry, target 3% over it.

## Sizing

- $100 a trade.

## Data

- Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes).

## Code

- **Master desk**: `sleeves/griffith/griffith_intraday.py`; not in this repo: `desk/vendor/griffith/config.json`
