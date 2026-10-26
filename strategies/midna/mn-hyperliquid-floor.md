# Hyperliquid momentum floor

Trades the strongest uncrowded daily mover among liquid Hyperliquid perps, long or short, with a 2R target.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Crypto perps |
| **Timeframe** | intraday (10-min scan) |
| **Universe** | Hyperliquid perps with day notional ≥ $25M |
| **Style** | Momentum |
| **Status** | live |

## Entry

- Long when up ≥ 1% with funding ≤ 0.004%; short when down ≥ 1% with funding ≥ -0.001%; BTC, ETH, SOL first.

## Exit

- Stop = max(0.6%, 1.2 × the mean hourly range of 8 hours), ≤ 8%; target 2R; closed on a mark through either.

## Sizing

- Risk 0.5% of equity per trade, single-name cap 20%, gross cap 60%, ≥ $50, at most 3 open.

## Data

- Hyperliquid public market data.

## Code

- **Master desk**: `sleeves/midna/hyperliquid.py`

## Notes

- The master desk drops Midna's 3% daily-loss halt.
